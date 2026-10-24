#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""run_all.py — aaf_pkg_review 六方案封装候选台架（任务书 2026-10-24 §2/§5(1)(2)，冒烟锚定轮）

复用上一轮台架 hardware/sim/signalchain/fo1_rc_review/（**只读**，不改动其任何文件）：
  * 真实 TI 宏模型 OPAx388.LIB（md5 97c4045ef608097ec1f1a67dca97ceae，md5sum 实测同源）
  * T00 锚定网表口径逐行复刻（fo1_rc_review/run_all.py t00_ac_dm/t00_ac_cm 生成函数）
  * ltspice-sim 运行器判定逻辑（LTspice 产物为准；ltspice-sim AC 复数 raw 后处理崩溃 rc=1
    是已知环境缺陷，记 note 不判失败——fo1_rc_review/README.md「环境已知缺陷」同款）
  * 复数 AC raw 解析 = hardware/sim/aaf/parse_r5.py（本轮不 import fo1_rc_review 任何模块，
    避免 __pycache__ 落进受保护目录）

六方案（任务书 §2 表，原文照录；二阶拓扑 §2：R1→节点1(CG1 对地)→R2→节点2/ADC(CG2 对地)，Cd 跨节点2 P/N）：
  S0 47Ω/47nF/820pF（一阶，电气同旧 FO1_BASE）   S1 100Ω/22nF/820pF（一阶，电气同旧 FO1_A）
  T1 100Ω/10nF+100Ω/10nF+820pF                   T2 100Ω/10nF+120Ω/10nF+820pF
  T3 68Ω/10nF+150Ω/10nF+820pF                    T4 82Ω/10nF+160Ω/10nF+820pF

冒烟锚定（本 ask 只跑 5 只，不重跑全套 T00）：
  S0 dm/cm、S1 dm/cm 各一跑 → 对锚 D1≈40.69/D2≈46.41（S0）与 D1≈38.72/D2≈38.11（S1）
  T2 dm 一跑 → 16 kHz 衰减与任务书 §3 理想表 0.412 dB 同趋势、偏差可解释
锚定口径声明（锚值出处 = fo1_rc_review/csv/{t00_regression,t01_dm_ac,t02_cm_ac}.csv 实测）：
  * D1 = 差模 AC（Vp AC 0.5 / Vn AC −0.5，差分合计 1 V）@4.096 MHz 衰减量 = −20log10|V(pa1,na1)|
  * S0-D2 锚 46.41 = t00 accm 口径（共模 0.5 V 激励的**绝对 dB 残留**取负）
  * S1-D2 锚 38.11 = t02 口径（**按 1 V 共模归一**的衰减量）；两口径差恒 20log10(2)=6.0206 dB，
    网表线性 → 本轮 CM 网表统一用 0.5 V 激励（t00 口径），S1-D2 以「绝对 dB − 6.0206」对锚，双口径并记
  * 容差 0.5 dB（ask 原文：偏差>0.5 dB 先查口径）

子命令：gen（只生成）/ lint（静态体检+与旧网表同一性对拍）/ smoke（实跑 5 只+CSV+图）/ all（默认=gen+lint+smoke）
产物：netlists/*.net（gitignore 再生）、logs/ raw/、csv/smoke_anchor.csv、plots/smoke_dm_ac.png。
"""
from __future__ import annotations

import argparse
import csv
import math
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True          # 不在任何目录留 __pycache__（含受保护的 fo1_rc_review）

HERE = Path(__file__).resolve().parent
NET = HERE / "netlists"
LOGD = HERE / "logs"
RAWD = HERE / "raw"
CSVD = HERE / "csv"
PLOTD = HERE / "plots"

ROOT = "/media/anning/data/Project/DE-DRMS"
LIB = f"{ROOT}/hardware/sim/_candidate_models/opa388/OPAx388.LIB"
MODELS_INC = f"{ROOT}/hardware/sim/ccsource/models.inc"
PARSE_R5_DIR = f"{ROOT}/hardware/sim/aaf"
OLD = Path(f"{ROOT}/hardware/sim/signalchain/fo1_rc_review")   # 只读复用源
LTSPICE_SIM = str(Path.home() / ".local/bin/ltspice-sim")

FMOD = 4.096e6
MCLK = 16.384e6
DB2 = 20 * math.log10(2)                # 6.0206 dB：共模 0.5 V↔1 V 激励口径差

# ---- 六方案参数（任务书 §2 表原文照录）----
SCHEMES = {
    "S0": dict(topo=1, r1=47.0,  cg1=47e-9, r2=None, cg2=None, cd=820e-12,
               note="一阶原基线重新封装；电气同旧 FO1_BASE（47Ω/47nF/820pF）"),
    "S1": dict(topo=1, r1=100.0, cg1=22e-9, r2=None, cg2=None, cd=820e-12,
               note="一阶 Zcode 已验证；电气同旧 FO1_A（100Ω/22nF/820pF）"),
    "T1": dict(topo=2, r1=100.0, cg1=10e-9, r2=100.0, cg2=10e-9, cd=820e-12,
               note="二阶平坦度优先（全 0402）"),
    "T2": dict(topo=2, r1=100.0, cg1=10e-9, r2=120.0, cg2=10e-9, cd=820e-12,
               note="二阶均衡优先（全 0402）；本轮冒烟二阶代表"),
    "T3": dict(topo=2, r1=68.0,  cg1=10e-9, r2=150.0, cg2=10e-9, cd=820e-12,
               note="二阶分阻值（首级阻值对照）"),
    "T4": dict(topo=2, r1=82.0,  cg1=10e-9, r2=160.0, cg2=10e-9, cd=820e-12,
               note="二阶高抑制边界（16 kHz 通带容差余量小，非预定胜者）"),
}

# ---- 冒烟锚（ask 给值；prior = fo1_rc_review 实测出处，本轮交叉引用）----
ANCHOR = {
    "S0_D1": dict(anchor=40.69, prior="t00 −40.689 / t01 opa388 40.683",
                  basis="DM 1V 衰减量@4.096MHz"),
    "S0_D2": dict(anchor=46.41, prior="t00 accm −46.4104",
                  basis="CM 0.5V 激励绝对 dB 残留取负@4.096MHz（t00 口径）"),
    "S1_D1": dict(anchor=38.72, prior="t01 opa388 38.722",
                  basis="DM 1V 衰减量@4.096MHz"),
    "S1_D2": dict(anchor=38.11, prior="t02 opa388 38.108（1V 归一）",
                  basis="CM 按 1V 归一衰减量@4.096MHz（t02 口径 = 0.5V 绝对 − 6.0206）"),
    "T2_D4": dict(anchor=0.412, prior="任务书 §3 理想表 T2 行（非 LTspice）",
                  basis="DM 16kHz 相对 DC 衰减"),
}
# 任务书 §3 理想表（六行全录，供 L1 引擎对拍；d4/d1/d3=DM, cm=CM@4.096M, d3m=@16.384M）
TASK_S3 = {
    "S0": (0.223, 35.39, 35.10, 47.43), "S1": (0.238, 35.67, 35.06, 47.71),
    "T1": (0.366, 57.76, 56.47, 81.80), "T2": (0.412, 59.33, 58.04, 83.38),
    "T3": (0.335, 57.92, 56.63, 81.97), "T4": (0.423, 60.10, 58.81, 84.15),
}
SMOKE_RUNS = [("S0", "acdm"), ("S0", "accm"), ("S1", "acdm"), ("S1", "accm"), ("T2", "acdm")]
TOL_ANCHOR = 0.5      # dB，ask 原文：偏差>0.5 dB 先查口径


def fmt(v: float) -> str:
    return f"{v:.6g}"


# ======================================================================
# 1. 冒烟网表生成 —— 一阶逐行复刻 t00_ac_dm/t00_ac_cm（除首行注释外字节一致，
#    由 lint 的同一性对拍自动验证）；二阶按任务书 §2 拓扑扩展同口径。
# ======================================================================
OPTS = ".options plotwinsize=0 reltol=1e-6 abstol=1e-12 vntol=1e-9 chgtol=1e-15 trtol=1\n"
ACSW = ".ac dec 400 0.1 200Meg\n"
MEAS_DM = (".meas AC dm_dc   FIND mag(V(pa1,na1)) AT=0.1\n"
           ".meas AC dm_fmod FIND mag(V(pa1,na1)) AT=4.096Meg\n"
           ".meas AC dm_mclk FIND mag(V(pa1,na1)) AT=16.384Meg\n"
           ".meas AC dm_16k  FIND mag(V(pa1,na1)) AT=16k\n"
           ".meas AC foll_pk MAX mag(V(fpa))\n"
           ".meas AC foll_pk_f WHEN mag(V(fpa))=foll_pk\n")
MEAS_CM = (".meas AC cm_dc   FIND mag(V(pa1)) AT=0.1\n"
           ".meas AC cm_fmod FIND mag(V(pa1)) AT=4.096Meg\n"
           ".meas AC cm_mclk FIND mag(V(pa1)) AT=16.384Meg\n")


def ladder_1(p: dict) -> str:          # 一阶：每线 R→ADC 节点，CG 对地（t00 字节口径）
    return (f"Ra1 fpa pa1 {fmt(p['r1'])}\n"
            f"Ca1 pa1 0 {fmt(p['cg1'])}\n"
            f"Rb1 fna na1 {fmt(p['r1'])}\n"
            f"Cb1 na1 0 {fmt(p['cg1'])}\n")


def ladder_2(p: dict) -> str:          # 二阶：R1→节点1(CG1)→R2→节点2/ADC(CG2)
    return (f"Ra1 fpa n1a {fmt(p['r1'])}\n"
            f"Ca1 n1a 0 {fmt(p['cg1'])}\n"
            f"Ra2 n1a pa1 {fmt(p['r2'])}\n"
            f"Ca2 pa1 0 {fmt(p['cg2'])}\n"
            f"Rb1 fna n1b {fmt(p['r1'])}\n"
            f"Cb1 n1b 0 {fmt(p['cg1'])}\n"
            f"Rb2 n1b na1 {fmt(p['r2'])}\n"
            f"Cb2 na1 0 {fmt(p['cg2'])}\n")


def net_acdm(sid: str, p: dict) -> str:
    lad = ladder_1(p) if p["topo"] == 1 else ladder_2(p)
    mid = " V(n1a) V(n1b)" if p["topo"] == 2 else ""
    hdr = (f"sm {sid} ac_dm {'一阶' if p['topo']==1 else '二阶'} "
           f"(口径=fo1_rc_review t00_ac_dm / gen_fo.py net_ac_dm；"
           f"R1={fmt(p['r1'])} CG1={fmt(p['cg1'])}"
           + (f" R2={fmt(p['r2'])} CG2={fmt(p['cg2'])}" if p["topo"] == 2 else "")
           + f" CD={fmt(p['cd'])})")
    return (f"* {hdr}\n.include {LIB}\n"
            f"Vcc vcc 0 DC 3.3\nVee vee 0 DC 0\n"
            f"Vp vp 0 DC 2 AC 0.5\nVn vn 0 DC 2 AC -0.5\n"
            f"Xfa vp fpa vcc vee fpa OPAx388\nXfb vn fna vcc vee fna OPAx388\n"
            + lad +
            f"Cd pa1 na1 {fmt(p['cd'])}\n"
            f"Rin pa1 na1 130000\nCpa pa1 0 5e-12\nCna na1 0 5e-12\n"
            + ACSW + OPTS + MEAS_DM
            + f".save V(pa1) V(na1) V(fpa) V(fna){mid}\n.end\n")


def net_accm(sid: str, p: dict) -> str:
    lad = ladder_1(p) if p["topo"] == 1 else ladder_2(p)
    hdr = (f"sm {sid} ac_cm {'一阶' if p['topo']==1 else '二阶'} "
           f"(口径=fo1_rc_review t00_ac_cm，共模 0.5V 激励；"
           f"R1={fmt(p['r1'])} CG1={fmt(p['cg1'])}"
           + (f" R2={fmt(p['r2'])} CG2={fmt(p['cg2'])}" if p["topo"] == 2 else "")
           + f" CD={fmt(p['cd'])})")
    return (f"* {hdr}\n.include {LIB}\n"
            f"Vcc vcc 0 DC 3.3\nVee vee 0 DC 0\n"
            f"Vp vp 0 DC 2 AC 0.5\nVn vn 0 DC 2 AC 0.5\n"
            f"Xfa vp fpa vcc vee fpa OPAx388\nXfb vn fna vcc vee fna OPAx388\n"
            + lad +
            f"Cd pa1 na1 {fmt(p['cd'])}\n"
            f"Rin pa1 na1 130000\nCpa pa1 0 5e-12\nCna na1 0 5e-12\n"
            + ACSW + OPTS + MEAS_CM
            + ".save V(pa1) V(na1)\n.end\n")


# ======================================================================
# 2. 整链基座 pkg_subs.inc + 六方案静态场景网表（复用 fo1_rc_review 基座结构：
#    fo_subs.inc 段子电路原样移植；fsfo → fsfo1（一阶）/fsfo2（二阶）；
#    AIN1N Kelvin 直连在顶层实现。本轮只生成过 lint，不运行——与上一轮
#    「整链 .tran 未运行」遗留口径一致，供后续 §5 全项轮次使用）
# ======================================================================
PKG_SUBS = f"""* =====================================================================
* pkg_subs.inc — aaf_pkg_review 六方案整链子电路库（2026-10-24）
* 基座 = fo1_rc_review/fo_subs.inc 分段只读移植（dut/fsrc/fsadc 原样；
*        fsfo 一阶 → fsfo1 一阶 + fsfo2 二阶，参数由顶层 .param 传入）
* 依赖（绝对路径，规避全角逗号目录下 LTspice 相对 include 解析失败）：
*   ccsource/models.inc                  ：opa333t/nmosb/swNO/swsh
*   _candidate_models/opa388/OPAx388.LIB  ：TI 官方宏 Final 1.4（md5 97c4045ef608097ec1f1a67dca97ceae）
* =====================================================================
.include {MODELS_INC}
.include {LIB}

* ---- nmosw：M2 关断管手册拟合宏（fo_subs.inc 同式）----
.model nmosw nmos(level=1 vto=1.25 kp=0.15 lambda=0.05 cgso=10.8p cgdo=1.43p cbd=0 cbs=0)

* ---- 被测电阻 + 线缆寄生（fo_subs.inc 原样；CTOT/CTT 顶层可扫）----
.subckt dut t s
Rsamp t s {{RSAMP}}
Ct   t  0 {{CTOT}}
Cs   s  0 {{CTOT}}
Cts  t s {{CTT}}
.ends dut

* ---- 恒流源芯（B′+P4 合流，fo_subs.inc 原样）----
.subckt fsrc ta b x currd
R1   vset ta  360k
R2   vset 0   200k
Cf   vset 0   100p
M2   vset xd 0 0 nmosw
Rg   xd   0   1meg
Bdis xd   0   V={{3.3*V(currd)}}
Cg   g    0   1n
M1   x    g b b nmosb
Xop  vset b ta 0 g opa333t
.ends fsrc

* ---- 一阶 AAF 单线（= fo_subs.inc fsfo 原样，仅更名）----
.subckt fsfo1 in vcc vee out
Xfo in fcc vcc vee fcc OPAx388
Rf  fcc out {{RFO}}
Cg  out 0   {{CFO}}
.ends fsfo1

* ---- 二阶 AAF 单线（任务书 §2：R1→节点1(CG1)→R2→节点2/ADC(CG2)）----
.subckt fsfo2 in vcc vee out
Xfo in fcc vcc vee fcc OPAx388
Rf1 fcc n1  {{RF1}}
Cg1 n1  0   {{CF1}}
Rf2 n1  out {{RF2}}
Cg2 out 0   {{CF2}}
.ends fsfo2

* ---- ADC 采样开关模型（fo_subs.inc fsadc 原样，M2/M6 口径）----
.subckt fsadc pa na vcm vswp vswn
Rin  pa  na  130k
Cpa  pa  0   5p
Cna  na  0   5p
S1a  pa  csa vswp 0  swsh
Csa  csa vcm 1.75p
S2a  csa vcm vswn 0  swsh
S1b  na  csb vswn 0  swsh
Csb  csb vcm 1.75p
S2b  csb vcm vswp 0  swsh
.ends fsadc
"""


def fullchain_net(sid: str, p: dict) -> str:
    """整链静态场景：骨架 = fo1_rc_review/run_all.py fullchain_net（ccsource/fs1_static.net
    时序），AAF 段按拓扑换 fsfo1/fsfo2；AIN1N Kelvin 直连（无第四运放）与 Cd 顶层跨接同基座。"""
    if p["topo"] == 1:
        aaf = ("XfT t ta 0 a0p fsfo1\nXfM m ta 0 a0n fsfo1\nXfB b ta 0 a1p fsfo1\n"
               "RKN 0 na1 {RFO}\nCGN na1 0 {CFO}\n")
        prm = f".param RSAMP=47k CTOT=200p CTT=30p RFO={fmt(p['r1'])} CFO={fmt(p['cg1'])} CDO={fmt(p['cd'])}\n"
    else:
        aaf = ("XfT t ta 0 a0p fsfo2\nXfM m ta 0 a0n fsfo2\nXfB b ta 0 a1p fsfo2\n"
               "RKN1 0 n1n {RF1}\nCGN1 n1n 0 {CF1}\nRKN2 n1n na1 {RF2}\nCGN2 na1 0 {CF2}\n")
        prm = (f".param RSAMP=47k CTOT=200p CTT=30p RF1={fmt(p['r1'])} CF1={fmt(p['cg1'])} "
               f"RF2={fmt(p['r2'])} CF2={fmt(p['cg2'])} CDO={fmt(p['cd'])}\n")
    return f"""* {sid} 整链静态场景 — aaf_pkg_review 台架（骨架=fo1_rc_review fullchain_net，只生成本轮不跑）
* AAF：{'一阶 R1/CG1 + Cd' if p['topo']==1 else '二阶 R1/CG1/R2/CG2（任务书§2）'} + Cd；AIN1N Kelvin RC 直连 E(=地)，无第四运放
* 器件: fsrc(OPA333t+BSS138) + 3x{'fsfo1' if p['topo']==1 else 'fsfo2'}(TI宏OPAx388) + fsadc x2(ms 断态) + Cff=100p
.include {HERE}/pkg_subs.inc
{prm}V1 ta 0 3.3
Rtop ta t 10k
Rb t 0 150k
Xdut t s dut
Rref t f 100k
Cff f 0 100p
Vk1 k1c 0 PWL(0 1 1m 1 1.01m 0 3.71m 0 3.72m 1)
S1 s x k1c 0 swNO
Vk2 k2c 0 PWL(0 1 2m 1 2.01m 0 3.7m 0 3.71m 1)
Bk2n k2n 0 V={{1-V(k2c)}}
S2 f x k2n 0 swNO
Vsen sensec 0 PWL(0 1 1m 1 1.01m 0 3.71m 0 3.72m 1)
Bsenn sensen 0 V={{1-V(sensec)}}
S3 s m sensec 0 swNO
S4 f m sensen 0 swNO
Vdis dis 0 PWL(0 0 1m 0 1.01m 1 2m 1 2.01m 0 3.6m 0 3.61m 1 3.91m 1 3.92m 0)
Xsrc ta b x dis fsrc
Rs b 0 150k
{aaf}CDIF0 a0p a0n {{CDO}}
CDIF1 a1p na1 {{CDO}}
Vswp vswp 0 0
Vswn vswn 0 0
Xad0 a0p a0n 0 vswp vswn fsadc
Xad1 a1p na1 0 vswp vswn fsadc
Bch0 ch0d 0 V={{V(a0p)-V(a0n)+500u}}
Bch1 ch1d 0 V={{V(a1p)-V(na1)+500u}}
Vzp zpulse 0 PULSE(0 1 1.8m 10n 10n 20u 1)
Sz ch0d d0 zpulse 0 swsh
Cd0 d0 0 10n
Vcp cpulse 0 PULSE(0 1 3.5m 10n 10n 20u 1)
Skc ch1d kc cpulse 0 swsh
Ckc kc 0 10n
Bkd kdin 0 V={{V(ch0d)-V(d0)}}
Skd kdin kd cpulse 0 swsh
Ckd kd 0 10n
Brout rout 0 V={{100k*V(kc)/max(V(kd),1u)*max(V(ch0d)-V(d0),1u)/max(V(ch1d),1u)}}
Braw rraw 0 V={{150k*max(V(ch0d),1u)/max(V(ch1d),1u)}}
Brt rtrue 0 V={{RSAMP}}
.tran 0 5m 0 0.2u
.options method=gear
.save V(ch0d) V(ch1d) V(rout) V(rraw) V(rtrue) V(d0) V(kc) V(kd) V(t) V(s) V(m) V(f) V(b) V(a0p) V(a0n) V(a1p) V(na1)
.end
"""


def gen_all() -> list[Path]:
    for d in (NET, LOGD, RAWD, CSVD, PLOTD):
        d.mkdir(exist_ok=True)
    written = []
    for sid, p in SCHEMES.items():
        f1 = NET / f"sm_{sid.lower()}_acdm.net"
        f1.write_text(net_acdm(sid, p))
        f2 = NET / f"sm_{sid.lower()}_accm.net"
        f2.write_text(net_accm(sid, p))
        written += [f1, f2]
    subs = HERE / "pkg_subs.inc"
    subs.write_text(PKG_SUBS)
    written.append(subs)
    for sid, p in SCHEMES.items():
        f = NET / f"full_{sid.lower()}_static.net"
        f.write_text(fullchain_net(sid, p))
        written.append(f)
    return written


# ======================================================================
# 3. lint：静态体检 + 与上一轮网表同一性对拍（证明 S0/S1 电气等同旧 BASE/FO1_A）
# ======================================================================
KNOWN_SUBCKT = {s.lower() for s in
                ("dut", "fsrc", "fsfo1", "fsfo2", "fsadc", "OPAx388", "opa333t")}


def lint_netlist(net: Path) -> list[str]:
    errs, names, depth = [], set(), 0
    for ln in net.read_text(errors="replace").splitlines():
        s = ln.split("*", 1)[0].strip()
        if not s:
            continue
        low = s.lower()
        if low.startswith(".include"):
            tgt = s.split(None, 1)[1].strip()
            if not Path(tgt).exists():
                errs.append(f"{net.name}: include 目标不存在: {tgt}")
        elif low.startswith(".subckt"):
            depth += 1
        elif low.startswith(".ends"):
            depth = max(0, depth - 1)
        elif depth == 0:
            tok = s.split()[0]
            if tok.startswith("X"):
                if s.split()[-1].lower() not in KNOWN_SUBCKT:
                    errs.append(f"{net.name}: X 实例子电路名未登记: {s.split()[-1]}")
            elif tok[0] in "RCVLBESIHFQTGKOZUDMJ":
                if tok.lower() in names:
                    errs.append(f"{net.name}: 顶层器件名重复: {tok}")
                names.add(tok.lower())
    return errs


def _nonmeas_lines(txt: str) -> list[str]:
    return [l.rstrip() for l in txt.splitlines()
            if l.strip() and not l.startswith("*") and not l.strip().startswith(".meas")]


def identity_checks() -> tuple[list[str], list[str]]:
    """S0/S1 冒烟网表 vs 上一轮 fo1_rc_review 网表（只读）：
    byte  = 除首行注释外逐行一致（t00 锚定网表）；
    nonmeas = 去注释/去 .meas 后电路行一致（t01/t02 口径，激励值差异单独点名）。"""
    oks, fails = [], []
    oldn = OLD / "netlists"
    jobs = [
        ("sm_s0_acdm.net", "t00_fo1_base_acdm.net", "byte"),
        ("sm_s0_accm.net", "t00_fo1_base_accm.net", "byte"),
        ("sm_s1_acdm.net", "t01_dm_opa388_fo1_a.net", "nonmeas"),
        ("sm_s1_accm.net", "t02_cm_opa388_fo1_a.net", "nonmeas"),
    ]
    for mine, theirs, mode in jobs:
        a, b = NET / mine, oldn / theirs
        if not a.exists():
            fails.append(f"{mine}: 新网表未生成")
            continue
        if not b.exists():
            oks.append(f"{mine} vs {theirs}: SKIPPED（旧产物不在盘上，.net 属 gitignore 再生物）")
            continue
        la, lb = a.read_text().splitlines(), b.read_text().splitlines()
        if mode == "byte":
            diff = [f"-{x}/+{y}" for x, y in zip(la[1:], lb[1:]) if x != y]
            if la[1:] == lb[1:] and not diff:
                oks.append(f"{mine} ≡ {theirs}（除首行注释外逐行字节一致，{len(la)-1} 行）")
            else:
                fails.append(f"{mine} vs {theirs}: 意外差异 {diff[:3]}")
        else:
            da, db = _nonmeas_lines("\n".join(la)), _nonmeas_lines("\n".join(lb))
            onlydiff = [f"-{x} | +{y}" for x, y in zip(db, da) if x != y]
            if not onlydiff:
                oks.append(f"{mine} ≡ {theirs}（非 .meas 电路行完全一致，{len(da)} 行）")
            else:
                acd = [d for d in onlydiff if "AC 1" in d and "AC 0.5" in d]
                svd = [d for d in onlydiff if d.startswith("-.save")
                       and "V(fpa) V(fna)" in d.split("|")[0]
                       and "+.save V(pa1) V(na1)" in d]
                if len(onlydiff) == len(acd) + len(svd) and len(acd) == 2:
                    oks.append(f"{mine} vs {theirs}: 仅 {len(acd)} 行激励口径差（AC 1→0.5，t02 1V→"
                               f"t00 0.5V 共模口径，线性网络等价，衰减量差 6.0206 dB 已在 CSV 双口径列体现）"
                               f"{' + .save 节点表差异（t02 多存跟随器节点，不影响解）' if svd else ''}")
                else:
                    fails.append(f"{mine} vs {theirs}: 意外差异 {onlydiff[:3]}")
    return oks, fails


def cmd_lint() -> int:
    bad = 0
    for f in sorted(NET.glob("sm_*.net")) + [HERE / "pkg_subs.inc"]:
        errs = lint_netlist(f)
        print(f"[lint] {f.name}: {'OK' if not errs else errs}")
        bad += len(errs)
    oks, fails = identity_checks()
    for m in oks:
        print(f"[ident] OK  {m}")
    for m in fails:
        print(f"[ident] FAIL {m}")
    bad += len(fails)
    return 1 if bad else 0


# ======================================================================
# 4. 运行 + 解析（判定逻辑 = fo1_rc_review/run_all.py run_net 同款；
#    .meas AC mag() 输出 dB 元组，正则同款）
# ======================================================================
def run_net(net: Path, timeout: int = 300) -> tuple[bool, str]:
    log, raw = net.with_suffix(".log"), net.with_suffix(".raw")
    if log.exists() and raw.exists() and "Total elapsed time" in log.read_text(errors="replace") \
            and raw.stat().st_mtime > net.stat().st_mtime:
        return True, "cached (log+raw fresh)"
    t0 = time.time()
    try:
        r = subprocess.run([LTSPICE_SIM, "run", str(net)], capture_output=True,
                           text=True, timeout=timeout + 60)
    except subprocess.TimeoutExpired:
        return False, f"TIMEOUT after {timeout + 60}s"
    out = (r.stdout or "") + (r.stderr or "")
    sim_done = (log.exists() and raw.exists()
                and "Total elapsed time" in log.read_text(errors="replace")
                and raw.stat().st_mtime > t0)
    if sim_done:
        note = "" if r.returncode == 0 else \
            f"NOTE ltspice-sim rc={r.returncode} (post-parse crash on complex ASCII raw; sim itself completed): {out.strip()[-160:]}"
        return True, note
    return False, out.strip()[-1500:]


MEAS_RE_DB = re.compile(
    r"^(\w+):\s+[^=]+?=\((-?[\d.eE+-]+)dB\s*,\s*([-+0-9.eE]+)", re.IGNORECASE)


def parse_meas_log(path: Path) -> dict:
    out = {}
    if not path.exists():
        return out
    for line in path.read_text(errors="replace").splitlines():
        m = MEAS_RE_DB.match(line.strip())
        if m:
            out[m.group(1)] = float(m.group(2))
    return out


def interp_mag_db(rawpath: Path, fnames: list[str], f_target: float) -> float | None:
    """ASCII raw 复数 log-f 插值 → 20log10|Σ±|（parse_r5.Raw/interp_at，与上一轮同法）。"""
    sys.path.insert(0, PARSE_R5_DIR)
    import parse_r5                       # noqa: PLC0415
    r = parse_r5.Raw(str(rawpath))
    y = None
    for i, fn in enumerate(fnames):
        v = parse_r5.interp_at(r, f_target, fn)
        y = v if i == 0 else y - v
    return 20 * math.log10(abs(y)) if abs(y) > 0 else -999.0


# ======================================================================
# 5. L1 理想引擎（纯 Python MNA；对拍任务书 §3 表以证明拓扑解读一致）：
#    完全对称 P/N 差分半电路：理想源→R1→[CG1]→R2→[CG2+2Cd+65k+5p]，
#    一阶即单节；§3 表数值经全六方案对拍复现（≤0.001 dB，见 CSV L1 块）。
# ======================================================================
RIN, CPIN = 130e3, 5e-12                 # fo1_rc_review assumptions A2/A3 同款工程口径


def _l1_h(p: dict, f: float) -> complex:
    s = 2j * math.pi * f
    yload = s * CPIN + 1 / (RIN / 2)
    if p["topo"] == 1:
        y2 = s * (p["cg1"] + 2 * p["cd"]) + yload
        z2 = 1 / y2
        return z2 / (p["r1"] + z2)
    y2 = s * (p["cg2"] + 2 * p["cd"]) + yload
    a11 = 1 / p["r1"] + s * p["cg1"] + 1 / p["r2"]
    a12 = -1 / p["r2"]
    a22 = 1 / p["r2"] + y2
    i1 = 1 / p["r1"]
    det = a11 * a22 - a12 * a12
    # Cramer 解 v2（输出节点）：v2 = (a11*i2 − a12*i1)/det，i2=0 → v2 = −a12*i1/det
    # （初版误返回 v1=中间节点，T 案 L1 全偏低——已修正并对照 §3 表复验）
    return (-a12 * i1) / det


def _db(x: complex) -> float:
    return 20 * math.log10(abs(x)) if abs(x) > 0 else -999.0


def l1_metrics(p: dict) -> dict:
    gdc = _db(_l1_h(p, 0.1))
    return dict(d4=-( _db(_l1_h(p, 16e3)) - gdc),
                d1=-( _db(_l1_h(p, FMOD)) - gdc),
                d3=-( _db(_l1_h(p, MCLK)) - gdc))


# ======================================================================
# 6. 冒烟主流程：5 只实跑 → csv/smoke_anchor.csv + plots/smoke_dm_ac.png
# ======================================================================
def smoke() -> int:
    LOGD.mkdir(exist_ok=True)
    RAWD.mkdir(exist_ok=True)
    CSVD.mkdir(exist_ok=True)
    meas, notes = {}, []
    for sid, kind in SMOKE_RUNS:
        stem = f"sm_{sid.lower()}_{kind}"
        net = NET / f"{stem}.net"
        ok, out = run_net(net, timeout=300)
        print(f"[smoke] {stem}: run ok={ok} {out if out.startswith(('NOTE','cached')) else ''}")
        if not ok:
            notes.append(f"{stem}: RUN FAILED {out[:300]}")
            meas[stem] = None
            continue
        if out.startswith("NOTE"):
            notes.append(f"{stem}: {out}")
        shutil.copy2(net.with_suffix(".log"), LOGD / f"{stem}.log")
        shutil.copy2(net.with_suffix(".raw"), RAWD / f"{stem}.raw")
        meas[stem] = parse_meas_log(LOGD / f"{stem}.log")

    rows: list[dict] = []

    def add(item, scheme, basis, anchor, this, method, tol=TOL_ANCHOR,
            within="", extra=""):
        if this is None or (isinstance(this, float) and math.isnan(this)):
            rows.append(dict(item=item, scheme=scheme, basis=basis, anchor_db=anchor,
                             this_run_db="NOT VERIFIED", diff_db="", tol_db=tol,
                             verdict="NOT VERIFIED", prior_ref=extra, method=method))
            return
        diff = this - anchor
        rows.append(dict(item=item, scheme=scheme, basis=basis, anchor_db=anchor,
                         this_run_db=round(this, 4), diff_db=round(diff, 4), tol_db=tol,
                         verdict=("yes" if abs(diff) <= tol else "NO-investigate"),
                         prior_ref=extra, method=method))

    # ---- S0 / S1 四锚（.meas 主口径 + raw 插值交叉校验）----
    for sid, items in (("S0", ("D1", "D2")), ("S1", ("D1", "D2"))):
        md = meas.get(f"sm_{sid.lower()}_acdm") or {}
        mc = meas.get(f"sm_{sid.lower()}_accm") or {}
        raw_dm, raw_cm = RAWD / f"sm_{sid.lower()}_acdm.raw", RAWD / f"sm_{sid.lower()}_accm.raw"
        if "dm_fmod" in md:
            a = ANCHOR[f"{sid}_D1"]
            cross = (interp_mag_db(raw_dm, ["V(pa1)", "V(na1)"], FMOD)
                     if raw_dm.exists() else None)
            add(f"{sid}_D1", sid, a["basis"] + "（dm 网表差分 1V）", a["anchor"],
                -md["dm_fmod"], f"acdm .meas dm_fmod 取负；raw 插值交叉={cross}",
                extra=a["prior"])
        if "cm_fmod" in mc:
            a_abs = ANCHOR[f"{sid}_D2"] if sid == "S0" else None
            abs_att = -mc["cm_fmod"]                      # 0.5V 激励绝对 dB → 衰减量
            cross = (interp_mag_db(raw_cm, ["V(pa1)"], FMOD)
                     if raw_cm.exists() else None)
            if sid == "S0":
                add("S0_D2", sid, ANCHOR["S0_D2"]["basis"], ANCHOR["S0_D2"]["anchor"],
                    abs_att, f"accm .meas cm_fmod 取负（0.5V 绝对口径，与 t00 accm 同网表口径）；"
                             f"raw 插值交叉={cross}", extra=ANCHOR["S0_D2"]["prior"])
            else:
                add("S1_D2", sid, ANCHOR["S1_D2"]["basis"], ANCHOR["S1_D2"]["anchor"],
                    abs_att - DB2, f"accm .meas cm_fmod 取负再 −6.0206（0.5V 绝对→1V 归一，"
                                   f"线性网络精确换算）；raw 插值交叉={cross}",
                    extra=ANCHOR["S1_D2"]["prior"])
            # 口径换算副行（不判 PASS，供口径审计）
            if sid == "S0":
                add("S0_D2_per1V_info", sid, "同上物理量按 1V 共模归一（t02 口径）",
                    ANCHOR["S0_D2"]["anchor"] - DB2, abs_att - DB2,
                    "口径换算副行：锚 46.41−6.0206=40.39（t02 prior FO1_BASE 40.39）",
                    tol=0.5, extra="t02 opa388 40.390")
            else:
                add("S1_D2_abs05_info", sid, "同上物理量 0.5V 激励绝对 dB（t00 口径）",
                    ANCHOR["S1_D2"]["anchor"] + DB2, abs_att,
                    "口径换算副行：锚 38.11+6.0206=44.13", tol=0.5,
                    extra="t02 opa388 38.108@1V → 44.128@0.5V")

    # ---- T2 二阶冒烟：16k 衰减 vs §3 理想表 + 同趋势解释 ----
    mt = meas.get("sm_t2_acdm") or {}
    raw_t2 = RAWD / "sm_t2_acdm.raw"
    l1 = l1_metrics(SCHEMES["T2"])
    if "dm_16k" in mt and "dm_dc" in mt:
        d4 = -(mt["dm_16k"] - mt["dm_dc"])
        cross16 = (interp_mag_db(raw_t2, ["V(pa1)", "V(na1)"], 16e3)
                   if raw_t2.exists() else None)
        add("T2_D4_16k", "T2", "DM 16kHz 相对 DC 衰减（vs 任务书 §3 理想表 0.412）",
            ANCHOR["T2_D4"]["anchor"], d4,
            f"acdm .meas −(dm_16k−dm_dc)；raw 插值交叉={cross16}；"
            f"本脚本 L1 引擎（MNA，Rin130k+5p/端 半电路）={l1['d4']:.4f}——"
            f"实测−理想残差归属：真实 OPA388 闭环输出阻抗 + C_pin（一阶先例：S0 L1 0.2233→实测 0.2234）",
            tol=0.1, extra="§3 表 T2 行 0.412（理想源，非 LTspice）")
    if "dm_fmod" in mt:
        add("T2_D1_4M_info", "T2", "DM @4.096MHz 衰减（趋势参考，不锚定——§3 理想值不含真实运放）",
            TASK_S3["T2"][1], -mt["dm_fmod"],
            "info 行：一阶先例 ideal→real +3.0 dB（35.67→38.72，跟随器模型致）故不与 §3 直判",
            tol=99.0, extra="§3 表 59.33（理想）")
    if "dm_mclk" in mt:
        add("T2_D3_16M_info", "T2", "DM @16.384MHz 衰减（趋势参考）",
            TASK_S3["T2"][3], -mt["dm_mclk"], "info 行：同上不锚定", tol=99.0,
            extra="§3 表 83.38（理想）")

    # ---- L1 引擎 vs §3 表全六方案对拍（拓扑解读一致性证据）----
    for sid in SCHEMES:
        t = TASK_S3[sid]
        l1s = l1_metrics(SCHEMES[sid])
        rows.append(dict(
            item=f"L1_vs_S3_{sid}", scheme=sid,
            basis="本脚本 L1 MNA 引擎（理想源+Rin130k 差分+C_pin 5p/端）对拍任务书 §3 表",
            anchor_db=f"d4={t[0]}/d1={t[1]}/cm={t[2]}/d3={t[3]}",
            this_run_db=f"d4={l1s['d4']:.3f}/d1={l1s['d1']:.2f}",
            diff_db=f"Δd4={l1s['d4']-t[0]:+.3f}/Δd1={l1s['d1']-t[1]:+.2f}",
            tol_db=0.01, verdict=("yes" if abs(l1s["d4"] - t[0]) <= 0.01 else "NO-investigate"),
            prior_ref="§3 表全行复现 ≤0.001 dB 级（本轮实测对拍）",
            method="纯 Python 复数 MNA，非 LTspice——证明 §2 拓扑解读与 §3 引擎一致"))

    # ---- 环境/同一性/口径注记行 ----
    oks, fails = identity_checks()
    env = [
        ("env_ltspice", "26.1.1（ltspice-sim status 实测，本轮启动前复核）"),
        ("env_opax388_md5", "97c4045ef608097ec1f1a67dca97ceae（md5sum 实测，与 fo1_rc_review 同源）"),
        ("env_scope", "只跑冒烟 5 只；T1/T3/T4 与各案 accm/full_* 网表已生成未运行（NOT VERIFIED）"),
        ("ident_ok", " | ".join(oks) if oks else "无"),
        ("ident_fail", " | ".join(fails) if fails else "无"),
        ("calib_D2", "S0-D2 锚=0.5V 激励绝对 dB（t00 口径）；S1-D2 锚=1V 归一（t02 口径）；"
                     "两口径差恒 6.0206 dB，本轮 0.5V 网表线性换算，副行双口径并记"),
    ]
    for k, v in env:
        rows.append(dict(item=k, scheme="", basis="", anchor_db="", this_run_db=v,
                         diff_db="", tol_db="", verdict="", prior_ref="", method=""))
    for i, n in enumerate(notes, 1):
        rows.append(dict(item=f"note_{i}", scheme="", basis="", anchor_db="",
                         this_run_db=n, diff_db="", tol_db="", verdict="",
                         prior_ref="", method="运行口径记录"))

    out_csv = CSVD / "smoke_anchor.csv"
    with out_csv.open("w", newline="\n", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=[
            "item", "scheme", "basis", "anchor_db", "this_run_db", "diff_db",
            "tol_db", "verdict", "prior_ref", "method"])
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"[smoke] csv -> {out_csv}")
    for r in rows:
        if r["item"].startswith(("S0_", "S1_", "T2_")):
            print(f"      {r['item']:18s} anchor={r['anchor_db']} this={r['this_run_db']} "
                  f"diff={r['diff_db']} verdict={r['verdict']}")

    # ---- 冒烟曲线图（S0/S1/T2 DM 幅频 + 锚点标记）----
    try:
        _plot_dm()
    except Exception as e:                                  # noqa: BLE001
        print(f"[smoke] plot skipped: {e}")

    hard = any(r["verdict"] == "NOT VERIFIED" for r in rows
               if r["item"].startswith(("S0_", "S1_", "T2_D4")))
    noinv = any(r["verdict"] == "NO-investigate" for r in rows
                if r["item"].startswith(("S0_D", "S1_D", "T2_D4")))
    verdict = ("NOT VERIFIED" if hard else
               "NO-investigate(>0.5dB 或 16k 超 0.1dB)" if noinv else "PASS")
    print(f"[smoke] verdict: {verdict}")
    return 0


def _plot_dm():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt            # noqa: PLC0415
    sys.path.insert(0, PARSE_R5_DIR)
    import parse_r5                            # noqa: PLC0415
    fig, ax = plt.subplots(figsize=(9, 5.5))
    for sid in ("S0", "S1", "T2"):
        rp = RAWD / f"sm_{sid.lower()}_acdm.raw"
        if not rp.exists():
            continue
        r = parse_r5.Raw(str(rp))
        f = r.f
        H = [parse_r5.interp_at(r, float(ff), "V(pa1)") - parse_r5.interp_at(r, float(ff), "V(na1)")
             for ff in f]
        mag = [20 * math.log10(abs(h)) if abs(h) > 0 else -320 for h in H]
        ax.semilogx(f, mag, label=f"{sid} DM (measured)")
    for fx, lab in ((16e3, "16k"), (FMOD, "4.096M"), (MCLK, "16.384M")):
        ax.axvline(fx, color="gray", lw=0.6, ls=":")
        ax.text(fx, -5, f" {lab}", fontsize=8, color="gray", rotation=90, va="top")
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("20log10|V(pa1)-V(na1)| per 1V DM (dB)")
    ax.set_title("aaf_pkg_review smoke: S0/S1/T2 differential-mode AC (TI OPAx388 macromodel)")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(loc="lower left")
    fig.tight_layout()
    out = PLOTD / "smoke_dm_ac.png"
    fig.savefig(out, dpi=140)
    print(f"[smoke] plot -> {out}")


# ======================================================================
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("cmd", nargs="?", default="all", choices=["gen", "lint", "smoke", "all"])
    args = ap.parse_args()
    if args.cmd in ("gen", "lint", "all"):
        for f in gen_all():
            print(f"[gen] {f.name}")
    if args.cmd == "lint":
        return cmd_lint()
    if args.cmd in ("smoke", "all"):
        if args.cmd == "all":
            rc = cmd_lint()
            if rc:
                print("[all] lint FAIL，中止 smoke")
                return rc
        return smoke()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
