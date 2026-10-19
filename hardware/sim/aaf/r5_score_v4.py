# -*- coding: utf-8 -*-
"""r5_score_v4.py — 按规格 v4 口径复评 r5_candidates_r2.json 的三案参数。

差异点（相对 opt_round5.dim_scores 的 v3 口径）：
  * D6 拆为 D6a（无源网络噪声增量 %, 硬指标，满分≤10%、淘汰>30%）+ D6b（总积分噪声，仅报告）
  * D8 考核条件改为「两线 R·C 乘积异向配对」：R×(1+m) 配 C×(1−m)，1% 单体失配
  * 总分 = min(D1,D2,D3,D4,D5,D6a,D7,D8,D9,D10)
  * C9 peaking ≤6 dB 硬约束复核

用法：cd hardware/sim/aaf && python r5_score_v4.py [--json out.json]
"""
from __future__ import annotations

import argparse
import json
import math
import os

import numpy as np

import opt_round5 as o5

HERE = os.path.dirname(os.path.abspath(__file__))
TH = {
    "D1": (120.0, 80.0), "D2": (100.0, 60.0), "D3": (150.0, 100.0),
    "D4": (0.05, 0.50), "D5": (500.0, 900.0),
    "D6a": (10.0, 30.0),          # % 增量；满分 ≤10%，淘汰 >30%
    "D7": (0.01, 0.05), "D8": (100.0, 80.0), "D10": (1.0, 5.0),
}
D8_M = 0.01


def ratio_score(x, full):
    if not np.isfinite(x) or x <= 0:
        return 0.0
    return float(min(x / full, 1.0))


def inv_score(x, full):
    if not np.isfinite(x) or x <= 0:
        return 0.0
    return float(min(full / x, 1.0))


def lerp_score(x, full, bare):
    if x <= full:
        return 1.0
    if x > bare:
        return 0.0
    return float(1.0 - (x - full) / (bare - full))


def cmrr_rc_paired(stages, m=D8_M, f_lo=10.0, f_hi=16e3, npts=60):
    """规格 v4 D8：两线 R·C 乘积异向配对。

    Line B = R×(1+m)，C_gnd 与 C_diff 均 ×(1−m)；乘积 R·C 回到 ≈1，时间常数匹配。
    返回 10 Hz–16 kHz 最差 CMRR（dB）。
    """
    f = np.logspace(math.log10(f_lo), math.log10(f_hi), npts)
    b = [(r * (1 + m), cg * (1 - m), cd * (1 - m)) for r, cg, cd in stages]
    cm, dm = o5._two_line_cm_dm([tuple(map(float, s)) for s in stages], b, f)
    return float(np.min(20 * np.log10(np.abs(cm) / np.maximum(np.abs(dm), 1e-300))))


def cmrr_rc_paired_exact_inv(stages, m=D8_M, f_lo=10.0, f_hi=16e3, npts=60):
    """对照口径：C×1/(1+m)（严格让 R·C 乘积精确等于原值）。"""
    f = np.logspace(math.log10(f_lo), math.log10(f_hi), npts)
    b = [(r * (1 + m), cg / (1 + m), cd / (1 + m)) for r, cg, cd in stages]
    cm, dm = o5._two_line_cm_dm([tuple(map(float, s)) for s in stages], b, f)
    return float(np.min(20 * np.log10(np.abs(cm) / np.maximum(np.abs(dm), 1e-300))))


def score_v4(stages, verbose=False):
    st = [tuple(map(float, s)) for s in stages]
    p = o5.predict(st)
    v_tot = p["V_n_lsb"]
    v_fol = p["V_n_lsb_follower"]
    dv_pct = 100.0 * (v_tot - v_fol) / v_fol if v_fol > 0 else float("inf")
    d6a = inv_score(dv_pct, TH["D6a"][0]) if dv_pct > 0 else 1.0
    d6b = v_tot                                  # LSB，仅报告
    d8 = cmrr_rc_paired(st)
    d8_inv = cmrr_rc_paired_exact_inv(st)
    t_us = o5.d5_worst_us(p)
    dtau_us = p["group_delay_flat_s"] * 1e6
    dims = {
        "D1": ratio_score(p["A_dm"], TH["D1"][0]),
        "D2": ratio_score(p["A_cm"], TH["D2"][0]),
        "D3": ratio_score(p["A_mclk"], TH["D3"][0]),
        "D4": lerp_score(p["dG_16k"], *TH["D4"]),
        "D5": inv_score(t_us, TH["D5"][0]),
        "D6a": d6a,
        "D7": lerp_score(p["sigma_dG_db"], *TH["D7"]),
        "D8": ratio_score(d8, TH["D8"][0]),
        "D9": 1.0 if p["kickback_ok"] else 0.0,
        "D10": lerp_score(dtau_us, *TH["D10"]),
    }
    pf = {
        "D1": p["A_dm"] >= TH["D1"][1], "D2": p["A_cm"] >= TH["D2"][1],
        "D3": p["A_mclk"] >= TH["D3"][1], "D4": p["dG_16k"] <= TH["D4"][1],
        "D5": t_us <= TH["D5"][1], "D6a": dv_pct <= TH["D6a"][1],
        "D7": p["sigma_dG_db"] <= TH["D7"][1], "D8": d8 >= TH["D8"][1],
        "D9": p["kickback_ok"], "D10": dtau_us <= TH["D10"][1],
    }
    hard = o5.hard_checks(p)
    hard["peaking_c9"] = p["peaking_db"] <= 6.0     # 规格 v4 §5.2 C9
    out = {
        "stages": [list(s) for s in st],
        "dims": dims, "pass": pf,
        "min_score": min(dims.values()),
        "failing": [k for k, v in pf.items() if not v],
        "hard": hard, "hard_ok": all(hard.values()),
        "pred": p,
        "d6a_pct": dv_pct, "d6b_lsb": d6b,
        "D6b_brickwall_lsb": o5.EN_FOLL_DIFF * math.sqrt(16e3) / o5.LSB_V,
        "cmrr_rc_paired_db": d8, "cmrr_rc_paired_inv_db": d8_inv,
        "cmrr_same_dir_db": p["CMRR_pb_db"],
        "peaking_db": p["peaking_db"], "peaking_f_hz": p["peaking_f_hz"],
    }
    if verbose:
        print(f"  fc={p['f_c_hz']/1e3:.1f}k  D1={p['A_dm']:.2f}  D2={p['A_cm']:.2f} "
              f"D3={p['A_mclk']:.2f}  dG16k={p['dG_16k']:.4f}  t5={t_us:.0f}us  "
              f"d6a={dv_pct:.3f}%  d6b={d6b:.2f}LSB  sD7={p['sigma_dG_db']:.4f}  "
              f"D8={d8:.2f}dB  dtau={dtau_us:.2f}us  pk={p['peaking_db']:.2f}dB@{p['peaking_f_hz']/1e3:.0f}k")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default="")
    args = ap.parse_args(argv)
    path = os.path.join(HERE, "r5_candidates_r2.json")
    with open(path, encoding="utf-8") as fh:
        cands = json.load(fh)
    out = {}
    for g in ("A", "B", "C"):
        st = cands[g]["stages"]
        print(f"=== 方案 {g}（{cands[g]['n_stages']} 级）")
        r = score_v4(st, verbose=True)
        print("   dims: " + "  ".join(f"{k}={v:.3f}" for k, v in r["dims"].items()))
        print(f"   min={r['min_score']:.4f}  未及格={r['failing']}  hard_ok={r['hard_ok']}")
        print(f"   CMRR 同向={r['cmrr_same_dir_db']:.1f}dB  R·C配对={r['cmrr_rc_paired_db']:.1f}dB "
              f"(严格倒数口径 {r['cmrr_rc_paired_inv_db']:.1f}dB)")
        print(f"   D6a={r['d6a_pct']:.3f}%  D6b={r['d6b_lsb']:.2f}LSB "
              f"(砖墙 {r['D6b_brickwall_lsb']:.2f})  C9 peaking={r['peaking_db']:.2f}dB")
        out[g] = r
    if args.json:
        with open(os.path.join(HERE, args.json), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(out, fh, ensure_ascii=False, indent=2, default=float)
        print("wrote", args.json)
    return out


if __name__ == "__main__":
    main()
