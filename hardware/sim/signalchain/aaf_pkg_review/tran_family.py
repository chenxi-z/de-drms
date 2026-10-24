#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tran_family.py — aaf_pkg_review 六方案瞬态族台架（T04 / T08 / T09 / THD，2026-10-24）

任务来源：AAF_基于已确认封装的候选参数与Zcode复核_2026-10-24.md §5(3)(4)(5) +
本轮分工（仿真·tran）。口径基座 = fo1_rc_review/tran_tests.py（家法逐条沿用）+
本目录 run_all.py 六方案参数（SCHEMES）与运行器（run_net）。

铁律执行：
  * 真实接线 = 3 颗 OPA388 系统中，每通道台架按真实接线：
    CH0 台架 = 2 颗跟随器（T/M 两线，其真实接线本就如此）；
    CH1 台架 = B 线跟随器 + AIN1N 经 Kelvin RC 直连 Rsense 底端（**无第四运放**，
    RKN/CGN 纯无源）；T08/T09/THD 全走 CH1 口径。
  * 理想 RC 数字（任务书 §3 表）只作对拍参考，绝不冒充 LTspice 实测。

T04 瞬态建立（0.1%/0.01% 双带）：
  阶跃幅度：CH0 = P 2→2.355V / N 2→1.645V（±0.355V @CM 2V，差分 0.71V，
  t00_tran2 锚定口径，带=710/71µV）；CH1 = B 0→1.17857V（系统真实 V_Rsense
  =3.3×200/560，带=1.1786mV/117.86µV）。阶跃沿 t=10µs/10ns（fsrc 使能沿 µs 级，10ns 保守）。
  判稳：raw 带外最后出带法（相对实际终值，自沿结束点 10.01µs 起计；
  run_all.tran_settle_from_raw / parse_r5.settle_us 同口径）。
  角点：nom / ch1 / tol(差模失配 P×1.01/1.05 N×0.99/0.95 Cd×1.05) /
  tolcm(同失配+纯共模阶跃 2→2.355V，测 CM→DM 泄漏) / vlo=3.135 / vhi=3.465（±5% 声明假设）/
  src10k / src120k（源阻抗角=跟随器输入侧串 10k/120k，标称滤波；上轮 600k 家法的
  工作量程版——任务书 §5(5) 10k–120k 工作量程）。

T08 ADC kickback（开关电容输入驱动稳健性，对照 D9）：
  fsadckb = ADS131A02 采样开关模型（M2/M6 口径：每侧 Cs/2=1.75pF，合计 3.5pF 差分；
  S1/S2 双相 50% 反相；fMOD=4.096MHz，r5 V8 时钟 PULSE ton=121.07n period=244.1406n）。
  Ron∈{1,100,1000}Ω @vcm=0.6V + vcm∈{0,2.0}V @Ron=100Ω——Ron/vcm 手册无值，声明假设
  （fo1_rc_review/assumptions.md A1/A8，沿用不重推）。
  D9 判据：每半周期采样窗（≈121ns）末残余，双口径：ownss=≤0.01%·|本脚 v_ss|；
  chan=≤0.01%·|通道差分稳态|（物理主判据）。
  二阶方案另单看节点1（R1/CG1 节点，即 R2+CG2 之前级）窗末回稳，与引脚分开列表。

T09 高频注入折回（4.096M 与 16.384M ±{1k,8k,16k}）：
  AC（L2）：Vb AC 1V（单端注入=非对称最坏），fsadckb 断态，16 频点 .meas + raw 复数插值
  （插值含相位 → 采样相位修正 e^{-j2πfT/2}：fMOD 族 N 贡献变号、4×fMOD 族不变）。
  瞬态（L3）：100mV 注入 + 实时钟，提取 csa/csb 采样序列，LSQ 拟合 δ 频率混叠分量，
  sinc³(OSR=32) 离线换算——显式声明非 LTspice 数字内核（无可信采样模型 → 只给有界风险）。
  折回换算参考 LSB=2×2.442/2^24=290.98nV（parse_r5 口径）。

THD（本轮新增）：
  CH1 口径（P=OPA388 驱动、N=Kelvin 纯 RC——非对称最坏，偶次谐波无对消，覆盖 CH0 对称情形）；
  激励 Vb=1.17857V + 0.5V·sin(2πf0t)，f0∈{1k,16k}（通带内代表频点）；
  负载=各案 RC 梯形 + fsadckb 实时钟（Ron=100 假设、vcm=0.6）；
  .tran 2.2ms（前 0.2ms 建立弃置）+ .four f0 10 次谐波 × 2 周期 —— 分析窗恰为
  2ms = 8192×T_MOD（时钟周期写全精度 244.140625n）→ 4.096MHz 开关纹波对分析窗正交，
  不污染 ≤10 次谐波；.four V(vb)（理想源）作数值地板对照。
  判决门：任务书未给 THD 门 → 以 24bit 满量程 LSB 换算给参考（谐波和 vs LSB/FS）。

产物：netlists/{t04,t08,t09,thd}_<方案ID小写>_<测试变体>.net、logs/、raw/、
csv/{t04_settling,t08_kickback,t09_ac_residual,t09_fold_check,thd_summary}.csv、
plots/（文件名含方案ID+测试ID）。S0/S1 与上轮 FO1_BASE/FO1_A 电气等同 →
对锚列（旧 CSV 只读引用）。

子命令：gen / lint / run / extract / all / pilot
"""
from __future__ import annotations

import csv
import math
import re
import shutil
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE))
sys.path.insert(0, "/media/anning/data/Project/DE-DRMS/hardware/sim/aaf")

import run_all  # noqa: E402  (本台架基座：SCHEMES / LIB / run_net)
from parse_r5 import Raw, interp_at  # noqa: E402

import matplotlib  # noqa: E402
matplotlib.use("Agg")
matplotlib.rcParams["font.family"] = ["Noto Sans CJK SC", "WenQuanYi Zen Hei", "DejaVu Sans"]
import matplotlib.pyplot as plt  # noqa: E402

NET, LOGD, RAWD, CSVD, PLOTD = (HERE / d for d in ("netlists", "logs", "raw", "csv", "plots"))
for d in (NET, LOGD, RAWD, CSVD, PLOTD):
    d.mkdir(exist_ok=True)

SCHEMES = run_all.SCHEMES
LIB = run_all.LIB
TOPT = ".options plotwinsize=0 reltol=1e-6 abstol=1e-12 vntol=1e-9 chgtol=1e-15 trtol=1\n"
SID = {k: k.lower() for k in SCHEMES}                       # s0/s1/t1/t2/t3/t4
VSENSE = 3.3 * 200e3 / 560e3                                # 1.178571 V
T_MOD = 244.1406e-9                                         # 家法时钟周期（与上轮一致 6 位）
T_MOD_EXACT = "244.140625n"                                 # THD 用全精度（2ms=8192 周期正交）
TON = 121.07e-9
FMOD, MCLK, OSR = 4.096e6, 16.384e6, 32
LSB_V = 2.0 * 2.442 / 2 ** 24                               # 290.98 nV

OLD = Path("/media/anning/data/Project/DE-DRMS/hardware/sim/signalchain/fo1_rc_review")  # 只读

FSADCKB = """* ---- fsadc 移植版：csa/csb 引出为端口（采样序列提取用；器件值=fo_subs.inc/fsadc）----
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
# 1. 梯形构建（一阶/二阶 × P 驱动侧 / N Kelvin 侧；k = (r_mult, c_mult)）
# ======================================================================
def ladder_p(p: dict, in_n: str, n1: str, out: str, km=(1.0, 1.0)) -> str:
    """驱动侧（跟随器输出 in_n → 节点1 → ADC 节点 out）。"""
    rk, ck = km
    if p["topo"] == 1:
        return (f"Ra1 {in_n} {out} {fmt(p['r1']*rk)}\n"
                f"Ca1 {out} 0 {fmt(p['cg1']*ck)}\n")
    return (f"Ra1 {in_n} {n1} {fmt(p['r1']*rk)}\n"
            f"Ca1 {n1} 0 {fmt(p['cg1']*ck)}\n"
            f"Ra2 {n1} {out} {fmt(p['r2']*rk)}\n"
            f"Ca2 {out} 0 {fmt(p['cg2']*ck)}\n")


def ladder_n_kelvin(p: dict, n1: str, out: str, km=(1.0, 1.0)) -> str:
    """Kelvin N 侧（地 → RKN1 → n1n(CGN1) → RKN2 → na1(CGN2)）——纯无源，无第四运放。"""
    rk, ck = km
    if p["topo"] == 1:
        return (f"RKN 0 {out} {fmt(p['r1']*rk)}\n"
                f"CGN {out} 0 {fmt(p['cg1']*ck)}\n")
    return (f"RKN1 0 {n1} {fmt(p['r1']*rk)}\n"
            f"CGN1 {n1} 0 {fmt(p['cg1']*ck)}\n"
            f"RKN2 {n1} {out} {fmt(p['r2']*rk)}\n"
            f"CGN2 {out} 0 {fmt(p['cg2']*ck)}\n")


def adc_static(p: dict, cdm=1.0) -> str:
    """ADC 静态负载（断态口径：Rin 130k + C_pin 5p/端）+ Cd 跨接。"""
    return (f"CD1 pa1 na1 {fmt(p['cd']*cdm)}\n"
            f"Rin pa1 na1 130000\nCpa pa1 0 5e-12\nCna na1 0 5e-12\n")


# ======================================================================
# 2. T04 网表（8 角点）
# ======================================================================
T04_SCENS = ["nom", "ch1", "tol", "tolcm", "vlo", "vhi", "src10k", "src120k"]


def t04_net(sid: str, p: dict, scen: str) -> str:
    vcc = {"vlo": 3.135, "vhi": 3.465}.get(scen, 3.3)
    topo2 = p["topo"] == 2
    km_p = (1.01, 1.05) if scen in ("tol", "tolcm") else (1.0, 1.0)
    km_n = (0.99, 0.95) if scen in ("tol", "tolcm") else (1.0, 1.0)
    cdm = 1.05 if scen in ("tol", "tolcm") else 1.0
    n1a = "n1a" if topo2 else "pa1"
    n1b = "n1b" if topo2 else "na1"

    if scen == "ch1":
        head = (f"* t04 {sid} ch1 — CH1 真实接线建立（B 0→{VSENSE:.5f}V，AIN1N Kelvin RC 无第四运放）\n"
                f"* 判稳：raw 带外最后出带法，相对实际终值，带 = 0.1%/{VSENSE:.2f}mV、"
                f"0.01%/{VSENSE*1e2:.2f}µV；阶跃沿 t=10µs/10ns（fsrc 使能沿 µs 级，10ns 保守口径）\n"
                f".include {LIB}\nVcc vcc 0 DC {vcc}\nVee vee 0 DC 0\n"
                f"Vb vb 0 PULSE(0 {fmt(VSENSE)} 10u 10n 10n 600u 2m)\n"
                f"Xfb vb fbp vcc vee fbp OPAx388\n")
        body = ladder_p(p, "fbp", "n1a", "a1p", km_p) + ladder_n_kelvin(p, "n1n", "na1", km_n) \
            + f"CD1 a1p na1 {fmt(p['cd']*cdm)}\n" \
            + "Rin a1p na1 130000\nCpa a1p 0 5e-12\nCna na1 0 5e-12\n"
        save = ".save V(a1p) V(na1) V(fbp)" + (" V(n1a) V(n1n)\n" if topo2 else "\n")
        meas = (".meas TRAN vfin FIND V(a1p,na1) AT=290u\n"
                ".meas TRAN vmax MAX V(a1p,na1) FROM=10u TO=290u\n"
                ".meas TRAN vmin MIN V(a1p,na1) FROM=10u TO=290u\n"
                ".meas TRAN nkick MAX V(na1) FROM=10u TO=290u\n")
        tstop, dt = "300u", "10n"
    else:
        # tolcm = 纯共模阶跃（P/N 同 2→2.355V）；其余 = 差模（N 2→1.645V）
        pulse_n = ("PULSE(2 2.355 10u 10n 10n 600u 2m)" if scen == "tolcm"
                   else "PULSE(2 1.645 10u 10n 10n 600u 2m)")
        if scen.startswith("src"):
            rs = 10e3 if scen == "src10k" else 120e3
            src = (f"Vp vp 0 PULSE(2 2.355 10u 10n 10n 600u 2m)\nVn vn 0 {pulse_n}\n"
                   f"Rsa vp fa {fmt(rs)}\nRsb vn fb {fmt(rs)}\n"
                   f"Xfa fa fpa vcc vee fpa OPAx388\nXfb fb fna vcc vee fna OPAx388\n")
        else:
            src = (f"Vp vp 0 PULSE(2 2.355 10u 10n 10n 600u 2m)\nVn vn 0 {pulse_n}\n"
                   f"Xfa vp fpa vcc vee fpa OPAx388\nXfb vn fna vcc vee fna OPAx388\n")
        body = ladder_p(p, "fpa", "n1a", "pa1", km_p) + ladder_n_sym(p, "n1b", "na1", km_n) \
            + adc_static(p, cdm)
        save = ".save V(pa1) V(na1) V(fpa) V(fna)" + (" V(n1a) V(n1b)\n" if topo2 else "\n")
        meas = (".meas TRAN vfin FIND V(pa1,na1) AT=290u\n"
                ".meas TRAN vmax MAX V(pa1,na1) FROM=10u TO=290u\n"
                ".meas TRAN vmin MIN V(pa1,na1) FROM=10u TO=290u\n")
        tstop, dt = "300u", "10n"
        tag = {"nom": "CH0 标称（±0.355V@CM2V 差模阶跃）",
               "tol": "CH0 容差失配+差模阶跃（P ×1.01/×1.05，N ×0.99/×0.95，C_D ×1.05）",
               "tolcm": "CH0 容差失配+纯共模阶跃（P/N 同 2→2.355V，测 CM→DM 泄漏建立）",
               "vlo": f"CH0 标称 + 供电角 Vcc={vcc}V（3.3V −5%，声明假设）",
               "vhi": f"CH0 标称 + 供电角 Vcc={vcc}V（3.3V +5%，声明假设）",
               "src10k": "CH0 源阻抗角 10kΩ（跟随器输入侧串联，标称滤波）",
               "src120k": "CH0 源阻抗角 120kΩ（工作量程上限，标称滤波）"}[scen]
        head = (f"* t04 {sid} {scen} — {tag}\n"
                f"* 判稳：raw 带外最后出带法，相对实际终值；带 = 0.1%/710µV、0.01%/71µV（0.71V 阶跃）\n"
                f".include {LIB}\nVcc vcc 0 DC {vcc}\nVee vee 0 DC 0\n" + src)
    return (head + body
            + f".tran 0 {tstop} 0 {dt}\n{TOPT}\n"
            + meas + save + ".end\n")


def ladder_n_sym(p: dict, n1: str, out: str, km) -> str:
    """CH0 台架 N 侧（跟随器 fna → 梯形 → na1）。"""
    rk, ck = km
    if p["topo"] == 1:
        return (f"Rb1 fna {out} {fmt(p['r1']*rk)}\n"
                f"Cb1 {out} 0 {fmt(p['cg1']*ck)}\n")
    return (f"Rb1 fna {n1} {fmt(p['r1']*rk)}\n"
            f"Cb1 {n1} 0 {fmt(p['cg1']*ck)}\n"
            f"Rb2 {n1} {out} {fmt(p['r2']*rk)}\n"
            f"Cb2 {out} 0 {fmt(p['cg2']*ck)}\n")


# ======================================================================
# 3. T08 网表（kickback；二阶另存节点1）
# ======================================================================
def t08_net(sid: str, p: dict, ron: float, vcm: float) -> str:
    topo2 = p["topo"] == 2
    save = ".save V(a1p) V(na1) V(csa1) V(csb1)" + (" V(n1a) V(n1n)\n" if topo2 else "\n")
    return (f"* t08 {sid} ron{ron:g} vcm{vcm:g} — ADC kickback（CH1 真实接线 + fsadckb 实时钟）\n"
            f"* 采样开关模型：每侧 Cs/2=1.75pF（差分合计 3.5pF），S1/S2 双相 50% 反相，fMOD=4.096MHz\n"
            f"* Ron={ron:g}Ω 手册无规格 → 声明假设（fo1 A1，扫 1/100/1k）；vcm={vcm:g}V 复位电位同为假设（fo1 A8）\n"
            f"* 判据 D9：每半周期 {TON*1e9:.2f}ns 采样窗末残余（ownss=≤0.01%·|本脚v_ss|；"
            f"chan=≤0.01%·|通道差分稳态|，主判据）；二阶另单看节点1（R1/CG1）回稳\n"
            f".include {LIB}\n"
            f".model swkb sw(ron={ron:g} roff=1t vt=0.5 vh=0.05)\n"
            f"Vcc vcc 0 DC 3.3\nVee vee 0 DC 0\n"
            f"Vb vb 0 DC {fmt(VSENSE)}\n"
            f"Xfb vb fbp vcc vee fbp OPAx388\n"
            + ladder_p(p, "fbp", "n1a", "a1p") + ladder_n_kelvin(p, "n1n", "na1") +
            f"CD1 a1p na1 {fmt(p['cd'])}\n"
            f"Rin a1p na1 130000\nCpa a1p 0 5e-12\nCna na1 0 5e-12\n"
            f"Vcm vcmn 0 DC {vcm:g}\n"
            f"Vswp swp 0 PULSE(0 1 0 0.5n 0.5n {fmt(TON)} {fmt(T_MOD)})\n"
            f"Vswn swn 0 PULSE(0 1 {fmt(T_MOD/2)} 0.5n 0.5n {fmt(TON)} {fmt(T_MOD)})\n"
            f"Xad1 a1p na1 vcmn swp swn csa1 csb1 fsadckb\n"
            f".tran 0 25u 0 0.2n\n{TOPT}\n"
            f".meas TRAN vpa_end FIND V(a1p) AT=24.8u\n"
            f".meas TRAN vna_end FIND V(na1) AT=24.8u\n"
            + save + FSADCKB + ".end\n")


# ======================================================================
# 4. T09 网表（AC + 折叠瞬态 × 2 时钟族 × ±{1k,8k,16k}）
# ======================================================================
def t09_freqs():
    fs = []
    for fc in (FMOD, MCLK):
        fs += [fc - 16e3, fc - 8e3, fc - 1e3, fc, fc + 1e3, fc + 8e3, fc + 16e3]
    fs += [8e3, 16e3]
    return fs


def t09_ac_net(sid: str, p: dict) -> str:
    meas = "".join(f".meas AC r{i} FIND mag(V(a1p,na1)) AT={fmt(f)}\n"
                   for i, f in enumerate(t09_freqs()))
    return (f"* t09 {sid} ac — 高频耦合 AC 注入（L2）：B 跟随器输入 1V AC，ADC 引脚差模残差\n"
            f"* 单端注入=非对称最坏情形；残差∝注入幅度（LTI），报告按 1V 归一 + 100mV 换算\n"
            f"* fsadckb 断态（swp=swn=0）：AC 不能带开关动作，时钟态折回见 t09_fold\n"
            f".include {LIB}\n"
            f".model swkb sw(ron=100 roff=1t vt=0.5 vh=0.05)\n"
            f"Vcc vcc 0 DC 3.3\nVee vee 0 DC 0\n"
            f"Vb vb 0 DC {fmt(VSENSE)} AC 1\n"
            f"Xfb vb fbp vcc vee fbp OPAx388\n"
            + ladder_p(p, "fbp", "n1a", "a1p") + ladder_n_kelvin(p, "n1n", "na1") +
            f"CD1 a1p na1 {fmt(p['cd'])}\n"
            f"Rin a1p na1 130000\nCpa a1p 0 5e-12\nCna na1 0 5e-12\n"
            f"Vswp swp 0 0\nVswn swn 0 0\n"
            f"Xad1 a1p na1 0 swp swn csa1 csb1 fsadckb\n"
            f".ac dec 500 100k 200Meg\n{TOPT}\n"
            + meas +
            f".save V(a1p) V(na1)\n" + FSADCKB + ".end\n")


T09_FOLDS = []                                   # (family_tag, sign, delta)
for ft, fc in (("f4m", FMOD), ("f16m", MCLK)):
    for sg in ("p", "m"):
        for d, dt_ in ((1e3, "1k"), (8e3, "8k"), (16e3, "16k")):
            T09_FOLDS.append((ft, fc, sg, d, dt_))


def t09_fold_net(sid: str, p: dict, fc: float, sg: str, delta: float) -> str:
    finj = fc + delta if sg == "p" else fc - delta
    tstop = "320u" if delta == 1e3 else "60u"
    return (f"* t09 {sid} fold {sg} — 折叠实测：100mV @{fmt(finj)}Hz 注入 + 实时采样时钟，提取采样序列\n"
            f"* 采样序列 = csa1/csb1 在各自保持窗末 2ns 均值（fsadckb 端口）；LSQ 拟合 {fmt(delta)}Hz 混叠分量；\n"
            f"* sinc³(OSR=32) 离线换算，声明：非 LTspice 数字内核（无可信采样模型 → 有界风险口径）\n"
            f".include {LIB}\n"
            f".model swkb sw(ron=100 roff=1t vt=0.5 vh=0.05)\n"
            f"Vcc vcc 0 DC 3.3\nVee vee 0 DC 0\n"
            f"Vb vb 0 DC {fmt(VSENSE)} SIN({fmt(VSENSE)} 0.1 {fmt(finj)} 0 0 0)\n"
            f"Xfb vb fbp vcc vee fbp OPAx388\n"
            + ladder_p(p, "fbp", "n1a", "a1p") + ladder_n_kelvin(p, "n1n", "na1") +
            f"CD1 a1p na1 {fmt(p['cd'])}\n"
            f"Rin a1p na1 130000\nCpa a1p 0 5e-12\nCna na1 0 5e-12\n"
            f"Vcm vcmn 0 DC 0.6\n"
            f"Vswp swp 0 PULSE(0 1 0 0.5n 0.5n {fmt(TON)} {fmt(T_MOD)})\n"
            f"Vswn swn 0 PULSE(0 1 {fmt(T_MOD/2)} 0.5n 0.5n {fmt(TON)} {fmt(T_MOD)})\n"
            f"Xad1 a1p na1 vcmn swp swn csa1 csb1 fsadckb\n"
            f".tran 0 {tstop} 0 0.5n\n{TOPT}\n"
            f".save V(a1p) V(na1) V(csa1) V(csb1) V(swp)\n" + FSADCKB + ".end\n")


# ======================================================================
# 5. THD 网表（CH1 口径 + 实时钟开关电容负载；.four 正交窗）
# ======================================================================
def thd_net(sid: str, p: dict, f0: float) -> str:
    nper = 1 if f0 == 1e3 else 16                # 分析窗恒 1ms = 4096×T_MOD（正交）
    return (f"* thd {sid} f{f0/1e3:g}k — THD（CH1 口径：P=OPA388 驱动，N=Kelvin 纯 RC，非对称最坏）\n"
            f"* 激励 Vb = {fmt(VSENSE)}V + 0.5V·sin(2π·{fmt(f0)}t)；负载 = 各案 RC 梯形 + fsadckb 实时钟\n"
            f"* 时钟周期写全精度 {T_MOD_EXACT}：分析窗（.four 末 {nper} 周期 = 1ms）恰为 4096 个采样周期\n"
            f"* → 4.096MHz 开关纹波对分析窗正交，不污染 ≤10 次谐波；.four V(vb)（理想源）= 数值地板对照\n"
            f"* 判决门：任务书未给 → 谐波和按 24bit 满量程 LSB={LSB_V*1e9:.2f}nV 换算给参考\n"
            f".include {LIB}\n"
            f".model swkb sw(ron=100 roff=1t vt=0.5 vh=0.05)\n"
            f"Vcc vcc 0 DC 3.3\nVee vee 0 DC 0\n"
            f"Vb vb 0 SIN({fmt(VSENSE)} 0.5 {fmt(f0)} 0 0 0)\n"
            f"Xfb vb fbp vcc vee fbp OPAx388\n"
            + ladder_p(p, "fbp", "n1a", "a1p") + ladder_n_kelvin(p, "n1n", "na1") +
            f"CD1 a1p na1 {fmt(p['cd'])}\n"
            f"Rin a1p na1 130000\nCpa a1p 0 5e-12\nCna na1 0 5e-12\n"
            f"Vcm vcmn 0 DC 0.6\n"
            f"Vswp swp 0 PULSE(0 1 0 0.5n 0.5n {fmt(TON)} {T_MOD_EXACT})\n"
            f"Vswn swn 0 PULSE(0 1 122.0703125n 0.5n 0.5n {fmt(TON)} {T_MOD_EXACT})\n"
            f"Xad1 a1p na1 vcmn swp swn csa1 csb1 fsadckb\n"
            f".tran 0 1.1m 0 5n\n{TOPT}\n"
            f".meas TRAN vpp_pin PP V(a1p,na1) FROM=100u TO=1.1m\n"
            f".four {fmt(f0)} 10 {nper} V(a1p,na1)\n"
            f".four {fmt(f0)} 10 {nper} V(fbp)\n"
            f".four {fmt(f0)} 10 {nper} V(vb)\n"
            f".save V(a1p) V(na1) V(fbp) V(vb)\n" + FSADCKB + ".end\n")


# ======================================================================
# 6. 生成
# ======================================================================
def gen_all() -> list[Path]:
    written = []
    for sid, p in SCHEMES.items():
        s = SID[sid]
        for scen in T04_SCENS:
            f = NET / f"t04_{s}_{scen}.net"
            f.write_text(t04_net(sid, p, scen))
            written.append(f)
        for ron in (1, 100, 1000):
            f = NET / f"t08_{s}_ron{ron:g}.net"
            f.write_text(t08_net(sid, p, ron, 0.6))
            written.append(f)
        for vcm in (0.0, 2.0):
            f = NET / f"t08_{s}_vcm{vcm:g}.net"
            f.write_text(t08_net(sid, p, 100, vcm))
            written.append(f)
        f = NET / f"t09_{s}_ac.net"
        f.write_text(t09_ac_net(sid, p))
        written.append(f)
        for ft, fc, sg, d, dt_ in T09_FOLDS:
            f = NET / f"t09_{s}_fold_{ft}_{sg}{dt_}.net"
            f.write_text(t09_fold_net(sid, p, fc, sg, d))
            written.append(f)
        for f0, tag in ((1e3, "f1k"), (16e3, "f16k")):
            f = NET / f"thd_{s}_{tag}.net"
            f.write_text(thd_net(sid, p, f0))
            written.append(f)
    return written


# ======================================================================
# 7. 运行（ltspice-sim；锁超时顺序重试；缓存跳过）
# ======================================================================
PRINT_LOCK = threading.Lock()


def run_core(net: Path, timeout: int) -> tuple[bool, str]:
    """run_all.run_net 同判定逻辑，但显式传 ltspice-sim --timeout
    （其内部默认 300s 会杀掉 THD 长仿真；锁排队内建，超时由本函数上层重试）。"""
    log, raw = net.with_suffix(".log"), net.with_suffix(".raw")
    if log.exists() and raw.exists() and "Total elapsed time" in log.read_text(errors="replace") \
            and raw.stat().st_mtime > net.stat().st_mtime:
        return True, "cached (log+raw fresh)"
    t0 = time.time()
    try:
        r = subprocess.run([run_all.LTSPICE_SIM, "--timeout", str(timeout),
                            "run", str(net)],
                           capture_output=True, text=True, timeout=timeout + 120)
    except subprocess.TimeoutExpired:
        return False, f"TIMEOUT after {timeout + 120}s (subprocess)"
    out = (r.stdout or "") + (r.stderr or "")
    sim_done = (log.exists() and raw.exists()
                and "Total elapsed time" in log.read_text(errors="replace")
                and raw.stat().st_mtime > t0)
    if sim_done:
        note = "" if r.returncode == 0 else \
            f"NOTE ltspice-sim rc={r.returncode} (post-parse crash on complex ASCII raw; sim itself completed): {out.strip()[-160:]}"
        return True, note
    return False, out.strip()[-1500:]


def run_one(net: Path, timeout: int, retries: int = 2):
    out = ""
    for attempt in range(retries + 1):
        ok, out = run_core(net, timeout)
        if ok:
            log, raw = net.with_suffix(".log"), net.with_suffix(".raw")
            shutil.copy2(log, LOGD / log.name)
            if raw.exists():
                shutil.copy2(raw, RAWD / raw.name)
            with PRINT_LOCK:
                extra = f" [{out[:100]}]" if out else ""
                print(f"[run] {net.name}: ok{extra}", flush=True)
            return net.name, True, out
        if attempt < retries:
            with PRINT_LOCK:
                print(f"[run] {net.name}: attempt {attempt+1} failed "
                      f"({out[:120]}), retry in 30s", flush=True)
            time.sleep(30)
    with PRINT_LOCK:
        print(f"[run] {net.name}: FAILED {out[:200]}", flush=True)
    log = net.with_suffix(".log")
    if log.exists():
        shutil.copy2(log, LOGD / log.name)
    return net.name, False, out


def all_jobs():
    jobs = []
    for sid in SCHEMES:
        s = SID[sid]
        for scen in T04_SCENS:
            jobs.append((NET / f"t04_{s}_{scen}.net", 600))
        for ron in (1, 100, 1000):
            jobs.append((NET / f"t08_{s}_ron{ron:g}.net", 1200))
        for vcm in (0.0, 2.0):
            jobs.append((NET / f"t08_{s}_vcm{vcm:g}.net", 1200))
        jobs.append((NET / f"t09_{s}_ac.net", 600))
        for ft, fc, sg, d, dt_ in T09_FOLDS:
            jobs.append((NET / f"t09_{s}_fold_{ft}_{sg}{dt_}.net",
                         1800 if d == 1e3 else 1200))
        for tag in ("f1k", "f16k"):
            jobs.append((NET / f"thd_{s}_{tag}.net", 1800))
    return jobs


def cmd_run(only: list[str] | None = None, workers: int = 6):
    jobs = all_jobs()
    if only:
        pats = tuple(only)
        jobs = [j for j in jobs if any(p in j[0].name for p in pats)]
    print(f"[plan] {len(jobs)} sims, workers={workers}")
    t0 = time.time()
    fails = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for name, ok, out in ex.map(lambda j: run_one(*j), jobs):
            if not ok:
                fails.append((name, out))
    print(f"[run] done in {time.time()-t0:.0f}s, fails={len(fails)}")
    for n, o in fails:
        print(f"  FAIL {n}: {o[:200]}")
    return fails


# ======================================================================
# 8. 提取器
# ======================================================================
def _load_tran(rawpath):
    r = Raw(str(rawpath))
    t = np.array([v.real if isinstance(v, complex) else v for v in r.cols[0]], dtype=float)
    return r, t


def settle_bands(rawpath, pa, na, t_edge_end, bands):
    """带外最后出带法（家法），多带一次算出；相对实际终值。"""
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


def parse_meas_tran(path) -> dict:
    """LTspice .meas TRAN log 行：`name: V(x,y)=1.23 at 2.9e-04` / `name: 1.23 FROM...`。"""
    out = {}
    path = Path(path)
    if not path.exists():
        return out
    for line in path.read_text(errors="replace").splitlines():
        s = line.strip()
        m = re.match(r"^(\w+):", s)
        if not m:
            continue
        mv = re.search(r"=([-\d.eE+]+)", s)
        if mv is None:
            mv = re.match(r"^\w+:\s+([-\d.eE+]+)", s)
        if mv:
            try:
                out[m.group(1)] = float(mv.group(1))
            except ValueError:
                pass
    return out


def kickback_extract(rawpath, pins, t_skip=8e-6, tol=1e-4):
    """D9 口径（家法）：每半周期窗 [k·T, k·T+TON] 与 [k·T+T/2, ...+TON]；
    **每个窗内对所有 pins 节点**取统计（P 主踢经 R2 传到节点1、N 踢经 Kelvin 梯形传到
    节点1——二阶两节点在两窗均受扰，故全部入表）。v_ss = 窗末 10% 均值；
    kick = 窗沿 ±2ns 台阶；残余 = 窗末点 vs v_ss。
    chan 判据用通道差分稳态 dm_v（P 主脚 − N 主脚尾部均值）。"""
    r, t = _load_tran(rawpath)
    curves = {n: np.array(r.col(f"V({n})"), dtype=float) for _, n in pins}
    m_tail = t >= t[-1] - 2e-6
    dm_v = float(np.mean(curves[pins[0][1]][m_tail]) - np.mean(curves[pins[1][1]][m_tail]))
    rows = []
    k = 0
    while True:
        t0 = k * T_MOD
        if t0 + T_MOD / 2 + TON > t[-1] - 2 * T_MOD:
            break
        if t0 >= t_skip:
            for ph, t_on in (("A", t0), ("B", t0 + T_MOD / 2)):
                for name, node in pins:
                    v = curves[node]
                    m = (t >= t_on) & (t <= t_on + TON)
                    if m.sum() < 20:
                        continue
                    seg_t, seg_v = t[m], v[m]
                    ntail = max(5, int(0.10 * len(seg_v)))
                    v_ss = float(np.mean(seg_v[-ntail:]))
                    amp = abs(float(np.interp(t_on + 2e-9, t, v))
                              - float(np.interp(t_on - 2e-9, t, v)))
                    e_end = abs(float(seg_v[-1]) - v_ss)
                    rows.append(dict(k=k, phase=ph, node=node, v_ss=v_ss,
                                     kick_amp_uv=amp * 1e6, resid_end_uv=e_end * 1e6,
                                     resid_max_uv=float(np.max(np.abs(seg_v - v_ss))) * 1e6,
                                     rel_to_ss=e_end / abs(v_ss) if v_ss else 0.0,
                                     rel_to_ch=e_end / abs(dm_v) if dm_v else 0.0,
                                     resid_lsb=e_end / LSB_V,
                                     pass01=bool(e_end <= tol * abs(v_ss))))
        k += 1
    stat = {}
    for ph in ("A", "B"):
        vss = [x["v_ss"] for x in rows if x["phase"] == ph and x["node"] == pins[0][1]][-4:]
        stat[ph] = (max(vss) - min(vss)) * 1e6 if len(vss) >= 2 else float("nan")
    worst = {}
    for key in {x["node"] for x in rows}:
        cand = [x for x in rows if x["node"] == key]
        worst[key] = max(cand, key=lambda x: x["rel_to_ch"]) if cand else None
    return rows, worst, stat, dm_v


def fold_extract(rawpath, delta, t_skip=15e-6):
    """采样序列（csa1 A 相窗末 / csb1 B 相窗末 各 2ns 均值）→ LSQ 拟合 delta 分量。"""
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


def sinc3_db(f, fmod=FMOD, osr=OSR):
    n = round(f / fmod)
    d = abs(f - n * fmod)
    if d < 1e-9:
        return 0.0
    x = math.pi * d / fmod
    m = abs(math.sin(osr * x) / (osr * math.sin(x)))
    return 20 * math.log10(m ** 3)


def parse_four_log(path) -> dict:
    """解析 LTspice .four 输出：{trace: {thd_pct, harmonics: {n: (amp, amp_norm, phase_deg)}}}。"""
    out: dict[str, dict] = {}
    path = Path(path)
    if not path.exists():
        return out
    cur = None
    for line in path.read_text(errors="replace").splitlines():
        s = line.strip()
        m = re.search(r"Fourier components of (.+)$", s)
        if m:
            cur = m.group(1).strip()
            out[cur] = {"thd_pct": None, "harmonics": {}}
            continue
        if cur:
            mm = re.match(r"^(\d+)\s+([\d.eE+-]+)\s+([\d.eE+-]+)\s+([\d.eE+-]+)\s+([-+\d.eE]+)", s)
            if mm and not s.lower().startswith(("number", "harmonic")):
                # 行格式：序号 频率 Fourier分量 归一化 相位 → 存 (amp, amp_norm, phase)
                out[cur]["harmonics"][int(mm.group(1))] = (
                    float(mm.group(3)), float(mm.group(4)), float(mm.group(5)))
                continue
            mt = re.search(r"Total Harmonic Distortion:\s*([\d.eE+-]+)\s*%?", s)
            if mt:
                out[cur]["thd_pct"] = float(mt.group(1))
                continue
            if re.match(r"^N-Period", s) or s.startswith("."):
                continue
    return out


# ======================================================================
# 9. 提取主流程 → CSV
# ======================================================================
def _old_rows(csvname: str) -> dict:
    """只读引用上一轮 CSV（S0↔FO1_BASE，S1↔FO1_A 电气等同）→ {(case,key): row}。"""
    f = OLD / "csv" / csvname
    if not f.exists():
        return {}
    with f.open(encoding="utf-8") as fh:
        return {(r.get("case", ""), r.get("scenario", r.get("tag", r.get("fold", "")))): r
                for r in csv.DictReader(fh)}


def extract_t04():
    rows = []
    old = _old_rows("t04_settling.csv")
    for sid in SCHEMES:
        s = SID[sid]
        old_case = {"S0": "FO1_BASE", "S1": "FO1_A"}.get(sid, "")
        for scen in T04_SCENS:
            raw = RAWD / f"t04_{s}_{scen}.raw"
            meas = parse_meas_tran(LOGD / f"t04_{s}_{scen}.log")
            if not raw.exists():
                rows.append(dict(scheme=sid, scenario=scen, ts10_us="NOT VERIFIED",
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
            old_ts01 = old.get((old_case, scen), {}).get("ts01_us", "") if old_case else ""
            rows.append(dict(
                scheme=sid, scenario=scen,
                step=("CH0 ±0.355V@CM2V" if scen != "ch1" else f"CH1 0→{VSENSE:.4f}V"),
                band10_uv=round(b10, 2), band01_uv=round(b01, 2),
                ts10_us=round(res[f"ts_{b10:.4g}uv"], 3),
                ts01_us=round(res[f"ts_{b01:.4g}uv"], 3),
                vfinal_v=round(res["vfinal_v"], 6),
                err_end_uv=round(res["err_end_uv"], 3),
                meas_vfin_v=meas.get("vfin", ""),
                anchor01_us=old_ts01, note=note,
                method="raw 带外最后出带法（相对实际终值，沿 10µs/10ns 后起计）；"
                       ".tran 300µs dt=10n；S0/S1 锚=fo1_rc_review 同名角点（电气等同）"))
    out = CSVD / "t04_settling.csv"
    with out.open("w", newline="\n", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"[csv] {out.name} ({len(rows)} rows)")
    return rows


def extract_t08():
    rows = []
    for sid in SCHEMES:
        s = SID[sid]
        topo2 = SCHEMES[sid]["topo"] == 2
        for tag in ["ron1", "ron100", "ron1000", "vcm0", "vcm2"]:
            ron = 100 if tag.startswith("vcm") else float(tag[3:])
            vcm = float(tag[3:]) if tag.startswith("vcm") else 0.6
            raw = RAWD / f"t08_{s}_{tag}.raw"
            meas = parse_meas_tran(LOGD / f"t08_{s}_{tag}.log")
            if not raw.exists():
                rows.append(dict(scheme=sid, tag=tag, node="*", note="sim failed"))
                continue
            pins = [("a1p", "a1p"), ("na1", "na1")]
            if topo2:
                pins += [("n1a_node1", "n1a"), ("n1n_node1", "n1n")]
            kb, worst, stat, dm_v = kickback_extract(raw, pins)
            for key in [n for _, n in pins]:
                sub = [x for x in kb if x["node"] == key]
                if not sub:
                    continue
                wkick = max(sub, key=lambda x: x["kick_amp_uv"])     # 最大踢幅（真实踢回事件）
                wres = max(sub, key=lambda x: x["resid_end_uv"])      # 最坏窗末残余
                allp = all(x["pass01"] for x in sub)
                is_pin = key in ("a1p", "na1")
                rows.append(dict(
                    scheme=sid, tag=tag, ron_ohm=ron, vcm_v=vcm,
                    node=("pin" if is_pin else "node1"),
                    node_name=key, n_windows=len(sub), dm_ss_v=round(dm_v, 6),
                    v_ss_v=round(float(np.mean([x["v_ss"] for x in sub])), 6),
                    kick_amp_uv=round(wkick["kick_amp_uv"], 2),
                    resid_end_uv=round(wres["resid_end_uv"], 3),
                    resid_end_lsb=round(wres["resid_lsb"], 2),
                    rel_to_ss=f"{wres['rel_to_ss']:.3e}",
                    pass01_ownss=allp,
                    rel_to_ch=f"{wres['rel_to_ch']:.3e}",
                    pass01_ch=bool(wres["rel_to_ch"] <= 1e-4),
                    meas_vpa_end_v=meas.get("vpa_end", ""),
                    meas_vna_end_v=meas.get("vna_end", ""),
                    tail_vss_spread_uv=round(stat.get("A", float("nan")), 3) if is_pin else "",
                    note=("D9 双判据：ownss=残余≤0.01%·|本脚v_ss|；chan=≤0.01%·|通道差分稳态|"
                          "（主判据）；kick=全窗最大踢幅、resid=最坏窗末残余；node1=二阶 R1/CG1 "
                          "节点回稳单看；Ron/vcm 声明假设")))
    out = CSVD / "t08_kickback.csv"
    with out.open("w", newline="\n", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"[csv] {out.name} ({len(rows)} rows)")
    return rows


def extract_t09():
    import cmath
    rows, folds = [], {}
    for sid in SCHEMES:
        s = SID[sid]
        raw = RAWD / f"t09_{s}_ac.raw"
        meas_m = {}
        logp = LOGD / f"t09_{s}_ac.log"
        if logp.exists():
            for line in logp.read_text(errors="replace").splitlines():
                mm = re.match(r"^(r\d+):\s+[^=]+?=\(([-\d.eE+]+)dB", line.strip())
                if mm:
                    meas_m[mm.group(1)] = float(mm.group(2))
        if not raw.exists():
            for f in t09_freqs():
                rows.append(dict(scheme=sid, f_inj_hz=f, note="sim failed"))
            continue
        r = Raw(str(raw))
        for i, f in enumerate(t09_freqs()):
            vp = interp_at(r, f, "V(a1p)")
            vn = interp_at(r, f, "V(na1)")
            dm = vp - vn
            dmp = vp - vn * cmath.exp(-2j * math.pi * f * T_MOD / 2)
            s3 = sinc3_db(f)
            rows.append(dict(
                scheme=sid, f_inj_hz=fmt(f),
                meas_r_db=meas_m.get(f"r{i}", ""),
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
                note="注入=1V AC @B 跟随器输入；phased=两侧反相采样修正(主口径)；"
                     "sinc³ 离线公式（OSR=32），非 LTspice 数字内核"))
    out = CSVD / "t09_ac_residual.csv"
    with out.open("w", newline="\n", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"[csv] {out.name} ({len(rows)} rows)")
    return rows


def extract_t09_folds():
    rows = []
    # AC 预测交叉表（同频点）：(scheme, finj) → (phased µV@100mV, dm µV@100mV)
    ac_pred = {}
    acr = CSVD / "t09_ac_residual.csv"
    if acr.exists():
        for r in csv.DictReader(acr.open(encoding="utf-8")):
            try:
                ac_pred[(r["scheme"], round(float(r["f_inj_hz"]), 1))] = (
                    float(r["alias_phased_uv_at100mV"]),
                    float(r["resid_dm_uv_at100mV"]))
            except (ValueError, KeyError):
                pass
    for sid in SCHEMES:
        s = SID[sid]
        for ft, fc, sg, d, dt_ in T09_FOLDS:
            raw = RAWD / f"t09_{s}_fold_{ft}_{sg}{dt_}.raw"
            if not raw.exists():
                rows.append(dict(scheme=sid, fold=f"{ft}_{sg}{dt_}", note="sim failed"))
                continue
            finj = fc + d if sg == "p" else fc - d
            ts, sm, amp, off, rrms = fold_extract(raw, d, t_skip=20e-6 if d == 1e3 else 15e-6)
            s3 = sinc3_db(d)
            pred = ac_pred.get((sid, round(finj, 1)))
            rows.append(dict(
                scheme=sid, fold=f"{ft}_{sg}{dt_}",
                n_samples=len(ts),
                inj=(f"100mV @{'4.096' if ft=='f4m' else '16.384'}M{'+' if sg=='p' else '-'}{dt_}Hz"
                     f"（B 跟随器输入, vcm=0.6, Ron=100Ω 假设）"),
                fitted_alias_uv=round(amp * 1e6, 3),
                ac_pred_phased_uv=round(pred[0], 3) if pred else "",
                fit_over_ac_pred=round(amp * 1e6 / pred[0], 3) if pred and pred[0] > 0 else "",
                sinc3_db_at_delta=round(s3, 3),
                output_alias_uv=round(amp * (10 ** (s3 / 20)) * 1e6, 3),
                lsb_uv=round(LSB_V * 1e6, 3),
                alias_in_lsb=round(amp * (10 ** (s3 / 20)) / LSB_V, 1),
                rel_to_vsense_ppm=round(amp * (10 ** (s3 / 20)) / VSENSE * 1e6, 2),
                fit_resid_rms_uv=round(rrms * 1e6, 3),
                layer="L3：采样序列 LTspice 实测 + sinc³ 离线换算（声明，非 LTspice 数字内核）；"
                      "fit_over_ac_pred 显著偏离 1 处=交流相位模型近完全对消失效，以实测为准"))
    out = CSVD / "t09_fold_check.csv"
    with out.open("w", newline="\n", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"[csv] {out.name} ({len(rows)} rows)")
    return rows


def extract_thd():
    rows = []
    for sid in SCHEMES:
        s = SID[sid]
        for f0, tag in ((1e3, "f1k"), (16e3, "f16k")):
            logp = LOGD / f"thd_{s}_{tag}.log"
            meas = parse_meas_tran(logp)
            four = parse_four_log(logp)
            key_pin = next((k for k in four if "a1p" in k), None)
            key_fbp = next((k for k in four if "fbp" in k), None)
            key_src = next((k for k in four if "vb" in k), None)
            if not key_pin:
                rows.append(dict(scheme=sid, f0_hz=f0, note="sim failed or no .four output"))
                continue
            hp = four[key_pin]["harmonics"]
            fund = hp.get(1, (float("nan"),) * 3)[0]
            thd_total_pct = four[key_pin]["thd_pct"]
            # 2–10 次谐波真失真（rss/基波）——LTspice "Total" 行含 4.096MHz 开关纹波
            # （=基波 256/4096 次谐波）泄漏，须分开报告
            amps = [hp[n][0] for n in hp if 2 <= n <= 10]
            harm_rss_v = math.sqrt(sum(a * a for a in amps)) if amps else 0.0
            thd_h2_10_pct = (harm_rss_v / fund * 100) if fund and fund > 0 else None
            harm_uv = {n: hp[n][0] * 1e6 for n in hp if n >= 2}
            dom_n = max(harm_uv, key=lambda n: harm_uv[n]) if harm_uv else None
            rows.append(dict(
                scheme=sid, f0_hz=f0,
                fundamental_pin_v=round(fund, 6),
                thd_total_pct=thd_total_pct,
                thd_h2_10_pct=round(thd_h2_10_pct, 8) if thd_h2_10_pct is not None else "",
                thd_h2_10_db=round(20 * math.log10(thd_h2_10_pct / 100), 1)
                if thd_h2_10_pct and thd_h2_10_pct > 0 else "",
                dominant_harm=dom_n,
                dominant_harm_uv=round(harm_uv[dom_n], 4) if dom_n else "",
                harm_h2_10_uv=round(harm_rss_v * 1e6, 4),
                harm_h2_10_lsb=round(harm_rss_v / LSB_V, 4),
                harm_h2_10_pct_fs=round(harm_rss_v / (2 * 2.442) * 100, 9),
                floor_src_thd_pct=(four.get(key_src, {}) or {}).get("thd_pct", "") if key_src else "",
                floor_src_harm2_uv=(four[key_src]["harmonics"].get(2, (float("nan"),))[0] * 1e6
                                    if key_src and 2 in four[key_src]["harmonics"] else ""),
                meas_vpp_pin_v=meas.get("vpp_pin", ""),
                thd_fbp_total_pct=(four.get(key_fbp, {}) or {}).get("thd_pct", "") if key_fbp else "",
                thd_fbp_h2_10_pct=(round(math.sqrt(sum(
                    four[key_fbp]["harmonics"][n][0] ** 2 for n in four[key_fbp]["harmonics"]
                    if 2 <= n <= 10)) / four[key_fbp]["harmonics"][1][0] * 100, 8)
                    if key_fbp and 1 in four[key_fbp]["harmonics"] else ""),
                note="CH1 口径（P=OPA388 驱动、N=Kelvin 纯 RC，非对称最坏）；激励 1.1786V+0.5V·sin；"
                     "负载=各案 RC+fsadckb 实时针（Ron=100/vcm=0.6 假设）；.four 10 谐波窗=1ms"
                     "=4096 采样周期正交；thd_total=LTspice Total 行（含 4.096MHz 开关纹波泄漏，"
                     "=基波 256/4096 次谐波），thd_h2_10=2–10 次谐波 rss（真带内失真）；"
                     "判决门未设 → 谐波和按 LSB(291.11nV)/FS 换算给参考；floor_src=理想输入源"))
    out = CSVD / "thd_summary.csv"
    with out.open("w", newline="\n", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"[csv] {out.name} ({len(rows)} rows)")
    return rows


# ======================================================================
# 10. 图（文件名含方案ID+测试ID）
# ======================================================================
def make_plots():
    # T04 汇总
    fig, ax = plt.subplots(figsize=(10, 5.5))
    wid = 0.12
    sids = list(SCHEMES)
    for i, sid in enumerate(sids):
        s = SID[sid]
        vals = []
        for scen in T04_SCENS:
            raw = RAWD / f"t04_{s}_{scen}.raw"
            if not raw.exists():
                vals.append(float("nan"))
                continue
            if scen == "ch1":
                res, _ = settle_bands(raw, "V(a1p)", "V(na1)", 10.01e-6, (VSENSE * 1e-4,))
                v = res[f"ts_{VSENSE*1e2:.4g}uv"]
            else:
                res, _ = settle_bands(raw, "V(pa1)", "V(na1)", 10.01e-6, (71e-6,))
                v = res["ts_71uv"]
            vals.append(v)
        ax.bar(np.arange(len(T04_SCENS)) + i * wid, vals, wid, label=sid)
    ax.set_xticks(np.arange(len(T04_SCENS)) + 2.5 * wid)
    ax.set_xticklabels(T04_SCENS, rotation=20)
    ax.set_ylabel("0.01% 建立时间 (µs)")
    ax.set_yscale("log")
    ax.set_title("T04 0.01% 建立时间（带外最后出带法；S0/S1=一阶，T1–T4=二阶）")
    ax.legend(fontsize=8, ncol=6)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(PLOTD / "t04_all_ts01_summary.png", dpi=110)
    plt.close(fig)

    for sid in sids:
        s = SID[sid]
        fig, ax = plt.subplots(figsize=(8, 5))
        for scen in T04_SCENS:
            raw = RAWD / f"t04_{s}_{scen}.raw"
            if not raw.exists():
                continue
            if scen == "ch1":
                _, (tt, dd, vf) = settle_bands(raw, "V(a1p)", "V(na1)", 10.01e-6,
                                               (VSENSE * 1e-4,))
                band01 = VSENSE * 1e2
            else:
                _, (tt, dd, vf) = settle_bands(raw, "V(pa1)", "V(na1)", 10.01e-6, (71e-6,))
                band01 = 71.0
            err = np.abs(dd - vf)
            m = err > 0
            ax.semilogy((tt[m] - 10.01e-6) * 1e6, err[m] * 1e6, lw=1, label=scen)
        ax.axhline(71, color="r", ls="--", lw=1, label="71µV (CH0 0.01%)")
        ax.axhline(710, color="orange", ls=":", lw=1, label="710µV (CH0 0.1%)")
        ax.set_xlabel("自阶跃沿起计 (µs)")
        ax.set_ylabel("|差分误差| (µV)")
        ax.set_title(f"t04_{s} 建立误差衰减（对数）")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3, which="both")
        fig.tight_layout()
        fig.savefig(PLOTD / f"t04_{s}_settle_curves.png", dpi=110)
        plt.close(fig)

        # T08 kick wave（ron100 主角）
        raw = RAWD / f"t08_{s}_ron100.raw"
        if raw.exists():
            topo2 = SCHEMES[sid]["topo"] == 2
            pins = [("a1p", "a1p"), ("na1", "na1")]
            kb, worst, stat, dm_v = kickback_extract(raw, pins, t_skip=20e-6)
            if kb:
                r, t = _load_tran(raw)
                P = np.array(r.col("V(a1p)"), dtype=float)
                N = np.array(r.col("V(na1)"), dtype=float)
                k_last = kb[-1]["k"]
                t0 = k_last * T_MOD
                vA = np.mean(P[-50:])
                vB = np.mean(N[-50:])
                m = (t >= t0 - 0.3 * T_MOD) & (t <= t0 + 1.3 * T_MOD)
                fig, ax = plt.subplots(figsize=(8, 5))
                ax.plot((t[m] - t0) * 1e9, (P[m] - vA) * 1e6, lw=1, label="V(a1p)−v_ss")
                ax.plot((t[m] - t0) * 1e9, (N[m] - vB) * 1e6, lw=1, label="V(na1)−v_ss")
                if topo2:
                    N1 = np.array(r.col("V(n1a)"), dtype=float)
                    ax.plot((t[m] - t0) * 1e9, (N1[m] - np.mean(N1[-50:])) * 1e6, lw=1,
                            label="V(n1a)−v_ss（节点1）")
                for ph, t_on, col in (("A 相窗(P)", 0, "tab:blue"),
                                      ("B 相窗(N)", T_MOD / 2, "tab:orange")):
                    ax.axvspan(t_on * 1e9, (t_on + TON) * 1e9, alpha=0.08, color=col)
                ax.axhline(abs(dm_v) * 1e6 * 1e-4, color="r", ls="--", lw=0.8,
                           label="+0.01%·|dm|")
                ax.axhline(-abs(dm_v) * 1e6 * 1e-4, color="r", ls="--", lw=0.8)
                ax.set_xlabel("自末周期起点起计 (ns)")
                ax.set_ylabel("引脚对稳态偏差 (µV)")
                ax.set_title(f"t08_{s} kickback（Ron=100Ω, vcm=0.6V, 末两相窗）")
                ax.legend(fontsize=8)
                ax.grid(alpha=0.3)
                fig.tight_layout()
                fig.savefig(PLOTD / f"t08_{s}_kick_wave.png", dpi=110)
                plt.close(fig)

        # T09 AC 残差棒图
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
            ax.set_title(f"t09_{s} 高频注入→引脚残差（L2 AC，断态负载）")
            ax.grid(alpha=0.3, axis="y")
            fig.tight_layout()
            fig.savefig(PLOTD / f"t09_{s}_ac_residual.png", dpi=110)
            plt.close(fig)

        # T09 fold 采样序列（两族各取 +8k 代表）
        for ft, lab in (("f4m", "4.104M"), ("f16m", "16.392M")):
            raw = RAWD / f"t09_{s}_fold_{ft}_p8k.raw"
            if not raw.exists():
                continue
            ts, sm, amp, off, rrms = fold_extract(raw, 8e3)
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
            ax.set_title(f"t09_{s} 折叠实测（100mV@{lab} 注入）")
            ax.legend(fontsize=8)
            ax.grid(alpha=0.3)
            fig.tight_layout()
            fig.savefig(PLOTD / f"t09_{s}_fold_{ft}_p8k.png", dpi=110)
            plt.close(fig)

        # THD 频谱棒图
        for f0, tag in ((1e3, "f1k"), (16e3, "f16k")):
            logp = LOGD / f"thd_{s}_{tag}.log"
            four = parse_four_log(logp)
            key_pin = next((k for k in four if "a1p" in k), None)
            if not key_pin:
                continue
            hp = four[key_pin]["harmonics"]
            ns = sorted(n for n in hp if 1 <= n <= 10)
            fig, ax = plt.subplots(figsize=(8, 5))
            ax.bar(ns, [20 * math.log10(hp[n][0]) if hp[n][0] > 0 else -160 for n in ns])
            ax.axhline(20 * math.log10(LSB_V), color="r", ls="--", lw=1,
                       label=f"1 LSB = {20*math.log10(LSB_V):.1f} dBV")
            ax.set_xlabel("谐波次数（基波 %g kHz）" % (f0 / 1e3))
            ax.set_ylabel("谐波幅度 (dBV)")
            ax.set_title(f"thd_{s}_{tag}：引脚谐波谱（.four，窗=2ms 正交）")
            ax.legend(fontsize=8)
            ax.grid(alpha=0.3, axis="y")
            fig.tight_layout()
            fig.savefig(PLOTD / f"thd_{s}_{tag}_spectrum.png", dpi=110)
            plt.close(fig)


# ======================================================================
# 11. lint（静态体检：include 存在性 + 器件名唯一 + 拓扑行核对）
# ======================================================================
def cmd_lint() -> int:
    bad = 0
    for f in sorted(list(NET.glob("t04_*.net")) + list(NET.glob("t08_*.net"))
                    + list(NET.glob("t09_*.net")) + list(NET.glob("thd_*.net"))):
        errs = run_all.lint_netlist(f)
        if errs:
            print(f"[lint] {f.name}: {errs}")
            bad += len(errs)
    print(f"[lint] done, {bad} errors" if bad else "[lint] all OK")
    return 1 if bad else 0


# ======================================================================
def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("cmd", nargs="?", default="all",
                    choices=["gen", "lint", "run", "extract", "all", "pilot"])
    ap.add_argument("--only", nargs="*", default=None, help="网表名子串过滤（run 用）")
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()
    if args.cmd in ("gen", "lint", "all", "pilot"):
        w = gen_all()
        print(f"[gen] {len(w)} netlists")
    if args.cmd == "lint":
        return cmd_lint()
    if args.cmd in ("run", "all", "pilot"):
        only = args.only
        if args.cmd == "pilot":
            only = ["t04_t2_nom", "t08_t2_ron100", "thd_t2_f1k", "t09_t2_ac"]
        fails = cmd_run(only=only, workers=args.workers)
        if args.cmd == "all" and fails:
            print("[all] 存在失败仿真，继续提取（失败项标 NOT VERIFIED）")
    if args.cmd in ("extract", "all"):
        extract_t04()
        extract_t08()
        extract_t09()
        extract_t09_folds()
        extract_thd()
        make_plots()
        print("[extract] done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
