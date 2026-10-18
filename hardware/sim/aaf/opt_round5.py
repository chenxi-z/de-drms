# -*- coding: utf-8 -*-
"""opt_round5.py — Round 5 抗混叠采集阶梯：十维理论预测 + Nelder-Mead 多起点求解

规格：docs/design/spec/2026-10-18-aa-driver-design.md（v4：§5 十维评分 / §4 架构 / §5.2 硬约束）
计划：docs/design/spec/2026-10-18-aa-driver-plan.md（Task 2 / Task 3）

把规格 §5.1 的 D1–D10 全部落到**理论预测**（不含 LTspice）：
  D1 A_dm@fMOD   D2 A_cm@fMOD   D3 A_dm@MCLK   D4 通带平坦度@16k   D5 容差最坏角建立
  D6 积分噪声    D7 容差敏感度    D8 CMRR@通带    D9 kickback 回稳   D10 群延迟平坦度

单位纪律（前战役踩过的坑，写成硬规则）：
  * ``opt_engine.settle_time()`` 返回 **秒**；与 µs 预算（500/900 µs）比较前**必须 ×1e6**。
  * ``predict()["t_settle_wc_s"]`` 与 ``group_delay_flat_s`` 保持 **秒**（引擎口径）；
    ``dim_scores()`` 内部统一换算后再与 µs 阈值比较。
  * LSB = 2 × 2.442 V / 2**24 = 290.98 nV（规格 §5.1 单位约定）。

新约束（规格 §3 + 计划 Task 2 Step 3）：fc ∈ [50 kHz, 80 kHz]（DM −3 dB 整体拐点，
由 16 kHz 平坦度 ≤0.5 dB 反推）；ΣR ≤5 kΩ；单电容 ≤100 nF；settle_wc ≤900 µs；ΔG@16k ≤0.5 dB。

拓扑（规格 §4 定稿）：每线 R_i + 对地 C_gnd,i 串联成阶梯；两线**末级**之间跨接 C_diff
（差分电容只允许出现在最后一级，落到引擎里即 ``stages[-1][2] = C_diff``）。

理论不可直接测的两维按计划用代理：
  D6 —— 对全部电阻（源内阻 + 各级 R + 130 kΩ 差分负载）做约翰逊噪声的完整 MNA 积分
        （比计划里"末级 R 约翰逊噪声"更严格，是它的超集）；
  D9 —— 采样电荷分享代理：τ_kb = (R_sw + R_last)·C_S 对比 fMOD 半周期 122 ns，
        外加电荷桶 droop = C_S/(C_S + C_pin)。
"""

from __future__ import annotations

import argparse
import json
import math
import os

import numpy as np
from scipy.optimize import minimize

from opt_engine import ladder_matrices

HERE = os.path.dirname(os.path.abspath(__file__))
FACTS_MD = os.path.join(HERE, "r5_datasheet_facts.md")

# ----------------------------------------------------------------------------
# 0. FACTS —— Task 1 的手册核实值（r5_datasheet_facts.md §1 python 代码块）
# ----------------------------------------------------------------------------

_FALLBACK_FACTS = {
    "MCLK_HZ": 16.384e6,
    "FMOD_HZ": 4.096e6,
    "FDATA_HZ": 128e3,
    "OSR": 32,
    "SINC3_F3DB_HZ": 33790.0,
    "SINC3_ATT_16K_DB": -0.67,
    "ADC_CS_PF": 3.5,
    "ADC_ZIN_OHM": 130e3,
    "ADC_RSW_OHM": None,
    "ADC_RSW_ASSUMPTION_OHM": 1.0,
    "ADC_SW_DUTY": 0.5,
    "ADC_SW_FREQ_HZ": 4.096e6,
    "OPA388_AOL_4M_DB": 7.0,
    "OPA388_GBW_HZ": 10e6,
}


def load_facts(path: str = FACTS_MD) -> dict:
    """从 Task 1 的 r5_datasheet_facts.md 抽出 FACTS 字典（缺失则回退同值副本）。"""
    facts = dict(_FALLBACK_FACTS)
    try:
        text = open(path, encoding="utf-8").read()
    except OSError:
        return facts
    i = text.find("```python")
    if i < 0:
        return facts
    j = text.find("```", i + 9)
    if j < 0:
        return facts
    ns: dict = {}
    try:
        exec(text[i + 9:j], ns)  # noqa: S102 —— 本仓库自有文档
    except Exception:
        return facts
    blk = ns.get("FACTS")
    if isinstance(blk, dict):
        facts.update(blk)
    return facts


FACTS = load_facts()

FMOD_HZ = float(FACTS["FMOD_HZ"])                 # 4.096 MHz
MCLK_HZ = float(FACTS["MCLK_HZ"])                 # 16.384 MHz
ADC_CS_F = float(FACTS["ADC_CS_PF"]) * 1e-12      # 3.5 pF（差分）
ADC_RSW = float(FACTS["ADC_RSW_ASSUMPTION_OHM"])  # 1 Ω（手册未给，规格 §7 缺省）
ADC_ZIN = float(FACTS["ADC_ZIN_OHM"])             # 130 kΩ 差分

LSB_V = 2.0 * 2.442 / 2 ** 24            # 290.98 nV（规格 §5.1）
K_B = 1.380649e-23
T_K = 298.15
R_SUM_MAX = 5e3
C_MAX = 100e-9
FC_LO, FC_HI = 50e3, 80e3
SETTLE_BUDGET_US = 900.0
SETTLE_BAND_V = 60e-6                     # 0.01% 建立带（单边；差分 2.4 Vpp → 120 µV）
DG_MAX_DB = 0.5                           # 通带平坦度硬门槛（D4 及格线）
KB_HALF_PERIOD_S = 0.5 / FMOD_HZ          # 122.07 ns

# 规格 §5.1 阈值（满分, 及格线）；D9 为二值维度
TH = {
    "D1": (120.0, 80.0), "D2": (100.0, 60.0), "D3": (150.0, 100.0),
    "D4": (0.05, 0.50), "D5": (500.0, 900.0), "D6": (0.3, 1.0),
    "D7": (0.01, 0.05), "D8": (100.0, 80.0), "D10": (1.0, 5.0),
}


# ----------------------------------------------------------------------------
# 1. 基础量测（向量化，与 opt_engine.H 逐点等价；test 里断言）
# ----------------------------------------------------------------------------

def h_vec(stages, mode: str, freqs, tol_r: float = 0.0, tol_c: float = 0.0) -> np.ndarray:
    """批量传函：一次 MNA 分解，对整组频率求复数响应（输出 = 引脚节点）。"""
    G, Cm, b = ladder_matrices(stages, mode, tol_r, tol_c)
    w = 2 * math.pi * np.atleast_1d(np.asarray(freqs, dtype=float))
    A = G[None, :, :] + 1j * w[:, None, None] * Cm[None, :, :]
    rhs = np.broadcast_to(b[None, :], (len(w), G.shape[0]))
    v = np.linalg.solve(A, rhs[:, :, None])[:, :, 0]
    return v[:, -1]


def gain_db(stages, mode: str, f, tol_r: float = 0.0, tol_c: float = 0.0):
    """相对 DC（0.1 Hz）增益，dB；f 可为标量或数组。"""
    vals = h_vec(stages, mode, f, tol_r, tol_c) / h_vec(stages, mode, 0.1)[0]
    db = 20 * np.log10(np.abs(vals))
    return float(db[0]) if np.ndim(f) == 0 else db


def fc_dm(stages, n_iter: int = 46) -> float:
    """DM −3 dB 频率（相对 DC 增益），对数二分。"""
    g0 = abs(h_vec(stages, "dm", 0.1)[0])
    tgt = g0 / math.sqrt(2.0)
    lo, hi = 1.0, 1e8
    for _ in range(n_iter):
        mid = math.sqrt(lo * hi)
        if abs(h_vec(stages, "dm", mid)[0]) > tgt:
            lo = mid
        else:
            hi = mid
    return math.sqrt(lo * hi)


def settle_time_fast(stages, mode="dm", band=SETTLE_BAND_V,
                     tol_r: float = 0.0, tol_c: float = 0.0, tmax=5e-3) -> float:
    """与 opt_engine.settle_time() 同定义的快速版（特征分解替代 expm），返回 **秒**。

    RC 阶梯的 C 矩阵对角正定，A = diag(C)⁻¹G 的特征值全为负实数，
    故 v(t) = v∞ + V·diag(e^{−λt})·V⁻¹·(−v∞) 与 expm(−At) 数学等价
    （test 里对多组参数断言与引擎一致）。
    """
    G, Cm, b = ladder_matrices(stages, mode, tol_r, tol_c)
    cdiag = np.diag(Cm)
    vinf = np.linalg.solve(G, b)
    A = G / cdiag[:, None]
    lam, V = np.linalg.eig(A)
    lam = np.real(lam)
    V = np.real(V)
    w = np.linalg.solve(V, -vinf)

    def err(t: float) -> float:
        return abs((vinf + V @ (np.exp(-lam * t) * w))[-1] - vinf[-1])

    if err(0.0) <= band:
        return 0.0
    if err(tmax) > band:
        return float("inf")
    lo, hi = 0.0, tmax
    for _ in range(48):
        mid = 0.5 * (lo + hi)
        if err(mid) <= band:
            hi = mid
        else:
            lo = mid
    return hi


def integrated_noise_lsb(stages, npts: int = 160) -> float:
    """ADC 引脚积分噪声（0.1 Hz ~ fMOD/2），单位 LSB（差分，双线）。

    每个电阻注入 4kTR 电流噪声，用 ladder_matrices 的 G/C 求各电阻到引脚的 NTF；
    单边结果 ×√2 得差分噪声。与 kT/C 解析值一致性见 test。
    """
    G, Cm, _b = ladder_matrices(stages, "dm")
    n = G.shape[0]
    f = np.logspace(-1, math.log10(FMOD_HZ / 2), npts)
    w = 2 * math.pi * f
    A = G[None, :, :] + 1j * w[:, None, None] * Cm[None, :, :]

    r_list, b_list = [], []
    v = np.zeros(n, complex); v[0] = -1.0                 # 源内阻 Rs = 1 Ω
    r_list.append(1.0); b_list.append(v)
    for i, (r, _cg, _cd) in enumerate(stages):            # 各级串联 R
        v = np.zeros(n, complex); v[i] = 1.0; v[i + 1] = -1.0
        r_list.append(float(r)); b_list.append(v)
    v = np.zeros(n, complex); v[n - 1] = 1.0              # 130 kΩ/2 差分负载
    r_list.append(ADC_ZIN / 2.0); b_list.append(v)

    B = np.stack(b_list, axis=1)
    B = np.broadcast_to(B[None, :, :], (len(f), n, B.shape[1]))
    X = np.linalg.solve(A, B)
    ntf = X[:, -1, :] / np.array(r_list)[None, :]
    psd = (4 * K_B * T_K * np.array(r_list)[None, :] * np.abs(ntf) ** 2).sum(axis=1)
    v_rms_single = math.sqrt(float(np.trapz(psd, f)))
    return math.sqrt(2.0) * v_rms_single / LSB_V


def cmrr_passband_db(stages, mism: float = 0.01, f_lo=10.0, f_hi=16e3, npts=40) -> float:
    """CMRR @通带最差值（10 Hz~16 kHz），两线阶梯 ±1% 失配。

    CM 模态下 C_diff 两端等电位、130 kΩ 差分负载无电流 → 两线解耦，
    故可用 opt_engine 的 tol_r/tol_c 精确表示（test 里用两线全 MNA 复核）。
    """
    f = np.logspace(math.log10(f_lo), math.log10(f_hi), npts)
    h_0 = h_vec(stages, "cm", f)
    h_1 = h_vec(stages, "cm", f, tol_r=mism, tol_c=mism)
    d = np.abs(h_1 - h_0)
    if np.any(d <= 0):
        return 200.0
    return float(np.min(20 * np.log10(np.abs(h_0) / d)))


def sigma_dg_db(stages, tol_r: float = 0.01, tol_c: float = 0.05) -> float:
    """D7 代理：各元件单独按容差扰动时 16 kHz 相对增益偏移的 RSS（dB）。"""
    base = gain_db(stages, "dm", 16e3)
    acc = 0.0
    for i in range(len(stages)):
        for k, tol in ((0, tol_r), (1, tol_c), (2, tol_c)):
            if stages[i][k] <= 0:
                continue
            s = list(stages[i])
            s[k] *= (1.0 + tol)
            st2 = stages[:i] + [tuple(s)] + stages[i + 1:]
            d = gain_db(st2, "dm", 16e3) - base
            acc += d * d
    return math.sqrt(acc)


def group_delay_us(stages, f_lo=0.1, f_hi=16e3, npts=120) -> tuple:
    """D10：0.1 Hz~16 kHz 群延迟变化量 Δτ（µs），返回 (Δτ, τ@0.1Hz)。"""
    f = np.logspace(math.log10(f_lo), math.log10(f_hi), npts)
    h = h_vec(stages, "dm", f)
    tau = -np.gradient(np.unwrap(np.angle(h)), 2 * math.pi * f)
    return float((tau.max() - tau.min()) * 1e6), float(tau[0] * 1e6)


def kickback_ns(stages) -> tuple:
    """D9 代理：返回 (τ_kb_ns, droop, 是否回稳)。

    采样瞬间 C_S 从引脚本地电容（末级 C_gnd + 2·C_diff + C_PIN）抽电荷：
      τ     = (R_sw + R_last)·C_S     —— 回稳到 0.01% 需 ~9.2τ ≤ 122 ns
      droop = C_S/(C_S + C_pin)       —— 必须 ≤ 0.01%（即 C_pin ≥ 35 nF）
    """
    r_last = float(stages[-1][0])
    c_pin = float(stages[-1][1]) + 2.0 * float(stages[-1][2]) + 5e-12
    tau = (ADC_RSW + r_last) * ADC_CS_F
    droop = ADC_CS_F / (ADC_CS_F + c_pin)
    ok = (9.2 * tau <= KB_HALF_PERIOD_S) and (droop <= 1e-4)
    return tau * 1e9, droop, bool(ok)


# ----------------------------------------------------------------------------
# 2. 十维预测 + 评分（规格 §5.1）
# ----------------------------------------------------------------------------

def predict(stages) -> dict:
    """规格 §5.1 十维理论预测值 + 硬约束量（时间量单位：秒）。"""
    stages = [tuple(map(float, s)) for s in stages]
    a_dm = -float(gain_db(stages, "dm", FMOD_HZ))
    a_cm = -float(gain_db(stages, "cm", FMOD_HZ))
    a_mclk = -float(gain_db(stages, "dm", MCLK_HZ))
    dg16 = abs(float(gain_db(stages, "dm", 16e3)))
    t_settle_s = settle_time_fast(stages, "dm", SETTLE_BAND_V, tol_r=0.01, tol_c=0.05)
    vn = integrated_noise_lsb(stages)
    sig = sigma_dg_db(stages)
    cmrr = cmrr_passband_db(stages)
    dtau_us, tau0_us = group_delay_us(stages)
    tau_kb_ns, droop, kb_ok = kickback_ns(stages)
    return {
        # —— 计划 Task 2 接口要求的六个键（dB / 秒）——
        "A_dm": a_dm,
        "A_cm": a_cm,
        "A_mclk": a_mclk,
        "dG_16k": dg16,
        "t_settle_wc_s": t_settle_s,
        "group_delay_flat_s": dtau_us * 1e-6,
        # —— 其余维度与硬约束量 ——
        "f_c_hz": fc_dm(stages),
        "V_n_lsb": vn,
        "sigma_dG_db": sig,
        "CMRR_pb_db": cmrr,
        "tau_kb_ns": tau_kb_ns,
        "kickback_droop": droop,
        "kickback_ok": kb_ok,
        "tau_dc_us": tau0_us,
        "r_sum_ohm": float(sum(s[0] for s in stages)),
        "c_max_f": float(max([c for s in stages for c in (s[1], s[2])] or [0.0])),
        "n_parts": 2 * len(stages) + sum(2 if s[1] > 0 else 0 for s in stages)
                   + sum(1 if s[2] > 0 else 0 for s in stages),
    }


def _lerp(x: float, full: float, bare: float, higher_is_better: bool = False) -> float:
    """full 处 1.0、bare 处 0.0，中间线性（D4/D7/D10 的规格插值方式）。"""
    if higher_is_better:
        if x >= full:
            return 1.0
        if x < bare:
            return 0.0
        return (x - bare) / (full - bare)
    if x <= full:
        return 1.0
    if x > bare:
        return 0.0
    return 1.0 - (x - full) / (bare - full)


def dim_scores(pred: dict) -> dict:
    """把预测值折成 D1–D10 的 [0,1] 分（规格 §5.1 归一化逐条实现）。"""
    t_us = pred["t_settle_wc_s"] * 1e6          # 秒 → µs（单位纪律）
    vn = pred["V_n_lsb"]
    return {
        "D1": _lerp(pred["A_dm"], *TH["D1"], higher_is_better=True),
        "D2": _lerp(pred["A_cm"], *TH["D2"], higher_is_better=True),
        "D3": _lerp(pred["A_mclk"], *TH["D3"], higher_is_better=True),
        "D4": _lerp(pred["dG_16k"], *TH["D4"]),
        "D5": _lerp(t_us, *TH["D5"]),
        "D6": _lerp(vn, *TH["D6"]),
        "D7": _lerp(pred["sigma_dG_db"], *TH["D7"]),
        "D8": _lerp(pred["CMRR_pb_db"], *TH["D8"], higher_is_better=True),
        "D9": 1.0 if pred["kickback_ok"] else 0.0,
        "D10": _lerp(pred["group_delay_flat_s"] * 1e6, *TH["D10"]),
    }


def pass_flags(dims: dict, pred: dict) -> dict:
    """逐维是否达到「及格线」（低于及格线 = 淘汰）。"""
    return {
        "D1": pred["A_dm"] >= TH["D1"][1],
        "D2": pred["A_cm"] >= TH["D2"][1],
        "D3": pred["A_mclk"] >= TH["D3"][1],
        "D4": pred["dG_16k"] <= TH["D4"][1],
        "D5": pred["t_settle_wc_s"] * 1e6 <= TH["D5"][1],
        "D6": pred["V_n_lsb"] <= TH["D6"][1],
        "D7": pred["sigma_dG_db"] <= TH["D7"][1],
        "D8": pred["CMRR_pb_db"] >= TH["D8"][1],
        "D9": pred["kickback_ok"],
        "D10": pred["group_delay_flat_s"] * 1e6 <= TH["D10"][1],
    }


def margin_ratios(pred: dict) -> dict:
    """相对及格线的裕量比（1.0 = 恰在及格线，>1 越好）。

    与 ``dim_scores()`` 的区别：**在及格线以下仍有梯度**，供 Nelder-Mead 使用；
    正式评分仍以规格 §5.1 的 ``dim_scores()`` 为准。
    """
    t_us = pred["t_settle_wc_s"] * 1e6
    dtau_us = pred["group_delay_flat_s"] * 1e6
    tau_kb_s = pred["tau_kb_ns"] * 1e-9
    # D9 的两条判据都折成比值：回稳时间比 + 电荷桶 droop 比
    kb_ratio = min(9.2 * tau_kb_s / KB_HALF_PERIOD_S,
                   pred["kickback_droop"] / 1e-4)
    return {
        "D1": pred["A_dm"] / TH["D1"][1],
        "D2": pred["A_cm"] / TH["D2"][1],
        "D3": pred["A_mclk"] / TH["D3"][1],
        "D4": TH["D4"][1] / max(pred["dG_16k"], 1e-9),
        "D5": TH["D5"][1] / max(t_us, 1e-9),
        "D6": TH["D6"][1] / max(pred["V_n_lsb"], 1e-9),
        "D7": TH["D7"][1] / max(pred["sigma_dG_db"], 1e-9),
        "D8": pred["CMRR_pb_db"] / TH["D8"][1],
        "D9": 1.0 / max(kb_ratio, 1e-9),
        "D10": TH["D10"][1] / max(dtau_us, 1e-9),
    }


def hard_checks(pred: dict) -> dict:
    """规格 §5.2 工程约束 + 计划 Task 2 的新 fc 约束。"""
    return {
        "fc_in_range": FC_LO <= pred["f_c_hz"] <= FC_HI,
        "r_sum": pred["r_sum_ohm"] <= R_SUM_MAX,
        "c_max": pred["c_max_f"] <= C_MAX,
        "settle": pred["t_settle_wc_s"] * 1e6 <= SETTLE_BUDGET_US,
        "dG_16k": pred["dG_16k"] <= DG_MAX_DB,
        "cdiff_layout": True,     # 结构由参数化保证：C_diff 只在末级
    }


def score_of(stages) -> tuple:
    """返回 (min(D1..D10), pred, dims)。"""
    pred = predict(stages)
    dims = dim_scores(pred)
    return min(dims.values()), pred, dims


def rank_key(rec) -> tuple:
    """候选排序键：先看过了几维及格线，再看 min，再看均分（短板制下的稳定化）。"""
    pf = pass_flags(rec["dims"], rec["pred"])
    n_pass = sum(pf.values())
    mean = float(np.mean(list(rec["dims"].values())))
    return (n_pass, rec["meta"]["min_score"], mean)


# ----------------------------------------------------------------------------
# 3. 求解器：fc 精确参数化 + Nelder-Mead 多起点
# ----------------------------------------------------------------------------
# 设计变量 x 维度 = 2n + 2：
#   x[0:n]      ln R_i            （Ω）
#   x[n:2n]     ln C_gnd,i        （F）
#   x[2n]       ln C_diff         （F，末级跨接）
#   x[2n+1]     ln fc_target      （Hz）
# fc 由「全体 R 同比缩放」精确命中（RC 网络 fc 与 R 成反比，缩放不改变曲线形状），
# 这样每条候选都严格满足 fc∈[50k,80k]，优化器只需处理其余约束。

def build_from_x(x, n: int):
    """x → (stages, fc_target)。R 等比缩放使整体 DM −3 dB 精确等于 fc_target。

    R 下限 1 Ω：低于此值已无工艺意义（E24 最小档），且会与引擎内源内阻 RS 同量级。
    """
    r = np.exp(np.clip(np.asarray(x[:n], float), math.log(1.0), math.log(5e3)))
    cg = np.exp(np.clip(np.asarray(x[n:2 * n], float), math.log(1e-9), math.log(C_MAX)))
    cd = math.exp(min(max(float(x[2 * n]), math.log(1e-9)), math.log(C_MAX)))
    fc_t = math.exp(min(max(float(x[2 * n + 1]), math.log(10e3)), math.log(500e3)))
    base = [(float(r[i]), float(cg[i]), 0.0) for i in range(n - 1)]
    base.append((float(r[-1]), float(cg[-1]), cd))
    # 精确缩放律：G ∝ 1/R、C 固定 ⇒ 全部极点 ∝ 1/R。RS 与 C_PIN 不参与缩放，
    # 故用 2 次「缩放 + 复测」迭代收敛到目标 fc（R≫RS 时 1 次即够）。
    s = 1.0
    for _ in range(3):
        fc0 = fc_dm([(rr * s, a, b) for rr, a, b in base], n_iter=34)
        s *= fc0 / fc_t
    return [(rr * s, a, b) for rr, a, b in base], fc_t


def power_mean(vals, p: float = 8.0) -> float:
    """幂平均（p→∞ 即 min）。比 softmin 更贴近短板制，且在某一维恒为 0 时仍有梯度。"""
    v = np.clip(np.asarray(vals, dtype=float), 0.0, None)
    return float((np.mean(v ** p)) ** (1.0 / p))


def objective(x, n: int) -> float:
    if not np.all(np.isfinite(x)):
        return 10.0
    stages, fc_t = build_from_x(x, n)
    cg = [s[1] for s in stages]
    cd = stages[-1][2]
    pen = 0.0
    if max(cg) > C_MAX:
        pen += 3.0 * (math.log(max(cg) / C_MAX)) ** 2
    if cd > C_MAX:
        pen += 3.0 * (math.log(cd / C_MAX)) ** 2
    if not (FC_LO * 0.999 <= fc_t <= FC_HI * 1.001):
        pen += 3.0 * (math.log(max(fc_t, FC_LO) / FC_HI)) ** 2
    if sum(s[0] for s in stages) > R_SUM_MAX:
        pen += 3.0 * (math.log(sum(s[0] for s in stages) / R_SUM_MAX)) ** 2
    try:
        pred = predict(stages)
    except Exception:
        return 10.0
    hard = hard_checks(pred)
    viol = 0.0
    if not hard["r_sum"]:
        viol += 2.0 * (pred["r_sum_ohm"] / R_SUM_MAX - 1.0)
    if not hard["settle"]:
        viol += 2.0 * (pred["t_settle_wc_s"] * 1e6 / SETTLE_BUDGET_US - 1.0)
    if not hard["dG_16k"]:
        viol += 4.0 * (pred["dG_16k"] - DG_MAX_DB)
    # 目标：最大化「十维相对及格线的有界裕量」的幂平均（p=8 ≈ min，短板制）。
    # 用 min(1, ratio) 而非原始 ratio：远优于及格线的维度封顶在 1，不再牵着优化器走；
    # 及格线以下 ratio<1 仍保留梯度（这是 round-4 只在及格线内打分所做的改进）。
    ratios = np.clip(list(margin_ratios(pred).values()), 1e-6, 1.0)
    return -power_mean(ratios, 8.0) + viol + pen


def uniform_start(n: int, fc_target: float, cg: float, cd: float) -> list:
    """均匀阶梯起点：R 用 fc 反解（利用 R ∝ 1/fc 的精确缩放律）。"""
    base = [(1.0, cg, 0.0) for _ in range(n - 1)] + [(1.0, cg, cd)]
    r = fc_dm(base, n_iter=40) / fc_target
    return [r] * n + [cg] * n + [cd] + [fc_target]


def initial_points(n: int, rng: np.random.Generator, n_starts: int) -> list:
    """确定性起点：fc × C_gnd × C_diff 网格 + 几何阶梯 + 种子随机扰动。"""
    grid = []
    for fc_t in (50e3, 60e3, 70e3, 80e3):
        for cg in (100e-9, 47e-9):
            for cd in (47e-9, 10e-9):
                grid.append(uniform_start(n, fc_t, cg, cd))
    pts = [grid[(i * 3) % len(grid)] for i in range(max(n_starts, 1))]
    for ratio in (3.0, 10.0):         # 前级大 R、末级小 R（FIN1 型几何递减）
        base = uniform_start(n, 62e3, 68e-9, 33e-9)
        rr = [base[i] / (ratio ** (i - (n - 1) / 2.0)) for i in range(n)]
        pts.append(rr + base[n:])
    for _ in range(3):
        b = np.array(pts[int(rng.integers(0, len(pts)))], dtype=float)
        z = np.log(b) + rng.normal(0, 0.6, size=len(b))
        pts.append(np.exp(z).tolist())
    return pts


def _pack(stages, fc_t: float) -> np.ndarray:
    n = len(stages)
    return np.array([math.log(max(s[0], 1e-9)) for s in stages]
                    + [math.log(max(s[1], 1e-18)) for s in stages]
                    + [math.log(max(stages[-1][2], 1e-18)), math.log(fc_t)])


def solve_candidate(n_stages: int, seed: int = 0, maxiter: int = 220,
                    n_starts: int = 3, verbose: bool = False) -> dict:
    """Task 2 接口：给定级数的多起点 Nelder-Mead 求解。

    返回 {"stages": [(R, C_gnd, C_diff), ...], "pred": {...}, "dims": {...}, "meta": {...}}
    """
    rng = np.random.default_rng(seed)
    starts = initial_points(n_stages, rng, n_starts)
    tried = []
    for k, s0 in enumerate(starts):
        st0 = [(s0[i], s0[n_stages + i], s0[2 * n_stages]) for i in range(n_stages)]
        fc_t = s0[2 * n_stages + 1]
        res = minimize(objective, _pack(st0, fc_t), args=(n_stages,),
                       method="Nelder-Mead",
                       options={"maxiter": maxiter, "xatol": 1e-3, "fatol": 1e-4})
        stages, _ = build_from_x(res.x, n_stages)
        mm, pred, dims = score_of(stages)
        rec = {"stages": stages, "pred": pred, "dims": dims,
               "meta": {"n_stages": n_stages, "seed": seed,
                        "min_score": mm, "feasible": all(hard_checks(pred).values()),
                        "start": k, "f_obj": float(res.fun), "n_starts": len(starts),
                        "hard": hard_checks(pred)}}
        tried.append(rec)
        if verbose:
            print(f"    start#{k:02d} min={mm:.3f} fc={pred['f_c_hz']/1e3:5.1f}k "
                  f"ΣR={pred['r_sum_ohm']:6.1f} DM={pred['A_dm']:5.1f} CM={pred['A_cm']:5.1f} "
                  f"dG={pred['dG_16k']:.3f} Vn={pred['V_n_lsb']:.2f} "
                  f"feasible={rec['meta']['feasible']}")
    feas = [r for r in tried if r["meta"]["feasible"]]
    pool = feas if feas else tried
    pool.sort(key=rank_key, reverse=True)
    best = pool[0]
    out = {
        "stages": [(round(float(r), 5), float(cg), float(cd)) for r, cg, cd in best["stages"]],
        "pred": best["pred"],
        "dims": best["dims"],
        "meta": dict(best["meta"]),
    }
    out["meta"]["all_starts"] = [
        {"start": r["meta"]["start"], "min_score": r["meta"]["min_score"],
         "f_c_hz": r["pred"]["f_c_hz"], "feasible": r["meta"]["feasible"],
         "stages": [[float(a), float(b), float(c)] for a, b, c in r["stages"]]}
        for r in tried
    ]
    return out


# ----------------------------------------------------------------------------
# 4. 报告
# ----------------------------------------------------------------------------

DIM_LABEL = {
    "D1": "A_dm@fMOD(dB)", "D2": "A_cm@fMOD(dB)", "D3": "A_mclk(dB)", "D4": "ΔG16k(dB)",
    "D5": "t_settle(µs)", "D6": "Vn(LSB)", "D7": "σΔG(dB)", "D8": "CMRR(dB)",
    "D9": "kickback", "D10": "Δτ(µs)",
}


def _dim_value(dim: str, pred: dict) -> float:
    return {
        "D1": pred["A_dm"], "D2": pred["A_cm"], "D3": pred["A_mclk"], "D4": pred["dG_16k"],
        "D5": pred["t_settle_wc_s"] * 1e6, "D6": pred["V_n_lsb"],
        "D7": pred["sigma_dG_db"], "D8": pred["CMRR_pb_db"],
        "D9": 1.0 if pred["kickback_ok"] else 0.0,
        "D10": pred["group_delay_flat_s"] * 1e6,
    }[dim]


def short_topo(stages) -> str:
    out = []
    for r, cg, cd in stages:
        s = f"{r:.2f}Ω/{cg*1e9:.0f}n"
        s += f"+{cd*1e9:.0f}nd" if cd > 0 else ""
        out.append(s)
    return "—".join(out)


def print_front(results: list) -> None:
    """帕累托前沿：按级数分组，组内按 rank_key（及格维度数 → min → 均值）降序。"""
    print("\n=== 帕累托前沿（理论预测，规格 §5.1 十维） ===")
    hdr = (f"{'级':>2} {'min':>5} {'过线':>4} {'fc/kHz':>6} {'ΣR/Ω':>7} {'A_dm':>6} "
           f"{'A_cm':>6} {'A_mk':>6} {'ΔG16k':>6} {'ts/µs':>6} {'Vn':>5} {'σΔG':>6} "
           f"{'CMRR':>5} {'Δτ/µs':>6}  拓扑")
    print(hdr)
    for r in sorted(results, key=lambda z: (z["meta"]["n_stages"],
                                            tuple(-v for v in rank_key(z)))):
        p, d = r["pred"], r["dims"]
        npass = sum(pass_flags(d, p).values())
        print(f"{r['meta']['n_stages']:>2} {r['meta']['min_score']:>5.3f} {npass:>3}/10 "
              f"{p['f_c_hz']/1e3:>6.1f} {p['r_sum_ohm']:>7.1f} {p['A_dm']:>6.1f} "
              f"{p['A_cm']:>6.1f} {p['A_mclk']:>6.1f} {p['dG_16k']:>6.3f} "
              f"{p['t_settle_wc_s']*1e6:>6.0f} {p['V_n_lsb']:>5.2f} {p['sigma_dG_db']:>6.3f} "
              f"{p['CMRR_pb_db']:>5.1f} {p['group_delay_flat_s']*1e6:>6.2f}  {short_topo(r['stages'])}")


def print_dims(rec: dict) -> None:
    """逐维打印：值 / 分 / 及格线（不过线的打 ×）。"""
    p, d = rec["pred"], rec["dims"]
    pf = pass_flags(d, p)
    line = "  ".join(
        f"{k}:{_dim_value(k, p):.3g}{'' if pf[k] else '×'}({d[k]:.2f})" for k in
        ("D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D10"))
    print("   " + line)


def rs_sensitivity(stages, rs_ohm: float) -> dict:
    """诊断：把源内阻从引擎默认 1 Ω 改成 rs_ohm 后的关键量。

    ``opt_engine.ladder_matrices()`` 内 rs 硬编码为 1 Ω（`rs = 1.0*(1+tol_r)`），
    因此这里本地重建 G/C（其余与引擎逐项一致），用于评估 V9 非理想跟随器工况
    （M7：OPA388 闭环 Z_o ≈ 34 Ω @4.096 MHz）。
    """
    n = len(stages) + 1
    G = np.zeros((n, n))
    Cd = np.zeros(n)
    b = np.zeros(n)
    G[0, 0] += 1.0 / rs_ohm
    b[0] += 1.0 / rs_ohm
    Cd[0] += 1e-12
    for i, (r, ccm, cdf) in enumerate(stages):
        a, bb = i, i + 1
        G[a, a] += 1 / r; G[bb, bb] += 1 / r
        G[a, bb] -= 1 / r; G[bb, a] -= 1 / r
        c_eff = ccm + (2 * cdf if True else 0.0)
        Cd[bb] += c_eff
    G[n - 1, n - 1] += 1 / 65000.0
    Cd[n - 1] += 5e-12

    def h_at(mode, f):
        w = 2 * math.pi * f
        Gi = G.copy()
        if mode == "cm":                       # CM: 差分负载不载、C_diff 开路
            Gi[n - 1, n - 1] -= 1 / 65000.0
            c = Cd.copy()
            for i, (_r, _cg, cdf) in enumerate(stages):
                c[i + 1] -= 2 * cdf
        else:
            c = Cd
        return np.linalg.solve(Gi + 1j * w * np.diag(c), b)[-1]

    g0_dm = abs(h_at("dm", 0.1))
    tgt = g0_dm / math.sqrt(2)
    lo, hi = 1.0, 1e8
    for _ in range(60):
        mid = math.sqrt(lo * hi)
        if abs(h_at("dm", mid)) > tgt:
            lo = mid
        else:
            hi = mid
    return {
        "f_c_hz": math.sqrt(lo * hi),
        "A_dm": -20 * math.log10(abs(h_at("dm", FMOD_HZ)) / g0_dm),
        "A_cm": -20 * math.log10(abs(h_at("cm", FMOD_HZ)) / abs(h_at("cm", 0.1))),
        "dG_16k": abs(20 * math.log10(abs(h_at("dm", 16e3)) / g0_dm)),
    }


def run_all(maxiter: int = 220, starts: int = 3) -> list:
    results = []
    for n in (2, 3, 4):
        print(f"\n--- {n} 级求解（Nelder-Mead × {starts} 起点，fc∈[50,80] kHz）---")
        r = solve_candidate(n, seed=0, maxiter=maxiter, n_starts=starts, verbose=True)
        print(f"  → min={r['meta']['min_score']:.3f}  fc={r['pred']['f_c_hz']/1e3:.1f} kHz  "
              f"ΣR={r['pred']['r_sum_ohm']:.1f} Ω  {short_topo(r['stages'])}")
        print_dims(r)
        print(f"     hard={r['meta']['hard']}")
        if not r["meta"]["feasible"]:
            print("     ⚠ 未找到满足全部硬约束的解")
        results.append(r)
    print_front(results)
    print("\n=== V9 非理想源内阻敏感性（M7：OPA388 闭环 Z_o ≈ 34 Ω @4.096 MHz） ===")
    for r in results:
        s = rs_sensitivity(r["stages"], 34.0)
        print(f"  {r['meta']['n_stages']} 级: fc {r['pred']['f_c_hz']/1e3:.1f}→{s['f_c_hz']/1e3:.1f} kHz, "
              f"A_dm {r['pred']['A_dm']:.1f}→{s['A_dm']:.1f} dB, "
              f"ΔG16k {r['pred']['dG_16k']:.3f}→{s['dG_16k']:.3f} dB")
    return results


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Round 5 十维理论优化（三案）")
    ap.add_argument("--maxiter", type=int, default=220)
    ap.add_argument("--starts", type=int, default=3)
    ap.add_argument("--json", default="")
    args = ap.parse_args(argv)
    results = run_all(args.maxiter, args.starts)
    if args.json:
        out = {str(r["meta"]["n_stages"]): r for r in results}
        with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(out, fh, ensure_ascii=False, indent=2)
        print(f"\n已写出 {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
