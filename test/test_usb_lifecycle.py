"""Compile the production USB lifecycle against HAL/USBX boundary doubles."""
import ctypes
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HEADER = r'''
#include <stdint.h>
#define __get_PRIMASK() 0U
#define __disable_irq() ((void)0)
#define __set_PRIMASK(x) ((void)(x))
typedef unsigned int UINT;
typedef unsigned long ULONG;
typedef struct { int unused; } PCD_HandleTypeDef;
#define UX_SUCCESS 0
#define UX_ERROR 1
#define UX_DEVICE_CONFIGURED 3
#define UX_DEVICE_RESET 0
#define UX_DEVICE_REMOVED 5
#define UX_DCD_STM32_DEVICE_SUSPENDED 244
#define UX_DCD_STM32_DEVICE_RESUMED 243
#define UX_DCD_STM32_DEVICE_DISCONNECTED 242
#define HAL_OK 0
#define GPIO_PIN_RESET 0
#define GPIO_PIN_SET 1
#define USB_VBUS_N_GPIO_Port 0
#define USB_VBUS_N_Pin 13
#define BQ_EN_GPIO_Port 0
#define BQ_EN_Pin 1
int HAL_GPIO_ReadPin(int, int);
void HAL_GPIO_WritePin(int, int, int);
int HAL_PCD_Start(PCD_HandleTypeDef *);
int HAL_PCD_Stop(PCD_HandleTypeDef *);
int HAL_PCDEx_SetRxFiFo(PCD_HandleTypeDef *, int);
int HAL_PCDEx_SetTxFiFo(PCD_HandleTypeDef *, int, int);
void HAL_PCD_DisconnectCallback(PCD_HandleTypeDef *);
UINT MX_USBX_Device_Stack_Init(void);
'''
MOCK = r'''
#include "app_usbx_device.h"
PCD_HandleTypeDef hpcd_USB_OTG_FS;
int vbus_absent=1, starts, stops, disconnects, charge500;
int stack_result, fifo_result, start_result, stop_result;
int fifo_words, msc_cancels;
void drms_msc_cancel(void) { ++msc_cancels; }
int HAL_GPIO_ReadPin(int p,int n) { return vbus_absent; }
void HAL_GPIO_WritePin(int p,int n,int value) { charge500=value; }
int HAL_PCD_Start(PCD_HandleTypeDef *p) { ++starts; return start_result; }
int HAL_PCD_Stop(PCD_HandleTypeDef *p) { ++stops; return stop_result; }
void HAL_PCD_DisconnectCallback(PCD_HandleTypeDef *p) { ++disconnects; }
int HAL_PCDEx_SetRxFiFo(PCD_HandleTypeDef *p,int words) { fifo_words+=words; return fifo_result; }
int HAL_PCDEx_SetTxFiFo(PCD_HandleTypeDef *p,int ep,int words) { fifo_words+=words; return fifo_result; }
UINT MX_USBX_Device_Stack_Init(void) { return stack_result; }
'''


class USBLifecycleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        p = Path(cls.tmp.name)
        (p / 'app_usbx_device.h').write_text(HEADER)
        (p / 'main.h').write_text('')
        (p / 'mock.c').write_text(MOCK)
        src = ROOT / 'firmware/DE-DRMS-Code/Core'
        subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Werror=implicit-function-declaration',
                        '-I', str(p), '-I', str(src / 'Inc'),
                        str(src / 'Src/drms_usb.c'), str(p / 'mock.c'),
                        '-o', str(p / 'usb.so')], check=True)
        cls.lib = ctypes.CDLL(str(p / 'usb.so'))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def value(self, name):
        return ctypes.c_int.in_dll(self.lib, name)

    def setUp(self):
        for name in ('starts', 'stops', 'disconnects', 'charge500', 'stack_result',
                     'fifo_result', 'start_result', 'stop_result', 'fifo_words', 'msc_cancels'):
            self.value(name).value = 0
        self.value('vbus_absent').value = 1
        self.assertEqual(self.lib.drms_usb_init(), 0)

    def test_no_vbus_never_attaches_and_fifos_fit_fs_ram(self):
        self.lib.drms_usb_poll()
        self.assertEqual(self.value('starts').value, 0)
        self.assertLessEqual(self.value('fifo_words').value, 320)
        self.assertEqual(self.value('fifo_words').value, 320)

    def test_attach_is_idempotent_and_detach_notifies_stack(self):
        self.value('vbus_absent').value = 0
        self.lib.drms_usb_poll()
        self.lib.drms_usb_poll()
        self.assertEqual(self.value('starts').value, 1)
        self.lib.drms_usb_state_change(3)
        self.assertEqual(self.value('charge500').value, 1)
        self.value('vbus_absent').value = 1
        self.lib.drms_usb_poll()
        self.assertEqual(self.value('stops').value, 1)
        self.assertEqual(self.value('disconnects').value, 1)
        self.assertEqual(self.value('charge500').value, 0)

    def test_suspend_and_unconfigure_revoke_current_immediately(self):
        self.value('vbus_absent').value = 0
        self.lib.drms_usb_poll()
        self.lib.drms_usb_state_change(3)
        self.lib.drms_usb_state_change(244)
        self.assertEqual(self.value('charge500').value, 0)
        self.lib.drms_usb_poll()
        self.assertEqual(self.value('charge500').value, 0)
        self.lib.drms_usb_state_change(243)
        self.assertEqual(self.value('charge500').value, 1)
        self.lib.drms_usb_state_change(0)
        self.assertEqual(self.value('charge500').value, 0)

    def test_reset_cancels_export_but_suspend_does_not(self):
        self.lib.drms_usb_state_change(3)
        self.lib.drms_usb_state_change(244)
        self.assertEqual(self.value('msc_cancels').value, 0)
        self.lib.drms_usb_state_change(0)
        self.assertEqual(self.value('msc_cancels').value, 1)

    def test_failed_start_retries_without_granting_current(self):
        self.value('vbus_absent').value = 0
        self.value('start_result').value = 1
        self.lib.drms_usb_poll()
        self.lib.drms_usb_state_change(3)
        self.assertEqual(self.value('charge500').value, 0)
        self.value('start_result').value = 0
        self.lib.drms_usb_poll()
        self.assertEqual(self.value('starts').value, 2)

    def test_failed_stack_or_fifo_prevents_start(self):
        for failure in ('stack_result', 'fifo_result'):
            with self.subTest(failure=failure):
                self.setUp()
                self.value(failure).value = 1
                self.assertNotEqual(self.lib.drms_usb_init(), 0)
                self.value('vbus_absent').value = 0
                self.lib.drms_usb_poll()
                self.assertEqual(self.value('starts').value, 0)

    def test_failed_stop_retries_with_low_current(self):
        self.value('vbus_absent').value = 0
        self.lib.drms_usb_poll()
        self.lib.drms_usb_state_change(3)
        self.value('vbus_absent').value = 1
        self.value('stop_result').value = 1
        self.lib.drms_usb_poll()
        self.assertEqual(self.value('charge500').value, 0)
        self.assertEqual(self.value('disconnects').value, 0)
        self.value('stop_result').value = 0
        self.lib.drms_usb_poll()
        self.assertEqual(self.value('disconnects').value, 1)


if __name__ == '__main__':
    unittest.main()
