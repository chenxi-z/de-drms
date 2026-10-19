"""Isolate D9: same kickback net, but R1 varied. If a stable R_iso makes D9 pass,
the failure is the follower instability, not the charge-bucket sizing."""
import os, sys
sys.path.insert(0, r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf")
import numpy as np
import parse_r5 as P
import gen_netlists_r3 as G3
import subprocess, time

LT = r"C:\Users\chenx\AppData\Local\Programs\ADI\LTspice\LTspice.exe"
D = r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf\r5_work\r3"

OPT = (".options plotwinsize=0 method=gear reltol=1e-5 abstol=1e-11 "
       "vntol=1e-8 chgtol=1e-14 trtol=3")


def build(r1, c1=1e-7, r2=13.0, c2=1e-7, cd=1.8e-8):
    st = [(r1, c1, 0.0), (r2, c2, cd)]
    txt = G3.v9k_kick({"stages": st}, ron=1.0, tag="v9k_iso",
                      tstop="40u", tstep="20n", edge="10n")
    return txt.replace('.options plotwinsize=0 reltol=1e-5 abstol=1e-12 vntol=1e-8 '
                       'chgtol=1e-15 trtol=2', OPT)


def run(name, text, timeout=200):
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


print("=== D9 isolation: R1 sweep, real model, gear, 40us ===")
print(" R1[ohm]  D9   worst_resid_uV  worst/ss   kick_amp_uV   pa2_pp_mV")
for r1 in (2.4, 6.8, 13.0, 47.0):
    raw, dt = run("iso_%s" % r1, build(r1), timeout=200)
    if raw is None:
        print("  %5.1f  TIMEOUT %.0fs" % (r1, dt)); continue
    k = P.kickback(raw, 2)
    t = np.array([v.real for v in raw.cols[0]], float)
    a = np.array(raw.col("V(pa2)"), float)
    print("  %5.1f  %.0f  %13.2f  %.3e  %10.1f  %9.3f   (%.0fs)"
          % (r1, k.get("D9", -1), k.get("worst_resid_uv", 0),
             k.get("worst_rel_to_ss", 0), k.get("kick_amp_uv", 0),
             a[t > 0.8 * t[-1]].ptp() * 1e3, dt), flush=True)
