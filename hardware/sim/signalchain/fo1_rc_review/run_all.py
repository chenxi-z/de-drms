#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""run_all.py — fo1_rc_review 四方案可复现台架（任务书 §6 自动化执行）

子命令：
  gen     生成全部网表（T00 回归 ×4 + 整链四方案静态场景 ×4 + fo_subs.inc），不跑
  t00     生成 + 实跑 FO1_BASE 的 T00 回归四项（差模 AC / 共模 AC / 瞬态建立 / 环路 PM），
          写 csv/t00_regression.csv（含与 2026-10-23 锚定值的差异表）
  all     = gen + t00（本轮默认：整链网表只生成不跑，留待 T01–T12）

口径（与 fo1_rc_review/README.md 勘察结论一致）：
  * T00 回归网表逐行复刻 aaf_first_order/gen_fo.py 的 FO1 生成函数——锚定值
    （D1 −40.7 / D2 −46.4 / D3 −62.7 dB、D4 0.230 dB、建立 ≈21 µs、PM 98.6°，
    docs/design/spec/2026-10-23-signal-chain-variants.md:33-38,57-61）出自该口径，
    换口径的偏差必须归因于口径而非环境。
  * D1/D2/D3 锚定值符号口径 = 20log10(mag(...)) 的原始 dB（差分激励 1 V / 共模 0.5 V），
    负值即残留幅度 dB；阈值 ≥80/60/100 dB 指衰减量（= −残留 dB）。
  * 整链网表 = fs_fullchain/fs_subs.inc 基座（dut 线缆寄生 / fsrc B′+P4 / fsadc M2/M6
    断态口径）+ 一阶 fsfo 替换 fslad + AIN1N Kelvin RC 直连（无第四运放），
    时序骨架照 ccsource/fs1_static.net；include 一律绝对路径（全角逗号目录陷阱）。

依赖：~/.local/bin/ltspice-sim（LTspice 26.1.1/wine）、hardware/sim/aaf/parse_r5.py、numpy。
产物：netlists/*.net（gitignore 不入库，靠本脚本再生）、logs/、raw/、csv/t00_regression.csv。
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

HERE = Path(__file__).resolve().parent
NET = HERE / "netlists"
LOGD = HERE / "logs"
RAWD = HERE / "raw"
CSVD = HERE / "csv"

ROOT = "/media/anning/data/Project/DE-DRMS"
LIB = f"{ROOT}/hardware/sim/_candidate_models/opa388/OPAx388.LIB"
MODELS_INC = f"{ROOT}/hardware/sim/ccsource/models.inc"
PARSE_R5_DIR = f"{ROOT}/hardware/sim/aaf"
LTSPICE_SIM = str(Path.home() / ".local/bin/ltspice-sim")

FMOD = 4.096e6
MCLK = 16.384e6

# ---- 四方案参数（任务书 §2 表，原文照录）----
CASES = {
    "FO1_BASE": dict(r=47.0, cg=47e-9, cd=820e-12),
    "FO1_A":    dict(r=100.0, cg=22e-9, cd=820e-12),
    "FO1_B":    dict(r=200.0, cg=10e-9, cd=820e-12),
    "FO1_C":    dict(r=100.0, cg=10e-9, cd=6.8e-9),
}
REG_CASE = "FO1_BASE"          # T00 回归锚定方案
ANCHORS = {                     # 2026-10-23 报告锚定值（signal-chain-variants.md:33-38,57-61）
    "D1_db": -40.7,             # 残留幅度 dB：20log10(mag(V(pa1,na1)))@4.096 MHz
    "D2_db": -46.4,             # 残留幅度 dB：20log10(mag(V(pa1)))@4.096 MHz（共模 0.5 V 激励）
    "D3_db": -62.7,             # 残留幅度 dB：20log10(mag(V(pa1,na1)))@16.384 MHz
    "D4_db": 0.230,             # 16 kHz 相对 DC 衰减量（正 dB）
    "settle_us": 21.0,          # 0.01% 建立（0.71 V 差分阶跃 → 71 µV 带 crossing）
    "pm_deg": 98.6,             # 跟随器 β=1 断环相位裕量
}


def fmt(v: float) -> str:
    return f"{v:.6g}"


# ======================================================================
# 1. T00 回归网表 —— 逐行复刻 aaf_first_order/gen_fo.py（FO1 参数化版）
#    改动仅限：文件头注释、参数名 p['r1']/p['c1']/p['cd'] → r/cg/cd。
# ======================================================================
def fo_ladder(p, pa="pa1", na="na1"):
    return (f"Ra1 fpa {pa} {fmt(p['r'])}\n"
            f"Ca1 {pa} 0 {fmt(p['cg'])}\n"
            f"Rb1 fna {na} {fmt(p['r'])}\n"
            f"Cb1 {na} 0 {fmt(p['cg'])}\n")


T00_HEAD = f".include {LIB}\nVcc vcc 0 DC 3.3\nVee vee 0 DC 0\n"


def t00_ac_dm(p):
    return (f"* t00 FO1_BASE ac_dm (口径=aaf_first_order/gen_fo.py net_ac_dm)\n{T00_HEAD}"
            f"Vp vp 0 DC 2 AC 0.5\nVn vn 0 DC 2 AC -0.5\n"
            f"Xfa vp fpa vcc vee fpa OPAx388\nXfb vn fna vcc vee fna OPAx388\n"
            + fo_ladder(p) +
            f"Cd pa1 na1 {fmt(p['cd'])}\n"
            f"Rin pa1 na1 130000\nCpa pa1 0 5e-12\nCna na1 0 5e-12\n"
            f".ac dec 400 0.1 200Meg\n"
            f".options plotwinsize=0 reltol=1e-6 abstol=1e-12 vntol=1e-9 chgtol=1e-15 trtol=1\n"
            f".meas AC dm_dc   FIND mag(V(pa1,na1)) AT=0.1\n"
            f".meas AC dm_fmod FIND mag(V(pa1,na1)) AT=4.096Meg\n"
            f".meas AC dm_mclk FIND mag(V(pa1,na1)) AT=16.384Meg\n"
            f".meas AC dm_16k  FIND mag(V(pa1,na1)) AT=16k\n"
            f".meas AC foll_pk MAX mag(V(fpa))\n"
            f".meas AC foll_pk_f WHEN mag(V(fpa))=foll_pk\n"
            f".save V(pa1) V(na1) V(fpa) V(fna)\n.end\n")


def t00_ac_cm(p):
    return (f"* t00 FO1_BASE ac_cm (口径=aaf_first_order/gen_fo.py net_ac_cm)\n{T00_HEAD}"
            f"Vp vp 0 DC 2 AC 0.5\nVn vn 0 DC 2 AC 0.5\n"
            f"Xfa vp fpa vcc vee fpa OPAx388\nXfb vn fna vcc vee fna OPAx388\n"
            + fo_ladder(p) +
            f"Cd pa1 na1 {fmt(p['cd'])}\n"
            f"Rin pa1 na1 130000\nCpa pa1 0 5e-12\nCna na1 0 5e-12\n"
            f".ac dec 400 0.1 200Meg\n"
            f".options plotwinsize=0 reltol=1e-6 abstol=1e-12 vntol=1e-9 chgtol=1e-15 trtol=1\n"
            f".meas AC cm_dc   FIND mag(V(pa1)) AT=0.1\n"
            f".meas AC cm_fmod FIND mag(V(pa1)) AT=4.096Meg\n"
            f".meas AC cm_mclk FIND mag(V(pa1)) AT=16.384Meg\n"
            f".save V(pa1) V(na1)\n.end\n")


def t00_loop(p):
    # 跟随器 β=1 断环 + 真实一阶差分半电路负载（2×Cd 虚地 + 65k + 5p，同 gen_fo net_loop）
    return (f"* t00 FO1_BASE loop (口径=aaf_first_order/gen_fo.py net_loop)\n{T00_HEAD}"
            f"Vp vp 0 DC 2 AC 0\nVinn inn 0 DC 2 AC 1\n"
            f"Xfa vp inn vcc vee fpa OPAx388\n"
            f"Ra1 fpa pa1 {fmt(p['r'])}\nCa1 pa1 0 {fmt(p['cg'])}\n"
            f"Cd pa1 0 {fmt(p['cd'] * 2)}\nRin pa1 0 65000\nCpa pa1 0 5e-12\n"
            f".ac dec 400 0.1 200Meg\n"
            f".options plotwinsize=0 reltol=1e-6 abstol=1e-12 vntol=1e-9 chgtol=1e-15 trtol=1\n"
            f".save V(fpa) V(inn)\n.end\n")


def t00_tran(p):
    # 原口径逐行复刻（gen_fo.py net_tran）。注意：其 PWL 极性产生差分 −0.71→0，
    # ts01 WHEN=0.709929 RISE=1 的上升穿越不存在（本机 LTspice 26.1.1 实测不出 ts01，
    # 旧 fo_results.json tran 空字段根因之一）。保留原样跑，ts01 由 tran2/raw 两口径补。
    return (f"* t00 FO1_BASE tran (口径=aaf_first_order/gen_fo.py net_tran)\n{T00_HEAD}"
            f"Vp vp 0 PWL(0 1.645 1u 1.645 1.01u 2.0)\n"
            f"Vn vn 0 PWL(0 2.355 1u 2.355 1.01u 2.0)\n"
            f"Xfa vp fpa vcc vee fpa OPAx388\nXfb vn fna vcc vee fna OPAx388\n"
            + fo_ladder(p) +
            f"Cd pa1 na1 {fmt(p['cd'])}\n"
            f"Rin pa1 na1 130000\nCpa pa1 0 5e-12\nCna na1 0 5e-12\n"
            f".tran 0 1m 0 10n\n"
            f".options plotwinsize=0 reltol=1e-6 abstol=1e-12 vntol=1e-9 chgtol=1e-15 trtol=1\n"
            f".meas TRAN vfin FIND V(pa1,na1) AT=0.9m\n"
            f".meas TRAN ts01 WHEN V(pa1,na1)=0.709929 RISE=1\n"
            f".meas TRAN vmax MAX V(pa1,na1) FROM=0 TO=1m\n"
            f".meas TRAN vmin MIN V(pa1,na1) FROM=0 TO=1m\n"
            f".save V(pa1,na1) V(fpa) V(fna)\n.end\n")


def t00_tran2(p):
    """极性翻转镜像版（差分 0→+0.71 V、共模恒 2 V）：与原极性 tran(−0.71→0) 在 LTI 网络
    下建立时间数学等价，用于镜像交叉校验。注意 gen_fo.py 原 ts01 阈值 0.709929 在两种极性
    下均物理不可达（DC 分压 0.999278 → 真终值 0.709487 > 0.71−71µV），故不设 ts01 meas，
    建立时间统一由 raw 带外出带法提取（见 run_t00）。"""
    return (f"* t00 FO1_BASE tran2 (极性翻转镜像：差分 0→+0.71V)\n{T00_HEAD}"
            f"Vp vp 0 PWL(0 2 1u 2 1.01u 2.355)\n"
            f"Vn vn 0 PWL(0 2 1u 2 1.01u 1.645)\n"
            f"Xfa vp fpa vcc vee fpa OPAx388\nXfb vn fna vcc vee fna OPAx388\n"
            + fo_ladder(p) +
            f"Cd pa1 na1 {fmt(p['cd'])}\n"
            f"Rin pa1 na1 130000\nCpa pa1 0 5e-12\nCna na1 0 5e-12\n"
            f".tran 0 1m 0 10n\n"
            f".options plotwinsize=0 reltol=1e-6 abstol=1e-12 vntol=1e-9 chgtol=1e-15 trtol=1\n"
            f".meas TRAN vfin FIND V(pa1,na1) AT=0.9m\n"
            f".meas TRAN vmax MAX V(pa1,na1) FROM=0 TO=1m\n"
            f".meas TRAN vmin MIN V(pa1,na1) FROM=0 TO=1m\n"
            f".save V(pa1,na1) V(fpa) V(fna)\n.end\n")


T00_GEN = {"acdm": t00_ac_dm, "accm": t00_ac_cm, "loop": t00_loop,
           "tran": t00_tran, "tran2": t00_tran2}


# ======================================================================
# 2. 整链基座：fo_subs.inc（fs_subs.inc 分段移植 + 一阶 fsfo 替换 fslad）
# ======================================================================
FO_SUBS = f"""* =====================================================================
* fo_subs.inc — fo1_rc_review 整链子电路库（2026-10-24）
* 基座 = fs_fullchain/fs_subs.inc 分段移植（dut/fsrc/fsadc 原样；fslad 四级 → fsfo 一阶）
* AIN1N Kelvin 接法（无第四运放）在顶层场景网表实现，不在本库。
* 依赖（绝对路径，规避全角逗号目录名下 LTspice 相对 include 解析失败）：
*   ccsource/models.inc                     ：opa333t/nmosb/swNO/swsh
*   _candidate_models/opa388/OPAx388.LIB    ：TI 官方宏 Final 1.4（md5 97c4045ef608097ec1f1a67dca97ceae）
* 一阶参数 RFO/CFO 由顶层 .param 传入（四方案共用同一子电路，仅参数不同）。
* =====================================================================
.include {MODELS_INC}
.include {LIB}

* ---- nmosw：M2 关断管手册拟合宏（fs_subs.inc 同式）----
.model nmosw nmos(level=1 vto=1.25 kp=0.15 lambda=0.05 cgso=10.8p cgdo=1.43p cbd=0 cbs=0)

* ---- 被测电阻 + 线缆寄生（fs_subs.inc 原样；CTOT/CTT 顶层可扫）----
.subckt dut t s
Rsamp t s {{RSAMP}}
Ct   t  0 {{CTOT}}
Cs   s  0 {{CTOT}}
Cts  t s {{CTT}}
.ends dut

* ---- 恒流源芯（B′+P4 合流，fs_subs.inc 原样）：ta(3.3VA) b(Rsense顶) x(BSS138漏极/回线) currd ----
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

* ---- 一阶 AAF 单线（替换 fslad 四级）：跟随器(TI 宏) + R(fcc→out) + C_G(out→0) ----
* 任务书 §2 拓扑：每条输入线各串一颗 R、各一颗对地 C_G；C_D 在顶层跨 pa/na（串联 R 之后）
.subckt fsfo in vcc vee out
Xfo in fcc vcc vee fcc OPAx388
Rf  fcc out {{RFO}}
Cg  out 0   {{CFO}}
.ends fsfo

* ---- ADC 采样开关模型（fs_subs.inc fsadc 原样，M2/M6 口径）----
* C_S=3.5pF 差分（每侧 1.75pF）；S1/S2 180° 反相 @fMOD=4.096MHz、各占 50%
* Ron=100Ω（swsh，lad4b D9 主口径；手册无规格 → 声明假设，T08 扫 1/100/1k）
* ms 场景：vswp=vswn=0（断态，只留 Z_IN/C_pin/C_S 负载）；µs 场景：顶层 PULSE 实时钟
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


def fullchain_net(case: str, p: dict) -> str:
    """整链静态场景网表：时序骨架 = ccsource/fs1_static.net（K1–K4 / δ0-k 校准 / 比值重构），
    器件换：opa388t 行为宏 → fsfo（TI 宏 + 一阶 RC）；平铺 Rsamp → dut（+线缆寄生）；
    平铺恒流源 → fsrc（B′+P4）；Rz 130k 负载 → fsadc（ms 断态口径）。
    AIN1N：E(=Rsense 底端=node 0) —RKN→ na1 + CGN 对地（Rf3/Cf3 母本模式，无第四运放）。"""
    return f"""* {case} 整链静态场景 — fo1_rc_review 台架（骨架=ccsource/fs1_static.net，只生成本轮不跑）
* 一阶 AAF：每线 R={fmt(p['r'])} Ω 串入 + C_G={fmt(p['cg'])} F 对地；C_D={fmt(p['cd'])} F 跨 AINxP/AINxN（串联 R 之后）
* 节点: ta轨/T顶/S样品底/F校准底/X漏极/B源极(E=Rsense底端=地)/m=ch0N切换后/a0p..na1=ADC引脚
* 器件: 恒流源 fsrc(OPA333t+BSS138, B′+P4: Cf=100p/Cg=1n/M2=nmosw) + 3xfsfo(TI宏OPAx388+一阶RC)
*       + AIN1N Kelvin RC + fsadc x2(M2/M6, ms 断态口径 vswp=vswn=0) + Cff=100p(判别D定档)
.include {HERE}/fo_subs_inc_placeholder
.param RSAMP=47k CTOT=200p CTT=30p RFO={fmt(p['r'])} CFO={fmt(p['cg'])} CDO={fmt(p['cd'])}
V1 ta 0 3.3
Rtop ta t 10k
Rb t 0 150k
Xdut t s dut
Rref t f 100k
Cff f 0 100p
* ---- K1–K4（TMUX 行为开关，时序 = fs1_static 母本：测量→零点→校准→测量）----
Vk1 k1c 0 PWL(0 1 1m 1 1.01m 0 3.71m 0 3.72m 1)
S1 s x k1c 0 swNO
Vk2 k2c 0 PWL(0 1 2m 1 2.01m 0 3.7m 0 3.71m 1)
Bk2n k2n 0 V={{1-V(k2c)}}
S2 f x k2n 0 swNO
Vsen sensec 0 PWL(0 1 1m 1 1.01m 0 3.71m 0 3.72m 1)
Bsenn sensen 0 V={{1-V(sensec)}}
S3 s m sensec 0 swNO
S4 f m sensen 0 swNO
* ---- 恒流源 B′+P4 + Rsense（低边：E=地）----
Vdis dis 0 PWL(0 0 1m 0 1.01m 1 2m 1 2.01m 0 3.6m 0 3.61m 1 3.91m 1 3.92m 0)
Xsrc ta b x dis fsrc
Rs b 0 150k
* ---- 3x 一阶跟随器线（T/M/B；TI 宏 OPAx388 + R + C_G）----
XfT t ta 0 a0p fsfo
XfM m ta 0 a0n fsfo
XfB b ta 0 a1p fsfo
* ---- AIN1N Kelvin：E(=地) —RKN→ na1 + CGN 对地（保留真实源阻抗与接地回路，无第四运放）----
RKN 0 na1 {{RFO}}
CGN na1 0 {{CFO}}
* ---- C_D 每差分通道 1 颗（串联 R 之后，跨 ADC 引脚）----
CDIF0 a0p a0n {{CDO}}
CDIF1 a1p na1 {{CDO}}
* ---- ADS131A02 等效负载（fsadc：Z_IN 130k + C_pin 5p/端 + C_S 1.75p/侧；ms 断态口径）----
Vswp vswp 0 0
Vswn vswn 0 0
Xad0 a0p a0n 0 vswp vswn fsadc
Xad1 a1p na1 0 vswp vswn fsadc
* ---- 通道差分 + 失调 500µV（fs README §三 ms 场景口径）----
Bch0 ch0d 0 V={{V(a0p)-V(a0n)+500u}}
Bch1 ch1d 0 V={{V(a1p)-V(na1)+500u}}
* ---- δ0/k 校准单拍采样 + 比值重构（fs1_static 母本）----
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


# ======================================================================
# 3. 生成入口
# ======================================================================
def gen_all() -> list[Path]:
    NET.mkdir(exist_ok=True)
    written = []
    # 3.1 T00 回归网表（FO1_BASE；其余方案同口径网表留待 T01 用 gen --case 扩展）
    p0 = CASES[REG_CASE]
    for kind, fn in T00_GEN.items():
        f = NET / f"t00_{REG_CASE.lower()}_{kind}.net"
        f.write_text(fn(p0))
        written.append(f)
    # 3.2 整链子电路库 + 四方案静态场景（本轮只生成不跑）
    subs = HERE / "fo_subs.inc"
    subs.write_text(FO_SUBS)
    written.append(subs)
    for case, p in CASES.items():
        stem = case.lower().replace("fo1_", "fo1_")
        f = NET / f"full_{stem}_static.net"
        # include 绝对路径（fo_subs.inc 在本目录，不用 netlists/ 下的副本）
        txt = fullchain_net(case, p).replace(
            f".include {HERE}/fo_subs_inc_placeholder", f".include {subs}")
        f.write_text(txt)
        written.append(f)
    return written


# ======================================================================
# 4. 运行 + 解析
# ======================================================================
def run_net(net: Path, timeout: int = 300) -> tuple[bool, str]:
    """ltspice-sim run。幂等：已有新鲜产物（.log 含 'Total elapsed time' 且 .raw 比网表新）
    则跳过。已知环境缺陷（2026-10-24 实测）：LTspice 26.1.1 + ltspice-sim 默认 ASCII raw 下，
    AC 分析的复数行（"1.0e-01,0.0"）令 ltspice-sim 内部后处理崩溃（rc=1，
    "could not convert string to float"）——仿真本体已完成（.log 有 elapsed time + .meas 输出，
    .raw 完整）。故成功判定以 LTspice 产物为准，ltspice-sim 后处理失败仅记 note。"""
    log = net.with_suffix(".log")
    raw = net.with_suffix(".raw")
    if log.exists() and raw.exists() and "Total elapsed time" in log.read_text(errors="replace") \
            and raw.stat().st_mtime > net.stat().st_mtime:
        return True, "cached (log+raw fresh)"
    t0 = time.time()
    cmd = [LTSPICE_SIM, "run", str(net)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 60)
    except subprocess.TimeoutExpired:
        return False, f"TIMEOUT after {timeout + 60}s"
    out = (r.stdout or "") + (r.stderr or "")
    sim_done = (log.exists() and raw.exists()
                and "Total elapsed time" in log.read_text(errors="replace")
                and raw.stat().st_mtime > t0)
    if sim_done:
        note = "" if r.returncode == 0 else \
            f"NOTE ltspice-sim rc={r.returncode} (post-parse crash on complex ASCII raw; sim itself completed): {out.strip()[-200:]}"
        return True, note
    return False, out.strip()[-2000:]


# .meas 输出两种实测格式（LTspice 26.1.1）：
#   AC:  `dm_fmod: mag(V(pa1,na1))=(-40.6891139774dB,0°) at 4096000`  ← (dB,°) 元组
#   TRAN:`ts01: v(pa1,na1)=0.709929 at 2.15e-05` / `vmax: ...=0.71 FROM 0 TO 0.001`
MEAS_RE_DB = re.compile(
    r"^(\w+):\s+[^=]+?=\((-?[\d.eE+-]+)dB\s*,\s*([-+0-9.eE]+)", re.IGNORECASE)
MEAS_RE_LIN = re.compile(
    r"^(\w+):\s+[^=]+?=\s*(-?[\d.eE+-]+)\s*(?:at\s+([-+0-9.eE]+))?", re.IGNORECASE)


def parse_meas_log(path: Path) -> dict:
    """返回 {name: {val, unit('dB'|'V'), at?}}。dB 元组优先匹配。
    gen_fo.py:103 原正则两种格式均不匹配（旧 fo_results.json 空字段根因，本轮实测确认）。"""
    out = {}
    if not path.exists():
        return out
    for line in path.read_text(errors="replace").splitlines():
        s = line.strip()
        m = MEAS_RE_DB.match(s)
        if m:
            d = {"val": float(m.group(2)), "unit": "dB"}
            at = re.search(r"\bat\s+([-+0-9.eE]+)", s)
            if at:
                d["at"] = float(at.group(1))
            out[m.group(1)] = d
            continue
        m = MEAS_RE_LIN.match(s)
        if m:
            try:
                val = float(m.group(2))
            except ValueError:
                continue          # 值是测量名引用（如 foll_pk AT …）→ 跳过
            d = {"val": val, "unit": "V"}
            if m.group(3):
                d["at"] = float(m.group(3))
            out[m.group(1)] = d
    return out


def interp_mag_db(rawpath: Path, fnames: list[str], f_target: float) -> float | None:
    """ASCII raw 复数插值 → 20log10|Σ±|（parse_r5.Raw + interp_at 同源实现）。
    fnames=["V(pa1)","V(na1)"] 时取复数差 V(pa1)-V(na1)（AC raw 无差分变量，只能两变量相减）。"""
    import numpy as np
    sys.path.insert(0, PARSE_R5_DIR)
    import parse_r5
    r = parse_r5.Raw(str(rawpath))
    y = None
    for i, fn in enumerate(fnames):
        v = parse_r5.interp_at(r, f_target, fn)
        y = v if i == 0 else y - v
    return 20 * math.log10(abs(y)) if abs(y) > 0 else -999.0


def loop_pm_ugf(rawpath: Path):
    """环路 PM/UGF（gen_fo.py:128-139 同口径：T=-V(fpa)/V(inn)，mag 跨 1 处 pm=180+ph）。"""
    import numpy as np
    sys.path.insert(0, PARSE_R5_DIR)
    import parse_r5
    d = parse_r5.Raw(str(rawpath))
    freq = d.f
    T = -np.array(d.col("V(fpa)")) / np.array(d.col("V(inn)"))
    mag = np.abs(T)
    ph = np.angle(T) * 180 / math.pi
    ugf = pm = None
    for i in range(1, len(freq)):
        if mag[i - 1] > 1 >= mag[i]:
            ugf = float(freq[i])
            pm = float(180 + ph[i])
            break
    return ugf, pm


def tran_settle_from_raw(rawpath: Path):
    """建立时间对照口径（parse_r5.settle_us 带外最后出带法，band=71µV，
    阶跃起点 t=1µs 后计）——与 .meas crossing 口径互为交叉校验。"""
    import numpy as np
    sys.path.insert(0, PARSE_R5_DIR)
    import parse_r5
    r = parse_r5.Raw(str(rawpath))
    t = np.array([v.real if isinstance(v, complex) else v for v in r.cols[0]], dtype=float)
    # LTspice 将 .save V(pa1,na1) 存为两个单端变量（实测 raw 变量表 ['time','V(fna)','V(fpa)','V(na1)','V(pa1)']）
    d = np.array(r.col("V(pa1)"), dtype=float) - np.array(r.col("V(na1)"), dtype=float)
    m = t >= 1.01e-6                       # 阶跃沿结束点
    tt, dd = t[m], d[m]
    vf = float(dd[-1])
    err = np.abs(dd - vf)
    band = 71e-6
    outside = np.where(err > band)[0]
    if len(outside) == 0:
        return 0.0, vf
    k = outside[-1]
    if k >= len(tt) - 1:
        return float("inf"), vf
    t0, t1, e0, e1 = tt[k], tt[k + 1], err[k], err[k + 1]
    tc = t0 + (t1 - t0) * (e0 - band) / (e0 - e1) if e0 != e1 else t1
    return float((tc - 1.01e-6) * 1e6), vf


# ======================================================================
# 5. T00 回归主流程
# ======================================================================
def run_t00() -> int:
    LOGD.mkdir(exist_ok=True)
    RAWD.mkdir(exist_ok=True)
    CSVD.mkdir(exist_ok=True)
    p0 = CASES[REG_CASE]
    stems = {k: f"t00_{REG_CASE.lower()}_{k}" for k in T00_GEN}
    timeouts = {"acdm": 300, "accm": 300, "loop": 300, "tran": 600, "tran2": 600}

    results, notes = {}, []
    for kind in T00_GEN:
        net = NET / f"{stems[kind]}.net"
        ok, out = run_net(net, timeout=timeouts[kind])
        log = net.with_suffix(".log")
        raw = net.with_suffix(".raw")
        print(f"[t00] {kind}: run ok={ok}")
        if out.startswith("NOTE"):
            notes.append(f"{kind}: {out}")
        if not ok or not log.exists() or not raw.exists():
            notes.append(f"{kind}: RUN FAILED rc-out={out[:300]}")
            results[kind] = None
            continue
        # 产物归档：logs/ raw/（.net 同名留 netlists/，均 gitignore，靠脚本再生）
        shutil.copy2(log, LOGD / f"{stems[kind]}.log")
        shutil.copy2(raw, RAWD / f"{stems[kind]}.raw")
        results[kind] = {"meas": parse_meas_log(log)}

    # ---- 指标提取（.meas AC mag() 输出即 dB 元组，直接取 dB 值；raw 插值交叉校验）----
    row_seed = []

    m = (results.get("acdm") or {}).get("meas", {})
    r_acdm = RAWD / f"{stems['acdm']}.raw"
    if m:
        d1 = m.get("dm_fmod", {}).get("val", float("nan"))
        d3 = m.get("dm_mclk", {}).get("val", float("nan"))
        d4 = -(m.get("dm_16k", {}).get("val", float("nan"))
               - m.get("dm_dc", {}).get("val", float("nan")))
        cross = {}
        if r_acdm.exists():
            pv, nv = ["V(pa1)"], ["V(na1)"]
            cross["D1"] = interp_mag_db(r_acdm, pv + nv, FMOD)
            cross["D3"] = interp_mag_db(r_acdm, pv + nv, MCLK)
            g16 = interp_mag_db(r_acdm, pv + nv, 16e3)
            gdc = interp_mag_db(r_acdm, pv + nv, 0.1)
            cross["D4"] = -(g16 - gdc)
        row_seed += [
            ("D1_db", d1, cross.get("D1"), "dB", 2.0,
             "acdm .meas dm_fmod（mag(V(pa1,na1))@4.096MHz，LTspice 输出即 dB）"),
            ("D3_db", d3, cross.get("D3"), "dB", 2.0,
             "acdm .meas dm_mclk（@16.384MHz）"),
            ("D4_db", d4, cross.get("D4"), "dB", max(0.1, abs(ANCHORS['D4_db']) * 0.1),
             "acdm .meas：16kHz 相对 DC 衰减 = -(dm_16k−dm_dc)"),
        ]

    m = (results.get("accm") or {}).get("meas", {})
    if m:
        d2 = m.get("cm_fmod", {}).get("val", float("nan"))
        cross = interp_mag_db(RAWD / f"{stems['accm']}.raw", ["V(pa1)"], FMOD) \
            if (RAWD / f"{stems['accm']}.raw").exists() else None
        row_seed.append(
            ("D2_db", d2, cross, "dB", 2.0,
             "accm .meas cm_fmod（mag(V(pa1))@4.096MHz，共模 0.5V 激励绝对 dB）"))

    # ---- 建立：主口径 = raw 带外最后出带法（终值 ±71µV，阶跃沿 1.01µs 后计）。
    #      gen_fo.py 原 ts01 .meas（=0.709929 RISE）在两种极性下均物理不可达：
    #      DC 分压 0.999278 → 真终值 0.709487 V > 0.71−71µV=0.709929，crossing 永不触发
    #      （本机实测无 ts01 输出）→ 旧报告 ≈21µs 不可能出自该 meas，产生口径不可考证；
    #      tran(−0.71→0) 与 tran2(0→+0.71) 互为 LTI 镜像，出带法结果应一致（交叉校验）。 ----
    raw_tran2 = RAWD / f"{stems['tran2']}.raw"
    raw_tran = RAWD / f"{stems['tran']}.raw"
    if raw_tran.exists():
        ts_us, vf = tran_settle_from_raw(raw_tran)
        ts2_us, vf2 = (tran_settle_from_raw(raw_tran2)
                       if raw_tran2.exists() else (None, None))
        row_seed.append(
            ("settle_us", ts_us, ts2_us, "µs",
             max(0.5, abs(ANCHORS['settle_us']) * 0.1),
             f"raw 带外出带法（vf={vf:.6f}V ±71µV）；镜像 tran2 出带法={ts2_us}µs；"
             f"锚定≈21µs 的原始产生口径不可考证（gen_fo ts01 meas 物理不可达）"))
        notes.append("tran/tran2：gen_fo.py 原 ts01 .meas（0.709929 RISE）物理不可达"
                     "（真终值 0.709487 < 阈值；本机 LTspice 26.1.1 实测无输出）——"
                     "旧 fo_results.json tran 空字段根因；21µs 锚定改以出带法口径对照")

    raw_loop = RAWD / f"{stems['loop']}.raw"
    if raw_loop.exists():
        ugf, pm = loop_pm_ugf(raw_loop)
        if pm is not None:
            row_seed.append(
                ("pm_deg", pm, None, "deg", abs(ANCHORS['pm_deg']) * 0.1,
                 f"T=-V(fpa)/V(inn) mag 跨 1 处 pm=180+ph（gen_fo.py 同口径），UGF={ugf/1e3:.1f}kHz"))

    # ---- 与锚定值对拍（2dB / 10%，超差必须排查口径不得写复现成功）----
    rows = []
    any_fail = False
    for name, val, cross, unit, tol, method in row_seed:
        anchor = ANCHORS[name]
        if val is None or (isinstance(val, float) and math.isnan(val)):
            rows.append(dict(item=name, anchor=anchor, this_run="NOT VERIFIED",
                             diff="", within_tol="N/A", unit=unit, tolerance=tol,
                             raw_crosscheck="", method=method))
            any_fail = True
            continue
        diff = val - anchor
        rel_ok = abs(diff) <= tol
        any_fail |= not rel_ok
        rows.append(dict(item=name, anchor=anchor, this_run=round(val, 4),
                         diff=round(diff, 4),
                         within_tol="yes" if rel_ok else "NO",
                         unit=unit, tolerance=round(tol, 4),
                         raw_crosscheck=(round(cross, 4)
                                         if isinstance(cross, float) else (cross or "")),
                         method=method))

    # 辅助行：环境与文件指纹（任务书 T00 要求：LTspice 版本/模型哈希/网表路径）
    env_lines = [
        dict(item="ltspice_version", anchor="", this_run="26.1.1 (ltspice-sim status)",
             diff="", within_tol="", unit="", tolerance="", raw_crosscheck="",
             method="~/.local/bin/ltspice-sim status 实测"),
        dict(item="opax388_md5", anchor="", this_run="97c4045ef608097ec1f1a67dca97ceae",
             diff="", within_tol="", unit="", tolerance="", raw_crosscheck="",
             method="md5sum OPAx388.LIB（fs_subs.inc:5 注记一致）"),
        dict(item="netlist_dir", anchor="", this_run="hardware/sim/signalchain/fo1_rc_review/netlists/",
             diff="", within_tol="", unit="", tolerance="", raw_crosscheck="",
             method="本脚本 gen 生成（.net gitignore 不入库，可再生）"),
    ]

    out_csv = CSVD / "t00_regression.csv"
    with out_csv.open("w", newline="\n", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=[
            "item", "anchor", "this_run", "diff", "within_tol", "unit",
            "tolerance", "raw_crosscheck", "method"])
        w.writeheader()
        for r in rows:
            w.writerow(r)
        for r in env_lines:
            w.writerow(r)
        for i, n in enumerate(notes, 1):
            w.writerow(dict(item=f"note_{i}", anchor="", this_run=n, diff="",
                            within_tol="", unit="", tolerance="",
                            raw_crosscheck="", method="口径排查记录"))
    print(f"[t00] csv -> {out_csv}")
    for r in rows:
        print(f"      {r['item']:10s} anchor={r['anchor']} this={r['this_run']} "
              f"diff={r['diff']} within_tol={r['within_tol']}")
    if notes:
        print("[t00] 说明/异常：", *notes, sep="\n  ")
    hard_fail = any("RUN FAILED" in n or "TIMEOUT" in n for n in notes)
    verdict = "NOT VERIFIED" if not rows else \
              ("DEVIATION-INVESTIGATE" if (any_fail or hard_fail) else
               "REPRODUCED (settle 口径换 raw 出带法，见 notes)")
    print(f"[t00] verdict: {verdict}")
    return 0


# ======================================================================
# 6. 静态 lint（不执行仿真）：include 存在性 / 器件名查重 / X 子电路名核对
# ======================================================================
KNOWN_SUBCKT = {s.lower() for s in
                ("dut", "fsrc", "fsfo", "fsadc", "OPAx388", "opa333t", "opa333m",
                 "opa388t", "opa391t3")}   # swNO/swsh 是 .model；子电路体内的 X 同样登记


def lint_netlist(net: Path) -> list[str]:
    errs = []
    lines = net.read_text(errors="replace").splitlines()
    names, depth = set(), 0
    for ln in lines:
        s = ln.split("*", 1)[0].strip()          # 去注释
        if not s or s.startswith((".", ";")):
            if s.lower().startswith(".include"):
                tgt = s.split(None, 1)[1].strip()
                if not Path(tgt).exists():
                    errs.append(f"{net.name}: include 目标不存在: {tgt}")
            if s.lower().startswith(".subckt"):
                depth += 1
            elif s.lower().startswith(".ends"):
                depth = max(0, depth - 1)
            continue
        if s.lower().startswith(".subckt"):
            depth += 1
            continue
        if s.lower().startswith(".ends"):
            depth = max(0, depth - 1)
            continue
        tok = s.split()[0]
        if tok.startswith("X"):
            subname = s.split()[-1].lower()
            if subname not in KNOWN_SUBCKT:
                errs.append(f"{net.name}: X 实例子电路名未登记: {s.split()[-1]}")
        elif tok[0] in "RCVLBESIHFQTGKOZUDMJ" and depth == 0:
            # 器件名查重仅顶层作用域（.subckt 体内是局部名，跨子电路同名合法）
            key = tok.lower()
            if key in names:
                errs.append(f"{net.name}: 顶层器件名重复(LTspice 大小写不敏感): {tok}")
            names.add(key)
    return errs


def cmd_lint() -> int:
    bad = 0
    for f in sorted(NET.glob("*.net")) + [HERE / "fo_subs.inc"]:
        errs = lint_netlist(f)
        print(f"[lint] {f.name}: {'OK' if not errs else errs}")
        bad += len(errs)
    return 1 if bad else 0


# ======================================================================
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("cmd", nargs="?", default="all",
                    choices=["gen", "t00", "lint", "all"])
    args = ap.parse_args()
    if args.cmd in ("gen", "t00", "lint", "all"):  # t00/lint 也先生成（网表缺失自动补）
        for f in gen_all():
            print(f"[gen] {f}")
    if args.cmd == "lint":
        return cmd_lint()
    if args.cmd in ("t00", "all"):
        return run_t00()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
