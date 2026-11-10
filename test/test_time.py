import ctypes
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Time(ctypes.Structure):
    _fields_ = [('year', ctypes.c_uint16), ('month', ctypes.c_ubyte), ('day', ctypes.c_ubyte),
                ('hour', ctypes.c_ubyte), ('minute', ctypes.c_ubyte), ('second', ctypes.c_ubyte),
                ('weekday', ctypes.c_ubyte), ('valid', ctypes.c_ubyte)]


class TimeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        src = ROOT / 'firmware/DE-DRMS-Code/Core'
        lib = Path(cls.tmp.name) / 'time.so'
        subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Wextra', '-Werror',
                        '-I', str(src / 'Inc'), str(src / 'Src/drms_time_codec.c'), '-o', str(lib)], check=True)
        cls.lib = ctypes.CDLL(str(lib))
        cls.lib.drms_time_parse.argtypes = [ctypes.c_char_p, ctypes.POINTER(Time)]
        cls.lib.drms_time_epoch_to_iso.argtypes = [ctypes.c_uint64, ctypes.c_void_p]

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_calendar_and_weekday(self):
        out = Time()
        self.assertEqual(self.lib.drms_time_parse(b'2026-11-04T13:14:15', ctypes.byref(out)), 1)
        self.assertEqual((out.year, out.month, out.day, out.weekday), (2026, 11, 4, 3))
        self.assertEqual(self.lib.drms_time_parse(b'2000-02-29T00:00:00', ctypes.byref(out)), 1)
        self.assertEqual(out.weekday, 2)

    def test_invalid_and_trailing_text_rejected(self):
        for value in (b'2025-02-29T00:00:00', b'2026-04-31T00:00:00', b'2100-01-01T00:00:00',
                      b'2026-11-04T24:00:00', b'2026-11-04T00:60:00', b'2026-11-04T00:00:60',
                      b'2026-11-04T00:00:00Z', b'2026/11/04T00:00:00', b'2026-00-01T00:00:00'):
            with self.subTest(value=value):
                self.assertEqual(self.lib.drms_time_parse(value, ctypes.byref(Time())), 0)

    def test_epoch_conversion_bounds_and_leap_days(self):
        import calendar, datetime
        for stamp in (946684800, 951782400, 1793798055, 4102444799):
            out=ctypes.create_string_buffer(20)
            self.assertEqual(self.lib.drms_time_epoch_to_iso(stamp,out),1)
            expected=datetime.datetime.fromtimestamp(stamp,datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S').encode()
            self.assertEqual(out.value,expected)
        for stamp in (0,946684799,4102444800,2**64-1):
            self.assertEqual(self.lib.drms_time_epoch_to_iso(stamp,ctypes.create_string_buffer(20)),0)


if __name__ == '__main__':
    unittest.main()
