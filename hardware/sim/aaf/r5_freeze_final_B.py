# -*- coding: utf-8 -*-
"""r5_freeze_final_B.py — 冻结 B 案最终参数（第 4 轮）

输入：第 3 轮冻结的 B 案（`r5_candidates_r2.json`）+ 本轮 C9 修复的平衡点搜索结果
输出：`r5_candidates_final_B.json`（C 案参数不变，对照保留在 r5_candidates_r2.json）

冻结门槛（逐条）
----------------
G1 R 落 E96、C 落 E12（规格 §5.2 C5）
G2 C9：跟随器节点 peaking ≤6 dB（规格 §5.2 C9），并要求 ≥1 dB 数值余量
G3 十维（v4 口径：D6a 线性增量、D8 用 R·C 乘积 1% 配对）全部 ≥ 及格线
G4 fc ∈ [50, 80] kHz（规格 §3）
G5 D4 在 **600 kΩ 高阻角**（叠加第 3 轮 V9e 实测的 OPA388 输入电容极点 −0.3076 dB）后 ≤0.5 dB
G6 第 4 轮 LTspice 瞬态实测：0…600 kΩ 全范围 + R+1%/C+5% 最坏角回稳（r5_p1p2_tran_r4.json）
G7 min 最大者胜

本轮已实测的候选（LTspice 真实 OPA388）
--------------------------------------
P1 6.19/6.04/13.7 Ω, 68/68/27 nF + 12 nF：
    跟随器峰 4.77 dB（引擎 4.75），D4 0.1849（600k 0.4924），D1 84.64 dB；
    瞬态 0/30k/50k/100k/150k/220k/400k/600k Ω 与最坏角全部回稳（35.7–39.8 µs）
P2 6.65/6.04/13.7 Ω, 82/56/27 nF + 12 nF：峰 4.69 dB，D4 0.1864，min 0.6968
P3 6.98/6.04/13.7 Ω, 68/68/22 nF + 12 nF：峰 4.22 dB，D4 0.1874，min 0.6946
"""
from __future__ import annotations

import json
import os

import opt_round5 as E
import r5_fix_B_c9 as F

HERE = os.path.dirname(os.path.abspath(__file__))

# 第 3 轮 V9e 实测（600 kΩ 样品端，OPA388 输入电容 4.5 pF → 16 kHz 额外 −0.3076 dB）
HIGHZ_D4_EXTRA_DB = 0.3076

# 第 4 轮 LTspice 实测（r5_p1p2_tran_r4.json / r5_pick_r4.json / r5_mech2_r4.json）
LT_EVIDENCE = {
    "P1": {
        "follower_peak_db": 4.77, "follower_peak_khz": 278.6,
        "d4_16k_db": 0.1849, "d4_600k_db": 0.4924,
        "d1_db": 84.64, "d2_db": 79.17, "d4_600k_d1_db": 124.61,
        "tran_stable_rs": [0, 10e3, 30e3, 50e3, 100e3, 150e3, 220e3, 400e3, 600e3],
        "tran_tset_us_range": [35.7, 39.8],
        "worst_corner_stable": True,
        "worst_corner_tset_us_range": [37.1, 39.1],
        "work": "r5_work/r4_mech/P1_*、FINDM_*、FIN_cm_*、FINTR_*",
    },
    "P2": {
        "follower_peak_db": 4.69, "follower_peak_khz": 274.2,
        "d4_16k_db": 0.1864, "d4_600k_db": 0.4939,
        "d1_db": 84.68, "d2_db": None, "d4_600k_d1_db": 124.64,
        "tran_stable_rs": [0, 30e3, 50e3, 100e3, 150e3, 220e3, 400e3, 600e3],
        "tran_tset_us_range": [31.8, 40.0],
        "worst_corner_stable": True,
        "worst_corner_tset_us_range": [38.3, 39.3],
        "work": "r5_work/r4_mech/P2_*",
    },
    "P3": {
        "follower_peak_db": 4.22, "follower_peak_khz": 277.3,
        "d4_16k_db": 0.1874, "d4_600k_db": 0.4949,
        "d1_db": 83.85, "d2_db": None, "d4_600k_d1_db": 123.80,
        "tran_stable_rs": [0, 10e3, 50e3, 100e3, 220e3, 400e3, 600e3],
        "tran_tset_us_range": [32.1, 38.4],
        "worst_corner_stable": True,
        "worst_corner_tset_us_range": [35.7, 38.4],
        "work": "r5_work/r4_mech/P3_*",
    },
}

CANDS = [
    dict(tag="P1", r=(6.19, 6.04, 13.7), c=(68e-9, 68e-9, 27e-9), cd=12e-9),
    dict(tag="P2", r=(6.65, 6.04, 13.7), c=(82e-9, 56e-9, 27e-9), cd=12e-9),
    dict(tag="P3", r=(6.98, 6.04, 13.7), c=(68e-9, 68e-9, 22e-9), cd=12e-9),
]


def evaluate(tag, r, c, cd):
    st = [(r[0], c[0], 0.0), (r[1], c[1], 0.0), (r[2], c[2], cd)]
    rec = F.score_v4(st, with_cmrr=True)
    rec["tag"] = tag
    rec["d4_highz"] = rec["raw"]["D4"] + HIGHZ_D4_EXTRA_DB
    lt = LT_EVIDENCE[tag]
    gates = {
        "G1_series": (r[0] in F.E96_R and r[1] in F.E96_R and r[2] in F.E96_R
                      and all(abs(v * 1e9 - round(v * 1e9)) < 1e-6 for v in c)),
        "G2_C9": rec["c9_ok"] and rec["c9_peak_db"] <= F.C9_LIMIT_DB - 1.0,
        "G3_dims": (not rec["failing"]) and rec["hard_ok"],
        "G4_fc": 50e3 <= rec["pred"]["f_c_hz"] <= 80e3,
        "G5_d4_highz": rec["d4_highz"] <= 0.50,
        "G6_ltspice_tran": lt["worst_corner_stable"] and len(lt["tran_stable_rs"]) >= 7,
    }
    rec["gates"] = gates
    rec["ok"] = all(gates.values())
    rec["lt"] = lt
    return rec


def main():
    rows = [evaluate(c["tag"], c["r"], c["c"], c["cd"]) for c in CANDS]
    hdr = ("tag  R/Ω(E96)              C/nF(E12)      fc/kHz  pk/dB  D4     D4@600k  "
           "D1     D2     min     gates")
    print(hdr)
    print("-" * len(hdr))
    for rec in rows:
        (r1, c1, _), (r2, c2, _), (r3, c3, _) = rec["stages"]
        g = "".join(k.split("_")[0][-1] if v else "×" for k, v in rec["gates"].items())
        print("%-4s %.2f/%.2f/%.2f           %.0f/%.0f/%.0f     %6.1f  %5.2f  %.4f %7.4f  "
              "%6.2f %5.1f  %.4f  %s" % (
                  rec["tag"], r1, r2, r3, c1 * 1e9, c2 * 1e9, c3 * 1e9, rec["fc_khz"],
                  rec["c9_peak_db"], rec["raw"]["D4"], rec["d4_highz"], rec["raw"]["D1"],
                  rec["raw"]["D2"], rec["min_score"], g))
        bad = [k for k, v in rec["gates"].items() if not v]
        if bad:
            print("     ✗ 未过门槛: %s" % bad)

    ok = [r for r in rows if r["ok"]]
    ok.sort(key=lambda z: -z["min_score"])
    if not ok:
        raise SystemExit("没有候选通过全部冻结门槛")
    ch = ok[0]
    print("\n★ 冻结 %s（min=%.4f，C9=%.2f dB，全部门槛通过）"
          % (ch["tag"], ch["min_score"], ch["c9_peak_db"]))

    p, raw = ch["pred"], ch["raw"]
    stages = [[float(a), float(b), float(c)] for a, b, c in ch["stages"]]
    out = {
        "grade": "B",
        "n_stages": 3,
        "stages": stages,
        "r_series": "E96",
        "c_series": "E12",
        "source": "r4/c9-fix",
        "pred": p,
        "dims": raw,
        "scores": ch["scores"],
        "pass": ch["pass"],
        "hard": ch["hard"],
        "min_score": ch["min_score"],
        "design_score": ch["min_score"],
        "c9": {
            "follower_node_peak_db": ch["c9_peak_db"],
            "follower_node_peak_hz": ch["c9_peak_f_hz"],
            "limit_db": F.C9_LIMIT_DB,
            "ok": ch["c9_ok"],
            "ltspice": {"peak_db": ch["lt"]["follower_peak_db"],
                        "peak_khz": ch["lt"]["follower_peak_khz"]},
            "note": ("C9 考核节点 = 跟随器输出（r5_report_r3 §4.2）。"
                     "引擎↔LTspice 在该候选 4.75↔4.77 dB；同法在 R1=2.74 为 10.65↔10.66、"
                     "R1=6.8 为 4.41↔4.43 dB（三点最大偏差 0.02 dB）"),
        },
        "ltspice_crosscheck": {
            "D1_dm_fmod_db": {"engine": p["A_dm"], "ltspice": ch["lt"]["d1_db"],
                              "delta_db": ch["lt"]["d1_db"] - p["A_dm"]},
            "D2_cm_fmod_db": {"engine": p["A_cm"], "ltspice": ch["lt"]["d2_db"],
                              "delta_db": (ch["lt"]["d2_db"] - p["A_cm"]
                                           if ch["lt"]["d2_db"] else None)},
            "D4_16k_db": {"engine": raw["D4"], "ltspice": ch["lt"]["d4_16k_db"],
                          "delta_db": ch["lt"]["d4_16k_db"] - raw["D4"]},
            "C9_follower_peak_db": {"engine": ch["c9_peak_db"],
                                    "ltspice": ch["lt"]["follower_peak_db"],
                                    "delta_db": ch["lt"]["follower_peak_db"] - ch["c9_peak_db"]},
            "D1_at_600k_ltspice_db": ch["lt"]["d4_600k_d1_db"],
            "D4_at_600k_ltspice_db": ch["lt"]["d4_600k_db"],
            "criterion": "规格 §8：AC 偏差 ≤0.5 dB；本轮最大 |Δ| 见上（D1 0.34 / D4 0.00 / C9 0.02）",
        },
        "highz": {
            "d4_at_600k_db": ch["d4_highz"],
            "d4_at_600k_db_ltspice": ch["lt"]["d4_600k_db"],
            "extra_db_from_opa388_cin": HIGHZ_D4_EXTRA_DB,
            "limit_db": 0.50,
            "ok": ch["d4_highz"] <= 0.50,
            "note": "第 3 轮 V9e 实测口径：600 kΩ 源 + OPA388 输入电容 4.5 pF 的输入极点",
        },
        "d5_ltspice": {
            "stable_source_impedances_ohm": ch["lt"]["tran_stable_rs"],
            "tset_us_range": ch["lt"]["tran_tset_us_range"],
            "worst_corner_stable": ch["lt"]["worst_corner_stable"],
            "work_dir": ch["lt"]["work"],
            "note": ("第 3 轮 50–220 kΩ 极限环在本参数下**消失**；"
                     "判据 2 V 阶跃 / 10 ns 沿 / 0.01%(200 µV) 带"),
        },
        "gates": ch["gates"],
        "change_vs_r3": {
            "from": [[2.74, 6.8e-08, 0.0], [6.04, 5.6e-08, 0.0],
                     [13.700000000000001, 5.6e-08, 1.2e-08]],
            "to": stages,
            "what": "首级 R 2.74 → 6.19 Ω；C1 68 → 68 nF（不变）、C2 56 → 68 nF、C3 56 → 27 nF",
            "why": ("C9：跟随器节点 peaking 10.66 → 4.75 dB（≤6 dB）；"
                    "同时 fc 由 79.9 kHz 维持在 79.9 kHz（C2/C3 减小抵消首级 R 增大的 fc 下移）"),
            "side_effects": ("D4 0.1877 → 0.1849 dB（略好）；D1 86.15 → 84.30 dB（−1.85，仍 ≥80）；"
                             "D2 83.06 → 78.83 dB（−4.2，仍 ≥60）；D10 0.087 → 0.083 µs；"
                             "D5 理论 53.1 µs 不变；器件数 13 件不变"),
        },
    }
    path = os.path.join(HERE, "r5_candidates_final_B.json")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2, default=float)
    print("已写出 %s" % path)
    return out


if __name__ == "__main__":
    main()
