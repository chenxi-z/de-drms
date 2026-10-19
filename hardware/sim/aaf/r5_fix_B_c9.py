# -*- coding: utf-8 -*-
"""r5_fix_B_c9.py — Round 5 第 4 轮：B 案 C9 修复（首级 R 2.74→6.8 Ω）的理论验证与平衡点搜索

背景
----
第 3 轮实测（`r5_report_r3.md` §4.4 / `r5_d5_coverage_gap_r3.json`）：
B 案首级 R1 由 2.74 Ω 提到 6.8 Ω，可把**跟随器输出节点** peaking 从 10.66 dB 压到 4.43 dB
（<6 dB，过 C9）。代价：C 值不动时 fc 由 79.9 kHz 降到 58.2 kHz，D4 平坦度从 0.188 恶化到 0.322 dB。

本脚本用 `opt_round5.py` 引擎（真实 OPA388 源模型 = Zout 复频查表 + G(f)）：
  1. 把引擎的十维预测折成**规格 v4 口径**（D6a 增量、D8 用 R·C 乘积配对 1%）
  2. 加 C9（跟随器节点 peaking ≤6 dB）作为硬门槛
  3. 在 R1=6.8 Ω 附近扫 R/C，找「C9 过 + 十维全过 + min 最大」的平衡点
  4. 取整到 E96（R）/E12（C），输出 r5_candidates_final_B.json

引擎与 LTspice 在**跟随器节点**的吻合度（C9 口径校验）：
    R1=2.74 → 引擎 10.65 dB / LTspice 10.66 dB
    R1=6.8  → 引擎  4.41 dB / LTspice  4.43 dB

用法：
    python r5_fix_B_c9.py                     # 搜索 + 打印
    python r5_fix_B_c9.py --json r5_candidates_final_B.json
"""
from __future__ import annotations

import argparse
import json
import math
import os

import numpy as np

import opt_round5 as E

HERE = os.path.dirname(os.path.abspath(__file__))

TH = dict(E.TH)
TH["D6a"] = (10.0, 30.0)          # §5.1 D6a：≤10% 满分 / >30% 淘汰（单位 %）
TH["D8"] = (100.0, 80.0)          # §5.1 D8：R·C 乘积配对口径

C9_LIMIT_DB = 6.0


# ------------------------------------------------------------- C9：跟随器节点
def follower_node_peak(stages, f_lo=1.0, f_hi=3e6, npts=4000):
    """跟随器输出节点（阶梯输入端 = 引擎 MNA 的节点 0）相对 DC 的增益峰值（dB）。

    C9 的**物理考核节点**（r5_report_r3 §4.2：谐振发生在被驱动节点，
    引脚处被末级 RC 压平 10–14 dB）。
    """
    f = np.logspace(math.log10(f_lo), math.log10(f_hi), npts)
    G, Cd = E._ladder_GC(stages, "dm")
    w = 2.0 * math.pi * f
    Zs = E._source_z(f)
    Gs = E._source_gain(f)
    A = G[None, :, :] + 1j * w[:, None, None] * np.diag(Cd)[None, :, :]
    A[:, 0, 0] += 1.0 / Zs
    rhs = np.zeros((len(f), G.shape[0]), dtype=complex)
    rhs[:, 0] = Gs / Zs
    v = np.linalg.solve(A, rhs[:, :, None])[:, :, 0]

    f0 = np.array([0.1])
    A0 = G + 1j * 2.0 * math.pi * 0.1 * np.diag(Cd)
    A0[0, 0] += 1.0 / E._source_z(f0)[0]
    rhs0 = np.zeros(G.shape[0], dtype=complex)
    rhs0[0] = E._source_gain(f0)[0] / E._source_z(f0)[0]
    v00 = np.linalg.solve(A0, rhs0)[0]
    g = 20.0 * np.log10(np.abs(v[:, 0]) / abs(v00))
    i = int(np.argmax(g))
    return float(g[i]), float(f[i])


# ------------------------------------------------------------- D8：配对口径
def _line(stages, kr, kc):
    return [(float(r) * kr, float(c) * kc, float(cd) * kc) for r, c, cd in stages]


def cmrr_paired(stages, m=0.01, f_lo=10.0, f_hi=16e3, npts=60):
    """规格 v4 §5.1a：两线按 R·C 乘积**异向**配对（B 线 R×(1+m)、C×(1−m)），10 Hz~16 kHz 最差。"""
    f = np.logspace(math.log10(f_lo), math.log10(f_hi), npts)
    cm, dm = E._two_line_cm_dm(stages, _line(stages, 1.0 + m, 1.0 - m), f)
    return float(np.min(20.0 * np.log10(np.abs(cm) / np.maximum(np.abs(dm), 1e-300))))


# ------------------------------------------------------------- v4 十维评分
def _ratio(x, full):
    return 0.0 if (not np.isfinite(x) or x <= 0) else float(min(x / full, 1.0))


def _inv(x, full):
    return 0.0 if (not np.isfinite(x) or x <= 0) else float(min(full / x, 1.0))


def _lin(x, full, bare):
    if x <= full:
        return 1.0
    if x >= bare:
        return 0.0
    return 1.0 - (x - full) / (bare - full)


def score_v4(stages, with_cmrr=True):
    """规格 v4 §5.1 十维（D6→D6a、D8→R·C 配对 1%）+ C9 硬门槛。"""
    p = E.predict(stages)
    d6a_pct = 100.0 * (p["V_n_lsb"] - p["V_n_lsb_follower"]) / p["V_n_lsb_follower"]
    cmrr_pair = cmrr_paired(stages, 0.01) if with_cmrr else float("nan")
    t_us = E.d5_worst_us(p)
    pkb, pkhz = follower_node_peak(stages)
    raw = {
        "D1": p["A_dm"], "D2": p["A_cm"], "D3": p["A_mclk"],
        "D4": p["dG_16k"], "D5": t_us, "D6a": d6a_pct,
        "D7": p["sigma_dG_db"], "D8": cmrr_pair, "D9": 1.0 if p["kickback_ok"] else 0.0,
        "D10": p["group_delay_flat_s"] * 1e6,
    }
    s = {
        "D1": _ratio(raw["D1"], 120.0), "D2": _ratio(raw["D2"], 100.0),
        "D3": _ratio(raw["D3"], 150.0), "D4": _lin(raw["D4"], 0.05, 0.50),
        "D5": _inv(raw["D5"], 500.0), "D6a": _inv(raw["D6a"], 10.0),
        "D7": _lin(raw["D7"], 0.01, 0.05), "D8": _ratio(raw["D8"], 100.0),
        "D9": raw["D9"], "D10": _lin(raw["D10"], 1.0, 5.0),
    }
    pf = {
        "D1": raw["D1"] >= 80.0, "D2": raw["D2"] >= 60.0, "D3": raw["D3"] >= 100.0,
        "D4": raw["D4"] <= 0.50, "D5": raw["D5"] <= 900.0, "D6a": raw["D6a"] <= 30.0,
        "D7": raw["D7"] <= 0.05, "D8": raw["D8"] >= 80.0, "D9": bool(raw["D9"]),
        "D10": raw["D10"] <= 5.0,
    }
    hard = E.hard_checks(p)
    hard["C9"] = pkb <= C9_LIMIT_DB
    if not with_cmrr:                 # D8 未算时不参与「淘汰」判定（只作筛选加速）
        pf.pop("D8", None)
        s.pop("D8", None)
    return {
        "stages": [tuple(map(float, s_)) for s_ in stages],
        "pred": p, "raw": raw, "scores": s, "pass": pf,
        "min_score": float(min(s.values())),
        "failing": [k for k, v in pf.items() if not v],
        "c9_peak_db": pkb, "c9_peak_f_hz": pkhz, "c9_ok": pkb <= C9_LIMIT_DB,
        "hard": hard, "hard_ok": all(hard.values()),
        "fc_khz": p["f_c_hz"] / 1e3,
    }


def fmt(rec, tag=""):
    r, s = rec["raw"], rec["scores"]
    bad = [k for k, v in rec["hard"].items() if not v]
    return ("%s fc=%6.1fk pk=%5.2f D1=%6.2f(%.3f) D2=%5.1f D3=%6.1f D4=%.4f(%.3f) "
            "D5=%5.1f D6a=%.2f%% D7=%.5f D8=%5.1f D10=%.3f | min=%.4f%s%s"
            % (tag, rec["fc_khz"], rec["c9_peak_db"], r["D1"], s["D1"], r["D2"], r["D3"],
               r["D4"], s["D4"], r["D5"], r["D6a"], r["D7"], r["D8"], r["D10"],
               rec["min_score"],
               "" if not bad else "  HARD-FAIL:%s" % bad,
               "" if not rec["failing"] else "  FAIL:%s" % rec["failing"]))


# ------------------------------------------------------------- 档位表
E96_R = [3.3, 3.6, 3.9, 4.22, 4.32, 4.42, 4.53, 4.64, 4.75, 4.87, 4.99, 5.11, 5.23,
         5.36, 5.49, 5.62, 5.76, 5.9, 6.04, 6.19, 6.34, 6.49, 6.65, 6.81, 6.98, 7.15,
         7.32, 7.5, 7.68, 7.87, 8.06, 8.25, 8.45, 8.66, 8.87, 9.09, 9.31, 9.53,
         9.76, 10.0, 10.2, 10.5, 10.7, 11.0, 11.3, 11.5, 11.8, 12.1, 12.4, 12.7, 13.0,
         13.3, 13.7, 14.0, 14.3, 14.7, 15.0, 15.4, 15.8, 16.2, 16.5, 16.9, 17.4, 17.8,
         18.2, 18.7, 19.1, 19.6, 20.0, 20.5, 21.0, 21.5, 22.1, 22.6, 23.2, 23.7, 24.3,
         24.9, 25.5, 26.1, 26.7, 27.4, 28.0, 28.7, 29.4, 30.1]
E12_C = [1.0, 1.2, 1.5, 1.8, 2.2, 2.7, 3.3, 3.9, 4.7, 5.6, 6.8, 8.2]


def c_table(mant, lo=1e-11, hi=100e-9):
    vals = set()
    for d in range(-12, -7):
        for m in mant:
            v = m * 10.0 ** d
            if lo * 0.999 <= v <= hi * 1.001:
                vals.add(round(v, 18))
    return sorted(vals)


C_E12 = c_table(E12_C)
# 搜索用子集：fc∈[50,80] kHz 且 ΣR≈25–40 Ω ⇒ 单级 C 必在 10–100 nF 量级
# （10 pF–6.8 nF 的档位在 fc 处被 fc_dm 直接筛掉，纳入只会白跑）
C_SEARCH = [v for v in C_E12 if 10e-9 <= v <= 100e-9]

B0 = [(2.74, 68e-9, 0.0), (6.04, 56e-9, 0.0), (13.7, 56e-9, 12e-9)]
B68 = [(6.8, 68e-9, 0.0), (6.04, 56e-9, 0.0), (13.7, 56e-9, 12e-9)]


def search(r1_list, c1_list, c2_list, c3_list, r2=6.04, r3=13.7, cd=12e-9,
           with_cmrr=False, monotone=True):
    """单调阶梯（C1≥C2≥C3，与原 B 案拓扑同形）全组合搜索。

    只在 fc∈[50,80] kHz 内做完整评分；fc 用廉价 MNA（2 ms），score_v4 用完整预测（30 ms）。
    """
    rows = []
    for r1 in r1_list:
        for c1 in c1_list:
            for c2 in c2_list:
                if monotone and c2 > c1:
                    continue
                for c3 in c3_list:
                    if monotone and c3 > c2:
                        continue
                    st = [(r1, c1, 0.0), (r2, c2, 0.0), (r3, c3, cd)]
                    fc = E.fc_dm(st)
                    if not (50e3 <= fc <= 80e3):
                        continue
                    rec = score_v4(st, with_cmrr=with_cmrr)
                    if not rec["c9_ok"] or not rec["hard_ok"] or rec["failing"]:
                        continue
                    rows.append(rec)
    rows.sort(key=lambda z: -z["min_score"])
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default="")
    ap.add_argument("--top", type=int, default=15)
    args = ap.parse_args(argv)

    print("=" * 118)
    print("基准对照（引擎口径 = 真实 OPA388 源模型；v4 评分 + C9 跟随器节点）")
    print("=" * 118)
    for nm, st in (("B 标称 R1=2.74", B0), ("B R1=6.8（C 不动）", B68)):
        print("  " + fmt(score_v4(st), nm))

    print("\n" + "=" * 118)
    print("① R1 扫描（R2/R3/C 全部保持原值）—— C9 与 D4/D1 的此消彼长")
    print("=" * 118)
    for r1 in (2.74, 3.9, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 10.0):
        st = [(r1, 68e-9, 0.0)] + B0[1:]
        print("  " + fmt(score_v4(st, with_cmrr=False), "R1=%5.2f" % r1))

    print("\n" + "=" * 118)
    print("② 粗搜：R1∈E96 [5.62,7.5] × C∈E12，fc∈[50,80] kHz，C9 过 + 十维全过")
    print("=" * 118)
    r1s = [5.62, 5.9, 6.19, 6.34, 6.49, 6.65, 6.81, 6.98, 7.15, 7.32, 7.5]
    rows = search(r1s, C_E12, C_E12, C_E12)
    print("  可行组合 = %d" % len(rows))
    for rec in rows[:args.top]:
        r1 = rec["stages"][0][0]
        c1, c2, c3 = (s[1] for s in rec["stages"])
        print("  R1=%5.2f C=%5.1f/%5.1f/%5.1f nF | %s" %
              (r1, c1 * 1e9, c2 * 1e9, c3 * 1e9, fmt(rec)))

    rows2 = []
    print("\n" + "=" * 118)
    print("③ 精搜：在②最优的 R1 上下各留 2 档（含完整 D8 配对口径）")
    print("=" * 118)
    if rows:
        best = rows[0]
        r1_best = best["stages"][0][0]
        i = E96_R.index(min(E96_R, key=lambda v: abs(v - r1_best)))
        r1_fine = E96_R[max(0, i - 2):i + 3]
        rows2 = search(r1_fine, C_E12, C_E12, C_E12, with_cmrr=True)
        print("  可行组合 = %d（R1 ∈ %s）" % (len(rows2), r1_fine))
        for rec in rows2[:args.top]:
            r1 = rec["stages"][0][0]
            c1, c2, c3 = (s[1] for s in rec["stages"])
            print("  R1=%5.2f C=%5.1f/%5.1f/%5.1f nF | %s" %
                  (r1, c1 * 1e9, c2 * 1e9, c3 * 1e9, fmt(rec)))
        if args.json:
            with open(os.path.join(HERE, args.json), "w", encoding="utf-8",
                      newline="\n") as fh:
                json.dump(rows2[:args.top], fh, ensure_ascii=False, indent=2,
                          default=float)
            print("\n已写出 %s（前 %d 名）" % (args.json, args.top))
    return rows, rows2


if __name__ == "__main__":
    main()
