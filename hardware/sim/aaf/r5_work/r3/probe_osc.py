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


def osc_net(r1, c1, amp, tstop="120u", tstep="5n"):
    L = ["* osc probe",
         ".include " + LIB,
         "Vcc vcc 0 DC 3.3",
         "Vee vee 0 DC 0",
         "Vp vp 0 PULSE(2 %s 10u 10n 10n 600u 2m)" % (2 + amp),
         "Xfa vp fpa vcc vee fpa OPAx388",
         "R1 fpa pa1 %s" % r1,
         "C1 pa1 0 %s" % c1,
         ".save V(fpa) V(pa1) V(vp)",
         ".tran 0 %s 0 %s" % (tstop, tstep),
         ".options plotwinsize=0 reltol=1e-5 abstol=1e-11 vntol=1e-8 chgtol=1e-14 trtol=2",
         ".end"]
    return "\n".join(L) + "\n"


print("=== single stage: follower + R1 + C1 ===", flush=True)
for r1, c1, amp in ((2.4, 100e-9, 1.0), (2.4, 100e-9, 0.1), (2.4, 10e-9, 1.0),
                    (24, 100e-9, 1.0), (100, 100e-9, 1.0), (2.4, 1e-9, 1.0)):
    raw, msg, dt = run("osc_r%s_c%s_%s" % (r1, c1, amp), osc_net(r1, c1, amp))
    if raw is None:
        print("  R=%s C=%s amp=%s: FAIL %s" % (r1, c1, amp, msg))
        continue
    t = np.array([v.real for v in raw.cols[0]], float)
    y = np.array(raw.col("V(fpa)"), float)
    yy = np.array(raw.col("V(pa1)"), float)
    q = t > 0.6 * t[-1]
    print("  R=%6.1f C=%6.2fn amp=%s: fpa tail pp=%8.3fmV pa1 tail pp=%8.3fmV err=%8.1fuV"
          % (r1, c1 * 1e9, amp, y[q].ptp() * 1e3, yy[q].ptp() * 1e3,
             abs(yy[-1] - (2 + amp)) * 1e6), flush=True)
