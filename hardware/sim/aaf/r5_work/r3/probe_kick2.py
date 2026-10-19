import os, sys, subprocess, time
sys.path.insert(0, r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf")
import numpy as np
import parse_r5 as P
import gen_netlists_r3 as G3

LT = r"C:\Users\chenx\AppData\Local\Programs\ADI\LTspice\LTspice.exe"
D = r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf\r5_work\r3"
ST = [(2.4, 1e-7, 0.0), (13.0, 1e-7, 1.8e-8)]


def build(tstop, tstep, opts, edge="10n"):
    txt = G3.v9k_kick({"stages": ST}, ron=1.0, tag="v9k_x", tstop=tstop,
                      tstep=tstep, edge=edge)
    return txt.replace('.options plotwinsize=0 reltol=1e-5 abstol=1e-12 vntol=1e-8 chgtol=1e-15 trtol=2',
                       opts)


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


TRIALS = [
    ("A_gear_loose_300n", "300n", "5n",
     ".options plotwinsize=0 method=gear reltol=1e-4 abstol=1e-10 vntol=1e-7 "
     "chgtol=1e-13 trtol=7"),
    ("B_gear_loose_1u", "1u", "5n",
     ".options plotwinsize=0 method=gear reltol=1e-4 abstol=1e-10 vntol=1e-7 "
     "chgtol=1e-13 trtol=7"),
    ("C_trap_loose_1u", "1u", "5n",
     ".options plotwinsize=0 reltol=1e-4 abstol=1e-10 vntol=1e-7 "
     "chgtol=1e-13 trtol=7"),
]
for nm, tstop, tstep, op in TRIALS:
    raw, dt = run(nm, build(tstop, tstep, op), timeout=100)
    if raw is None:
        print("%-16s TIMEOUT/timeout (%.0fs)" % (nm, dt), flush=True)
        continue
    t = np.array([v.real for v in raw.cols[0]], float)
    a = np.array(raw.col("V(pa2)"), float)
    print("%-16s npts=%6d tmax=%6.3fus  pa2 last=%.6f pp=%.4f mV  (%.1fs)"
          % (nm, len(t), t[-1] * 1e6, a[-1], a.ptp() * 1e3, dt), flush=True)
