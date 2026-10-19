"""D6a decomposition: ladder Johnson noise vs ADC-load Johnson noise.

Three noise nets with the real model:
  full        : ladder resistors + 130k differential load both noisy
  ladder_nl   : ladder noiseless, 130k load noisy
  load_nl     : ladder noisy, 130k load noiseless
  all_nl      : both noiseless  (== follower-only baseline)
"""
import os, sys, subprocess, time, json
sys.path.insert(0, r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf")
import numpy as np
import parse_r5 as P

LT = r"C:\Users\chenx\AppData\Local\Programs\ADI\LTspice\LTspice.exe"
D = r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf\r5_work\r3"
LIB = r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf\lib\OPAx388.LIB"
ST = [(2.4, 1e-7, 0.0), (13.0, 1e-7, 1.8e-8)]
LSB = 2.0 * 2.442 / 2 ** 24
FMOD = 4.096e6


def line(side, src, node, st, nl):
    out, prev = [], src
    for i, (r, cg, cd) in enumerate(st, 1):
        if nl:
            out.append("R%s%d %s %s%d R_NOISELESS %s" % (side, i, prev, node, i, r))
        else:
            out.append("R%s%d %s %s%d %s" % (side, i, prev, node, i, r))
        out.append("C%s%d %s%d 0 %s" % (side, i, node, i, cg))
        prev = "%s%d" % (node, i)
    return out


def net(ladder_nl, load_nl):
    L = ["* d6a decomposition", ".include " + LIB,
         ".model R_NOISELESS RES (T_ABS=-273.15)",
         "Vcc vcc 0 DC 3.3", "Vee vee 0 DC 0",
         "Vp vp 0 DC 2 AC 1", "Vn vn 0 DC 2 AC 0",
         "Xfa vp fpa vcc vee fpa OPAx388", "Xfb vn fna vcc vee fna OPAx388"]
    L += line("a", "fpa", "pa", ST, ladder_nl)
    L += line("b", "fna", "na", ST, ladder_nl)
    L += ["Cd pa2 na2 %s" % ST[-1][2]]
    L += ["Rin pa2 na2 %s 130000" % ("R_NOISELESS" if load_nl else "")]
    L += ["Cpa pa2 0 5e-12", "Cna na2 0 5e-12",
          ".noise V(pa2,na2) Vp dec 200 0.1 2.048Meg",
          ".options plotwinsize=0 reltol=1e-6 abstol=1e-12 vntol=1e-9 chgtol=1e-15",
          ".end"]
    return "\n".join(x for x in L if x.strip()) + "\n"


def run(name, text, timeout=120):
    open(os.path.join(D, name + ".net"), "w", encoding="ascii", newline="\n").write(text)
    for ext in (".raw", ".log"):
        q = os.path.join(D, name + ext)
        if os.path.exists(q):
            os.remove(q)
    subprocess.run([LT, "-b", "-ascii", name + ".net"], cwd=D,
                   capture_output=True, text=True, timeout=timeout)
    q = os.path.join(D, name + ".raw")
    return P.Raw(q) if os.path.exists(q) else None


def integ(raw):
    f = np.array([v.real for v in raw.cols[0]], float)
    d = np.abs(np.array(raw.col("v(onoise)")))
    m = f <= FMOD / 2
    return float(np.sqrt(np.trapz(d[m] ** 2, f[m]))), f, d


res = {}
for nm, ln, ld in (("full", False, False), ("ladder_nl", True, False),
                   ("load_nl", False, True), ("all_nl", True, True)):
    raw = run("d6a_" + nm, net(ln, ld))
    v, f, d = integ(raw)
    res[nm] = {"nv": v * 1e9, "lsb": v / LSB,
               "dens_1k_nv": float(np.interp(1e3, f, d)) * 1e9}
    print("%-10s Vn=%8.3f nV  %7.3f LSB   dens@1k=%7.3f nV/rtHz" % (nm, v * 1e9, v / LSB,
                                                                    res[nm]["dens_1k_nv"]),
          flush=True)

tot = res["full"]["nv"]
fol = res["all_nl"]["nv"]
ladder_only = np.hypot(res["full"]["nv"], 0)
# quadrature decomposition
p_ladder = np.hypot(res["load_nl"]["nv"], 0)
print("\n--- decomposition ---")
print("follower only            : %.3f nV" % fol)
print("+ ladder only (noisy/load nl): %.3f nV  -> ladder contribution %.3f nV (%.2f %%)"
      % (res["load_nl"]["nv"], np.hypot(res["load_nl"]["nv"], fol) * 0
         + np.sqrt(max(res["load_nl"]["nv"] ** 2 - fol ** 2, 0)),
         100 * np.sqrt(max(res["load_nl"]["nv"] ** 2 - fol ** 2, 0)) / fol))
print("+ load only (ladder nl)  : %.3f nV  -> 130k contribution %.3f nV (%.2f %%)"
      % (res["ladder_nl"]["nv"],
         np.sqrt(max(res["ladder_nl"]["nv"] ** 2 - fol ** 2, 0)),
         100 * np.sqrt(max(res["ladder_nl"]["nv"] ** 2 - fol ** 2, 0)) / fol))
print("full                     : %.3f nV -> total passive %.3f nV (%.2f %%)"
      % (tot, np.sqrt(max(tot ** 2 - fol ** 2, 0)),
         100 * np.sqrt(max(tot ** 2 - fol ** 2, 0)) / fol))
print("arithmetic (tot-fol)/fol : %.3f %%" % (100 * (tot - fol) / fol))
with open(os.path.join(D, "d6a_decomp.json"), "w", encoding="utf-8", newline="\n") as fh:
    json.dump(res, fh, ensure_ascii=False, indent=2)
