"""v2 记录格式编解码测试：C 编码器与 Python 解码器互验（C4/T2b）。

规格：docs/design/2026-11-06-record-v2-format.md（冻结）。
覆盖：黄金文件（独立手工编码）、字段交叉一致、逐字节截断、逐字节位翻转、
重复 END、END 后数据、超长块、v1 只读兼容、未知末边界保护。
"""
import ctypes
import binascii
import re
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
import zlib

from test_acquisition import Raw
from test_record_boundary import End, Token, Position
from test_user_config import build_body

ROOT = Path(__file__).resolve().parents[1]

HEADER = r'''
#ifndef MOCK_V2_H
#define MOCK_V2_H
#include <stdint.h>
#include <stddef.h>
#endif
'''


def crc32(b):
    return zlib.crc32(b) & 0xFFFFFFFF


def chunk(ctype, payload):
    """独立手工 chunk 编码（黄金文件用，不经 C）。"""
    return struct.pack('<HH', ctype, len(payload)) + payload


def hand_header(rate=4000, uid=(0x11223344, 0x55667788, 0x99AABBCC), record_id=7,
                anchor=(3, 4000, 100, 123456), config=b'', nominal=True):
    body = struct.pack('<HHIIIIIQIIQQH', 2, 16, 1 if nominal else 0, rate,
                       *uid, record_id, *anchor, len(config)) + config
    return chunk(1, body + struct.pack('<I', crc32(body)))


def hand_data(sequences):
    frames = b''.join(bytes(12) + struct.pack('<I', s) for s in sequences)
    return chunk(2, frames + struct.pack('<I', crc32(frames)))


def hand_valid_data(sequences):
    frame = bytearray(12)
    frame[0] = 0x22
    frame[3:6] = (280000).to_bytes(3, 'big')
    frame[6:9] = (4200000).to_bytes(3, 'big')
    frame[9:11] = binascii.crc_hqx(frame[:9], 0xffff).to_bytes(2, 'big')
    frames = b''.join(frame + struct.pack('<I', sequence) for sequence in sequences)
    return chunk(2, frames + struct.pack('<I', crc32(frames)))


def hand_end(gen=3, record_id=7, ring_end=3, lost=1, first=100, end_excl=103,
             last=102, end_known=True, capture=1, log_drop=0, quality=1,
             unknown=False, storage=False, reason=9):
    body = struct.pack('<IQQQQQQBQQQBBI', gen, record_id, ring_end, lost,
                       first, end_excl if end_known else 0, last,
                       1 if end_known else 0, capture, log_drop, quality,
                       1 if unknown else 0, 1 if storage else 0, reason)
    return chunk(3, body + struct.pack('<I', crc32(body)))


class V2CodecTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        p = Path(cls.tmp.name)
        (p / 'main.h').write_text(HEADER)
        src = ROOT / 'firmware/DE-DRMS-Code/Core'
        subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Werror=implicit-function-declaration',
                        '-I', str(p), '-I', str(src / 'Inc'),
                        *[str(src / f'Src/drms_{name}.c') for name in ('log_codec', 'measurement')],
                        '-o', str(p / 'codec.so')], check=True)
        cls.lib = ctypes.CDLL(str(p / 'codec.so'))
        cls.lib.drms_log_v2_pack_header.argtypes = [ctypes.c_char_p, ctypes.c_uint32, ctypes.c_void_p]
        cls.lib.drms_log_v2_pack_data.argtypes = [ctypes.c_char_p, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_uint32]
        cls.lib.drms_log_v2_pack_end.argtypes = [ctypes.c_char_p, ctypes.c_uint32, ctypes.c_void_p]
        sys_path_setup()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def c_end(self, **kw):
        """经 C 编码器构造 END chunk（默认与 hand_end 相同）。"""
        d = dict(gen=3, record_id=7, ring_end=3, lost=1, first=100, end_excl=103,
                 last=102, end_known=True, capture=1, log_drop=0, quality=1,
                 unknown=False, storage=False, reason=9)
        d.update(kw)
        gen_off = 0 if d['end_known'] else 1
        end = End()
        end.end_exclusive.generation = d['gen'] + gen_off
        end.record_id = d['record_id']
        end.ring_end = d['ring_end']
        end.lost_count = d['lost']
        end.first.index = d['first']
        end.end_known = d['end_known']
        end.end_exclusive.index = d['end_excl']
        end.last_confirmed.index = d['last']
        end.capture_lost = d['capture']
        end.log_dropped = d['log_drop']
        end.quality_bad = d['quality']
        end.unknown_loss = d['unknown']
        end.storage_error = d['storage']
        end.reason = d['reason']
        buf = ctypes.create_string_buffer(256)
        n = self.lib.drms_log_v2_pack_end(buf, 256, ctypes.byref(end))
        self.assertGreater(n, 0)
        return buf.raw[:n]

    def c_file(self):
        """C 编码完整最小文件（与 hand_* 相同内容）。"""
        meta = V2Meta()
        meta.flags = 1
        meta.rate_hz = 4000
        meta.uid_w0, meta.uid_w1, meta.uid_w2 = 0x11223344, 0x55667788, 0x99AABBCC
        meta.record_id = 7
        meta.anchor.acquisition_generation = 3
        meta.anchor.rate_hz = 4000
        meta.anchor.sample_seq0 = 100
        meta.anchor.mono_us0 = 123456
        hbuf = ctypes.create_string_buffer(8192)
        n = self.lib.drms_log_v2_pack_header(hbuf, 8192, ctypes.byref(meta))
        self.assertGreater(n, 0)
        frames = (Raw * 3)()
        for i, seq in enumerate((100, 101, 102)):
            frames[i].sequence = seq
        ubuf = ctypes.create_string_buffer(8192)
        nu = self.lib.drms_log_v2_pack_data(ubuf, 8192, frames, 3)
        self.assertGreater(nu, 0)
        return hbuf.raw[:n] + ubuf.raw[:nu] + self.c_end()

    def decode(self, data):
        from de_drms_log import LogReaderV2
        import io

        class Refused:
            complete = lambda self: False
            summary = lambda self: {'no_reported_loss': False, 'complete': False}
        try:
            return LogReaderV2(io.BytesIO(data))
        except ValueError:
            return Refused()  # 识别失败 = 非法文件，同样不报告成功

    def test_encoder_stack_fits_storage_thread(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'codec.o'
            source = ROOT / 'firmware/DE-DRMS-Code/Core'
            subprocess.run(['cc', '-O0', '-fstack-usage', '-I', str(source / 'Inc'),
                            '-c', str(source / 'Src/drms_log_codec.c'), '-o', str(output)], check=True)
            usage = output.with_suffix('.su').read_text()
            for name in ('drms_log_v2_pack_header', 'drms_log_v2_pack_data', 'drms_log_v2_pack_end'):
                match = re.search(r'\b' + name + r'\s+(\d+)\s+', usage)
                self.assertIsNotNone(match, name)
                self.assertLess(int(match.group(1)), 512, name)

    def test_maximum_data_block_and_insufficient_capacity(self):
        frames = (Raw * 256)()
        for i in range(256):
            frames[i].sequence = i
        output = ctypes.create_string_buffer(4104)
        self.assertEqual(self.lib.drms_log_v2_pack_data(output, 4103, frames, 256), 0)
        length = self.lib.drms_log_v2_pack_data(output, 4104, frames, 256)
        self.assertEqual(length, 4104)
        self.assertEqual(output.raw, hand_data(range(256)))

    def test_decoder_rejects_header_end_identity_mismatch(self):
        for end in (hand_end(record_id=8), hand_end(gen=4)):
            reader = self.decode(hand_header() + end)
            self.assertFalse(reader.complete())

    def test_cli_streams_v2_data_to_csv(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / 'record.bin'
            csv_path = Path(directory) / 'record.csv'
            log.write_bytes(self.c_file())
            result = subprocess.run(['python3', str(ROOT / 'tools/de_drms_log.py'), str(log),
                                     '--csv', str(csv_path), '--allow-incomplete'],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            rows = csv_path.read_text().splitlines()
            self.assertEqual(len(rows), 4)
            self.assertIn('sequence', rows[0])

    def test_golden_file_hand_encoded_matches_c_encoder(self):
        """黄金文件：独立手工编码与 C 编码器逐字节一致，且双端可解码。"""
        golden = hand_header() + hand_data((100, 101, 102)) + hand_end()
        self.assertEqual(self.c_file(), golden)
        reader = self.decode(golden)
        self.assertTrue(reader.complete())
        self.assertEqual(reader.header['rate'], 4000)
        self.assertEqual(reader.header['uid'], (0x11223344, 0x55667788, 0x99AABBCC))
        self.assertEqual(reader.header['anchor']['sample_seq0'], 100)
        self.assertEqual(reader.records, 3)
        self.assertEqual(reader.end['first_index'], 100)
        self.assertEqual(reader.end['end_exclusive_index'], 103)
        self.assertEqual(reader.end['capture_lost'], 1)
        self.assertEqual(reader.end['quality_bad'], 1)
        self.assertEqual(reader.end['reason'], 9)
        self.assertTrue(reader.summary()['no_reported_loss'] is False)  # INCOMPLETE

    def test_config_snapshot_round_trip(self):
        config = build_body(1)  # T5 schema1 编码
        meta = V2Meta()
        meta.flags = 1
        meta.rate_hz = 4000
        meta.record_id = 9
        meta.anchor.acquisition_generation = 1
        meta.anchor.rate_hz = 4000
        meta.anchor.sample_seq0 = 0
        meta.anchor.mono_us0 = 0
        meta.config = ctypes.cast(ctypes.create_string_buffer(config, len(config)), ctypes.c_void_p)
        meta.config_len = len(config)
        hbuf = ctypes.create_string_buffer(8192)
        n = self.lib.drms_log_v2_pack_header(hbuf, 8192, ctypes.byref(meta))
        self.assertGreater(n, 0)
        reader = self.decode(hbuf.raw[:n] + hand_valid_data((5,)) + hand_end(
            gen=1, record_id=9, ring_end=1, lost=0, first=0, end_excl=1, last=0,
            capture=0, quality=0, reason=0))
        self.assertTrue(reader.complete())
        self.assertEqual(reader.header['config'], config)
        self.assertEqual(reader.end['reason'], 0)
        self.assertTrue(reader.summary()['no_reported_loss'])

    def test_corrupt_adc_frame_is_not_reported_lossless(self):
        reader = self.decode(hand_header() + hand_data((100,)) + hand_end(
            first=100, end_excl=101, last=100, capture=0, quality=0,
            reason=0, ring_end=1))
        self.assertTrue(reader.complete())
        self.assertFalse(reader.summary()['no_reported_loss'])

    def test_empty_record_is_valid(self):
        reader = self.decode(hand_header() + hand_end(
            first=100, end_excl=100, last=0, end_known=True, capture=0,
            quality=0, reason=12, ring_end=0))
        self.assertTrue(reader.complete())
        self.assertEqual(reader.records, 0)
        self.assertEqual(reader.end['reason'], 12)
        self.assertTrue(reader.summary()['no_reported_loss'])

    def test_every_truncation_is_incomplete_or_invalid(self):
        golden = self.c_file()
        for cut in range(len(golden)):
            with self.subTest(cut=cut):
                reader = self.decode(golden[:cut])
                self.assertFalse(reader.complete(), cut)

    def test_every_bit_flip_is_caught(self):
        golden = self.c_file()
        for pos in range(len(golden)):
            for bit in (0, 3):
                with self.subTest(pos=pos, bit=bit):
                    damaged = bytearray(golden)
                    damaged[pos] ^= (1 << bit)
                    reader = self.decode(bytes(damaged))
                    self.assertFalse(reader.summary()['no_reported_loss'], (pos, bit))

    def test_duplicate_end_and_trailing_bytes_rejected(self):
        golden = self.c_file()
        with self.subTest('duplicate END'):
            reader = self.decode(golden + hand_end())
            self.assertFalse(reader.complete())
        with self.subTest('trailing bytes'):
            reader = self.decode(golden + b'\x00')
            self.assertFalse(reader.complete())
        with self.subTest('END before HEADER'):
            reader = self.decode(hand_end())
            self.assertFalse(reader.complete())
        with self.subTest('unknown chunk type'):
            body = struct.pack('<HH', 9, 4) + struct.pack('<I', crc32(b''))
            reader = self.decode(hand_header() + body + hand_end())
            self.assertFalse(reader.complete())
        with self.subTest('oversize chunk length'):
            head = struct.pack('<HH', 2, 0xFFFF)
            reader = self.decode(hand_header() + head + b'\x00' * 100)
            self.assertFalse(reader.complete())
        with self.subTest('DATA length not multiple of 16'):
            bad = chunk(2, b'\x00' * 5 + struct.pack('<I', crc32(b'\x00' * 5)))
            reader = self.decode(hand_header() + bad + hand_end())
            self.assertFalse(reader.complete())

    def test_unknown_end_keeps_begin_generation(self):
        end = End()
        end.record_id = 7
        end.first.generation = 3
        end.first.index = 100
        end.end_known = False
        end.unknown_loss = True
        end.reason = 9
        buf = ctypes.create_string_buffer(256)
        length = self.lib.drms_log_v2_pack_end(buf, 256, ctypes.byref(end))
        self.assertEqual(struct.unpack_from('<I', buf.raw, 4)[0], 3)
        reader = self.decode(hand_header() + buf.raw[:length])
        self.assertTrue(reader.complete())
        self.assertFalse(reader.summary()['no_reported_loss'])

    def test_unknown_end_boundary_cannot_carry_pseudo_exact_end(self):
        with self.subTest('C encoder refuses'):
            buf = ctypes.create_string_buffer(256)
            end = End()
            end.end_known = 0
            end.end_exclusive.index = 100
            self.assertEqual(self.lib.drms_log_v2_pack_end(buf, 256, ctypes.byref(end)), 0)
        with self.subTest('decoder refuses'):
            body = struct.pack('<IQQQQQQBQQQBBI', 3, 7, 0, 0, 100, 100, 0,
                               0, 0, 0, 0, 1, 0, 8)
            bad = chunk(3, body + struct.pack('<I', crc32(body)))
            reader = self.decode(hand_header() + bad)
            self.assertFalse(reader.complete())

    def test_v1_fixture_still_decodes_with_old_rules(self):
        # v1 文件（C v1 packer 生成）仍按旧规则解码，v2 读取器不误吞
        meta = V1Meta()
        meta.rate = 4000
        meta.scale = 150000.0
        meta.reference_ohms = 100000.0
        meta.serial = 1234
        hbuf = ctypes.create_string_buffer(64)
        self.lib.drms_log_pack_header(hbuf, ctypes.byref(meta))
        frame = Raw(sequence=5)
        rbuf = ctypes.create_string_buffer(16)
        self.lib.drms_log_pack_record(rbuf, ctypes.byref(frame))
        fbuf = ctypes.create_string_buffer(64)
        self.lib.drms_log_pack_footer(fbuf, 1, 0, 0, 0, 42)
        v1 = hbuf.raw + rbuf.raw + fbuf.raw
        from de_drms_log import LogReader
        import io
        reader = LogReader(io.BytesIO(v1))
        rows = list(reader)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['sequence'], 5)
        self.assertTrue(reader.summary()['clean_end'])


def sys_path_setup():
    import sys
    sys.path.insert(0, str(ROOT / 'tools'))


class V1Meta(ctypes.Structure):
    _fields_ = [('rate', ctypes.c_uint32), ('calibrated', ctypes.c_uint32),
                ('calibration_generation', ctypes.c_uint32), ('start_ticks', ctypes.c_uint32),
                ('serial', ctypes.c_uint32), ('scale', ctypes.c_double),
                ('reference_ohms', ctypes.c_double), ('year', ctypes.c_uint16),
                *[(name, ctypes.c_ubyte) for name in ('month', 'day', 'hour', 'minute', 'second', 'time_valid')]]


class TimeAnchor(ctypes.Structure):
    _fields_ = [('acquisition_generation', ctypes.c_uint32), ('rate_hz', ctypes.c_uint32),
                ('sample_seq0', ctypes.c_uint64), ('mono_us0', ctypes.c_uint64)]


class V2Meta(ctypes.Structure):
    _fields_ = [('flags', ctypes.c_uint32), ('rate_hz', ctypes.c_uint32),
                ('uid_w0', ctypes.c_uint32), ('uid_w1', ctypes.c_uint32),
                ('uid_w2', ctypes.c_uint32), ('record_id', ctypes.c_uint64),
                ('anchor', TimeAnchor), ('config', ctypes.c_void_p),
                ('config_len', ctypes.c_uint16)]



if __name__ == '__main__':
    unittest.main()
