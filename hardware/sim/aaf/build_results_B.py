# -*- coding: utf-8 -*-
"""build_results_B.py — 方案 B（3 级）十维实测值汇总 → r5_results_B.json

消费 `parse_r5.analyze('B')` 的嵌套实测结果 + `xcheck_B.py` 的 0 Ω 理论 + V9e/V9f 补充量。

十维口径（规格 §5.1 / ask）：
  D1 A_dm@4.096 MHz (dB, 正=衰减)   D2 A_cm@4.096 MHz (dB)   D3 A_dm@16.384 MHz (dB)
  D4 |ΔG|@16 kHz (dB)               D5 建立 µs（0.01% 带）     D6 噪声 nVrms
  D7 σ(ΔG@16k) (dB)                 D8 CMRR 通带最差 (dB)      D9 1.0/0.0   D10 Δτ µs

交叉验证（规格 §8）：AC 四项 ≤0.5 dB、建立 ≤5%。
理论基准用 **源阻抗 0 Ω**（§5.1 标准测试条件）——opt_round5/opt_engine 内 rs 硬编码 1 Ω，
直接对拍会凭空差 1.54 dB，见 xcheck_B.py 文件头。

用法：python build_results_B.py
"""
from __future__ import annotations

import json
import math
import os

import numpy as np

import parse_r5 as P
import xcheck_B as X

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "r5_results_B.json")
SCHEME = "B"

FMOD, MCLK = 4.096e6, 16.384e6

# 引擎/解析器缺省判定带 120 µV 是 2 V 阶跃的 0.006%；规格写的 0.01% = 200 µV。
# parse_r5.analyze() 两档都算：V4["tset_us"] = 规格带，V4["tset_engine_band_us"] = 严格带。
BAND_SPEC = 200e-6


def _r(x, n=4):
    return round(float(x), n)


def build():
    cand = json.load(open(os.path.join(HERE, "r5_candidates.json"), encoding="utf-8"))[SCHEME]
    st = [tuple(map(float, s)) for s in cand["stages"]]
    ns = len(st)
    res = P.analyze(SCHEME, HERE)

    # ---------------- V9 补充：600 kΩ 样品端（规格 §5.1 高源阻抗工况） ----------------
    v9e = P.Raw(os.path.join(HERE, f"r5_{SCHEME}_v9e.raw"))
    pa, na = f"V(pa{ns})", f"V(na{ns})"

    def gdb(rr, f, diff=True):
        v = (P.interp_at(rr, f, pa) - P.interp_at(rr, f, na)) if diff else P.interp_at(rr, f, pa)
        return P.db(v)

    dc6 = gdb(v9e, 0.1)
    v9_600k = {
        "A_dm_db": _r(-(gdb(v9e, FMOD) - dc6), 2),
        "A_mclk_db": _r(-(gdb(v9e, MCLK) - dc6), 2),
        "dG_16k_db": _r(abs(gdb(v9e, 16e3) - dc6), 4),
        # 600 kΩ + 跟随器输入电容构成的 RC（跟随器输入节点 V(fa) 相对源）
        "input_rc_droop_16k_db": _r(P.db(P.interp_at(v9e, 16e3, "V(fa)"))
                                    - P.db(P.interp_at(v9e, 16e3, "V(vp)")), 4),
    }
    # 由 16 kHz 的相对跌落反解等效输入电容
    r16 = 10 ** (v9_600k["input_rc_droop_16k_db"] / 20.0)
    v9_600k["implied_Cin_pF"] = _r(
        math.sqrt(max(1.0 / r16 ** 2 - 1.0, 0.0)) / (2 * math.pi * 16e3 * 600e3) * 1e12, 2)

    # ---------------- CH1 vs CH2 群延迟差（规格 §5.1 注：相位测量要求） ----------------
    # two_line 的节点编号：P 线 0..n-1（引脚 = n-1），N 线 n..2n-1（引脚 = 2n-1）
    f = np.logspace(1, math.log10(16e3), 200)
    v3 = X.two_line(st, f, 1.01, 1.01, 1.0, 1.0, dm=False)
    jp, jn = ns, 2 * ns + 1          # ns = len(stages) = n-1
    tp = -np.gradient(np.unwrap(np.angle(v3[:, jp])), 2 * math.pi * f)
    tn = -np.gradient(np.unwrap(np.angle(v3[:, jn])), 2 * math.pi * f)
    ch_diff_mismatch_ns = _r(np.abs(tp - tn).max() * 1e9, 3)

    # ---------------- 温度角 ----------------
    tcorner = {}
    for tt in (-20, 85):
        rr = P.Raw(os.path.join(HERE, f"r5_{SCHEME}_v1t{tt:+d}C.raw"))
        dc = gdb(rr, 0.1)
        tcorner[f"{tt:+d}C"] = {"dG_16k_db": _r(abs(gdb(rr, 16e3) - dc), 4),
                                "A_dm_db": _r(-(gdb(rr, FMOD) - dc), 3)}

    # ---------------- 十维 ----------------
    # D5 口径：规格 §5.1 D5 原文「建立时间（最坏角）… **测试须覆盖高源阻抗工况（样品 600 kΩ 端）**」。
    # 全部候选（都是 R×1.01 / C×1.05 最坏角）：
    #   V4   0 Ω 源 + **理想**跟随器                       24.65 µs（基线，与理论对拍用）
    #   V9c  跟随器直驱阶梯 + **真实 OPA388**              34.68 µs ← 实测最慢
    #   V9f  600 kΩ 样品端 + 真实 OPA388                   30.32 µs（规格要求覆盖的工况）
    #   V4b  600 kΩ + 理想跟随器 + 8.5 pF 未自举输入电容   51.18 µs（**显式悲观上界**，非真实模型）
    # 取 V9c/V9f 的较慢者作 D5：两者都是真实运放模型；V9c 更慢是因为 0 Ω 源下阶跃沿更陡，
    # 更充分地激励了跟随器的瞬态恢复（600 kΩ + 4.5 pF 的 2.7 µs 输入极点把沿拉缓了）。
    # 低阻端（73 Ω）的样品正是这种陡沿工况，故 V9c 才是物理最坏角。
    d = res["dims"]
    v9c_us = res["V9"].get("t_settle_us")
    v9f_us = res["V9"].get("t_settle_us_600k")
    d5_candidates = {
        "V4_0ohm_ideal_follower_us": _r(res["V4"]["tset_us"], 2),
        "V9c_0ohm_real_follower_us": _r(v9c_us, 2) if v9c_us else None,
        "V9f_600k_real_follower_us": _r(v9f_us, 2) if v9f_us else None,
        "V4b_600k_ideal_unbootstrapped_us_UPPER_BOUND": _r(res["V4b"]["tset_us"], 2),
    }
    d5_real = [x for x in (v9c_us, v9f_us) if x]
    d5_value = max(d5_real) if d5_real else res["V4"]["tset_us"]

    dims = {
        "D1": _r(d["D1"], 3),
        "D2": _r(d["D2"], 3),
        "D3": _r(d["D3"], 3),
        "D4": _r(d["D4"], 4),
        "D5": _r(d5_value, 2),
        "D6": _r(d["D6"], 1),
        "D7": _r(d["D7"], 4),
        "D8": _r(d["D8"], 2),
        "D9": float(d["D9"]),
        "D10": _r(d["D10"], 4),
    }

    # ---------------- 理论（0 Ω 源，双线 MNA） ----------------
    th = X.predict_zero_source(st)
    th_r = {k: _r(v, 4) for k, v in th.items()}

    # ---------------- 交叉验证 ----------------
    # 规格 §8 给两条容差：AC ≤0.5 dB、建立 ≤5%。噪声不在该条内，按 5% 相对量级校核
    # （不是 0.5 dB：0.844 dB 只是 +10% 幅度，混用会把单位搞错）。
    xc = {}
    for name, lt, thv in (
            ("A_dm", dims["D1"], th["A_dm"]),
            ("A_cm", dims["D2"], th["A_cm"]),
            ("A_mclk", dims["D3"], th["A_mclk"]),
            ("dG_16k", dims["D4"], th["dG_16k"]),
            ("CMRR", dims["D8"], th["CMRR_pb_db"]),
            ("dtau_us", dims["D10"], th["dtau_us"])):
        dlt = lt - thv
        xc[name] = {"lt": _r(lt, 4), "th": _r(thv, 4), "delta": _r(dlt, 4),
                    "pass_0p5": bool(abs(dlt) <= 0.5)}
    # 噪声：相对偏差口径（0.5 dB 不适用）
    dlt_n = dims["D6"] - th["Vn_nv"]
    xc["Vn_nv"] = {"lt": _r(dims["D6"], 2), "th": _r(th["Vn_nv"], 2),
                   "delta": _r(dlt_n, 2),
                   "rel_pct": _r(100 * dlt_n / th["Vn_nv"], 2),
                   "pass_5pct": bool(abs(dlt_n) <= 0.05 * th["Vn_nv"])}
    # D7：理论 MC30（逐元件独立均匀分布，与 V5 网表同种子同口径）
    # 注意：D7 是**统计量**（σ 的估计）。30 样本下 σ̂ 的相对标准误 ≈ 1/√(2(n−1)) = 13.1%，
    # 套 §8 的 5% 判据会把纯抽样噪声判成模型错误 → 改用「落在 2σ 抽样带内」。
    rng = np.random.default_rng(20261018)
    gmc = []
    for _ in range(30):
        sx = [(st[i][0] * rng.uniform(0.99, 1.01), st[i][1] * rng.uniform(0.95, 1.05),
               st[i][2] * rng.uniform(0.95, 1.05)) for i in range(ns)]
        sy = [(st[i][0] * rng.uniform(0.99, 1.01), st[i][1] * rng.uniform(0.95, 1.05),
               st[i][2] * rng.uniform(0.95, 1.05)) for i in range(ns)]
        gmc.append(0.5 * (X.dm_gain_db(sx, 16e3)[0] + X.dm_gain_db(sy, 16e3)[0]))
    th_d7 = float(np.std(gmc, ddof=1))
    se_d7 = th_d7 / math.sqrt(2 * (len(gmc) - 1))
    d7_delta = dims["D7"] - th_d7
    xc["D7_sigma"] = {"lt": _r(dims["D7"], 4), "th": _r(th_d7, 4),
                      "delta": _r(d7_delta, 4),
                      "rel_pct": _r(100 * d7_delta / th_d7, 2),
                      "se_1sigma": _r(se_d7, 4),
                      "z_score": _r(d7_delta / se_d7, 2),
                      "criterion": "|z| <= 2（30 样本 σ̂ 抽样标准误 13.1%，5% 判据不适用）",
                      "pass_stat": bool(abs(d7_delta) <= 2 * se_d7)}
    xc["D7_opt_round5_proxy"] = {
        "value": _r(cand["pred"]["sigma_dG_db"], 5),
        "note": "opt_round5 代理为 +tol 单点扰动 RSS，非均匀分布 sigma；"
                "比实测高 ~3x（漏了 √3 与逐元件独立抽样）"}
    # 建立时间：**同工况对拍**——V4（0 Ω 源 + 最坏角）↔ 理论的 0 Ω 最坏角。
    # D5 的取值是 600 kΩ 工况（规格要求覆盖），但那条链含跟随器，理论引擎没有运放模型，
    # 不能拿它跟纯无源理论比（否则会把跟随器延迟记成"引擎偏差"）。
    dlt = res["V4"]["tset_us"] - th["t_settle_wc_us"]
    xc["t_settle"] = {"lt": _r(res["V4"]["tset_us"], 3),
                      "th": _r(th["t_settle_wc_us"], 3),
                      "delta": _r(dlt, 3),
                      "rel_pct": _r(100 * dlt / th["t_settle_wc_us"], 3),
                      "pass_5pct": bool(abs(dlt) <= 0.05 * th["t_settle_wc_us"])}

    ac_names = ("A_dm", "A_cm", "A_mclk", "dG_16k")
    ac_fail = [k for k in ac_names if not xc[k]["pass_0p5"]]
    xcheck_pass = (not ac_fail and xc["t_settle"]["pass_5pct"]
                   and xc["Vn_nv"]["pass_5pct"] and xc["D7_sigma"]["pass_stat"])

    out = {
        "scheme": SCHEME,
        "grade": cand.get("grade"),
        "n_stages": ns,
        "stages": cand["stages"],
        "dims": dims,
        "xcheck_pass": bool(xcheck_pass),
        "xcheck": xc,
        "xcheck_fail_dims": ac_fail + [k for k, kk in (("t_settle", "pass_5pct"),
                                                          ("Vn_nv", "pass_5pct"),
                                                          ("D7_sigma", "pass_stat"))
                                       if not xc[k][kk]],
        "D5_candidates_us": d5_candidates,
        "theory_zero_source": th_r,
        "theory_engine_1ohm_pred": {k: _r(cand["pred"][k], 4) for k in
                                    ("A_dm", "A_cm", "A_mclk", "dG_16k",
                                     "CMRR_pb_db", "V_n_lsb")},
        "detail": {
            "V1_g_dc_db": _r(res["V1"]["g_dc_db"], 5),
            "V1_g_16k_db": _r(res["V1"]["g_16k_db"], 5),
            "D10_tau_100Hz_us": _r(res["V1"]["tau_at_100Hz_us"], 4),
            "D10_tau_16k_us": _r(res["V1"]["tau_at_16k_us"], 4),
            "D8_worst_f_hz": _r(res["V3"]["D8_worst_f_hz"], 1),
            "D8_cmrr_10Hz_db": _r(res["V3"]["cmrr_10"], 2),
            "D8_cmrr_16k_db": _r(res["V3"]["cmrr_16k"], 2),
            "D5_V4_final_v": _r(res["V4"]["vfinal_v"], 6),
            "D5_V4_strict_band_120uV_us": _r(res["V4"]["tset_engine_band_us"], 2),
            "D5_V4b_600k_ideal_follower_us": _r(res["V4b"]["tset_us"], 2),
            "D5_V6_mc_min_us": _r(res["V6"]["min_us"], 2),
            "D5_V6_mc_mean_us": _r(res["V6"]["mean_us"], 2),
            "D5_V6_mc_max_us": _r(res["V6"]["max_us"], 2),
            "D5_V6_n": res["V6"]["n"],
            "D7_n": res["V5"]["n"],
            "D7_mean_db": _r(res["V5"]["mean_db"], 4),
            "D7_min_db": _r(res["V5"]["min_db"], 4),
            "D7_max_db": _r(res["V5"]["max_db"], 4),
            "D7_p2p_db": _r(res["V5"]["p2p_db"], 4),
            "D6_LSB": _r(res["V7"]["D6_Vn_lsb"], 4),
            "D6_dens_1k_nV": _r(res["V7"]["dens_1k_nv"], 4),
            "D6_f_max_hz": res["V7"]["f_max_hz"],
            "D9_criterion": res["V8"]["ron1"]["criterion"],
            "D9_kick_amp_uv": _r(res["V8"]["ron1"]["kick_amp_uv"], 3),
            "D9_worst_resid_uv": _r(res["V8"]["ron1"]["worst_resid_uv"], 4),
            "D9_worst_rel_to_ss": float(res["V8"]["ron1"]["worst_rel_to_ss"]),
            "D9_ron100": float(res["V8"]["ron100"]["D9"]),
            "D9_ron1000": float(res["V8"]["ron1000"]["D9"]),
            "CH1_CH2_group_delay_diff_nominal_us": _r(res["V1"]["CH_tau_diff_us"], 9),
            "CH1_CH2_group_delay_diff_1pct_mismatch_ns": ch_diff_mismatch_ns,
            "temp_corners": tcorner,
        },
        "V9": {k: (_r(v, 4) if isinstance(v, float) else v)
               for k, v in res["V9"].items() if not k.startswith("raw_")},
        "V9_600k": v9_600k,
        "raw_files": {
            "V1": f"hardware/sim/aaf/r5_{SCHEME}_v1.raw",
            "V2": f"hardware/sim/aaf/r5_{SCHEME}_v2.raw",
            "V3": f"hardware/sim/aaf/r5_{SCHEME}_v3.raw",
            "V4": f"hardware/sim/aaf/r5_{SCHEME}_v4.raw",
            "V4b": f"hardware/sim/aaf/r5_{SCHEME}_v4b.raw",
            "V5": f"hardware/sim/aaf/r5_{SCHEME}_v5mc01..30.raw",
            "V6": f"hardware/sim/aaf/r5_{SCHEME}_v6mc01..30.raw",
            "V7": f"hardware/sim/aaf/r5_{SCHEME}_v7.raw",
            "V8": f"hardware/sim/aaf/r5_{SCHEME}_v8_ron1|100|1000.raw",
            "V9": f"hardware/sim/aaf/r5_{SCHEME}_v9a..v9f.raw",
            "T": [f"hardware/sim/aaf/r5_{SCHEME}_v1t-20C.raw",
                  f"hardware/sim/aaf/r5_{SCHEME}_v1t+85C.raw"],
        },
    }
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
    return out


if __name__ == "__main__":
    r = build()
    print(json.dumps(r["dims"], ensure_ascii=False, indent=2))
    print(f"\nxcheck_pass = {r['xcheck_pass']}  失败项 = {r['xcheck_fail_dims']}")
    print(f"{'项':16s} {'LTspice':>10s} {'理论(0Ω)':>10s} {'Δ':>10s}")
    for k, v in r["xcheck"].items():
        if "lt" not in v:
            print(f"  {k:22s} (参考值 {v.get('value')}，不参与判定)")
            continue
        extra = (f"{v['rel_pct']:+.2f}%" if "rel_pct" in v
                 else f"{v['delta']:+.3f} dB")
        ok = v.get("pass_0p5", v.get("pass_5pct", v.get("pass_stat", True)))
        print(f"  {k:14s} {v['lt']:10.3f} {v['th']:10.3f} {extra:>10s} {'✓' if ok else '✗'}")
    print("\nV9 (真实 OPA388):", json.dumps(r["V9"], ensure_ascii=False))
    print("V9_600k:", json.dumps(r["V9_600k"], ensure_ascii=False))
    print("\n→", OUT)
