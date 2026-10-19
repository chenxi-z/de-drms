#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""parse_r5_r4_B.py — 第 4 轮方案 B（C9 修复定档参数）十维实测提取 + 理论交叉验证

数据来源：`r5_work/r4_B/r5_B_r4_*.raw`（gen_netlists_r5_r4.py 生成、run_r4_B.py 批跑）

**全部维度主口径 = 真实 OPA388 模型**（lib/OPAx388.LIB，TI SBOS777D Rev D 宏模型）。
0 Ω 理想源只保留 v1i/v2i/v4i/v7i 四个网表，用于规格 §8 的「纯无源理论 ↔ 理想源 LTspice」
同口径对拍（A 块），不参与打分。

十维键
  D1 A_dm@4.096 MHz (dB)   D2 A_cm@4.096 MHz (dB)   D3 A_dm@16.384 MHz (dB)
  D4 |ΔG|@16 kHz (dB)      D5 建立 µs（0.01% 带，源阻抗五档取最慢）
  D6a 无源网络噪声增量 %（(V_tot−V_nl)/V_nl，同带宽同传函）
  D6b 总积分噪声 LSB（0.1 Hz–2.048 MHz，仅报告）
  D7 σ(ΔG@16k) (dB)        D8 CMRR@通带最差（R·C 乘积异向配对，1% 档为主）
  D9 kickback 122.07 ns 回稳（二值）   D10 Δτ@0.1 Hz–16 kHz (µs)
另报 C9：跟随器节点 peaking 与 ADC 引脚 peaking（两处都测）。

用法
----
    python parse_r5_r4_B.py --json r5_results_r4_B.json
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

from parse_r5 import (                       # noqa: E402
    LSB_V, FMOD, MCLK, TBAND_SPEC, TBAND_DIFF, Raw, db, interp_at,
    settle_us, noise_nv, kickback,
)
from parse_r5_A import _cap_lock             # noqa: E402  D9 的物理判据
import opt_round5 as O5                      # noqa: E402  真实模型理论引擎
import xcheck_B as X                         # noqa: E402  0 Ω 纯无源双线 MNA
import r5_score_v4 as S4                     # noqa: E402  D8 配对口径

D = os.path.join(HERE, "r5_work", "r4_B")
CAND = os.path.join(HERE, "r5_candidates_final_B.json")
TAGS = {
    "D1": "r5_B_r4_v1.raw @4.096 MHz（真实 OPA388）",
    "D3": "r5_B_r4_v1.raw @16.384 MHz",
    "D4": "r5_B_r4_v1.raw @16 kHz 相对 DC",
    "D10": "r5_B_r4_v1.raw 群延迟 0.1 Hz–16 kHz",
    "D2": "r5_B_r4_v2.raw @4.096 MHz 共模",
    "D5": "r5_B_r4_v9f_s*_r4 五档源阻抗 × 三套数值设置",
    "D6a": "r5_B_r4_v9d.raw vs r5_B_r4_v9d_nl.raw 同带宽积分噪声",
    "D6b": "r5_B_r4_v9d.raw 积分 0.1 Hz–2.048 MHz",
    "D7": "r5_B_r4_v5mc01..30.raw（真实模型逐元件 MC，R±1%/C±5%）",
    "D8": "r5_B_r4_v3p010.raw（R×1.01 配 C×0.99，10 Hz–16 kHz 最差）",
    "D9": "r5_B_r4_v8r_ron1.raw（真实 OPA388 + ADC 采样开关模型）",
}
D5_RS_K = (10, 50, 100, 220, 600)
D5_SETTINGS = ("gear20n", "trap60us", "gear5n")


def R(tag):
    p = os.path.join(D, f"r5_B_r4_{tag}.raw")
    return Raw(p) if os.path.exists(p) else None


def _pin(ns=3):
    return f"V(pa{ns})", f"V(na{ns})"


# ------------------------------------------------------------------ AC
def ac_dm(raw, ns=3, label=""):
    pa, na = _pin(ns)
    f = np.asarray(raw.f, float)
    p = np.asarray(raw.col(pa), complex)
    n = np.asarray(raw.col(na), complex)
    dm = p - n
    g = 20 * np.log10(np.abs(dm) / abs(dm[0]))
    o = {
        "g_dc_db": float(g[0]),
        "g_16k_db": float(np.interp(16e3, f, g)),
        "D1_A_dm_db": float(-np.interp(FMOD, f, g)),
        "D3_A_mclk_db": float(-np.interp(MCLK, f, g)),
        "D4_dG_16k_db": float(abs(np.interp(16e3, f, g))),
        "pin_peak_db": float(np.max(g)),
        "pin_peak_hz": float(f[int(np.argmax(g))]),
    }
    # C9：跟随器输出节点（谐振发生在被驱动节点）
    foll = {}
    for nm in ("V(fpa)", "V(fna)"):
        if nm in raw.names:
            y = np.asarray(raw.col(nm), complex)
            gg = 20 * np.log10(np.abs(y) / abs(y[0]))
            foll[nm] = {"peak_db": float(np.max(gg)),
                        "peak_f_hz": float(f[int(np.argmax(gg))])}
    if foll:
        w = max(foll.values(), key=lambda d: d["peak_db"])
        o["follower_peak_db"] = w["peak_db"]
        o["follower_peak_f_hz"] = w["peak_f_hz"]
        o["follower_per_line"] = foll
    # D10
    m = (f >= 0.1) & (f <= 16e3)
    ph = np.unwrap(np.angle(dm[m]))
    tau = -np.gradient(ph, 2 * math.pi * f[m])
    o["D10_dtau_us"] = float((tau.max() - tau.min()) * 1e6)
    o["tau_100Hz_us"] = float(tau[0] * 1e6)
    o["tau_16k_us"] = float(tau[-1] * 1e6)
    # CH1 vs CH2（同一差分对两腿）群延迟差 —— 规格 §5.1a 要求单列
    tp = -np.gradient(np.unwrap(np.angle(p[m])), 2 * math.pi * f[m])
    tn = -np.gradient(np.unwrap(np.angle(n[m])), 2 * math.pi * f[m])
    o["legs_tau_diff_ns"] = float(np.max(np.abs(tp - tn)) * 1e9)
    if label:
        o["label"] = label
    return o


def ac_cm(raw, ns=3):
    pa, _ = _pin(ns)
    f = np.asarray(raw.f, float)
    p = np.asarray(raw.col(pa), complex)
    g = 20 * np.log10(np.abs(p) / abs(p[0]))
    return {"D2_A_cm_db": float(-np.interp(FMOD, f, g)),
            "g_cm_dc_db": float(g[0]),
            "g_cm_fmod_db": float(np.interp(FMOD, f, g))}


def cmrr_passband(raw, ns=3, f_lo=10.0, f_hi=16e3):
    pa, na = _pin(ns)
    f = np.asarray(raw.f, float)
    p = np.asarray(raw.col(pa), complex)
    n = np.asarray(raw.col(na), complex)
    m = (f >= f_lo) & (f <= f_hi)
    cm = np.abs((p[m] + n[m]) / 2.0)
    dm = np.abs(p[m] - n[m])
    r = 20 * np.log10(cm / np.maximum(dm, 1e-300))
    k = int(np.argmin(r))
    return {"CMRR_db": float(r[k]), "worst_f_hz": float(f[m][k]),
            "cmrr_10Hz_db": float(r[0]), "cmrr_16k_db": float(r[-1]),
            "n_pts": int(m.sum())}


# ------------------------------------------------------------------ 瞬态
def tran_scan(tag, ns=3):
    """建立时间 + 是否真的回稳（尾窗判据）。"""
    p = os.path.join(D, f"r5_B_r4_{tag}.raw")
    if not os.path.exists(p):
        return None
    rr = Raw(p)
    t = np.asarray(rr.cols[0], float)
    d = (np.asarray(rr.col(_pin(ns)[0]), float)
         - np.asarray(rr.col(_pin(ns)[1]), float))
    m = t >= 0.75 * t[-1]
    tail = d[m]
    pp = float(tail.max() - tail.min())
    out = {"t_end_us": float(t[-1] * 1e6),
           "tail_pp_uv": pp * 1e6,
           "vss_v": float(np.median(tail)),
           "stable_200uV": bool(pp <= 200e-6),
           "stable_1mV": bool(pp <= 1e-3)}
    # 尾窗振荡频率（用 fpa 过零）
    for nm in ("V(fpa)", "V(fna)"):
        if nm in rr.names:
            y = np.asarray(rr.col(nm), float)[m]
            tt = t[m]
            s = np.where(np.diff(np.signbit(np.diff(y))))[0]
            if len(s) > 4:
                per = float(np.median(np.diff(tt[s])))
                out.setdefault("nodes", {})[nm] = {
                    "pp_mv": float((y.max() - y.min()) * 1e3),
                    "f_osc_khz": float(1.0 / per / 1e3)}
            else:
                out.setdefault("nodes", {})[nm] = {
                    "pp_mv": float((y.max() - y.min()) * 1e3), "f_osc_khz": 0.0}
    for band, nm in ((TBAND_SPEC, "spec_200uV"), (TBAND_DIFF, "engine_120uV")):
        ts, vf, ef = settle_us(rr, ns, band=band)
        out[nm] = {"tset_us": ts, "vfinal_v": vf, "err_final_uv": ef * 1e6}
    return out


# ------------------------------------------------------------------ 主流程
def build():
    with open(CAND, encoding="utf-8") as fh:
        cand = json.load(fh)
    st = [tuple(map(float, s)) for s in cand["stages"]]
    ns = len(st)
    res = {"scheme": "B", "round": 4, "n_stages": ns,
           "stages": st, "dir": D,
           "parameter_source": "r5_candidates_final_B.json (r4/c9-fix)",
           "units": {"D1/D2/D3/D4/D8/D10": "dB", "D5": "µs", "D6a": "%",
                     "D6b": "LSB", "D9": "binary"}}

    # ---- AC（真实模型）----
    r1 = R("v1")
    real = ac_dm(r1, ns, "v1 real OPA388 AC DM")
    real_cm = ac_cm(R("v2"), ns)
    ctl = ac_dm(R("v1i"), ns, "v1i ideal 0ohm AC DM")
    ctl_cm = ac_cm(R("v2i"), ns)

    # ---- AC 随源阻抗（C9/D4/D1 的高阻补充口径）----
    ac_rs = {}
    for k in (0, 10, 50, 100, 220, 600):
        rr = R(f"v9e_s{k:03d}k")
        if rr is None:
            continue
        o = ac_dm(rr, ns, f"v9e_s{k:03d}k")
        ac_rs[f"{k}k"] = {
            "D1_A_dm_db": o["D1_A_dm_db"], "D4_dG_16k_db": o["D4_dG_16k_db"],
            "follower_peak_db": o.get("follower_peak_db"),
            "follower_peak_hz": o.get("follower_peak_f_hz"),
            "pin_peak_db": o["pin_peak_db"], "pin_peak_hz": o["pin_peak_hz"],
        }
    res["c9_by_source"] = ac_rs
    # 温度角（规格 §5.1：只报 D4/D10 趋势；电阻温漂未代入）
    temp = {}
    for t in (-20, 85):
        rr = R(f"v1t{t:+d}C")
        if rr is None:
            continue
        o = ac_dm(rr, ns, f"v1t{t:+d}C")
        temp[f"{t:+d}C"] = {"D4_dG_16k_db": o["D4_dG_16k_db"],
                            "D10_dtau_us": o["D10_dtau_us"],
                            "D1_A_dm_db": o["D1_A_dm_db"]}
    if temp:
        temp["25C"] = {"D4_dG_16k_db": real["D4_dG_16k_db"],
                       "D10_dtau_us": real["D10_dtau_us"],
                       "D1_A_dm_db": real["D1_A_dm_db"]}
        temp["note"] = ("C0G −30 ppm/℃ 已折进容值；**电阻温漂未代入**"
                        "（BOM 未定型，E.10 #6）")
        res["temperature_corners"] = temp
    # C9 全工况最差值（0 Ω 主口径 + 五档源阻抗）
    _c9wb = max((v["follower_peak_db"] for v in ac_rs.values()
                 if v.get("follower_peak_db") is not None), default=None)

    # ---- D8（真实模型，配对主口径 1%）----
    d8 = {"paired": {}, "same_direction": {}}
    for m in (0.001, 0.005, 0.01):
        rr = R(f"v3p{int(m*1000):03d}")
        if rr:
            d8["paired"][f"{m*100:g}%"] = cmrr_passband(rr, ns)
    rr = R("v3s010")
    if rr:
        d8["same_direction"]["1%"] = cmrr_passband(rr, ns)
    # 规格正文 §5.1a：D8 考核条件 = R·C 乘积配对；记分取 1% 档（与规格正文一致）
    D8 = d8["paired"].get("1%", {}).get("CMRR_db")

    # ---- D7（真实模型 MC 30 次）----
    pa, na = _pin(ns)
    vals = []
    for k in range(1, 31):
        p = os.path.join(D, f"r5_B_r4_v5mc{k:02d}.raw")
        if not os.path.exists(p):
            continue
        rr = Raw(p)
        g = db(interp_at(rr, 16e3, pa) - interp_at(rr, 16e3, na))
        g0 = db(interp_at(rr, 0.1, pa) - interp_at(rr, 0.1, na))
        vals.append(g - g0)
    mc = ({"n": len(vals), "sigma_db": float(np.std(vals, ddof=1)),
           "mean_db": float(np.mean(vals)), "min_db": float(np.min(vals)),
           "max_db": float(np.max(vals)),
           "p2p_db": float(np.max(vals) - np.min(vals))} if vals else None)

    # ---- D6a / D6b ----
    nz = {}
    for tag in ("v9d", "v9d_nl", "v9n"):
        rr = R(tag)
        if rr:
            nz[tag] = noise_nv(rr)
    v_tot = nz["v9d"]["D6_Vn_nv"]
    v_nl = nz["v9d_nl"]["D6_Vn_nv"]
    v_alone = nz["v9n"]["D6_Vn_nv"]
    d6a_lin = 100.0 * (v_tot - v_nl) / v_nl
    d6a_quad = 100.0 * math.sqrt(max(v_tot ** 2 - v_nl ** 2, 0.0)) / v_nl
    d6b = nz["v9d"]["D6_Vn_lsb"]
    # 噪声谱峰（C9 的频域旁证）
    rr = R("v9d")
    f9 = np.asarray(rr.f, float)
    dn = np.abs(np.asarray(rr.col("v(onoise)"), float))
    i_pk = int(np.argmax(dn))
    noise_peak = {"dens_peak_nv": float(dn[i_pk] * 1e9),
                  "dens_peak_f_hz": float(f9[i_pk]),
                  "dens_1k_nv": float(np.interp(1e3, f9, dn) * 1e9),
                  "dens_1M_nv": float(np.interp(1e6, f9, dn) * 1e9),
                  "peak_over_1k_db": float(20 * math.log10(dn[i_pk] /
                                                           np.interp(1e3, f9, dn)))}

    # ---- D5（五档源阻抗 × 三套数值设置）----
    d5 = {}
    for k in D5_RS_K:
        base = f"v9f_s{k:03d}k"
        d5[f"{k}k"] = {"gear20n": tran_scan(base)}
        d5[f"{k}k"]["trap60us"] = tran_scan(base + "_trap")
        d5[f"{k}k"]["gear5n"] = tran_scan(base + "_gear5n")
    d5["0ohm_real_model"] = {"gear20n": tran_scan("v4")}
    d5["0ohm_ideal_source"] = {"gear20n": tran_scan("v4i")}
    # 每档是否出现等幅振荡（尾窗判据），并做「三设置一致性」判定
    summary = {}
    for k in D5_RS_K:
        row = d5[f"{k}k"]
        ts = {s: (row[s]["spec_200uV"]["tset_us"] if row[s] else None)
              for s in D5_SETTINGS}
        stb = {s: (row[s]["stable_200uV"] if row[s] else None)
               for s in D5_SETTINGS}
        got = [v for v in ts.values() if v is not None]
        spread = ((max(got) - min(got)) / min(got) * 100.0) if got else None
        summary[f"{k}k"] = {"tset_us": ts, "stable": stb,
                            "spread_pct": spread,
                            "settings_agree_5pct": (spread is not None
                                                    and spread <= 5.0)}
    all_ts = [v for row in summary.values() for v in row["tset_us"].values()
              if v is not None]
    all_stable = all(v for row in summary.values() for v in row["stable"].values()
                     if v is not None)
    D5 = max(all_ts) if all_ts else None

    # ---- D9 ----
    d9 = {}
    for ron in (1, 100, 1000):
        p = os.path.join(D, f"r5_B_r4_v8r_ron{ron:g}.raw")
        if not os.path.exists(p):
            continue
        rr = Raw(p)
        kb = kickback(rr, ns)
        kb["cap_lock"] = _cap_lock(rr, ns)
        d9[f"ron{ron:g}"] = kb
    D9 = float(d9["ron1"]["D9"]) if "ron1" in d9 else None

    dims = {
        "D1": real["D1_A_dm_db"],
        "D2": real_cm["D2_A_cm_db"],
        "D3": real["D3_A_mclk_db"],
        "D4": real["D4_dG_16k_db"],
        "D5": D5,
        "D6a": d6a_lin,
        "D6b": d6b,
        "D7": mc["sigma_db"] if mc else None,
        "D8": D8,
        "D9": D9,
        "D10": real["D10_dtau_us"],
    }
    res["dims"] = dims
    res["real_model"] = {**real, **real_cm,
                         "c9_follower_ok": bool(real.get("follower_peak_db", 9e9) <= 6.0),
                         "c9_pin_ok": bool(real["pin_peak_db"] <= 6.0)}
    res["control_ideal"] = {**ctl, **ctl_cm}
    res["c9_follower_db"] = real.get("follower_peak_db")
    res["c9_follower_hz"] = real.get("follower_peak_f_hz")
    res["c9_pin_db"] = real["pin_peak_db"]
    res["c9_pin_hz"] = real["pin_peak_hz"]
    res["c9_limit_db"] = 6.0
    res["c9_worst_over_sources_db"] = _c9wb
    res["c9_ok"] = bool(res["real_model"]["c9_follower_ok"]
                        and res["real_model"]["c9_pin_ok"]
                        and (_c9wb is not None and _c9wb <= 6.0))
    res["d5_by_source"] = summary
    res["D5_detail"] = d5
    res["D5_all_settings_stable"] = bool(all_stable)
    # 判别链结果（r5_d5_discrim_r4_B.json：含旧参数正对照）
    disc_p = os.path.join(HERE, "r5_d5_discrim_r4_B.json")
    if os.path.exists(disc_p):
        with open(disc_p, encoding="utf-8") as fh:
            dsc = json.load(fh)
        res["D5_discrimination"] = {
            "positive_control_old_B_100k": dsc.get("old_B_control", {}).get("100k"),
            "new_B_sweep": dsc.get("new_B_sweep"),
            "poles": dsc.get("poles"),
            "verdict": ("旧参数（R1=2.74）在 100 kΩ 三套设置下均给出 0.4989/0.5239/0.4993 Vpp "
                        "等幅振荡（FFT 峰 120/133/120 kHz）→ 判据敏感、且不是单一积分法伪影；"
                        "本轮参数五档 × 三设置尾窗 pp 最大 43.5 µV（trap 60 µs 窗的 45–60 µs "
                        "段），gear 与 trap 在**同一时间窗**上逐窗一致（如 100 kΩ：45–50 µs "
                        "28.90 vs 28.85 µV、55–60 µs 5.16 vs 5.13 µV），是仍在指数衰减的同一"
                        "尾段而非纹波，gear 400 µs 窗末已降到 0.004 µV → 50–220 kΩ 极限环在"
                        "本参数下消失，且不是数值伪影造成的假阴性"),
        }
    res["D8_detail"] = d8
    res["D7_detail"] = mc
    res["D6_detail"] = {
        "total_with_ladder_nv": v_tot,
        "ladder_R_noiseless_nv": v_nl,
        "follower_alone_fullband_nv": v_alone,
        "D6a_linear_pct": d6a_lin,
        "D6a_quadrature_pct": d6a_quad,
        "D6b_lsb": d6b, "D6b_nv": v_tot,
        "lsb_nv": LSB_V * 1e9,
        "noise_spectrum": noise_peak,
        "raw": {k: os.path.join(D, f"r5_B_r4_{k}.raw") for k in nz},
    }
    res["D9_detail"] = d9
    res["sources"] = TAGS
    res["highz"] = {
        "d4_at_600k_db": res["c9_by_source"]["600k"]["D4_dG_16k_db"],
        "d1_at_600k_db": res["c9_by_source"]["600k"]["D1_A_dm_db"],
        "limit_db": 0.50,
        "ok": bool(res["c9_by_source"]["600k"]["D4_dG_16k_db"] <= 0.50),
        "margin_db": float(0.50 - res["c9_by_source"]["600k"]["D4_dG_16k_db"]),
        "note": "规格 §5.1 标准测试条件 D4 是 0 Ω 源（= 0.1849 dB）；600 kΩ 端是"
                "客户使用工况的披露项。首级 R 由 2.74→6.19 Ω 后该项仍为 0.4924 dB，"
                "**距 0.5 dB 及格线只有 0.008 dB 余量**，来源是 600 kΩ×(OPA388 输入电容"
                "≈4.5 pF) 的输入极点，与本段阶梯无关。",
    }
    return res, cand, st, ns


def _notes(res):
    d5 = res["d5_by_source"]
    return {
        "口径": "十维主数据全部来自**真实 OPA388 模型**（lib/OPAx388.LIB，TI SBOS777D "
                "Rev D 宏模型，Green-Williams-Lis Final 1.4）；0 Ω 理想源仅 v1i/v2i/v4i/v7i "
                "四个网表作规格 §8 的 A 块（纯无源）同口径对拍。V1–V9 全部用 `.net` "
                "批处理（`LTspice.exe -b -ascii`），未用任何 `.asc`。",
        "D1–D4/D10/C9": "r5_B_r4_v1.raw（AC DM dec 400，0.1 Hz–200 MHz，DC 参考 0.1 Hz，"
                        "差分取 V(pa3)−V(na3)）。C9 同时保存 V(fpa)/V(fna)：跟随器节点 "
                        f"{res['c9_follower_db']:.3f} dB @ {res['c9_follower_hz']/1e3:.1f} kHz，"
                        f"引脚 {res['c9_pin_db']:.4f} dB。",
        "D2": "r5_B_r4_v2.raw（AC CM 扫到 200 MHz，取标称档；配对失配档只扫到 100 kHz 不够取 fMOD）。",
        "D5": "五档源阻抗 10k/50k/100k/220k/600k（R×1.01 / C×1.05 最坏角）+ 0 Ω 对照，"
              "每档三套数值设置。取全部档位全部设置里**最慢**的 "
              f"{res['dims']['D5']:.2f} µs（220 kΩ / gear20n）。判据 = 2 V 差分阶跃、10 ns 沿、"
              "0.01%(200 µV) 差分带。",
        "D5_稳定性": _d5_verdict(res),
        "D6a": _d6a_note(res),
        "D6b": f"{res['dims']['D6b']:.3f} LSB（0.1 Hz–2.048 MHz，仅报告不进 min）。",
        "D7": "真实模型 MC30（逐元件均匀分布，R ±1% / C ±5%，种子 20261018，与引擎同抽样）。"
              f"LTspice σ = {res['dims']['D7']:.5f} dB；同抽样双线 MNA 理论 "
              f"{res['xcheck'].get('D7_same_draws', {}).get('sigma_db', float('nan')):.5f} dB，"
              f"相对差 {res['xcheck'].get('D7_same_draws', {}).get('rel_pct', float('nan')):.2f}%"
              "（排除抽样噪声后再比）。",
        "D8": "R·C 乘积异向配对（B 线 R×(1+m) 配 C×(1−m)，C_gnd 参与配对，C_diff 是跨接"
              "两线的共享件故不参与逐线配对）。三档：0.1% "
              f"{res['D8_detail']['paired']['0.1%']['CMRR_db']:.2f} dB、0.5% "
              f"{res['D8_detail']['paired']['0.5%']['CMRR_db']:.2f} dB、1% "
              f"{res['D8_detail']['paired']['1%']['CMRR_db']:.3f} dB（记分用 1%，与规格正文一致）；"
              "同向 1% 对照 "
              f"{res['D8_detail']['same_direction']['1%']['CMRR_db']:.2f} dB。"
              "⚠ 若改用**严格倒数**口径 C/(1+m)，1% 档理论值是 "
              f"{res['xcheck']['B_real_model']['cmrr_1pct_paired']['theory_exact_inverse_db']:.2f} dB"
              "（与规格 §5.1a 引用的 110–112 dB 一致）——口径差异请规格方定。",
        "D9": "真实 OPA388 + ADC 采样开关（M2 C_S=3.5 pF、M6 S1/S2 50% 反相、Ron=1 Ω 缺省假设）。"
              "判据 = 122.07 ns 窗内引脚残差 ≤0.01% 稳态值。"
              f"worst_rel_to_ss = {res['D9_detail']['ron1']['worst_rel_to_ss']:.2e}；"
              f"物理判据（采样电容 vs 引脚）worst_rel = "
              f"{res['D9_detail']['ron1']['cap_lock']['worst_rel']:.2e}。Ron=100/1000 Ω 同样通过。",
        "C9": f"跟随器节点 {res['c9_follower_db']:.3f} dB（≤6）@ "
              f"{res['c9_follower_hz']/1e3:.1f} kHz；ADC 引脚 {res['c9_pin_db']:.4f} dB。"
              "**但 50 kΩ 源阻抗时跟随器节点升到 "
              f"{res['c9_by_source']['50k']['follower_peak_db']:.3f} dB**（仍 ≤6 dB，余量仅 "
              f"{6.0 - res['c9_by_source']['50k']['follower_peak_db']:.2f} dB）——"
              "C9 的实测口径应含源阻抗扫描，见 c9_by_source。",
        "温度角": "−20/+85 ℃ 只折 C0G 的 −30 ppm/℃（电阻温漂未代入，BOM 未定型 E.10 #6）；"
                  "D4 在 −20/25/+85 ℃ 为 "
                  f"{res['temperature_corners']['-20C']['D4_dG_16k_db']:.4f}/"
                  f"{res['temperature_corners']['25C']['D4_dG_16k_db']:.4f}/"
                  f"{res['temperature_corners']['+85C']['D4_dG_16k_db']:.4f} dB，"
                  "对 D4 无实质影响。",
        "数值方法": "真实模型瞬态主口径 gear/reltol 1e-5/maxstep 20 ns（TI 宏模型内部 1 F 电容"
                    "在 trap + 紧容差下会咬死步长：本轮实测 trap reltol 1e-5 在 60 µs 窗内即"
                    "写出 338 MB 且 200 s 未完成，400 µs 窗达 920 MB——故复核档取 trap "
                    "reltol 1e-4 + 60 µs 窗）。",
    }


def _d6a_note(res):
    lin = res["D6_detail"]["D6a_linear_pct"]
    quad = res["D6_detail"]["D6a_quadrature_pct"]
    lhs = (1 + lin / 100.0) ** 2
    rhs = 1 + (quad / 100.0) ** 2
    return (
        f"规格字面公式 (V_tot−V_nl)/V_nl = {lin:.4f}%（v9d 真实阶梯 vs v9d_nl "
        "阶梯电阻全 noiseless；两网表除 R 的 `noiseless` 标志外逐行相同，传函一致）。"
        f"另报正交口径 √(V_tot²−V_nl²)/V_nl = {quad:.2f}%——**两者不是矛盾的两种算法**："
        "同一组数据的两种归一化，(1+线性)² = 1 + 正交² "
        f"（核对：{lhs:.6f} vs {rhs:.6f}，差 {100*(lhs-rhs)/lhs:+.3f}%）。"
        "规格 D6a 写的是「总噪声 vs 跟随器自身噪声的增量比例」→ **记分用线性口径 "
        f"{lin:.3f}%（满分）**；正交口径 "
        f"{quad:.1f}% 若被采用会落到 {10.0/quad:.3f} 分，故一并披露并请规格方确认。")


def _d5_verdict(res):
    dsc = res.get("D5_discrimination", {})
    pc = dsc.get("positive_control_old_B_100k", {}) or {}
    pp = pc.get("tail_pp_uv", {})
    return ("ask 要求的判别：①**正对照**——第 3 轮旧参数（R1=2.74 Ω）在 100 kΩ 用三套设置"
            "重跑，尾窗 pp = "
            + "/".join(f"{v/1e3:.2f}mV" if v else "-" for v in
                       (pp.get("gear20n_400us"), pp.get("trap60us"), pp.get("gear5n_150us")))
            + "，三设置**全部复现等幅振荡**（FFT 峰 120/133/120 kHz）→ 判据不是只在"
            "某一积分法下才报，也排除「单一积分法的数值伪影」。"
            "②本轮参数五档 × 三设置全部回稳（尾窗 pp ≤ 43.5 µV），且 gear/trap 在共同时间窗"
            "上逐窗一致 → 既非「真实不稳定」，也非「数值伪影掩盖」。"
            f"③频率对照：旧参数振荡 120–133 kHz，比它的跟随器-首级极点 "
            f"f=1/(2πR1C1)={dsc.get('poles', {}).get('old_B_follower_load_pole_khz', float('nan')):.0f} kHz "
            "低 6–7 倍、也比小信号 AC 的跟随器峰（≈290 kHz）低一半 —— 这种「振荡频率明显"
            "低于线性谐振点」是大信号非线性极限环的典型特征（与第 3 轮 E4/E5 的"
            "「关掉模型输入电容/换理想跟随器即消失」一致），而不是环路 RHP 极点。"
            f"本轮参数极点 {dsc.get('poles', {}).get('new_B_follower_load_pole_khz', float('nan')):.0f} kHz，"
            "小信号 AC 在 278–292 kHz 只有 2.3–5.8 dB 峰，未见发散趋势。"
            "→ 结论：**B 案本参数下 50–220 kΩ 无极限环，不构成淘汰项**。")


# ------------------------------------------------------------------ 理论 + 交叉验证
def theory_and_xcheck(res, cand, st, ns):
    p = O5.predict(st)                      # 真实 OPA388 源模型
    th0 = X.predict_zero_source(st)         # 纯无源（rs→0）
    res["theory_engine_pred"] = {k: float(v) for k, v in p.items()
                                 if isinstance(v, (int, float))}
    res["theory_zero_source"] = {k: float(v) for k, v in th0.items()}

    rm = res["real_model"]
    ctl = res["control_ideal"]
    xc = {"B_real_model": {"rows": []}, "A_zero_source_ideal": {"rows": []},
          "note": "B = 含跟随器（主口径，TI 宏模型 vs 引擎 opa388 源模型）；"
                  "A = 纯无源（0 Ω 理想源 LTspice vs rs→0 MNA）"}

    for lab, lt, thv in (("D1 A_dm@fMOD", rm["D1_A_dm_db"], p["A_dm"]),
                         ("D2 A_cm@fMOD", rm["D2_A_cm_db"], p["A_cm"]),
                         ("D3 A_mclk@MCLK", rm["D3_A_mclk_db"], p["A_mclk"]),
                         ("D4 dG@16k", rm["D4_dG_16k_db"], p["dG_16k"]),
                         ("D10 dtau_us", rm["D10_dtau_us"],
                          p["group_delay_flat_s"] * 1e6)):
        dv = float(lt) - float(thv)
        xc["B_real_model"]["rows"].append(
            {"item": lab, "theory": float(thv), "ltspice": float(lt),
             "abs_diff": dv, "pass_0p5": bool(abs(dv) <= 0.5)})
    # 噪声
    th_nv = p["V_n_lsb"] * LSB_V * 1e9
    xc["B_real_model"]["noise_total"] = {
        "theory_nv": float(th_nv),
        "ltspice_nv": float(res["D6_detail"]["total_with_ladder_nv"]),
        "rel_pct": float(100 * (res["D6_detail"]["total_with_ladder_nv"] - th_nv) / th_nv),
        "pass_5pct": bool(abs(res["D6_detail"]["total_with_ladder_nv"] - th_nv)
                          <= 0.05 * th_nv)}
    # D5：引擎是线性模态分解，不含运放压摆/过载恢复 → 单列、不并入 pass
    th_us = O5.d5_worst_us(p)
    xc["B_real_model"]["settle_informational"] = {
        "theory_us": float(th_us), "ltspice_us": float(res["dims"]["D5"]),
        "theory_zero_source_corner_us": float(p["t_settle_wc_s"] * 1e6),
        "theory_highz_premise_us": float(p["t_settle_highz_s"] * 1e6),
        "note": ("引擎 D5 的两个数：0 Ω 最坏角 %.2f µs、600 kΩ 高阻角 %.2f µs"
                 "（后者把 600 kΩ×8.5 pF 的未自举输入极点当前置 RC）。"
                 "LTspice 真实 TI 模型五档源阻抗实测最慢 %.2f µs。差异来源："
                 "①TI 模型的输入电容被自举/远小于 8.5 pF 悲观上界（本轮 600 kΩ 档 "
                 "D4 只劣化 0.307 dB，与 4.5 pF 而非 8.5 pF 一致）；"
                 "②引擎不含运放大信号恢复，而真实模型在本参数下恢复更快（R1 6.19 Ω "
                 "把 68 nF 首级容性负载与输出隔离）。两者都远低于 500 µs 满分线，"
                 "不影响评分；按规格 §8 以 LTspice 为准。"
                 % (p["t_settle_wc_s"] * 1e6, p["t_settle_highz_s"] * 1e6,
                    res["dims"]["D5"])),
        "informational": True}
    # C9
    th_c9 = p["peaking_db"]
    xc["C9_peaking"] = {
        "engine_pin_peak_db": float(th_c9),
        "engine_peaking_hz": float(p["peaking_f_hz"]),
        "ltspice_pin_peak_db": res["c9_pin_db"],
        "ltspice_follower_peak_db": res["c9_follower_db"],
        "ltspice_follower_hz": res["c9_follower_hz"],
        "ltspice_worst_over_sources_db": res["c9_worst_over_sources_db"],
        "limit_db": 6.0,
        "pass_follower": bool(res["c9_follower_db"] is not None
                              and res["c9_follower_db"] <= 6.0),
        "pass_pin": bool(res["c9_pin_db"] <= 6.0),
        "pass_worst_source": bool(res["c9_worst_over_sources_db"] is not None
                                  and res["c9_worst_over_sources_db"] <= 6.0)}
    # D6a：LTspice 与引擎同口径（都是「总噪声相对同带宽跟随器噪声的线性增量」）
    th_d6a = 100.0 * (p["V_n_lsb"] - p["V_n_lsb_follower"]) / p["V_n_lsb_follower"]
    lt_d6a = res["D6_detail"]["D6a_linear_pct"]
    xc["B_real_model"]["d6a_pct"] = {
        "theory_pct": float(th_d6a), "ltspice_pct": float(lt_d6a),
        "rel_pct": float(100 * (lt_d6a - th_d6a) / th_d6a),
        "pass_5pct": bool(abs(lt_d6a - th_d6a) <= 0.05 * th_d6a),
        "note": "引擎 V_n_lsb/V_n_lsb_follower 与 v9d/v9d_nl 都是「总噪声 vs 同带宽"
                "跟随器噪声」的线性增量口径"}
    # D7：同抽样理论（p.d. 口径，排除抽样噪声）
    if res.get("D7_detail"):
        try:
            import gen_netlists_r5 as G5          # noqa: N813
            from parse_r3_B import _two_line_abcd, _mc_sigma_theory_same_draws
            xc["D7_same_draws"] = _mc_sigma_theory_same_draws(st, ns)
            xc["D7_same_draws"]["ltspice_sigma_db"] = res["D7_detail"]["sigma_db"]
            xc["D7_same_draws"]["rel_pct"] = float(
                100 * (res["D7_detail"]["sigma_db"]
                       - xc["D7_same_draws"]["sigma_db"])
                / xc["D7_same_draws"]["sigma_db"])
            xc["D7_same_draws"]["pass_5pct"] = bool(abs(xc["D7_same_draws"]["rel_pct"]) <= 5.0)
        except Exception as e:                      # noqa: BLE001
            xc["D7_same_draws"] = {"error": repr(e)}

    # D8：配对 1%
    th_cmrr = S4.cmrr_rc_paired(st, 0.01)
    th_cmrr_inv = S4.cmrr_rc_paired_exact_inv(st, 0.01)
    lt_cmrr = res["D8_detail"]["paired"].get("1%", {}).get("CMRR_db")
    if lt_cmrr is not None:
        xc["B_real_model"]["cmrr_1pct_paired"] = {
            "theory_db": float(th_cmrr),
            "theory_exact_inverse_db": float(th_cmrr_inv),
            "ltspice_db": float(lt_cmrr),
            "abs_diff": float(lt_cmrr - th_cmrr),
            "pass_0p5": bool(abs(lt_cmrr - th_cmrr) <= 0.5),
            "note": "理论 = 引擎双线 MNA（源模型 opa388）；LT = TI 宏模型。"
                    "规格正文写 C×(1−m)，严格倒数口径另列"}

    # ---- A 块：纯无源 ----
    for lab, lt, thv in (("D1 A_dm@fMOD", ctl["D1_A_dm_db"], th0["A_dm"]),
                         ("D2 A_cm@fMOD", ctl["D2_A_cm_db"], th0["A_cm"]),
                         ("D3 A_mclk@MCLK", ctl["D3_A_mclk_db"], th0["A_mclk"]),
                         ("D4 dG@16k", ctl["D4_dG_16k_db"], th0["dG_16k"]),
                         ("D10 dtau_us", ctl["D10_dtau_us"], th0["dtau_us"])):
        dv = float(lt) - float(thv)
        xc["A_zero_source_ideal"]["rows"].append(
            {"item": lab, "theory": float(thv), "ltspice": float(lt),
             "abs_diff": dv, "pass_0p5": bool(abs(dv) <= 0.5)})
    v4i = res["D5_detail"]["0ohm_ideal_source"]["gear20n"]
    if v4i:
        th_s = th0["t_settle_wc_us"]
        lt_s = v4i["spec_200uV"]["tset_us"]
        rel = (lt_s - th_s) / th_s
        xc["A_zero_source_ideal"]["settle"] = {
            "theory_us": float(th_s), "ltspice_us": float(lt_s),
            "rel_diff": float(rel), "pass_5pct": bool(abs(rel) <= 0.05),
            "note": "0 Ω 最坏角（R×1.01/C×1.05）同工况对拍，200 µV 差分带"}
    rr = R("v7i")
    if rr:
        lt_nv = noise_nv(rr)["D6_Vn_nv"]
        th_nv0 = th0["Vn_nv"]
        xc["A_zero_source_ideal"]["noise"] = {
            "theory_nv": float(th_nv0), "ltspice_nv": float(lt_nv),
            "rel_pct": float(100 * (lt_nv - th_nv0) / th_nv0),
            "pass_5pct": bool(abs(lt_nv - th_nv0) <= 0.05 * th_nv0)}

    # ---- D5 三设置一致性 ----
    conv = {}
    for k, row in res["d5_by_source"].items():
        conv[k] = row["tset_us"]
    worst_spread = max((row["spread_pct"] for row in res["d5_by_source"].values()
                        if row["spread_pct"] is not None), default=None)
    xc["D5_convergence"] = {
        "by_source_us": conv,
        "worst_spread_pct": worst_spread,
        "settings": "gear20n(400µs 窗) / trap reltol 1e-4(60µs 窗) / gear 5ns reltol 1e-6(150µs 窗)",
        "pass": bool(worst_spread is not None and worst_spread <= 5.0)}

    ac_b = [r for r in xc["B_real_model"]["rows"] if not r["pass_0p5"]]
    ac_a = [r for r in xc["A_zero_source_ideal"]["rows"] if not r["pass_0p5"]]
    xc["ac_fail_B"] = [r["item"] for r in ac_b]
    xc["ac_fail_A"] = [r["item"] for r in ac_a]
    xc["pass_criteria"] = ("规格 §8：AC 衰减 |Δ|≤0.5 dB（A/B 两块 rows）+ 建立 ≤5%"
                           "（A 块 0 Ω 最坏角）+ D5 三设置一致性 ≤5% + 噪声 ≤5%")
    xc["pass"] = bool(not ac_a and not ac_b
                      and xc["A_zero_source_ideal"].get("settle", {}).get("pass_5pct", True)
                      and xc["A_zero_source_ideal"].get("noise", {}).get("pass_5pct", True)
                      and xc["D5_convergence"]["pass"]
                      and xc["B_real_model"]["noise_total"]["pass_5pct"]
                      and xc["B_real_model"]["d6a_pct"]["pass_5pct"]
                      and xc["C9_peaking"]["pass_follower"]
                      and xc["C9_peaking"]["pass_worst_source"]
                      and xc.get("D7_same_draws", {}).get("pass_5pct", True))
    res["xcheck"] = xc
    res["notes"] = _notes(res)
    # 与本轮冻结文件的引擎预测逐项对照（提醒：冻结文件 pred 是引擎值，不是实测）
    frozen = cand.get("pred", {})
    res["vs_frozen_pred"] = {
        "note": "r5_candidates_final_B.json 的 dims 是**引擎预测**；本文件是 LTspice 实测",
        "items": {
            "D1": {"frozen": frozen.get("A_dm"), "ltspice": res["dims"]["D1"]},
            "D2": {"frozen": frozen.get("A_cm"), "ltspice": res["dims"]["D2"]},
            "D3": {"frozen": frozen.get("A_mclk"), "ltspice": res["dims"]["D3"]},
            "D4": {"frozen": frozen.get("dG_16k"), "ltspice": res["dims"]["D4"]},
            "D5": {"frozen": frozen.get("t_settle_highz_s", 0) * 1e6,
                   "ltspice": res["dims"]["D5"]},
            "D6a": {"frozen": 100.0 * (frozen.get("V_n_lsb", 0)
                                       - frozen.get("V_n_lsb_follower", 0))
                    / frozen.get("V_n_lsb_follower", 1),
                    "ltspice": res["dims"]["D6a"]},
            "D6b": {"frozen": frozen.get("V_n_lsb"), "ltspice": res["dims"]["D6b"]},
            "D7": {"frozen": frozen.get("sigma_dG_db"), "ltspice": res["dims"]["D7"]},
            "D8": {"frozen": 95.46518427684504,
                   "ltspice": res["dims"]["D8"],
                   "note": "冻结文件 dims.D8 为 95.47（配对 1% 引擎值）"},
            "D10": {"frozen": frozen.get("group_delay_flat_s", 0) * 1e6,
                    "ltspice": res["dims"]["D10"]},
            "C9": {"frozen": cand.get("c9", {}).get("follower_node_peak_db"),
                   "ltspice": res["c9_follower_db"]},
        },
    }
    return res


# ------------------------------------------------------------------ 评分（规格 v4 §5.1）
def score(dims):
    def ratio(x, full):
        return 0.0 if x is None else float(min(x / full, 1.0))

    def inv(x, full):
        return 0.0 if (x is None or x <= 0) else float(min(full / x, 1.0))

    def lin(x, full, bare):
        if x is None:
            return None
        if x <= full:
            return 1.0
        if x > bare:
            return 0.0
        return float(1.0 - (x - full) / (bare - full))

    s = {
        "D1": ratio(dims["D1"], 120.0),
        "D2": ratio(dims["D2"], 100.0),
        "D3": ratio(dims["D3"], 150.0),
        "D4": lin(dims["D4"], 0.05, 0.5),
        "D5": inv(dims["D5"], 500.0),
        "D6a": inv(dims["D6a"], 10.0) if (dims["D6a"] or 0) > 0 else 1.0,
        "D7": lin(dims["D7"], 0.01, 0.05),
        "D8": ratio(dims["D8"], 100.0),
        "D9": float(dims["D9"]) if dims["D9"] is not None else 0.0,
        "D10": lin(dims["D10"], 1.0, 5.0),
    }
    pf = {
        "D1": dims["D1"] >= 80, "D2": dims["D2"] >= 60, "D3": dims["D3"] >= 100,
        "D4": dims["D4"] <= 0.5,
        "D5": dims["D5"] is not None and dims["D5"] <= 900,
        "D6a": dims["D6a"] <= 30.0,
        "D7": dims["D7"] is not None and dims["D7"] <= 0.05,
        "D8": dims["D8"] is not None and dims["D8"] >= 80,
        "D9": dims["D9"] == 1.0,
        "D10": dims["D10"] <= 5.0,
    }
    return s, pf, float(min(s.values()))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=os.path.join(HERE, "r5_results_r4_B.json"))
    args = ap.parse_args(argv)

    res, cand, st, ns = build()
    res = theory_and_xcheck(res, cand, st, ns)
    s, pf, mn = score(res["dims"])
    res["scores"] = s
    res["pass"] = pf
    res["min_score"] = mn
    res["failing"] = [k for k, v in pf.items() if not v]
    res["raw_files"] = os.path.join(D, "r5_B_r4_*.raw")
    res["work_dir"] = D
    res["netlist_files"] = os.path.join(D, "r5_B_r4_*.net")
    res["generator"] = "gen_netlists_r5_r4.py"
    res["runner"] = "run_r4_B.py"
    res["discrimination_script"] = "r5_d5_discrim_r4_B.py"

    with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=2, default=float)

    print("=== 方案 B 第 4 轮（规格 v4，真实 OPA388 主口径）===")
    for k in ("D1", "D2", "D3", "D4", "D5", "D6a", "D6b", "D7", "D8", "D9", "D10"):
        v = res["dims"][k]
        sc = res["scores"].get(k)
        vs = "None" if v is None else f"{v:.4f}"
        ss = "None" if sc is None else f"{sc:.4f}"
        tag = "" if k == "D6b" else ("过线" if res["pass"].get(k) else "×淘汰")
        print(f"  {k:5s} {vs:>14}  分={ss:>8}  {tag}")
    print(f"  min = {mn:.4f}   未及格 = {res['failing']}")
    print(f"\nC9：跟随器 {res['c9_follower_db']:.3f} dB @ {res['c9_follower_hz']/1e3:.1f} kHz"
          f" | 引脚 {res['c9_pin_db']:.4f} dB | 限 6 dB | ok={res['c9_ok']}")
    print("C9 随源阻抗（跟随器节点峰值 / 引脚峰值 dB）：")
    for k, v in res["c9_by_source"].items():
        print(f"  {k:>6s}  foll={v['follower_peak_db']:6.3f} @ {v['follower_peak_hz']/1e3:6.1f} kHz"
              f"   pin={v['pin_peak_db']:.4f}   D4={v['D4_dG_16k_db']:.4f}"
              f"   D1={v['D1_A_dm_db']:.2f}")
    print("\nD5 五档源阻抗（µs，三设置）：")
    for k, row in res["d5_by_source"].items():
        ts = row["tset_us"]
        print(f"  {k:>6s}  gear20n={ts['gear20n']}  trap60us={ts['trap60us']}"
              f"  gear5n={ts['gear5n']}  spread={row['spread_pct']:.2f}%"
              f"  stable={row['stable']}")
    print("\n--- 交叉验证（规格 §8）---")
    for blk, name in (("B_real_model", "B 含跟随器"),
                      ("A_zero_source_ideal", "A 纯无源")):
        print(f"  [{name}]")
        for r in res["xcheck"][blk]["rows"]:
            print(f"    {r['item']:16s} 理论 {r['theory']:9.3f} | LT {r['ltspice']:9.3f} "
                  f"| Δ {r['abs_diff']:+.4f} {'OK' if r['pass_0p5'] else 'FAIL'}")
        for k in ("noise", "noise_total", "settle", "cmrr_1pct_paired"):
            if k in res["xcheck"][blk]:
                v = res["xcheck"][blk][k]
                ok = v.get("pass_0p5", v.get("pass_5pct"))
                nums = "  ".join(f"{kk}={vv:.4g}" for kk, vv in v.items()
                                 if isinstance(vv, (int, float)))
                print(f"    {k:20s} {nums}  {'OK' if ok else 'FAIL'}")
    print("  C9:", json.dumps(res["xcheck"]["C9_peaking"], ensure_ascii=False))
    print("  D5_convergence:", json.dumps(res["xcheck"]["D5_convergence"],
                                         ensure_ascii=False))
    print(f"  xcheck pass = {res['xcheck']['pass']}")
    print("→", args.json)
    return res


if __name__ == "__main__":
    main()
