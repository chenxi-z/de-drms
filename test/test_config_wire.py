"""CDC settings conversion against the real configuration validator."""
import ctypes
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
from test_user_config import FakeFlash, BaselinePolicy

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / 'firmware/DE-DRMS-Code'

def tlv(tag, data):
    return struct.pack('<HH', tag | 0x8000, len(data)) + data

def settings(intervals=b'', names=None):
    values = [(72, struct.pack('<I', 4000)), (73, struct.pack('<I', 30000)),
              (74, struct.pack('<Q', 0)), (75, struct.pack('<Q', 0)),
              (76, struct.pack('<Q', 0)), (77, struct.pack('<Q', 32000)),
              (78, intervals), (79, '仪器'.encode()), (80, '试件'.encode()),
              (81, struct.pack('<I', 100)), (82, struct.pack('<Q', 50000)),
              (83, struct.pack('<d', 0.01))]
    result = b''.join(tlv(tag, value) for tag, value in values)
    if names is not None:
        result += struct.pack('<HH', 84, len(names)) + names
    return result

class ConfigWireTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        p = Path(cls.tmp.name)
        (p / 'main.h').write_text('#include <stdint.h>\n')
        (p / 'fake.c').write_text(FakeFlash.CODE)
        subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Werror',
            '-I', str(p), '-I', str(PROJECT / 'Core/Inc'),
            str(PROJECT / 'App/interfaces/cdc/drms_config_wire.c'),
            str(PROJECT / 'App/interfaces/cdc/drms_cdc_frame.c'),
            str(PROJECT / 'Core/Src/drms_user_config.c'),
            str(PROJECT / 'Core/Src/drms_measurement.c'), str(p / 'fake.c'),
            '-o', str(p / 'config.so')], check=True)
        cls.lib = ctypes.CDLL(str(p / 'config.so'))
        cls.lib.drms_config_wire_to_body.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t]
        cls.lib.drms_user_config_apply.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_uint64]
        cls.lib.drms_user_config_get_baseline_policy.argtypes = [ctypes.POINTER(BaselinePolicy)]
        cls.lib.drms_user_config_get_wire.argtypes = [ctypes.c_void_p, ctypes.c_uint32]

    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()

    def setUp(self):
        self.lib.fake_reset()
        self.lib.drms_user_config_init()

    def convert(self, payload):
        src = ctypes.create_string_buffer(payload)
        out = ctypes.create_string_buffer(4096)
        length = self.lib.drms_config_wire_to_body(src, len(payload), out, len(out))
        return out, length

    def test_full_settings_convert_and_round_trip_without_losing_extensions(self):
        interval = struct.pack('<dddHBBBB', 0.5, 1.5, 0.1, 7, 2, 1, 2, 0)
        names = struct.pack('<HB', 7, 6) + '试件'.encode()
        original = settings(interval, names)
        output, length = self.convert(original)
        self.assertGreater(length, 0)
        self.assertEqual(self.lib.drms_user_config_apply(output, length, 0), 0)
        policy = BaselinePolicy()
        self.assertEqual(self.lib.drms_user_config_get_baseline_policy(ctypes.byref(policy)), 1)
        self.assertEqual((policy.min_count, policy.min_duration_us), (100, 50000))
        exported = ctypes.create_string_buffer(4096)
        n = self.lib.drms_user_config_export(exported, len(exported))
        self.assertIn(original, exported.raw[:n])
        saved_wire = ctypes.create_string_buffer(1024)
        n = self.lib.drms_user_config_get_wire(saved_wire, len(saved_wire))
        self.assertEqual(saved_wire.raw[:n], original)
        self.assertEqual(self.lib.drms_user_config_get_wire(saved_wire, n-1), 0)
        self.assertEqual(self.lib.drms_user_config_save(1), 0)
        self.lib.drms_user_config_init()
        self.lib.drms_user_config_load()
        n = self.lib.drms_user_config_get_wire(saved_wire, len(saved_wire))
        self.assertEqual(saved_wire.raw[:n], original)

    def test_missing_required_and_invalid_names_rejected(self):
        self.assertEqual(self.convert(settings()[:-12])[1], 0)
        interval = struct.pack('<dddHBBBB', 0.5, 1.5, 0.1, 7, 2, 1, 0, 0)
        self.assertEqual(self.convert(settings(interval, struct.pack('<HB', 8, 1) + b'x'))[1], 0)
        self.assertEqual(self.convert(settings(interval, struct.pack('<HB', 7, 2) + b'\xc0\x80'))[1], 0)

    def test_invalid_interval_and_monitor_values_rejected(self):
        def interval(lo, hi, h, ident, level=1, closed=0, direction=0, reserved=0):
            return struct.pack('<dddHBBBB', lo, hi, h, ident, level, closed, direction, reserved)
        for data in (interval(1, 1, 0, 1), interval(0, 1, .5, 1),
                     interval(0, 1, .1, 1, direction=3),
                     interval(0, 1, .1, 1, reserved=1),
                     interval(0, 1, .1, 1) + interval(.5, 2, .1, 2),
                     interval(0, 1, .1, 1) + interval(1, 2, .1, 1)):
            with self.subTest(data=data):
                self.assertEqual(self.convert(settings(data))[1], 0)
        self.assertEqual(self.convert(settings().replace(tlv(72, struct.pack('<I', 4000)),
                                                        tlv(72, struct.pack('<I', 1))))[1], 0)
        self.assertEqual(self.convert(settings().replace(tlv(77, struct.pack('<Q', 32000)),
                                                        tlv(77, struct.pack('<Q', 1))))[1], 0)

    def test_optional_future_field_is_preserved_and_critical_field_rejected(self):
        future = struct.pack('<HH', 900, 3) + b'xyz'
        original = settings() + future
        output, length = self.convert(original)
        self.assertGreater(length, 0)
        self.assertEqual(self.lib.drms_user_config_apply(output, length, 0), 0)
        exported = ctypes.create_string_buffer(4096)
        n = self.lib.drms_user_config_export(exported, len(exported))
        self.assertIn(original, exported.raw[:n])
        self.assertEqual(self.convert(settings() + tlv(900, b'xyz'))[1], 0)

    def test_duplicate_fields_and_bad_text_rejected(self):
        self.assertEqual(self.convert(settings() + tlv(72, struct.pack('<I', 4000)))[1], 0)
        self.assertEqual(self.convert(settings().replace('仪器'.encode(), b'\x00' * 6))[1], 0)
        entry = struct.pack('<dddHBBBB', .5, 1.5, .1, 7, 2, 1, 0, 0)
        name = struct.pack('<HB', 7, 1) + b'a'
        self.assertEqual(self.convert(settings(entry, name + name))[1], 0)

    def test_short_output_does_not_write_past_capacity(self):
        data = settings()
        source = ctypes.create_string_buffer(data)
        output = ctypes.create_string_buffer(b'Z' * 64, 64)
        self.assertEqual(self.lib.drms_config_wire_to_body(source, len(data), output, 48), 0)
        self.assertEqual(output.raw, b'Z' * 64)
