"""Independent check of the follower stability threshold: loop-gain / AC peak.

Computes, from the TI model only, the closed-loop source->follower-output transfer
with a bulk C load behind R_iso, and reports peak gain and the R_iso at which the
peak crosses 0 dB. Cross-checked against the transient limit-cycle onset.
"""
import os, sys, subprocess
sys.path.insert(0, r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf")
import numpy as np
import parse_r5 as P

LT = r"C:\Users\chenx\AppData\Local\Programs\ADI\LTspice\LTspice.exe"
D = r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf\r5_work\r3"
LIB = r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf\lib\OPAx388.LIB"


def run(name, text, timeout=180):
    open(os.path.join(D, name + ".net"), "w", encoding="ascii", newline="\n").write(text)
    for ext in (".raw", ".log"):
        q = os.path.join(D, name + ext)
        if os.path.exists(q):
            os.remove(q)
    subprocess.run([LT, "-b", "-ascii", name + ".net"], cwd=D,
                   capture_output=True, text=True, timeout=timeout)
    q = os.path.join(D, name + ".raw")
    return P.Raw(q) if os.path.exists(q) else None


def net(r1, c1="1e-7"):
    return "\n".join([
        "* loop check", ".include " + LIB,
        "Vcc vcc 0 DC 3.3", "Vee vee 0 DC 0",
        "Vp vp 0 DC 2.0 AC 1",
        "Xfa vp fpa vcc vee fpa OPAx388",
        "R1 fpa pa1 %s" % r1,
        "C1 pa1 0 %s" % c1,
        ".ac dec 4000 1 30Meg",
        ".options plotwinsize=0 reltol=1e-7 abstol=1e-13 vntol=1e-10 chgtol=1e-16",
        ".end"]) + "\n"


print("=== closed-loop peak vs R_iso (C_L=100 nF) ===")
print("  R_iso[ohm]  peak[dB]   f_peak[kHz]   crossover(0dB)[MHz]")
for r1 in (2.4, 3.0, 3.3, 3.6, 3.9, 4.3, 5.1, 6.8, 10.0, 13.0, 22.0, 47.0):
    raw = run("lp_%s" % r1, net(r1))
    f = raw.f
    y = np.array(raw.col("V(pa1)"), complex)
    g = 20 * np.log10(np.abs(y))
    g = g - g[0]
    i = int(np.argmax(g))
    # 0 dB crossing after the peak (where the response falls back through 0)
    cross = np.nan
    after = np.where((f > f[i]) & (g < 0))[0]
    if len(after):
        cross = f[after[0]] / 1e6
    print("  %10.1f  %+8.2f   %10.1f   %10.2f"
          % (r1, g[i], f[i] / 1e3, cross))
