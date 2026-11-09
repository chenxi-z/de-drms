"""Exercise the v2 stream framing against the published wire vectors."""
import ctypes
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / 'firmware/DE-DRMS-Code'


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


if __name__ == '__main__':
    unittest.main()
