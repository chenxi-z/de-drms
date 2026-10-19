import os, sys, subprocess, time
sys.path.insert(0, r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf")
import numpy as np
import parse_r5 as P

LT = r"C:\Users\chenx\AppData\Local\Programs\ADI\LTspice\LTspice.exe"
LIB = r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf\lib\OPAx388.LIB"


def run(name, text, timeout=240):
    open(name + ".net", "w", encoding="ascii", newline="\n").write(text)
    for f in (name + ".raw", name + ".log"):
        if os.path.exists(f):
            os.remove(f)
    t0 = time.time()
    try:
        subprocess.run([LT, "-b", "-ascii", name + ".net"], capture_output=True,
                       text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, "TIMEOUT", time.time() - t0
    try:
        return (P.Raw(name + ".raw") if os.path.exists(name + ".raw") else None), "", time.time() - t0
    except Exception:
        return None, "PARSE", time.time() - t0


def net(amp, r1, c1):
    """Small-signal step: amplitude swept. Small step should stay in linear region."""
    L = ["* small signal step",
         ".include " + LIB,
         "Vcc vcc 0 DC 3.3",
         "Vee vee 0 DC 0",
         "Vp vp 0 PULSE(2 %s 10u 10n 10n 600u 2m)" % (2 + amp),
         "Xfa vp fpa vcc vee fpa OPAx388",
         "R1 fpa pa1 %s" % r1,
         "C1 pa1 0 %s" % c1,
         ".save V(fpa) V(pa1)",
         ".tran 0 150u 0 10n",
         ".options plotwinsize=0 reltol=1e-6 abstol=1e-12 vntol=1e-9 chgtol=1e-15 trtol=1",
         ".end"]
    return "\n".join(L) + "\n"


print("=== step amplitude sweep, R=2.4 C=100n ===", flush=True)
for amp in (1.0, 0.3, 0.1, 0.03, 0.01, 0.001, 1e-4):
    raw, msg, dt = run("amp_%g" % amp, net(amp, 2.4, "1e-7"))
    if raw is None:
        print("  amp=%g FAIL %s" % (amp, msg)); continue
    t = np.array([v.real for v in raw.cols[0]], float)
    y = np.array(raw.col("V(pa1)"), float)
    q = t > 0.6 * t[-1]
    seg = y[q]
    print("  amp=%-8g: tail pp/amp=%9.3f  (abs pp=%9.3f mV)  mean=%.6f npts=%d %.1fs"
          % (amp, seg.ptp() / amp, seg.ptp() * 1e3, seg.mean(), len(t), dt), flush=True)
