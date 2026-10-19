#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""parse_r5_r3.py — 方案 C 第 3 轮（规格 v4 口径）实测提取 + 理论交叉验证

数据来源
--------
`r5_work/r3_C/r5_C_r3_*.raw`（由 `gen_netlists_r5_r3.py` 生成、`run_r3_C.py` 批跑）。

**主口径 = 真实 OPA388 模型**（规格 v4 §5）：D1/D2/D3/D4/D7/D8/D10 取 `v9a`/`v9b`/`v3p*`/`v5mc_r*`；
理想 0 Ω 源（`v1`/`v2`/`v3s*`/`v5mc*`）**只作对照报告**。

十维键（ask 约定）
  D1 A_dm@4.096 MHz (dB)          D2 A_cm@4.096 MHz (dB)      D3 A_dm@16.384 MHz (dB)
  D4 |ΔG|@16 kHz (dB)             D5 建立 µs（0.01% 带，600 kΩ 最坏角）
  D6a 无源网络噪声增量 %（(V_tot−V_foll)/V_foll，真实模型、同带宽）
  D6b 总积分噪声 LSB（0.1 Hz~2.048 MHz，真实模型）
  D7 σ(ΔG@16k) (dB)               D8 CMRR@通带最差 (dB，R·C 乘积异向配对)
  D9 kickback 122.07 ns 回稳（1.0/0.0）                         D10 Δτ@0.1 Hz~16 kHz (µs)
另有 C9 peaking（真实模型全频段 DM 增益峰值，dB）。

用法
----
    python parse_r5_r3.py --json ../r5_results_r3_C.json
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

from parse_r5 import (  # noqa: E402  复用唯一一份 ASCII raw 解析
    LSB_V, FMOD, MCLK, TBAND_SPEC, TBAND_DIFF, Raw, db, interp_at, pin_names,
    settle_us, noise_nv, kickback,
)
from parse_r5_A import _cap_lock  # noqa: E402  D9 的物理判据（采样电容残余）

D = os.path.join(HERE, "r5_work", "r3_C")
KEY = "C"


def R(tag):
    p = os.path.join(D, f"r5_C_r3_{tag}.raw")
    return Raw(p) if os.path.exists(p) else None


def _pin(ns):
    return f"V(pa{ns})", f"V(na{ns})"


# ------------------------------------------------------------------ AC 指标
def ac_metrics(raw, ns, label=""):
    """DM/CM 增益、平坦度、群延迟、全频段峰值（C9）。"""
    pa, na = _pin(ns)
    f = np.asarray(raw.f, float)
    p = np.asarray(raw.col(pa), complex)
    n = np.asarray(raw.col(na), complex)
    dm = p - n
    cm = (p + n) / 2.0
    g = 20 * np.log10(np.abs(dm) / abs(dm[0]))
    o = {
        "g_dc_db": float(g[0]),
        "g_16k_db": float(np.interp(16e3, f, g)),
        "D1_A_dm_db": float(-np.interp(FMOD, f, g)),
        "D3_A_mclk_db": float(-np.interp(MCLK, f, g)),
        "D4_dG_16k_db": float(abs(np.interp(16e3, f, g))),
        # C9：0.1 Hz~200 MHz 全频段 DM 增益峰值（相对 DC）
        "peaking_db": float(np.max(g)),
        "peaking_f_hz": float(f[int(np.argmax(g))]),
        # CM 侧也报一次（共模谐振同样计入积分噪声）
        "peaking_cm_db": float(np.max(20 * np.log10(np.maximum(np.abs(cm) / abs(cm[0]), 1e-300)))),
    }
    # C9：**有源谐振发生在跟随器输出节点**（若网表存了 fpa/fna）——引脚处被
    # 无源阶梯低通压平，只看引脚会漏判（规格 v4 §5.2 C9 的理由正是「与阶梯电容
    # 形成谐振」，谐振点在被驱动节点）。两处都报，判定用跟随器输出。
    foll = {}
    for nm in ("V(fpa)", "V(fna)"):
        if nm in raw.names:
            y = np.asarray(raw.col(nm), complex)
            gg = 20 * np.log10(np.abs(y) / abs(y[0]))
            foll[nm] = {"peak_db": float(np.max(gg)),
                        "peak_f_hz": float(f[int(np.argmax(gg))])}
    if foll:
        w = max(foll.values(), key=lambda d: d["peak_db"])
        o["C9_peak_follower_db"] = w["peak_db"]
        o["C9_peak_follower_f_hz"] = w["peak_f_hz"]
        o["C9_per_line"] = foll

    # D10 群延迟 0.1 Hz~16 kHz
    m = (f >= 0.1) & (f <= 16e3)
    ph = np.unwrap(np.angle(dm[m]))
    tau = -np.gradient(ph, 2 * math.pi * f[m])
    o["D10_dtau_us"] = float((tau.max() - tau.min()) * 1e6)
    o["tau_100Hz_us"] = float(tau[0] * 1e6)
    o["tau_16k_us"] = float(tau[-1] * 1e6)
    # CH1 vs CH2（同一差分对的 p/n 两腿）群延迟差 —— 规格 §5.1a 要求单列
    tp = -np.gradient(np.unwrap(np.angle(p[m])), 2 * math.pi * f[m])
    tn = -np.gradient(np.unwrap(np.angle(n[m])), 2 * math.pi * f[m])
    o["CH_legs_tau_diff_ns"] = float(np.max(np.abs(tp - tn)) * 1e9)
    if label:
        o["label"] = label
    return o


def cm_metrics(raw, ns):
    """共模：衰减 @fMOD（相对 DC 单线电压）。"""
    pa, _ = _pin(ns)
    f = np.asarray(raw.f, float)
    p = np.asarray(raw.col(pa), complex)
    g = 20 * np.log10(np.abs(p) / abs(p[0]))
    return {"D2_A_cm_db": float(-np.interp(FMOD, f, g)),
            "g_cm_dc_db": float(g[0]),
            "g_cm_fmod_db": float(np.interp(FMOD, f, g))}


def cmrr_passband(raw, ns, f_lo=10.0, f_hi=16e3):
    """CMRR = 20log10(|Vcm|/|Vdiff|)，取通带最差。"""
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
def settle_all(path, ns, t_step=10e-6):
    rr = Raw(path)
    out = {}
    for band, nm in ((TBAND_SPEC, "spec_200uV"), (TBAND_DIFF, "engine_120uV")):
        ts, vf, ef = settle_us(rr, ns, band=band, t_step=t_step)
        out[nm] = {"tset_us": ts, "vfinal_v": vf, "err_final_uv": ef * 1e6}
    return out


# ------------------------------------------------------------------ 主流程
def analyze():
    with open(os.path.join(HERE, "r5_candidates_r2.json"), encoding="utf-8") as fh:
        cand = json.load(fh)[KEY]
    st = [tuple(map(float, s)) for s in cand["stages"]]
    ns = len(st)
    res = {"scheme": KEY, "round": 3, "n_stages": ns, "stages": st,
           "dir": D, "units": {
               "D1/D2/D3/D4/D8/D10": "dB", "D5": "µs", "D6a": "%",
               "D6b": "LSB", "D9": "binary"}}

    # ================= 主口径：真实 OPA388 =================
    r9a = R("v9a")
    real = {}
    real.update(ac_metrics(r9a, ns, "v9a real OPA388 AC DM"))
    real_cm = cm_metrics(R("v9b"), ns)

    # ================= 对照：理想 0 Ω 源 =================
    ctrl = {}
    ctrl.update(ac_metrics(R("v1"), ns, "v1 ideal 0ohm AC DM"))
    ctrl_cm = cm_metrics(R("v2"), ns)

    # ================= D2 =================
    D2_real = real_cm["D2_A_cm_db"]
    D2_ctrl = ctrl_cm["D2_A_cm_db"]

    # ================= D8（真实模型，配对 / 同向） =================
    d8 = {"paired": {}, "same_direction_real": {}, "same_direction_ideal": {}}
    for m in (0.001, 0.005, 0.01):
        tag = f"v3p{int(m*1000):03d}"
        rr = R(tag)
        if rr:
            d8["paired"][f"{m*100:g}%"] = cmrr_passband(rr, ns)
    for m in (0.001, 0.005, 0.01):
        tag = f"v3sr{int(m*1000):03d}"
        rr = R(tag)
        if rr:
            d8["same_direction_real"][f"{m*100:g}%"] = cmrr_passband(rr, ns)
    for m in (0.001, 0.005, 0.01):
        tag = f"v3s{int(m*1000):03d}"
        rr = R(tag)
        if rr:
            d8["same_direction_ideal"][f"{m*100:g}%"] = cmrr_passband(rr, ns)

    # 规格 v4 考核条件：两线 R·C 乘积配对；取三档里**最优**档作为 D8 记分
    # （ask 原文：「D8 单位 dB（配对条件下最优档）」）
    if d8["paired"]:
        best_key = max(d8["paired"], key=lambda k: d8["paired"][k]["CMRR_db"])
        D8 = d8["paired"][best_key]["CMRR_db"]
        D8_best_m = best_key
    else:
        D8, D8_best_m = None, None

    # ================= D7（真实模型 MC 30 次） =================
    def mc_sigma(prefix, n=30):
        vals = []
        for k in range(1, n + 1):
            p = os.path.join(D, f"r5_C_r3_{prefix}{k:02d}.raw")
            if not os.path.exists(p):
                continue
            rr = Raw(p)
            pa, na = _pin(ns)
            g = db(interp_at(rr, 16e3, pa) - interp_at(rr, 16e3, na))
            g0 = db(interp_at(rr, 0.1, pa) - interp_at(rr, 0.1, na))
            vals.append(g - g0)
        if not vals:
            return None
        return {"n": len(vals), "sigma_db": float(np.std(vals, ddof=1)),
                "mean_db": float(np.mean(vals)), "min_db": float(np.min(vals)),
                "max_db": float(np.max(vals)), "p2p_db": float(np.max(vals) - np.min(vals))}

    mc_real = mc_sigma("v5mc_r")
    mc_ideal = mc_sigma("v5mc")

    # ================= D6a / D6b（真实模型噪声） =================
    nz = {}
    for tag in ("v9d", "v9d_nl", "v9n", "v7"):
        rr = R(tag)
        if rr:
            nz[tag] = noise_nv(rr)
    v_tot = nz["v9d"]["D6_Vn_nv"]
    v_foll = nz["v9d_nl"]["D6_Vn_nv"]        # 同带宽（阶梯传函）下的跟随器自身噪声
    v_alone = nz["v9n"]["D6_Vn_nv"]          # 纯跟随器（无阶梯，全带宽）——仅供对照
    v_ideal = nz["v7"]["D6_Vn_nv"] if "v7" in nz else None
    d6a_literal = 100.0 * (v_tot - v_foll) / v_foll
    d6a_quad = 100.0 * math.sqrt(max(v_tot ** 2 - v_foll ** 2, 0.0)) / v_foll
    d6b = nz["v9d"]["D6_Vn_lsb"]
    # 全频段噪声谱峰值（C9 的频域旁证）
    rr = R("v9d")
    f9 = np.asarray(rr.f, float)
    d9 = np.abs(np.asarray(rr.col("v(onoise)"), float))
    dens_peak = float(np.max(d9))
    noise_peaking = {
        "dens_peak_nv": dens_peak * 1e9,
        "dens_peak_f_hz": float(f9[int(np.argmax(d9))]),
        "dens_1k_nv": float(np.interp(1e3, f9, d9) * 1e9),
        "dens_1M_nv": float(np.interp(1e6, f9, d9) * 1e9),
        "peak_over_1k_db": float(20 * math.log10(dens_peak / np.interp(1e3, f9, d9))),
    }

    # ================= D5（真实模型瞬态，多设置收敛核对） =================
    d5 = {}
    for tag in ("v9c", "v9c_b", "v9c_nom", "v9f", "v9f_b", "v9f_long"):
        p = os.path.join(D, f"r5_C_r3_{tag}.raw")
        if not os.path.exists(p):
            continue
        try:
            d5[tag] = settle_all(p, ns)
        except Exception as e:                                  # noqa: BLE001
            d5[tag] = {"error": repr(e)}
    # 每个真实模型瞬态都判一次「是否真的稳定到直流工作点」：
    # 末 20% 窗口内任一条线跟随器输出的 std > 10 mV 即判为**未稳定**（极限环/自激）。
    # 这一项独立于建立时间：如果它不通过，tset 只是"最后一次越过 0.01% 带的时刻"，
    # 数值本身没有物理意义（波形在带内来回穿）。
    for tag in list(d5):
        if not tag.startswith("v9"):
            continue
        rr = Raw(os.path.join(D, f"r5_C_r3_{tag}.raw"))
        t = np.asarray(rr.cols[0], float)
        m = t >= 0.8 * t[-1]
        worst = {}
        for nm in ("V(fpa)", "V(fna)", "V(pa4)", "V(na4)"):
            if nm in rr.names:
                y = np.asarray(rr.col(nm), float)
                worst[nm] = {"mean": float(y[m].mean()), "std": float(y[m].std()),
                             "p2p": float(y[m].max() - y[m].min())}
        if worst:
            smax = max(v["std"] for v in worst.values())
            d5[tag]["stability"] = {
                "tail_window": "last 20% of run",
                "nodes": worst,
                "max_std_v": smax,
                "stable": bool(smax <= 10e-3),
            }
    for tag in ("v4", "v4b"):
        p = os.path.join(D, f"r5_C_r3_{tag}.raw")
        if os.path.exists(p):
            d5[tag + "_ideal"] = settle_all(p, ns)

    # D5 记分口径：规格 §5.1「最坏角 + 测试须覆盖高源阻抗工况（样品 600 kΩ 端）」
    # → v9f 系列（真实 OPA388 + 600 kΩ + R×1.01/C×1.05）。取三条独立设置在
    # 「已判为 stable」的前提下最慢的一个；若都不 stable 则记 None（不外推）。
    d5_real = {k: v["spec_200uV"]["tset_us"] for k, v in d5.items()
               if k.startswith("v9f")
               and "spec_200uV" in v
               and v.get("stability", {}).get("stable", False)}
    d5_value = max(d5_real.values()) if d5_real else None

    # ================= V6 蒙特卡洛瞬态 30 次（D5 统计稳健性） =================
    v6 = []
    for k in range(1, 31):
        pp = os.path.join(D, f"r5_C_r3_v6mc{k:02d}.raw")
        if not os.path.exists(pp):
            continue
        try:
            tk, _, _ = settle_us(Raw(pp), ns, band=TBAND_SPEC)
            if np.isfinite(tk):
                v6.append(float(tk))
        except Exception:                                       # noqa: BLE001
            pass
    res["V6_mc_transient"] = ({"n": len(v6), "min_us": float(np.min(v6)),
                               "mean_us": float(np.mean(v6)),
                               "max_us": float(np.max(v6))} if v6 else None)

    # ================= v9e：600 kΩ 样品端 AC（§5.1 高阻工况的 AC 视角） =================
    r9e = R("v9e")
    if r9e is not None:
        f = np.asarray(r9e.f, float)
        dme = (np.asarray(r9e.col(f"V(pa{ns})"), complex)
               - np.asarray(r9e.col(f"V(na{ns})"), complex))
        ge = 20 * np.log10(np.abs(dme) / abs(dme[0]))
        fae = np.asarray(r9e.col("V(fa)"), complex)
        gfa = 20 * np.log10(np.abs(fae) / abs(fae[0]))
        res["V9e_600k_ac"] = {
            "D1_A_dm_db": float(-np.interp(FMOD, f, ge)),
            "D3_A_mclk_db": float(-np.interp(MCLK, f, ge)),
            "dG_16k_db": float(abs(np.interp(16e3, f, ge))),
            "input_node_droop_16k_db": float(np.interp(16e3, f, gfa)),
            "note": "**不改写 D4**（规格 §5.1 标准测试条件：V1–V6 源阻抗 0 Ω，D4→V1）。"
                    "此块仅作灵敏度披露：600 kΩ 端 16 kHz 平坦度劣化到 0.49 dB，"
                    "逼近 0.5 dB 及格线；来源是 600 kΩ×(OPA388 输入电容 ≈9.4 pF) 的输入极点",
        }

    # ================= D9（真实模型 kickback + 灵敏度） =================
    d9 = {}
    for ron in (1, 100, 1000):
        p = os.path.join(D, f"r5_C_r3_v8r_ron{ron:g}.raw")
        if not os.path.exists(p):
            continue
        rr = Raw(p)
        kb = kickback(rr, ns)
        kb["cap_lock"] = _cap_lock(rr, ns)
        d9[f"ron{ron:g}"] = kb
    for ron in (1, 100, 1000):
        p = os.path.join(D, f"r5_C_r3_v8_ron{ron:g}.raw")
        if os.path.exists(p):
            kb = kickback(Raw(p), ns)
            kb["cap_lock"] = _cap_lock(Raw(p), ns)
            d9[f"ideal_ron{ron:g}"] = kb

    D9 = float(d9["ron1"]["D9"]) if "ron1" in d9 else None

    # ================= 汇总 dims =================
    dims = {
        "D1": real["D1_A_dm_db"],
        "D2": D2_real,
        "D3": real["D3_A_mclk_db"],
        "D4": real["D4_dG_16k_db"],
        "D5": d5_value,
        "D6a": d6a_literal,
        "D6b": d6b,
        "D7": mc_real["sigma_db"] if mc_real else None,
        "D8": D8,
        "D9": D9,
        "D10": real["D10_dtau_us"],
    }
    res["dims"] = dims

    res["real_model"] = {**real, **real_cm,
                         "peaking_ok_c9": bool(real["peaking_db"] <= 6.0)}
    res["ideal_control"] = {**ctrl, **ctrl_cm}

    res["D8_detail"] = {"note": "考核条件 = 两线 R·C 乘积异向配对（R×(1+m) 配 C×(1−m)），"
                                "真实 OPA388 模型；ideal_* 为 0 Ω 理想源对照",
                        **d8, "D8_best_pair_m": D8_best_m}
    res["D7_detail"] = {"real_opamp": mc_real, "ideal_source": mc_ideal}
    res["D6_detail"] = {"total_with_ladder_nv": v_tot,
                        "follower_via_ladder_nv": v_foll,
                        "follower_alone_fullband_nv": v_alone,
                        "ideal_v7_nv": v_ideal,
                        "D6a_literal_pct": d6a_literal,
                        "D6a_quadrature_pct": d6a_quad,
                        "D6b_lsb": d6b,
                        "D6b_nv": nz["v9d"]["D6_Vn_nv"],
                        "lsb_nv": LSB_V * 1e9,
                        "noise_spectrum": noise_peaking,
                        "raw": {k: os.path.join(D, f"r5_C_r3_{k}.raw") for k in nz}}
    res["D5_detail"] = d5
    res["D9_detail"] = d9

    return res, cand, st, ns


# ------------------------------------------------------------------ 理论 + 交叉验证
def theory_and_xcheck(res, cand, st, ns):
    """规格 §8 交叉验证。**必须同口径**：理论有两套源模型，LTspice 也有两套。

      A. 纯无源：理论 rs→0（xcheck_B） ↔ LTspice 理想 0 Ω（v1/v2/v4）
      B. 含跟随器：理论 opa388 源模型（opt_round5.predict） ↔ LTspice TI 宏模型（v9a/v9b/v9d）
    拿 A 的理论去比 B 的实测会凭空差 26–40 dB —— 那是跟随器在 fMOD 的 34–42 Ω 输出阻抗
    与 GBW 滚降，不是模型误差（第 1 轮就踩过这个坑，见 gen_netlists_r5.py 文件头）。
    """
    import opt_round5 as o5
    import xcheck_B as X
    import r5_score_v4 as S4

    p = o5.predict(st)                       # 理论（含 opa388 源模型）
    th0 = X.predict_zero_source(st)          # 理论（纯无源，rs→0）
    res["theory_engine_pred"] = {k: float(v) for k, v in p.items()
                                 if isinstance(v, (int, float))}
    res["theory_zero_source"] = {k: float(v) for k, v in th0.items()}

    d = res["dims"]
    rm = res["real_model"]
    ctl = res["ideal_control"]
    xc = {"B_real_model": {"rows": []},
          "A_zero_source_ideal": {"rows": []},
          "note": "B = 含跟随器（主口径）；A = 纯无源（规格 §5.1 理想源对照）"}

    # ---------- B：真实模型，理论(opa388 源模型) ↔ LTspice(TI 宏模型) ----------
    for lab, lt, thv in (("D1 A_dm@fMOD", rm["D1_A_dm_db"], p["A_dm"]),
                         ("D2 A_cm@fMOD", rm["D2_A_cm_db"], p["A_cm"]),
                         ("D3 A_mclk@MCLK", rm["D3_A_mclk_db"], p["A_mclk"]),
                         ("D4 dG@16k", rm["D4_dG_16k_db"], p["dG_16k"]),
                         ("D10 dtau_us", rm["D10_dtau_us"], p["group_delay_flat_s"] * 1e6)):
        dv = float(lt) - float(thv)
        xc["B_real_model"]["rows"].append(
            {"item": lab, "theory": float(thv), "ltspice": float(lt),
             "abs_diff": dv, "pass_0p5": bool(abs(dv) <= 0.5)})
    # 噪声：引擎 V_n_lsb（含跟随器）↔ LT v9d 总积分噪声
    th_nv = p["V_n_lsb"] * LSB_V * 1e9
    th_foll_nv = p["V_n_lsb_follower"] * LSB_V * 1e9
    xc["B_real_model"]["noise_total"] = {
        "theory_nv": float(th_nv), "ltspice_nv": float(res["D6_detail"]["total_with_ladder_nv"]),
        "rel_pct": float(100 * (res["D6_detail"]["total_with_ladder_nv"] - th_nv) / th_nv),
        "pass_5pct": bool(abs(res["D6_detail"]["total_with_ladder_nv"] - th_nv) <= 0.05 * th_nv)}
    xc["B_real_model"]["noise_follower_only"] = {
        "theory_nv": float(th_foll_nv),
        "ltspice_nv": float(res["D6_detail"]["follower_via_ladder_nv"]),
        "rel_pct": float(100 * (res["D6_detail"]["follower_via_ladder_nv"] - th_foll_nv)
                         / th_foll_nv),
        "pass_5pct": bool(abs(res["D6_detail"]["follower_via_ladder_nv"] - th_foll_nv)
                          <= 0.05 * th_foll_nv),
        "note": "LT 用 v9d_nl（阶梯电阻全 noiseless，只留跟随器经阶梯的传递）对引擎 V_n_lsb_follower"}
    # D8：CMRR 属 AC 量，但它是两个小量之比且在 16 kHz（跟随器环路增益已降），
    # 单列一行、单列判据，不与 D1–D4 混算。
    th_cmrr = S4.cmrr_rc_paired(st, 0.01)
    lt_cmrr = res["D8_detail"]["paired"].get("1%", {}).get("CMRR_db")
    if lt_cmrr is not None:
        dv = lt_cmrr - th_cmrr
        xc["B_real_model"]["cmrr_1pct_paired"] = {
            "theory_db": float(th_cmrr), "ltspice_db": float(lt_cmrr),
            "abs_diff": float(dv), "pass_0p5": bool(abs(dv) <= 0.5),
            "note": "理论 = opt_round5 双线 MNA，源模型 opa388；"
                    "LT = TI 宏模型。差 0.8 dB 来自跟随器有限环路增益/CMRR 建模差异"}

    # ---------- A：纯无源，理论(rs→0) ↔ LTspice 理想 0 Ω ----------
    for lab, lt, thv in (("D1 A_dm@fMOD", ctl["D1_A_dm_db"], th0["A_dm"]),
                         ("D2 A_cm@fMOD", ctl["D2_A_cm_db"], th0["A_cm"]),
                         ("D3 A_mclk@MCLK", ctl["D3_A_mclk_db"], th0["A_mclk"]),
                         ("D4 dG@16k", ctl["D4_dG_16k_db"], th0["dG_16k"]),
                         ("D10 dtau_us", ctl["D10_dtau_us"], th0["dtau_us"])):
        dv = float(lt) - float(thv)
        xc["A_zero_source_ideal"]["rows"].append(
            {"item": lab, "theory": float(thv), "ltspice": float(lt),
             "abs_diff": dv, "pass_0p5": bool(abs(dv) <= 0.5)})
    th_nv0 = th0["Vn_nv"]
    lt_nv0 = res["D6_detail"].get("ideal_v7_nv")
    if lt_nv0:
        xc["A_zero_source_ideal"]["noise"] = {
            "theory_nv": float(th_nv0), "ltspice_nv": float(lt_nv0),
            "rel_pct": float(100 * (lt_nv0 - th_nv0) / th_nv0),
            "pass_5pct": bool(abs(lt_nv0 - th_nv0) <= 0.05 * th_nv0)}

    # ---------- 建立（同工况：0 Ω 最坏角，纯无源） ----------
    v4 = res["D5_detail"].get("v4_ideal", {}).get("spec_200uV", {})
    th_s = th0["t_settle_wc_us"]
    lt_s = v4.get("tset_us")
    if lt_s:
        rel = (lt_s - th_s) / th_s
        xc["A_zero_source_ideal"]["settle"] = {
            "theory_us": float(th_s), "ltspice_us": float(lt_s),
            "rel_diff": float(rel), "pass_5pct": bool(abs(rel) <= 0.05),
            "note": "0 Ω 最坏角（R×1.01/C×1.05）同工况对拍"}

    # ---------- D5 收敛性：三条独立设置 ----------
    conv = {}
    for k in ("v9f", "v9f_b", "v9f_long"):
        if k in res["D5_detail"] and "spec_200uV" in res["D5_detail"][k]:
            conv[k] = res["D5_detail"][k]["spec_200uV"]["tset_us"]
    if conv:
        lo, hi = min(conv.values()), max(conv.values())
        spread = (hi - lo) / lo if lo > 0 else float("inf")
        xc["D5_convergence"] = {
            "values_us": conv, "spread_pct": float(100 * spread),
            "settings": "v9f = gear20ns(第2轮口径)；v9f_b = gear+2ns+reltol 1e-6；"
                        "v9f_long = gear20ns + 600µs 窗口",
            "pass": bool(spread <= 0.05)}

    # ---------- C9 ----------
    c9_f = rm.get("C9_peak_follower_db")
    xc["C9_peaking"] = {
        "pin_dm_peak_db": rm["peaking_db"],
        "follower_node_peak_db": c9_f,
        "follower_node_f_hz": rm.get("C9_peak_follower_f_hz"),
        "limit_db": 6.0,
        "pass_pin_level": bool(rm["peaking_db"] <= 6.0),
        "pass_follower_level": bool(c9_f is not None and c9_f <= 6.0),
        # 基线：旧参数 A 案的同一节点峰值（第 2 轮把 +30.7 dB 记为"案例"，本轮复核为 +14.0 dB）
        "baseline_A_old_params_follower_db": 14.01,
        "baseline_A_old_params_pin_dm_db": 1.73,
        "note": "引擎 peaking_db 与 v4 评分脚本都按**引脚 DM** 定义 → 本方案通过（无峰）；"
                "但跟随器输出节点有 11.2 dB 峰（C9 的物理机理所在处），引脚处被阶梯低通压平。"
                "两者都报，见 D5 的 0 Ω 大幅边沿极限环"}

    # ---------- D5 稳定性的专项旁证（0 Ω 大幅边沿工况） ----------
    xc["D5_stability_note"] = {
        "v9c_0ohm_corner": res["D5_detail"].get("v9c", {}).get("stability"),
        "v9c_nominal_params_0ohm": res["D5_detail"].get("v9c_nom", {}).get("stability"),
        "v9f_600k_corner": res["D5_detail"].get("v9f", {}).get("stability"),
        "small_signal_loop": "chk_smallpert.raw：DC 1.0 V 上叠加 1 mV/0.1 µs 脉冲，"
                             "扰动在 ~40 µs 内衰减到 1e-10 量级（fna p2p 2.5e-3 → 4.9e-13 V）"
                             "→ **小信号环路稳定、无 RHP 极点**",
        "mechanism": "follower 节点有 11.2 dB @320 kHz 的传输峰，源于 TI 模型在 100–600 kHz "
                     "的**负实部输出阻抗**（AC 实测 Re(Zo) = −0.12 Ω@100k、−1.25 Ω@320k、"
                     "−3.57 Ω@1M）。负阻 + 阶梯电容在**大信号**（2 V 全摆幅、10 ns 沿）"
                     "下进入模型过载/恢复块的非线性区，形成不衰减的极限环；同工况的"
                     "小信号扰动则正常衰减。",
        "amplitude_threshold": {
            "note": "单线 N 线 2 V 初始电平、10 ns 沿、不同下跳幅度（chk_step*.raw）",
            "0.05V": "稳定（尾窗 std 3.2e-11）", "0.10V": "稳定（6.3e-11）",
            "0.20V": "稳定（1.3e-10）", "0.30V": "极限环（std 0.48 V）",
            "0.50V": "极限环（std 0.46 V）", "1.00V": "极限环（std 0.21 V）"},
        "verdict": "0 Ω + 10 ns 全摆幅边沿工况的 tset 数值无物理意义，**不用于 D5 记分**；"
                   "D5 按规格 §5.1 取 600 kΩ 高阻端工况（v9f，该工况稳定到 1.8e-9 V）。"
                   "**但阈值 0.2–0.3 V 提示**：本拓扑在 0 Ω 源、>0.2 V 快速阶跃下会进极限环，"
                   "属必须交付前复核的 A 类风险。**边沿速率阈值**（chk_edge_*）："
                   "10 ns / 100 ns / 1 µs 沿均复现极限环，10 µs 沿则完全稳定；"
                   "在跟随器输入侧串 73 Ω / 1 kΩ / 10 kΩ 都不能改善（chk_rs*，栅极电容主导）。"
                   "600 kΩ 工况之所以稳定，是因为输入侧 600 kΩ×8.5 pF 把边沿自然拉慢到 ~2.7 µs。",
    }

    ac_b = [r for r in xc["B_real_model"]["rows"] if not r["pass_0p5"]]
    ac_a = [r for r in xc["A_zero_source_ideal"]["rows"] if not r["pass_0p5"]]
    xc["ac_fail_B"] = [r["item"] for r in ac_b]
    xc["ac_fail_A"] = [r["item"] for r in ac_a]
    # 规格 §8 只给**两条**判据：AC 衰减偏差 ≤0.5 dB、建立偏差 ≤5%。
    # CMRR 是"两个小量之比"，不是衰减量，0.5 dB 判据对其不适用（95 dB 处的 0.84 dB
    # 是 10% 的电压比差，对应失配等效 0.08%→0.09%）。故**单列**、不并入 pass，
    # 但在报告与 notes 里如实给出数值。
    xc["pass_criteria"] = ("规格 §8：AC 衰减 ≤0.5 dB（A/B 两块的全部 rows）+ 建立 ≤5%"
                           "（A 块 settle）+ D5 三设置一致性 ≤5% + 噪声 5%")
    xc["pass"] = bool(
        not ac_a
        and not ac_b
        and xc["A_zero_source_ideal"].get("settle", {}).get("pass_5pct", True)
        and xc["D5_convergence"]["pass"]
        and xc["B_real_model"]["noise_total"]["pass_5pct"]
        and xc["B_real_model"]["noise_follower_only"]["pass_5pct"])
    xc["cmrr_out_of_band"] = xc["B_real_model"].get("cmrr_1pct_paired", {}).get("abs_diff")
    res["xcheck"] = xc
    return res


# ------------------------------------------------------------------ 评分（规格 v4 §5.1）
def score(dims):
    def ratio(x, full):
        return 1.0 if x is None else float(min(x / full, 1.0))

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
        "D5": inv(dims["D5"], 500.0) if dims["D5"] else 0.0,
        "D6a": inv(dims["D6a"], 10.0) if dims["D6a"] and dims["D6a"] > 0 else 1.0,
        "D7": lin(dims["D7"], 0.01, 0.05),
        "D8": ratio(dims["D8"], 100.0),
        "D9": float(dims["D9"]) if dims["D9"] is not None else 0.0,
        "D10": lin(dims["D10"], 1.0, 5.0),
    }
    pf = {
        "D1": dims["D1"] >= 80, "D2": dims["D2"] >= 60, "D3": dims["D3"] >= 100,
        "D4": dims["D4"] <= 0.5, "D5": dims["D5"] is not None and dims["D5"] <= 900,
        "D6a": dims["D6a"] <= 30.0,
        "D7": dims["D7"] is not None and dims["D7"] <= 0.05,
        "D8": dims["D8"] is not None and dims["D8"] >= 80,
        "D9": dims["D9"] == 1.0, "D10": dims["D10"] <= 5.0,
    }
    return s, pf, float(min(s.values()))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=os.path.join(HERE, "r5_results_r3_C.json"))
    args = ap.parse_args(argv)

    res, cand, st, ns = analyze()
    res = theory_and_xcheck(res, cand, st, ns)
    s, pf, mn = score(res["dims"])
    res["scores"] = s
    res["pass"] = pf
    res["min_score"] = mn
    res["failing"] = [k for k, v in pf.items() if not v]

    with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=2, default=float)

    print("=== 方案 C 第 3 轮（规格 v4，真实 OPA388 主口径）===")
    for k in ("D1", "D2", "D3", "D4", "D5", "D6a", "D6b", "D7", "D8", "D9", "D10"):
        v = res["dims"][k]
        sc = res["scores"].get(k)
        vs = "None" if v is None else f"{v:.4f}"
        ss = "None" if sc is None else f"{sc:.4f}"
        tag = "" if k == "D6b" else ("过线" if res["pass"].get(k) else "×淘汰")
        print(f"  {k:5s} {vs:>12}  分={ss:>8}  {tag}")
    print(f"  min = {mn:.4f}   未及格 = {res['failing']}")
    print("\n--- 交叉验证（规格 §8）---")
    for blk, name in (("B_real_model", "B 含跟随器：理论(opa388源) vs LT(TI宏模型)"),
                      ("A_zero_source_ideal", "A 纯无源：理论(rs→0) vs LT(理想0Ω)")):
        print(f"  [{name}]")
        for r in res["xcheck"][blk]["rows"]:
            print(f"    {r['item']:16s} 理论 {r['theory']:9.3f} | LT {r['ltspice']:9.3f} "
                  f"| Δ {r['abs_diff']:+.3f} {'✓' if r['pass_0p5'] else '✗'}")
        for k in ("noise", "noise_total", "noise_follower_only", "settle", "cmrr_1pct_paired"):
            if k in res["xcheck"][blk]:
                v = res["xcheck"][blk][k]
                ok = v.get("pass_0p5", v.get("pass_5pct"))
                nums = "  ".join(f"{kk}={vv:.4g}" for kk, vv in v.items()
                                 if isinstance(vv, (int, float)))
                print(f"    {k:22s} {nums}  {'✓' if ok else '✗'}")
    for k in ("D5_convergence", "C9_peaking"):
        print(f"  {k}: {json.dumps(res['xcheck'][k], ensure_ascii=False)}")
    print(f"  xcheck pass = {res['xcheck']['pass']}")
    print("→", args.json)
    return res


if __name__ == "__main__":
    main()
