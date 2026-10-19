import os, sys, subprocess, time
sys.path.insert(0, r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf")
import numpy as np
import parse_r5 as P

LT = r"C:\Users\chenx\AppData\Local\Programs\ADI\LTspice\LTspice.exe"
LIB = r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf\lib\OPAx388.LIB"


def run(name, text, timeout=240):
    open(name + ".net", "w", encoding="ascii", newline="\n").write(text)
    raw = name + ".raw"
    for f in (raw, name + ".log"):
        if os.path.exists(f):
            os.remove(f)
    t0 = time.time()
    try:
        subprocess.run([LT, "-b", "-ascii", name + ".net"], capture_output=True,
                       text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, "TIMEOUT", time.time() - t0
    try:
        return (P.Raw(raw) if os.path.exists(raw) else None), "", time.time() - t0
    except Exception as e:
        return None, "PARSE:%s" % e, time.time() - t0


def net(r1, c1, opts, method="", tstop="150u", tstep="20n"):
    L = ["* stability matrix",
         ".include " + LIB,
         "Vcc vcc 0 DC 3.3",
         "Vee vee 0 DC 0",
         "Vp vp 0 PULSE(2 3 10u 10n 10n 600u 2m)",
         "Xfa vp fpa vcc vee fpa OPAx388",
         "R1 fpa pa1 %s" % r1,
         "C1 pa1 0 %s" % c1,
         ".save V(fpa) V(pa1)",
         ".tran 0 %s 0 %s" % (tstop, tstep),
         opts,
         ".end"]
    return "\n".join(L) + "\n"


def analyse(raw):
    t = np.array([v.real for v in raw.cols[0]], float)
    y = np.array(raw.col("V(pa1)"), float)
    q = t > 0.6 * t[-1]
    seg = y[q]
    pp = float(seg.ptp())
    # dominant frequency in tail
    x = seg - seg.mean()
    fx = np.fft.rfftfreq(len(seg), d=float(np.median(np.diff(t[q]))))
    X = np.abs(np.fft.rfft(x)) * 2 / len(x)
    k = int(np.argmax(X[1:])) + 1 if len(X) > 2 else 0
    return pp, (fx[k] if k else 0.0), float(seg.mean())


print("=== R1 sweep, C1=100nF, trap, reltol 1e-5 ===", flush=True)
for r1 in (2.4, 3.0, 4.0, 5.0, 6.8, 10.0, 15.0):
    raw, msg, dt = run("m_r%s" % r1, net(r1, "1e-7",
                                          ".options plotwinsize=0 reltol=1e-5 abstol=1e-11 "
                                          "vntol=1e-8 chgtol=1e-14 trtol=2"))
    if raw is None:
        print("  R=%5.1f FAIL %s" % (r1, msg)); continue
    pp, f, mean = analyse(raw)
    print("  R=%5.1f : tail pp=%9.3f mV  f=%7.1f kHz  mean=%.4f  %.1fs"
          % (r1, pp * 1e3, f / 1e3, mean, dt), flush=True)

print("\n=== integration method / timestep check at R1=2.4 ===", flush=True)
cases = [("trap20n", "trap", "20n", ".options plotwinsize=0 reltol=1e-5 abstol=1e-11 vntol=1e-8 chgtol=1e-14 trtol=2"),
         ("trap5n", "trap", "5n", ".options plotwinsize=0 reltol=1e-5 abstol=1e-11 vntol=1e-8 chgtol=1e-14 trtol=2"),
         ("gear20n", "gear", "20n", ".options plotwinsize=0 method=gear reltol=1e-5 abstol=1e-11 vntol=1e-8 chgtol=1e-14 trtol=2"),
         ("trap2n", "trap", "2n", ".options plotwinsize=0 reltol=1e-6 abstol=1e-12 vntol=1e-9 chgtol=1e-15 trtol=1")]
for nm, meth, ts, op in cases:
    raw, msg, dt = run("x_%s" % nm, net(2.4, "1e-7", op, tstop="60u", tstep=ts))
    if raw is None:
        print("  %-8s FAIL %s" % (nm, msg)); continue
    pp, f, mean = analyse(raw)
    print("  %-8s: tail pp=%9.3f mV  f=%7.1f kHz  mean=%.4f  npts=%d %.1fs"
          % (nm, pp * 1e3, f / 1e3, mean, len(raw.cols[0]), dt), flush=True)
