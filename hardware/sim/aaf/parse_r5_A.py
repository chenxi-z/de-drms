# -*- coding: utf-8 -*-
"""parse_r5_A.py — 方案 A 十维实测值提取 + 理论/引擎交叉验证（Round 5 复测）

背景
----
`parse_r5.py` 由另一会话维护（默认口径 `--rs 1`，即 `opt_engine` 的源内阻镜像）。
本文件**只做方案 A**、并处理规格 §5.1 的 **0 Ω 理想源**口径与交叉验证口径的分离：
  * ``rs0/`` —— 规格口径（正式评分）：V1–V9 全量，源阻抗 0 Ω
  * ``rs1/`` —— 引擎镜像口径（仅交叉验证）：V1/V2/V3/V4/V4b/V7

十维 → 仿真映射（规格 §7 覆盖矩阵）
  D1 → V1 @4.096 MHz 差分衰减      D2 → V2 @4.096 MHz 共模衰减
  D3 → V1 @16.384 MHz 差分衰减     D4 → V1 16 kHz 相对 DC 增益偏差
  D5 → V4 最坏角 0.01% 建立        D6 → V7 积分噪声（0.1 Hz–2.048 MHz）
  D7 → V5 30× MC 的 σ(ΔG@16k)      D8 → V3 CMRR@通带最差
  D9 → V8 kickback 122 ns 回稳     D10 → V1 群延迟 0.1 Hz–16 kHz 变化量

单位：衰减/CMRR dB（正值 = 衰减量）、建立 µs、噪声 nVrms、群延迟 µs、D9 二值。

用法::

    python parse_r5_A.py --dir r5_work/rs0 --mirror r5_work/rs1 \\
                         --json r5_results_A.json
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from parse_r5 import (  # noqa: E402  —— 复用 ASCII raw 解析（唯一实现）
    LSB_V, FMOD, MCLK, KB_WIN_S, TBAND_DIFF, Raw, db, interp_at, pin_names,
    d1_d3_d4_d10, d2, d8, settle_us, noise_nv, kickback,
)

# 0.01% 建立带。差分阶跃幅度 = 2 V（±1 V/线），故 0.01% = 200 µV 差分。
# `parse_r5.TBAND_DIFF`（120 µV）是前战役按 2.4 Vpp 定的口径，相当于 0.006%，
# 比规格更严 —— 本文件两者都算：规格口径 200 µV 用于 D5 打分，120 µV 用于与
# `opt_engine` 同带宽交叉验证（引擎的 60 µV 单边 = 差分 120 µV）。
TBAND_SPEC = 200e-6
STEP_DIFF_V = 2.0


def _settle_both(path, ns):
    """同一 .raw 上、两种带宽的建立时间（µs）。"""
    r = Raw(path)
    spec_us, _, _ = settle_us(r, ns, band=TBAND_SPEC)
    eng_us, _, _ = settle_us(r, ns, band=TBAND_DIFF)
    return spec_us, eng_us


# --------------------------------------------------------------- 单点提取
def _v1_metrics(raw, ns):
    """V1 → D1/D3/D4/D10 + CH 间群延迟差（规格 §5.1 注：须单列）。"""
    o = d1_d3_d4_d10(raw, ns)
    pa, na = pin_names(range(ns))
    f = raw.f
    m = (f >= 0.1) & (f <= 16e3)
    tau_p = -np.gradient(np.unwrap(np.angle(np.array(raw.col(pa))[m])),
                         2 * math.pi * f[m])
    tau_n = -np.gradient(np.unwrap(np.angle(np.array(raw.col(na))[m])),
                         2 * math.pi * f[m])
    o["CH_tau_diff_us"] = float(np.max(np.abs(tau_p - tau_n)) * 1e6)
    o["tau_p_16k_us"] = float(tau_p[-1] * 1e6)
    o["tau_n_16k_us"] = float(tau_n[-1] * 1e6)
    return o


def _mc_sigma(dirpath, key, ns, tag, n=30):
    """V5 蒙特卡洛：16 kHz 相对增益的样本标准差（ddof=1）。"""
    g16 = []
    for k in range(1, n + 1):
        p = os.path.join(dirpath, f"r5_{key}_{tag}mc{k:02d}.raw")
        if not os.path.exists(p):
            continue
        rr = Raw(p)
        pa, na = pin_names(range(ns))
        dcg = db(interp_at(rr, 0.1, pa) - interp_at(rr, 0.1, na))
        g = db(interp_at(rr, 16e3, pa) - interp_at(rr, 16e3, na))
        g16.append(g - dcg)
    if not g16:
        return {}
    return {"n": len(g16), "sigma_db": float(np.std(g16, ddof=1)),
            "mean_db": float(np.mean(g16)), "min_db": float(np.min(g16)),
            "max_db": float(np.max(g16)),
            "p2p_db": float(np.max(g16) - np.min(g16))}


def _cap_lock(raw, nstage, tol=1e-4):
    """D9 的**物理判据**：采样电容是否在 fMOD 半周期内追上引脚电压。

    规格 §5.1 D9 =「fMOD 半周期（122 ns）内回稳到 0.01% 带内」。
    `parse_r5.kickback()` 的判据是「引脚相对自身稳态值」，在**无外部扰动**时
    分母趋零、近乎自证。真正决定 ADC 误差的是**采样电容 C_S 在采样窗口末端
    与引脚之间的残余电压** |V_C_S − V_pin| / |V_pin|：这直接是电荷转移误差。

    这里按后者各算一遍，取 10 个周期最差值。
    """
    pa, _ = pin_names(range(nstage))
    t = np.array([v.real if isinstance(v, complex) else v for v in raw.cols[0]], dtype=float)
    p = np.array(raw.col(pa), dtype=float)
    cs = np.array(raw.col("V(csa)"), dtype=float) if "V(csa)" in raw.names else None
    if cs is None:
        return {"available": False}
    T = 1.0 / FMOD
    rows = []
    for k in range(2, 12):
        t_on = k * T
        t_end = t_on + KB_WIN_S
        if t_end > t[-1] - 2 * T:
            break
        vp = float(np.interp(t_end, t, p))
        vc = float(np.interp(t_end, t, cs))
        kick = abs(float(np.interp(t_on + 2e-9, t, p)) - float(np.interp(t_on - 2e-9, t, p)))
        rows.append({"k": k, "kick_uv": kick * 1e6,
                     "resid_nv": abs(vc - vp) * 1e9,
                     "rel": abs(vc - vp) / abs(vp) if vp else 0.0})
    if not rows:
        return {"available": False}
    worst = max(rows, key=lambda r: r["rel"])
    return {"available": True, "worst_rel": worst["rel"],
            "worst_resid_nv": worst["resid_nv"],
            "worst_kick_uv": max(r["kick_uv"] for r in rows),
            "n_cycles": len(rows), "pass": worst["rel"] <= tol, "detail": rows[:3]}


def _mc_settle(dirpath, key, ns, n=30):
    ts = []
    for k in range(1, n + 1):
        p = os.path.join(dirpath, f"r5_{key}_v6mc{k:02d}.raw")
        if not os.path.exists(p):
            continue
        tk, _, _ = settle_us(Raw(p), ns, band=TBAND_DIFF)
        if tk != float("inf"):
            ts.append(tk)
    if not ts:
        return {}
    return {"n": len(ts), "min_us": float(np.min(ts)),
            "mean_us": float(np.mean(ts)), "max_us": float(np.max(ts))}


def _v9(dirpath, key, ns):
    """"V9 真实 OPA388"——AC DM/CM、600 kΩ 高阻 AC/瞬态、噪声。"""
    o = {}
    pa, na = pin_names(range(ns))

    def _get(tag):
        p = os.path.join(dirpath, f"r5_{key}_{tag}.raw")
        return (Raw(p), p) if os.path.exists(p) else (None, None)

    rr, p = _get("v9a")
    if rr:
        dcg = db(interp_at(rr, 0.1, pa) - interp_at(rr, 0.1, na))
        o["A_dm"] = -(db(interp_at(rr, FMOD, pa) - interp_at(rr, FMOD, na)) - dcg)
        o["A_mclk"] = -(db(interp_at(rr, MCLK, pa) - interp_at(rr, MCLK, na)) - dcg)
        o["dG_16k"] = abs(db(interp_at(rr, 16e3, pa) - interp_at(rr, 16e3, na)) - dcg)
        o["raw_v9a"] = p
    rr, p = _get("v9b")
    if rr:
        o["A_cm"] = -(db(interp_at(rr, FMOD, pa)) -
                      db(interp_at(rr, 0.1, pa)))
        o["raw_v9b"] = p
    rr, p = _get("v9c")
    if rr:
        tk, _, _ = settle_us(rr, ns, band=TBAND_SPEC)
        tke, _, _ = settle_us(rr, ns, band=TBAND_DIFF)
        o["t_settle_us"] = tk
        o["t_settle_us_120uv"] = tke
        o["raw_v9c"] = p
    rr, p = _get("v9d")
    if rr:
        o["Vn_nv"] = noise_nv(rr)["D6_Vn_nv"]
        o["raw_v9d"] = p
    rr, p = _get("v9e")           # 600 kΩ 高阻 + AC
    if rr:
        dcg = db(interp_at(rr, 0.1, pa) - interp_at(rr, 0.1, na))
        o["A_dm_600k"] = -(db(interp_at(rr, FMOD, pa) - interp_at(rr, FMOD, na)) - dcg)
        o["dG_16k_600k"] = abs(db(interp_at(rr, 16e3, pa) - interp_at(rr, 16e3, na)) - dcg)
        o["raw_v9e"] = p
    rr, p = _get("v9f")           # 600 kΩ + 最坏角瞬态
    if rr:
        tk, _, _ = settle_us(rr, ns, band=TBAND_SPEC)
        tke, _, _ = settle_us(rr, ns, band=TBAND_DIFF)
        o["t_settle_600k_us"] = tk
        o["t_settle_600k_us_120uv"] = tke
        o["raw_v9f"] = p
    return o


# --------------------------------------------------------------- 汇总
def analyze_A(dirpath: str, mirror_dir: str | None = None, key="A") -> dict:
    with open(os.path.join(HERE, "r5_candidates.json"), encoding="utf-8") as fh:
        cand = json.load(fh)[key]
    ns = len(cand["stages"])

    def P(name):
        return os.path.join(dirpath, name)

    missing = [n for n in ("v1", "v2", "v3", "v4", "v7") if not os.path.exists(P(f"r5_{key}_{n}.raw"))]
    if missing:
        raise SystemExit(f"缺 .raw：{missing}（先跑 run_r5.py --cand {key} --dir {dirpath}）")

    res = {"candidate": key, "n_stages": ns, "stages": cand["stages"],
           "theory_pred": cand["pred"], "dir": dirpath, "raw": {}}

    # ---- AC 主项 ----
    r1 = Raw(P(f"r5_{key}_v1.raw"))
    res["V1"] = _v1_metrics(r1, ns)
    res["raw"]["V1"] = r1.path
    res.update({k: v for k, v in res["V1"].items()})

    r2 = Raw(P(f"r5_{key}_v2.raw"))
    res["V2"] = d2(r2, ns)
    res["raw"]["V2"] = r2.path
    res["D2_A_cm_db"] = res["V2"]["D2_A_cm_db"]

    r3 = Raw(P(f"r5_{key}_v3.raw"))
    res["V3"] = d8(r3, ns)
    res["raw"]["V3"] = r3.path
    res["D8_CMRR_db"] = res["V3"]["D8_CMRR_db"]

    # ---- 瞬态 ----
    r4 = Raw(P(f"r5_{key}_v4.raw"))
    t4, vf4, e4 = settle_us(r4, ns, band=TBAND_SPEC)
    t4e, _, _ = settle_us(r4, ns, band=TBAND_DIFF)
    res["V4"] = {"tset_us": t4, "tset_us_120uv": t4e,
                 "vfinal_v": vf4, "err_final_uv": e4 * 1e6}
    res["raw"]["V4"] = r4.path

    if os.path.exists(P(f"r5_{key}_v4b.raw")):
        r4b = Raw(P(f"r5_{key}_v4b.raw"))
        t4b, vf4b, e4b = settle_us(r4b, ns, band=TBAND_SPEC)
        t4be, _, _ = settle_us(r4b, ns, band=TBAND_DIFF)
        res["V4b"] = {"tset_us": t4b, "tset_us_120uv": t4be,
                      "err_final_uv": e4b * 1e6}
        res["raw"]["V4b"] = r4b.path

    # ---- D7 / V6 ----
    res["V5"] = _mc_sigma(dirpath, key, ns, "v5")
    if res["V5"]:
        res["D7_sigma_dG_db"] = res["V5"]["sigma_db"]
        res["raw"]["V5"] = os.path.join(dirpath, f"r5_{key}_v5mc01.raw")
    res["V6"] = _mc_settle(dirpath, key, ns)   # 沿用 120 µV 口径（与引擎对拍用）
    if res["V6"]:
        res["raw"]["V6"] = os.path.join(dirpath, f"r5_{key}_v6mc01.raw")

    # ---- 噪声 ----
    r7 = Raw(P(f"r5_{key}_v7.raw"))
    res["V7"] = noise_nv(r7)
    res["raw"]["V7"] = r7.path
    res["D6_Vn_nv"] = res["V7"]["D6_Vn_nv"]
    res["D6_Vn_lsb"] = res["V7"]["D6_Vn_lsb"]

    # ---- Kickback 三档 Ron ----
    kb = {}
    for ron in (1, 100, 1000):
        p = P(f"r5_{key}_v8_ron{ron:g}.raw")
        if os.path.exists(p):
            d = kickback(Raw(p), ns)
            d["cap_lock"] = _cap_lock(Raw(p), ns)
            kb[f"ron{ron:g}"] = d
            res["raw"][f"V8_ron{ron:g}"] = p
    if kb:
        res["V8"] = kb
        first = "ron1" if "ron1" in kb else list(kb)[0]
        res["D9"] = kb[first]["D9"]

    # ---- V9 ----
    v9 = _v9(dirpath, key, ns)
    if v9:
        res["V9"] = v9

    # ---- 温度角（§5.1：只报 D4/D7 趋势，不参与评分）----
    temps = {}
    for T in (-20, 85):
        p = P(f"r5_{key}_v1_t{T}.raw")
        if not os.path.exists(p):
            continue
        rr = Raw(p)
        pa, na = pin_names(range(ns))
        dcg = db(interp_at(rr, 0.1, pa) - interp_at(rr, 0.1, na))
        temps[f"{T}C"] = {
            "dG_16k_db": abs(db(interp_at(rr, 16e3, pa) - interp_at(rr, 16e3, na)) - dcg),
            "A_dm_fmod_db": -(db(interp_at(rr, FMOD, pa) - interp_at(rr, FMOD, na)) - dcg),
            "raw": p,
        }
    if temps:
        res["temperature"] = temps

    # ---- 十维实测（数值口径，正值 = 衰减量）----
    # D5 = §5.1「最坏角 + 测试须覆盖高源阻抗工况（样品 600 kΩ 端）」。
    # 候选里取**最大**（最悲观）：
    #   V4  0 Ω 源、R+1%/C+5%           —— 基线
    #   V4b 600 kΩ + 理想跟随器 + 8.5 pF 未自举输入电容（悲观上界）
    #   V9c 0 Ω 源 + 真实 OPA388        —— 跟随器非理想性
    #   V9f 600 kΩ + 真实 OPA388 + 最坏角 —— 规格要求的真实最坏角
    # 打分取 V4b/V9f 中较大者所代表的物理最坏工况；**同时**记录 V9f（真实模型）值。
    d5_candidates = {}
    if res.get("V4"):
        d5_candidates["V4_0ohm_corner"] = res["V4"]["tset_us"]
    if res.get("V4b"):
        d5_candidates["V4b_600k_ideal"] = res["V4b"]["tset_us"]
    if v9.get("t_settle_us") is not None:
        d5_candidates["V9c_0ohm_real"] = v9["t_settle_us"]
    if v9.get("t_settle_600k_us") is not None:
        d5_candidates["V9f_600k_real"] = v9["t_settle_600k_us"]
    d5 = max(d5_candidates.values()) if d5_candidates else None

    res["dims"] = {
        "D1": res["D1_A_dm_db"],
        "D2": res["D2_A_cm_db"],
        "D3": res["D3_A_mclk_db"],
        "D4": res["D4_dG_16k_db"],
        "D5": d5,
        "D6": res["D6_Vn_nv"],
        "D7": res.get("D7_sigma_dG_db"),
        "D8": res["D8_CMRR_db"],
        "D9": res.get("D9"),
        "D10": res["D10_dtau_us"],
    }
    res["D5_candidates_us"] = d5_candidates

    # ---- 交叉验证（rs=1 引擎镜像口径）----
    if mirror_dir and os.path.isdir(mirror_dir):
        res["xcheck"] = xcheck(cand, ns, mirror_dir)
    return res


def xcheck(cand, ns, mirror_dir) -> dict:
    """规格 §8：理论 vs LTspice（AC ≤0.5 dB、建立 ≤5%）。

    **必须同口径比较**：`opt_engine.ladder_matrices()` 源内阻硬编码 1 Ω，
    故镜像网表也取 Rs=1 Ω；拿规格 0 Ω 网表去比会凭空多出 ~1.08 dB 偏差。
    """
    from opt_round5 import predict, gain_db, settle_time_fast, SETTLE_BAND_V

    st = [tuple(map(float, s)) for s in cand["stages"]]
    th = predict(st)

    def rd(tag):
        p = os.path.join(mirror_dir, f"r5_{cand['grade']}_{tag}.raw")
        return Raw(p) if os.path.exists(p) else None

    rows, worst_ac = [], 0.0
    r1 = rd("v1")
    if r1:
        pa, na = pin_names(range(ns))
        dcg = db(interp_at(r1, 0.1, pa) - interp_at(r1, 0.1, na))
        for lab, f, thv in (("D1 A_dm@fMOD", FMOD, th["A_dm"]),
                            ("D3 A_mclk@MCLK", MCLK, th["A_mclk"]),
                            ("D4 dG@16k", 16e3, th["dG_16k"])):
            lt = db(interp_at(r1, f, pa) - interp_at(r1, f, na)) - dcg
            lt = -lt if lab != "D4 dG@16k" else abs(lt)
            d = abs(lt - thv)
            worst_ac = max(worst_ac, d)
            rows.append({"item": lab, "theory": thv, "ltspice": lt,
                         "abs_diff": d, "pass": d <= 0.5})
    r2 = rd("v2")
    if r2:
        pa, _ = pin_names(range(ns))
        lt = -(db(interp_at(r2, FMOD, pa)) - db(interp_at(r2, 0.1, pa)))
        d = abs(lt - th["A_cm"])
        worst_ac = max(worst_ac, d)
        rows.append({"item": "D2 A_cm@fMOD", "theory": th["A_cm"], "ltspice": lt,
                     "abs_diff": d, "pass": d <= 0.5})

    r4 = rd("v4")
    settle = None
    if r4:
        lt_us, _, _ = settle_us(r4, ns, band=TBAND_DIFF)
        th_us = settle_time_fast(st, "dm", SETTLE_BAND_V,
                                 tol_r=0.01, tol_c=0.05) * 1e6
        rel = abs(lt_us - th_us) / th_us if th_us > 0 else float("inf")
        settle = {"theory_us": th_us, "ltspice_us": lt_us,
                  "rel_diff": rel, "pass": rel <= 0.05}

    # D8 CMRR 也要交叉验证（同为 AC 量，判据 ≤0.5 dB）
    r3 = rd("v3")
    if r3:
        pa, na = pin_names(range(ns))
        f = r3.f
        m = (f >= 10) & (f <= 16e3)
        cm = np.abs(np.array(r3.col(pa))[m])
        dm = np.abs(np.array(r3.col(pa))[m] - np.array(r3.col(na))[m])
        lt_cmrr = float(np.min(20 * np.log10(cm / dm)))
        from opt_round5 import cmrr_passband_db
        th_cmrr = cmrr_passband_db(st)
        d = abs(lt_cmrr - th_cmrr)
        worst_ac = max(worst_ac, d)
        rows.append({"item": "D8 CMRR@通带", "theory": th_cmrr, "ltspice": lt_cmrr,
                     "abs_diff": d, "pass": d <= 0.5})

    r7 = rd("v7")
    noise = None
    if r7:
        lt_nv = noise_nv(r7)["D6_Vn_nv"]
        th_nv = th["V_n_lsb"] * LSB_V * 1e9
        rel = abs(lt_nv - th_nv) / th_nv if th_nv > 0 else float("inf")
        noise = {"theory_nv": th_nv, "ltspice_nv": lt_nv,
                 "rel_diff": rel, "pass": rel <= 0.05}

    ok = worst_ac <= 0.5 and (settle is None or settle["pass"])
    return {"ac_rows": rows, "worst_ac_diff_db": worst_ac,
            "settle": settle, "noise": noise,
            "pass": bool(ok), "rs_mirror_ohm": 1.0,
            "note": "理论引擎 rs 硬编码 1 Ω；镜像网表同取 1 Ω，规格 0 Ω 口径另见 dims"}


# --------------------------------------------------------------- 评分
def _lerp(x, full, bare, higher=False):
    if higher:
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


def score(dims: dict) -> dict:
    """规格 §5.1「归一化方式」逐条实现（**不是**统一线性插值）。

    规格原文：
      D1 min(A_dm/120,1)      D2 min(A_cm/100,1)      D3 min(A_mclk/150,1)
      D4 ΔG≤0.05→1；0.05<ΔG≤0.5 线性 1−(ΔG−0.05)/0.45
      D5 min(500/t_s,1)       D6 min(0.3/V_n[LSB],1)  D7 线性 1−(σ−0.01)/0.04
      D8 min(CMRR/100,1)      D9 二值                D10 线性 1−(Δτ−1)/4
    及格线（越线淘汰）另由 ``pass_flags()`` 单列 —— **不是**归一化的一部分。
    """
    def _lin(x, full, bare):
        if x <= full:
            return 1.0
        if x > bare:
            return 0.0
        return 1.0 - (x - full) / (bare - full)

    out = {}
    for k, v in dims.items():
        if v is None:
            out[k] = None
        elif k == "D9":
            out[k] = float(v)
        elif k in ("D1", "D2", "D3", "D8"):
            out[k] = min(float(v) / {"D1": 120.0, "D2": 100.0,
                                     "D3": 150.0, "D8": 100.0}[k], 1.0)
        elif k in ("D5", "D6"):
            # 双曲型 min(满分阈值/实测, 1)；实测为 0 时封 1。
            # **单位纪律**：dims["D6"] 是 nVrms（本报告口径），规格阈值 0.3 是 **LSB**，
            # 比较前必须换算：1 LSB = 290.98 nV。D5 的 dims 本身即 µs，与 500 µs 同单位。
            if k == "D6":
                v_lsb = float(v) / (LSB_V * 1e9)
                out[k] = 1.0 if v_lsb <= 0.3 else min(0.3 / v_lsb, 1.0)
            else:
                out[k] = 1.0 if v <= 500.0 else min(500.0 / float(v), 1.0)
        elif k == "D4":
            out[k] = _lin(float(v), 0.05, 0.5)
        elif k == "D7":
            out[k] = _lin(float(v), 0.01, 0.05)
        elif k == "D10":
            out[k] = _lin(float(v), 1.0, 5.0)
    return out


def pass_flags(dims: dict) -> dict:
    """规格 §5.1「及格线（越线淘汰）」逐维判定（与归一化分数无关）。"""
    d = dims
    return {
        "D1": d["D1"] >= 80.0,
        "D2": d["D2"] >= 60.0,
        "D3": d["D3"] >= 100.0,
        "D4": d["D4"] <= 0.5,
        "D5": d["D5"] <= 900.0,
        "D6": d["D6"] <= 1.0 * (LSB_V * 1e9),      # D6 比较基准是 LSB, dims 存 nV
        "D7": d["D7"] is not None and d["D7"] <= 0.05,
        "D8": d["D8"] >= 80.0,
        "D9": d["D9"] == 1.0,
        "D10": d["D10"] <= 5.0,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.path.join(HERE, "r5_work", "rs0"))
    ap.add_argument("--mirror", default=os.path.join(HERE, "r5_work", "rs1"))
    ap.add_argument("--json", default=os.path.join(HERE, "r5_results_A.json"))
    args = ap.parse_args(argv)

    res = analyze_A(args.dir, args.mirror)
    res["scores"] = score(res["dims"])
    res["pass"] = pass_flags(res["dims"])
    res["min_score"] = min(v for v in res["scores"].values() if v is not None)
    print("=== 方案 A 十维实测（规格 §5.1）===")
    for k in ("D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D10"):
        v = res["dims"].get(k)
        s = res["scores"].get(k)
        p = res["pass"].get(k)
        print(f"  {k}: {v if v is None else round(v, 4)}  → 分 "
              f"{None if s is None else round(s, 3)}  {'过线' if p else '×淘汰'}")
    print(f"  min(D1..D10) = {res['min_score']:.3f}")
    if "xcheck" in res:
        x = res["xcheck"]
        print(f"\n=== 交叉验证（rs=1 镜像）worst AC {x['worst_ac_diff_db']:.3f} dB, pass={x['pass']} ===")
        for r in x["ac_rows"]:
            print(f"  {r['item']:18s} 理论 {r['theory']:8.3f} | LT {r['ltspice']:8.3f} "
                  f"| Δ {r['abs_diff']:.3f} {'✓' if r['pass'] else '✗'}")
        if x.get("settle"):
            s = x["settle"]
            print(f"  建立        理论 {s['theory_us']:8.1f} | LT {s['ltspice_us']:8.1f} "
                  f"| 相对 {s['rel_diff']*100:.2f}% {'✓' if s['pass'] else '✗'}")
        if x.get("noise"):
            n = x["noise"]
            print(f"  噪声        理论 {n['theory_nv']:8.1f} | LT {n['ltspice_nv']:8.1f} "
                  f"| 相对 {n['rel_diff']*100:.2f}% {'✓' if n['pass'] else '✗'}")
    with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=2)
    print("\n→", args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
