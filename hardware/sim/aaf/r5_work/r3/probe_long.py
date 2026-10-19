"""Settle/D9 timing probes with the real model, long window."""
import os, sys, subprocess, time
sys.path.insert(0, r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf")
import numpy as np
import parse_r5 as P
import gen_netlists_r3 as G3

LT = r"C:\Users\chenx\AppData\Local\Programs\ADI\LTspice\LTspice.exe"
D = r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf\r5_work\r3"


def run(name, text, timeout):
    p = os.path.join(D, name + ".net")
    open(p, "w", encoding="ascii", newline="\n").write(text)
    for ext in (".raw", ".log"):
        q = os.path.join(D, name + ext)
        if os.path.exists(q):
            os.remove(q)
    t0 = time.time()
    try:
        subprocess.run([LT, "-b", "-ascii", name + ".net"], cwd=D,
                       capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, "TIMEOUT", time.time() - t0
    q = os.path.join(D, name + ".raw")
    return (P.Raw(q) if os.path.exists(q) else None), "", time.time() - t0


# 2 ms window to decide: sustained limit cycle vs slow decay
txt = G3.v9c_tran({"stages": [(2.4 * 1.01, 1e-7 * 1.05, 0.0),
                              (13.0 * 1.01, 1e-7 * 1.05, 1.8e-8 * 1.05)]},
                  tag="v9c_long", tstop="2m", tstep="3n")
raw, msg, dt = run("v9c_long", txt, timeout=420)
if raw is None:
    print("v9c_long FAIL", msg, round(dt, 1))
else:
    t = np.array([v.real for v in raw.cols[0]], float)
    p = np.array(raw.col("V(pa2)"), float)
    n = np.array(raw.col("V(na2)"), float)
    d = p - n
    print("v9c_long: npts=%d tmax=%.3f ms  %.1fs" % (len(t), t[-1] * 1e3, dt))
    for e in np.arange(0.2e-3, t[-1] - 0.19e-3, 0.2e-3):
        m = (t >= e) & (t < e + 0.2e-3)
        if m.sum() > 20:
            print("   t=%5.2f..%5.2f ms  dm pp=%9.3f mV  mean=%9.6f"
                  % (e * 1e3, (e + 0.2e-3) * 1e3, d[m].ptp() * 1e3, d[m].mean()))

# D9 with a short window
for tstop, tstep in (("600n", "2n"), ("600n", "1n")):
    txt = G3.v9k_kick({"stages": [(2.4, 1e-7, 0.0), (13.0, 1e-7, 1.8e-8)]},
                      ron=1.0, tag="v9k_try", tstop=tstop, tstep=tstep)
    raw, msg, dt = run("v9k_try_%s_%s" % (tstop, tstep), txt, timeout=300)
    if raw is None:
        print("v9k tstop=%s tstep=%s FAIL %s %.1fs" % (tstop, tstep, msg, dt), flush=True)
        continue
    t = np.array([v.real for v in raw.cols[0]], float)
    a = np.array(raw.col("V(pa2)"), float)
    print("v9k tstop=%s tstep=%s: npts=%d tmax=%.3f us  pp(last 20%%)=%.4f mV %.1fs"
          % (tstop, tstep, len(t), t[-1] * 1e6, a[t > 0.8 * t[-1]].ptp() * 1e3, dt),
          flush=True)
