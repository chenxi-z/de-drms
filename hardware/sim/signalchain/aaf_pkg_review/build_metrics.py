#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_metrics.py — tran 族汇总指标（读 5 张 CSV → csv/tran_metrics.json + stdout）"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CSVD = HERE / "csv"
SCHEMES = ["S0", "S1", "T1", "T2", "T3", "T4"]


def read(name):
    with (CSVD / name).open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def f(x, default=None):
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def main():
    t04 = {(r["scheme"], r["scenario"]): r for r in read("t04_settling.csv")}
    t08 = read("t08_kickback.csv")
    t09a = read("t09_ac_residual.csv")
    t09f = read("t09_fold_check.csv")
    thd = {(r["scheme"], r["f0_hz"]): r for r in read("thd_summary.csv")}

    metrics: dict[str, dict[str, float]] = {}
    for sid in SCHEMES:
        m: dict[str, float] = {}
        for scen, key in (("nom", "nom"), ("ch1", "ch1"), ("tol", "tol"), ("tolcm", "tolcm"),
                          ("vlo", "vlo"), ("vhi", "vhi"), ("src10k", "src10k"),
                          ("src120k", "src120k")):
            r = t04.get((sid, scen), {})
            v = f(r.get("ts01_us"))
            if v is not None:
                m[f"T04_ts01_{key}_us"] = v
        v = f(t04.get((sid, "nom"), {}).get("ts10_us"))
        if v is not None:
            m["T04_ts10_nom_us"] = v
        # T08：引脚最坏（全部 ron/vcm 角）
        pin = [r for r in t08 if r["scheme"] == sid and r.get("node") == "pin"]
        n1 = [r for r in t08 if r["scheme"] == sid and r.get("node") == "node1"]
        r100 = [r for r in pin if r["tag"] == "ron100" and r["node_name"] == "a1p"]
        if r100:
            m["T08_kick_a1p_ron100_uv"] = f(r100[0]["kick_amp_uv"])
        if pin:
            m["T08_resid_worst_uv"] = max(f(r["resid_end_uv"], 0) for r in pin)
            m["T08_rel_ch_worst"] = max(f(r["rel_to_ch"], 0) for r in pin)
            m["T08_d9_chan_pass"] = 1.0 if all(
                r.get("pass01_ch") == "True" for r in pin) else 0.0
        if n1:
            m["T08_node1_resid_worst_uv"] = max(f(r["resid_end_uv"], 0) for r in n1)
            m["T08_node1_rel_ch_worst"] = max(f(r["rel_to_ch"], 0) for r in n1)
        # T09：AC 引脚残差 @fMOD + 折回最坏（实测瞬态口径）
        for r in t09a:
            if r["scheme"] == sid and abs(f(r["f_inj_hz"], 0) - 4.096e6) < 1:
                m["T09_ac_dm_resid_db_at_fmod"] = f(r["resid_dm_phased_db"])
        fol = [r for r in t09f if r["scheme"] == sid and r.get("output_alias_uv")]
        if fol:
            worst = max(fol, key=lambda r: f(r["output_alias_uv"], 0))
            m["T09_fold_worst_alias_uv_100mV"] = f(worst["output_alias_uv"])
            m["T09_fold_worst_alias_lsb"] = f(worst["alias_in_lsb"])
        # THD
        for f0, tag in (("1000.0", "1k"), ("16000.0", "16k")):
            r = thd.get((sid, f0)) or thd.get((sid, f0.rstrip(".0")))
            if r is None:                     # f0_hz 列可能是 "1000"/"16000"
                for cand, rr in thd.items():
                    if cand[0] == sid and abs(f(cand[1], 0) - f(f0, 0)) < 1:
                        r = rr
                        break
            if r and r.get("thd_total_pct"):
                m[f"THD_total_{tag}_pct"] = f(r["thd_total_pct"])
                if r.get("thd_h2_10_pct") != "":
                    m[f"THD_h2_10_{tag}_pct"] = f(r["thd_h2_10_pct"])
                    m[f"THD_h2_10_{tag}_lsb"] = f(r["harm_h2_10_lsb"])
                if r.get("dominant_harm"):
                    m[f"THD_dom_harm_{tag}"] = f(r["dominant_harm"])
        metrics[sid] = m

    out = CSVD / "tran_metrics.json"
    out.write_text(json.dumps(metrics, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False, indent=1))
    print(f"[metrics] -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
