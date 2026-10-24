#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""run_stab.py — fo1_rc_review 测试族 stab：T05 噪声 + T07 真实 OPA388 环路稳定性（四方案）

任务书（hardware/sim/Zcode_LTspice_一阶RC四方案复核任务书.md）§3/§4：
  T05 噪声   .noise 带内/宽带、RC 增量（D6a）、与 OPA388/ADC 噪声区分（逐器件归属）
  T07 稳定性 真实 OPA388 环路：PM（断环方式/注入点声明）、全频闭环 peaking（C9≤6dB）、瞬态过冲

铁律（任务书 §1「特别核对」）：真实接线 = 3 颗 OPA388（T/M/B 三线）+ AIN1N 经 RC
直连 Rsense 底端 E（Kelvin 地，无第四颗运放）。本脚本网表按通道拆分考核：
  CH0 = a0p/a0n（T、M 两线各有 OPA388 跟随器——真实接线本就对称）
  CH1 = a1p/na1（B 线 OPA388 跟随器 + na1 Kelvin RC 直连地，非对称，AIN1N 不当作运放）

口径来源（全部既有实测口径，逐条引用）：
  * D6a/D6b  = aaf/r5_results_r4_B.json D6_detail：D6a 线性公式 (V_tot−V_nl)/V_nl×100%
    （v9d 真实 RC vs v9d_nl 顶层 R 全 noiseless，两网表传函逐点一致）；D6b = 0.1Hz–
    2.048MHz(fMOD/2) 积分，仅报告；阈值 ≤10% 满分 / >30% 淘汰（spec 2026-10-18-aa-driver.md:75）
  * .noise 差分输出 = aaf/gen_netlists_r5.py:331 `​.noise V(pa,na) Vp dec …`（LTspice 支持）
  * 积分 = parse_r5.noise_nv 同法（log 网格 trapz，numpy2 用 trapezoid）
  * PM  = t00/gen_fo net_loop 口径：跟随器 β=1 输入参考断环（IN+ 注入 AC、IN− DC 偏置
    + AC 地），T=−V(fcc)/V(inn)，mag 跨 1 处 PM=180+ph；FO1_BASE 锚定 98.6°
    （run_all.py ANCHORS；t00 实测 98.568°）
  * C9  = 跟随器输出节点全频闭环增益峰值 ≤6dB（r4 口径，score_r5_r4.py:33
    「按跟随器输出节点考核」）；ADC 引脚节点峰值另报（副口径）
  * ADC 负载 = Rin 130k + C_pin 5p/端（断态口径，采样开关/C_S 不在噪声网表——
    aaf v7/v9d 同法）；kT/C_S 与 ADC 内部噪声不在 .noise，解析另注
  * CH1 直流偏置 = 真实工作点：B 点 1.2V（8µA×150k）、na1=0V（E=地）；
    CH0 共模 2V（t00/aaf 一贯口径）

依赖：~/.local/bin/ltspice-sim、hardware/sim/aaf/parse_r5.py、numpy、matplotlib。
产物：netlists/t05_* t07_*（gitignore 不入库，靠本脚本再生）、logs/、raw/、
       csv/t05_noise.csv、csv/t07_stability.csv、plots/t05_* t07_*。

用法：
  python3 run_stab.py gen     # 只生成网表
  python3 run_stab.py run     # 生成 + 全部实跑（顺序；ltspice-sim 自带文件锁）
  python3 run_stab.py parse   # 只解析已有 raw 出 CSV/图（不跑仿真）
  python3 run_stab.py all     # gen + run + parse
"""
from __future__ import annotations

import csv
import math
import shutil
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_all  # noqa: E402  台架共享：CASES/LIB/run_net/parse_r5 引入

from run_all import CASES, LIB, NET, LOGD, RAWD, CSVD, fmt, run_net  # noqa: E402

PLOTD = HERE / "plots"
sys.path.insert(0, run_all.PARSE_R5_DIR)
import parse_r5  # noqa: E402

FMOD = 4.096e6
FB_BROAD = 2.048e6          # fMOD/2（D6b 口径）
FB_INBAND = 16e3            # 测量通带上沿（D4 口径）
LSB_V = 2.0 * 2.442 / 2 ** 24   # 290.98 nV（parse_r5.py:32 同源）
C9_TH = 6.0                 # dB，spec C9
D6A_FULL, D6A_FAIL = 10.0, 30.0   # %，spec D6a

TOPT = (".options plotwinsize=0 reltol=1e-6 abstol=1e-12 vntol=1e-9 "
        "chgtol=1e-15 trtol=1")
HEAD = f".include {LIB}\nVcc vcc 0 DC 3.3\nVee vee 0 DC 0\n"


def _case_id(case: str) -> str:
    return case.lower()                     # fo1_base / fo1_a / fo1_b / fo1_c


# ======================================================================
# 1. 网表生成
# ======================================================================
def ch0_body(p: dict, nl: dict[str, bool]) -> str:
    """CH0 差分通道（T/M 双跟随器，真实接线本就对称）。
    nl: {'ra':…,'rb':…,'rin':…} → True 表示该电阻加 `noiseless`。"""
    a = " noiseless" if nl.get("ra") else ""
    b = " noiseless" if nl.get("rb") else ""
    c = " noiseless" if nl.get("rin") else ""
    return (f"Vp vp 0 DC 2 AC 1\nVn vn 0 DC 2 AC 0\n"
            f"XfT vp ftp vcc vee ftp OPAx388\nXfM vn ftm vcc vee ftm OPAx388\n"
            f"Ra1 ftp a0p {fmt(p['r'])}{a}\nCa1 a0p 0 {fmt(p['cg'])}\n"
            f"Rb1 ftm a0n {fmt(p['r'])}{b}\nCb1 a0n 0 {fmt(p['cg'])}\n"
            f"Cd a0p a0n {fmt(p['cd'])}\n"
            f"Rin a0p a0n 130000{c}\nCpa a0p 0 5p\nCna a0n 0 5p\n")


def ch1_body(p: dict, nl: dict[str, bool]) -> str:
    """CH1 差分通道（真实非对称接线）：B 线 OPA388 跟随器 → R/C_G → a1p；
    AIN1N=na1 经 RKN 直连地（E=Kelvin 地）+ CGN 对地，**无第四颗运放**。
    DC 工作点：B=1.2V（8µA×150k）、na1=0V。"""
    a = " noiseless" if nl.get("ra") else ""
    b = " noiseless" if nl.get("rkn") else ""
    c = " noiseless" if nl.get("rin") else ""
    return (f"Vb bin 0 DC 1.2 AC 1\n"
            f"XfB bin fbk vcc vee fbk OPAx388\n"
            f"Rf fbk a1p {fmt(p['r'])}{a}\nCg a1p 0 {fmt(p['cg'])}\n"
            f"Cd a1p na1 {fmt(p['cd'])}\n"
            f"RKN 0 na1 {fmt(p['r'])}{b}\nCGN na1 0 {fmt(p['cg'])}\n"
            f"Rin a1p na1 130000{c}\nCpa a1p 0 5p\nCna na1 0 5p\n")


def t05_noise(case: str, p: dict, ch: str, variant: str) -> str:
    """T05 .noise。variant: n1=全部电阻带噪（D6a 分子/D6b）；
    n3=顶层 R 全 noiseless（D6a 分母，r4 v9d_nl 口径；传函与 n1 逐点一致）。"""
    if variant == "n1":
        nl = {}
        note = "all resistors noisy (total = D6a numerator / D6b)"
    else:
        nl = {"ra": True, "rb": True, "rkn": True, "rin": True}
        note = "top-level R all `noiseless` (OPA388-only = D6a denominator, r4 v9d_nl)"
    body = ch0_body(p, nl) if ch == "ch0" else ch1_body(p, nl)
    pins = "a0p,a0n" if ch == "ch0" else "a1p,na1"
    src = "Vp" if ch == "ch0" else "Vb"
    obs = "V(a0p,a0n)" if ch == "ch0" else "V(a1p,na1)"
    return (f"* t05 {_case_id(case)} {ch} {variant} — noise, {note}\n"
            f"* {ch} wiring: " +
            ("T/M both OPA388 followers (real CH0 is symmetric)" if ch == "ch0"
             else "B OPA388 follower + AIN1N Kelvin RC direct (NO 4th opamp)") +
            f"; ADC load Rin130k+5p/side, switches OFF (static)\n"
            f"{HEAD}{body}"
            f".noise {obs} {src} dec 200 0.1 50Meg\n{TOPT}\n"
            f".save v(onoise) v(inoise)\n.end\n")


def t07_loop(case: str, p: dict, ch: str) -> str:
    """T07 环路增益。断环方式 = 输入参考断环（β=1 跟随器）：
    注入点 = 同相输入端（Vinn AC 1），反相端接 DC 偏置源（AC 地）→ 环路在输入处断开，
    T(f)=−V(fcc)/V(inn) 即 Aol(带真实负载)；PM=180+ph @|T|=1（gen_fo net_loop/t00 同口径）。
    ch0 = 差分半电路负载（R+C_G+2C_D 虚地+65k+5p，t00_loop 逐行同构）；
    ch1 = 真实全负载（C_D 跨到 na1，na1=RKN/CGN/5p 接地，Rin 130k 差分）。"""
    if ch == "ch0":
        load = (f"Vp vp 0 DC 2 AC 0\nVinn inn 0 DC 2 AC 1\n"
                f"Xfa vp inn vcc vee fcc OPAx388\n"
                f"Ra1 fcc pa1 {fmt(p['r'])}\nCa1 pa1 0 {fmt(p['cg'])}\n"
                f"Cd pa1 0 {fmt(p['cd'] * 2)}\nRin pa1 0 65000\nCpa pa1 0 5p\n")
    else:
        load = (f"Vb vb 0 DC 1.2 AC 0\nVinn inn 0 DC 1.2 AC 1\n"
                f"XfB vb inn vcc vee fcc OPAx388\n"
                f"Rf fcc a1p {fmt(p['r'])}\nCg a1p 0 {fmt(p['cg'])}\n"
                f"Cd a1p na1 {fmt(p['cd'])}\n"
                f"RKN 0 na1 {fmt(p['r'])}\nCGN na1 0 {fmt(p['cg'])}\n"
                f"Rin a1p na1 130000\nCpa a1p 0 5p\nCna na1 0 5p\n")
    return (f"* t07 {_case_id(case)} loop_{ch} — follower loop gain, broken at input\n"
            f"* inject AC1 at IN+ (Vinn), IN- at DC bias (AC gnd); T=-V(fcc)/V(inn)\n"
            f"* load: {'differential half-circuit (t00_loop konvention)' if ch == 'ch0' else 'real asymmetric CH1 full load'}\n"
            f"{HEAD}{load}"
            f".ac dec 400 0.1 200Meg\n{TOPT}\n"
            f".save V(fcc) V(inn)\n.end\n")


def t07_pk(case: str, p: dict, ch: str) -> str:
    """T07 全频闭环 peaking（C9）。真实 OPA388 闭环、小信号 AC：
    CH0 差分激励（±0.5V AC、共模恒 2V）；CH1 单端激励（B 线 AC 1、na1 Kelvin 被动响应）。
    C9 主口径 = 跟随器输出节点（ftp,ftm / fbk）峰值（r4 §4.2）；ADC 引脚节点另报。"""
    if ch == "ch0":
        body = (f"Vp vp 0 DC 2 AC 0.5\nVn vn 0 DC 2 AC -0.5\n"
                f"XfT vp ftp vcc vee ftp OPAx388\nXfM vn ftm vcc vee ftm OPAx388\n"
                f"Ra1 ftp a0p {fmt(p['r'])}\nCa1 a0p 0 {fmt(p['cg'])}\n"
                f"Rb1 ftm a0n {fmt(p['r'])}\nCb1 a0n 0 {fmt(p['cg'])}\n"
                f"Cd a0p a0n {fmt(p['cd'])}\n"
                f"Rin a0p a0n 130000\nCpa a0p 0 5p\nCna a0n 0 5p\n")
        pin, fo = "V(a0p,a0n)", "V(ftp,ftm)"
        sv = "V(a0p) V(a0n) V(ftp) V(ftm)"
    else:
        body = (f"Vb bin 0 DC 1.2 AC 1\n"
                f"XfB bin fbk vcc vee fbk OPAx388\n"
                f"Rf fbk a1p {fmt(p['r'])}\nCg a1p 0 {fmt(p['cg'])}\n"
                f"Cd a1p na1 {fmt(p['cd'])}\n"
                f"RKN 0 na1 {fmt(p['r'])}\nCGN na1 0 {fmt(p['cg'])}\n"
                f"Rin a1p na1 130000\nCpa a1p 0 5p\nCna na1 0 5p\n")
        pin, fo = "V(a1p,na1)", "V(fbk)"
        sv = "V(a1p) V(na1) V(fbk)"
    return (f"* t07 {_case_id(case)} pk_{ch} — closed-loop full-band peaking (C9<=6dB)\n"
            f"* C9 primary = follower-output node ({fo}); ADC-pin node secondary ({pin})\n"
            f"{HEAD}{body}"
            f".ac dec 400 0.1 200Meg\n{TOPT}\n"
            f".meas AC g_dc  FIND mag({pin}) AT=0.1\n"
            f".meas AC pk_pin MAX mag({pin})\n"
            f".meas AC pk_pin_f WHEN mag({pin})=pk_pin\n"
            f".meas AC gdc_fo FIND mag({fo}) AT=0.1\n"
            f".meas AC pk_fo MAX mag({fo})\n"
            f".meas AC pk_fo_f WHEN mag({fo})=pk_fo\n"
            f".save {sv}\n.end\n")


def t07_os(case: str, p: dict, ch: str) -> str:
    """T07 瞬态过冲：+100 mV 小信号阶跃（10 ns 沿），闭环差分 ADC 引脚电压响应。
    CH0：双端反相阶跃（差分 +0.1V、共模恒 2V）；CH1：B 线单端阶跃（1.15→1.25V）。"""
    if ch == "ch0":
        body = (f"Vp vp 0 PWL(0 1.95 1u 1.95 1.01u 2.0)\n"
                f"Vn vn 0 PWL(0 2.05 1u 2.05 1.01u 2.0)\n"
                f"XfT vp ftp vcc vee ftp OPAx388\nXfM vn ftm vcc vee ftm OPAx388\n"
                f"Ra1 ftp a0p {fmt(p['r'])}\nCa1 a0p 0 {fmt(p['cg'])}\n"
                f"Rb1 ftm a0n {fmt(p['r'])}\nCb1 a0n 0 {fmt(p['cg'])}\n"
                f"Cd a0p a0n {fmt(p['cd'])}\n"
                f"Rin a0p a0n 130000\nCpa a0p 0 5p\nCna a0n 0 5p\n")
        obs, sv = "V(a0p,a0n)", "V(a0p) V(a0n)"
    else:
        body = (f"Vb bin 0 PWL(0 1.15 1u 1.15 1.01u 1.25)\n"
                f"XfB bin fbk vcc vee fbk OPAx388\n"
                f"Rf fbk a1p {fmt(p['r'])}\nCg a1p 0 {fmt(p['cg'])}\n"
                f"Cd a1p na1 {fmt(p['cd'])}\n"
                f"RKN 0 na1 {fmt(p['r'])}\nCGN na1 0 {fmt(p['cg'])}\n"
                f"Rin a1p na1 130000\nCpa a1p 0 5p\nCna na1 0 5p\n")
        obs, sv = "V(a1p,na1)", "V(a1p) V(na1)"
    return (f"* t07 {_case_id(case)} os_{ch} — transient overshoot, +100mV step @10ns edge\n"
            f"{HEAD}{body}"
            f".tran 0 30u 0 2n\n{TOPT}\n"
            f".meas TRAN vfin FIND {obs} AT=29u\n"
            f".meas TRAN vmax MAX {obs} FROM=1.05u TO=30u\n"
            f".meas TRAN vmin MIN {obs} FROM=1.05u TO=30u\n"
            f".save {sv}\n.end\n")


T05_TESTS = None  # noqa: N816（占位说明）测试清单由 netlist_jobs() 生成：
# t05 × {ch0,ch1} × {n1,n3} + t07 × {loop,pk,os} × {ch0,ch1}，共 4案×10=40 网表


def netlist_jobs():
    """yield (stem, netlist_text, timeout)"""
    for case, p in CASES.items():
        cid = _case_id(case)
        for ch in ("ch0", "ch1"):
            for v in ("n1", "n3"):
                stem = f"t05_{cid}_{ch}_{v}"
                yield stem, t05_noise(case, p, ch, v), 300
            for kind, fn in (("loop", t07_loop), ("pk", t07_pk), ("os", t07_os)):
                stem = f"t07_{cid}_{kind}_{ch}"
                yield stem, fn(case, p, ch), 600


def gen_all() -> list[Path]:
    NET.mkdir(exist_ok=True)
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
# 2. 运行
# ======================================================================
def run_all_nets(force: bool = False) -> dict[str, str]:
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
        print(f"[run] {stem}: ok={ok} ({dt:.1f}s)" + (f" {out[:120]}" if not ok else ""))
        log, raw = net.with_suffix(".log"), net.with_suffix(".raw")
        if ok and log.exists() and raw.exists():
            shutil.copy2(log, LOGD / f"{stem}.log")
            shutil.copy2(raw, RAWD / f"{stem}.raw")
        status[stem] = "ok" if ok else f"FAIL: {out[:300]}"
    return status


# ======================================================================
# 3. 解析
# ======================================================================
def _col(raw, name):
    try:
        return np.abs(np.asarray(raw.col(name), dtype=float))
    except KeyError:
        return None


def integrate_band(f, dens, fmax):
    m = f <= fmax
    return float(np.sqrt(np.trapezoid(dens[m] ** 2, f[m])))


def noise_metrics(rawpath: Path):
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
    # 逐器件归属（LTspice .noise 保存每器件贡献密度；独立源功率可加）
    groups = {"opa_nV": [], "passR_nV": [], "adcRin_nV": []}
    lname = {n.lower(): n for n in r.names}
    for low, orig in lname.items():
        if not low.startswith("v("):
            continue
        if low.startswith("v(xf"):                       # OPA388 宏内部全部器件
            groups["opa_nV"].append(orig)
        elif low in ("v(ra1)", "v(rb1)", "v(rf)", "v(rkn)"):
            groups["passR_nV"].append(orig)              # AAF 串联 R / Kelvin R
        elif low == "v(rin)":
            groups["adcRin_nV"].append(orig)             # ADC 等效输入阻抗 130k
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
        out[key] = math.sqrt(float(np.trapezoid(acc[f <= FB_BROAD],
                                                f[f <= FB_BROAD]))) * 1e9 if acc is not None else None
    # 交叉校验：Σ器件² ≈ onoise²
    tot2 = out["vn_bb_nV"] ** 2
    parts2 = sum((out[k] or 0) ** 2 for k in ("opa_nV", "passR_nV", "adcRin_nV"))
    out["attr_xcheck_pct"] = (abs(tot2 - parts2) / tot2 * 100) if tot2 else float("nan")
    out["_raw_f"] = f
    out["_raw_d"] = d
    return out


def loop_pm(rawpath: Path):
    """T=-V(fcc)/V(inn)（run_all.loop_pm_ugf 同口径，节点名换 fcc/inn）。"""
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


def ac_peaking(rawpath: Path, pos: str, neg: str, fo_node: str):
    """闭环增益峰（相对 0.1Hz）@ADC 引脚与跟随器输出节点。返回 dB、峰频、DC 基准。"""
    d = parse_r5.Raw(str(rawpath))
    f = d.f
    pin = np.array(d.col(f"V({pos})")) - np.array(d.col(f"V({neg})"))
    fo = np.array(d.col(fo_node))
    out = {}
    for tag, y in (("pin", pin), ("fo", fo)):
        g = 20 * np.log10(np.abs(y) / np.abs(y[0]))
        k = int(np.argmax(g))
        out[f"peak_{tag}_db"] = float(g[k])
        out[f"peak_{tag}_f_hz"] = float(f[k])
        out[f"gdc_{tag}_db"] = float(20 * math.log10(abs(y[0])))
    return out


def tran_overshoot(rawpath: Path, pos: str, neg: str, step=0.1):
    d = parse_r5.Raw(str(rawpath))
    t = np.array([v.real for v in d.cols[0]], dtype=float)
    y = np.array(d.col(f"V({pos})"), dtype=float) - np.array(d.col(f"V({neg})"), dtype=float)
    m = t >= 1.05e-6
    tt, yy = t[m], y[m]
    vf = float(np.mean(yy[-max(5, len(yy) // 50):]))
    overshoot = (float(yy.max()) - vf) / step * 100
    undershoot = (vf - float(yy.min())) / step * 100
    # 振铃频率：过冲峰后相邻极小/极大对（若有可见振铃）
    ring_hz = None
    if overshoot > 0.05:
        pk = []
        for i in range(2, len(yy) - 2):
            if yy[i] > yy[i - 1] and yy[i] > yy[i + 1] and yy[i] > vf + 0.002 * step:
                pk.append(tt[i])
        pk = pk[:6]
        if len(pk) >= 2:
            ring_hz = 1.0 / np.mean(np.diff(pk))
    return {"overshoot_pct": overshoot, "undershoot_pct": undershoot,
            "vfinal_v": vf, "vmax_v": float(yy.max()), "t_peak_s": float(tt[int(np.argmax(yy))]),
            "ring_hz": ring_hz, "_t": tt, "_y": yy}


def parse_meas_log(path: Path) -> dict:
    return run_all.parse_meas_log(path)


# ======================================================================
# 4. CSV / plots
# ======================================================================
def write_csvs(results: dict) -> tuple[Path, Path]:
    CSVD.mkdir(exist_ok=True)
    # ---- t05_noise.csv ----
    f1 = CSVD / "t05_noise.csv"
    cols = ["case", "r_ohm", "cg_nf", "cd_pf", "channel", "variant",
            "vn_inband_nVrms", "vn_broadband_nVrms", "vn_broadband_lsb",
            "dens_10Hz_nVrtHz", "dens_1k_nVrtHz", "dens_16k_nVrtHz",
            "dens_100k_nVrtHz", "dens_1M_nVrtHz",
            "d6a_linear_pct", "d6a_quad_pct", "d6a_judge",
            "opa388_share_nVrms", "passR_share_nVrms", "adcRin_share_nVrms",
            "attr_xcheck_pct", "method_note"]
    with f1.open("w", newline="\n", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for row in results["t05"]:
            w.writerow(row)
    # ---- t07_stability.csv ----
    f2 = CSVD / "t07_stability.csv"
    cols2 = ["case", "r_ohm", "cg_nf", "cd_pf", "test",
             "ugf_hz", "pm_deg", "peak_fo_db", "peak_fo_f_hz", "gdc_fo_db",
             "peak_pin_db", "peak_pin_f_hz", "gdc_pin_db",
             "c9_max_db", "c9_pass_le6dB",
             "overshoot_pct", "undershoot_pct", "vfinal_v", "vmax_v", "ring_hz",
             "meas_note", "method_note"]
    with f2.open("w", newline="\n", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols2)
        w.writeheader()
        for row in results["t07"]:
            w.writerow(row)
    return f1, f2


def make_plots(results: dict):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    PLOTD.mkdir(exist_ok=True)
    for case, p in CASES.items():
        cid = _case_id(case)
        # --- 噪声谱 ---
        fig, ax = plt.subplots(figsize=(8, 5))
        for ch, v, lab in (("ch0", "n1", "CH0 total (T/M followers, noisy)"),
                           ("ch1", "n1", "CH1 total (B follower + Kelvin, noisy)"),
                           ("ch1", "n3", "CH1 OPA388-only (R noiseless)")):
            m = results["t05_dense"][(cid, ch, v)]
            if m:
                ax.loglog(m["f"], m["d"] * 1e9, label=lab, lw=1.2)
        ax.axvline(FB_INBAND, ls=":", c="gray")
        ax.axvline(FB_BROAD, ls=":", c="gray")
        ax.set_xlabel("Frequency [Hz]")
        ax.set_ylabel("Differential output noise [nV/rtHz]")
        ax.set_title(f"T05 noise density — {cid}  "
                     f"(R={fmt(p['r'])} C_G={fmt(p['cg']*1e9)}nF C_D={fmt(p['cd']*1e12)}pF)")
        ax.legend(fontsize=8)
        ax.grid(True, which="both", alpha=0.3)
        fig.tight_layout()
        fig.savefig(PLOTD / f"t05_{cid}_noise_density.png", dpi=130)
        plt.close(fig)
        # --- 环路增益 ---
        fig, (a1, a2) = plt.subplots(2, 1, figsize=(8, 6.5), sharex=True)
        for ch, c in (("ch0", "tab:blue"), ("ch1", "tab:orange")):
            m = results["t07_loop"][(cid, ch)]
            if not m:
                continue
            f, T = m["f"], m["T"]
            mag = 20 * np.log10(np.abs(T))
            ph = np.angle(T) * 180 / math.pi
            a1.semilogx(f, mag, c=c, label=f"{ch} (PM={m['pm']:.1f}deg, UGF={m['ugf']/1e3:.0f}kHz)")
            a2.semilogx(f, ph, c=c)
            if m["pm"] is not None:
                a1.axvline(m["ugf"], ls=":", c=c, alpha=0.6)
        a1.axhline(0, c="k", lw=0.6)
        a1.set_ylabel("|T| [dB]")
        a1.legend(fontsize=8)
        a1.grid(True, which="both", alpha=0.3)
        a2.set_ylabel("phase(T) [deg]")
        a2.set_xlabel("Frequency [Hz]")
        a2.grid(True, which="both", alpha=0.3)
        fig.suptitle(f"T07 loop gain (broken at IN+, beta=1) — {cid}")
        fig.tight_layout()
        fig.savefig(PLOTD / f"t07_{cid}_loopgain.png", dpi=130)
        plt.close(fig)
        # --- peaking + 过冲 ---
        fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.2))
        for ch in ("ch0", "ch1"):
            m = results["t07_pk"][(cid, ch)]
            if m:
                a1.semilogx(m["f"], m["g_pin_db"], label=f"{ch} pin")
                a1.semilogx(m["f"], m["g_fo_db"], label=f"{ch} follower out", ls="--")
        a1.axhline(C9_TH, c="r", ls=":", lw=1)
        a1.set_xlabel("Frequency [Hz]")
        a1.set_ylabel("Closed-loop gain rel. DC [dB]")
        a1.set_title("C9 peaking (red = 6dB line)")
        a1.legend(fontsize=7)
        a1.grid(True, which="both", alpha=0.3)
        for ch in ("ch0", "ch1"):
            m = results["t07_os"][(cid, ch)]
            if m:
                tt = (m["_t"] - 1.01e-6) * 1e6
                yy = (m["_y"] - m["vfinal_v"] + 0.1) / 0.1
                a2.plot(tt, yy, label=f"{ch} (os={m['overshoot_pct']:.2f}%)")
        a2.axhline(1.0, c="k", lw=0.6)
        a2.set_xlim(0, 3)
        a2.set_xlabel("time after step edge [us]")
        a2.set_ylabel("step response [norm]")
        a2.set_title("Transient overshoot (+100mV @10ns)")
        a2.legend(fontsize=7)
        a2.grid(True, alpha=0.3)
        fig.suptitle(f"T07 peaking & overshoot — {cid}")
        fig.tight_layout()
        fig.savefig(PLOTD / f"t07_{cid}_pk_os.png", dpi=130)
        plt.close(fig)
    return sorted(PLOTD.glob("t05_*.png")) + sorted(PLOTD.glob("t07_*.png"))


# ======================================================================
# 5. 主流程
# ======================================================================
def parse_all(run_status: dict) -> dict:
    results = {"t05": [], "t07": [], "t05_dense": {}, "t07_loop": {},
               "t07_pk": {}, "t07_os": {}, "run_status": run_status}
    for case, p in CASES.items():
        cid = _case_id(case)
        base = dict(case=cid, r_ohm=p["r"], cg_nf=round(p["cg"] * 1e9, 3),
                    cd_pf=round(p["cd"] * 1e12, 3))
        # ---------- T05 ----------
        nm = {}
        for ch in ("ch0", "ch1"):
            for v in ("n1", "n3"):
                stem = f"t05_{cid}_{ch}_{v}"
                raw = RAWD / f"{stem}.raw"
                if run_status.get(stem) != "ok" or not raw.exists():
                    results["t05"].append(dict(base, channel=ch, variant=v,
                                               method_note=f"NOT VERIFIED: run failed — "
                                               f"{run_status.get(stem, 'not run')}"))
                    continue
                nm[(ch, v)] = noise_metrics(raw)
                results["t05_dense"][(cid, ch, v)] = {
                    "f": nm[(ch, v)].pop("_raw_f"), "d": nm[(ch, v)].pop("_raw_d")}
        dens_keys = ("dens_10Hz_nV", "dens_1k_nV", "dens_16k_nV",
                     "dens_100k_nV", "dens_1M_nV")

        def dens_cols(m):
            return {f"{k.replace('_nV', '_nVrtHz')}": round(m[k], 3) for k in dens_keys}

        for ch in ("ch0", "ch1"):
            n1, n3 = nm.get((ch, "n1")), nm.get((ch, "n3"))
            if n1:
                row = dict(base, channel=ch, variant="n1",
                           vn_inband_nVrms=round(n1["vn_ib_nV"], 2),
                           vn_broadband_nVrms=round(n1["vn_bb_nV"], 2),
                           vn_broadband_lsb=round(n1["vn_bb_nV"] / (LSB_V * 1e9), 3),
                           **dens_cols(n1),
                           opa388_share_nVrms=round(n1["opa_nV"], 2) if n1["opa_nV"] else None,
                           passR_share_nVrms=round(n1["passR_nV"], 2) if n1["passR_nV"] else None,
                           adcRin_share_nVrms=round(n1["adcRin_nV"], 2) if n1["adcRin_nV"] else None,
                           attr_xcheck_pct=round(n1["attr_xcheck_pct"], 3))
                if n3:
                    d6a = (n1["vn_bb_nV"] - n3["vn_bb_nV"]) / n3["vn_bb_nV"] * 100
                    d6q = math.sqrt(max(n1["vn_bb_nV"] ** 2 - n3["vn_bb_nV"] ** 2, 0)
                                    ) / n3["vn_bb_nV"] * 100
                    row.update(d6a_linear_pct=round(d6a, 4), d6a_quad_pct=round(d6q, 4),
                               d6a_judge=("PASS<=10%" if d6a <= D6A_FULL else
                                          "PASS<=30%" if d6a <= D6A_FAIL else "FAIL>30%"))
                    row["method_note"] = (f"D6a=(n1-n3)/n3 bb={FB_BROAD:.3e}Hz linear r4口径; "
                                          f"n3(bb)={n3['vn_bb_nV']:.1f}nV; D6b=LSB col")
                else:
                    row["method_note"] = "D6a NOT VERIFIED (n3 run failed)"
                results["t05"].append(row)
            if n3:
                results["t05"].append(dict(
                    base, channel=ch, variant="n3",
                    vn_inband_nVrms=round(n3["vn_ib_nV"], 2),
                    vn_broadband_nVrms=round(n3["vn_bb_nV"], 2),
                    vn_broadband_lsb=round(n3["vn_bb_nV"] / (LSB_V * 1e9), 3),
                    **dens_cols(n3),
                    method_note="OPA388-only through same RC (D6a denominator)"))
        # ---------- T07 ----------
        for ch in ("ch0", "ch1"):
            stem = f"t07_{cid}_loop_{ch}"
            raw = RAWD / f"{stem}.raw"
            if run_status.get(stem) == "ok" and raw.exists():
                ugf, pm, f, T = loop_pm(raw)
                results["t07_loop"][(cid, ch)] = {"ugf": ugf, "pm": pm, "f": f, "T": T}
                results["t07"].append(dict(
                    base, test=f"loop_{ch}", ugf_hz=round(ugf, 1) if ugf else None,
                    pm_deg=round(pm, 2) if pm is not None else None,
                    method_note="T=-V(fcc)/V(inn); broken at IN+ (AC1), IN- AC-gnd; "
                                "beta=1 follower, T=Aol(real load); PM=180+ph@|T|=1"))
            else:
                results["t07"].append(dict(base, test=f"loop_{ch}",
                    method_note=f"NOT VERIFIED: {run_status.get(stem, 'not run')}"))
            stem = f"t07_{cid}_pk_{ch}"
            raw = RAWD / f"{stem}.raw"
            if run_status.get(stem) == "ok" and raw.exists():
                pos, neg = (("a0p", "a0n") if ch == "ch0" else ("a1p", "na1"))
                fo_node = "V(ftp)" if ch == "ch0" else "V(fbk)"
                if ch == "ch0":       # 差分跟随器输出节点
                    pk = ac_peaking(raw, pos, neg, "V(ftp)")
                    # CH0 fo 节点取 ftp-ftm 差分：单独算
                    d = parse_r5.Raw(str(raw))
                    fo = np.array(d.col("V(ftp)")) - np.array(d.col("V(ftm)"))
                    g = 20 * np.log10(np.abs(fo) / abs(fo[0]))
                    k = int(np.argmax(g))
                    pk["peak_fo_db"], pk["peak_fo_f_hz"] = float(g[k]), float(d.f[k])
                    pk["gdc_fo_db"] = float(20 * math.log10(abs(fo[0])))
                else:
                    pk = ac_peaking(raw, pos, neg, fo_node)
                c9 = max(pk["peak_fo_db"], pk["peak_pin_db"])
                d = parse_r5.Raw(str(raw))
                pin = np.array(d.col(f"V({pos})")) - np.array(d.col(f"V({neg})"))
                fo_ = np.array(d.col("V(ftp)")) - np.array(d.col("V(ftm)")) if ch == "ch0" \
                    else np.array(d.col("V(fbk)"))
                results["t07_pk"][(cid, ch)] = {
                    "f": d.f,
                    "g_pin_db": 20 * np.log10(np.abs(pin) / abs(pin[0])),
                    "g_fo_db": 20 * np.log10(np.abs(fo_) / abs(fo_[0])),
                    "pk": pk}
                meas = parse_meas_log(NETD_meas(stem))
                results["t07"].append(dict(
                    base, test=f"pk_{ch}",
                    peak_fo_db=round(pk["peak_fo_db"], 3), peak_fo_f_hz=round(pk["peak_fo_f_hz"]),
                    gdc_fo_db=round(pk["gdc_fo_db"], 3),
                    peak_pin_db=round(pk["peak_pin_db"], 3),
                    peak_pin_f_hz=round(pk["peak_pin_f_hz"]),
                    gdc_pin_db=round(pk["gdc_pin_db"], 3),
                    c9_max_db=round(c9, 3),
                    c9_pass_le6dB=("yes" if c9 <= C9_TH else "NO"),
                    meas_note=str(meas),
                    method_note="C9 primary=follower-out node (r4口径), "
                                "secondary=ADC pin; rel. DC(0.1Hz)"))
            else:
                results["t07"].append(dict(base, test=f"pk_{ch}",
                    method_note=f"NOT VERIFIED: {run_status.get(stem, 'not run')}"))
            stem = f"t07_{cid}_os_{ch}"
            raw = RAWD / f"{stem}.raw"
            if run_status.get(stem) == "ok" and raw.exists():
                pos, neg = (("a0p", "a0n") if ch == "ch0" else ("a1p", "na1"))
                os_ = tran_overshoot(raw, pos, neg)
                meas = parse_meas_log(NETD_meas(stem))
                vfin = meas.get("vfin", {}).get("val")
                results["t07_os"][(cid, ch)] = os_
                results["t07"].append(dict(
                    base, test=f"os_{ch}",
                    overshoot_pct=round(os_["overshoot_pct"], 4),
                    undershoot_pct=round(os_["undershoot_pct"], 4),
                    vfinal_v=round(os_["vfinal_v"], 6),
                    vmax_v=round(os_["vmax_v"], 6),
                    ring_hz=round(os_["ring_hz"], 1) if os_["ring_hz"] else None,
                    meas_note=f"meas vfin={vfin}",
                    method_note="+100mV step @10ns edge; overshoot rel. final, "
                                "differential ADC-pin voltage"))
            else:
                results["t07"].append(dict(base, test=f"os_{ch}",
                    method_note=f"NOT VERIFIED: {run_status.get(stem, 'not run')}"))
    return results


def NETD_meas(stem: str) -> Path:
    return NET / f"{stem}.log"


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("cmd", nargs="?", default="all", choices=["gen", "run", "parse", "all"])
    args = ap.parse_args(argv)
    cmd = args.cmd
    if cmd in ("gen", "run", "all"):
        for f in gen_all():
            print(f"[gen] {f.name}")
    status = {}
    if cmd in ("run", "all"):
        status = run_all_nets()
    if cmd == "parse":
        # 由产物存在性重建 run 状态（幂等：log+raw 新鲜即 ok）
        for stem, _, _ in netlist_jobs():
            if stem in status:
                continue
            log, raw = NET / f"{stem}.log", NET / f"{stem}.raw"
            ok = (log.exists() and raw.exists()
                  and "Total elapsed time" in log.read_text(errors="replace")
                  and raw.stat().st_mtime > log.stat().st_mtime - 5)
            status[stem] = "ok" if ok else "missing/failed"
    if cmd in ("parse", "all", "run"):
        results = parse_all(status)
        c1, c2 = write_csvs(results)
        print(f"[csv] {c1}\n[csv] {c2}")
        plots = make_plots(results)
        for pp in plots:
            print(f"[plot] {pp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
