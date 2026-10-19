"""D9 (kickback) — final measurement, real OPA388 model, edge-aligned.

Switch timing exactly as gen_netlists_r5.gen_v8 (spec §7 construction): 0.5 ns edges,
S1/S2 180 deg out of phase, 121.07 ns on each, period 244.1406 ns.
Measurement point = 90 % of the sampling window (te + 0.9*122.07 ns) so the sample is
inside the ON window and clear of the closing edge; also report the value at 100 %.

Warm-up 40 us in gear (this is what converges), then a 5 us fine tail at 0.05 ns.
"""
import os, sys, subprocess, time, json
sys.path.insert(0, r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf")
import numpy as np
import parse_r5 as P
import gen_netlists_r3 as G3

LT = r"C:\Users\chenx\AppData\Local\Programs\ADI\LTspice\LTspice.exe"
D = r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf\r5_work\r3"
OPT = (".options plotwinsize=0 method=gear reltol=1e-5 abstol=1e-11 "
       "vntol=1e-8 chgtol=1e-14 trtol=3")
FMOD = 4.096e6
WIN = 0.5 / FMOD


def build(st, ron=1.0, tstop="40u", tstart="35u", tstep="0.05n"):
    txt = G3.v9k_kick({"stages": st}, ron=ron, tag="v9k_final",
                      tstop=tstop, tstep=tstep, edge="0.5n")
    txt = txt.replace('.options plotwinsize=0 reltol=1e-5 abstol=1e-12 vntol=1e-8 '
                      'chgtol=1e-15 trtol=2', OPT)
    txt = txt.replace(".save V(pa2) V(na2) V(csa) V(csb) V(fpa) V(fna)",
                      ".save V(pa2) V(na2) V(csa) V(csb) V(swp) V(swn) V(fpa) V(fna)")
    txt = txt.replace(".tran 0 %s 0 %s" % (tstop, tstep),
                      ".tran 0 %s %s %s" % (tstop, tstart, tstep))
    return txt


def run(name, text, timeout=600):
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


def measure(raw, ron):
    t = np.array([v.real for v in raw.cols[0]], float)
    a = np.array(raw.col("V(pa2)"), float)
    cs = np.array(raw.col("V(csa)"), float)
    sw = np.array(raw.col("V(swp)"), float)
    idx = np.where((sw[:-1] < 0.5) & (sw[1:] >= 0.5))[0]
    edges = []
    for i in idx:
        w = (0.5 - sw[i]) / (sw[i + 1] - sw[i]) if sw[i + 1] != sw[i] else 0.0
        edges.append(t[i] + w * (t[i + 1] - t[i]))
    rows = []
    for te in edges[3:]:
        if te + WIN > t[-1] - 1e-9:
            break
        v_pre = float(np.interp(te - 2e-9, t, a))
        seg = a[(t >= te) & (t <= te + 0.9 * WIN)]
        if len(seg) < 20:
            continue
        t90 = te + 0.9 * WIN
        v90 = float(np.interp(t90, t, a))
        cs90 = float(np.interp(t90, t, cs))
        v100 = float(np.interp(te + WIN, t, a))
        rows.append({
            "t0_ns": round(te * 1e9, 2),
            "kick_uv": (float(np.interp(te + 1e-9, t, a)) - v_pre) * 1e6,
            "droop_uv": (v_pre - float(seg.min())) * 1e6,
            "resid90_uv": abs(v90 - v_pre) * 1e6,
            "resid90_rel": abs(v90 - v_pre) / abs(v_pre),
            "cs90_rel": abs(cs90 - v90) / abs(v90),
            "resid100_uv": abs(v100 - v_pre) * 1e6,
            "resid100_rel": abs(v100 - v_pre) / abs(v_pre),
        })
    if not rows:
        return {"available": False}
    we = max(rows, key=lambda r: r["resid90_rel"])
    wc = max(rows, key=lambda r: r["cs90_rel"])
    return {"available": True, "ron_ohm": ron, "n_cycles": len(rows),
            "worst_resid90_uv": we["resid90_uv"],
            "worst_resid90_rel": we["resid90_rel"],
            "worst_resid100_rel": max(r["resid100_rel"] for r in rows),
            "worst_kick_uv": max(abs(r["kick_uv"]) for r in rows),
            "worst_droop_uv": max(r["droop_uv"] for r in rows),
            "worst_cs90_rel": wc["cs90_rel"],
            "pin_pass_0p01pct": bool(we["resid90_rel"] <= 1e-4),
            "cs_pass_0p01pct": bool(wc["cs90_rel"] <= 1e-4),
            "detail": rows[-3:]}


if __name__ == "__main__":
    ST = [(2.4, 1e-7, 0.0), (13.0, 1e-7, 1.8e-8)]
    out = {}
    for ron in (1.0, 100.0, 1000.0):
        raw, dt = run("dk_ron%g" % ron, build(ST, ron=ron), timeout=600)
        if raw is None:
            print("ron=%g TIMEOUT %.0fs" % (ron, dt), flush=True)
            out["ron%g" % ron] = {"available": False, "err": "TIMEOUT"}
            continue
        m = measure(raw, ron)
        m["sim_s"] = round(dt, 1)
        out["ron%g" % ron] = m
        print("ron=%g: %s" % (ron, json.dumps({k: v for k, v in m.items() if k != "detail"})),
              flush=True)
    with open(os.path.join(D, "d9_final.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
    print("→ d9_final.json")
