# -*- coding: utf-8 -*-
"""r5_mech_limitcycle.py — D5 中间阻抗「等幅极限环」的机理研判（第 4 轮）

问题（第 3 轮遗留）
------------------
B/C 案在源阻抗 50–300 kΩ 时，真实 OPA388 模型的瞬态呈**等幅极限环**（不回稳），
而 0 Ω 与 600 kΩ 两端稳定。到底是
  (a) 跟随器驱动容性负载的真实不稳定（Zout_cl 负实部 + 阶梯电容 + Rs∥Cin 输入极点），还是
  (b) LTspice 数值伪影？

本脚本生成并批跑以下判别性实验（全部真实 OPA388 模型，2 V 差分阶跃、10 ns 沿、判据 200 µV）：

  E1 基线          B 标称（R1=2.74）@ Rs = 0/50k/100k/220k/600k      —— 复现第 3 轮
  E2 C9 修复后     B R1=6.8 @ 同样 Rs 扫描                           —— C9 修复能否顺带消掉极限环
  E3 数值收敛      E1@100k 用 4 组求解器设置（gear/trap × maxstep/reltol）—— 区分 (b)
  E4 输入电容      E1@100k 但把模型 C_C_DIFF/C_C_COM 置 ≈0（本地副本，不动 lib/）
                   —— 检验「Rs ∥ 输入电容」是否是必要环节
  E5 无源网络单独  E1@100k 但跟随器换成理想 VCVS（E=1）
                   —— 无源阶梯 + Rs 本身是否稳定
  E6 小信号 AC     Rs 扫描下跟随器节点/引脚增益峰（线性口径）
                   —— 小信号是否真的不稳定（有 RHP 极点则 AC 会看到发散趋势）

输出：r5_work/r4_mech/*.net|*.raw|*.log + r5_d5_mech_r4.json
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, "lib", "OPAx388.LIB")
WD = os.path.join(HERE, "r5_work", "r4_mech")
LTSPICE = r"C:\Users\chenx\AppData\Local\Programs\ADI\LTspice\LTspice.exe"

# 阶梯（B 标称 / B-C9 修复 / 第 4 轮冻结候选）
LAD_B = dict(r1=2.74, r2=6.04, r3=13.7, c1=68e-9, c2=56e-9, c3=56e-9, cd=12e-9)
LAD_B68 = dict(r1=6.8, r2=6.04, r3=13.7, c1=68e-9, c2=56e-9, c3=56e-9, cd=12e-9)
LAD_FIN = dict(r1=6.65, r2=6.04, r3=13.7, c1=82e-9, c2=56e-9, c3=27e-9, cd=12e-9)

OPTS = {
    "gear20n": ".options plotwinsize=0 method=gear reltol=1e-5 abstol=1e-11 vntol=1e-8 chgtol=1e-14 trtol=7\n.tran 0 400u 0 20n",
    "trap40n": ".options plotwinsize=0 method=trap reltol=1e-4 abstol=1e-11 vntol=1e-8 chgtol=1e-14 trtol=3\n.tran 0 400u 0 40n",
    "gear2n": ".options plotwinsize=0 method=gear reltol=1e-7 abstol=1e-13 vntol=1e-10 chgtol=1e-16 trtol=2\n.tran 0 400u 0 2n",
    "trap5n": ".options plotwinsize=0 method=trap reltol=1e-6 abstol=1e-13 vntol=1e-10 chgtol=1e-16 trtol=2\n.tran 0 400u 0 5n",
}


def netlist(r1, r2, r3, c1, c2, c3, cd, rs, *, include=LIB, ideal_follower=False,
            opts="gear20n", save_pin=3, tag=""):
    """差分双线阶梯 + 可选 Rs + 真实/理想跟随器。"""
    L = [f"* mech {tag}", f".include {include}", "Vcc vcc 0 DC 3.3", "Vee vee 0 DC 0",
         "Vp vp 0 PULSE(2 3 10u 10n 10n 500u 2m)",
         "Vn vn 0 PULSE(2 1 10u 10n 10n 500u 2m)"]
    if rs > 0:
        L += [f"Rsa vp fa {rs:.6g}", f"Rsb vn fb {rs:.6g}"]
        fa, fb = "fa", "fb"
    else:
        fa, fb = "vp", "vn"
    if ideal_follower:
        L += [f"Efa fpa 0 {fa} 0 1", f"Efb fna 0 {fb} 0 1"]
    else:
        L += [f"Xfa {fa} fpa vcc vee fpa OPAx388", f"Xfb {fb} fna vcc vee fna OPAx388"]
    L += [f"Ra1 fpa pa1 {r1:.6g}", f"Ca1 pa1 0 {c1:.6g}",
          f"Ra2 pa1 pa2 {r2:.6g}", f"Ca2 pa2 0 {c2:.6g}",
          f"Ra3 pa2 pa3 {r3:.6g}", f"Ca3 pa3 0 {c3:.6g}",
          f"Rb1 fna na1 {r1:.6g}", f"Cb1 na1 0 {c1:.6g}",
          f"Rb2 na1 na2 {r2:.6g}", f"Cb2 na2 0 {c2:.6g}",
          f"Rb3 na2 na3 {r3:.6g}", f"Cb3 na3 0 {c3:.6g}",
          f"Cd pa3 na3 {cd:.6g}", "Rin pa3 na3 130000",
          "Cpa pa3 0 5e-12", "Cna na3 0 5e-12",
          OPTS[opts],
          f".save V(pa{save_pin}) V(na{save_pin}) V(fpa) V(fna)",
          ".end"]
    return "\n".join(L) + "\n"


def ac_netlist(r1, r2, r3, c1, c2, c3, cd, rs, *, include=LIB, ideal_follower=False, tag=""):
    L = [f"* mechAC {tag}", f".include {include}", "Vcc vcc 0 DC 3.3", "Vee vee 0 DC 0",
         "Vp vp 0 DC 2 AC 0.5", "Vn vn 0 DC 2 AC -0.5"]
    if rs > 0:
        L += [f"Rsa vp fa {rs:.6g}", f"Rsb vn fb {rs:.6g}"]
        fa, fb = "fa", "fb"
    else:
        fa, fb = "vp", "vn"
    if ideal_follower:
        L += [f"Efa fpa 0 {fa} 0 1", f"Efb fna 0 {fb} 0 1"]
    else:
        L += [f"Xfa {fa} fpa vcc vee fpa OPAx388", f"Xfb {fb} fna vcc vee fna OPAx388"]
    L += [f"Ra1 fpa pa1 {r1:.6g}", f"Ca1 pa1 0 {c1:.6g}",
          f"Ra2 pa1 pa2 {r2:.6g}", f"Ca2 pa2 0 {c2:.6g}",
          f"Ra3 pa2 pa3 {r3:.6g}", f"Ca3 pa3 0 {c3:.6g}",
          f"Rb1 fna na1 {r1:.6g}", f"Cb1 na1 0 {c1:.6g}",
          f"Rb2 na1 na2 {r2:.6g}", f"Cb2 na2 0 {c2:.6g}",
          f"Rb3 na2 na3 {r3:.6g}", f"Cb3 na3 0 {c3:.6g}",
          f"Cd pa3 na3 {cd:.6g}", "Rin pa3 na3 130000",
          "Cpa pa3 0 5e-12", "Cna na3 0 5e-12",
          ".ac dec 1000 0.1 20Meg",
          ".options plotwinsize=0 reltol=1e-6 abstol=1e-12 vntol=1e-9 chgtol=1e-15 trtol=1",
          ".save V(fpa) V(fna) V(pa3) V(na3)",
          ".end"]
    return "\n".join(L) + "\n"


def run(path, timeout=400):
    """批跑 LTspice（-b -ascii），返回 (ok, elapsed_note)。"""
    try:
        p = subprocess.run([LTSPICE, "-b", "-ascii", path], capture_output=True,
                           timeout=timeout)
        return p.returncode == 0, (p.stdout or b"").decode(errors="replace")[-300:]
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT"


def _num(tok):
    if "," in tok:                     # AC 复数值 "re,im"
        a, b = tok.split(",")
        return complex(float(a), float(b))
    return float(tok)


def parse_raw(path):
    txt = open(path, "r", encoding="ascii", errors="replace").read()
    i = txt.find("Values:")
    head, body = txt[:i], txt[i + len("Values:"):]
    names, npts, nvars = [], 0, 0
    in_vars = False
    for line in head.splitlines():
        s = line.strip()
        if s.startswith("No. Variables:"):
            nvars = int(s.split(":")[1])
        elif s.startswith("No. Points:"):
            npts = int(s.split(":")[1])
        elif s == "Variables:":
            in_vars = True
        elif in_vars:
            parts = line.split("\t")
            if len(parts) >= 3 and parts[2].strip():
                names.append(parts[2].strip())
    vals = []
    for line in body.splitlines():
        if not line.strip():
            continue
        toks = line.replace("\t", " ").split()
        if line.startswith("\t"):
            vals += [_num(t) for t in toks]
        else:
            vals.append(_num(toks[-1]))
    vals = vals[:npts * nvars]
    cols = {names[k]: np.array(vals[k::nvars]) for k in range(nvars)}
    return cols, names


def analyze_tran(path):
    """尾段（后 20%）差分峰峰值 + 振荡频率 + 建立时间（200 µV 带）。"""
    cols, names = parse_raw(path)
    t = cols[names[0]]
    pa = [n for n in names if n.lower().startswith("v(pa")]
    na = [n for n in names if n.lower().startswith("v(na")]
    d = cols[pa[0]] - cols[na[0]]
    m = t >= 0.8 * t[-1]
    tt, dd = t[m], d[m]
    pp = float(dd.max() - dd.min())
    # 尾段局部极值 → 主频
    s = np.where(np.diff(np.signbit(np.diff(dd))))[0]
    if len(s) > 4:
        per = 2.0 * float(np.median(np.diff(tt[s])))
        f_osc = 1.0 / per if per > 0 else 0.0
    else:
        f_osc = 0.0
    # 建立时间（0.01% = 200 µV of 2 V）：最后一次出带之后不再入带
    vss = float(np.median(dd))
    band = 200e-6
    out = np.where(np.abs(d - vss) > band)[0]
    tset = float(t[out[-1]]) if len(out) else 0.0
    return {"tail_pp_uv": pp * 1e6, "f_osc_khz": f_osc / 1e3,
            "v_ss": vss, "t_settle_us": tset * 1e6, "npts": int(len(t)),
            "stable": bool(pp <= band)}


def analyze_ac(path):
    cols, names = parse_raw(path)
    f = np.asarray(cols[names[0]], float)
    pa = [n for n in names if n.lower().startswith("v(pa")][0]
    na = [n for n in names if n.lower().startswith("v(na")][0]
    fp = [n for n in names if n.lower().startswith("v(fp")][0]
    fn = [n for n in names if n.lower().startswith("v(fn")][0]
    dm = np.abs(np.asarray(cols[pa]) - np.asarray(cols[na]))
    dm_f = np.abs(np.asarray(cols[fp]) - np.asarray(cols[fn])) / 2.0   # 单线 |V(fpa)|
    g_pin = 20 * np.log10(np.maximum(dm / dm[0], 1e-300))
    g_fol = 20 * np.log10(np.maximum(dm_f / dm_f[0], 1e-300))
    i = int(np.argmax(g_pin))
    j = int(np.argmax(g_fol))
    return {"pin_peak_db": float(g_pin[i]), "pin_peak_khz": float(f[i] / 1e3),
            "foll_peak_db": float(g_fol[j]), "foll_peak_khz": float(f[j] / 1e3),
            "g_16k_db": float(np.interp(16e3, f, g_pin)),
            "g_fmod_db": float(-np.interp(4.096e6, f, g_pin))}


def make_zero_cin_lib():
    """生成本地副本：把输入电容 C_C_DIFF / C_C_COM0/1 置 ≈0（不动 lib/ 原件）。"""
    src = open(LIB, "r", encoding="ascii", errors="replace").read()
    out = src
    for nm in ("C_C_DIFF", "C_C_COM0", "C_C_COM1"):
        lines = out.splitlines()
        for k, ln in enumerate(lines):
            if ln.strip().startswith(nm):
                parts = ln.split()
                parts[-1] = "1E-15"          # 1 fF ≈ 0
                lines[k] = " ".join(parts)
        out = "\n".join(lines)
    path = os.path.join(WD, "OPAx388_noCin.LIB")
    open(path, "w", encoding="ascii", newline="\n").write(out)
    return path


def main(argv=None):
    os.makedirs(WD, exist_ok=True)
    res = {"experiments": {}}
    jobs = []

    # ---- E1 基线：B 标称 Rs 扫描 ----
    for rs in (0, 50e3, 100e3, 220e3, 600e3):
        tag = "E1_B_r1_2.74_rs%g" % rs
        jobs.append(("E1", tag, LAD_B, rs, None, False, "gear20n"))

    # ---- E2 C9 修复后：R1=6.8 Rs 扫描 ----
    for rs in (0, 50e3, 100e3, 220e3, 300e3, 600e3):
        tag = "E2_B68_rs%g" % rs
        jobs.append(("E2", tag, LAD_B68, rs, None, False, "gear20n"))

    # ---- E2b 第 4 轮冻结候选 ----
    for rs in (0, 100e3, 220e3, 600e3):
        tag = "E2b_FIN_rs%g" % rs
        jobs.append(("E2b", tag, LAD_FIN, rs, None, False, "gear20n"))

    # ---- E3 数值收敛：E1@100k 四组设置 ----
    for opts in OPTS:
        tag = "E3_B_r1_2.74_rs100000_%s" % opts
        jobs.append(("E3", tag, LAD_B, 100e3, None, False, opts))

    # ---- E4 输入电容置零（同一 Rs=100k）----
    lib0 = make_zero_cin_lib()
    for opts in ("gear20n", "trap40n"):
        tag = "E4_noCin_rs100000_%s" % opts
        jobs.append(("E4", tag, LAD_B, 100e3, lib0, False, opts))
    for rs in (0, 220e3, 600e3):
        tag = "E4_noCin_rs%g" % rs
        jobs.append(("E4", tag, LAD_B, rs, lib0, False, "gear20n"))

    # ---- E5 理想跟随器（无源网络单独）----
    for rs in (0, 100e3, 600e3):
        tag = "E5_ideal_rs%g" % rs
        jobs.append(("E5", tag, LAD_B, rs, None, True, "gear20n"))

    n_ok = 0
    for exp, tag, lad, rs, inc, ideal, opts in jobs:
        net = os.path.join(WD, tag + ".net")
        txt = netlist(lad["r1"], lad["r2"], lad["r3"], lad["c1"], lad["c2"], lad["c3"],
                      lad["cd"], rs, include=inc or LIB, ideal_follower=ideal,
                      opts=opts, tag=tag)
        open(net, "w", encoding="ascii", newline="\n").write(txt)
        ok, msg = run(net)
        raw = os.path.join(WD, tag + ".raw")
        row = {"rs_ohm": rs, "opts": opts, "ideal_follower": ideal,
               "include": "noCin" if inc else "lib", "ran": bool(ok and os.path.exists(raw))}
        if row["ran"]:
            try:
                row.update(analyze_tran(raw))
                n_ok += 1
            except Exception as e:      # noqa: BLE001
                row["error"] = repr(e)
        else:
            row["error"] = msg
        res["experiments"].setdefault(exp, {})[tag] = row
        print("%-6s %-38s %s" % (exp, tag,
              ("pp=%9.1f uV  f=%6.1f kHz  tset=%8.1f us  %s" %
               (row.get("tail_pp_uv", -1), row.get("f_osc_khz", -1),
                row.get("t_settle_us", -1), "STABLE" if row.get("stable") else "LIMIT"))
              if row["ran"] else "FAILED " + str(row.get("error"))[:80]))

    # ---- E6 小信号 AC ----
    print("\n--- E6 小信号 AC（线性口径：跟随器节点峰 / 引脚峰）---")
    for rs in (0, 50e3, 100e3, 220e3, 600e3):
        tag = "E6_AC_rs%g" % rs
        net = os.path.join(WD, tag + ".net")
        open(net, "w", encoding="ascii", newline="\n").write(
            ac_netlist(LAD_B["r1"], LAD_B["r2"], LAD_B["r3"], LAD_B["c1"], LAD_B["c2"],
                       LAD_B["c3"], LAD_B["cd"], rs, tag=tag))
        ok, msg = run(net)
        raw = os.path.join(WD, tag + ".raw")
        if ok and os.path.exists(raw):
            row = analyze_ac(raw)
            row["ran"] = True
            res["experiments"].setdefault("E6", {})[tag] = row
            print("  Rs=%8.0f  follower_peak=%6.2f dB @%7.1f kHz   pin_peak=%6.2f dB @%7.1f kHz"
                  % (rs, row["foll_peak_db"], row["foll_peak_khz"],
                     row["pin_peak_db"], row["pin_peak_khz"]))
        else:
            res["experiments"].setdefault("E6", {})[tag] = {"ran": False, "error": msg}
            print("  Rs=%8.0f  FAILED" % rs)

    res["n_ok"] = n_ok
    res["n_jobs"] = len(jobs)
    out = os.path.join(HERE, "r5_d5_mech_r4.json")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=2)
    print("\n已写出 %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
