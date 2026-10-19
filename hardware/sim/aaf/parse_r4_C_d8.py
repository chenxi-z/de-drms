#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""parse_r4_C_d8.py — 第 4 轮补测：方案 C 的 D8（真实 OPA388 模型口径）

数据源：r5_work/r4_C_d8/r4_C_d8_*.raw（gen_netlists_r4_C_d8.py 生成、LTspice -b -ascii 批跑）

* 主口径：真实 OPA388（v9b_p001/p005/p010），与方案 B 第 3 轮 D8 网表同形
* 对照：同向失配 s001/s005/s010、0 Ω 理想源配对 1%（v3p010）、标称 nom
* CMRR 定义同时给两种：
    - cm_pin  = |V(pa)|            （方案 B 第 3 轮 parse_r3_B.ac_cm 的口径）
    - cm_half = |(V(pa)+V(na))/2|  （方案 C 第 3 轮 parse_r5_r3.cmrr_passband 的口径；
                                     也与 r5_score_v4.cmrr_rc_paired 的理论一致）
  两者在共模激励下只差 O(失配²)，但为可追溯两套都报；**D8 记分取 cm_pin**，
  与 B 案第 3 轮同口径。

用法：python parse_r4_C_d8.py
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from parse_r5 import Raw  # noqa: E402
import opt_round5 as O5    # noqa: E402
import r5_score_v4 as S4   # noqa: E402

D = os.path.join(HERE, "r5_work", "r4_C_d8")
CAND = os.path.join(HERE, "r5_candidates_r2.json")
NS = 4


def _cmrr(tag, f_lo=10.0, f_hi=16e3):
    p = os.path.join(D, f"r4_C_d8_{tag}.raw")
    r = Raw(p)
    pa, na = f"V(pa{NS})", f"V(na{NS})"
    f = np.asarray(r.f, float)
    a = np.asarray(r.col(pa), complex)
    b = np.asarray(r.col(na), complex)
    m = (f >= f_lo) & (f <= f_hi)
    out = {}
    for nm, cm in (("cm_pin", np.abs(a[m])), ("cm_half", np.abs((a[m] + b[m]) / 2.0))):
        dm = np.abs(a[m] - b[m])
        with np.errstate(divide="ignore"):
            v = 20 * np.log10(cm / np.maximum(dm, 1e-300))
        v = np.clip(np.nan_to_num(v, nan=-300.0, posinf=300.0, neginf=-300.0), -300.0, 300.0)
        k = int(np.argmin(v))
        out[nm] = {"CMRR_db": float(v[k]), "worst_f_hz": float(f[m][k]),
                   "cmrr_10Hz_db": float(v[0]), "cmrr_16k_db": float(v[-1])}
    out["n_pts"] = int(m.sum())
    out["g_cm_dc_db"] = float(20 * math.log10(abs(r.col(pa)[0])))
    return out


def _theory(m, mode):
    st = [tuple(map(float, s)) for s in json.load(open(CAND, encoding="utf-8"))["C"]["stages"]]
    if mode == "paired":
        sb = [(r * (1 + m), cg * (1 - m), cd * (1 - m)) for r, cg, cd in st]
    else:
        sb = [(r * (1 + m), cg * (1 + m), cd * (1 + m)) for r, cg, cd in st]
    f = np.logspace(1.0, math.log10(16e3), 60)
    cm, dm = O5._two_line_cm_dm(st, sb, f, "opa388")
    v = np.clip(np.nan_to_num(20 * np.log10(np.abs(cm) / np.maximum(np.abs(dm), 1e-300)),
                              nan=-300.0), -300.0, 300.0)
    k = int(np.argmin(v))
    return {"CMRR_db": float(v[k]), "worst_f_hz": float(f[k]), "n_pts": len(f)}


def _theory_ideal(m):
    st = [tuple(map(float, s)) for s in json.load(open(CAND, encoding="utf-8"))["C"]["stages"]]
    sb = [(r * (1 + m), cg * (1 - m), cd * (1 - m)) for r, cg, cd in st]
    f = np.logspace(1.0, math.log10(16e3), 60)
    cm, dm = O5._two_line_cm_dm(st, sb, f, "ideal")
    v = 20 * np.log10(np.abs(cm) / np.maximum(np.abs(dm), 1e-300))
    return float(np.min(v))


def main():
    res = {"scheme": "C", "round": 4, "dim_fixed": "D8",
           "dir": D, "netlist_generator": "gen_netlists_r4_C_d8.py",
           "netlist_form": "同方案 B 第 3 轮 v9b_p*/v9b_s*：.include OPAx388.LIB + Xfa/Xfb，"
                           "Vp/Vn DC 2 V AC 1，.ac dec 400 1 40k",
           "note": "r3 复核发现 C 案 D8 网表（gen_v3）从未实例化 OPA388，"
                   "故 94.66 dB 是 0 Ω 理想源值；本轮用真实 OPA388 重测"}

    paired, same = {}, {}
    for m, tag in ((0.001, "p001"), (0.005, "p005"), (0.01, "p010")):
        key = f"{m*100:g}%"
        paired[key] = _cmrr(f"v9b_{tag}")
        paired[key]["theory_opa388"] = _theory(m, "paired")
        same[f"{m*100:g}%"] = _cmrr(f"v9b_s{tag[-3:]}")
        same[f"{m*100:g}%"]["theory_opa388"] = _theory(m, "same")
    res["paired_real"] = paired
    res["same_direction_real"] = same
    res["ideal_control_1pct"] = {"ltspice": _cmrr("v3p010"), "theory_ideal": _theory_ideal(0.01)}
    res["nominal_real"] = _cmrr("v9b_nom")

    # D8 = 1% 配对档、真实模型、cm_pin 口径（与 B 案 r3 同口径）
    d8 = paired["1%"]["cm_pin"]["CMRR_db"]
    th = paired["1%"]["theory_opa388"]["CMRR_db"]
    res["D8_value"] = {"D8_db": d8, "m": "1%", "mode": "paired", "source_model": "opa388",
                       "cmrr_def": "|V(pa)| / |V(pa)-V(na)|，10 Hz–16 kHz 最差",
                       "theory_db": th, "abs_diff_vs_theory": d8 - th}
    # 与 r3 的 0 Ω 值对照
    r3 = json.load(open(os.path.join(HERE, "r5_results_r3_C.json"), encoding="utf-8"))
    r3_d8 = r3["D8_detail"]["paired"]["1%"]["CMRR_db"]
    res["comparison_r3"] = {
        "r3_D8_1pct_db": r3_d8,
        "r3_netlist_had_opa388": bool(
            "OPAx388" in open(os.path.join(HERE, "r5_work", "r3_C",
                                           "r5_C_r3_v3p010.net"), encoding="ascii").read()),
        "r3_theory_same_direction_db": r3["theory_engine_pred"]["CMRR_pb_db"],
        "r4_D8_1pct_db": d8,
        "delta_db": d8 - r3_d8,
        "r4_ideal_source_control_db": res["ideal_control_1pct"]["ltspice"]["cm_pin"]["CMRR_db"],
    }
    res["xcheck"] = {
        "item": "D8 CMRR 1% paired (real OPA388)",
        "theory_db": th, "ltspice_db": d8, "abs_diff": d8 - th,
        "criterion": "≤0.5 dB", "pass": bool(abs(d8 - th) <= 0.5)}
    # 各档 xcheck
    res["xcheck_all"] = []
    for mode, v in (("paired", paired), ("same", same)):
        for k, d in v.items():
            dv = d["cm_pin"]["CMRR_db"] - d["theory_opa388"]["CMRR_db"]
            res["xcheck_all"].append({"m": k, "mode": mode,
                                      "theory_db": d["theory_opa388"]["CMRR_db"],
                                      "ltspice_db": d["cm_pin"]["CMRR_db"],
                                      "abs_diff": dv, "pass_0p5": bool(abs(dv) <= 0.5)})
    res["dims"] = {"D8": d8}
    return res


if __name__ == "__main__":
    r = main()
    print(json.dumps(r, indent=1, ensure_ascii=False))
