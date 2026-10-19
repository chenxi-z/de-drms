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


def net(lo, hi, r1, c1, tstop="150u", tstep="5n"):
    L = ["* step probe",
         ".include " + LIB,
         "Vcc vcc 0 DC 3.3",
         "Vee vee 0 DC 0",
         "Vp vp 0 PULSE(%s %s 10u 10n 10n 600u 2m)" % (lo, hi),
         "Xfa vp fpa vcc vee fpa OPAx388",
         "R1 fpa pa1 %s" % r1,
         "C1 pa1 0 %s" % c1,
         ".save V(fpa) V(pa1) V(vp)",
         ".tran 0 %s 0 %s" % (tstop, tstep),
         ".options plotwinsize=0 reltol=1e-5 abstol=1e-11 vntol=1e-8 chgtol=1e-14 trtol=2",
         ".end"]
    return "\n".join(L) + "\n"


print("=== step level vs stability (R1=2.4, C1=100n) ===", flush=True)
for lo, hi in ((2.0, 3.0), (2.0, 2.8), (2.0, 2.6), (1.5, 2.0), (0.5, 1.0), (2.0, 2.2)):
    raw, msg, dt = run("step_%s_%s" % (lo, hi), net(lo, hi, 2.4, 100e-9))
    if raw is None:
        print("  %s->%s: FAIL %s" % (lo, hi, msg)); continue
    t = np.array([v.real for v in raw.cols[0]], float)
    yy = np.array(raw.col("V(pa1)"), float)
    q = t > 0.6 * t[-1]
    print("  %s->%s V: tail pp=%8.3f mV  final=%8.5f  (target %s)  settle_us=%s"
          % (lo, hi, yy[q].ptp() * 1e3, yy[-1], hi,
             "osc" if yy[q].ptp() > 1e-3 else "ok"), flush=True)
