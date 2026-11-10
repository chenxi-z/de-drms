"""Asynchronous file request ownership, cancellation, and storage-worker isolation."""
import ctypes
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]/'firmware/DE-DRMS-Code'
MOCK = r'''
#include "drms_file_service.h"
#include <string.h>
uint32_t calls_open,calls_read,calls_close,calls_list,disconnect_in_open,disconnect_in_read;
uint32_t close_result;
DRMS_Result drms_file_backend_open(uint32_t id,uint32_t s,uint32_t g,uint64_t *size) {
 (void)id;(void)g;++calls_open;*size=8;if(disconnect_in_open) drms_file_service_disconnect(s);return DRMS_OK; }
DRMS_Result drms_file_backend_read(uint32_t s,uint32_t g,uint64_t o,uint16_t n,uint8_t *p,uint16_t *actual,uint8_t *eof) {
 (void)g;(void)o;++calls_read;memset(p,'A',n);*actual=n;*eof=1;if(disconnect_in_read) drms_file_service_disconnect(s);return DRMS_OK; }
DRMS_Result drms_file_backend_close(uint32_t s,uint32_t g) { (void)s;(void)g;++calls_close;return (DRMS_Result)close_result; }
DRMS_Result drms_file_backend_list_step(uint32_t cursor,uint32_t g,uint32_t *id,uint64_t *size,uint32_t *next) {
 (void)g;++calls_list;*next=cursor+1;if(cursor<3)return DRMS_ACCEPTED;*id=cursor;*size=8;return DRMS_OK; }
'''
class Request(ctypes.Structure):
    _fields_=[('kind',ctypes.c_uint32),('session',ctypes.c_uint32),('generation',ctypes.c_uint32),
              ('file_id',ctypes.c_uint32),('cursor',ctypes.c_uint32),('offset',ctypes.c_uint64),('count',ctypes.c_uint16)]
class Reply(ctypes.Structure):
    _fields_=[('ticket',ctypes.c_uint64),('result',ctypes.c_int),('file_id',ctypes.c_uint32),('next_cursor',ctypes.c_uint32),
              ('size',ctypes.c_uint64),('offset',ctypes.c_uint64),('length',ctypes.c_uint16),('eof',ctypes.c_uint8),('data',ctypes.c_ubyte*768)]
class FileServiceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(); p=Path(cls.tmp.name)
        (p/'main.h').write_text('#include <stdint.h>\n#define __get_PRIMASK() 0u\n#define __disable_irq() ((void)0)\n#define __set_PRIMASK(x) ((void)(x))\n')
        (p/'mock.c').write_text(MOCK)
        subprocess.run(['cc','-shared','-fPIC','-Wall','-Werror','-I',str(p),'-I',str(ROOT/'Core/Inc'),
                        str(ROOT/'Core/Src/drms_file_service.c'),str(p/'mock.c'),'-o',str(p/'service.so')],check=True)
        cls.lib=ctypes.CDLL(str(p/'service.so'))
        cls.lib.drms_file_service_submit.argtypes=[ctypes.POINTER(Request),ctypes.POINTER(ctypes.c_uint64)]
        cls.lib.drms_file_service_take.argtypes=[ctypes.c_uint64,ctypes.POINTER(Reply)]
    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()
    def val(self,name): return ctypes.c_uint32.in_dll(self.lib,name)
    def setUp(self):
        self.lib.drms_file_service_init()
        for name in ('calls_open','calls_read','calls_close','calls_list','disconnect_in_open','disconnect_in_read','close_result'): self.val(name).value=0
    def submit(self, kind, **kwargs):
        req=Request(kind=kind,session=4,generation=7,**kwargs); ticket=ctypes.c_uint64()
        return self.lib.drms_file_service_submit(ctypes.byref(req),ctypes.byref(ticket)),ticket.value
    def take(self,ticket):
        out=Reply(); return self.lib.drms_file_service_take(ticket,ctypes.byref(out)),out
    def test_open_read_close_only_storage_poll_touches_backend(self):
        result,t=self.submit(2,file_id=42); self.assertEqual(result,1)
        self.assertEqual(self.val('calls_open').value,0); self.assertEqual(self.take(t)[0],1)
        self.lib.drms_file_service_poll(); code,r=self.take(t); self.assertEqual((code,r.result,r.size),(0,0,8))
        self.assertEqual(self.lib.drms_file_service_quiescent(),0)
        result,t=self.submit(3,offset=2,count=3); self.assertEqual(result,1)
        self.lib.drms_file_service_poll(); code,r=self.take(t)
        self.assertEqual((code,r.result,r.offset,r.length,bytes(r.data[:3])),(0,0,2,3,b'AAA'))
        result,t=self.submit(4); self.assertEqual(result,1); self.lib.drms_file_service_poll()
        self.assertEqual(self.take(t)[1].result,0); self.assertEqual(self.lib.drms_file_service_quiescent(),1)
    def test_list_yields_between_probes_and_can_cancel(self):
        result,t=self.submit(1,cursor=0); self.assertEqual(result,1)
        self.lib.drms_file_service_poll(); self.assertEqual(self.val('calls_list').value,1)
        self.assertEqual(self.take(t)[0],1)
        self.lib.drms_file_service_disconnect(4); self.lib.drms_file_service_poll()
        self.assertEqual(self.lib.drms_file_service_quiescent(),1)
        self.assertEqual(self.take(t)[0],4)
    def test_disconnect_during_open_closes_before_reuse(self):
        self.val('disconnect_in_open').value=1
        result,t=self.submit(2,file_id=42); self.assertEqual(result,1)
        self.lib.drms_file_service_poll()
        self.assertEqual(self.val('calls_close').value,1)
        self.assertEqual(self.take(t)[0],4)
        self.assertEqual(self.lib.drms_file_service_quiescent(),1)
    def test_close_failure_quarantines_and_keeps_resource_unavailable(self):
        result,t=self.submit(2,file_id=42); self.lib.drms_file_service_poll(); self.take(t)
        self.val('close_result').value=10
        self.lib.drms_file_service_disconnect(4); self.lib.drms_file_service_poll()
        self.assertEqual(self.lib.drms_file_service_quiescent(),0)
        self.assertEqual(self.lib.drms_file_service_quarantined(),1)
        self.assertEqual(self.submit(2,file_id=42)[0],10)
        self.assertEqual(self.lib.drms_file_service_after_media_abort(),0)
        self.assertEqual(self.lib.drms_file_service_quiescent(),1)
        self.assertEqual(self.submit(2,file_id=42)[0],1)
    def test_disconnect_during_read_discards_bytes_and_closes_handle(self):
        _,ticket=self.submit(2,file_id=42); self.lib.drms_file_service_poll(); self.take(ticket)
        self.val('disconnect_in_read').value=1
        _,ticket=self.submit(3,offset=0,count=8)
        self.lib.drms_file_service_poll()
        self.assertEqual(self.take(ticket)[0],4)
        self.assertEqual((self.val('calls_read').value,self.val('calls_close').value),(1,1))
        self.assertEqual(self.lib.drms_file_service_quiescent(),1)
    def test_wrong_session_or_generation_cannot_use_open_handle(self):
        _,ticket=self.submit(2,file_id=42); self.lib.drms_file_service_poll(); self.take(ticket)
        ticket_out=ctypes.c_uint64()
        for session,generation in ((5,7),(4,8)):
            req=Request(kind=3,session=session,generation=generation,count=1)
            self.assertEqual(self.lib.drms_file_service_submit(ctypes.byref(req),ctypes.byref(ticket_out)),4)
        self.assertEqual(self.val('calls_read').value,0)
