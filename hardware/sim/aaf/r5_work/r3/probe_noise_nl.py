import os, sys, subprocess, time
sys.path.insert(0, r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf")
import numpy as np
import parse_r5 as P

LT = r"C:\Users\chenx\AppData\Local\Programs\ADI\LTspice\LTspice.exe"
LIB = r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf\lib\OPAx388.LIB"


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
    return (P.Raw(name + ".raw") if os.path.exists(name + ".raw") else None), "", time.time() - t0


ST = [(2.4, 1e-7, 0.0), (13.0, 1e-7, 1.8e-8)]


def line(side, src, node, st, noiseless=False):
    out = []
    prev = src
    for i, (r, cg, cd) in enumerate(st, 1):
        if noiseless:
            out.append("R%s%d %s %s%d R_NOISELESS %s" % (side, i, prev, node, i, r))
        else:
            out.append("R%s%d %s %s%d %s" % (side, i, prev, node, i, r))
        out.append("C%s%d %s%d 0 %s" % (side, i, node, i, cg))
        prev = "%s%d" % (node, i)
    return out


def noise_net(nl_ladder, nl_load):
    L = ["* noise noiseless test", ".include " + LIB,
         ".model R_NOISELESS RES (T_ABS=-273.15)",
         "Vcc vcc 0 DC 3.3", "Vee vee 0 DC 0",
         "Vp vp 0 DC 2 AC 1", "Vn vn 0 DC 2 AC 0",
         "Xfa vp fpa vcc vee fpa OPAx388", "Xfb vn fna vcc vee fna OPAx388"]
    L += line("a", "fpa", "pa", ST, nl_ladder)
    L += line("b", "fna", "na", ST, nl_ladder)
    L += ["Cd pa2 na2 1.8e-8"]
    L += ["Rin pa2 na2 %s 130000" % ("R_NOISELESS" if nl_load else "")]
    L += ["Cpa pa2 0 5e-12", "Cna na2 0 5e-12",
          ".noise V(pa2,na2) Vp dec 200 0.1 2.048Meg",
          ".options plotwinsize=0 reltol=1e-6 abstol=1e-12 vntol=1e-9 chgtol=1e-15",
          ".end"]
    return "\n".join(x for x in L if x.strip()) + "\n"


print("=== noise: normal / ladder-noiseless / all-noiseless ===", flush=True)
for nm, a, b in (("n_plain", False, False), ("n_nl_ladder", True, False), ("n_nl_all", True, True)):
    raw, msg, dt = run(nm, noise_net(a, b))
    if raw is None:
        print("  %s FAIL %s" % (nm, msg)); continue
    f = np.array([v.real for v in raw.cols[0]], float)
    d = np.abs(np.array(raw.col("v(onoise)")))
    m = f <= 2.048e6
    tot = float(np.sqrt(np.trapz(d[m] ** 2, f[m])))
    print("  %-12s : Vn = %8.2f nV = %6.3f LSB   dens@1k=%.3f nV  (%.1fs)"
          % (nm, tot * 1e9, tot / 290.98e-9, float(np.interp(1e3, f, d)) * 1e9, dt), flush=True)
