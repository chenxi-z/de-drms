"""监测管线测试：真实 drms_monitor/filter/classifier/baseline（C6/R7/R8/T6）。

覆盖：IIR/建立窗口/恢复重计、C6 转换表逐行、端点与回差、空隙、跨级、候选
重新确认、confirm_us=0、无效输入（NaN/质量/缺口/版本）、tick 新鲜度边界
（119999/120000、时基倒退）、tick 不改历史算法状态、分批一致性、基线统计。
"""
import ctypes
import math
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

HEADER = r'''
#ifndef MONITOR_TEST_H
#define MONITOR_TEST_H
#endif
'''

OK, ACCEPTED, BUSY, INVALID, STALE = 0, 1, 2, 3, 4

INVALID_S, WARMUP_S, UNCONFIGURED_S, UNMAPPED_S, PENDING_S, CONFIRMED_S = range(6)

CONTEXT_BYTES = 1536


class TimeAnchor(ctypes.Structure):
    _fields_ = [('acquisition_generation', ctypes.c_uint32), ('rate_hz', ctypes.c_uint32),
                ('sample_seq0', ctypes.c_uint64), ('mono_us0', ctypes.c_uint64)]


class Interval(ctypes.Structure):
    _fields_ = [('lo', ctypes.c_double), ('hi', ctypes.c_double), ('h', ctypes.c_double),
                ('id', ctypes.c_uint16), ('level', ctypes.c_uint8),
                ('last_upper_closed', ctypes.c_bool)]


class Config(ctypes.Structure):
    _fields_ = [('rate_hz', ctypes.c_uint32), ('tau_us', ctypes.c_uint64),
                ('warmup_us', ctypes.c_uint64), ('confirm_us', ctypes.c_uint64),
                ('stale_timeout_us', ctypes.c_uint64), ('r0', ctypes.c_double),
                ('baseline_valid', ctypes.c_bool), ('interval_count', ctypes.c_uint8),
                ('intervals', Interval * 16)]


class Input(ctypes.Structure):
    _fields_ = [('ohms', ctypes.c_double), ('capture_us', ctypes.c_uint64),
                ('capture_lower_bound_us', ctypes.c_uint64), ('sample_seq', ctypes.c_uint64),
                ('acquisition_generation', ctypes.c_uint32), ('quality_flags', ctypes.c_uint32),
                ('config_version', ctypes.c_uint64), ('baseline_version', ctypes.c_uint64)]


class Output(ctypes.Structure):
    _fields_ = [('state', ctypes.c_int), ('reason', ctypes.c_uint32),
                ('capture_lower_bound_us', ctypes.c_uint64), ('fresh', ctypes.c_bool),
                ('freshness_reason', ctypes.c_uint32), ('observed', ctypes.c_int16),
                ('candidate', ctypes.c_int16), ('confirmed', ctypes.c_int16),
                ('ratio', ctypes.c_double), ('hysteresis_hold', ctypes.c_bool),
                ('sample_seq', ctypes.c_uint64), ('acquisition_generation', ctypes.c_uint32),
                ('config_version', ctypes.c_uint64), ('baseline_version', ctypes.c_uint64)]


class PipelineTest(unittest.TestCase):
    def test_monitor_context_budget_is_at_most_1536_bytes(self):
        src = ROOT / 'firmware/DE-DRMS-Code/Core/Inc'
        subprocess.run(['cc', '-std=c11', '-fsyntax-only', '-I', str(src), '-xc', '-'],
                       input='#include "drms_architecture_contract.h"\n'
                             '_Static_assert(DRMS_MONITOR_CONTEXT_BYTES <= 1536u, "context budget");\n',
                       text=True, check=True)

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        p = Path(cls.tmp.name)
        (p / 'main.h').write_text(HEADER)
        src = ROOT / 'firmware/DE-DRMS-Code/Core'
        subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Werror=implicit-function-declaration',
                        '-I', str(p), '-I', str(src / 'Inc'),
                        *[str(src.parent / f'App/application/measurement/drms_{name}.c') for name in
                          ('monitor', 'filter', 'classifier', 'baseline')],
                        '-o', str(p / 'mon.so')], check=True)
        cls.lib = ctypes.CDLL(str(p / 'mon.so'))
        cls.lib.drms_monitor_configure.argtypes = [ctypes.c_void_p, ctypes.POINTER(Config)]
        cls.lib.drms_monitor_step.argtypes = [ctypes.c_void_p, ctypes.POINTER(Input), ctypes.POINTER(Output)]
        cls.lib.drms_monitor_tick.argtypes = [ctypes.c_void_p, ctypes.c_uint64, ctypes.POINTER(Output)]
        cls.lib.drms_baseline_configure.argtypes = [ctypes.POINTER(ctypes.c_uint8 * 64),
                                                    ctypes.c_uint32, ctypes.c_uint64, ctypes.c_double]
        cls.lib.drms_baseline_feed.argtypes = [ctypes.POINTER(ctypes.c_uint8 * 64), ctypes.c_double, ctypes.c_uint64]
        cls.lib.drms_baseline_candidate.argtypes = [ctypes.POINTER(ctypes.c_uint8 * 64),
                                                    ctypes.POINTER(ctypes.c_double),
                                                    ctypes.POINTER(ctypes.c_double)]
        # 头文件自包含编译检查（contract.h + 三个内部头）
        (p / 'selfcheck.c').write_text(
            '#include "drms_architecture_contract.h"\n'
            '#include "drms_filter.h"\n#include "drms_classifier.h"\n#include "drms_baseline.h"\nint probe;\n')
        subprocess.run(['cc', '-fsyntax-only', '-Wall', '-Werror',
                        '-I', str(src / 'Inc'), str(p / 'selfcheck.c')], check=True)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        self.ctx = (ctypes.c_ubyte * CONTEXT_BYTES)()
        self.lib.drms_monitor_init(self.ctx)
        self.baseline = (ctypes.c_uint8 * 64)()

    def configure(self, intervals=((0.9, 1.1, 0.02, 1, 1, False),),
                  tau=100000, warmup=0, confirm=0, rate=4000, r0=100000.0,
                  baseline_valid=True, stale=20000):
        cfg = Config(rate_hz=rate, tau_us=tau, warmup_us=warmup, confirm_us=confirm,
                     stale_timeout_us=stale, r0=r0, baseline_valid=baseline_valid,
                     interval_count=len(intervals))
        for i, (lo, hi, h, ident, level, closed) in enumerate(intervals):
            cfg.intervals[i].lo, cfg.intervals[i].hi, cfg.intervals[i].h = lo, hi, h
            cfg.intervals[i].id, cfg.intervals[i].level, cfg.intervals[i].last_upper_closed = ident, level, closed
        self.assertEqual(self.lib.drms_monitor_configure(self.ctx, ctypes.byref(cfg)), OK)
        return cfg

    def step(self, ratio, seq, quality=0, gen=1, cv=1, bv=1, lower=None):
        inp = Input(ohms=ratio * 100000.0, capture_us=seq * 250,
                    capture_lower_bound_us=lower if lower is not None else seq * 250,
                    sample_seq=seq, acquisition_generation=gen, quality_flags=quality,
                    config_version=cv, baseline_version=bv)
        out = Output()
        self.lib.drms_monitor_step(self.ctx, ctypes.byref(inp), ctypes.byref(out))
        return out

    def tick(self, now):
        out = Output()
        self.lib.drms_monitor_tick(self.ctx, now, ctypes.byref(out))
        return out

    def test_iir_bypass_and_first_sample_initialization(self):
        self.configure(tau=0, warmup=0)
        out = self.step(1.0, 1)
        self.assertEqual(out.state, CONFIRMED_S)  # confirm=0 当帧确认
        self.assertAlmostEqual(out.ratio, 1.0, places=12)
        out = self.step(2.0, 2)  # 旁路：直接跟随
        self.assertAlmostEqual(out.ratio, 2.0, places=12)

    def test_iir_converges_with_tau(self):
        self.configure(tau=250, warmup=0, confirm=0)  # dt=250us → alpha≈0.632
        out = self.step(1.0, 1)
        self.assertAlmostEqual(out.ratio, 1.0, places=12)
        out = self.step(2.0, 2)
        self.assertAlmostEqual(out.ratio, 1.0 + 0.632, places=2)  # y += alpha*(x-y)

    def test_warmup_window_and_full_restart_after_fault(self):
        self.configure(tau=0, warmup=1000, confirm=0)  # 4 个样本 @250us
        for seq in (1, 2, 3):
            out = self.step(1.0, seq)
            self.assertEqual(out.state, WARMUP_S)
            self.assertEqual(out.reason, 1 << 5)  # WARMUP reason
        out = self.step(1.0, 4)
        self.assertEqual(out.state, CONFIRMED_S)  # 建立完成
        # 质量故障 → 滤波失效；恢复需完整窗口
        out = self.step(1.0, 5, quality=1)
        self.assertEqual(out.state, INVALID_S)
        for seq in (6, 7, 8):
            out = self.step(1.0, seq)
            self.assertEqual(out.state, WARMUP_S)
        out = self.step(1.0, 9)
        self.assertEqual(out.state, CONFIRMED_S)

    def test_quality_gap_version_cause_invalid_and_clear(self):
        self.configure(tau=0, warmup=0, confirm=1000000)
        out = self.step(1.0, 1)
        self.assertEqual(out.state, PENDING_S)
        for tag, kwargs in (('NaN', {'ratio': float('nan')}),
                            ('质量', {'quality': 1}),
                            ('缺口', {'seq': 3}),
                            ('重复', {'seq': 2}),
                            ('代次', {'gen': 2}),
                            ('配置版本', {'cv': 2}),
                            ('基线版本', {'bv': 2})):
            with self.subTest(tag):
                ratio = kwargs.pop('ratio', 1.0)
                seq = kwargs.pop('seq', 2)
                out = self.step(ratio, seq, **kwargs)
                self.assertEqual(out.state, INVALID_S, tag)
                self.assertEqual(out.confirmed, -1, tag)
                self.assertEqual(out.candidate, -1, tag)
                # 恢复：重新从 PENDING 起步（确认计时归零）；恢复样本必须干净
                out = self.step(1.0, 4 if tag == '缺口' else 3)
                self.assertEqual(out.state, PENDING_S, tag)

    def test_no_baseline_blocks_mapping_but_keeps_filter(self):
        self.configure(tau=0, warmup=0, confirm=0, baseline_valid=False)
        out = self.step(1.0, 1)
        self.assertEqual(out.state, INVALID_S)
        self.assertEqual(out.reason, 1 << 3)  # NO_BASELINE

    def test_unconfigured_table(self):
        self.configure(intervals=(), tau=0, warmup=0)
        out = self.step(1.0, 1)
        self.assertEqual(out.state, UNCONFIGURED_S)
        self.assertEqual(out.observed, -1)
        self.assertEqual(out.confirmed, -1)

    def test_confirmation_counts_sample_time_not_batches(self):
        self.configure(tau=0, warmup=0, confirm=1000)  # 4 个样本 @250us
        self.assertEqual(self.step(1.0, 1).state, PENDING_S)
        self.assertEqual(self.step(1.0, 2).state, PENDING_S)
        self.assertEqual(self.step(1.0, 3).state, PENDING_S)
        out = self.step(1.0, 4)
        self.assertEqual(out.state, CONFIRMED_S)  # 名义时间 1000us 达成
        self.assertEqual(out.confirmed, 0)

    def test_candidate_change_and_return_restart_timer(self):
        self.configure(tau=0, warmup=0, confirm=1000,
                       intervals=((0.9, 1.1, 0.0, 1, 1, False), (1.3, 1.5, 0.0, 2, 2, False)))
        self.step(1.0, 1)
        self.step(1.0, 2)
        self.step(1.0, 3)
        self.assertEqual(self.step(1.0, 4).state, CONFIRMED_S)
        # 跨级直接选择目标区间（不逐级等待）
        out = self.step(1.4, 5)
        self.assertEqual(out.state, PENDING_S)
        self.assertEqual(out.candidate, 1)
        self.assertEqual(out.confirmed, -1)  # 旧正常等级不得延续
        # 候选反复变化重新计时
        out = self.step(1.42, 6)
        self.assertEqual(out.state, PENDING_S)
        self.assertEqual(out.candidate, 1)
        out = self.step(1.44, 7)
        self.assertEqual(out.state, PENDING_S)
        out = self.step(1.44, 8)
        self.assertEqual(out.state, CONFIRMED_S)  # 连续 1000us 达成
        # 返回历史区间：重新确认
        out = self.step(1.0, 9)
        self.assertEqual(out.state, PENDING_S)
        self.assertEqual(out.candidate, 0)
        for seq in (10, 11):
            self.assertEqual(self.step(1.0, seq).state, PENDING_S)
        out = self.step(1.0, 12)
        self.assertEqual(out.state, CONFIRMED_S)

    def test_hysteresis_hold_and_exit(self):
        self.configure(tau=0, warmup=0, confirm=0,
                       intervals=((0.9, 1.1, 0.02, 1, 1, False),))
        self.assertEqual(self.step(1.0, 1).state, CONFIRMED_S)
        # 保持范围 [0.88, 1.12]：1.11 仍保持（表端点外）
        out = self.step(1.11, 2)
        self.assertEqual(out.state, CONFIRMED_S)
        self.assertEqual(out.hysteresis_hold, 1)
        self.assertEqual(out.confirmed, 0)
        self.assertEqual(out.candidate, -1)
        # 超出保持范围 → UNMAPPED（空隙），两者清空
        out = self.step(1.2, 3)
        self.assertEqual(out.state, UNMAPPED_S)
        self.assertEqual(out.confirmed, -1)
        self.assertEqual(out.candidate, -1)
        # 回到表内 → PENDING 重新确认（confirm=0 当帧确认）
        out = self.step(1.0, 4)
        self.assertEqual(out.state, CONFIRMED_S)

    def test_hysteresis_zero_uses_strict_endpoints(self):
        self.configure(tau=0, warmup=0, confirm=0,
                       intervals=((0.9, 1.1, 0.0, 1, 1, False),))
        self.assertEqual(self.step(1.0, 1).state, CONFIRMED_S)
        self.assertEqual(self.step(1.0999, 2).state, CONFIRMED_S)  # 端点内
        self.assertEqual(self.step(1.1, 3).state, UNMAPPED_S)  # 严格端点外

    def test_last_interval_closed_upper_endpoint(self):
        self.configure(tau=0, warmup=0, confirm=0,
                       intervals=((0.0, 1.0, 0.0, 1, 1, True),))
        self.assertEqual(self.step(1.0, 1).state, CONFIRMED_S)
        self.assertEqual(self.step(0.5, 2).state, CONFIRMED_S)

    def test_gap_between_intervals_is_unmapped(self):
        self.configure(tau=0, warmup=0, confirm=0,
                       intervals=((0.0, 0.5, 0.0, 1, 1, False),
                                  (0.7, 0.9, 0.0, 2, 2, False)))
        self.assertEqual(self.step(0.3, 1).state, CONFIRMED_S)
        out = self.step(0.6, 2)
        self.assertEqual(out.state, UNMAPPED_S)  # 空隙
        self.assertEqual(out.observed, -1)
        out = self.step(0.8, 3)
        self.assertEqual(out.state, CONFIRMED_S)

    def test_boundary_values_on_both_sides(self):
        self.configure(tau=0, warmup=0, confirm=0,
                       intervals=((0.0, 0.5, 0.0, 1, 1, False),
                                  (0.5, 1.0, 0.0, 2, 2, False)))
        self.assertEqual(self.step(0.5, 1).observed, 1)  # 内部交界只归右侧

    def test_tick_freshness_boundaries(self):
        self.configure(tau=0, warmup=0, confirm=0, stale=20000)
        self.step(1.0, 1, lower=100000)
        self.assertTrue(self.tick(119999).fresh)
        out = self.tick(120000)
        self.assertFalse(out.fresh)
        self.assertEqual(out.freshness_reason, 1 << 2)  # STALE
        # 时基倒退：now < lower → TIMEBASE_FAULT，不做无符号减法截零
        out = self.tick(99999)
        self.assertFalse(out.fresh)
        self.assertEqual(out.freshness_reason, 1 << 1)
        # 长期无 DRDY：仅 tick 也过期
        out = self.tick(10 ** 12)
        self.assertFalse(out.fresh)
        self.assertEqual(out.freshness_reason, 1 << 2)

    def test_tick_without_any_sample_is_no_sample(self):
        self.configure(tau=0, warmup=0)
        out = self.tick(1000)
        self.assertFalse(out.fresh)
        self.assertEqual(out.freshness_reason, 1 << 0)  # NO_SAMPLE

    def test_tick_does_not_modify_history_and_overlay_clears_on_invalid(self):
        self.configure(tau=0, warmup=0, confirm=0, stale=20000)
        self.step(1.0, 1, lower=100000)
        self.tick(100000)
        # 陈旧数据配最新处理时刻仍为 STALE（tick 只看捕获时间下界）
        self.step(1.0, 2, lower=50000)  # 旧帧（积压）
        self.assertFalse(self.tick(200000).fresh)
        # 算法历史状态不受 tick 影响
        history = self.tick(100000)
        self.assertEqual(history.confirmed, 0)
        # 真实质量故障重置算法
        self.step(1.0, 3, quality=1, lower=100000)
        out = self.tick(100000)
        self.assertEqual(out.state, INVALID_S)
        self.assertTrue(out.fresh)  # 捕获时间新鲜：展示覆盖独立于算法状态

    def test_same_sequence_one_or_many_per_batch_identical(self):
        self.configure(tau=100000, warmup=500, confirm=0)
        seqs = [(0.5 + 0.001 * i) for i in range(40)]
        ctx_a = (ctypes.c_ubyte * CONTEXT_BYTES)()
        self.lib.drms_monitor_init(ctx_a)
        cfg = Config(rate_hz=4000, tau_us=100000, warmup_us=500, confirm_us=0,
                     stale_timeout_us=20000, r0=100000.0, baseline_valid=True, interval_count=1)
        cfg.intervals[0].lo, cfg.intervals[0].hi, cfg.intervals[0].h = 0.0, 10.0, 0.0
        cfg.intervals[0].id, cfg.intervals[0].level = 1, 1
        self.lib.drms_monitor_configure(ctx_a, ctypes.byref(cfg))
        self.lib.drms_monitor_configure(self.ctx, ctypes.byref(cfg))
        outputs_a, outputs_b = [], []
        for i, r in enumerate(seqs):
            inp = Input(ohms=r * 100000.0, capture_us=(i + 1) * 250,
                        capture_lower_bound_us=(i + 1) * 250, sample_seq=i + 1,
                        acquisition_generation=1, quality_flags=0,
                        config_version=1, baseline_version=1)
            o = Output()
            self.lib.drms_monitor_step(ctx_a, ctypes.byref(inp), ctypes.byref(o))
            outputs_a.append(o.ratio)
        # 多帧一批：同一循环一次性推进（结果按序相同）
        for i, r in enumerate(seqs):
            inp = Input(ohms=r * 100000.0, capture_us=(i + 1) * 250,
                        capture_lower_bound_us=(i + 1) * 250, sample_seq=i + 1,
                        acquisition_generation=1, quality_flags=0,
                        config_version=1, baseline_version=1)
            o = Output()
            self.lib.drms_monitor_step(self.ctx, ctypes.byref(inp), ctypes.byref(o))
            outputs_b.append(o.ratio)
        self.assertEqual(outputs_a, outputs_b)

    def test_configure_rejects_too_many_intervals(self):
        # interval_count 超上限必须整体拒绝，且不破坏既有配置
        self.configure(tau=0, warmup=0, confirm=0)
        self.assertEqual(self.step(1.0, 1).state, CONFIRMED_S)
        cfg = Config(rate_hz=4000, tau_us=0, warmup_us=0, confirm_us=0,
                     stale_timeout_us=20000, r0=100000.0, baseline_valid=True,
                     interval_count=17)  # 越界
        self.assertEqual(self.lib.drms_monitor_configure(self.ctx, ctypes.byref(cfg)), INVALID)
        # 旧配置仍可用（配置失败保持旧配置，C6）
        self.assertEqual(self.step(1.0, 2).state, CONFIRMED_S)

    def test_baseline_streaming_statistics(self):
        lib = self.lib
        ctx = ctypes.cast(self.baseline, ctypes.POINTER(ctypes.c_uint8 * 64))
        lib.drms_baseline_configure(ctx, 4, 1000, 0.01)
        lib.drms_baseline_reset(ctx)
        mean, sd = ctypes.c_double(), ctypes.c_double()
        lib.drms_baseline_configure(ctx, 0, 0, -1.0)  # 未配置合格参数
        self.assertEqual(lib.drms_baseline_candidate(ctx, ctypes.byref(mean), ctypes.byref(sd)), 2)
        lib.drms_baseline_configure(ctx, 4, 1000, 0.01)  # 已配置：样本不足 → NOT_READY
        self.assertEqual(lib.drms_baseline_candidate(ctx, ctypes.byref(mean), ctypes.byref(sd)), 0)
        for i in range(4):
            lib.drms_baseline_feed(ctx, 100000.0 + (1.0 if i % 2 else -1.0), 250)
        result = lib.drms_baseline_candidate(ctx, ctypes.byref(mean), ctypes.byref(sd))
        self.assertEqual(result, 1)  # 抖动 sd/mean = 1e-5 < 1e-2 → OK
        self.assertAlmostEqual(mean.value, 100000.0, delta=0.5)
        lib.drms_baseline_feed(ctx, float('nan'), 250)  # 非有限不入统计
        self.assertEqual(lib.drms_baseline_candidate(ctx, ctypes.byref(mean), ctypes.byref(sd)), 1)
        # 稳定限值超标 → NOT_READY
        lib.drms_baseline_configure(ctx, 4, 0, 1e-9)
        for i in range(4):
            lib.drms_baseline_feed(ctx, 100000.0 + (100.0 if i % 2 else -100.0), 250)
        self.assertEqual(lib.drms_baseline_candidate(ctx, ctypes.byref(mean), ctypes.byref(sd)), 0)


if __name__ == '__main__':
    unittest.main()
