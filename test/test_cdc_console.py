"""CDC console keeps framing across short packets and disconnected sessions."""
import ctypes
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HEADER = r'''
#include <stddef.h>
#include <stdint.h>
typedef unsigned int UINT;
typedef unsigned long ULONG;
typedef unsigned char UCHAR;
typedef void VOID;
typedef struct { unsigned int ux_slave_class_cdc_acm_data_dtr_state; } UX_SLAVE_CLASS_CDC_ACM;
typedef struct { int unused; } TX_THREAD;
#define UX_NULL ((void *)0)
#define UX_SUCCESS 0
#define UX_DEVICE_RESET 0
#define UX_SLAVE_CLASS_CDC_ACM_IOCTL_ABORT_PIPE 4
#define UX_SLAVE_CLASS_CDC_ACM_ENDPOINT_XMIT 1
#define UX_SLAVE_CLASS_CDC_ACM_ENDPOINT_RCV 2
#define UX_TRANSFER_TIMEOUT 0x5c
#define UX_WAIT_FOREVER (~0UL)
#define UX_SLAVE_CLASS_CDC_ACM_IOCTL_SET_READ_TIMEOUT 8
#define UX_SLAVE_CLASS_CDC_ACM_IOCTL_SET_WRITE_TIMEOUT 9
#define TX_TIMER_TICKS_PER_SECOND 100
#define TX_PARAMETER_NOT_USED(x) ((void)(x))
#define TX_NO_TIME_SLICE 0
#define TX_AUTO_START 1
#define TX_SUCCESS 0
UINT ux_device_class_cdc_acm_ioctl(void *,UINT,VOID *);
UINT ux_device_class_cdc_acm_read(void *,UCHAR *,ULONG,ULONG *);
UINT ux_device_class_cdc_acm_write(void *,UCHAR *,ULONG,ULONG *);
void tx_thread_sleep(ULONG);
UINT tx_thread_create(TX_THREAD *,char *,void (*)(ULONG),ULONG,VOID *,ULONG,UINT,UINT,ULONG,UINT);
UINT tx_thread_terminate(TX_THREAD *);
UINT tx_thread_delete(TX_THREAD *);
uint32_t HAL_GetTick(void);
uint32_t HAL_GetUIDw0(void);
uint32_t HAL_GetUIDw1(void);
uint32_t HAL_GetUIDw2(void);
'''
MOCK = r'''
#include "app_usbx_device.h"
#include "drms_cdc.h"
#include "drms_control.h"
#include "drms_application.h"
#include "drms_file_service.h"
#include <string.h>
#include <stdio.h>
UX_SLAVE_CLASS_CDC_ACM cdc={1};
char incoming[64],written[1056];
unsigned int read_status,read_calls,writes,can_io=1,disconnect_during_read,indefinite_io,abort_calls,revocations,incoming_len,written_len,write_short;
uint32_t HAL_GetTick(void) { return 0; }
uint32_t HAL_GetUIDw0(void) { return 1; }
uint32_t HAL_GetUIDw1(void) { return 2; }
uint32_t HAL_GetUIDw2(void) { return 3; }
int drms_entropy_boot_id(void *ctx,uint64_t *out) { *out=0x123456789abcdef0ULL; return 1; }
static DRMS_Token test_token;
uint64_t observed_version;
uint32_t observed_operation;
uint32_t observed_file_id, disconnected_session;
uint32_t file_close_calls;
uint32_t file_view_enabled;
uint32_t file_list_view_enabled;
uint32_t file_read_ready,file_read_submits;
uint8_t observed_payload[1024];
uint32_t observed_length;
static DRMS_Result test_dispatch(const DRMS_Token *token, const DRMS_ControlRequest *request) {
 observed_version=request->expected_version;observed_file_id=request->value;observed_operation=request->operation;test_token=*token;
 if (request->operation == DRMS_OP_CONFIG_APPLY && request->payload_length <= sizeof(observed_payload)) {
   observed_length=request->payload_length; memcpy(observed_payload, request->payload, observed_length);
 }
 return DRMS_ACCEPTED;
}
void install_control(void) { drms_control_init(test_dispatch); }
void complete_operation(void) {
 DRMS_ControlRequest request={.source=DRMS_SOURCE_CDC,.request_id=123,.operation=DRMS_OP_MSC_EXPORT};
 drms_control_submit(&request);drms_control_poll(1);
 drms_control_complete(test_token,DRMS_OK,DRMS_RES_TF_ACCESS);
}
uint32_t control_queued(void) { DRMS_ControlSnapshot s; drms_control_get_snapshot(&s); return s.requests_queued; }
void process_one(void) { drms_control_poll(1); }
uint32_t drms_application_snapshot(DRMS_ApplicationSnapshot *out) {
 memset(out,0,sizeof(*out));out->revision=8;out->mono_us=123000;out->acquisition=3;
 out->rate=4000;out->fresh=1;out->classification=2;out->ohms_valid=1;out->ohms=10000;out->media_generation=9;
 return 1;
}
DRMS_Result drms_application_record_snapshot(uint64_t id, DRMS_ApplicationRecord *out) {
 if (id && id != 7) return DRMS_INVALID;
 *out=(DRMS_ApplicationRecord){.record=7,.phase=1,.result=DRMS_ACCEPTED,.capture_lost=2,.log_dropped=3};
 return DRMS_OK;
}
void drms_application_file_disconnect(uint32_t session) { disconnected_session=session; }
uint32_t drms_application_file_snapshot(DRMS_ApplicationFile *out) {
 if(!file_view_enabled) return 0;
 *out=(DRMS_ApplicationFile){.operation=1,.size=123,.session=1,.generation=9,.phase=1}; return 1;
}
uint32_t drms_application_file_list_snapshot(DRMS_ApplicationFileList *out) {
 if(!file_list_view_enabled) return 0;
 *out=(DRMS_ApplicationFileList){.operation=1,.session=1,.generation=9,.cursor=40,
   .file_id=42,.size=123,.next_cursor=43,.phase=2,.result=DRMS_OK};return 1;
}
DRMS_Result drms_application_file_close(uint32_t session, uint64_t op) {
 if (session!=1 || op!=55) return DRMS_STALE;
 ++file_close_calls; return DRMS_ACCEPTED;
}
DRMS_Result drms_file_service_submit(const DRMS_FileRequest *request, uint64_t *ticket) {
 if(request->kind!=DRMS_FILE_READ || request->session!=1 || request->generation!=9) return DRMS_INVALID;
 ++file_read_submits; *ticket=77; return DRMS_ACCEPTED;
}
DRMS_Result drms_file_service_take(uint64_t ticket, DRMS_FileReply *out) {
 if(ticket!=77) return DRMS_STALE;
 if(!file_read_ready) return DRMS_ACCEPTED;
 memset(out,0,sizeof(*out));out->ticket=77;out->result=DRMS_OK;out->offset=2;out->length=3;out->eof=0;
 memcpy(out->data,"abc",3); return DRMS_OK;
}
UINT ux_device_class_cdc_acm_ioctl(void *a,UINT b,VOID *c) { if(c==(void *)UX_WAIT_FOREVER) ++indefinite_io;if(b==4) ++abort_calls;return 0; }
UINT ux_device_class_cdc_acm_read(void *a,UCHAR *b,ULONG n,ULONG *actual) {
 ++read_calls; *actual=incoming_len;memcpy(b,incoming,*actual);incoming_len=0;
 if(disconnect_during_read) drms_cdc_deactivate();
 return read_status;
}
UINT ux_device_class_cdc_acm_write(void *a,UCHAR *b,ULONG n,ULONG *actual) {
 ++writes;memcpy(written,b,n);written[n]=0;written_len=n;*actual=write_short ? n-1 : n;return 0;
}
void tx_thread_sleep(ULONG a) {}
UINT tx_thread_create(TX_THREAD *a,char *b,void (*c)(ULONG),ULONG d,VOID *e,ULONG f,UINT g,UINT h,ULONG i,UINT j) { return 0; }
UINT tx_thread_terminate(TX_THREAD *a) { return 0; }
UINT tx_thread_delete(TX_THREAD *a) { return 0; }
unsigned int drms_usb_can_io(void) { return can_io; }
unsigned int drms_usb_state_change(unsigned long n) { if(!n) ++revocations;return 0; }
void change_parameters(void) { drms_cdc_parameter_change(&cdc); }
int drms_console_dispatch(const char *line) { (void)line; return 0; }
size_t drms_console_status(char *out,size_t size) { return snprintf(out,size,"OK status\r\n"); }
void activate(void) { drms_cdc_activate(&cdc); }
void set_dtr(UINT n) { cdc.ux_slave_class_cdc_acm_data_dtr_state=n; }
'''


class CDCConsoleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        p = Path(cls.tmp.name)
        (p / 'app_usbx_device.h').write_text(HEADER)
        (p / 'main.h').write_text('#include <stdint.h>\n#define __get_PRIMASK() 0U\n#define __disable_irq() ((void)0)\n#define __set_PRIMASK(x) ((void)(x))\nuint32_t HAL_GetTick(void);\nuint32_t HAL_GetUIDw0(void);\nuint32_t HAL_GetUIDw1(void);\nuint32_t HAL_GetUIDw2(void);\n')
        (p / 'mock.c').write_text(MOCK)
        src = ROOT / 'firmware/DE-DRMS-Code/Core'
        subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Werror=implicit-function-declaration',
                        '-I', str(p), '-I', str(src / 'Inc'),
                        str(src / 'Src/drms_cdc.c'), str(src / 'Src/drms_console.c'),
                        str(src.parent / 'App/interfaces/cdc/drms_cdc_v2.c'),
                        str(src.parent / 'App/interfaces/cdc/drms_cdc_frame.c'),
                        str(src / 'Src/drms_measurement.c'),
                        str(src / 'Src/drms_control.c'),
                        str(src / 'Src/drms_boot_identity.c'),
                        str(src / 'Src/drms_config_snapshot.c'),
                        str(p / 'mock.c'), '-o', str(p / 'cdc.so')], check=True)
        cls.lib = ctypes.CDLL(str(p / 'cdc.so'))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def value(self, name):
        return ctypes.c_uint.in_dll(self.lib, name)

    def send(self, data, drain=True):
        buf = (ctypes.c_char * 64).in_dll(self.lib, 'incoming')
        ctypes.memmove(buf, data, len(data))
        self.value('incoming_len').value = len(data)
        self.lib.drms_cdc_poll()
        if drain:
            self.lib.drms_cdc_tx_poll()

    def setUp(self):
        for name in ('read_status', 'read_calls', 'writes', 'disconnect_during_read', 'indefinite_io', 'abort_calls', 'revocations', 'write_short'):
            self.value(name).value = 0
        self.value('can_io').value = 1
        self.lib.set_dtr(1)
        self.lib.install_control()
        self.lib.drms_config_snapshot_init()
        self.lib.drms_cdc_start()
        self.lib.activate()

    def test_v2_hello_from_actual_cdc_stream(self):
        self.lib.drms_boot_identity_get.restype = ctypes.c_uint64
        self.assertEqual(self.lib.drms_boot_identity_get(), 0x123456789abcdef0)
        wire = bytes.fromhex('040201010101010102010101010101010101010105d7970e6600')
        self.send(wire[:8])
        self.assertEqual(self.value('writes').value, 0)
        self.send(wire[8:])
        self.assertEqual(self.value('writes').value, 1)
        size = self.value('written_len').value
        reply = bytes((ctypes.c_ubyte * 512).in_dll(self.lib, 'written')[:size])
        self.assertEqual(reply[-1], 0)
        # Decode standard COBS and inspect fixed response header and CRC.
        raw = bytearray(); i = 0
        while i < len(reply) - 1:
            code = reply[i]; i += 1
            raw += reply[i:i + code - 1]; i += code - 1
            if code != 255 and i < len(reply) - 1: raw.append(0)
        import struct, zlib
        self.assertEqual(struct.unpack_from('<BBHIQ', raw), (2, 2, 1, 1, 1))
        self.assertEqual(struct.unpack_from('<I', raw, len(raw) - 4)[0], zlib.crc32(raw[:-4]))

    def test_receiver_does_not_write_until_sender_runs_and_drops_stale_reply(self):
        self.send(b'PING\n', drain=False)
        self.assertEqual(self.value('writes').value, 0)
        self.assertEqual(self.value('read_calls').value, 1)
        self.send(b'PING\n', drain=False)
        self.assertEqual(self.value('read_calls').value, 2)
        self.lib.drms_cdc_tx_poll()
        self.assertEqual(self.value('writes').value, 1)
        self.lib.drms_cdc_deactivate()
        self.lib.activate()
        self.lib.drms_cdc_tx_poll()  # previous connection's second reply is stale
        self.assertEqual(self.value('writes').value, 1)

    def test_full_reply_queue_rejects_request_before_admission(self):
        import struct, zlib
        self.send(bytes.fromhex('040201010101010102010101010101010101010105d7970e6600'))
        for _ in range(4):
            self.send(b'PING\n', drain=False)
        raw = struct.pack('<BBHIQHH', 2, 1, 35, 1, 2, 0, 0)
        raw += struct.pack('<I', zlib.crc32(raw))
        wire = bytearray(b'\x00'); start = 0; code = 1
        for byte in raw:
            if not byte:
                wire[start] = code; start = len(wire); wire.append(0); code = 1
            else:
                wire.append(byte); code += 1
        wire[start] = code; wire.append(0)
        self.send(bytes(wire), drain=False)
        self.assertEqual(self.lib.control_queued(), 0)
        self.assertEqual(self.value('drms_cdc_tx_dropped').value, 1)
        self.lib.drms_cdc_tx_poll()
        self.send(bytes(wire), drain=False)
        self.assertEqual(self.lib.control_queued(), 1)

    def test_safe_stop_uses_reserved_reply_when_normal_queue_is_full(self):
        import struct, zlib
        self.send(bytes.fromhex('040201010101010102010101010101010101010105d7970e6600'))
        for _ in range(4): self.send(b'PING\n', drain=False)
        raw = struct.pack('<BBHIQHH', 2, 1, 18, 1, 2, 0, 0)
        raw += struct.pack('<I', zlib.crc32(raw))
        wire = bytearray(b'\x00'); start = 0; code = 1
        for byte in raw:
            if byte == 0:
                wire[start] = code; start = len(wire); wire.append(0); code = 1
            else:
                wire.append(byte); code += 1
        wire[start] = code; wire.append(0)
        self.send(bytes(wire), drain=False)
        self.assertEqual(self.lib.drms_control_safe_stop_take(), 1)
        self.lib.drms_cdc_tx_poll()
        size = self.value('written_len').value
        encoded = bytes((ctypes.c_ubyte * 512).in_dll(self.lib, 'written')[:size])
        decoded = bytearray(); i = 0
        while i < len(encoded)-1:
            code = encoded[i]; i += 1; decoded += encoded[i:i+code-1]; i += code-1
            if code != 255 and i < len(encoded)-1: decoded.append(0)
        self.assertEqual(struct.unpack_from('<H', decoded, 2)[0], 18)
        self.assertEqual(struct.unpack_from('<H', decoded, 24)[0], 1)  # ACCEPTED
        first = bytes(decoded)
        self.send(bytes(wire), drain=False)
        self.assertEqual(self.lib.drms_control_safe_stop_take(), 0)
        self.lib.drms_cdc_tx_poll()
        size = self.value('written_len').value
        encoded = bytes((ctypes.c_ubyte * 512).in_dll(self.lib, 'written')[:size])
        decoded = bytearray(); i = 0
        while i < len(encoded)-1:
            code = encoded[i]; i += 1; decoded += encoded[i:i+code-1]; i += code-1
            if code != 255 and i < len(encoded)-1: decoded.append(0)
        self.assertEqual(bytes(decoded), first)

    def test_v2_read_error_discards_until_next_delimiter(self):
        hello = bytes.fromhex('040201010101010102010101010101010101010105d7970e6600')
        self.send(hello[:6])
        self.value('read_status').value = 1
        self.send(b'')
        self.value('read_status').value = 0
        self.send(hello[6:])
        self.assertEqual(self.value('writes').value, 0)
        self.send(hello)
        self.assertEqual(self.value('writes').value, 1)

    def test_short_usb_write_is_counted(self):
        self.value('write_short').value = 1
        self.send(b'PING\n')
        self.assertEqual(self.value('drms_cdc_tx_errors').value, 1)

    def test_v2_session_survives_suspend_but_changes_after_disconnect(self):
        hello = bytes.fromhex('040201010101010102010101010101010101010105d7970e6600')
        def session_id():
            size = self.value('written_len').value
            encoded = bytes((ctypes.c_ubyte * 512).in_dll(self.lib, 'written')[:size])
            raw = bytearray(); i = 0
            while i < len(encoded) - 1:
                code = encoded[i]; i += 1
                raw += encoded[i:i + code - 1]; i += code - 1
                if code != 255 and i < len(encoded) - 1: raw.append(0)
            return int.from_bytes(raw[4:8], 'little')
        self.send(hello)
        self.assertEqual(session_id(), 1)
        self.value('can_io').value = 0
        self.lib.drms_cdc_poll()
        self.value('can_io').value = 1
        self.send(hello)
        self.assertEqual(session_id(), 1)
        self.lib.drms_cdc_deactivate()
        self.lib.activate()
        self.send(hello)
        self.assertEqual(session_id(), 2)

    def test_v2_unimplemented_command_gets_unsupported_reply(self):
        import struct, zlib
        self.send(bytes.fromhex('040201010101010102010101010101010101010105d7970e6600'))
        raw = struct.pack('<BBHIQHH', 2, 1, 102, 1, 2, 0, 0)
        raw += struct.pack('<I', zlib.crc32(raw))
        encoded = bytearray(b'\x00'); start = 0; code = 1
        for byte in raw:
            if byte == 0:
                encoded[start] = code; start = len(encoded); encoded.append(0); code = 1
            else:
                encoded.append(byte); code += 1
                if code == 255:
                    encoded[start] = code; start = len(encoded); encoded.append(0); code = 1
        encoded[start] = code; encoded.append(0)
        self.send(bytes(encoded))
        size = self.value('written_len').value
        wire = bytes((ctypes.c_ubyte * 512).in_dll(self.lib, 'written')[:size])
        decoded = bytearray(); i = 0
        while i < len(wire) - 1:
            code = wire[i]; i += 1
            decoded += wire[i:i + code - 1]; i += code - 1
            if code != 255 and i < len(wire) - 1: decoded.append(0)
        self.assertEqual(struct.unpack_from('<BBHIQ', decoded), (2, 2, 102, 1, 2))
        self.assertEqual(struct.unpack_from('<HHH', decoded, 20), (0x8001, 2, 11))

    def test_v2_get_operation_returns_retained_result(self):
        import struct
        self.lib.complete_operation()
        self.send(bytes.fromhex('040201010101010102010101010101010101010105d7970e6600'))
        self.send(bytes.fromhex('04020103020101010202010101010101020c0101040b800802010101010101010550a62bcd00'))
        size = self.value('written_len').value
        wire = bytes((ctypes.c_ubyte * 512).in_dll(self.lib, 'written')[:size])
        decoded = bytearray(); i = 0
        while i < len(wire) - 1:
            code = wire[i]; i += 1
            decoded += wire[i:i + code - 1]; i += code - 1
            if code != 255 and i < len(wire) - 1: decoded.append(0)
        self.assertEqual(struct.unpack_from('<BBHIQ', decoded), (2, 2, 3, 1, 2))
        fields = {}; pos = 20
        while pos < len(decoded) - 4:
            tag, size = struct.unpack_from('<HH', decoded, pos); pos += 4
            fields[tag & 0x7fff] = decoded[pos:pos+size]; pos += size
        self.assertEqual(int.from_bytes(fields[1], 'little'), 0)
        self.assertEqual(int.from_bytes(fields[11], 'little'), 1)
        self.assertEqual(fields[45], b'\x02')
        self.assertEqual(fields[44], b'\x02')

    def test_v2_status_contains_consistent_snapshot(self):
        import struct, zlib
        self.send(bytes.fromhex('040201010101010102010101010101010101010105d7970e6600'))
        raw = struct.pack('<BBHIQHH', 2, 1, 2, 1, 2, 0, 0)
        raw += struct.pack('<I', zlib.crc32(raw))
        wire = bytearray(b'\x00'); start = 0; code = 1
        for byte in raw:
            if byte == 0:
                wire[start] = code; start = len(wire); wire.append(0); code = 1
            else:
                wire.append(byte); code += 1
        wire[start] = code; wire.append(0)
        self.send(bytes(wire))
        size = self.value('written_len').value
        encoded = bytes((ctypes.c_ubyte * 512).in_dll(self.lib, 'written')[:size])
        decoded = bytearray(); i = 0
        while i < len(encoded)-1:
            code = encoded[i]; i += 1
            decoded += encoded[i:i+code-1]; i += code-1
            if code != 255 and i < len(encoded)-1: decoded.append(0)
        fields = {}; pos = 20
        while pos < len(decoded)-4:
            tag, size = struct.unpack_from('<HH', decoded, pos); pos += 4
            fields[tag & 0x7fff] = decoded[pos:pos+size]; pos += size
        self.assertEqual(int.from_bytes(fields[1], 'little'), 0)
        self.assertEqual(int.from_bytes(fields[9], 'little'), 8)
        self.assertEqual(fields[16], b'\x03')
        self.assertEqual(int.from_bytes(fields[30], 'little'), 4000)
        self.assertEqual(struct.unpack('<d', fields[23])[0], 10000.0)
        self.assertIn(85, fields)

    def test_v2_mutating_retries_do_not_enqueue_twice(self):
        import struct, zlib
        def frame(op, number, flags=0):
            raw = struct.pack('<BBHIQHH', 2, 1, op, 1, number, 0, flags)
            raw += struct.pack('<I', zlib.crc32(raw))
            encoded = bytearray(b'\x00'); start = 0; code = 1
            for byte in raw:
                if not byte:
                    encoded[start] = code; start = len(encoded); encoded.append(0); code = 1
                else:
                    encoded.append(byte); code += 1
            encoded[start] = code; encoded.append(0)
            return bytes(encoded)
        def fields():
            size = self.value('written_len').value
            wire = bytes((ctypes.c_ubyte * 512).in_dll(self.lib, 'written')[:size])
            raw = bytearray(); i = 0
            while i < len(wire)-1:
                code = wire[i]; i += 1; raw += wire[i:i+code-1]; i += code-1
                if code != 255 and i < len(wire)-1: raw.append(0)
            result = {}; pos = 20
            while pos < len(raw)-4:
                tag, length = struct.unpack_from('<HH', raw, pos); pos += 4
                result[tag & 0x7fff] = raw[pos:pos+length]; pos += length
            return result
        self.send(bytes.fromhex('040201010101010102010101010101010101010105d7970e6600'))
        request = frame(35, 2)
        self.send(request)
        first = fields()
        self.assertEqual(int.from_bytes(first[1], 'little'), 1)
        self.assertEqual(int.from_bytes(first[11], 'little'), 1)
        self.assertEqual(self.lib.control_queued(), 1)
        self.send(request)
        self.assertEqual(fields(), first)
        self.assertEqual(self.lib.control_queued(), 1)
        self.send(frame(35, 2, 1))
        self.assertEqual(int.from_bytes(fields()[1], 'little'), 3)
        self.assertEqual(self.lib.control_queued(), 1)
        for number in (3, 4, 5):
            self.send(frame(35, number))
            self.assertEqual(int.from_bytes(fields()[1], 'little'), 1)
        self.assertEqual(self.lib.control_queued(), 4)
        self.send(frame(35, 6))
        self.assertEqual(int.from_bytes(fields()[1], 'little'), 2)
        self.send(frame(35, 6))
        self.assertEqual(int.from_bytes(fields()[1], 'little'), 4)
        self.assertEqual(self.lib.control_queued(), 4)

    def test_v2_msc_export_and_release_are_admitted(self):
        import struct, zlib
        self.send(bytes.fromhex('040201010101010102010101010101010101010105d7970e6600'))
        for opcode, number in ((48, 2), (49, 3)):
            raw = struct.pack('<BBHIQHH', 2, 1, opcode, 1, number, 0, 0)
            raw += struct.pack('<I', zlib.crc32(raw))
            wire = bytearray(b'\x00'); start = 0; code = 1
            for byte in raw:
                if byte == 0:
                    wire[start] = code; start = len(wire); wire.append(0); code = 1
                else:
                    wire.append(byte); code += 1
            wire[start] = code; wire.append(0)
            self.send(bytes(wire))
            self.assertEqual(self.lib.control_queued(), number - 1)

    def test_v2_resume_admitted_while_control_is_stopped(self):
        import struct, zlib
        self.send(bytes.fromhex('040201010101010102010101010101010101010105d7970e6600'))
        self.lib.drms_control_stop()
        raw = struct.pack('<BBHIQHH', 2, 1, 19, 1, 2, 0, 0)
        raw += struct.pack('<I', zlib.crc32(raw))
        wire = bytearray(b'\x00'); start = 0; code = 1
        for byte in raw:
            if byte == 0:
                wire[start] = code; start = len(wire); wire.append(0); code = 1
            else:
                wire.append(byte); code += 1
        wire[start] = code; wire.append(0)
        self.send(bytes(wire))
        self.assertEqual(self.lib.control_queued(), 1)

    def test_v2_save_passes_full_expected_version_to_control(self):
        import struct, zlib
        self.send(bytes.fromhex('040201010101010102010101010101010101010105d7970e6600'))
        payload = struct.pack('<HHQ', 0x8030, 8, 0x100000001)
        raw = struct.pack('<BBHIQHH', 2, 1, 34, 1, 2, len(payload), 0) + payload
        raw += struct.pack('<I', zlib.crc32(raw))
        wire = bytearray(b'\x00'); start = 0; code = 1
        for byte in raw:
            if byte == 0:
                wire[start] = code; start = len(wire); wire.append(0); code = 1
            else:
                wire.append(byte); code += 1
        wire[start] = code; wire.append(0)
        self.send(bytes(wire))
        self.assertEqual(self.lib.control_queued(), 1)
        self.lib.process_one()
        self.assertEqual(ctypes.c_uint64.in_dll(self.lib, 'observed_version').value, 0x100000001)

    def test_v2_set_utc_passes_full_epoch_to_control(self):
        import struct, zlib
        self.send(bytes.fromhex('040201010101010102010101010101010101010105d7970e6600'))
        payload=struct.pack('<HHQ',0x8033,8,4102444799)
        raw=struct.pack('<BBHIQHH',2,1,37,1,2,len(payload),0)+payload
        raw+=struct.pack('<I',zlib.crc32(raw));wire=bytearray(b'\0');start=0;code=1
        for byte in raw:
            if byte==0:wire[start]=code;start=len(wire);wire.append(0);code=1
            else:wire.append(byte);code+=1
        wire[start]=code;wire.append(0);self.send(bytes(wire))
        self.assertEqual(self.lib.control_queued(),1)
        self.lib.process_one()
        self.assertEqual(ctypes.c_uint64.in_dll(self.lib,'observed_version').value,4102444799)

    def test_v2_calibration_command_is_admitted_once(self):
        import struct, zlib
        self.send(bytes.fromhex('040201010101010102010101010101010101010105d7970e6600'))
        raw = struct.pack('<BBHIQHH', 2, 1, 36, 1, 2, 0, 0)
        raw += struct.pack('<I', zlib.crc32(raw))
        wire = bytearray(b'\0'); start = 0; code = 1
        for byte in raw:
            if byte == 0:
                wire[start] = code; start = len(wire); wire.append(0); code = 1
            else:
                wire.append(byte); code += 1
        wire[start] = code; wire.append(0)
        self.send(bytes(wire)); self.send(bytes(wire))
        self.assertEqual(self.lib.control_queued(), 1)
        self.lib.process_one()
        self.assertEqual(ctypes.c_uint32.in_dll(self.lib, 'observed_operation').value, 6)

    def test_v2_begin_record_returns_stable_identifiers(self):
        import struct, zlib
        self.send(bytes.fromhex('040201010101010102010101010101010101010105d7970e6600'))
        payload = struct.pack('<HHI', 0x8032, 4, 200)
        raw = struct.pack('<BBHIQHH', 2, 1, 16, 1, 2, len(payload), 0) + payload
        raw += struct.pack('<I', zlib.crc32(raw))
        wire = bytearray(b'\0'); start = 0; code = 1
        for byte in raw:
            if byte == 0:
                wire[start] = code; start = len(wire); wire.append(0); code = 1
            else:
                wire.append(byte); code += 1
        wire[start] = code; wire.append(0)
        def exchange():
            self.send(bytes(wire)); n = self.value('written_len').value
            encoded = bytes((ctypes.c_ubyte * 1056).in_dll(self.lib, 'written')[:n])
            decoded = bytearray(); i = 0
            while i < len(encoded) - 1:
                count = encoded[i]; i += 1; decoded += encoded[i:i + count - 1]; i += count - 1
                if count != 255 and i < len(encoded) - 1: decoded.append(0)
            fields = {}; i = 20
            while i < len(decoded) - 4:
                tag, length = struct.unpack_from('<HH', decoded, i); i += 4
                fields[tag & 0x7fff] = decoded[i:i + length]; i += length
            return fields
        first = exchange()
        self.assertEqual(tuple(int.from_bytes(first[t], 'little') for t in (1, 11, 12)), (1, 1, 1))
        self.assertEqual(exchange(), first)
        self.assertEqual(self.lib.control_queued(), 1)

    def test_v2_get_record_reports_active_record_and_counters(self):
        import struct, zlib
        self.send(bytes.fromhex('040201010101010102010101010101010101010105d7970e6600'))
        payload = struct.pack('<HHQ', 0x800c, 8, 7)
        raw = struct.pack('<BBHIQHH', 2, 1, 4, 1, 2, len(payload), 0) + payload
        raw += struct.pack('<I', zlib.crc32(raw))
        wire = bytearray(b'\0'); start = 0; code = 1
        for byte in raw:
            if byte == 0:
                wire[start] = code; start = len(wire); wire.append(0); code = 1
            else:
                wire.append(byte); code += 1
        wire[start] = code; wire.append(0)
        self.send(bytes(wire))
        n = self.value('written_len').value
        encoded = bytes((ctypes.c_ubyte * 1056).in_dll(self.lib, 'written')[:n])
        decoded = bytearray(); i = 0
        while i < len(encoded)-1:
            count = encoded[i]; i += 1; decoded += encoded[i:i+count-1]; i += count-1
            if count != 255 and i < len(encoded)-1: decoded.append(0)
        fields = {}; i = 20
        while i < len(decoded)-4:
            tag, length = struct.unpack_from('<HH', decoded, i); i += 4
            fields[tag & 0x7fff] = decoded[i:i+length]; i += length
        self.assertEqual(int.from_bytes(fields[1], 'little'), 1)
        self.assertEqual(int.from_bytes(fields[12], 'little'), 7)
        self.assertEqual((fields[45][0], fields[41][0], fields[40][0]), (1, 0, 0))
        self.assertEqual((int.from_bytes(fields[38], 'little'), int.from_bytes(fields[39], 'little')), (2, 3))

    def test_v2_file_open_admission_is_idempotent_and_disconnect_revokes(self):
        import struct, zlib
        self.send(bytes.fromhex('040201010101010102010101010101010101010105d7970e6600'))
        payload = struct.pack('<HHIHHI', 0x8038, 4, 42, 0x8055, 4, 9)
        raw = struct.pack('<BBHIQHH', 2, 1, 50, 1, 2, len(payload), 0) + payload
        raw += struct.pack('<I', zlib.crc32(raw))
        wire = bytearray(b'\0'); start = 0; code = 1
        for byte in raw:
            if byte == 0:
                wire[start] = code; start = len(wire); wire.append(0); code = 1
            else:
                wire.append(byte); code += 1
        wire[start] = code; wire.append(0)
        self.send(bytes(wire)); self.send(bytes(wire))
        self.assertEqual(self.lib.control_queued(), 1)
        self.lib.process_one()
        self.assertEqual((ctypes.c_uint64.in_dll(self.lib,'observed_version').value,
                          self.value('observed_file_id').value), (9,42))
        self.value('file_view_enabled').value=1
        payload=struct.pack('<HHQ',0x800b,8,1)
        raw=struct.pack('<BBHIQHH',2,1,3,1,3,len(payload),0)+payload
        raw+=struct.pack('<I',zlib.crc32(raw))
        query=bytearray(b'\0');start=0;code=1
        for byte in raw:
            if byte==0:
                query[start]=code;start=len(query);query.append(0);code=1
            else: query.append(byte);code+=1
        query[start]=code;query.append(0)
        self.send(bytes(query))
        n=self.value('written_len').value
        encoded=bytes((ctypes.c_ubyte*1056).in_dll(self.lib,'written')[:n])
        decoded=bytearray();i=0
        while i<len(encoded)-1:
            count=encoded[i];i+=1;decoded+=encoded[i:i+count-1];i+=count-1
            if count!=255 and i<len(encoded)-1:decoded.append(0)
        self.assertIn(struct.pack('<HHQ',57,8,123),decoded)
        self.value('file_view_enabled').value=0
        self.lib.drms_cdc_deactivate()
        self.lib.drms_cdc_poll()  # worker observes the disconnect
        self.assertEqual(self.value('disconnected_session').value,1)

    def test_v2_file_close_retries_do_not_submit_twice(self):
        import struct, zlib
        self.value('file_close_calls').value=0
        self.send(bytes.fromhex('040201010101010102010101010101010101010105d7970e6600'))
        payload=struct.pack('<HHQ',0x800b,8,55)
        raw=struct.pack('<BBHIQHH',2,1,52,1,2,len(payload),0)+payload
        raw+=struct.pack('<I',zlib.crc32(raw))
        wire=bytearray(b'\0');start=0;code=1
        for byte in raw:
            if byte==0:
                wire[start]=code;start=len(wire);wire.append(0);code=1
            else: wire.append(byte);code+=1
        wire[start]=code;wire.append(0)
        self.send(bytes(wire)); self.send(bytes(wire))
        self.assertEqual(self.value('file_close_calls').value,1)

    def test_v2_file_read_is_nonblocking_and_retry_returns_data(self):
        import struct, zlib
        self.value('file_view_enabled').value=1
        self.value('file_read_ready').value=0; self.value('file_read_submits').value=0
        self.send(bytes.fromhex('040201010101010102010101010101010101010105d7970e6600'))
        payload=struct.pack('<HHQHHQHHH',0x800b,8,1,0x8034,8,2,0x8035,2,3)
        def send_read(number):
            raw=struct.pack('<BBHIQHH',2,1,51,1,number,len(payload),0)+payload
            raw+=struct.pack('<I',zlib.crc32(raw)); wire=bytearray(b'\0');start=0;code=1
            for byte in raw:
                if byte==0: wire[start]=code;start=len(wire);wire.append(0);code=1
                else: wire.append(byte);code+=1
            wire[start]=code;wire.append(0);self.send(bytes(wire))
            n=self.value('written_len').value
            encoded=bytes((ctypes.c_ubyte*1056).in_dll(self.lib,'written')[:n]); decoded=bytearray();i=0
            while i<len(encoded)-1:
                count=encoded[i];i+=1;decoded+=encoded[i:i+count-1];i+=count-1
                if count!=255 and i<len(encoded)-1:decoded.append(0)
            fields={};i=20
            while i<len(decoded)-4:
                tag,length=struct.unpack_from('<HH',decoded,i);i+=4
                fields[tag&0x7fff]=decoded[i:i+length];i+=length
            return fields
        self.assertEqual(int.from_bytes(send_read(2)[1],'little'),2)
        self.assertEqual(int.from_bytes(send_read(3)[1],'little'),2)
        self.assertEqual(self.value('file_read_submits').value,1)
        self.value('file_read_ready').value=1
        fields=send_read(4)
        self.assertEqual((int.from_bytes(fields[1],'little'),fields[54],fields[55][0]),(0,b'abc',0))
        self.value('file_view_enabled').value=0

    def test_v2_file_list_waits_for_worker_and_returns_media_generation(self):
        import struct, zlib
        self.value('file_list_view_enabled').value=0
        self.send(bytes.fromhex('040201010101010102010101010101010101010105d7970e6600'))
        payload=struct.pack('<HHI',0x803a,4,40)
        def query(number):
            raw=struct.pack('<BBHIQHH',2,1,53,1,number,len(payload),0)+payload
            raw+=struct.pack('<I',zlib.crc32(raw));wire=bytearray(b'\0');start=0;code=1
            for byte in raw:
                if byte==0:wire[start]=code;start=len(wire);wire.append(0);code=1
                else:wire.append(byte);code+=1
            wire[start]=code;wire.append(0);self.send(bytes(wire))
            n=self.value('written_len').value; encoded=bytes((ctypes.c_ubyte*1056).in_dll(self.lib,'written')[:n])
            decoded=bytearray();i=0
            while i<len(encoded)-1:
                count=encoded[i];i+=1;decoded+=encoded[i:i+count-1];i+=count-1
                if count!=255 and i<len(encoded)-1:decoded.append(0)
            fields={};i=20
            while i<len(decoded)-4:
                tag,length=struct.unpack_from('<HH',decoded,i);i+=4;fields[tag&0x7fff]=decoded[i:i+length];i+=length
            return fields
        self.assertEqual(int.from_bytes(query(2)[1],'little'),2)
        self.assertEqual(self.lib.control_queued(),1)
        self.lib.process_one()
        self.value('file_list_view_enabled').value=1
        fields=query(3)
        self.assertEqual(tuple(int.from_bytes(fields[x],'little') for x in (1,56,57,59,85)),(0,42,123,43,9))
        self.value('file_list_view_enabled').value=0

    def test_v2_apply_owns_nested_payload_through_disconnect(self):
        import struct, zlib
        from test_config_wire import settings
        self.send(bytes.fromhex('040201010101010102010101010101010101010105d7970e6600'))
        config = settings()
        payload = struct.pack('<HHQHH', 0x8030, 8, 0x100000001, 0x8031, len(config)) + config
        raw = struct.pack('<BBHIQHH', 2, 1, 33, 1, 2, len(payload), 0) + payload
        raw += struct.pack('<I', zlib.crc32(raw))
        wire = bytearray(b'\0'); start = 0; code = 1
        for byte in raw:
            if byte == 0:
                wire[start] = code; start = len(wire); wire.append(0); code = 1
            else:
                wire.append(byte); code += 1
                if code == 255:
                    wire[start] = code; start = len(wire); wire.append(0); code = 1
        wire[start] = code; wire.append(0)
        for i in range(0, len(wire), 64): self.send(bytes(wire[i:i+64]))
        self.assertEqual(self.lib.control_queued(), 1)
        self.lib.drms_cdc_deactivate()
        self.lib.process_one()
        self.assertEqual(ctypes.c_uint64.in_dll(self.lib, 'observed_version').value, 0x100000001)
        n = self.value('observed_length').value
        self.assertEqual(bytes((ctypes.c_ubyte * 1024).in_dll(self.lib, 'observed_payload')[:n]), config)

    def test_v2_get_config_returns_full_published_snapshot(self):
        import struct, zlib
        from test_config_wire import settings
        config = settings() + struct.pack('<HH', 900, 700) + b'x' * 700
        self.lib.drms_config_snapshot_publish.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint64, ctypes.c_uint64]
        source = ctypes.create_string_buffer(config)
        self.assertEqual(self.lib.drms_config_snapshot_publish(source, len(config), 12, 10), 1)
        self.send(bytes.fromhex('040201010101010102010101010101010101010105d7970e6600'))
        raw = struct.pack('<BBHIQHH', 2, 1, 32, 1, 2, 0, 0)
        raw += struct.pack('<I', zlib.crc32(raw))
        wire = bytearray(b'\0'); start = 0; code = 1
        for byte in raw:
            if byte == 0:
                wire[start] = code; start = len(wire); wire.append(0); code = 1
            else:
                wire.append(byte); code += 1
        wire[start] = code; wire.append(0)
        self.send(bytes(wire))
        n = self.value('written_len').value
        encoded = bytes((ctypes.c_ubyte * 1056).in_dll(self.lib, 'written')[:n])
        decoded = bytearray(); i = 0
        while i < len(encoded)-1:
            count = encoded[i]; i += 1
            decoded += encoded[i:i+count-1]; i += count-1
            if count != 255 and i < len(encoded)-1: decoded.append(0)
        fields = {}; i = 20
        while i < len(decoded)-4:
            tag, length = struct.unpack_from('<HH', decoded, i); i += 4
            fields[tag & 0x7fff] = decoded[i:i+length]; i += length
        self.assertEqual(int.from_bytes(fields[1], 'little'), 0)
        self.assertEqual(fields[49], config)
        self.assertEqual((int.from_bytes(fields[31], 'little'), int.from_bytes(fields[32], 'little')), (12, 10))

    def test_short_and_empty_packets_preserve_line(self):
        self.send(b'PI')
        self.send(b'')
        self.send(b'NG\n')
        self.assertEqual((ctypes.c_char * 512).in_dll(self.lib, 'written').value, b'OK PONG\r\n')

    def test_no_software_timeout_can_leave_an_old_pending_endpoint(self):
        self.assertEqual(self.value('indefinite_io').value, 2)

    def test_line_change_aborts_old_io_and_cannot_join_partial_commands(self):
        self.send(b'PI')
        self.lib.change_parameters()
        self.send(b'NG\n')
        self.assertEqual((ctypes.c_char * 512).in_dll(self.lib, 'written').value, b'ERR unsupported\r\n')
        self.assertEqual(self.value('abort_calls').value, 2)
        self.lib.drms_cdc_deactivate()
        self.assertEqual(self.value('revocations').value, 1)

    def test_disconnected_read_cannot_reply_to_later_session(self):
        self.value('disconnect_during_read').value = 1
        self.send(b'PING\n')
        self.assertEqual(self.value('writes').value, 0)

    def test_suspended_or_closed_terminal_does_not_start_read(self):
        self.value('can_io').value = 0
        self.send(b'PING\n')
        self.assertEqual(self.value('read_calls').value, 0)
        self.value('can_io').value = 1
        self.lib.set_dtr(0)
        self.send(b'PING\n')
        self.assertEqual(self.value('read_calls').value, 0)

    def test_reconnect_does_not_keep_partial_command(self):
        self.send(b'PI')
        self.lib.drms_cdc_deactivate()
        self.lib.activate()
        self.send(b'NG\n')
        self.assertEqual((ctypes.c_char * 512).in_dll(self.lib, 'written').value, b'ERR unsupported\r\n')


if __name__ == '__main__':
    unittest.main()
