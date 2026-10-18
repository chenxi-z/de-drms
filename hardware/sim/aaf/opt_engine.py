# -*- coding: utf-8 -*-
"""opt_engine.py — 抗混叠滤波器理论引擎 + 结构/参数优化
对称双线网络的模态分解：
  CM: 差分电容开路、Rin 不载 → 单边阶梯，C_i = Ccm_i
  DM: 差分电容 ×2、Rin/2=65k 接引脚到虚地 → 单边阶梯，C_i = Ccm_i + 2·Cdiff_i
传函/建立时间全部解析（RC 网络极点全实），LTspice 仅做终验。
"""
import numpy as np
from scipy.linalg import expm

RS = 1.0          # 源内阻（跟随器）
RL_DM = 65000.0   # DM: Rin 130k/2 到虚地
CPIN = 5e-12

def ladder_matrices(stages, mode, tol_r=0.0, tol_c=0.0):
    """阶梯：源—Rs—x0—R1—x1—...—R_N—xN(引脚)。节点数 = len(stages)+1。
    C_{i+1} 挂在 x_{i+1}。DM: C_eff=Ccm+2·Cdiff，xN 加 65k；CM: C_eff=Ccm。"""
    n = len(stages) + 1                      # 节点数
    G = np.zeros((n, n)); C = np.zeros(n); b = np.zeros(n)
    rs = 1.0 * (1 + tol_r)
    G[0, 0] += 1 / rs; b[0] += 1 / rs
    C[0] += 1e-12                            # 源节点走线寄生，稳定数值
    for i, (r, ccm, cdf) in enumerate(stages):
        r_ = r * (1 + tol_r)
        a, bb = i, i + 1
        G[a, a] += 1 / r_; G[bb, bb] += 1 / r_
        G[a, bb] -= 1 / r_; G[bb, a] -= 1 / r_
        c_eff = ccm * (1 + tol_c)
        if mode == "dm":
            c_eff += 2 * cdf * (1 + tol_c)
        C[bb] += c_eff
    if mode == "dm":
        G[n-1, n-1] += 1 / RL_DM
    C[n-1] += CPIN
    return G, np.diag(C), b

def H(stages, mode, f, tol_r=0.0, tol_c=0.0):
    """传函 |H(f)| 与相位（度），输出=引脚节点"""
    G, Cm, b = ladder_matrices(stages, mode, tol_r, tol_c)
    n = Cm.shape[0] - 1          # 引脚节点 = 最后一个
    out = []
    for w in 2 * np.pi * np.atleast_1d(f):
        v = np.linalg.solve(G + 1j * w * Cm, b)
        out.append(v[-1])
    return np.array(out)

def settle_time(stages, mode, band, tol_r=0.0, tol_c=0.0, tmax=5e-3):
    """阶跃 1V（源侧）后的引脚建立时间（绝对误差 band 伏）"""
    G, Cm, b = ladder_matrices(stages, mode, tol_r, tol_c)
    n = Cm.shape[0] - 1
    A = np.linalg.solve(Cm, G)
    vinf = np.linalg.solve(G, b)
    t = 0.0
    lo, hi = 0.0, tmax
    def err(tt):
        v = vinf + expm(-A * tt) @ (-vinf)
        return abs(v[-1] - vinf[-1])
    if err(lo) <= band:
        return 0.0
    if err(hi) > band:
        return float("inf")
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if err(mid) <= band:
            hi = mid
        else:
            lo = mid
    return hi

def atten_db(stages, mode, f, tol_r=0.0, tol_c=0.0):
    h = H(stages, mode, f, tol_r, tol_c)
    h0 = H(stages, mode, 10.0, tol_r, tol_c)[0]
    return float(20 * np.log10(np.abs(h[0]) / abs(h0)))

# ============ W9 锚点验证：理论 vs LTspice ============
W9 = [(1000, 8.2e-9, 8.2e-9), (220, 15e-9, 10e-9)]
if __name__ == "__main__":
    print("=== W9 理论 vs LTspice（probe 实测） ===")
    ltspice = {"dm_fmod": -102.0, "dm_mclk": -126.1, "cm_fmod": -85.1, "cm_mclk": -109.2,
               "s01": 484e-6, "s001": 649e-6}
    th_dm_fmod = atten_db(W9, "dm", 4.096e6)
    th_dm_mclk = atten_db(W9, "dm", 16.384e6)
    th_cm_fmod = atten_db(W9, "cm", 4.096e6)
    th_cm_mclk = atten_db(W9, "cm", 16.384e6)
    # LTspice 的 Berr 带宽是差模输出的 120µV → 单边 60µV
    th_s01 = settle_time(W9, "dm", 0.6e-3, tol_r=0.01, tol_c=0.05) * 1e6
    th_s001 = settle_time(W9, "dm", 60e-6, tol_r=0.01, tol_c=0.05) * 1e6
    rows = [
        ("DM@fMOD", th_dm_fmod, ltspice["dm_fmod"]),
        ("DM@MCLK", th_dm_mclk, ltspice["dm_mclk"]),
        ("CM@fMOD", th_cm_fmod, ltspice["cm_fmod"]),
        ("CM@MCLK", th_cm_mclk, ltspice["cm_mclk"]),
    ]
    for name, th, lt in rows:
        print(f"  {name:8s}: 理论 {th:8.2f} dB | LTspice {lt:8.2f} dB | 差 {abs(th-lt):.2f} dB")
    print(f"  settle0.1%: 理论 {th_s01:.0f} µs | LTspice {ltspice['s01']*1e6:.0f} µs")
    print(f"  settle0.01%: 理论 {th_s001:.0f} µs | LTspice {ltspice['s001']*1e6:.0f} µs")
