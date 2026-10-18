# -*- coding: utf-8 -*-
"""r5_evidence_r2.py — 生成 r5_candidates_r2.json 的 D6/D8 定量证据块并合并 LTspice 验证。

用法：cd hardware/sim/aaf && python r5_evidence_r2.py
（依赖 r5_candidates_r2.json、r5_r2_ltspice.json）
"""
from __future__ import annotations

import json
import math
import os

import numpy as np

import opt_round5 as o5

HERE = os.path.dirname(os.path.abspath(__file__))
LSB = o5.LSB_V
EN = o5.EN_FOLL_DIFF


def mc_cmrr(stages, tol, n=600, seed=20261018):
    """逐元件独立失配的 CMRR 蒙特卡洛（最差频点）。"""
    rng = np.random.default_rng(seed)
    f = np.logspace(1, math.log10(16e3), 30)
    vals = []
    for _ in range(n):
        b = [(r * (1 + rng.uniform(-tol, tol)),
              c * (1 + rng.uniform(-tol, tol)),
              d * (1 + rng.uniform(-tol, tol))) for r, c, d in stages]
        cm, dm = o5._two_line_cm_dm(stages, b, f)
        vals.append(float(np.min(20 * np.log10(np.abs(cm) / np.maximum(np.abs(dm), 1e-300)))))
    v = np.array(vals)
    return {"median_db": float(np.median(v)), "p95_worst_db": float(np.quantile(v, 0.05)),
            "p99_worst_db": float(np.quantile(v, 0.01)), "tol": tol, "n": n}


def rc_matched_cmrr(stages, eps=0.01):
    """两线按 R·C 乘积配对（R×(1+eps) 配 C/(1+eps)）时的 CMRR。"""
    f = np.logspace(1, math.log10(16e3), 50)
    b = [(r * (1 + eps), c / (1 + eps), d / (1 + eps)) for r, c, d in stages]
    cm, dm = o5._two_line_cm_dm(stages, b, f)
    return float(np.min(20 * np.log10(np.abs(cm) / np.maximum(np.abs(dm), 1e-300))))


def d6_block():
    lo2 = (10 ** (-0.5 / 20)) ** 2
    enbw_pass = (LSB * 1.0 / EN) ** 2
    enbw_d4 = 16000 * lo2
    return {
        "en_diff_nv_rtHz": EN * 1e9,
        "en_source": "TI OPAx388 SBOS777D 模型实测（互谱 V(fpa,fna)，白噪至 2 MHz）",
        "enbw_max_for_pass_hz": enbw_pass,
        "enbw_min_forced_by_D4_hz": enbw_d4,
        "incompatibility_ratio": enbw_d4 / enbw_pass,
        "brick_wall_16k_lsb": EN * math.sqrt(16e3) / LSB,
        "required_en_for_pass_nv": LSB * 1e9 / math.sqrt(enbw_d4),
        "derivation": [
            "无源 RC 阶梯 |H(f)/H(0)| <= 1 对所有 f 成立（无增益）",
            "D4 及格（16 kHz 处 >= -0.5 dB）=> ENBW >= 16000 x 0.8913 = %.0f Hz" % enbw_d4,
            "D6 及格（<= 1 LSB）=> ENBW <= (291/9.905)^2 = %.0f Hz" % enbw_pass,
            "两者相差 %.1f 倍 => 在本器件下不可同时满足" % (enbw_d4 / enbw_pass),
            "极端情形：16 kHz 理想砖墙的 Vn = %.2f LSB，仍超线 %.1f 倍"
            % (EN * math.sqrt(16e3) / LSB, EN * math.sqrt(16e3) / LSB),
        ],
        "verdict": "D6 与 D4 物理冲突（非拓扑/参数可解），需用户裁决",
    }


def main():
    path = os.path.join(HERE, "r5_candidates_r2.json")
    with open(path, encoding="utf-8") as fh:
        cands = json.load(fh)

    lt_path = os.path.join(HERE, "r5_r2_ltspice.json")
    lt = {}
    if os.path.exists(lt_path):
        with open(lt_path, encoding="utf-8") as fh:
            lt = json.load(fh)

    d8 = {
        "spec_v3_corner": "两线整线 R/C x1.01（1% 失配）",
        "cmrr_at_1pct_db": {},
        "mismatch_required_for_80db_pct": {},
        "mc_per_element": {},
        "rc_product_matching": {},
        "verdict": "D8 及格需两线匹配 <=0.025-0.034%（规格 V3 的 1% 差 30-40x）；"
                   "逐元件 0.05% 时 P95 才勉强 >=80 dB",
    }

    for g in ("A", "B", "C"):
        st = [tuple(s) for s in cands[g]["stages"]]
        p = o5.predict(st)
        d = o5.dim_scores(p)
        pf = o5.pass_flags(d, p)
        cands[g].update({"pred": p, "dims": d, "pass": pf,
                         "hard": o5.hard_checks(p),
                         "design_score": o5.design_score(d),
                         "min_score": min(d.values())})
        cands[g].setdefault("snap", {})
        cands[g]["snap"]["failing_dims"] = [k for k, v in pf.items() if not v]
        cands[g]["snap"]["npass"] = sum(pf.values())
        cands[g]["snap"]["hard_ok"] = all(o5.hard_checks(p).values())
        if g in lt:
            cands[g]["ltspice"] = {
                "model": "TI OPAx388 SBOS777D Rev D，V9a/V9b/V9d，与引擎同拓扑",
                "r_work_dir": "r5_work/r2",
                **{k: float(v) for k, v in lt[g].items() if isinstance(v, (int, float))},
            }

        d8["cmrr_at_1pct_db"][g] = o5.cmrr_two_line(st, 0.01)
        d8["mismatch_required_for_80db_pct"][g] = o5.cmrr_required_mismatch(st, 80.0) * 100
        d8["mc_per_element"][g] = {
            "1pct": mc_cmrr(st, 0.01),
            "0.1pct": mc_cmrr(st, 1e-3),
            "0.05pct": mc_cmrr(st, 5e-4),
            "0.02pct": mc_cmrr(st, 2e-4),
        }
        d8["rc_product_matching"][g] = {
            "same_direction_1pct_db": o5.cmrr_two_line(st, 0.01),
            "rc_product_matched_1pct_db": rc_matched_cmrr(st, 0.01),
        }

    out = {g: cands[g] for g in ("A", "B", "C")}
    out["_evidence"] = {
        "D6": d6_block(),
        "D8": d8,
        "engine_model": {
            "source_model": "opa388：Zout_cl(f) 复数查表 + G(f)=A_OL/(1+A_OL)",
            "zout_table": "r5_zout_opa388_ti.json（700 点，10 Hz–100 MHz，TI 模型 1 mA 注入实测）",
            "note": "手册 M7 的 34 Ω 只给模、忽略相位；实测表保留 100–280 kHz 的负实部（有源谐振）",
        },
        "D5_model": {
            "pre_rc": "600 kΩ ∥ 8.5 pF（跟随器输入侧，理想缓冲隔离）",
            "note": "V9c/V9f 的 LTspice 实跑本轮未取到可信值（求解器未收敛），"
                    "D5 以理论值报告（53 us，远优于 500 us 满分线）",
        },
        "xcheck": {
            "ac_engine_vs_ltspice_max_abs_diff_db": {
                g: max(abs(out[g]["pred"]["A_dm"] - out[g]["ltspice"]["D1_lt"]),
                       abs(out[g]["pred"]["A_cm"] - out[g]["ltspice"].get("D2_lt", 0)),
                       abs(out[g]["pred"]["dG_16k"] - out[g]["ltspice"].get("D4_lt", 0)))
                for g in ("A", "B", "C") if "ltspice" in out[g]
            },
            "noise_engine_vs_ltspice": {
                g: {"engine_lsb": out[g]["pred"]["V_n_lsb"],
                    "ltspice_lsb": out[g]["ltspice"].get("D6_lsb"),
                    "rel_diff_pct": 100 * (out[g]["pred"]["V_n_lsb"]
                                           / out[g]["ltspice"]["D6_lsb"] - 1)}
                for g in ("A", "B", "C") if "ltspice" in out[g]
            },
        },
    }

    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2, default=float)

    print("=== 三案冻结汇总 ===")
    for g in ("A", "B", "C"):
        v = out[g]
        p = v["pred"]
        print("%s: %s" % (g, v["stages"]))
        print("   fc=%.1fk D1=%.1f D2=%.1f D3=%.1f dG=%.3f D5=%.0fus D6=%.2f pk=%.1f CMRR=%.1f"
              % (p["f_c_hz"] / 1e3, p["A_dm"], p["A_cm"], p["A_mclk"], p["dG_16k"],
                 o5.d5_worst_us(p), p["V_n_lsb"], p["peaking_db"], p["CMRR_pb_db"]))
        print("   未及格=%s min=%.4f" % (v["snap"]["failing_dims"], v["min_score"]))
    print("\nD6:", out["_evidence"]["D6"]["verdict"])
    print("D8:", out["_evidence"]["D8"]["verdict"])
    print("\n写入", path)


if __name__ == "__main__":
    main()
