"""Decisive probes for candidate A real-model transients (D5 / D9).

Builds three nets exactly in the style of gen_netlists_r5.gen_v9c / gen_v9f / gen_v8,
but with solver settings tuned per the ask (trap, small max timestep, long window).
"""
import os, sys, json, subprocess, time
sys.path.insert(0, r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf")
import numpy as np
import parse_r5 as P

LT = r"C:\Users\chenx\AppData\Local\Programs\ADI\LTspice\LTspice.exe"
ROOT = r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf"
LIB = os.path.join(ROOT, "lib", "OPAx388.LIB")
D = os.path.join(ROOT, "r5_work", "r3", "probe_d5")
os.makedirs(D, exist_ok=True)

cand = json.load(open(os.path.join(ROOT, "r5_candidates_r2.json"), encoding="utf-8"))["A"]
ST = [tuple(map(float, s)) for s in cand["stages"]]
NS = len(ST)


def line(side, src, node, st):
    out, prev = [], src
    for i, (r, cg, cd) in enumerate(st, 1):
        out.append("R%s%d %s %s%d %.10g" % (side, i, prev, node, i, r))
        out.append("C%s%d %s%d 0 %.10g" % (side, i, node, i, cg))
        prev = "%s%d" % (node, i)
    return out


def common(st):
    a, b = "pa%d" % len(st), "na%d" % len(st)
    return ["Cd %s %s %.10g" % (a, b, st[-1][2]),
            "Rin %s %s 130000" % (a, b),
            "Cpa %s 0 5e-12" % a, "Cna %s 0 5e-12" % b]


def head(tag):
    return ["* r3 probe " + tag, ".include " + LIB,
            "Vcc vcc 0 DC 3.3", "Vee vee 0 DC 0"]


def tran_net(tag, st, hz=False, zc=False, tstop="500u", tstep="10n", opts=None):
    L = head(tag)
    L += ["Vp vp 0 PULSE(2 3 10u 10n 10n 600u 2m)",
          "Vn vn 0 PULSE(2 1 10u 10n 10n 600u 2m)"]
    if zc:
        L += ["Rsa vp fa 600k", "Rsb vn fb 600k",
              "Xfa fa fpa vcc vee fpa OPAx388", "Xfb fb fna vcc vee fna OPAx388"]
    else:
        L += ["Xfa vp fpa vcc vee fpa OPAx388", "Xfb vn fna vcc vee fna OPAx388"]
    L += line("a", "fpa", "pa", st) + line("b", "fna", "na", st) + common(st)
    L += [".save V(pa%d) V(na%d) V(fpa) V(fna)" % (NS, NS)]
    L += [".tran 0 %s 0 %s" % (tstop, tstep)]
    L += [opts or ".options plotwinsize=0 reltol=1e-5 abstol=1e-11 vntol=1e-8 "
                 "chgtol=1e-14 trtol=2"]
    L += [".end"]
    return "\n".join(L) + "\n"


def kick_net(tag, st, ron=1.0, tstop="6u", tstep="0.05n"):
    a, b = "pa%d" % NS, "na%d" % NS
    L = head(tag)
    L += [".model SWK SW(Ron=%g Roff=1e12 Vt=0.5 Vh=0)" % ron,
          "Vp vp 0 DC 3.2", "Vn vn 0 DC 0.8", "Vcm vcm 0 DC 2.0",
          "Xfa vp fpa vcc vee fpa OPAx388", "Xfb vn fna vcc vee fna OPAx388"]
    L += line("a", "fpa", "pa", st) + line("b", "fna", "na", st) + common(st)
    L += ["S1a %s csa swp 0 SWK" % a, "Csa csa vcm 1.75e-12", "S2a csa vcm swn 0 SWK",
          "S1b %s csb swn 0 SWK" % b, "Csb csb vcm 1.75e-12", "S2b csb vcm swp 0 SWK",
          "Vswp swp 0 PULSE(0 1 0 0.5n 0.5n 121.07n 244.1406n)",
          "Vswn swn 0 PULSE(0 1 122.07n 0.5n 0.5n 121.07n 244.1406n)",
          ".save V(%s) V(%s) V(csa) V(csb)" % (a, b),
          ".tran 0 %s 0 %s" % (tstop, tstep),
          ".options plotwinsize=0 reltol=1e-5 abstol=1e-12 vntol=1e-8 "
          "chgtol=1e-15 trtol=2",
          ".end"]
    return "\n".join(L) + "\n"


def run(name, text, timeout=600):
    path = os.path.join(D, name + ".net")
    open(path, "w", encoding="ascii", newline="\n").write(text)
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


def ana(raw, ns=NS):
    t = np.array([v.real for v in raw.cols[0]], float)
    p = np.array(raw.col("V(pa%d)" % ns), float)
    n = np.array(raw.col("V(na%d)" % ns), float)
    d = p - n
    m = t >= 10e-6
    tt, dd = t[m], d[m]
    vf = float(dd[-1])
    out = np.where(np.abs(dd - vf) > 200e-6)[0]
    ts = float((tt[out[-1]] - 10e-6) * 1e6) if len(out) else 0.0
    q = t > 0.7 * t[-1]
    return dict(tset_us=round(ts, 2), final=round(vf, 6), npts=len(t),
                tail_pp_mV=round(float((d[q].max() - d[q].min()) * 1e3), 3),
                tail_mean=round(float(d[q].mean()), 6),
                err_uv=round(float(abs(vf - 2.0) * 1e6), 1))


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    cases = [
        ("d5_nom_0ohm", tran_net("nom0", ST)),
        ("d5_wc_0ohm", tran_net("wc0", [(r * 1.01, c * 1.05, cd * 1.05)
                                        for r, c, cd in ST])),
        ("d5_wc_600k", tran_net("wc600", [(r * 1.01, c * 1.05, cd * 1.05)
                                          for r, c, cd in ST], zc=True)),
        ("d9_kick_ron1", kick_net("kick", ST, 1.0)),
    ]
    for nm, txt in cases:
        if which != "all" and which not in nm:
            continue
        raw, msg, dt = run(nm, txt)
        if raw is None:
            print("%-16s FAIL %s (%.1fs)" % (nm, msg, dt), flush=True)
            continue
        print("%-16s %s  (%.1fs)" % (nm, ana(raw), dt), flush=True)
