"""Exercise the v2 stream framing against the published wire vectors."""
import ctypes
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import struct

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / 'firmware/DE-DRMS-Code'

class FieldRule(ctypes.Structure):
    _fields_ = [('id', ctypes.c_uint16), ('min_len', ctypes.c_uint16),
                ('max_len', ctypes.c_uint16), ('kind', ctypes.c_uint8),
                ('required', ctypes.c_uint8)]

class FieldView(ctypes.Structure):
    _fields_ = [('value', ctypes.POINTER(ctypes.c_uint8)), ('length', ctypes.c_uint16)]


class CDCFrameTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        out = Path(cls.tmp.name) / 'frame.so'
        subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Werror',
                        '-I', str(PROJECT / 'Core/Inc'),
                        str(PROJECT / 'App/interfaces/cdc/drms_cdc_frame.c'),
                        str(PROJECT / 'Core/Src/drms_measurement.c'),
                        '-o', str(out)], check=True)
        cls.lib = ctypes.CDLL(str(out))
        cls.lib.drms_cdc_frame_size.restype = ctypes.c_size_t
        cls.lib.drms_cdc_frame_init.argtypes = [ctypes.c_void_p]
        cls.lib.drms_cdc_frame_tick.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
        cls.callback = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t)
        cls.lib.drms_cdc_frame_feed.argtypes = [ctypes.c_void_p, ctypes.c_uint8, ctypes.c_uint32, cls.callback, ctypes.c_void_p]
        cls.lib.drms_cdc_frame_encode.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t,
                                                  ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t]
        cls.lib.drms_cdc_frame_encode.restype = ctypes.c_size_t
        cls.lib.drms_cdc_fields_validate.argtypes = [ctypes.c_void_p, ctypes.c_size_t,
            ctypes.POINTER(FieldRule), ctypes.c_size_t, ctypes.POINTER(FieldView)]
        cls.vectors = json.loads((ROOT / 'shared/protocol/de-drms-cdc-v2.json').read_text())['vectors']

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        self.ctx = ctypes.create_string_buffer(self.lib.drms_cdc_frame_size())
        self.lib.drms_cdc_frame_init(self.ctx)
        self.frames = []
        self.on_frame = self.callback(lambda _, data, length: self.frames.append(bytes(data[:length])))

    def feed(self, data, now=0):
        for byte in data:
            self.lib.drms_cdc_frame_feed(self.ctx, byte, now, self.on_frame, None)

    def test_published_vectors_round_trip(self):
        for vector in self.vectors.values():
            raw = bytes.fromhex(vector['decoded_hex'])
            wire = bytes.fromhex(vector['wire_hex'])
            self.feed(wire)
            self.assertEqual(self.frames.pop(), raw)
            result = (ctypes.c_uint8 * 1054)()
            data = (ctypes.c_uint8 * len(raw)).from_buffer_copy(raw)
            n = self.lib.drms_cdc_frame_encode(data, len(raw), result, len(result))
            self.assertEqual(bytes(result[:n]), wire)

    def test_bad_crc_overflow_and_timeout_resynchronize(self):
        wire = bytes.fromhex(self.vectors['hello']['wire_hex'])
        corrupt = bytearray(wire)
        corrupt[-2] ^= 1
        self.feed(corrupt + bytes([3]) * 1100 + b'\x00' + wire)
        self.assertEqual(len(self.frames), 1)
        self.frames.clear()
        self.feed(wire[:3], 100)
        self.feed(wire[3:] + wire, 1100)
        self.assertEqual(len(self.frames), 1)

    def test_timeout_can_be_driven_without_new_bytes(self):
        wire = bytes.fromhex(self.vectors['hello']['wire_hex'])
        self.feed(wire[:4], 0xfffffff0)
        self.lib.drms_cdc_frame_tick(self.ctx, (0xfffffff0 + 1000) & 0xffffffff)
        self.feed(wire[4:] + wire, (0xfffffff0 + 1000) & 0xffffffff)
        self.assertEqual(len(self.frames), 1)

    def test_split_and_concatenated_frames(self):
        wire = bytes.fromhex(self.vectors['hello']['wire_hex'])
        self.feed(wire[:7])
        self.assertFalse(self.frames)
        self.feed(wire[7:] + b'\x00' + wire)
        self.assertEqual(len(self.frames), 2)

    def test_tlv_schema_validates_required_duplicates_and_unknown(self):
        rules = (FieldRule * 2)(FieldRule(48, 8, 8, 0, 1), FieldRule(55, 1, 1, 1, 0))
        views = (FieldView * 2)()
        def check(payload):
            buf = ctypes.create_string_buffer(payload)
            return self.lib.drms_cdc_fields_validate(buf, len(payload), rules, 2, views)
        required = struct.pack('<HHQ', 0x8000 | 48, 8, 123)
        optional = struct.pack('<HHB', 55, 1, 1)
        self.assertEqual(check(required + optional), 0)
        self.assertEqual(views[0].length, 8)
        self.assertNotEqual(check(optional), 0)
        self.assertNotEqual(check(required + required), 0)
        self.assertNotEqual(check(required + struct.pack('<HHB', 55, 1, 2)), 0)
        self.assertNotEqual(check(required + struct.pack('<HH', 0x8000 | 900, 0)), 0)
        self.assertEqual(check(required + struct.pack('<HH', 900, 0)), 0)
        self.assertNotEqual(check(required + struct.pack('<HHB', 56, 1, 3)), 0)
        self.assertNotEqual(check(struct.pack('<HHQ', 48, 8, 123)), 0)
        self.assertNotEqual(check(required + b'\x01'), 0)

    def test_tlv_limits_and_float_validation(self):
        rules = (FieldRule * 1)(FieldRule(83, 8, 8, 2, 1))
        views = (FieldView * 1)()
        def check(payload):
            buf = ctypes.create_string_buffer(payload)
            return self.lib.drms_cdc_fields_validate(buf, len(payload), rules, 1, views)
        self.assertEqual(check(struct.pack('<HHd', 0x8000 | 83, 8, 0.01)), 0)
        self.assertNotEqual(check(struct.pack('<HHd', 0x8000 | 83, 8, float('nan'))), 0)
        self.assertNotEqual(check(struct.pack('<HHd', 0x8000 | 83, 8, float('inf'))), 0)
        self.assertNotEqual(check(struct.pack('<HHd', 0x8000 | 83, 8, 1.0) + struct.pack('<HH', 900, 0) * 64), 0)

    def test_known_field_registry_matches_machine_schema(self):
        schema = json.loads((ROOT / 'shared/protocol/de-drms-cdc-v2.json').read_text())
        known = {field['tag'] for field in schema['fields'].values()}
        for tag in range(1, 100):
            payload = struct.pack('<HH', tag, 0)
            buf = ctypes.create_string_buffer(payload)
            result = self.lib.drms_cdc_fields_validate(buf, len(payload), None, 0, None)
            self.assertEqual(result != 0, tag in known, tag)


if __name__ == '__main__':
    unittest.main()
