"""Long press, low battery and the flush/release barriers before soft shutdown."""
import ctypes
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HEADER = r'''
#include <stdint.h>
#define GPIO_PIN_RESET 0
#define PWR_BTN_GPIO_Port 0
#define PWR_BTN_Pin 5
#define USB_VBUS_N_GPIO_Port 0
#define USB_VBUS_N_Pin 13
#define BQ_PG_GPIO_Port 0
#define BQ_PG_Pin 6
int HAL_GPIO_ReadPin(int,int);
uint32_t HAL_GetTick(void);
'''
MOCK = r'''
#include "main.h"
uint32_t ticks,button_low,usb_low,pg_low,entries,stops;
volatile uint32_t drms_battery_mv=3700,drms_battery_valid=1;
int HAL_GPIO_ReadPin(int p,int n) { return !(n==5?button_low:n==13?usb_low:pg_low); }
uint32_t HAL_GetTick(void) { return ticks; }
int drms_console_dispatch(const char *line) { ++stops;return 1; }
int drms_power_backend_enter(void) { ++entries;return 0; }
'''


class PowerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        p = Path(cls.tmp.name)
        (p / 'main.h').write_text(HEADER)
        (p / 'mock.c').write_text(MOCK)
        src = ROOT / 'firmware/DE-DRMS-Code/Core'
        subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Werror=implicit-function-declaration',
                        '-I', str(p), '-I', str(src / 'Inc'), str(src / 'Src/drms_power.c'),
                        str(p / 'mock.c'), '-o', str(p / 'power.so')], check=True)
        cls.lib = ctypes.CDLL(str(p / 'power.so'))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def value(self, name):
        return ctypes.c_uint32.in_dll(self.lib, name)

    def setUp(self):
        for name in ('ticks', 'button_low', 'usb_low', 'pg_low', 'entries', 'stops'):
            self.value(name).value = 0
        self.value('drms_battery_mv').value = 3700
        self.value('drms_battery_valid').value = 1
        self.lib.drms_power_init()

    def advance(self, ms):
        self.value('ticks').value += ms
        self.lib.drms_power_poll()

    def test_long_press_waits_for_both_storage_and_button_release(self):
        self.value('button_low').value = 1
        self.lib.drms_power_poll()
        self.advance(2001)
        self.assertEqual(self.value('drms_shutdown_requested').value, 1)
        self.assertEqual(self.value('stops').value, 1)
        self.advance(100)
        self.assertEqual(self.value('entries').value, 0)
        self.value('drms_storage_shutdown_ready').value = 1
        self.advance(100)
        self.assertEqual(self.value('entries').value, 0)
        self.value('button_low').value = 0
        self.advance(1)
        self.advance(51)
        self.assertEqual(self.value('entries').value, 1)

    def test_usb_presence_cancels_pending_shutdown(self):
        self.value('button_low').value = 1
        self.lib.drms_power_poll()
        self.advance(2001)
        self.value('usb_low').value = 1
        self.advance(1)
        self.assertEqual(self.value('drms_shutdown_requested').value, 0)
        self.assertEqual(self.value('entries').value, 0)

    def test_low_battery_requires_five_valid_battery_only_readings(self):
        self.value('drms_battery_mv').value = 3450
        for _ in range(4):
            self.advance(1000)
        self.assertEqual(self.value('drms_shutdown_requested').value, 0)
        self.advance(1000)
        self.assertEqual(self.value('drms_shutdown_requested').value, 1)
        self.assertEqual(self.value('drms_power_low_battery').value, 1)

    def test_external_power_or_invalid_battery_cannot_trigger_low_battery_shutdown(self):
        self.value('drms_battery_mv').value = 3000
        self.value('pg_low').value = 1
        for _ in range(6):
            self.advance(1000)
        self.assertEqual(self.value('drms_shutdown_requested').value, 0)
        self.value('pg_low').value = 0
        self.value('drms_battery_valid').value = 0
        for _ in range(6):
            self.advance(1000)
        self.assertEqual(self.value('drms_shutdown_requested').value, 0)

    def test_waking_with_button_held_does_not_immediately_power_off_again(self):
        self.value('button_low').value = 1
        self.lib.drms_power_init()
        self.advance(3000)
        self.assertEqual(self.value('drms_shutdown_requested').value, 0)


if __name__ == '__main__':
    unittest.main()
