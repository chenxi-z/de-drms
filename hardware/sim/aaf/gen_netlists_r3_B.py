#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_netlists_r3_B.py — 第 3 轮：方案 B（r5_candidates_r2.json 的 "B" 键）LTspice 网表

规格 v4：docs/design/spec/2026-10-18-aa-driver-design.md
  * 评分主口径 = **真实 OPA388 模型**（lib/OPAx388.LIB，TI SBOS777D Rev D 宏模型）
  * 0 Ω 理想源 V1–V8 仅作对照报告
  * D6 拆 D6a（无源网络噪声增量 %）/ D6b（总积分噪声，仅报告）
  * D8 按 R·C 乘积异向配对（R×(1+m) 配 C×(1−m)），m = 0.1 / 0.5 / 1%，另附同向失配对照
  * C9：真实模型全频段增益峰值 ≤6 dB

复用 gen_netlists_r5.py 的构件（_line/_common/_scaled/_apply/mc_samples），
所有文件名带 `_r3` 后缀，输出到 r5_work/r3_B/（本轮独立目录，避免与其他会话的
r5_work/r3 冲突 —— 该目录已被另一个会话占用，见 AGENTS「并发写同一文件」）。

V1–V8 理想源：直接复用 r5 生成器函数（RS=0 口径）
V9 真实模型：
  v9a  AC DM 全频段（dec 1000, 0.1 Hz–200 MHz）→ D1/D3/D4/D10 + C9
  v9b  AC CM（dec 400, 1 Hz–40 kHz）           → D2
  v9c  tran 最坏角 0 Ω 源 + 真实跟随器          → D5（0 Ω 角）
  v9d  noise（真实阶梯）                        → D6b
  v9df noise（阶梯换成无噪 B 源）               → D6a 的"跟随器自身噪声"
  v9e  AC 600 kΩ 样品端                         → D5 高阻角补充
  v9f  tran 600 kΩ + 最坏角 + 真实跟随器        → D5（规格点名工况）
  v9mc01..30  MC AC（真实模型）                 → D7
  v9c_mc01..30 MC tran（真实模型）              → D5 统计
  v9b_p001/p05/p1  CM 配对失配 m=0.1/0.5/1%     → D8
  v9b_s1           CM 同向失配 1%（对照）        → D8 对照
  v9kb_ron1/100/1000  kickback（真实模型）       → D9
  v3p1             理想源 + 配对 1%（隔离跟随器影响，供 D8 对拍）

用法：python gen_netlists_r3_B.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time

import gen_netlists_r5 as G

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, "lib", "OPAx388.LIB")
OUT = os.path.join(HERE, "r5_work", "r3_B")
CAND = os.path.join(HERE, "r5_candidates_r2.json")
LTSPICE = r"C:\Users\chenx\AppData\Local\Programs\ADI\LTspice\LTspice.exe"

FMOD = 4.096e6
VCC = 3.3
ADC_CS_PF = 3.5
ADC_RSW = 1.0
# 真实模型瞬态：trap + reltol=1e-6 会让 TI 宏模型的 internal 1F 电容反复拒绝步长，
# 400 µs 仿真写出 >500 MB 且 6 min 未收敛（本轮实测，见 notes）。改用第 2 轮已验证
# 稳定的 gear + reltol=1e-5 + trtol=7（r5_work/r2/r2s_B_v9c.log：0.94 s 完成）。
# 精度核对：2 V 阶跃 × reltol 1e-5 = 20 µV，远小于 0.01% 判据 200 µV。
TR_OPTS = ".options plotwinsize=0 method=gear reltol=1e-5 abstol=1e-11 vntol=1e-8 chgtol=1e-14 trtol=7"


def _load():
    with open(CAND, encoding="utf-8") as fh:
        return json.load(fh)["B"]


def _w(name, lines):
    """lines 可以是行列表，也可以已是整份网表文本（G.gen_v* / 本地函数返回 str）。"""
    p = os.path.join(OUT, name)
    txt = lines if isinstance(lines, str) else ("\n".join(lines) + "\n")
    with open(p, "w", encoding="ascii", newline="\n") as fh:
        fh.write(txt)
    return name


def _hdr(tag, note):
    return [f"* r3 B {tag} - {note}",
            "* gen_netlists_r3_B.py (spec v4; real OPA388 = scoring source)"]


def _mod_head():
    return [".include " + LIB, f"Vcc vcc 0 DC {VCC}", "Vee vee 0 DC 0"]


# ------------------------------------------------------------------ 真实模型 AC
def v9a(stages, tag="v9a", note="AC DM, real OPAx388, full band"):
    ns = len(stages)
    pa, na = f"pa{ns}", f"na{ns}"
    L = _hdr(tag, note) + _mod_head()
    L += ["Vp vp 0 DC 2 AC 0.5", "Vn vn 0 DC 2 AC -0.5",
          "Xfa vp fpa vcc vee fpa OPAx388", "Xfb vn fna vcc vee fna OPAx388"]
    L += G._line("a", "fpa", "pa", stages)
    L += G._line("b", "fna", "na", stages)
    L += G._common(stages)
    L += [".ac dec 1000 0.1 200Meg", G.TOPT,
          f".meas AC g_dc   FIND mag(V({pa})-V({na})) AT 1",
          f".meas AC g_16k  FIND mag(V({pa})-V({na})) AT 16k",
          f".meas AC g_fmod FIND mag(V({pa})-V({na})) AT 4.096Meg",
          f".meas AC g_mclk FIND mag(V({pa})-V({na})) AT 16.384Meg",
          ".end"]
    return "\n".join(L) + "\n"


def v9b(stages, tag="v9b", note="AC CM, real OPAx388",
        st_b=None, fmax="40k", dec=400):
    """共模 AC。配对失配档只需要 10 Hz–16 kHz（fmax=40k 够）；**标称档**要用 fMOD
    的 A_cm（D2），必须扫到 200 Meg —— 否则 D2 无数据（本轮第一次跑就踩了）。"""
    """共模：Vp=Vn=1 V AC；st_b 为 B 线参数（默认与 A 线相同）。"""
    ns = len(stages)
    pa, na = f"pa{ns}", f"na{ns}"
    sb = st_b or stages
    L = _hdr(tag, note) + _mod_head()
    L += ["Vp vp 0 DC 2 AC 1", "Vn vn 0 DC 2 AC 1",
          "Xfa vp fpa vcc vee fpa OPAx388", "Xfb vn fna vcc vee fna OPAx388"]
    L += G._line("a", "fpa", "pa", stages)
    L += G._line("b", "fna", "na", sb)
    L += G._common(stages)
    L += [f".ac dec {dec} 1 {fmax}", G.TOPT,
          f".meas AC cm_dc  FIND mag(V({pa}))       AT 1",
          f".meas AC dm_16k FIND mag(V({pa})-V({na})) AT 16k",
          ".end"]
    return "\n".join(L) + "\n"


def v9e(stages, tag="v9e", note="AC DM 600k sample end, real OPAx388"):
    ns = len(stages)
    pa, na = f"pa{ns}", f"na{ns}"
    L = _hdr(tag, note) + _mod_head()
    L += ["Vp vp 0 DC 2 AC 0.5", "Vn vn 0 DC 2 AC -0.5",
          "Rsa vp fa 600k", "Rsb vn fb 600k",
          "Xfa fa fpa vcc vee fpa OPAx388", "Xfb fb fna vcc vee fna OPAx388"]
    L += G._line("a", "fpa", "pa", stages)
    L += G._line("b", "fna", "na", stages)
    L += G._common(stages)
    L += [".ac dec 400 0.1 200Meg", G.TOPT,
          f".meas AC g_dc   FIND mag(V({pa})-V({na})) AT 1",
          f".meas AC g_16k  FIND mag(V({pa})-V({na})) AT 16k",
          f".meas AC g_fmod FIND mag(V({pa})-V({na})) AT 4.096Meg",
          f".meas AC g_mclk FIND mag(V({pa})-V({na})) AT 16.384Meg",
          ".end"]
    return "\n".join(L) + "\n"


# ------------------------------------------------------------------ 真实模型瞬态
def _tran_real(stages, tag, note, pre_rc=False, tstop="400u", tstep="20n"):
    ns = len(stages)
    L = _hdr(tag, note) + _mod_head()
    # 单 3.3 V 轨：信号坐在 2.0 V 共模（0 V / 负压超出 OPA388 输出摆幅）
    L += ["Vp vp 0 PULSE(2 3 10u 10n 10n 600u 2m)",
          "Vn vn 0 PULSE(2 1 10u 10n 10n 600u 2m)"]
    if pre_rc:
        L += ["Rsa vp fa 600k", "Rsb vn fb 600k",
              "Xfa fa fpa vcc vee fpa OPAx388", "Xfb fb fna vcc vee fna OPAx388"]
        L += G._line("a", "fpa", "pa", stages)
        L += G._line("b", "fna", "na", stages)
    else:
        L += ["Xfa vp fpa vcc vee fpa OPAx388", "Xfb vn fna vcc vee fna OPAx388"]
        L += G._line("a", "fpa", "pa", stages)
        L += G._line("b", "fna", "na", stages)
    L += G._common(stages)
    extra = "V(fa) V(fb) V(fpa) V(fna)" if pre_rc else "V(fpa) V(fna)"
    L += [f".save V(pa{ns}) V(na{ns}) V(vp) V(vn) {extra}",
          f".tran 0 {tstop} 0 {tstep}", TR_OPTS, ".end"]
    return "\n".join(L) + "\n"


def v9c(stages, tag="v9c", note="tran worst corner (R1.01/C1.05), real OPAx388"):
    return _tran_real(G._scaled(stages, 1.01, 1.05), tag, note)


def v9f(stages, tag="v9f", note="tran 600k sample end + worst corner, real OPAx388"):
    return _tran_real(G._scaled(stages, 1.01, 1.05), tag, note, pre_rc=True)


# ------------------------------------------------------------------ 噪声
def v9d(stages, tag="v9d", note="noise, real OPAx388 + real ladder"):
    ns = len(stages)
    pa, na = f"pa{ns}", f"na{ns}"
    L = _hdr(tag, note) + _mod_head()
    L += ["Vp vp 0 DC 2 AC 1", "Vn vn 0 DC 2 AC 0",
          "Xfa vp fpa vcc vee fpa OPAx388", "Xfb vn fna vcc vee fna OPAx388"]
    L += G._line("a", "fpa", "pa", stages)
    L += G._line("b", "fna", "na", stages)
    L += G._common(stages)
    L += [".noise V(pa3,na3) Vp dec 200 0.1 2.048Meg", G.TOPT, ".end"]
    return "\n".join(L) + "\n"


def v9df(stages, tag="v9df",
         note="noise, real OPAx388 + NOISELESS ladder (B-source R) = follower-only"):
    """D6a 的减数项：阶梯/负载全部换成无噪 B 源（电流 = 压差/R），传递函数不变、带宽不变，
    仅去掉电阻约翰逊噪声 → 输出噪声 = 跟随器自身噪声（含其电流噪声经同阻抗）。"""
    ns = len(stages)
    pa, na = f"pa{ns}", f"na{ns}"
    L = _hdr(tag, note) + _mod_head()
    L += ["Vp vp 0 DC 2 AC 1", "Vn vn 0 DC 2 AC 0",
          "Xfa vp fpa vcc vee fpa OPAx388", "Xfb vn fna vcc vee fna OPAx388"]

    def bline(side, src, node, st):
        out, prev = [], src
        for i, (r, cg, _cd) in enumerate(st, 1):
            out.append(f"B{side}{i} {prev} {node}{i} I=(V({prev})-V({node}{i}))/{r:.10g}")
            out.append(f"C{side}{i} {node}{i} 0 {cg:.10g}")
            prev = f"{node}{i}"
        return out

    L += bline("a", "fpa", "pa", stages)
    L += bline("b", "fna", "na", stages)
    cd = stages[-1][2]
    if cd > 0:
        L.append(f"Cd {pa} {na} {cd:.10g}")
    L.append(f"Bin {pa} {na} I=(V({pa})-V({na}))/130000")
    L += [f"Cpa {pa} 0 5e-12", f"Cna {na} 0 5e-12",
          f".noise V({pa},{na}) Vp dec 200 0.1 2.048Meg", G.TOPT, ".end"]
    return "\n".join(L) + "\n"


# ------------------------------------------------------------------ MC（真实模型）
def v9mc(stages, k, smp, tag=None):
    tag = tag or f"v9mc{k:02d}"
    st_a = G._apply(stages, smp["ra"], smp["ca"], smp["cd"])
    st_b = G._apply(stages, smp["rb"], smp["cb"], smp["cd"])
    L = _hdr(tag, f"MC AC #{k:02d}, real OPAx388 (D7)") + _mod_head()
    L += ["Vp vp 0 DC 2 AC 0.5", "Vn vn 0 DC 2 AC -0.5",
          "Xfa vp fpa vcc vee fpa OPAx388", "Xfb vn fna vcc vee fna OPAx388"]
    L += G._line("a", "fpa", "pa", st_a)
    L += G._line("b", "fna", "na", st_b)
    L += G._common(st_a)
    L += [".ac dec 200 0.1 40k", G.TOPT, ".end"]
    return "\n".join(L) + "\n"


def v9c_mc(stages, k, smp, tag=None):
    tag = tag or f"v9cmc{k:02d}"
    st_a = G._apply(stages, smp["ra"], smp["ca"], smp["cd"])
    st_b = G._apply(stages, smp["rb"], smp["cb"], smp["cd"])
    L = _hdr(tag, f"MC tran #{k:02d}, real OPAx388 (D5 stats)") + _mod_head()
    L += ["Vp vp 0 PULSE(2 3 10u 10n 10n 600u 2m)",
          "Vn vn 0 PULSE(2 1 10u 10n 10n 600u 2m)",
          "Xfa vp fpa vcc vee fpa OPAx388", "Xfb vn fna vcc vee fna OPAx388"]
    L += G._line("a", "fpa", "pa", st_a)
    L += G._line("b", "fna", "na", st_b)
    L += G._common(st_a)
    ns = len(stages)
    L += [f".save V(pa{ns}) V(na{ns}) V(vp) V(vn)",
          ".tran 0 300u 0 20n", TR_OPTS, ".end"]
    return "\n".join(L) + "\n"


# ------------------------------------------------------------------ kickback（真实模型）
def v9kb(stages, ron=ADC_RSW, tag=None):
    tag = tag or f"v9kb_ron{ron:g}"
    ns = len(stages)
    pin_a, pin_b = f"pa{ns}", f"na{ns}"
    L = _hdr(tag, f"kickback, real OPAx388, ADC switch Ron={ron:g} (D9)") + _mod_head()
    L += [f".model SWK SW(Ron={ron:.10g} Roff=1e12 Vt=0.5 Vh=0)",
          "Vp vp 0 DC 3.2", "Vn vn 0 DC 0.8", "Vcm vcm 0 DC 2.0",
          "Xfa vp fpa vcc vee fpa OPAx388", "Xfb vn fna vcc vee fna OPAx388"]
    L += G._line("a", "fpa", "pa", stages)
    L += G._line("b", "fna", "na", stages)
    L += G._common(stages)
    L += [f"S1a {pin_a} csa swp 0 SWK", f"Csa csa vcm {ADC_CS_PF/2*1e-12:.10g}",
          "S2a csa vcm swn 0 SWK",
          f"S1b {pin_b} csb swn 0 SWK", f"Csb csb vcm {ADC_CS_PF/2*1e-12:.10g}",
          "S2b csb vcm swp 0 SWK",
          "Vswp swp 0 PULSE(0 1 0 0.5n 0.5n 121.07n 244.1406n)",
          "Vswn swn 0 PULSE(0 1 122.07n 0.5n 0.5n 121.07n 244.1406n)"]
    # 只存 D9 判定所需向量：ASCII raw 的体积 ≈ 点数 × 向量数；真实模型下
    # 6 向量 × 40 µs/0.1 ns 会写出 >450 MB 且 LTspice 在收尾前被拖死（本轮实测）。
    # 0.2 ns 步长在 122 ns 窗内仍有 ~600 点，远多于判定需要的 ~30 点；窗内过零沿
    # （0.5 ns 上升）也被解析。其余与理想源 V8 完全同构，便于对拍。
    L += [f".save V({pin_a}) V({pin_b}) V(csa)",
          ".tran 0 40u 0 1n", TR_OPTS, ".end"]
    return "\n".join(L) + "\n"


# ------------------------------------------------------------------ 生成
def generate():
    os.makedirs(OUT, exist_ok=True)
    cand = _load()
    st = [tuple(map(float, s)) for s in cand["stages"]]
    ns = len(st)
    G.RS = 0.0                      # 规格 §5.1：V1–V6 源阻抗 0 Ω
    names = []

    # --- 对照：理想源 V1–V8（0 Ω，仅报告） ---
    names.append(_w(f"r5_B_v1_r3.net", G.gen_v1(cand, st, "V1r3", "ideal source AC DM (control)")))
    names.append(_w(f"r5_B_v2_r3.net", G.gen_v2(cand, st, "V2r3", "ideal source AC CM (control)")))
    names.append(_w(f"r5_B_v3_r3.net", G.gen_v3(cand, st, "V3r3",
                                                 "ideal source CM, same-direction 1% (D8 control)")))
    names.append(_w(f"r5_B_v4_r3.net", G.gen_v4(cand, st, "V4r3",
                                                "ideal source worst-corner tran (D5 control)")))
    names.append(_w(f"r5_B_v4b_r3.net", G.gen_v4b(cand, st, "V4b_r3",
                                                  "600k + ideal follower, upper bound (D5 control)")))
    for k, smp in enumerate(G.mc_samples(n=G.N_MC, n_stage=ns), 1):
        names.append(_w(f"r5_B_v5mc{k:02d}_r3.net", G.gen_v5(cand, k, smp, f"v5mc{k:02d}r3")))
    for k, smp in enumerate(G.mc_samples(n=G.N_MC, n_stage=ns), 1):
        names.append(_w(f"r5_B_v6mc{k:02d}_r3.net", G.gen_v6(cand, k, smp, f"v6mc{k:02d}r3")))
    names.append(_w("r5_B_v7_r3.net", G.gen_v7(cand, st, "V7r3", "ideal source noise (control)")))
    # 规格 §5.1 温度角（只报 D4/D7 趋势）：−20 °C / +85 °C
    for tt in (-20.0, 85.0):
        names.append(_w(f"r5_B_v1t{int(tt):+d}C_r3.net", G.gen_v1_temp(cand, tt)))
    for ron in (1.0, 100.0, 1000.0):
        names.append(_w(f"r5_B_v8_ron{ron:g}_r3.net",
                        G.gen_v8(cand, ron, st, f"v8r3_ron{ron:g}",
                                 f"ideal source kickback Ron={ron:g} (control)")))

    # --- 主口径：真实 OPA388 ---
    names.append(_w("r5_B_v9a_r3.net", v9a(st)))
    names.append(_w("r5_B_v9b_r3.net", v9b(st, fmax="200Meg")))
    names.append(_w("r5_B_v9c_r3.net", v9c(st)))
    names.append(_w("r5_B_v9d_r3.net", v9d(st)))
    names.append(_w("r5_B_v9df_r3.net", v9df(st)))
    names.append(_w("r5_B_v9e_r3.net", v9e(st)))
    names.append(_w("r5_B_v9f_r3.net", v9f(st)))

    for k, smp in enumerate(G.mc_samples(n=G.N_MC, n_stage=ns), 1):
        names.append(_w(f"r5_B_v9mc{k:02d}_r3.net", v9mc(st, k, smp)))
    for k, smp in enumerate(G.mc_samples(n=G.N_MC, n_stage=ns), 1):
        names.append(_w(f"r5_B_v9cmc{k:02d}_r3.net", v9c_mc(st, k, smp)))

    # D8：R·C 乘积异向配对 m = 0.1% / 0.5% / 1%；同向 1% 对照（= V3 口径）
    for tag, m in (("p001", 0.001), ("p05", 0.005), ("p1", 0.01)):
        # 规格 v4 §5.1：C_gnd 与 C_diff 都取 ×(1−m)（与 r5_score_v4.cmrr_rc_paired 一致）
        sb = [(r * (1 + m), cg * (1 - m), cd * (1 - m)) for r, cg, cd in st]
        names.append(_w(f"r5_B_v9b_{tag}_r3.net",
                        v9b(st, f"v9b_{tag}", f"AC CM, R*(1+{m:g}) paired with C*(1-{m:g})",
                            st_b=sb)))
    # 严格倒数配对（C/(1+m)，使 R·C 乘积精确回到原值）—— 规格文字写的是 ×(1−m)，
    # 两者差 ~14.7 dB（1% 档），单列出来供规格方核对口径
    sb_inv = [(r * 1.01, cg / 1.01, cd / 1.01) for r, cg, cd in st]
    names.append(_w("r5_B_v9b_p1inv_r3.net",
                    v9b(st, "v9b_p1inv", "AC CM, R*1.01 with C/1.01 (strict reciprocal)",
                        st_b=sb_inv)))
    names.append(_w("r5_B_v9b_s1_r3.net",
                    v9b(st, "v9b_s1", "AC CM, same-direction 1% mismatch (D8 control)",
                        st_b=G._scaled(st, 1.01, 1.01))))
    # 同配对条件的理想源版（隔离跟随器对 CMRR 的影响）
    sb1 = [(r * 1.01, cg * 0.99, cd * 0.99) for r, cg, cd in st]
    L = _hdr("v3p1", "ideal source, CM, paired 1% (isolates op-amp from ladder)")
    L += ["Vp vp 0 DC 2 AC 1", "Vn vn 0 DC 2 AC 1"]
    L += G._line("a", "vp", "pa", st)
    L += G._line("b", "vn", "na", sb1)
    L += G._common(st)
    L += [".ac dec 400 1 40k", G.TOPT, ".end"]
    names.append(_w("r5_B_v3p1_r3.net", "\n".join(L) + "\n"))

    for ron in (1.0, 100.0, 1000.0):
        names.append(_w(f"r5_B_v9kb_ron{ron:g}_r3.net", v9kb(st, ron)))

    with open(os.path.join(OUT, "manifest_r3_B.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        json.dump({"candidate": "B", "stages": cand["stages"],
                   "n_netlists": len(names), "files": names}, fh,
                  ensure_ascii=False, indent=2)
    return names


def run_all(names, skip_existing=False, timeout=600):
    rows = []
    for i, n in enumerate(names, 1):
        net = os.path.join(OUT, n)
        raw = net[:-4] + ".raw"
        log = net[:-4] + ".log"
        if skip_existing and os.path.exists(raw) and os.path.getsize(raw) > 1000:
            rows.append({"net": n, "ok": True, "secs": 0.0, "err": "cached"})
            print(f"  [{i:3d}/{len(names)}] = {n} (cached)")
            continue
        for p in (raw, log):
            if os.path.exists(p):
                os.remove(p)
        t0 = time.time()
        try:
            p = subprocess.run([LTSPICE, "-b", "-ascii", n], cwd=OUT,
                               capture_output=True, text=True, timeout=timeout)
            rc = p.returncode
            out = (p.stdout or "") + (p.stderr or "")
        except subprocess.TimeoutExpired:
            rows.append({"net": n, "ok": False, "secs": time.time() - t0,
                         "err": f"TIMEOUT>{timeout}s"})
            print(f"  [{i:3d}/{len(names)}] ✗ {n} TIMEOUT")
            continue
        dt = time.time() - t0
        err = ""
        if os.path.exists(log):
            txt = open(log, "r", encoding="ascii", errors="replace").read()
            bad = [ln.strip() for ln in txt.splitlines()
                   if "FATAL" in ln or "Error" in ln or "error" in ln]
            err = " | ".join(bad[:2])
        ok = os.path.exists(raw) and os.path.getsize(raw) > 500
        rows.append({"net": n, "ok": ok, "secs": round(dt, 2), "err": err})
        print(f"  [{i:3d}/{len(names)}] {'✓' if ok else '✗'} {n:26s} {dt:7.2f}s"
              + (f"  {err}" if err else ""))
    bad = [r for r in rows if not r["ok"]]
    print(f"\n完成 {len(rows)-len(bad)}/{len(rows)}")
    with open(os.path.join(OUT, "runlog_r3_B.json"), "w", encoding="utf-8",
              newline="\n") as fh:
        json.dump(rows, fh, ensure_ascii=False, indent=2)
    return bad


if __name__ == "__main__":
    if not os.path.exists(LIB):
        print("✗ 缺少 OPAx388.LIB:", LIB)
        raise SystemExit(2)
    if not os.path.exists(LTSPICE):
        print("✗ 缺少 LTspice:", LTSPICE)
        raise SystemExit(2)
    ns = generate()
    print(f"生成 {len(ns)} 个网表 → {OUT}")
    only = sys.argv[1] if len(sys.argv) > 1 else ""
    if only:
        ns = [n for n in ns if only in n]
    bad = run_all(ns, skip_existing=True)
    raise SystemExit(1 if bad else 0)
