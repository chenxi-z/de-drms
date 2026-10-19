#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_results_r4_C_d8fix.py — 组装 r5_results_r4_C_d8fix.json

D8 = 第 4 轮真实 OPA388 补测（1% 配对档）；其余维度原样抄 r5_results_r3_C.json。
"""
from __future__ import annotations

import json
import os

import parse_r4_C_d8 as P

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "r5_results_r4_C_d8fix.json")
R3 = os.path.join(HERE, "r5_results_r3_C.json")


def main():
    d8 = P.main()
    with open(R3, encoding="utf-8") as fh:
        r3 = json.load(fh)
    r3_dims = r3["dims"]
    dims = dict(r3_dims)
    dims["D8"] = d8["dims"]["D8"]
    provenance = {k: ("round4 real-OPA388 re-measure" if k == "D8"
                      else "r5_results_r3_C.json") for k in dims}

    res = {
        "scheme": "C",
        "grade": "C",
        "round": 4,
        "round_scope": "D8 补测（第 3 轮复核：C 案 D8 网表为 0 Ω 理想源，未实例化 OPA388）",
        "n_stages": r3["n_stages"],
        "stages": r3["stages"],
        "dims": dims,
        "dims_provenance": provenance,
        "dims_note": ("D8 = 本轮真实 OPA388、**1% 配对档**实测（ask 指定口径）；"
                      "D1–D7、D9、D10 原样沿用 r5_results_r3_C.json（第 3 轮实测，"
                      "含 D6a/D6b 两个子键）。第 3 轮 dims.D8=135.474 dB 是"
                      "「配对三档取最优（m=0.1%）」的 **0 Ω 理想源**值，口径与本轮不同，"
                      "不可直接相减；同档可比数见 D8_detail_r4.like_for_like_1pct。"),
        "units": r3["units"],
        "D8_detail_r4": d8,
        "D8_score": {
            "value_db": dims["D8"], "full_scale_db": 100.0,
            "score": min(dims["D8"] / 100.0, 1.0),
            "pass_threshold_db": 80.0, "pass": bool(dims["D8"] >= 80.0),
        },
        "xcheck_D8": d8["xcheck"],
        "xcheck_pass": bool(d8["xcheck"]["pass"]),
        "raw_files": {
            "work_dir": d8["dir"],
            "netlists": sorted(f for f in os.listdir(d8["dir"]) if f.endswith(".net")),
            "generator": "hardware/sim/aaf/gen_netlists_r4_C_d8.py",
            "parser": "hardware/sim/aaf/parse_r4_C_d8.py",
            "primary": "r5_work/r4_C_d8/r4_C_d8_v9b_p010.net|.raw|.log（1% 配对，真实 OPA388）",
        },
        "notes": [
            "第 3 轮 C 案 D8 网表 r5_work/r3_C/r5_C_r3_v3p010.net 中 OPAx388 出现 0 次、无 Xfa/Xfb"
            "（grep -c OPAx388 = 0），故其 94.66 dB（1% 档）与 135.47 dB（dims 取值）均为 0 Ω 理想源口径。",
            "本轮按方案 B 第 3 轮 r5_B_v9b_p*_r3.net 的同形网表重生成：.include lib/OPAx388.LIB、"
            "Xfa/Xfb 单位增益跟随器、Vp/Vn DC 2 V AC 1、.ac dec 400 1 40k、"
            "B 线 R×(1+m) 配 C_gnd×(1−m) 且 C_diff×(1−m)。",
            "C_diff 是否随配对缩放对结果无影响（实测 LT 两侧均 95.5238 dB；理论同样逐位相同），"
            "因共模激励下 C_diff 两端等电位不载流，仅在两线失配时承接二阶不平衡电流。",
            "全部 8 个网表 LTspice -b -ascii 均 OK（1–2.2 s/个，0 失败），见 D8_detail_r4.dir 下的 .log。",
            "xcheck_pass 判据：D8 理论（opt_round5 双线 MNA，源模型 opa388）vs LTspice 实测，"
            "|Δ| ≤ 0.5 dB → 实测 0.021 dB，通过。三档配对 + 三档同向共 6 项全部 ≤0.122 dB。",
        ],
    }
    # 同档可比：r3 的 1% 配对档（实为理想源）↔ 本轮真实模型
    res["D8_detail_r4"]["like_for_like_1pct"] = {
        "r3_1pct_paired_db": d8["comparison_r3"]["r3_D8_1pct_db"],
        "r4_1pct_paired_real_db": d8["comparison_r3"]["r4_D8_1pct_db"],
        "delta_db": d8["comparison_r3"]["delta_db"],
        "r4_ideal_source_control_db": d8["comparison_r3"]["r4_ideal_source_control_db"],
        "note": "r3 的 1% 档在 0 Ω 理想源下为 94.66 dB；本轮同档理想源对照 94.61 dB（差 0.05 dB 来自 "
                "r3 用 dec 200/无 C_diff 缩放）；真实 OPA388 把该档抬到 95.52 dB（跟随器输出阻抗使两线 "
                "失配电流略有衰减）。",
    }
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=2)
    print("wrote", OUT)
    print("D8 =", dims["D8"], "dB; xcheck =", res["xcheck_pass"])


if __name__ == "__main__":
    main()
