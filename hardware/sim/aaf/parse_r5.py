#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""parse_r5.py — Round 5 LTspice ASCII .raw 解析 + 十维实测值提取

复用 `parse_and_plot.py` 的头部/点索引处理（本文件独立实现，避免其模块级副作用），
对 LTspice `-b -ascii` 的 `.raw` 求：
  D1/D2/D3  AC 增益 @fMOD / @MCLK（dB，正值 = 衰减量）
  D4        |ΔG@16 kHz|（dB，相对 DC）
  D5        0.01% 建立时间（µs；2 V 阶跃 → 200 µV 带 = 规格字面 0.01%；
            另报引擎口径 120 µV 带，供 §8 对拍）
  D6        积分噪声 0.1 Hz ~ fMOD/2（nVrms，差分；另给 LSB）
  D7        MC 30 次 16 kHz 增益偏差 σ（dB）
  D8        CMRR @通带最差值（dB）
  D9        kickback 122.07 ns 内回稳（0.01% 带）→ 1.0 / 0.0
  D10       群延迟 0.1 Hz~16 kHz 变化量 Δτ（µs）

用法： python parse_r5.py --cand C
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import re

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))

LSB_V = 2.0 * 2.442 / 2 ** 24          # 290.98 nV（规格 §5.1 单位约定）
FMOD = 4.096e6
MCLK = 16.384e6
KB_WIN_S = 0.5 / FMOD                  # 122.07 ns
TBAND_DIFF = 120e-6                    # 引擎口径（60 µV 单边 ×2）
TBAND_SPEC = 200e-6                    # 规格口径：2 V 阶跃 × 0.01% = 200 µV（差分）


# ------------------------------------------------------------------ raw 读取
class Raw:
    """LTspice ASCII .raw：头部（Flags/No. Variables/No. Points/Variables）+ 点表。"""

    def __init__(self, path):
        txt = open(path, "r", encoding="ascii", errors="replace").read()
        i = txt.find("Values:")
        if i < 0:
            raise RuntimeError("no 'Values:' in " + path)
        head, body = txt[:i], txt[i + len("Values:"):]
        self.path = path
        self.flags = ""
        self.nvars = self.npts = 0
        self.names = []
        self.title = ""
        self.plotname = ""
        in_vars = False
        for line in head.splitlines():
            s = line.strip()
            if s.startswith("Title:"):
                self.title = s.split(":", 1)[1].strip()
            elif s.startswith("Plotname:"):
                self.plotname = s.split(":", 1)[1].strip()
            elif s.startswith("Flags:"):
                self.flags = s.split(":", 1)[1].strip()
            elif s.startswith("No. Variables:"):
                self.nvars = int(s.split(":")[1])
            elif s.startswith("No. Points:"):
                self.npts = int(s.split(":")[1])
            elif s == "Variables:":
                in_vars = True
            elif in_vars:
                parts = line.split("\t")
                if len(parts) >= 3 and parts[2].strip():
                    self.names.append(parts[2].strip())
        self.complex = "complex" in self.flags

        vals = []
        for line in body.splitlines():
            if not line.strip():
                continue
            toks = line.replace("\t", " ").split()
            if line.startswith("\t"):
                for tok in toks:
                    vals.append(self._num(tok))
            else:
                # 每个点首行： "idx<TAB><TAB>val" → 取最后一个 token
                vals.append(self._num(toks[-1]))
        need = self.npts * self.nvars
        vals = vals[:need]
        self.cols = [vals[k::self.nvars] for k in range(self.nvars)]

    def _num(self, tok):
        if "," in tok:
            a, b = tok.split(",")
            return complex(float(a), float(b))
        return float(tok)

    def idx(self, name):
        for i, n in enumerate(self.names):
            if n.lower() == name.lower():
                return i
        raise KeyError(f"{name} not in {self.names}")

    def col(self, name):
        return self.cols[self.idx(name)]

    @property
    def f(self):
        return np.array([v.real if isinstance(v, complex) else v
                         for v in self.cols[0]], dtype=float)


def db(x):
    a = abs(x)
    return 20 * math.log10(a) if a > 0 else -999.0


def interp_at(raw: Raw, f_target: float, name="V(pa4)"):
    """在 log-f 网格上线性插值取指定频率的复数值（AC 分析为对数刻度）。"""
    f = raw.f
    y = np.array(raw.col(name))
    if f_target <= f[0]:
        return y[0]
    if f_target >= f[-1]:
        return y[-1]
    lx = np.log(f)
    j = int(np.searchsorted(lx, math.log(f_target)))
    j = max(1, min(j, len(f) - 1))
    w = (math.log(f_target) - lx[j - 1]) / (lx[j] - lx[j - 1])
    return y[j - 1] * (1 - w) + y[j] * w


def pin_names(stages):
    n = len(stages)
    return f"V(pa{n})", f"V(na{n})"


# ------------------------------------------------------------------ 各维提取
def d1_d3_d4_d10(raw_v1, nstage):
    pa, na = pin_names(range(nstage))
    f = raw_v1.f
    p = np.array(raw_v1.col(pa), dtype=complex)
    n = np.array(raw_v1.col(na), dtype=complex)
    d = p - n
    dc = interp_at(raw_v1, 0.1, pa) - interp_at(raw_v1, 0.1, na)
    g_dc = db(dc)
    out = {}
    out["g_dc_db"] = g_dc
    out["g_16k_db"] = db(interp_at(raw_v1, 16e3, pa) - interp_at(raw_v1, 16e3, na))
    out["D4_dG_16k_db"] = abs(out["g_16k_db"] - g_dc)
    out["D1_A_dm_db"] = -(db(interp_at(raw_v1, FMOD, pa) - interp_at(raw_v1, FMOD, na)) - g_dc)
    out["D3_A_mclk_db"] = -(db(interp_at(raw_v1, MCLK, pa) - interp_at(raw_v1, MCLK, na)) - g_dc)

    # D10：群延迟 = −dφ/dω，在 0.1 Hz~16 kHz 的 log 网格上求数值微分
    m = (f >= 0.1) & (f <= 16e3)
    ff = f[m]
    ph = np.unwrap(np.angle(d[m]))
    tau = -np.gradient(ph, 2 * math.pi * ff)
    out["D10_dtau_us"] = float((tau.max() - tau.min()) * 1e6)
    out["tau_at_100Hz_us"] = float(tau[0] * 1e6)
    out["tau_at_16k_us"] = float(tau[-1] * 1e6)
    return out


def d2(raw_v2, nstage):
    pa, _ = pin_names(range(nstage))
    dc = db(interp_at(raw_v2, 0.1, pa))
    g = db(interp_at(raw_v2, FMOD, pa))
    return {"D2_A_cm_db": -(g - dc), "g_cm_dc_db": dc, "g_cm_fmod_db": g}


def d8(raw_v3, nstage):
    """CMRR = 20log10(|Vcm_out| / |Vdiff_out|)，取 10 Hz~16 kHz 最差。"""
    pa, na = pin_names(range(nstage))
    f = raw_v3.f
    p = np.array(raw_v3.col(pa), dtype=complex)
    n = np.array(raw_v3.col(na), dtype=complex)
    m = (f >= 10) & (f <= 16e3)
    cm = np.abs(p[m])
    dm = np.abs(p[m] - n[m])
    with np.errstate(divide="ignore"):
        cmrr = 20 * np.log10(cm / dm)
    k = int(np.argmin(cmrr))
    return {"D8_CMRR_db": float(cmrr[k]), "D8_worst_f_hz": float(f[m][k]),
            "cmrr_10": float(cmrr[0]), "cmrr_16k": float(cmrr[-1])}


def settle_us(raw, nstage, band=TBAND_DIFF, t_step=10e-6, t_end=None):
    """差分 0.01% 建立时间（µs）。返回 (t_us, vfinal, err_final)。"""
    pa, na = pin_names(range(nstage))
    t = np.array([v.real if isinstance(v, complex) else v for v in raw.cols[0]], dtype=float)
    p = np.array(raw.col(pa), dtype=float)
    n = np.array(raw.col(na), dtype=float)
    d = p - n
    if t_end is None:
        t_end = t[-1]
    m = t >= t_step
    tt, dd = t[m], d[m]
    vf = float(dd[-1])
    err = np.abs(dd - vf)
    # 最后一次超出带外的时刻
    outside = np.where(err > band)[0]
    if len(outside) == 0:
        return 0.0, vf, float(err.min())
    k = outside[-1]
    if k >= len(tt) - 1:
        return float("inf"), vf, float(err[-1])
    # 线性插值跨带点
    t0, t1 = tt[k], tt[k + 1]
    e0, e1 = err[k], err[k + 1]
    tc = t0 + (t1 - t0) * (e0 - band) / (e0 - e1) if e0 != e1 else t1
    return float((tc - t_step) * 1e6), vf, float(err[-1])


def noise_nv(raw):
    """.noise 输出：v(onoise) 是 V/√Hz（差分输出谱密度）。trapz 积分 → nVrms。"""
    f = np.array([v.real if isinstance(v, complex) else v for v in raw.cols[0]], dtype=float)
    dens = np.abs(np.array(raw.col("v(onoise)")))
    fmax = min(FMOD / 2, f[-1])
    m = f <= fmax
    tot = math.sqrt(float(np.trapz(dens[m] ** 2, f[m])))
    return {"D6_Vn_nv": tot * 1e9, "D6_Vn_lsb": tot / LSB_V,
            "D6_Vn_uv": tot * 1e6, "f_max_hz": float(f[m][-1]),
            "dens_1k_nv": float(np.interp(1e3, f, dens) * 1e9)}


# ------------------------------------------------------------------ V8 kickback
def kickback(raw, nstage, tol=1e-4):
    """D9：fMOD 半周期（122.07 ns）窗内是否回稳到**稳态值的 0.01% 带**。

    规格 sec 5.1 / sec 7 原文：「fMOD 半周期（122 ns）内回稳到 0.01% 带内」、
    「判据 = 回稳到稳态值 0.01% 带内」→ 参考量是**采样节点稳态值**：
        |v_pin(t_end) − v_ss| ≤ 0.01% × |v_ss|
    同时输出三项旁证供核查：相对 kick 幅度的残余比、相对满量程的残余、窗口内峰值。

    窗口起点 = S1 导通沿（t = k·t_MOD），窗口长 = t_MOD/2 = 122.07 ns（M6：各占 50%）。
    """
    pa, _ = pin_names(range(nstage))
    t = np.array([v.real if isinstance(v, complex) else v for v in raw.cols[0]], dtype=float)
    p = np.array(raw.col(pa), dtype=float)
    T = 1.0 / FMOD
    rows = []
    k = 2
    while True:
        t_on = k * T
        t_end = t_on + KB_WIN_S
        if t_end > t[-1] - 2 * T:
            break
        m = (t >= t_on) & (t <= t_end)
        if m.sum() < 30:
            break
        seg_t, seg_v = t[m], p[m]
        ntail = max(5, int(0.10 * len(seg_v)))
        v_ss = float(np.mean(seg_v[-ntail:]))
        # 本次采样注入的 kick 幅度（窗口 ±2 ns 的台阶），仅作旁证
        amp = abs(float(np.interp(t_on + 2e-9, t, p)) - float(np.interp(t_on - 2e-9, t, p)))
        e_end = abs(float(seg_v[-1]) - v_ss)
        e_max = float(np.max(np.abs(seg_v - v_ss)))
        rows.append({
            "k": k, "t_on_ns": round(t_on * 1e9, 2), "v_ss": v_ss,
            "kick_amp_uv": amp * 1e6,
            "resid_end_uv": e_end * 1e6, "resid_max_uv": e_max * 1e6,
            "rel_to_ss": e_end / abs(v_ss) if v_ss else 0.0,
            "rel_to_fs": e_end / 2.442,
            "rel_to_kick": e_end / amp if amp > 0 else 0.0,
            "pass": bool(e_end <= tol * abs(v_ss)),
        })
        k += 1
    if not rows:
        return {"D9": 0.0, "note": "no complete cycle found", "detail": []}
    worst = max(rows, key=lambda r: r["rel_to_ss"])
    return {"D9": 1.0 if all(r["pass"] for r in rows) else 0.0,
            "criterion": "residual <= 0.01% of steady-state value within 122.07 ns",
            "n_cycles": len(rows),
            "worst_resid_uv": worst["resid_end_uv"],
            "worst_rel_to_ss": worst["rel_to_ss"],
            "worst_rel_to_fs": worst["rel_to_fs"],
            "worst_rel_to_kick": worst["rel_to_kick"],
            "kick_amp_uv": worst["kick_amp_uv"],
            "detail": rows[:3]}


# ------------------------------------------------------------------ 汇总
def _ch_delay(raw, ns):
    """CH1/CH2 群延迟差专项（规格 sec 5.1a 要求单列）：两线各自 16 kHz 群延迟之差。"""
    pa, na = pin_names(range(ns))
    f = raw.f
    m = (f >= 0.1) & (f <= 16e3)
    out = {}
    for nm, key in ((pa, "tau_p_16k_us"), (na, "tau_n_16k_us")):
        ph = np.unwrap(np.angle(np.array(raw.col(nm), dtype=complex)[m]))
        tau = -np.gradient(ph, 2 * math.pi * f[m])
        out[key] = float(tau[-1] * 1e6)
    out["CH_tau_diff_us"] = out["tau_p_16k_us"] - out["tau_n_16k_us"]
    return out


def crosscheck(key, ns, d, mirror, res) -> dict:
    """规格 sec 8：AC 偏差 ≤0.5 dB、建立偏差 ≤5%。

    对拍对象 = **镜像口径（rs = 1 Ω 网表）**的 LTspice 结果 vs 理论预测，
    因为引擎 `opt_engine.ladder_matrices()` 把 rs 硬编码 1 Ω。0 Ω 口径的实测在
    ``res['dims']`` 里，是评分口径，不参与本判据（两口径 @fMOD 可差 2 dB）。
    """
    th = res["theory_pred"]
    out = {"mirror_dir": mirror, "rs_mirror_ohm": 1.0,
           "note": "引擎 rs 硬编码 1 Ω；镜像网表同取 1 Ω 后对拍（规格 0 Ω 口径见 dims）",
           "ac_rows": []}
    if not mirror or not os.path.isdir(mirror):
        out["pass"] = False
        out["reason"] = "镜像口径目录缺失，未做同口径对拍"
        return out

    def Rd(tag):
        q = os.path.join(mirror, f"r5_{key}_{tag}.raw")
        return Raw(q) if os.path.exists(q) else None

    r1, r2 = Rd("v1"), Rd("v2")
    pa, na = pin_names(range(ns))
    if r1 is not None:
        dc = interp_at(r1, 0.1, pa) - interp_at(r1, 0.1, na)
        lt = {
            "D1 A_dm@fMOD": -(db(interp_at(r1, FMOD, pa) - interp_at(r1, FMOD, na)) - db(dc)),
            "D3 A_mclk@MCLK": -(db(interp_at(r1, MCLK, pa) - interp_at(r1, MCLK, na)) - db(dc)),
            "D4 dG@16k": abs(db(interp_at(r1, 16e3, pa) - interp_at(r1, 16e3, na)) - db(dc)),
        }
        for item, key_th in (("D1 A_dm@fMOD", "A_dm"), ("D3 A_mclk@MCLK", "A_mclk"),
                             ("D4 dG@16k", "dG_16k")):
            dv = abs(lt[item] - th[key_th])
            out["ac_rows"].append({"item": item, "theory": th[key_th],
                                   "ltspice": lt[item], "abs_diff": dv,
                                   "pass": bool(dv <= 0.5)})
    if r2 is not None:
        lv = -db(interp_at(r2, FMOD, pa))
        dv = abs(lv - th["A_cm"])
        out["ac_rows"].append({"item": "D2 A_cm@fMOD", "theory": th["A_cm"],
                               "ltspice": lv, "abs_diff": dv, "pass": bool(dv <= 0.5)})
    out["worst_ac_diff_db"] = max((r["abs_diff"] for r in out["ac_rows"]), default=None)

    # 建立：镜像口径 V4（corner）vs 引擎 settle_wc（同 120 µV 带）
    q4 = os.path.join(mirror, f"r5_{key}_v4.raw")
    if os.path.exists(q4):
        lt_us, _, _ = settle_us(Raw(q4), ns, band=TBAND_DIFF)
        th_us = th["t_settle_wc_s"] * 1e6
        rel = abs(lt_us - th_us) / th_us if th_us else float("inf")
        out["settle"] = {"theory_us": th_us, "ltspice_us": lt_us,
                         "rel_diff": rel, "pass": bool(rel <= 0.05)}

    # 噪声：V7 实测 vs 引擎 V_n_lsb
    if "D6_Vn_lsb" in res:
        lt = res["D6_Vn_lsb"]
        th_ = th["V_n_lsb"]
        rel = abs(lt - th_) / th_ if th_ else float("inf")
        out["noise"] = {"theory_lsb": th_, "ltspice_lsb": lt,
                        "rel_diff": rel, "pass": bool(rel <= 0.05)}

    out["pass"] = bool(all(r["pass"] for r in out["ac_rows"])
                       and out.get("settle", {}).get("pass", False))
    return out


def analyze(key: str, d: str = HERE, mirror: str = "") -> dict:
    """解析一套 .raw（d = 规格 0 Ω 口径），可选对拍镜像口径（mirror = rs 1 Ω 目录）。

    **两套口径为什么必须分开**（AGENTS「并发写同一文件」留痕 + 本次实测）：
      * 规格 sec 5.1 明写「V1–V6 源阻抗 0 Ω」→ d 目录网表按 0 Ω 生成，**这是评分口径**；
      * 理论引擎把 rs 硬编码 1 Ω → mirror 目录按 1 Ω 生成，**只用于 sec 8 交叉验证**；
      * C 案 ΣR 仅 19 Ω，1 Ω 源内阻占比大，两口径 @fMOD 差 2.1 dB —— 混比会假报"交叉验证失败"。
    """
    with open(os.path.join(HERE, "r5_candidates.json"), encoding="utf-8") as fh:
        cand = json.load(fh)[key]
    ns = len(cand["stages"])
    res = {"candidate": key, "n_stages": ns, "stages": cand["stages"],
           "theory_pred": cand["pred"], "dir": d, "raw": {}}
    pa, na = pin_names(range(ns))

    def has(tag):
        return os.path.exists(os.path.join(d, f"r5_{key}_{tag}.raw"))

    # ---------------- V1 / V2 / V3（AC）
    if has("v1"):
        r1 = Raw(os.path.join(d, f"r5_{key}_v1.raw"))
        v1 = d1_d3_d4_d10(r1, ns)
        v1.update(_ch_delay(r1, ns))
        res["V1"] = v1
        res["raw"]["V1"] = r1.path
        for k in ("g_dc_db", "g_16k_db", "D4_dG_16k_db", "D1_A_dm_db", "D3_A_mclk_db",
                  "D10_dtau_us", "tau_at_100Hz_us", "tau_at_16k_us", "CH_tau_diff_us",
                  "tau_p_16k_us", "tau_n_16k_us"):
            res[k] = v1[k]
    if has("v2"):
        r2 = Raw(os.path.join(d, f"r5_{key}_v2.raw"))
        res["V2"] = d2(r2, ns)
        res["raw"]["V2"] = r2.path
        res["D2_A_cm_db"] = res["V2"]["D2_A_cm_db"]
    if has("v3"):
        r3 = Raw(os.path.join(d, f"r5_{key}_v3.raw"))
        res["V3"] = d8(r3, ns)
        res["raw"]["V3"] = r3.path
        res["D8_CMRR_db"] = res["V3"]["D8_CMRR_db"]

    # ---------------- V4 / V4b（瞬态建立）
    def do_settle(tag):
        q = os.path.join(d, f"r5_{key}_{tag}.raw")
        if not os.path.exists(q):
            return None
        rr = Raw(q)
        ts, vf, ef = settle_us(rr, ns, band=TBAND_SPEC)
        te, _, _ = settle_us(rr, ns, band=TBAND_DIFF)
        return {"tset_us": ts, "tset_engine_band_us": te, "vfinal_v": vf,
                "err_final_uv": ef * 1e6, "raw": q}

    res["V4"] = do_settle("v4")
    res["V4b"] = do_settle("v4b")
    if res["V4"]:
        res["raw"]["V4"] = res["V4"]["raw"]
        res["D5_tset_us"] = res["V4"]["tset_us"]
    if res["V4b"]:
        res["raw"]["V4b"] = res["V4b"]["raw"]

    # ---------------- V5（MC AC ×30）
    g16 = []
    for k in range(1, 31):
        q = os.path.join(d, f"r5_{key}_v5mc{k:02d}.raw")
        if not os.path.exists(q):
            continue
        rr = Raw(q)
        dc = interp_at(rr, 0.1, pa) - interp_at(rr, 0.1, na)
        g = interp_at(rr, 16e3, pa) - interp_at(rr, 16e3, na)
        g16.append(db(g) - db(dc))
    if g16:
        res["V5"] = {"n": len(g16), "sigma_db": float(np.std(g16, ddof=1)),
                     "mean_db": float(np.mean(g16)), "min_db": float(np.min(g16)),
                     "max_db": float(np.max(g16)),
                     "p2p_db": float(np.max(g16) - np.min(g16))}
        res["D7_sigma_dG_db"] = res["V5"]["sigma_db"]

    # ---------------- V6（MC 瞬态 ×30）
    tl = []
    for k in range(1, 31):
        q = os.path.join(d, f"r5_{key}_v6mc{k:02d}.raw")
        if not os.path.exists(q):
            continue
        tk, _, _ = settle_us(Raw(q), ns, band=TBAND_SPEC)
        tl.append(tk)
    if tl:
        res["V6"] = {"n": len(tl), "min_us": float(np.min(tl)),
                     "mean_us": float(np.mean(tl)), "max_us": float(np.max(tl))}

    # ---------------- V7（噪声）
    if has("v7"):
        r7 = Raw(os.path.join(d, f"r5_{key}_v7.raw"))
        res["V7"] = noise_nv(r7)
        res["raw"]["V7"] = r7.path
        res["D6_Vn_nv"] = res["V7"]["D6_Vn_nv"]
        res["D6_Vn_lsb"] = res["V7"]["D6_Vn_lsb"]

    # ---------------- V8（kickback：Ron = 1 / 100 / 1000 Ω）
    kb = {}
    for ron in (1, 100, 1000):
        q = os.path.join(d, f"r5_{key}_v8_ron{ron:g}.raw")
        if os.path.exists(q):
            kb[f"ron{ron:g}"] = kickback(Raw(q), ns)
    if kb:
        res["V8"] = kb
        res["D9"] = kb["ron1"]["D9"] if "ron1" in kb else list(kb.values())[0]["D9"]
        res["raw"]["V8"] = os.path.join(d, f"r5_{key}_v8_ron1.raw")

    # ---------------- V9（真实 OPA388）
    v9 = {}
    q = os.path.join(d, f"r5_{key}_v9a.raw")
    if os.path.exists(q):
        rr = Raw(q)
        dc = interp_at(rr, 0.1, pa) - interp_at(rr, 0.1, na)
        v9.update({
            "A_dm": -(db(interp_at(rr, FMOD, pa) - interp_at(rr, FMOD, na)) - db(dc)),
            "A_mclk": -(db(interp_at(rr, MCLK, pa) - interp_at(rr, MCLK, na)) - db(dc)),
            "dG_16k": abs(db(interp_at(rr, 16e3, pa) - interp_at(rr, 16e3, na)) - db(dc)),
            "raw_v9a": q})
        res["raw"]["V9a"] = q
    q = os.path.join(d, f"r5_{key}_v9b.raw")
    if os.path.exists(q):
        v9["A_cm"] = -db(interp_at(Raw(q), FMOD, pa))
    for tag, kk in (("v9c", "t_settle_us"), ("v9f", "t_settle_us_600k")):
        q = os.path.join(d, f"r5_{key}_{tag}.raw")
        if os.path.exists(q):
            tk, _, _ = settle_us(Raw(q), ns, band=TBAND_SPEC)
            v9[kk] = tk
            v9["raw_" + tag] = q
            res["raw"][tag.upper()] = q
    q = os.path.join(d, f"r5_{key}_v9d.raw")
    if os.path.exists(q):
        v9["Vn_nv"] = noise_nv(Raw(q))["D6_Vn_nv"]
    q = os.path.join(d, f"r5_{key}_v9e.raw")
    if os.path.exists(q):
        rr = Raw(q)
        dc = interp_at(rr, 0.1, pa) - interp_at(rr, 0.1, na)
        v9["A_dm_600k"] = -(db(interp_at(rr, FMOD, pa) - interp_at(rr, FMOD, na)) - db(dc))
        v9["A_mclk_600k"] = -(db(interp_at(rr, MCLK, pa) - interp_at(rr, MCLK, na)) - db(dc))
    if v9:
        res["V9"] = v9

    # ---------------- 十维实测
    dims = {}
    for src, dst in (("D1_A_dm_db", "D1"), ("D2_A_cm_db", "D2"), ("D3_A_mclk_db", "D3"),
                     ("D4_dG_16k_db", "D4"), ("D5_tset_us", "D5"), ("D6_Vn_nv", "D6"),
                     ("D7_sigma_dG_db", "D7"), ("D8_CMRR_db", "D8"), ("D9", "D9"),
                     ("D10_dtau_us", "D10")):
        if src in res:
            dims[dst] = res[src]
    res["dims"] = dims

    res["xcheck"] = crosscheck(key, ns, d, mirror, res)
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cand", default="C")
    ap.add_argument("--dir", default=HERE)
    ap.add_argument("--mirror", default="")
    ap.add_argument("--json", default="")
    args = ap.parse_args(argv)
    res = analyze(args.cand, args.dir, args.mirror)
    for k, v in res.items():
        if k in ("raw", "V8", "theory_pred", "stages", "V1", "V2", "V3", "V4",
                 "V4b", "V5", "V6", "V7", "V9", "xcheck"):
            continue
        print(f"  {k:22s} {v}")
    print("\nxcheck:", json.dumps(res["xcheck"], ensure_ascii=False, indent=1))
    if args.json:
        with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(res, fh, ensure_ascii=False, indent=2)
        print("→", args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
