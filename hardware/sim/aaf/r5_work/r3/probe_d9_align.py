"""D9 re-measurement with proper switch-edge alignment.

The earlier parse_r5.kickback() assumed S1 turns on at k*T, but the PULSE control has a
finite rise so the SW threshold is crossed later. Here we save V(swp)/V(swn), find the
real edge, and measure the pin residual over exactly 122.07 ns from that edge.
Also reports the charge-bucket droop (physically the quantity D9 is about).
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


def build(st, tstop="40u", tstart="0", tstep="20n", ron=1.0, edge="2n"):
    txt = G3.v9k_kick({"stages": st}, ron=ron, tag="v9k_align",
                      tstop=tstop, tstep=tstep, edge=edge)
    txt = txt.replace('.options plotwinsize=0 reltol=1e-5 abstol=1e-12 vntol=1e-8 '
                      'chgtol=1e-15 trtol=2', OPT)
    txt = txt.replace(".save V(pa2) V(na2) V(csa) V(csb) V(fpa) V(fna)",
                      ".save V(pa2) V(na2) V(csa) V(csb) V(swp) V(swn) V(fpa) V(fna)")
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


def measure(raw, ron_label=""):
    t = np.array([v.real for v in raw.cols[0]], float)
    a = np.array(raw.col("V(pa2)"), float)
    cs = np.array(raw.col("V(csa)"), float)
    sw = np.array(raw.col("V(swp)"), float)
    # rising crossings of the control through Vt=0.5 (SW threshold)
    idx = np.where((sw[:-1] < 0.5) & (sw[1:] >= 0.5))[0]
    edges = []
    for i in idx:
        w = (0.5 - sw[i]) / (sw[i + 1] - sw[i]) if sw[i + 1] != sw[i] else 0.0
        edges.append(t[i] + w * (t[i + 1] - t[i]))
    rows = []
    for te in edges[3:]:
        if te + WIN > t[-1]:
            break
        t0 = te
        t1 = te + WIN
        v_pre = float(np.interp(t0 - 2e-9, t, a))
        v_end = float(np.interp(t1, t, a))
        seg = a[(t >= t0) & (t <= t1)]
        if len(seg) < 10:
            continue
        v_cs_end = float(np.interp(t1, t, cs))
        rows.append({
            "t0_ns": round(te * 1e9, 2),
            "kick_uv": (float(np.interp(t0 + 2e-9, t, a)) - v_pre) * 1e6,
            "droop_uv": (v_pre - seg.min()) * 1e6,
            "resid_uv": abs(v_end - v_pre) * 1e6,
            "resid_rel": abs(v_end - v_pre) / abs(v_pre),
            "cs_resid_nv": abs(v_cs_end - v_end) * 1e9,
            "cs_rel": abs(v_cs_end - v_end) / abs(v_end),
        })
    if not rows:
        return {"available": False}
    worst_e = max(rows, key=lambda r: r["resid_rel"])
    worst_cs = max(rows, key=lambda r: r["cs_rel"])
    return {"available": True, "n_cycles": len(rows), "ron": ron_label,
            "worst_pin_resid_uv": worst_e["resid_uv"],
            "worst_pin_rel": worst_e["resid_rel"],
            "pin_pass_0p01pct": bool(worst_e["resid_rel"] <= 1e-4),
            "worst_kick_uv": max(r["kick_uv"] for r in rows),
            "worst_droop_uv": max(r["droop_uv"] for r in rows),
            "worst_cs_resid_nv": worst_cs["cs_resid_nv"],
            "worst_cs_rel": worst_cs["cs_rel"],
            "cs_pass_0p01pct": bool(worst_cs["cs_rel"] <= 1e-4),
            "detail": rows[-3:]}


if __name__ == "__main__":
    out = {}
    # real model, candidate A, 40 us warm-up + fine tail
    for lbl, st in (("A_real", [(2.4, 1e-7, 0.0), (13.0, 1e-7, 1.8e-8)]),
                    ("A_real_600k", [(2.4, 1e-7, 0.0), (13.0, 1e-7, 1.8e-8)])):
        raw, dt = run("dl_%s" % lbl, build(st, tstop="40u", tstart="35u",
                                           tstep="0.05n"), timeout=420)
        if raw is None:
            out[lbl] = {"available": False, "err": "TIMEOUT %.0fs" % dt}
            print(lbl, "TIMEOUT %.0fs" % dt, flush=True)
            continue
        m = measure(raw, "real/Ron=1")
        m["sim_s"] = round(dt, 1)
        out[lbl] = m
        print(lbl, json.dumps(m, ensure_ascii=False)[:400], flush=True)
    with open(os.path.join(D, "d9_align.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
    print("→ d9_align.json")
