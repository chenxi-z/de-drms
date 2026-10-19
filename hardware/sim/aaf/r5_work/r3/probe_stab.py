import os, sys, subprocess, time
sys.path.insert(0, r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf")
import numpy as np
import parse_r5 as P

LT = r"C:\Users\chenx\AppData\Local\Programs\ADI\LTspice\LTspice.exe"
LIB = r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf\lib\OPAx388.LIB"


def run(name, text, timeout=200):
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
    try:
        return (P.Raw(raw) if os.path.exists(raw) else None), "", time.time() - t0
    except Exception as e:
        return None, "PARSE %s" % e, time.time() - t0


def net(r1, c1, tstop="120u", tstep="20n"):
    L = ["* stab probe",
         ".include " + LIB,
         "Vcc vcc 0 DC 3.3",
         "Vee vee 0 DC 0",
         "Vp vp 0 PULSE(2 3 10u 20n 20n 600u 2m)",
         "Xfa vp fpa vcc vee fpa OPAx388",
         "R1 fpa pa1 %s" % r1,
         "C1 pa1 0 %s" % c1,
         ".save V(fpa) V(pa1)",
         ".tran 0 %s 0 %s" % (tstop, tstep),
         ".options plotwinsize=0 reltol=1e-4 abstol=1e-10 vntol=1e-7 chgtol=1e-13 trtol=3",
         ".end"]
    return "\n".join(L) + "\n"


print("=== R_iso x C_L stability (unity follower, 3.3V single supply) ===", flush=True)
for r1 in (2.4, 13.0, 100.0, 470.0, 1000.0):
    row = []
    for c1 in (1e-9, 10e-9, 18e-9, 100e-9):
        raw, msg, dt = run("st_r%s_c%s" % (r1, c1), net(r1, c1))
        if raw is None:
            row.append("%6s:%s" % ("%.0fn" % (c1 * 1e9), msg[:8])); continue
        t = np.array([v.real for v in raw.cols[0]], float)
        yy = np.array(raw.col("V(pa1)"), float)
        q = t > 0.6 * t[-1]
        pp = yy[q].ptp()
        row.append("%6.0fn:%s" % (c1 * 1e9, "OSC%.0fm" % (pp * 1e3) if pp > 1e-3 else "ok"))
    print("  R_iso=%6.0f  " % r1 + "  ".join(row) + "   (%.1fs)" % dt, flush=True)
