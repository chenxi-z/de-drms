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


def net(r1, c1, edge, amp, tstop="200u", tstep="5n"):
    L = ["* edge probe",
         ".include " + LIB,
         "Vcc vcc 0 DC 3.3",
         "Vee vee 0 DC 0",
         "Vp vp 0 PULSE(2 %s 10u %s %s 600u 2m)" % (2 + amp, edge, edge),
         "Xfa vp fpa vcc vee fpa OPAx388",
         "R1 fpa pa1 %s" % r1,
         "C1 pa1 0 %s" % c1,
         ".save V(fpa) V(pa1) V(vp)",
         ".tran 0 %s 0 %s" % (tstop, tstep),
         ".options plotwinsize=0 reltol=1e-5 abstol=1e-11 vntol=1e-8 chgtol=1e-14 trtol=2",
         ".end"]
    return "\n".join(L) + "\n"


print("=== edge-rate / amplitude sweep, R=2.4, C=100n ===", flush=True)
for edge in ("10n", "100n", "1u", "10u"):
    for amp in (1.0, 0.1):
        raw, msg, dt = run("edge_%s_amp%s" % (edge, amp), net(2.4, 100e-9, edge, amp))
        if raw is None:
            print("  edge=%s amp=%s FAIL %s" % (edge, amp, msg)); continue
        t = np.array([v.real for v in raw.cols[0]], float)
        yy = np.array(raw.col("V(pa1)"), float)
        q = t > 0.6 * t[-1]
        print("  edge=%-4s amp=%-4s: tail pp=%9.3f uV final=%.7f (target %.2f) %.1fs"
              % (edge, amp, yy[q].ptp() * 1e6, yy[-1], 2 + amp, dt), flush=True)
