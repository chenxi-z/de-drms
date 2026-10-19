# -*- coding: utf-8 -*-
"""r5_mech_limitcycle2.py — D5 中间阻抗极限环：决定性判别实验（第 4 轮补）

第 1 轮判别（r5_mech_limitcycle.py）已得到：
  E2   R1=6.8 Ω 后 0–600 kΩ 全范围回稳 → 极限环与 C9 同源（首级 R↔阶梯电容的有源谐振）
  E3   gear20n 与 trap40n 两法给出同一幅度（498.9 / 498.8 mV）→ 不是积分方法伪影
  E4   把模型输入电容 C_C_DIFF/C_C_COM0/1 置 1 fF 后，100 kΩ 极限环**消失**
  E5   跟随器换成理想 VCVS 后全 Rs 稳定 → 无源阶梯本身无失稳
  E6   小信号 AC 在 Rs=50k–220k 出现跟随器节点 +15.9…+20.3 dB / 引脚 +2.6…+7.4 dB 的峰

本脚本再做三项**决定性**判别：
  F1 自治性：输入保持 DC（无阶跃）——若仍自振 = 真·不稳定平衡点；若安静 = 边沿触发的非线性极限环
  F2 数值收敛：缩短窗（150 µs）+ 更紧的 reltol/maxstep（gear 5n/2n、trap 5n），看幅度是否随步长变化
  F3 边沿形状：把 10 ns PULSE 换成 RC 平滑过的 PWL（等效 100 ns / 1 µs 有限斜率），看是否仍触发
  F4 停止点：把 OPA388 换成本地副本，仅把 CLAW/CL 限幅块（G_G12/G_G13/G_G39）增益降 10×，
     看极限环是否消失 —— 定位到宏模型的具体非线性块
"""
from __future__ import annotations

import json
import math
import os
import subprocess
import sys

import numpy as np

import r5_mech_limitcycle as M

HERE = os.path.dirname(os.path.abspath(__file__))
WD = M.WD
LTSPICE = M.LTSPICE
LIB = M.LIB

B = M.LAD_B


def build(tag, rs=100e3, *, src="step", amp=2.0, edge="10n", opts="gear20n",
          include=None, sweep=None):
    """src: 'step' 阶跃 / 'dc' 纯直流 / 'smooth' 平滑边沿"""
    inc = include or LIB
    L = [f"* {tag}", f".include {inc}", "Vcc vcc 0 DC 3.3", "Vee vee 0 DC 0"]
    if src == "dc":
        L += [f"Vp vp 0 DC {2 + amp / 2}", f"Vn vn 0 DC {2 - amp / 2}"]
    elif src == "smooth":
        # PWL：0→10 µs 保持 2±amp/2，用 40 段线性段近似 1 µs 指数沿
        n = 40
        t0, tau = 10e-6, 1e-6 / 3.0
        pts_p = ["0 2"]
        pts_n = ["0 2"]
        for k in range(1, n + 1):
            tk = t0 + tau * 3.0 * k / n
            frac = 1 - math.exp(-3.0 * k / n)
            pts_p.append(f"{tk*1e6:.6f}u {2 + amp/2*frac:.9f}")
            pts_n.append(f"{tk*1e6:.6f}u {2 - amp/2*frac:.9f}")
        pts_p.append("900u %g" % (2 + amp / 2))
        pts_n.append("900u %g" % (2 - amp / 2))
        L += ["Vp vp 0 PWL(" + " ".join(pts_p) + ")",
              "Vn vn 0 PWL(" + " ".join(pts_n) + ")"]
    else:
        L += [f"Vp vp 0 PULSE(2 {2+amp/2} 10u {edge} {edge} 500u 2m)",
              f"Vn vn 0 PULSE(2 {2-amp/2} 10u {edge} {edge} 500u 2m)"]
    if rs > 0:
        L += [f"Rsa vp fa {rs:.6g}", f"Rsb vn fb {rs:.6g}"]
        fa, fb = "fa", "fb"
    else:
        fa, fb = "vp", "vn"
    L += [f"Xfa {fa} fpa vcc vee fpa OPAx388", f"Xfb {fb} fna vcc vee fna OPAx388",
          f"Ra1 fpa pa1 {B['r1']:.6g}", f"Ca1 pa1 0 {B['c1']:.6g}",
          f"Ra2 pa1 pa2 {B['r2']:.6g}", f"Ca2 pa2 0 {B['c2']:.6g}",
          f"Ra3 pa2 pa3 {B['r3']:.6g}", f"Ca3 pa3 0 {B['c3']:.6g}",
          f"Rb1 fna na1 {B['r1']:.6g}", f"Cb1 na1 0 {B['c1']:.6g}",
          f"Rb2 na1 na2 {B['r2']:.6g}", f"Cb2 na2 0 {B['c2']:.6g}",
          f"Rb3 na2 na3 {B['r3']:.6g}", f"Cb3 na3 0 {B['c3']:.6g}",
          f"Cd pa3 na3 {B['cd']:.6g}", "Rin pa3 na3 130000",
          "Cpa pa3 0 5e-12", "Cna na3 0 5e-12"]
    L += [M.OPTS.get(opts, M.OPTS["gear20n"]) if opts in M.OPTS else opts,
          ".save V(pa3) V(na3) V(fpa) V(fna)", ".end", ""]
    return "\n".join(L)


def run(tag, txt, timeout=380):
    p = os.path.join(WD, tag + ".net")
    open(p, "w", encoding="ascii", newline="\n").write(txt)
    try:
        r = subprocess.run([LTSPICE, "-b", "-ascii", p], capture_output=True,
                           timeout=timeout)
        ok = r.returncode == 0
    except subprocess.TimeoutExpired:
        return None, "TIMEOUT"
    raw = os.path.join(WD, tag + ".raw")
    if not (ok and os.path.exists(raw)):
        return None, "FAIL"
    c, n = M.parse_raw(raw)
    t = np.asarray(c[n[0]], float)
    d = np.asarray(c["V(pa3)"]) - np.asarray(c["V(na3)"])
    fp = np.asarray(c["V(fpa)"])
    fn = np.asarray(c["V(fna)"])
    m = t >= 0.75 * t[-1]
    s = np.where(np.diff(np.signbit(np.diff(d[m]))))[0]
    per = float(np.median(np.diff(t[m][s]))) if len(s) > 4 else 0.0
    vss = float(np.median(d[m]))
    band = 200e-6
    out = np.where(np.abs(d - vss) > band)[0]
    return {"tail_pp_uv": float((d[m].max() - d[m].min()) * 1e6),
            "f_khz": (1.0 / per / 1e3 if per > 0 else 0.0),
            "fna_pp_mv": float((fn[m].max() - fn[m].min()) * 1e3),
            "fpa_pp_mv": float((fp[m].max() - fp[m].min()) * 1e3),
            "vss": vss,
            "tset_us": float(t[out[-1]] * 1e6) if len(out) else 0.0,
            "t_end_us": float(t[-1] * 1e6),
            "stable": bool((d[m].max() - d[m].min()) * 1e6 <= 200.0)}, "ok"


def make_claw_weak():
    """本地副本：CLAW/CL 限幅块的 VCC/CLAMP 参考电压降 10×，检验该块是否为振荡源。"""
    src = open(LIB, "r", encoding="ascii", errors="replace").read().splitlines()
    out = []
    for ln in src:
        s = ln.strip()
        if s.startswith(("V_V_ORN", "V_V_ORP", "V_V_GRN", "V_V_GRP")):
            parts = ln.split()
            parts[-1] = "%g" % (float(parts[-1]) / 10.0)
            ln = " ".join(parts)
        out.append(ln)
    path = os.path.join(WD, "OPAx388_weakclaw.LIB")
    open(path, "w", encoding="ascii", newline="\n").write("\n".join(out))
    return path


def main():
    os.makedirs(WD, exist_ok=True)
    res = {}

    print("=== F1 自治性：输入纯 DC（无阶跃），Rs=100 kΩ ===")
    for src in ("dc", "step"):
        r, st = run("F1_%s" % src, build("F1_%s" % src, src=src))
        res["F1_" + src] = r or {"error": st}
        print("  %-6s %s" % (src, ("diff pp=%9.1f uV  fna=%7.1f mV  %s" %
                                  (r["tail_pp_uv"], r["fna_pp_mv"],
                                   "OSC" if not r["stable"] else "quiet")) if r else st))

    print("\n=== F2 数值收敛：同一工况、不同 reltol/maxstep（窗 150 µs）===")
    for opts_name, opts in (
            ("gear20n", ".options plotwinsize=0 method=gear reltol=1e-5 abstol=1e-11 vntol=1e-8 chgtol=1e-14 trtol=7\n.tran 0 150u 0 20n"),
            ("gear5n", ".options plotwinsize=0 method=gear reltol=1e-6 abstol=1e-12 vntol=1e-9 chgtol=1e-15 trtol=3\n.tran 0 150u 0 5n"),
            ("trap5n", ".options plotwinsize=0 method=trap reltol=1e-6 abstol=1e-12 vntol=1e-9 chgtol=1e-15 trtol=3\n.tran 0 150u 0 5n"),
            ("gear2n", ".options plotwinsize=0 method=gear reltol=1e-7 abstol=1e-13 vntol=1e-10 chgtol=1e-16 trtol=2\n.tran 0 150u 0 2n"),
    ):
        r, st = run("F2_" + opts_name, build("F2_" + opts_name, opts=opts_name))
        res["F2_" + opts_name] = r or {"error": st}
        print("  %-8s %s" % (opts_name, ("pp=%9.1f uV  fna=%7.1f mV  f=%6.1f kHz" %
                                        (r["tail_pp_uv"], r["fna_pp_mv"], r["f_khz"]))
                             if r else "FAILED " + st[:40]))

    print("\n=== F3 边沿形状（等效斜率）@Rs=100 kΩ ===")
    for lab, kw in (("step_10ns", dict(src="step", edge="10n")),
                    ("step_1us", dict(src="step", edge="1u")),
                    ("smooth_exp1us", dict(src="smooth")),
                    ("step_10us", dict(src="step", edge="10u"))):
        r, st = run("F3_" + lab, build("F3_" + lab, **kw))
        res["F3_" + lab] = r or {"error": st}
        print("  %-14s %s" % (lab, ("pp=%9.1f uV  %s" %
                                    (r["tail_pp_uv"], "OSC" if not r["stable"] else "settled"))
                              if r else "FAILED " + st[:40]))

    print("\n=== F4 宏模型非线性块定位（CLAW/CL 限幅参考降 10×）===")
    lib2 = make_claw_weak()
    r, st = run("F4_weakclaw", build("F4_weakclaw", include=lib2))
    res["F4_weakclaw"] = r or {"error": st}
    print("  weakclaw  %s" % (("pp=%9.1f uV  %s" % (r["tail_pp_uv"],
                              "OSC" if not r["stable"] else "settled")) if r else "FAILED " + st[:60]))

    out = os.path.join(HERE, "r5_d5_mech2_r4.json")
    json.dump(res, open(out, "w", encoding="utf-8", newline="\n"),
              ensure_ascii=False, indent=2, default=float)
    print("\n已写出 %s" % out)


if __name__ == "__main__":
    sys.exit(main())
