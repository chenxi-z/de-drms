import os, sys, subprocess, time
sys.path.insert(0, r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf")
import numpy as np
import parse_r5 as P
import gen_netlists_r3 as G3

LT = r"C:\Users\chenx\AppData\Local\Programs\ADI\LTspice\LTspice.exe"
D = r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf\r5_work\r3"
ST = [(2.4, 1e-7, 0.0), (13.0, 1e-7, 1.8e-8)]


def run(name, text, timeout):
    open(os.path.join(D, name + ".net"), "w", encoding="ascii", newline="\n").write(text)
    for ext in (".raw", ".log"):
        q = os.path.join(D, name + ext)
        if os.path.exists(q):
            os.remove(q)
    t0 = time.time()
    try:
        subprocess.run([LT, "-b", "-ascii", name + ".net"], cwd=D,
                       capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, time.time() - t0
    q = os.path.join(D, name + ".raw")
    return (P.Raw(q) if os.path.exists(q) else None), time.time() - t0


for tstop, tstep in (("1.2u", "2n"), ("1.2u", "1n"), ("0.8u", "0.5n")):
    txt = G3.v9k_kick({"stages": ST}, ron=1.0, tag="v9k_try",
                      tstop=tstop, tstep=tstep)
    raw, dt = run("kt_%s_%s" % (tstop, tstep), txt, timeout=150)
    if raw is None:
        print("tstop=%s tstep=%s : TIMEOUT %.0fs" % (tstop, tstep, dt), flush=True)
        continue
    t = np.array([v.real for v in raw.cols[0]], float)
    a = np.array(raw.col("V(pa2)"), float)
    cs = np.array(raw.col("V(csa)"), float)
    print("tstop=%s tstep=%s : npts=%d tmax=%.3fus  pa2 pp(last 30%%)=%.4f mV  %.1fs"
          % (tstop, tstep, len(t), t[-1] * 1e6,
             a[t > 0.7 * t[-1]].ptp() * 1e3, dt), flush=True)
