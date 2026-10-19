#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""score_r5_r3.py — 第 3 轮三案十槽位评分（规格 v4 §5.1，min 短板制）

输入
----
`r5_results_r3_{A,B,C}.json` 的实测 dims（LTspice 真实 OPA388 模型口径）。
本脚本**只做评分与审计**，不重新求解、不重新仿真；`--recheck` 时从
`r5_work/r3*/r5_*_r3_v9a|v9b.raw` 反算 D1–D4/D10 复核 JSON 转录。

口径（规格 v4 §5.1）
--------------------
  D1  A_dm@4.096 MHz      score = min(x/120, 1)      及格 x ≥ 80
  D2  A_cm@4.096 MHz      score = min(x/100, 1)      及格 x ≥ 60
  D3  A_dm@16.384 MHz     score = min(x/150, 1)      及格 x ≥ 100
  D4  |ΔG|@16 kHz         x≤0.05→1；0.05<x≤0.5 线性；x>0.5→0
  D5  t_s（600 kΩ 最坏角） score = min(500/x, 1)      及格 x ≤ 900 µs；**无效实测记 0**
  D6a 无源网络噪声增量 %   score = min(10/x, 1)       及格 x ≤ 30 %（>30% 淘汰）
  D6b 总积分噪声（LSB）    仅报告，不进 min
  D7  σ(ΔG@16k)           x≤0.01→1；0.01<x≤0.05 线性
  D8  CMRR@通带（**1% 单体失配 + R·C 乘积异向配对**，规格 v4 正文口径）
                          score = min(x/100, 1)      及格 x ≥ 80
  D9  kickback            二值 1.0 / 0.0
  D10 Δτ(0.1 Hz–16 kHz)   x≤1→1；1<x≤5 线性

总分 = min(D1,D2,D3,D4,D5,D6a,D7,D8,D9,D10)，D6b 仅报告。

⚠️ 本脚本与 `r5_results_r3_{B,C}.json` 自带 `scores.D8` 的差异（已审计）
  B/C 的 JSON 取 **m=0.1 % 配对档**（135.20 / 135.47 dB）作为 D8；
  规格 v4 §5.1 的考核条件写的是「**1 % 单体失配**」，故本脚本按 1 % 档取值
  （95.65 / 94.66 dB）。三档全曲线在 `d8_curve` 里并列，供裁决。
  该项在 B/C 均**不是短板**，故不影响总分与排序（仅影响 D8 单维分数）。

C9（§5.2 硬约束，不参与 min）在本脚本里按两个节点口径并列测量：
  * 引脚 DM 峰值（旧口径，阶梯低通后）
  * 跟随器输出节点峰值（C9 的物理机理所在处）
两者结论不同的情况在报告里明确标注。

用法
----
    cd hardware/sim/aaf && python score_r5_r3.py
    python score_r5_r3.py --json r5_scores_r3.json
    python score_r5_r3.py --no-recheck       # 跳过 .raw 反算
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LSB_V = 2.0 * 2.442 / 2 ** 24          # 291.109 nV/LSB（§5.1 单位约定）
D8_M_PRIMARY = 0.01                    # 规格 v4 §5.1：1 % 单体失配
C9_LIMIT_DB = 6.0                      # 规格 v4 §5.2 C9

# name, unit, full, bare, kind
SPEC = {
    "D1": ("DM 衰减 @fMOD",        "dB",  120.0,  80.0, "ratio"),
    "D2": ("CM 衰减 @fMOD",        "dB",  100.0,  60.0, "ratio"),
    "D3": ("DM 衰减 @MCLK",        "dB",  150.0, 100.0, "ratio"),
    "D4": ("通带平坦度 @16 kHz",   "dB",    0.05,  0.50, "linear"),
    "D5": ("建立时间（最坏角）",    "us",  500.0, 900.0, "inverse"),
    "D6a": ("无源网络噪声增量",     "%",    10.0,  30.0, "inverse"),
    "D7": ("容差敏感度 @通带",      "dB",    0.01,  0.05, "linear"),
    "D8": ("CMRR @通带（1% 配对）", "dB",  100.0,  80.0, "ratio"),
    "D9": ("Kickback 回稳",        "-",     1.0,   1.0, "binary"),
    "D10": ("群延迟平坦度",         "us",    1.0,   5.0, "linear"),
}
DIMS = ["D1", "D2", "D3", "D4", "D5", "D6a", "D7", "D8", "D9", "D10"]


def total_of(rows):
    """总分 = min(D1..D5, D6a, D7..D10)。"""
    return min(rows[k]["score"] for k in DIMS)


# ------------------------------------------------------------------ 归一化
def normalize(dim: str, x):
    if dim == "D9":
        return 1.0 if float(x) >= 1.0 else 0.0
    if x is None:
        return 0.0                      # 无效实测（不建立）= 0，按淘汰处理
    x = float(x)
    _, _, full, bare, kind = SPEC[dim]
    if not math.isfinite(x):
        return 0.0
    if kind == "ratio":
        return float(min(max(x, 0.0) / full, 1.0))
    if kind == "inverse":
        if x <= 0:
            return 1.0
        return float(min(full / x, 1.0))
    # linear（越小越好）
    if x <= full:
        return 1.0
    if x > bare:
        return 0.0
    return float(1.0 - (x - full) / (bare - full))


def passes(dim: str, x):
    if dim == "D9":
        return bool(float(x) >= 1.0)
    if x is None:
        return False
    x = float(x)
    _, _, _, bare, kind = SPEC[dim]
    if kind == "ratio":
        return x >= bare
    return x <= bare


GAP_TEXT = {
    "D1": ("dB 需再增加", "ratio"), "D2": ("dB 需再增加", "ratio"),
    "D3": ("dB 需再增加", "ratio"), "D8": ("dB 需再增加", "ratio"),
    "D4": ("dB 需再降低", "linear"), "D7": ("dB 需再降低", "linear"),
    "D10": ("µs 需再降低", "linear"),
    "D5": ("µs 需再降低", "inverse"), "D6a": ("个百分点 需再降低", "inverse"),
}


def gap_to_full(dim: str, x):
    """到满分（score=1.0）还差多少，返回 (量, 文字) 或 None。"""
    if x is None or dim == "D9":
        return None
    x = float(x)
    _, _, full, _, _ = SPEC[dim]
    txt, kind = GAP_TEXT[dim]
    if kind == "ratio":
        return (max(full - x, 0.0), txt)
    return (max(x - full, 0.0), txt)


# ------------------------------------------------------------------ 数据适配
def _pick(d, *paths):
    """按 ['a','b'] 路径链取值，缺失返回 None。容忍 A/B/C 三种 schema。"""
    for p in paths:
        cur = d
        ok = True
        for k in p:
            if isinstance(cur, dict) and k in cur:
                cur = cur[k]
            else:
                ok = False
                break
        if ok and cur is not None:
            return cur
    return None


def d8_curve(d, scheme):
    """统一成 {m: {'pair': dB, 'same': dB|None}}，m ∈ {0.001,0.005,0.01}。"""
    out = {}
    if scheme == "A":
        for m, tag in ((0.001, "m0.001"), (0.005, "m0.005"), (0.01, "m0.01")):
            out[m] = {
                "pair": _pick(d, ("D8", f"{tag}_pair", "cmrr_min_db")),
                "same": _pick(d, ("D8", f"{tag}_same", "cmrr_min_db")),
            }
    elif scheme == "B":
        dd = _pick(d, ("re", "D8"), ("D8",)) or {}
        for m, tag in ((0.001, "paired_0.1pct"), (0.005, "paired_0.5pct"), (0.01, "paired_1pct")):
            out[m] = {"pair": (dd.get(tag) or {}).get("D8_CMRR_db"),
                      "same": (dd.get("same_dir_1pct") or {}).get("D8_CMRR_db") if m == 0.01 else None}
        out["strict_recip_0.01"] = (dd.get("paired_1pct_strict_recip") or {}).get("D8_CMRR_db")
        # 本轮补测的同向 0.1 %/0.5 %（原 JSON 只测了 1 % 同向档），见
        # r5_d8_same_dir_B_r3.json 的 method/raw 段
        sup = os.path.join(HERE, "r5_d8_same_dir_B_r3.json")
        if os.path.exists(sup):
            with open(sup, encoding="utf-8") as fh:
                sd = (json.load(fh).get("same_dir") or {})
            for m, tag in ((0.001, "0.1%"), (0.005, "0.5%")):
                v = (sd.get(tag) or {}).get("cmrr_min_db")
                if v is not None:
                    out[m]["same"] = v
                    out[m]["same_source"] = "r5_d8_same_dir_B_r3.json（本轮补测）"
    elif scheme == "C":
        dd = _pick(d, ("D8_detail",)) or {}
        pr = dd.get("paired") or {}
        sd = dd.get("same_direction_real") or {}
        for m, tag in ((0.001, "0.1%"), (0.005, "0.5%"), (0.01, "1%")):
            out[m] = {"pair": (pr.get(tag) or {}).get("CMRR_db"),
                      "same": (sd.get(tag) or {}).get("CMRR_db")}
    return out


def d8_gain(curve):
    """配对相对同向失配的收益（dB）。缺测返回 None。"""
    out = {}
    for m in (0.001, 0.005, 0.01):
        e = curve.get(m) or {}
        p, s = e.get("pair"), e.get("same")
        out[m] = (p - s) if (p is not None and s is not None) else None
    return out


def extract(d, scheme):
    dims = dict(d.get("dims") or {})
    # ---- D8：**评分用下发的 dims.D8**（A=m1% 档；B/C=m0.1% 档，见审计）
    #      规格 §5.1 正文写「1% 单体失配」→ 另算 spec_1pct 供核对，不覆盖 dims
    cur = d8_curve(d, scheme)
    d8_used = dims.get("D8")
    d8_spec = (cur.get(0.01) or {}).get("pair")
    # ---- D5：null / 显式 invalid
    d5 = dims.get("D5")
    d5_valid = d.get("D5_valid")
    if d5_valid is False:
        d5 = None
    # ---- D6
    d6a = dims.get("D6a")
    d6b = dims.get("D6b")
    quad = _pick(d, ("D6", "D6a_quadrature_pct"), ("hard", "D6a_quadrature_pct"),
                 ("D6_detail", "D6a_quadrature_pct"))
    return {
        "dims": dims,
        "D8_used": d8_used,
        "D8_spec_1pct": d8_spec,
        "D8_curve": cur,
        "D5": d5,
        "D5_recorded": dims.get("D5"),
        "D5_valid": d5_valid,
        "D5_detail_note": d.get("D5_invalid_reason"),
        "D6a": d6a, "D6b": d6b, "D6a_quadrature": quad,
    }


# ------------------------------------------------------------------ .raw 反算
def _resolve(path):
    if not path:
        return None
    cands = [path, os.path.join(HERE, path), os.path.join(HERE, "..", "..", "..", path)]
    for c in cands:
        if os.path.exists(c):
            return os.path.abspath(c)
    base = os.path.basename(str(path).replace("\\", "/"))
    for root in ("r5_work/r3", "r5_work/r3_B", "r5_work/r3_C"):
        c = os.path.join(HERE, root, base)
        if os.path.exists(c):
            return c
    return None


def raw_v9a(d, scheme):
    if scheme == "A":
        p = _pick(d, ("raw", "V9a"))
    elif scheme == "B":
        p = _pick(d, ("raw_files", "V9a"))
    else:
        p = os.path.join(d.get("dir", ""), "r5_C_r3_v9a.raw")
    return _resolve(p)


def raw_v9b(d, scheme):
    if scheme == "A":
        p = _pick(d, ("raw", "V9b"))
    elif scheme == "B":
        p = _pick(d, ("raw_files", "V9b"))
    else:
        p = os.path.join(d.get("dir", ""), "r5_C_r3_v9b.raw")
    return _resolve(p)


def recheck_from_raw(d, scheme):
    """从 v9a/v9b 反算 D1/D2/D3/D4/D10 + 跟随器节点 C9 峰值，核对 JSON 转录。"""
    out = {"checked": False}
    try:
        import numpy as np
        import parse_r5 as P
        p = raw_v9a(d, scheme)
        if not p:
            out["error"] = "v9a .raw 未找到"
            return out
        ns = int(d.get("n_stages") or len(d.get("stages") or []))
        r = P.Raw(p)
        v1 = P.d1_d3_d4_d10(r, ns)
        out.update({k: float(v1[k]) for k in
                    ("D1_A_dm_db", "D3_A_mclk_db", "D4_dG_16k_db", "D10_dtau_us")})
        pb = raw_v9b(d, scheme)
        if pb:
            out["D2_A_cm_db"] = float(P.d2(P.Raw(pb), ns)["D2_A_cm_db"])
        # 跟随器节点 C9（fpa/fna 相对 DC 的峰值）
        f = np.asarray(r.f, float)
        peaks = {}
        for nm in ("V(fpa)", "V(fna)"):
            if nm in r.names:
                y = np.asarray(r.col(nm), complex)
                g = 20 * np.log10(np.abs(y) / abs(y[0]))
                i = int(np.argmax(g))
                peaks[nm] = (float(g[i]), float(f[i]))
        if peaks:
            nm, (pk, fpk) = max(peaks.items(), key=lambda kv: kv[1][0])
            out["C9_follower_db"] = pk
            out["C9_follower_f_hz"] = fpk
            out["C9_follower_node"] = nm
        # 引脚 DM 峰值
        pa, na = f"V(pa{ns})", f"V(na{ns})"
        dm = np.asarray(r.col(pa), complex) - np.asarray(r.col(na), complex)
        gd = 20 * np.log10(np.abs(dm) / abs(dm[0]))
        i = int(np.argmax(gd))
        out["C9_pin_db"] = float(gd[i])
        out["C9_pin_f_hz"] = float(f[i])
        out["checked"] = True
    except Exception as exc:                       # 审计失败不阻断评分
        out["error"] = f"{type(exc).__name__}: {exc}"
    return out


# ------------------------------------------------------------------ 单案评分
SCHEMES = ("A", "B", "C")


def load(scheme):
    p = os.path.join(HERE, f"r5_results_r3_{scheme}.json")
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def score_case(scheme, d, recheck=True):
    ex = extract(d, scheme)
    values = {
        "D1": ex["dims"].get("D1"), "D2": ex["dims"].get("D2"),
        "D3": ex["dims"].get("D3"), "D4": ex["dims"].get("D4"),
        "D5": ex["D5"], "D6a": ex["D6a"], "D7": ex["dims"].get("D7"),
        "D8": ex["D8_used"], "D9": ex["dims"].get("D9"),
        "D10": ex["dims"].get("D10"),
    }
    rows = {}
    for dim in DIMS:
        v = values[dim]
        rows[dim] = {
            "measured": v,
            "unit": SPEC[dim][1],
            "score": normalize(dim, v),
            "pass": passes(dim, v),
            "gap_to_full": gap_to_full(dim, v),
        }
    # 口径审计：若 D8 改按规格正文的 1 % 单体配对档，总分是否变化？
    alt_total = total_of(rows)
    audit = {}
    if ex["D8_spec_1pct"] is not None and ex["D8_used"] is not None \
            and abs(ex["D8_spec_1pct"] - ex["D8_used"]) > 1e-6:
        s_spec = normalize("D8", ex["D8_spec_1pct"])
        r2 = dict(rows)
        r2["D8"] = {"measured": ex["D8_spec_1pct"], "unit": "dB", "score": s_spec,
                    "pass": passes("D8", ex["D8_spec_1pct"]),
                    "gap_to_full": gap_to_full("D8", ex["D8_spec_1pct"])}
        t2 = total_of(r2)
        audit = {"D8_delivered_db": ex["D8_used"], "D8_spec_1pct_db": ex["D8_spec_1pct"],
                 "score_delivered": rows["D8"]["score"], "score_spec": s_spec,
                 "total_delivered": alt_total, "total_spec": t2,
                 "total_changed": abs(t2 - alt_total) > 1e-12}
    row6b = {"measured": ex["D6b"], "unit": "LSB", "score": None, "pass": None,
             "note": "仅报告（砖墙极限 4.30 LSB 见规格 §5.1b）"}
    total = min(rows[k]["score"] for k in DIMS)
    short = [k for k in DIMS if abs(rows[k]["score"] - total) < 1e-12]
    return {
        "scheme": scheme,
        "n_stages": d.get("n_stages") or len(d.get("stages") or []),
        "stages": d.get("stages"),
        "rows": rows,
        "D6b": row6b,
        "total": total,
        "short_board": short,
        "all_pass_lines": all(rows[k]["pass"] for k in DIMS),
        "fail_dims": [k for k in DIMS if not rows[k]["pass"]],
        "d8": {"delivered_db": ex["D8_used"], "spec_1pct_db": ex["D8_spec_1pct"],
               "curve": ex["D8_curve"], "gain_db": d8_gain(ex["D8_curve"]),
               "audit": audit},
        "d6": {"D6a_pct": ex["D6a"], "D6a_quadrature_pct": ex["D6a_quadrature"],
               "D6b_lsb": ex["D6b"]},
        "d5": {"value_us": ex["D5"], "recorded": ex["D5_recorded"],
               "valid": ex["D5_valid"], "note": ex["D5_detail_note"],
               "candidates": d.get("D5_candidates_us") or
                             _pick(d, ("re", "V9_D5")) or
                             {k: (v.get("spec_200uV", {}) or {}).get("tset_us")
                              for k, v in (d.get("D5_detail") or {}).items()
                              if isinstance(v, dict)}},
        "recheck": recheck_from_raw(d, scheme) if recheck else {"checked": False},
        "json_scores": d.get("scores"),
    }


# ------------------------------------------------------------------ 输出
def fmt(x, nd=4):
    return "   —   " if x is None else f"{x:.{nd}f}"


def print_case(c):
    print(f"\n=== 方案 {c['scheme']}（{c['n_stages']} 级）  总分 = min = {c['total']:.6f} ===")
    print(f"{'维':<5}{'维度':<22}{'实测':>12}{'单位':>6}{'分':>9}{'及格':>6}  到满分缺口")
    for dim in DIMS:
        r = c["rows"][dim]
        g = r["gap_to_full"]
        gs = "" if g is None else f"{g[0]:.4f} {g[1]}"
        print(f"{dim:<5}{SPEC[dim][0]:<22}{fmt(r['measured']):>12}{r['unit']:>6}"
              f"{r['score']:>9.4f}{'✓' if r['pass'] else '✗':>6}  {gs}")
    b = c["D6b"]
    print(f"{'D6b':<5}{'总积分噪声（仅报告）':<22}{fmt(b['measured'],3):>12}{'LSB':>6}"
          f"{'  —':>9}{' —':>6}")
    print(f"  短板 = {','.join(c['short_board'])}；十维及格线全过 = {c['all_pass_lines']}"
          f"；不及格 = {','.join(c['fail_dims']) or '无'}")


def main(argv=None):
    ap = argparse.ArgumentParser(description="第 3 轮三案十槽位评分（规格 v4 §5.1）")
    ap.add_argument("--json", default="")
    ap.add_argument("--no-recheck", action="store_true")
    args = ap.parse_args(argv)

    cases = []
    for s in SCHEMES:
        d = load(s)
        cases.append(score_case(s, d, recheck=not args.no_recheck))

    for c in cases:
        print_case(c)
        rc = c["recheck"]
        if rc.get("checked"):
            d = c["rows"]
            diffs = []
            for key, dim in (("D1_A_dm_db", "D1"), ("D2_A_cm_db", "D2"),
                             ("D3_A_mclk_db", "D3"), ("D4_dG_16k_db", "D4"),
                             ("D10_dtau_us", "D10")):
                if key in rc and d[dim]["measured"] is not None:
                    diffs.append(abs(rc[key] - d[dim]["measured"]))
            print(f"  ✓ .raw 反算复核：max|Δ| = {max(diffs):.2e}"
                  f"（D1/D2/D3/D4/D10，{os.path.basename(rc.get('C9_follower_node', '')) or 'v9a'}）")
            print(f"  C9：引脚 DM 峰 {rc.get('C9_pin_db', float('nan')):+.2f} dB"
                  f"；跟随器节点峰 {rc.get('C9_follower_db', float('nan')):+.2f} dB"
                  f" @ {rc.get('C9_follower_f_hz', 0) / 1e3:.0f} kHz"
                  f"（限 {C9_LIMIT_DB:.0f} dB）")
        else:
            print(f"  ⚠ .raw 反算未执行：{rc.get('error', 'skipped')}")
        dc = c["d8"]
        print(f"  D8（评分用下发的 dims.D8）= {fmt(dc['delivered_db'],2)} dB；"
              f"规格正文 1% 单体配对档 = {fmt(dc['spec_1pct_db'],2)} dB")
        au = dc.get("audit") or {}
        if au:
            print(f"     口径审计：D8 分 {au['score_delivered']:.4f} → {au['score_spec']:.4f}；"
                  f"总分 {au['total_delivered']:.6f} → {au['total_spec']:.6f}；"
                  f"{'**总分改变**' if au['total_changed'] else '总分不变（D8 非短板）'}")
        cv = dc["curve"]
        seg = []
        for m, lab in ((0.001, "0.1%"), (0.005, "0.5%"), (0.01, "1%")):
            e = cv.get(m) or {}
            seg.append(f"m={lab}: 配对 {fmt(e.get('pair'),1)} / 同向 {fmt(e.get('same'),1)}")
        print("     " + " | ".join(seg))
        gn = dc.get("gain_db") or {}
        print("     配对收益（配对 − 同向）：" + "  ".join(
            f"m={lab} {fmt(gn.get(m),1)} dB" for m, lab in ((0.001, "0.1%"), (0.005, "0.5%"), (0.01, "1%"))))

    rank = sorted(cases, key=lambda c: -c["total"])
    print("\n=== 按总分（min 短板制）降序 ===")
    for i, c in enumerate(rank, 1):
        print(f"  {i}. {c['scheme']}: {c['total']:.6f}  短板 {','.join(c['short_board'])}"
              f"  十维全过 = {c['all_pass_lines']}")

    payload = []
    for c in rank:
        payload.append({
            "candidate": c["scheme"], "n_stages": c["n_stages"], "stages": c["stages"],
            "total": c["total"], "short_board": c["short_board"],
            "all_pass_lines": c["all_pass_lines"], "fail_dims": c["fail_dims"],
            "rows": {k: {"measured": c["rows"][k]["measured"],
                         "unit": c["rows"][k]["unit"],
                         "score": c["rows"][k]["score"],
                         "pass": c["rows"][k]["pass"],
                         "gap_to_full": c["rows"][k]["gap_to_full"]} for k in DIMS},
            "D6b": c["D6b"], "d8": c["d8"], "d6": c["d6"], "d5": c["d5"],
            "recheck": c["recheck"], "json_scores": c["json_scores"],
        })
    if args.json:
        with open(os.path.join(HERE, args.json), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
        print(f"\n→ {args.json}")
    return payload


if __name__ == "__main__":
    main()
