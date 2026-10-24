#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""t06_t11.py — aaf_pkg_review 六方案 T06 RC 容差 + T11 温度/供电角台架（tol 族，2026-10-24）

任务书 hardware/sim/AAF_基于已确认封装的候选参数与Zcode复核_2026-10-24.md §3/§5(3)(4)(5)：
  T06  模式A 未配对量产：P/N 独立随机（R±1% 基线、C±5% 基线，另跑 C±1%）
      → 每方案 ≥1000 组纯 Python 线性 RC 蒙特卡洛（L1） + ≥30 组 LTspice 完整角点（L2，本轮 A5=47 角）
      模式B 配对后：D8 官方考核条件「R·C 乘积异向配对（R×(1+m) 配 C×(1−m)，1% 单体失配）」
      （docs/design/spec/2026-10-18-aa-driver.md:78,103）重算。
      **二阶配对口径（本轮双口径并报）**：①各自配 = R1C1 与 R2C2 每线每级独立 m~U(±1%)，
      级内 R×(1+m) 配 C×(1−m)——D8 字面条件的自然延伸；②整线同 m（B2L）= 每线单一 m，
      R1C1/R2C2/R1C2 三乘积同保持——配对上限口径。二阶传递函数含 R1·C2 交叉乘积，
      各自配不保持该项 → CMRR 上限显著低于整线同 m（本轮 L1 数值实证：T2 极值角 48 vs 113 dB）。
      通道间（CH0↔CH1）不配对（D8 只考核同通道 P/N 两线；通道间配对属 Hratio 采购动作）。
      输出 16 kHz 衰减 / Hratio 幅相 / **CMRR 两口径**（RC 自身 = CH0 对称通道失配驱动；
      整链 Kelvin = CH1 真实接线 AIN1N 无源 RC 直连，结构性 + 失配）的 mean/σ/P1/P99，
      分布假设 = 带内均匀独立。
  T11  温度与供电角：−20/25/+85 ℃ × 模拟轨 3.3 V ±1.5%（TPS7A2033 精度 max），
      RC 温漂代入（C0G ±30 ppm/℃ spec:93；R ±100 ppm/℃ 声明假设——BOM AAF 电阻料号未定稿），
      全部 R 同向 / 全部 C 同向（τ 最坏向）；PM@温度 NOT VERIFIED（OPAx388 宏断环 AC 线性化
      仅 25–27 ℃ 有效，fo1_rc_review/REPORT.md §7.2 定论沿用，本轮 T2 t85 一跑复核）。

铁律（ask 原文）：真实接线 = 3 颗 OPA388（Xfa/Xfb=CH0 两线，Xfc=CH1 P 线）+ AIN1N 经
RKN/CGN 直连 Rsense 底端（Kelvin 地，无第四颗运放）；L1 线性 RC 结果一律标 L1 层，
不得称 LTspice 结果；.meas 定量值全部落 CSV。

层级：[L1] = 纯 Python 线性 MC（理想源+Rin130k+Cpin5p/端，Kelvin 结构项不在模型内→
其 Kelvin CMRR 仅含失配分量）；[L2] = LTspice 26.1.1 实跑（TI OPAx388 宏 Final 1.4）。

子命令：gen | run | mc | parse | plots | all
产物：netlists/t06_*.net t11_*.net、logs/ raw/、
      csv/t06_mc_{all,summary}.csv csv/t06_ltspice_{corners,summary}.csv
      csv/t06_l1_l2_xcheck.csv csv/t06_d7_d8_verdict.csv csv/t11_corners.csv、
      plots/t06_mc_dist_*.png plots/t06_ltspice_vs_mc.png plots/t06_kelvin_cmrr.png plots/t11_corner_scan.png
"""
from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
import shutil
import subprocess
import sys
import time
import zlib
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
NET = HERE / "netlists"
LOGD = HERE / "logs"
RAWD = HERE / "raw"
CSVD = HERE / "csv"
PLTD = HERE / "plots"

sys.path.insert(0, str(HERE))
import run_all  # noqa: E402  aaf_pkg_review 台架基建（本目录，非 fo1_rc_review）

sys.path.insert(0, run_all.PARSE_R5_DIR)
import parse_r5  # noqa: E402

ROOT = run_all.ROOT
LIB = run_all.LIB
SCHEMES = run_all.SCHEMES               # S0/S1 一阶 + T1–T4 二阶（任务书 §2 原文照录）
FMOD, MCLK = run_all.FMOD, run_all.MCLK
fmt = run_all.fmt

# ---- 容差 / 温漂 / 角点常量（来源全部声明，沿 fo1 t06_t11.py 同源口径）----
TOL_R = 0.01                              # R ±1%（任务书 §3/ask）
TOL_C5 = 0.05                             # C0G ±5% 基线（ask）
TOL_C1 = 0.01                             # 另跑 C±1%（ask）
PPM_R = 100e-6                            # R 温漂声明假设（0402 薄膜 1% 典型；AAF 料号未定稿）
PPM_C = 30e-6                             # C0G ±30 ppm/℃（spec:93）
TEMPS = {"m20": -20.0, "t25": 25.0, "t85": 85.0}          # spec:93
VSUP = {"v32505": 3.2505, "v33000": 3.3000, "v33495": 3.3495}  # 3.3V ±1.5%
RIN, CPIN = 130e3, 5e-12                  # fsadc 断态负载（fo1 assumptions A2/A3，沿用）
SEED = 20261024
NMC = 1000                                # ≥1000 组/方案/档（ask）
FLOOR_DB = 200.0                          # CMRR 数值地板判定（fo1 t06 同款）


# ----------------------------------------------------------------------
# 1. 器件键位（一阶 10 键 / 二阶 18 键；值 = 标称×(1+dev)）
# ----------------------------------------------------------------------
def _keys(sid: str):
    p = SCHEMES[sid]
    if p["topo"] == 1:
        ch0 = dict(rp=["r0p"], rn=["r0n"], cp=["cg0p"], cn=["cg0n"], cd="cd0")
        ch1 = dict(rp=["r1p"], rn=["rkn"], cp=["cg1p"], cn=["cgn"], cd="cd1")
    else:
        ch0 = dict(rp=["r0p1", "r0p2"], rn=["r0n1", "r0n2"],
                   cp=["cg0p1", "cg0p2"], cn=["cg0n1", "cg0n2"], cd="cd0")
        ch1 = dict(rp=["r1p1", "r1p2"], rn=["rkn1", "rkn2"],
                   cp=["cg1p1", "cg1p2"], cn=["cgn1", "cgn2"], cd="cd1")
    return ch0, ch1


def dev_vals(sid: str, devs: dict) -> dict:
    """相对偏差 dict → 元件值 dict。键位：一阶 r0p/cg0p/.../cd1；二阶每键带级号
    （r0p1/r0p2/cg0p1/...，P 线与 N 线各一级，CH1 N 线 = rkn*/cgn*）。"""
    p = SCHEMES[sid]
    ch0, ch1 = _keys(sid)
    base = {}
    for ch in (ch0, ch1):
        if p["topo"] == 1:
            for k in ch["rp"] + ch["rn"]:
                base[k] = p["r1"]
            for k in ch["cp"] + ch["cn"]:
                base[k] = p["cg1"]
        else:
            for j, r in ((1, p["r1"]), (2, p["r2"])):
                for pre in (ch["rp"][j - 1][:-1], ch["rn"][j - 1][:-1]):
                    base[pre + str(j)] = r
            for j, cg in ((1, p["cg1"]), (2, p["cg2"])):
                for pre in (ch["cp"][j - 1][:-1], ch["cn"][j - 1][:-1]):
                    base[pre + str(j)] = cg
        base[ch["cd"]] = p["cd"]
    return {k: base[k] * (1.0 + devs.get(k, 0.0)) for k in base}


def sg(x: float) -> str:
    return "+" if x > 0 else ("-" if x < 0 else "0")


# ----------------------------------------------------------------------
# 2. 角点集（确定性最坏角，非随机样本）：A5=47 角（≥30 满足 ask）+ A1=8 + B2=4
# ----------------------------------------------------------------------
def build_corners(sid: str) -> list[tuple[str, str, str, dict]]:
    ch0, ch1 = _keys(sid)
    out: list[tuple[str, str, str, dict]] = [("A5", "c00", "全标称", {})]

    # g1–g8：全局同向 R×CG×CD ∈ {±}³（τ_DM/τ_CM 绝对极值）
    for i, (dr, dcg, dcd) in enumerate(itertools.product((1, -1), repeat=3)):
        d = {}
        for ch in (ch0, ch1):
            for k in ch["rp"] + ch["rn"]:
                d[k] = dr * TOL_R
            for k in ch["cp"] + ch["cn"]:
                d[k] = dcg * TOL_C5
            d[ch["cd"]] = dcd * TOL_C5
        out.append(("A5", f"g{i + 1}",
                    f"全局 R{sg(dr)}1% CG{sg(dcg)}5% CD{sg(dcd)}5%", d))
    # m1–m16：CH0 P/N 整线失配（RC 自身 CMRR 最坏方向全覆盖）
    for i, (a, b, c, dd) in enumerate(itertools.product((1, -1), repeat=4)):
        d = {}
        for k in ch0["rp"]:
            d[k] = a * TOL_R
        for k in ch0["rn"]:
            d[k] = b * TOL_R
        for k in ch0["cp"]:
            d[k] = c * TOL_C5
        for k in ch0["cn"]:
            d[k] = dd * TOL_C5
        out.append(("A5", f"m{i + 1}",
                    f"CH0 失配 P(R{sg(a)}) N(R{sg(b)}) P(CG{sg(c)}) N(CG{sg(dd)})", d))
    # k1–k16：CH1 P/N 整线失配（Kelvin CMRR 失配分量最坏；本轮新增口径）
    for i, (a, b, c, dd) in enumerate(itertools.product((1, -1), repeat=4)):
        d = {}
        for k in ch1["rp"]:
            d[k] = a * TOL_R
        for k in ch1["rn"]:
            d[k] = b * TOL_R
        for k in ch1["cp"]:
            d[k] = c * TOL_C5
        for k in ch1["cn"]:
            d[k] = dd * TOL_C5
        out.append(("A5", f"k{i + 1}",
                    f"CH1 Kelvin 失配 P(R{sg(a)}) N(R{sg(b)}) P(CG{sg(c)}) N(CG{sg(dd)})", d))
    # d1–d4：CG 与 CD 反向（τ 部分抵消/反向极端角，沿 fo1 t06 d 角意图）
    out += [
        ("A5", "d1", "CH0 CG全-5% CD+5%（τ 反向）",
         {**{k: -TOL_C5 for k in ch0["cp"] + ch0["cn"]}, ch0["cd"]: TOL_C5}),
        ("A5", "d2", "CH0 CG全+5% CD-5%（τ 反向）",
         {**{k: TOL_C5 for k in ch0["cp"] + ch0["cn"]}, ch0["cd"]: -TOL_C5}),
        ("A5", "d3", "CH1 CG全-5% CD+5%（τ 反向）",
         {**{k: -TOL_C5 for k in ch1["cp"] + ch1["cn"]}, ch1["cd"]: TOL_C5}),
        ("A5", "d4", "CH1 CG全+5% CD-5%（τ 反向）",
         {**{k: TOL_C5 for k in ch1["cp"] + ch1["cn"]}, ch1["cd"]: -TOL_C5}),
    ]
    # x1–x2：通道间整通道反向（Hratio 幅相最坏）
    def ch_all(ch, sr, sc, scd):
        d = {}
        for k in ch["rp"] + ch["rn"]:
            d[k] = sr * TOL_R
        for k in ch["cp"] + ch["cn"]:
            d[k] = sc * TOL_C5
        d[ch["cd"]] = scd * TOL_C5
        return d
    out.append(("A5", "x1", "CH0 全+ vs CH1 全−（Hratio 最坏）",
                {**ch_all(ch0, 1, 1, 1), **ch_all(ch1, -1, -1, -1)}))
    out.append(("A5", "x2", "CH0 全− vs CH1 全+（Hratio 最坏）",
                {**ch_all(ch0, -1, -1, -1), **ch_all(ch1, 1, 1, 1)}))
    # q1–q8：C±1% 档全局角（ask「基线另跑 C±1%」）
    for i, (dr, dcg, dcd) in enumerate(itertools.product((1, -1), repeat=3)):
        d = {}
        for ch in (ch0, ch1):
            for k in ch["rp"] + ch["rn"]:
                d[k] = dr * TOL_R
            for k in ch["cp"] + ch["cn"]:
                d[k] = dcg * TOL_C1
            d[ch["cd"]] = dcd * TOL_C1
        out.append(("A1", f"q{i + 1}",
                    f"全局C±1% R{sg(dr)}1% CG{sg(dcg)}1% CD{sg(dcd)}1%", d))
    # b1–b4：模式B **整线同 m** 配对极值角（R1C1/R2C2/R1C2 三乘积同保持 → 配对上限口径）
    def pair_devs(ch, sp):
        d = {}
        for rk, ck in zip(ch["rp"], ch["cp"]):
            d[rk] = sp * TOL_R
            d[ck] = -sp * TOL_R
        for rk, ck in zip(ch["rn"], ch["cn"]):
            d[rk] = -sp * TOL_R
            d[ck] = sp * TOL_R
        return d
    out.append(("B2", "b1", "CH0 整线同m配对极值 P(R全+1/C全-1) N(反) CD+5%",
                {**pair_devs(ch0, 1), ch0["cd"]: TOL_C5}))
    out.append(("B2", "b2", "CH1 整线同m配对极值 P(R全+1/C全-1) N(反) CD-5%",
                {**pair_devs(ch1, 1), ch1["cd"]: -TOL_C5}))
    out.append(("B2", "b3", "双通道整线同m配对极值（Hratio@配对）",
                {**pair_devs(ch0, 1), ch0["cd"]: TOL_C5,
                 **pair_devs(ch1, 1), ch1["cd"]: -TOL_C5}))
    out.append(("B2", "b4", "CH0 整线配对极值 vs CH1 反向整线配对（Hratio@配对最坏）",
                {**pair_devs(ch0, 1), ch0["cd"]: TOL_C5,
                 **pair_devs(ch1, -1), ch1["cd"]: TOL_C5}))
    # b5/b6：模式B **各自配（每级独立 m）** 最坏角（仅二阶：级 1 P+N−、级 2 P−N+
    # → R1·C2 交叉乘积在线间最坏；一阶无级间自由度，与 b1/b2 反向重合故不生成）
    if SCHEMES[sid]["topo"] == 2:
        def pair_stage_devs(ch, s1, s2):
            d = {}
            for j, s in ((1, s1), (2, s2)):
                d[ch["rp"][j - 1]] = s * TOL_R
                d[ch["cp"][j - 1]] = -s * TOL_R
                d[ch["rn"][j - 1]] = -s * TOL_R
                d[ch["cn"][j - 1]] = s * TOL_R
            return d
        out.append(("B2", "b5", "CH0 各自配最坏（级1 P(R+1/C-1) N(反)、级2 反向，R1C2 极值）",
                    {**pair_stage_devs(ch0, 1, -1), ch0["cd"]: TOL_C5}))
        out.append(("B2", "b6", "CH1 各自配最坏（同上，Kelvin 口径）",
                    {**pair_stage_devs(ch1, 1, -1), ch1["cd"]: TOL_C5}))
    return out


def temp_devs(sid: str, temp: float) -> dict:
    """T11 RC 温漂：全部 R 同向 ±100ppm×ΔT、全部 C 同向 ±30ppm×ΔT（ΔT=T−25，τ 最坏向）。"""
    ch0, ch1 = _keys(sid)
    dT = temp - 25.0
    d = {}
    for ch in (ch0, ch1):
        for k in ch["rp"] + ch["rn"]:
            d[k] = PPM_R * dT
        for k in ch["cp"] + ch["cn"]:
            d[k] = PPM_C * dT
        d[ch["cd"]] = PPM_C * dT
    return d


# ----------------------------------------------------------------------
# 3. L2 网表生成（真实接线：3× OPAx388 + AIN1N Kelvin RC 直连，无第四运放）
# ----------------------------------------------------------------------
def _head(temp: float, vcc: float) -> str:
    return (f".include {LIB}\n.temp {temp:g}\n"
            f"Vcc vcc 0 DC {vcc:g}\nVee vee 0 DC 0\n")


def _ch0(v: dict, sid: str, ac_p: str, ac_n: str) -> str:
    t = (f"Vp vp 0 DC 2 AC {ac_p}\nVn vn 0 DC 2 AC {ac_n}\n"
         f"Xfa vp fpa vcc vee fpa OPAx388\nXfb vn fnb vcc vee fnb OPAx388\n")
    if SCHEMES[sid]["topo"] == 1:
        t += (f"Ra0 fpa a0p {fmt(v['r0p'])}\nCa0 a0p 0 {fmt(v['cg0p'])}\n"
              f"Rb0 fnb a0n {fmt(v['r0n'])}\nCb0 a0n 0 {fmt(v['cg0n'])}\n")
    else:
        t += (f"Ra01 fpa n0ap {fmt(v['r0p1'])}\nCa01 n0ap 0 {fmt(v['cg0p1'])}\n"
              f"Ra02 n0ap a0p {fmt(v['r0p2'])}\nCa02 a0p 0 {fmt(v['cg0p2'])}\n"
              f"Rb01 fnb n0an {fmt(v['r0n1'])}\nCb01 n0an 0 {fmt(v['cg0n1'])}\n"
              f"Rb02 n0an a0n {fmt(v['r0n2'])}\nCb02 a0n 0 {fmt(v['cg0n2'])}\n")
    return t + f"Cd0 a0p a0n {fmt(v['cd0'])}\n"


def _ch1(v: dict, sid: str, ac_b: str, ac_en) -> str:
    """CH1 真实接线：P 线经 Xfc 跟随器；N 线 = AIN1N 经 RKN/CGN 直连 Kelvin 地。
    ac_en=None → dm 网表（N 线源 = 地，单端口径 H1=V(a1p,na1)/1V）；
    ac_en='0.5' → cm 网表（Kelvin 地节点 en 受共模激励，结构性 CM→DM 可见）。"""
    t = f"Vb vb 0 DC 2 AC {ac_b}\n"
    nsrc = "0"
    if ac_en is not None:
        t += f"Ven en 0 DC 2 AC {ac_en}\n"
        nsrc = "en"
    t += "Xfc vb fcc vcc vee fcc OPAx388\n"
    if SCHEMES[sid]["topo"] == 1:
        t += (f"Ra1 fcc a1p {fmt(v['r1p'])}\nCa1 a1p 0 {fmt(v['cg1p'])}\n"
              f"Rkn {nsrc} na1 {fmt(v['rkn'])}\nCgn na1 0 {fmt(v['cgn'])}\n")
    else:
        t += (f"Ra11 fcc n1ap {fmt(v['r1p1'])}\nCa11 n1ap 0 {fmt(v['cg1p1'])}\n"
              f"Ra12 n1ap a1p {fmt(v['r1p2'])}\nCa12 a1p 0 {fmt(v['cg1p2'])}\n"
              f"Rkn1 {nsrc} n1an {fmt(v['rkn1'])}\nCgn1 n1an 0 {fmt(v['cgn1'])}\n"
              f"Rkn2 n1an na1 {fmt(v['rkn2'])}\nCgn2 na1 0 {fmt(v['cgn2'])}\n")
    return t + f"Cd1 a1p na1 {fmt(v['cd1'])}\n"


def _adc_load() -> str:
    return (f"Rin0 a0p a0n {RIN:g}\nCp0 a0p 0 {CPIN:g}\nCn0 a0n 0 {CPIN:g}\n"
            f"Rin1 a1p na1 {RIN:g}\nCp1 a1p 0 {CPIN:g}\nCn1 na1 0 {CPIN:g}\n")


OPTS = ".options plotwinsize=0 reltol=1e-6 abstol=1e-12 vntol=1e-9 chgtol=1e-15 trtol=1\n"
ACSW = ".ac dec 400 0.1 200Meg\n"
# .meas 全部落 CSV（ask 铁律）；ph() 差分语法在 LTspice 26.1.1 输出不可信（本轮实测
# proto: 返回 (26.02dB,180°) 而真实相位 −20.0°）→ 相位一律取 raw 复数插值，不用 .meas ph
MEAS_DM = (".meas AC h0_dc   FIND mag(V(a0p,a0n)) AT=0.1\n"
           ".meas AC h0_1k   FIND mag(V(a0p,a0n)) AT=1k\n"
           ".meas AC h0_8k   FIND mag(V(a0p,a0n)) AT=8k\n"
           ".meas AC h0_16k  FIND mag(V(a0p,a0n)) AT=16k\n"
           ".meas AC h0_fmod FIND mag(V(a0p,a0n)) AT=4.096Meg\n"
           ".meas AC h0_mclk FIND mag(V(a0p,a0n)) AT=16.384Meg\n"
           ".meas AC h1_dc   FIND mag(V(a1p,na1)) AT=0.1\n"
           ".meas AC h1_1k   FIND mag(V(a1p,na1)) AT=1k\n"
           ".meas AC h1_8k   FIND mag(V(a1p,na1)) AT=8k\n"
           ".meas AC h1_16k  FIND mag(V(a1p,na1)) AT=16k\n")
MEAS_CM = (".meas AC c0dm_10  FIND mag(V(a0p,a0n)) AT=10\n"
           ".meas AC c0dm_1k  FIND mag(V(a0p,a0n)) AT=1k\n"
           ".meas AC c0dm_16k FIND mag(V(a0p,a0n)) AT=16k\n"
           ".meas AC c0dm_max MAX mag(V(a0p,a0n)) FROM=10 TO=16k\n"
           ".meas AC c1dm_10  FIND mag(V(a1p,na1)) AT=10\n"
           ".meas AC c1dm_1k  FIND mag(V(a1p,na1)) AT=1k\n"
           ".meas AC c1dm_16k FIND mag(V(a1p,na1)) AT=16k\n"
           ".meas AC c1dm_max MAX mag(V(a1p,na1)) FROM=10 TO=16k\n"
           ".meas AC cm0_16k  FIND mag(V(a0p)) AT=16k\n"
           ".meas AC cm0_fmod FIND mag(V(a0p)) AT=4.096Meg\n"
           ".meas AC cm1_fmod FIND mag(V(a1p)) AT=4.096Meg\n")


def net_dm(v: dict, sid: str, temp=27.0, vcc=3.3) -> str:
    """差模 AC：CH0 Vp/Vn=±0.5（差分 1V）+ CH1 Vb=1 单端（E=地；物理真实激励口径，
    fo1 t06 同源）；两通道仅共地/共轨（AC 地），一表同取 H0 与 H1。"""
    return (f"* t06/t11 dm {sid}: H0=V(a0p,a0n)/1V, H1=V(a1p,na1)/1V; "
            f"3xOPA388 + AIN1N Kelvin RC（无第四运放）\n"
            + _head(temp, vcc) + _ch0(v, sid, "0.5", "-0.5")
            + _ch1(v, sid, "1", None) + _adc_load() + ACSW + OPTS
            + MEAS_DM + ".save V(a0p) V(a0n) V(a1p) V(na1)\n.end\n")


def net_cm(v: dict, sid: str, temp=27.0, vcc=3.3) -> str:
    """共模 AC：CH0 Vp=Vn=0.5（RC 自身口径）+ CH1 Vb=Ven=0.5（整链 Kelvin 口径，
    Kelvin 地节点 en 受共模激励→结构性 CM→DM 可见）；归一 /0.5 → 每 1V 共模。"""
    return (f"* t06 cm {sid}: RC自身=V(a0p,a0n)/0.5, Kelvin=V(a1p,na1)/0.5; "
            f"两口径一表同取（通道解耦）\n"
            + _head(temp, vcc) + _ch0(v, sid, "0.5", "0.5")
            + _ch1(v, sid, "0.5", "0.5") + _adc_load() + ACSW + OPTS
            + MEAS_CM + ".save V(a0p) V(a0n) V(a1p) V(na1)\n.end\n")


def net_loop(sid: str, temp=25.0, vcc=3.3) -> str:
    """环路 PM（t00_loop 口径：跟随器 β=1 断环 + 方案真实差分半电路负载；
    fo1_rc_review/t06_t11.py net_loop 同源，二阶负载按任务书 §2 梯形扩展）。
    Cd→2Cd 虚地、Rin 130k 差分→65k 半电路、Cpin 5p/端。"""
    p = SCHEMES[sid]
    if p["topo"] == 1:
        lad = (f"Ra1 fpa pa1 {fmt(p['r1'])}\nCa1 pa1 0 {fmt(p['cg1'])}\n"
               f"Cd pa1 0 {fmt(p['cd'] * 2)}\n")
    else:
        lad = (f"Ra1 fpa n1a {fmt(p['r1'])}\nCa1 n1a 0 {fmt(p['cg1'])}\n"
               f"Ra2 n1a pa1 {fmt(p['r2'])}\nCa2 pa1 0 {fmt(p['cg2'])}\n"
               f"Cd pa1 0 {fmt(p['cd'] * 2)}\n")
    return (f"* t11 loop PM {sid}: T=-V(fpa)/V(inn) mag 跨 1 处 pm=180+ph\n"
            + _head(temp, vcc)
            + "Vp vp 0 DC 2 AC 0\nVinn inn 0 DC 2 AC 1\n"
            "Xfa vp inn vcc vee fpa OPAx388\n"
            + lad + f"Rin pa1 0 {RIN / 2:g}\nCpa pa1 0 {CPIN:g}\n"
            + ACSW + OPTS + ".save V(fpa) V(inn)\n.end\n")


def net_op(temp: float, vcc: float) -> str:
    """.op：裸跟随器 V(in)-V(out)=Vos(T)（OPAx388 宏唯一 TEMP 参数 = VOS_DRIFT 实证）。
    方案无关（同一颗运放模型）→ 全六方案共用 3 跑。"""
    return (f"* t11 op: Vos(T)（VOS_DRIFT: DC+POL*DRIFT*(TEMP-27), 0.005uV/C）方案无关\n"
            + _head(temp, vcc)
            + "Vi vi 0 DC 2\nXf vi fo vcc vee fo OPAx388\n"
            ".op\n.save V(vi) V(fo)\n.end\n")


def gen_all() -> list[Path]:
    for d in (NET, LOGD, RAWD, CSVD, PLTD):
        d.mkdir(exist_ok=True)
    written = []
    for sid in SCHEMES:
        cs = sid.lower()
        for mode, tag, _desc, devs in build_corners(sid):
            v = dev_vals(sid, devs)
            for kind in ("dm", "cm"):
                f = NET / f"t06_{cs}_{mode}_{tag}_{kind}.net"
                f.write_text(net_dm(v, sid) if kind == "dm" else net_cm(v, sid))
                written.append(f)
        for tk, tv in TEMPS.items():
            for vk, vv in VSUP.items():
                v = dev_vals(sid, temp_devs(sid, tv))
                f = NET / f"t11_{cs}_{tk}_{vk}_dm.net"
                f.write_text(net_dm(v, sid, temp=tv, vcc=vv))
                written.append(f)
                if tk == "t25":                     # PM 仅 25℃（宏 25–27℃ 有效窗内）
                    f = NET / f"t11_{cs}_{tk}_{vk}_loop.net"
                    f.write_text(net_loop(sid, temp=tv, vcc=vv))
                    written.append(f)
        if sid == "T2":                              # 宏塌陷复核一跑（m20/t85 不再全跑）
            f = NET / "t11_t2_t85_v33000_loop.net"
            f.write_text(net_loop(sid, temp=85.0, vcc=3.3))
            written.append(f)
    for tk, tv in TEMPS.items():                     # Vos(T)：方案无关 3 跑
        f = NET / f"t11_x_{tk}_v33000_op.net"
        f.write_text(net_op(tv, 3.3))
        written.append(f)
    return written


# ----------------------------------------------------------------------
# 4. 批量运行（run_all.run_net 幂等 + ltspice-sim 锁排队；超时串行重试一轮）
# ----------------------------------------------------------------------
def _run_job(args):
    net, to = args
    ok, out = run_all.run_net(Path(net), timeout=to)
    return net, ok, out


def run_all_nets(workers: int = 4) -> int:
    jobs = []
    for f in sorted(NET.glob("t06_*.net")):
        jobs.append((str(f), 300))
    for f in sorted(NET.glob("t11_*_dm.net")) + sorted(NET.glob("t11_*_loop.net")):
        jobs.append((str(f), 300))
    for f in sorted(NET.glob("t11_x_*_op.net")):
        jobs.append((str(f), 120))
    print(f"[run] {len(jobs)} nets, {workers} workers")
    t0, fails = time.time(), []

    def archive(net):
        p = Path(net)
        for src, dst in ((p.with_suffix(".log"), LOGD / p.with_suffix(".log").name),
                         (p.with_suffix(".raw"), RAWD / p.with_suffix(".raw").name)):
            if src.exists():
                shutil.copy2(src, dst)

    with ProcessPoolExecutor(max_workers=workers) as ex:
        for net, ok, out in ex.map(_run_job, jobs):
            if not ok:
                fails.append((net, out))
                print(f"  FAIL {Path(net).name}: {out[:120]}")
            else:
                archive(net)
    # 锁超时顺序重试（ask：遇锁超时顺序重试）
    still = []
    for net, out in fails:
        print(f"  RETRY {Path(net).name}")
        ok, out2 = run_all.run_net(Path(net), timeout=600)
        if ok:
            archive(net)
        else:
            still.append((net, out2))
    print(f"[run] done in {time.time() - t0:.0f}s, fails={len(still)}")
    for net, out in still:
        print("  note:", Path(net).name, out[:200])
    return len(still)


# ----------------------------------------------------------------------
# 5. L1 线性 RC 引擎（纯 Python/numpy 复数 MNA；理想源驱动）
# ----------------------------------------------------------------------
F_KEY = np.array([0.1, 1e3, 8e3, 16e3, FMOD, MCLK])
F_CMRR = np.logspace(1, math.log10(16e3), 241)       # 10 Hz–16 kHz CMRR 网格
F_ALL = np.unique(np.concatenate([F_KEY, F_CMRR]))


def _pair_h(f, lp, ln, cd, vs_p, vs_n):
    """单通道 P/N 阶梯对（每线 1 或 2 级 (R,C)），理想源 vs_p/vs_n，跨接 Cd+Rin，
    输出端 Cpin/端。返回 V(out_p)−V(out_n)（复数数组）。"""
    s = 2j * np.pi * f
    ycd = s * cd + 1.0 / RIN
    if len(lp) == 1:
        (rp, cp), (rn, cn) = lp[0], ln[0]
        y11 = 1.0 / rp + s * (cp + CPIN) + ycd
        y22 = 1.0 / rn + s * (cn + CPIN) + ycd
        det = y11 * y22 - ycd * ycd
        i1, i2 = vs_p / rp, vs_n / rn
        v2p = (i1 * y22 + ycd * i2) / det
        v2n = (y11 * i2 + ycd * i1) / det
        return v2p - v2n
    (r1p, c1p), (r2p, c2p) = lp
    (r1n, c1n), (r2n, c2n) = ln
    g1p, g2p, g1n, g2n = 1 / r1p, 1 / r2p, 1 / r1n, 1 / r2n
    Y = np.zeros(f.shape + (4, 4), dtype=complex)
    Y[..., 0, 0] = g1p + s * c1p + g2p
    Y[..., 0, 1] = -g2p
    Y[..., 1, 0] = -g2p
    Y[..., 1, 1] = g2p + s * (c2p + CPIN) + ycd
    Y[..., 1, 3] = -ycd
    Y[..., 2, 2] = g1n + s * c1n + g2n
    Y[..., 2, 3] = -g2n
    Y[..., 3, 2] = -g2n
    Y[..., 3, 3] = g2n + s * (c2n + CPIN) + ycd
    Y[..., 3, 1] = -ycd
    I = np.zeros(f.shape + (4,), dtype=complex)
    I[..., 0] = vs_p / r1p
    I[..., 2] = vs_n / r1n
    V = np.linalg.solve(Y, I[..., None])[..., 0]
    return V[..., 1] - V[..., 3]


def _lines(v: dict, sid: str, ch: str):
    if ch == 0:
        rp, rn, cp, cn = "r0p", "r0n", "cg0p", "cg0n"
    else:
        rp, rn, cp, cn = "r1p", "rkn", "cg1p", "cgn"
    if SCHEMES[sid]["topo"] == 1:
        return [(v[rp], v[cp])], [(v[rn], v[cn])]
    return ([(v[rp + "1"], v[cp + "1"]), (v[rp + "2"], v[cp + "2"])],
            [(v[rn + "1"], v[cn + "1"]), (v[rn + "2"], v[cn + "2"])])


def l1_curves(v: dict, sid: str, f=F_ALL):
    lp0, ln0 = _lines(v, sid, 0)
    lp1, ln1 = _lines(v, sid, 1)
    return dict(
        h0dm=_pair_h(f, lp0, ln0, v["cd0"], 0.5, -0.5),
        h0cm=_pair_h(f, lp0, ln0, v["cd0"], 1.0, 1.0),     # 每 1V 共模
        h1dm=_pair_h(f, lp1, ln1, v["cd1"], 1.0, 0.0),
        h1cm=_pair_h(f, lp1, ln1, v["cd1"], 1.0, 1.0),     # 每 1V 共模
    )


def _at(f, arr, f0):
    return complex(np.interp(math.log(f0), np.log(f), np.real(arr))
                   + 1j * np.interp(math.log(f0), np.log(f), np.imag(arr)))


def db(x) -> float:
    a = abs(x)
    return 20 * math.log10(a) if a > 0 else -999.0


def metrics_from_hs(h0dm, h0cm, h1dm, h1cm, f) -> dict:
    out: dict = {}
    g0dc, g1dc = db(_at(f, h0dm, 0.1)), db(_at(f, h1dm, 0.1))
    for fk in (1e3, 8e3, 16e3):
        y0, y1 = _at(f, h0dm, fk), _at(f, h1dm, fk)
        out[f"h0_{int(fk)}_db"], out[f"h1_{int(fk)}_db"] = db(y0), db(y1)
        out[f"hr_mag_{int(fk)}_db"] = db(y0) - db(y1)
        out[f"hr_ph_{int(fk)}_deg"] = math.degrees(
            math.atan2(y0.imag, y0.real) - math.atan2(y1.imag, y1.real))
    out["atten16k_db"] = -(out["h0_16000_db"] - g0dc)
    out["atten16k_ch1_db"] = -(out["h1_16000_db"] - g1dc)
    out["d1_db"] = -(db(_at(f, h0dm, FMOD)) - g0dc)
    out["d3_db"] = -(db(_at(f, h0dm, MCLK)) - g0dc)
    band = (f >= 10) & (f <= 16e3)
    if h0cm is not None:
        cmrr = 20 * np.log10(np.abs(h0dm[band]) / np.maximum(np.abs(h0cm[band]), 1e-30))
        k = int(np.argmin(cmrr))
        out["cmrr_rc_min_db"] = float(cmrr[k])
        out["cmrr_rc_worst_hz"] = float(f[band][k])
        out["cmrr_rc_16k_db"] = float(cmrr[-1])
    if h1cm is not None:
        cmrr = 20 * np.log10(np.abs(h1dm[band]) / np.maximum(np.abs(h1cm[band]), 1e-30))
        k = int(np.argmin(cmrr))
        out["cmrr_kelvin_min_db"] = float(cmrr[k])
        out["cmrr_kelvin_worst_hz"] = float(f[band][k])
        out["cmrr_kelvin_16k_db"] = float(cmrr[-1])
    return out


# ---- MC 采样（带内均匀独立；B2 = D8 官方 R·C 乘积异向配对，二阶逐级各自配）----
def sample_devs(sid: str, mode: str, rng) -> dict:
    ch0, ch1 = _keys(sid)
    devs = {}
    if mode in ("A5", "A1"):
        ct = TOL_C5 if mode == "A5" else TOL_C1
        for ch in (ch0, ch1):
            for k in ch["rp"] + ch["rn"]:
                devs[k] = rng.uniform(-TOL_R, TOL_R)
            for k in ch["cp"] + ch["cn"]:
                devs[k] = rng.uniform(-ct, ct)
            devs[ch["cd"]] = rng.uniform(-ct, ct)
        return devs
    if mode == "B2":
        for ch in (ch0, ch1):
            for rk_list, ck_list in ((ch["rp"], ch["cp"]), (ch["rn"], ch["cn"])):
                for rk, ck in zip(rk_list, ck_list):   # 每线每级独立 m（各自配）
                    m = rng.uniform(-TOL_R, TOL_R)
                    devs[rk] = m
                    devs[ck] = -m
            devs[ch["cd"]] = rng.uniform(-TOL_C5, TOL_C5)
        return devs
    if mode == "B2L":
        for ch in (ch0, ch1):
            for rk_list, ck_list in ((ch["rp"], ch["cp"]), (ch["rn"], ch["cn"])):
                m = rng.uniform(-TOL_R, TOL_R)          # 每线单一 m（整线同 m）
                for rk, ck in zip(rk_list, ck_list):
                    devs[rk] = m
                    devs[ck] = -m
            devs[ch["cd"]] = rng.uniform(-TOL_C5, TOL_C5)
        return devs
    raise ValueError(mode)


MC_MODES = [
    ("A5", "模式A 未配对 R±1% C±5% 独立均匀"),
    ("A1", "模式A R±1% C±1% 独立均匀（ask 另跑档）"),
    ("B2", "模式B R·C 乘积异向配对 m~U(±1%)（D8 官方考核条件的二阶自然延伸 = "
           "**各自配**：每线每级独立 m，R×(1+m) 配 C×(1−m)；通道间不配对，C_D 独立 ±5%。"
           "二阶梯形传递函数含 R1·C2 交叉乘积，级间独立 m 不保持该项 → CMRR 上限受制"),
    ("B2L", "模式B 整线同 m 配对（二阶上限口径）：每线单一 m（R1/R2 同偏、C1/C2 同偏），"
            "R1C1/R2C2/R1C2 三乘积同保持到 (1−m²)；一阶无级间自由度与 B2 恒等（自检）"),
]
MC_KEYS = ["atten16k_db", "atten16k_ch1_db",
           "hr_mag_1000_db", "hr_mag_8000_db", "hr_mag_16000_db",
           "hr_ph_1000_deg", "hr_ph_8000_deg", "hr_ph_16000_deg",
           "d1_db", "d3_db",
           "cmrr_rc_min_db", "cmrr_rc_16k_db",
           "cmrr_kelvin_min_db", "cmrr_kelvin_16k_db"]
KELVIN_L1_NOTE = ("L1 理想源模型：Kelvin 结构项（运放闭环输出阻抗 vs 无源 N 线）不在模型内，"
                  "cmrr_kelvin_* 仅含失配分量（真实整链 Kelvin 口径以 L2 为准，"
                  "L2 标称角即结构地板）")


def run_mc() -> None:
    rows, summ = [], []
    for sid in SCHEMES:
        for mode, desc in MC_MODES:
            rng = np.random.default_rng(SEED + zlib.crc32(f"{sid}{mode}".encode()) % 10000)
            ms = []
            for i in range(NMC):
                m = metrics_from_hs(**l1_curves(dev_vals(sid, sample_devs(sid, mode, rng)), sid),
                                    f=F_ALL)
                m["sample"] = i
                ms.append(m)
            keys = [k for k in ms[0] if k != "sample"]
            rows += [dict(scheme=sid, mode=mode, **{k: m[k] for k in keys}) for m in ms]
            for k in keys:
                a = np.array([m[k] for m in ms], dtype=float)
                summ.append(dict(scheme=sid, mode=mode, desc=desc, metric=k, n=NMC,
                                 mean=float(a.mean()), sigma=float(a.std(ddof=1)),
                                 p1=float(np.percentile(a, 1)),
                                 p99=float(np.percentile(a, 99)),
                                 min=float(a.min()), max=float(a.max()),
                                 layer="L1",
                                 dist="uniform independent (B2: per-line per-stage paired m)",
                                 note=KELVIN_L1_NOTE if k.startswith("cmrr_kelvin") else ""))
    with (CSVD / "t06_mc_all.csv").open("w", newline="\n", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    with (CSVD / "t06_mc_summary.csv").open("w", newline="\n", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(summ[0].keys()))
        w.writeheader()
        w.writerows(summ)
    print(f"[mc] {len(rows)} samples -> csv/t06_mc_all.csv + t06_mc_summary.csv")
    # L1 标称自检：DC 分压 = Rin/(Rin+2ΣR)（t00 口径 0.999278 同族）
    for sid in SCHEMES:
        v = dev_vals(sid, {})
        h = l1_curves(v, sid, np.array([0.1]))["h0dm"]
        lp, _ = _lines(v, sid, 0)
        rsum = sum(r for r, _ in lp) * 2
        print(f"[mc] {sid} L1 DC check: |H0(0.1Hz)|={abs(h[0]):.6f} "
              f"theory={RIN / (RIN + rsum):.6f}")


# ----------------------------------------------------------------------
# 6. LTspice 解析（dm/cm/loop/op → CSV；.meas 值一并落表）
# ----------------------------------------------------------------------
def _raw_diff(rawpath: Path, pa: str, na: str) -> np.ndarray:
    r = parse_r5.Raw(str(rawpath))
    return np.array(r.col(pa), dtype=complex) - np.array(r.col(na), dtype=complex)


def _meas_db(logpath: Path) -> dict:
    return run_all.parse_meas_log(logpath)      # {name: dB float}（aaf run_all 口径）


def parse_t06() -> None:
    rows = []
    MEAS_F = dict(h0_dc=0.1, h0_1k=1e3, h0_8k=8e3, h0_16k=16e3, h0_fmod=FMOD,
                  h0_mclk=MCLK, h1_dc=0.1, h1_1k=1e3, h1_8k=8e3, h1_16k=16e3,
                  c0dm_10=10, c0dm_1k=1e3, c0dm_16k=16e3,
                  c1dm_10=10, c1dm_1k=1e3, c1dm_16k=16e3,
                  cm0_16k=16e3, cm0_fmod=FMOD, cm1_fmod=FMOD)
    for sid in SCHEMES:
        cs = sid.lower()
        for mode, tag, desc, devs in build_corners(sid):
            dm_raw = RAWD / f"t06_{cs}_{mode}_{tag}_dm.raw"
            cm_raw = RAWD / f"t06_{cs}_{mode}_{tag}_cm.raw"
            row = dict(scheme=sid, mode=mode, corner=tag, desc=desc,
                       devs=json.dumps(devs, sort_keys=True))
            if not dm_raw.exists() or not cm_raw.exists():
                row["status"] = "NOT VERIFIED (raw missing)"
                rows.append(row)
                continue
            try:
                dmd, cmd_ = parse_r5.Raw(str(dm_raw)), parse_r5.Raw(str(cm_raw))
                f, fc = dmd.f, cmd_.f
                assert len(f) == len(fc) and np.allclose(f, fc), "dm/cm 网格不一致"
                h0 = np.array(dmd.col("V(a0p)"), dtype=complex) - np.array(dmd.col("V(a0n)"), dtype=complex)
                h1 = np.array(dmd.col("V(a1p)"), dtype=complex) - np.array(dmd.col("V(na1)"), dtype=complex)
                h0c_raw = np.array(cmd_.col("V(a0p)"), dtype=complex) - np.array(cmd_.col("V(a0n)"), dtype=complex)
                h1c_raw = np.array(cmd_.col("V(a1p)"), dtype=complex) - np.array(cmd_.col("V(na1)"), dtype=complex)
                se0 = np.array(cmd_.col("V(a0p)"), dtype=complex)   # 单端 CM 残留（D2 口径）
                se1 = np.array(cmd_.col("V(a1p)"), dtype=complex)
                h0c, h1c = h0c_raw / 0.5, h1c_raw / 0.5             # 每 1V 共模
                if not (0.98 < abs(h0[0]) < 1.01 and 0.98 < abs(h1[0]) < 1.01):
                    raise RuntimeError("raw curve corrupt")
                m = metrics_from_hs(h0, h0c, h1, h1c, f)
                # .meas 值落 CSV + 与 raw 插值同口径交叉校验（xchk_*）
                md = _meas_db(LOGD / f"t06_{cs}_{mode}_{tag}_dm.log")
                mc = _meas_db(LOGD / f"t06_{cs}_{mode}_{tag}_cm.log")
                for mk, fq in MEAS_F.items():
                    mv = md.get(mk, mc.get(mk))
                    if mv is None:
                        continue
                    m[f"meas_{mk}"] = mv
                    if mk.endswith("_max"):
                        continue
                    if mk.startswith("h0"):
                        h = h0
                    elif mk.startswith("h1"):
                        h = h1
                    elif mk.startswith("c0dm"):
                        h = h0c_raw
                    elif mk.startswith("c1dm"):
                        h = h1c_raw
                    elif mk.startswith("cm0"):
                        h = se0
                    else:
                        h = se1
                    m[f"xchk_{mk}"] = mv - db(_at(f, h, fq))
                row.update(status="OK", **m)
            except Exception as e:                           # noqa: BLE001
                row["status"] = f"NOT VERIFIED ({e})"
            rows.append(row)
    lead = ["scheme", "mode", "corner", "desc", "status"]
    keys = lead + [k for k in dict.fromkeys(
        k for r in rows for k in r if k not in lead + ["devs"])] + ["devs"]
    with (CSVD / "t06_ltspice_corners.csv").open("w", newline="\n",
                                                 encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    # 汇总（确定性角点集合，非随机样本；CMRR 数值地板角剔除并计数）
    summ = []
    for sid in SCHEMES:
        for mode in ("A5", "A1", "B2"):
            sel = [r for r in rows if r["scheme"] == sid and r["mode"] == mode
                   and r.get("status") == "OK"]
            for k in ("atten16k_db", "atten16k_ch1_db", "hr_mag_16000_db",
                      "hr_ph_16000_deg", "d1_db", "d3_db",
                      "cmrr_rc_min_db", "cmrr_kelvin_min_db"):
                vals = [r[k] for r in sel if k in r]
                if not vals:
                    continue
                sub = [v for v in vals if v < FLOOR_DB] if k.startswith("cmrr") else vals
                n_floor = len(vals) - len(sub)
                if not sub:
                    summ.append(dict(scheme=sid, mode=mode, metric=k, n=0, mean="",
                                     sigma="", p1="", p99="", min="", max="",
                                     layer="L2",
                                     note=f"全部 {len(vals)} 角为数值地板（≥{FLOOR_DB:g} dB），"
                                          f"失配散布见 MC 统计"))
                    continue
                a = np.array(sub, dtype=float)
                summ.append(dict(scheme=sid, mode=mode, metric=k, n=len(a),
                                 mean=float(a.mean()), sigma=float(a.std(ddof=1)),
                                 p1=float(np.percentile(a, 1)),
                                 p99=float(np.percentile(a, 99)),
                                 min=float(a.min()), max=float(a.max()), layer="L2",
                                 note=("确定性角点集合（非随机样本），σ/P1/P99 仅作汇总；"
                                       f"数值地板角剔除 n={n_floor}"
                                       if n_floor else
                                       "确定性角点集合（非随机样本），σ/P1/P99 仅作汇总")))
    with (CSVD / "t06_ltspice_summary.csv").open("w", newline="\n",
                                                 encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(summ[0].keys()))
        w.writeheader()
        w.writerows(summ)
    print(f"[parse] t06 corners={len(rows)} -> t06_ltspice_corners.csv + summary")


def loop_pm_ugf(rawpath: Path):
    """环路 PM/UGF（fo1_rc_review/run_all.py:422 同口径复制：T=-V(fpa)/V(inn)，
    mag 跨 1 处 pm=180+ph）。"""
    d = parse_r5.Raw(str(rawpath))
    freq = d.f
    T = -np.array(d.col("V(fpa)")) / np.array(d.col("V(inn)"))
    mag, ph = np.abs(T), np.angle(T) * 180 / math.pi
    for i in range(1, len(freq)):
        if mag[i - 1] > 1 >= mag[i]:
            return float(freq[i]), float(180 + ph[i])
    return None, None


PM_NV = ("NOT VERIFIED (OPAx388 macro loop-AC linearization collapses at .temp "
         "outside 25-27C: DC loop gain ~2.4e4 vs 2.4e7 — model defect, fo1 REPORT "
         "§7.2; dm AC unaffected)")


def parse_t11() -> None:
    rows = []
    vos_by_t = {}
    for tk, tv in TEMPS.items():
        op_raw = RAWD / f"t11_x_{tk}_v33000_op.raw"
        if op_raw.exists():
            r = parse_r5.Raw(str(op_raw))
            vos_by_t[tk] = float(np.real(r.col("V(vi)")[0]) - np.real(r.col("V(fo)")[0]))
    for sid in SCHEMES:
        cs = sid.lower()
        for tk, tv in TEMPS.items():
            for vk, vv in VSUP.items():
                row = dict(scheme=sid, temp_c=tv, vcc_v=vv,
                           vos_op_v=(vos_by_t.get(tk, "") if vk == "v33000" else ""),
                           vos_note="方案无关（裸跟随器单跑 t11_x_*_op 共用）"
                                    if vk == "v33000" else "")
                dm_raw = RAWD / f"t11_{cs}_{tk}_{vk}_dm.raw"
                if dm_raw.exists():
                    f = parse_r5.Raw(str(dm_raw)).f
                    h0 = _raw_diff(dm_raw, "V(a0p)", "V(a0n)")
                    h1 = _raw_diff(dm_raw, "V(a1p)", "V(na1)")
                    if not (0.98 < abs(h0[0]) < 1.01 and 0.98 < abs(h1[0]) < 1.01):
                        row.update(status_dm="NOT VERIFIED (raw curve corrupt)")
                    else:
                        m = metrics_from_hs(h0, None, h1, None, f)
                        row.update(status_dm="OK", **m)
                    md = _meas_db(LOGD / f"t11_{cs}_{tk}_{vk}_dm.log")
                    for mk in ("h0_16k", "h1_16k", "h0_fmod"):
                        if mk in md:
                            row[f"meas_{mk}"] = md[mk]
                else:
                    row.update(status_dm="NOT VERIFIED (raw missing)")
                lp_raw = RAWD / f"t11_{cs}_{tk}_{vk}_loop.raw"
                if lp_raw.exists():
                    dl = parse_r5.Raw(str(lp_raw))
                    tgm = np.abs(-np.array(dl.col("V(fpa)")) / np.array(dl.col("V(inn)")))
                    if tgm[0] > 1e6:
                        ugf, pm = loop_pm_ugf(lp_raw)
                        row.update(pm_deg=pm, ugf_hz=ugf, status_loop="OK")
                    else:
                        row.update(pm_deg="", ugf_hz="", status_loop=PM_NV)
                else:
                    row.update(pm_deg="", ugf_hz="",
                               status_loop=("NOT VERIFIED (PM@温度不跑：宏 25–27℃ 限制，"
                                            "fo1 REPORT §7.2 沿用；T2 t85 复核一跑见该行)"
                                            if tk != "t25" else "NOT VERIFIED (raw missing)"))
                rows.append(row)
    lead = ["scheme", "temp_c", "vcc_v", "status_dm", "status_loop"]
    keys = lead + [k for k in dict.fromkeys(
        k for r in rows for k in r if k not in lead)]
    with (CSVD / "t11_corners.csv").open("w", newline="\n", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    print(f"[parse] t11 rows={len(rows)} -> csv/t11_corners.csv")


def xcheck() -> None:
    """L1↔L2 标称角对拍 + S0/S1 冒烟锚交叉校验（口径一致性证据）。"""
    rows = []
    corners = {}
    pth = CSVD / "t06_ltspice_corners.csv"
    if pth.exists():
        for r in csv.DictReader(pth.open(encoding="utf-8")):
            if r["corner"] == "c00" and r.get("status") == "OK":
                corners[r["scheme"]] = r
    for sid in SCHEMES:
        l1 = metrics_from_hs(**l1_curves(dev_vals(sid, {}), sid), f=F_ALL)
        l2 = corners.get(sid)
        for k in ("atten16k_db", "d1_db", "d3_db", "hr_mag_16000_db",
                  "hr_ph_16000_deg", "cmrr_rc_min_db", "cmrr_kelvin_min_db"):
            v1 = l1.get(k)
            v2 = float(l2[k]) if (l2 and l2.get(k) not in (None, "")) else None
            if k.startswith("cmrr_rc") and v1 is not None and v1 > FLOOR_DB:
                note = "标称匹配对称网表：L1/L2 均数值地板（非物理值），失配散布见 MC/角点"
            elif k.startswith("cmrr_kelvin") and v2 is not None:
                note = ("Kelvin 结构项 L1 缺失（理想源）→ L2 值即结构地板，"
                        "delta 无意义（L1 失配=0）")
            else:
                note = ("L1 理想源 vs L2 真实 OPA388 宏"
                        "（跟随器闭环输出阻抗 + C_pin 差异）")
            rows.append(dict(scheme=sid, metric=k,
                             l1=float(v1) if v1 is not None else "",
                             l2=v2 if v2 is not None else "",
                             delta=(float(v1) - v2) if (v1 is not None and v2 is not None
                                                     and not k.startswith("cmrr")) else "",
                             note=note))
    # S0/S1 冒烟锚（smoke_anchor.csv 本轮实测值）：D1=dm @4.096M；D2=单端 CM 残留
    anchors = {"S0_D1": 40.6891, "S0_D2": 46.4104, "S1_D1": 38.7351, "S1_D2": 44.1291}
    for sid, items in (("S0", ("D1", "D2")), ("S1", ("D1", "D2"))):
        r = corners.get(sid)
        if not r:
            continue
        for it in items:
            if it == "D1":
                mine = float(r["d1_db"])
                rows.append(dict(scheme=sid, metric=f"anchor_{sid}_{it}",
                                 l1="", l2=mine, delta=mine - anchors[f"{sid}_{it}"],
                                 note=f"对锚 smoke_anchor {anchors[f'{sid}_{it}']}（容差 0.5dB）"))
            else:
                mv = r.get(f"meas_cm0_fmod")
                if mv not in (None, ""):
                    mine = -float(mv)      # 0.5V 激励绝对 dB 取负 = t00 口径衰减量
                    rows.append(dict(scheme=sid, metric=f"anchor_{sid}_{it}",
                                     l1="", l2=mine, delta=mine - anchors[f"{sid}_{it}"],
                                     note=f"对锚 smoke_anchor {anchors[f'{sid}_{it}']}"
                                          f"（S1 锚已 +6.0206 折回 0.5V 绝对口径）"))
    with (CSVD / "t06_l1_l2_xcheck.csv").open("w", newline="\n",
                                              encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["scheme", "metric", "l1", "l2", "delta", "note"])
        w.writeheader()
        w.writerows(rows)
    print(f"[xcheck] {len(rows)} rows -> csv/t06_l1_l2_xcheck.csv")


def verdicts() -> None:
    """D4/D7/D8 判定（阈值 = spec V1 表：D4≤0.05 满分/>0.5 淘汰；D7 σ≤0.05/>0.05；
    D8≥80 及格/≥100 满分。CMRR 两口径分列；FAIL 如实保留）。"""
    mc = {}
    pth = CSVD / "t06_mc_summary.csv"
    if pth.exists():
        for r in csv.DictReader(pth.open(encoding="utf-8")):
            mc[(r["scheme"], r["mode"], r["metric"])] = r
    lt, corners = {}, {}
    pth = CSVD / "t06_ltspice_corners.csv"
    if pth.exists():
        for r in csv.DictReader(pth.open(encoding="utf-8")):
            if r.get("status") != "OK":
                continue
            lt[(r["scheme"], r["mode"])] = lt.get((r["scheme"], r["mode"]), []) + [r]
            if r["corner"] == "c00":
                corners[r["scheme"]] = r
    rows = []
    for sid in SCHEMES:
        c0 = corners.get(sid, {})
        d4n = float(c0["atten16k_db"]) if c0.get("atten16k_db") else None
        if d4n is not None:
            rows.append(dict(scheme=sid, dim="D4", mode="标称", cond="L2 c00 标称角",
                             value=round(d4n, 4), unit="dB",
                             verdict=("PASS" if d4n <= 0.05 else
                                      "FAIL" if d4n > 0.5 else "PARTIAL"),
                             threshold="≤0.05 满分 / >0.5 淘汰",
                             basis=f"L2 标称 16k 衰减（smoke 同口径）"))
        a5 = lt.get((sid, "A5"), [])
        if a5:
            d4c = max(float(r["atten16k_db"]) for r in a5 if r.get("atten16k_db"))
            rows.append(dict(scheme=sid, dim="D4", mode="A5", cond="模式A 47 角最坏",
                             value=round(d4c, 4), unit="dB",
                             verdict=("PASS" if d4c <= 0.05 else
                                      "FAIL" if d4c > 0.5 else "PARTIAL"),
                             threshold="≤0.05 满分 / >0.5 淘汰",
                             basis=f"L2 确定性角点集合 max（n={len(a5)}）"))
        for mode, cond in (("A5", "模式A R±1%C±5%"), ("A1", "模式A R±1%C±1%"),
                           ("B2", "模式B R·C异向配对-各自配(D8字面延伸)"),
                           ("B2L", "模式B R·C异向配对-整线同m(二阶上限)")):
            r = mc.get((sid, mode, "atten16k_db"))
            if r:
                v = float(r["sigma"])
                rows.append(dict(scheme=sid, dim="D7", mode=mode, cond=cond,
                                 value=round(v, 5), unit="dB",
                                 verdict=("PASS" if v <= 0.05 else "FAIL"),
                                 threshold="σ≤0.05 dB（满分≤0.01）",
                                 basis=f"MC L1 n={r['n']}；mean={float(r['mean']):.5f}, "
                                       f"P1={float(r['p1']):.4f}, P99={float(r['p99']):.4f}"))
            for cal, mk in (("D8-RC自身", "cmrr_rc_min_db"),
                            ("D8-Kelvin", "cmrr_kelvin_min_db")):
                r = mc.get((sid, mode, mk))
                if r:
                    v = float(r["p1"])
                    note = ("MC L1 n=%s P1；mean=%.1f, min=%.1f, σ=%.1f"
                            % (r["n"], float(r["mean"]), float(r["min"]), float(r["sigma"])))
                    if mk.startswith("cmrr_kelvin"):
                        note += "；L1 仅失配分量（结构项缺失，见 KELVIN_L1_NOTE）"
                    rows.append(dict(scheme=sid, dim=cal, mode=mode, cond=cond,
                                     value=round(v, 1), unit="dB",
                                     verdict=("PASS" if v >= 80 else "FAIL"),
                                     threshold="CMRR≥80 dB @10Hz–16kHz（满分≥100）",
                                     basis=note))
        # L2 角点佐证：RC 失配角最坏 / Kelvin 结构地板与失配角最坏；
        # B2 分两口径：各自配角（b5/b6，仅二阶）与整线同m角（b1–b4）
        bsel = lt.get((sid, "B2"), [])
        for cal, mk in (("D8-RC自身", "cmrr_rc_min_db"),
                        ("D8-Kelvin", "cmrr_kelvin_min_db")):
            vals = [float(r[mk]) for r in lt.get((sid, "A5"), [])
                    if r.get(mk) not in (None, "") and float(r[mk]) < FLOOR_DB]
            if vals:
                rows.append(dict(scheme=sid, dim=cal, mode="A5-LTspice",
                                 cond="模式A 真失配角（L2 角点集合）",
                                 value=round(min(vals), 1), unit="dB",
                                 verdict=("PASS" if min(vals) >= 80 else "FAIL"),
                                 threshold="CMRR≥80 dB @10Hz–16kHz",
                                 basis=f"LTspice L2 最坏角（确定性，非统计；n={len(vals)}）"
                                       + (f"；标称 c00 结构地板={float(c0[mk]):.1f} dB"
                                          if mk == "cmrr_kelvin_min_db"
                                          and c0.get(mk) not in (None, "") else "")))
            for bmode, btags, bcond in (
                    ("B2-LTspice", ("b5", "b6"), "模式B 各自配最坏角（级间反 m，R1C2 极值）"),
                    ("B2L-LTspice", ("b1", "b2", "b3", "b4"), "模式B 整线同m配对极值角")):
                vals = [float(r[mk]) for r in bsel
                        if r["corner"] in btags and r.get(mk) not in (None, "")
                        and float(r[mk]) < FLOOR_DB]
                if vals:
                    rows.append(dict(scheme=sid, dim=cal, mode=bmode,
                                     cond=bcond, value=round(min(vals), 1), unit="dB",
                                     verdict=("PASS" if min(vals) >= 80 else "FAIL"),
                                     threshold="CMRR≥80 dB @10Hz–16kHz",
                                     basis=f"LTspice L2 最坏角（确定性，非统计；n={len(vals)}）"
                                           + ("；一阶无 b5/b6（各自配≡整线同m）"
                                              if SCHEMES[sid]["topo"] == 1 else "")))
    with (CSVD / "t06_d7_d8_verdict.csv").open("w", newline="\n",
                                               encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["scheme", "dim", "mode", "cond", "value",
                                           "unit", "verdict", "threshold", "basis"])
        w.writeheader()
        w.writerows(rows)
    print(f"[verdict] {len(rows)} rows -> csv/t06_d7_d8_verdict.csv")


# ----------------------------------------------------------------------
# 7. 图
# ----------------------------------------------------------------------
def make_plots() -> None:
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["font.sans-serif"] = ["Noto Sans CJK SC", "DejaVu Sans"]
    matplotlib.rcParams["axes.unicode_minus"] = False
    import matplotlib.pyplot as plt

    mc = list(csv.DictReader((CSVD / "t06_mc_all.csv").open(encoding="utf-8")))
    lt = [r for r in csv.DictReader((CSVD / "t06_ltspice_corners.csv").open(encoding="utf-8"))
          if r.get("status") == "OK"]
    colors = {"A5": "#dc2626", "A1": "#2563eb", "B2": "#059669", "B2L": "#d97706"}
    labels = {"A5": "A 未配对 R1%/C5%", "A1": "A 未配对 R1%/C1%",
              "B2": "B R·C 异向配对-各自配 1%",
              "B2L": "B R·C 异向配对-整线同m 1%"}

    # 7.1 每方案 4 联分布（含 Kelvin 两口径）+ LTspice 角点 rug
    for sid in SCHEMES:
        fig, axes = plt.subplots(1, 4, figsize=(18, 3.8))
        panels = ((axes[0], "atten16k_db", "16 kHz 衰减 (dB, D4 口径)"),
                  (axes[1], "hr_mag_16000_db", "Hratio 幅度误差 @16k (dB)"),
                  (axes[2], "cmrr_rc_min_db", "CMRR RC自身 最坏 10Hz–16kHz (dB)"),
                  (axes[3], "cmrr_kelvin_min_db", "CMRR Kelvin 最坏 10Hz–16kHz (dB)"))
        for ax, key, xlab in panels:
            for mode in ("A5", "A1", "B2", "B2L"):
                a = np.array([float(r[key]) for r in mc
                              if r["scheme"] == sid and r["mode"] == mode
                              and float(r[key]) < FLOOR_DB])
                ax.hist(a, bins=60, histtype="step", lw=1.4, color=colors[mode],
                        label=f"{labels[mode]} (n={len(a)})")
            for mode in ("A5", "A1", "B2", "B2L"):
                a = np.array([float(r[key]) for r in lt
                              if r["scheme"] == sid and r["mode"] == mode
                              and r.get(key) not in (None, "")
                              and float(r[key]) < FLOOR_DB])
                if len(a):
                    ax.plot(a, np.full(len(a), ax.get_ylim()[1] * 0.98), "|",
                            color=colors[mode], ms=10, mew=1.2)
            ax.set_xlabel(xlab + ("（L1 Kelvin=仅失配分量）" if "kelvin" in key else ""))
            ax.grid(alpha=0.3)
            if key.startswith("cmrr"):
                ax.axvline(80, color="k", ls="--", lw=0.8, label="D8 及格 80 dB")
        axes[0].set_ylabel("组数")
        axes[0].legend(fontsize=7)
        p = SCHEMES[sid]
        fig.suptitle(f"T06 容差 MC（L1 线性 RC，n={NMC}/档）+ LTspice 角点（| Rug）— {sid} "
                     f"{'一阶' if p['topo'] == 1 else '二阶'} "
                     f"R1={p['r1']:g} CG1={p['cg1'] * 1e9:g}nF"
                     + (f" R2={p['r2']:g} CG2={p['cg2'] * 1e9:g}nF"
                        if p["topo"] == 2 else "")
                     + f" CD={p['cd'] * 1e12:g}pF")
        fig.tight_layout()
        f = PLTD / f"t06_mc_dist_{sid.lower()}.png"
        fig.savefig(f, dpi=140)
        plt.close(fig)
        print(f"[plots] {f}")

    # 7.2 L1 MC vs L2 角点散点（atten16k–CMRR 平面，RC 与 Kelvin 两口径）
    for cal, key, fname, title in (
            ("RC自身", "cmrr_rc_min_db", "t06_ltspice_vs_mc.png",
             "CMRR_min RC自身 (dB)"),
            ("Kelvin", "cmrr_kelvin_min_db", "t06_kelvin_cmrr.png",
             "CMRR_min 整链Kelvin (dB)")):
        fig, axes = plt.subplots(1, 6, figsize=(19, 3.4), sharey=True)
        for ax, sid in zip(axes, SCHEMES):
            for mode in ("A5", "A1", "B2", "B2L"):
                a = np.array([[float(r["atten16k_db"]), float(r[key])]
                              for r in mc if r["scheme"] == sid and r["mode"] == mode
                              and float(r[key]) < FLOOR_DB])
                if len(a):
                    ax.plot(a[:, 0], a[:, 1], ".", ms=1.5, alpha=0.25,
                            color=colors[mode], label=labels[mode])
            a = np.array([[float(r["atten16k_db"]), float(r[key])]
                          for r in lt if r["scheme"] == sid
                          and r.get(key) not in (None, "") and float(r[key]) < FLOOR_DB])
            if len(a):
                ax.plot(a[:, 0], a[:, 1], "kx", ms=7, mew=1.3, label="LTspice 角点 (L2)")
            ax.axhline(80, color="k", ls="--", lw=0.8)
            ax.set_title(sid, fontsize=10)
            ax.set_xlabel("atten16k (dB)")
            ax.grid(alpha=0.3)
        axes[0].set_ylabel(title)
        axes[0].legend(fontsize=7, markerscale=4)
        fig.suptitle(f"T06 容差平面：16k 衰减 vs CMRR-{cal}（点=L1 Python MC，×=L2 LTspice 角点；"
                     "虚线=D8 80dB；Kelvin 图 L1 点仅含失配分量）")
        fig.tight_layout()
        f = PLTD / fname
        fig.savefig(f, dpi=140)
        plt.close(fig)
        print(f"[plots] {f}")

    # 7.3 T11 角点扫描（D4 / Hratio / PM vs T×V）
    if (CSVD / "t11_corners.csv").exists():
        t11 = list(csv.DictReader((CSVD / "t11_corners.csv").open(encoding="utf-8")))
        fig, axes = plt.subplots(1, 3, figsize=(13.5, 3.8))
        for sid, mk in zip(SCHEMES, "oX+sv^"):
            for vk, col in zip(VSUP, ("#dc2626", "#374151", "#2563eb")):
                xs = [r for r in t11 if r["scheme"] == sid
                      and r["vcc_v"] == f"{VSUP[vk]:g}" and r.get("status_dm") == "OK"]
                if not xs:
                    continue
                t = [float(r["temp_c"]) for r in xs]
                axes[0].plot(t, [float(r["atten16k_db"]) for r in xs], mk, color=col,
                             ms=5, label=f"{sid} V={VSUP[vk]:g}" if sid == "S0" else "")
                axes[1].plot(t, [float(r["hr_mag_16000_db"]) for r in xs], mk,
                             color=col, ms=5)
                lp = [r for r in xs if r.get("status_loop") == "OK" and r.get("pm_deg")]
                if lp:
                    axes[2].plot([float(r["temp_c"]) for r in lp],
                                 [float(r["pm_deg"]) for r in lp], mk, color=col, ms=5)
        axes[0].set_title("D4 @16k (dB)", fontsize=10)
        axes[1].set_title("Hratio 幅度误差 @16k (dB)", fontsize=10)
        axes[2].set_title("环路 PM (deg)（仅 25℃ 实测；宏 25–27℃ 限制）", fontsize=10)
        for ax in axes:
            ax.set_xlabel("温度 (℃)")
            ax.grid(alpha=0.3)
        axes[0].legend(fontsize=7)
        fig.suptitle("T11 温度×模拟轨角点（RC 温漂代入：R±100ppm/℃ 声明假设、C0G ±30ppm/℃ "
                     "全同向；轨 3.3V±1.5%；PM@−20/+85℃ NOT VERIFIED 宏模型限制）")
        fig.tight_layout()
        f = PLTD / "t11_corner_scan.png"
        fig.savefig(f, dpi=140)
        plt.close(fig)
        print(f"[plots] {f}")


# ======================================================================
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("cmd", nargs="?", default="all",
                    choices=["gen", "run", "mc", "parse", "plots", "all"])
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    if args.cmd in ("gen", "all"):
        n = gen_all()
        print(f"[gen] {len(n)} netlists")
    if args.cmd in ("run", "all"):
        bad = run_all_nets(args.workers)
        if bad:
            print(f"[run] {bad} fails — 继续解析，缺失项将标 NOT VERIFIED")
    if args.cmd in ("mc", "all"):
        run_mc()
    if args.cmd in ("parse", "all"):
        parse_t06()
        parse_t11()
        xcheck()
        verdicts()
    if args.cmd in ("plots", "all"):
        make_plots()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
