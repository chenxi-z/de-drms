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
        return None, "PARSE", time.time() - t0


def net(vcc, dclo, dchi, r1, c1, opts):
    L = ["* rail probe",
         ".include " + LIB,
         "Vcc vcc 0 DC %s" % vcc,
         "Vee vee 0 DC 0",
         "Vp vp 0 PULSE(%s %s 10u 20n 20n 600u 2m)" % (dclo, dchi),
         "Xfa vp fpa vcc vee fpa OPAx388",
         "R1 fpa pa1 %s" % r1,
         "C1 pa1 0 %s" % c1,
         ".save V(fpa) V(pa1)",
         ".tran 0 120u 0 20n",
         opts,
         ".end"]
    return "\n".join(L) + "\n"


OPT = ".options plotwinsize=0 reltol=1e-4 abstol=1e-10 vntol=1e-7 chgtol=1e-13 trtol=3"
print("=== does the 100nF load limit cycle depend on rail / level? ===", flush=True)
cases = [
    ("3.3V 1.0->1.5V", 3.3, 1.0, 1.5),
    ("3.3V 1.6->1.7V", 3.3, 1.6, 1.7),
    ("3.3V 0.5->1.0V", 3.3, 0.5, 1.0),
    ("5.0V 2.0->3.0V", 5.0, 2.0, 3.0),
    ("5.0V 2.4->2.5V", 5.0, 2.4, 2.5),
    ("10V  5.0->6.0V", 10.0, 5.0, 6.0),
]
for nm, vcc, lo, hi in cases:
    raw, msg, dt = run("rail_%s" % nm.replace(" ", "_").replace(">", "_"),
                       net(vcc, lo, hi, 2.4, 100e-9, OPT))
    if raw is None:
        print("  %-16s FAIL %s" % (nm, msg)); continue
    t = np.array([v.real for v in raw.cols[0]], float)
    yy = np.array(raw.col("V(pa1)"), float)
    q = t > 0.6 * t[-1]
    print("  %-16s tail pp=%9.3f mV final=%.5f" % (nm, yy[q].ptp() * 1e3, yy[-1]), flush=True)
