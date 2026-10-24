#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ac_family.py — fo1_rc_review AC 测试族（T01/T02/T03/T10，任务书 §4）四方案批跑 + 解析

覆盖（每方案 7 网表 × 4 = 28）：
  T01 差模 AC  t01_{case}_dm_ideal    L1：0Ω 理想源直驱一阶 RC + ADC 无源负载（无运放）
              t01_{case}_dm_opa388   L2 CH0 口径：双 OPA388 对称（gen_fo.py net_ac_dm 逐行同口径，meas 扩展）
              t01_{case}_dm_kelvin   L2 CH1 真实接线：1×OPA388(P线) + AIN1N Kelvin RC 直连 E（铁律：无第四运放）
  T02 共模 AC  t02_{case}_cm_ideal / cm_opa388 / cm_kelvin   共模激励 1 V AC（任务书 §4 T02）
  T03 通道匹配 t03_{case}_ch0_realsrc  CH0 实际源阻抗口径（差分源每侧串 23.5k = 样品 47k 浮动源阻抗）
              （CH1 实际源条件 ≈ 0Ω：B 点由 BSS138 低阻驱动、E=地 → 由 dm_kelvin 兼任，CSV 注明）
  T10 群延迟   无新网表：dm_ideal / dm_opa388 / dm_kelvin raw 相位微分 + CH0/CH1 失配

口径与归一化声明：
  * DM 激励 = 差分 1 V（Vp AC 0.5 / Vn AC −0.5，共模 DC 2 V）→ |V(P)−V(N)| 即传递函数幅度
  * Kelvin 差分激励 Vbp=2.5 V/Ven=1.5 V（DC 共模 2 V 对齐 CH0，差分 ±0.5 V 同归一化）
  * CM 激励 = 1 V AC（任务书 §4 原文）；与 T00 锚定（0.5 V 激励）绝对 dB 差 6.02 dB，衰减量口径不受影响
  * H 的分母 = 激励源端差分/共模电压（运放输入侧/RC 输入侧），非 ADC 引脚
  * CMRR_RC(f) = 20log10|H_DM/H_CM→DM| = g_dm(f) − g_cmdm(f)（dB 域同口径网表对相减）
  * 对称网表（ideal/opa388 CH0）的 CM→DM 是求解器数值底（器件完全对称），
    真实未配对 CMRR_RC 由 T06 容差 MC 负责；Kelvin 通道 CM→DM 是结构性失配（真实值）

依赖：run_all.py（CASES/run_net/parse_meas_log 台架）、aaf/parse_r5.py（复数 AC raw）。
产物：netlists/*.net（gitignore）、logs/ raw/ 归档、csv/{t01_dm_ac,t02_cm_ac,t03_channel_match,t10_group_delay}.csv、plots/t0*_*.png
"""
from __future__ import annotations

import csv
import math
import re
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, "/media/anning/data/Project/DE-DRMS/hardware/sim/aaf")
import run_all          # noqa: E402  台架：CASES / run_net / parse_meas_log
import parse_r5         # noqa: E402  复数 AC raw 解析（T00 已验证）

NET = HERE / "netlists"
LOGD = HERE / "logs"
RAWD = HERE / "raw"
CSVD = HERE / "csv"
PLOTD = HERE / "plots"

CASES = run_all.CASES                       # FO1_BASE / FO1_A / FO1_B / FO1_C
STEM = {k: k.lower() for k in CASES}        # fo1_base / fo1_a / fo1_b / fo1_c
LIB = run_all.LIB
FMOD, MCLK = run_all.FMOD, run_all.MCLK

AC = ".ac dec 400 0.1 200Meg\n"
OPTS = (".options plotwinsize=0 reltol=1e-6 abstol=1e-12 vntol=1e-9 "
        "chgtol=1e-15 trtol=1\n")
PWR = "Vcc vcc 0 DC 3.3\nVee vee 0 DC 0\n"
# CH0 实际源阻抗：样品 RSAMP=47k 差分浮动（fullchain_net 同值）→ 每侧 23.5k
RSRC_CH0_SIDE = 23500.0

FLOOR_DB = -320.0        # 求解器数值底封顶（|H|=0 时 dB 无定义）


def fmt(v: float) -> str:
    return f"{v:.6g}"


def adc_load(p: str, n: str) -> str:
    """ADS131A02 引脚无源负载：Zin 130k 差分 + C_pin 5p/端（fsadc 断态，A2/A3 声明假设）。"""
    return f"Rin {p} {n} 130000\nCpa {p} 0 5e-12\nCna {n} 0 5e-12\n"


def meas_dm(p: str, n: str, foll: str | None = None) -> str:
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
    if foll:
        s += (f".meas AC foll_dc FIND mag(V({foll})) AT=0.1\n"
              f".meas AC foll_pk MAX mag(V({foll}))\n"
              f".meas AC foll_pk_f WHEN mag(V({foll}))=foll_pk\n")
    return s


def meas_cm(p: str, n: str) -> str:
    vd = f"V({p},{n})"
    return (f".meas AC cm_dc   FIND mag(V({p})) AT=0.1\n"
            f".meas AC cm_1k   FIND mag(V({p})) AT=1k\n"
            f".meas AC cm_8k   FIND mag(V({p})) AT=8k\n"
            f".meas AC cm_16k  FIND mag(V({p})) AT=16k\n"
            f".meas AC cm_fmod FIND mag(V({p})) AT=4.096Meg\n"
            f".meas AC cm_mclk FIND mag(V({p})) AT=16.384Meg\n"
            f".meas AC cmdm_dc   FIND mag({vd}) AT=0.1\n"
            f".meas AC cmdm_10   FIND mag({vd}) AT=10\n"
            f".meas AC cmdm_1k   FIND mag({vd}) AT=1k\n"
            f".meas AC cmdm_8k   FIND mag({vd}) AT=8k\n"
            f".meas AC cmdm_16k  FIND mag({vd}) AT=16k\n"
            f".meas AC cmdm_fmod FIND mag({vd}) AT=4.096Meg\n")


# ----------------------------------------------------------------------
# 网表生成（include 一律绝对路径 —— 全角逗号目录陷阱，fs_subs.inc:3-5）
# ----------------------------------------------------------------------
def n_dm_ideal(case: str, p: dict) -> str:
    return (f"* t01 {case} dm_ideal - L1 ideal source(0ohm) drives 1st-order RC + ADC passive load, DM 1V\n"
            f".include {LIB}\n"
            f"Vp vp 0 DC 2 AC 0.5\nVn vn 0 DC 2 AC -0.5\n"
            f"Ra1 vp pa1 {fmt(p['r'])}\nCa1 pa1 0 {fmt(p['cg'])}\n"
            f"Rb1 vn na1 {fmt(p['r'])}\nCb1 na1 0 {fmt(p['cg'])}\n"
            f"Cd pa1 na1 {fmt(p['cd'])}\n"
            + adc_load("pa1", "na1")
            + AC + OPTS + meas_dm("pa1", "na1")
            + ".save V(pa1) V(na1)\n.end\n")


def n_dm_opa388(case: str, p: dict) -> str:
    return (f"* t01 {case} dm_opa388 - L2 CH0: dual OPA388 symmetric (gen_fo.py net_ac_dm same setup), DM 1V\n"
            f".include {LIB}\n{PWR}"
            f"Vp vp 0 DC 2 AC 0.5\nVn vn 0 DC 2 AC -0.5\n"
            f"Xfa vp fpa vcc vee fpa OPAx388\nXfb vn fna vcc vee fna OPAx388\n"
            f"Ra1 fpa pa1 {fmt(p['r'])}\nCa1 pa1 0 {fmt(p['cg'])}\n"
            f"Rb1 fna na1 {fmt(p['r'])}\nCb1 na1 0 {fmt(p['cg'])}\n"
            f"Cd pa1 na1 {fmt(p['cd'])}\n"
            + adc_load("pa1", "na1")
            + AC + OPTS + meas_dm("pa1", "na1", foll="fpa")
            + ".save V(pa1) V(na1) V(fpa) V(fna)\n.end\n")


def n_dm_kelvin(case: str, p: dict) -> str:
    return (f"* t01 {case} dm_kelvin - L2 CH1 real wiring: 1xOPA388(P line) + AIN1N Kelvin RC to E (no 4th opamp), DM 1V\n"
            f"* nodes: bp=B(Rsense top) en=E(Rsense bottom/Kelvin gnd) a1p=AIN1P na1=AIN1N fcc=follower out\n"
            f"* DC bias: Vbp=2.5/Ven=1.5 (common-mode 2V aligned to CH0; real chain E=0/B=1.2V, small-signal equivalent)\n"
            f".include {LIB}\n{PWR}"
            f"Vbp bp 0 DC 2.5 AC 0.5\nVen en 0 DC 1.5 AC -0.5\n"
            f"XfB bp fcc vcc vee fcc OPAx388\n"
            f"Rf  fcc a1p {fmt(p['r'])}\nCG  a1p 0 {fmt(p['cg'])}\n"
            f"RKN en na1 {fmt(p['r'])}\nCGN na1 0 {fmt(p['cg'])}\n"
            f"CD  a1p na1 {fmt(p['cd'])}\n"
            + adc_load("a1p", "na1")
            + AC + OPTS + meas_dm("a1p", "na1", foll="fcc")
            + ".save V(a1p) V(na1) V(fcc)\n.end\n")


def n_cm_ideal(case: str, p: dict) -> str:
    return (f"* t02 {case} cm_ideal - L1 common-mode 1V AC into symmetric RC + ADC load\n"
            f".include {LIB}\n"
            f"Vp vp 0 DC 2 AC 1\nVn vn 0 DC 2 AC 1\n"
            f"Ra1 vp pa1 {fmt(p['r'])}\nCa1 pa1 0 {fmt(p['cg'])}\n"
            f"Rb1 vn na1 {fmt(p['r'])}\nCb1 na1 0 {fmt(p['cg'])}\n"
            f"Cd pa1 na1 {fmt(p['cd'])}\n"
            + adc_load("pa1", "na1")
            + AC + OPTS + meas_cm("pa1", "na1")
            + ".save V(pa1) V(na1)\n.end\n")


def n_cm_opa388(case: str, p: dict) -> str:
    return (f"* t02 {case} cm_opa388 - L2 CH0 dual OPA388 symmetric, common-mode 1V AC\n"
            f".include {LIB}\n{PWR}"
            f"Vp vp 0 DC 2 AC 1\nVn vn 0 DC 2 AC 1\n"
            f"Xfa vp fpa vcc vee fpa OPAx388\nXfb vn fna vcc vee fna OPAx388\n"
            f"Ra1 fpa pa1 {fmt(p['r'])}\nCa1 pa1 0 {fmt(p['cg'])}\n"
            f"Rb1 fna na1 {fmt(p['r'])}\nCb1 na1 0 {fmt(p['cg'])}\n"
            f"Cd pa1 na1 {fmt(p['cd'])}\n"
            + adc_load("pa1", "na1")
            + AC + OPTS + meas_cm("pa1", "na1")
            + ".save V(pa1) V(na1) V(fpa) V(fna)\n.end\n")


def n_cm_kelvin(case: str, p: dict) -> str:
    return (f"* t02 {case} cm_kelvin - L2 CH1 real wiring common-mode 1V AC: P line buffered, N line Kelvin RC\n"
            f".include {LIB}\n{PWR}"
            f"Vbp bp 0 DC 2 AC 1\nVen en 0 DC 2 AC 1\n"
            f"XfB bp fcc vcc vee fcc OPAx388\n"
            f"Rf  fcc a1p {fmt(p['r'])}\nCG  a1p 0 {fmt(p['cg'])}\n"
            f"RKN en na1 {fmt(p['r'])}\nCGN na1 0 {fmt(p['cg'])}\n"
            f"CD  a1p na1 {fmt(p['cd'])}\n"
            + adc_load("a1p", "na1")
            + AC + OPTS + meas_cm("a1p", "na1")
            + ".save V(a1p) V(na1) V(fcc)\n.end\n")


def n_ch0_realsrc(case: str, p: dict) -> str:
    return (f"* t03 {case} ch0_realsrc - CH0 actual source impedance: DM 1V via 23.5k/side (=sample 47k floating)\n"
            f".include {LIB}\n{PWR}"
            f"Vsp srcp 0 DC 2 AC 0.5\nRsp srcp vp {fmt(RSRC_CH0_SIDE)}\n"
            f"Vsn srcn 0 DC 2 AC -0.5\nRsn srcn vn {fmt(RSRC_CH0_SIDE)}\n"
            f"Xfa vp fpa vcc vee fpa OPAx388\nXfb vn fna vcc vee fna OPAx388\n"
            f"Ra1 fpa pa1 {fmt(p['r'])}\nCa1 pa1 0 {fmt(p['cg'])}\n"
            f"Rb1 fna na1 {fmt(p['r'])}\nCb1 na1 0 {fmt(p['cg'])}\n"
            f"Cd pa1 na1 {fmt(p['cd'])}\n"
            + adc_load("pa1", "na1")
            + AC + OPTS + meas_dm("pa1", "na1", foll="fpa")
            + ".save V(pa1) V(na1) V(fpa) V(fna)\n.end\n")


GENS = {
    "t01_dm_ideal": n_dm_ideal,
    "t01_dm_opa388": n_dm_opa388,
    "t01_dm_kelvin": n_dm_kelvin,
    "t02_cm_ideal": n_cm_ideal,
    "t02_cm_opa388": n_cm_opa388,
    "t02_cm_kelvin": n_cm_kelvin,
    "t03_ch0_realsrc": n_ch0_realsrc,
}


def gen_all() -> list[Path]:
    NET.mkdir(exist_ok=True)
    written = []
    for case, p in CASES.items():
        for tid, fn in GENS.items():
            f = NET / f"{tid}_{STEM[case]}.net"
            f.write_text(fn(case, p))
            written.append(f)
    return written


# ----------------------------------------------------------------------
# 运行（复用台架 run_net：LTspice 产物为准，ltspice-sim 复数后处理崩溃记 note）
# ----------------------------------------------------------------------
def run_one(args):
    tid, case = args
    net = NET / f"{tid}_{STEM[case]}.net"
    ok, out = run_all.run_net(net, timeout=300)
    log, raw = net.with_suffix(".log"), net.with_suffix(".raw")
    if ok:
        stem = f"{tid}_{STEM[case]}"
        shutil.copy2(log, LOGD / f"{stem}.log")
        shutil.copy2(raw, RAWD / f"{stem}.raw")
    return tid, case, ok, out


def run_all_nets(workers: int = 4) -> list[str]:
    LOGD.mkdir(exist_ok=True)
    RAWD.mkdir(exist_ok=True)
    jobs = [(tid, case) for case in CASES for tid in GENS]
    failures, notes = [], []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for tid, case, ok, out in ex.map(run_one, jobs):
            tag = f"{tid}/{case}"
            if not ok:
                failures.append(tag)
                print(f"[run] FAIL {tag}: {out[-300:]}")
            else:
                if out and not out.startswith("cached"):
                    print(f"[run] ok   {tag} {('[' + out[:60] + ']') if out.startswith('NOTE') else ''}")
                else:
                    print(f"[run] ok   {tag} ({out[:30]})")
            if out.startswith("NOTE"):
                notes.append(f"{tag}: {out}")
    return failures


# ----------------------------------------------------------------------
# 解析：复数 AC raw → H(f)、fc、幅相、D1/D3/D4、peaking、CMRR、Hratio、群延迟
# ----------------------------------------------------------------------
def load_H(rawpath: Path, pnode: str, nnode: str):
    r = parse_r5.Raw(str(rawpath))
    f = np.asarray(r.f, dtype=float)
    H = (np.asarray(r.col(f"V({pnode})"), dtype=complex)
         - np.asarray(r.col(f"V({nnode})"), dtype=complex))
    return f, H


def load_single(rawpath: Path, node: str):
    r = parse_r5.Raw(str(rawpath))
    return np.asarray(r.f, dtype=float), np.asarray(r.col(f"V({node})"), dtype=complex)


def db(x):
    a = np.abs(x)
    return 20 * np.log10(np.where(a > 0, a, 1e-320))


def H_at(f, H, ft):
    """log-f 网格复数线性插值（parse_r5.interp_at 同法）。"""
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
    """−3 dB 截止（相对 DC 值），log-f 域 dB 线性插值；取自 DC 起首个下穿。"""
    g = db(H)
    target = g[0] - 3.0102999566398
    for i in range(1, len(f)):
        if g[i - 1] > target >= g[i]:
            lf = np.log10(f)
            w = (target - g[i - 1]) / (g[i] - g[i - 1])
            return float(10 ** (lf[i - 1] + w * (lf[i] - lf[i - 1])))
    return None


def group_delay(f, H, fmax=16e3):
    m = f <= fmax
    ff = f[m]
    ph = np.unwrap(np.angle(H[m]))
    tau = -np.gradient(ph, 2 * np.pi * ff)        # s
    return ff, tau


def parse_ph_meas(log: Path) -> dict:
    """LTspice 26.1.1 实测：.meas AC ph(V(x)) 输出 (20log10|φ| dB, 0°/180°) 元组，
    180° 分量 = 负号 → φ = ∓10^(dB/20)（冒烟验证：ph_16k=(22.294dB,180°) →
    −12.94° ≈ 理论 −atan(16k/69.6k)=−12.91°）。"""
    out = {}
    if not log.exists():
        return out
    for line in log.read_text(errors="replace").splitlines():
        m = re.match(r"^(\w+):\s+[^=]+?=\(?(-?[\d.eE+-]+)dB\s*,\s*(180|0)°", line.strip())
        if m:
            try:
                v = 10 ** (float(m.group(2)) / 20)
                out[m.group(1)] = -v if m.group(3) == "180" else v
            except ValueError:
                pass
    return out


# ----------------------------------------------------------------------
# 主分析：四 CSV + 图
# ----------------------------------------------------------------------
def analyze():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    CSVD.mkdir(exist_ok=True)
    PLOTD.mkdir(exist_ok=True)
    t01_rows, t02_rows, t03_rows, t10_rows = [], [], [], []
    notver = []
    max_meas_raw_diff = 0.0

    for case, p in CASES.items():
        cs = STEM[case]
        raws = {tid: RAWD / f"{tid}_{cs}.raw" for tid in GENS}
        logs = {tid: LOGD / f"{tid}_{cs}.log" for tid in GENS}

        # ---------- H 加载 ----------
        Hs = {}
        try:
            Hs["ideal"] = load_H(raws["t01_dm_ideal"], "pa1", "na1")
            Hs["opa388"] = load_H(raws["t01_dm_opa388"], "pa1", "na1")
            Hs["kelvin"] = load_H(raws["t01_dm_kelvin"], "a1p", "na1")
            Hs["realsrc"] = load_H(raws["t03_ch0_realsrc"], "pa1", "na1")
        except Exception as e:                                   # noqa: BLE001
            notver.append(f"{case}: DM raw 缺失/解析失败: {e}")
            continue
        CMs = {}
        for port in ("ideal", "opa388", "kelvin"):
            pn = ("pa1", "na1") if port != "kelvin" else ("a1p", "na1")
            try:
                CMs[port] = load_H(raws[f"t02_cm_{port}"], pn[0], pn[1])
            except Exception as e:                               # noqa: BLE001
                notver.append(f"{case}: cm_{port} raw 缺失: {e}")

        fc_dm_theory = 1 / (2 * math.pi * p["r"] * (p["cg"] + 2 * p["cd"])) / 1e3
        fc_cm_theory = 1 / (2 * math.pi * p["r"] * p["cg"]) / 1e3

        # ================= T01 差模 AC =================
        for port in ("ideal", "opa388", "kelvin"):
            f, H = Hs[port]
            g = db(H)
            fc = fc_from_H(f, H)
            row = dict(
                case=case, port=port,
                fc_kHz=round(fc / 1e3, 3) if fc else None,
                fc_theory_kHz=round(fc_dm_theory, 3),
                g_dc_dB=round(db_at(f, H, 0.1), 4),
                g_1k_dB=round(db_at(f, H, 1e3), 4),
                g_8k_dB=round(db_at(f, H, 8e3), 4),
                g_16k_dB=round(db_at(f, H, 16e3), 4),
                ph_1k_deg=round(ph_at(f, H, 1e3), 4),
                ph_8k_deg=round(ph_at(f, H, 8e3), 4),
                ph_16k_deg=round(ph_at(f, H, 16e3), 4),
                D1_resid_dB=round(db_at(f, H, FMOD), 3),
                D1_atten_dB=round(db_at(f, H, 0.1) - db_at(f, H, FMOD), 3),
                D3_resid_dB=round(db_at(f, H, MCLK), 3),
                D3_atten_dB=round(db_at(f, H, 0.1) - db_at(f, H, MCLK), 3),
                D4_atten16k_dB=round(db_at(f, H, 0.1) - db_at(f, H, 16e3), 4),
                peaking_dB=round(float(g.max() - g[0]), 4),
                pk_freq_Hz=round(float(f[int(np.argmax(g))]), 1),
                norm="H=V(P)-V(N) per 1V DM excitation @source")
            # .meas 交叉校验（dm_fmod/dm_mclk/dm_16k 的 dB）
            tid = f"t01_dm_{port}"
            mm = run_all.parse_meas_log(logs[tid])
            cross = []
            for mk, col in (("dm_fmod", "D1_resid_dB"), ("dm_mclk", "D3_resid_dB"),
                            ("dm_16k", "g_16k_dB"), ("dm_1k", "g_1k_dB")):
                mv = mm.get(mk, {}).get("val")
                if mv is not None and not math.isnan(mv):
                    d = abs(mv - row[col])
                    max_meas_raw_diff = max(max_meas_raw_diff, d)
                    cross.append(f"{mk}:{d:.4f}")
            row["meas_vs_raw_maxdiff_dB"] = ";".join(cross) if cross else "no .meas parsed"
            ph_m = parse_ph_meas(logs[tid])
            row["ph_meas_16k_deg"] = (round(ph_m["ph_16k"], 4)
                                      if "ph_16k" in ph_m else "meas-parse-n/a")
            # 跟随器 peaking（opa388/kelvin 口径）
            foll = mm.get("foll_pk", {}).get("val")
            foll_dc = mm.get("foll_dc", {}).get("val")
            if foll is not None and foll_dc is not None and not (math.isnan(foll) or math.isnan(foll_dc)):
                row["foll_peaking_dB"] = round(foll - foll_dc, 4)
                row["foll_pk_freq_Hz"] = mm.get("foll_pk_f", {}).get("at")
            else:
                row["foll_peaking_dB"] = None
                row["foll_pk_freq_Hz"] = None
            t01_rows.append(row)

        # ================= T02 共模 AC =================
        for port in ("ideal", "opa388", "kelvin"):
            if port not in CMs:
                continue
            fc, HC = CMs[port]        # HC = V(P)-V(N) under CM excitation → CM→DM
            f = fc
            # 输出共模（单端 V(P)）另取
            pn = "pa1" if port != "kelvin" else "a1p"
            _, Vcm = load_single(raws[f"t02_cm_{port}"], pn)
            cmdm = db(HC)
            row = dict(
                case=case, port=port,
                cm_dc_resid_dB=round(db_at(f, Vcm, 0.1), 4),
                cm_16k_resid_dB=round(db_at(f, Vcm, 16e3), 4),
                D2_resid_1Vexc_dB=round(db_at(f, Vcm, FMOD), 3),
                D2_atten_dB=round(db_at(f, Vcm, 0.1) - db_at(f, Vcm, FMOD), 3),
                cmdm_dc_dB=round(db_at(f, HC, 0.1), 2),
                cmdm_10Hz_dB=round(db_at(f, HC, 10), 2),
                cmdm_1k_dB=round(db_at(f, HC, 1e3), 2),
                cmdm_8k_dB=round(db_at(f, HC, 8e3), 2),
                cmdm_16k_dB=round(db_at(f, HC, 16e3), 2),
                cmdm_fmod_dB=round(db_at(f, HC, FMOD), 2),
                norm="H_CM=V(P) single-end, H_CM-to-DM=V(P)-V(N), per 1V CM excitation")
            # CMRR_RC(f) = g_dm(f) − g_cmdm(f)，同口径 DM 网表对；10 Hz–16 kHz 最差
            if port in dict(ideal=Hs["ideal"], opa388=Hs["opa388"], kelvin=Hs["kelvin"]):
                fdm, Hdm = Hs[port]
                band = (f >= 10) & (f <= 16e3)
                cmrr = db(Hdm[band]) - cmdm[band]
                k = int(np.argmin(cmrr))
                row["CMRR_RC_worst_dB"] = round(float(cmrr[k]), 2)
                row["CMRR_RC_worst_f_Hz"] = round(float(f[band][k]), 1)
                row["CMRR_RC_1k_dB"] = round(db_at(f, Hdm, 1e3) - db_at(f, HC, 1e3), 2)
                row["CMRR_RC_16k_dB"] = round(db_at(f, Hdm, 16e3) - db_at(f, HC, 16e3), 2)
                row["note"] = ("对称网表 cmdm=求解器数值底(器件完全对称),真实未配对 CMRR 须 T06 容差 MC"
                               if port != "kelvin" else
                               "Kelvin 结构性 CM→DM(P线经运放/N线无源RC),真实失配非数值底")
            # .meas 校验
            mm = run_all.parse_meas_log(logs[f"t02_cm_{port}"])
            cross = []
            for mk, col in (("cm_fmod", "D2_resid_1Vexc_dB"), ("cmdm_16k", "cmdm_16k_dB")):
                mv = mm.get(mk, {}).get("val")
                if mv is not None and not math.isnan(mv):
                    cross.append(f"{mk}:|diff|={abs(mv - row[col]):.3f}")
            row["meas_vs_raw"] = ";".join(cross) if cross else "no .meas parsed"
            t02_rows.append(row)

        # ================= T03 通道匹配 =================
        f0, H0 = Hs["opa388"]
        f1, H1 = Hs["kelvin"]
        fr, H0r = Hs["realsrc"]
        for src, Ha, Hb, note in (
                ("ideal0ohm", H0, H1,
                 "H0=CH0 dual-opa388, H1=CH1 Kelvin, both 0ohm DM source"),
                ("real_src", H0r, H1,
                 "H0=CH0 with 23.5k/side (sample 47k); H1: CH1 source=low-Z(BSS138)/gnd ≈0ohm → same as ideal0ohm")):
            Hratio = Ha / Hb
            gr = db(Hratio)
            ph0c = np.unwrap(np.angle(Ha))
            ph1c = np.unwrap(np.angle(Hb))
            dphi = np.degrees(ph0c - ph1c)
            for flab, ft in (("DC", 0.1), ("1k", 1e3), ("8k", 8e3), ("16k", 16e3)):
                i = int(np.argmin(np.abs(f0 - ft)))
                t03_rows.append(dict(
                    case=case, src=src, f=flab,
                    H0_mag_dB=round(db_at(f0, Ha, ft), 4),
                    H1_mag_dB=round(db_at(f1, Hb, ft), 4),
                    Hratio_mag_dB=round(db_at(f0, Hratio, ft), 4),
                    Hratio_ph_deg=round(float(dphi[i]), 4),
                    note=note))
            # 8k/16k 幅度比误差与相位差摘要行
            t03_rows.append(dict(
                case=case, src=src, f="worst(1k-16k)",
                H0_mag_dB=None, H1_mag_dB=None,
                Hratio_mag_dB=round(float(gr[(f0 >= 1e3) & (f0 <= 16e3)].max()
                                          - gr[(f0 >= 1e3) & (f0 <= 16e3)].min()), 4),
                Hratio_ph_deg=round(float(np.abs(dphi[(f0 >= 1e3) & (f0 <= 16e3)]).max()), 4),
                note="|Hratio| p-p(dB) / |Δφ| max over 1k-16k"))

        # ================= T10 群延迟 =================
        for port, lab in (("ideal", "L1_ideal"), ("opa388", "CH0_opa388"),
                          ("kelvin", "CH1_kelvin"), ("realsrc", "CH0_realsrc")):
            f, H = Hs[port]
            ff, tau = group_delay(f, H)
            t10_rows.append(dict(
                case=case, channel=lab,
                tau_1k_us=round(float(np.interp(1e3, ff, tau)) * 1e6, 4),
                tau_8k_us=round(float(np.interp(8e3, ff, tau)) * 1e6, 4),
                tau_16k_us=round(float(np.interp(16e3, ff, tau)) * 1e6, 4),
                tau_min_us=round(float(tau.min()) * 1e6, 4),
                tau_max_us=round(float(tau.max()) * 1e6, 4),
                dtau_0p1Hz_16k_us=round(float(tau.max() - tau.min()) * 1e6, 4),
                D10_pass_le5us="yes" if (tau.max() - tau.min()) * 1e6 <= 5.0 else "NO"))
        # CH0/CH1 相位失配（unwrap 曲线差）
        ph0c = np.unwrap(np.angle(Hs["opa388"][1]))
        ph1c = np.unwrap(np.angle(Hs["kelvin"][1]))
        f0 = Hs["opa388"][0]
        dphi = np.degrees(ph0c - ph1c)
        ff0, tau0 = group_delay(*Hs["opa388"])
        ff1, tau1 = group_delay(*Hs["kelvin"])
        t10_rows.append(dict(
            case=case, channel="CH0_vs_CH1_mismatch",
            tau_1k_us=round(float((np.interp(1e3, ff0, tau0) - np.interp(1e3, ff1, tau1))) * 1e6, 4),
            tau_8k_us=round(float((np.interp(8e3, ff0, tau0) - np.interp(8e3, ff1, tau1))) * 1e6, 4),
            tau_16k_us=round(float((np.interp(16e3, ff0, tau0) - np.interp(16e3, ff1, tau1))) * 1e6, 4),
            tau_min_us=None, tau_max_us=None, dtau_0p1Hz_16k_us=None,
            D10_pass_le5us=(f"dphi@1k={dphi[np.argmin(np.abs(f0-1e3))]:.4f}deg, "
                            f"@8k={dphi[np.argmin(np.abs(f0-8e3))]:.4f}deg, "
                            f"@16k={dphi[np.argmin(np.abs(f0-16e3))]:.4f}deg")))

        # ================= 图 =================
        _plot_t01(plt, case, Hs, PLOTD)
        _plot_t02(plt, case, CMs, Hs, PLOTD)
        _plot_t03(plt, case, Hs, PLOTD)
        _plot_t10(plt, case, Hs, PLOTD)

    # ---- CSV 落盘 ----
    def wcsv(path, rows):
        keys = []
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
    wcsv(CSVD / "t03_channel_match.csv", t03_rows)
    wcsv(CSVD / "t10_group_delay.csv", t10_rows)
    print(f"[xcheck] .meas vs raw 最大差 {max_meas_raw_diff:.4f} dB")
    return notver


def _plot_t01(plt, case, Hs, PLOTD):
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
    for port, lab in (("ideal", "L1 ideal src"), ("opa388", "CH0 dual OPA388"),
                      ("kelvin", "CH1 Kelvin"), ("realsrc", "CH0 real-src 47k")):
        f, H = Hs[port]
        a1.semilogx(f, db(H), label=lab)
        a2.semilogx(f, np.degrees(np.angle(H)), label=lab)
    a1.set_ylabel("|H_DM| dB")
    a1.grid(True, which="both", alpha=0.3)
    a1.legend(fontsize=8)
    a1.set_title(f"T01 differential-mode AC - {case} (norm: 1V DM @source)")
    a2.set_ylabel("phase deg")
    a2.set_xlabel("Hz")
    a2.grid(True, which="both", alpha=0.3)
    for ax in (a1, a2):
        for fx in (4.096e6, 16.384e6):
            ax.axvline(fx, color="r", ls=":", lw=0.7)
    fig.tight_layout()
    fig.savefig(PLOTD / f"t01_{STEM[case]}_dm_bode.png", dpi=150)
    plt.close(fig)


def _plot_t02(plt, case, CMs, Hs, PLOTD):
    fig, a1 = plt.subplots(figsize=(9, 5.5))
    for port in ("ideal", "opa388", "kelvin"):
        rp = RAWD / f"t02_cm_{port}_{STEM[case]}.raw"
        if not rp.exists():
            continue
        pn = "pa1" if port != "kelvin" else "a1p"
        f, Vcm = load_single(rp, pn)
        a1.semilogx(f, db(Vcm), label=f"CM out ({port})")
        if port in CMs:
            _, HC = CMs[port]
            a1.semilogx(f, db(HC), ls="--", label=f"CM-to-DM ({port})")
    a1.set_xscale("log")
    a1.set_ylabel("dB rel 1V CM")
    a1.grid(True, which="both", alpha=0.3)
    a1.legend(fontsize=8)
    a1.set_title(f"T02 common-mode: output CM + CM-to-DM leakage - {case}")
    a1.axvline(FMOD, color="r", ls=":", lw=0.7)
    a1.set_xlabel("Hz")
    fig.tight_layout()
    fig.savefig(PLOTD / f"t02_{STEM[case]}_cm_leak.png", dpi=150)
    plt.close(fig)


def _plot_t03(plt, case, Hs, PLOTD):
    f0, H0 = Hs["opa388"]
    _, H1 = Hs["kelvin"]
    _, H0r = Hs["realsrc"]
    Hratio = H0 / H1
    Hratio_r = H0r / H1
    m = f0 <= 1e6
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
    a1.semilogx(f0[m], db(H0[m]), label="H0 (CH0)")
    a1.semilogx(f0[m], db(H1[m]), label="H1 (CH1 Kelvin)")
    a1.semilogx(f0[m], db(Hratio[m]), lw=2, label="H0/H1")
    a1.semilogx(f0[m], db(Hratio_r[m]), lw=1, ls="--", label="H0r/H1 (real-src)")
    a2.semilogx(f0[m], np.degrees(np.unwrap(np.angle(Hratio[m]))), label="phase H0/H1")
    a2.semilogx(f0[m], np.degrees(np.unwrap(np.angle(Hratio_r[m]))), ls="--",
                label="phase H0r/H1")
    a1.set_ylabel("dB")
    a1.grid(True, which="both", alpha=0.3)
    a1.legend(fontsize=8)
    a1.set_title(f"T03 channel match H0/H1 - {case}")
    a2.set_ylabel("phase deg")
    a2.set_xlabel("Hz")
    a2.grid(True, which="both", alpha=0.3)
    fig.tight_layout()
    fig.savefig(PLOTD / f"t03_{STEM[case]}_hratio.png", dpi=150)
    plt.close(fig)


def _plot_t10(plt, case, Hs, PLOTD):
    fig, a1 = plt.subplots(figsize=(9, 5))
    for port, lab in (("ideal", "L1 ideal"), ("opa388", "CH0 OPA388"),
                      ("kelvin", "CH1 Kelvin"), ("realsrc", "CH0 real-src")):
        f, H = Hs[port]
        ff, tau = group_delay(f, H)
        a1.semilogx(ff, tau * 1e6, label=lab)
    a1.set_ylabel("group delay us")
    a1.set_xlabel("Hz")
    a1.grid(True, which="both", alpha=0.3)
    a1.legend(fontsize=8)
    a1.set_title(f"T10 group delay 0.1Hz-16kHz - {case}")
    fig.tight_layout()
    fig.savefig(PLOTD / f"t10_{STEM[case]}_groupdelay.png", dpi=150)
    plt.close(fig)


# ----------------------------------------------------------------------
def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("cmd", nargs="?", default="all", choices=["gen", "run", "lint", "all"])
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--only", default="", help="仅跑指定 case（如 FO1_BASE）")
    args = ap.parse_args()

    global CASES
    if args.only:
        CASES = {k: v for k, v in run_all.CASES.items() if k == args.only}

    if args.cmd in ("gen", "all", "run", "lint"):
        for f in gen_all():
            pass
    if args.cmd == "lint":
        bad = 0
        for tid in GENS:
            for case in CASES:
                errs = run_all.lint_netlist(NET / f"{tid}_{STEM[case]}.net")
                if errs:
                    print(f"[lint] {tid}_{STEM[case]}: {errs}")
                    bad += len(errs)
        print(f"[lint] done, {bad} errors")
        return 1 if bad else 0
    if args.cmd in ("run", "all"):
        fails = run_all_nets(args.workers)
        if fails:
            print(f"[run] FAILED: {fails}")
    if args.cmd == "all":
        nv = analyze()
        if nv:
            print("[not-verified]", *nv, sep="\n  ")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
