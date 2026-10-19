#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_netlists_r4_C_d8.py — 第 4 轮补测：方案 C 的 D8 真实 OPA388 模型网表

背景
----
第 3 轮复核发现：`gen_netlists_r5_r3.py` 里 D8 的 `v3p*`/`v3sr*` 走的是 `gen_v3()`，
而 `gen_v3()` 从不实例化 OPA388（文件头写 "real OPA388" 但网表里没有 `.include`
也没有 `Xfa/Xfb`），且其 `_scale_line()` 对 C_diff 不缩放。→ C 案第 3 轮 D8
（94.66 dB @1%）实为 0 Ω 理想源口径，不满足规格 v4 §5「评分主口径 = 真实 OPA388 模型」。

本文件按 **方案 B 第 3 轮 D8 网表的同口径**（`r5_work/r3_B/r5_B_v9b_p{001,05,1}_r3.net`）
为方案 C 重新生成：
  * `.include lib/OPAx388.LIB` + `Xfa/Xfb` 两个单位增益跟随器
  * B 线 R×(1+m)，C_gnd ×(1−m)，**C_diff ×(1−m)**（与 r5_score_v4.cmrr_rc_paired 一致，
    也与 B 案 r3 网表一致；注意这与 C 案 r3 的 gen_v3 口径不同——后者 C_diff 不缩放）
  * m = 0.1% / 0.5% / 1% 三档配对 + 同向失配 m = 0.1/0.5/1%（对照）
  * 另出 0 Ω 理想源配对的 1% 对照（隔离跟随器影响，对应 B 的 v3p1）

网表参数完全沿用 B 案 r3：Vp/Vn DC 2 V AC 1、`.ac dec 400 1 40k`、同一 TOPT、
Cd/Rin 130k/Cpa Cna 5 pF。

用法：python gen_netlists_r4_C_d8.py [--outdir r5_work/r4_C_d8]
"""
from __future__ import annotations

import argparse
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, "lib", "OPAx388.LIB")
CAND = os.path.join(HERE, "r5_candidates_r2.json")
TOPT = ".options plotwinsize=0 reltol=1e-6 abstol=1e-12 vntol=1e-9 chgtol=1e-15 trtol=1"
VCC = 3.3
RLOAD = 130e3
CPIN = 5e-12
D8_M = (0.001, 0.005, 0.01)


def _fmt(x):
    return f"{x:.10g}"


def _line(side, src, node, stages):
    out, prev = [], src
    for i, (r, cg, _cd) in enumerate(stages, 1):
        out.append(f"R{side}{i} {prev} {node}{i} {_fmt(r)}")
        out.append(f"C{side}{i} {node}{i} 0 {_fmt(cg)}")
        prev = f"{node}{i}"
    return out


def _common(stages):
    n = len(stages)
    out = []
    cd = stages[-1][2]
    if cd > 0:
        out.append(f"Cd pa{n} na{n} {_fmt(cd)}")
    out.append(f"Rin pa{n} na{n} {_fmt(RLOAD)}")
    out.append(f"Cpa pa{n} 0 {_fmt(CPIN)}")
    out.append(f"Cna na{n} 0 {_fmt(CPIN)}")
    return out


def _hdr(tag, note):
    return [f"* r4 C d8fix {tag} - {note}",
            "* gen_netlists_r4_C_d8.py (round-4 re-test; same form as B r3 v9b_p*)"]


def _pair(stages, m, mode):
    if mode == "paired":
        return [(r * (1 + m), cg * (1 - m), cd * (1 - m)) for r, cg, cd in stages]
    return [(r * (1 + m), cg * (1 + m), cd * (1 + m)) for r, cg, cd in stages]


def gen_cm(stages, tag, m, mode, real=True):
    """共模 AC。mode='paired'：R×(1+m) 配 C×(1−m)；'same'：R/C 同 ×(1+m)。"""
    n = len(stages)
    sb = _pair(stages, m, mode)
    desc = ("R*(1+%g) PAIRED with C*(1-%g)" % (m, m) if mode == "paired"
            else "same-direction %g%% mismatch (control)" % (m * 100))
    L = _hdr(tag, ("real OPA388, AC CM, " + desc) if real
             else ("ideal 0ohm source, AC CM, " + desc))
    if real:
        L.append(".include " + LIB)
        L.append(f"Vcc vcc 0 DC {VCC}")
        L.append("Vee vee 0 DC 0")
    L += ["Vp vp 0 DC 2 AC 1", "Vn vn 0 DC 2 AC 1"]
    if real:
        L += ["Xfa vp fpa vcc vee fpa OPAx388", "Xfb vn fna vcc vee fna OPAx388"]
        L += _line("a", "fpa", "pa", stages)
        L += _line("b", "fna", "na", sb)
    else:
        L += _line("a", "vp", "pa", stages)
        L += _line("b", "vn", "na", sb)
    L += _common(stages)
    L += [".ac dec 400 1 40k", TOPT,
          f".meas AC cm_dc  FIND mag(V(pa{n}))       AT 1",
          f".meas AC dm_16k FIND mag(V(pa{n})-V(na{n})) AT 16k",
          ".end"]
    return "\n".join(L) + "\n"


def generate(outdir):
    os.makedirs(outdir, exist_ok=True)
    with open(CAND, encoding="utf-8") as fh:
        st = [tuple(map(float, s)) for s in json.load(fh)["C"]["stages"]]
    files = []

    def w(name, text):
        with open(os.path.join(outdir, name), "w", encoding="ascii", newline="\n") as fh:
            fh.write(text)
        files.append(name)

    for m in D8_M:
        k = int(round(m * 1000))
        w(f"r4_C_d8_v9b_p{k:03d}.net",
          gen_cm(st, f"v9b_p{k:03d}", m, "paired", real=True))
        w(f"r4_C_d8_v9b_s{k:03d}.net",
          gen_cm(st, f"v9b_s{k:03d}", m, "same", real=True))
    # 0 Ω 理想源配对 1% 对照（同 B 的 v3p1）
    w("r4_C_d8_v3p010.net", gen_cm(st, "v3p010", 0.01, "paired", real=False))
    # 标称（无失配）真实模型共模，作基线
    w("r4_C_d8_v9b_nom.net", gen_cm(st, "v9b_nom", 0.0, "paired", real=True))
    return files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default=os.path.join(HERE, "r5_work", "r4_C_d8"))
    a = ap.parse_args()
    fs = generate(a.outdir)
    print(f"{len(fs)} netlists -> {a.outdir}")
    for f in fs:
        print("  ", f)


if __name__ == "__main__":
    main()
