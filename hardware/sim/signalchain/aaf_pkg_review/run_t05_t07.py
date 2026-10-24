#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""run_t05_t07.py — aaf_pkg_review 测试族 stab：T05 噪声 + T07 真实 OPA388 环路稳定性（六方案）

任务依据：hardware/sim/AAF_基于已确认封装的候选参数与Zcode复核_2026-10-24.md §3/§5(3)(4)(5)。
  T05 噪声   .noise 带内(0.1–16k)/宽带(0.1–2.048M=fMOD/2)、各案 RC 增量（D6a 双口径）、
             与运放/ADC 噪声区分（LTspice .noise 逐器件归属）——口径沿用上一轮
             fo1_rc_review/run_stab.py（逐行同构，锚定值对拍见 ANCHORS）。
  T07 稳定性 真实 OPA388 环路：PM（断环方式声明）、全频闭环 peaking（C9≤6dB）、瞬态过冲；
             二阶重点 = 首级 R1+CG1 与后级 R2+CG2 对运放容性负载的**叠加影响**
             （loop 全梯形 vs loopL 仅首级 分解跑 + 解析 Z_load@UGF 交叉）；
             AIN1N 不当作运放（CH1 Kelvin 无源梯形，无环路）；
             PM@温度沿用上一轮宏模型限制结论（fo1 REPORT §7.2：.temp 仅 25–27 ℃，
             温度趋势 NOT VERIFIED），本轮不重推、只交 25 ℃。

铁律（任务书 §5(2) 同款）：真实接线 = 3 颗 OPA388（T/M/B 三线）+ AIN1N 经 RC 直连
Rsense 底端 E（Kelvin 地），**无第四颗运放**。按通道拆分考核：
  CH0 = a0p/a0n（T、M 两线各 1 颗 OPA388——真实接线本就对称）
  CH1 = a1p/na1（B 线 OPA388 + na1 Kelvin 无源 RC 直连地；DC 工作点 B=1.2V、na1=0V）

口径来源（逐条引用，不重新发明）：
  * D6a 线性口径 (n1−n3)/n3、正交口径 √(n1²−n3²)/n3、阈值 ≤10% 满分/>30% 淘汰
    —— fo1_rc_review/run_stab.py（r4 冻结口径）；n3 = 顶层 R 全 `noiseless`
  * 积分 = parse_r5.noise_nv 同法（log 网格 trapz，0.1 Hz 起积分）
  * ADC 负载 = Rin 130k 差分 + C_pin 5p/端（断态口径，采样开关/C_S 不在噪声网表）
  * PM 断环 = 输入参考断环：AC 1V 注入跟随器同相端（Vinn），反相端 DC 偏置 AC 地，
    β=1，T=−V(fcc)/V(inn)，PM=180+ph@|T|=1（t00/gen_fo net_loop 同口径，
    FO1_BASE 锚 98.57°/2786 kHz）
  * C9 主口径 = 跟随器输出节点全频闭环峰值 ≤6 dB（r4 §4.2）；ADC 引脚节点副口径
  * 瞬态过冲 = +100 mV 阶跃（10 ns 沿），差分 ADC 引脚电压，相对各自终值
  * LSB = 2×2.442/2^24 = 290.98 nV（parse_r5.py:32 同源）

六方案（SCHEMES 见 run_all.py，任务书 §2 表原文照录）：
  S0 47Ω/47nF/820pF（一阶，≡旧 FO1_BASE） S1 100Ω/22nF/820pF（一阶，≡旧 FO1_A）
  T1 100/10n+100/10n+820p  T2 100/10n+120/10n+820p
  T3 68/10n+150/10n+820p   T4 82/10n+160/10n+820p（二阶 R1→CG1→R2→CG2，Cd 跨 ADC 节点）

锚定（S0/S1 电气等同旧 FO1_BASE/FO1_A → 本轮实测须复现上一轮 t05/t07 数值）：
  锚值出处 = fo1_rc_review/csv/{t05_noise,t07_stability}.csv（只读引用，不改动）。

产物（文件名含方案ID+测试ID）：netlists/t05_* t07_*、logs/、raw/、
  csv/t05_noise.csv、csv/t07_stability.csv、csv/t07_load_decomp.csv、plots/t05_* t07_*。

用法：python3 run_t05_t07.py gen|lint|run|parse|all
"""
from __future__ import annotations

import csv
import math
import re
import shutil
import sys
import time
from pathlib import Path

import numpy as np

sys.dont_write_bytecode = True          # 不写 __pycache__（先置位再 import 本台架模块）

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_all                            # noqa: E402  本台架（aaf_pkg_review，非 fo1_rc_review）
from run_all import (CSVD, LIB, LOGD, NET, PARSE_R5_DIR, RAWD, SCHEMES,  # noqa: E402
                     fmt, run_net)

sys.path.insert(0, PARSE_R5_DIR)
import parse_r5                           # noqa: E402

PLOTD = HERE / "plots"
OLD = Path("/media/anning/data/Project/DE-DRMS/hardware/sim/signalchain/fo1_rc_review")  # 只读锚定源

FMOD = 4.096e6
FB_BROAD = 2.048e6                        # fMOD/2（宽带积分上沿，D6b 口径）
FB_INBAND = 16e3                          # 测量通带上沿（带内口径）
LSB_V = 2.0 * 2.442 / 2 ** 24             # 290.98 nV（parse_r5.py:32 同源）
C9_TH = 6.0                               # dB，spec C9
D6A_FULL, D6A_FAIL = 10.0, 30.0           # %，spec D6a（沿用 fo1 口径）

TOPT = ".options plotwinsize=0 reltol=1e-6 abstol=1e-12 vntol=1e-9 chgtol=1e-15 trtol=1\n"
HEAD = f".include {LIB}\nVcc vcc 0 DC 3.3\nVee vee 0 DC 0\n"

# ---- 锚定值（上一轮 fo1_rc_review 实测；S0≡FO1_BASE、S1≡FO1_A，容差内须复现）----
ANCH_T05 = {   # (sid, ch, variant) -> (inband_nV, bb_nV)；n3 无 inband 锚也一并给
    ("s0", "ch0", "n1"): (1245.31, 3301.13), ("s0", "ch1", "n1"): (887.43, 2352.09),
    ("s0", "ch0", "n3"): (1235.53, 3275.19), ("s0", "ch1", "n3"): (873.65, 2315.97),
    ("s1", "ch0", "n1"): (1254.55, 3254.75), ("s1", "ch1", "n1"): (901.50, 2338.48),
    ("s1", "ch0", "n3"): (1233.84, 3201.01), ("s1", "ch1", "n3"): (872.46, 2263.51),
}
ANCH_D6A = {("s0", "ch0"): 0.7917, ("s0", "ch1"): 1.5596,
            ("s1", "ch0"): 1.6788, ("s1", "ch1"): 3.3124}
ANCH_T07 = {  # (sid, test) -> dict；os 锚 = 上一轮 overshoot_pct
    ("s0", "loop_ch0"): dict(ugf=2786121.2, pm=98.57),
    ("s0", "loop_ch1"): dict(ugf=2786121.2, pm=98.55),
    ("s1", "loop_ch0"): dict(ugf=4597269.9, pm=96.93),
    ("s1", "loop_ch1"): dict(ugf=4597269.9, pm=96.91),
    ("s0", "pk_ch0"): dict(c9=0.691), ("s0", "pk_ch1"): dict(c9=0.694),
    ("s1", "pk_ch0"): dict(c9=0.330), ("s1", "pk_ch1"): dict(c9=0.333),
    ("s0", "os_ch0"): dict(os=0.0), ("s0", "os_ch1"): dict(os=0.0),
    ("s1", "os_ch0"): dict(os=0.0001), ("s1", "os_ch1"): dict(os=0.0001),
}
TOL = dict(noise_rel=0.003, d6a_abs=0.03, pm=0.05, ugf_rel=0.002,
           c9=0.005, os=0.005)           # 同网表+同引擎应近位复现；超差先查口径再判


# ======================================================================
# 1. 网表生成（一阶逐行对齐 fo1_rc_review/run_stab.py 生成物，lint 自动同一性对拍；
#    二阶按任务书 §2 梯形扩展同口径：R1→n1(CG1)→R2→ADC(CG2)，Cd 跨 ADC 节点 P/N）
# ======================================================================
def _nl(flag: bool) -> str:
    return " noiseless" if flag else ""


def ch0_body(p: dict, noiseless: bool) -> str:
    """CH0 差分通道（T/M 双跟随器，真实接线本就对称）。noiseless=True 即 n3 变体
    （顶层 R 全 `noiseless`，D6a 分母，r4 v9d_nl 口径）。"""
    n = _nl(noiseless)
    if p["topo"] == 1:
        return (f"Vp vp 0 DC 2 AC 1\nVn vn 0 DC 2 AC 0\n"
                f"XfT vp ftp vcc vee ftp OPAx388\nXfM vn ftm vcc vee ftm OPAx388\n"
                f"Ra1 ftp a0p {fmt(p['r1'])}{n}\nCa1 a0p 0 {fmt(p['cg1'])}\n"
                f"Rb1 ftm a0n {fmt(p['r1'])}{n}\nCb1 a0n 0 {fmt(p['cg1'])}\n"
                f"Cd a0p a0n {fmt(p['cd'])}\n"
                f"Rin a0p a0n 130000{n}\nCpa a0p 0 5p\nCna a0n 0 5p\n")
    return (f"Vp vp 0 DC 2 AC 1\nVn vn 0 DC 2 AC 0\n"
            f"XfT vp ftp vcc vee ftp OPAx388\nXfM vn ftm vcc vee ftm OPAx388\n"
            f"Ra1 ftp n1a {fmt(p['r1'])}{n}\nCa1 n1a 0 {fmt(p['cg1'])}\n"
            f"Ra2 n1a a0p {fmt(p['r2'])}{n}\nCa2 a0p 0 {fmt(p['cg2'])}\n"
            f"Rb1 ftm n1b {fmt(p['r1'])}{n}\nCb1 n1b 0 {fmt(p['cg1'])}\n"
            f"Rb2 n1b a0n {fmt(p['r2'])}{n}\nCb2 a0n 0 {fmt(p['cg2'])}\n"
            f"Cd a0p a0n {fmt(p['cd'])}\n"
            f"Rin a0p a0n 130000{n}\nCpa a0p 0 5p\nCna a0n 0 5p\n")


def ch1_body(p: dict, noiseless: bool) -> str:
    """CH1 差分通道（真实非对称接线）：B 线 OPA388 → 梯形 → a1p；
    AIN1N=na1 经 Kelvin 无源梯形直连地（**无第四颗运放**）。DC：B=1.2V、na1=0V。
    二阶 Kelvin N 线同梯形（RKN1/CGN1/RKN2/CGN2，与 run_all.py fullchain_net 同构）。"""
    n = _nl(noiseless)
    if p["topo"] == 1:
        return (f"Vb bin 0 DC 1.2 AC 1\n"
                f"XfB bin fbk vcc vee fbk OPAx388\n"
                f"Rf fbk a1p {fmt(p['r1'])}{n}\nCg a1p 0 {fmt(p['cg1'])}\n"
                f"Cd a1p na1 {fmt(p['cd'])}\n"
                f"RKN 0 na1 {fmt(p['r1'])}{n}\nCGN na1 0 {fmt(p['cg1'])}\n"
                f"Rin a1p na1 130000{n}\nCpa a1p 0 5p\nCna na1 0 5p\n")
    return (f"Vb bin 0 DC 1.2 AC 1\n"
            f"XfB bin fbk vcc vee fbk OPAx388\n"
            f"Rf1 fbk n1a {fmt(p['r1'])}{n}\nCg1 n1a 0 {fmt(p['cg1'])}\n"
            f"Rf2 n1a a1p {fmt(p['r2'])}{n}\nCg2 a1p 0 {fmt(p['cg2'])}\n"
            f"Cd a1p na1 {fmt(p['cd'])}\n"
            f"RKN1 0 n1n {fmt(p['r1'])}{n}\nCGN1 n1n 0 {fmt(p['cg1'])}\n"
            f"RKN2 n1n na1 {fmt(p['r2'])}{n}\nCGN2 na1 0 {fmt(p['cg2'])}\n"
            f"Rin a1p na1 130000{n}\nCpa a1p 0 5p\nCna na1 0 5p\n")


def t05_net(sid: str, p: dict, ch: str, variant: str) -> str:
    body = ch0_body(p, variant == "n3") if ch == "ch0" else ch1_body(p, variant == "n3")
    obs = "V(a0p,a0n)" if ch == "ch0" else "V(a1p,na1)"
    src = "Vp" if ch == "ch0" else "Vb"
    note = ("all resistors noisy (total = D6a numerator / D6b)" if variant == "n1"
            else "top-level R all `noiseless` (OPA388-only = D6a denominator, r4 v9d_nl)")
    wire = ("T/M both OPA388 followers (real CH0 is symmetric)" if ch == "ch0"
            else "B OPA388 follower + AIN1N Kelvin RC direct (NO 4th opamp)")
    return (f"* t05 {sid.lower()} {ch} {variant} — noise, {note}\n"
            f"* {ch} wiring: {wire}; ADC load Rin130k+5p/side, switches OFF (static)\n"
            f"{HEAD}{body}"
            f".noise {obs} {src} dec 200 0.1 50Meg\n{TOPT}"
            f".save v(onoise) v(inoise)\n.end\n")


def _loop_load(p: dict, mode: str) -> str:
    """T07 断环负载。mode: full=真实全梯形（ch0 差分半电路 / ch1 真实非对称全负载）；
    first1=仅首级（R1+CG1，二阶专属分解诊断——隔离后级 R2+CG2 的叠加影响）。"""
    if mode == "first1":                    # 仅二阶；负载 = R1 + CG1（首级容性负载单独考核）
        return (f"Rf1 fcc n1a {fmt(p['r1'])}\nCg1 n1a 0 {fmt(p['cg1'])}\n")
    if p["topo"] == 1:                      # ch0 差分半电路（t00_loop 同构：Cd×2 虚地+65k+5p）
        return (f"Ra1 fcc pa1 {fmt(p['r1'])}\nCa1 pa1 0 {fmt(p['cg1'])}\n"
                f"Cd pa1 0 {fmt(2 * p['cd'])}\nRin pa1 0 65000\nCpa pa1 0 5p\n")
    return (f"Rf1 fcc n1a {fmt(p['r1'])}\nCg1 n1a 0 {fmt(p['cg1'])}\n"
            f"Rf2 n1a pa1 {fmt(p['r2'])}\nCg2 pa1 0 {fmt(p['cg2'])}\n"
            f"Cd pa1 0 {fmt(2 * p['cd'])}\nRin pa1 0 65000\nCpa pa1 0 5p\n")


def _loop_load_ch1(p: dict) -> str:
    if p["topo"] == 1:
        return (f"Rf fcc a1p {fmt(p['r1'])}\nCg a1p 0 {fmt(p['cg1'])}\n"
                f"Cd a1p na1 {fmt(p['cd'])}\n"
                f"RKN 0 na1 {fmt(p['r1'])}\nCGN na1 0 {fmt(p['cg1'])}\n"
                f"Rin a1p na1 130000\nCpa a1p 0 5p\nCna na1 0 5p\n")
    return (f"Rf1 fcc n1a {fmt(p['r1'])}\nCg1 n1a 0 {fmt(p['cg1'])}\n"
            f"Rf2 n1a a1p {fmt(p['r2'])}\nCg2 a1p 0 {fmt(p['cg2'])}\n"
            f"Cd a1p na1 {fmt(p['cd'])}\n"
            f"RKN1 0 n1n {fmt(p['r1'])}\nCGN1 n1n 0 {fmt(p['cg1'])}\n"
            f"RKN2 n1n na1 {fmt(p['r2'])}\nCGN2 na1 0 {fmt(p['cg2'])}\n"
            f"Rin a1p na1 130000\nCpa a1p 0 5p\nCna na1 0 5p\n")


def t07_loop_net(sid: str, p: dict, ch: str, mode: str = "full") -> str:
    """T07 环路增益网表。断环方式（声明）：输入参考断环——AC 1V 注入跟随器同相输入端
    （Vinn），反相端接 DC 偏置源（AC 地）；β=1 电压跟随器环路在输入处断开，
    T(f)=−V(fcc)/V(inn)=Aol(带真实负载)；PM=180+ph@|T|=1（t00/gen_fo 同口径）。"""
    if ch == "ch1":
        load = (f"Vb vb 0 DC 1.2 AC 0\nVinn inn 0 DC 1.2 AC 1\n"
                f"XfB vb inn vcc vee fcc OPAx388\n" + _loop_load_ch1(p))
        lnote = "real asymmetric CH1 full load (AIN1N passive Kelvin ladder, NO 4th opamp)"
    else:
        dc = 2.0
        load = (f"Vp vp 0 DC {dc:g} AC 0\nVinn inn 0 DC {dc:g} AC 1\n"
                f"Xfa vp inn vcc vee fcc OPAx388\n" + _loop_load(p, mode))
        if mode == "first1":
            lnote = "FIRST-STAGE-ONLY load R1+CG1 (2nd-order decomposition diag; no 2nd stage)"
        elif p["topo"] == 1:
            lnote = "differential half-circuit (t00_loop konvention)"
        else:
            lnote = ("differential half-circuit, 2-stage ladder R1-CG1-R2-CG2 "
                     "(2Cd virt-gnd + 65k + 5p, t00_loop extension)")
    return (f"* t07 {sid.lower()} loop{'' if mode == 'full' else 'l'}_{ch} — follower loop gain, "
            f"broken at input\n"
            f"* inject AC1 at IN+ (Vinn), IN- at DC bias (AC gnd); T=-V(fcc)/V(inn)\n"
            f"* load: {lnote}\n"
            f"{HEAD}{load}"
            f".ac dec 400 0.1 200Meg\n{TOPT}"
            f".save V(fcc) V(inn)\n.end\n")


def t07_pk_net(sid: str, p: dict, ch: str) -> str:
    """T07 全频闭环 peaking（C9≤6dB）。真实 OPA388 闭环小信号 AC。
    C9 主口径 = 跟随器输出节点（V(ftp,ftm) / V(fbk)）峰值（r4 §4.2）；ADC 引脚副口径。"""
    if ch == "ch0":
        # 整行精确替换（不可子串替换：换序会把 "DC 2 AC 0.5" 劈成 "DC 2 AC -0.5.5"）
        body = ch0_body(p, False).replace(
            "Vp vp 0 DC 2 AC 1", "Vp vp 0 DC 2 AC 0.5").replace(
            "Vn vn 0 DC 2 AC 0", "Vn vn 0 DC 2 AC -0.5")
        pin, fo = "V(a0p,a0n)", "V(ftp,ftm)"
        sv = "V(a0p) V(a0n) V(ftp) V(ftm)"
    else:
        body = ch1_body(p, False)
        pin, fo = "V(a1p,na1)", "V(fbk)"
        sv = "V(a1p) V(na1) V(fbk)"
    return (f"* t07 {sid.lower()} pk_{ch} — closed-loop full-band peaking (C9<=6dB)\n"
            f"* C9 primary = follower-output node ({fo}); ADC-pin node secondary ({pin})\n"
            f"{HEAD}{body}"
            f".ac dec 400 0.1 200Meg\n{TOPT}"
            f".meas AC g_dc  FIND mag({pin}) AT=0.1\n"
            f".meas AC pk_pin MAX mag({pin})\n"
            f".meas AC pk_pin_f WHEN mag({pin})=pk_pin\n"
            f".meas AC gdc_fo FIND mag({fo}) AT=0.1\n"
            f".meas AC pk_fo MAX mag({fo})\n"
            f".meas AC pk_fo_f WHEN mag({fo})=pk_fo\n"
            f".save {sv}\n.end\n")


def t07_os_net(sid: str, p: dict, ch: str) -> str:
    """T07 瞬态过冲：+100 mV 小信号阶跃（10 ns 沿），闭环差分 ADC 引脚电压响应。
    CH0 双端反相阶跃（差分 +0.1V、共模恒 2V）；CH1 B 线单端阶跃（1.15→1.25V）。"""
    if ch == "ch0":
        body = ch0_body(p, False).replace(
            "Vp vp 0 DC 2 AC 1", "Vp vp 0 PWL(0 1.95 1u 1.95 1.01u 2.0)").replace(
            "Vn vn 0 DC 2 AC 0", "Vn vn 0 PWL(0 2.05 1u 2.05 1.01u 2.0)")
        obs, sv = "V(a0p,a0n)", "V(a0p) V(a0n)"
    else:
        body = ch1_body(p, False).replace(
            "Vb bin 0 DC 1.2 AC 1", "Vb bin 0 PWL(0 1.15 1u 1.15 1.01u 1.25)")
        obs, sv = "V(a1p,na1)", "V(a1p) V(na1)"
    return (f"* t07 {sid.lower()} os_{ch} — transient overshoot, +100mV step @10ns edge\n"
            f"{HEAD}{body}"
            f".tran 0 30u 0 2n\n{TOPT}"
            f".meas TRAN vfin FIND {obs} AT=29u\n"
            f".meas TRAN vmax MAX {obs} FROM=1.05u TO=30u\n"
            f".meas TRAN vmin MIN {obs} FROM=1.05u TO=30u\n"
            f".save {sv}\n.end\n")


def netlist_jobs():
    """yield (stem, netlist_text, timeout)。共 24(t05)+36(t07 主)+4(t07 二阶分解)=64 只。"""
    for sid, p in SCHEMES.items():
        s = sid.lower()
        for ch in ("ch0", "ch1"):
            for v in ("n1", "n3"):
                yield f"t05_{s}_{ch}_{v}", t05_net(sid, p, ch, v), 300
            yield f"t07_{s}_loop_{ch}", t07_loop_net(sid, p, ch), 600
            yield f"t07_{s}_pk_{ch}", t07_pk_net(sid, p, ch), 600
            yield f"t07_{s}_os_{ch}", t07_os_net(sid, p, ch), 600
        if p["topo"] == 2:                       # 二阶专属：仅首级负载分解（叠加影响隔离）
            yield f"t07_{s}_loopl_ch0", t07_loop_net(sid, p, "ch0", "first1"), 600


def gen_all() -> list[Path]:
    for d in (NET, LOGD, RAWD, CSVD, PLOTD):
        d.mkdir(exist_ok=True)
    written, seen = [], set()
    for stem, txt, _ in netlist_jobs():
        if stem in seen:
            continue
        seen.add(stem)
        f = NET / f"{stem}.net"
        f.write_text(txt)
        written.append(f)
    return written


# ======================================================================
# 2. lint：静态体检 + S0/S1 与上一轮网表同一性对拍（去注释行后逐行一致）
# ======================================================================
KNOWN_SUBCKT = {"opax388"}


def _circuit_lines(txt: str) -> list[str]:
    return [l.rstrip() for l in txt.splitlines()
            if l.strip() and not l.startswith("*")]


IDENT_JOBS = [  # (本轮网表, 上一轮网表)——S0≡FO1_BASE、S1≡FO1_A 电气等同证明
    ("t05_s0_ch0_n1.net", "t05_fo1_base_ch0_n1.net"),
    ("t05_s0_ch0_n3.net", "t05_fo1_base_ch0_n3.net"),
    ("t05_s0_ch1_n1.net", "t05_fo1_base_ch1_n1.net"),
    ("t05_s0_ch1_n3.net", "t05_fo1_base_ch1_n3.net"),
    ("t05_s1_ch0_n1.net", "t05_fo1_a_ch0_n1.net"),
    ("t05_s1_ch0_n3.net", "t05_fo1_a_ch0_n3.net"),
    ("t05_s1_ch1_n1.net", "t05_fo1_a_ch1_n1.net"),
    ("t05_s1_ch1_n3.net", "t05_fo1_a_ch1_n3.net"),
    ("t07_s0_loop_ch0.net", "t07_fo1_base_loop_ch0.net"),
    ("t07_s0_loop_ch1.net", "t07_fo1_base_loop_ch1.net"),
    ("t07_s1_loop_ch0.net", "t07_fo1_a_loop_ch0.net"),
    ("t07_s1_loop_ch1.net", "t07_fo1_a_loop_ch1.net"),
    ("t07_s0_pk_ch0.net", "t07_fo1_base_pk_ch0.net"),
    ("t07_s0_pk_ch1.net", "t07_fo1_base_pk_ch1.net"),
    ("t07_s0_os_ch0.net", "t07_fo1_base_os_ch0.net"),
    ("t07_s0_os_ch1.net", "t07_fo1_base_os_ch1.net"),
]


def lint() -> int:
    bad = 0
    for f in sorted(NET.glob("t05_*.net")) + sorted(NET.glob("t07_*.net")):
        errs = []
        depth = 0
        names = set()
        for ln in f.read_text(errors="replace").splitlines():
            s = ln.split("*", 1)[0].strip()
            if not s:
                continue
            low = s.lower()
            if low.startswith(".include"):
                tgt = s.split(None, 1)[1].strip()
                if not Path(tgt).exists():
                    errs.append(f"include 目标不存在: {tgt}")
            elif low.startswith(".subckt"):
                depth += 1
            elif low.startswith(".ends"):
                depth = max(0, depth - 1)
            elif depth == 0:
                tok = s.split()[0]
                if tok.startswith("X"):
                    if s.split()[-1].lower() not in KNOWN_SUBCKT:
                        errs.append(f"X 实例子电路名未登记: {s.split()[-1]}")
                elif tok[0] in "RCVLBESIHFQTGKOZUDMJ":
                    if tok.lower() in names:
                        errs.append(f"顶层器件名重复: {tok}")
                    names.add(tok.lower())
        if errs:
            print(f"[lint] {f.name}: {errs}")
            bad += len(errs)
    print(f"[lint] 静态体检 {'OK' if not bad else f'{bad} err'}")
    for mine, theirs in IDENT_JOBS:
        a, b = NET / mine, OLD / "netlists" / theirs
        if not a.exists():
            print(f"[ident] FAIL {mine}: 新网表未生成")
            bad += 1
            continue
        if not b.exists():
            print(f"[ident] SKIP {mine} vs {theirs}: 旧产物不在盘（gitignore 再生物）")
            continue
        la, lb = _circuit_lines(a.read_text()), _circuit_lines(b.read_text())
        if la == lb:
            print(f"[ident] OK  {mine} ≡ {theirs}（去注释行后逐行一致，{len(la)} 行）")
        else:
            diff = [f"-{x}/+{y}" for x, y in zip(lb, la) if x != y] or \
                   [f"len {len(lb)} vs {len(la)}"]
            print(f"[ident] FAIL {mine} vs {theirs}: {diff[:4]}")
            bad += 1
    return 1 if bad else 0


# ======================================================================
# 3. 实跑（run_net = aaf_pkg_review/run_all.py：LTspice 产物判定 + rc=1 环境缺陷容忍）
# ======================================================================
def run_all_nets() -> dict[str, str]:
    LOGD.mkdir(exist_ok=True)
    RAWD.mkdir(exist_ok=True)
    status = {}
    for stem, _, timeout in netlist_jobs():
        if stem in status:
            continue
        net = NET / f"{stem}.net"
        t0 = time.time()
        ok, out = run_net(net, timeout=timeout)
        dt = time.time() - t0
        print(f"[run] {stem}: ok={ok} ({dt:.1f}s)" + (f" | {out[:140]}" if not ok else
                                                      (f" | {out[:100]}" if out else "")),
              flush=True)
        log, raw = net.with_suffix(".log"), net.with_suffix(".raw")
        if ok and log.exists() and raw.exists():
            shutil.copy2(log, LOGD / f"{stem}.log")
            shutil.copy2(raw, RAWD / f"{stem}.raw")
        status[stem] = "ok" if ok else f"FAIL: {out[:300]}"
    return status


# ======================================================================
# 4. 解析（noise_metrics/loop_pm/ac_peaking/tran_overshoot = 上一轮同法移植）
# ======================================================================
MEAS_DB_RE = re.compile(
    r"^(\w+):\s+[^=]+?=\((-?[\d.eE+-]+)dB\s*,\s*([-+0-9.eE]+)", re.IGNORECASE)
MEAS_PLAIN_RE = re.compile(
    r"^(\w+):\s+[^=]+?=([+-]?[\d.]+(?:e[+-]?\d+)?)\s*(?:at|FROM|$)", re.IGNORECASE)


def parse_meas_lines(path: Path) -> dict:
    """log 内 .meas 行 → {name: float}。dB 元组取 dB 分量；裸值（TRAN/AT）直取。"""
    out = {}
    if not path.exists():
        return out
    for line in path.read_text(errors="replace").splitlines():
        s = line.strip()
        m = MEAS_DB_RE.match(s)
        if m:
            out[m.group(1)] = float(m.group(2))
            continue
        m = MEAS_PLAIN_RE.match(s)
        if m:
            out[m.group(1)] = float(m.group(2))
    return out


def meas_log_raw(path: Path) -> str:
    """把 .meas 原文逐行带回 CSV（定量值留痕，不二次加工）。"""
    if not path.exists():
        return ""
    return " | ".join(l.strip() for l in path.read_text(errors="replace").splitlines()
                      if re.match(r"^\w+:", l.strip()))[:900]


def _col(raw, name):
    try:
        return np.abs(np.asarray(raw.col(name), dtype=float))
    except KeyError:
        return None


def integrate_band(f, dens, fmax):
    m = f <= fmax
    return float(np.sqrt(np.trapezoid(dens[m] ** 2, f[m])))


def noise_metrics(rawpath: Path):
    """.noise → 带内/宽带积分 + 定点密度 + 逐器件归属（上一轮同法）。"""
    r = parse_r5.Raw(str(rawpath))
    f = r.f
    d = np.abs(np.asarray(r.col("v(onoise)"), dtype=float))
    out = {
        "vn_bb_nV": integrate_band(f, d, FB_BROAD) * 1e9,
        "vn_ib_nV": integrate_band(f, d, FB_INBAND) * 1e9,
        "dens_10Hz_nV": float(np.interp(10, f, d)) * 1e9,
        "dens_1k_nV": float(np.interp(1e3, f, d)) * 1e9,
        "dens_16k_nV": float(np.interp(16e3, f, d)) * 1e9,
        "dens_100k_nV": float(np.interp(100e3, f, d)) * 1e9,
        "dens_1M_nV": float(np.interp(1e6, f, d)) * 1e9,
    }
    # 逐器件归属（.noise 每器件贡献密度列；独立源功率可加）。二阶新增 Ra2/Rb2/Rf2/RKN2。
    passR_names = ("v(ra1)", "v(rb1)", "v(rf)", "v(rkn)",
                   "v(ra2)", "v(rb2)", "v(rf1)", "v(rf2)", "v(rkn1)", "v(rkn2)")
    groups = {"opa_nV": [], "passR_nV": [], "adcRin_nV": []}
    for n in r.names:
        low = n.lower()
        if not low.startswith("v("):
            continue
        if low.startswith("v(xf"):
            groups["opa_nV"].append(n)
        elif low in passR_names:
            groups["passR_nV"].append(n)
        elif low == "v(rin)":
            groups["adcRin_nV"].append(n)
    for key, names in groups.items():
        if not names:
            out[key] = None
            continue
        acc = None
        for n in names:
            c = _col(r, n)
            if c is None:
                continue
            acc = c ** 2 if acc is None else acc + c ** 2
        out[key] = (math.sqrt(float(np.trapezoid(acc[f <= FB_BROAD],
                                                 f[f <= FB_BROAD]))) * 1e9
                    if acc is not None else None)
    tot2 = out["vn_bb_nV"] ** 2
    parts2 = sum((out[k] or 0) ** 2 for k in ("opa_nV", "passR_nV", "adcRin_nV"))
    out["attr_xcheck_pct"] = (abs(tot2 - parts2) / tot2 * 100) if tot2 else float("nan")
    out["_f"], out["_d"] = f, d
    return out


def loop_pm(rawpath: Path):
    """T=−V(fcc)/V(inn)；mag 下穿 1 处 UGF、PM=180+ph（上一轮同法）。"""
    d = parse_r5.Raw(str(rawpath))
    freq = d.f
    T = -np.array(d.col("V(fcc)")) / np.array(d.col("V(inn)"))
    mag, ph = np.abs(T), np.angle(T) * 180 / math.pi
    ugf = pm = None
    for i in range(1, len(freq)):
        if mag[i - 1] > 1 >= mag[i]:
            ugf, pm = float(freq[i]), float(180 + ph[i])
            break
    return ugf, pm, freq, T


def ac_peaking(rawpath: Path, pos: str, neg: str, fo_diff: bool):
    """闭环增益峰（相对 0.1 Hz）@ADC 引脚差分 与 跟随器输出节点（ch0 取 ftp−ftm 差分）。"""
    d = parse_r5.Raw(str(rawpath))
    f = d.f
    pin = np.array(d.col(f"V({pos})")) - np.array(d.col(f"V({neg})"))
    fo = (np.array(d.col("V(ftp)")) - np.array(d.col("V(ftm)"))) if fo_diff \
        else np.array(d.col("V(fbk)"))
    out = {}
    for tag, y in (("pin", pin), ("fo", fo)):
        g = 20 * np.log10(np.abs(y) / np.abs(y[0]))
        k = int(np.argmax(g))
        out[f"peak_{tag}_db"] = float(g[k])
        out[f"peak_{tag}_f_hz"] = float(f[k])
        out[f"gdc_{tag}_db"] = float(20 * math.log10(abs(y[0])))
        out[f"_g_{tag}"] = g
    out["_f"] = f
    return out


def tran_overshoot(rawpath: Path, pos: str, neg: str, step=0.1):
    d = parse_r5.Raw(str(rawpath))
    t = np.array([v.real for v in d.cols[0]], dtype=float)
    y = (np.array(d.col(f"V({pos})"), dtype=float)
         - np.array(d.col(f"V({neg})"), dtype=float))
    m = t >= 1.05e-6
    tt, yy = t[m], y[m]
    vf = float(np.mean(yy[-max(5, len(yy) // 50):]))
    overshoot = (float(yy.max()) - vf) / step * 100
    undershoot = (vf - float(yy.min())) / step * 100
    ring_hz = None
    if overshoot > 0.05:
        pk = []
        for i in range(2, len(yy) - 2):
            if yy[i] > yy[i - 1] and yy[i] > yy[i + 1] and yy[i] > vf + 0.002 * step:
                pk.append(tt[i])
        pk = pk[:6]
        if len(pk) >= 2:
            ring_hz = 1.0 / float(np.mean(np.diff(pk)))
    return {"overshoot_pct": overshoot, "undershoot_pct": undershoot,
            "vfinal_v": vf, "vmax_v": float(yy.max()), "t_peak_s": float(tt[int(np.argmax(yy))]),
            "ring_hz": ring_hz, "_t": tt, "_y": yy}


# ---- 解析层：运放输出负载阻抗（二阶 R1+CG1 / R2+CG2 叠加影响的量化口径）----
def z_load_ch0(p: dict, f: float, first_only: bool = False):
    """[解析] ch0 差分半电路下运放输出节点到地的负载阻抗（无源网络闭式）。
    一阶：Z = R1 + 1/(s(CG1+2Cd) + 1/65k + s·5p)。
    二阶：Z = R1 + 1/(s·CG1 + 1/(R2 + Z2))，Z2 = 1/(s(CG2+2Cd)+1/65k+s·5p)。
    first_only：仅首级 Z = R1 + 1/(s·CG1)（与 loopL 网表同构）。"""
    s = 2j * math.pi * f
    if p["topo"] == 1:
        y2 = s * (p["cg1"] + 2 * p["cd"]) + 1 / 65000.0 + s * 5e-12
        return p["r1"] + 1 / y2
    if first_only:
        return p["r1"] + 1 / (s * p["cg1"])
    y2 = s * (p["cg2"] + 2 * p["cd"]) + 1 / 65000.0 + s * 5e-12
    z2 = 1 / y2
    y1 = s * p["cg1"] + 1 / (p["r2"] + z2)
    return p["r1"] + 1 / y1


def c_eff_pf(p: dict, f: float, first_only: bool = False):
    z = z_load_ch0(p, f, first_only)
    w = 2 * math.pi * f
    im = z.imag
    ceq = (-1 / (w * im) * 1e12) if im < 0 else float("nan")
    return abs(z), ceq


# ======================================================================
# 5. CSV / plots
# ======================================================================
T05_COLS = ["scheme", "topo", "r1_ohm", "cg1_nf", "r2_ohm", "cg2_nf", "cd_pf",
            "channel", "variant", "vn_inband_nVrms", "vn_broadband_nVrms",
            "vn_broadband_lsb", "dens_10Hz_nVrtHz", "dens_1k_nVrtHz",
            "dens_16k_nVrtHz", "dens_100k_nVrtHz", "dens_1M_nVrtHz",
            "d6a_linear_pct", "d6a_quad_pct", "d6a_judge",
            "opa388_share_nVrms", "passR_share_nVrms", "adcRin_share_nVrms",
            "attr_xcheck_pct", "anchor_val", "anchor_diff_pct", "anchor_verdict",
            "method_note"]
T07_COLS = ["scheme", "topo", "r1_ohm", "cg1_nf", "r2_ohm", "cg2_nf", "cd_pf", "test",
            "ugf_hz", "pm_deg", "peak_fo_db", "peak_fo_f_hz", "gdc_fo_db",
            "peak_pin_db", "peak_pin_f_hz", "gdc_pin_db", "c9_max_db", "c9_pass_le6dB",
            "overshoot_pct", "undershoot_pct", "vfinal_v", "vmax_v", "ring_hz",
            "meas_gdc_fo_db", "meas_pk_fo_db", "meas_pk_fo_f_hz",
            "meas_gdc_pin_db", "meas_pk_pin_db", "meas_pk_pin_f_hz",
            "meas_vfin_v", "meas_vmax_v", "meas_vmin_v",
            "anchor_val", "anchor_diff", "anchor_verdict", "meas_note", "method_note"]
DECOMP_COLS = ["scheme", "test", "layer", "pm_deg", "ugf_hz", "zload_ugf_ohm",
               "ceq_ugf_pf", "pm_delta_vs_first1_deg", "note"]


def _base_row(sid: str, p: dict) -> dict:
    return dict(scheme=sid, topo=p["topo"], r1_ohm=p["r1"], cg1_nf=round(p["cg1"] * 1e9, 3),
                r2_ohm=p.get("r2"), cg2_nf=(round(p["cg2"] * 1e9, 3) if p.get("cg2") else None),
                cd_pf=round(p["cd"] * 1e12, 3))


def _anchor_check(val, anchor, kind):
    if val is None or anchor is None:
        return "", "", ""
    if kind == "rel":
        d = (val - anchor) / anchor * 100
        return anchor, round(d, 4), ("yes" if abs(d) <= TOL["noise_rel"] * 100 else "NO-investigate")
    d = val - anchor
    tol = {"pm": TOL["pm"], "c9": TOL["c9"], "os": TOL["os"]}[kind]
    return anchor, round(d, 4), ("yes" if abs(d) <= tol else "NO-investigate")


def parse_all(run_status: dict) -> dict:
    results = {"t05": [], "t07": [], "decomp": [], "dense": {}, "loop": {},
               "pk": {}, "os": {}, "status": run_status}
    for sid, p in SCHEMES.items():
        s = sid.lower()
        base = _base_row(sid, p)
        # ---------------- T05 ----------------
        nm = {}
        for ch in ("ch0", "ch1"):
            for v in ("n1", "n3"):
                stem = f"t05_{s}_{ch}_{v}"
                raw = RAWD / f"{stem}.raw"
                if run_status.get(stem) != "ok" or not raw.exists():
                    results["t05"].append(dict(base, channel=ch, variant=v,
                        method_note=f"NOT VERIFIED: run failed — {run_status.get(stem, 'not run')}"))
                    continue
                nm[(ch, v)] = noise_metrics(raw)
                results["dense"][(s, ch, v)] = {"f": nm[(ch, v)].pop("_f"),
                                                "d": nm[(ch, v)].pop("_d")}
        dens_keys = ("dens_10Hz_nV", "dens_1k_nV", "dens_16k_nV",
                     "dens_100k_nV", "dens_1M_nV")

        def dens_cols(m):
            return {f"{k.replace('_nV', '_nVrtHz')}": round(m[k], 3) for k in dens_keys}

        for ch in ("ch0", "ch1"):
            n1, n3 = nm.get((ch, "n1")), nm.get((ch, "n3"))
            for v, m in (("n1", n1), ("n3", n3)):
                if not m:
                    continue
                anc = ANCH_T05.get((s, ch, v))
                av, ad, averdict = _anchor_check(m["vn_bb_nV"], anc[1] if anc else None, "rel")
                row = dict(base, channel=ch, variant=v,
                           vn_inband_nVrms=round(m["vn_ib_nV"], 2),
                           vn_broadband_nVrms=round(m["vn_bb_nV"], 2),
                           vn_broadband_lsb=round(m["vn_bb_nV"] / (LSB_V * 1e9), 3),
                           **dens_cols(m),
                           opa388_share_nVrms=round(m["opa_nV"], 2) if m["opa_nV"] else None,
                           passR_share_nVrms=round(m["passR_nV"], 2) if m["passR_nV"] else None,
                           adcRin_share_nVrms=round(m["adcRin_nV"], 2) if m["adcRin_nV"] else None,
                           attr_xcheck_pct=round(m["attr_xcheck_pct"], 3),
                           anchor_val=av, anchor_diff_pct=ad, anchor_verdict=averdict,
                           method_note=(f"bb=0.1-{FB_BROAD:.3e}Hz inband=0.1-{FB_INBAND:.0f}Hz "
                                        "trapz; per-device from .noise cols"))
                if v == "n1" and n3:
                    d6a = (n1["vn_bb_nV"] - n3["vn_bb_nV"]) / n3["vn_bb_nV"] * 100
                    d6q = math.sqrt(max(n1["vn_bb_nV"] ** 2 - n3["vn_bb_nV"] ** 2, 0)
                                    ) / n3["vn_bb_nV"] * 100
                    anc_d = ANCH_D6A.get((s, ch))
                    dav, dad, davd = ("", "", "")
                    if anc_d is not None:
                        dd = d6a - anc_d
                        dav = anc_d
                        dad = round(dd, 4)
                        davd = "yes" if abs(dd) <= TOL["d6a_abs"] else "NO-investigate"
                    row.update(d6a_linear_pct=round(d6a, 4), d6a_quad_pct=round(d6q, 4),
                               d6a_judge=("PASS<=10%" if d6a <= D6A_FULL else
                                          "PASS<=30%" if d6a <= D6A_FAIL else "FAIL>30%"),
                               anchor_val=f"{row['anchor_val'] or ''}|d6a:{dav}",
                               anchor_diff_pct=f"{row['anchor_diff_pct'] or ''}|d6a:{dad}",
                               anchor_verdict=f"{row['anchor_verdict'] or ''}|d6a:{davd}",
                               method_note=row["method_note"] +
                                          f"; D6a=(n1-n3)/n3 linear r4口径, n3(bb)="
                                          f"{n3['vn_bb_nV']:.1f}nV; quad口径并列")
                elif v == "n1":
                    row["method_note"] += "; D6a NOT VERIFIED (n3 run failed)"
                if v == "n3":
                    row["method_note"] = "OPA388-only through same ladder (D6a denominator)"
                results["t05"].append(row)
        # ---------------- T07 loop / pk / os ----------------
        for ch in ("ch0", "ch1"):
            stem = f"t07_{s}_loop_{ch}"
            raw = RAWD / f"{stem}.raw"
            if run_status.get(stem) == "ok" and raw.exists():
                ugf, pm, f, T = loop_pm(raw)
                results["loop"][(s, ch)] = {"ugf": ugf, "pm": pm, "f": f, "T": T}
                anc = ANCH_T07.get((sid.lower(), f"loop_{ch}"), {})
                pm_ok = _anchor_check(pm, anc.get("pm"), "pm")
                ugd = ((ugf - anc["ugf"]) / anc["ugf"] * 100) if anc.get("ugf") else ""
                ugv = ("yes" if abs(ugd) <= TOL["ugf_rel"] * 100 else "NO-investigate") if ugd != "" else ""
                results["t07"].append(dict(
                    base, test=f"loop_{ch}", ugf_hz=round(ugf, 1) if ugf else None,
                    pm_deg=round(pm, 2) if pm is not None else None,
                    anchor_val=(f"pm:{pm_ok[0]}" if pm_ok[0] != "" else "") +
                               (f"|ugf:{anc.get('ugf')}" if anc.get("ugf") else ""),
                    anchor_diff=(f"pm:{pm_ok[1]}" if pm_ok[0] != "" else "") + f"|ugf%:{round(ugd, 4) if ugd != '' else ''}",
                    anchor_verdict=(f"pm:{pm_ok[2]}" if pm_ok[0] != "" else "") + f"|ugf:{ugv}",
                    meas_note=meas_log_raw(NET / f"{stem}.log"),
                    method_note="T=-V(fcc)/V(inn); broken at IN+ (AC1), IN- AC-gnd; beta=1; "
                                "PM=180+ph@|T|=1 (t00/gen_fo口径); "
                                + ("1st-order half-circuit" if p["topo"] == 1 else
                                   "2nd-order half-circuit R1-CG1-R2-CG2")))
            else:
                results["t07"].append(dict(base, test=f"loop_{ch}",
                    method_note=f"NOT VERIFIED: {run_status.get(stem, 'not run')}"))
            stem = f"t07_{s}_pk_{ch}"
            raw = RAWD / f"{stem}.raw"
            if run_status.get(stem) == "ok" and raw.exists():
                pos, neg = (("a0p", "a0n") if ch == "ch0" else ("a1p", "na1"))
                pk = ac_peaking(raw, pos, neg, fo_diff=(ch == "ch0"))
                c9 = max(pk["peak_fo_db"], pk["peak_pin_db"])
                meas = parse_meas_lines(NET / f"{stem}.log")
                anc = ANCH_T07.get((sid.lower(), f"pk_{ch}"), {})
                c9_ok = _anchor_check(round(c9, 3), anc.get("c9"), "c9")
                results["pk"][(s, ch)] = {"f": pk.pop("_f"), "g_pin": pk.pop("_g_pin"),
                                          "g_fo": pk.pop("_g_fo"), "pk": pk}
                results["t07"].append(dict(
                    base, test=f"pk_{ch}",
                    peak_fo_db=round(pk["peak_fo_db"], 3), peak_fo_f_hz=round(pk["peak_fo_f_hz"]),
                    gdc_fo_db=round(pk["gdc_fo_db"], 3),
                    peak_pin_db=round(pk["peak_pin_db"], 3), peak_pin_f_hz=round(pk["peak_pin_f_hz"]),
                    gdc_pin_db=round(pk["gdc_pin_db"], 3),
                    c9_max_db=round(c9, 3), c9_pass_le6dB=("yes" if c9 <= C9_TH else "NO"),
                    meas_gdc_fo_db=meas.get("gdc_fo"), meas_pk_fo_db=meas.get("pk_fo"),
                    meas_pk_fo_f_hz=meas.get("pk_fo_f"), meas_gdc_pin_db=meas.get("g_dc"),
                    meas_pk_pin_db=meas.get("pk_pin"), meas_pk_pin_f_hz=meas.get("pk_pin_f"),
                    anchor_val=f"c9:{c9_ok[0]}" if c9_ok[0] != "" else "",
                    anchor_diff=f"c9:{c9_ok[1]}" if c9_ok[0] != "" else "",
                    anchor_verdict=f"c9:{c9_ok[2]}" if c9_ok[0] != "" else "",
                    meas_note=meas_log_raw(NET / f"{stem}.log"),
                    method_note="C9 primary=follower-out node (r4口径), secondary=ADC pin; "
                                "rel. DC(0.1Hz); meas_* 列=LTspice .meas 原值"))
            else:
                results["t07"].append(dict(base, test=f"pk_{ch}",
                    method_note=f"NOT VERIFIED: {run_status.get(stem, 'not run')}"))
            stem = f"t07_{s}_os_{ch}"
            raw = RAWD / f"{stem}.raw"
            if run_status.get(stem) == "ok" and raw.exists():
                pos, neg = (("a0p", "a0n") if ch == "ch0" else ("a1p", "na1"))
                o = tran_overshoot(raw, pos, neg)
                meas = parse_meas_lines(NET / f"{stem}.log")
                anc = ANCH_T07.get((sid.lower(), f"os_{ch}"), {})
                os_ok = _anchor_check(round(o["overshoot_pct"], 4), anc.get("os"), "os")
                results["os"][(s, ch)] = o
                results["t07"].append(dict(
                    base, test=f"os_{ch}",
                    overshoot_pct=round(o["overshoot_pct"], 4),
                    undershoot_pct=round(o["undershoot_pct"], 4),
                    vfinal_v=round(o["vfinal_v"], 6), vmax_v=round(o["vmax_v"], 6),
                    ring_hz=round(o["ring_hz"], 1) if o["ring_hz"] else None,
                    meas_vfin_v=meas.get("vfin"), meas_vmax_v=meas.get("vmax"),
                    meas_vmin_v=meas.get("vmin"),
                    anchor_val=f"os:{os_ok[0]}" if os_ok[0] != "" else "",
                    anchor_diff=f"os:{os_ok[1]}" if os_ok[0] != "" else "",
                    anchor_verdict=f"os:{os_ok[2]}" if os_ok[0] != "" else "",
                    meas_note=meas_log_raw(NET / f"{stem}.log"),
                    method_note="+100mV step @10ns edge; overshoot rel. final, "
                                "differential ADC-pin voltage; meas_* 列=.meas 原值"))
            else:
                results["t07"].append(dict(base, test=f"os_{ch}",
                    method_note=f"NOT VERIFIED: {run_status.get(stem, 'not run')}"))
        # ---------------- T07 二阶叠加影响分解（loopL 仅首级 + 解析 Z_load）----------------
        if p["topo"] == 2:
            stem = f"t07_{s}_loopl_ch0"
            raw = RAWD / f"{stem}.raw"
            pm1 = ugf1 = None
            if run_status.get(stem) == "ok" and raw.exists():
                ugf1, pm1, _, _ = loop_pm(raw)
                results["loop"][(s, "ch0_1st")] = {"ugf": ugf1, "pm": pm1}
                results["decomp"].append(dict(
                    scheme=sid, test="loopl_ch0(first-stage-only)", layer="LTspice",
                    pm_deg=round(pm1, 2) if pm1 is not None else None,
                    ugf_hz=round(ugf1, 1) if ugf1 else None,
                    note="仅首级负载 R1+CG1（无后级）——隔离后级 R2+CG2 叠加影响"))
            else:
                results["decomp"].append(dict(
                    scheme=sid, test="loopl_ch0(first-stage-only)", layer="LTspice",
                    note=f"NOT VERIFIED: {run_status.get(stem, 'not run')}"))
            full = results["loop"].get((s, "ch0"))
            if full and full.get("pm") is not None and pm1 is not None:
                results["decomp"].append(dict(
                    scheme=sid, test="stacking_delta(full−first1)", layer="LTspice",
                    pm_deg=round(full["pm"], 2), ugf_hz=round(full["ugf"], 1),
                    pm_delta_vs_first1_deg=round(full["pm"] - pm1, 2),
                    note=f"全梯形 PM−仅首级 PM = {full['pm'] - pm1:+.2f}°（后级 R2+CG2 叠加代价）"))
            # 解析层：运放输出负载阻抗/等效电容 @UGF（闭式，非 LTspice）
            if full and full.get("ugf"):
                z_full, c_full = c_eff_pf(p, full["ugf"])
                z_1, c_1 = c_eff_pf(p, full["ugf"], first_only=True)
                results["decomp"].append(dict(
                    scheme=sid, test="zload@UGF(full)", layer="解析",
                    zload_ugf_ohm=round(z_full, 1), ceq_ugf_pf=round(c_full, 2),
                    ugf_hz=round(full["ugf"], 1),
                    note=f"[解析]Z=R1+1/(sCG1+1/(R2+Z2))，Z2=(CG2+2Cd)||65k||5p @UGF="
                         f"{full['ugf']:.0f}Hz；C_eq=−1/(ω·ImZ)"))
                results["decomp"].append(dict(
                    scheme=sid, test="zload@UGF(first1)", layer="解析",
                    zload_ugf_ohm=round(z_1, 1), ceq_ugf_pf=round(c_1, 2),
                    ugf_hz=round(full["ugf"], 1),
                    note=f"[解析]Z=R1+1/(sCG1) 同频点；对照 full 行见后级叠加使 |Z|↓/C_eq↑"))
        else:
            full = results["loop"].get((s, "ch0"))
            if full and full.get("ugf"):
                z_full, c_full = c_eff_pf(p, full["ugf"])
                results["decomp"].append(dict(
                    scheme=sid, test="zload@UGF(1st-order)", layer="解析",
                    zload_ugf_ohm=round(z_full, 1), ceq_ugf_pf=round(c_full, 2),
                    ugf_hz=round(full["ugf"], 1),
                    note="[解析]一阶 Z=R1+1/(s(CG1+2Cd)+1/65k+s·5p) @UGF（对照二阶行）"))
    return results


def write_csvs(res: dict) -> list[Path]:
    CSVD.mkdir(exist_ok=True)
    f1 = CSVD / "t05_noise.csv"
    with f1.open("w", newline="\n", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=T05_COLS)
        w.writeheader()
        for r in res["t05"]:
            w.writerow(r)
        for k, v in t05_notes().items():
            w.writerow(dict(scheme=f"note_{k}", method_note=v))
    f2 = CSVD / "t07_stability.csv"
    with f2.open("w", newline="\n", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=T07_COLS)
        w.writeheader()
        for r in res["t07"]:
            w.writerow(r)
        for k, v in t07_notes().items():
            w.writerow(dict(scheme=f"note_{k}", method_note=v))
    f3 = CSVD / "t07_load_decomp.csv"
    with f3.open("w", newline="\n", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=DECOMP_COLS)
        w.writeheader()
        for r in res["decomp"]:
            w.writerow(r)
    return [f1, f2, f3]


def t05_notes() -> dict:
    return {
        "1_scope": "T05 范围=AAF 段（跟随器+RC 梯形+ADC 引脚负载 Rin130k+5p/端，采样开关断态，"
                   "跟随器输入由理想无噪直流源驱动）；前端源阻抗噪声（Rsense 150k Johnson、"
                   "Rtop 分压、TMUX 通路）为六方案共同项不在本段（fo1 t05 note_1 同款），解析估算"
                   "≈16 µVrms 量级主导通道噪声但六方案相同",
        "2_adc_noise": "ADC 内部噪声（kT/C_S、量化、基准、sinc³ 成形）不在 .noise——沿用 fo1 "
                       "REPORT §7.3：系统口径须查 SBAS590E p23 Table 1（手册在 Obsidian 库不在"
                       "本仓库）→ ADC 内部噪声数值对比 NOT VERIFIED；解析补充 kT/C_S="
                       "√(kT/3.5pF)=34.4 µV/次采样",
        "3_d6a_dual": "D6a 双口径：判罚按 r4 冻结线性口径 (n1−n3)/n3；正交口径 √(n1²−n3²)/n3 并列"
                      "（物理功率叠加）。阈值 ≤10% 满分 / >30% 淘汰，未放宽",
        "4_wiring": "真实接线落实：CH0=T/M 两线各 1 颗 OPA388（真实接线本就对称）；CH1=B 线单 "
                    "OPA388 + AIN1N 经 Kelvin 无源梯形直连地（无第四颗运放，DC=0V）。二阶 Kelvin "
                    "N 线同梯形 RKN1/CGN1/RKN2/CGN2（与 run_all.py fullchain_net 同构）",
        "5_attr": "逐器件归属=LTspice .noise 每器件贡献列（OPA388=v(xf*)，passR=Ra1/Ra2/Rb1/Rb2/"
                  "Rf/Rf1/Rf2/RKN/RKN1/RKN2，adcRin=Rin）；attr_xcheck_pct=|Σ器件²−onoise²|/onoise²"
                  "×100%（0=功率和精确成立）",
        "6_anchor": "S0/S1 锚值=fo1_rc_review/csv/t05_noise.csv（S0≡FO1_BASE、S1≡FO1_A 电气等同，"
                    "同一性由 lint 对拍证明）；容差 bb ±0.3%、D6a ±0.03 pct-point",
    }


def t07_notes() -> dict:
    return {
        "1_break_method": "断环方式声明（任务书 T07）：输入参考断环——AC 1V 注入跟随器同相输入端"
                          "（Vinn），反相端接 DC 偏置源（AC 地）；β=1 电压跟随器环路在输入处断开，"
                          "T(f)=−V(fcc)/V(inn)=Aol(带真实负载)；PM=180+ph@|T|=1（t00/gen_fo 同口径，"
                          "S0 ch0 锚 98.57°/2786 kHz 上一轮 t07_stability.csv）",
        "2_loads": "负载：loop_ch0=差分半电路（Cd×2 虚地 + Rin/2=65k + 5p；二阶为 R1-CG1-R2-CG2 "
                   "全梯形半电路）；loop_ch1=真实非对称全负载（B 线梯形 + AIN1N Kelvin 无源梯形，"
                   "无第四颗运放→na1 侧无环路，AIN1N 不当作运放）；loopl_ch0=二阶仅首级（R1+CG1）"
                   "分解诊断，隔离后级叠加影响",
        "3_pm_temp": "PM@温度沿用上一轮宏模型限制结论（fo1 REPORT §7.2）：OPAx388 宏模型断环 AC "
                     "线性化仅在 .temp 25–27 ℃ 窗口正确（30 ℃ 起直流环路增益塌 1000×，宏模型缺陷"
                     "二分实证），温度趋势 NOT VERIFIED，本轮只交 25 ℃（默认温度），不重推",
        "4_c9_anchor": "C9 主口径=跟随器输出节点全频闭环峰值（r4 §4.2）≤6 dB；ADC 引脚节点副口径。"
                       "S0/S1 锚=上一轮 t07_stability.csv（0.691/0.694、0.330/0.333 dB）",
        "5_os": "瞬态过冲=+100 mV 阶跃（10 ns 沿）闭环差分 ADC 引脚电压响应，相对各自终值（os_ch1 "
                "vfin≈1.248 V≠1.25 V 系 R/130k 直流分压物理，非误差——上一轮 note_4 同款）",
        "6_env": "环境：LTspice 26.1.1 + wine-11.0（ltspice-sim status ready）；OPAx388.LIB md5 "
                 "97c4045ef608097ec1f1a67dca97ceae（与 fo1_rc_review 同源，本轮 md5sum 复核）。"
                 "ltspice-sim 对复数 AC raw 后处理崩溃 rc=1 为已知环境缺陷（仿真本体完成，以 "
                 "LTspice .log/.raw 产物判定成功，fo1 README「环境已知缺陷」同款）",
    }


def make_plots(res: dict) -> list[Path]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt            # noqa: PLC0415
    PLOTD.mkdir(exist_ok=True)
    out = []
    # ---- 每方案噪声谱 ----
    for sid, p in SCHEMES.items():
        s = sid.lower()
        fig, ax = plt.subplots(figsize=(8, 5))
        for (ch, v), lab in ((("ch0", "n1"), "CH0 total (T/M followers, noisy)"),
                             (("ch1", "n1"), "CH1 total (B follower + Kelvin, noisy)"),
                             (("ch1", "n3"), "CH1 OPA388-only (R noiseless)")):
            m = res["dense"].get((s, ch, v))
            if m:
                ax.loglog(m["f"], m["d"] * 1e9, label=lab, lw=1.2)
        ax.axvline(FB_INBAND, ls=":", c="gray")
        ax.axvline(FB_BROAD, ls=":", c="gray")
        ax.set_xlabel("Frequency [Hz]")
        ax.set_ylabel("Differential output noise [nV/rtHz]")
        topo = "1st-order" if p["topo"] == 1 else \
            f"2nd-order R1={fmt(p['r1'])}/CG1={fmt(p['cg1']*1e9)}nF R2={fmt(p['r2'])}/CG2={fmt(p['cg2']*1e9)}nF"
        ax.set_title(f"T05 noise density — {sid} ({topo}, CD={fmt(p['cd']*1e12)}pF)")
        ax.legend(fontsize=8)
        ax.grid(True, which="both", alpha=0.3)
        fig.tight_layout()
        f = PLOTD / f"t05_{s}_noise_density.png"
        fig.savefig(f, dpi=130)
        plt.close(fig)
        out.append(f)
    # ---- 六方案 CH0 总噪声对比 ----
    fig, ax = plt.subplots(figsize=(9, 5.5))
    for sid in SCHEMES:
        m = res["dense"].get((sid.lower(), "ch0", "n1"))
        if m:
            ax.loglog(m["f"], m["d"] * 1e9, label=f"{sid} CH0 total", lw=1.2)
    ax.axvline(FB_INBAND, ls=":", c="gray")
    ax.axvline(FB_BROAD, ls=":", c="gray")
    ax.set_xlabel("Frequency [Hz]")
    ax.set_ylabel("Differential output noise [nV/rtHz]")
    ax.set_title("T05 CH0 noise density — six schemes (TI OPAx388 macromodel, all-R noisy)")
    ax.legend(fontsize=8)
    ax.grid(True, which="both", alpha=0.3)
    fig.tight_layout()
    f = PLOTD / "t05_all_schemes_ch0_noise.png"
    fig.savefig(f, dpi=130)
    plt.close(fig)
    out.append(f)
    # ---- 每方案环路增益 + 二阶分解叠加 ----
    for sid, p in SCHEMES.items():
        s = sid.lower()
        fig, (a1, a2) = plt.subplots(2, 1, figsize=(8, 6.5), sharex=True)
        for ch, c in (("ch0", "tab:blue"), ("ch1", "tab:orange")):
            m = res["loop"].get((s, ch))
            if not m:
                continue
            f, T = m["f"], m["T"]
            a1.semilogx(f, 20 * np.log10(np.abs(T)), c=c,
                        label=f"{ch} (PM={m['pm']:.1f}°, UGF={m['ugf']/1e3:.0f}kHz)")
            a2.semilogx(f, np.angle(T) * 180 / np.pi, c=c)
            if m["pm"] is not None:
                a1.axvline(m["ugf"], ls=":", c=c, alpha=0.6)
        m1 = res["loop"].get((s, "ch0_1st"))
        if m1:
            a1.axvline(m1["ugf"], ls="--", c="green", alpha=0.7)
            a1.text(m1["ugf"], 20, f" 1st-stage-only UGF={m1['ugf']/1e3:.0f}kHz\n PM={m1['pm']:.1f}°",
                    fontsize=7, color="green")
        a1.axhline(0, c="k", lw=0.6)
        a1.set_ylabel("|T| [dB]")
        a1.legend(fontsize=8)
        a1.grid(True, which="both", alpha=0.3)
        a2.set_ylabel("phase(T) [deg]")
        a2.set_xlabel("Frequency [Hz]")
        a2.grid(True, which="both", alpha=0.3)
        fig.suptitle(f"T07 loop gain (broken at IN+, beta=1) — {sid}")
        fig.tight_layout()
        f = PLOTD / f"t07_{s}_loopgain.png"
        fig.savefig(f, dpi=130)
        plt.close(fig)
        out.append(f)
        # ---- peaking + 过冲 ----
        fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.2))
        for ch in ("ch0", "ch1"):
            m = res["pk"].get((s, ch))
            if m:
                a1.semilogx(m["f"], m["g_pin"], label=f"{ch} ADC pin")
                a1.semilogx(m["f"], m["g_fo"], label=f"{ch} follower out", ls="--")
        a1.axhline(C9_TH, c="r", ls=":", lw=1)
        a1.set_xscale("log")
        a1.set_xlabel("Frequency [Hz]")
        a1.set_ylabel("Closed-loop gain rel. DC [dB]")
        a1.set_title("C9 peaking (red = 6dB line)")
        a1.legend(fontsize=7)
        a1.grid(True, which="both", alpha=0.3)
        for ch in ("ch0", "ch1"):
            m = res["os"].get((s, ch))
            if m:
                tt = (m["_t"] - 1.01e-6) * 1e6
                yy = (m["_y"] - m["vfinal_v"] + 0.1) / 0.1
                a2.plot(tt, yy, label=f"{ch} (os={m['overshoot_pct']:.2f}%)")
        a2.axhline(1.0, c="k", lw=0.6)
        a2.set_xlim(0, 3)
        a2.set_xlabel("time after step edge [µs]")
        a2.set_ylabel("step response [norm]")
        a2.set_title("Transient overshoot (+100mV @10ns)")
        a2.legend(fontsize=7)
        a2.grid(True, alpha=0.3)
        fig.suptitle(f"T07 peaking & overshoot — {sid}")
        fig.tight_layout()
        f = PLOTD / f"t07_{s}_pk_os.png"
        fig.savefig(f, dpi=130)
        plt.close(fig)
        out.append(f)
    # ---- PM/UGF 六方案汇总 ----
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.2))
    xs = list(SCHEMES)
    for ch, mk in (("ch0", "o"), ("ch1", "s")):
        pms = [res["loop"].get((s.lower(), ch), {}).get("pm") for s in xs]
        ugs = [res["loop"].get((s.lower(), ch), {}).get("ugf") for s in xs]
        a1.plot(xs, pms, mk + "-", label=f"loop_{ch}")
        a2.plot(xs, [u / 1e6 if u else None for u in ugs], mk + "-", label=f"loop_{ch}")
    p1 = [res["loop"].get((s.lower(), "ch0_1st"), {}).get("pm") for s in xs]
    a1.plot(xs, p1, "^--", c="green", label="loop_ch0 1st-stage-only (T1–T4)")
    a1.axhline(45, c="r", ls=":", lw=1)
    a1.text(0.1, 46, "45° eng. ref", fontsize=7, color="r")
    a1.set_ylabel("PM [deg]")
    a1.legend(fontsize=8)
    a1.grid(True, alpha=0.3)
    a2.set_ylabel("UGF [MHz]")
    a2.legend(fontsize=8)
    a2.grid(True, alpha=0.3)
    fig.suptitle("T07 summary: PM / UGF across six schemes (25°C)")
    fig.tight_layout()
    f = PLOTD / "t07_pm_ugf_summary.png"
    fig.savefig(f, dpi=130)
    plt.close(fig)
    out.append(f)
    return out


# ======================================================================
def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("cmd", nargs="?", default="all", choices=["gen", "lint", "run", "parse", "all"])
    args = ap.parse_args(argv)
    if args.cmd in ("gen", "run", "all"):
        for f in gen_all():
            print(f"[gen] {f.name}")
    if args.cmd == "lint":
        return lint()
    status = {}
    if args.cmd in ("run", "all"):
        status = run_all_nets()
    if args.cmd == "parse":
        for stem, _, _ in netlist_jobs():          # 由产物存在性重建 run 状态（幂等）
            if stem in status:
                continue
            log, raw = NET / f"{stem}.log", NET / f"{stem}.raw"
            ok = (log.exists() and raw.exists()
                  and "Total elapsed time" in log.read_text(errors="replace")
                  and raw.stat().st_mtime > log.stat().st_mtime - 5)
            status[stem] = "ok" if ok else "missing/failed"
    if args.cmd in ("parse", "all", "run"):
        res = parse_all(status)
        for c in write_csvs(res):
            print(f"[csv] {c}")
        for pp in make_plots(res):
            print(f"[plot] {pp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
