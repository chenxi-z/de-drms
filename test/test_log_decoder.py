"""Decode fixtures produced by the C encoder, using the machine-readable spec."""
import binascii
import ctypes
import importlib.util
import io
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
from test_logging import Metadata
from test_acquisition import Raw

ROOT = Path(__file__).resolve().parents[1]
MODULE_SPEC = importlib.util.spec_from_file_location('de_drms_log', ROOT / 'tools/de_drms_log.py')
DECODER = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(DECODER)


class LogDecoderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        src = ROOT / 'firmware/DE-DRMS-Code/Core'
        lib = Path(cls.tmp.name) / 'codec.so'
        subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Wextra', '-Werror',
                        '-I', str(src / 'Inc'), str(src / 'Src/drms_log_codec.c'),
                        str(src / 'Src/drms_measurement.c'), '-o', str(lib)], check=True)
        cls.lib = ctypes.CDLL(str(lib))
        cls.lib.drms_log_pack_header.argtypes = [ctypes.c_void_p, ctypes.POINTER(Metadata)]
        cls.lib.drms_log_pack_record.argtypes = [ctypes.c_void_p, ctypes.POINTER(Raw)]

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def fixture(self, sequences=(10, 12), corrupt=False, footer=True, overruns=1, scale=150000.):
        metadata = Metadata(rate=4000, calibrated=1, scale=scale, reference=100000.)
        header = ctypes.create_string_buffer(64)
        self.lib.drms_log_pack_header(header, ctypes.byref(metadata))
        data = header.raw
        for index, sequence in enumerate(sequences):
            payload = b'\x22\x10\x00' + (280000).to_bytes(3, 'big') + (4200000).to_bytes(3, 'big')
            payload += binascii.crc_hqx(payload, 0xffff).to_bytes(2, 'big') + b'\x00'
            if corrupt and index == 0:
                payload = payload[:4] + bytes([payload[4] ^ 1]) + payload[5:]
            frame = Raw(sequence=sequence)
            frame.bytes[:] = payload
            record = ctypes.create_string_buffer(16)
            self.lib.drms_log_pack_record(record, ctypes.byref(frame))
            data += record.raw
        if footer:
            tail = ctypes.create_string_buffer(64)
            self.lib.drms_log_pack_footer(tail, len(sequences), 0, overruns, 0, 1000)
            data += tail.raw
        return data

    def test_c_encoder_matches_schema_and_ratio(self):
        reader = DECODER.LogReader(io.BytesIO(self.fixture()))
        rows = list(reader)
        self.assertTrue(reader.clean_end)
        self.assertEqual(reader.records, 2)
        self.assertEqual(reader.sequence_gaps, 1)
        self.assertEqual(rows[0]['ohms'], 10000.)
        self.assertEqual(rows[0]['status_hex'], '2210')
        self.assertEqual(rows[1]['elapsed_s'], 2 / 4000)

    def test_valid_crc_cannot_hide_an_impossible_calibration_factor(self):
        for scale in (float('nan'), 1e300, 0.):
            with self.subTest(scale=scale):
                with self.assertRaisesRegex(ValueError, 'scale_ohms'):
                    DECODER.LogReader(io.BytesIO(self.fixture(scale=scale)))

    def test_crc_failed_frame_cannot_produce_resistance(self):
        reader = DECODER.LogReader(io.BytesIO(self.fixture(corrupt=True)))
        rows = list(reader)
        self.assertEqual(reader.crc_errors, 1)
        self.assertIsNone(rows[0]['ohms'])
        self.assertEqual(rows[1]['ohms'], 10000.)

    def test_power_loss_recovers_complete_prefix_and_marks_unclean(self):
        reader = DECODER.LogReader(io.BytesIO(self.fixture(sequences=(1,), footer=False) + b'abc'))
        self.assertEqual(len(list(reader)), 1)
        self.assertFalse(reader.clean_end)
        self.assertEqual(reader.partial_bytes, 3)
        reader = DECODER.LogReader(io.BytesIO(self.fixture()[:-10]))
        self.assertEqual(len(list(reader)), 2)
        self.assertFalse(reader.clean_end)

    def test_counter_wrap_and_bad_header(self):
        reader = DECODER.LogReader(io.BytesIO(self.fixture(sequences=(0xffffffff, 0))))
        rows = list(reader)
        self.assertEqual(reader.sequence_gaps, 0)
        self.assertEqual(rows[1]['elapsed_s'], 1 / 4000)
        bad = bytearray(self.fixture())
        bad[12] ^= 1
        with self.assertRaisesRegex(ValueError, 'CRC32'):
            DECODER.LogReader(io.BytesIO(bad))

    def test_clean_file_end_is_not_a_lossless_capture_guarantee(self):
        reader = DECODER.LogReader(io.BytesIO(self.fixture()))
        list(reader)
        self.assertTrue(reader.clean_end)
        self.assertFalse(reader.summary()['no_reported_loss'])
        reader = DECODER.LogReader(io.BytesIO(self.fixture(sequences=(10,11), overruns=0)))
        list(reader)
        self.assertTrue(reader.summary()['no_reported_loss'])

    def test_cli_reports_loss_as_nonzero_unless_recovery_requested(self):
        p = Path(self.tmp.name) / 'lossy.BIN'
        p.write_bytes(self.fixture(sequences=(10,11), corrupt=True, overruns=0))
        command = ['python3', str(ROOT / 'tools/de_drms_log.py'), str(p)]
        result = subprocess.run(command, capture_output=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn(b'"no_reported_loss": false', result.stderr)
        result = subprocess.run(command + ['--allow-incomplete'], capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn(b'"no_reported_loss": false', result.stderr)

    def test_cli_refuses_to_overwrite_its_input(self):
        p = Path(self.tmp.name) / 'sample.BIN'
        data = self.fixture()
        p.write_bytes(data)
        result = subprocess.run(['python3', str(ROOT / 'tools/de_drms_log.py'), str(p), '--csv', str(p)], capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(p.read_bytes(), data)


if __name__ == '__main__':
    unittest.main()
