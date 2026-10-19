import os, sys, json, math
sys.path.insert(0, r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf")
import numpy as np
import parse_r5 as P

D = r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf\r5_work\r3"
LSB = 2.0 * 2.442 / 2 ** 24
FMOD, MCLK = 4.096e6, 16.384e6


def at(raw, f, node):
    return P.interp_at(raw, f, node)


def main():
    out = {}
    # ---------- V9a: D1/D3/D4/D10 + C9 peaking ----------
    r = P.Raw(os.path.join(D, "r5_A_r3_v9a.raw"))
    f = r.f
    p = np.array(r.col("V(pa2)"), complex)
    n = np.array(r.col("V(na2)"), complex)
    d = p - n
    dc = at(r, 0.1, "V(pa2)") - at(r, 0.1, "V(na2)")
    gdc = P.db(dc)
    out["V9a"] = {
        "g_dc_db": gdc,
        "g_16k_db": P.db(at(r, 16e3, "V(pa2)") - at(r, 16e3, "V(na2)")),
        "g_fmod_db": P.db(at(r, FMOD, "V(pa2)") - at(r, FMOD, "V(na2)")),
        "g_mclk_db": P.db(at(r, MCLK, "V(pa2)") - at(r, MCLK, "V(na2)")),
    }
    out["V9a"]["D1_A_dm_db"] = -(out["V9a"]["g_fmod_db"] - gdc)
    out["V9a"]["D3_A_mclk_db"] = -(out["V9a"]["g_mclk_db"] - gdc)
    out["V9a"]["D4_dG_16k_db"] = abs(out["V9a"]["g_16k_db"] - gdc)

    # D10 group delay
    m = (f >= 0.1) & (f <= 16e3)
    ph = np.unwrap(np.angle(d[m]))
    tau = -np.gradient(ph, 2 * math.pi * f[m])
    out["V9a"]["D10_dtau_us"] = float((tau.max() - tau.min()) * 1e6)
    out["V9a"]["tau_100Hz_us"] = float(tau[0] * 1e6)
    out["V9a"]["tau_16k_us"] = float(tau[-1] * 1e6)
    # CH1 vs CH2 (per-line) group delay difference
    tp = -np.gradient(np.unwrap(np.angle(p[m])), 2 * math.pi * f[m])
    tn = -np.gradient(np.unwrap(np.angle(n[m])), 2 * math.pi * f[m])
    out["V9a"]["CH_tau_diff_max_us"] = float(np.max(np.abs(tp - tn)) * 1e6)
    out["V9a"]["tau_p_16k_us"] = float(tp[-1] * 1e6)
    out["V9a"]["tau_n_16k_us"] = float(tn[-1] * 1e6)

    # C9 peaking from v9a itself (0.1 Hz .. 200 MHz)
    g = 20 * np.log10(np.abs(d) / abs(d[0]))
    mm = (f >= 1.0) & (f <= 2e6)
    i = int(np.argmax(g[mm]))
    out["V9a"]["C9_peaking_db_1Hz_2MHz"] = float(g[mm][i])
    out["V9a"]["C9_peaking_f_hz"] = float(f[mm][i])
    # also full band
    i2 = int(np.argmax(g))
    out["V9a"]["peak_all_db"] = float(g[i2])
    out["V9a"]["peak_all_f_hz"] = float(f[i2])

    # ---------- V9pk: fine peaking ----------
    rp = P.Raw(os.path.join(D, "r5_A_r3_v9pk.raw"))
    fp = rp.f
    dp = np.array(rp.col("V(pa2)"), complex) - np.array(rp.col("V(na2)"), complex)
    gp = 20 * np.log10(np.abs(dp) / abs(dp[0]))
    mp = (fp >= 1.0) & (fp <= 2e6)
    ip = int(np.argmax(gp[mp]))
    out["V9pk"] = {"peaking_db": float(gp[mp][ip]), "f_hz": float(fp[mp][ip]),
                   "npts": len(fp)}
    # per-node peak (line A pin, follower output) for diagnostics
    for nm in ("V(pa1)", "V(pa2)", "V(fpa)"):
        if nm in rp.names:
            y = np.array(rp.col(nm), complex)
            gy = 20 * np.log10(np.abs(y) / abs(y[0]))
            j = int(np.argmax(gy[mp]))
            out["V9pk"]["peak_" + nm] = [float(gy[mp][j]), float(fp[mp][j])]

    # ---------- V9b: D2 ----------
    rb = P.Raw(os.path.join(D, "r5_A_r3_v9b.raw"))
    out["V9b"] = {
        "g_cm_dc_db": P.db(at(rb, 0.1, "V(pa2)")),
        "g_cm_fmod_db": P.db(at(rb, FMOD, "V(pa2)")),
        "D2_A_cm_db": -(P.db(at(rb, FMOD, "V(pa2)")) - P.db(at(rb, 0.1, "V(pa2)"))),
        "g_cm_mclk_db": P.db(at(rb, MCLK, "V(pa2)")),
    }

    # ---------- V9d / V9dn: D6a / D6b ----------
    def integ(path):
        rr = P.Raw(path)
        ff = np.array([v.real for v in rr.cols[0]], float)
        dens = np.abs(np.array(rr.col("v(onoise)")))
        msk = ff <= FMOD / 2
        return float(np.sqrt(np.trapz(dens[msk] ** 2, ff[msk]))), ff, dens

    tot, f1, d1 = integ(os.path.join(D, "r5_A_r3_v9d.raw"))
    fol, f2, d2 = integ(os.path.join(D, "r5_A_r3_v9dn.raw"))
    out["D6"] = {
        "V9d_total_nv": tot * 1e9, "V9d_total_lsb": tot / LSB,
        "V9dn_follower_only_nv": fol * 1e9, "V9dn_follower_only_lsb": fol / LSB,
        "D6a_increment_pct": 100.0 * (tot - fol) / fol if fol > 0 else None,
        "D6b_total_lsb": tot / LSB,
        "dens_1k_total_nv": float(np.interp(1e3, f1, d1)) * 1e9,
        "dens_1k_foll_nv": float(np.interp(1e3, f2, d2)) * 1e9,
    }
    # D6a alternative definition (quadrature): sqrt(tot^2 - fol^2)/fol
    out["D6"]["D6a_quadrature_pct"] = (100.0 * math.sqrt(max(tot ** 2 - fol ** 2, 0.0)) / fol
                                       if fol > 0 else None)

    # ---------- D8 paired mismatch ----------
    d8 = {}
    for m in (0.001, 0.005, 0.01):
        for kind in ("pair", "same"):
            q = os.path.join(D, f"r5_A_r3_v9p_m{m:g}_{kind}.raw")
            if not os.path.exists(q):
                continue
            rr = P.Raw(q)
            ff = rr.f
            pp = np.array(rr.col("V(pa2)"), complex)
            nn = np.array(rr.col("V(na2)"), complex)
            sel = (ff >= 10) & (ff <= 16e3)
            cm = np.abs((pp[sel] + nn[sel]) / 2.0)
            dm = np.abs(pp[sel] - nn[sel])
            cmrr = 20 * np.log10(cm / np.maximum(dm, 1e-300))
            k = int(np.argmin(cmrr))
            d8[f"m{m:g}_{kind}"] = {
                "cmrr_min_db": float(cmrr[k]),
                "f_worst_hz": float(ff[sel][k]),
                "cmrr_10hz_db": float(cmrr[0]),
                "cmrr_16k_db": float(cmrr[-1]),
            }
    out["D8"] = d8

    print(json.dumps(out, indent=1, ensure_ascii=False, default=float))
    with open(os.path.join(D, "core_r3.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2, default=float)


if __name__ == "__main__":
    main()
