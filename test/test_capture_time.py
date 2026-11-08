"""采集时间侧表测试：编译真实 drms_capture_time.c，验证 65×32B 侧表与名义时间换算。

契约：C3 时间元数据（docs/design/2026-11-05-firmware-architecture.md）与计划第四次复检 T1 项。
publish 仅生产者在块首帧入环前调用；lookup 仅消费者在释放环槽前调用；
覆盖资格使用传入的原始环已消费水位（consumed_raw_next），不依赖 valid 标志单独判断。
"""
import ctypes
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

OK, ACCEPTED, BUSY, INVALID, STALE = 0, 1, 2, 3, 4
IO_ERROR = 6

BLOCK = 64
SLOTS = 65


class CaptureTimeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        p = Path(cls.tmp.name)
        (p / 'selfcheck.c').write_text('#include "drms_architecture_contract.h"\n'
                                       '#include "drms_capture_time.h"\nint probe;\n')
        src = ROOT / 'firmware/DE-DRMS-Code/Core'
        subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Werror=implicit-function-declaration',
                        '-I', str(src / 'Inc'), str(src / 'Src/drms_capture_time.c'),
                        '-o', str(p / 'capture.so')], check=True)
        # contract.h 与 capture_time.h 均须自包含可编译
        subprocess.run(['cc', '-fsyntax-only', '-Wall', '-Werror',
                        '-I', str(src / 'Inc'), str(p / 'selfcheck.c')], check=True)
        cls.lib = ctypes.CDLL(str(p / 'capture.so'))
        cls.lib.drms_capture_time_publish.argtypes = [ctypes.c_uint64, ctypes.c_uint64,
                                                      ctypes.c_uint32, ctypes.c_uint64]
        cls.lib.drms_capture_time_lookup.argtypes = [ctypes.c_uint64, ctypes.c_uint32,
                                                     ctypes.POINTER(ctypes.c_uint64)]
        cls.lib.drms_capture_time_nominal_us.argtypes = [ctypes.c_void_p, ctypes.c_uint64]
        cls.lib.drms_capture_time_nominal_us.restype = ctypes.c_uint64

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        self.lib.drms_capture_time_reset()

    def publish(self, raw_ticket, consumed, generation, mono_us):
        return self.lib.drms_capture_time_publish(raw_ticket, consumed, generation, mono_us)

    def lookup(self, raw_ticket, generation):
        out = ctypes.c_uint64(0)
        result = self.lib.drms_capture_time_lookup(raw_ticket, generation, ctypes.byref(out))
        return result, out.value

    def test_block_lookup_returns_first_frame_capture_time(self):
        self.assertEqual(self.publish(0, 0, 7, 1000), OK)
        for ticket in (0, 1, 63):
            result, bound = self.lookup(ticket, 7)
            self.assertEqual((result, bound), (OK, 1000), ticket)
        # 未发布的块不可用
        self.assertEqual(self.lookup(64, 7)[0], STALE)

    def test_publish_rejects_unaligned_ticket(self):
        self.assertEqual(self.publish(1, 0, 1, 5), INVALID)
        self.assertEqual(self.publish(63, 0, 1, 5), INVALID)

    def test_lookup_rejects_null_and_generation_mismatch(self):
        self.assertEqual(self.publish(0, 0, 7, 1000), OK)
        out = ctypes.c_uint64(0)
        self.assertEqual(self.lib.drms_capture_time_lookup(0, 7, None), INVALID)
        result, _ = self.lookup(0, 8)
        self.assertEqual(result, STALE)

    def test_slot_zero_overwrite_at_block_65_requires_consumed_watermark(self):
        """槽 0 在第 65 块到达时仍按真实消费水位判断是否可覆盖。"""
        self.assertEqual(self.publish(0, 0, 3, 1000), OK)
        # 旧块 0 的帧未全部消费（consumed < 64）→ 拒绝覆盖
        self.assertEqual(self.publish(65 * BLOCK, 63, 3, 65000), IO_ERROR)
        result, bound = self.lookup(0, 3)
        self.assertEqual((result, bound), (OK, 1000))  # 旧时间未被改写
        # 消费水位达到旧块末尾 → 允许覆盖
        self.assertEqual(self.publish(65 * BLOCK, 64, 3, 65000), OK)
        self.assertEqual(self.lookup(0, 3)[0], STALE)  # 已被新块替换
        self.assertEqual(self.lookup(65 * BLOCK, 3), (OK, 65000))

    def test_4096_frame_sliding_window_crosses_65_blocks_without_mixing(self):
        """4096 帧滑动窗口跨 65 块不串时间；窗口内全部可查且时间正确。"""
        generation = 5
        published = 0
        consumed = 0
        times = {}
        for block in range(71):  # 覆盖跨过 65 块的完整循环
            ticket = block * BLOCK
            mono = 100000 + block * 7919
            self.assertEqual(self.publish(ticket, consumed, generation, mono),
                             OK, block)
            times[ticket] = mono
            published = ticket + BLOCK
            consumed = max(0, published - 4096)
        # 窗口内每个 ticket 的时间必须等于其所在块的发布时间
        for ticket in range(published - 4096, published):
            result, bound = self.lookup(ticket, generation)
            self.assertEqual(result, OK, ticket)
            self.assertEqual(bound, times[(ticket // BLOCK) * BLOCK], ticket)
        # 窗口外最老数据允许 STALE（槽已合法覆盖）
        self.assertEqual(self.lookup(0, generation)[0], STALE)

    def test_same_block_republish_updates_lower_bound(self):
        self.assertEqual(self.publish(128, 0, 1, 5000), OK)
        self.assertEqual(self.publish(128, 0, 1, 5100), OK)
        self.assertEqual(self.lookup(130, 1), (OK, 5100))

    def test_generation_switch_requires_reset(self):
        self.assertEqual(self.publish(0, 0, 1, 100), OK)
        # 未 reset 就换代发布：同一槽位拒绝，不得覆盖旧代时间
        self.assertEqual(self.publish(65 * BLOCK, 4096, 2, 200), STALE)
        result, bound = self.lookup(0, 1)
        self.assertEqual((result, bound), (OK, 100))
        # 正确顺序：确认旧环不再使用 → reset → 新代发布
        self.lib.drms_capture_time_reset()
        self.assertEqual(self.lookup(0, 1)[0], STALE)
        self.assertEqual(self.publish(0, 0, 2, 300), OK)
        self.assertEqual(self.lookup(3, 2), (OK, 300))
        self.assertEqual(self.lookup(3, 1)[0], STALE)

    def test_side_table_budget_is_fixed_65x32_bytes(self):
        self.assertEqual(self.lib.drms_capture_time_bytes(), 65 * 32)

    def test_nominal_time_quotient_remainder_conversion(self):
        class Anchor(ctypes.Structure):
            _fields_ = [('acquisition_generation', ctypes.c_uint32),
                        ('rate_hz', ctypes.c_uint32),
                        ('sample_seq0', ctypes.c_uint64),
                        ('mono_us0', ctypes.c_uint64)]

        def nominal(anchor, seq):
            return self.lib.drms_capture_time_nominal_us(ctypes.byref(anchor), seq)

        a = Anchor(1, 4000, 100, 1000)
        self.assertEqual(nominal(a, 100), 1000)              # 锚点本身
        self.assertEqual(nominal(a, 103), 1000 + 750)        # 商余分解：3*1e6/4000
        self.assertEqual(nominal(a, 4100), 1000 + 1000000)   # 恰好一个采样率块
        # 低 32 位序号回绕：seq0=0xFFFFFFF0 之后 0x10000000F
        w = Anchor(2, 4000, 0xFFFFFFF0, 1000)
        self.assertEqual(nominal(w, 0x10000000F), 1000 + 7750)
        # 长时间运行：2^31 个样本 @4 kSPS ≈ 6.2 天，不得溢出 64 位
        long = Anchor(3, 4000, 0, 5)
        self.assertEqual(nominal(long, 2**31), 5 + 2**31 * 1000000 // 4000)
        # 128 kSPS：大 rate 同样正确
        h = Anchor(4, 128000, 0, 7)
        self.assertEqual(nominal(h, 2**33), 7 + 2**33 * 1000000 // 128000)


if __name__ == '__main__':
    unittest.main()
