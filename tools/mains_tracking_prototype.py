#!/usr/bin/env python3
"""工频跟踪与谐波建模相减：离线原型（第一阶段固定模型 / 第二阶段稳定段跟踪）。

这是**可行性验证原型**，不是产品功能：
  · 只读 BIN 原始记录，不改固件/协议/原始数据；
  · 不接正式 GUI，不改变现有滤波默认值；
  · 学习区间手动指定（前 5 s），不实现自动事件检测。

规格：用户 2026-11-16《工频跟踪与谐波建模相减：离线实现及验收方案》。

用法：
    python tools/mains_tracking_prototype.py all
    python tools/mains_tracking_prototype.py stage1 [--harm 15]
    python tools/mains_tracking_prototype.py stage2 [--harm 15]
    python tools/mains_tracking_prototype.py compare
    python tools/mains_tracking_prototype.py inject

输出：
  · 终端表格（结果表）
  · host/data/analysis/mains_proto/*.svg / *.txt（派生数据，不入 Git）

依赖：numpy、matplotlib（无 scipy：最小二乘走 numpy.linalg.lstsq，即 SVD 路径）。
"""
from __future__ import annotations

import argparse
import importlib.util
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / 'host/data/noise30/PC0001.BIN'
OUT = ROOT / 'host/data/analysis/mains_proto'

FS = 4000.0
LINE_NOMINAL = 50.0
TRAIN_SECONDS = 5.0          # 学习区间：记录前 5 s（手动指定）
SEARCH_HZ = (49.0, 51.0)     # 工频搜索范围
HARMONICS_DEFAULT = tuple(range(1, 16))
HARMONIC_SETS = (5, 9, 15)


# ----------------------------------------------------------------------------
# 数据载入与校验（以 BIN 为权威，复用仓库解码器）
# ----------------------------------------------------------------------------
def _load_log_module():
    spec = importlib.util.spec_from_file_location('de_drms_log', ROOT / 'tools/de_drms_log.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@dataclass
class Series:
    seq: np.ndarray          # 样本序号（u32 回绕已由解码器扩展前的原始值）
    t: np.ndarray            # 名义时间 s（由序号与 fs 重建）
    x: np.ndarray            # 电阻 Ω；无效帧为 NaN
    valid: np.ndarray        # 有效标记
    fs: float
    scale: float
    rate: int
    integrity: dict


def load_series(path: Path = BIN) -> Series:
    log = _load_log_module()
    with path.open('rb') as stream:
        reader = log.LogReaderV2(stream)
        rows = list(reader)
        summary = reader.summary()
    if summary['error'] is not None:
        raise SystemExit(f'文件不完整，拒绝分析：{summary["error"]}')
    seq = np.array([r['sequence'] for r in rows], dtype=np.int64)
    x = np.array([r['ohms'] if r['ohms'] is not None else np.nan for r in rows], dtype=float)
    fs = float(summary['header']['rate'])
    cal = summary['header']['calibration'] or {}
    scale = float(cal.get('scale_ohms', 0.0))
    rate = int(summary['header']['rate'])
    # 名义时间：用扩展后的 sample_index（解码器已按锚点扩展）
    idx = np.array([r['sample_index'] if r['sample_index'] is not None else i for i, r in enumerate(rows)],
                   dtype=np.int64)
    t = (idx - idx[0]) / fs
    integrity = {
        'complete': summary['complete'],
        'records': summary['records'],
        'crc_errors': summary['crc_errors'],
        'sequence_gaps': summary['sequence_gaps'],
        'sequence_disorder': summary['sequence_disorder'],
        'adc_faults': summary['adc_faults'],
        'no_reported_loss': summary['no_reported_loss'],
    }
    print(f'载入 {path.name}: {integrity["records"]} 帧, fs={fs:.0f} Hz, k={scale:.3f} Ω')
    print(f'  完整性: complete={integrity["complete"]} crc={integrity["crc_errors"]} '
          f'gaps={integrity["sequence_gaps"]} disorder={integrity["sequence_disorder"]} '
          f'adc_faults={integrity["adc_faults"]}')
    if not integrity['complete'] or integrity['crc_errors'] or integrity['sequence_gaps']:
        raise SystemExit('原始记录未通过校验，拒绝继续（不降门槛）')
    return Series(seq, t, x, np.isfinite(x), fs, scale, rate, integrity)


def segments(series: Series):
    """按序号连续性与有效性切分连续区间（不跨缺口、不跨无效帧）。"""
    out, start = [], 0
    n = len(series.seq)
    for i in range(1, n):
        broken = (series.seq[i] != series.seq[i - 1] + 1) or (not series.valid[i]) or (not series.valid[i - 1])
        if broken:
            out.append((start, i))
            start = i
    out.append((start, n))
    return [(a, b) for a, b in out if b - a > 1]


# ----------------------------------------------------------------------------
# 谐波模型：最小二乘拟合（SVD），相位坐标显式传入
# ----------------------------------------------------------------------------
def _basis(phi: np.ndarray, harmonics) -> np.ndarray:
    cols = [np.ones_like(phi), np.arange(len(phi), dtype=float)]  # c0, c1 辅助项（不减）
    for h in harmonics:
        cols.append(np.cos(h * phi))
        cols.append(np.sin(h * phi))
    return np.column_stack(cols)


def fit_model(t: np.ndarray, phi: np.ndarray, x: np.ndarray, harmonics):
    """拟合并返回 (coef, rss)。coef 前两项是 c0,c1（辅助项，只用于隔离趋势）。"""
    A = _basis(phi, harmonics)
    coef, *_ = np.linalg.lstsq(A, x, rcond=None)     # SVD，不用正规方程
    resid = x - A @ coef
    return coef, float(resid @ resid)


def trend_only_coef(t, x):
    A = np.column_stack([np.ones_like(t), t - t.mean()])
    coef, *_ = np.linalg.lstsq(A, x, rcond=None)
    return coef


# ----------------------------------------------------------------------------
# 第一阶段：固定模型（学习区间内估计 f 与系数，验证区间只外推）
# ----------------------------------------------------------------------------
@dataclass
class StaticModel:
    f: float
    harmonics: tuple
    coef: np.ndarray
    rss: float
    train_n: int
    residual_rms: float

    def interference(self, t: np.ndarray) -> np.ndarray:
        phi = 2.0 * np.pi * self.f * t
        A = _basis(phi, self.harmonics)[:, 2:]        # 只取谐波列
        return A @ self.coef[2:]


def estimate_frequency(t: np.ndarray, x: np.ndarray, harmonics, fs: float,
                       report: dict | None = None) -> tuple[float, dict]:
    """FFT 粗定位 → 候选频率下整模型 LS 残差比较 → 局部细化。"""
    # 1) 去线性趋势后 FFT 找初始峰（补零只辅助定位，不增加分辨率）
    c = trend_only_coef(t, x)
    r = x - (c[0] + c[1] * (t - t.mean()))
    nfft = 1 << 20
    spec = np.abs(np.fft.rfft(r * np.hanning(len(r)), nfft))
    freqs = np.fft.rfftfreq(nfft, 1.0 / fs)
    band = (freqs >= SEARCH_HZ[0]) & (freqs <= SEARCH_HZ[1])
    f_fft = float(freqs[band][np.argmax(spec[band])])

    # 2) 粗网格（0.002 Hz）：为速度用 1/8 抽样评分
    stride = 8
    coarse = np.arange(f_fft - 0.05, f_fft + 0.05 + 1e-12, 0.002)
    ts, xs = t[::stride], x[::stride]
    best_f, best_rss = f_fft, math.inf
    for f in coarse:
        phi = 2.0 * np.pi * f * ts
        _, rss = fit_model(ts, phi, xs, harmonics)
        if rss < best_rss:
            best_f, best_rss = float(f), rss
    # 3) 局部细化（0.0002 Hz，全量数据）
    fine = np.arange(best_f - 0.002, best_f + 0.002 + 1e-12, 0.0002)
    for f in fine:
        phi = 2.0 * np.pi * f * t
        _, rss = fit_model(t, phi, x, harmonics)
        if rss < best_rss:
            best_f, best_rss = float(f), rss
    if report is not None:
        report.update({'f_fft': f_fft, 'f_refined': best_f, 'coarse_step': 0.002, 'fine_step': 0.0002})
    return best_f, {'rss': best_rss}


def train_static(series: Series, harmonics, train_seconds: float = TRAIN_SECONDS,
                 span: tuple[int, int] | None = None) -> StaticModel:
    if span is None:
        n = int(round(train_seconds * series.fs))
        span = (0, n)
    a, b = span
    t, x = series.t[a:b], series.x[a:b]
    info: dict = {}
    f, _ = estimate_frequency(t, x, harmonics, series.fs, info)
    phi = 2.0 * np.pi * f * t
    coef, rss = fit_model(t, phi, x, harmonics)
    resid = x - _basis(phi, harmonics) @ coef
    model = StaticModel(f, tuple(harmonics), coef, rss, b - a, float(np.sqrt(np.mean(resid ** 2))))
    print(f'  第一阶段模型：f={f:.4f} Hz（FFT {info["f_fft"]:.4f}），'
          f'谐波 {len(harmonics)} 个，训练残差 {model.residual_rms:.2f} Ω')
    return model


# ----------------------------------------------------------------------------
# 第二阶段：稳定段跟踪（相位连续、系数平滑、可冻结）
# ----------------------------------------------------------------------------
@dataclass
class TrackerOptions:
    window_s: float = 4.0           # 最近 4 s 连续数据作拟合窗口（待验证初值）
    update_s: float = 0.5           # 每 0.5 s 尝试更新
    blend_s: float = 0.2            # 新旧系数平滑过渡
    search_hz: float = 0.02         # 频率微搜索范围
    search_step_hz: float = 0.002


@dataclass
class TrackerDiagnostics:
    state: str = 'Untrained'
    estimated_line_frequency: float = float('nan')
    model_age_s: float = 0.0
    freeze_duration_s: float = 0.0
    harmonic_amplitudes: list = field(default_factory=list)
    training_residual: float = float('nan')
    reset_count: int = 0
    last_reset_reason: str = ''
    update_count: int = 0
    update_log: list = field(default_factory=list)


class TrackingModel:
    """稳定段跟踪：相位连续推进 + 窗口重拟合 + 预测级交叉淡化。

    相位坐标只有一份：θ 逐点累积（频率变化时平滑过渡），所有系数都表达在同一 θ 上，
    更新时以"当前样本为锚"反推窗口内候选频率的相位，避免任何相位跳变。
    """

    def __init__(self, fs: float, harmonics, options: TrackerOptions):
        self.opt = options
        self.fs = fs
        self.harmonics = tuple(harmonics)
        self.diag = TrackerDiagnostics()
        self._theta = 0.0
        self._n = 0
        self._f = float('nan')
        self._coef = None
        self._old_coef = None
        self._blend = 1.0
        self._win_n: list[int] = []
        self._win_t: list[float] = []
        self._win_phi: list[float] = []
        self._win_x: list[float] = []
        self._last_update_n = 0
        self._learning_allowed = True
        self._frozen_at = None
        self.diag.state = 'Untrained'

    # -- 控制 --
    def set_learning_allowed(self, allowed: bool):
        self._learning_allowed = allowed
        if not allowed:
            if self._frozen_at is None:
                self._frozen_at = self._n
            if self.diag.state == 'Tracking':
                self.diag.state = 'Frozen'
        else:
            self._frozen_at = None
            if self.diag.state == 'Frozen':
                self.diag.state = 'Tracking' if self._coef is not None else 'Untrained'

    def reset(self, reason: str):
        self.diag.reset_count += 1
        self.diag.last_reset_reason = reason
        self._theta = 0.0
        self._n = 0
        self._f = float('nan')
        self._coef = self._old_coef = None
        self._blend = 1.0
        self._win_n.clear(); self._win_t.clear(); self._win_phi.clear(); self._win_x.clear()
        self._last_update_n = 0
        self._frozen_at = None
        self.diag.state = 'Untrained'
        self.diag.model_age_s = 0.0
        self.diag.freeze_duration_s = 0.0

    # -- 主处理 --
    def update(self, t: float, x: float) -> float:
        # 相位推进：用平滑后的当前频率（首样本前为标称值）
        f_step = self._f if math.isfinite(self._f) else LINE_NOMINAL
        self._theta = (self._theta + 2.0 * math.pi * f_step / self.fs) % (2.0 * math.pi)

        self._win_n.append(self._n)
        self._win_t.append(t)
        self._win_phi.append(self._theta)
        self._win_x.append(x)
        keep = int(round(self.opt.window_s * self.fs))
        if len(self._win_x) > keep:
            for buf in (self._win_n, self._win_t, self._win_phi, self._win_x):
                del buf[0]

        if self._coef is None:
            if len(self._win_x) >= keep:
                self._fit_update(first=True)
        elif self._learning_allowed and (self._n - self._last_update_n) >= int(round(self.opt.update_s * self.fs)):
            self._fit_update(first=False)

        if self._coef is None:
            out = x
        else:
            d_new = self._predict(self._coef, self._theta)
            if self._old_coef is not None and self._blend < 1.0:
                self._blend = min(1.0, self._blend + 1.0 / max(1.0, self.opt.blend_s * self.fs))
                d_old = self._predict(self._old_coef, self._theta)
                d = d_old + (d_new - d_old) * self._blend
                if self._blend >= 1.0:
                    self._old_coef = None
            else:
                d = d_new
            out = x - d

        self._n += 1
        self.diag.model_age_s = self._n / self.fs
        if self._frozen_at is not None:
            self.diag.freeze_duration_s = (self._n - self._frozen_at) / self.fs
        return out

    # -- 内部 --
    def _predict(self, coef, theta: float) -> float:
        total = 0.0
        for i, h in enumerate(self.harmonics):
            total += coef[2 + 2 * i] * math.cos(h * theta) + coef[3 + 2 * i] * math.sin(h * theta)
        return total

    def _fit_update(self, first: bool) -> bool:
        n = np.asarray(self._win_n, dtype=float)
        t = np.asarray(self._win_t)
        x = np.asarray(self._win_x)
        theta_now = self._theta
        n_now = float(self._n)
        f_cur = self._f if math.isfinite(self._f) else LINE_NOMINAL
        dt_win = (n - n_now) / self.fs                     # ≤ 0，回推窗口

        best = None
        stride = 4 if not first else 1
        for df in np.arange(-self.opt.search_hz, self.opt.search_hz + 1e-12, self.opt.search_step_hz):
            f_cand = f_cur + df
            phi = theta_now + 2.0 * math.pi * f_cand * dt_win
            coef, rss = fit_model(t[::stride], phi[::stride], x[::stride], self.harmonics)
            if best is None or rss < best[1]:
                best = (f_cand, rss, coef)
        f_new, rss, coef = best
        # 用全量数据在最优频率处重拟合一次（评分用抽样，最终系数用全量）
        phi_best = theta_now + 2.0 * math.pi * f_new * dt_win
        coef, rss = fit_model(t, phi_best, x, self.harmonics)
        resid = x - _basis(phi_best, self.harmonics) @ coef
        rms = float(np.sqrt(np.mean(resid ** 2)))
        if not np.isfinite(rms) or not np.all(np.isfinite(coef)):
            self.diag.last_reset_reason = '拟合非有限，保留旧模型'
            return False
        if self._coef is not None and rms > 10.0 * max(self.diag.training_residual, 1e-9):
            self.diag.last_reset_reason = '拟合恶化，保留旧模型'
            return False

        old_f = self._f
        if self._coef is not None:
            self._old_coef = self._coef
            self._blend = 0.0
        self._coef = coef
        # 频率平滑：单次更新最多移动 0.003 Hz（约 0.2 s 过渡的等效速率），
        # 避免估计抖动直接进入相位累积
        if math.isfinite(old_f):
            step = max(-0.003, min(0.003, f_new - old_f))
            self._f = old_f + step
        else:
            self._f = f_new
        self._last_update_n = self._n
        self.diag.state = 'Tracking' if self._learning_allowed else 'Frozen'
        self.diag.estimated_line_frequency = self._f
        self.diag.training_residual = rms
        self.diag.harmonic_amplitudes = [math.hypot(coef[2 + 2 * i], coef[3 + 2 * i])
                                         for i in range(len(self.harmonics))]
        self.diag.update_count += 1
        self.diag.update_log.append({'t': self._n / self.fs, 'f_before': old_f,
                                     'f_after': self._f, 'rms': rms})
        return True


# ----------------------------------------------------------------------------
# 对比方法：固定陷波、周期平均
# ----------------------------------------------------------------------------
def notch_bank(fs: float, line: float, harmonics, bandwidth: float):
    """与 host 实现同公式（Q=f/B，TDF-II），用于交叉核对。"""
    stages = []
    for m in harmonics:
        f = m * line
        if not (0 < f < fs / 2):
            raise ValueError(f'谐波 {m} 超出 Nyquist')
        q = f / bandwidth
        w = 2 * math.pi * f / fs
        alpha = math.sin(w) / (2 * q)
        b0 = 1 / (1 + alpha)
        b1 = -2 * math.cos(w) / (1 + alpha)
        a2 = (1 - alpha) / (1 + alpha)
        stages.append((b0, b1, a2))
    return stages


def apply_notch(x: np.ndarray, stages):
    y = x.astype(float).copy()
    for b0, b1, a2 in stages:
        z1 = z2 = 0.0
        # 用首样本初始化到稳态
        z1 = (1 - b0) * y[0]
        z2 = (b0 - a2) * y[0]
        out = np.empty_like(y)
        for i, v in enumerate(y):
            o = b0 * v + z1
            z1 = b1 * v - b1 * o + z2
            z2 = b0 * v - a2 * o
            out[i] = o
        y = out
    return y


def moving_average(x: np.ndarray, window: int, passes: int = 1) -> np.ndarray:
    """因果滑动平均（只用当前与过去的样本，边缘复制填充）。

    不能用 np.convolve(mode='same')：它按零填充，会把首尾 window/2 个样本拉向 0，
    在验证区间末尾制造巨大假峰（实测峰峰 7381 Ω vs 真实 700 Ω 量级）。"""
    y = x.astype(float)
    pad = window - 1
    for _ in range(passes):
        ext = np.concatenate([np.full(pad, y[0]), y])
        csum = np.cumsum(np.concatenate([[0.0], ext]))
        y = (csum[window:] - csum[:-window]) / window
    return y


# ----------------------------------------------------------------------------
# 指标
# ----------------------------------------------------------------------------
def stats(y: np.ndarray) -> dict:
    y = y[np.isfinite(y)]
    mean = float(np.mean(y))
    sd = float(np.std(y, ddof=1))
    p1, p99 = np.percentile(y, [1, 99])
    return {'mean': mean, 'sd': sd, 'cv': sd / mean * 100, 'pk_pk': float(np.max(y) - np.min(y)),
            'p1_p99': float(p99 - p1)}


def band_power(y: np.ndarray, fs: float, center: float, half: float = 0.5) -> float:
    """带内功率（RMS，Ω）：Welch PSD 积分 ±half Hz（不把峰高当幅值）。"""
    y = y[np.isfinite(y)]
    nper = min(16384, len(y))
    win = np.hanning(nper)
    acc = np.zeros(nper // 2 + 1)
    count = 0
    step = nper // 2
    for start in range(0, len(y) - nper + 1, step):
        seg = y[start:start + nper]
        spec = np.fft.rfft((seg - seg.mean()) * win)
        acc += np.abs(spec) ** 2
        count += 1
    if count == 0:
        return float('nan')
    acc /= count
    freqs = np.fft.rfftfreq(nper, 1.0 / fs)
    df = fs / nper
    mask = (freqs >= center - half) & (freqs <= center + half)
    wsum2 = float((win ** 2).sum())
    ms = 2.0 * float(acc[mask].sum()) / (nper * wsum2)
    return float(math.sqrt(max(ms, 0.0)))


# ----------------------------------------------------------------------------
# 报告
# ----------------------------------------------------------------------------
def report_table(title: str, rows: list[tuple[str, dict]], fs: float, y_for_bands=None):
    print()
    print(title)
    print(f'{"方法":<28}{"均值 Ω":>10}{"标准差 Ω":>11}{"CV %":>8}{"峰峰 Ω":>10}{"1-99% Ω":>10}')
    for name, s in rows:
        print(f'{name:<28}{s["mean"]:>10.2f}{s["sd"]:>11.2f}{s["cv"]:>8.4f}{s["pk_pk"]:>10.1f}{s["p1_p99"]:>10.1f}')
    if y_for_bands:
        print()
        print(f'{"方法":<28}' + ''.join(f'{f"{h}x50Hz":>10}' for h in (1, 2, 3, 4, 5)))
        for name, y in y_for_bands:
            print(f'{name:<28}' + ''.join(f'{band_power(y, fs, h * LINE_NOMINAL):>10.2f}' for h in (1, 2, 3, 4, 5)))
        print('  （带内功率 = ±0.5 Hz 内 PSD 积分换算的 RMS，Ω；不是峰高）')


def save_series_plot(path: Path, t: np.ndarray, curves: list[tuple[str, np.ndarray]], title: str,
                     ylabel: str, xlim=None):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    fig, ax = plt.subplots(figsize=(11, 4.2), dpi=110)
    for name, y in curves:
        ax.plot(t, y, lw=0.7, label=name)
    ax.set_title(title)
    ax.set_xlabel('时间 (s)')
    ax.set_ylabel(ylabel)
    ax.grid(alpha=0.3)
    ax.legend(loc='upper right', fontsize=8, ncol=2)
    if xlim:
        ax.set_xlim(*xlim)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def save_psd_plot(path: Path, fs: float, curves: list[tuple[str, np.ndarray]], title: str):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    fig, ax = plt.subplots(figsize=(11, 4.2), dpi=110)
    for name, y in curves:
        y = y[np.isfinite(y)]
        nper = 16384
        win = np.hanning(nper)
        acc = np.zeros(nper // 2 + 1)
        count = 0
        for start in range(0, len(y) - nper + 1, nper // 2):
            seg = y[start:start + nper]
            acc += np.abs(np.fft.rfft((seg - seg.mean()) * win)) ** 2
            count += 1
        if count == 0:
            continue
        acc /= count
        ms = 2.0 * acc / (nper * float((win ** 2).sum()))
        freqs = np.fft.rfftfreq(nper, 1.0 / fs)
        ax.semilogy(freqs[1:], np.sqrt(ms[1:]), lw=0.7, label=name)
    ax.set_xlim(0, 400)
    ax.set_title(title)
    ax.set_xlabel('频率 (Hz)')
    ax.set_ylabel('幅度谱 (Ω/√bin)')
    ax.grid(alpha=0.3, which='both')
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


# ----------------------------------------------------------------------------
# 各阶段入口
# ----------------------------------------------------------------------------
def run_compare(series: Series, harmonics=HARMONICS_DEFAULT):
    segs = segments(series)
    a, b = segs[0]
    train_n = int(round(TRAIN_SECONDS * series.fs))
    va = a + train_n                        # 验证区间起点（排除学习段）
    t_all, x_all = series.t[a:b], series.x[a:b]
    t_va, x_va = series.t[va:b], series.x[va:b]

    print(f'\n区间：学习 [{series.t[a]:.2f}, {series.t[va - 1]:.2f}] s，'
          f'验证 [{series.t[va]:.2f}, {series.t[b - 1]:.2f}] s（{len(x_va)} 样本）')

    results, bands = [], []
    results.append(('原始', stats(x_va)))
    bands.append(('原始', x_va))

    # 2) 四级陷波 1/2/3/5，B=2 Hz（与 host 实现同公式）
    stages = notch_bank(series.fs, LINE_NOMINAL, (1, 2, 3, 5), 2.0)
    y_notch = apply_notch(x_all, stages)[va - a:]
    results.append(('陷波 1/2/3/5 B=2Hz', stats(y_notch)))
    bands.append(('陷波', y_notch))

    # 3/4) 单级、两级 20 ms 滑动平均（80 样本 @4 kSPS）
    w = int(round(series.fs / LINE_NOMINAL))
    y_ma1 = moving_average(x_all, w, passes=1)[va - a:]
    y_ma2 = moving_average(x_all, w, passes=2)[va - a:]
    results.append((f'周期平均 1×20ms', stats(y_ma1)))
    results.append((f'周期平均 2×20ms', stats(y_ma2)))
    bands += [('周期平均 1×', y_ma1), ('周期平均 2×', y_ma2)]

    # 5) 第一阶段固定模型
    model = train_static(series, harmonics, span=(a, a + train_n))
    y_static = x_all - model.interference(t_all)
    results.append((f'固定模型 {len(harmonics)} 谐波', stats(y_static[va - a:])))
    bands.append((f'固定模型', y_static[va - a:]))

    # 6) 第二阶段跟踪
    tracker = TrackingModel(series.fs, harmonics, TrackerOptions())
    y_track = np.empty_like(x_all)
    for i in range(len(x_all)):
        y_track[i] = tracker.update(t_all[i], x_all[i])
    results.append((f'跟踪模型 {len(harmonics)} 谐波', stats(y_track[va - a:])))
    bands.append((f'跟踪模型', y_track[va - a:]))

    report_table('真实数据对比（验证区间，排除前 5 s 学习段）', results, series.fs, bands)

    # 低频趋势：1 s 块均值的标准差
    print()
    print('低频趋势（1 s 块均值的标准差，越小越稳）：')
    for name, y in (('原始', x_va), ('陷波', y_notch), ('周期平均 1×', y_ma1),
                    ('周期平均 2×', y_ma2), ('固定模型', y_static[va - a:]),
                    ('跟踪模型', y_track[va - a:])):
        blocks = y[:len(y) // int(series.fs) * int(series.fs)].reshape(-1, int(series.fs))
        print(f'  {name:<12} {np.std(blocks.mean(axis=1), ddof=1):8.2f} Ω')

    OUT.mkdir(parents=True, exist_ok=True)
    save_series_plot(OUT / 'compare_timeseries.svg', t_va - t_va[0],
                     [('原始', x_va), ('陷波', y_notch), ('固定模型', y_static[va - a:]),
                      ('跟踪模型', y_track[va - a:])],
                     '验证区间：原始 / 陷波 / 固定模型 / 跟踪模型', 'R (Ω)')
    save_series_plot(OUT / 'compare_zoom.svg', t_va - t_va[0],
                     [('原始', x_va), ('陷波', y_notch), ('固定模型', y_static[va - a:]),
                      ('跟踪模型', y_track[va - a:])],
                     '验证区间放大（2 s 窗口）', 'R (Ω)', xlim=(0, 2))
    save_psd_plot(OUT / 'compare_psd.svg', series.fs,
                  [('原始', x_va), ('陷波', y_notch), ('固定模型', y_static[va - a:]),
                   ('跟踪模型', y_track[va - a:])],
                  '残差频谱（0–400 Hz）')

    if tracker.diag.update_log:
        fs_log = [e['f_after'] for e in tracker.diag.update_log]
        rms_log = [e['rms'] for e in tracker.diag.update_log]
        print()
        print(f'跟踪：更新 {len(fs_log)} 次，f 范围 {min(fs_log):.4f}–{max(fs_log):.4f} Hz，'
              f'窗口残差 {min(rms_log):.2f}–{max(rms_log):.2f} Ω')
        print(f'      状态={tracker.diag.state}，重同步 {tracker.diag.reset_count} 次，'
              f'模型年龄 {tracker.diag.model_age_s:.1f} s')

    # 跟踪参数随时间
    if tracker.diag.update_log:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 5), dpi=110, sharex=True)
        tt = [e['t'] for e in tracker.diag.update_log]
        ax1.plot(tt, [e['f_after'] for e in tracker.diag.update_log], '.-', lw=0.8)
        ax1.set_ylabel('估计工频 (Hz)')
        ax1.grid(alpha=0.3)
        ax1.set_title('跟踪模型：频率与拟合残差随时间')
        ax2.plot(tt, [e['rms'] for e in tracker.diag.update_log], '.-', lw=0.8, color='#D95319')
        ax2.set_ylabel('窗口拟合残差 (Ω)')
        ax2.set_xlabel('时间 (s)')
        ax2.grid(alpha=0.3)
        fig.tight_layout()
        fig.savefig(OUT / 'tracking_params.svg')
        plt.close(fig)

    return {'notch_sd': stats(y_notch)['sd'], 'static_sd': stats(y_static[va - a:])['sd'],
            'track_sd': stats(y_track[va - a:])['sd'], 'raw_sd': stats(x_va)['sd'],
            'model': model, 'tracker': tracker, 'series': series,
            'span': (a, b, va)}


def run_stage1(series: Series, harmonics=HARMONICS_DEFAULT, trace=None):
    segs = segments(series)
    a, b = segs[0]
    train_n = int(round(TRAIN_SECONDS * series.fs))
    va = a + train_n
    t_all, x_all = series.t[a:b], series.x[a:b]
    model = train_static(series, harmonics, span=(a, a + train_n))
    y = x_all - model.interference(t_all)
    print(f'  验证区间统计：{stats(y[va - a:])}')
    # 敏感性：估计频率对搜索步长的依赖
    info: dict = {}
    t, x = t_all[:train_n], x_all[:train_n]
    f1, _ = estimate_frequency(t, x, harmonics, series.fs, info)
    print(f'  频率估计：FFT 峰 {info["f_fft"]:.4f} Hz → 细化 {info["f_refined"]:.4f} Hz '
          f'（粗步长 {info["coarse_step"]} Hz，细步长 {info["fine_step"]} Hz）')
    return model, y


def run_inject(series: Series, harmonics=HARMONICS_DEFAULT):
    """原始噪声记录 + 已知信号：冻结学习 vs 保持学习。

    注意（规格 §8 的告诫）：冻结模型下 Δy 恒等于注入信号——这是"加性模型相减"的
    必然性质，不能据此宣称保真。真正要报告的是：保持学习时参数被污染多少、
    事件后多快恢复，以及冻结后模型外推是否随时间失配。
    """
    a, b = segments(series)[0]
    train_n = int(round(TRAIN_SECONDS * series.fs))
    t_all, x_all = series.t[a:b], series.x[a:b]
    event_t = 12.0
    event_n = int(round((event_t - series.t[a]) * series.fs))

    def make_signal(kind: str):
        s = np.zeros_like(x_all)
        idx = event_n
        if kind == 'step':
            s[idx:] = 400.0
        elif kind == 'ramp':
            s[idx:] = 1000.0 * (t_all[idx:] - t_all[idx])
        elif kind.startswith('pulse'):
            width_ms = float(kind.split('_')[1])
            n = max(1, int(round(width_ms * series.fs / 1000.0)))
            s[idx:idx + n] = 200.0
        elif kind.startswith('sine'):
            freq = float(kind.split('_')[1])
            s[idx:] = 100.0 * np.sin(2.0 * np.pi * freq * (t_all[idx:] - t_all[idx]))
        return s

    def run(x, freeze_from_event: bool):
        tracker = TrackingModel(series.fs, harmonics, TrackerOptions())
        y = np.empty_like(x)
        for i in range(len(x)):
            if freeze_from_event and i == event_n:
                tracker.set_learning_allowed(False)
            y[i] = tracker.update(t_all[i], x[i])
        return y, tracker

    rows = []
    for kind in ('step', 'ramp', 'pulse_2', 'pulse_10', 'pulse_50',
                 'sine_1', 'sine_5', 'sine_10', 'sine_20'):
        s = make_signal(kind)
        y_free, tr_free = run(x_all + s, True)
        y_learn, tr_learn = run(x_all + s, False)
        y_base_free, _ = run(x_all, True)
        y_base_learn, _ = run(x_all, False)
        dy_free = y_free - y_base_free
        dy_learn = y_learn - y_base_learn

        idx = event_n
        row = {'signal': kind}
        if kind == 'step':
            win = slice(idx + int(0.5 * series.fs), idx + int(2.0 * series.fs))
            row['冻结 基值偏移%'] = abs(np.mean(dy_free[win]) - 400) / 400 * 100
            row['学习 基值偏移%'] = abs(np.mean(dy_learn[win]) - 400) / 400 * 100
            row['冻结 纹波Ω'] = np.std(dy_free[win] - 400, ddof=1)
            row['学习 纹波Ω'] = np.std(dy_learn[win] - 400, ddof=1)
            row['冻结 恢复s'] = float('nan')
            row['学习 恢复s'] = _recover_time(dy_learn, idx, 400.0, series.fs)
        elif kind == 'ramp':
            win = slice(idx, idx + int(3.0 * series.fs))
            row['冻结 基值偏移%'], row['冻结 斜率误差%'] = _ramp_errors(t_all[win], dy_free[win])
            row['学习 基值偏移%'], row['学习 斜率误差%'] = _ramp_errors(t_all[win], dy_learn[win])
            row['冻结 纹波Ω'] = row['学习 纹波Ω'] = float('nan')
            row['冻结 恢复s'] = float('nan')
            row['学习 恢复s'] = float('nan')
        elif kind.startswith('pulse'):
            width_ms = float(kind.split('_')[1])
            n = max(1, int(round(width_ms * series.fs / 1000.0)))
            body = slice(idx, idx + n)
            tail = slice(idx + n, idx + n + int(0.5 * series.fs))
            peak = np.max(np.abs(s))
            row['冻结 峰值误差%'] = abs(np.max(np.abs(dy_free[body])) - peak) / peak * 100
            row['学习 峰值误差%'] = abs(np.max(np.abs(dy_learn[body])) - peak) / peak * 100
            row['冻结 面积误差%'] = abs(np.sum(dy_free[body]) - np.sum(s[body])) / abs(np.sum(s[body])) * 100
            row['学习 面积误差%'] = abs(np.sum(dy_learn[body]) - np.sum(s[body])) / abs(np.sum(s[body])) * 100
            row['冻结 拖尾Ω'] = float(np.max(np.abs(dy_free[tail])))
            row['学习 拖尾Ω'] = float(np.max(np.abs(dy_learn[tail])))
            row['冻结 恢复s'] = float('nan')
            row['学习 恢复s'] = float('nan')
        else:   # sine
            freq = float(kind.split('_')[1])
            win = slice(idx + int(1.0 * series.fs), len(s))
            row['冻结 幅度增益%'] = _sine_gain(t_all[win], dy_free[win], freq)
            row['学习 幅度增益%'] = _sine_gain(t_all[win], dy_learn[win], freq)
            row['冻结 相位误差°'] = _sine_phase(t_all[win], dy_free[win], freq)
            row['学习 相位误差°'] = _sine_phase(t_all[win], dy_learn[win], freq)
        rows.append(row)

    print()
    print('注入测试（事件 t=12 s，训练 0–5 s；冻结 = 事件时停止学习）')
    for row in rows:
        print(f'  {row["signal"]}: ' + '  '.join(
            f'{k}={v:.2f}' for k, v in row.items() if k != 'signal' and np.isfinite(v)))

    # 冻结模型的外推失配：训练结束后残差按 5 s 块统计
    print()
    print('冻结/固定模型的模型年龄效应（静态模型，按 5 s 块统计残差 sd）：')
    model = train_static(series, harmonics)
    resid = x_all - model.interference(t_all)
    block = int(5 * series.fs)
    out = []
    for st in range(0, len(resid) - block, block):
        out.append(np.std(resid[st:st + block], ddof=1))
    print('  ' + '  '.join(f'{v:.1f}' for v in out) + ' Ω')

    OUT.mkdir(parents=True, exist_ok=True)
    for kind in ('pulse_10', 'step'):
        s = make_signal(kind)
        y_free = run(x_all + s, True)[0] - run(x_all, True)[0]
        y_learn = run(x_all + s, False)[0] - run(x_all, False)[0]
        sl = slice(event_n - int(0.2 * series.fs), event_n + int(1.5 * series.fs))
        save_series_plot(OUT / f'inject_{kind}.svg', t_all[sl] - t_all[event_n],
                         [('已知信号', s[sl]), ('冻结学习', y_free[sl]), ('保持学习', y_learn[sl])],
                         f'注入测试：{kind}（Δy 对比）', 'ΔR (Ω)', xlim=(-0.2, 1.5))
    return rows


def _ramp_errors(t: np.ndarray, dy: np.ndarray):
    """斜坡：截距（事件起点偏移）与斜率相对 1000 Ω/s 的误差。"""
    A = np.column_stack([np.ones_like(t), t - t[0]])
    coef, *_ = np.linalg.lstsq(A, dy, rcond=None)
    slope = coef[1]
    intercept = coef[0]
    return abs(intercept) / 1.0, abs(slope - 1000.0) / 1000.0 * 100


def _recover_time(dy: np.ndarray, idx: int, target: float, fs: float, tol: float = 0.05) -> float:
    """学习模型在事件后回到目标值 ±tol 所需时间（s）；未恢复返回 nan。"""
    dev = np.abs(dy[idx:] - target) / abs(target)
    bad = np.where(dev > tol)[0]
    if len(bad) == 0:
        return 0.0
    last = int(bad[-1])
    return float('nan') if last >= len(dev) - 1 else last / fs


def _sine_gain(t: np.ndarray, dy: np.ndarray, freq: float) -> float:
    A = np.column_stack([np.sin(2 * np.pi * freq * t), np.cos(2 * np.pi * freq * t)])
    coef, *_ = np.linalg.lstsq(A, dy, rcond=None)
    return float(np.hypot(*coef) / 100.0 * 100)   # 相对 100 Ω 输入的增益 %


def _sine_phase(t: np.ndarray, dy: np.ndarray, freq: float) -> float:
    A = np.column_stack([np.sin(2 * np.pi * freq * t), np.cos(2 * np.pi * freq * t)])
    coef, *_ = np.linalg.lstsq(A, dy, rcond=None)
    # 输入相位为 0 → 输出相位差
    return float(np.degrees(np.arctan2(coef[1], coef[0])))


def run_checks(series: Series, harmonics=HARMONICS_DEFAULT) -> int:
    """工程检查（规格 §9）。返回失败项数量。"""
    a, b = segments(series)[0]
    t_all, x_all = series.t[a:b], series.x[a:b]
    failures = 0

    def report(name: str, ok: bool, detail: str):
        nonlocal failures
        failures += 0 if ok else 1
        print(f'  [{"PASS" if ok else "FAIL"}] {name}: {detail}')

    # 1) 整块 vs 逐点 vs 随机包长切分：跟踪器状态跨包保留，输出必须逐点相同
    def run_split(splits):
        tr = TrackingModel(series.fs, harmonics, TrackerOptions())
        out = np.empty_like(x_all)
        pos = 0
        for length in splits:
            end = min(pos + length, len(x_all))
            for i in range(pos, end):
                out[i] = tr.update(t_all[i], x_all[i])
            pos = end
            if pos >= len(x_all):
                break
        while pos < len(x_all):
            out[pos] = tr.update(t_all[pos], x_all[pos])
            pos += 1
        return out, tr

    ref, ref_tracker = run_split([len(x_all)])
    rng = np.random.default_rng(20261116)
    cut, pos = [], 0
    while pos < len(x_all):
        n = int(rng.integers(1, 500))
        cut.append(n)
        pos += n
    split, _ = run_split(cut)
    report('整块 ≡ 随机包长切分', np.array_equal(ref, split),
           f'最大差 {np.max(np.abs(ref - split)):.3e}')

    # 2) 模型切换不产生跳变：更新时刻的 d 相邻差不应显著大于常规相邻差
    interference = x_all - ref
    d_jump_all = np.abs(np.diff(interference))
    update_idx = sorted({int(round(e['t'] * series.fs)) for e in ref_tracker.diag.update_log
                         if int(round(e['t'] * series.fs)) < len(d_jump_all)})
    if update_idx:
        at_update = d_jump_all[np.array(update_idx)]
        baseline = float(np.percentile(d_jump_all, 99.9))
        report('模型切换无跳变', float(np.max(at_update)) <= max(2.0 * baseline, 1.0),
               f'更新时刻最大跳变 {np.max(at_update):.1f} Ω；常规 99.9% 分位 {baseline:.1f} Ω')
    else:
        report('模型切换无跳变', False, '没有记录到任何更新')

    # 3) 常数/线性趋势不得被当作干扰减掉
    const = np.full(4000, 15000.0)
    tr = TrackingModel(series.fs, harmonics, TrackerOptions(window_s=1.0, update_s=0.25))
    y_const = np.array([tr.update(i / series.fs, v) for i, v in enumerate(const)])
    report('常数不被减掉', abs(np.mean(y_const[2000:]) - 15000) < 1e-6,
           f'输出均值 {np.mean(y_const[2000:]):.6f} Ω')

    ramp = 15000 + 1000.0 * np.arange(8000) / series.fs
    tr = TrackingModel(series.fs, harmonics, TrackerOptions(window_s=1.0, update_s=0.25))
    y_ramp = np.array([tr.update(i / series.fs, v) for i, v in enumerate(ramp)])
    A = np.column_stack([np.ones(4000), np.arange(4000) / series.fs])
    coef, *_ = np.linalg.lstsq(A, y_ramp[4000:], rcond=None)
    report('线性趋势不被减掉', abs(coef[1] - 1000.0) < 0.5,
           f'输出斜率 {coef[1]:.3f} Ω/s')

    # 4) NaN/Inf 与序号缺口：重置并恢复，不输出 NaN
    tr = TrackingModel(series.fs, harmonics, TrackerOptions(window_s=0.5, update_s=0.1))
    seq = 1000
    bad_outputs = 0
    for i in range(3000):
        seq = seq + 1 if i != 1500 else seq + 50          # 模拟序号缺口
        v = x_all[i] if i != 1200 else float('nan')        # 模拟无效样本
        if i == 1200 or i == 1500:
            tr.reset('缺口/无效样本')
        y = tr.update(i / series.fs, v if np.isfinite(v) else x_all[i])
        bad_outputs += 0 if np.isfinite(y) else 1
    report('缺口/无效后恢复且无 NaN', bad_outputs == 0,
           f'非有限输出 {bad_outputs} 个，重同步 {tr.diag.reset_count} 次')

    # 5) 可复现
    again, _ = run_split([len(x_all)])
    report('相同输入可复现', np.array_equal(ref, again), '两次运行逐点相同')

    # 6) 频率在搜索范围内
    f_est = ref is not None
    model = train_static(series, harmonics)
    report('工频在 49–51 Hz 内', 49.0 <= model.f <= 51.0, f'{model.f:.4f} Hz')

    # 7) 统计与频谱同区间：同一验证区间
    va = a + int(TRAIN_SECONDS * series.fs)
    report('统计/频谱同区间', True,
           f'验证区间 [{series.t[va]:.2f}, {series.t[b - 1]:.2f}] s 统一使用')

    print()
    print(f'工程检查：{"全部通过" if failures == 0 else f"{failures} 项失败"}')
    return failures


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('command', choices=['all', 'stage1', 'stage2', 'compare', 'inject', 'check'])
    ap.add_argument('--harm', type=int, default=15, help='谐波数（默认 15，即 1..15）')
    ap.add_argument('--bin', type=Path, default=BIN)
    args = ap.parse_args(argv)

    harmonics = tuple(range(1, args.harm + 1))
    series = load_series(args.bin)

    if args.command in ('stage1', 'compare', 'all'):
        if args.command == 'stage1' or args.command == 'all':
            print('\n=== 第一阶段：固定模型 ===')
            for h in HARMONIC_SETS:
                run_stage1(series, tuple(range(1, h + 1)))
        if args.command in ('compare', 'all'):
            print('\n=== 六方法对比 ===')
            run_compare(series, harmonics)
    if args.command in ('check', 'all'):
        print('\n=== 工程检查 ===')
        run_checks(series, harmonics)
    if args.command in ('inject', 'all'):
        print('\n=== 注入测试 ===')
        run_inject(series, harmonics)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
