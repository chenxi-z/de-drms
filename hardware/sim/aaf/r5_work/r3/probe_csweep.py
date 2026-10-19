import os, sys, subprocess, time
sys.path.insert(0, r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf")
import numpy as np
import parse_r5 as P

LT = r"C:\Users\chenx\AppData\Local\Programs\ADI\LTspice\LTspice.exe"
LIB = r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf\lib\OPAx388.LIB"


def run(name, text, timeout=240):
    open(name + ".net", "w", encoding="ascii", newline="\n").write(text)
    raw = name + ".raw"
    if os.path.exists(raw):
        os.remove(raw)
    t0 = time.time()
    try:
        subprocess.run([LT, "-b", "-ascii", name + ".net"], capture_output=True,
                       text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, "TIMEOUT", time.time() - t0
    return (P.Raw(raw) if os.path.exists(raw) else None), "", time.time() - t0


def net(r1, c1, opts, amp=1.0, tstop="150u", tstep="5n"):
    L = ["* sweep probe",
         ".include " + LIB,
         "Vcc vcc 0 DC 3.3",
         "Vee vee 0 DC 0",
         "Vp vp 0 PULSE(2 %s 10u 10n 10n 600u 2m)" % (2 + amp),
         "Xfa vp fpa vcc vee fpa OPAx388",
         "R1 fpa pa1 %s" % r1,
         "C1 pa1 0 %s" % c1,
         ".save V(fpa) V(pa1)",
         ".tran 0 %s 0 %s" % (tstop, tstep),
         opts,
         ".end"]
    return "\n".join(L) + "\n"


OPT_TIGHT = ".options plotwinsize=0 reltol=1e-7 abstol=1e-13 vntol=1e-10 chgtol=1e-16 trtol=1"
OPT_DEF = ".options plotwinsize=0"

print("=== C sweep at R=2.4 (tight opts) ===", flush=True)
for c1 in (1e-9, 3.3e-9, 10e-9, 22e-9, 47e-9, 100e-9):
    raw, msg, dt = run("sw_c%s" % c1, net(2.4, c1, OPT_TIGHT))
    if raw is None:
        print("  C=%gn FAIL %s" % (c1 * 1e9, msg)); continue
    t = np.array([v.real for v in raw.cols[0]], float)
    yy = np.array(raw.col("V(pa1)"), float)
    q = t > 0.6 * t[-1]
    print("  C=%7.1f nF: tail pp=%9.3f uV  final=%.7f  npts=%d  %.1fs"
          % (c1 * 1e9, yy[q].ptp() * 1e6, yy[-1], len(t), dt), flush=True)
