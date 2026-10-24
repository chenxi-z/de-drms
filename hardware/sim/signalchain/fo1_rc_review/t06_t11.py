#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""t06_t11.py — T06 RC 容差（模式A/B 蒙特卡洛+LTspice 角点）+ T11 温度/供电角台架

任务书（hardware/sim/Zcode_LTspice_一阶RC四方案复核任务书.md）§3/§4：
  T06  模式A 未配对量产：P/N 独立随机（R±1% 基线、C±5% 基线，另跑 C±1%）
      → ≥1000 组纯 Python 线性 RC 蒙特卡洛（L1） + ≥30 组 LTspice 完整角点抽样（L2）
      模式B 配对/标定后：按 D8 官方考核条件「R·C 乘积异向配对（R×(1+m) 配 C×(1−m)，
      1% 单体失配）」重算（docs/design/spec/2026-10-18-aa-driver.md:78,103）。
      输出 16 kHz 衰减 / Hratio 幅相 / CMRR 的 mean/σ/P1/P99，分布假设 = 带内均匀独立。
  T11  温度与供电角：−20/25/+85 ℃（spec:93 口径）× 模拟轨 3.3 V ±1.5%（TPS7A2033
      精度 max，主文档 :771），RC 温漂代入（C0G ±30 ppm/℃ spec:93；R ±100 ppm/℃
      声明假设——BOM 中 AAF 电阻料号未定稿）+ OPA388 模型 TEMP 响应（仅 Vos 漂移，
      见 assumptions）→ D4/H0/H1 幅相/PM。

铁律（任务书 §1「特别核对」）：CH1 的 AIN1N = Rsense 底端 Kelvin 地经 R_N/C_GN 直连，
无第四颗 OPA388。所有 L2 网表 = 3× OPA388 + AIN1N Kelvin RC + fsadc 断态负载
（Z_IN 130k + C_pin 5p/端，声明假设 A2/A3）。

子命令：gen | run | mc | parse | plots | all
产物：netlists/*.net、logs/、raw/、csv/t06_*.csv + t11_*.csv、plots/t06_*.png + t11_*.png
"""
from __future__ import annotations

import argparse
import csv
import itertools
import math
import shutil
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
NET = HERE / "netlists"
LOGD = HERE / "logs"
RAWD = HERE / "raw"
CSVD = HERE / "csv"
PLTD = HERE / "plots"

sys.path.insert(0, str(HERE))
import run_all  # noqa: E402  台架基建：run_net / parse_meas_log / loop_pm_ugf

sys.path.insert(0, run_all.PARSE_R5_DIR)
import parse_r5  # noqa: E402

ROOT = run_all.ROOT
LIB = run_all.LIB
CASES = run_all.CASES                     # FO1_BASE/A/B/C（任务书 §2 原文照录）
FMOD, MCLK = run_all.FMOD, run_all.MCLK

# ---- 容差 / 温漂 / 角点常量（来源全部声明）----
TOL_R = 0.01                              # R ±1%（任务书 §3.1）
TOL_C5 = 0.05                             # C0G ±5% 基线（任务书 §3.1）
TOL_C1 = 0.01                             # 另跑 C±1%（任务书/ask）
PPM_R = 100e-6                            # R 温漂声明假设（0402 厚膜 1% 典型；BOM AAF 料号未定稿）
PPM_C = 30e-6                             # C0G ±30 ppm/℃（spec :93 指定）
TEMPS = {"m20": -20.0, "t25": 25.0, "t85": 85.0}          # spec :93
VSUP = {"v32505": 3.2505, "v33000": 3.3000, "v33495": 3.3495}  # 3.3V ±1.5%（主文档 :771）
RIN, CPIN = 130e3, 5e-12                  # fsadc 断态负载（assumptions A2/A3）
SEED = 20261024                           # MC 种子（可复现）
NMC = 1000                                # ≥1000 组（任务书 T06）

DEV_KEYS = ["r0p", "r0n", "cg0p", "cg0n", "cd0", "r1p", "rkn", "cg1p", "cgn", "cd1"]


def fmt(v: float) -> str:
    return f"{v:.8g}"


# ======================================================================
# 1. 网表生成（L2 真实接线：3× OPA388 + AIN1N Kelvin RC）
# ======================================================================
def _head(temp: float, vcc: float) -> str:
    return (f".include {LIB}\n.temp {temp:g}\n"
            f"Vcc vcc 0 DC {vcc:g}\nVee vee 0 DC 0\n")


def _ch0(v: dict, ac_p: str, ac_n: str) -> str:
    return (f"Vp vp 0 DC 2 AC {ac_p}\nVn vn 0 DC 2 AC {ac_n}\n"
            f"Xfa vp fpa vcc vee fpa OPAx388\nXfb vn fnb vcc vee fnb OPAx388\n"
            f"Ra0 fpa a0p {fmt(v['r0p'])}\nCa0 a0p 0 {fmt(v['cg0p'])}\n"
            f"Rb0 fnb a0n {fmt(v['r0n'])}\nCb0 a0n 0 {fmt(v['cg0n'])}\n"
            f"Cd0 a0p a0n {fmt(v['cd0'])}\n")


def _ch1(v: dict, ac_b: str) -> str:
    # AIN1N Kelvin：E(=Rsense 底端=地) —RKN→ na1 + CGN 对地，无第四运放（任务书 §1 铁律）
    return (f"Vb vb 0 DC 2 AC {ac_b}\n"
            f"Xfc vb fcc vcc vee fcc OPAx388\n"
            f"Ra1 fcc a1p {fmt(v['r1p'])}\nCa1 a1p 0 {fmt(v['cg1p'])}\n"
            f"Rkn 0 na1 {fmt(v['rkn'])}\nCgn na1 0 {fmt(v['cgn'])}\n"
            f"Cd1 a1p na1 {fmt(v['cd1'])}\n")


def _adc_load() -> str:
    return (f"Rin0 a0p a0n {RIN:g}\nCp0 a0p 0 {CPIN:g}\nCn0 a0n 0 {CPIN:g}\n"
            f"Rin1 a1p na1 {RIN:g}\nCp1 a1p 0 {CPIN:g}\nCn1 na1 0 {CPIN:g}\n")


OPTS = (".options plotwinsize=0 reltol=1e-6 abstol=1e-12 vntol=1e-9 chgtol=1e-15 trtol=1\n")


def net_dm(v: dict, temp=27.0, vcc=3.3) -> str:
    """差模 AC：Vp/Vn = ±0.5（差分 1 V，spec :91 口径）+ Vb = 1（CH1 单端激励，
    两通道网络解耦、互不影响，一表同时取 H0 与 H1）。"""
    return (f"* t06/t11 dm: H0=V(a0p,a0n)/1, H1=V(a1p,na1)/1; 3xOPA388 + AIN1N Kelvin RC\n"
            + _head(temp, vcc) + _ch0(v, "0.5", "-0.5") + _ch1(v, "1") + _adc_load()
            + ".ac dec 400 0.1 200Meg\n" + OPTS
            + ".meas AC h0_dc   FIND mag(V(a0p,a0n)) AT=0.1\n"
            + ".meas AC h0_16k  FIND mag(V(a0p,a0n)) AT=16k\n"
            + ".meas AC h0_fmod FIND mag(V(a0p,a0n)) AT=4.096Meg\n"
            + ".meas AC h0_mclk FIND mag(V(a0p,a0n)) AT=16.384Meg\n"
            + ".meas AC h1_dc   FIND mag(V(a1p,na1)) AT=0.1\n"
            + ".meas AC h1_16k  FIND mag(V(a1p,na1)) AT=16k\n"
            + ".save V(a0p) V(a0n) V(a1p) V(na1) V(fpa) V(fnb) V(fcc)\n.end\n")


def net_cm(v: dict, temp=27.0, vcc=3.3) -> str:
    """共模 AC：Vp=Vn=0.5（共模 0.5 V，与 T00 accm 锚定口径一致，便于对拍；
    CMRR 为比值指标，归一化后与激励幅度无关）。"""
    return (f"* t06 cm: H_CMtoDM=V(a0p,a0n)/0.5; CH1 不激励（H1 在 dm 表取）\n"
            + _head(temp, vcc) + _ch0(v, "0.5", "0.5") + _ch1(v, "0") + _adc_load()
            + ".ac dec 400 0.1 200Meg\n" + OPTS
            + ".meas AC cm_dm_10  FIND mag(V(a0p,a0n)) AT=10\n"
            + ".meas AC cm_dm_16k FIND mag(V(a0p,a0n)) AT=16k\n"
            + ".meas AC cm_dm_min MIN mag(V(a0p,a0n)) FROM=10 TO=16k\n"
            + ".meas AC cm_out_16k FIND mag(V(a0p)) AT=16k\n"
            + ".meas AC cm_out_fmod FIND mag(V(a0p)) AT=4.096Meg\n"
            + ".save V(a0p) V(a0n)\n.end\n")


def net_loop(p: dict, temp=27.0, vcc=3.3) -> str:
    """环路 PM（t00_loop 口径：跟随器 β=1 断环 + 真实一阶差分半电路负载
    2×C_D 虚地 + 65k + 5p；gen_fo.py net_loop 同源，T11 温度/轨角用）。"""
    return (f"* t11 loop PM: T=-V(fpa)/V(inn) mag 跨 1 处 pm=180+ph（run_all 同口径）\n"
            + _head(temp, vcc)
            + "Vp vp 0 DC 2 AC 0\nVinn inn 0 DC 2 AC 1\n"
            "Xfa vp inn vcc vee fpa OPAx388\n"
            f"Ra1 fpa pa1 {fmt(p['r'])}\nCa1 pa1 0 {fmt(p['cg'])}\n"
            f"Cd pa1 0 {fmt(p['cd'] * 2)}\nRin pa1 0 {RIN / 2:g}\nCpa pa1 0 {CPIN:g}\n"
            ".ac dec 400 0.1 200Meg\n" + OPTS
            + ".save V(fpa) V(inn)\n.end\n")


def net_op(temp: float, vcc: float) -> str:
    """.op：测跟随器 V(in)-V(out) = Vos（OPAx388 VOS_DRIFT 的 TEMP 响应实证）。"""
    return (f"* t11 op: Vos(T) 实证（VOS_DRIFT: DC+POL*DRIFT*(TEMP-27), 0.005uV/C）\n"
            + _head(temp, vcc)
            + "Vi vi 0 DC 2\nXf vi fo vcc vee fo OPAx388\n"
            ".op\n.save V(vi) V(fo)\n.end\n")


# ======================================================================
# 2. 角点定义（模式A：31 组 C±5% + 8 组 C±1%；确定性最坏角，非随机样本）
# ======================================================================
def dev_vals(case: str, devs: dict) -> dict:
    """相对偏差 dict → 元件值 dict。devs[key] 为相对偏差（如 0.01）。"""
    p = CASES[case]
    base = dict(r0p=p["r"], r0n=p["r"], cg0p=p["cg"], cg0n=p["cg"], cd0=p["cd"],
                r1p=p["r"], rkn=p["r"], cg1p=p["cg"], cgn=p["cg"], cd1=p["cd"])
    return {k: base[k] * (1.0 + devs.get(k, 0.0)) for k in DEV_KEYS}


def sg(x: float) -> str:
    return "+" if x > 0 else ("-" if x < 0 else "0")


def build_corners() -> list[tuple[str, str, str, dict]]:
    """(mode, tag, desc, devs) 列表。mode: A5=C±5% 基线 31 组；A1=C±1% 8 组。"""
    out: list[tuple[str, str, str, dict]] = [("A5", "c00", "全标称", {})]
    # 全局同向组合：R×CG×CD ∈ {±}³（τ_DM/τ_CM 绝对极值）——8 组
    for i, (dr, dcg, dcd) in enumerate(itertools.product((1, -1), repeat=3)):
        devs = {k: dr * TOL_R for k in ("r0p", "r0n", "r1p", "rkn")}
        devs.update({k: dcg * TOL_C5 for k in ("cg0p", "cg0n", "cg1p", "cgn")})
        devs.update({"cd0": dcd * TOL_C5, "cd1": dcd * TOL_C5})
        out.append(("A5", f"g{i + 1}",
                    f"全局 R{sg(dr)}1% CG{sg(dcg)}5% CD{sg(dcd)}5%", devs))
    # CH0 P/N 失配 16 组：r0p,r0n ∈ ±1%，cg0p,cg0n ∈ ±5%（CMRR/D8 最坏方向全覆盖）
    for i, (a, b, c, d) in enumerate(itertools.product((1, -1), repeat=4)):
        out.append(("A5", f"m{i + 1}",
                    f"CH0 失配 r0p{sg(a)} r0n{sg(b)} cg0p{sg(c)} cg0n{sg(d)}",
                    dict(r0p=a * TOL_R, r0n=b * TOL_R,
                         cg0p=c * TOL_C5, cg0n=d * TOL_C5)))
    # τ_DM 极值：C_G 与 C_D 反向（差模时间常数 R(C_G+2C_D) 最大/最小）——4 组
    out += [
        ("A5", "d1", "CH0 cg0p−5% cd0+5%（τDM 大）", dict(cg0p=-TOL_C5, cd0=+TOL_C5)),
        ("A5", "d2", "CH0 cg0p+5% cd0−5%（τDM 小）", dict(cg0p=+TOL_C5, cd0=-TOL_C5)),
        ("A5", "d3", "CH1 cg1p−5% cd1+5%（τDM 大）", dict(cg1p=-TOL_C5, cd1=+TOL_C5)),
        ("A5", "d4", "CH1 cg1p+5% cd1−5%（τDM 小）", dict(cg1p=+TOL_C5, cd1=-TOL_C5)),
    ]
    # 通道间失配（Hratio 最坏）：CH0 全 + vs CH1 全 −，及反向——2 组
    full_p = {k: v for k, v in
              list(zip(("r0p", "cg0p", "cd0"), (TOL_R, TOL_C5, TOL_C5)))}
    full_m = {k: -v for k, v in
              list(zip(("r0p", "cg0p", "cd0"), (TOL_R, TOL_C5, TOL_C5)))}
    ch1_p = dict(r1p=TOL_R, rkn=TOL_R, cg1p=TOL_C5, cgn=TOL_C5, cd1=TOL_C5)
    ch1_m = {k: -v for k, v in ch1_p.items()}
    out.append(("A5", "x1", "CH0 全+ vs CH1 全−（Hratio 最坏）", {**full_p, **ch1_m}))
    out.append(("A5", "x2", "CH0 全− vs CH1 全+（Hratio 最坏）", {**full_m, **ch1_p}))
    # C±1% 档：全局 8 组
    for i, (dr, dcg, dcd) in enumerate(itertools.product((1, -1), repeat=3)):
        devs = {k: dr * TOL_R for k in ("r0p", "r0n", "r1p", "rkn")}
        devs.update({k: dcg * TOL_C1 for k in ("cg0p", "cg0n", "cg1p", "cgn")})
        devs.update({"cd0": dcd * TOL_C1, "cd1": dcd * TOL_C1})
        out.append(("A1", f"q{i + 1}",
                    f"全局C±1% R{sg(dr)}1% CG{sg(dcg)}1% CD{sg(dcd)}1%", devs))
    return out


# ======================================================================
# 3. T11 温度/轨角点（RC 温漂代入 + 模型 TEMP）
# ======================================================================
def temp_devs(case: str, temp: float) -> dict:
    dT = temp - 25.0
    return {k: (PPM_R if k[0] == "r" else PPM_C) * dT for k in DEV_KEYS}


# ======================================================================
# 4. 生成入口
# ======================================================================
def gen_all() -> list[Path]:
    for d in (NET, LOGD, RAWD, CSVD, PLTD):
        d.mkdir(exist_ok=True)
    written = []
    for case in CASES:
        cs = case.lower()
        # T06 角点 ×(dm, cm)
        for mode, tag, _desc, devs in build_corners():
            v = dev_vals(case, devs)
            for kind in ("dm", "cm"):
                f = NET / f"t06_{cs}_{mode}_{tag}_{kind}.net"
                f.write_text(net_dm(v) if kind == "dm" else net_cm(v))
                written.append(f)
        # T11：T×V 9 组 ×(dm, loop) + 3 温度 op
        for tk, tv in TEMPS.items():
            for vk, vv in VSUP.items():
                v = dev_vals(case, temp_devs(case, tv))
                f = NET / f"t11_{cs}_{tk}_{vk}_dm.net"
                f.write_text(net_dm(v, temp=tv, vcc=vv))
                written.append(f)
                f = NET / f"t11_{cs}_{tk}_{vk}_loop.net"
                lp = dict(r=v["r0p"], cg=v["cg0p"], cd=v["cd0"])
                f.write_text(net_loop(lp, temp=tv, vcc=vv))
                written.append(f)
            f = NET / f"t11_{cs}_{tk}_v33000_op.net"
            f.write_text(net_op(tv, 3.3))
            written.append(f)
    return written


# ======================================================================
# 5. 批量运行（并行；run_all.run_net 幂等 + ltspice-sim 逐文件锁）
# ======================================================================
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
    for f in sorted(NET.glob("t11_*_op.net")):
        jobs.append((str(f), 120))
    print(f"[run] {len(jobs)} nets, {workers} workers")
    t0, bad, notes = time.time(), 0, []
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for net, ok, out in ex.map(_run_job, jobs):
            stem = Path(net).name
            if not ok:
                bad += 1
                notes.append(f"{stem}: {out[:200]}")
                print(f"  FAIL {stem}")
            else:
                # 归档 log/raw（netlists/ 旁产物 → logs/ raw/）
                p = Path(net)
                lg, rw = p.with_suffix(".log"), p.with_suffix(".raw")
                if lg.exists():
                    shutil.copy2(lg, LOGD / lg.name)
                if rw.exists():
                    shutil.copy2(rw, RAWD / rw.name)
    print(f"[run] done in {time.time() - t0:.0f}s, fails={bad}")
    for n in notes:
        print("  note:", n)
    return bad


# ======================================================================
# 6. L1 线性 RC 引擎（纯 Python MC；含 ADC 断态线性负载；理想源驱动）
# ======================================================================
F_KEY = np.array([0.1, 1e3, 8e3, 16e3, FMOD, MCLK])
F_CMRR = np.logspace(1, math.log10(16e3), 241)   # 10 Hz–16 kHz CMRR 网格
F_ALL = np.unique(np.concatenate([F_KEY, F_CMRR]))


def _h_two_node(rp, cgp, rn, cgn, cd, vp, vn, f):
    """两节点差分 RC 网络（每线 R+C_G，跨接 C_D+Rin，每端 Cpin 对地）。
    rp,cgp: P 线；rn,cgn: N 线；vp,vn: 理想源复激励（频率无关）。返回 (Vp_node-Vn_node)。"""
    s = 2j * np.pi * f
    ycd = s * cd + 1.0 / RIN
    y11 = 1.0 / rp + s * cgp + ycd + s * CPIN
    y22 = 1.0 / rn + s * cgn + ycd + s * CPIN
    y12 = -ycd
    i1, i2 = vp / rp, vn / rn
    det = y11 * y22 - y12 * y12
    v1 = (i1 * y22 - i2 * y12) / det
    v2 = (y11 * i2 - y12 * i1) / det
    return v1 - v2


def h0_dm(v, f=F_ALL):
    return _h_two_node(v["r0p"], v["cg0p"], v["r0n"], v["cg0n"], v["cd0"], 0.5, -0.5, f)


def h0_cm(v, f=F_ALL):
    # 共模激励 0.5 V（T00 accm 锚定口径）→ 除以 0.5 归一到 1 V 共模输入
    # （2026-10-24 L1↔L2 对拍发现原实现漏除，CMRR 恒高 6 dB，已修）
    return _h_two_node(v["r0p"], v["cg0p"], v["r0n"], v["cg0n"], v["cd0"], 0.5, 0.5, f) / 0.5


def h1(v, f=F_ALL):
    # CH1 Kelvin：P 侧激励 1 V，N 侧理想地（源=0），C_D/Rin/Cpin 跨接保留
    return _h_two_node(v["r1p"], v["cg1p"], v["rkn"], v["cgn"], v["cd1"], 1.0, 0.0, f)


def _at(f_arr, y_arr, f0):
    return complex(np.interp(math.log(f0), np.log(f_arr), y_arr.real)
                   + 1j * np.interp(math.log(f0), np.log(f_arr), y_arr.imag))


def db(x: float) -> float:
    return 20 * math.log10(abs(x)) if abs(x) > 0 else -999.0


def metrics_from_hs(h0dm, h0cm, h1v, f=F_ALL) -> dict:
    """从三条复响应取全部指标（频率网格 F_ALL）。"""
    g0dc = db(_at(f, h0dm, 0.1))
    g1dc = db(_at(f, h1v, 0.1))
    out = {}
    for fk in (1e3, 8e3, 16e3):
        y0, y1 = _at(f, h0dm, fk), _at(f, h1v, fk)
        out[f"h0_{int(fk)}_db"] = db(y0)
        out[f"h1_{int(fk)}_db"] = db(y1)
        out[f"hr_mag_{int(fk)}_db"] = db(y0) - db(y1)
        out[f"hr_ph_{int(fk)}_deg"] = math.degrees(
            math.atan2(y0.imag, y0.real) - math.atan2(y1.imag, y1.real))
    out["atten16k_db"] = -(out["h0_16000_db"] - g0dc)          # D4 口径
    out["atten16k_ch1_db"] = -(out["h1_16000_db"] - g1dc)
    out["h0_fmod_db"] = db(_at(f, h0dm, FMOD))
    out["h0_mclk_db"] = db(_at(f, h0dm, MCLK))
    out["d1_db"] = -(out["h0_fmod_db"] - g0dc)
    out["d3_db"] = -(out["h0_mclk_db"] - g0dc)
    # CMRR = |H_DM| / |H_CM→DM|，10 Hz–16 kHz 最坏（spec D8 口径；激励已归一）
    m = (f >= 10) & (f <= 16e3)
    cmrr = 20 * np.log10(np.abs(h0dm[m]) / np.maximum(np.abs(h0cm[m]), 1e-30))
    k = int(np.argmin(cmrr))
    out["cmrr_min_db"] = float(cmrr[k])
    out["cmrr_worst_hz"] = float(f[m][k])
    out["cmrr_16k_db"] = float(cmrr[-1])
    return out


def metrics_l1(vals: dict) -> dict:
    return metrics_from_hs(h0_dm(vals), h0_cm(vals), h1(vals))


# ---- MC 采样（带内均匀独立；B2 = D8 官方 R·C 乘积异向配对）----
def sample_devs(mode: str, rng) -> dict:
    if mode in ("A5", "A1"):
        ct = TOL_C5 if mode == "A5" else TOL_C1
        return {k: rng.uniform(-TOL_R if k[0] == "r" else -ct,
                               TOL_R if k[0] == "r" else ct) for k in DEV_KEYS}
    if mode == "B2":   # 配对：每通道每线 m~U(±1%)，R×(1+m) 配 C×(1−m)；C_D 独立 ±5%
        devs = {}
        for line in ("0p", "0n", "1p", "kn"):
            m = rng.uniform(-TOL_R, TOL_R)
            devs["r" + line] = m
            devs["cg" + line] = -m
        devs["cd0"] = rng.uniform(-TOL_C5, TOL_C5)
        devs["cd1"] = rng.uniform(-TOL_C5, TOL_C5)
        return devs
    raise ValueError(mode)


MC_MODES = [("A5", "模式A 未配对 R±1% C±5% 独立均匀"),
            ("A1", "模式A R±1% C±1% 独立均匀（任务书另跑档）"),
            ("B2", "模式B R·C 乘积异向配对 m~U±1%（D8 官方考核条件），C_D±5%")]


def run_mc() -> None:
    rows, summ = [], []
    for case in CASES:
        for mode, desc in MC_MODES:
            rng = np.random.default_rng(SEED + hash((case, mode)) % 10000)
            ms = []
            for i in range(NMC):
                devs = sample_devs(mode, rng)
                m = metrics_l1(dev_vals(case, devs))
                m["sample"] = i
                ms.append(m)
            keys = [k for k in ms[0] if k != "sample"]
            rows += [dict(case=case, mode=mode, **{k: m[k] for k in keys})
                     for m in ms]
            for k in keys:
                a = np.array([m[k] for m in ms], dtype=float)
                summ.append(dict(case=case, mode=mode, desc=desc, metric=k,
                                 n=NMC, mean=float(a.mean()),
                                 sigma=float(a.std(ddof=1)),
                                 p1=float(np.percentile(a, 1)),
                                 p99=float(np.percentile(a, 99)),
                                 min=float(a.min()), max=float(a.max()),
                                 dist="uniform independent (B2: paired m)"))
    with (CSVD / "t06_mc_all.csv").open("w", newline="\n", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    with (CSVD / "t06_mc_summary.csv").open("w", newline="\n", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(summ[0].keys()))
        w.writeheader()
        w.writerows(summ)
    print(f"[mc] {len(rows)} samples -> csv/t06_mc_all.csv, summary -> t06_mc_summary.csv")
    # L1 标称自检：DC 分压应 = 130k/(130k+2R)（README/T00 口径 0.999278）
    for case in CASES:
        v = dev_vals(case, {})
        h = h0_dm(v, np.array([0.1]))
        r = CASES[case]["r"]
        print(f"[mc] {case} L1 DC check: |H0(0.1Hz)|={abs(h[0]):.6f} "
              f"theory={RIN / (RIN + 2 * r):.6f}")


# ======================================================================
# 7. LTspice 解析（dm/cm/loop/op → CSV）
# ======================================================================
def _raw_h(raw_path: Path, names: tuple[str, str]) -> np.ndarray:
    r = parse_r5.Raw(str(raw_path))
    return (np.array(r.col(names[0]), dtype=complex)
            - np.array(r.col(names[1]), dtype=complex))


def parse_t06() -> None:
    rows = []
    for case in CASES:
        cs = case.lower()
        for mode, tag, desc, devs in build_corners():
            dm_raw = RAWD / f"t06_{cs}_{mode}_{tag}_dm.raw"
            cm_raw = RAWD / f"t06_{cs}_{mode}_{tag}_cm.raw"
            if not dm_raw.exists() or not cm_raw.exists():
                rows.append(dict(case=case, mode=mode, corner=tag, desc=desc,
                                 status="NOT VERIFIED (raw missing)"))
                continue
            f = parse_r5.Raw(str(dm_raw)).f
            h0 = _raw_h(dm_raw, ("V(a0p)", "V(a0n)"))
            h1 = _raw_h(dm_raw, ("V(a1p)", "V(na1)"))
            fc = parse_r5.Raw(str(cm_raw)).f
            h0c = _raw_h(cm_raw, ("V(a0p)", "V(a0n)")) / 0.5   # 共模 0.5V 归一
            assert len(f) == len(fc) and np.allclose(f, fc), "dm/cm 网格不一致"
            m = metrics_from_hs(h0, h0c, h1, f)
            rows.append(dict(case=case, mode=mode, corner=tag, desc=desc,
                             status="OK", **m))
    keys = sorted({k for r in rows for k in r}, key=lambda k: (k != "case",
                  k not in ("mode", "corner", "desc", "status"), k))
    with (CSVD / "t06_ltspice_corners.csv").open("w", newline="\n",
                                                 encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    # 汇总统计（角点集合，非随机样本——注明）
    summ = []
    for case in CASES:
        for mode in ("A5", "A1"):
            sel = [r for r in rows if r["case"] == case and r["mode"] == mode
                   and r.get("status") == "OK"]
            for k in ("atten16k_db", "hr_mag_16000_db", "hr_ph_16000_deg",
                      "cmrr_min_db", "cmrr_16k_db"):
                # CMRR 指标：P/N 对称角（全局 g/q 组与 m 组内 4 个同向组合）的
                # CM→DM 泄漏落到仿真数值地板（>200 dB），不代表真实 CMRR——
                # 统计只取真失配角（<200 dB），地板角单独计数注明。
                sub = ([r for r in sel if float(r[k]) < 200] if k.startswith("cmrr")
                       else sel)
                n_floor = (len(sel) - len(sub)) if k.startswith("cmrr") else 0
                if not sub:      # A1 档 8 个全局角全部对称 → CMRR 无真失配角
                    summ.append(dict(case=case, mode=mode, metric=k, n=0,
                                     mean="", sigma="", p1="", p99="", min="", max="",
                                     note="无真失配角（全部为 P/N 对称全局角，CMRR 落"
                                          "数值地板）；A1 档 CMRR 散布见 MC 统计"))
                    continue
                a = np.array([r[k] for r in sub], dtype=float)
                summ.append(dict(case=case, mode=mode, metric=k, n=len(a),
                                 mean=float(a.mean()), sigma=float(a.std(ddof=1)),
                                 p1=float(np.percentile(a, 1)),
                                 p99=float(np.percentile(a, 99)),
                                 min=float(a.min()), max=float(a.max()),
                                 note=("确定性角点集合（非随机样本）；CMRR 仅统计真失配"
                                       f"角 n={len(a)}，对称角数值地板 n={n_floor} 剔除"
                                       if k.startswith("cmrr") else
                                       "确定性角点集合（非随机样本），σ/P1/P99 仅作汇总")))
    with (CSVD / "t06_ltspice_summary.csv").open("w", newline="\n",
                                                 encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(summ[0].keys()))
        w.writeheader()
        w.writerows(summ)
    print(f"[parse] t06 corners={len(rows)} -> t06_ltspice_corners.csv + summary")


def parse_t11() -> None:
    rows = []
    for case in CASES:
        cs = case.lower()
        for tk, tv in TEMPS.items():
            # Vos(T) 实证（op）
            op_raw = RAWD / f"t11_{cs}_{tk}_v33000_op.raw"
            vos = ""
            if op_raw.exists():
                r = parse_r5.Raw(str(op_raw))
                vos = float(np.real(r.col("V(vi)")[0]) - np.real(r.col("V(fo)")[0]))
            for vk, vv in VSUP.items():
                dm_raw = RAWD / f"t11_{cs}_{tk}_{vk}_dm.raw"
                lp_raw = RAWD / f"t11_{cs}_{tk}_{vk}_loop.raw"
                row = dict(case=case, temp_c=tv, vcc_v=vv,
                           vos_op_v=(vos if vk == "v33000" else ""))
                if dm_raw.exists():
                    f = parse_r5.Raw(str(dm_raw)).f
                    h0 = _raw_h(dm_raw, ("V(a0p)", "V(a0n)"))
                    h1 = _raw_h(dm_raw, ("V(a1p)", "V(na1)"))
                    if not (0.98 < abs(h0[0]) < 1.01 and 0.98 < abs(h1[0]) < 1.01):
                        row.update(status_dm="NOT VERIFIED (raw curve corrupt)")
                    else:
                        m = metrics_from_hs(h0, np.full_like(h0, 1e-30), h1, f)
                        # cmrr 无 cm 网表 → 置空
                        for k in ("cmrr_min_db", "cmrr_worst_hz", "cmrr_16k_db"):
                            m[k] = ""
                        row.update(status_dm="OK", **m)
                else:
                    row.update(status_dm="NOT VERIFIED (raw missing)")
                if lp_raw.exists():
                    # raw 完整性守卫（2026-10-24 实测归因）：OPAx388 TI 宏 Final 1.4 在
                    # .temp 偏离 25/26/27℃ 窗口（30℃ 起与零下）时，断环 AC 线性化的
                    # 直流环路增益塌 1000×（2.43e7→2.43e4，恒定幅度、与方案/RC 无关；
                    # 同温度 dm 闭环 AC 正常、RC 温漂单独代入正常）→ 判定为宏模型缺陷，
                    # 非电路物理。塌陷曲线的 PM 读数无意义，剔除并如实标注。
                    dl = parse_r5.Raw(str(lp_raw))
                    tgm = np.abs(-np.array(dl.col("V(fpa)"))
                                 / np.array(dl.col("V(inn)")))
                    if tgm[0] > 1e6:
                        ugf, pm = run_all.loop_pm_ugf(lp_raw)
                        row.update(pm_deg=pm, ugf_hz=ugf, status_loop="OK")
                    else:
                        row.update(pm_deg="", ugf_hz="", status_loop=(
                            "NOT VERIFIED (OPAx388 macro loop-AC linearization "
                            "collapses at .temp outside 25-27C: DC loop gain "
                            "2.4e4 vs 2.4e7 — model defect; dm AC unaffected)"))
                else:
                    row.update(status_loop="NOT VERIFIED (raw missing)")
                rows.append(row)
    keys = sorted({k for r in rows for k in r},
                  key=lambda k: (k != "case", k not in ("temp_c", "vcc_v"), k))
    with (CSVD / "t11_corners.csv").open("w", newline="\n", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    print(f"[parse] t11 rows={len(rows)} -> csv/t11_corners.csv")


# ======================================================================
# 8. 图
# ======================================================================
def make_plots() -> None:
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["font.sans-serif"] = ["Noto Sans CJK SC", "DejaVu Sans"]
    matplotlib.rcParams["axes.unicode_minus"] = False
    import matplotlib.pyplot as plt

    # 8.1 MC 分布（每方案：atten16k / hr_mag16k / cmrr_min，三档叠加 + LTspice 角点 rug）
    try:
        mc = list(csv.DictReader((CSVD / "t06_mc_all.csv").open(encoding="utf-8")))
        lt = [r for r in csv.DictReader(
            (CSVD / "t06_ltspice_corners.csv").open(encoding="utf-8"))
            if r.get("status") == "OK"]
    except FileNotFoundError:
        print("[plots] mc/corner csv 缺失，跳过")
        return
    colors = {"A5": "#dc2626", "A1": "#2563eb", "B2": "#059669"}
    labels = {"A5": "A 未配对 R1%/C5%", "A1": "A 未配对 R1%/C1%",
              "B2": "B R·C 异向配对 1%"}
    for case in CASES:
        fig, axes = plt.subplots(1, 3, figsize=(13.5, 3.8))
        for ax, key, xlab in (
                (axes[0], "atten16k_db", "16 kHz 衰减 (dB, D4 口径)"),
                (axes[1], "hr_mag_16000_db", "Hratio 幅度误差 @16k (dB)"),
                (axes[2], "cmrr_min_db", "CMRR 最坏 10Hz–16kHz (dB)")):
            for mode in ("A5", "A1", "B2"):
                a = np.array([float(r[key]) for r in mc
                              if r["case"] == case and r["mode"] == mode])
                ax.hist(a, bins=60, histtype="step", lw=1.4,
                        color=colors[mode], label=f"{labels[mode]} (n={len(a)})")
            for mode in ("A5", "A1"):
                a = np.array([float(r[key]) for r in lt
                              if r["case"] == case and r["mode"] == mode])
                if len(a):
                    ax.plot(a, np.full(len(a), ax.get_ylim()[1] * 0.98), "|",
                            color=colors[mode], ms=10, mew=1.2)
            ax.set_xlabel(xlab)
            ax.grid(alpha=0.3)
            if key == "cmrr_min_db":
                ax.axvline(80, color="k", ls="--", lw=0.8, label="D8 及格 80 dB")
        axes[0].set_ylabel("组数")
        axes[0].legend(fontsize=7)
        fig.suptitle(f"T06 容差蒙特卡洛（L1 线性 RC，n={NMC}/档）+ LTspice 角点（| Rug）"
                     f" — {case}  R={CASES[case]['r']:g}Ω CG={CASES[case]['cg'] * 1e9:g}nF"
                     f" CD={CASES[case]['cd'] * 1e9:g}nF")
        fig.tight_layout()
        f = PLTD / f"t06_mc_dist_{case.lower()}.png"
        fig.savefig(f, dpi=140)
        plt.close(fig)
        print(f"[plots] {f}")

    # 8.2 LTspice 角点 vs MC 散点（atten16k–CMRR 平面，L1↔L2 一致性视图）
    fig, axes = plt.subplots(1, 4, figsize=(16, 4), sharey=True)
    for ax, case in zip(axes, CASES):
        for mode in ("A5", "A1", "B2"):
            a = np.array([[float(r["atten16k_db"]), float(r["cmrr_min_db"])]
                          for r in mc if r["case"] == case and r["mode"] == mode])
            ax.plot(a[:, 0], a[:, 1], ".", ms=1.5, alpha=0.25, color=colors[mode],
                    label=labels[mode])
        a = np.array([[float(r["atten16k_db"]), float(r["cmrr_min_db"])]
                      for r in lt if r["case"] == case])
        ax.plot(a[:, 0], a[:, 1], "kx", ms=7, mew=1.3, label="LTspice 角点 (L2)")
        ax.axhline(80, color="k", ls="--", lw=0.8)
        ax.set_title(case, fontsize=10)
        ax.set_xlabel("atten16k (dB)")
        ax.grid(alpha=0.3)
    axes[0].set_ylabel("CMRR_min (dB)")
    axes[0].legend(fontsize=7, markerscale=4)
    fig.suptitle("T06 容差平面：16k 衰减 vs CMRR（点=L1 Python MC，×=L2 LTspice 角点；虚线=D8 80dB）")
    fig.tight_layout()
    f = PLTD / "t06_ltspice_vs_mc.png"
    fig.savefig(f, dpi=140)
    plt.close(fig)
    print(f"[plots] {f}")

    # 8.3 T11 角点扫描（D4 / PM / Vos vs T×V）
    if (CSVD / "t11_corners.csv").exists():
        t11 = list(csv.DictReader((CSVD / "t11_corners.csv").open(encoding="utf-8")))
        fig, axes = plt.subplots(1, 3, figsize=(13.5, 3.8))
        tks = list(TEMPS)
        for case, mk in zip(CASES, "ox+s^"):
            for vk, col in zip(VSUP, ("#dc2626", "#374151", "#2563eb")):
                xs = [r for r in t11 if r["case"] == case and r["vcc_v"] == f"{VSUP[vk]:g}"
                      and r.get("status_dm") == "OK"]
                if not xs:
                    continue
                t = [r["temp_c"] for r in xs]
                axes[0].plot(t, [float(r["atten16k_db"]) for r in xs], mk,
                             color=col, ms=5,
                             label=f"{case} V={VSUP[vk]:g}" if case == "FO1_BASE" else "")
                lp = [r for r in xs if r.get("status_loop") == "OK"]
                if lp:
                    axes[1].plot([r["temp_c"] for r in lp],
                                 [float(r["pm_deg"]) for r in lp], mk, color=col, ms=5)
                axes[2].plot(t, [float(r["hr_mag_16000_db"]) for r in xs], mk,
                             color=col, ms=5)
        axes[0].set_title("D4 @16k (dB)", fontsize=10)
        axes[1].set_title("环路 PM (deg)", fontsize=10)
        axes[2].set_title("Hratio 幅度误差 @16k (dB)", fontsize=10)
        for ax in axes:
            ax.set_xlabel("温度 (℃)")
            ax.grid(alpha=0.3)
        axes[0].legend(fontsize=7)
        fig.suptitle("T11 温度×模拟轨角点（RC 温漂代入：R±100ppm/℃ 假设、C0G ±30ppm/℃；"
                     "轨 3.3V±1.5%）")
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
        if bad and args.cmd == "all":
            print(f"[run] {bad} fails — 继续解析，缺失项将标 NOT VERIFIED")
    if args.cmd in ("mc", "all"):
        run_mc()
    if args.cmd in ("parse", "all"):
        parse_t06()
        parse_t11()
    if args.cmd in ("plots", "all"):
        make_plots()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
