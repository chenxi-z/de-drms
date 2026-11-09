"""CRC, ADS131A02 word format, nominal/reference ratios and rate validation."""
import binascii
import ctypes
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Sample(ctypes.Structure):
    _fields_ = [('voltage', ctypes.c_int32), ('sense', ctypes.c_int32),
                ('status', ctypes.c_uint16), ('flags', ctypes.c_uint16)]


class MeasurementTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        src = ROOT / 'firmware/DE-DRMS-Code/Core'
        lib = Path(cls.tmp.name) / 'measurement.so'
        subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Wextra', '-Werror',
                        '-I', str(src / 'Inc'), str(src / 'Src/drms_measurement.c'),
                        '-o', str(lib)], check=True)
        cls.lib = ctypes.CDLL(str(lib))
        cls.lib.drms_crc16.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
        cls.lib.drms_crc16.restype = ctypes.c_uint16
        cls.lib.drms_crc32.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
        cls.lib.drms_crc32.restype = ctypes.c_uint32
        cls.lib.drms_decode_frame.argtypes = [ctypes.c_void_p, ctypes.POINTER(Sample)]
        cls.lib.drms_resistance.argtypes = [ctypes.POINTER(Sample), ctypes.c_double,
                                            ctypes.POINTER(ctypes.c_double)]
        cls.lib.drms_reference_scale.argtypes = [ctypes.c_int64, ctypes.c_int64,
                                                 ctypes.c_double, ctypes.POINTER(ctypes.c_double)]

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def frame(self, voltage, sense, status=0x2200):
        payload = status.to_bytes(2, 'big') + b'\0'
        payload += (voltage & 0xffffff).to_bytes(3, 'big')
        payload += (sense & 0xffffff).to_bytes(3, 'big')
        return payload + binascii.crc_hqx(payload, 0xffff).to_bytes(2, 'big') + b'\0'

    def test_standard_crc_vectors(self):
        self.assertEqual(self.lib.drms_crc16(b'123456789', 9), 0x29b1)
        self.assertEqual(self.lib.drms_crc32(b'123456789', 9), 0xcbf43926)

    def test_positive_negative_and_sign_extension(self):
        for a, b in ((1234567, 4000000), (-1, -1234), (-8388608, 8388607)):
            with self.subTest(a=a, b=b):
                sample = Sample()
                self.lib.drms_decode_frame(self.frame(a, b), ctypes.byref(sample))
                self.assertEqual((sample.voltage, sample.sense), (a, b))

    def test_corruption_and_adc_fault_are_not_measurements(self):
        frame = bytearray(self.frame(1000000, 4000000))
        frame[4] ^= 1
        sample = Sample()
        self.assertEqual(self.lib.drms_decode_frame(bytes(frame), ctypes.byref(sample)), 0)
        self.assertTrue(sample.flags & 1)
        self.assertEqual(self.lib.drms_decode_frame(self.frame(1, 2, 0x2202), ctypes.byref(sample)), 0)
        self.assertTrue(sample.flags & 4)

    def test_reserved_status_bit_cannot_be_accepted_as_valid_format(self):
        sample = Sample()
        self.assertEqual(self.lib.drms_decode_frame(self.frame(280000, 4200000, 0x2280), ctypes.byref(sample)), 0)
        self.assertTrue(sample.flags & 2)

    def test_ground_referenced_input_comparator_warning_is_preserved(self):
        sample = Sample()
        self.assertEqual(self.lib.drms_decode_frame(self.frame(100000, 4000000, 0x2210), ctypes.byref(sample)), 1)
        self.assertEqual(sample.status, 0x2210)

    def test_ratio_and_reference_calibration_cancel_nominal_rsense(self):
        sample = Sample(200000, 3000000, 0x2200, 0)
        scale, ohms = ctypes.c_double(), ctypes.c_double()
        self.assertEqual(self.lib.drms_reference_scale(2000000, 3000000, 100000., ctypes.byref(scale)), 1)
        self.assertAlmostEqual(scale.value, 150000.)
        self.assertEqual(self.lib.drms_resistance(ctypes.byref(sample), scale.value, ctypes.byref(ohms)), 1)
        self.assertAlmostEqual(ohms.value, 10000.)

    def test_zero_denominator_saturation_and_nonfinite_scale_rejected(self):
        out = ctypes.c_double()
        for sample, scale in ((Sample(1, 0, 0x2200, 0), 150000.),
                              (Sample(8388607, 3000000, 0x2200, 0), 150000.),
                              (Sample(1, 3000000, 0x2200, 0), float('nan'))):
            self.assertEqual(self.lib.drms_resistance(ctypes.byref(sample), scale, ctypes.byref(out)), 0)
        self.assertEqual(self.lib.drms_reference_scale(0, 1, 100000., ctypes.byref(out)), 0)

    def test_excitation_guard_rejects_collapsed_current_and_compliance_stack(self):
        for a, b, expected in ((280000, 4200000, 1), (200000, 3000000, 0), (6000000, 4200000, 0)):
            self.assertEqual(self.lib.drms_excitation_ok(ctypes.byref(Sample(a, b, 0x2200, 0))), expected)

    def test_supported_rates_are_exact_clock_divisors(self):
        for rate, value in ((1000, 0x20), (4000, 0x22), (8000, 0x25),
                            (16000, 0x28), (32000, 0x2b), (64000, 0x2d), (128000, 0x2f)):
            out = ctypes.c_ubyte()
            self.assertEqual(self.lib.drms_rate_register(rate, ctypes.byref(out)), 1)
            self.assertEqual(out.value, value)
        self.assertEqual(self.lib.drms_rate_register(12345, ctypes.byref(ctypes.c_ubyte())), 0)


if __name__ == '__main__':
    unittest.main()
