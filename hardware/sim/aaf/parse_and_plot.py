# -*- coding: utf-8 -*-
"""aa6: 解析 LTspice ASCII .raw（UTF-16LE 头），出对比图 + 评分表。
用法: python parse_and_plot.py  （在 aaf 目录下）
"""
import re, math, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

LT = "LTspice"

def unwrap(tok):
    if "," in tok:
        a, b = tok.split(",")
        return complex(float(a), float(b))
    return float(tok)

def read_raw(path):
    txt = open(path, "r", encoding="ascii", errors="replace").read()
    marker = "Values:"
    idx = txt.find(marker)
    if idx < 0:
        raise RuntimeError("no Values: in " + path)
    header = txt[:idx]
    body = txt[idx + len(marker):]
    flags = ""
    nvars = npts = 0
    varnames = []
    invars = False
    for line in header.splitlines():
        s = line.strip()
        if s.startswith("Flags:"): flags = s.split(":", 1)[1].strip()
        elif s.startswith("No. Variables:"): nvars = int(s.split(":")[1])
        elif s.startswith("No. Points:"): npts = int(s.split(":")[1])
        elif s == "Variables:":
            invars = True
            continue
        elif invars:
            parts = line.split("	")
            if len(parts) >= 3 and parts[2].strip():
                varnames.append(parts[2].strip())
    vals = []
    first = True
    for line in body.splitlines():
        if not line.strip():
            continue
        if line.startswith("	"):
            for tok in line.strip().replace("	", " ").split():
                vals.append(unwrap(tok))
        else:
            # 点首行: "idx<TAB><TAB>val" —— 取最后一个 token
            toks = line.strip().replace("	", " ").split()
            vals.append(unwrap(toks[-1]))

    need = npts * nvars
    vals = vals[:need]
    cols = [vals[i::nvars] for i in range(nvars)]
    return varnames, cols, flags

def db(x):
    return 20 * math.log10(abs(x) if abs(x) > 0 else 1e-30)

# ---------- AC ----------
def load_ac(path):
    names, cols, flags = read_raw(path)
    freq = [v.real for v in cols[0]]
    # 找 V(p) V(n)（DM 文件）或 V(p)（CM 文件）
    out = {"f": freq}
    for i, n in enumerate(names):
        out[n] = cols[i]
    return out

dm = {}
cm = {}
for v, prefix in [("V0", "aa1_v0"), ("V1", "aa2_v1"), ("V2", "aa3_v2"), ("V3", "aa4_v3"), ("V2b", "aa6_v2b"), ("V4", "aa7_v4"), ("V5r", "aa13_v5r"), ("V6r", "aa14_v6r"), ("V6r2", "aa19_v6r2"), ("W9", "aa20_w9")]:
    d = load_ac(prefix + ("_ac_dm.raw" if not prefix.startswith("aa20") else "_dm.raw"))
    dm[v] = d
    c = load_ac(prefix + ("_ac_cm.raw" if not prefix.startswith("aa20") else "_cm.raw"))
    cm[v] = c

# ---------- TRAN ----------
def settle_from_raw(path, vfinal, band01=1.2e-3, band001=120e-6, t0=10e-6):
    names, cols, flags = read_raw(path)
    t = cols[0]
    iv = names.index("V(e)") if "V(e)" in names else None
    e = cols[iv]
    # 从阶跃 t0 之后找最后一次进入带宽并保持的时刻
    t01 = t001 = None
    for i in range(len(t)):
        if t[i] < t0:
            continue
        if e[i] <= band01 and t01 is None:
            t01 = t[i]
        if e[i] <= band001 and t001 is None:
            t001 = t[i]
    emin = min(e[i] for i in range(len(t)) if t[i] >= t0)
    return t, e, t01, t001, emin

tran = {}
for v, prefix, vf in [("V0", "aa1_v0", 1.181818), ("V1", "aa16_v1", 1.181818), ("V3", "aa4_v3", 1.181818), ("V5r", "aa17_v5r", 1.172932), ("V6r", "aa18_v6r", 1.177856), ("V6r2", "aa19_v6r2", 1.175277), ("W9", "aa20_w9", 1.178000)]:
    t, e, s01, s001, emin = settle_from_raw(prefix + "_tran1.raw" if prefix in ("aa16_v1", "aa17_v5r", "aa18_v6r") else prefix + "_tran.raw", vf)
    tran[v] = (t, e, s01, s001, emin)

# ---------- 数值汇总 ----------
print("=== 汇总（自 .raw 计算，独立于 .meas） ===")
print(f"{'变体':4s} {'DM@fMOD':>9s} {'DM@MCLK':>9s} {'CM@fMOD':>9s} {'droop@1k':>9s} {'settle0.1%':>10s} {'settle0.01%':>11s} {'err_min':>10s}")
res = {}
for v in ["V0", "V1", "V3", "V5r", "V6r", "V6r2", "W9"]:
    d = dm[v]
    i = min(range(len(d["f"])), key=lambda k: abs(d["f"][k] - 4.096e6))
    j = min(range(len(d["f"])), key=lambda k: abs(d["f"][k] - 16.384e6))
    k1 = min(range(len(d["f"])), key=lambda k: abs(d["f"][k] - 1e3))
    gpf = d["V(p)"][i] - d["V(n)"][i]
    gmf = d["V(p)"][j] - d["V(n)"][j]
    g1 = d["V(p)"][k1] - d["V(n)"][k1]
    cmf = cm[v]["V(p)"][i]
    t, e, s01, s001, emin = tran[v]
    res[v] = dict(gf=db(gpf), gm=db(gmf), cm=db(cmf),
                  droop=db(g1) - db(d["V(p)"][0] - d["V(n)"][0]) if False else (db(g1)),
                  s01=s01, s001=s001, emin=emin)
    print(f"{v:4s} {db(gpf):8.1f}dB {db(gmf):8.1f}dB {db(cmf):8.1f}dB {db(g1):8.3f}dB "
          f"{(s01*1e6 if s01 else float('nan')):9.0f}us {(s001*1e6 if s001 else float('nan')):10.0f}us {emin:9.2e}")

# 噪声：V0 .noise raw
try:
    names, cols, flags = read_raw("aa5_v0_noise.raw")
    f = [v.real for v in cols[0]]
    oname = [n for n in names if "onoise" in n.lower().replace("v(", "")][0]
    # .noise 的复杂列：onoise 密度（幅值）
    idx = names.index(oname)
    dens = [abs(v) for v in cols[idx]]
    tot = math.sqrt(sum(dd ** 2 for dd in dens))  # 粗积分（均匀 df）
    df = (math.log10(1e6) - math.log10(10)) / (len(f) - 1)  # dec
    # 梯形积分 sum(dens^2 * df_hz)
    import bisect
    tot2 = 0.0
    for i in range(1, len(f)):
        dfhz = f[i] - f[i - 1]
        tot2 += 0.5 * (dens[i] ** 2 + dens[i - 1] ** 2) * dfhz
    print(f"\nV0 输出噪声积分(10Hz–1MHz) = {math.sqrt(tot2)*1e6:.3f} uV rms")
except Exception as ex:
    print("noise parse skip:", ex)

# ---------- 画图 ----------
cmap = {"V0": "#2563eb", "V1": "#ea580c", "V3": "#7c3aed", "V5r": "#059669", "V6r": "#dc2626", "V6r2": "#ca8a04", "W9": "#db2777"}
plt.figure(figsize=(11, 7))
for v in ["V0", "V1", "V3", "V5r", "V6r", "V6r2", "W9"]:
    d = dm[v]
    f = d["f"]
    g = [db(a - b) for a, b in zip(d["V(p)"], d["V(n)"])]
    plt.semilogx(f, g, color=cmap[v], lw=1.8, label=v)
for x, lab in [(4.096e6, "fMOD 4.096M"), (16.384e6, "MCLK 16.384M"), (64e3, "64k")]:
    plt.axvline(x, color="#9ca3af", ls=":", lw=1)
    plt.text(x, -118, lab, rotation=90, fontsize=8, va="bottom", color="#6b7280")
plt.axhline(-60, color="#d1d5db", lw=1)
plt.text(12, -58, "-60 dB", fontsize=8, color="#9ca3af")
plt.ylim(-140, 5); plt.xlim(10, 1e8)
plt.grid(True, which="both", alpha=0.3)
plt.xlabel("Frequency (Hz)"); plt.ylabel("DM gain (dB, 1V diff in)")
plt.title("Anti-alias DM response — all variants")
plt.legend(loc="lower left")
plt.tight_layout(); plt.savefig("aa_bode_dm.png", dpi=150); plt.close()

plt.figure(figsize=(11, 7))
for v in ["V0", "V1", "V3", "V5r", "V6r", "V6r2", "W9"]:
    d = cm[v]
    f = d["f"]
    g = [db(a) for a in d["V(p)"]]
    plt.semilogx(f, g, color=cmap[v], lw=1.8, label=v)
for x, lab in [(4.096e6, "fMOD"), (16.384e6, "MCLK")]:
    plt.axvline(x, color="#9ca3af", ls=":", lw=1)
plt.ylim(-140, 5); plt.xlim(10, 1e8)
plt.grid(True, which="both", alpha=0.3)
plt.xlabel("Frequency (Hz)"); plt.ylabel("CM gain (dB, 1V common in)")
plt.title("Anti-alias common-mode response — all variants")
plt.legend(loc="lower left")
plt.tight_layout(); plt.savefig("aa_bode_cm.png", dpi=150); plt.close()

plt.figure(figsize=(11, 7))
for v in ["V0", "V1", "V3", "V5r", "V6r", "V6r2", "W9"]:
    t, e, s01, s001, emin = tran[v]
    plt.plot([x * 1e6 for x in t], [y * 1e3 for y in e], color=cmap[v], lw=1.5, label=v)
    if s01:
        plt.axvline(s01 * 1e6, color=cmap[v], ls=":", lw=1)
plt.axhline(1.2, color="#9ca3af", ls="--", lw=1); plt.text(600, 1.35, "0.1% band", fontsize=9, color="#6b7280")
plt.axhline(0.12, color="#d1d5db", ls="--", lw=1); plt.text(600, 0.22, "0.01% band", fontsize=9, color="#9ca3af")
plt.xlim(0, 1200)
plt.yscale("log"); plt.ylim(1e-6, 10)
plt.grid(True, which="both", alpha=0.3)
plt.xlabel("Time (us)"); plt.ylabel("|V(p)-V(n) - V_final| (mV)")
plt.title("Full-scale step settling (2.4V pk-pk DM, 1us edge) — log scale")
plt.legend(loc="upper right")
plt.tight_layout(); plt.savefig("aa_settle.png", dpi=150); plt.close()

# kick 图（V0）
names, cols, flags = read_raw("aa1_v0_kick.raw")
t = [x * 1e6 for x in cols[0]]
ip = names.index("V(p)"); inn = names.index("V(n)")
plt.figure(figsize=(11, 5))
plt.plot(t, [x * 1e3 for x in cols[ip]], lw=1, label="V(AIN0P) kick ripple")
plt.plot(t, [x * 1e3 for x in cols[inn]], lw=1, label="V(AIN0N) kick ripple")
plt.xlabel("Time (us)"); plt.ylabel("mV")
plt.title("Sampling kick ripple @fMOD (Q=3pC/244ns) — V0: 89uVpp on P line")
plt.legend(); plt.grid(True, alpha=0.3)
plt.tight_layout(); plt.savefig("aa_kick.png", dpi=150); plt.close()

print("\nplots saved: aa_bode_dm.png aa_bode_cm.png aa_settle.png aa_kick.png")
