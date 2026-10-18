# -*- coding: utf-8 -*-
"""aa20: 第三轮探针——高阶/低阻节点提性能。生成 W1-W6 网表、跑 LTspice、解析评分。"""
import subprocess, os, sys, math

LT = r"C:\Users\chenx\AppData\Local\Programs\ADI\LTspice\LTspice.exe"

# 变体定义：stages = [(R, Ccm, Cdiff), ...] 最后一级即引脚节点；串阻总和决定 DC 分压
VARIANTS = {
    "W11": [(1000, 8.2e-9, 0), (220, 15e-9, 10e-9)],
}

def fmt(x):
    if x >= 1: return f"{x:g}"
    return f"{x*1e9:g}n" if x >= 1e-12 else f"{x*1e12:g}p"

def netlist(kind, vname, stages):
    rs = sum(s[0] for s in stages)
    vfin = 1.2 * 130000 / (130000 + 2 * rs)
    if kind == "dm":
        src = "Vp sp 0 DC 0 AC 0.5\nVn sn 0 DC 0 AC -0.5"
        outp, outn, meas = "V(p)", "V(n)", "V(p)-V(n)"
    elif kind == "cm":
        src = "Vp sp 0 DC 0 AC 1\nVn sn 0 DC 0 AC 1"
        outp, outn, meas = "V(p)", "V(n)", "V(p)"
    else:
        src = ("Vp sp 0 PWL(0 -0.6  9.9u -0.6  10.4u 0.6  1.6m 0.6)\n"
               "Vn sn 0 PWL(0 0.6  9.9u 0.6  10.4u -0.6  1.6m -0.6)")
    lines = [f"* aa20 {vname} {kind}"]
    lines.append(src)
    lines.append("Rs1 sp p0 1\nRs2 sn n0 1")
    for i, (r, ccm, cdf) in enumerate(stages):
        nxt = f"p{i+1}" if i + 1 < len(stages) else "p"
        nxt2 = f"n{i+1}" if i + 1 < len(stages) else "n"
        lines.append(f"R{2*i+1}a p{i} {nxt} {fmt(r)}")
        lines.append(f"R{2*i+1}b n{i} {nxt2} {fmt(r)}")
        if ccm > 0:
            lines.append(f"Ca{i} {nxt} 0 {fmt(ccm)}")
            lines.append(f"Cb{i} {nxt2} 0 {fmt(ccm)}")
        if cdf > 0:
            lines.append(f"Cd{i} {nxt} {nxt2} {fmt(cdf)}")
    lines.append("Cp p 0 5p\nCn n 0 5p\nRin p n 130k")
    if kind == "tran":
        lines.append(f"Berr e 0 V=abs(v(p)-v(n)-{vfin:.6f})")
        lines.append(".tran 0 1.6m 0 200n\n.options plotwinsize=0")
    else:
        lines.append(".ac dec 401 10 100Meg")
        if kind == "dm":
            lines.append(".meas AC g_fmod FIND mag(V(p)-V(n)) AT 4.096Meg")
            lines.append(".meas AC g_mclk FIND mag(V(p)-V(n)) AT 16.384Meg")
        else:
            lines.append(".meas AC g_fmod FIND mag(V(p)) AT 4.096Meg")
            lines.append(".meas AC g_mclk FIND mag(V(p)) AT 16.384Meg")
    lines.append(".end")
    return "\n".join(lines) + "\n"

# ---------- 生成与运行 ----------
for vname, stages in VARIANTS.items():
    for kind in ("dm", "cm", "tran"):
        fn = f"aa20_{vname.lower()}_{kind}.net"
        open(fn, "w", newline="\n").write(netlist(kind, vname, stages))
        r = subprocess.run([LT, "-b", "-ascii", os.path.abspath(fn)],
                           capture_output=True, timeout=120)
        if not os.path.exists(fn.replace(".net", ".log")):
            print(f"{fn}: RUN FAIL rc={r.returncode}")

# ---------- 解析（复用 read_raw） ----------
src = open("parse_and_plot.py", encoding="utf-8").read()
fn_ = src[src.index("def unwrap"):src.index("def db")]
ns = {}
exec(fn_, ns)
read_raw = ns["read_raw"]

def dbv(x):
    return 20 * math.log10(abs(x) if abs(x) > 0 else 1e-30)

print(f"{'变体':4s} {'DM@fMOD':>9s} {'DM@MCLK':>9s} {'CM@fMOD':>9s} {'CM@MCLK':>9s} {'settle0.1%':>10s} {'settle0.01%':>11s} {'件/通道':>7s}")
for vname, stages in VARIANTS.items():
    # AC dm
    names, cols, _ = read_raw(f"aa20_{vname.lower()}_dm.raw")
    f = cols[0]
    def at(freq, expr):
        i = min(range(len(f)), key=lambda k: abs(f[k] - freq))
        return eval(expr, {"cols": cols, "names": names, "i": i})
    dm_fmod = dbv(at(4.096e6, "cols[names.index('V(p)')][i]-cols[names.index('V(n)')][i]"))
    dm_mclk = dbv(at(16.384e6, "cols[names.index('V(p)')][i]-cols[names.index('V(n)')][i]"))
    names, cols, _ = read_raw(f"aa20_{vname.lower()}_cm.raw")
    f = cols[0]
    cm_fmod = dbv(cols[names.index("V(p)")][min(range(len(f)), key=lambda k: abs(f[k]-4.096e6))])
    cm_mclk = dbv(cols[names.index("V(p)")][min(range(len(f)), key=lambda k: abs(f[k]-16.384e6))])
    # tran
    names, cols, _ = read_raw(f"aa20_{vname.lower()}_tran.raw")
    t = cols[names.index("time")]
    e = cols[names.index("V(e)")]
    s01 = s001 = None
    for i in range(len(t)):
        if t[i] < 11e-6: continue
        if s01 is None and e[i] <= 1.2e-3: s01 = t[i] - 10e-6
        if s001 is None and e[i] <= 120e-6: s001 = t[i] - 10e-6
    ncomp = sum(2 for s in stages if s[1] > 0) + sum(1 for s in stages if s[2] > 0) + 2 * len(stages)
    f01 = f"{s01*1e6:8.0f}u" if s01 else "    >1.6m"
    f001 = f"{s001*1e6:9.0f}u" if s001 else "     >1.6m"
    print(f"{vname:4s} {dm_fmod:8.1f}dB {dm_mclk:8.1f}dB {cm_fmod:8.1f}dB {cm_mclk:8.1f}dB {f01:>10s} {f001:>11s} {ncomp:7d}")
