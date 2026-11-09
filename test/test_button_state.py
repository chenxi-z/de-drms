"""Button debounce, hold, boot-held suppression and timer rollover."""
import ctypes
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'firmware/DE-DRMS-Code/App/interfaces/local_ui'


class Button(ctypes.Structure):
    _fields_ = [('raw_since', ctypes.c_uint32), ('press_since', ctypes.c_uint32),
                ('raw', ctypes.c_uint8), ('stable', ctypes.c_uint8),
                ('ignore', ctypes.c_uint8), ('long_fired', ctypes.c_uint8)]


class ButtonTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        path = Path(cls.tmp.name) / 'button.so'
        subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Werror',
                        str(SRC / 'drms_button.c'), '-o', str(path)], check=True)
        cls.lib = ctypes.CDLL(str(path))
        cls.lib.drms_button_init.argtypes = [ctypes.POINTER(Button), ctypes.c_uint32, ctypes.c_uint8]
        cls.lib.drms_button_step.argtypes = [ctypes.POINTER(Button), ctypes.c_uint32, ctypes.c_uint8]
        cls.lib.drms_button_step.restype = ctypes.c_uint8

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        self.button = Button()
        self.lib.drms_button_init(ctypes.byref(self.button), 0, 0)

    def step(self, time, pressed):
        return self.lib.drms_button_step(ctypes.byref(self.button), time & 0xffffffff, pressed)

    def test_bounce_then_short_only_after_stable_release(self):
        self.assertEqual(self.step(10, 1), 0)
        self.assertEqual(self.step(25, 0), 0)
        self.assertEqual(self.step(40, 1), 0)
        self.assertEqual(self.step(90, 1), 0)
        self.assertEqual(self.step(200, 0), 0)
        self.assertEqual(self.step(249, 0), 0)
        self.assertEqual(self.step(250, 0), 1)
        self.assertEqual(self.step(300, 0), 0)

    def test_long_does_not_produce_short_on_release(self):
        self.step(10, 1)
        self.step(60, 1)
        self.assertEqual(self.step(2010, 1), 2)
        self.assertEqual(self.step(2020, 0), 0)
        self.assertEqual(self.step(2070, 0), 0)

    def test_held_at_boot_requires_stable_release(self):
        self.lib.drms_button_init(ctypes.byref(self.button), 0, 1)
        self.assertEqual(self.step(2100, 1), 0)
        self.step(2200, 0)
        self.assertEqual(self.step(2250, 0), 0)
        self.step(2300, 1)
        self.step(2350, 1)
        self.step(2400, 0)
        self.assertEqual(self.step(2450, 0), 1)

    def test_release_at_long_threshold_without_intermediate_poll(self):
        self.step(10, 1)
        self.step(60, 1)
        self.assertEqual(self.step(2010, 0), 0)
        self.assertEqual(self.step(2060, 0), 2)
        self.assertEqual(self.step(2100, 0), 0)

    def test_long_threshold_and_wrap(self):
        self.lib.drms_button_init(ctypes.byref(self.button), 0xfffffff0, 0)
        self.step(0xfffffff5, 1)
        self.step(0xfffffff5 + 50, 1)
        self.assertEqual(self.step(0xfffffff5 + 2000, 1), 2)


if __name__ == '__main__':
    unittest.main()
