# -*- coding: utf-8 -*-
"""snap_round4.py — 连续最优解 snap 到 E24/E12 实际值，邻域理论评分 + LTspice 终验"""
import itertools, math, os, subprocess
import numpy as np
from opt_engine import atten_db, settle_time

LT = r"C:\Users\chenx\AppData\Local\Programs\ADI\LTspice\LTspice.exe"
BUDGET_US = 900.0

R1_SET = [270, 300, 330, 360]
R2_SET = [2100, 2200, 2400, 2700, 3000]
C1_SET = [47e-9]
C1D_SET = [39e-9, 43e-9, 47e-9]
C2CM_SET = [6.8e-9, 8.2e-9, 10e-9]
C2D_SET = [5.6e-9, 6.8e-9, 8.2e-9, 10e-9]

def margins(stages, verbose=False):
    rsum = sum(s[0] for s in stages)
    n_parts = 2 * len(stages) + sum(2 if s[1] > 0 else 0 for s in stages) + sum(1 if s[2] > 0 else 0 for s in stages)
    if rsum > 5000 or n_parts > 14:
        return None
    dm = -atten_db(stages, "dm", 4.096e6)
    cm = -atten_db(stages, "cm", 4.096e6)
    mk = -atten_db(stages, "dm", 16.384e6)
    t001_w = settle_time(stages, "dm", 60e-6, tol_r=0.01, tol_c=0.05) * 1e6
    if not np.isfinite(t001_w) or t001_w > BUDGET_US:
        return None
    m = {"dm": dm / 80, "cm": cm / 60, "mk": mk / 120, "st": BUDGET_US / t001_w}
    mmin = min(m.values())
    if verbose:
        print(f"  DM {dm:.0f} CM {cm:.0f} MCLK {mk:.0f} t001w {t001_w:.0f}µs → minM={mmin:.3f}")
    return mmin, m, dm, cm, mk, t001_w, n_parts

cands = []
for r1, r2, c1, c1d, c2cm, c2d in itertools.product(R1_SET, R2_SET, C1_SET, C1D_SET, C2CM_SET, C2D_SET):
    st = [(r1, c1, c1d), (r2, c2cm, c2d)]
    r = margins(st)
    if r:
        cands.append((r[0], st, r))
cands.sort(key=lambda t: -t[0])
print("=== snap 后 Top 6（理论） ===")
for mm, st, r in cands[:6]:
    stg = "—".join(f"{s[0]}R/({s[1]*1e9:.0f}n+{s[2]*1e9:.1f}nd)" for s in st)
    print(f"minM={mm:.3f}  {stg}  [DM {r[2]:.0f} CM {r[3]:.0f} MCLK {r[4]:.0f} t001w {r[5]:.0f}µs N{r[6]}]")

# W9 基线
print("\nW9 基线:")
w9m = margins([(1000, 8.2e-9, 8.2e-9), (220, 15e-9, 10e-9)], verbose=True)

# ============ 冠军 LTspice 终验 ============
best = cands[0][1]
gdc = 130000 / (130000 + 2 * sum(s[0] for s in best))
stages_net = []
for i, (r, ccm, cdf) in enumerate(best):
    nxt = f"p{i+1}" if i + 1 < len(best) else "p"
    nxt2 = f"n{i+1}" if i + 1 < len(best) else "n"
    stages_net.append(f"R{2*i}a p{i} {nxt} {r}")
    stages_net.append(f"R{2*i}b n{i} {nxt2} {r}")
    stages_net.append(f"Ca{i} {nxt} 0 {ccm:g}")
    stages_net.append(f"Cb{i} {nxt2} 0 {ccm:g}")
    if cdf > 0:
        stages_net.append(f"Cd{i} {nxt} {nxt2} {cdf:g}")
tail = "Cp p 0 5p\nCn n 0 5p\nRin p n 130k"

for kind in ("dm", "cm"):
    src = "Vp sp 0 DC 0 AC 0.5\nVn sn 0 DC 0 AC -0.5" if kind == "dm" else "Vp sp 0 DC 0 AC 1\nVn sn 0 DC 0 AC 1"
    meas = (".meas AC g_fmod FIND mag(V(p)-V(n)) AT 4.096Meg\n.meas AC g_mclk FIND mag(V(p)-V(n)) AT 16.384Meg"
            if kind == "dm" else
            ".meas AC g_fmod FIND mag(V(p)) AT 4.096Meg\n.meas AC g_mclk FIND mag(V(p)) AT 16.384Meg")
    txt = f"* fin1 final {kind}\n{src}\nRs1 sp p0 1\nRs2 sn n0 1\n" + "\n".join(stages_net) + f"\n{tail}\n.ac dec 401 10 100Meg\n{meas}\n.end"
    fn = f"fin1_ac_{kind}.net"
    open(fn, "w", newline="\n").write(txt)
    subprocess.run([LT, "-b", "-ascii", os.path.abspath(fn)], capture_output=True, timeout=120)

tran_txt = f"""* fin1 final tran (worst corner R+1% C+5%)
Vp sp 0 PWL(0 -0.600000  9.9u -0.600000  10.4u 0.600000  1.6m 0.600000)
Vn sn 0 PWL(0 0.600000  9.9u 0.600000  10.4u -0.600000  1.6m -0.600000)
Rs1 sp p0 1.01
Rs2 sn n0 1.01
""" + "\n".join(x.replace(" 47n", " 49.35n").replace(" 8.2n", " 8.61n").replace(" 6.8n", " 7.14n").replace(f" {best[1][0]}", f" {best[1][0]*1.01:g}").replace(f" {best[0][0]} ", f" {best[0][0]*1.01:g} ") for x in stages_net) + f"""
Cp p 0 5.25p
Cn n 0 5.25p
Rin p n 130k
Berr e 0 V=abs(v(p)-v(n)-{gdc*1.2:.6f})
.tran 0 1.6m 0 200n
.options plotwinsize=0
.end"""
open("fin1_tran.net", "w", newline="\n").write(tran_txt)
subprocess.run([LT, "-b", "-ascii", os.path.abspath("fin1_tran.net")], capture_output=True, timeout=120)

print("\n=== LTspice 终验（冠军 snap 版） ===")
for kind in ("dm", "cm"):
    log = open(f"fin1_ac_{kind}.log", encoding="ascii", errors="replace").read()
    for line in log.splitlines():
        if line.startswith("g_"):
            print(" ", line.split(":")[0], "=", line.split("=")[1].split(",")[0].strip(), "dB")

src2 = open("parse_and_plot.py", encoding="utf-8").read()
fn2 = src2[src2.index("def unwrap"):src2.index("def db")]
ns = {}
exec(fn2, ns)
names, cols, _ = ns["read_raw"]("fin1_tran.raw")
t = cols[names.index("time")]
e = cols[names.index("V(e)")]
s01 = s001 = None
for i in range(len(t)):
    if t[i] < 11e-6: continue
    if s01 is None and e[i] <= 1.2e-3: s01 = t[i] - 10e-6
    if s001 is None and e[i] <= 120e-6: s001 = t[i] - 10e-6
print(f"worst-corner tran: 0.1% = {s01*1e6:.0f} µs  0.01% = {s001*1e6:.0f} µs（容差最坏角 R+1% C+5%）")
