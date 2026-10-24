#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tran_tests.py — fo1_rc_review 瞬态族台架（T04 建立时间 / T08 ADC kickback / T09 高频耦合折叠）

任务书 §4（hardware/sim/Zcode_LTspice_一阶RC四方案复核任务书.md:148-153）+
本轮分工（仿真·tran）。铁律：真实接线 = 3 颗 OPA388 + AIN1N 经 RC 直连 Rsense 底端
（Kelvin 地，无第四运放）——CH1 台架按此接线，CH0 台架 = 2 颗跟随器（其真实接线本就如此）。

口径（全部沿用既有家法）：
  * T04 建立：raw 带外最后出带法（parse_r5.settle_us / run_all.tran_settle_from_raw 同口径），
    相对**实际终值**，从阶跃沿结束点起计；0.1%/0.01% 双带。
    角点：标称 / CH1 真实接线 / 容差失配(纯差模) / 容差失配(纯共模阶跃→差模泄漏) /
    600kΩ 高源阻抗(r5 V9f 家法：跟随器输入侧串 600k) / 供电角 ±5%(3.135/3.465 V)。
    CH0 阶跃 = ±0.355 V @CM 2V（t00_tran2 锚定口径，可与 T00 回归 20.85 µs 直接对拍）；
    CH1 阶跃 = 0→1.17857 V（系统真实 V_Rsense = 3.3×200/560，fsrc vset 分压）。
  * T08 kickback：fsadc 开关电容采样模型（M2/M6 口径：每侧 Cs/2=1.75pF，S1/S2 180° 反相 50%，
    fMOD=4.096MHz），r5 V8 家法时钟（PULSE ton=121.07n period=244.1406n）；
    Ron∈{1,100,1000}Ω 扫值（手册无规格 → 声明假设，r5:158/V8 规范）；
    vcm∈{0,0.6,2.0}V（ADC 采样电容复位电位，手册无值 → 声明假设）。
    判据 D9：每半周期(≈122ns)窗末残余 ≤ 稳态值的 0.01%（parse_r5.kickback 同口径）。
  * T09：AC 注入（L2）16 个频点残差 + 瞬态折叠实测（4.096MHz+8k，100mV 注入，
    实时钟采样序列 LSQ 拟合 → L3 sinc³(OSR=32) 离线换算，显式声明非 LTspice 数字内核）。

依赖：~/.local/bin/ltspice-sim、aaf/parse_r5.py、numpy、matplotlib(Agg)。
产物：netlists/t04|t08|t09_*、logs/、raw/、csv/t04_settling.csv / t08_kickback.csv /
t09_ac_residual.csv / t09_fold_check.csv、plots/t04|t08|t09_*。
"""
from __future__ import annotations

import csv
import math
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, "/media/anning/data/Project/DE-DRMS/hardware/sim/aaf")

import run_all  # noqa: E402  (台架基座：run_net / CASES / LIB)
from parse_r5 import Raw, interp_at  # noqa: E402

import matplotlib  # noqa: E402
matplotlib.use("Agg")
matplotlib.rcParams["font.family"] = ["Noto Sans CJK SC", "WenQuanYi Zen Hei", "DejaVu Sans"]
import matplotlib.pyplot as plt  # noqa: E402

NET, LOGD, RAWD, CSVD, PLOTD = (HERE / d for d in ("netlists", "logs", "raw", "csv", "plots"))
for d in (NET, LOGD, RAWD, CSVD, PLOTD):
    d.mkdir(exist_ok=True)

LIB = run_all.LIB
TOPT = ".options plotwinsize=0 reltol=1e-6 abstol=1e-12 vntol=1e-9 chgtol=1e-15 trtol=1"
CASES = run_all.CASES                     # FO1_BASE/A/B/C → r/cg/cd
SID = {"FO1_BASE": "fo1_base", "FO1_A": "fo1_a", "FO1_B": "fo1_b", "FO1_C": "fo1_c"}
VSENSE = 3.3 * 200e3 / 560e3              # 1.178571 V（fsrc vset 分压 → V_Rsense 稳态）
T_MOD = 244.1406e-9                       # r5 V8 时钟周期（网表与提取共用，勿改单侧）
TON = 121.07e-9                           # r5 V8 导通窗（半周期少 1ns 防交叠）
FMOD = 4.096e6
OSR = 32
LSB_V = 2.0 * 2.442 / 2 ** 24             # 290.98 nV（parse_r5 口径）

# fsadckb = fsadc 逐行移植（fo_subs.inc:228-238）+ csa/csb 提升为端口（供 .save 采样序列）
FSADCKB = """* ---- fsadc 移植版：csa/csb 引出为端口（采样序列提取用；器件值与 fs_subs.inc 一致）----
.subckt fsadckb pa na vcm vswp vswn csa csb
Rin  pa  na  130k
Cpa  pa  0   5p
Cna  na  0   5p
S1a  pa  csa vswp 0  swkb
Csa  csa vcm 1.75p
S2a  csa vcm vswn 0  swkb
S1b  na  csb vswn 0  swkb
Csb  csb vcm 1.75p
S2b  csb vcm vswp 0  swkb
.ends fsadckb
"""


def fmt(v: float) -> str:
    return f"{v:.6g}"


# ======================================================================
# 1. T04 网表
# ======================================================================
def ch1_rc(r, cg, cd):
    """CH1 真实接线：B 线跟随器→R→a1p + C_G；E(地)—RKN→na1 + C_GN；C_D 跨引脚；ADC 静态负载。"""
    return (f"Xfb vb fbp vcc vee fbp OPAx388\n"
            f"RKB fbp a1p {fmt(r)}\nCGB a1p 0 {fmt(cg)}\n"
            f"RKN 0 na1 {fmt(r)}\nCGN na1 0 {fmt(cg)}\n"
            f"CD1 a1p na1 {fmt(cd)}\n"
            f"Rin a1p na1 130000\nCpa a1p 0 5e-12\nCna na1 0 5e-12\n")


def t04_net(case, p, scen):
    """CH0 台架（nom/tol/tolcm/vlo/vhi/600k）与 CH1 台架（ch1）。
    CH0 阶跃：P 2→2.355 V、N 2→1.645 V（±0.355V @CM 2V，t00_tran2 锚定口径）；
    tolcm：P/N 同 2→2.355 V（纯共模阶跃）；600k：阶跃经 600k 进跟随器输入（r5 V9f 家法）。"""
    r, cg, cd = p["r"], p["cg"], p["cd"]
    vcc = {"vlo": 3.135, "vhi": 3.465}.get(scen, 3.3)
    if scen == "ch1":
        head = (f"* t04 {SID[case]} ch1 — CH1 真实接线建立（B 0→{VSENSE:.5f}V，AIN1N Kelvin RC 无第四运放）\n"
                f"* 判稳：raw 带外最后出带法，相对实际终值，带 = 0.1%/{VSENSE*1e3:.2f}mV、"
                f"0.01%/{VSENSE*1e6:.1f}µV；阶跃沿 t=10µs/10ns（系统真实 fsrc 使能沿为 µs 级，10ns 属保守口径）\n"
                f".include {LIB}\nVcc vcc 0 DC {vcc}\nVee vee 0 DC 0\n"
                f"Vb vb 0 PULSE(0 {fmt(VSENSE)} 10u 10n 10n 600u 2m)\n")
        body = ch1_rc(r, cg, cd)
        save = ".save V(a1p) V(na1) V(fbp)\n"
        meas = (f".meas TRAN vfin FIND V(a1p,na1) AT=290u\n"
                f".meas TRAN vmax MAX V(a1p,na1) FROM=10u TO=290u\n"
                f".meas TRAN vmin MIN V(a1p,na1) FROM=10u TO=290u\n"
                f".meas TRAN nkick MAX V(na1) FROM=10u TO=290u\n")
        tstop, dt = "300u", "10n"
    else:
        if scen == "600k":
            src = ("Vp vp 0 PULSE(2 2.355 10u 10n 10n 600u 2m)\n"
                   "Vn vn 0 PULSE(2 1.645 10u 10n 10n 600u 2m)\n"
                   "Rsa vp fa 600k\nRsb vn fb 600k\n"
                   "Xfa fa fpa vcc vee fpa OPAx388\nXfb fb fna vcc vee fna OPAx388\n")
        else:
            src = ("Vp vp 0 PULSE(2 2.355 10u 10n 10n 600u 2m)\n"
                   "Vn vn 0 PULSE(2 1.645 10u 10n 10n 600u 2m)\n"
                   "Xfa vp fpa vcc vee fpa OPAx388\nXfb vn fna vcc vee fna OPAx388\n")
        if scen in ("tol", "tolcm"):     # 最坏失配角：P 路 ×1.01/×1.05，N 路 ×0.99/×0.95
            rp, cp_, rn, cn, cdx = r * 1.01, cg * 1.05, r * 0.99, cg * 0.95, cd * 1.05
        elif scen == "600k":             # r5 V9f 家法：对称最坏慢角 ×1.01/×1.05
            rp = cp_ = rn = cn = None
            cdx = cd * 1.05
        else:                            # nom / vlo / vhi 标称
            rp = cp_ = rn = cn = None
            cdx = cd
        if scen == "tolcm":
            src = ("Vp vp 0 PULSE(2 2.355 10u 10n 10n 600u 2m)\n"
                   "Vn vn 0 PULSE(2 2.355 10u 10n 10n 600u 2m)\n"
                   "Xfa vp fpa vcc vee fpa OPAx388\nXfb vn fna vcc vee fna OPAx388\n")
        if scen in ("tol", "tolcm"):
            body = (f"Ra1 fpa pa1 {fmt(rp)}\nCa1 pa1 0 {fmt(cp_)}\n"
                    f"Rb1 fna na1 {fmt(rn)}\nCb1 na1 0 {fmt(cn)}\n")
        elif scen == "600k":
            body = (f"Ra1 fpa pa1 {fmt(r*1.01)}\nCa1 pa1 0 {fmt(cg*1.05)}\n"
                    f"Rb1 fna na1 {fmt(r*1.01)}\nCb1 na1 0 {fmt(cg*1.05)}\n")
        else:
            body = (f"Ra1 fpa pa1 {fmt(r)}\nCa1 pa1 0 {fmt(cg)}\n"
                    f"Rb1 fna na1 {fmt(r)}\nCb1 na1 0 {fmt(cg)}\n")
        body += (f"Cd pa1 na1 {fmt(cdx)}\n"
                 f"Rin pa1 na1 130000\nCpa pa1 0 5e-12\nCna na1 0 5e-12\n")
        tag = {"nom": "CH0 标称（±0.355V@CM2V 差模阶跃）",
               "tol": "CH0 容差失配+差模阶跃（P ×1.01/×1.05，N ×0.99/×0.95，C_D ×1.05）",
               "tolcm": "CH0 容差失配+纯共模阶跃（2→2.355V，测 CM→DM 泄漏建立）",
               "600k": "CH0 600kΩ 高源阻抗（r5 V9f 家法）+ 对称慢角 ×1.01/×1.05",
               "vlo": f"CH0 标称 + 供电角 Vcc={vcc}V（3.3V −5%，声明假设）",
               "vhi": f"CH0 标称 + 供电角 Vcc={vcc}V（3.3V +5%，声明假设）"}[scen]
        head = (f"* t04 {SID[case]} {scen} — {tag}\n"
                f"* 判稳：raw 带外最后出带法，相对实际终值；带 = 0.1%/710µV、0.01%/71µV（0.71V 阶跃）\n"
                f".include {LIB}\nVcc vcc 0 DC {vcc}\nVee vee 0 DC 0\n" + src)
        save = ".save V(pa1) V(na1) V(fpa) V(fna)\n"
        meas = (".meas TRAN vfin FIND V(pa1,na1) AT=290u\n"
                ".meas TRAN vmax MAX V(pa1,na1) FROM=10u TO=290u\n"
                ".meas TRAN vmin MIN V(pa1,na1) FROM=10u TO=290u\n")
        tstop, dt = ("400u", "20n") if scen == "600k" else ("300u", "10n")
    return (head + body
            + f".tran 0 {tstop} 0 {dt}\n{TOPT}\n"
            + meas + save + ".end\n")


# ======================================================================
# 2. T08 / T09 网表
# ======================================================================
def t08_net(case, p, ron, vcm):
    r, cg, cd = p["r"], p["cg"], p["cd"]
    return (f"* t08 {SID[case]} ron{ron:g} vcm{vcm:g} — ADC kickback（CH1 真实接线 + fsadckb 实时钟）\n"
            f"* Ron={ron:g}Ω 手册无规格 → 声明假设（r5:158，扫 1/100/1k）；vcm={vcm:g}V 采样电容复位电位同为假设\n"
            f"* 判据 D9：每半周期 {TON*1e9:.2f}ns 窗末 |v_pin−v_ss| ≤ 0.01%·|v_ss|（parse_r5.kickback 同口径）\n"
            f".include {LIB}\n"
            f".model swkb sw(ron={ron:g} roff=1t vt=0.5 vh=0.05)\n"
            f"Vcc vcc 0 DC 3.3\nVee vee 0 DC 0\n"
            f"Vb vb 0 DC {fmt(VSENSE)}\n"
            + ch1_rc(r, cg, cd) +
            f"Vcm vcmn 0 DC {vcm:g}\n"
            f"Vswp swp 0 PULSE(0 1 0 0.5n 0.5n {fmt(TON)} {fmt(T_MOD)})\n"
            f"Vswn swn 0 PULSE(0 1 {fmt(T_MOD/2)} 0.5n 0.5n {fmt(TON)} {fmt(T_MOD)})\n"
            f"Xad1 a1p na1 vcmn swp swn csa1 csb1 fsadckb\n"
            f".tran 0 25u 0 0.2n\n{TOPT}\n"
            f".meas TRAN vpa_end FIND V(a1p) AT=24.8u\n"
            f".meas TRAN vna_end FIND V(na1) AT=24.8u\n"
            f".save V(a1p) V(na1) V(csa1) V(csb1)\n" + FSADCKB + ".end\n")


def t09_ac_net(case, p):
    r, cg, cd = p["r"], p["cg"], p["cd"]
    freqs = t09_freqs()
    meas = "".join(f".meas AC r{i} FIND mag(V(a1p,na1)) AT={fmt(f)}\n"
                   for i, f in enumerate(freqs))
    return (f"* t09 {SID[case]} ac — 高频耦合 AC 注入（L2）：P 跟随器输入 1V AC，ADC 引脚残差\n"
            f"* 单端注入=非对称最坏情形；残差∝注入幅度（LTI），报告按 1V 归一 + 100mV 换算\n"
            f"* fsadckb 断态（swp=swn=0）：AC 分析不能带开关动作，时钟态残差见 t09_fold\n"
            f".include {LIB}\n"
            f".model swkb sw(ron=100 roff=1t vt=0.5 vh=0.05)\n"
            f"Vcc vcc 0 DC 3.3\nVee vee 0 DC 0\n"
            f"Vb vb 0 DC {fmt(VSENSE)} AC 1\n"
            + ch1_rc(r, cg, cd) +
            f"Vswp swp 0 0\nVswn swn 0 0\n"
            f"Xad1 a1p na1 0 swp swn csa1 csb1 fsadckb\n"
            f".ac dec 500 100k 200Meg\n{TOPT}\n"
            + meas +
            f".save V(a1p) V(na1)\n" + FSADCKB + ".end\n")


def t09_fold_net(case, p):
    r, cg, cd = p["r"], p["cg"], p["cd"]
    finj = 4.104e6                       # fMOD + 8k
    return (f"* t09 {SID[case]} fold — 折叠实测：100mV @4.104MHz 注入 + 实时采样时钟，提取采样序列\n"
            f"* 采样序列 = csa/csb（fsadckb 端口）在各自保持窗末的均值；LSQ 拟合 8kHz 混叠分量（L3）\n"
            f"* sinc³(OSR=32) 离线换算，声明：非 LTspice 数字内核仿真（任务书 §3.2 L3）\n"
            f".include {LIB}\n"
            f".model swkb sw(ron=100 roff=1t vt=0.5 vh=0.05)\n"
            f"Vcc vcc 0 DC 3.3\nVee vee 0 DC 0\n"
            f"Vb vb 0 DC {fmt(VSENSE)} SIN({fmt(VSENSE)} 0.1 {fmt(finj)} 0 0 0)\n"
            + ch1_rc(r, cg, cd) +
            f"Vcm vcmn 0 DC 0.6\n"
            f"Vswp swp 0 PULSE(0 1 0 0.5n 0.5n {fmt(TON)} {fmt(T_MOD)})\n"
            f"Vswn swn 0 PULSE(0 1 {fmt(T_MOD/2)} 0.5n 0.5n {fmt(TON)} {fmt(T_MOD)})\n"
            f"Xad1 a1p na1 vcmn swp swn csa1 csb1 fsadckb\n"
            f".tran 0 60u 0 0.5n\n{TOPT}\n"
            f".save V(a1p) V(na1) V(csa1) V(csb1) V(swp)\n" + FSADCKB + ".end\n")


def t09_freqs():
    fs = []
    for fc in (4.096e6, 16.384e6):
        fs += [fc - 16e3, fc - 8e3, fc - 1e3, fc, fc + 1e3, fc + 8e3, fc + 16e3]
    fs += [8e3, 16e3]                    # 带内参考点
    return fs


def sinc3_db(f, fmod=FMOD, osr=OSR):
    n = round(f / fmod)
    d = abs(f - n * fmod)
    if d < 1e-9:
        return 0.0
    x = math.pi * d / fmod
    m = abs(math.sin(osr * x) / (osr * math.sin(x)))
    return 20 * math.log10(m ** 3)


# ======================================================================
# 3. 生成入口
# ======================================================================
T04_SCENS = ["nom", "ch1", "tol", "tolcm", "600k", "vlo", "vhi"]


def gen_all():
    written = []
    for case, p in CASES.items():
        for scen in T04_SCENS:
            f = NET / f"t04_{SID[case]}_{scen}.net"
            f.write_text(t04_net(case, p, scen))
            written.append(f)
        for ron in (1, 100, 1000):
            f = NET / f"t08_{SID[case]}_ron{ron:g}.net"
            f.write_text(t08_net(case, p, ron, 0.6))
            written.append(f)
        for vcm in (0.0, 2.0):           # vcm=0.6 由 ron100 覆盖
            f = NET / f"t08_{SID[case]}_vcm{vcm:g}.net"
            f.write_text(t08_net(case, p, 100, vcm))
            written.append(f)
        f = NET / f"t09_{SID[case]}_ac.net"
        f.write_text(t09_ac_net(case, p))
        written.append(f)
        f = NET / f"t09_{SID[case]}_fold.net"
        f.write_text(t09_fold_net(case, p))
        written.append(f)
    return written


# ======================================================================
# 4. 提取器
# ======================================================================
def _load_tran(rawpath):
    r = Raw(str(rawpath))
    t = np.array([v.real if isinstance(v, complex) else v for v in r.cols[0]], dtype=float)
    return r, t


def settle_bands(rawpath, pa, na, t_edge_end, bands):
    """带外最后出带法（run_all.tran_settle_from_raw 家法），多带一次算出。"""
    r, t = _load_tran(rawpath)
    d = np.array(r.col(pa), dtype=float) - np.array(r.col(na), dtype=float)
    m = t >= t_edge_end
    tt, dd = t[m], d[m]
    vf = float(dd[-1])
    err = np.abs(dd - vf)
    out = {"vfinal_v": vf, "err_end_uv": float(err[-1]) * 1e6}
    for band in bands:
        outside = np.where(err > band)[0]
        if len(outside) == 0:
            out[f"ts_{band*1e6:.4g}uv"] = 0.0
            continue
        k = outside[-1]
        if k >= len(tt) - 1:
            out[f"ts_{band*1e6:.4g}uv"] = float("inf")
            continue
        t0, t1, e0, e1 = tt[k], tt[k + 1], err[k], err[k + 1]
        tc = t0 + (t1 - t0) * (e0 - band) / (e0 - e1) if e0 != e1 else t1
        out[f"ts_{band*1e6:.4g}uv"] = float((tc - t_edge_end) * 1e6)
    return out, (tt, dd, vf)


def kickback_extract(rawpath, t_skip=8e-6, tol=1e-4):
    """D9 口径（parse_r5.kickback 同法）：每半周期窗 [k·T, k·T+TON] 与
    [k·T+T/2, k·T+T/2+TON]，P 引脚在 A 相、N 引脚在 B 相。
    v_ss = 窗末 10% 均值；kick 幅度 = 窗沿 ±2ns 台阶；残余 = 窗末点 vs v_ss。
    双判据：ownss = 残余≤0.01%·|本引脚 v_ss|（家法字面；Kelvin N 脚 v_ss≈1mV 时退化）；
           chan  = 残余≤0.01%·|通道差分稳态|（对测量的扰动，物理主判据）。"""
    r, t = _load_tran(rawpath)
    P = np.array(r.col("V(a1p)"), dtype=float)
    N = np.array(r.col("V(na1)"), dtype=float)
    m_tail = t >= t[-1] - 2e-6
    dm_v = float(np.mean(P[m_tail]) - np.mean(N[m_tail]))   # 通道差分稳态
    rows = []
    k = 0
    while True:
        t0 = k * T_MOD
        if t0 + T_MOD / 2 + TON > t[-1] - 2 * T_MOD:
            break
        if t0 >= t_skip:
            for ph, t_on, v in (("A", t0, P), ("B", t0 + T_MOD / 2, N)):
                m = (t >= t_on) & (t <= t_on + TON)
                if m.sum() < 20:
                    continue
                seg_t, seg_v = t[m], v[m]
                ntail = max(5, int(0.10 * len(seg_v)))
                v_ss = float(np.mean(seg_v[-ntail:]))
                amp = abs(float(np.interp(t_on + 2e-9, t, v))
                          - float(np.interp(t_on - 2e-9, t, v)))
                e_end = abs(float(seg_v[-1]) - v_ss)
                e_max = float(np.max(np.abs(seg_v - v_ss)))
                rows.append(dict(k=k, phase=ph, v_ss=v_ss, kick_amp_uv=amp * 1e6,
                                 resid_end_uv=e_end * 1e6, resid_max_uv=e_max * 1e6,
                                 rel_to_ss=e_end / abs(v_ss) if v_ss else 0.0,
                                 rel_to_ch=e_end / abs(dm_v) if dm_v else 0.0,
                                 resid_lsb=e_end / LSB_V,
                                 pass01=bool(e_end <= tol * abs(v_ss))))
        k += 1
    # 稳态平稳性：同相 v_ss 尾部 4 窗峰峰
    stat = {}
    for ph in ("A", "B"):
        vss = [x["v_ss"] for x in rows if x["phase"] == ph][-4:]
        stat[ph] = (max(vss) - min(vss)) * 1e6 if len(vss) >= 2 else float("nan")
    worst = {ph: max((x for x in rows if x["phase"] == ph), key=lambda x: x["rel_to_ch"],
                     default=None) for ph in ("A", "B")}
    return rows, worst, stat, dm_v


def fold_extract(rawpath, delta=8e3, t_skip=15e-6):
    """采样序列提取 + LSQ 拟合混叠分量。P 样本 = csa1 在 A 相窗末 2ns 均值；
    N 样本 = csb1 在 B 相窗末 2ns 均值；差分样本 = P−N（保持时刻差 T/2 引入
    相位 πδT ≪ 1 rad，忽略）。"""
    r, t = _load_tran(rawpath)
    csa = np.array(r.col("V(csa1)"), dtype=float)
    csb = np.array(r.col("V(csb1)"), dtype=float)
    ts, sm = [], []
    k = 0
    while True:
        t0 = k * T_MOD
        if t0 + T_MOD > t[-1]:
            break
        tA = t0 + TON - 2e-9
        tB = t0 + T_MOD / 2 + TON - 2e-9
        if t0 >= t_skip:
            mA = (t >= tA) & (t <= tA + 2e-9)
            mB = (t >= tB) & (t <= tB + 2e-9)
            if mA.sum() and mB.sum():
                ts.append(tA + 1e-9)
                sm.append(float(np.mean(csa[mA])) - float(np.mean(csb[mB])))
        k += 1
    ts, sm = np.array(ts), np.array(sm)
    w = 2 * math.pi * delta
    A_ = np.column_stack([np.sin(w * ts), np.cos(w * ts), np.ones_like(ts)])
    coef, *_ = np.linalg.lstsq(A_, sm, rcond=None)
    amp = math.hypot(coef[0], coef[1])
    resid_rms = float(np.sqrt(np.mean((sm - A_ @ coef) ** 2)))
    return ts, sm, amp, float(coef[2]), resid_rms


# ======================================================================
# 5. 主流程
# ======================================================================
def run_one(net: Path, timeout: int):
    ok, out = run_all.run_net(net, timeout=timeout)
    log, raw = net.with_suffix(".log"), net.with_suffix(".raw")
    print(f"[run] {net.name}: ok={ok}" + (f" {out[:120]}" if not ok else ""))
    if ok:
        shutil.copy2(log, LOGD / log.name)
        shutil.copy2(raw, RAWD / raw.name)
    else:
        if log.exists():
            shutil.copy2(log, LOGD / log.name)
    return net.name, ok, out


def main():
    t0 = time.time()
    gen = gen_all()
    print(f"[gen] {len(gen)} netlists")

    jobs = []
    for case in CASES:
        s = SID[case]
        for scen in T04_SCENS:
            jobs.append((NET / f"t04_{s}_{scen}.net", 600))
        for ron in (1, 100, 1000):
            jobs.append((NET / f"t08_{s}_ron{ron:g}.net", 1200))
        for vcm in (0.0, 2.0):
            jobs.append((NET / f"t08_{s}_vcm{vcm:g}.net", 1200))
        jobs.append((NET / f"t09_{s}_ac.net", 600))
        jobs.append((NET / f"t09_{s}_fold.net", 1200))
    print(f"[plan] {len(jobs)} sims")

    fails = []
    with ThreadPoolExecutor(max_workers=3) as ex:
        for name, ok, out in ex.map(lambda j: run_one(*j), jobs):
            if not ok:
                fails.append((name, out))
    print(f"[run] done in {time.time()-t0:.0f}s, fails={len(fails)}")
    for n, o in fails:
        print(f"  FAIL {n}: {o[:200]}")

    # ---- T04 CSV ----
    rows = []
    for case in CASES:
        s = SID[case]
        for scen in T04_SCENS:
            raw = RAWD / f"t04_{s}_{scen}.raw"
            if not raw.exists():
                rows.append(dict(case=case, scenario=scen, ts10_us="NOT VERIFIED",
                                 ts01_us="NOT VERIFIED", note="sim failed"))
                continue
            if scen == "ch1":
                res, _ = settle_bands(raw, "V(a1p)", "V(na1)", 10.01e-6,
                                      (VSENSE * 1e-3, VSENSE * 1e-4))
                b10, b01 = VSENSE * 1e3, VSENSE * 1e2
                r_, t_ = _load_tran(raw)
                na = np.array(r_.col("V(na1)"), dtype=float)
                m = t_ >= 10e-6
                nkick = float(np.max(np.abs(na[m]))) * 1e6
                note = f"CH1 真实接线；na1 C_D 耦合踢峰 {nkick:.1f}µV"
            else:
                res, _ = settle_bands(raw, "V(pa1)", "V(na1)", 10.01e-6,
                                      (710e-6, 71e-6))
                b10, b01 = 710.0, 71.0
                note = ""
                if scen == "tolcm":
                    r_, t_ = _load_tran(raw)
                    d = np.array(r_.col("V(pa1)"), dtype=float) - np.array(r_.col("V(na1)"), dtype=float)
                    m = t_ >= 10.01e-6
                    err = d[m] - float(d[m][-1])
                    note = f"CM→DM 泄漏峰 {float(np.max(np.abs(err)))*1e6:.1f}µV（终值 {float(d[m][-1])*1e6:.2f}µV）"
            rows.append(dict(
                case=case, scenario=scen,
                step=("CH0 ±0.355V@CM2V" if scen != "ch1" else f"CH1 0→{VSENSE:.4f}V"),
                band10_uv=round(b10, 2), band01_uv=round(b01, 2),
                ts10_us=round(res[f"ts_{b10:.4g}uv"], 3),
                ts01_us=round(res[f"ts_{b01:.4g}uv"], 3),
                vfinal_v=round(res["vfinal_v"], 6),
                err_end_uv=round(res["err_end_uv"], 3), note=note,
                method="raw 带外最后出带法（相对实际终值，沿 10µs/10ns 后起计）"))
    with (CSVD / "t04_settling.csv").open("w", newline="\n", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("[csv] t04_settling.csv")

    # ---- T08 CSV ----
    rows = []
    for case in CASES:
        s = SID[case]
        for tag in ["ron1", "ron100", "ron1000", "vcm0", "vcm2"]:
            ron = 100 if tag.startswith("vcm") else float(tag[3:])
            vcm = float(tag[3:]) / 1000 if tag.startswith("vcm") else 0.6
            raw = RAWD / f"t08_{s}_{tag}.raw"
            if not raw.exists():
                rows.append(dict(case=case, tag=tag, pin="*", note="sim failed"))
                continue
            kb, worst, stat, dm_v = kickback_extract(raw)
            for ph, pin in (("A", "a1p"), ("B", "na1")):
                ww = worst[ph]
                nph = sum(1 for x in kb if x["phase"] == ph)
                allp = all(x["pass01"] for x in kb if x["phase"] == ph)
                rows.append(dict(
                    case=case, tag=tag, ron_ohm=ron, vcm_v=vcm, pin=pin,
                    n_cycles=nph, dm_ss_v=round(dm_v, 6),
                    v_ss_v=round(ww["v_ss"], 6) if ww else "",
                    kick_amp_uv=round(ww["kick_amp_uv"], 2) if ww else "",
                    resid_end_uv=round(ww["resid_end_uv"], 3) if ww else "",
                    resid_end_lsb=round(ww["resid_lsb"], 2) if ww else "",
                    rel_to_ss=f"{ww['rel_to_ss']:.3e}" if ww else "",
                    pass01_ownss=allp,
                    rel_to_ch=f"{ww['rel_to_ch']:.3e}" if ww else "",
                    pass01_ch=bool(ww and ww["rel_to_ch"] <= 1e-4),
                    tail_vss_spread_uv=round(stat[ph], 3),
                    note="D9 双判据：ownss=残余≤0.01%·|本脚v_ss|（Kelvin N 脚 v_ss≈1mV 时退化）；"
                         "chan=残余≤0.01%·|通道差分稳态|（主判据）；Ron/vcm 均声明假设"))
    with (CSVD / "t08_kickback.csv").open("w", newline="\n", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("[csv] t08_kickback.csv")

    # ---- T09 AC CSV ----
    rows = []
    ac_pred = {}
    ac_pred_ph = {}
    for case in CASES:
        s = SID[case]
        raw = RAWD / f"t09_{s}_ac.raw"
        if not raw.exists():
            for f in t09_freqs():
                rows.append(dict(case=case, f_inj_hz=f, note="sim failed"))
            continue
        r = Raw(str(raw))
        for f in t09_freqs():
            vp = interp_at(r, f, "V(a1p)")
            vn = interp_at(r, f, "V(na1)")
            dm = vp - vn
            # 采样相位修正：两侧 S1 反相（M2/M6），N 样本晚 T/2 → 混叠幅度 |P−N·e^{−j2πfT/2}|
            # fMOD×(2n+1) 族（fMOD±δ）N 贡献变号（|P+N|）；16.384M=4×fMOD 族不变号。
            # FO1_C 实测验证：修正预测与折叠瞬态拟合差 <0.3%（t09_fold_check.csv）
            import cmath
            dmp = vp - vn * cmath.exp(-2j * math.pi * f * T_MOD / 2)
            s3 = sinc3_db(f)
            rows.append(dict(
                case=case, f_inj_hz=fmt(f),
                resid_pinP_db=round(20 * math.log10(abs(vp)), 3),
                resid_pinN_db=round(20 * math.log10(abs(vn)), 3),
                resid_dm_db=round(20 * math.log10(abs(dm)), 3),
                resid_dm_phased_db=round(20 * math.log10(abs(dmp)), 3),
                resid_dm_uv_at100mV=round(abs(dm) * 0.1 * 1e6, 4),
                sinc3_db=round(s3, 3),
                alias_to_output_db=round(20 * math.log10(abs(dm)) + s3, 3),
                alias_to_output_phased_db=round(20 * math.log10(abs(dmp)) + s3, 3),
                alias_phased_uv_at100mV=round(abs(dmp) * 0.1 * (10 ** (s3 / 20)) * 1e6, 4),
                layer="L2 AC(断态) + L3 sinc³ 换算",
                note="注入=1V AC @P 跟随器输入；phased=两侧反相采样修正(主口径)；"
                     "sinc³ 离线公式，非 LTspice 数字内核"))
            if abs(f - 4.104e6) < 1:
                ac_pred[case] = abs(dm) * 0.1
                ac_pred_ph[case] = abs(dmp) * 0.1
    with (CSVD / "t09_ac_residual.csv").open("w", newline="\n", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("[csv] t09_ac_residual.csv")

    # ---- T09 fold CSV ----
    rows = []
    for case in CASES:
        s = SID[case]
        raw = RAWD / f"t09_{s}_fold.raw"
        if not raw.exists():
            rows.append(dict(case=case, note="sim failed"))
            continue
        ts, sm, amp, off, rrms = fold_extract(raw)
        pred = ac_pred.get(case, float("nan"))
        pred_ph = ac_pred_ph.get(case, float("nan"))
        s3 = sinc3_db(8e3)
        rows.append(dict(
            case=case, n_samples=len(ts), t_skip_us=15,
            inj="100mV @4.104MHz (=fMOD+8k), P 跟随器输入, vcm=0.6, Ron=100Ω(假设)",
            fitted_alias_uv=round(amp * 1e6, 3),
            ac_pred_alias_uv=round(pred * 1e6, 3) if pred == pred else "",
            ac_pred_phased_uv=round(pred_ph * 1e6, 3) if pred_ph == pred_ph else "",
            fit_over_pred=round(amp / pred, 4) if pred == pred and pred > 0 else "",
            fit_over_pred_phased=round(amp / pred_ph, 4) if pred_ph == pred_ph and pred_ph > 0 else "",
            fit_resid_rms_uv=round(rrms * 1e6, 3),
            sinc3_db_at_8k=round(s3, 3),
            output_alias_uv=round(amp * (10 ** (s3 / 20)) * 1e6, 3),
            lsb_uv=round(LSB_V * 1e6, 3),
            alias_in_lsb=round(amp * (10 ** (s3 / 20)) / LSB_V, 1),
            rel_to_vsense_ppm=round(amp * (10 ** (s3 / 20)) / VSENSE * 1e6, 2),
            layer="L3：采样序列 LTspice 实测 + sinc³ 离线换算（声明）"))
    with (CSVD / "t09_fold_check.csv").open("w", newline="\n", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("[csv] t09_fold_check.csv")

    make_plots()
    print(f"[done] {time.time()-t0:.0f}s")
    return 0


# ======================================================================
# 6. 图
# ======================================================================
def make_plots():
    # T04：误差衰减曲线（每方案一图）+ ts01 汇总
    fig, ax = plt.subplots(figsize=(8, 5))
    wid = 0.2
    scens = [s for s in T04_SCENS]
    for i, case in enumerate(CASES):
        s = SID[case]
        vals = []
        for scen in scens:
            raw = RAWD / f"t04_{s}_{scen}.raw"
            if not raw.exists():
                vals.append(0)
                continue
            if scen == "ch1":
                res, _ = settle_bands(raw, "V(a1p)", "V(na1)", 10.01e-6, (VSENSE * 1e-4,))
                v = res[f"ts_{VSENSE*1e2:.4g}uv"]
            else:
                res, _ = settle_bands(raw, "V(pa1)", "V(na1)", 10.01e-6, (71e-6,))
                v = res["ts_71uv"]
            vals.append(v)
        ax.bar(np.arange(len(scens)) + i * wid, vals, wid, label=case)
    ax.set_xticks(np.arange(len(scens)) + 1.5 * wid)
    ax.set_xticklabels(scens, rotation=20)
    ax.axhline(900, color="r", ls="--", lw=1, label="D5 及格线 900µs")
    ax.axhline(500, color="orange", ls=":", lw=1, label="D5 满分线 500µs")
    ax.set_ylabel("0.01% 建立时间 (µs)")
    ax.set_yscale("log")
    ax.set_title("T04 0.01% 建立时间（带外最后出带法）")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(PLOTD / "t04_ts01_summary.png", dpi=110)
    plt.close(fig)

    for case in CASES:
        s = SID[case]
        fig, ax = plt.subplots(figsize=(8, 5))
        for scen in T04_SCENS:
            raw = RAWD / f"t04_{s}_{scen}.raw"
            if not raw.exists():
                continue
            if scen == "ch1":
                _, (tt, dd, vf) = settle_bands(raw, "V(a1p)", "V(na1)", 10.01e-6,
                                               (VSENSE * 1e-4,))
            else:
                _, (tt, dd, vf) = settle_bands(raw, "V(pa1)", "V(na1)", 10.01e-6, (71e-6,))
            err = np.abs(dd - vf)
            m = err > 0
            ax.semilogy((tt[m] - 10.01e-6) * 1e6, err[m] * 1e6, lw=1, label=scen)
        ax.axhline(71, color="r", ls="--", lw=1, label="71µV (0.01% of 0.71V)")
        ax.axhline(710, color="orange", ls=":", lw=1, label="710µV (0.1%)")
        ax.set_xlabel("自阶跃沿起计 (µs)")
        ax.set_ylabel("|差分误差| (µV)")
        ax.set_title(f"T04 {case} 建立误差衰减（对数）")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3, which="both")
        fig.tight_layout()
        fig.savefig(PLOTD / f"t04_{s}_settle_curves.png", dpi=110)
        plt.close(fig)

    # T08：最坏角（ron100/vcm0.6）两相窗内波形放大 + 判据带
    for case in CASES:
        s = SID[case]
        raw = RAWD / f"t08_{s}_ron100.raw"
        if not raw.exists():
            continue
        kb, worst, stat, dm_v = kickback_extract(raw, t_skip=20e-6)
        if not kb:
            continue
        r, t = _load_tran(raw)
        P = np.array(r.col("V(a1p)"), dtype=float)
        N = np.array(r.col("V(na1)"), dtype=float)
        k_last = kb[-1]["k"]
        t0 = k_last * T_MOD
        vssA = [x["v_ss"] for x in kb if x["k"] == k_last and x["phase"] == "A"]
        vssB = [x["v_ss"] for x in kb if x["k"] == k_last and x["phase"] == "B"]
        vA = vssA[0] if vssA else float(np.mean(P[-50:]))
        vB = vssB[0] if vssB else float(np.mean(N[-50:]))
        m = (t >= t0 - 0.3 * T_MOD) & (t <= t0 + 1.3 * T_MOD)
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.plot((t[m] - t0) * 1e9, (P[m] - vA) * 1e6, lw=1, label="V(a1p)−v_ss")
        ax.plot((t[m] - t0) * 1e9, (N[m] - vB) * 1e6, lw=1, label="V(na1)−v_ss")
        for ph, t_on, col in (("A 相窗(P)", 0, "tab:blue"), ("B 相窗(N)", T_MOD / 2, "tab:orange")):
            ax.axvspan(t_on * 1e9, (t_on + TON) * 1e9, alpha=0.08, color=col)
        ax.axhline(vA * 1e6 * 1e-4, color="r", ls="--", lw=0.8, label="+0.01%·v_ss(A)")
        ax.axhline(vA * 1e6 * -1e-4, color="r", ls="--", lw=0.8, label="−0.01%·v_ss(A)")
        ax.set_xlabel("自末周期起点起计 (ns)")
        ax.set_ylabel("引脚对各自稳态偏差 (µV)")
        ax.set_title(f"T08 {case} kickback（Ron=100Ω, vcm=0.6V, 末两相窗）")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)
        fig.tight_layout()
        fig.savefig(PLOTD / f"t08_{s}_kick_wave.png", dpi=110)
        plt.close(fig)

    # T09：AC 残差棒图 + fold 采样序列
    for case in CASES:
        s = SID[case]
        raw = RAWD / f"t09_{s}_ac.raw"
        if raw.exists():
            r = Raw(str(raw))
            fs = t09_freqs()
            vals = []
            for f in fs:
                dm = interp_at(r, f, "V(a1p)") - interp_at(r, f, "V(na1)")
                vals.append(20 * math.log10(abs(dm)))
            fig, ax = plt.subplots(figsize=(9, 5))
            lbl = [f"{f/1e6:.4f}M" if f >= 1e6 else f"{f/1e3:.0f}k" for f in fs]
            ax.bar(range(len(fs)), vals)
            ax.set_xticks(range(len(fs)))
            ax.set_xticklabels(lbl, rotation=60, fontsize=7)
            ax.set_ylabel("ADC 引脚差模残差 dBV（1V 注入）")
            ax.set_title(f"T09 {case} 高频注入→引脚残差（L2 AC，断态负载）")
            ax.grid(alpha=0.3, axis="y")
            fig.tight_layout()
            fig.savefig(PLOTD / f"t09_{s}_ac_residual.png", dpi=110)
            plt.close(fig)
        raw = RAWD / f"t09_{s}_fold.raw"
        if raw.exists():
            ts, sm, amp, off, rrms = fold_extract(raw)
            w = 2 * math.pi * 8e3
            A_ = np.column_stack([np.sin(w * ts), np.cos(w * ts), np.ones_like(ts)])
            coef, *_ = np.linalg.lstsq(A_, sm, rcond=None)
            ph0 = math.atan2(coef[1], coef[0])
            fig, ax = plt.subplots(figsize=(8, 5))
            ax.plot(ts * 1e6, sm * 1e6, ".", ms=3, label="采样序列（LTspice 实测）")
            ax.plot(ts * 1e6, (off + amp * np.sin(w * ts + ph0)) * 1e6, "r-", lw=1,
                    label=f"LSQ 拟合 8kHz 混叠: {amp*1e6:.1f}µV")
            ax.set_xlabel("时间 (µs)")
            ax.set_ylabel("差分采样值 (µV)")
            ax.set_title(f"T09 {case} 折叠实测（100mV@4.104MHz 注入）")
            ax.legend(fontsize=8)
            ax.grid(alpha=0.3)
            fig.tight_layout()
            fig.savefig(PLOTD / f"t09_{s}_fold.png", dpi=110)
            plt.close(fig)


if __name__ == "__main__":
    raise SystemExit(main())
