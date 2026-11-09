"""CDC console keeps framing across short packets and disconnected sessions."""
import ctypes
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HEADER = r'''
#include <stddef.h>
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
'''
MOCK = r'''
#include "app_usbx_device.h"
#include "drms_cdc.h"
#include <string.h>
#include <stdio.h>
UX_SLAVE_CLASS_CDC_ACM cdc={1};
char incoming[64],written[512];
unsigned int read_status,read_calls,writes,can_io=1,disconnect_during_read,indefinite_io,abort_calls,revocations;
UINT ux_device_class_cdc_acm_ioctl(void *a,UINT b,VOID *c) { if(c==(void *)UX_WAIT_FOREVER) ++indefinite_io;if(b==4) ++abort_calls;return 0; }
UINT ux_device_class_cdc_acm_read(void *a,UCHAR *b,ULONG n,ULONG *actual) {
 ++read_calls; *actual=strlen(incoming);memcpy(b,incoming,*actual);incoming[0]=0;
 if(disconnect_during_read) drms_cdc_deactivate();
 return read_status;
}
UINT ux_device_class_cdc_acm_write(void *a,UCHAR *b,ULONG n,ULONG *actual) {
 ++writes;memcpy(written,b,n);written[n]=0;*actual=n;return 0;
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
        (p / 'mock.c').write_text(MOCK)
        src = ROOT / 'firmware/DE-DRMS-Code/Core'
        subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Werror=implicit-function-declaration',
                        '-I', str(p), '-I', str(src / 'Inc'),
                        str(src / 'Src/drms_cdc.c'), str(src / 'Src/drms_console.c'),
                        str(p / 'mock.c'), '-o', str(p / 'cdc.so')], check=True)
        cls.lib = ctypes.CDLL(str(p / 'cdc.so'))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def value(self, name):
        return ctypes.c_uint.in_dll(self.lib, name)

    def send(self, data):
        buf = (ctypes.c_char * 64).in_dll(self.lib, 'incoming')
        buf.value = data
        self.lib.drms_cdc_poll()

    def setUp(self):
        for name in ('read_status', 'read_calls', 'writes', 'disconnect_during_read', 'indefinite_io', 'abort_calls', 'revocations'):
            self.value(name).value = 0
        self.value('can_io').value = 1
        self.lib.set_dtr(1)
        self.lib.activate()

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
