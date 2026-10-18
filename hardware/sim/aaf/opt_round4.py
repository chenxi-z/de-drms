# -*- coding: utf-8 -*-
"""opt_round4.py — 结构/参数联合优化（理论引擎快评 + Nelder-Mead 多起点）
目标：max min( DM/80, CM/60, MCLK/120, 900/t001_worst )，硬约束见 obj()。
"""
import numpy as np
import math
from scipy.optimize import minimize
from opt_engine import atten_db, settle_time

BUDGET_US = 900.0
MARGIN_LINES = {"dm_fmod": 80.0, "cm_fmod": 60.0, "dm_mclk": 120.0}

def margins(stages, rsum_max=5000.0):
    rsum = sum(s[0] for s in stages)
    n_parts = 2 * len(stages) + sum(2 if s[1] > 0 else 0 for s in stages) + sum(1 if s[2] > 0 else 0 for s in stages)
    if rsum > rsum_max or n_parts > 14:
        return None, None, n_parts, rsum
    if any(c > 47e-9 for s in stages for c in (s[1], s[2])):
        return None, None, n_parts, rsum          # C0G 实际上限 47nF
    try:
        dm = -atten_db(stages, "dm", 4.096e6)
        cm = -atten_db(stages, "cm", 4.096e6)
        mk = -atten_db(stages, "dm", 16.384e6)
        t001_w = settle_time(stages, "dm", 60e-6, tol_r=0.01, tol_c=0.05) * 1e6  # 秒→µs，容差最坏角
    except Exception:
        return None, None, n_parts, rsum
    if not np.isfinite(t001_w) or t001_w > BUDGET_US:
        return None, None, n_parts, rsum
    m = {"dm": dm / MARGIN_LINES["dm_fmod"], "cm": cm / MARGIN_LINES["cm_fmod"],
         "mk": mk / MARGIN_LINES["dm_mclk"], "st": BUDGET_US / t001_w, "pt": 14.0 / n_parts}
    return min(m.values()), m, n_parts, rsum

def obj(x, nst):
    stages = []
    for i in range(nst):
        r = math.exp(x[3 * i]); ccm = math.exp(x[3 * i + 1]); cdf = math.exp(x[3 * i + 2])
        stages.append((r, ccm, cdf))
    if stages[0][0] < 200 or stages[0][0] > 4000:
        return 10.0
    mm, _, _, _ = margins(stages)
    if mm is None:
        return 10.0
    return -mm

import math
BOUNDS2 = [(math.log(300), math.log(2500)), (math.log(3e-9), math.log(33e-9)), (math.log(2e-9), math.log(22e-9)),
           (math.log(68), math.log(1200)), (math.log(6.8e-9), math.log(68e-9)), (math.log(3.3e-9), math.log(47e-9))]
BOUNDS3 = BOUNDS2 + [(math.log(33), math.log(900)), (math.log(6.8e-9), math.log(68e-9)), (math.log(1e-12), math.log(33e-9))]

starts2 = [
    [1000, 8.2e-9, 8.2e-9, 220, 15e-9, 10e-9],       # W9
    [1000, 8.2e-9, 0, 220, 15e-9, 10e-9],            # W11
    [1000, 15e-9, 4.7e-9, 330, 22e-9, 10e-9],        # V6r2 近亲
    [680, 4.7e-9, 4.7e-9, 470, 22e-9, 15e-9],
    [1500, 10e-9, 3.3e-9, 300, 33e-9, 6.8e-9],
]
starts3 = [
    [1000, 4.7e-9, 4.7e-9, 470, 10e-9, 10e-9, 100, 22e-9, 1e-12],     # W3
    [1000, 2.2e-9, 2.2e-9, 470, 4.7e-9, 4.7e-9, 100, 10e-9, 10e-9],  # W4
    [1500, 4.7e-9, 4.7e-9, 560, 10e-9, 10e-9, 150, 15e-9, 1e-12],
]

results = []
for nst, bounds, starts in [(2, BOUNDS2, starts2), (3, BOUNDS3, starts3)]:
    for si, s0 in enumerate(starts):
        x0 = [math.log(max(v, 1e-12)) for v in s0]
        res = minimize(obj, x0, args=(nst,), method="Nelder-Mead",
                       options={"maxiter": 1200, "xatol": 1e-3, "fatol": 1e-4})
        stages = [tuple(math.exp(res.x[3*i + k]) for k in range(3)) for i in range(nst)]
        mm, m, nparts, rsum = margins(stages)
        if mm is not None:
            results.append((mm, nst, stages, m, nparts, rsum, res.fun))
    print(f"{nst}-stage 扫完")

results.sort(key=lambda t: -t[0])
print("\n=== 连续优化 Top 8（理论快评，min-margin 越大越好） ===")
seen = set()
shown = 0
for mm, nst, stages, m, nparts, rsum, _ in results:
    key = tuple(round(v, 2) for s in stages for v in s)
    if key in seen:
        continue
    seen.add(key)
    stg = "—".join(f"{r:.0f}R/({c*1e9:.1f}n+{d*1e9:.1f}nd)" for r, c, d in stages)
    print(f"minM={mm:.3f}  {stg}  [DM {m['dm']*80:.0f} CM {m['cm']*60:.0f} MCLK {m['mk']*120:.0f} t001w {900/m['st']:.0f}µs N{nparts}]")
    shown += 1
    if shown >= 8:
        break
