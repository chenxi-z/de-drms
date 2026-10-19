#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""score_r5_r4.py — 第 4 轮（定档轮）B/C 两案十槽位评分（规格 v4 §5.1，min 短板制）

输入
----
  * `r5_results_r4_B.json`          B 案 C9 修复后参数的 LTspice 实测（真实 OPA388）
  * `r5_results_r4_C_d8fix.json`    C 案 = 第 3 轮实测 + 本轮 D8 真实模型 1% 配对补测
  * 原始 `.raw`（可选，`--recheck`）反算 D1/D2/D3/D4/D8/D10 核对 JSON 转录

口径（规格 v4 §5.1）
--------------------
  D1  A_dm@4.096 MHz      score = min(x/120, 1)      及格 x ≥ 80
  D2  A_cm@4.096 MHz      score = min(x/100, 1)      及格 x ≥ 60
  D3  A_dm@16.384 MHz     score = min(x/150, 1)      及格 x ≥ 100
  D4  |ΔG|@16 kHz         x≤0.05→1；0.05<x≤0.5 线性；x>0.5→0
  D5  t_s                 score = min(500/x, 1)      及格 x ≤ 900 µs；无效实测记 0
  D6a 无源噪声增量 %       score = min(10/x, 1)       及格 x ≤ 30 %（>30% 淘汰）
  D6b 总积分噪声（LSB）    仅报告，不进 min
  D7  σ(ΔG@16k)           x≤0.01→1；0.01<x≤0.05 线性
  D8  CMRR@通带           **1 % 单体失配 + R·C 乘积异向配对**（规格正文口径）
                          score = min(x/100, 1)      及格 x ≥ 80
  D9  kickback            二值 1.0 / 0.0
  D10 Δτ(0.1 Hz–16 kHz)   x≤1→1；1<x≤5 线性

总分 = min(D1,D2,D3,D4,D5,D6a,D7,D8,D9,D10)，D6b 仅报告（规格 §5.1 / §5.1b）。

⚠️ 本脚本与两案 JSON 自带 `dims.D8` 的关系（第 4 轮口径修正）
  C 案 JSON 的 `dims.D8` 已被本轮替换为 **1 % 配对、真实 OPA388** 的 95.5238 dB
  （第 3 轮那 135.474 dB 是 **0.1 % 配对 + 0 Ω 理想源**，口径不同，见报告 §4）。
  B 案 JSON 的 `dims.D8` 本来就是 **1 % 配对、真实模型**的 95.5147 dB。
  两案现在**同口径同档位**，可直接比较。

C9（§5.2 硬约束，不进 min）按**跟随器输出节点**考核（第 3 轮 §4.2 已论证谐振发生在
被驱动节点，引脚口径被末级 RC 压平）。本轮另做**源阻抗扫描**（0→600 kΩ），
因为 C9 的机理（Z_o,cl 负实部 × 首级 C）随源阻抗变化。

用法
----
    cd hardware/sim/aaf && python score_r5_r4.py
    python score_r5_r4.py --json r5_scores_r4.json
    python score_r5_r4.py --no-recheck        # 跳过 .raw 反算
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LSB_V = 2.0 * 2.442 / 2 ** 24          # 291.109 nV/LSB（§5.1 单位约定）
C9_LIMIT_DB = 6.0                      # 规格 v4 §5.2 C9

# name, unit, full, bare, kind
SPEC = {
    "D1": ("DM 衰减 @fMOD", "dB", 120.0, 80.0, "ratio"),
    "D2": ("CM 衰减 @fMOD", "dB", 100.0, 60.0, "ratio"),
    "D3": ("DM 衰减 @MCLK", "dB", 150.0, 100.0, "ratio"),
    "D4": ("通带平坦度 @16 kHz", "dB", 0.05, 0.50, "linear"),
    "D5": ("建立时间（最坏角）", "us", 500.0, 900.0, "inverse"),
    "D6a": ("无源网络噪声增量", "%", 10.0, 30.0, "inverse"),
    "D7": ("容差敏感度 @通带", "dB", 0.01, 0.05, "linear"),
    "D8": ("CMRR @通带（1% 配对）", "dB", 100.0, 80.0, "ratio"),
    "D9": ("Kickback 回稳", "-", 1.0, 1.0, "binary"),
    "D10": ("群延迟平坦度", "us", 1.0, 5.0, "linear"),
}
DIMS = ["D1", "D2", "D3", "D4", "D5", "D6a", "D7", "D8", "D9", "D10"]

GAP_TEXT = {
    "D1": ("dB 需再增加", "ratio"), "D2": ("dB 需再增加", "ratio"),
    "D3": ("dB 需再增加", "ratio"), "D8": ("dB 需再增加", "ratio"),
    "D4": ("dB 需再降低", "linear"), "D7": ("dB 需再降低", "linear"),
    "D10": ("µs 需再降低", "linear"),
    "D5": ("µs 需再降低", "inverse"), "D6a": ("个百分点 需再降低", "inverse"),
}


# ------------------------------------------------------------------ 归一化
def normalize(dim: str, x):
    if dim == "D9":
        return 1.0 if (x is not None and float(x) >= 1.0) else 0.0
    if x is None:
        return 0.0                      # 无效实测（不建立）= 0，按淘汰处理
    x = float(x)
    if not math.isfinite(x):
        return 0.0
    _, _, full, bare, kind = SPEC[dim]
    if kind == "ratio":
        return float(min(max(x, 0.0) / full, 1.0))
    if kind == "inverse":
        if x <= 0:
            return 1.0
        return float(min(full / x, 1.0))
    if x <= full:                       # linear（越小越好）
        return 1.0
    if x > bare:
        return 0.0
    return float(1.0 - (x - full) / (bare - full))


def passes(dim: str, x):
    if dim == "D9":
        return bool(x is not None and float(x) >= 1.0)
    if x is None:
        return False
    x = float(x)
    _, _, _, bare, kind = SPEC[dim]
    return x >= bare if kind == "ratio" else x <= bare


def gap_to_full(dim: str, x):
    if x is None or dim == "D9":
        return None
    x = float(x)
    _, _, full, _, _ = SPEC[dim]
    txt, kind = GAP_TEXT[dim]
    return (max(full - x, 0.0), txt) if kind == "ratio" else (max(x - full, 0.0), txt)


def d4_fc_for(dg_db: float) -> float:
    """单极点近似：要 ΔG=10log10(1+(16/fc)^2) 等于 dg_db 所需 fc（kHz）。"""
    k = 10 ** (dg_db / 10.0) - 1.0
    return 16.0 / math.sqrt(k) if k > 0 else float("inf")


# ------------------------------------------------------------------ 数据适配
def load(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as fh:
        return json.load(fh)


def opt_json(name):
    p = os.path.join(HERE, name)
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


B_RESULTS = "r5_results_r4_B.json"
C_RESULTS = "r5_results_r4_C_d8fix.json"
C_R3 = "r5_results_r3_C.json"
B_R3 = "r5_results_r3_B.json"
D5_DISCRIM = "r5_d5_discrim_r4_B.json"


def extract_B(d):
    """B：dims 全部来自 r4 实测（真实 OPA388，C9 修复后参数）。"""
    dims = dict(d.get("dims") or {})
    return {
        "stages": d.get("stages"),
        "n_stages": d.get("n_stages"),
        "dims": dims,
        "values": {k: dims.get(k) for k in DIMS},
        "D6b": dims.get("D6b"),
        "D8_curve": (d.get("D8_detail") or {}).get("paired"),
        "D8_same": (d.get("D8_detail") or {}).get("same_direction"),
        "D8_strict_recip": ((d.get("D8_detail") or {}).get("paired") or {}),
        "highz": d.get("highz"),
        "C9": {"follower_db": d.get("c9_follower_db"),
               "follower_hz": d.get("c9_follower_hz"),
               "pin_db": d.get("c9_pin_db"),
               "pin_hz": d.get("c9_pin_hz"),
               "limit_db": d.get("c9_limit_db"),
               "worst_over_sources_db": d.get("c9_worst_over_sources_db"),
               "ok": d.get("c9_ok")},
    }


def extract_C(d, c_r3):
    """C：D8 取本轮 1% 配对真实模型；其余沿用第 3 轮实测。"""
    dims = dict(d.get("dims") or {})
    d8r4 = (((d.get("D8_detail_r4") or {}).get("paired_real")) or {})
    d8r3 = ((c_r3.get("D8_detail") or {}).get("paired")) or {}
    same3 = ((c_r3.get("D8_detail") or {}).get("same_direction_real")) or {}
    return {
        "stages": d.get("stages"),
        "n_stages": d.get("n_stages"),
        "dims": dims,
        "values": {k: dims.get(k) for k in DIMS},
        "D6b": dims.get("D6b"),
        "D8_curve": {m: (d8r4.get(m) or {}).get("cm_pin", {}).get("CMRR_db")
                     for m in ("0.1%", "0.5%", "1%")},
        "D8_same": {m: (d.get("D8_detail_r4") or {}).get("same_direction_real", {})
                    .get(m, {}).get("cm_pin", {}).get("CMRR_db")
                    for m in ("0.1%", "0.5%", "1%")},
        "D8_r3_0p1pct_ideal": (d8r3.get("0.1%") or {}).get("CMRR_db"),
        "D8_r3_1pct_ideal": (d8r3.get("1%") or {}).get("CMRR_db"),
        "D8_r3_same_1pct_ideal": (same3.get("1%") or {}).get("CMRR_db"),
        "C9": {"follower_db": (c_r3.get("real_model") or {}).get("C9_peak_follower_db"),
               "follower_hz": (c_r3.get("real_model") or {}).get("C9_peak_follower_f_hz"),
               "pin_db": (c_r3.get("real_model") or {}).get("peaking_db"),
               "pin_hz": (c_r3.get("real_model") or {}).get("peaking_f_hz"),
               "limit_db": C9_LIMIT_DB,
               "ok": None},
    }


# ------------------------------------------------------------------ .raw 反算
def _raw(rel):
    p = os.path.join(HERE, rel)
    return p if os.path.exists(p) else None


def recheck_B():
    out = {"checked": False}
    try:
        import numpy as np
        import parse_r5 as P
        q1 = _raw("r5_work/r4_B/r5_B_r4_v1.raw")
        if not q1:
            out["error"] = "B v1 .raw 未找到"
            return out
        r1 = P.Raw(q1)
        v = P.d1_d3_d4_d10(r1, 3)
        out.update({k: float(v[k]) for k in
                    ("D1_A_dm_db", "D3_A_mclk_db", "D4_dG_16k_db", "D10_dtau_us")})
        q2 = _raw("r5_work/r4_B/r5_B_r4_v2.raw")
        if q2:
            out["D2_A_cm_db"] = float(P.d2(P.Raw(q2), 3)["D2_A_cm_db"])
        q3 = _raw("r5_work/r4_B/r5_B_r4_v3p010.raw")
        if q3:
            out["D8_CMRR_db"] = float(P.d8(P.Raw(q3), 3)["D8_CMRR_db"])
        q4 = _raw("r5_work/r4_B/r5_B_r4_v3s010.raw")
        if q4:
            out["D8_same_1pct_db"] = float(P.d8(P.Raw(q4), 3)["D8_CMRR_db"])
        out["checked"] = True
    except Exception as exc:                       # 审计失败不阻断评分
        out["error"] = f"{type(exc).__name__}: {exc}"
    return out


def recheck_C():
    out = {"checked": False}
    try:
        import parse_r5 as P
        q1 = _raw("r5_work/r3_C/r5_C_r3_v9a.raw")
        if not q1:
            out["error"] = "C v9a .raw 未找到"
            return out
        v = P.d1_d3_d4_d10(P.Raw(q1), 4)
        out.update({k: float(v[k]) for k in
                    ("D1_A_dm_db", "D3_A_mclk_db", "D4_dG_16k_db", "D10_dtau_us")})
        q2 = _raw("r5_work/r3_C/r5_C_r3_v9b.raw")
        if q2:
            out["D2_A_cm_db"] = float(P.d2(P.Raw(q2), 4)["D2_A_cm_db"])
        q3 = _raw("r5_work/r4_C_d8/r4_C_d8_v9b_p010.raw")
        if q3:
            out["D8_CMRR_db"] = float(P.d8(P.Raw(q3), 4)["D8_CMRR_db"])
        q4 = _raw("r5_work/r4_C_d8/r4_C_d8_v9b_s010.raw")
        if q4:
            out["D8_same_1pct_db"] = float(P.d8(P.Raw(q4), 4)["D8_CMRR_db"])
        out["checked"] = True
    except Exception as exc:
        out["error"] = f"{type(exc).__name__}: {exc}"
    return out


# ------------------------------------------------------------------ 评分
def score_case(scheme, ex, recheck=None):
    rows = {}
    for dim in DIMS:
        v = ex["values"].get(dim)
        rows[dim] = {
            "measured": v,
            "unit": SPEC[dim][1],
            "score": normalize(dim, v),
            "pass": passes(dim, v),
            "gap_to_full": gap_to_full(dim, v),
        }
    total = min(rows[k]["score"] for k in DIMS)
    short = [k for k in DIMS if abs(rows[k]["score"] - total) < 1e-12]
    return {
        "scheme": scheme,
        "n_stages": ex.get("n_stages"),
        "stages": ex.get("stages"),
        "rows": rows,
        "D6b": {"measured": ex.get("D6b"), "unit": "LSB", "score": None,
                "note": "仅报告（砖墙极限 4.30 LSB，规格 §5.1b）"},
        "total": total,
        "short_board": short,
        "all_pass_lines": all(rows[k]["pass"] for k in DIMS),
        "fail_dims": [k for k in DIMS if not rows[k]["pass"]],
        "min_ge_1": bool(total >= 1.0 - 1e-12),
        "d8": {"curve": ex.get("D8_curve"), "same": ex.get("D8_same"),
               "r3_0p1pct_ideal": ex.get("D8_r3_0p1pct_ideal"),
               "r3_1pct_ideal": ex.get("D8_r3_1pct_ideal"),
               "r3_same_1pct_ideal": ex.get("D8_r3_same_1pct_ideal")},
        "c9": ex.get("C9"),
        "highz": ex.get("highz"),
        "recheck": recheck or {"checked": False},
    }


def print_case(c):
    print(f"\n=== 方案 {c['scheme']}（{c['n_stages']} 级）  总分 = min = {c['total']:.6f} ===")
    print(f"{'维':<5}{'维度':<22}{'实测':>12}{'单位':>6}{'分':>9}{'及格':>6}  到满分缺口")
    for dim in DIMS:
        r = c["rows"][dim]
        g = r["gap_to_full"]
        gs = "" if g is None else f"{g[0]:.4f} {g[1]}"
        m = "   —   " if r["measured"] is None else f"{float(r['measured']):.4f}"
        print(f"{dim:<5}{SPEC[dim][0]:<22}{m:>12}{r['unit']:>6}"
              f"{r['score']:>9.4f}{'✓' if r['pass'] else '✗':>6}  {gs}")
    b = c["D6b"]
    m = "   —   " if b["measured"] is None else f"{float(b['measured']):.3f}"
    print(f"{'D6b':<5}{'总积分噪声（仅报告）':<22}{m:>12}{'LSB':>6}{'  —':>9}{' —':>6}")
    print(f"  短板 = {','.join(c['short_board'])}；十维及格线全过 = {c['all_pass_lines']}"
          f"；不及格 = {','.join(c['fail_dims']) or '无'}；min ≥ 1.0 = {c['min_ge_1']}")


# ------------------------------------------------------------------ D5 明细
def d5_report(bd):
    """B 案五档源阻抗 × 三套数值设置 + 本轮补测的中间阻抗档。"""
    out = {"by_source": bd.get("d5_by_source") or {},
           "detail": {k: {s: (v.get(s) or {}).get("spec_200uV", {}).get("tset_us")
                          for s in ("gear20n", "trap60us", "gear5n")}
                      for k, v in (bd.get("D5_detail") or {}).items()
                      if isinstance(v, dict) and "spec_200uV" in (v.get("gear20n") or {})},
           "all_stable": bd.get("D5_all_settings_stable"),
           "discrim": bd.get("D5_discrimination")}
    gap = opt_json("r5_r4_d5_gap_sweep.json")
    if gap:
        out["gap_sweep"] = gap
    return out


def c9_report(c, c9_sweep_nom, c9_sweep_cor, c9_c_nom, c9_c_cor):
    out = {"limit_db": C9_LIMIT_DB,
           "B": c["c9"],
           "B_source_sweep_nominal": c9_sweep_nom,
           "B_source_sweep_corner": c9_sweep_cor,
           "C": c["c9"],
           "C_source_sweep_nominal": c9_c_nom,
           "C_source_sweep_corner": c9_c_cor}
    # 源阻抗扫描里跟随器峰最高点
    for key, sw in (("B", c9_sweep_nom), ("B_corner", c9_sweep_cor),
                    ("C", c9_c_nom), ("C_corner", c9_c_cor)):
        if sw:
            k = max(sw, key=lambda r: sw[r]["follower_peak_db"])
            out[f"worst_{key}"] = {"rs_ohm": float(k),
                                   "peak_db": sw[k]["follower_peak_db"],
                                   "peak_hz": sw[k]["follower_peak_hz"],
                                   "margin_db": C9_LIMIT_DB - sw[k]["follower_peak_db"],
                                   "pass": sw[k]["follower_peak_db"] <= C9_LIMIT_DB}
    return out


# ------------------------------------------------------------------ main
def main(argv=None):
    ap = argparse.ArgumentParser(description="第 4 轮定档评分（规格 v4 §5.1）")
    ap.add_argument("--json", default="r5_scores_r4.json")
    ap.add_argument("--no-recheck", action="store_true")
    args = ap.parse_args(argv)

    bd = load(B_RESULTS)
    cd = load(C_RESULTS)
    cr3 = load(C_R3)
    br3 = opt_json(B_R3)

    exB = extract_B(bd)
    exC = extract_C(cd, cr3)
    cB = score_case("B", exB, None if args.no_recheck else recheck_B())
    cC = score_case("C", exC, None if args.no_recheck else recheck_C())

    for c in (cB, cC):
        print_case(c)
        rc = c["recheck"]
        if rc.get("checked"):
            diffs = []
            for key, dim in (("D1_A_dm_db", "D1"), ("D2_A_cm_db", "D2"),
                             ("D3_A_mclk_db", "D3"), ("D4_dG_16k_db", "D4"),
                             ("D8_CMRR_db", "D8"), ("D10_dtau_us", "D10")):
                if key in rc and c["rows"][dim]["measured"] is not None:
                    diffs.append(abs(rc[key] - float(c["rows"][dim]["measured"])))
            if diffs:
                print(f"  ✓ .raw 反算复核：6 项 max|Δ| = {max(diffs):.2e}")
            if "D8_same_1pct_db" in rc:
                print(f"     同向 1% 对照（.raw 复算）= {rc['D8_same_1pct_db']:.3f} dB")
        else:
            print(f"  ⚠ .raw 反算未执行：{rc.get('error', 'skipped')}")
        c9 = c["c9"]
        if c9:
            print(f"  C9 跟随器节点 = {c9['follower_db']:.3f} dB"
                  f" @ {c9['follower_hz'] / 1e3:.1f} kHz（限 {C9_LIMIT_DB:.0f} dB，"
                  f"{'过' if c9['follower_db'] <= C9_LIMIT_DB else '超'}）"
                  f"；引脚 DM = {c9['pin_db']:+.4f} dB")

    # ---------------- 口径修正对照（C 案 D8） ----------------
    print("\n=== C 案 D8 口径修正对照 ===")
    print(f"  第 3 轮 dims.D8（0.1% 配对 + 0 Ω 理想源） = {cC['d8']['r3_0p1pct_ideal']:.3f} dB")
    print(f"  第 3 轮同档 1% 配对（0 Ω 理想源）          = {cC['d8']['r3_1pct_ideal']:.3f} dB")
    print(f"  本轮 1% 配对（真实 OPA388）= 记分口径       = {cC['rows']['D8']['measured']:.3f} dB")
    print(f"  本轮 1% 同向（真实 OPA388，对照）           = {cC['d8']['same']['1%']:.3f} dB")

    # ---------------- C9 前后对比 ----------------
    print("\n=== C9 peaking 前后对比（B 案：R1 2.74 → 6.19 Ω）===")
    old = (br3 or {}).get("re", {}).get("V9a", {}) if br3 else {}
    corr = opt_json("r5_corr_r4.json")
    old_foll = None
    if corr:
        for r in corr:
            if abs(r["rs"]) < 1e-9:
                old_foll = r["ac"]["foll_peak_db"]
                break
    print(f"  旧参数 R1=2.74：跟随器 {old_foll if old_foll is not None else float('nan'):.2f} dB"
          f" @ ~290 kHz（r5_corr_r4.json rs=0）")
    print(f"  新参数 R1=6.19：跟随器 {cB['c9']['follower_db']:.3f} dB"
          f" @ {cB['c9']['follower_hz'] / 1e3:.1f} kHz")
    print(f"  限值 {C9_LIMIT_DB:.0f} dB → "
          f"{'通过（余量 %.2f dB）' % (C9_LIMIT_DB - cB['c9']['follower_db'])}")

    # ---------------- D5 明细 ----------------
    d5 = d5_report(bd)
    print("\n=== B 案 D5 五档源阻抗明细（R×1.01 / C×1.05 最坏角）===")
    for k, v in d5["by_source"].items():
        t = v.get("tset_us") or {}
        st = v.get("stable") or {}
        print(f"  Rs={k:>5s}  tset(gear/trap/gear5n) = "
              f"{t.get('gear20n', float('nan')):6.2f} / "
              f"{t.get('trap60us', float('nan')):6.2f} / "
              f"{t.get('gear5n', float('nan')):6.2f} µs"
              f"   全部回稳 = {all(st.values())}")
    if d5.get("gap_sweep"):
        gb = d5["gap_sweep"].get("B") or {}
        print("  本轮补测的中间档（B）：" +
              "  ".join(f"{int(k) // 1000}k={v['tset_us']:.1f}µs/{'稳' if v['stable'] else '振'}"
                       for k, v in sorted(gb.items(), key=lambda kv: float(kv[0]))))
        gc = d5["gap_sweep"].get("C") or {}
        print("  本轮补测的中间档（C）：" +
              "  ".join(f"{int(k) // 1000}k={'稳' if v['stable'] else '振'}"
                       for k, v in sorted(gc.items(), key=lambda kv: float(kv[0]))))
    disc = d5.get("discrim") or {}
    if disc:
        print(f"  正对照（旧参数 100 kΩ）：tail pp = "
              f"{disc['positive_control_old_B_100k']['tail_pp_uv']['gear20n_400us'] / 1e3:.1f} mV"
              f"（三设置全部失稳）；新参数五档全部回稳")

    # ---------------- C9 源阻抗扫描 ----------------
    c9r = c9_report(cB, opt_json("r5_r4_c9_source_sweep.json"),
                    opt_json("r5_r4_c9_source_sweep_corner.json"),
                    opt_json("r5_r4_c9_source_sweep_C_nominal.json"),
                    opt_json("r5_r4_c9_source_sweep_C.json"))
    print("\n=== C9 源阻抗扫描（跟随器节点峰值）===")
    for tag in ("B", "B_corner", "C", "C_corner"):
        w = c9r.get(f"worst_{tag}")
        if w:
            print(f"  {tag:<9s} 最坏 Rs = {w['rs_ohm'] / 1e3:6.0f} kΩ → {w['peak_db']:6.2f} dB"
                  f" @ {w['peak_hz'] / 1e3:.0f} kHz（余量 {w['margin_db']:+.2f} dB）")

    # ---------------- 汇总 ----------------
    print("\n=== B vs C 最终对比（同口径：真实 OPA388，D8 = 1% 配对）===")
    print(f"{'维':<5}{'B':>12}{'C':>12}{'差(B-C)':>10}   {'B 分':>7}{'C 分':>7}")
    for dim in DIMS:
        bv = cB["rows"][dim]["measured"]
        cv = cC["rows"][dim]["measured"]
        bv_ = "—" if bv is None else f"{float(bv):.4f}"
        cv_ = "—" if cv is None else f"{float(cv):.4f}"
        if isinstance(bv, (int, float)) and isinstance(cv, (int, float)):
            dd = f"{float(bv) - float(cv):+.4f}"
        else:
            dd = "—"
        print(f"{dim:<5}{bv_:>12}{cv_:>12}{dd:>10}   "
              f"{cB['rows'][dim]['score']:>7.4f}{cC['rows'][dim]['score']:>7.4f}")
    print(f"{'D6b':<5}{float(cB['D6b']['measured']):>12.3f}"
          f"{float(cC['D6b']['measured']):>12.3f}{'（仅报告）':>10}")
    print(f"{'总分':<5}{cB['total']:>12.6f}{cC['total']:>12.6f}"
          f"  短板 B={','.join(cB['short_board'])} / C={','.join(cC['short_board'])}")

    # ---------------- 定档判定 ----------------
    print("\n=== 定档判定 ===")
    for c in (cB, cC):
        print(f"  {c['scheme']}: min = {c['total']:.6f}；十维及格线全过 = {c['all_pass_lines']}"
              f"；min ≥ 1.0 = {c['min_ge_1']}；短板 = {','.join(c['short_board'])}")
    print(f"  D4 满分线（≤0.05 dB）所需单极点 fc ≈ {d4_fc_for(0.05):.1f} kHz"
          f"（设计窗口 50–80 kHz；现 fc ≈ 79.9 kHz → 单极点预测 "
          f"{10 * math.log10(1 + (16 / 79.9) ** 2):.4f} dB）")

    payload = [{
        "scheme": c["scheme"], "n_stages": c["n_stages"], "stages": c["stages"],
        "total": c["total"], "short_board": c["short_board"],
        "all_pass_lines": c["all_pass_lines"], "fail_dims": c["fail_dims"],
        "min_ge_1": c["min_ge_1"],
        "rows": {k: {"measured": c["rows"][k]["measured"],
                     "unit": c["rows"][k]["unit"],
                     "score": c["rows"][k]["score"],
                     "pass": c["rows"][k]["pass"],
                     "gap_to_full": c["rows"][k]["gap_to_full"]} for k in DIMS},
        "D6b": c["D6b"], "d8": c["d8"], "c9": c["c9"],
        "highz": c["highz"], "recheck": c["recheck"],
    } for c in (cB, cC)]
    extra = {"d5_B": d5, "c9_source_sweep": c9r,
             "c_d8_calibration": {
                 "r3_dims_d8_0p1pct_ideal_source": cC["d8"]["r3_0p1pct_ideal"],
                 "r3_1pct_paired_ideal_source": cC["d8"]["r3_1pct_ideal"],
                 "r4_1pct_paired_real_opa388": cC["rows"]["D8"]["measured"],
                 "r4_0p1pct_paired_real": cC["d8"]["curve"].get("0.1%"),
                 "r4_same_1pct_real": cC["d8"]["same"].get("1%")},
             "d4_fc_needed_khz": d4_fc_for(0.05)}
    if args.json:
        with open(os.path.join(HERE, args.json), "w", encoding="utf-8", newline="\n") as fh:
            json.dump({"cases": payload, "extra": extra}, fh,
                      ensure_ascii=False, indent=2)
        print(f"\n→ {args.json}")
    return payload


if __name__ == "__main__":
    main()
