import os
import os, subprocess, time
import sys; sys.path.insert(0, os.path.abspath("."))
import numpy as np
import parse_r5 as P

LT = r"C:\Users\chenx\AppData\Local\Programs\ADI\LTspice\LTspice.exe"
LIB = os.path.abspath("lib/OPAx388.LIB")
D = os.path.abspath("r5_work/r3")

def run(name, text):
    p = os.path.join(D, name + ".net")
    open(p, "w", encoding="ascii", newline="\n").write(text)
    raw = p[:-4] + ".raw"
    if os.path.exists(raw): os.remove(raw)
    t0 = time.time()
    try:
        r = subprocess.run([LT, "-b", "-ascii", name + ".net"], cwd=D,
                           capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired:
        return None, "TIMEOUT", time.time()-t0
    return (P.Raw(raw) if os.path.exists(raw) else None), (r.stdout or "")[-300:], time.time()-t0

head = f".include {LIB}\nVcc vcc 0 DC 3.3\nVee vee 0 DC 0\n"

# P1: 纯跟随器阶跃，无阶梯
for trel in ("10n", "1u"):
    txt = head + f"""Vp vp 0 PULSE(2 3 10u 10n 10n 600u 2m)
Xfa vp fpa vcc vee fpa OPAx388
.save V(vp) V(fpa)
.tran 0 300u 0 {trel}
.options plotwinsize=0 method=trap reltol=1e-6 abstol=1e-12 vntol=1e-9 chgtol=1e-15
.end
"""
    raw, msg, dt = run(f"probe_foll_{trel}", txt)
    if raw is None:
        print("P1", trel, "FAILED", msg); continue
    t = np.array([v.real for v in raw.cols[0]], float)
    y = np.array(raw.col("V(fpa)"), float)
    vf = y[-1]
    err = np.abs(y - vf)
    i = np.where((t > 10e-6) & (err > 2e-6))[0]  # 0.01% of 1V = 100uV... use 2e-6? no: 0.01%*1V=100uV
    print(f"P1 {trel}: npts={len(t)} dt={dt:.2f}s final={vf:.9f} max_after10us={y[t>10e-6].max():.6f}")
    # settle to 0.01% of 1 V step
    band = 1e-4*1.0
    tt, yy = t[t>10e-6], y[t>10e-6]
    vf2 = yy[-1]
    out = np.where(np.abs(yy-vf2) > band)[0]
    print("   settle(0.01% of 1V) =", (tt[out[-1]]-10e-6)*1e6 if len(out) else 0.0, "us ; "
          f"final_err={abs(yy[-1]-3.0):.3e}  tail@{tt[-1]*1e6:.0f}us={yy[-1]:.9f}")
