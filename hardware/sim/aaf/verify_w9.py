# -*- coding: utf-8 -*-
"""verify_w9.py — W9 抗混叠滤波器全指标验证套件
覆盖：AC(DM/CM/CMRR/相位/群延迟/fc/droop) + 噪声 + kick + 阶跃建立(最坏/实际换路幅度)
     + 10ms 斜坡跟踪 + 蒙特卡洛容差(60 AC + 30 tran)
"""
import subprocess, os, math, random
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

LT = r"C:\Users\chenx\AppData\Local\Programs\ADI\LTspice\LTspice.exe"

# W9 拓扑: [(R, Ccm, Cdiff), ...]  首级源侧，末级引脚侧
STAGES = [(1000, 8.2e-9, 8.2e-9), (220, 15e-9, 10e-9)]
RSUM = sum(s[0] for s in STAGES)          # 1221
GDC = 130000 / (130000 + 2 * RSUM)        # 直流增益(含 Zin 分压) 0.981556
VFINAL = 1.2 * GDC                        # 2.4V 峰峰阶跃的终值

def fmt(x):
    if x >= 1: return f"{x:g}"
    return f"{x*1e9:g}n"

def stage_net(body_stages):
    L = []
    for i, (r, ccm, cdf) in enumerate(body_stages):
        nxt = f"p{i+1}" if i + 1 < len(body_stages) else "p"
        nxt2 = f"n{i+1}" if i + 1 < len(body_stages) else "n"
        L.append(f"R{2*i}a p{i} {nxt} {fmt(r)}")
        L.append(f"R{2*i}b n{i} {nxt2} {fmt(r)}")
        if ccm: L.append(f"Ca{i} {nxt} 0 {fmt(ccm)}"); L.append(f"Cb{i} {nxt2} 0 {fmt(ccm)}")
        if cdf: L.append(f"Cd{i} {nxt} {nxt2} {fmt(cdf)}")
    return L

def run(name, text):
    fn = name + ".net"
    open(fn, "w", newline="\n").write(text)
    subprocess.run([LT, "-b", "-ascii", os.path.abspath(fn)], capture_output=True, timeout=300)
    if not os.path.exists(name + ".raw"):
        raise RuntimeError(f"{name} no raw")

src = open("parse_and_plot.py", encoding="utf-8").read()
fn_ = src[src.index("def unwrap"):src.index("def db")]
ns = {}
exec(fn_, ns)
read_raw = ns["read_raw"]

def dbv(x): return 20 * math.log10(abs(x) if abs(x) > 0 else 1e-30)

# ============ 1. 标称 AC（单端激励法：Vp=1,Vn=0 → DM=A-B, CM=A+B）============
ac_text = f"""* w9 nominal AC single-ended
Vp sp 0 DC 0 AC 1
Vn sn 0 DC 0 AC 0
Rs1 sp p0 1
Rs2 sn n0 1
""" + "\n".join(stage_net(STAGES)) + """
Cp p 0 5p
Cn n 0 5p
Rin p n 130k
.ac dec 801 1 1Gig
.end"""
run("w9v_ac", ac_text)
names, cols, _ = read_raw("w9v_ac.raw")
f = [v.real for v in cols[0]]
A = cols[names.index("V(p)")]
B = cols[names.index("V(n)")]
dm = [a - b for a, b in zip(A, B)]
cm = [a + b for a, b in zip(A, B)]
def idx(fr): return min(range(len(f)), key=lambda k: abs(f[k] - fr))
def mag(x): return abs(x)
def ph(x): return math.degrees(math.atan2(x.imag, x.real))

dc = mag(dm[idx(10)])
print("=== AC 标称 ===")
print(f"DC 增益: {dbv(dc):+.3f} dB (理论 {dbv(GDC):+.3f}, Zin 分压)")
for fr in [100, 1e3, 10e3, 64e3]:
    i = idx(fr)
    print(f"droop @{fr:g}Hz: {dbv(mag(dm[i])/dc):+.3f} dB")
# fc
fc = None
for i in range(len(f)):
    if mag(dm[i]) < dc * 0.70711 and f[i] > 100:
        fc = f[i]; break
print(f"DM fc(-3dB): {fc/1e3:.2f} kHz (理论 1/(2π·1k·23.2n)≈6.9k 量级)")
i = idx(4.096e6)
print(f"DM@fMOD: {dbv(mag(dm[i])/dc):.1f} dB   CM@fMOD: {dbv(mag(cm[i])/dc):.1f} dB")
i = idx(16.384e6)
print(f"DM@MCLK: {dbv(mag(dm[i])/dc):.1f} dB   CM@MCLK: {dbv(mag(cm[i])/dc):.1f} dB")
print("CMRR = DM/CM:")
for fr in [100, 1e3, 10e3, 64e3, 4.096e6]:
    i = idx(fr)
    print(f"  @{fr:g}Hz: {dbv(mag(dm[i])/mag(cm[i])):.1f} dB")
# 群延迟 τg = -dφ/dω（1kHz 附近差分）
i0, i1 = idx(300), idx(3e3)
w0, w1 = 2*math.pi*f[i0], 2*math.pi*f[i1]
p0, p1 = -ph(dm[i0]), -ph(dm[i1])
if p1 < p0: p1 += 360
tg = math.radians(p1 - p0) / (w1 - w0)
print(f"群延迟 @~1kHz: {tg*1e6:.1f} µs（ch0/ch1 同构 → 比值中抵消）")

# ============ 2. 噪声 ============
noise_text = f"""* w9 noise
Vp sp 0 DC 0 AC 1
Vn sn 0 DC 0 AC 0
Rs1 sp p0 1
Rs2 sn n0 1
""" + "\n".join(stage_net(STAGES)) + """
Cp p 0 5p
Cn n 0 5p
Rin p n 130k
.noise V(p) Vp dec 200 10 1Meg
.end"""
run("w9v_noise", noise_text)
names, cols, _ = read_raw("w9v_noise.raw")
oname = [n for n in names if "onoise" in n.lower().replace(" ", "")][0]
dens = [abs(v) for v in cols[names.index(oname)]]
fn_ = [v.real for v in cols[0]]
tot2 = sum(0.5 * (dens[k]**2 + dens[k-1]**2) * (fn_[k]-fn_[k-1]) for k in range(1, len(fn_)))
print(f"\n=== 噪声 ===\nONOISE 积分(10Hz-1MHz): {math.sqrt(tot2)*1e6:.3f} µV rms")
i_n = min(range(len(fn_)), key=lambda k: abs(fn_[k] - 1e3))
print(f"onoise @1kHz: {dens[i_n]*1e9:.2f} nV/√Hz（ADC 底噪 ~0.41 µV rms @128kSPS → 占比 <0.2%）")

# ============ 3. 满度阶跃 + 实际换路幅度阶跃 ============
def step_net(name, amp, vfin):
    return f"""* {name}
Vp sp 0 PWL(0 {-amp/2:+.6f}  9.9u {-amp/2:+.6f}  10.4u {amp/2:+.6f}  1.6m {amp/2:+.6f})
Vn sn 0 PWL(0 {amp/2:+.6f}  9.9u {amp/2:+.6f}  10.4u {-amp/2:+.6f}  1.6m {-amp/2:+.6f})
Rs1 sp p0 1
Rs2 sn n0 1
""" + "\n".join(stage_net(STAGES)) + f"""
Cp p 0 5p
Cn n 0 5p
Rin p n 130k
Berr e 0 V=abs(v(p)-v(n)-{vfin:.6f})
.tran 0 1.6m 0 200n
.options plotwinsize=0
.end"""

def settle(name):
    names, cols, _ = read_raw(name + ".raw")
    t = cols[names.index("time")]
    e = cols[names.index("V(e)")]
    s01 = s001 = None; ov = 0
    for i in range(len(t)):
        if t[i] < 11e-6: continue
        if s01 is None and e[i] <= 1.2e-3: s01 = t[i] - 10e-6
        if s001 is None and e[i] <= 120e-6: s001 = t[i] - 10e-6
        if t[i] < 100e-6: ov = max(ov, e[i])
    return s01, s001, ov, min(e[i] for i in range(len(t)) if t[i] > 11e-6)

# 满度 2.4V（最坏判据）: 输入从 -1.2G 到 +1.2G（G=DC 增益），终值 = G*1.2
s01, s001, ov, emin = settle("w9v_step_fs") if os.path.exists("w9v_step_fs.raw") else (None,)*4
fs_text = f"""* w9 full-scale step
Vp sp 0 PWL(0 -0.600000  9.9u -0.600000  10.4u 0.600000  1.6m 0.600000)
Vn sn 0 PWL(0 0.600000  9.9u 0.600000  10.4u -0.600000  1.6m -0.600000)
Rs1 sp p0 1
Rs2 sn n0 1
""" + "\n".join(stage_net(STAGES)) + f"""
Cp p 0 5p
Cn n 0 5p
Rin p n 130k
Berr e 0 V=abs(v(p)-v(n)-{2*GDC*1.2 - GDC*1.2:.6f})
.tran 0 1.6m 0 200n
.options plotwinsize=0
.end"""
# 终值 = +1.2*G；初值 = -1.2*G
fs_text = fs_text.replace(f"Berr e 0 V=abs(v(p)-v(n)-{2*GDC*1.2 - GDC*1.2:.6f})",
                          f"Berr e 0 V=abs(v(p)-v(n)-{GDC*1.2:.6f})")
run("w9v_step_fs", fs_text)
s01, s001, ov, emin = settle("w9v_step_fs")
print(f"\n=== 阶跃建立 ===\n满度 2.4Vpp: 0.1% = {s01*1e6:.0f} µs  0.01% = {s001*1e6:.0f} µs  前沿峰值误差 {ov*1e3:.0f} mV  误差底 {emin*1e6:.1f} µV")

# 实际换路幅度 0.71V（10k 样品，ch0-: F→V_N）
act_text = step_net("w9v_step_act", 0.71, 0.71 * GDC)
run("w9v_step_act", act_text)
s01, s001, ov, emin = settle("w9v_step_act")
print(f"实际换路 0.71V: 0.1% = {s01*1e6:.0f} µs  0.01% = {s001*1e6:.0f} µs（模式切换真实等待）")

# ============ 4. 10ms 斜坡跟踪（冲击形状） ============
ramp_text = f"""* w9 impact ramp 10ms full-scale
Vp sp 0 PWL(0 -0.600000  10u -0.600000  10.01m 0.600000  15m 0.600000)
Vn sn 0 PWL(0 0.600000  10u 0.600000  10.01m -0.600000  15m -0.600000)
Rs1 sp p0 1
Rs2 sn n0 1
""" + "\n".join(stage_net(STAGES)) + f"""
Cp p 0 5p
Cn n 0 5p
Rin p n 130k
Berr e 0 V=abs(v(p)-v(n)-{GDC*1.2:.6f}*(2*limit((time-10u)/10m,0,1)-1))
.tran 0 15m 0 2u
.options plotwinsize=0
.meas TRAN ramp_err MAX V(e) FROM 100u TO 10m
.end"""
run("w9v_ramp", ramp_text)
import re
log = open("w9v_ramp.log", encoding="ascii", errors="replace").read()
m = re.search(r"ramp_err.*?=([0-9.eE+-]+)", log)
print(f"\n=== 10ms 斜坡跟踪 ===\n单通道最大跟踪误差: {float(m.group(1))*1e3:.2f} mV（ch0/ch1 同构 → 比值 R(t)=V_sample/V_Rsense 逐点精确，此误差不影响 R）")

# ============ 5. kick（W9） ============
kick_text = f"""* w9 kick
Vp sp 0 DC 1.2
Vn sn 0 DC 0.6
Rs1 sp p0 1
Rs2 sn n0 1
""" + "\n".join(stage_net(STAGES)) + """
Ik p 0 PULSE(0 120u 50n 2n 2n 24n 244.14n)
Cp p 0 5p
Cn n 0 5p
Rin p n 130k
.tran 0 10u 0 1n
.options plotwinsize=0
.meas TRAN vrip PP V(p)
.meas TRAN vripn PP V(n)
.end"""
run("w9v_kick", kick_text)
log = open("w9v_kick.log", encoding="ascii", errors="replace").read()
print(f"\n=== kick ===\n" + "\n".join(l for l in log.splitlines() if l.startswith("vrip")))

# ============ 6. 蒙特卡洛（R ±1%, C ±5%；60 AC + 30 tran） ============
print("\n=== 蒙特卡洛（R ±1%, C ±5%, C0G 实际 ±2% 取保守 ±5%） ===")
rng = random.Random(20261018)
mc_ac, mc_tran = [], []
NAC, NTR = 60, 30
for i in range(NAC + NTR):
    stages = [(r * (1 + rng.uniform(-0.01, 0.01)), c * (1 + rng.uniform(-0.05, 0.05)), cd * (1 + rng.uniform(-0.05, 0.05)))
              for (r, c, cd) in STAGES]
    rsum = sum(s[0] for s in stages)
    g = 130000 / (130000 + 2 * rsum)
    is_tran = i >= NAC
    if is_tran:
        txt = f"""* mc tran {i}
Vp sp 0 PWL(0 -0.600000  9.9u -0.600000  10.4u 0.600000  1.6m 0.600000)
Vn sn 0 PWL(0 0.600000  9.9u 0.600000  10.4u -0.600000  1.6m -0.600000)
Rs1 sp p0 1
Rs2 sn n0 1
""" + "\n".join(stage_net(stages)) + f"""
Cp p 0 5p
Cn n 0 5p
Rin p n 130k
Berr e 0 V=abs(v(p)-v(n)-{g*1.2:.6f})
.tran 0 1.6m 0 200n
.options plotwinsize=0
.end"""
        nm = f"mc_t{i}"
        run(nm, txt)
        names, cols, _ = read_raw(nm + ".raw")
        t = cols[names.index("time")]
        e = cols[names.index("V(e)")]
        s001 = None
        for k in range(len(t)):
            if t[k] < 11e-6: continue
            if e[k] <= 120e-6: s001 = t[k] - 10e-6; break
        mc_tran.append(s001)
        os.remove(nm + ".raw"); os.remove(nm + ".log"); os.remove(nm + ".net")
        if (i - NAC) % 10 == 9: print(f"  tran {i-NAC+1}/{NTR}")
    else:
        txt = f"""* mc ac {i}
Vp sp 0 DC 0 AC 1
Vn sn 0 DC 0 AC 0
Rs1 sp p0 1
Rs2 sn n0 1
""" + "\n".join(stage_net(stages)) + """
Cp p 0 5p
Cn n 0 5p
Rin p n 130k
.ac dec 201 10 100Meg
.end"""
        nm = f"mc_a{i}"
        run(nm, txt)
        names, cols, _ = read_raw(nm + ".raw")
        f = cols[0]
        A = cols[names.index("V(p)")]; B = cols[names.index("V(n)")]
        dm = [a - b for a, b in zip(A, B)]
        cm = [a + b for a, b in zip(A, B)]
        def idxk(fr): return min(range(len(f)), key=lambda k: abs(f[k] - fr))
        i0 = idxk(10)
        i1 = idxk(4.096e6); i2 = idxk(16.384e6)
        mc_ac.append((dbv(mag(dm[i1]) / mag(dm[i0])), dbv(mag(cm[i1]) / mag(cm[i0])), dbv(mag(dm[i2]) / mag(dm[i0]))))
        os.remove(nm + ".raw"); os.remove(nm + ".log"); os.remove(nm + ".net")

def stats(v):
    v = sorted(v); n = len(v)
    return f"min {v[0]:.1f} / 均值 {sum(v)/n:.1f} / max {v[-1]:.1f} dB"
dm_f = [x[0] for x in mc_ac]; cm_f = [x[1] for x in mc_ac]; mk_f = [x[2] for x in mc_ac]
print(f"DM@fMOD 60 样本: {stats(dm_f)}")
print(f"CM@fMOD 60 样本: {stats(cm_f)}")
print(f"DM@MCLK 60 样本: {stats(mk_f)}")
st = sorted(x*1e6 for x in mc_tran if x)
if st:
    print(f"settle0.01% {len(st)} 样本: min {st[0]:.0f} / 均值 {sum(st)/len(st):.0f} / max {st[-1]:.0f} µs")

# ============ 7. MC 直方图图 ============
plt.figure(figsize=(12, 4))
plt.subplot(1, 3, 1); plt.hist(dm_f, bins=14, color="#2563eb", alpha=0.8)
plt.title("DM@fMOD (dB)"); plt.xlabel("dB"); plt.grid(alpha=0.3)
plt.subplot(1, 3, 2); plt.hist(cm_f, bins=14, color="#059669", alpha=0.8)
plt.title("CM@fMOD (dB)"); plt.xlabel("dB"); plt.grid(alpha=0.3)
plt.subplot(1, 3, 3)
if st: plt.hist(st, bins=12, color="#dc2626", alpha=0.8)
plt.title("settle 0.01% (us)"); plt.xlabel("us"); plt.grid(alpha=0.3)
plt.tight_layout(); plt.savefig("w9_mc_hist.png", dpi=150); plt.close()

# CMRR 曲线
plt.figure(figsize=(9, 5))
cmrr = [dbv(mag(dm[i]) / mag(cm[i])) for i in range(len(f))]
fr_ = [v.real for v in f if True]
plt.semilogx(fr_, cmrr, lw=2, color="#2563eb")
for x in [4.096e6, 16.384e6]: plt.axvline(x, color="#9ca3af", ls=":")
plt.grid(True, which="both", alpha=0.3); plt.xlim(10, 1e8); plt.ylim(0, 40)
plt.xlabel("Frequency (Hz)"); plt.ylabel("CMRR = |DM/CM| (dB)")
plt.title("W9 CMRR vs frequency")
plt.tight_layout(); plt.savefig("w9_cmrr.png", dpi=150); plt.close()
print("\nplots: w9_mc_hist.png w9_cmrr.png")
