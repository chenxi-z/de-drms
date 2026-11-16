"""RAW 实时流攒批状态机测试：编译真实 drms_raw_stream.c，验证批格式、换代冲刷与丢失记账。

契约：shared/protocol/de-drms-cdc-v2.json 的 RAW_EVENT（opcode 131）——
"RAW data 为同一代次连续的 16 字节记录；缺口或换代另起帧"，
"lost 为本次订阅累计未交付条目数（曲线点或原始帧）"。
线程角色：feed=应用处理线程，publish=CDC 发送线程，subscribe/unsubscribe=CDC 接收线程。
"""
import ctypes
from pathlib import Path
import subprocess
import tempfile
import unittest

from _platform import CC, EXT
ROOT = Path(__file__).resolve().parents[1]

BATCH = 60
SLOT = 1040


class RawStreamTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import tempfile
        cls.tmp_dir = tempfile.mkdtemp(prefix='drms_raw_')
        p = Path(cls.tmp_dir)
        shim = p / 'shim'
        shim.mkdir()
        (shim / 'main.h').write_text(
            '#include <stdint.h>\n'
            '#define __get_PRIMASK() 0u\n'
            '#define __disable_irq() ((void)0)\n'
            '#define __set_PRIMASK(x) ((void)(x))\n')
        core = ROOT / 'firmware/DE-DRMS-Code/Core'
        cdc = ROOT / 'firmware/DE-DRMS-Code/App/interfaces/cdc'
        subprocess.run([CC, '-shared', '-fPIC', '-Wall', '-Werror=implicit-function-declaration',
                        '-I', str(shim), '-I', str(core / 'Inc'), '-I', str(cdc),
                        str(core / 'Src/drms_raw_stream.c'),
                        str(core / 'Src/drms_measurement.c'),
                        str(cdc / 'drms_cdc_frame.c'),
                        '-o', str(p / f'raw{EXT}')], check=True)
        (p / 'selfcheck.c').write_text('#include "drms_raw_stream.h"\nint probe;\n')
        subprocess.run([CC, '-fsyntax-only', '-Wall', '-Werror',
                        '-I', str(core / 'Inc'), str(p / 'selfcheck.c')], check=True)
        cls.lib = ctypes.CDLL(str(p / f'raw{EXT}'))
        cls.lib.drms_raw_stream_subscribe.argtypes = [ctypes.c_uint32]
        cls.lib.drms_raw_stream_subscribe.restype = ctypes.c_uint32
        cls.lib.drms_raw_stream_feed.argtypes = [ctypes.c_uint32, ctypes.c_uint32,
                                                 ctypes.c_uint32, ctypes.c_char_p]
        cls.lib.drms_raw_stream_publish.argtypes = [ctypes.c_uint32, ctypes.c_void_p,
                                                    ctypes.c_void_p, ctypes.c_void_p,
                                                    ctypes.c_void_p]
        cls.lib.drms_raw_stream_publish.restype = ctypes.c_uint
        cls.lib.drms_raw_stream_lost.restype = ctypes.c_uint64
        cls.lib.drms_raw_stream_active.restype = ctypes.c_uint32
        cls.lib.drms_raw_stream_period_ms.restype = ctypes.c_uint32

    @classmethod
    def tearDownClass(cls):
        # Windows 下加载过的 DLL 句柄可能晚于清理释放，忽略删除失败
        import shutil
        shutil.rmtree(cls.tmp_dir, ignore_errors=True)

    def setUp(self):
        self.lib.drms_raw_stream_reset()
        self.assertEqual(self.lib.drms_raw_stream_subscribe(4000), 15)

    # ---- Python 侧发送/限流桩 ----
    def make_send(self, deliver=True):
        state = {'wire': None, 'len': 0, 'calls': 0}

        @ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.POINTER(ctypes.c_ubyte),
                          ctypes.c_size_t, ctypes.c_uint32)
        def send(ctx, data, length, priority):
            state['calls'] += 1
            if not deliver:
                return 0
            state['wire'] = bytes(ctypes.cast(data, ctypes.POINTER(ctypes.c_ubyte))[0:length])
            state['len'] = length
            return 1
        return state, send

    @staticmethod
    @ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32)
    def _room_ok(ctx, priority):
        return 1

    @staticmethod
    @ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32)
    def _room_full(ctx, priority):
        return 0

    def feed_n(self, count, gen=2, first=100, rate=4000):
        for i in range(count):
            frame = bytes([i & 0xFF]) * 12 + (first + i).to_bytes(4, 'little')
            self.lib.drms_raw_stream_feed(gen, first + i, rate, frame)

    def decode(self, wire):
        """经真实 COBS 解帧器回解，验证定界/CRC；返回去 COBS 后的原始消息。"""
        p = Path(self.tmp_dir)
        lib = self.lib
        decoded = {}

        @ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.POINTER(ctypes.c_ubyte), ctypes.c_size_t)
        def handler(user, frame, length):
            decoded['raw'] = bytes(ctypes.cast(frame, ctypes.POINTER(ctypes.c_ubyte))[0:length])

        fc = ctypes.create_string_buffer(lib.drms_cdc_frame_size())
        lib.drms_cdc_frame_init(fc)
        for b in wire:
            lib.drms_cdc_frame_feed(fc, b, 0, handler, None)
        # CRC 校验失败会体现为 handler 不回调
        self.assertIn('raw', decoded)
        raw = decoded['raw']
        self.assertLessEqual(len(raw), 1048)
        return raw

    @staticmethod
    def parse_tlvs(raw):
        """按 v2 头 + TLV 列表解析；返回 (header dict, {tag: value bytes})。"""
        hdr = {'major': raw[0], 'kind': raw[1], 'opcode': int.from_bytes(raw[2:4], 'little'),
               'session': int.from_bytes(raw[4:8], 'little'),
               'request_id': int.from_bytes(raw[8:16], 'little'),
               'payload_len': int.from_bytes(raw[16:18], 'little'),
               'flags': int.from_bytes(raw[18:20], 'little')}
        fields = {}
        pos = 20
        end = 20 + hdr['payload_len']
        while pos < end:
            tag = int.from_bytes(raw[pos:pos + 2], 'little')
            length = int.from_bytes(raw[pos + 2:pos + 4], 'little')
            fields[tag & 0x7FFF] = raw[pos + 4:pos + 4 + length]
            pos += 4 + length
        assert pos == end, f'TLV 越界: {pos} != {end}'
        return hdr, fields

    # ---- 用例 ----
    def test_subscribe_gates(self):
        self.lib.drms_raw_stream_reset()
        self.assertEqual(self.lib.drms_raw_stream_subscribe(0), 0)
        self.assertEqual(self.lib.drms_raw_stream_subscribe(16001), 0)
        self.assertEqual(self.lib.drms_raw_stream_subscribe(16000), 4)
        self.assertEqual(self.lib.drms_raw_stream_subscribe(8000), 8)
        self.assertEqual(self.lib.drms_raw_stream_subscribe(4000), 15)
        self.assertEqual(self.lib.drms_raw_stream_period_ms(), 15)
        self.assertEqual(self.lib.drms_raw_stream_active(), 1)

    def test_batch_layout_and_fields(self):
        state, send = self.make_send()
        self.feed_n(BATCH, gen=2, first=100)
        sent = self.lib.drms_raw_stream_publish(0xAABBCCDD, send, None, self._room_ok, None)
        self.assertEqual(sent, BATCH)
        # COBS 输出随零分布浮动：上界 = 1040+块头5+定界符1
        self.assertGreaterEqual(state['len'], 1021)
        self.assertLessEqual(state['len'], 1046)
        raw = self.decode(state['wire'])
        hdr, fields = self.parse_tlvs(raw)
        self.assertEqual(hdr['major'], 2)
        self.assertEqual(hdr['kind'], 3)
        self.assertEqual(hdr['opcode'], 131)
        self.assertEqual(hdr['session'], 0xAABBCCDD)
        self.assertEqual(hdr['request_id'], 0)
        self.assertEqual(hdr['flags'], 0)
        self.assertEqual(hdr['payload_len'], 1016)
        data = fields[54]
        self.assertEqual(len(data), 960)
        for i in range(BATCH):
            frame = data[i * 16:(i + 1) * 16]
            self.assertEqual(frame[0:12], bytes([i & 0xFF]) * 12)
            self.assertEqual(int.from_bytes(frame[12:16], 'little'), 100 + i)
        self.assertEqual(int.from_bytes(fields[62], 'little'), 1)          # 流内序号
        self.assertEqual(int.from_bytes(fields[21], 'little'), 2)          # 代次
        self.assertEqual(int.from_bytes(fields[22], 'little'), 100)        # 批首序号
        self.assertEqual(int.from_bytes(fields[30], 'little'), 4000)       # 采样率
        self.assertEqual(int.from_bytes(fields[63], 'little'), 0)          # lost

    def test_stream_sequence_increments(self):
        state, send = self.make_send()
        self.feed_n(BATCH)
        self.lib.drms_raw_stream_publish(1, send, None, self._room_ok, None)
        raw1 = self.decode(state['wire'])
        self.assertEqual(int.from_bytes(self.parse_tlvs(raw1)[1][62], 'little'), 1)
        self.feed_n(BATCH, first=200)
        self.lib.drms_raw_stream_publish(1, send, None, self._room_ok, None)
        raw2 = self.decode(state['wire'])
        self.assertEqual(int.from_bytes(self.parse_tlvs(raw2)[1][62], 'little'), 2)
        self.assertEqual(int.from_bytes(self.parse_tlvs(raw2)[1][22], 'little'), 200)

    def test_generation_change_flushes_early(self):
        state, send = self.make_send()
        self.feed_n(30, gen=2, first=100)
        self.feed_n(1, gen=3, first=130)   # 换代：批立即冲刷，不跨代次
        sent = self.lib.drms_raw_stream_publish(1, send, None, self._room_ok, None)
        raw = self.decode(state['wire'])
        hdr, fields = self.parse_tlvs(raw)
        self.assertEqual(len(fields[54]), 30 * 16)
        self.assertEqual(int.from_bytes(fields[21], 'little'), 2)
        self.assertEqual(int.from_bytes(fields[22], 'little'), 100)
        self.assertEqual(int.from_bytes(fields[63], 'little'), 0)
        # 新批从换代帧开始
        self.feed_n(BATCH, gen=3, first=130)
        self.lib.drms_raw_stream_publish(1, send, None, self._room_ok, None)
        hdr2, fields2 = self.parse_tlvs(self.decode(state['wire']))
        self.assertEqual(len(fields2[54]), 60 * 16)
        self.assertEqual(int.from_bytes(fields2[21], 'little'), 3)
        self.assertEqual(int.from_bytes(fields2[22], 'little'), 130)

    def test_no_feed_without_subscription(self):
        state, send = self.make_send()
        self.lib.drms_raw_stream_unsubscribe()
        self.assertEqual(self.lib.drms_raw_stream_active(), 0)
        self.feed_n(BATCH)
        self.assertEqual(self.lib.drms_raw_stream_publish(1, send, None, self._room_ok, None), 0)
        self.assertEqual(self.lib.drms_raw_stream_lost(), 0)
        # 重新订阅后流内序号从 1 重新计
        self.lib.drms_raw_stream_subscribe(4000)
        self.feed_n(BATCH, first=500)
        self.lib.drms_raw_stream_publish(1, send, None, self._room_ok, None)
        self.assertEqual(int.from_bytes(self.parse_tlvs(self.decode(state['wire']))[1][62], 'little'), 1)

    def test_mailbox_occupied_drops_whole_batch(self):
        state, send = self.make_send()
        self.feed_n(BATCH, first=100)                       # 批 A 完成入邮箱
        self.feed_n(BATCH, first=200)                       # 批 B 完成：邮箱占用 → 整批丢
        self.assertEqual(self.lib.drms_raw_stream_lost(), BATCH)
        self.lib.drms_raw_stream_publish(1, send, None, self._room_ok, None)
        hdr, fields = self.parse_tlvs(self.decode(state['wire']))
        self.assertEqual(int.from_bytes(fields[22], 'little'), 100)        # 发出的是批 A
        self.assertEqual(int.from_bytes(fields[63], 'little'), BATCH)      # lost 随批携带

    def test_can_send_full_retains_batch(self):
        state, send = self.make_send()
        self.feed_n(BATCH, first=100)
        self.assertEqual(self.lib.drms_raw_stream_publish(1, send, None, self._room_full, None), 0)
        self.assertEqual(self.lib.drms_raw_stream_lost(), 0)               # 延时不算丢失
        self.assertEqual(self.lib.drms_raw_stream_publish(1, send, None, self._room_full, None), 0)
        self.assertEqual(self.lib.drms_raw_stream_publish(1, send, None, self._room_ok, None), BATCH)
        self.assertEqual(self.lib.drms_raw_stream_lost(), 0)

    def test_send_failure_counts_lost(self):
        state, send = self.make_send(deliver=False)
        self.feed_n(BATCH)
        self.assertEqual(self.lib.drms_raw_stream_publish(1, send, None, self._room_ok, None), 0)
        self.assertEqual(self.lib.drms_raw_stream_lost(), BATCH)

    def test_resubscribe_resets_lost_and_sequence(self):
        state, send = self.make_send(deliver=False)
        self.feed_n(BATCH)
        self.lib.drms_raw_stream_publish(1, send, None, self._room_ok, None)
        self.assertEqual(self.lib.drms_raw_stream_lost(), BATCH)
        self.lib.drms_raw_stream_subscribe(4000)
        self.assertEqual(self.lib.drms_raw_stream_lost(), 0)
        good, send_ok = self.make_send()
        self.feed_n(BATCH, first=900)
        self.lib.drms_raw_stream_publish(1, send_ok, None, self._room_ok, None)
        self.assertEqual(int.from_bytes(self.parse_tlvs(self.decode(good['wire']))[1][62], 'little'), 1)

    def test_unsubscribe_mid_batch_drops_silently(self):
        state, send = self.make_send()
        self.feed_n(30)
        self.lib.drms_raw_stream_unsubscribe()
        self.feed_n(BATCH, first=300)                       # 未订阅：喂入被忽略
        self.lib.drms_raw_stream_subscribe(4000)
        self.assertEqual(self.lib.drms_raw_stream_lost(), 0)
        # 新订阅后从新批开始；单帧批靠换代冲刷才会发出
        self.feed_n(1, gen=5, first=400)
        self.feed_n(1, gen=6, first=401)
        self.lib.drms_raw_stream_publish(1, send, None, self._room_ok, None)
        hdr, fields = self.parse_tlvs(self.decode(state['wire']))
        self.assertEqual(len(fields[54]), 16)
        self.assertEqual(int.from_bytes(fields[21], 'little'), 5)
        self.assertEqual(int.from_bytes(fields[22], 'little'), 400)

    def test_send_failure_after_lost_snapshot_is_monotone(self):
        """先丢一批（邮箱占用），下一批携带的 lost 必须覆盖该丢失。"""
        deliver, send_ok = self.make_send()
        self.feed_n(BATCH, first=100)                       # 批 A
        self.feed_n(BATCH, first=200)                       # 批 B 丢弃，lost=60
        self.feed_n(BATCH, first=300)                       # 批 C 完成时邮箱仍占用？A 占用，B 已丢，C 丢弃
        self.assertEqual(self.lib.drms_raw_stream_lost(), 2 * BATCH)
        # 消费者取走批 A；lost 快照取发送时刻（当前累计 120，对客户端单调不减）
        self.lib.drms_raw_stream_publish(1, send_ok, None, self._room_ok, None)
        hdr, fields = self.parse_tlvs(self.decode(deliver['wire']))
        self.assertEqual(int.from_bytes(fields[22], 'little'), 100)
        lost_in_batch = int.from_bytes(fields[63], 'little')
        self.assertEqual(lost_in_batch, 2 * BATCH)
        # 再发时批 C 位置已丢，批 D 新数据继续，lost 单调不减
        self.feed_n(BATCH, first=400)
        self.lib.drms_raw_stream_publish(1, send_ok, None, self._room_ok, None)
        hdr2, fields2 = self.parse_tlvs(self.decode(deliver['wire']))
        self.assertGreaterEqual(int.from_bytes(fields2[63], 'little'), lost_in_batch)


if __name__ == '__main__':
    unittest.main()
