#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""parse_r3.py — 方案 A 第 3 轮十维实测提取（规格 v4 口径）

主口径：**真实 OPA388 模型**（TI OPAx388.LIB）。
  D1/D2/D3/D4/D10 ← V9a（差分 AC）/ V9b（共模 AC）
  D5              ← V9c（0 Ω，最坏角）/ V9f（600 kΩ 样品端，最坏角）；取较大者
  D6a             ← V9d（总噪声）vs V9dn（阶梯 + 负载 noiseless，仅跟随器噪声）
  D6b             ← V9d 总积分噪声（LSB，仅报告）
  D7              ← V9m MC ×30（真实模型）
  D8              ← V9p 配对/同向失配扫描，取**配对**条件下的最优档（m=1%，规格考核条件）
  D9              ← V9k（真实模型 kickback）；不收敛时如实标 unverified
  C9 (硬约束)     ← V9pk 全频段峰值

对照口径（0 Ω 理想源，V1–V8）只作报告，**不参与打分**。

用法::

    python parse_r3.py --json r5_results_r3_A.json
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

from parse_r5 import (  # noqa: E402
    LSB_V, FMOD, MCLK, KB_WIN_S, TBAND_DIFF, Raw, db, interp_at, pin_names,
    d1_d3_d4_d10, d2, d8, settle_us, noise_nv, kickback,
)

TBAND_SPEC = 200e-6          # 规格 0.01 % of 2 V
D = os.path.join(HERE, "r5_work", "r3")
KEY = "A"


# ------------------------------------------------------------------ 通用
def _has(tag):
    return os.path.exists(os.path.join(D, f"r5_{KEY}_r3_{tag}.raw"))


def _raw(tag):
    return Raw(os.path.join(D, f"r5_{KEY}_r3_{tag}.raw"))


def _ac_dm(raw, ns):
    a, b = f"V(pa{ns})", f"V(na{ns})"
    dc = interp_at(raw, 0.1, a) - interp_at(raw, 0.1, b)
    return {
        "g_dc_db": db(dc),
        "g_16k_db": db(interp_at(raw, 16e3, a) - interp_at(raw, 16e3, b)),
        "g_fmod_db": db(interp_at(raw, FMOD, a) - interp_at(raw, FMOD, b)),
        "g_mclk_db": db(interp_at(raw, MCLK, a) - interp_at(raw, MCLK, b)),
    }


def _d1_d3_d4_d10(raw, ns):
    """D1/D3/D4/D10，主口径（真实模型）。"""
    a, b = f"V(pa{ns})", f"V(na{ns})"
    f = raw.f
    p = np.array(raw.col(a), complex)
    n = np.array(raw.col(b), complex)
    d = p - n
    gdc = db(interp_at(raw, 0.1, a) - interp_at(raw, 0.1, b))
    o = {
        "D1": -(db(interp_at(raw, FMOD, a) - interp_at(raw, FMOD, b)) - gdc),
        "D3": -(db(interp_at(raw, MCLK, a) - interp_at(raw, MCLK, b)) - gdc),
        "D4": abs(db(interp_at(raw, 16e3, a) - interp_at(raw, 16e3, b)) - gdc),
    }
    m = (f >= 0.1) & (f <= 16e3)
    tau = -np.gradient(np.unwrap(np.angle(d[m])), 2 * math.pi * f[m])
    o["D10"] = float((tau.max() - tau.min()) * 1e6)
    o["tau_100Hz_us"] = float(tau[0] * 1e6)
    o["tau_16k_us"] = float(tau[-1] * 1e6)
    tp = -np.gradient(np.unwrap(np.angle(p[m])), 2 * math.pi * f[m])
    tn = -np.gradient(np.unwrap(np.angle(n[m])), 2 * math.pi * f[m])
    o["CH_tau_diff_us"] = float(np.max(np.abs(tp - tn)) * 1e6)
    o["tau_p_16k_us"] = float(tp[-1] * 1e6)
    o["tau_n_16k_us"] = float(tn[-1] * 1e6)
    return o


def _d2(raw, ns):
    a = f"V(pa{ns})"
    return {"D2": -(db(interp_at(raw, FMOD, a)) - db(interp_at(raw, 0.1, a))),
            "g_cm_dc_db": db(interp_at(raw, 0.1, a)),
            "g_cm_fmod_db": db(interp_at(raw, FMOD, a))}


def _noise_int(raw):
    f = np.array([v.real if isinstance(v, complex) else v for v in raw.cols[0]], float)
    dens = np.abs(np.array(raw.col("v(onoise)")))
    m = f <= FMOD / 2
    tot = float(math.sqrt(np.trapz(dens[m] ** 2, f[m])))
    return {"v": tot, "f": f, "dens": dens}


def _settle(tag, ns, band=TBAND_SPEC):
    q = os.path.join(D, f"r5_{KEY}_r3_{tag}.raw")
    if not os.path.exists(q):
        return None
    r = Raw(q)
    t = np.array([v.real if isinstance(v, complex) else v for v in r.cols[0]], float)
    p = np.array(r.col(f"V(pa{ns})"), float)
    n = np.array(r.col(f"V(na{ns})"), float)
    d = p - n
    ts, vf, ef = settle_us(r, ns, band=band)
    # 是否真的稳住了：看最后一个 20 % 窗内的峰峰值
    q20 = t > 0.8 * t[-1]
    pp = float(np.ptp(d[q20]))
    # 环路是否自激：末段窗口峰峰值远超 0.01 % 带即判"未建立"
    converged = pp <= band
    return {"tset_us": ts, "vfinal_v": vf, "err_final_uv": ef * 1e6,
            "tail_pp_uv": pp * 1e6, "converged": bool(converged),
            "t_max_us": float(t[-1] * 1e6), "npts": len(t),
            "tail_pp_mv": pp * 1e3}


# ------------------------------------------------------------------ 主流程
def analyze(cand_json=os.path.join(HERE, "r5_candidates_r2.json"), key="A"):
    with open(cand_json, encoding="utf-8") as fh:
        cand = json.load(fh)[key]
    st = [tuple(map(float, s)) for s in cand["stages"]]
    ns = len(st)
    res = {"candidate": key, "n_stages": ns, "stages": cand["stages"],
           "primary_model": "TI OPAx388 SBOS777D Rev D (lib/OPAx388.LIB)",
           "dir": D, "raw": {}, "dims": {}, "notes": []}

    # ---------- AC 主项（真实模型）----------
    if _has("v9a"):
        r = _raw("v9a")
        res["V9a"] = _ac_dm(r, ns)
        res["primary"] = _d1_d3_d4_d10(r, ns)
        res["raw"]["V9a"] = r.path
    if _has("v9b"):
        r = _raw("v9b")
        res["V9b"] = _d2(r, ns)
        res["raw"]["V9b"] = r.path
    if _has("v9e"):
        r = _raw("v9e")
        gg = {"g_dc_db": db(interp_at(r, 0.1, f"V(pa{ns})") - interp_at(r, 0.1, f"V(na{ns})"))}
        gg["g_16k_db"] = db(interp_at(r, 16e3, f"V(pa{ns})") - interp_at(r, 16e3, f"V(na{ns})"))
        gg["g_fmod_db"] = db(interp_at(r, FMOD, f"V(pa{ns})") - interp_at(r, FMOD, f"V(na{ns})"))
        gg["A_dm_fmod_db"] = -(gg["g_fmod_db"] - gg["g_dc_db"])
        gg["dG_16k_db"] = abs(gg["g_16k_db"] - gg["g_dc_db"])
        gg["input_rc_droop_16k_db"] = (db(interp_at(r, 16e3, "V(fa)"))
                                       - db(interp_at(r, 16e3, "V(vp)")))
        res["V9e_600k"] = gg
        res["raw"]["V9e"] = r.path

    # ---------- C9 peaking ----------
    pk = {}
    if _has("v9pk"):
        rp = _raw("v9pk")
        f, a, b = rp.f, f"V(pa{ns})", f"V(na{ns})"
        dp = np.array(rp.col(a), complex) - np.array(rp.col(b), complex)
        g = 20 * np.log10(np.abs(dp) / abs(dp[0]))
        m = (f >= 1.0) & (f <= 2e6)
        i = int(np.argmax(g[m]))
        pk = {"peaking_db": float(g[m][i]), "f_hz": float(f[m][i]),
              "band": "1 Hz - 2 MHz", "npts": len(f)}
        # 各节点各自峰值（C9 判据是**任何节点**的全频段增益峰）
        nodes = {}
        for nm in ("V(pa1)", "V(pa2)", "V(fpa)", "V(fna)"):
            if nm in rp.names:
                y = np.array(rp.col(nm), complex)
                gy = 20 * np.log10(np.abs(y) / abs(y[0]))
                j = int(np.argmax(gy[m]))
                nodes[nm] = {"peak_db": float(gy[m][j]), "f_hz": float(f[m][j])}
        if not nodes and _has("v9a"):
            # v9pk 只存了引脚；退回 v9a（dec 600，0.1 Hz–200 MHz）看内部节点
            ra = _raw("v9a")
            fa = ra.f
            m2 = (fa >= 1.0) & (fa <= 2e6)
            for nm in ("V(pa1)", "V(pa2)", "V(fpa)", "V(fna)"):
                if nm in ra.names:
                    y = np.array(ra.col(nm), complex)
                    gy = 20 * np.log10(np.abs(y) / abs(y[0]))
                    j = int(np.argmax(gy[m2]))
                    nodes[nm] = {"peak_db": float(gy[m2][j]), "f_hz": float(fa[m2][j])}
        pk["nodes"] = nodes
        pk["worst_node_db"] = max((v["peak_db"] for v in nodes.values()), default=None)
        pk["C9_limit_db"] = 6.0
        pk["C9_pass_diff_pin"] = bool(pk["peaking_db"] <= 6.0)
        pk["C9_pass_any_node"] = bool((pk["worst_node_db"] or 0.0) <= 6.0)
        pk["C9_pass"] = pk["C9_pass_any_node"]
    res["C9"] = pk

    # ---------- 稳定性 / D5 证据 ----------
    stab = {}
    for tag, lab in (("v9c", "V9c_0ohm_corner"), ("v9f", "V9f_600k_corner")):
        q = os.path.join(D, f"r5_{KEY}_r3_{tag}.raw")
        if not os.path.exists(q):
            continue
        rr = Raw(q)
        t = np.array([v.real if isinstance(v, complex) else v for v in rr.cols[0]], float)
        p = np.array(rr.col(f"V(pa{ns})"), float)
        n = np.array(rr.col(f"V(na{ns})"), float)
        dm = p - n
        msk = t > 0.7 * t[-1]
        seg, tt = dm[msk], t[msk]
        x = seg - seg.mean()
        fx = np.fft.rfftfreq(len(seg), d=float(np.median(np.diff(tt))))
        X = np.abs(np.fft.rfft(x)) * 2 / len(seg)
        k = int(np.argmax(X[1:])) + 1 if len(X) > 2 else 0
        # 前后两个 20 % 窗的峰峰值，看是等幅还是衰减
        e1 = t > 0.2 * t[-1]
        e1 &= t < 0.4 * t[-1]
        stab[lab] = {
            "tail_pp_mv": float(seg.ptp() * 1e3),
            "osc_f_hz": float(fx[k]) if k else None,
            "osc_amp_mv": float(X[k] * 1e3) if k else None,
            "envelope_start_mv": float((dm[e1].max() - dm[e1].min()) * 1e3),
            "envelope_end_mv": float(seg.ptp() * 1e3),
            "sustained": bool(seg.ptp() > 1e-4 * abs(seg.mean()) * 10),
            "t_max_us": float(t[-1] * 1e6),
            "note": "等幅极限环 → 电路不稳定；0.01% 建立带永远进不去",
        }
    if stab:
        res["stability"] = stab
        # 稳定性边界实测（`probe_loopcheck.py` / `probe_stab_final.py`）
        res["stability_threshold"] = {
            "closed_loop_peak_vs_Riso_100nF": {
                "2.4": 23.69, "3.0": 26.32, "3.3": 19.58, "3.6": 15.85, "3.9": 13.26,
                "4.3": 10.71, "5.1": 7.19, "6.8": 2.71, "10.0": 0.0, "13.0": 0.0},
            "peak_f_hz": 302000.0,
            "transient": {"Riso_2p4_us": "never settles (limit cycle)",
                          "Riso_10_us": 27.02, "Riso_13_us": 38.27},
            "conclusion": ("候选 A 的 R1 = 2.4 Ω 直接驱动 100 nF 使 OPA388 跟随器在"
                           "闭环外另成回路：AC 在 302 kHz 出现 +23.7 dB 尖峰（该处"
                           "H(fpa) 已 >1，即跟随器输出端被负载网络推成增益峰），"
                           "瞬态表现为 158–185 kHz 等幅极限环（幅值不衰减、与阶跃幅度"
                           "无关），0.01 % 建立带永不进入。把 R1 提高到 ≥10 Ω（对跟随器"
                           "隔离足够，−3 dB 点仍在通带之外）即恢复稳定：R1=10 Ω 时"
                           "27 µs 建立、R1=13 Ω 时 38 µs。"),
            "source": "r5_work/r3/probe_loopcheck.py, probe_stab_final.py, probe_d9_iso.py",
        }

    # ---------- 噪声（D6a / D6b）----------
    d6 = {}
    if _has("v9d"):
        tot = _noise_int(_raw("v9d"))
        d6["total_nv"] = tot["v"] * 1e9
        d6["total_lsb"] = tot["v"] / LSB_V
        d6["dens_1k_nv"] = float(np.interp(1e3, tot["f"], tot["dens"])) * 1e9
        res["raw"]["V9d"] = os.path.join(D, f"r5_{KEY}_r3_v9d.raw")
    if _has("v9dn"):
        fol = _noise_int(_raw("v9dn"))
        d6["follower_only_nv"] = fol["v"] * 1e9
        d6["follower_only_lsb"] = fol["v"] / LSB_V
        d6["dens_1k_foll_nv"] = float(np.interp(1e3, fol["f"], fol["dens"])) * 1e9
        res["raw"]["V9dn"] = os.path.join(D, f"r5_{KEY}_r3_v9dn.raw")
    if "total_nv" in d6 and "follower_only_nv" in d6:
        d6["D6a_pct"] = 100.0 * (d6["total_nv"] - d6["follower_only_nv"]) / d6["follower_only_nv"]
        d6["D6a_quadrature_pct"] = 100.0 * math.sqrt(
            max(d6["total_nv"] ** 2 - d6["follower_only_nv"] ** 2, 0.0)) / d6["follower_only_nv"]
        d6["D6b_lsb"] = d6["total_lsb"]
        d6["brickwall_4p3_lsb"] = 4.3038657093146275
    # D6a 的进一步分解（阶梯 vs 130 kΩ 负载）——`probe_d6a.py` → `d6a_decomp.json`
    dec = os.path.join(D, "d6a_decomp.json")
    if os.path.exists(dec):
        with open(dec, encoding="utf-8") as fh:
            dd = json.load(fh)
        d6["decomposition"] = dd
        fol = dd["all_nl"]["nv"]
        d6["ladder_only_pct_quadrature"] = 100.0 * math.sqrt(
            max(dd["load_nl"]["nv"] ** 2 - fol ** 2, 0.0)) / fol
        d6["load130k_pct_quadrature"] = 100.0 * math.sqrt(
            max(dd["ladder_nl"]["nv"] ** 2 - fol ** 2, 0.0)) / fol
    res["D6"] = d6

    # ---------- D8 配对 / 同向失配 ----------
    d8o = {}
    for m in (0.001, 0.005, 0.01):
        for kind in ("pair", "same"):
            tag = f"v9p_m{m:g}_{kind}"
            if not _has(tag):
                continue
            r = _raw(tag)
            f = r.f
            p = np.array(r.col(f"V(pa{ns})"), complex)
            n = np.array(r.col(f"V(na{ns})"), complex)
            sel = (f >= 10) & (f <= 16e3)
            cm = np.abs((p[sel] + n[sel]) / 2.0)
            dm = np.abs(p[sel] - n[sel])
            cmrr = 20 * np.log10(cm / np.maximum(dm, 1e-300))
            k = int(np.argmin(cmrr))
            d8o[f"m{m:g}_{kind}"] = {
                "cmrr_min_db": float(cmrr[k]), "f_worst_hz": float(f[sel][k]),
                "cmrr_10hz_db": float(cmrr[0]), "cmrr_16k_db": float(cmrr[-1])}
            res["raw"][tag] = r.path
    if "m0.01_pair" in d8o:
        d8o["D8_primary_db"] = d8o["m0.01_pair"]["cmrr_min_db"]
        d8o["D8_condition"] = "R·C 乘积异向配对，m=1% 单体失配（规格 v4 §5.1 D8）"
    res["D8"] = d8o

    # ---------- D5 ----------
    d5c = {}
    for tag, lab in (("v9c", "V9c_0ohm_real"), ("v9f", "V9f_600k_real")):
        s = _settle(tag, ns)
        if s:
            d5c[lab] = s["tset_us"]
            res.setdefault("V9c" if tag == "v9c" else "V9f", {}).update(s)
            res["raw"][tag.upper()] = os.path.join(D, f"r5_{KEY}_r3_{tag}.raw")
    # 0 Ω 对照（理想源）
    for tag, lab in (("v4", "V4_0ohm_ideal_corner"), ("v4b", "V4b_600k_ideal")):
        s = _settle(tag, ns)
        if s:
            d5c[lab] = s["tset_us"]
            res.setdefault(tag.upper(), {}).update(s)
    res["D5_candidates_us"] = d5c
    # D5 主口径 = 真实模型最坏角（0 Ω 与 600 kΩ 两个工况取较大者）。
    # **但真实模型瞬态是等幅极限环（不衰减），0.01 % 带永不进入** —— 此时
    # `settle_us` 返回的是「最后一次越带时刻」，必然等于仿真窗末尾 t_end−10 µs，
    # 是**窗口伪值**而不是建立时间。这种情况判 D5 = None（未取得有效实测），
    # 判据侧按「最坏角不建立」处理，绝不拿 490 µs 当实测通过。
    real = [(k, d5c[k]) for k in ("V9c_0ohm_real", "V9f_600k_real") if k in d5c]
    res["D5_real_us"] = max((v for _, v in real), default=None)
    stalled = any(
        res.get("V9c" if k == "V9c_0ohm_real" else "V9f", {}).get("converged") is False
        for k, _ in real)
    res["D5_valid"] = bool(real) and not stalled
    # 理论值只作参照，明确标注**不是实测**（ask 禁止拿理论冒充实测）
    import opt_round5 as _o5
    _st = [tuple(map(float, x)) for x in cand["stages"]]
    _p = _o5.predict(_st, source="opa388")
    res["D5_theory_reference_only_NOT_measured"] = {
        "t_settle_wc_us_0ohm": _p["t_settle_wc_s"] * 1e6,
        "t_settle_highz_us_600k": _p["t_settle_highz_s"] * 1e6,
        "d5_worst_us": _o5.d5_worst_us(_p),
        "note": "opt_round5 的无源网络理论值，**不含跟随器的稳定性问题**；"
                "因真实模型瞬态自激，该值不能作为 D5 实测，仅列出以便对照。",
    }
    if stalled:
        res["D5_invalid_reason"] = (
            "真实 OPA388 模型瞬态为**等幅极限环**（0 Ω 时 158–185 kHz / 169 mV pp；"
            "600 kΩ 时 94 kHz / 604 mV pp），500 µs 内不衰减 → 0.01 % 建立带永不满足。"
            "settle_us 给出的 489.997 µs = t_end − 10 µs 的窗口伪值，不作为实测值。"
            "判据按『最坏角不建立』= 淘汰。")

    # ---------- D7 MC（真实模型）----------
    g16 = []
    for k in range(1, 31):
        q = os.path.join(D, f"r5_{KEY}_r3_v9m_mc{k:02d}.raw")
        if not os.path.exists(q):
            continue
        r = Raw(q)
        a, b = f"V(pa{ns})", f"V(na{ns})"
        dcg = db(interp_at(r, 0.1, a) - interp_at(r, 0.1, b))
        g = db(interp_at(r, 16e3, a) - interp_at(r, 16e3, b))
        g16.append(g - dcg)
    if g16:
        res["D7_mc"] = {"n": len(g16), "sigma_db": float(np.std(g16, ddof=1)),
                        "mean_db": float(np.mean(g16)),
                        "min_db": float(np.min(g16)), "max_db": float(np.max(g16)),
                        "p2p_db": float(np.max(g16) - np.min(g16))}
        res["raw"]["V9m"] = os.path.join(D, f"r5_{KEY}_r3_v9m_mc01.raw")

    # ---------- D9 kickback ----------
    # 判据（规格 §5.1 D9）：fMOD 半周期（122.07 ns）内回稳到 0.01 % 带内。
    # 开关时序按规格 §7 构建规范：0.5 ns 沿、S1/S2 180° 反相、各 121.07 ns（= gen_v8 原样）。
    # 真实模型：gear 预热 40 µs + 0.05 ns 细采样尾窗，按 V(swp) 过 0.5 V 的真实沿对齐
    # （`r5_work/r3/probe_d9_final.py` → `d9_final.json`）。
    d9 = {}
    fin = os.path.join(D, "d9_final.json")
    if os.path.exists(fin):
        with open(fin, encoding="utf-8") as fh:
            d9["real_model"] = json.load(fh)
    # 0 Ω 理想源对照（同一 0.01 % 判据、同一开关时序）
    for tag in ("v8_ron1", "v8_ron100", "v8_ron1000"):
        q = os.path.join(D, f"r5_{KEY}_r3_{tag}.raw")
        if not os.path.exists(q):
            continue
        rr = Raw(q)
        if len(rr.cols[0]) == 0:
            continue
        kb = kickback(rr, ns)
        d9.setdefault("ideal_0ohm", {})[tag] = {
            "D9": kb.get("D9"), "worst_rel_to_ss": kb.get("worst_rel_to_ss"),
            "worst_resid_uv": kb.get("worst_resid_uv"),
            "n_cycles": kb.get("n_cycles")}
    rm = d9.get("real_model", {})
    if rm.get("ron1", {}).get("available"):
        d9["D9_real"] = 1.0 if rm["ron1"]["pin_pass_0p01pct"] else 0.0
        d9["criterion_used"] = ("pin residual <= 0.01% of pre-kick value within 122.07 ns "
                                "measured from the real S1 edge (V(swp) crossing 0.5 V), "
                                "Ron=1/100/1000 ohm")
        d9["worst_pin_rel"] = rm["ron1"]["worst_resid90_rel"]
        d9["worst_pin_resid_uv"] = rm["ron1"]["worst_resid90_uv"]
        d9["charge_bucket_cs_rel"] = rm["ron1"]["worst_cs90_rel"]
        d9["all_ron_pass"] = all(rm[k].get("pin_pass_0p01pct", False)
                                 for k in ("ron1", "ron100", "ron1000") if k in rm)
    res["D9"] = d9

    # ---------- 汇总说明 ----------
    res["notes"] = [
        "主评分口径 = TI OPAx388 SBOS777D Rev D 模型（lib/OPAx388.LIB），全部 AC/噪声/瞬态"
        "均由 LTspice -b -ascii 实测；0 Ω 理想源（V1–V8）仅作对照报告，不参与打分。",
        "D6a 定义：同带宽下（真实模型总积分噪声 − 阶梯与负载强制 noiseless 的跟随器自身噪声）"
        "/ 跟随器自身噪声，算术比 = 0.17 %；正交分解 5.83 %（阶梯约翰逊噪声）+ 0.08 %（130 kΩ 负载）。",
        "D8 主口径 = R·C 乘积异向配对、m = 1 %（规格 v4 §5.1 考核条件）；m = 0.1/0.5 % 与同向失配"
        "全部实测并列在 D8 段。",
        "D9 判据按规格 §5.1：引脚残差在 122.07 ns 内回落到 0.01 % 带内；测量窗口按 V(swp) 过 0.5 V "
        "的真实开关沿对齐；Ron = 1/100/1000 Ω 三档全过。",
        "D5 未取得有效实测值：真实模型瞬态自激（见 stability / D5_invalid_reason），"
        "0 Ω 与 600 kΩ 两个最坏角都呈等幅极限环，0.01 % 带永不满足。按『最坏角不建立』判淘汰。",
    ]

    # ---------- 0 Ω 对照（V1–V3 / V7 / V5）----------
    comp = {}
    if _has("v1"):
        comp["V1"] = _ac_dm(_raw("v1"), ns)
        comp["V1"].update({k: v for k, v in d1_d3_d4_d10(_raw("v1"), ns).items()})
    if _has("v2"):
        comp["V2"] = _d2(_raw("v2"), ns)
    if _has("v3"):
        comp["V3"] = d8(_raw("v3"), ns)
    if _has("v7"):
        comp["V7"] = noise_nv(_raw("v7"))
    g0 = []
    for k in range(1, 31):
        q = os.path.join(D, f"r5_{KEY}_r3_v5mc{k:02d}.raw")
        if not os.path.exists(q):
            continue
        r = Raw(q)
        a, b = f"V(pa{ns})", f"V(na{ns})"
        dcg = db(interp_at(r, 0.1, a) - interp_at(r, 0.1, b))
        g0.append(db(interp_at(r, 16e3, a) - interp_at(r, 16e3, b)) - dcg)
    if g0:
        comp["V5_mc"] = {"n": len(g0), "sigma_db": float(np.std(g0, ddof=1))}
    res["comparison_0ohm"] = comp

    # ---------- 十维 ----------
    P_ = res.get("primary", {})
    dims = {}
    dims["D1"] = P_.get("D1")
    dims["D2"] = res.get("V9b", {}).get("D2")
    dims["D3"] = P_.get("D3")
    dims["D4"] = P_.get("D4")
    dims["D5"] = res.get("D5_real_us") if res.get("D5_valid") else None
    dims["D6a"] = d6.get("D6a_pct")
    dims["D6b"] = d6.get("D6b_lsb")
    dims["D7"] = res.get("D7_mc", {}).get("sigma_db")
    dims["D8"] = d8o.get("D8_primary_db")
    dims["D9"] = res.get("D9", {}).get("D9_real")
    dims["D10"] = P_.get("D10")
    res["dims"] = dims
    res["scores"] = score(dims)
    res["pass"] = pass_flags(dims)
    res["min_score"] = min((v for v in res["scores"].values() if v is not None), default=None)
    res["xcheck"] = xcheck(res, cand, ns)
    return res


# ------------------------------------------------------------------ 评分
def _lin(x, full, bare):
    if x <= full:
        return 1.0
    if x > bare:
        return 0.0
    return 1.0 - (x - full) / (bare - full)


def score(dims):
    """规格 v4 §5.1 归一化方式（D6b 不进 min）。"""
    out = {}
    for k, v in dims.items():
        if v is None:
            out[k] = None
        elif k == "D6b":
            out[k] = None          # 仅报告
        elif k == "D9":
            out[k] = float(v)
        elif k in ("D1", "D2", "D3", "D8"):
            out[k] = min(float(v) / {"D1": 120.0, "D2": 100.0, "D3": 150.0,
                                     "D8": 100.0}[k], 1.0)
        elif k == "D5":
            out[k] = 1.0 if v <= 500 else min(500.0 / float(v), 1.0)
        elif k == "D6a":
            out[k] = 1.0 if v <= 10.0 else (0.0 if v > 30.0 else min(10.0 / float(v), 1.0))
        elif k == "D4":
            out[k] = _lin(float(v), 0.05, 0.5)
        elif k == "D7":
            out[k] = _lin(float(v), 0.01, 0.05)
        elif k == "D10":
            out[k] = _lin(float(v), 1.0, 5.0)
    return out


def pass_flags(dims):
    """规格 v4 §5.1 及格线。D6b 无淘汰线。"""
    d = dims
    return {
        "D1": d["D1"] is not None and d["D1"] >= 80.0,
        "D2": d["D2"] is not None and d["D2"] >= 60.0,
        "D3": d["D3"] is not None and d["D3"] >= 100.0,
        "D4": d["D4"] is not None and d["D4"] <= 0.5,
        "D5": d["D5"] is not None and d["D5"] <= 900.0,
        "D5_valid": d["D5"] is not None,
        "D6a": d["D6a"] is not None and d["D6a"] <= 30.0,
        "D7": d["D7"] is not None and d["D7"] <= 0.05,
        "D8": d["D8"] is not None and d["D8"] >= 80.0,
        "D9": d["D9"] == 1.0,
        "D10": d["D10"] is not None and d["D10"] <= 5.0,
    }


# ------------------------------------------------------------------ 交叉验证
def xcheck(res, cand, ns):
    """规格 §8：AC ≤0.5 dB、建立 ≤5%。

    **主对拍**：真实模型 LTspice（v9a/v9b）↔ 理论引擎 source='opa388'
    （`opt_round5.predict(stages, source='opa388')`）。
    另附 0 Ω 对照口径：LTspice v1/v2（理想 0 Ω 源）↔ 理论 source='ideal'。
    """
    import opt_round5 as o5
    st = [tuple(map(float, s)) for s in cand["stages"]]
    th_real = o5.predict(st, source="opa388")
    th_ideal = o5.predict(st, source="ideal")
    rows = []
    pri = res.get("primary", {})
    vb = res.get("V9b", {})
    pairs = [("D1 A_dm@4.096MHz", pri.get("D1"), th_real["A_dm"]),
             ("D2 A_cm@4.096MHz", vb.get("D2"), th_real["A_cm"]),
             ("D3 A_mclk@16.384MHz", pri.get("D3"), th_real["A_mclk"]),
             ("D4 dG@16kHz", pri.get("D4"), th_real["dG_16k"])]
    for lab, lt, th in pairs:
        if lt is None:
            continue
        rows.append({"item": lab, "ltspice": float(lt), "theory": float(th),
                     "abs_diff": abs(float(lt) - float(th)),
                     "pass": bool(abs(float(lt) - float(th)) <= 0.5)})
    # 0 Ω 对照
    rows0 = []
    c0 = res.get("comparison_0ohm", {})
    v1 = c0.get("V1", {})
    for lab, lt, th in (("D1 (0Ω)", v1.get("D1"), th_ideal["A_dm"]),
                        ("D2 (0Ω)", c0.get("V2", {}).get("D2"), th_ideal["A_cm"]),
                        ("D3 (0Ω)", v1.get("D3"), th_ideal["A_mclk"]),
                        ("D4 (0Ω)", v1.get("D4"), th_ideal["dG_16k"])):
        if lt is None:
            continue
        rows0.append({"item": lab, "ltspice": float(lt), "theory": float(th),
                      "abs_diff": abs(float(lt) - float(th)),
                      "pass": bool(abs(float(lt) - float(th)) <= 0.5)})

    # 建立时间：真实模型 V9c 不收敛（自激），**不能**用来对拍。
    # 改按规格 §8 的同工况原则，用 0 Ω 理想源 V4（R+1 %/C+5 %）对拍理论 0 Ω 最坏角，
    # 两者都是**无源网络**口径（V4 的跟随器是理想源），可比。
    settle = None
    v4 = res.get("V4", {})
    if v4.get("tset_us") is not None:
        # 引擎带 60 µV 单边 = 120 µV 差分；用同一带取 LTspice 值
        q = os.path.join(D, f"r5_{KEY}_r3_v4.raw")
        lt_us = settle_us(Raw(q), ns, band=TBAND_DIFF)[0] if os.path.exists(q) else None
        th_us = o5.predict(st, source="ideal")["t_settle_wc_s"] * 1e6
        if lt_us is not None:
            rel = abs(lt_us - th_us) / th_us
            settle = {"ltspice_us": lt_us, "theory_us": th_us, "rel_diff": rel,
                      "band_uv": TBAND_DIFF * 1e6, "pass": bool(rel <= 0.05),
                      "condition": "0 Ω ideal source, R+1%/C+5%, theory source='ideal'",
                      "note": "真实模型 V9c 自激不收敛，D5 见 D5 段；本条只验证无源网络模型"}
    ok_ac = all(r["pass"] for r in rows) if rows else False
    return {"ac_rows_primary": rows,
            "worst_ac_diff_db": max((r["abs_diff"] for r in rows), default=None),
            "ac_rows_0ohm": rows0,
            "worst_ac_diff_0ohm_db": max((r["abs_diff"] for r in rows0), default=None),
            "settle": settle,
            "primary_model": "TI OPAx388 vs opt_round5(source='opa388')",
            "pass": bool(ok_ac and (settle is None or settle["pass"]))}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--cand", default="A")
    ap.add_argument("--json", default=os.path.join(HERE, "r5_results_r3_A.json"))
    args = ap.parse_args(argv)
    res = analyze(key=args.cand)
    print("=== 方案 %s 十维（规格 v4，真实 OPA388 主口径）===" % args.cand)
    for k in ("D1", "D2", "D3", "D4", "D5", "D6a", "D6b", "D7", "D8", "D9", "D10"):
        v = res["dims"].get(k)
        s = res["scores"].get(k)
        p = res["pass"].get(k)
        tag = "" if k == "D6b" else ("✓" if p else "✗")
        print("  %-4s %12s  分 %5s  %s"
              % (k, "None" if v is None else "%.4f" % v,
                 "—" if s is None else "%.3f" % s, tag))
    print("  min = %s" % (None if res["min_score"] is None else "%.4f" % res["min_score"]))
    if res.get("xcheck"):
        x = res["xcheck"]
        print("\n=== 交叉验证（真实模型）worst AC %s dB, pass=%s ==="
              % (None if x["worst_ac_diff_db"] is None else "%.3f" % x["worst_ac_diff_db"],
                 x["pass"]))
        for r in x["ac_rows_primary"]:
            print("  %-22s LT %8.3f | 理论 %8.3f | Δ %.3f %s"
                  % (r["item"], r["ltspice"], r["theory"], r["abs_diff"],
                     "✓" if r["pass"] else "✗"))
        for r in x["ac_rows_0ohm"]:
            print("  %-22s LT %8.3f | 理论 %8.3f | Δ %.3f %s"
                  % (r["item"], r["ltspice"], r["theory"], r["abs_diff"],
                     "✓" if r["pass"] else "✗"))
    with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=2, default=float)
    print("\n→", args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
