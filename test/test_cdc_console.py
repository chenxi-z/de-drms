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
UINT ux_device_class_cdc_acm_ioctl(void *,UINT,VOID *);
UINT ux_device_class_cdc_acm_read(void *,UCHAR *,ULONG,ULONG *);
UINT ux_device_class_cdc_acm_write(void *,UCHAR *,ULONG,ULONG *);
void tx_thread_sleep(ULONG);
UINT tx_thread_create(TX_THREAD *,char *,void (*)(ULONG),ULONG,VOID *,ULONG,UINT,UINT,ULONG,UINT);
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
#include <string.h>
#include <stdio.h>
UX_SLAVE_CLASS_CDC_ACM cdc={1};
char incoming[64],written[512];
unsigned int read_status,read_calls,writes,can_io=1,disconnect_during_read,indefinite_io,abort_calls,revocations,incoming_len,written_len;
uint32_t HAL_GetTick(void) { return 0; }
uint32_t HAL_GetUIDw0(void) { return 1; }
uint32_t HAL_GetUIDw1(void) { return 2; }
uint32_t HAL_GetUIDw2(void) { return 3; }
int drms_entropy_boot_id(void *ctx,uint64_t *out) { *out=0x123456789abcdef0ULL; return 1; }
static DRMS_Token test_token;
static DRMS_Result test_dispatch(const DRMS_Token *token, const DRMS_ControlRequest *request) {
 (void)request;test_token=*token;return DRMS_ACCEPTED;
}
void install_control(void) { drms_control_init(test_dispatch); }
void complete_operation(void) {
 DRMS_ControlRequest request={.source=DRMS_SOURCE_CDC,.request_id=123,.operation=DRMS_OP_MSC_EXPORT};
 drms_control_submit(&request);drms_control_poll(1);
 drms_control_complete(test_token,DRMS_OK,DRMS_RES_TF_ACCESS);
}
uint32_t drms_application_snapshot(DRMS_ApplicationSnapshot *out) {
 memset(out,0,sizeof(*out));out->revision=8;out->mono_us=123000;out->acquisition=3;
 out->rate=4000;out->fresh=1;out->classification=2;out->ohms_valid=1;out->ohms=10000;
 return 1;
}
UINT ux_device_class_cdc_acm_ioctl(void *a,UINT b,VOID *c) { if(c==(void *)UX_WAIT_FOREVER) ++indefinite_io;if(b==4) ++abort_calls;return 0; }
UINT ux_device_class_cdc_acm_read(void *a,UCHAR *b,ULONG n,ULONG *actual) {
 ++read_calls; *actual=incoming_len;memcpy(b,incoming,*actual);incoming_len=0;
 if(disconnect_during_read) drms_cdc_deactivate();
 return read_status;
}
UINT ux_device_class_cdc_acm_write(void *a,UCHAR *b,ULONG n,ULONG *actual) {
 ++writes;memcpy(written,b,n);written[n]=0;written_len=n;*actual=n;return 0;
}
void tx_thread_sleep(ULONG a) {}
UINT tx_thread_create(TX_THREAD *a,char *b,void (*c)(ULONG),ULONG d,VOID *e,ULONG f,UINT g,UINT h,ULONG i,UINT j) { return 0; }
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
                        str(p / 'mock.c'), '-o', str(p / 'cdc.so')], check=True)
        cls.lib = ctypes.CDLL(str(p / 'cdc.so'))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def value(self, name):
        return ctypes.c_uint.in_dll(self.lib, name)

    def send(self, data):
        buf = (ctypes.c_char * 64).in_dll(self.lib, 'incoming')
        ctypes.memmove(buf, data, len(data))
        self.value('incoming_len').value = len(data)
        self.lib.drms_cdc_poll()

    def setUp(self):
        for name in ('read_status', 'read_calls', 'writes', 'disconnect_during_read', 'indefinite_io', 'abort_calls', 'revocations'):
            self.value(name).value = 0
        self.value('can_io').value = 1
        self.lib.set_dtr(1)
        self.lib.install_control()
        self.lib.drms_cdc_start()
        self.lib.activate()

    def test_v2_hello_from_actual_cdc_stream(self):
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
