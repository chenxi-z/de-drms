"""D9 with fine resolution in the tail: simulate 40 us but only store the last 5 us.

`.tran 0 <stop> <start> <step>` lets LTspice integrate the warm-up cheaply in terms of
*saved* points while still sampling the last window finely.
"""
import os, sys, subprocess, time
sys.path.insert(0, r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf")
import numpy as np
import parse_r5 as P
import gen_netlists_r3 as G3

LT = r"C:\Users\chenx\AppData\Local\Programs\ADI\LTspice\LTspice.exe"
D = r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf\r5_work\r3"
OPT = (".options plotwinsize=0 method=gear reltol=1e-5 abstol=1e-11 "
       "vntol=1e-8 chgtol=1e-14 trtol=3")


def build(r1=2.4, c1=1e-7, r2=13.0, c2=1e-7, cd=1.8e-8,
          tstop="40u", tstart="35u", tstep="0.05n"):
    st = [(r1, c1, 0.0), (r2, c2, cd)]
    txt = G3.v9k_kick({"stages": st}, ron=1.0, tag="v9k_fine",
                      tstop=tstop, tstep=tstep, edge="10n")
    txt = txt.replace('.options plotwinsize=0 reltol=1e-5 abstol=1e-12 vntol=1e-8 '
                      'chgtol=1e-15 trtol=2', OPT)
    txt = txt.replace(".tran 0 %s 0 %s" % (tstop, tstep),
                      ".tran 0 %s %s %s" % (tstop, tstart, tstep))
    return txt


def run(name, text, timeout=420):
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


for r1 in (2.4, 13.0):
    txt = build(r1=r1)
    raw, dt = run("fine_%s" % r1, txt, timeout=420)
    if raw is None:
        print("R1=%s TIMEOUT %.0fs" % (r1, dt)); continue
    t = np.array([v.real for v in raw.cols[0]], float)
    a = np.array(raw.col("V(pa2)"), float)
    cs = np.array(raw.col("V(csa)"), float)
    print("R1=%s npts=%d t=%.1f..%.1f us (%.0fs)" % (r1, len(t), t[0] * 1e6, t[-1] * 1e6, dt))
    k = P.kickback(raw, 2)
    print("   kickback(): D9=%s resid=%.2f uV  rel=%.3e  ncyc=%s  kick=%.1f uV"
          % (k.get("D9"), k.get("worst_resid_uv", 0), k.get("worst_rel_to_ss", 0),
             k.get("n_cycles"), k.get("kick_amp_uv", 0)))
    T = 1 / 4.096e6
    k0 = int(round(t[0] / T)) + 2
    for kk in (k0, k0 + 1):
        ton = kk * T
        m = (t >= ton) & (t <= ton + 122.07e-9)
        if m.sum() < 10:
            continue
        st, sv = t[m], a[m]
        print("   cycle %d: n=%d v_start=%.6f v_end=%.6f min=%.6f max=%.6f "
              "end-start=%.2f uV"
              % (kk, m.sum(), sv[0], sv[-1], sv.min(), sv.max(), (sv[-1] - sv[0]) * 1e6))
