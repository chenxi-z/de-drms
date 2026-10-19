#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_netlists_r5_r4.py — R5 第 4 轮：方案 B 定档基线（C9 修复参数）的 LTspice 网表

参数来源：`r5_candidates_final_B.json`（"grade": "B"）
    stages = [(6.19, 68n, 0), (6.04, 68n, 0), (13.7, 27n, 12n)]

相对第 3 轮（gen_netlists_r5_r3.py / gen_netlists_r3_B.py）的改动
------------------------------------------------------------
1. **全部 V1–V9 主口径 = 真实 OPA388 模型**（规格 v4 §5「评分主口径」）。
   0 Ω 理想源只保留四个最便宜的对照网表（v1i/v2i/v4i/v7i），用于规格 §8 的
   「纯无源理论 ↔ 理想源 LTspice」同口径对拍。
2. **D5 源阻抗五档**：10k/50k/100k/220k/600k Ω（覆盖设计量程 10–120 kΩ 与
   1% 可用范围到 600 kΩ），全部在 R×1.01 / C×1.05 最坏角下。
   每档配 **两套独立数值设置**（gear20n 主口径 / trap20n 复核），
   100k 与 220k 额外加 gear5n —— 用来区分「真实不稳定」与「数值伪影」。
3. **C9 双节点**：AC DM 网表同时 `.save V(fpa) V(fna)`（跟随器输出，考核节点）
   与引脚 V(pa3)/V(na3)（ADC 引脚口径）。
4. **D8 按 R·C 乘积异向配对，1% 档为主**（规格正文 §5.1a），另出 0.1%/0.5%
   与同向 1% 对照。
5. D6a 用 v9d（真实阶梯）vs v9d_nl（阶梯电阻全 `noiseless`），两者传函逐点相同。

文件命名：`r5_B_r4_<tag>.net`，输出目录 `r5_work/r4_B/`（不覆盖第 3 轮任何文件）。

用法
----
    python gen_netlists_r5_r4.py                 # 写全部网表
    python gen_netlists_r5_r4.py --cand B        # 指定键（默认 B）
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import gen_netlists_r5 as G          # noqa: E402  mc_samples（同种子同分布）

FMOD = 4.096e6
VCC = 3.3
CPIN = 5e-12          # 引擎的引脚对地电容
RLOAD = 130e3         # M3：ADS131A02 差分输入阻抗
ADC_CS_PF = 3.5       # M2 采样电容
VCM_DC = 2.0

LIB = os.path.join(HERE, "lib", "OPAx388.LIB")

# AC 求解精度
TOPT = (".options plotwinsize=0 reltol=1e-6 abstol=1e-12 vntol=1e-9 "
        "chgtol=1e-15 trtol=1")

# 真实模型瞬态：TI 宏模型内部 1 F 电容会咬步长，gear + 宽松容差是第 2/3 轮
# 已验证稳定的档（2 V 阶跃 × reltol 1e-5 = 20 µV ≪ 200 µV 判据带）。
TR_GEAR20 = (".options plotwinsize=0 method=gear reltol=1e-5 abstol=1e-11 "
             "vntol=1e-8 chgtol=1e-14 trtol=7")
TR_TRAP20 = (".options plotwinsize=0 method=trap reltol=1e-5 abstol=1e-11 "
             "vntol=1e-8 chgtol=1e-14 trtol=3")
TR_GEAR5 = (".options plotwinsize=0 method=gear reltol=1e-6 abstol=1e-12 "
            "vntol=1e-9 chgtol=1e-15 trtol=3")

# D5 源阻抗五档（Ω）
D5_RS = (10e3, 50e3, 100e3, 220e3, 600e3)

D8_M = (0.001, 0.005, 0.01)


def _fmt(x):
    return f"{x:.10g}"


def _hdr(tag, note):
    return [f"* r5 B r4 {tag} - {note}",
            "* gen_netlists_r5_r4.py (spec v4; real OPA388 = scoring source)"]


def _opa_head():
    return [f".include {LIB}", f"Vcc vcc 0 DC {VCC}", "Vee vee 0 DC 0"]


def _line(side, src, node, stages, noiseless=False):
    """src — R1 — n1(C1) — R2 — n2(C2) — … — R_N — nN。"""
    nl = " noiseless" if noiseless else ""
    out, prev = [], src
    for i, (r, cg, _cd) in enumerate(stages, 1):
        out.append(f"R{side}{i} {prev} {node}{i} {_fmt(r)}{nl}")
        out.append(f"C{side}{i} {node}{i} 0 {_fmt(cg)}")
        prev = f"{node}{i}"
    return out


def _common(stages, a="pa", b="na", noiseless=False):
    n = len(stages)
    cd = stages[-1][2]
    nl = " noiseless" if noiseless else ""
    out = []
    if cd > 0:
        out.append(f"Cd {a}{n} {b}{n} {_fmt(cd)}")
    out.append(f"Rin {a}{n} {b}{n} {_fmt(RLOAD)}{nl}")
    out.append(f"Cpa {a}{n} 0 {_fmt(CPIN)}")
    out.append(f"Cna {b}{n} 0 {_fmt(CPIN)}")
    return out


def _scale(stages, kr, kc):
    """逐线缩放：R×kr、C_gnd×kc；C_diff 是跨接两线的共享件，**不参与逐线配对**。"""
    return [(float(r) * kr, float(cg) * kc, float(cd)) for r, cg, cd in stages]


def _save(n, extra=""):
    return [f".save V(pa{n}) V(na{n}) {extra}".strip()]


def _foll(a="fpa", b="fna"):
    return f"V({a}) V({b})"


# ================================================================== V1/V2
def gen_v1(cand, tag="v1", note="real OPA388, AC DM full band (D1/D3/D4/D10/C9)"):
    st = cand["stages"]
    n = len(st)
    L = _hdr(tag, note) + _opa_head()
    L += ["Vp vp 0 DC 2 AC 0.5", "Vn vn 0 DC 2 AC -0.5",
          "Xfa vp fpa vcc vee fpa OPAx388", "Xfb vn fna vcc vee fna OPAx388"]
    L += _line("a", "fpa", "pa", st) + _line("b", "fna", "na", st) + _common(st)
    L += [".ac dec 400 0.1 200Meg", TOPT, *_save(n, _foll()), ".end"]
    return "\n".join(L) + "\n"


def gen_v2(cand, tag="v2", note="real OPA388, AC CM full band (D2)"):
    st = cand["stages"]
    n = len(st)
    L = _hdr(tag, note) + _opa_head()
    L += ["Vp vp 0 DC 2 AC 1", "Vn vn 0 DC 2 AC 1",
          "Xfa vp fpa vcc vee fpa OPAx388", "Xfb vn fna vcc vee fna OPAx388"]
    L += _line("a", "fpa", "pa", st) + _line("b", "fna", "na", st) + _common(st)
    L += [".ac dec 400 0.1 200Meg", TOPT, *_save(n, _foll()), ".end"]
    return "\n".join(L) + "\n"


# ================================================================== V3（D8）
def gen_v3(cand, tag, m, mode="paired", note=""):
    """失配 AC 共模。mode='paired'：R×(1+m) 配 C×(1−m)；'same'：R/C 同 ×(1+m)。"""
    st = cand["stages"]
    n = len(st)
    if mode == "paired":
        stb = _scale(st, 1 + m, 1 - m)
        note = note or f"real OPA388, CM mismatch R*C PAIRED m={m*100:g}% (D8)"
    else:
        stb = _scale(st, 1 + m, 1 + m)
        note = note or f"real OPA388, CM mismatch SAME-direction m={m*100:g}% (control)"
    L = _hdr(tag, note) + _opa_head()
    L += ["Vp vp 0 DC 2 AC 1", "Vn vn 0 DC 2 AC 1",
          "Xfa vp fpa vcc vee fpa OPAx388", "Xfb vn fna vcc vee fna OPAx388"]
    L += _line("a", "fpa", "pa", st) + _line("b", "fna", "na", stb) + _common(st)
    L += [".ac dec 200 0.1 100k", TOPT, *_save(n), ".end"]
    return "\n".join(L) + "\n"


# ================================================================== V4（D5 0Ω）
def _step_src(edge="10n", pw="600u", per="2m", amp=1.0, hi=3.0, lo=1.0):
    return [f"Vp vp 0 PULSE(2 {hi} 10u {edge} {edge} {pw} {per})",
            f"Vn vn 0 PULSE(2 {lo} 10u {edge} {edge} {pw} {per})"]


def gen_v4(cand, tag="v4", note="real OPA388, worst corner, 0ohm source (D5, 0ohm)"):
    st = _scale(cand["stages"], 1.01, 1.05)
    n = len(st)
    L = _hdr(tag, note) + _opa_head()
    L += _step_src()
    L += ["Xfa vp fpa vcc vee fpa OPAx388", "Xfb vn fna vcc vee fna OPAx388"]
    L += _line("a", "fpa", "pa", st) + _line("b", "fna", "na", st) + _common(st)
    L += _save(n, _foll()) + [".tran 0 400u 0 20n", TR_GEAR20, ".end"]
    return "\n".join(L) + "\n"


# ================================================================== V9f（D5 源阻抗扫描）
def gen_v9f(cand, rs, tag, note, opts="gear20n", corner=True, tstop="400u",
            maxstep="20n"):
    st = _scale(cand["stages"], 1.01, 1.05) if corner else cand["stages"]
    n = len(st)
    L = _hdr(tag, note) + _opa_head()
    L += _step_src()
    if rs > 0:
        L += [f"Rsa vp fa {_fmt(rs)}", f"Rsb vn fb {_fmt(rs)}"]
        fa, fb = "fa", "fb"
    else:
        fa, fb = "vp", "vn"
    L += [f"Xfa {fa} fpa vcc vee fpa OPAx388", f"Xfb {fb} fna vcc vee fna OPAx388"]
    L += _line("a", "fpa", "pa", st) + _line("b", "fna", "na", st) + _common(st)
    o = {"gear20n": TR_GEAR20, "trap20n": TR_TRAP20, "gear5n": TR_GEAR5}[opts]
    L += _save(n, "V(fa) V(fb) " + _foll())
    L += [f".tran 0 {tstop} 0 {maxstep}", o, ".end"]
    return "\n".join(L) + "\n"


# ================================================================== V5/V6 蒙特卡洛
def _mc_lines(stages, smp):
    sta, stb = [], []
    n = len(stages)
    for i in range(n):
        r, cg, cd = [float(x) for x in stages[i]]
        kcd = smp["cd"] if i == n - 1 else 1.0
        sta.append((r * smp["ra"][i], cg * smp["ca"][i], cd * kcd))
        stb.append((r * smp["rb"][i], cg * smp["cb"][i], cd * kcd))
    return sta, stb


def gen_v5(cand, k, smp, tag):
    st = cand["stages"]
    n = len(st)
    sta, stb = _mc_lines(st, smp)
    L = _hdr(tag, f"MC AC DM #{k:02d} (D7, real OPA388, R+-1%/C+-5%)") + _opa_head()
    L += ["Vp vp 0 DC 2 AC 0.5", "Vn vn 0 DC 2 AC -0.5",
          "Xfa vp fpa vcc vee fpa OPAx388", "Xfb vn fna vcc vee fna OPAx388"]
    L += _line("a", "fpa", "pa", sta) + _line("b", "fna", "na", stb) + _common(sta)
    L += [".ac dec 100 0.1 100k", TOPT, *_save(n), ".end"]
    return "\n".join(L) + "\n"


def gen_v6(cand, k, smp, tag):
    st = cand["stages"]
    n = len(st)
    sta, stb = _mc_lines(st, smp)
    L = _hdr(tag, f"MC transient #{k:02d} (D5 statistics, real OPA388, corner)") + _opa_head()
    L += _step_src()
    L += ["Xfa vp fpa vcc vee fpa OPAx388", "Xfb vn fna vcc vee fna OPAx388"]
    L += _line("a", "fpa", "pa", sta) + _line("b", "fna", "na", stb) + _common(sta)
    L += _save(n, _foll())
    L += [".tran 0 300u 0 20n", TR_GEAR20, ".end"]
    return "\n".join(L) + "\n"


# ================================================================== 噪声
def gen_noise(cand, tag, note, noiseless=False, obs=None, src_ac=(1, 0)):
    st = cand["stages"]
    n = len(st)
    L = _hdr(tag, note) + _opa_head()
    L += [f"Vp vp 0 DC 2 AC {src_ac[0]}", f"Vn vn 0 DC 2 AC {src_ac[1]}",
          "Xfa vp fpa vcc vee fpa OPAx388", "Xfb vn fna vcc vee fna OPAx388"]
    L += _line("a", "fpa", "pa", st, noiseless=noiseless)
    L += _line("b", "fna", "na", st, noiseless=noiseless)
    L += _common(st, noiseless=noiseless)
    obs = obs or f"V(pa{n},na{n})"
    L += [f".noise {obs} Vp dec 200 0.1 2.048Meg", TOPT, ".end"]
    return "\n".join(L) + "\n"


# ================================================================== kickback
def gen_noise_alone(cand, tag="v9n"):
    """纯跟随器（无阶梯）的差分输出噪声 —— D6a 的分母对照。"""
    L = _hdr(tag, "real OPA388 alone, output noise (D6a reference)") + _opa_head()
    L += ["Vp vp 0 DC 2 AC 1", "Vn vn 0 DC 2 AC 0",
          "Xfa vp fpa vcc vee fpa OPAx388", "Xfb vn fna vcc vee fna OPAx388"]
    L += [".noise V(fpa,fna) Vp dec 200 0.1 2.048Meg", TOPT, ".end"]
    return "\n".join(L) + "\n"
def gen_kickback(cand, ron=1.0, tag=None, vp=2.6, vn=1.4, tstop="40u", maxstep="0.5n"):
    st = cand["stages"]
    n = len(st)
    tag = tag or f"v8r_ron{ron:g}"
    L = _hdr(tag, "kickback, real OPA388 follower + ADC sampling switch (D9)")
    L += [f".model SWK SW(Ron={_fmt(ron)} Roff=1e12 Vt=0.5 Vh=0)"] + _opa_head()
    L += [f"Vp vp 0 DC {vp}", f"Vn vn 0 DC {vn}",
          "Xfa vp fpa vcc vee fpa OPAx388", "Xfb vn fna vcc vee fna OPAx388"]
    L += _line("a", "fpa", "pa", st) + _line("b", "fna", "na", st)
    L += _common(st)
    L += ["Vcm vcm 0 DC 2.0"]
    pin_a, pin_b = f"pa{n}", f"na{n}"
    L += [f"S1a {pin_a} csa swp 0 SWK", f"Csa csa vcm {_fmt(ADC_CS_PF/2*1e-12)}",
          "S2a csa vcm swn 0 SWK",
          f"S1b {pin_b} csb swn 0 SWK", f"Csb csb vcm {_fmt(ADC_CS_PF/2*1e-12)}",
          "S2b csb vcm swp 0 SWK",
          "Vswp swp 0 PULSE(0 1 0 0.5n 0.5n 121.07n 244.1406n)",
          "Vswn swn 0 PULSE(0 1 122.07n 0.5n 0.5n 121.07n 244.1406n)"]
    L += _save(n, "V(csa) V(csb) " + _foll())
    L += [f".tran 0 {tstop} 0 {maxstep}", TR_GEAR20, ".end"]
    return "\n".join(L) + "\n"


# ================================================================== V9e（AC 随源阻抗）
def gen_ac_rs(cand, rs, tag, note):
    """600 kΩ 级高源阻抗工况的 AC 视角：Rs → 跟随器 → 阶梯。"""
    st = cand["stages"]
    n = len(st)
    L = _hdr(tag, note) + _opa_head()
    L += ["Vp vp 0 DC 2 AC 0.5", "Vn vn 0 DC 2 AC -0.5"]
    if rs > 0:
        L += [f"Rsa vp fa {_fmt(rs)}", f"Rsb vn fb {_fmt(rs)}"]
        fa, fb = "fa", "fb"
    else:
        fa, fb = "vp", "vn"
    L += [f"Xfa {fa} fpa vcc vee fpa OPAx388", f"Xfb {fb} fna vcc vee fna OPAx388"]
    L += _line("a", "fpa", "pa", st) + _line("b", "fna", "na", st) + _common(st)
    L += [".ac dec 1000 0.1 20Meg", TOPT,
          *_save(n, "V(fa) V(fb) " + _foll()), ".end"]
    return "\n".join(L) + "\n"


# ================================================================== V1 温度角
def gen_v1_temp(cand, temp, tag):
    """规格 §5.1：温度角只报通带相关项（D4/D7 趋势）。

    C0G 的 −30 ppm/°C 显式折进容值（LTspice 电容缺省 TC1=0）。
    电阻温漂**未代入**：BOM 未定型（E.10 #6 由用户核实）——报告须明示该假设。
    """
    st = cand["stages"]
    n = len(st)
    kc = 1.0 + (-30e-6) * (temp - 25.0)
    stx = _scale(st, 1.0, kc)
    L = _hdr(tag, f"real OPA388, AC DM at {temp:+.0f} degC (D4/D10 trend)") + _opa_head()
    L += ["* resistor tempco NOT applied: BOM not frozen (E.10 #6 owned by user)"]
    L += [f".temp {temp:g}",
          "Vp vp 0 DC 2 AC 0.5", "Vn vn 0 DC 2 AC -0.5",
          "Xfa vp fpa vcc vee fpa OPAx388", "Xfb vn fna vcc vee fna OPAx388"]
    L += _line("a", "fpa", "pa", stx) + _line("b", "fna", "na", stx) + _common(stx)
    L += [".ac dec 400 0.1 200Meg", TOPT, *_save(n, _foll()), ".end"]
    return "\n".join(L) + "\n"


# ================================================================== 理想源对照
def gen_v1i(cand, tag="v1i"):
    st = cand["stages"]
    n = len(st)
    L = _hdr(tag, "ideal 0ohm source, AC DM (control for spec sec8 A-block)")
    L += ["Vp vp 0 DC 2 AC 0.5", "Vn vn 0 DC 2 AC -0.5"]
    L += _line("a", "vp", "pa", st) + _line("b", "vn", "na", st) + _common(st)
    L += [".ac dec 400 0.1 200Meg", TOPT, *_save(n), ".end"]
    return "\n".join(L) + "\n"


def gen_v2i(cand, tag="v2i"):
    st = cand["stages"]
    n = len(st)
    L = _hdr(tag, "ideal 0ohm source, AC CM (control)")
    L += ["Vp vp 0 DC 2 AC 1", "Vn vn 0 DC 2 AC 1"]
    L += _line("a", "vp", "pa", st) + _line("b", "vn", "na", st) + _common(st)
    L += [".ac dec 400 0.1 200Meg", TOPT, *_save(n), ".end"]
    return "\n".join(L) + "\n"


def gen_v4i(cand, tag="v4i"):
    st = _scale(cand["stages"], 1.01, 1.05)
    n = len(st)
    L = _hdr(tag, "ideal 0ohm source, worst-corner transient (control for settle)")
    L += ["Vp vp 0 PULSE(0 1 10u 10n 10n 600u 2m)",
          "Vn vn 0 PULSE(0 -1 10u 10n 10n 600u 2m)"]
    L += _line("a", "vp", "pa", st) + _line("b", "vn", "na", st) + _common(st)
    L += _save(n) + [".tran 0 500u 0 10n", TOPT, ".end"]
    return "\n".join(L) + "\n"


def gen_v7i(cand, tag="v7i"):
    st = cand["stages"]
    n = len(st)
    L = _hdr(tag, "ideal 0ohm source, output noise (control for spec sec8)")
    L += ["Vp vp 0 DC 2 AC 1", "Vn vn 0 DC 2 AC 0"]
    L += _line("a", "vp", "pa", st) + _line("b", "vn", "na", st) + _common(st)
    L += [f".noise V(pa{n},na{n}) Vp dec 200 0.1 2.048Meg", TOPT, ".end"]
    return "\n".join(L) + "\n"


# ================================================================== 生成全部
def generate(cand, outdir):
    os.makedirs(outdir, exist_ok=True)
    files = []
    ns = len(cand["stages"])

    def w(name, text):
        with open(os.path.join(outdir, name), "w", encoding="ascii", newline="\n") as fh:
            fh.write(text)
        files.append(name)

    # ---- 主口径：真实 OPA388 ----
    w("r5_B_r4_v1.net", gen_v1(cand))
    w("r5_B_r4_v2.net", gen_v2(cand))
    for m in D8_M:
        w(f"r5_B_r4_v3p{int(m*1000):03d}.net",
          gen_v3(cand, f"v3p{int(m*1000):03d}", m, "paired"))
    w("r5_B_r4_v3s010.net",
      gen_v3(cand, "v3s010", 0.01, "same"))
    w("r5_B_r4_v4.net", gen_v4(cand))
    for k, smp in enumerate(G.mc_samples(n=G.N_MC, n_stage=ns), 1):
        w(f"r5_B_r4_v5mc{k:02d}.net", gen_v5(cand, k, smp, f"v5mc{k:02d}"))
        w(f"r5_B_r4_v6mc{k:02d}.net", gen_v6(cand, k, smp, f"v6mc{k:02d}"))
    w("r5_B_r4_v9d.net", gen_noise(
        cand, "v9d", "real OPA388, noise with real ladder (D6a numerator / D6b)"))
    w("r5_B_r4_v9d_nl.net", gen_noise(
        cand, "v9d_nl", "real OPA388, ladder R all noiseless (D6a denominator)",
        noiseless=True))
    w("r5_B_r4_v9n.net", gen_noise_alone(cand))
    for ron in (1.0, 100.0, 1000.0):
        w(f"r5_B_r4_v8r_ron{ron:g}.net", gen_kickback(cand, ron))

    # ---- D5 源阻抗五档：主口径 gear20n（400 µs 窗）+ 两套独立数值复核 ----
    # 复核组用 150 µs 窗：本轮实测 trap 在 400 µs 窗 + TI 宏模型下会写入数百 MB 的
    # .raw 并超时（见 r5_work/r4_B/CHK_* 的 .log 证据），缩短窗即可完成且
    # 覆盖全部建立过程（各档 tset 27–31 µs）。
    for rs in D5_RS:
        k = int(rs / 1e3)
        w(f"r5_B_r4_v9f_s{k:03d}k.net", gen_v9f(
            cand, rs, f"v9f_s{k:03d}k",
            f"real OPA388, Rs={k}k, worst corner (D5 source sweep, gear20n 400us)"))
        w(f"r5_B_r4_v9f_s{k:03d}k_trap.net", gen_v9f(
            cand, rs, f"v9f_s{k:03d}k_trap",
            f"real OPA388, Rs={k}k, worst corner, TRAP reltol 1e-4, 60us (numeric check)",
            opts="trap20n", tstop="60u"))
        w(f"r5_B_r4_v9f_s{k:03d}k_gear5n.net", gen_v9f(
            cand, rs, f"v9f_s{k:03d}k_gear5n",
            f"real OPA388, Rs={k}k, worst corner, GEAR reltol 1e-6 maxstep 5ns, 150us",
            opts="gear5n", tstop="150u", maxstep="5n"))

    # ---- AC 随源阻抗（C9 与 D4 在高阻端的补充口径）----
    for rs in (0,) + D5_RS:
        k = int(rs / 1e3)
        w(f"r5_B_r4_v9e_s{k:03d}k.net", gen_ac_rs(
            cand, rs, f"v9e_s{k:03d}k",
            f"real OPA388, AC DM with Rs={k}k sample-side (C9/D4 vs source)"))

    # ---- 温度角（规格 §5.1：只报 D4/D10 趋势）----
    for t in (-20, 85):
        w(f"r5_B_r4_v1t{t:+d}C.net", gen_v1_temp(cand, t, f"v1t{t:+d}C"))

    # ---- 0 Ω 理想源对照（规格 §8 的 A 块）----
    w("r5_B_r4_v1i.net", gen_v1i(cand))
    w("r5_B_r4_v2i.net", gen_v2i(cand))
    w("r5_B_r4_v4i.net", gen_v4i(cand))
    w("r5_B_r4_v7i.net", gen_v7i(cand))
    return files


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--cand", default="B")
    ap.add_argument("--file", default="r5_candidates_final_B.json")
    ap.add_argument("--outdir", default=os.path.join(HERE, "r5_work", "r4_B"))
    args = ap.parse_args(argv)
    with open(os.path.join(HERE, args.file), encoding="utf-8") as fh:
        cand = json.load(fh)
    if "stages" not in cand:                 # 兼容 {A/B/C: {...}} 结构
        cand = cand[args.cand]
    cand = {"stages": [tuple(map(float, s)) for s in cand["stages"]]}
    files = generate(cand, args.outdir)
    print(f"scheme {args.cand}: {len(files)} netlists -> {args.outdir}")
    for f in files:
        print("  ", f)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
