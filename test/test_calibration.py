"""CRC/commit-protected calibration records, including every torn write boundary."""
import ctypes
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Calibration(ctypes.Structure):
    _fields_ = [('scale', ctypes.c_double), ('reference', ctypes.c_double),
                ('generation', ctypes.c_uint32), ('rate', ctypes.c_uint32),
                ('valid', ctypes.c_uint32)]


class CalibrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        src = ROOT / 'firmware/DE-DRMS-Code/Core'
        lib = Path(cls.tmp.name) / 'cal.so'
        subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Wextra', '-Werror',
                        '-I', str(src / 'Inc'), str(src / 'Src/drms_calibration_codec.c'),
                        str(src / 'Src/drms_measurement.c'), '-o', str(lib)], check=True)
        cls.lib = ctypes.CDLL(str(lib))
        cls.lib.drms_calibration_pack.argtypes = [ctypes.c_void_p, ctypes.POINTER(Calibration)]
        cls.lib.drms_calibration_unpack.argtypes = [ctypes.c_void_p, ctypes.POINTER(Calibration)]
        cls.lib.drms_calibration_newer.argtypes = [ctypes.c_uint32, ctypes.c_uint32]

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def pack(self, scale=150000.):
        record = ctypes.create_string_buffer(64)
        cal = Calibration(scale, 100000., 27, 4000, 1)
        self.lib.drms_calibration_pack(record, ctypes.byref(cal))
        return record.raw

    def test_valid_record_roundtrip(self):
        out = Calibration()
        self.assertEqual(self.lib.drms_calibration_unpack(self.pack(), ctypes.byref(out)), 1)
        self.assertEqual((out.scale, out.reference, out.generation, out.rate, out.valid),
                         (150000., 100000., 27, 4000, 1))

    def test_every_torn_prefix_is_rejected_until_commit_complete(self):
        record = self.pack()
        for boundary in range(64):
            with self.subTest(boundary=boundary):
                torn = record[:boundary] + b'\xff' * (64 - boundary)
                self.assertEqual(self.lib.drms_calibration_unpack(torn, ctypes.byref(Calibration())), 0)

    def test_bit_corruption_and_nonfinite_factor_rejected(self):
        record = bytearray(self.pack())
        record[20] ^= 4
        self.assertEqual(self.lib.drms_calibration_unpack(bytes(record), ctypes.byref(Calibration())), 0)
        self.assertEqual(self.lib.drms_calibration_unpack(self.pack(float('nan')), ctypes.byref(Calibration())), 0)

    def test_generation_wrap_selects_new_record(self):
        self.assertEqual(self.lib.drms_calibration_newer(0, 0xffffffff), 1)
        self.assertEqual(self.lib.drms_calibration_newer(0xffffffff, 0), 0)
        self.assertEqual(self.lib.drms_calibration_newer(1, 1), 0)


if __name__ == '__main__':
    unittest.main()
