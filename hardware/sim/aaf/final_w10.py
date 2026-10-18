# -*- coding: utf-8 -*-
"""final_w10.py — 冠军 FIN1 (330R-47n/47nd-2k7-6.8n/5.6nd) 角验证 + MC30 + 理论/仿真叠加"""
import subprocess, os, math, random
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from opt_engine import atten_db, settle_time

LT = r"C:\Users\chenx\AppData\Local\Programs\ADI\LTspice\LTspice.exe"
STAGES = [(330, 47e-9, 47e-9), (2700, 6.8e-9, 5.6e-9)]
RSUM = sum(s[0] for s in STAGES)

def run(name, text):
    open(name + ".net", "w", newline="\n").write(text)
    subprocess.run([LT, "-b", "-ascii", os.path.abspath(name + ".net")], capture_output=True, timeout=300)

def stages_net(scale_r=1.0, scale_c=1.0, ccm2_extra=0.0):
    L = []
    for i, (r, ccm, cdf) in enumerate(STAGES):
        nxt = f"p{i+1}" if i + 1 < len(STAGES) else "p"
        nxt2 = f"n{i+1}" if i + 1 < len(STAGES) else "n"
        L.append(f"R{2*i}a p{i} {nxt} {r*scale_r:.4f}")
        L.append(f"R{2*i}b n{i} {nxt2} {r*scale_r:.4f}")
        cc = (ccm + (ccm2_extra if i == 1 else 0)) * scale_c
        L.append(f"Ca{i} {nxt} 0 {cc:.4g}")
        L.append(f"Cb{i} {nxt2} 0 {cc:.4g}")
        cd = cdf * scale_c
        if cdf > 0:
            L.append(f"Cd{i} {nxt} {nxt2} {cd:.4g}")
    return L

TAIL = "Cp p 0 5p\nCn n 0 5p\nRin p n 130k"

# ---- 标称 AC ----
for kind in ("dm", "cm"):
    src = "Vp sp 0 DC 0 AC 0.5\nVn sn 0 DC 0 AC -0.5" if kind == "dm" else "Vp sp 0 DC 0 AC 1\nVn sn 0 DC 0 AC 1"
    meas = (".meas AC g_fmod FIND mag(V(p)-V(n)) AT 4.096Meg\n.meas AC g_mclk FIND mag(V(p)-V(n)) AT 16.384Meg"
            if kind == "dm" else
            ".meas AC g_fmod FIND mag(V(p)) AT 4.096Meg\n.meas AC g_mclk FIND mag(V(p)) AT 16.384Meg")
    run(f"fin1_ac_{kind}", f"* fin1 {kind}\n{src}\nRs1 sp p0 1\nRs2 sn n0 1\n" +
        "\n".join(stages_net()) + f"\n{TAIL}\n.ac dec 801 10 100Meg\n{meas}\n.end")

# ---- 最坏角 tran（R+1%, C+5%，参考用角增益）----
gcorner = 130000 / (130000 + 2 * RSUM * 1.01)
corner = f"""* fin1 worst-corner tran
Vp sp 0 PWL(0 -0.600000  9.9u -0.600000  10.4u 0.600000  1.6m 0.600000)
Vn sn 0 PWL(0 0.600000  9.9u 0.600000  10.4u -0.600000  1.6m -0.600000)
Rs1 sp p0 1.01
Rs2 sn n0 1.01
""" + "\n".join(stages_net(scale_r=1.01, scale_c=1.05)) + f"""
{TAIL}
Berr e 0 V=abs(v(p)-v(n)-{gcorner*1.2:.6f})
.tran 0 1.6m 0 200n
.options plotwinsize=0
.end"""
run("fin1_tran_corner", corner)

# ---- 标称 tran ----
gnom = 130000 / (130000 + 2 * RSUM)
nom = f"""* fin1 nominal tran
Vp sp 0 PWL(0 -0.600000  9.9u -0.600000  10.4u 0.600000  1.6m 0.600000)
Vn sn 0 PWL(0 0.600000  9.9u 0.600000  10.4u -0.600000  1.6m -0.600000)
Rs1 sp p0 1
Rs2 sn n0 1
""" + "\n".join(stages_net()) + f"""
{TAIL}
Berr e 0 V=abs(v(p)-v(n)-{gnom*1.2:.6f})
.tran 0 1.6m 0 200n
.options plotwinsize=0
.end"""
run("fin1_tran_nom", nom)

# ---- 噪声 ----
run("fin1_noise", f"""* fin1 noise
Vp sp 0 DC 0 AC 1
Vn sn 0 DC 0 AC 0
Rs1 sp p0 1
Rs2 sn n0 1
""" + "\n".join(stages_net()) + f"""
{TAIL}
.noise V(p) Vp dec 200 10 1Meg
.end""")

# ---- MC30 tran ----
rng = random.Random(42)
mc = []
for i in range(30):
    stg = [(r * (1 + rng.uniform(-0.01, 0.01)), c * (1 + rng.uniform(-0.05, 0.05)), cd * (1 + rng.uniform(-0.05, 0.05)))
           for (r, c, cd) in STAGES]
    g = 130000 / (130000 + 2 * sum(s[0] for s in stg))
    txt = f"""* mc {i}
Vp sp 0 PWL(0 -0.600000  9.9u -0.600000  10.4u 0.600000  1.6m 0.600000)
Vn sn 0 PWL(0 0.600000  9.9u 0.600000  10.4u -0.600000  1.6m -0.600000)
Rs1 sp p0 1
Rs2 sn n0 1
""" + "\n".join(stages_net.__wrapped__(stg) if hasattr(stages_net, '__wrapped__') else []) + f"""
{TAIL}
Berr e 0 V=abs(v(p)-v(n)-{g*1.2:.6f})
.tran 0 1.6m 0 200n
.options plotwinsize=0
.end"""
    # 直接内联（不用 stages_net，随机值）
    L = []
    for j, (r, ccm, cdf) in enumerate(stg):
        nxt = f"p{j+1}" if j + 1 < len(stg) else "p"
        nxt2 = f"n{j+1}" if j + 1 < len(stg) else "n"
        L.append(f"R{2*j}a p{j} {nxt} {r:.4f}")
        L.append(f"R{2*j}b n{j} {nxt2} {r:.4f}")
        L.append(f"Ca{j} {nxt} 0 {ccm:.4g}")
        L.append(f"Cb{j} {nxt2} 0 {ccm:.4g}")
        L.append(f"Cd{j} {nxt} {nxt2} {cdf:.4g}")
    txt = f"""* mc {i}
Vp sp 0 PWL(0 -0.600000  9.9u -0.600000  10.4u 0.600000  1.6m 0.600000)
Vn sn 0 PWL(0 0.600000  9.9u 0.600000  10.4u -0.600000  1.6m -0.600000)
Rs1 sp p0 1
Rs2 sn n0 1
""" + "\n".join(L) + f"""
{TAIL}
Berr e 0 V=abs(v(p)-v(n)-{g*1.2:.6f})
.tran 0 1.6m 0 200n
.options plotwinsize=0
.end"""
    nm = f"fin1_mc{i}"
    run(nm, txt)

# ============ 解析 ============
src = open("parse_and_plot.py", encoding="utf-8").read()
fn2 = src[src.index("def unwrap"):src.index("def db")]
ns = {}
exec(fn2, ns)
read_raw = ns["read_raw"]
def dbv(x): return 20 * math.log10(abs(x) if abs(x) > 0 else 1e-30)

print("=== FIN1 LTspice AC ===")
for kind in ("dm", "cm"):
    log = open(f"fin1_ac_{kind}.log", encoding="ascii", errors="replace").read()
    for line in log.splitlines():
        if line.startswith("g_"):
            val = line.split("=")[1].split(",")[0].replace("(", "").strip()
            print(f"  {line.split(':')[0]} ({kind}) = {val} dB")

# 理论 vs 仿真叠加图
names, cols, _ = read_raw("fin1_ac_dm.raw")
f = [v.real for v in cols[0]]
dm_lt = [abs(a - b) for a, b in zip(cols[names.index("V(p)")], cols[names.index("V(n)")])]
names, cols, _ = read_raw("fin1_ac_cm.raw")
cm_lt = [abs(v) for v in cols[names.index("V(p)")]]
f_th = np.logspace(1, 8, 400)
dm_th = [abs(atten_db(STAGES, "dm", ff)) for ff in f_th]
cm_th = [abs(atten_db(STAGES, "cm", ff)) for ff in f_th]
plt.figure(figsize=(11, 6.5))
plt.semilogx(f, [20*math.log10(x) for x in dm_lt], ".", ms=2, color="#dc2626", label="DM LTspice")
plt.semilogx(f, [20*math.log10(x) for x in cm_lt], ".", ms=2, color="#059669", label="CM LTspice")
plt.semilogx(f_th, dm_th, lw=2, color="#7f1d1d", label="DM theory")
plt.semilogx(f_th, cm_th, lw=2, color="#064e3b", label="CM theory")
for x, t in [(4.096e6, "fMOD"), (16.384e6, "MCLK")]: plt.axvline(x, color="#9ca3af", ls=":")
plt.grid(True, which="both", alpha=0.3); plt.xlim(10, 1e8); plt.ylim(-160, 5)
plt.xlabel("Frequency (Hz)"); plt.ylabel("Gain rel. DC (dB)")
plt.title("FIN1 = 330R-(47n+47nd)-2k7-(6.8n+5.6nd)  theory vs LTspice")
plt.legend(loc="lower left"); plt.tight_layout(); plt.savefig("fin1_bode_overlay.png", dpi=150); plt.close()

def settle_of(rawf, ref):
    names, cols, _ = read_raw(rawf)
    t = cols[names.index("time")]
    e = cols[names.index("V(e)")]
    s01 = s001 = None
    for i in range(len(t)):
        if t[i] < 11e-6: continue
        if s01 is None and e[i] <= 1.2e-3: s01 = t[i] - 10e-6
        if s001 is None and e[i] <= 120e-6: s001 = t[i] - 10e-6
    return s01, s001, min(e[i] for i in range(len(t)) if t[i] > 11e-6)

print("\n=== FIN1 tran ===")
for nm in ("fin1_tran_nom.raw", "fin1_tran_corner.raw"):
    s01, s001, emin = settle_of(nm, None)
    f01 = f"{s01*1e6:.0f}" if s01 else ">1590"
    f001 = f"{s001*1e6:.0f}" if s001 else ">1590"
    print(f"{nm}: 0.1%={f01}us 0.01%={f001}us err_min={emin*1e6:.1f}uV")

print("\n=== FIN1 MC30 settle 0.01% ===")
st = []
for i in range(30):
    names, cols, _ = read_raw(f"fin1_mc{i}.raw")
    t = cols[names.index("time")]
    e = cols[names.index("V(e)")]
    s001 = None
    for k in range(len(t)):
        if t[k] < 11e-6: continue
        if e[k] <= 120e-6: s001 = t[k] - 10e-6; break
    if s001: st.append(s001 * 1e6)
st.sort()
print(f"min {st[0]:.0f} / p50 {st[len(st)//2]:.0f} / max {st[-1]:.0f} µs ({len(st)}/30 在 1.6ms 内进带)")

print("\n=== FIN1 噪声 ===")
names, cols, _ = read_raw("fin1_noise.raw")
oname = [n for n in names if "onoise" in n.lower().replace(" ", "")][0]
dens = [abs(v) for v in cols[names.index(oname)]]
fr_ = [v.real for v in cols[0]]
tot2 = sum(0.5*(dens[k]**2 + dens[k-1]**2)*(fr_[k]-fr_[k-1]) for k in range(1, len(fr_)))
print(f"ONOISE 积分 = {math.sqrt(tot2)*1e6:.3f} µV rms")

# 理论对照（同一网络）
print("\n=== 理论 vs LTspice（FIN1） ===")
print("  DM@fMOD 见下行逐点对比")
for mode, fr, simv in [("dm", 4.096e6, None), ("dm", 16.384e6, None), ("cm", 4.096e6, None), ("cm", 16.384e6, None)]:
    th = -atten_db(STAGES, mode, fr)
    names_, cols_, _ = read_raw(f"fin1_ac_{mode}.raw")
    f_ = [v.real for v in cols_[0]]
    ik = min(range(len(f_)), key=lambda k: abs(f_[k]-fr))
    if mode == "dm":
        sim = dbv(abs(cols_[names_.index('V(p)')][ik] - cols_[names_.index('V(n)')][ik]))
    else:
        sim = dbv(abs(cols_[names_.index('V(p)')][ik]))
    print(f"  {mode.upper()}@{fr/1e6:.3f}M: 理论 {th:8.2f} | 仿真 {sim:8.2f} | 差 {abs(th-sim):.2f} dB")
print(f"  settle0.01% worst角: 理论 {settle_time(STAGES,'dm',60e-6,tol_r=0.01,tol_c=0.05)*1e6:.0f} µs")
