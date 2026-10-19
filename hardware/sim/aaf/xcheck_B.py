# -*- coding: utf-8 -*-
"""xcheck_B.py — 方案 B 的独立理论交叉验证（规格 §8：AC ≤0.5 dB、建立 ≤5%）

与 opt_round5.predict() 的区别（这是本文件存在的理由）：
  * opt_round5/opt_engine 的 ladder_matrices() 把源内阻硬编码为 **1 Ω**（opt_engine.py:20
    `rs = 1.0*(1+tol_r)`，注释为"源节点走线寄生"）。规格 §5.1 标准测试条件规定
    **V1–V6 源阻抗 0 Ω**，故交叉验证必须用 rs→0 的理论值，否则会凭空差出 1.54 dB。
  * CMRR 用真正的**双线 MNA**（两线各自 ±1% 失配），而不是单线 tol 近似。

用法：python xcheck_B.py
"""
from __future__ import annotations

import json
import math
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FMOD, MCLK = 4.096e6, 16.384e6
CPIN = 5e-12
RIN_DIFF = 130e3
RS = 1e-6          # 规格 §5.1：源阻抗 0 Ω（数值上取 1 µΩ 避免奇异）
# 规格 §5.1 D5 判据「0.01% 建立带」。V4 每线阶跃 1 V → 0.01% = 100 µV/线（差分 200 µV）。
# 注意：不能沿用 opt_engine 的 60 µV（那是 0.006%，比规格严 1.67×，会把 LTspice 判成超 5%）。
SETTLE_BAND = 100e-6


def two_line(stages, f, kr_a=1.0, kc_a=1.0, kr_b=1.0, kc_b=1.0,
             dm=True, rs=RS):
    """对称两线阶梯的全 MNA（复频域），返回各节点复电压。

    dm=True  → 差分激励（+1 V / −1 V，等价于 §5.1 的 1 V 差分）；
    dm=False → 共模激励（+1 V / +1 V），返回单线电压即可。
    """
    f = np.atleast_1d(np.asarray(f, dtype=float))
    n = len(stages) + 1
    N = 2 * n
    G = np.zeros((N, N))
    Cd = np.zeros(N)
    b = np.zeros(N)
    for sign, off, kr, kc in ((1.0, 0, kr_a, kc_a), (-1.0 if dm else 1.0, n, kr_b, kc_b)):
        G[off, off] += 1.0 / rs
        Cd[off] += 1e-12
        b[off] += sign / rs
        for i, (r, cg, cdf) in enumerate(stages):
            a, bb = off + i, off + i + 1
            rr = r * kr
            G[a, a] += 1.0 / rr
            G[bb, bb] += 1.0 / rr
            G[a, bb] -= 1.0 / rr
            G[bb, a] -= 1.0 / rr
            Cd[bb] += cg * kc + (2.0 * cdf * kc if dm else 0.0)
        Cd[off + n - 1] += CPIN
    if dm:
        G[n - 1, n - 1] += 2.0 / RIN_DIFF
        G[2 * n - 1, 2 * n - 1] += 2.0 / RIN_DIFF
    A = G[None, :, :] + 1j * 2 * math.pi * f[:, None, None] * np.diag(Cd)[None, :, :]
    return np.linalg.solve(A, np.broadcast_to(b[None, :], (len(f), N))[:, :, None])[:, :, 0]


def dm_gain_db(stages, f):
    """差分输出 / 差模输入 = (Vp−Vn)/2（激励为 ±1 V）。"""
    v = two_line(stages, f, dm=True)
    n = len(stages) + 1
    d = np.abs(v[:, n - 1] - v[:, 2 * n - 1]) / 2.0
    v0 = two_line(stages, 0.1, dm=True)
    d0 = abs(v0[0, n - 1] - v0[0, 2 * n - 1]) / 2.0
    return 20 * np.log10(d / d0)


def cm_gain_db(stages, f):
    v = two_line(stages, f, dm=False)
    n = len(stages) + 1
    g = np.abs(v[:, n - 1])
    g0 = abs(two_line(stages, 0.1, dm=False)[0, n - 1])
    return 20 * np.log10(g / g0)


def cmrr_db(stages, f_lo=10.0, f_hi=16e3, npts=200, mism=0.01):
    f = np.logspace(math.log10(f_lo), math.log10(f_hi), npts)
    v0 = two_line(stages, f, dm=False)
    v1 = two_line(stages, f, 1 + mism, 1 + mism, 1.0, 1.0, dm=False)
    n = len(stages) + 1
    cm = np.abs(v0[:, n - 1])
    dm = np.abs(v1[:, n - 1] - v1[:, 2 * n - 1])
    r = 20 * np.log10(cm / dm)
    return float(np.min(r)), float(f[int(np.argmin(r))])


def group_delay_us(stages, f_lo=0.1, f_hi=16e3, npts=400):
    f = np.logspace(math.log10(f_lo), math.log10(f_hi), npts)
    v = two_line(stages, f, dm=True)
    n = len(stages) + 1
    ph = np.unwrap(np.angle(v[:, n - 1] - v[:, 2 * n - 1]))
    tau = -np.gradient(ph, 2 * math.pi * f)
    return float((tau.max() - tau.min()) * 1e6), float(tau[0] * 1e6), float(tau[-1] * 1e6)


def settle_us(stages, kr=1.0, kc=1.0, band=SETTLE_BAND, tmax=5e-3):
    """阶跃 1 V（每线）后的 0.01% 建立时间（解析模态分解），返回 µs。

    判据口径与 LTspice V4 完全一致：**单线** |v_pin − v_∞| ≤ band（V4 两线对称，
    差分误差 = 2×单线误差；band=100 µV/线 即差分 200 µV = 2 V 阶跃的 0.01%）。
    """
    n = len(stages) + 1
    N = 2 * n
    G = np.zeros((N, N))
    Cd = np.zeros(N)
    b = np.zeros(N)
    for off in (0, n):
        G[off, off] += 1.0 / RS
        Cd[off] += 1e-12
        b[off] += 1.0 / RS
        for i, (r, cg, cdf) in enumerate(stages):
            a, bb = off + i, off + i + 1
            rr = r * kr
            G[a, a] += 1.0 / rr
            G[bb, bb] += 1.0 / rr
            G[a, bb] -= 1.0 / rr
            G[bb, a] -= 1.0 / rr
            Cd[bb] += cg * kc + 2.0 * cdf * kc
        Cd[off + n - 1] += CPIN
        G[off + n - 1, off + n - 1] += 2.0 / RIN_DIFF
    vinf = np.linalg.solve(G, b)
    A = G / Cd[:, None]
    lam, V = np.linalg.eig(A)
    lam, V = np.real(lam), np.real(V)
    w = np.linalg.solve(V, -vinf)

    def err(t):
        return abs((vinf + V @ (np.exp(-lam * t) * w))[-1] - vinf[-1])

    if err(tmax) > band:
        return float("inf")
    lo, hi = 0.0, tmax
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if err(mid) <= band:
            hi = mid
        else:
            lo = mid
    return hi * 1e6


def noise_nv(stages, f_lo=0.1, f_hi=FMOD / 2, npts=400):
    """全部电阻约翰逊噪声 → 差分输出的积分噪声（nVrms）。"""
    K_B, T_K = 1.380649e-23, 298.15
    n = len(stages) + 1
    N = 2 * n
    G = np.zeros((N, N))
    Cd = np.zeros(N)
    for off in (0, n):
        G[off, off] += 1.0 / RS
        Cd[off] += 1e-12
        for i, (r, cg, cdf) in enumerate(stages):
            a, bb = off + i, off + i + 1
            G[a, a] += 1.0 / r
            G[bb, bb] += 1.0 / r
            G[a, bb] -= 1.0 / r
            G[bb, a] -= 1.0 / r
            Cd[bb] += cg + 2.0 * cdf
        Cd[off + n - 1] += CPIN
        G[off + n - 1, off + n - 1] += 2.0 / RIN_DIFF

    f = np.logspace(math.log10(f_lo), math.log10(f_hi), npts)
    A = G[None, :, :] + 1j * 2 * math.pi * f[:, None, None] * np.diag(Cd)[None, :, :]

    # 每个电阻的噪声电流注入向量 + 电阻值
    inj, rvals = [], []
    for off in (0, n):
        for i, (r, _cg, _cd) in enumerate(stages):
            v = np.zeros(N)
            v[off + i], v[off + i + 1] = 1.0, -1.0
            inj.append(v)
            rvals.append(r)
        v = np.zeros(N)
        v[off + n - 1] = 1.0
        inj.append(v)
        rvals.append(RIN_DIFF / 2.0)
    B = np.stack(inj, axis=1)
    X = np.linalg.solve(A, np.broadcast_to(B[None, :, :], (len(f), N, B.shape[1])))
    psd = np.zeros(len(f))
    for j, rr in enumerate(rvals):
        # 注入向量是"单位串联电压"，等效电流 = 1/rr → 传函须除以 rr 才是 V/A
        ntf = (X[:, n - 1, j] - X[:, 2 * n - 1, j]) / rr
        psd += 4 * K_B * T_K * rr * np.abs(ntf) ** 2
    return math.sqrt(float(np.trapz(psd, f))) * 1e9


def predict_zero_source(stages):
    return {
        "A_dm": -float(dm_gain_db(stages, FMOD)[0]),
        "A_cm": -float(cm_gain_db(stages, FMOD)[0]),
        "A_mclk": -float(dm_gain_db(stages, MCLK)[0]),
        "dG_16k": abs(float(dm_gain_db(stages, 16e3)[0])),
        "t_settle_wc_us": settle_us(stages, 1.01, 1.05),
        "t_settle_nom_us": settle_us(stages, 1.0, 1.0),
        "CMRR_pb_db": cmrr_db(stages)[0],
        "Vn_nv": noise_nv(stages),
        "dtau_us": group_delay_us(stages)[0],
    }


if __name__ == "__main__":
    cand = json.load(open(os.path.join(HERE, "r5_candidates.json"), encoding="utf-8"))["B"]
    st = [tuple(map(float, s)) for s in cand["stages"]]
    print("方案 B  理论（源阻抗 0 Ω，双线 MNA）")
    for k, v in predict_zero_source(st).items():
        print(f"  {k:20s} {v:10.4f}")
    print("\n对照：opt_round5.predict()（源内阻硬编码 1 Ω）")
    for k in ("A_dm", "A_cm", "A_mclk", "dG_16k", "CMRR_pb_db", "V_n_lsb"):
        print(f"  {k:14s} {cand['pred'][k]:10.4f}")
