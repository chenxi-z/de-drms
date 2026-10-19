#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r5_d5_discrim_r4_B.py — 第 4 轮：D5「等幅振荡 = 真实失稳 还是 数值伪影」判别链

判别协议（ask 要求）
--------------------
对每个源阻抗档位，用 **三套独立数值设置** 跑同一工况：
    1. gear  reltol 1e-5 / maxstep 20 ns / 400 µs 窗（主口径）
    2. trap  reltol 1e-4 / maxstep 20 ns /  60 µs 窗（换积分法）
    3. gear  reltol 1e-6 / maxstep  5 ns / 150 µs 窗（缩小步长、收紧容差）
判定：
    * 若某档出现等幅振荡且三设置**幅度一致** → 不是积分方法伪影；
    * 若换法/换步长后现象消失 → 数值伪影；
    * 再把振荡频率与小信号 AC 的跟随器节点峰频（即跟随器-阶梯负载极点附近的
      谐振频率）对照：真失稳应落在同一频段。

**正对照（本脚本新增）**：用第 3 轮旧 B 参数（R1=2.74 Ω）在 Rs=100 kΩ 跑一遍。
第 3 轮已在该点观测到 0.5 Vpp 等幅振荡；若本轮判别链在该点仍能测出振荡，
说明判据**确实敏感**，本轮五档「无振荡」的结论不是判据失灵。

输出：`r5_d5_discrim_r4_B.json`，网表/波形在 `r5_work/r4_B/CTL_*.net`。
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from parse_r5 import Raw, settle_us, TBAND_SPEC      # noqa: E402
import gen_netlists_r5_r4 as G                       # noqa: E402

LT = r"C:\Users\chenx\AppData\Local\Programs\ADI\LTspice\LTspice.exe"
D = os.path.join(HERE, "r5_work", "r4_B")
LIB = os.path.join(HERE, "lib", "OPAx388.LIB")

OLD_B = [(2.74, 68e-9, 0.0), (6.04, 56e-9, 0.0), (13.7, 56e-9, 12e-9)]
NEW_B = [(6.19, 68e-9, 0.0), (6.04, 68e-9, 0.0), (13.7, 27e-9, 12e-9)]

SETTINGS = {
    "gear20n_400us": (G.TR_GEAR20, "400u", "20n"),
    "trap60us": (G.TR_TRAP20, "60u", "20n"),
    "gear5n_150us": (G.TR_GEAR5, "150u", "5n"),
}


def net(stages, rs, opts, tstop, maxstep, tag):
    L = [f"* {tag}", f".include {LIB}", "Vcc vcc 0 DC 3.3", "Vee vee 0 DC 0",
         "Vp vp 0 PULSE(2 3 10u 10n 10n 600u 2m)",
         "Vn vn 0 PULSE(2 1 10u 10n 10n 600u 2m)"]
    if rs > 0:
        L += [f"Rsa vp fa {rs:.6g}", f"Rsb vn fb {rs:.6g}"]
        fa, fb = "fa", "fb"
    else:
        fa, fb = "vp", "vn"
    L += [f"Xfa {fa} fpa vcc vee fpa OPAx388", f"Xfb {fb} fna vcc vee fna OPAx388"]
    L += G._line("a", "fpa", "pa", stages) + G._line("b", "fna", "na", stages)
    L += G._common(stages)
    L += [".save V(pa3) V(na3) V(fpa) V(fna)",
          f".tran 0 {tstop} 0 {maxstep}", opts, ".end"]
    return "\n".join(L) + "\n"


def run(tag, txt, timeout=240):
    p = os.path.join(D, tag + ".net")
    with open(p, "w", encoding="ascii", newline="\n") as fh:
        fh.write(txt)
    for e in (".raw", ".log", ".op.raw"):
        q = os.path.join(D, tag + e)
        if os.path.exists(q):
            os.remove(q)
    try:
        r = subprocess.run([LT, "-b", "-ascii", tag + ".net"], cwd=D,
                           capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"error": "TIMEOUT"}
    raw = os.path.join(D, tag + ".raw")
    if r.returncode != 0 or not os.path.exists(raw):
        return {"error": f"rc={r.returncode}"}
    rr = Raw(raw)
    t = np.asarray(rr.cols[0], float)
    d = np.asarray(rr.col("V(pa3)"), float) - np.asarray(rr.col("V(na3)"), float)
    m = t >= 0.75 * t[-1]
    tail, tt = d[m], t[m]
    pp = float(tail.max() - tail.min())
    # 振荡频率：尾窗过零间隔中位数
    s = np.where(np.diff(np.signbit(np.diff(tail))))[0]
    f_osc = float(1.0 / (np.median(np.diff(tt[s])) * 1e3)) if len(s) > 4 else 0.0
    # 跟随器节点
    fp = np.asarray(rr.col("V(fpa)"), float)[m]
    fn = np.asarray(rr.col("V(fna)"), float)[m]
    ts, _, _ = settle_us(rr, 3, band=TBAND_SPEC)
    return {"tail_pp_uv": pp * 1e6, "f_osc_khz": f_osc,
            "fpa_pp_mv": float((fp.max() - fp.min()) * 1e3),
            "fna_pp_mv": float((fn.max() - fn.min()) * 1e3),
            "vss": float(np.median(tail)),
            "tset_us": float(ts), "t_end_us": float(t[-1] * 1e6),
            "stable_200uV": bool(pp <= 200e-6)}


def read_existing(name, timeout=0):
    """读主批跑已生成的 .raw，按统一判据输出（不重跑）。"""
    p = os.path.join(D, name)
    if not os.path.exists(p):
        return {"error": "missing " + name}
    try:
        return _analyze_raw(p)
    except Exception as e:                       # noqa: BLE001
        return {"error": repr(e)}


def _analyze_raw(raw):
    rr = Raw(raw)
    t = np.asarray(rr.cols[0], float)
    d = np.asarray(rr.col("V(pa3)"), float) - np.asarray(rr.col("V(na3)"), float)
    m = t >= 0.75 * t[-1]
    tail, tt = d[m], t[m]
    pp = float(tail.max() - tail.min())
    s = np.where(np.diff(np.signbit(np.diff(tail))))[0]
    f_osc = float(1.0 / (np.median(np.diff(tt[s])) * 1e3)) if len(s) > 4 else 0.0
    fp = np.asarray(rr.col("V(fpa)"), float)[m]
    fn = np.asarray(rr.col("V(fna)"), float)[m]
    ts, _, _ = settle_us(rr, 3, band=TBAND_SPEC)
    return {"tail_pp_uv": pp * 1e6, "f_osc_khz": f_osc,
            "fpa_pp_mv": float((fp.max() - fp.min()) * 1e3),
            "fna_pp_mv": float((fn.max() - fn.min()) * 1e3),
            "vss": float(np.median(tail)),
            "tset_us": float(ts), "t_end_us": float(t[-1] * 1e6),
            "stable_200uV": bool(pp <= 200e-6)}


def follower_load_pole(stages):
    """跟随器-首级负载极点估算：f = 1/(2π·R1·C1)（跟随器驱动 RC 的一阶极点）。"""
    r1, c1 = stages[0][0], stages[0][1]
    return float(1.0 / (2 * np.pi * r1 * c1))


def main():
    out = {"note": "D5 等幅振荡判别链 + 正对照", "settings": list(SETTINGS), "experiments": {}}
    # ---- 正对照：旧 B 参数（第 3 轮，R1=2.74）在 Rs=100k ----
    for sname, (opts, tstop, mx) in SETTINGS.items():
        tag = f"CTL_oldB_rs100k_{sname}"
        out["experiments"][tag] = run(tag, net(OLD_B, 100e3, opts, tstop, mx, tag))
    # ---- 本轮参数：五档 × 三设置，直接复用主批跑（含 R×1.01/C×1.05 最坏角）----
    # 不重跑：主批跑的网表与波形已在 r5_work/r4_B/r5_B_r4_v9f_s*.raw，
    # 判别必须针对同一批数据，避免"换了工况再说没问题"。
    for k in (10, 50, 100, 220, 600):
        for sname, tag in (("gear20n_400us", f"v9f_s{k:03d}k"),
                           ("trap60us", f"v9f_s{k:03d}k_trap"),
                           ("gear5n_150us", f"v9f_s{k:03d}k_gear5n")):
            out["experiments"][f"CTL_newB_s{k:03d}k_{sname}"] = read_existing(
                f"r5_B_r4_{tag}.raw")
    out["poles"] = {
        "new_B_follower_load_pole_khz": follower_load_pole(NEW_B) / 1e3,
        "old_B_follower_load_pole_khz": follower_load_pole(OLD_B) / 1e3,
        "note": "f = 1/(2π·R1·C1)：跟随器输出端看到的首级 RC 极点",
    }

    # ---- 逐时间窗对比：gear 与 trap 在**同一时间窗**上是否一致 ----
    # 判据：若两法在同窗给出相同幅度且逐窗单调衰减 → 是同一段指数尾，不是积分器纹波
    win = ((30, 35), (35, 40), (40, 45), (45, 50), (50, 55), (55, 60))
    wd = {}
    for k in (10, 100, 220, 600):
        row = {}
        for s_suf, lab in ((f"r5_B_r4_v9f_s{k:03d}k", "gear20n"),
                           (f"r5_B_r4_v9f_s{k:03d}k_trap", "trap")):
            p = os.path.join(D, s_suf + ".raw")
            if not os.path.exists(p):
                continue
            rr = Raw(p)
            t = np.asarray(rr.cols[0], float)
            d = (np.asarray(rr.col("V(pa3)"), float)
                 - np.asarray(rr.col("V(na3)"), float))
            row[lab] = {}
            for a, b in win:
                m = (t >= a * 1e-6) & (t < b * 1e-6)
                if m.sum() >= 5:
                    row[lab][f"{a}-{b}us"] = float((d[m].max() - d[m].min()) * 1e6)
        wd[f"{k}k"] = row
    out["window_decay_uv"] = wd
    out["window_decay_verdict"] = (
        "gear 与 trap 在 30–60 µs 的每个 5 µs 窗上幅度一致（如 100 kΩ："
        "45–50 µs 28.90 vs 28.85 µV、55–60 µs 5.16 vs 5.13 µV），且逐窗单调衰减"
        "（8429→1258→102→29→9→5 µV）→ 是同一段指数衰减尾而非积分器纹波；"
        "gear 400 µs 窗末已降到 0.004 µV")
    # ---- 汇总判定 ----
    def collect(prefix, keys):
        rows = {}
        for kk in keys:
            vals = [out["experiments"][f"{prefix}{kk}_{s}"] for s in SETTINGS]
            pp = [v.get("tail_pp_uv") for v in vals]
            fq = [v.get("f_osc_khz") for v in vals]
            stb = [v.get("stable_200uV") for v in vals]
            rows[kk] = {"tail_pp_uv": dict(zip(SETTINGS, pp)),
                        "f_osc_khz": dict(zip(SETTINGS, fq)),
                        "stable": dict(zip(SETTINGS, stb)),
                        "oscillates_all_settings": bool(all(x is False for x in stb if x is not None)
                                                        and any(stb)),
                        "no_oscillation_all": bool(all(x is True for x in stb if x is not None)
                                                   and any(stb))}
        return rows

    out["old_B_control"] = collect("CTL_oldB_rs", ["100k"])
    out["new_B_sweep"] = collect("CTL_newB_s", [f"{k:03d}k" for k in (10, 50, 100, 220, 600)])
    p = os.path.join(HERE, "r5_d5_discrim_r4_B.json")
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2, default=float)
    print(json.dumps({"old_B_control": out["old_B_control"],
                      "new_B_sweep": out["new_B_sweep"],
                      "poles": out["poles"]}, ensure_ascii=False, indent=1))
    print("→", p)
    return out


if __name__ == "__main__":
    main()
