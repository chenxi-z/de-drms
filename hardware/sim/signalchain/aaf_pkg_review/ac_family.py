#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ac_family.py — aaf_pkg_review AC 测试族（T01/T02/T03/T10 + L3 离线；任务书 2026-10-24 §3/§5(3)(4)(5)）

六方案批跑（S0/S1 一阶、T1–T4 二阶），三层口径（L1/L2/L3 不得混谈，fo1 assumptions.md §B）：
  L1 理想源     t01_{sid}_dm_ideal / t02_{sid}_cm_ideal  0Ω 理想源直驱 RC + 130k/5p 负载（LTspice 实跑，
               与 run_all.py L1 MNA 引擎、任务书 §3 表三方对拍；§3 表负载=130k 纯差分无采样开关，
               偏差解释而非凑数——run_all L1 引擎含 5p/端已复现 §3 全表 ≤0.001 dB，见 smoke_anchor.csv）
  L2 真实 OPA388 t01_{sid}_dm_opa388 / t02_{sid}_cm_opa388  双 OPA388 对称（sm 台架同口径，meas 扩展
               fc/8k/16k 幅相/peaking/折叠点）
               t01_{sid}_dm_kelvin / t02_{sid}_cm_kelvin  CH1 真实接线：1×OPA388(P线) + AIN1N 经 RC
               直连 Rsense 底端 E（铁律：无第四运放；fo1 A13 口径：DC 共模 2V 偏置）
  L2 整链 Kelvin t02_{sid}_cm_full / t03_{sid}_fc_rs{1k,10k,47k,120k}
               恒流源(fsrc,OPA333t) + 3×OPA388(fsfo1/fsfo2) + fsadc×2 + dut 寄生(A4: 200p/端+30p 线间)
               开关态=测量态 DC（K1/S3 通、K2/S4 断、电流源开）；DM 激励=Iac 1A 串入 t→DUT（线性网络
               归一化）；CM 激励=Vint 1V 经 dut 对地寄生电容耦合进 t/s（线缆共模物理路径）
               —— CMRR『整链 Kelvin』口径 = G_dm/G_cmdm（G_dm 以 V(t2)−V(s) 为输入，G_cmdm 以 V(vint) 为输入）
  T10 群延迟    无新网表：raw 相位微分（1k/8k/16k）+ 整链 CH0/CH1 同激励相位失配
  L3 离线       纯 Python：sinc³ H(z)=[(1−z⁻³²)/(32(1−z⁻¹))]³（fMOD=4.096M、OSR=32 全局同设，
               A11 口径，四锚点自证）× 模拟 Hratio / 4.096M±{1k,8k,16k} 折叠（AAF 残留取 t01 raw
               实测插值，非斜率修正）——**非 LTspice 数字内核仿真**，折叠增益按最坏 0 dB（A12）

锚定对拍（容差 0.5 dB）：S0_D1=40.69 / S0_D2=46.41(0.5V 绝对) / S1_D1=38.72 / S1_D2=38.11(1V 归一)
—— 同 sm 台架 ANCHOR；本轮 cm 网表统一 0.5V 激励（t00 口径）。

用法：python3 ac_family.py {gen,lint,probe,run,analyze,l3,all}
产物：netlists/t*.net（gitignore 再生）、logs/ raw/ 归档、csv/{t01_dm_ac,t02_cm_ac,t02_cm_full,
      t03_channel_match,t10_group_delay,l3_sinc3_alias}.csv、plots/t*.png
"""
from __future__ import annotations

import argparse
import csv
import math
import re
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

sys.dont_write_bytecode = True          # 不在任何目录留 __pycache__
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, "/media/anning/data/Project/DE-DRMS/hardware/sim/aaf")

import run_all          # noqa: E402  台架：SCHEMES / run_net / fmt / _l1_h / l1_metrics
import parse_r5         # noqa: E402  复数 AC raw 解析（smoke 已验证）

NET = HERE / "netlists"
LOGD = HERE / "logs"
RAWD = HERE / "raw"
CSVD = HERE / "csv"
PLOTD = HERE / "plots"

SCHEMES = run_all.SCHEMES
STEM = {k: k.lower() for k in SCHEMES}
LIB = run_all.LIB
FMOD, MCLK = run_all.FMOD, run_all.MCLK
AC = ".ac dec 400 0.1 200Meg\n"
OPTS = (".options plotwinsize=0 reltol=1e-6 abstol=1e-12 vntol=1e-9 "
        "chgtol=1e-15 trtol=1\n")
PWR = "Vcc vcc 0 DC 3.3\nVee vee 0 DC 0\n"
FOLD_OFFS = (1e3, 8e3, 16e3)
RSENSE = 150e3
# T03 DUT 扫：10k/47k/120k = 任务书 §5(5) 工作量程点名；1k = 低端扩展（设计下限 10k 之下，
# 源阻抗趋低极限；合规栈 8µA×1k+1.2V=1.21V 合法）。600k 不可运行：8µA×600k=4.8V 超 3.3V
# 合规栈（fo1 assumptions A7 同结论），不入扫——见 CSV note。
DUT_SWEEP = (1e3, 10e3, 47e3, 120e3)
FLOOR_DB = -320.0


def fmt(v: float) -> str:
    return run_all.fmt(v)


def adc_load(p: str, n: str) -> str:
    """ADS131A02 引脚无源负载：Zin 130k 差分 + C_pin 5p/端（fsadc 断态，A2/A3 声明假设）。"""
    return f"Rin {p} {n} 130000\nCpa {p} 0 5e-12\nCna {n} 0 5e-12\n"


# ======================================================================
# .meas 模板
# ======================================================================
def meas_dm(p: str, n: str, foll: str | None = None, fold: bool = True) -> str:
    v = f"V({p},{n})"
    s = (f".meas AC dm_dc   FIND mag({v}) AT=0.1\n"
         f".meas AC dm_1k   FIND mag({v}) AT=1k\n"
         f".meas AC dm_8k   FIND mag({v}) AT=8k\n"
         f".meas AC dm_16k  FIND mag({v}) AT=16k\n"
         f".meas AC dm_fmod FIND mag({v}) AT=4.096Meg\n"
         f".meas AC dm_mclk FIND mag({v}) AT=16.384Meg\n"
         f".meas AC dm_pk   MAX mag({v})\n"
         f".meas AC dm_pk_f WHEN mag({v})=dm_pk\n"
         f".meas AC ph_1k  FIND ph({v}) AT=1k\n"
         f".meas AC ph_8k  FIND ph({v}) AT=8k\n"
         f".meas AC ph_16k FIND ph({v}) AT=16k\n")
    if fold:
        for off in FOLD_OFFS:
            for sgn in ("+", "-"):
                f_ = FMOD + (off if sgn == "+" else -off)
                tag = f"{int(off/1e3)}k"
                s += f".meas AC dm_fp{tag} FIND mag({v}) AT={fmt(f_)}\n" if sgn == "+" \
                    else f".meas AC dm_fm{tag} FIND mag({v}) AT={fmt(f_)}\n"
    if foll:
        s += (f".meas AC foll_dc FIND mag(V({foll})) AT=0.1\n"
              f".meas AC foll_pk MAX mag(V({foll}))\n"
              f".meas AC foll_pk_f WHEN mag(V({foll}))=foll_pk\n")
    return s


def meas_cm(p: str, n: str, fold: bool = False) -> str:
    vd = f"V({p},{n})"
    s = (f".meas AC cm_dc   FIND mag(V({p})) AT=0.1\n"
         f".meas AC cm_1k   FIND mag(V({p})) AT=1k\n"
         f".meas AC cm_8k   FIND mag(V({p})) AT=8k\n"
         f".meas AC cm_16k  FIND mag(V({p})) AT=16k\n"
         f".meas AC cm_fmod FIND mag(V({p})) AT=4.096Meg\n"
         f".meas AC cm_mclk FIND mag(V({p})) AT=16.384Meg\n"
         f".meas AC cmdm_dc   FIND mag({vd}) AT=0.1\n"
         f".meas AC cmdm_1k   FIND mag({vd}) AT=1k\n"
         f".meas AC cmdm_8k   FIND mag({vd}) AT=8k\n"
         f".meas AC cmdm_16k  FIND mag({vd}) AT=16k\n"
         f".meas AC cmdm_fmod FIND mag({vd}) AT=4.096Meg\n")
    if fold:
        for off in FOLD_OFFS:
            for sgn in ("+", "-"):
                f_ = FMOD + (off if sgn == "+" else -off)
                tag = f"{int(off/1e3)}k"
                s += f".meas AC cm_fp{tag} FIND mag(V({p})) AT={fmt(f_)}\n" if sgn == "+" \
                    else f".meas AC cm_fm{tag} FIND mag(V({p})) AT={fmt(f_)}\n"
    return s


# ======================================================================
# 网表生成 —— 舱口径（t01/t02 三口径）
# ======================================================================
def _lad(sid: str, in_p: str, in_n: str) -> str:
    """每方案 P/N 双线 ladder（一阶=run_all.ladder_1 节点名口径；二阶=ladder_2）。"""
    p = SCHEMES[sid]
    if p["topo"] == 1:
        return (f"Ra1 {in_p} pa1 {fmt(p['r1'])}\nCa1 pa1 0 {fmt(p['cg1'])}\n"
                f"Rb1 {in_n} na1 {fmt(p['r1'])}\nCb1 na1 0 {fmt(p['cg1'])}\n")
    return (f"Ra1 {in_p} n1a {fmt(p['r1'])}\nCa1 n1a 0 {fmt(p['cg1'])}\n"
            f"Ra2 n1a pa1 {fmt(p['r2'])}\nCa2 pa1 0 {fmt(p['cg2'])}\n"
            f"Rb1 {in_n} n1b {fmt(p['r1'])}\nCb1 n1b 0 {fmt(p['cg1'])}\n"
            f"Rb2 n1b na1 {fmt(p['r2'])}\nCb2 na1 0 {fmt(p['cg2'])}\n")


def _lad_kelvin_n(sid: str, en: str) -> str:
    """Kelvin N 线（AIN1N 经 RC 直连 E，无运放）——与整链 fullchain_net Kelvin 段同构。"""
    p = SCHEMES[sid]
    if p["topo"] == 1:
        return f"RKN {en} na1 {fmt(p['r1'])}\nCGN na1 0 {fmt(p['cg1'])}\n"
    return (f"RKN1 {en} n1n {fmt(p['r1'])}\nCGN1 n1n 0 {fmt(p['cg1'])}\n"
            f"RKN2 n1n na1 {fmt(p['r2'])}\nCGN2 na1 0 {fmt(p['cg2'])}\n")


def _lad_kelvin_p(sid: str, fcc: str) -> str:
    """Kelvin P 线（1×OPA388 跟随器后接 AAF）。"""
    p = SCHEMES[sid]
    if p["topo"] == 1:
        return f"Rf {fcc} a1p {fmt(p['r1'])}\nCG a1p 0 {fmt(p['cg1'])}\n"
    return (f"Rf1 {fcc} n1p {fmt(p['r1'])}\nCG1p n1p 0 {fmt(p['cg1'])}\n"
            f"Rf2 n1p a1p {fmt(p['r2'])}\nCG2p a1p 0 {fmt(p['cg2'])}\n")


def n_dm_ideal(sid: str) -> str:
    p = SCHEMES[sid]
    return (f"* t01 {sid} dm_ideal - L1: 0ohm ideal source drives RC ladder + ADC passive load, DM 1V"
            f" ({'1st' if p['topo']==1 else '2nd'} order)\n"
            f".include {LIB}\n"
            f"Vp vp 0 DC 2 AC 0.5\nVn vn 0 DC 2 AC -0.5\n"
            + _lad(sid, "vp", "vn")
            + f"Cd pa1 na1 {fmt(p['cd'])}\n"
            + adc_load("pa1", "na1")
            + AC + OPTS + meas_dm("pa1", "na1")
            + ".save V(pa1) V(na1)\n.end\n")


def n_dm_opa388(sid: str) -> str:
    p = SCHEMES[sid]
    mid = " V(n1a) V(n1b)" if p["topo"] == 2 else ""
    return (f"* t01 {sid} dm_opa388 - L2 CH0: dual OPA388 symmetric (sm_acdm same circuit), DM 1V\n"
            f".include {LIB}\n{PWR}"
            f"Vp vp 0 DC 2 AC 0.5\nVn vn 0 DC 2 AC -0.5\n"
            f"Xfa vp fpa vcc vee fpa OPAx388\nXfb vn fna vcc vee fna OPAx388\n"
            + _lad(sid, "fpa", "fna")
            + f"Cd pa1 na1 {fmt(p['cd'])}\n"
            + adc_load("pa1", "na1")
            + AC + OPTS + meas_dm("pa1", "na1", foll="fpa")
            + f".save V(pa1) V(na1) V(fpa) V(fna){mid}\n.end\n")


def n_dm_kelvin(sid: str) -> str:
    p = SCHEMES[sid]
    return (f"* t01 {sid} dm_kelvin - L2 CH1 real wiring: 1xOPA388(P line) + AIN1N Kelvin RC to E"
            f" (no 4th opamp), DM 1V; DC bias Vbp=2.5/Ven=1.5 (fo1 A13 caliber, CM 2V aligned CH0)\n"
            f".include {LIB}\n{PWR}"
            f"Vbp bp 0 DC 2.5 AC 0.5\nVen en 0 DC 1.5 AC -0.5\n"
            f"XfB bp fcc vcc vee fcc OPAx388\n"
            + _lad_kelvin_p(sid, "fcc") + _lad_kelvin_n(sid, "en")
            + f"CD a1p na1 {fmt(p['cd'])}\n"
            + adc_load("a1p", "na1")
            + AC + OPTS + meas_dm("a1p", "na1", foll="fcc")
            + ".save V(a1p) V(na1) V(fcc)\n.end\n")


def n_cm_ideal(sid: str) -> str:
    p = SCHEMES[sid]
    return (f"* t02 {sid} cm_ideal - L1 common-mode 0.5V AC (t00 caliber) into symmetric RC + ADC load\n"
            f".include {LIB}\n"
            f"Vp vp 0 DC 2 AC 0.5\nVn vn 0 DC 2 AC 0.5\n"
            + _lad(sid, "vp", "vn")
            + f"Cd pa1 na1 {fmt(p['cd'])}\n"
            + adc_load("pa1", "na1")
            + AC + OPTS + meas_cm("pa1", "na1")
            + ".save V(pa1) V(na1)\n.end\n")


def n_cm_opa388(sid: str) -> str:
    p = SCHEMES[sid]
    return (f"* t02 {sid} cm_opa388 - L2 CH0 dual OPA388 symmetric, common-mode 0.5V AC (t00 caliber)\n"
            f".include {LIB}\n{PWR}"
            f"Vp vp 0 DC 2 AC 0.5\nVn vn 0 DC 2 AC 0.5\n"
            f"Xfa vp fpa vcc vee fpa OPAx388\nXfb vn fna vcc vee fna OPAx388\n"
            + _lad(sid, "fpa", "fna")
            + f"Cd pa1 na1 {fmt(p['cd'])}\n"
            + adc_load("pa1", "na1")
            + AC + OPTS + meas_cm("pa1", "na1", fold=True)
            + ".save V(pa1) V(na1) V(fpa) V(fna)\n.end\n")


def n_cm_kelvin(sid: str) -> str:
    p = SCHEMES[sid]
    return (f"* t02 {sid} cm_kelvin - L2 CH1 real wiring common-mode 0.5V AC: P line buffered,"
            f" N line Kelvin RC (structural mismatch, real CM-to-DM not solver floor)\n"
            f".include {LIB}\n{PWR}"
            f"Vbp bp 0 DC 2 AC 0.5\nVen en 0 DC 2 AC 0.5\n"
            f"XfB bp fcc vcc vee fcc OPAx388\n"
            + _lad_kelvin_p(sid, "fcc") + _lad_kelvin_n(sid, "en")
            + f"CD a1p na1 {fmt(p['cd'])}\n"
            + adc_load("a1p", "na1")
            + AC + OPTS + meas_cm("a1p", "na1")
            + ".save V(a1p) V(na1) V(fcc)\n.end\n")


# ======================================================================
# 网表生成 —— 整链口径（t02_cm_full / t03_fc_rs*）
# ======================================================================
FC_TMPL = """V1 ta 0 3.3
Rtop ta t 10k
Rb t 0 150k
{excite}{dut}
Rref t f 100k
Cff f 0 100p
Vk1 k1c 0 DC 1
S1 s x k1c 0 swNO
Vk2 k2c 0 DC 1
Bk2n k2n 0 V={{1-V(k2c)}}
S2 f x k2n 0 swNO
Vsen sensec 0 DC 1
Bsenn sensen 0 V={{1-V(sensec)}}
S3 s m sensec 0 swNO
S4 f m sensen 0 swNO
Vdis dis 0 DC 0
Xsrc ta b x dis fsrc
Rs b 0 150k
{aaf}CDIF0 a0p a0n {{CDO}}
CDIF1 a1p na1 {{CDO}}
Vswp vswp 0 0
Vswn vswn 0 0
Xad0 a0p a0n 0 vswp vswn fsadc
Xad1 a1p na1 0 vswp vswn fsadc
"""


def _fc_params(sid: str, rs: float) -> str:
    p = SCHEMES[sid]
    if p["topo"] == 1:
        aaf = ("XfT t ta 0 a0p fsfo1\nXfM m ta 0 a0n fsfo1\nXfB b ta 0 a1p fsfo1\n"
               "RKN 0 na1 {RFO}\nCGN na1 0 {CFO}\n")
        prm = (f".param RSAMP={fmt(rs)} CTOT=200p CTT=30p RFO={fmt(p['r1'])} "
               f"CFO={fmt(p['cg1'])} CDO={fmt(p['cd'])}\n")
    else:
        aaf = ("XfT t ta 0 a0p fsfo2\nXfM m ta 0 a0n fsfo2\nXfB b ta 0 a1p fsfo2\n"
               "RKN1 0 n1n {RF1}\nCGN1 n1n 0 {CF1}\nRKN2 n1n na1 {RF2}\nCGN2 na1 0 {CF2}\n")
        prm = (f".param RSAMP={fmt(rs)} CTOT=200p CTT=30p RF1={fmt(p['r1'])} "
               f"CF1={fmt(p['cg1'])} RF2={fmt(p['r2'])} CF2={fmt(p['cg2'])} CDO={fmt(p['cd'])}\n")
    return prm, aaf


def n_cm_full(sid: str) -> str:
    """整链 Kelvin 共模口径：Vint 1V AC 经 dut 对地寄生电容耦合进 t/s（线缆共模物理路径，
    vint DC=0 → 直流工作点与测量态相同）。dutcm = dut 变体（Ct/Cs 改接 vint）。"""
    prm, aaf = _fc_params(sid, 47e3)
    meas = (".meas AC cmo_dc   FIND mag(V(a0p)) AT=0.1\n"
            ".meas AC cmo_1k   FIND mag(V(a0p)) AT=1k\n"
            ".meas AC cmo_8k   FIND mag(V(a0p)) AT=8k\n"
            ".meas AC cmo_16k  FIND mag(V(a0p)) AT=16k\n"
            ".meas AC cmo_fmod FIND mag(V(a0p)) AT=4.096Meg\n"
            ".meas AC cmdm0_dc   FIND mag(V(a0p,a0n)) AT=0.1\n"
            ".meas AC cmdm0_1k   FIND mag(V(a0p,a0n)) AT=1k\n"
            ".meas AC cmdm0_8k   FIND mag(V(a0p,a0n)) AT=8k\n"
            ".meas AC cmdm0_16k  FIND mag(V(a0p,a0n)) AT=16k\n"
            ".meas AC cmdm0_fmod FIND mag(V(a0p,a0n)) AT=4.096Meg\n"
            ".meas AC vtc_dc   FIND mag(V(t)) AT=0.1\n"
            ".meas AC vtc_16k  FIND mag(V(t)) AT=16k\n"
            ".meas AC vtc_fmod FIND mag(V(t)) AT=4.096Meg\n")
    body = FC_TMPL.format(
        excite="Vint vint 0 DC 0 AC 1\n",
        dut=("Xdut t s vint dutcm\n"
             ".subckt dutcm tt ss vip\n"
             "Rsamp tt ss {RSAMP}\nCt tt vip {CTOT}\nCs ss vip {CTOT}\nCts tt ss {CTT}\n"
             ".ends dutcm\n"),
        aaf=aaf)
    return (f"* t02 {sid} cm_full - fullchain Kelvin CM caliber: Vint 1V via cable parasitics into t/s;"
            f" fsrc+3xOPA388+fsadc; switches frozen at measure state (DC); RSAMP=47k\n"
            f".include {HERE}/pkg_subs.inc\n{prm}{body}"
            + AC + OPTS + meas
            + ".save V(a0p) V(a0n) V(a1p) V(na1) V(t) V(s) V(m) V(b) V(vint)\n.end\n")


def n_rs_bench(sid: str, rs: float) -> str:
    """T03 舱级 real-src 口径（fo1 ac_family n_ch0_realsrc 的 DUT 扫描推广）：
    差分 1V 源经 rs/2 每侧串入 → 双 OPA388 AAF（CH0）。CH0 源阻抗 = DUT 阻值 rs；
    CH1 源阻抗 ≈0（B 点由恒流环低阻驱动、E=地）→ H1 用 t01_dm_kelvin 0Ω 口径兼任
    （fo1 同款声明近似，CSV note 注明）。"""
    p = SCHEMES[sid]
    return (f"* t03 {sid} rs={fmt(rs)} bench real-src: DM 1V via {fmt(rs/2)}/side (=DUT {fmt(rs)} floating),\n"
            f"* dual OPA388 CH0 caliber; CH1 counterpart = t01_dm_kelvin (0ohm source, same normalization)\n"
            f".include {LIB}\n{PWR}"
            f"Vsp srcp 0 DC 2 AC 0.5\nRsp srcp vp {fmt(rs/2)}\n"
            f"Vsn srcn 0 DC 2 AC -0.5\nRsn srcn vn {fmt(rs/2)}\n"
            f"Xfa vp fpa vcc vee fpa OPAx388\nXfb vn fna vcc vee fna OPAx388\n"
            + _lad(sid, "fpa", "fna")
            + f"Cd pa1 na1 {fmt(p['cd'])}\n"
            + adc_load("pa1", "na1")
            + AC + OPTS + meas_dm("pa1", "na1", foll="fpa", fold=False)
            + ".save V(pa1) V(na1) V(fpa) V(fna) V(vp) V(vn)\n.end\n")


def n_fc_vs(sid: str) -> str:
    """整链串模口径：Vex 1V AC 串在 dut 底端 s→K1 之间（DC 0 = 短路，直流工作点=测量态
    不受扰动；AC = DUT 支路 1V 串模干扰）。真实接线全保留（fsrc+3×OPA388+Kelvin RC+fsadc）。
    H0=(a0p-a0n) 含串模（m 接 s）、H1=(a1p-na1) 为串模经环路的感应。"""
    prm, aaf = _fc_params(sid, 47e3)
    meas = (".meas AC h0_dc  FIND mag(V(a0p,a0n)) AT=0.1\n"
            ".meas AC h0_1k  FIND mag(V(a0p,a0n)) AT=1k\n"
            ".meas AC h0_8k  FIND mag(V(a0p,a0n)) AT=8k\n"
            ".meas AC h0_16k FIND mag(V(a0p,a0n)) AT=16k\n"
            ".meas AC h0_fmod FIND mag(V(a0p,a0n)) AT=4.096Meg\n"
            ".meas AC h1_dc  FIND mag(V(a1p,na1)) AT=0.1\n"
            ".meas AC h1_1k  FIND mag(V(a1p,na1)) AT=1k\n"
            ".meas AC h1_8k  FIND mag(V(a1p,na1)) AT=8k\n"
            ".meas AC h1_16k FIND mag(V(a1p,na1)) AT=16k\n"
            ".meas AC h1_fmod FIND mag(V(a1p,na1)) AT=4.096Meg\n")
    body = FC_TMPL.format(
        excite="Vex s s2 DC 0 AC 1\n",
        dut="Xdut t s dut\n",
        aaf=aaf).replace("S1 s x k1c 0 swNO", "S1 s2 x k1c 0 swNO")
    return (f"* t03 {sid} fc_vs - fullchain series-mode caliber: Vex 1V AC serial in s->K1"
            f" (DC short); fsrc+3xOPA388+fsadc; RSAMP=47k\n"
            f".include {HERE}/pkg_subs.inc\n{prm}{body}"
            + AC + OPTS + meas
            + ".save V(a0p) V(a0n) V(a1p) V(na1) V(t) V(s) V(s2) V(m) V(b)\n.end\n")


GENS = {
    "t01_dm_ideal": lambda s: n_dm_ideal(s),
    "t01_dm_opa388": lambda s: n_dm_opa388(s),
    "t01_dm_kelvin": lambda s: n_dm_kelvin(s),
    "t02_cm_ideal": lambda s: n_cm_ideal(s),
    "t02_cm_opa388": lambda s: n_cm_opa388(s),
    "t02_cm_kelvin": lambda s: n_cm_kelvin(s),
    "t02_cm_full": lambda s: n_cm_full(s),
}


def gen_all() -> list[Path]:
    for d in (NET, LOGD, RAWD, CSVD, PLOTD):
        d.mkdir(exist_ok=True)
    written = []
    for sid in SCHEMES:
        for tid, fn in GENS.items():
            f = NET / f"{tid}_{STEM[sid]}.net"
            f.write_text(fn(sid))
            written.append(f)
        for rs in DUT_SWEEP:
            f = NET / f"t03_rs{int(rs/1e3)}k_{STEM[sid]}.net"
            f.write_text(n_rs_bench(sid, rs))
            written.append(f)
        f = NET / f"t03_fcvs_{STEM[sid]}.net"
        f.write_text(n_fc_vs(sid))
        written.append(f)
    return written


# ======================================================================
# lint（run_all.lint_netlist 扩展 dutcm 登记 + 舱网表激励/负载行静态断言）
# ======================================================================
LINT_SUBCKT = run_all.KNOWN_SUBCKT | {"dutcm"}


def lint_one(net: Path) -> list[str]:
    errs = []
    txt = net.read_text(errors="replace").splitlines()
    depth = 0
    for ln in txt:
        s = ln.split("*", 1)[0].strip()
        if not s:
            continue
        low = s.lower()
        if low.startswith(".include"):
            tgt = s.split(None, 1)[1].strip()
            if not Path(tgt).exists():
                errs.append(f"{net.name}: include target missing: {tgt}")
        elif low.startswith(".subckt"):
            depth += 1
        elif low.startswith(".ends"):
            depth = max(0, depth - 1)
        elif depth == 0:
            tok = s.split()[0]
            if tok.startswith("X"):
                if s.split()[-1].lower() not in LINT_SUBCKT:
                    errs.append(f"{net.name}: X subckt not registered: {s.split()[-1]}")
    body = "\n".join(txt)
    if ".ac dec" not in body:
        errs.append(f"{net.name}: no .ac directive")
    if ".end" not in body:
        errs.append(f"{net.name}: no .end")
    # 铁律断言：kelvin 舱网表恰 1 颗 OPA388（P 线）；整链网表恰 3 个 fsfo1/fsfo2
    # 跟随器实例（XfT/XfM/XfB，运放在其子电路内）——不得出现第四颗运放
    if "kelvin" in net.name:
        n_op = sum(1 for l in txt if l.strip().startswith("X")
                   and l.split()[-1] == "OPAx388")
        if n_op != 1:
            errs.append(f"{net.name}: OPAx388 count {n_op} != 1 (no 4th opamp rule)")
    if "cm_full" in net.name or "fcvs" in net.name:
        n_fo = sum(1 for l in txt if l.strip().startswith("X")
                   and l.split()[-1] in ("fsfo1", "fsfo2"))
        if n_fo != 3:
            errs.append(f"{net.name}: fsfo follower count {n_fo} != 3 (XfT/XfM/XfB)")
        n_op = sum(1 for l in txt if l.strip().startswith("X")
                   and l.split()[-1] == "OPAx388")
        if n_op != 0:
            errs.append(f"{net.name}: top-level OPAx388 {n_op} != 0 (opamps live in fsfo subs)")
    return errs


def cmd_lint() -> int:
    bad = 0
    n = 0
    for stem in job_list():                    # 只 lint 本族网表（目录与其他测试族共享）
        f = NET / f"{stem}.net"
        if not f.exists():
            print(f"[lint] {f.name}: MISSING")
            bad += 1
            continue
        n += 1
        errs = lint_one(f)
        if errs:
            print(f"[lint] {f.name}: {errs}")
            bad += len(errs)
    print(f"[lint] {n} own netlists, {bad} errors")
    return 1 if bad else 0


# ======================================================================
# 运行（run_all.run_net 台架：LTspice 产物为准；ltspice-sim 复数后处理崩溃记 note）
# ======================================================================
def job_list(probe: bool = False):
    jobs = []
    for sid in SCHEMES:
        for tid in GENS:
            jobs.append(f"{tid}_{STEM[sid]}")
        for rs in DUT_SWEEP:
            jobs.append(f"t03_rs{int(rs/1e3)}k_{STEM[sid]}")
        jobs.append(f"t03_fcvs_{STEM[sid]}")
    if probe:
        return ["t01_dm_ideal_s0", "t01_dm_opa388_s1", "t03_rs47k_t2", "t03_fcvs_t2",
                "t02_cm_full_t2"]
    return jobs


def run_one(stem: str, timeout: int):
    net = NET / f"{stem}.net"
    ok, out = run_all.run_net(net, timeout=timeout)
    if ok:
        shutil.copy2(net.with_suffix(".log"), LOGD / f"{stem}.log")
        shutil.copy2(net.with_suffix(".raw"), RAWD / f"{stem}.raw")
    return stem, ok, out


def run_all_nets(workers: int = 4, probe: bool = False) -> list[str]:
    LOGD.mkdir(exist_ok=True)
    RAWD.mkdir(exist_ok=True)
    jobs = job_list(probe)
    failures, notes = [], []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for stem, ok, out in ex.map(lambda j: run_one(j, 600), jobs):
            if not ok:
                failures.append(stem)
                print(f"[run] FAIL {stem}: {out[-400:]}")
            else:
                tag = out[:44] if out.startswith(("NOTE", "cached")) else "ok"
                print(f"[run] ok   {stem} ({tag})")
            if out.startswith("NOTE"):
                notes.append(f"{stem}: {out}")
    if notes:
        (LOGD / "run_notes.txt").write_text("\n".join(notes) + "\n")
    return failures


# ======================================================================
# 解析工具（fo1 ac_family 同法；本轮自含，不 import fo1 模块）
# ======================================================================
def load_H(rawpath: Path, pn: str, nn: str):
    r = parse_r5.Raw(str(rawpath))
    f = np.asarray(r.f, dtype=float)
    H = (np.asarray(r.col(f"V({pn})"), dtype=complex)
         - np.asarray(r.col(f"V({nn})"), dtype=complex))
    return f, H


def load_single(rawpath: Path, node: str):
    r = parse_r5.Raw(str(rawpath))
    return np.asarray(r.f, dtype=float), np.asarray(r.col(f"V({node})"), dtype=complex)


def db(x):
    a = np.abs(x)
    return 20 * np.log10(np.where(a > 0, a, 1e-320))


def H_at(f, H, ft):
    if ft <= f[0]:
        return H[0]
    if ft >= f[-1]:
        return H[-1]
    lx = np.log(f)
    j = int(np.searchsorted(lx, math.log(ft)))
    j = max(1, min(j, len(f) - 1))
    w = (math.log(ft) - lx[j - 1]) / (lx[j] - lx[j - 1])
    return H[j - 1] * (1 - w) + H[j] * w


def db_at(f, H, ft):
    v = abs(H_at(f, H, ft))
    return 20 * math.log10(v) if v > 0 else FLOOR_DB


def ph_at(f, H, ft):
    return math.degrees(np.angle(H_at(f, H, ft)))


def fc_from_H(f, H):
    g = db(H)
    target = g[0] - 3.0102999566398
    for i in range(1, len(f)):
        if g[i - 1] > target >= g[i]:
            lf = np.log10(f)
            w = (target - g[i - 1]) / (g[i] - g[i - 1])
            return float(10 ** (lf[i - 1] + w * (lf[i] - lf[i - 1])))
    return None


def group_delay(f, H, fmax=16e3):
    m = (f >= 0.1) & (f <= fmax)
    ff = f[m]
    ph = np.unwrap(np.angle(H[m]))
    return ff, -np.gradient(ph, 2 * math.pi * ff)


MEAS_RE = re.compile(
    r"^(\w+):\s+[^=]+?=\((-?[\d.eE+-]+)dB\s*,\s*([-+0-9.eE]+)", re.IGNORECASE)
MEAS_AT_RE = re.compile(r"^(\w+):\s+.*?=\S+\s+AT\s+([0-9.eE+-]+)", re.IGNORECASE)


def parse_meas(path: Path) -> tuple[dict, dict]:
    """→ ({name: dB}, {name: at_freq})；LTspice .meas AC mag()/ph() 输出 (dB,°) 元组。"""
    md, at = {}, {}
    if not path.exists():
        return md, at
    for line in path.read_text(errors="replace").splitlines():
        s = line.strip()
        m = MEAS_RE.match(s)
        if m:
            md[m.group(1)] = float(m.group(2))
            continue
        m = MEAS_AT_RE.match(s)
        if m:
            at[m.group(1)] = float(m.group(2))
    return md, at


def meas_deg(path: Path, name: str) -> float | None:
    """.meas AC ph() → (dB,°)：φ = ∓10^(dB/20)（fo1 冒烟验证同法）。"""
    if not path.exists():
        return None
    for line in path.read_text(errors="replace").splitlines():
        m = re.match(rf"^{name}:\s+[^=]+?=\(?(-?[\d.eE+-]+)dB\s*,\s*(180|0)°",
                     line.strip())
        if m:
            v = 10 ** (float(m.group(1)) / 20)
            return -v if m.group(2) == "180" else v
    return None


# ======================================================================
# 分析主流程
# ======================================================================
def analyze() -> list[str]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    CSVD.mkdir(exist_ok=True)
    PLOTD.mkdir(exist_ok=True)
    t01_rows, t02_rows, t02f_rows, t03_rows, t10_rows = [], [], [], [], []
    notver: list[str] = []
    max_xdiff = 0.0
    S3 = run_all.TASK_S3            # (d4_16k, d1_4M, cm_4M, d3_16M) 任务书 §3 理想表

    for sid, p in SCHEMES.items():
        cs = STEM[sid]
        rp = {tid: RAWD / f"{tid}_{cs}.raw" for tid in GENS}
        lg = {tid: LOGD / f"{tid}_{cs}.log" for tid in GENS}
        rp["fcvs"] = RAWD / f"t03_fcvs_{cs}.raw"

        # ---------- H 加载 ----------
        Hs: dict[str, tuple] = {}
        try:
            Hs["ideal"] = load_H(rp["t01_dm_ideal"], "pa1", "na1")
            Hs["opa388"] = load_H(rp["t01_dm_opa388"], "pa1", "na1")
            Hs["kelvin"] = load_H(rp["t01_dm_kelvin"], "a1p", "na1")
        except Exception as e:                                  # noqa: BLE001
            notver.append(f"{sid}: DM raw missing/parse fail: {e}")
            continue
        CMs: dict[str, tuple] = {}
        for port in ("ideal", "opa388", "kelvin"):
            pn = "a1p" if port == "kelvin" else "pa1"
            try:
                CMs[port] = load_H(rp[f"t02_cm_{port}"], pn, "na1")
            except Exception as e:                              # noqa: BLE001
                notver.append(f"{sid}: cm_{port} raw missing: {e}")
        try:
            CMF = load_H(rp["t02_cm_full"], "a0p", "a0n")
            _, Vt_f = load_single(rp["t02_cm_full"], "t")
            _, Va0p_f = load_single(rp["t02_cm_full"], "a0p")
            _, Va1p_f = load_single(rp["t02_cm_full"], "a1p")
        except Exception as e:                                  # noqa: BLE001
            CMF = None
            notver.append(f"{sid}: cm_full raw missing/parse fail: {e}")

        l1 = run_all.l1_metrics(p)          # L1 MNA 引擎（§3 表已对拍复现）
        s3 = S3[sid]

        # ================= T01 差模 AC（三口径） =================
        for port in ("ideal", "opa388", "kelvin"):
            f, H = Hs[port]
            g = db(H)
            fc = fc_from_H(f, H)
            # 一阶解析 fc；二阶由 L1 引擎数值求（同函数复用）
            if p["topo"] == 1:
                fc_th = 1 / (2 * math.pi * p["r1"] * (p["cg1"] + 2 * p["cd"])) / 1e3
            else:
                fh = np.array([_l1_h_f(p, ff) for ff in f])
                fc_th = (fc_from_H(f, fh) or float("nan")) / 1e3
            row = dict(
                scheme=sid, port=port,
                fc_kHz=round(fc / 1e3, 3) if fc else None,
                fc_theory_kHz=round(fc_th, 3),
                g_dc_dB=round(db_at(f, H, 0.1), 4),
                g_8k_dB=round(db_at(f, H, 8e3), 4),
                g_16k_dB=round(db_at(f, H, 16e3), 4),
                ph_8k_deg=round(ph_at(f, H, 8e3), 4),
                ph_16k_deg=round(ph_at(f, H, 16e3), 4),
                D1_atten_dB=round(db_at(f, H, 0.1) - db_at(f, H, FMOD), 3),
                D3_atten_dB=round(db_at(f, H, 0.1) - db_at(f, H, MCLK), 3),
                D4_16k_dB=round(db_at(f, H, 0.1) - db_at(f, H, 16e3), 4),
                peaking_dB=round(float(g.max() - g[0]), 4),
                pk_freq_Hz=round(float(f[int(np.argmax(g))]), 1),
                L1_d4=round(l1["d4"], 4), L1_d1=round(l1["d1"], 3), L1_d3=round(l1["d3"], 3),
                S3_d4=s3[0], S3_d1=s3[1], S3_d3=s3[3],
                norm="H=V(P)-V(N) per 1V DM @source")
            # 折叠点残留（4.096M±{1k,8k,16k}，raw 实测插值）
            for off in FOLD_OFFS:
                tag = f"{int(off/1e3)}k"
                row[f"resid_fmod_m{tag}_dB"] = round(db_at(f, H, FMOD - off), 2)
                row[f"resid_fmod_p{tag}_dB"] = round(db_at(f, H, FMOD + off), 2)
            # .meas 交叉校验（.meas dB = 20log10|V| 绝对值，与 raw db_at 同口径直接对减；
            # 衰减量口径另列 = −meas）
            tid = f"t01_dm_{port}"
            md, at = parse_meas(lg[tid])
            row["meas_dm_fmod_dB"] = round(-md["dm_fmod"], 3) if "dm_fmod" in md else None
            row["meas_dm_16k_dB"] = round(md["dm_16k"], 4) if "dm_16k" in md else None
            if "dm_fmod" in md and not math.isnan(md["dm_fmod"]):
                max_xdiff = max(max_xdiff, abs(md["dm_fmod"] - db_at(f, H, FMOD)))
                max_xdiff = max(max_xdiff, abs(md["dm_16k"] - db_at(f, H, 16e3)))
            ph_m16 = meas_deg(lg[tid], "ph_16k")
            row["meas_ph_16k_deg"] = round(ph_m16, 4) if ph_m16 is not None else None
            foll_pk = md.get("foll_pk")
            foll_dc = md.get("foll_dc")
            if foll_pk is not None and foll_dc is not None \
                    and not (math.isnan(foll_pk) or math.isnan(foll_dc)):
                row["foll_peaking_dB"] = round(foll_pk - foll_dc, 4)
                row["foll_pk_freq_Hz"] = at.get("foll_pk_f")
            else:
                row["foll_peaking_dB"] = None
                row["foll_pk_freq_Hz"] = None
            t01_rows.append(row)

        # ================= T02 共模 AC（舱口径：RC 自身 vs Kelvin） =================
        for port in ("ideal", "opa388", "kelvin"):
            if port not in CMs:
                continue
            f, HC = CMs[port]               # HC = V(P)-V(N) under CM 0.5V → CM→DM
            pn = "a1p" if port == "kelvin" else "pa1"
            _, Vcm = load_single(rp[f"t02_cm_{port}"], pn)
            cmdm = db(HC)
            row = dict(
                scheme=sid, port=port,
                cm_dc_resid_dB=round(db_at(f, Vcm, 0.1), 4),
                cm_16k_resid_dB=round(db_at(f, Vcm, 16e3), 4),
                D2_resid_05V_dB=round(db_at(f, Vcm, FMOD), 3),
                D2_atten_dB=round(db_at(f, Vcm, 0.1) - db_at(f, Vcm, FMOD), 3),
                D2_resid_1V_dB=round(db_at(f, Vcm, FMOD) - 6.0206, 3),
                cmdm_dc_dB=round(db_at(f, HC, 0.1), 2),
                cmdm_1k_dB=round(db_at(f, HC, 1e3), 2),
                cmdm_8k_dB=round(db_at(f, HC, 8e3), 2),
                cmdm_16k_dB=round(db_at(f, HC, 16e3), 2),
                cmdm_fmod_dB=round(db_at(f, HC, FMOD), 2),
                norm="CM excitation 0.5V (t00 caliber); H_CM=V(P) single-end; H_CM-to-DM=V(P)-V(N)")
            # CMRR『RC 自身』口径：对称网表（ideal/opa388）DM 增益 − CM→DM
            if port in Hs:
                fdm, Hdm = Hs[port]
                band = (f >= 10) & (f <= 16e3)
                cmrr = db(Hdm[band]) - cmdm[band]
                k = int(np.argmin(cmrr))
                row["CMRR_RC_worst_dB"] = round(float(cmrr[k]), 2)
                row["CMRR_RC_worst_f_Hz"] = round(float(f[band][k]), 1)
                row["CMRR_RC_1k_dB"] = round(db_at(f, Hdm, 1e3) - db_at(f, HC, 1e3), 2)
                row["CMRR_RC_16k_dB"] = round(db_at(f, Hdm, 16e3) - db_at(f, HC, 16e3), 2)
                row["caliber_note"] = ("RC-self caliber: symmetric bench netlist;"
                                       " cmdm=solver numerical floor (devices exactly paired),"
                                       " real unmatched CMRR needs tolerance MC (fo1 T06 scope, not this round)"
                                       if port != "kelvin" else
                                       "Kelvin structural caliber: P line via opamp / N line passive RC —"
                                       " real mismatch, not solver floor")
            md, _ = parse_meas(lg[f"t02_cm_{port}"])
            if "cm_fmod" in md and not math.isnan(md["cm_fmod"]):
                row["meas_cm_fmod_dB"] = round(md["cm_fmod"], 3)
                max_xdiff = max(max_xdiff, abs(md["cm_fmod"] - db_at(f, Vcm, FMOD)))
            # 折叠点（opa388 网表测了 fold 点）
            if port == "opa388":
                for off in FOLD_OFFS:
                    tag = f"{int(off/1e3)}k"
                    row[f"cmres_fmod_m{tag}_dB"] = round(db_at(f, Vcm, FMOD - off), 2)
                    row[f"cmres_fmod_p{tag}_dB"] = round(db_at(f, Vcm, FMOD + off), 2)
            t02_rows.append(row)

        # ================= T02 整链 Kelvin 共模口径 =================
        if CMF is not None:
            f, Hcmdm0 = CMF                      # V(a0p)-V(a0n) per 1V vint（CM→DM 转换）
            _, Va0p = load_single(rp["t02_cm_full"], "a0p")
            _, Va1p = load_single(rp["t02_cm_full"], "a1p")
            _, Vt = load_single(rp["t02_cm_full"], "t")
            row = dict(
                scheme=sid, caliber="fullchain_kelvin",
                inj="Vint 1V AC via dut parasitics (Ct/Cs 200p to vint, Cts 30p)",
                vcm_cable_dc_dB=round(db_at(f, Vt, 0.1), 2),
                vcm_cable_16k_dB=round(db_at(f, Vt, 16e3), 2),
                vcm_cable_fmod_dB=round(db_at(f, Vt, FMOD), 2),
                ch0_cmout_1k_dB=round(db_at(f, Va0p, 1e3), 2),
                ch0_cmout_16k_dB=round(db_at(f, Va0p, 16e3), 2),
                ch0_cmout_fmod_dB=round(db_at(f, Va0p, FMOD), 2),
                ch0_cmdm_1k_dB=round(db_at(f, Hcmdm0, 1e3), 2),
                ch0_cmdm_8k_dB=round(db_at(f, Hcmdm0, 8e3), 2),
                ch0_cmdm_16k_dB=round(db_at(f, Hcmdm0, 16e3), 2),
                ch0_cmdm_fmod_dB=round(db_at(f, Hcmdm0, FMOD), 2),
                ch1_cmout_fmod_dB=round(db_at(f, Va1p, FMOD), 2),
                norm="per 1V Vint injected into cable parasitic; RSAMP=47k")
            # CMRR『整链 Kelvin』口径：G_dm（DUT 支路 1V 串模，t03_fcvs）vs G_cmdm（线缆 1V 共模）
            try:
                fF, H0F = load_H(rp["fcvs"], "a0p", "a0n")
                G_dm = H0F                     # per 1V Vex (series-mode at DUT)
                G_cmdm = Hcmdm0                # per 1V vint (cable CM)
                cmrr_f = db(G_dm) - db(G_cmdm)
                band = (f >= 10) & (f <= 16e3)
                k = int(np.argmin(cmrr_f[band]))
                row["CMRR_full_worst_dB"] = round(float(cmrr_f[band][k]), 2)
                row["CMRR_full_worst_f_Hz"] = round(float(f[band][k]), 1)
                row["CMRR_full_1k_dB"] = round(float(db_at(f, G_dm, 1e3) - db_at(f, G_cmdm, 1e3)), 2)
                row["CMRR_full_16k_dB"] = round(float(db_at(f, G_dm, 16e3) - db_at(f, G_cmdm, 16e3)), 2)
                row["CMRR_def"] = ("G_dm=(a0p-a0n) per 1V Vex series-mode at DUT vs "
                                   "G_cmdm=(a0p-a0n) per 1V vint cable CM; different injection"
                                   " points by physics (declared), same-output dB subtraction")
            except Exception as e:                                  # noqa: BLE001
                row["CMRR_full_worst_dB"] = None
                row["CMRR_def"] = f"t03_fcvs raw unavailable: {e}"
            md, _ = parse_meas(lg["t02_cm_full"])
            if "cmdm0_16k" in md and not math.isnan(md["cmdm0_16k"]):
                row["meas_cmdm0_16k_dB"] = round(md["cmdm0_16k"], 2)
            t02f_rows.append(row)

        # ================= T03 通道匹配 + DUT 工作量程扫 =================
        # 主口径 = 舱级 real-src：CH0 源阻抗 = DUT 阻值（差分源每侧 rs/2），CH1 = 0Ω Kelvin
        # （CH1 源阻抗 ≈0：B 点恒流环低阻驱动、E=地；fo1 同款声明近似）
        for rs in DUT_SWEEP:
            stem = f"t03_rs{int(rs/1e3)}k_{cs}"
            try:
                fR, H0r = load_H(RAWD / f"{stem}.raw", "pa1", "na1")
            except Exception as e:                                  # noqa: BLE001
                notver.append(f"{sid} rs={rs}: bench raw missing: {e}")
                continue
            fK, H1k = Hs["kelvin"]                # 0Ω 源 CH1（与 t01_dm_kelvin 同 raw）
            Hratio = H0r / H1k
            gr = db(Hratio)
            ph0 = np.unwrap(np.angle(H0r))
            ph1 = np.unwrap(np.angle(H1k))
            dphi = np.degrees(ph0 - ph1)
            gdc = db_at(fR, Hratio, 0.1)
            band = (fR >= 1e3) & (fR <= 16e3)
            for flab, ft in (("DC", 0.1), ("1k", 1e3), ("8k", 8e3), ("16k", 16e3)):
                i = int(np.argmin(np.abs(fR - ft)))
                t03_rows.append(dict(
                    scheme=sid, caliber="bench_realsrc", rs_ohm=int(rs), f=flab,
                    H0_mag_dB=round(db_at(fR, H0r, ft), 4),
                    H1_mag_dB=round(db_at(fK, H1k, ft), 4),
                    Hratio_mag_dB=round(float(gr[i]), 4),
                    Hratio_vs_DC_dB=round(float(gr[i] - gdc), 5),
                    R_err_vs_DC_ppm=round(float((10 ** ((gr[i] - gdc) / 20) - 1) * 1e6), 1),
                    dphi_deg=round(float(dphi[i]), 4),
                    norm="H0=CH0 DM 1V via rs/2 per side; H1=CH1 Kelvin 0ohm (t01_dm_kelvin);"
                         " R_err normalized to DC (k-caliber removes DC gain); 1V DM normalization"))
            t03_rows.append(dict(
                scheme=sid, caliber="bench_realsrc", rs_ohm=int(rs), f="worst(1k-16k)",
                H0_mag_dB=None, H1_mag_dB=None,
                Hratio_mag_dB=None,
                Hratio_vs_DC_dB=round(float((gr[band] - gdc).max() - (gr[band] - gdc).min()), 5),
                R_err_vs_DC_ppm=round(float(max(abs(10 ** ((gr[band] - gdc) / 20) - 1)) * 1e6), 1),
                dphi_deg=round(float(np.abs(dphi[band]).max()), 4),
                norm="|Hratio/DC| p-p(dB) / max|R_err|(ppm) / max|dphi|(deg) over 1k-16k;"
                     " 600k NOT run: 8uA*600k=4.8V exceeds 3.3V compliance (fo1 A7)"))
        # 附加口径 = 整链串模（真实接线：fsrc+3×OPA388+Kelvin RC+fsadc，Vex 1V 串在 s→K1）
        try:
            fV, H0v = load_H(rp["fcvs"], "a0p", "a0n")
            _, H1v = load_H(rp["fcvs"], "a1p", "na1")
            ph0 = np.unwrap(np.angle(H0v))
            ph1 = np.unwrap(np.angle(H1v))
            dphi = np.degrees(ph0 - ph1)
            for flab, ft in (("DC", 0.1), ("1k", 1e3), ("8k", 8e3), ("16k", 16e3)):
                i = int(np.argmin(np.abs(fV - ft)))
                t03_rows.append(dict(
                    scheme=sid, caliber="fullchain_seriesmode", rs_ohm=47000, f=flab,
                    H0_mag_dB=round(db_at(fV, H0v, ft), 4),
                    H1_mag_dB=round(db_at(fV, H1v, ft), 4),
                    Hratio_mag_dB=round(float(db(H0v / H1v)[i]), 4),
                    Hratio_vs_DC_dB=None,
                    R_err_vs_DC_ppm=None,
                    dphi_deg=round(float(dphi[i]), 4),
                    norm="per 1V Vex series-mode injected at s->K1; H1 = loop-coupled response"
                         " (physically small: CC loop rejects current-mode AC); RSAMP=47k;"
                         " not an R-ratio caliber - documents real-wiring series-mode split"))
        except Exception as e:                                      # noqa: BLE001
            notver.append(f"{sid}: fcvs raw missing: {e}")

        # ================= T10 群延迟 + CH0/CH1 相位失配 =================
        for port, lab in (("ideal", "L1_ideal"), ("opa388", "CH0_opa388_bench"),
                          ("kelvin", "CH1_kelvin_bench")):
            f, H = Hs[port]
            ff, tau = group_delay(f, H)
            t10_rows.append(dict(
                scheme=sid, channel=lab, caliber="bench",
                tau_1k_us=round(float(np.interp(1e3, ff, tau)) * 1e6, 4),
                tau_8k_us=round(float(np.interp(8e3, ff, tau)) * 1e6, 4),
                tau_16k_us=round(float(np.interp(16e3, ff, tau)) * 1e6, 4),
                dtau_0p1_16k_us=round(float(tau.max() - tau.min()) * 1e6, 4)))
        try:
            fF, H0 = load_H(rp["fcvs"], "a0p", "a0n")
            _, H1 = load_H(rp["fcvs"], "a1p", "na1")
            ff0, tau0 = group_delay(fF, H0)
            ff1, tau1 = group_delay(fF, H1)
            ph0 = np.unwrap(np.angle(H0))
            ph1 = np.unwrap(np.angle(H1))
            dphi = np.degrees(ph0 - ph1)
            t10_rows.append(dict(
                scheme=sid, channel="CH0_fullchain_rs47k", caliber="fullchain",
                tau_1k_us=round(float(np.interp(1e3, ff0, tau0)) * 1e6, 4),
                tau_8k_us=round(float(np.interp(8e3, ff0, tau0)) * 1e6, 4),
                tau_16k_us=round(float(np.interp(16e3, ff0, tau0)) * 1e6, 4),
                dtau_0p1_16k_us=round(float(tau0.max() - tau0.min()) * 1e6, 4)))
            t10_rows.append(dict(
                scheme=sid, channel="CH1_fullchain_rs47k", caliber="fullchain",
                tau_1k_us=round(float(np.interp(1e3, ff1, tau1)) * 1e6, 4),
                tau_8k_us=round(float(np.interp(8e3, ff1, tau1)) * 1e6, 4),
                tau_16k_us=round(float(np.interp(16e3, ff1, tau1)) * 1e6, 4),
                dtau_0p1_16k_us=round(float(tau1.max() - tau1.min()) * 1e6, 4)))
            t10_rows.append(dict(
                scheme=sid, channel="CH0_minus_CH1_mismatch", caliber="fullchain",
                tau_1k_us=round(float((np.interp(1e3, ff0, tau0) - np.interp(1e3, ff1, tau1))) * 1e6, 4),
                tau_8k_us=round(float((np.interp(8e3, ff0, tau0) - np.interp(8e3, ff1, tau1))) * 1e6, 4),
                tau_16k_us=round(float((np.interp(16e3, ff0, tau0) - np.interp(16e3, ff1, tau1))) * 1e6, 4),
                dtau_0p1_16k_us=None,
                dphi_1k_deg=round(float(dphi[np.argmin(np.abs(fF - 1e3))]), 4),
                dphi_8k_deg=round(float(dphi[np.argmin(np.abs(fF - 8e3))]), 4),
                dphi_16k_deg=round(float(dphi[np.argmin(np.abs(fF - 16e3))]), 4)))
        except Exception as e:                                      # noqa: BLE001
            notver.append(f"{sid}: fullchain tau mismatch calc fail: {e}")
        # 台架口径失配（opa388 vs kelvin 网表对，上一轮同款对照）
        f0, H0b = Hs["opa388"]
        _, H1b = Hs["kelvin"]
        dphib = np.degrees(np.unwrap(np.angle(H0b)) - np.unwrap(np.angle(H1b)))
        ff0b, tau0b = group_delay(f0, H0b)
        ff1b, tau1b = group_delay(f0, H1b)
        t10_rows.append(dict(
            scheme=sid, channel="CH0_minus_CH1_bench", caliber="bench-pair",
            tau_1k_us=round(float((np.interp(1e3, ff0b, tau0b) - np.interp(1e3, ff1b, tau1b))) * 1e6, 4),
            tau_8k_us=round(float((np.interp(8e3, ff0b, tau0b) - np.interp(8e3, ff1b, tau1b))) * 1e6, 4),
            tau_16k_us=round(float((np.interp(16e3, ff0b, tau0b) - np.interp(16e3, ff1b, tau1b))) * 1e6, 4),
            dtau_0p1_16k_us=None,
            dphi_1k_deg=round(float(dphib[np.argmin(np.abs(f0 - 1e3))]), 4),
            dphi_8k_deg=round(float(dphib[np.argmin(np.abs(f0 - 8e3))]), 4),
            dphi_16k_deg=round(float(dphib[np.argmin(np.abs(f0 - 16e3))]), 4)))

        # ---------- 图（每方案一张 T01 bode；总览图最后统一画） ----------
        _plot_t01_scheme(plt, sid, Hs, PLOTD)

    # ================= 总览图 =================
    _plot_overview(plt, t01_rows, PLOTD)

    # ---------- CSV 落盘 ----------
    def wcsv(path, rows):
        keys: list[str] = []
        for r in rows:
            for k in r:
                if k not in keys:
                    keys.append(k)
        with open(path, "w", newline="\n", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=keys)
            w.writeheader()
            for r in rows:
                w.writerow(r)
        print(f"[csv] {path} rows={len(rows)}")

    wcsv(CSVD / "t01_dm_ac.csv", t01_rows)
    wcsv(CSVD / "t02_cm_ac.csv", t02_rows)
    wcsv(CSVD / "t02_cm_full.csv", t02f_rows)
    wcsv(CSVD / "t03_channel_match.csv", t03_rows)
    wcsv(CSVD / "t10_group_delay.csv", t10_rows)
    print(f"[xcheck] .meas vs raw max |diff| = {max_xdiff:.4f} dB")
    return notver


def _l1_h_f(p: dict, f: float) -> complex:
    """L1 MNA 半电路复传函（run_all._l1_h 同式，独立入口便于二阶 fc 数值求取）。"""
    return run_all._l1_h(p, f)


# ======================================================================
# 图
# ======================================================================
def _plot_t01_scheme(plt, sid, Hs, PLOTD):
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
    for port, lab in (("ideal", "L1 ideal src"), ("opa388", "CH0 dual OPA388"),
                      ("kelvin", "CH1 Kelvin")):
        f, H = Hs[port]
        a1.semilogx(f, db(H), label=lab)
        a2.semilogx(f, np.degrees(np.angle(H)), label=lab)
    a1.set_ylabel("|H_DM| dB")
    a1.grid(True, which="both", alpha=0.3)
    a1.legend(fontsize=8)
    a1.set_title(f"T01 DM AC 3-caliber - {sid} "
                 f"({'1st-order' if SCHEMES[sid]['topo']==1 else '2nd-order'})")
    a2.set_ylabel("phase deg")
    a2.set_xlabel("Hz")
    a2.grid(True, which="both", alpha=0.3)
    for ax in (a1, a2):
        for fx in (16e3, FMOD, MCLK):
            ax.axvline(fx, color="r", ls=":", lw=0.7)
    fig.tight_layout()
    fig.savefig(PLOTD / f"t01_{STEM[sid]}_dm_bode.png", dpi=140)
    plt.close(fig)


def _plot_overview(plt, t01_rows, PLOTD):
    # DM @opa388 口径六方案对比（关键曲线）
    fig, a1 = plt.subplots(figsize=(9.5, 6))
    for sid in SCHEMES:
        rp = RAWD / f"t01_dm_opa388_{STEM[sid]}.raw"
        if not rp.exists():
            continue
        f, H = load_H(rp, "pa1", "na1")
        a1.semilogx(f, db(H), label=f"{sid}")
    for fx, lab in ((16e3, "16k"), (FMOD, "4.096M"), (MCLK, "16.384M")):
        a1.axvline(fx, color="gray", ls=":", lw=0.8)
        a1.text(fx, 0, f" {lab}", fontsize=8, color="gray", rotation=90, va="bottom")
    a1.set_xlabel("Hz")
    a1.set_ylabel("20log10|V(pa1)-V(na1)| per 1V DM (dB)")
    a1.set_title("T01 DM AC all schemes - CH0 dual OPA388 caliber (LTspice, TI OPAx388 macro)")
    a1.grid(True, which="both", alpha=0.3)
    a1.legend(loc="lower left", fontsize=9)
    fig.tight_layout()
    fig.savefig(PLOTD / "t01_all_schemes_dm_opa388.png", dpi=140)
    plt.close(fig)

    # T02 CM→DM（kelvin 结构性）+ 整链
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(9.5, 8), sharex=True)
    for sid in SCHEMES:
        rp = RAWD / f"t02_cm_kelvin_{STEM[sid]}.raw"
        if rp.exists():
            f, HC = load_H(rp, "a1p", "na1")
            a1.semilogx(f, db(HC), label=f"{sid}")
        rp = RAWD / f"t02_cm_full_{STEM[sid]}.raw"
        if rp.exists():
            f, HC = load_H(rp, "a0p", "a0n")
            a2.semilogx(f, db(HC), label=f"{sid}")
    for ax, ttl in ((a1, "T02 CM-to-DM leakage - Kelvin bench caliber (per 1V CM 0.5V excitation)"),
                    (a2, "T02 CM-to-DM - fullchain Kelvin caliber (per 1V Vint into cable parasitics)")):
        ax.set_ylabel("dB")
        ax.grid(True, which="both", alpha=0.3)
        ax.legend(fontsize=8)
        ax.set_title(ttl)
        ax.axvline(FMOD, color="r", ls=":", lw=0.7)
        ax.axvline(16e3, color="gray", ls=":", lw=0.7)
    a2.set_xlabel("Hz")
    fig.tight_layout()
    fig.savefig(PLOTD / "t02_cmdm_all_schemes.png", dpi=140)
    plt.close(fig)

    # T03 Hratio 幅相（舱级 rs=47k 全方案 + T2 全 rs 扫）
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(9.5, 8), sharex=True)
    for sid in SCHEMES:
        rp = RAWD / f"t03_rs47k_{STEM[sid]}.raw"
        if not rp.exists():
            continue
        f, H0r = load_H(rp, "pa1", "na1")
        rk = RAWD / f"t01_dm_kelvin_{STEM[sid]}.raw"
        _, H1k = load_H(rk, "a1p", "na1")
        Hratio = H0r / H1k
        gdc = db_at(f, Hratio, 0.1)
        dphi = np.degrees(np.unwrap(np.angle(H0r)) - np.unwrap(np.angle(H1k)))
        a1.semilogx(f, db(Hratio) - gdc, label=f"{sid} rs47k")
        a2.semilogx(f, dphi, label=f"{sid}")
    for rs in DUT_SWEEP:
        rp = RAWD / f"t03_rs{int(rs/1e3)}k_t2.raw"
        if rp.exists():
            f, H0r = load_H(rp, "pa1", "na1")
            rk = RAWD / "t01_dm_kelvin_t2.raw"
            _, H1k = load_H(rk, "a1p", "na1")
            Hratio = H0r / H1k
            gdc = db_at(f, Hratio, 0.1)
            a1.semilogx(f, db(Hratio) - gdc, ls="--", lw=1, label=f"T2 rs={int(rs/1e3)}k")
    a1.set_ylabel("H0/H1 rel DC (dB)")
    a1.grid(True, which="both", alpha=0.3)
    a1.legend(fontsize=8)
    a1.set_title("T03 bench real-src ratio deviation H0(CH0,src=rs)/H1(CH1 Kelvin,0ohm) rel DC")
    a1.set_xlim(1e2, 1e6)
    a2.set_ylabel("phase(H0/H1) deg")
    a2.set_xlabel("Hz")
    a2.grid(True, which="both", alpha=0.3)
    a2.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(PLOTD / "t03_hratio_all.png", dpi=140)
    plt.close(fig)

    # T10 群延迟（六方案 CH0/CH1 整链串模口径）
    fig, a1 = plt.subplots(figsize=(9.5, 5.5))
    for sid in SCHEMES:
        rp = RAWD / f"t03_fcvs_{STEM[sid]}.raw"
        if not rp.exists():
            continue
        for pn, nn, lab in (("a0p", "a0n", "CH0"), ("a1p", "na1", "CH1")):
            f, H = load_H(rp, pn, nn)
            ff, tau = group_delay(f, H)
            a1.semilogx(ff, tau * 1e6, label=f"{sid} {lab}")
    a1.set_xlabel("Hz")
    a1.set_ylabel("group delay (us)")
    a1.set_title("T10 fullchain series-mode group delay 0.1Hz-16kHz (RSAMP=47k)")
    a1.grid(True, which="both", alpha=0.3)
    a1.legend(fontsize=7, ncol=3)
    fig.tight_layout()
    fig.savefig(PLOTD / "t10_groupdelay_all.png", dpi=140)
    plt.close(fig)


# ======================================================================
# L3 离线：sinc³ 比值 + 折叠（非 LTspice 数字内核仿真，A11/A12 口径）
# ======================================================================
def sinc3(f: float) -> complex:
    if f == 0.0:
        return complex(1.0, 0.0)
    w = 2.0 * math.pi * f / FMOD
    num = 1j * 2.0 * math.sin(w * 32 / 2.0) * np.exp(-1j * w * 32 / 2.0)
    den = 32 * 1j * 2.0 * math.sin(w / 2.0) * np.exp(-1j * w / 2.0)
    if abs(den) < 1e-300:
        w2 = w + 1e-9
        den = 32 * 1j * 2.0 * math.sin(w2 / 2.0) * np.exp(-1j * w2 / 2.0)
    return (num / den) ** 3


def sinc3_db(f: float) -> float:
    return 20.0 * math.log10(abs(sinc3(f)) + 1e-300)


def sinc3_gd_us(f: float, df: float = 1.0) -> float:
    if f <= df:
        f = df
    a, b = sinc3(f - df), sinc3(f + df)
    dp = math.atan2(b.imag, b.real) - math.atan2(a.imag, a.real)
    while dp > math.pi:
        dp -= 2 * math.pi
    while dp < -math.pi:
        dp += 2 * math.pi
    return -dp / (2 * math.pi) / (2 * df) * 1e6


def validate_sinc3() -> float:
    errs = []
    target = 10 ** (-3.0 / 20.0)
    lo, hi = 1.0, 128e3 * 0.45
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if abs(sinc3(mid)) > target:
            lo = mid
        else:
            hi = mid
    f3db = 0.5 * (lo + hi)
    if abs(f3db - 33488.0) / 33488.0 > 0.01:
        errs.append(f"f3dB {f3db:.1f}")
    for f, ref in ((8e3, -0.17), (16e3, -0.67)):
        if abs(sinc3_db(f) - ref) > 0.01:
            errs.append(f"@{f}")
    gd0 = sinc3_gd_us(100.0)
    if abs(gd0 - 11.3525) > 0.02:
        errs.append(f"gd0 {gd0:.4f}")
    if errs:
        raise AssertionError("sinc3 self-check failed: " + ";".join(errs))
    return f3db


def cmd_l3() -> list[str]:
    rows = []
    notver = []
    f3db = validate_sinc3()
    print(f"[l3-validate] sinc3 f3dB={f3db:.1f}Hz (anchor 33488), 8k={sinc3_db(8e3):+.4f}dB, "
          f"16k={sinc3_db(16e3):+.4f}dB, DC-gd={sinc3_gd_us(100):.4f}us (anchor 11.3525)")

    for sid in SCHEMES:
        cs = STEM[sid]
        # ---- Block A: Hratio × sinc³（两通道同设 OSR=32 全局 → 比值中消去，数值演示） ----
        # 口径 = 舱级 real-src rs=47k（CH0 源阻抗 = 样品 47k）对 CH1 Kelvin 0Ω
        try:
            rR, H0r = load_H(RAWD / f"t03_rs47k_{cs}.raw", "pa1", "na1")
            rK, H1k = load_H(RAWD / f"t01_dm_kelvin_{cs}.raw", "a1p", "na1")
            rF, H0, H1 = rR, H0r, H1k
        except Exception as e:                                      # noqa: BLE001
            notver.append(f"{sid}: l3 blockA raw missing: {e}")
            H0 = H1 = None
        if H0 is not None:
            Hratio = H0 / H1
            gdc = db_at(rF, Hratio, 0.1)
            for flab, ft in (("1k", 1e3), ("8k", 8e3), ("16k", 16e3)):
                i = int(np.argmin(np.abs(rF - ft)))
                c0, c1 = H0[i], H1[i]
                S = sinc3(ft)
                rat_ana = c0 / c1
                rat_dig = (c0 * S) / (c1 * S)
                canc = abs(20 * math.log10(abs(rat_dig) / abs(rat_ana)))
                ang = lambda c: math.degrees(math.atan2(c.imag, c.real))
                dph = (ang(rat_dig) - ang(rat_ana) + 180) % 360 - 180
                rows.append(dict(
                    block="A_hratio_sinc3", scheme=sid, src="bench_realsrc_rs47k", f=flab,
                    sinc3_dB=f"{sinc3_db(ft):+.4f}",
                    Hratio_vs_DC_dB=f"{db(Hratio)[i]-gdc:+.5f}",
                    R_err_vs_DC_ppm=f"{(10 ** ((db(Hratio)[i]-gdc) / 20) - 1) * 1e6:+.1f}",
                    dphi_deg=f"{ang(rat_ana):+.4f}",
                    sinc_cancel_mag_dB=f"{canc:.2e}",
                    sinc_cancel_ph_deg=f"{abs(dph):.2e}",
                    note="OSR=32 global same-setting both channels -> sinc3 cancels in ratio; "
                         "cancel residuals are pure numerical floor; R_err normalized to DC"))
        # ---- Block B: 4.096M±{1k,8k,16k} 折叠（AAF 残留 = t01 raw 实测插值，非斜率修正） ----
        for port, pn, nn, exe in (("dm_opa388", "pa1", "na1", "1V DM @source"),
                                  ("dm_kelvin", "a1p", "na1", "1V DM @Rsense")):
            try:
                f, H = load_H(RAWD / f"t01_{port}_{cs}.raw", pn, nn)
            except Exception as e:                                  # noqa: BLE001
                notver.append(f"{sid}: l3 blockB {port} raw missing: {e}")
                continue
            for off in (0.0,) + FOLD_OFFS:
                for sgn in ("+", "-") if off else ("+",):
                    finj = FMOD + (off if sgn == "+" else -off)
                    folded = abs(finj - round(finj / FMOD) * FMOD)
                    aaf = db_at(f, H, finj)
                    s_fold = sinc3_db(folded) if folded > 0 else 0.0
                    total = aaf + s_fold
                    uv100 = 0.1 * 10 ** (total / 20) * 1e6
                    rows.append(dict(
                        block="B_alias", scheme=sid, src=port,
                        f=f"{finj/1e6:.6f}M",
                        sinc3_dB=f"{s_fold:+.4f}",
                        aaf_resid_dB=f"{aaf:+.3f}",
                        total_fold_dB=f"{total:+.3f}",
                        uv_per_100mV=f"{uv100:.2f}",
                        ppm_ch1_per100mV=f"{uv100/1.2*1e6/1e6:.1f}",
                        ppm_ch0_47k_per100mV=f"{uv100/0.376*1e6/1e6:.1f}",
                        note=f"folds to {folded/1e3:.3f}kHz; AAF resid = t01 raw measured interp "
                             f"(not slope-corrected); excitation {exe}; alias gain 0dB worst-case (A12); "
                             f"per 100mV injected at AAF input; CH1 sig=1.2V, CH0 sig@47k=0.376V"))
        # ---- Block B2: 整链线缆共模路径折回（t02_cm_full raw） ----
        try:
            f, HC = load_H(RAWD / f"t02_cm_full_{cs}.raw", "a0p", "a0n")
        except Exception as e:                                      # noqa: BLE001
            notver.append(f"{sid}: l3 blockB2 raw missing: {e}")
            HC = None
        if HC is not None:
            for off in (0.0,) + FOLD_OFFS:
                finj = FMOD + off
                folded = abs(finj - round(finj / FMOD) * FMOD)
                aaf = db_at(f, HC, finj)
                s_fold = sinc3_db(folded) if folded > 0 else 0.0
                rows.append(dict(
                    block="B2_alias_fullchain_cm", scheme=sid, src="cm_full_vint",
                    f=f"{finj/1e6:.6f}M",
                    sinc3_dB=f"{s_fold:+.4f}",
                    aaf_resid_dB=f"{aaf:+.3f}",
                    total_fold_dB=f"{aaf+s_fold:+.3f}",
                    uv_per_100mV=f"{0.1*10**((aaf+s_fold)/20)*1e6:.3f}",
                    ppm_ch1_per100mV=f"{0.1*10**((aaf+s_fold)/20)/1.2*1e6:.2f}",
                    ppm_ch0_47k_per100mV=f"{0.1*10**((aaf+s_fold)/20)/0.376*1e6:.2f}",
                    note="fullchain caliber: 100mV CM interference coupled via cable parasitics"))
        # ---- Block D: 群延迟复合（模拟 + sinc³，µs）—— 整链串模口径 ----
        try:
            rT, H0 = load_H(RAWD / f"t03_fcvs_{cs}.raw", "a0p", "a0n")
            _, H1 = load_H(RAWD / f"t03_fcvs_{cs}.raw", "a1p", "na1")
            for ch, Hx in (("CH0", H0), ("CH1", H1)):
                ff, tau = group_delay(rT, Hx)
                for flab, ft in (("1k", 1e3), ("8k", 8e3), ("16k", 16e3)):
                    ta = float(np.interp(ft, ff, tau)) * 1e6
                    ts = sinc3_gd_us(ft)
                    rows.append(dict(
                        block="D_group_delay", scheme=sid, src=ch, f=flab,
                        tau_ana_us=f"{ta:.4f}", tau_sinc3_us=f"{ts:.4f}",
                        tau_total_us=f"{ta+ts:.4f}",
                        note="analog(fullchain series-mode rs47k) + sinc3(numeric diff, "
                             "3*31/2/fMOD=11.3525us at DC); sinc3 identical both channels "
                             "-> mismatch stays analog-only"))
        except Exception as e:                                      # noqa: BLE001
            notver.append(f"{sid}: l3 blockD fail: {e}")

    # 声明行
    rows.insert(0, dict(
        block="STATEMENT", scheme="", src="",
        note="L3 = offline Python post-processing (analog AC raw x sinc3 transfer function); "
             "NOT an LTspice digital-kernel simulation. sinc3 H(z)=[(1-z^-32)/(32(1-z^-1))]^3, "
             "fMOD=4.096MHz, OSR=32 global (A11); alias gain 0dB worst-case, aperture not modeled (A12)."))

    out = CSVD / "l3_sinc3_alias.csv"
    keys: list[str] = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with open(out, "w", newline="\n", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"[csv] {out} rows={len(rows)}")

    # 折叠柱状图（B 块 CH0 口径 total）
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(10, 5))
    labels, vals = [], []
    for r in rows:
        if r.get("block") == "B_alias" and r.get("src") == "dm_opa388":
            labels.append(f"{r['scheme']}\n{r['f']}")
            vals.append(float(r["total_fold_dB"]))
    ax.bar(range(len(vals)), vals, color="#2563eb", alpha=0.8)
    ax.set_xticks(range(len(vals)))
    ax.set_xticklabels(labels, fontsize=6.5, rotation=90)
    ax.set_ylabel("total fold-back suppression (dB)")
    ax.set_title("L3 fold-back @4.096MHz±{0,1k,8k,16k}: AAF measured + sinc3 (CH0 dm_opa388 caliber, per 1V)")
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(PLOTD / "l3_fold_back_bar.png", dpi=140)
    plt.close(fig)
    return notver


# ======================================================================
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("cmd", nargs="?", default="all",
                    choices=["gen", "lint", "probe", "run", "analyze", "l3", "all"])
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    if args.cmd in ("gen", "all", "probe", "run", "lint"):
        n = len(gen_all())
        print(f"[gen] {n} netlists -> {NET}")
    if args.cmd == "lint":
        return cmd_lint()
    if args.cmd in ("probe", "run", "all"):
        fails = run_all_nets(args.workers, probe=(args.cmd == "probe"))
        if fails:
            print(f"[run] FAILED ({len(fails)}): {fails}")
    if args.cmd in ("all", "analyze"):
        nv = analyze()
        if nv:
            print("[not-verified]", *nv, sep="\n  ")
    if args.cmd in ("all", "l3"):
        nv = cmd_l3()
        if nv:
            print("[l3-not-verified]", *nv, sep="\n  ")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
