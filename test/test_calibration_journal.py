"""Power interruption at each quadword never destroys the previous calibration."""
import ctypes
from pathlib import Path
import subprocess
import tempfile
import unittest
from test_calibration import Calibration

ROOT = Path(__file__).resolve().parents[1]
MOCK = r'''
#include <stdint.h>
#include <string.h>
uint8_t flash[2][64];
int failure_at,programs,begin_result=1;
void reset_flash(void) { memset(flash,255,sizeof(flash));failure_at=programs=0;begin_result=1; }
int drms_cal_backend_read(unsigned int slot,uint8_t out[64]) { memcpy(out,flash[slot],64);return 1; }
int drms_cal_backend_begin(void) { return begin_result; }
int drms_cal_backend_erase(unsigned int slot) { memset(flash[slot],255,64);return 1; }
int drms_cal_backend_program(unsigned int slot,unsigned int offset,const uint8_t data[16]) {
 ++programs;
 if(programs==failure_at) { memcpy(flash[slot]+offset,data,7);return 0; }
 memcpy(flash[slot]+offset,data,16);return 1;
}
void drms_cal_backend_end(void) {}
'''


class CalibrationJournalTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        p = Path(cls.tmp.name)
        (p / 'mock.c').write_text(MOCK)
        src = ROOT / 'firmware/DE-DRMS-Code/Core'
        subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Wextra', '-Werror',
                        '-I', str(src / 'Inc'),
                        *[str(src / f'Src/drms_{name}.c') for name in
                          ('calibration_codec', 'calibration_journal', 'measurement')],
                        str(p / 'mock.c'), '-o', str(p / 'journal.so')], check=True)
        cls.lib = ctypes.CDLL(str(p / 'journal.so'))
        cls.lib.drms_calibration_load.argtypes = [ctypes.POINTER(Calibration)]
        cls.lib.drms_calibration_save.argtypes = [ctypes.POINTER(Calibration)]

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def value(self, name):
        return ctypes.c_int.in_dll(self.lib, name)

    def setUp(self):
        self.lib.reset_flash()
        self.cal = Calibration()
        self.lib.drms_calibration_load(ctypes.byref(self.cal))

    def test_blank_flash_uses_uncalibrated_nominal_factor(self):
        self.assertEqual((self.cal.scale, self.cal.reference, self.cal.valid), (150000., 100000., 0))

    def test_every_interrupted_save_keeps_old_record(self):
        for boundary in range(1, 5):
            with self.subTest(boundary=boundary):
                self.setUp()
                self.cal.valid = 1
                self.assertEqual(self.lib.drms_calibration_save(ctypes.byref(self.cal)), 1)
                self.value('programs').value = 0
                self.value('failure_at').value = boundary
                self.cal.scale = 151000.
                self.assertEqual(self.lib.drms_calibration_save(ctypes.byref(self.cal)), 0)
                self.lib.drms_calibration_load(ctypes.byref(self.cal))
                self.assertEqual((self.cal.scale, self.cal.generation), (150000., 1))

    def test_successful_save_loads_newest_slot(self):
        self.cal.valid = 1
        self.assertEqual(self.lib.drms_calibration_save(ctypes.byref(self.cal)), 1)
        self.cal.scale = 151000.
        self.assertEqual(self.lib.drms_calibration_save(ctypes.byref(self.cal)), 1)
        self.lib.drms_calibration_load(ctypes.byref(self.cal))
        self.assertEqual((self.cal.scale, self.cal.generation), (151000., 2))

    def test_busy_or_unsupported_backend_does_not_write(self):
        self.cal.valid = 1
        self.value('begin_result').value = 0
        self.assertEqual(self.lib.drms_calibration_save(ctypes.byref(self.cal)), 0)
        self.assertEqual(self.value('programs').value, 0)


if __name__ == '__main__':
    unittest.main()
