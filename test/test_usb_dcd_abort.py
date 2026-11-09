"""Actual ST DCD must not rearm an endpoint after its pending request was aborted."""
import ctypes
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HEADER = r'''
#ifndef DCD_TEST_H
#define DCD_TEST_H
typedef unsigned int UINT;
typedef unsigned long ULONG;
typedef void VOID;
typedef struct { int unused; } UX_DCD_STM32_ED;
typedef struct { void *pcd_handle; } UX_DCD_STM32;
typedef struct { struct { ULONG bmAttributes,bEndpointAddress; } ux_slave_endpoint_descriptor;void *ux_slave_endpoint_ed; } UX_SLAVE_ENDPOINT;
typedef struct {
 UX_SLAVE_ENDPOINT *ux_slave_transfer_request_endpoint;
 ULONG ux_slave_transfer_request_phase,ux_slave_transfer_request_requested_length;
 ULONG ux_slave_transfer_request_actual_length,ux_slave_transfer_request_completion_code;
 ULONG ux_slave_transfer_request_status,ux_slave_transfer_request_timeout;
 unsigned char *ux_slave_transfer_request_data_pointer;
 int ux_slave_transfer_request_semaphore;
} UX_SLAVE_TRANSFER;
#define UX_SUCCESS 0
#define UX_ABORTED 171
#define UX_MASK_ENDPOINT_TYPE 3
#define UX_ISOCHRONOUS_ENDPOINT 1
#define UX_ENDPOINT_DIRECTION 128
#define UX_TRANSFER_PHASE_DATA_OUT 1
#define UX_TRANSFER_STATUS_PENDING 1
#define UX_TRANSFER_STATUS_ABORT 2
#define UX_INTERRUPT_SAVE_AREA unsigned int saved_mask;
#define UX_DISABLE saved_mask=mask_interrupts();
#define UX_RESTORE restore_interrupts(saved_mask);
unsigned int mask_interrupts(void);
void restore_interrupts(unsigned int);
int HAL_PCD_EP_Transmit(void *,ULONG,unsigned char *,ULONG);
int HAL_PCD_EP_Receive(void *,ULONG,unsigned char *,ULONG);
UINT _ux_utility_semaphore_get(int *,ULONG);
#endif
'''
MOCK = r'''
#include "ux_api.h"
unsigned int arms,unmasked_arms,irq_masked,abort_after_arm,pending_abort;
static UX_SLAVE_TRANSFER *active;
unsigned int mask_interrupts(void) { unsigned int old=irq_masked;irq_masked=1;return old; }
void restore_interrupts(unsigned int old) {
 irq_masked=old;
 if(!old && pending_abort) {
  pending_abort=0;active->ux_slave_transfer_request_status=UX_TRANSFER_STATUS_ABORT;
  active->ux_slave_transfer_request_completion_code=UX_ABORTED;
  active->ux_slave_transfer_request_semaphore=1;
 }
}
static int arm(void) {
 ++arms;if(!irq_masked) ++unmasked_arms;
 if(abort_after_arm) { pending_abort=1;if(!irq_masked) restore_interrupts(0); }
 else { active->ux_slave_transfer_request_completion_code=0;active->ux_slave_transfer_request_semaphore=1; }
 return 0;
}
int HAL_PCD_EP_Transmit(void *h,ULONG ep,unsigned char *p,ULONG n) { return arm(); }
int HAL_PCD_EP_Receive(void *h,ULONG ep,unsigned char *p,ULONG n) { return arm(); }
UINT _ux_utility_semaphore_get(int *s,ULONG t) { if(*s) {--*s;return 0;} return 13; }
UINT _ux_dcd_stm32_transfer_request(UX_DCD_STM32 *,UX_SLAVE_TRANSFER *);
UINT run(int already_aborted,int transmit) {
 UX_DCD_STM32 dcd={0};UX_DCD_STM32_ED ed={0};
 UX_SLAVE_ENDPOINT ep={.ux_slave_endpoint_descriptor={2,transmit?0x81:1},.ux_slave_endpoint_ed=&ed};
 UX_SLAVE_TRANSFER transfer={.ux_slave_transfer_request_endpoint=&ep,
   .ux_slave_transfer_request_phase=transmit?1:2,.ux_slave_transfer_request_requested_length=64,
   .ux_slave_transfer_request_status=already_aborted?2:1,.ux_slave_transfer_request_timeout=~0UL,
   .ux_slave_transfer_request_semaphore=already_aborted?1:0,
   .ux_slave_transfer_request_completion_code=already_aborted?UX_ABORTED:0};
 active=&transfer;return _ux_dcd_stm32_transfer_request(&dcd,&transfer);
}
'''


class USBDCDAbortTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        p = Path(cls.tmp.name)
        (p / 'ux_api.h').write_text(HEADER)
        for name in ('ux_dcd_stm32.h', 'ux_utility.h', 'ux_device_stack.h'):
            (p / name).write_text('#include "ux_api.h"')
        (p / 'mock.c').write_text(MOCK)
        src = ROOT / 'firmware/DE-DRMS-Code/Middlewares/ST/usbx/common/usbx_stm32_device_controllers/ux_dcd_stm32_transfer_request.c'
        # Its sibling DCD header also gets replaced by this boundary mock.
        (p / 'transfer.c').write_text(src.read_text())
        subprocess.run(['cc', '-shared', '-fPIC', '-Werror=implicit-function-declaration',
                        '-I', str(p), str(p / 'transfer.c'), str(p / 'mock.c'),
                        '-o', str(p / 'dcd.so')], check=True)
        cls.lib = ctypes.CDLL(str(p / 'dcd.so'))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def value(self, name):
        return ctypes.c_uint.in_dll(self.lib, name)

    def setUp(self):
        for name in ('arms', 'unmasked_arms', 'irq_masked', 'abort_after_arm', 'pending_abort'):
            self.value(name).value = 0

    def test_aborted_request_is_never_rearmed(self):
        for direction in (0, 1):
            self.setUp()
            self.assertEqual(self.lib.run(1, direction), 171)
            self.assertEqual(self.value('arms').value, 0)

    def test_arm_is_atomic_with_usb_reset_irq(self):
        for direction in (0, 1):
            self.setUp()
            self.value('abort_after_arm').value = 1
            self.assertEqual(self.lib.run(0, direction), 171)
            self.assertEqual(self.value('arms').value, 1)
            self.assertEqual(self.value('unmasked_arms').value, 0)
            self.assertEqual(self.value('irq_masked').value, 0)


if __name__ == '__main__':
    unittest.main()
