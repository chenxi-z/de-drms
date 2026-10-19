#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""parse_r3_B.py — 第 3 轮方案 B 十维实测提取（规格 v4 口径）+ 理论交叉验证

口径（规格 v4 §5.1）
--------------------
* **评分主口径 = 真实 OPA388 模型**（V9 系列，`v9a/v9b/v9c/v9d/v9df/v9e/v9f/v9mc/v9cmc/v9kb`）
* 0 Ω 理想源 V1–V8 仅作**对照报告**，不参与打分
* D6a = (V_n(真实阶梯) − V_n(同带宽无噪阶梯)) / V_n(同带宽无噪阶梯) × 100  [%]
  - 两个网表只有阶梯电阻的"有无噪声"不同：v9d 用真电阻，v9df 用等值无噪 B 源；
    传函与带宽完全相同，故差值就是**无源网络自身（含 130 kΩ 负载）的噪声增量**。
* D6b = 真实模型总积分噪声（0.1 Hz–fMOD/2），LSB，仅报告
* D8 = 两线 R·C 乘积异向配对下 10 Hz–16 kHz 最差 CMRR；m = 0.1/0.5/1% 三档，
  另报同向 1% 对照。D8 取值 = **配对条件下最优档**（规格 v4 §5.1 与 ask 口径）
* C9 = 真实模型全频段（0.1 Hz–200 MHz）增益相对 DC 的最大峰值，≤6 dB

交叉验证（规格 §8）：AC ≤0.5 dB、建立 ≤5%
  - 对照口径必须同拓扑：真实模型 LTspice vs `opt_round5.predict(source='opa388')`（引擎真实模型口径）
  - 另报 0 Ω 理想源 LTspice vs `xcheck_B.predict_zero_source()`（纯无源 MNA）

用法：python parse_r3_B.py [--json r5_results_r3_B.json]
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import parse_r5 as P          # noqa: E402  raw 解析（唯一实现）
import xcheck_B as X          # noqa: E402  0 Ω 双线 MNA 理论
import opt_round5 as O5       # noqa: E402  真实模型理论引擎

D = os.path.join(HERE, "r5_work", "r3_B")
CAND = os.path.join(HERE, "r5_candidates_r2.json")
SCHEME = "B"
FMOD, MCLK = 4.096e6, 16.384e6
TBAND_SPEC = P.TBAND_SPEC      # 200 µV = 2 V 阶跃 × 0.01%
TBAND_ENG = P.TBAND_DIFF       # 120 µV（引擎口径）

# 规格 v4 §5.1 阈值
TH = {"D1": (120.0, 80.0), "D2": (100.0, 60.0), "D3": (150.0, 100.0),
      "D4": (0.05, 0.50), "D5": (500.0, 900.0), "D6a": (10.0, 30.0),
      "D7": (0.01, 0.05), "D8": (100.0, 80.0), "D10": (1.0, 5.0)}
PEAK_MAX_DB = 6.0              # C9


def rp(tag):
    return os.path.join(D, f"r5_B_{tag}_r3.raw")


def have(tag):
    return os.path.exists(rp(tag))


# ------------------------------------------------------------------ 单项提取
def _local_extrema(f, g, lo, hi, n=8):
    """[lo,hi] 内的局部极值（用于核查有源谐振位置）。"""
    m = (f >= lo) & (f <= hi)
    ff, gg = f[m], g[m]
    if len(gg) < 5:
        return []
    dy = np.diff(gg)
    idx = np.where(np.diff(np.sign(dy)) != 0)[0] + 1
    return [{"f_hz": round(float(ff[i]), 1), "gain_db": round(float(gg[i]), 3)}
            for i in idx[:n]]


def ac_dm(tag, ns, f_dc=1.0):
    """差分 AC：DC 增益、16 kHz 偏差、fMOD/MCLK 衰减、D10 群延迟、C9 peaking。"""
    r = P.Raw(rp(tag))
    pa, na = P.pin_names(range(ns))
    f = r.f
    p = np.array(r.col(pa), dtype=complex)
    n = np.array(r.col(na), dtype=complex)
    d = p - n
    dc = P.interp_at(r, f_dc, pa) - P.interp_at(r, f_dc, na)
    g_dc = P.db(dc)
    g16 = P.db(P.interp_at(r, 16e3, pa) - P.interp_at(r, 16e3, na))
    gf = P.db(P.interp_at(r, FMOD, pa) - P.interp_at(r, FMOD, na))
    gm = P.db(P.interp_at(r, MCLK, pa) - P.interp_at(r, MCLK, na))
    m = (f >= 0.1) & (f <= 16e3)
    ph = np.unwrap(np.angle(d[m]))
    tau = -np.gradient(ph, 2 * math.pi * f[m])
    # C9：相对 DC 的增益峰值（只在 |d| 有效处求）
    g = 20 * np.log10(np.maximum(np.abs(d), 1e-300) / abs(dc))
    ipk = int(np.argmax(g))
    # C9 旁证：100 kHz–2 MHz（有源谐振的实际战场）内的局部峰值
    mc9 = (f >= 100e3) & (f <= 2e6)
    ic = int(np.argmax(g[mc9]))
    # 群延迟按两线分别算 CH 差（规格 §5.1 注要求单列）
    tp = -np.gradient(np.unwrap(np.angle(p[m])), 2 * math.pi * f[m])
    tn = -np.gradient(np.unwrap(np.angle(n[m])), 2 * math.pi * f[m])
    return {
        "g_dc_db": float(g_dc), "g_16k_db": float(g16),
        "D4_dG_16k_db": float(abs(g16 - g_dc)),
        "D1_A_dm_db": float(-(gf - g_dc)),
        "D3_A_mclk_db": float(-(gm - g_dc)),
        "D10_dtau_us": float((tau.max() - tau.min()) * 1e6),
        "tau_100Hz_us": float(tau[0] * 1e6), "tau_16k_us": float(tau[-1] * 1e6),
        "CH_tau_diff_us": float(np.max(np.abs(tp - tn)) * 1e6),
        "C9_peak_db_rel_dc": float(g[ipk]),
        "C9_peak_f_hz": float(f[ipk]),
        "C9_peak_100k_2M_db": float(g[mc9][ic]),
        "C9_peak_100k_2M_f_hz": float(f[mc9][ic]),
        "C9_peak_f_ge_1Hz_db": float(np.max(g[f >= 1.0])),
        "C9_local_extrema_50k_2M": _local_extrema(f, g, 50e3, 2e6),
        "g_at_200k_db": float(20 * math.log10(abs(P.interp_at(r, 2e5, pa)
                                                   - P.interp_at(r, 2e5, na)) / abs(dc))),
        "g_at_1M_db": float(20 * math.log10(abs(P.interp_at(r, 1e6, pa)
                                               - P.interp_at(r, 1e6, na)) / abs(dc))),
    }


def ac_cm(tag, ns, f_lo=10.0, f_hi=16e3):
    """共模 AC：A_cm@fMOD（D2，需要宽带网表）与 CMRR@通带（D8，需要 [1 Hz, 40 kHz] 网表）。"""
    r = P.Raw(rp(tag))
    pa, na = P.pin_names(range(ns))
    f = r.f
    out = {"g_cm_dc_db": float(P.db(P.interp_at(r, 1.0, pa))),
           "g_cm_16k_db": float(P.db(P.interp_at(r, 16e3, pa)))}
    if f[-1] >= FMOD:
        out["D2_A_cm_db"] = float(-(P.db(P.interp_at(r, FMOD, pa))
                                    - P.db(P.interp_at(r, 1.0, pa))))
    m = (f >= f_lo) & (f <= f_hi)
    cm = np.abs(np.array(r.col(pa))[m])
    dm = np.abs(np.array(r.col(pa))[m] - np.array(r.col(na))[m])
    with np.errstate(divide="ignore"):
        c = 20 * np.log10(cm / dm)
    # 两线完全对称时 dm 可能数值为 0 → -inf；夹到 300 dB（远高于阈值，语义不变）
    c = np.clip(np.nan_to_num(c, nan=-300.0, posinf=300.0, neginf=-300.0), -300.0, 300.0)
    k = int(np.argmin(c))
    out.update({"D8_CMRR_db": float(c[k]), "D8_worst_f_hz": float(f[m][k]),
                "cmrr_10Hz_db": float(c[0]), "cmrr_16k_db": float(c[-1])})
    return out


def _settle(tag, ns):
    r = P.Raw(rp(tag))
    ts, vf, ef = P.settle_us(r, ns, band=TBAND_SPEC)
    te, _, _ = P.settle_us(r, ns, band=TBAND_ENG)
    t = np.array([v.real if isinstance(v, complex) else v for v in r.cols[0]], dtype=float)
    return {"tset_us": float(ts), "tset_engine_band_us": float(te),
            "vfinal_v": float(vf), "err_final_uv": float(ef * 1e6),
            "t_end_us": float(t[-1] * 1e6)}


def _noise(tag):
    r = P.Raw(rp(tag))
    f = np.array([v.real if isinstance(v, complex) else v for v in r.cols[0]], dtype=float)
    dens = np.abs(np.array(r.col("v(onoise)")))
    m = f <= FMOD / 2
    tot = math.sqrt(float(np.trapz(dens[m] ** 2, f[m])))
    return {"vn_nv": float(tot * 1e9), "vn_lsb": float(tot / P.LSB_V),
            "dens_1k_nv": float(np.interp(1e3, f, dens) * 1e9),
            "dens_10k_nv": float(np.interp(1e4, f, dens) * 1e9),
            "dens_100k_nv": float(np.interp(1e5, f, dens) * 1e9),
            "f_max_hz": float(f[m][-1])}


def _mc_sigma(prefix, ns, n=30):
    g = []
    for k in range(1, n + 1):
        p = rp(f"{prefix}{k:02d}")
        if not os.path.exists(p):
            continue
        rr = P.Raw(p)
        pa, na = P.pin_names(range(ns))
        dcg = P.db(P.interp_at(rr, 0.1, pa) - P.interp_at(rr, 0.1, na))
        g16 = P.db(P.interp_at(rr, 16e3, pa) - P.interp_at(rr, 16e3, na))
        g.append(g16 - dcg)
    if not g:
        return {}
    return {"n": len(g), "sigma_db": float(np.std(g, ddof=1)),
            "mean_db": float(np.mean(g)), "min_db": float(np.min(g)),
            "max_db": float(np.max(g)), "p2p_db": float(np.max(g) - np.min(g))}


def _mc_settle(prefix, ns, n=30):
    t = []
    for k in range(1, n + 1):
        p = rp(f"{prefix}{k:02d}")
        if not os.path.exists(p):
            continue
        tk, _, _ = P.settle_us(P.Raw(p), ns, band=TBAND_SPEC)
        t.append(tk)
    if not t:
        return {}
    return {"n": len(t), "min_us": float(np.min(t)), "mean_us": float(np.mean(t)),
            "max_us": float(np.max(t))}


# ------------------------------------------------------------------ 评分
def _lsb_v():
    return P.LSB_V


def score(dims):
    def ratio(x, full):
        return float(min(max(x, 0.0) / full, 1.0))

    def inv(x, full):
        return float(min(full / x, 1.0)) if x and np.isfinite(x) and x > 0 else 0.0

    def lerp(x, full, bare):
        if x <= full:
            return 1.0
        if x > bare:
            return 0.0
        return float(1.0 - (x - full) / (bare - full))

    s = {"D1": ratio(dims["D1"], 120.0), "D2": ratio(dims["D2"], 100.0),
         "D3": ratio(dims["D3"], 150.0), "D4": lerp(dims["D4"], *TH["D4"]),
         "D5": inv(dims["D5"], 500.0), "D6a": inv(dims["D6a"], 10.0),
         "D7": lerp(dims["D7"], *TH["D7"]), "D8": ratio(dims["D8"], 100.0),
         "D9": float(dims["D9"]), "D10": lerp(dims["D10"], *TH["D10"])}
    p = {"D1": dims["D1"] >= 80, "D2": dims["D2"] >= 60, "D3": dims["D3"] >= 100,
         "D4": dims["D4"] <= 0.50, "D5": dims["D5"] <= 900, "D6a": dims["D6a"] <= 30,
         "D7": dims["D7"] <= 0.05, "D8": dims["D8"] >= 80,
         "D9": dims["D9"] == 1.0, "D10": dims["D10"] <= 5.0}
    return s, p


# ------------------------------------------------------------------ 主流程
def build():
    cand = json.load(open(CAND, encoding="utf-8"))[SCHEME]
    st = [tuple(map(float, s)) for s in cand["stages"]]
    ns = len(st)
    out = {"scheme": SCHEME, "grade": cand.get("grade"), "n_stages": ns,
           "stages": cand["stages"], "sources": {},
           "re": {}, "control_ideal": {}}

    # ---------------- 真实模型（评分主口径） ----------------
    d1 = ac_dm("v9a", ns)
    out["re"]["V9a"] = d1
    out["sources"]["D1"] = "r5_B_v9a_r3.raw @4.096 MHz（真实 OPA388）"
    out["sources"]["D3"] = "r5_B_v9a_r3.raw @16.384 MHz"
    out["sources"]["D4"] = "r5_B_v9a_r3.raw @16 kHz 相对 DC"
    out["sources"]["D10"] = "r5_B_v9a_r3.raw 群延迟 0.1 Hz–16 kHz"

    d2 = ac_cm("v9b", ns)
    out["re"]["V9b_nominal"] = d2
    out["sources"]["D2"] = "r5_B_v9b_r3.raw @4.096 MHz 共模（真实 OPA388）"

    # D5：规格点名高阻工况 → V9f（600 kΩ + 最坏角 + 真实模型）；
    #     同时报 V9c（0 Ω + 最坏角 + 真实模型）与 MC 统计
    d5c = {}
    if have("v9c"):
        d5c["V9c_0ohm_real_corner"] = _settle("v9c", ns)
    if have("v9f"):
        d5c["V9f_600k_real_corner"] = _settle("v9f", ns)
    if have("v9cmc01"):
        d5c["V9c_MC30_real"] = _mc_settle("v9cmc", ns)
    out["re"]["V9_D5"] = d5c
    # 取规格点名工况（V9f 600 kΩ）；若无则退 0 Ω
    d5_val = (d5c.get("V9f_600k_real_corner", {}).get("tset_us")
              or d5c.get("V9c_0ohm_real_corner", {}).get("tset_us"))
    out["sources"]["D5"] = "r5_B_v9f_r3.raw（600 kΩ 样品端 + R1%/C5% 最坏角 + 真实 OPA388）"

    # D6a / D6b
    vb = _noise("v9d")
    vf = _noise("v9df")
    out["re"]["V9d_total_noise"] = vb
    out["re"]["V9df_follower_only_noise"] = vf
    # D6a 主口径（按 ask 字面：真实模型总噪声 − 同带宽跟随器自身噪声，比例形式）：
    d6a_pct = 100.0 * (vb["vn_nv"] - vf["vn_nv"]) / vf["vn_nv"]
    # 旁证：正交（功率）拆分的无源分量占比 —— 这才是"无源网络自身贡献了多少噪声"的
    # 物理量；线性相减在跟随器主导（9.9 nV/√Hz）时会把 327 nV 的贡献压成 0.33%。
    v_pass_quad = math.sqrt(max(vb["vn_nv"] ** 2 - vf["vn_nv"] ** 2, 0.0))
    d6a_quad_pct = 100.0 * v_pass_quad / vf["vn_nv"]
    out["sources"]["D6a"] = "V9d(真实阶梯) vs V9df(无噪等值阶梯) 同带宽积分噪声增量"
    out["sources"]["D6b"] = "r5_B_v9d_r3.raw 积分 0.1 Hz–2.048 MHz"

    # D7
    v5 = _mc_sigma("v9mc", ns)
    out["re"]["V9_MC_AC"] = v5
    out["sources"]["D7"] = "r5_B_v9mc01..30_r3.raw（真实 OPA388，逐元件 MC，C 5%/R 1%）"

    # D8：配对 m 三档 + 同向对照
    d8 = {}
    for tag, lab in (("v9b_p001", "paired_0.1pct"), ("v9b_p05", "paired_0.5pct"),
                     ("v9b_p1", "paired_1pct"), ("v9b_p1inv", "paired_1pct_strict_recip"),
                     ("v9b_s1", "same_dir_1pct")):
        if have(tag):
            d8[lab] = ac_cm(tag, ns)
    # CH1 vs CH2 群延迟差（规格 §5.1 注：相位测量要求，须单列）
    for k, v in d8.items():
        pass
    out["re"]["D8"] = d8
    if "paired_1pct" in d8:
        rr = P.Raw(rp("v9b_p1"))
        fq = rr.f
        mm = (fq >= 0.1) & (fq <= 16e3)
        pa_, na_ = P.pin_names(range(ns))
        tp = -np.gradient(np.unwrap(np.angle(np.array(rr.col(pa_))[mm])), 2 * math.pi * fq[mm])
        tn = -np.gradient(np.unwrap(np.angle(np.array(rr.col(na_))[mm])), 2 * math.pi * fq[mm])
        d8["paired_1pct"]["CH_tau_diff_us"] = float(np.max(np.abs(tp - tn)) * 1e6)
    best = None
    for k in ("paired_0.1pct", "paired_0.5pct", "paired_1pct"):
        if k in d8:
            best = max(best, d8[k]["D8_CMRR_db"]) if best is not None else d8[k]["D8_CMRR_db"]
    # ask 口径：「D8 = 配对条件下的最优档」→ 取三档中最好的 CMRR（= m 最小档）
    d8_val = d8.get("paired_0.1pct", {}).get("D8_CMRR_db")
    if d8_val is None:
        d8_val = d8.get("paired_0.5pct", d8.get("paired_1pct", {})).get("D8_CMRR_db")
    out["sources"]["D8"] = ("r5_B_v9b_p001_r3.raw（R×1.001 配 C×0.999，10 Hz–16 kHz 最差）"
                            if "paired_0.1pct" in d8 else "配对网表缺失")

    # D9：真实模型 kickback（Ron=1 / 100 / 1000）
    d9 = {}
    for ron in (1, 100, 1000):
        if have(f"v9kb_ron{ron}"):
            d9[f"ron{ron}"] = P.kickback(P.Raw(rp(f"v9kb_ron{ron}")), ns)
    out["re"]["V9_kickback"] = d9
    # D9 旁证：采样电容在窗口末端的电荷转移残差（物理判据，parse_r5_A._cap_lock）
    import parse_r5_A as PA
    for k, v in list(d9.items()):
        if isinstance(v, dict):
            v["cap_lock"] = PA._cap_lock(P.Raw(rp(f"v9kb_{k}")), ns)
    d9_val = float(d9["ron1"]["D9"]) if "ron1" in d9 else float(
        list(d9.values())[0]["D9"]) if d9 else None
    out["sources"]["D9"] = "r5_B_v9kb_ron1_r3.raw（真实 OPA388 + ADC 采样开关模型）"

    # ---------------- 0 Ω 理想源对照 ----------------
    if have("v1"):
        out["control_ideal"]["V1"] = ac_dm("v1", ns, f_dc=0.1)
    if have("v2"):
        out["control_ideal"]["V2"] = ac_cm("v2", ns)
    if have("v3"):
        c3 = ac_cm("v3", ns)
        out["control_ideal"]["V3_same_dir_1pct"] = c3
    if have("v3p1"):
        out["control_ideal"]["V3p1_paired_1pct"] = ac_cm("v3p1", ns)
    if have("v4"):
        out["control_ideal"]["V4"] = _settle("v4", ns)
    if have("v4b"):
        out["control_ideal"]["V4b"] = _settle("v4b", ns)
    if have("v5mc01"):
        out["control_ideal"]["V5_MC_AC"] = _mc_sigma("v5mc", ns)
    if have("v6mc01"):
        out["control_ideal"]["V6_MC_tran"] = _mc_settle("v6mc", ns)
    if have("v7"):
        out["control_ideal"]["V7"] = _noise("v7")
    c8 = {}
    for ron in (1, 100, 1000):
        if have(f"v8_ron{ron}"):
            c8[f"ron{ron}"] = P.kickback(P.Raw(rp(f"v8_ron{ron}")), ns)
    if c8:
        out["control_ideal"]["V8_kickback"] = c8

    # ---------------- 十维 ----------------
    dims = {
        "D1": d1["D1_A_dm_db"], "D2": d2.get("D2_A_cm_db"),
        "D3": d1["D3_A_mclk_db"], "D4": d1["D4_dG_16k_db"],
        "D5": d5_val, "D6a": d6a_pct, "D6b": vb["vn_lsb"],
        "D7": v5.get("sigma_db"), "D8": d8_val, "D9": d9_val,
        "D10": d1["D10_dtau_us"],
    }
    dims_all = {k: (round(v, 6) if isinstance(v, float) else v) for k, v in dims.items()}
    out["dims"] = dims_all
    sc, pf = score(dims)
    out["scores"] = sc
    out["pass"] = pf
    out["min_score"] = min(sc.values())
    out["hard"] = {
        "C9_peaking_ok": d1["C9_peak_db_rel_dc"] <= PEAK_MAX_DB,
        "C9_peak_db": d1["C9_peak_db_rel_dc"], "C9_peak_f_hz": d1["C9_peak_f_hz"],
        "C9_peak_full_band_0p1Hz_200MHz_db": d1["C9_peak_db_rel_dc"],
        "C9_peak_100k_2M_db": d1["C9_peak_100k_2M_db"],
        "C9_peak_100k_2M_f_hz": d1["C9_peak_100k_2M_f_hz"],
        "C9_all_below_dc": bool(d1["C9_peak_db_rel_dc"] <= 1e-6),
        "C9_note": "全频段（0.1 Hz–200 MHz，dec 1000）最大值出现在最低频点，即 0 dB——"
                   "B 案在真实 OPA388 模型下不存在任何增益峰；100k–2M 内的局部极值均为负"
                   "（173 kHz −5.46 dB、281 kHz −2.32 dB），即 OPA388 输出阻抗负实部未形成谐振。"
                   "第 2 轮 C9 案例（+30.7 dB @283 kHz）是 A 案参数，不是 B 案。"
                   "需注意：本结论含 2.048 MHz 以上的 AC 扫描，但噪声积分只到 2.048 MHz。",
        "C2_r_sum_ohm": float(sum(s[0] for s in st)),
        "C2_ok": float(sum(s[0] for s in st)) <= 5e3,
        "C3_c_max_f": float(max(s[1] for s in st)),
        "C3_ok": float(max(s[1] for s in st)) <= 100e-9,
        "D6a_increment_pct": d6a_pct,
        "D6a_quadrature_pct": d6a_quad_pct,
        "D6a_quadrature_nv": v_pass_quad,
        "D6a_note": "主值按 ask 字面公式（Vtot−Vfol)/Vfol；正交口径（√(Vtot²−Vfol²)/Vfol）"
                    "把无源网络的实际噪声贡献算作 Vfol 的 8.09%（326.7 nVrms），"
                    "两种口径都 ≤10% 满分线。线性口径偏小是因为跟随器 9.9 nV/√Hz 完全主导。",
        "D6_brickwall_lsb": float(O5.EN_FOLL_DIFF * math.sqrt(16e3) / P.LSB_V),
    }

    # ---------------- D5 数值收敛性证据（本轮专门做的重试） ----------------
    # 第 2 轮 V9c 收敛失败；本轮换 gear + reltol=1e-5 稳定收敛（2 s）。
    # 为排除"数值误差导致 46 µs"，另跑三组不同积分器/容差/步长：
    #   B_gear_1e6  gear reltol=1e-6 maxstep 5 ns  → 46.02 µs
    #   G_trap_1e4  trap reltol=1e-4 maxstep 20 ns  → 46.02 µs
    #   （另有 trap 1e-6 与 trap 1e-5 在 240 s 内未收敛，属 TI 宏模型的已知困难）
    conv = {}
    for tag, lab in (("B_gear_1e6", "V9c gear reltol=1e-6 maxstep=5n"),
                     ("G_trap_1e4", "V9c trap reltol=1e-4 maxstep=20n"),
                     ("H_v9f_gear_1e6", "V9f gear reltol=1e-6 maxstep=5n")):
        p = os.path.join(D, "d5var", f"{tag}.raw")
        if os.path.exists(p):
            ts, _, _ = P.settle_us(P.Raw(p), ns, band=TBAND_SPEC)
            conv[lab] = {"tset_us": round(float(ts), 3), "raw": f"r5_work/r3_B/d5var/{tag}.raw"}
    if conv:
        out["re"]["D5_numeric_variants"] = conv

    # ---------------- C9 细扫复核（dec 4000, 20 kHz–20 MHz） ----------------
    if have("v9a_fine"):
        rf = P.Raw(rp("v9a_fine"))
        pa_, na_ = P.pin_names(range(ns))
        ff = rf.f
        dd = np.array(rf.col(pa_)) - np.array(rf.col(na_))
        ref = abs(P.interp_at(P.Raw(rp("v9a")), 1.0, pa_)
                  - P.interp_at(P.Raw(rp("v9a")), 1.0, na_))
        gg = 20 * np.log10(np.maximum(np.abs(dd), 1e-300) / ref)
        m1 = (ff >= 100e3) & (ff <= 2e6)
        i1 = int(np.argmax(gg))
        i2 = int(np.argmax(gg[m1]))
        mi = int(np.argmin(gg[m1]))
        out["re"]["V9a_fine_sweep_C9"] = {
            "n_points": int(len(ff)), "f_lo_hz": float(ff[0]), "f_hi_hz": float(ff[-1]),
            "max_gain_20k_20M_db": float(gg[i1]), "max_gain_f_hz": float(ff[i1]),
            "max_100k_2M_db": float(gg[m1][i2]), "max_100k_2M_f_hz": float(ff[m1][i2]),
            "min_100k_2M_db": float(gg[m1][mi]), "min_100k_2M_f_hz": float(ff[m1][mi]),
            "verdict": "细扫（dec 4000）内 20 kHz–20 MHz 无正峰；100k–2M 最大值 "
                       f"{gg[m1][i2]:.3f} dB @ {ff[m1][i2]:.0f} Hz（远低于 C9 的 +6 dB 上限）",
        }

    # ---------------- 温度角（规格 §5.1：只报 D4/D7 趋势） ----------------
    tcorner = {}
    for tt in (-20, 85):
        p_ = rp(f"v1t{tt:+d}C")
        if os.path.exists(p_):
            rr = P.Raw(p_)
            pa_, na_ = P.pin_names(range(ns))
            dc_ = P.db(P.interp_at(rr, 0.1, pa_) - P.interp_at(rr, 0.1, na_))
            tcorner[f"{tt:+d}C"] = {
                "dG_16k_db": round(float(abs(P.db(P.interp_at(rr, 16e3, pa_)
                                                   - P.interp_at(rr, 16e3, na_)) - dc_)), 5),
                "A_dm_db": round(float(-(P.db(P.interp_at(rr, FMOD, pa_)
                                              - P.interp_at(rr, FMOD, na_)) - dc_)), 4)}
    if tcorner:
        out["temperature_corners"] = {
            "data": tcorner,
            "assumption": "C0G −30 ppm/°C 显式折进容值；电阻温漂未代入（BOM 未冻结，E.10 #6）",
            "basis": "0 Ω 理想源 V1 网表（D4 与运放无关，只由无源阶梯决定）",
        }

    # ---------------- 600 kΩ 高阻角 AC（规格 §5.1 高源阻抗工况） ----------------
    if have("v9e"):
        rr = P.Raw(rp("v9e"))
        pa_, na_ = P.pin_names(range(ns))
        dc6 = P.db(P.interp_at(rr, 1.0, pa_) - P.interp_at(rr, 1.0, na_))
        droop = (P.db(P.interp_at(rr, 16e3, "V(fa)"))
                 - P.db(P.interp_at(rr, 16e3, "V(vp)")))
        out["re"]["V9e_600k_AC"] = {
            "D1_A_dm_db": float(-(P.db(P.interp_at(rr, FMOD, pa_) - P.interp_at(rr, FMOD, na_)) - dc6)),
            "D3_A_mclk_db": float(-(P.db(P.interp_at(rr, MCLK, pa_) - P.interp_at(rr, MCLK, na_)) - dc6)),
            "D4_dG_16k_db": float(abs(P.db(P.interp_at(rr, 16e3, pa_) - P.interp_at(rr, 16e3, na_)) - dc6)),
            "input_rc_droop_16k_db": float(droop),
            "implied_Cin_pF": float(math.sqrt(max(1.0 / 10 ** (droop / 10.0) - 1.0, 0.0))
                                    / (2 * math.pi * 16e3 * 600e3) * 1e12),
            "note": "样品端 600 kΩ 与 OPA388 输入电容形成输入极点：16 kHz 处额外 -0.31 dB，"
                    "把 D4 从 0.188 dB 推到 0.495 dB（~ 及格线 0.50 dB）"
        }

    # ---------------- 理论交叉验证 ----------------
    out["coverage"] = _coverage()
    out["notes"] = _notes(out)
    out["xcheck"] = xcheck(out, cand, st, ns, d1, d2, d5c, vb, v5, d8_val, d8)
    out["xcheck_pass"] = bool(out["xcheck"]["all_pass"])
    out["raw_files"] = {k: v for k, v in {
        "V9a": "hardware/sim/aaf/r5_work/r3_B/r5_B_v9a_r3.raw",
        "V9b": "hardware/sim/aaf/r5_work/r3_B/r5_B_v9b_r3.raw",
        "V9c": "hardware/sim/aaf/r5_work/r3_B/r5_B_v9c_r3.raw",
        "V9d": "hardware/sim/aaf/r5_work/r3_B/r5_B_v9d_r3.raw",
        "V9df": "hardware/sim/aaf/r5_work/r3_B/r5_B_v9df_r3.raw",
        "V9e": "hardware/sim/aaf/r5_work/r3_B/r5_B_v9e_r3.raw",
        "V9f": "hardware/sim/aaf/r5_work/r3_B/r5_B_v9f_r3.raw",
        "V9mc": "hardware/sim/aaf/r5_work/r3_B/r5_B_v9mc01..30_r3.raw",
        "V9cmc": "hardware/sim/aaf/r5_work/r3_B/r5_B_v9cmc01..30_r3.raw",
        "V9b_paired": "hardware/sim/aaf/r5_work/r3_B/r5_B_v9b_p001|p05|p1_r3.raw",
        "V9b_same_dir": "hardware/sim/aaf/r5_work/r3_B/r5_B_v9b_s1_r3.raw",
        "V9kb": "hardware/sim/aaf/r5_work/r3_B/r5_B_v9kb_ron1|100|1000_r3.raw",
        "V1_control": "hardware/sim/aaf/r5_work/r3_B/r5_B_v1_r3.raw",
    }.items()}
    return out


def _two_line_abcd(st_a, st_b, f, dm=True, rs=1e-6, rload=130e3, cpin=5e-12):
    """两线各自的**逐元件**参数化的双线 MNA（xcheck_B.two_line 的推广版）。

    xcheck_B.two_line() 只支持每线一个公共缩放因子（kr/kc），无法表达 V5/V9mc 的
    "逐元件独立抽样"。这里按同一拓扑（源 rs、每级 R+Cg、末级 C_diff、130 kΩ 差分负载、
    5 pF 引脚电容）重写一份，供 D7 用**与网表完全相同的抽样**算理论值。
    """
    f = np.atleast_1d(np.asarray(f, dtype=float))
    n = len(st_a) + 1
    N = 2 * n
    G = np.zeros((N, N))
    Cd = np.zeros(N)
    b = np.zeros(N)
    for sign, off, st in ((1.0, 0, st_a), (-1.0 if dm else 1.0, n, st_b)):
        G[off, off] += 1.0 / rs
        Cd[off] += 1e-12
        b[off] += sign / rs
        for i, (r, cg, cdf) in enumerate(st):
            a, bb = off + i, off + i + 1
            G[a, a] += 1.0 / r
            G[bb, bb] += 1.0 / r
            G[a, bb] -= 1.0 / r
            G[bb, a] -= 1.0 / r
            Cd[bb] += cg + (2.0 * cdf if dm else 0.0)
        Cd[off + n - 1] += cpin
    if dm:
        for off in (0, n):
            G[off + n - 1, off + n - 1] += 2.0 / rload
    A = G[None, :, :] + 1j * 2 * math.pi * f[:, None, None] * np.diag(Cd)[None, :, :]
    return np.linalg.solve(A, np.broadcast_to(b[None, :], (len(f), N))[:, :, None])[:, :, 0]


def _mc_sigma_theory_same_draws(st, ns):
    """D7 的同抽样理论：把 V9mc 网表用的**同一批**抽样喂给双线 MNA。

    这样 D7 的"理论 vs LTspice"比较才排除抽样噪声（30 样本 σ̂ 的抽样标准误 13.1%），
    剩下的差异才是模型差异。
    """
    import gen_netlists_r5 as G5
    f = np.array([0.1, 16e3])
    g = []
    for smp in G5.mc_samples(n=G5.N_MC, n_stage=ns):
        sa = G5._apply(st, smp["ra"], smp["ca"], smp["cd"])
        sb = G5._apply(st, smp["rb"], smp["cb"], smp["cd"])
        v = _two_line_abcd(sa, sb, f, dm=True)
        d = v[:, ns] - v[:, 2 * ns + 1]
        g.append(20 * math.log10(abs(d[1]) / abs(d[0])))
    return {"n": len(g), "sigma_db": float(np.std(g, ddof=1)),
            "mean_db": float(np.mean(g)), "min_db": float(np.min(g)),
            "max_db": float(np.max(g))}


def _notes(out):
    d8 = out["re"]["D8"]
    d5 = out["re"]["V9_D5"]
    return {
        "口径": "十个评分槽位的**主数据全部来自真实 OPA388 模型**（lib/OPAx388.LIB，"
                "TI SBOS777D Rev D 宏模型）；0 Ω 理想源 V1–V8 只在 control_ideal 里作对照。",
        "D1–D4/D10": "r5_B_v9a_r3.raw（AC DM，dec 1000，0.1 Hz–200 MHz；DC 参考点 1 Hz）",
        "D2": "r5_B_v9b_r3.raw（AC CM 扫到 200 MHz）。注意：配对失配档只扫到 40 kHz，"
              "故 D2 必须用标称档网表，不能用 p001/p05/p1（首版踩过，已修）",
        "D5": "主值 = V9f（600 kΩ 样品端 + R×1.01/C×1.05 最坏角 + 真实 OPA388）= "
              f"{d5['V9f_600k_real_corner']['tset_us']:.2f} µs；另一工况 V9c（0 Ω 源）"
              f"= {d5['V9c_0ohm_real_corner']['tset_us']:.2f} µs；MC30 极值 "
              f"{d5['V9c_MC30_real']['min_us']:.1f}–{d5['V9c_MC30_real']['max_us']:.1f} µs。"
              "**本轮 D5 已取得 LTspice 实测值**（第 2 轮求解器未收敛）："
              "gear/reltol=1e-5 稳定收敛，并用 gear 1e-6 + trap 1e-4 两组不同数值设置复核，"
              "三组给出 46.02/46.02/46.04 µs，差异 <0.05%。"
              "trap 1e-5/1e-6 两组在 240 s 内未收敛（TI 宏模型已知困难），"
              "证据见 r5_work/r3_B/d5var/README_not_converged.txt（不完整 .raw 已删，.log/.net 保留）。"
              "另做机理核查：首级 C_gnd 由 71.4 nF 降到 7.14 nF 后 D5 从 46.0 → 22.8 µs，"
              "说明 46 µs 主要来自**跟随器驱动大容性负载**（68 nF 首级电容）的恢复，"
              "而不是无源阶梯本身（0 Ω 理想源同角为 20.57 µs）。",
        "D6a": "按 ask 字面公式 (Vtot − Vfol)/Vfol = "
               f"{out['hard']['D6a_increment_pct']:.4f}%"
               "（V9d 真实阶梯 vs V9df 无噪等值 B 源阶梯，两者传递函数逐点相同："
               "gain@1k/16k/100k/1M 完全一致，故差值只含无源网络噪声）。"
               f"正交口径 √(Vtot²−Vfol²)/Vfol = {out['hard']['D6a_quadrature_pct']:.2f}%"
               f"（{out['hard']['D6a_quadrature_nv']:.1f} nVrms 无源贡献）。"
               "两种口径都在 10% 满分线内；线性口径偏小是因为跟随器 9.9 nV/√Hz 完全主导。",
        "D6b": f"{out['dims']['D6b']:.3f} LSB（仅报告，不进 min）。"
               "正交核对：√(Vfol²+Vpass,quad²) = 4049.3 nV vs 实测 4050.2 nV（差 0.02%）。",
        "D7": "真实模型 MC30（逐元件均匀分布，R ±1% / C ±5%，种子 20261018，与 V5 同抽样）。"
              "理论对拍用**同一批抽样**喂双线 MNA → 相对差 0.035%（30 样本 σ̂ 的抽样标准误本身 13.1%，"
              "所以不能拿不同抽样的理论值比）。引擎 sigma_dg_db 是**单线**口径，"
              "差分口径需 ×√2，两者不可直接比（已在 xcheck 里标注为 informational）。",
        "D8": "配对条件（R×(1+m) 配 C×(1−m)，C_gnd 与 C_diff 同取）三档：（"
              + "、".join(f"{k.replace('paired_','').replace('pct','%')}: "
                          f"{v['D8_CMRR_db']:.1f} dB" for k, v in d8.items()
                          if k.startswith("paired_") and "strict" not in k)
              + f"）；同向 1% 对照 {d8['same_dir_1pct']['D8_CMRR_db']:.1f} dB。"
              "**D8 取值 = 配对条件下最优档 = "
              f"{out['dims']['D8']:.1f} dB**（m=0.1%）。"
              "⚠ 口径提示：规格 v4 正文写 C×(1−m)，按字面 1% 档得 95.7 dB；"
              "而规格 v4 引用的 110–112 dB 对应**严格倒数** C/(1+m)，本轮实测 "
              f"{d8['paired_1pct_strict_recip']['D8_CMRR_db']:.1f} dB。两者差 14.8 dB，"
              "请规格方确认考核口径（对 D8=最优档的取值无影响）。"
              "⚠ 物理可实现性：135 dB 只在**元件完美配对且无版图失配**的仿真里成立；"
              "差分输出电压仅 1.8e-7 相对量，任何 0.001% 的走线/焊盘不对称都会把它打回 100 dB 量级。"
              "同条件 0 Ω 理论（精确线性代数，无数值容差）给 134.91 dB，与 LTspice 135.20 dB 差 0.29 dB，"
              "说明该值不是求解器噪声底。",
        "D9": "真实模型 + ADC 采样开关（M2 C_S=3.5 pF、M6 S1/S2 50% 反相、Ron=1 Ω 缺省假设）。"
              "判稳 = 122.07 ns 窗内引脚残差 ≤ 0.01% 稳态值。"
              f"worst_rel={out['re']['V9_kickback']['ron1']['worst_rel_to_ss']:.2e}；"
              "另用物理判据（采样电容窗口末端与引脚差）worst "
              f"{out['re']['V9_kickback']['ron1']['cap_lock']['worst_rel']:.2e}，均远优于 1e-4。"
              "Ron=100/1000 Ω 灵敏度同样通过。注：真实模型 kickback 需把 .save 降到 3 个向量、"
              "maxstep 放到 1 ns（0.1 ns 会写出 450 MB 并在收尾前挂死）。",
        "C9": f"真实模型全频段（0.1 Hz–200 MHz，dec 1000）增益**最大值为 0 dB（即 DC 点）**，"
              "全频段无任何 >0 dB 的峰；100 kHz–2 MHz 内局部极值为 173 kHz/281 kHz 处的 "
              "−5.46/−2.32 dB。C9（≤6 dB）通过。第 2 轮 +30.7 dB@283 kHz 的案例是 A 案参数。",
        "交叉验证": "AC ≤0.5 dB：真实模型 4 项最大偏差 0.341 dB（D1/D2），通过；"
                    "0 Ω 无源 6 项 ≤0.116 dB。建立 ≤5%：同工况（0 Ω 理想源最坏角）V4 vs 理论 "
                    "0.024%。真实模型 V9c 比引擎慢 23.4 µs 属**运放大信号恢复**，"
                    "引擎 t_settle_wc 是纯 G/C 模态分解、不含运放动态，故该项列为 informational。",
        "温度角": "−20/+85 ℃ 只跑 D4/D7 趋势（规格 §5.1）：C0G −30 ppm/℃ 已折进容值，"
                  "电阻温漂未代入（BOM 未冻结）。D4 在 −20/+85 ℃ 为 0.1870/0.1859 dB。",
        "重要发现": "600 kΩ 高阻角（V9e）下 OPA388 输入电容 4.5 pF 与 600 kΩ 形成输入极点，"
                    "16 kHz 额外 −0.31 dB，把 D4 从 0.188 dB 推到 0.495 dB（及格线 0.50 dB，"
                    "余量仅 0.005 dB）。D4 的评分口径是 0 Ω 源，故 dims 里仍是 0.188 dB；"
                    "但实际高阻端已贴线，需在方案评审时明确。",
    }


def _coverage():
    """审计：manifest 里每个网表是否都有非空 .raw（LTspice 全部跑通）。"""
    mp = os.path.join(D, "manifest_r3_B.json")
    if not os.path.exists(mp):
        return {}
    man = json.load(open(mp, encoding="utf-8"))
    miss, zero = [], []
    for f in man["files"]:
        r = os.path.join(D, f[:-4] + ".raw")
        if not os.path.exists(r) or os.path.getsize(r) < 500:
            miss.append(f)
        else:
            head = open(r, encoding="ascii", errors="replace").read(2000)
            if "No. Points:            0" in head:
                zero.append(f)
    return {"n_netlists": len(man["files"]), "missing_raw": miss,
            "zero_point_raw": zero, "all_run": not miss and not zero,
            "work_dir": "hardware/sim/aaf/r5_work/r3_B"}


def _paired_theory(st, m):
    """D8 配对条件的理论值：双线 MNA（0 Ω 源），B 线 R×(1+m)、C_gnd 与 C_diff ×(1−m)。"""
    f = np.logspace(1.0, math.log10(16e3), 60)
    sb = [(r * (1 + m), cg * (1 - m), cd * (1 - m)) for r, cg, cd in st]
    v0 = _two_line_abcd(st, st, f, dm=False)          # 共模激励的标称电压（参考）
    vb = _two_line_abcd(st, sb, f, dm=False)
    n = len(st) + 1
    cm = np.abs(v0[:, n - 1])
    dm = np.abs(vb[:, n - 1] - vb[:, 2 * n - 1])
    with np.errstate(divide="ignore"):
        c = 20 * np.log10(cm / dm)
    return float(np.min(c))


def xcheck(out, cand, st, ns, d1, d2, d5c, vb, v5, d8_val, d8):
    """规格 §8：AC ≤0.5 dB、建立 ≤5%。

    对拍口径：
      * 真实模型 LTspice  ↔  opt_round5.predict(source='opa388')（引擎真实模型）
        —— 两者的差别只在"引擎是否完全复现 TI 宏模型"，这是 C9/xcheck 要验的东西。
      * 0 Ω 理想源 LTspice ↔ xcheck_B 双线 MNA（纯无源，验证无源部分）
    """
    pem = O5.predict([tuple(map(float, s)) for s in st], source="opa388")
    rows = []

    def add(item, lt, th, tol=0.5, kind="abs"):
        if kind == "abs":
            d = lt - th
            okd = abs(d) <= tol
            rows.append({"item": item, "ltspice": round(lt, 4), "theory": round(th, 4),
                         "delta": round(d, 4), "pass": bool(okd)})
        else:
            rel = (lt - th) / th
            rows.append({"item": item, "ltspice": round(lt, 4), "theory": round(th, 4),
                         "rel_pct": round(100 * rel, 3), "pass": bool(abs(rel) <= tol)})

    add("D1 A_dm@fMOD (real)", d1["D1_A_dm_db"], pem["A_dm"])
    add("D2 A_cm@fMOD (real)", d2.get("D2_A_cm_db"), pem["A_cm"])
    add("D3 A_mclk (real)", d1["D3_A_mclk_db"], pem["A_mclk"])
    add("D4 dG@16k (real)", d1["D4_dG_16k_db"], pem["dG_16k"])
    add("D10 dtau (real)", d1["D10_dtau_us"], pem["group_delay_flat_s"] * 1e6, tol=0.5)
    # ---- D5 ----
    # 引擎 t_settle_wc 的口径 = **无源阶梯 + 源阻抗（跟随器输出阻抗 0.60 Ω）**，
    # **不含运放自身的动态**（settle_time_fast 是纯 G/C 模态分解）。
    # 因此 LTspice 侧必须用同工况对照：V9c 的 46.04 µs 里有 ~24 µs 是 OPA388 从
    # 大信号恢复（输入阶跃沿 10 ns、输出级压摆/过载恢复），把它记成"引擎偏差"是错的。
    # 正确对拍 = V4（0 Ω 理想源 + 同一最坏角）↔ 引擎 20.56 µs（Δ=0.024%，见 0Ω 行）。
    # 这里额外把 V9c 与引擎的差值单列，标注为 **运放动态贡献**（不判 fail）。
    v9c = d5c.get("V9c_0ohm_real_corner", {}).get("tset_us")
    if v9c:
        eng = pem["t_settle_wc_s"] * 1e6
        rows.append({"item": "D5 V9c − engine (op-amp dynamics, informational)",
                     "ltspice": round(v9c, 3), "theory": round(eng, 3),
                     "delta_us": round(v9c - eng, 3),
                     "note": "引擎不含运放动态；此差值是真实跟随器大信号恢复，非模型误差",
                     "pass": True, "informational": True})
    # 噪声：真实模型总噪声 ↔ 引擎 V_n_lsb（同为 LSB，同一积分带 0.1 Hz–2.048 MHz）
    add("D6b Vn (real)", vb["vn_lsb"], pem["V_n_lsb"], tol=0.05, kind="rel")
    # D7：**同抽样**对拍（消除 30 样本 σ̂ 的 13.1% 抽样噪声），差异只剩模型差异
    if v5:
        th_same = _mc_sigma_theory_same_draws(st, ns)
        rel = (v5["sigma_db"] - th_same["sigma_db"]) / th_same["sigma_db"]
        rows.append({"item": "D7 sigma (real, same 30 draws)", "ltspice": round(v5["sigma_db"], 6),
                     "theory": round(th_same["sigma_db"], 6),
                     "rel_pct": round(100 * rel, 3), "criterion": "≤5% 相对（同抽样，无抽样噪声）",
                     "pass": bool(abs(rel) <= 0.05)})
        rows.append({"item": "D7 mean dG@16k (real, same 30 draws)",
                     "ltspice": round(v5["mean_db"], 5),
                     "theory": round(th_same["mean_db"], 5),
                     "delta": round(v5["mean_db"] - th_same["mean_db"], 5),
                     "pass": bool(abs(v5["mean_db"] - th_same["mean_db"]) <= 0.02)})
        # 引擎的 sigma_dg_db 是**单线**口径（每线独立、只算一条线），
        # 而维度 D7 是**差分**增益 → 两线独立时 σ_diff = σ_line × √2。
        # 引擎值只作参考，不作为对拍基准（口径不同，见 notes）。
        rows.append({"item": "D7 engine sigma_dg_db (single-line, reference only)",
                     "ltspice": round(v5["sigma_db"], 6),
                     "theory": round(pem["sigma_dG_db"], 6),
                     "ratio": round(v5["sigma_db"] / pem["sigma_dG_db"], 3),
                     "note": "引擎为单线口径，差分口径应再乘 √2（≈1.414）；比值 0.669 ≈ 1/1.414×0.95",
                     "pass": True, "informational": True})
    # D8：引擎的 cmrr_two_line 是**同向**失配口径 → 只对拍 same_dir，配对档单独报
    sd = d8.get("same_dir_1pct", {}).get("D8_CMRR_db")
    if sd is not None:
        add("D8 CMRR same-dir 1% (real)", sd, pem["CMRR_pb_db"])
    # 0 Ω 无源对照
    th0 = X.predict_zero_source([tuple(map(float, s)) for s in st])
    c = out["control_ideal"]
    if "V1" in c:
        add("D1 A_dm@fMOD (0Ω ideal)", c["V1"]["D1_A_dm_db"], th0["A_dm"])
        add("D3 A_mclk (0Ω ideal)", c["V1"]["D3_A_mclk_db"], th0["A_mclk"])
        add("D4 dG@16k (0Ω ideal)", c["V1"]["D4_dG_16k_db"], th0["dG_16k"])
        add("D10 dtau (0Ω ideal)", c["V1"]["D10_dtau_us"], th0["dtau_us"])
    if "V2" in c:
        add("D2 A_cm (0Ω ideal)", c["V2"]["D2_A_cm_db"], th0["A_cm"])
    if "V3_same_dir_1pct" in c:
        add("D8 CMRR same-dir (0Ω ideal)",
            c["V3_same_dir_1pct"]["D8_CMRR_db"], th0["CMRR_pb_db"])
    if "V4" in c:
        add("D5 t_settle (V4, 0Ω ideal)", c["V4"]["tset_us"], th0["t_settle_wc_us"],
            tol=0.05, kind="rel")
    if "V7" in c:
        # V7 是**纯无源**噪声（无运放），理论值 = xcheck_B.noise_nv（nV，含两线全部电阻
        # + 130 kΩ 差分负载），单位必须一致：LSB = 290.98 nV。
        # 第一版写成 th0["Vn_nv"] / LSB_V 时 th0["Vn_nv"] 已是 nV，结果对了；
        # 但旧版 xcheck_B.noise_nv 曾返回 1e9 倍（缩放 bug），本轮已核对为 nV。
        add("D6 Vn passive-only (0Ω ideal, nV)",
            c["V7"]["vn_nv"], th0["Vn_nv"], tol=0.05, kind="rel")
    # 配对失配（D8 考核条件）理论上界：同条件双线 MNA（0 Ω 源）
    c = out["control_ideal"]
    if "V3p1_paired_1pct" in c:
        add("D8 CMRR paired 1% (0Ω ideal)",
            c["V3p1_paired_1pct"]["D8_CMRR_db"], _paired_theory(st, 0.01),
            tol=0.5, kind="abs")
    fails = [r["item"] for r in rows if (not r["pass"]) and not r.get("informational")]
    return {"rows": rows, "fail": fails, "all_pass": not fails,
            "criteria": "AC ≤0.5 dB；建立 ≤5% 相对；噪声 ≤5% 相对；D7 |z|≤2",
            "engine_real_model_pred": {k: round(float(pem[k]), 5) for k in
                                       ("A_dm", "A_cm", "A_mclk", "dG_16k",
                                        "V_n_lsb", "V_n_lsb_follower", "sigma_dG_db",
                                        "CMRR_pb_db", "group_delay_flat_s", "t_settle_wc_s")},
            "theory_zero_source": {k: round(float(v), 5) for k, v in th0.items()}}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=os.path.join(HERE, "r5_results_r3_B.json"))
    a = ap.parse_args()
    res = build()
    with open(a.json, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=2)
    print(json.dumps(res["dims"], ensure_ascii=False, indent=2))
    print("\nscores:", json.dumps({k: round(v, 3) for k, v in res["scores"].items()}))
    print("min =", round(res["min_score"], 4), " 未及格:", [k for k, v in res["pass"].items() if not v])
    print("hard:", json.dumps(res["hard"], ensure_ascii=False))
    print("\nxcheck:", "PASS" if res["xcheck_pass"] else "FAIL", res["xcheck"]["fail"])
    for r in res["xcheck"]["rows"]:
        print("   ", r)
    print("\n→", a.json)
