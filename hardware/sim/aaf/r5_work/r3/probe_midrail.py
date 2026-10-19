"""Rail-artifact check: same differential step, different DC common-mode level.

If the limit cycle survives with the swing centered far from the rails, it is the
R_iso/C_load loop, not the model's rail/clamp blocks.
"""
import os, sys, subprocess, time
sys.path.insert(0, r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf")
import numpy as np
import parse_r5 as P

LT = r"C:\Users\chenx\AppData\Local\Programs\ADI\LTspice\LTspice.exe"
D = r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf\r5_work\r3"
LIB = r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf\lib\OPAx388.LIB"
ST = [(2.4, 1e-7, 0.0), (13.0, 1e-7, 1.8e-8)]


def line(side, src, node, st):
    out, prev = [], src
    for i, (r, cg, cd) in enumerate(st, 1):
        out.append("R%s%d %s %s%d %.10g" % (side, i, prev, node, i, r))
        out.append("C%s%d %s%d 0 %.10g" % (side, i, node, i, cg))
        prev = "%s%d" % (node, i)
    return out


def net(lo_lvl, hi_lvl, amp, tstop="200u"):
    """Differential step: line A lo->hi, line B = 2*cm - that."""
    cm = 0.5 * (lo_lvl + hi_lvl)
    L = ["* midrail check", ".include " + LIB,
         "Vcc vcc 0 DC 3.3", "Vee vee 0 DC 0",
         "Vp vp 0 PULSE(%.6g %.6g 10u 10n 10n 600u 2m)" % (cm - amp / 2, cm + amp / 2),
         "Vn vn 0 PULSE(%.6g %.6g 10u 10n 10n 600u 2m)" % (cm + amp / 2, cm - amp / 2),
         "Xfa vp fpa vcc vee fpa OPAx388", "Xfb vn fna vcc vee fna OPAx388"]
    L += line("a", "fpa", "pa", ST) + line("b", "fna", "na", ST)
    L += ["Cd pa2 na2 1.8e-8", "Rin pa2 na2 130000",
          "Cpa pa2 0 5e-12", "Cna na2 0 5e-12",
          ".save V(pa2) V(na2) V(fpa) V(fna)",
          ".tran 0 %s 0 10n" % tstop,
          ".options plotwinsize=0 reltol=1e-5 abstol=1e-11 vntol=1e-8 "
          "chgtol=1e-14 trtol=2",
          ".end"]
    return "\n".join(L) + "\n"


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


print("=== mid-rail vs near-rail differential step, candidate A ===")
cases = [
    ("near-rail 2.0->3.0/1.0", 2.0, 3.0, 2.0),
    ("mid-rail  1.0->2.0/0.0", 0.0, 2.0, 2.0),
    ("mid-rail  0.8->1.8/-0.2", -0.2, 1.8, 2.0),
    ("mid-rail  small 100 mV", 1.45, 1.55, 0.1),
]
for nm, lo, hi, amp in cases:
    raw, dt = run("mr_%d" % abs(hash(nm) % 10000), net(lo, hi, amp), timeout=180)
    if raw is None:
        print("  %-26s TIMEOUT %.0fs" % (nm, dt), flush=True); continue
    t = np.array([v.real for v in raw.cols[0]], float)
    p = np.array(raw.col("V(pa2)"), float)
    n = np.array(raw.col("V(na2)"), float)
    d = p - n
    q = t > 0.75 * t[-1]
    print("  %-26s npts=%6d tail dm pp=%9.3f mV  mean=%.6f  (%.0fs)"
          % (nm, len(t), d[q].ptp() * 1e3, d[q].mean(), dt), flush=True)
