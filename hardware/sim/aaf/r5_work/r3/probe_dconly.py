import os, sys, subprocess, time
sys.path.insert(0, r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf")
import numpy as np
import parse_r5 as P

LT = r"C:\Users\chenx\AppData\Local\Programs\ADI\LTspice\LTspice.exe"
LIBAF = r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf"
LIB = os.path.join(LIBAF, "lib", "OPAx388.LIB")


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


def dc_net(r1, c1):
    """No step at all: DC operating point only, then transient with everything at DC."""
    L = ["* dc-only stability",
         ".include " + LIB,
         "Vcc vcc 0 DC 3.3",
         "Vee vee 0 DC 0",
         "Vp vp 0 DC 2.0",
         "Xfa vp fpa vcc vee fpa OPAx388",
         "R1 fpa pa1 %s" % r1,
         "C1 pa1 0 %s" % c1,
         ".save V(fpa) V(pa1)",
         ".tran 0 100u 0 20n",
         ".options plotwinsize=0 reltol=1e-5 abstol=1e-11 vntol=1e-8 chgtol=1e-14 trtol=2",
         ".end"]
    return "\n".join(L) + "\n"


print("=== DC-only (no step): does it self-oscillate? ===", flush=True)
for r1 in (2.4, 3.0, 4.0, 6.8, 13.0):
    raw, msg, dt = run("dc_r%s" % r1, dc_net(r1, "1e-7"))
    if raw is None:
        print("  R=%5.1f FAIL %s" % (r1, msg)); continue
    t = np.array([v.real for v in raw.cols[0]], float)
    y = np.array(raw.col("V(pa1)"), float)
    print("  R=%5.1f : final=%.9f  pp(10-100us)=%9.6f mV npts=%d"
          % (r1, y[-1], (y.max() - y.min()) * 1e3, len(t)), flush=True)
