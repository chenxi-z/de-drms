"""Storage-owner file access: generated names, session and media-generation guards."""
import ctypes
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1] / 'firmware/DE-DRMS-Code'
HEADER = r'''
#include <stdint.h>
typedef unsigned int UINT;
typedef unsigned long ULONG;
typedef unsigned long long ULONG64;
typedef struct { int unused; } FX_MEDIA;
typedef struct { ULONG64 fx_file_current_file_size; } FX_FILE;
#define FX_SUCCESS 0
#define FX_OPEN_FOR_READ 0
#define FX_NOT_FOUND 4
UINT fx_file_open(FX_MEDIA *, FX_FILE *, char *, UINT);
UINT fx_file_extended_seek(FX_FILE *, ULONG64);
UINT fx_file_read(FX_FILE *, void *, ULONG, ULONG *);
UINT fx_file_close(FX_FILE *);
'''
MOCK = r'''
#include "app_filex.h"
#include "drms_architecture_contract.h"
#include <string.h>
FX_MEDIA sdio_disk;
volatile unsigned int drms_storage_mounted = 1;
volatile uint32_t drms_log_state;
uint32_t mock_generation=1, mock_owner, opens, closes, reads, fail_read, strict_names;
char opened_name[32];
static uint32_t pos;
uint32_t drms_storage_media_generation(void) { return mock_generation; }
DRMS_Owner drms_msc_owner(void) { return (DRMS_Owner)mock_owner; }
UINT fx_file_open(FX_MEDIA *m,FX_FILE *f,char *name,UINT mode) {
 (void)m;(void)mode; ++opens; strcpy(opened_name,name);
 if(strict_names && strcmp(name,"DRMS0042.BIN")) return FX_NOT_FOUND;
 f->fx_file_current_file_size=10;pos=0;return FX_SUCCESS; }
UINT fx_file_extended_seek(FX_FILE *f,ULONG64 offset) { (void)f;pos=(uint32_t)offset;return 0; }
UINT fx_file_read(FX_FILE *f,void *out,ULONG n,ULONG *actual) {
 (void)f; ++reads; if(fail_read) return 1; memcpy(out,"0123456789"+pos,n);pos+=n;*actual=n;return 0; }
UINT fx_file_close(FX_FILE *f) { (void)f;++closes;return 0; }
'''

class FileBackendTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(); p=Path(cls.tmp.name)
        (p/'app_filex.h').write_text(HEADER); (p/'mock.c').write_text(MOCK)
        subprocess.run(['cc','-shared','-fPIC','-Wall','-Werror','-I',str(p),'-I',str(ROOT/'Core/Inc'),
                        str(ROOT/'Core/Src/drms_file_backend.c'),str(p/'mock.c'),'-o',str(p/'f.so')],check=True)
        cls.lib=ctypes.CDLL(str(p/'f.so'))
        cls.lib.drms_file_backend_open.argtypes=[ctypes.c_uint32,ctypes.c_uint32,ctypes.c_uint32,ctypes.POINTER(ctypes.c_uint64)]
        cls.lib.drms_file_backend_read.argtypes=[ctypes.c_uint32,ctypes.c_uint32,ctypes.c_uint64,ctypes.c_uint16,ctypes.c_void_p,ctypes.POINTER(ctypes.c_uint16),ctypes.POINTER(ctypes.c_uint8)]
    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()
    def value(self,name): return ctypes.c_uint32.in_dll(self.lib,name)
    def setUp(self):
        self.lib.drms_file_backend_init()
        for name in ('opens','closes','reads','mock_owner','drms_log_state','fail_read','strict_names'): self.value(name).value=0
        self.value('mock_generation').value=1; self.value('drms_storage_mounted').value=1
    def open(self, ident=42,session=4,generation=1):
        size=ctypes.c_uint64(); result=self.lib.drms_file_backend_open(ident,session,generation,ctypes.byref(size))
        return result,size.value
    def read(self, session=4,generation=1,offset=0,count=4):
        out=ctypes.create_string_buffer(768); n=ctypes.c_uint16(); eof=ctypes.c_uint8()
        result=self.lib.drms_file_backend_read(session,generation,offset,count,out,ctypes.byref(n),ctypes.byref(eof))
        return result,out.raw[:n.value],eof.value
    def test_open_is_numeric_read_is_bounded_and_repeatable(self):
        self.assertEqual(self.open(),(0,10))
        self.assertEqual(bytes((ctypes.c_char*32).in_dll(self.lib,'opened_name')).split(b'\0')[0],b'DRMS0042.BIN')
        self.assertEqual(self.read(offset=7,count=6),(0,b'789',1))
        self.assertEqual(self.read(offset=7,count=6),(0,b'789',1))
        self.assertEqual(self.read(offset=10,count=1),(0,b'',1))
        self.assertEqual(self.read(offset=11)[0],3)
        self.assertEqual(self.read(count=769)[0],3)
        self.assertEqual(self.read(count=0)[0],3)
    def test_wrong_session_and_swapped_media_never_read(self):
        self.assertEqual(self.open()[0],0)
        self.assertEqual(self.read(session=5)[0],4)
        self.assertEqual(self.value('reads').value,0)
        self.value('mock_generation').value=2
        self.assertEqual(self.read()[0],4)
        self.assertEqual(self.value('reads').value,0)
        self.assertEqual(self.value('closes').value,0)
    def test_recording_or_msc_blocks_access_and_io_error_closes(self):
        self.value('drms_log_state').value=1
        self.assertEqual(self.open()[0],2)
        self.value('drms_log_state').value=0; self.value('mock_owner').value=2
        self.assertEqual(self.open()[0],2)
        self.value('mock_owner').value=0
        self.assertEqual(self.open()[0],0)
        self.value('fail_read').value=1
        self.assertEqual(self.read()[0],6)
        self.assertEqual(self.value('closes').value,1)
        self.assertEqual(self.open(ident=10000)[0],3)
        self.value('strict_names').value=1
        self.assertEqual(self.open(ident=41)[0],3)
    def test_listing_checks_only_one_candidate_and_enforces_media_epoch(self):
        self.value('strict_names').value = 1
        found=ctypes.c_uint32(); size=ctypes.c_uint64(); cursor=ctypes.c_uint32()
        self.lib.drms_file_backend_list_step.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_uint32)]
        def step(pos, generation=1):
            return self.lib.drms_file_backend_list_step(pos,generation,ctypes.byref(found),ctypes.byref(size),ctypes.byref(cursor))
        self.assertEqual(step(40),1)  # no match; caller yields and advances
        self.assertEqual((cursor.value,self.value('opens').value),(41,1))
        self.assertEqual(step(42),0)
        self.assertEqual((found.value,size.value,cursor.value),(42,10,43))
        self.assertEqual(step(44,2),4)
        self.assertEqual(step(10000),12)
