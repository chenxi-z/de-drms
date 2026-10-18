# -*- coding: utf-8 -*-
"""snap_round5.py — Round 5 三案 E 系列取整 + 邻域枚举 + 参数冻结

计划：docs/design/spec/2026-10-18-aa-driver-plan.md Task 3

流程（沿用 snap_round4.py 的取整 → 邻域枚举 → 理论重评分思路）：
  1. ``opt_round5.solve_candidate(n)`` 取连续最优（n = 2/3/4 → 方案 A/B/C）
  2. 每个 R 落到 E24、每个 C 落到 E12（规格 §5.2 C5/E24 起步、C3 单电容 ≤100 nF）
  3. 在取整结果周围做 ±1 档邻域枚举（R 上/下各一档、C 上/下各一档，组合搜索）
  4. 用同一套 ``opt_round5.predict()`` 重评分，取过线维度最多、min 最高者
  5. 把三案的最终参数写入 ``r5_candidates.json``

输出结构：
  {"A": {"grade": "A", "n_stages": 2, "stages": [[R,C_gnd,C_diff], ...],
         "pred": {...}, "dims": {...}, "pass": {...}, "snap": {...}},
   "B": {...}, "C": {...}}

取整损失 >5% 的维度、以及取整后跌破及格线的维度，都会在控制台标红（ANSI / 文字前缀）
并写进 ``snap.lossy_dims`` / ``snap.failing_dims``。
"""

from __future__ import annotations

import itertools
import json
import math
import os
import sys

import opt_round5 as o5

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_JSON = os.path.join(HERE, "r5_candidates.json")

# ---- E24（1% 电阻）与 E12（电容；C0G 常用档）--------------------------------
E24 = [1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0,
       3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1]
E12 = [1.0, 1.2, 1.5, 1.8, 2.2, 2.7, 3.3, 3.9, 4.7, 5.6, 6.8, 8.2]

# 可购范围（与既有 README/原理图一致的常用档）
R_MIN, R_MAX = 1.0, 5100.0      # Ω，覆盖 1 Ω ~ 5.1 kΩ
C_MIN, C_MAX = 10e-12, 100e-9   # F，覆盖 10 pF ~ 100 nF（C0G）


def _series_table(mant, lo, hi):
    """生成 [lo, hi] 内、尾数为 mant 的档位表（升序、去重）。

    十进制指数由 lo/hi 自动推出，因此同一函数可用于 Ω（1~5.1k）与 F（10p~100n）。
    """
    vals = set()
    d_lo = int(math.floor(math.log10(lo))) - 1
    d_hi = int(math.ceil(math.log10(hi))) + 1
    for d in range(d_lo, d_hi + 1):
        for m in mant:
            v = m * (10.0 ** d)
            if lo * 0.999 <= v <= hi * 1.001:
                vals.add(round(v, 15))
    return sorted(vals)


R_TABLE = _series_table(E24, R_MIN, R_MAX)
C_TABLE = _series_table(E12, C_MIN, C_MAX)


def snap_value(v: float, table: list) -> int:
    """返回 table 中与 v 最接近的下标。"""
    return min(range(len(table)), key=lambda i: abs(table[i] - v))


def fmt_c(c: float) -> str:
    if c <= 0:
        return "0"
    if c >= 1e-9:
        return f"{c*1e9:.4g}nF"
    return f"{c*1e12:.4g}pF"


def fmt_r(r: float) -> str:
    return f"{r:.4g}Ω"


def topo(stages) -> str:
    out = []
    for r, cg, cd in stages:
        s = f"{fmt_r(r)}/{fmt_c(cg)}"
        if cd > 0:
            s += f"+{fmt_c(cd)}"
        out.append(s)
    return " — ".join(out)


# ---------------------------------------------------------------- 邻域枚举

def neighbours(stages, span_r: int = 1, span_c: int = 1):
    """生成 ±span 档的组合邻域（每维独立上下档；C_diff=0 的级不参与 C_diff 枚举）。"""
    r_opts, cg_opts, cd_opts = [], [], []
    for r, cg, cd in stages:
        i = snap_value(r, R_TABLE)
        r_opts.append(R_TABLE[max(0, i - span_r): i + span_r + 1])
        j = snap_value(cg, C_TABLE)
        cg_opts.append(C_TABLE[max(0, j - span_c): j + span_c + 1])
        if cd > 0:
            k = snap_value(cd, C_TABLE)
            cd_opts.append(C_TABLE[max(0, k - span_c): k + span_c + 1])
        else:
            cd_opts.append([0.0])
    n = len(stages)
    for rs in itertools.product(*r_opts):
        for cgs in itertools.product(*cg_opts):
            for cds in itertools.product(*cd_opts):
                yield [(rs[i], cgs[i], cds[i]) for i in range(n)]


def evaluate(stages):
    """用统一口径重评分（与 opt_round5 完全同源）。"""
    mm, pred, dims = o5.score_of(stages)
    return {"min_score": mm, "pred": pred, "dims": dims,
            "pass": o5.pass_flags(dims, pred),
            "hard": o5.hard_checks(pred)}


def _key(ev):
    """候选排序：硬约束全过 > 过线维数 > min > 均分。"""
    hard_ok = all(ev["hard"].values())
    npass = sum(ev["pass"].values())
    mean = float(sum(ev["dims"].values()) / len(ev["dims"]))
    return (hard_ok, npass, ev["min_score"], mean)


DIM_UNIT = {
    "D1": ("A_dm", "dB"), "D2": ("A_cm", "dB"), "D3": ("A_mclk", "dB"),
    "D4": ("dG_16k", "dB"), "D5": ("t_settle_wc_s", "µs"), "D6": ("V_n_lsb", "LSB"),
    "D7": ("sigma_dG_db", "dB"), "D8": ("CMRR_pb_db", "dB"), "D9": ("kickback_ok", ""),
    "D10": ("group_delay_flat_s", "µs"),
}


def dim_raw(dim: str, pred: dict) -> float:
    key, unit = DIM_UNIT[dim]
    v = pred[key]
    if dim == "D5":
        return v * 1e6
    if dim == "D10":
        return v * 1e6
    if dim == "D9":
        return 1.0 if v else 0.0
    return float(v)


RED, YELLOW, RESET = "\033[31m", "\033[33m", "\033[0m"
if not sys.stdout.isatty():          # 重定向到文件时用文字前缀，避免转义码污染日志
    RED, YELLOW, RESET = "[红] ", "[黄] ", ""


def report_diff(grade: str, cont, snapped, snapped_ev) -> dict:
    """打印取整前后逐维对比；标红 >5% 损失与跌破及格线，返回结构化结果。"""
    lossy, failing, lines = [], [], []
    for dim in (f"D{i}" for i in range(1, 11)):
        a = dim_raw(dim, cont["pred"])
        b = dim_raw(dim, snapped_ev["pred"])
        sa, sb = cont["dims"][dim], snapped_ev["dims"][dim]
        if dim == "D9":
            loss = 0.0 if sa >= sb else 1.0
        else:
            loss = 0.0 if a == 0 else abs(b - a) / abs(a)
        if loss > 0.05:
            lossy.append({"dim": dim, "before": a, "after": b, "loss_pct": loss * 100})
        if not snapped_ev["pass"][dim]:
            failing.append({"dim": dim, "value": b, "line": o5.TH[dim][1],
                            "score": sb})
        tag = ""
        if not snapped_ev["pass"][dim] and cont["pass"][dim]:
            tag = RED + "×跌破及格线"
        elif not snapped_ev["pass"][dim]:
            tag = RED + "×未及格"
        elif loss > 0.05:
            tag = YELLOW + "↓损失>5%"
        unit = DIM_UNIT[dim][1]
        lines.append(f"    {dim:>4} {a:>10.4g} → {b:>10.4g} {unit:<4} "
                     f"分数 {sa:.3f} → {sb:.3f} {tag}{RESET}")
    print(f"\n  【{grade} 案】取整前后理论评分对比（{cont['pred']['n_parts']} 件/线）")
    print("\n".join(lines))
    return {"lossy_dims": lossy, "failing_dims": failing}


def solve_and_snap(n_stages: int, grade: str, seed: int = 0,
                   maxiter: int = 220, n_starts: int = 3) -> dict:
    print(f"\n{'='*78}\n方案 {grade}（{n_stages} 级）\n{'='*78}")
    cont = o5.solve_candidate(n_stages, seed=seed, maxiter=maxiter, n_starts=n_starts)
    print(f"  连续最优：{topo(cont['stages'])}")
    print(f"    fc={cont['pred']['f_c_hz']/1e3:.2f} kHz  ΣR={cont['pred']['r_sum_ohm']:.2f} Ω  "
          f"min={cont['meta']['min_score']:.3f}")
    cont_ev = evaluate(cont["stages"])

    # 1) 直接取整
    base = []
    for r, cg, cd in cont["stages"]:
        sr = R_TABLE[snap_value(r, R_TABLE)]
        scg = C_TABLE[snap_value(cg, C_TABLE)]
        scd = C_TABLE[snap_value(cd, C_TABLE)] if cd > 0 else 0.0
        base.append((sr, scg, scd))
    print(f"  直接取整：{topo(base)}")

    # 2) 邻域枚举（±1 档），取 _key 最优
    best, best_ev, tried = base, evaluate(base), 0
    for cand in neighbours(base, span_r=1, span_c=1):
        tried += 1
        ev = evaluate(cand)
        if _key(ev) > _key(best_ev):
            best, best_ev = cand, ev
    print(f"  邻域枚举 {tried} 个组合 → {topo(best)}")

    # 3) 若 fc 越界，再放宽 fc：允许邻域外扩但不改档位表（只在 ±2 档内找 fc 合规者）
    if not best_ev["hard"]["fc_in_range"]:
        print(RED + "  ⚠ 取整后 fc 越界，扩到 ±2 档重搜" + RESET)
        for cand in neighbours(base, span_r=2, span_c=2):
            ev = evaluate(cand)
            if ev["hard"]["fc_in_range"] and _key(ev) > _key(best_ev):
                best, best_ev = cand, ev

    diff = report_diff(grade, cont_ev, best, best_ev)
    print(f"  冻结参数：{topo(best)}")
    print(f"    fc={best_ev['pred']['f_c_hz']/1e3:.2f} kHz (约束 {o5.FC_LO/1e3:.0f}–"
          f"{o5.FC_HI/1e3:.0f} kHz)  ΣR={best_ev['pred']['r_sum_ohm']:.1f} Ω  "
          f"min={best_ev['min_score']:.3f}")
    hard = best_ev["hard"]
    bad_hard = [k for k, v in hard.items() if not v]
    if bad_hard:
        print(RED + f"  ⚠ 硬约束未满足：{bad_hard}" + RESET)

    return {
        "grade": grade,
        "n_stages": n_stages,
        "stages": [[float(r), float(cg), float(cd)] for r, cg, cd in best],
        "pred": best_ev["pred"],
        "dims": best_ev["dims"],
        "pass": best_ev["pass"],
        "hard": hard,
        "continuous": {
            "stages": [list(map(float, s)) for s in cont["stages"]],
            "pred": cont["pred"],
            "dims": cont["dims"],
            "min_score": cont["meta"]["min_score"],
        },
        "snap": {
            "r_series": "E24",
            "c_series": "E12",
            "n_neighbourhood": tried,
            "lossy_dims": diff["lossy_dims"],
            "failing_dims": diff["failing_dims"],
            "hard_ok": not bad_hard,
            "min_before": cont["meta"]["min_score"],
            "min_after": best_ev["min_score"],
        },
    }


def main(argv=None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Round 5 三案 E 系列取整与冻结")
    ap.add_argument("--maxiter", type=int, default=220)
    ap.add_argument("--starts", type=int, default=3)
    ap.add_argument("--out", default=OUT_JSON)
    args = ap.parse_args(argv)

    print(f"R 档位 {len(R_TABLE)} 个（{R_TABLE[0]:g}~{R_TABLE[-1]:g} Ω，E24）")
    print(f"C 档位 {len(C_TABLE)} 个（{C_TABLE[0]*1e12:g} pF~{C_TABLE[-1]*1e9:g} nF，E12）")

    out = {}
    for grade, n in (("A", 2), ("B", 3), ("C", 4)):
        out[grade] = solve_and_snap(n, grade, maxiter=args.maxiter,
                                    n_starts=args.starts)

    # 连续解的帕累托前沿（与 opt_round5.print_front 同口径）
    front = []
    for g in ("A", "B", "C"):
        c = out[g]
        front.append({"stages": [tuple(s) for s in c["continuous"]["stages"]],
                      "pred": c["continuous"]["pred"],
                      "dims": c["continuous"]["dims"],
                      "meta": {"n_stages": c["n_stages"],
                               "min_score": c["continuous"]["min_score"]}})
    o5.print_front(front)

    # 汇总
    print(f"\n{'='*78}\n三案冻结汇总（理论预测，E24/E12 取整后）\n{'='*78}")
    print(f"{'案':>2} {'级':>2} {'min':>6} {'过线':>5} {'fc/kHz':>7} {'ΣR/Ω':>7} "
          f"{'件/线':>5}  拓扑")
    any_fail = False
    for g in ("A", "B", "C"):
        c = out[g]
        npass = sum(c["pass"].values())
        line = (f"{g:>2} {c['n_stages']:>2} {c['dims'] and min(c['dims'].values()):>6.3f} "
                f"{npass:>3}/10 {c['pred']['f_c_hz']/1e3:>7.2f} {c['pred']['r_sum_ohm']:>7.1f} "
                f"{c['pred']['n_parts']:>5}  {topo([tuple(s) for s in c['stages']])}")
        if npass < 10:
            any_fail = True
            print(RED + line + f"   ×不及格维度 {[k for k,v in c['pass'].items() if not v]}" + RESET)
        else:
            print(line)
        if not c["snap"]["hard_ok"]:
            print(RED + f"   ⚠ {g} 案硬约束未满足：{[k for k,v in c['hard'].items() if not v]}" + RESET)

    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
    print(f"\n已写出 {args.out}")
    if any_fail:
        print(RED + "\n⚠ 至少一案的某些维度未达及格线（详见上方红色标记与 JSON 的 "
                    "snap.failing_dims）" + RESET)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
