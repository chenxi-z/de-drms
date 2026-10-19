#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""score_r5.py — Round 5 三案十维评分（规格 §5.1 阈值 + 归一化公式，min 短板制）

本脚本只做**评分与裁决**，不重新仿真：输入是 `r5_results_{A,B,C}.json` 的 `dims`
（LTspice 实测值，各维口径见 parse_r5.py 的 docstring），按
`docs/design/spec/2026-10-18-aa-driver-design.md` §5.1 逐维归一化，
总分 = min(D1..D10)；及格线另算（§5.1「及格线（越线淘汰）」），两者互不替代。

同时输出 spec §5.1a 点名的 **CH1 vs CH2 群延迟差专项**。⚠️ 口径说明：
LTspice 拓扑只有**一个差分通道的两条腿**（p/n 线），并未把 CH1(AIN1P/N) 与
CH2(AIN2P/N) 建成两个独立通道。因此这里给出的是
  ① 标称下线间（p−n）群延迟差；
  ② 1% 失配角（V3：n 线 R/C ×1.01）下线间群延迟差 —— 即「四线统一全配」下
     CH1/CH2 各自元件容差造成的通道间失配上界代理。
真正的 CH1−CH2 需要把两套标准单元分别建网表（四线全仿），本脚本无法从现有
.raw 得到，报告里如实标注为「代理值」。

用法：
    python score_r5.py                # 打印十维评分表 + 排序 + CH 专项
    python score_r5.py --json out.json
"""
from __future__ import annotations

import argparse
import json
import math
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
LTSPICE = r"C:\Users\chenx\AppData\Local\Programs\ADI\LTspice\LTspice.exe"
LSB_V = 2.0 * 2.442 / 2 ** 24          # §5.1 单位约定：291.10 nV/ LSB
LSB_NV = LSB_V * 1e9

# §5.1 维度表： (满分阈值, 及格线, 归一化类型)
#   ratio   : score = min(x/full, 1)   pass = x >= bare      （越大越好：D1/D2/D3/D8）
#   inverse : score = min(full/x, 1)   pass = x <= bare      （越小越好：D5）
#   linear  : x<=full→1，x>bare→0，其间 1-(x-full)/(bare-full)   （D4/D7/D10）
#   binary  : D9
SPEC = {
    "D1": ("DM 衰减 @fMOD",      "dB",  120.0,  80.0, "ratio"),
    "D2": ("CM 衰减 @fMOD",      "dB",  100.0,  60.0, "ratio"),
    "D3": ("DM 衰减 @MCLK",      "dB",  150.0, 100.0, "ratio"),
    "D4": ("通带平坦度 @16k",     "dB",    0.05,  0.5, "linear"),
    "D5": ("建立时间（最坏角）",  "us",  500.0, 900.0, "inverse"),
    "D6": ("积分噪声 @ADC 引脚",  "LSB",   0.3,   1.0, "inverse"),
    "D7": ("容差敏感度 @通带",    "dB",    0.01,  0.05, "linear"),
    "D8": ("CMRR @通带",         "dB",  100.0,  80.0, "ratio"),
    "D9": ("Kickback 回稳",      "-",     1.0,   1.0, "binary"),
    "D10": ("群延迟平坦度",       "us",    1.0,   5.0, "linear"),
}
DIMS = [f"D{i}" for i in range(1, 11)]
# D6 在 results.dims 里是 nVrms，评分口径是 LSB
NV_DIMS = {"D6"}


def normalize(dim: str, value: float) -> float:
    """§5.1 归一化公式，返回 [0,1]。"""
    _, _, full, bare, kind = SPEC[dim]
    x = float(value)
    if kind == "binary":
        return 1.0 if x == 1.0 else 0.0
    if kind == "ratio":
        return min(max(x, 0.0) / full, 1.0)
    if kind == "inverse":
        if x <= 0:
            return 1.0
        return min(full / x, 1.0)
    # linear（越小越好，两段线性）
    if x <= full:
        return 1.0
    if x > bare:
        return 0.0
    return 1.0 - (x - full) / (bare - full)


def passes(dim: str, value: float) -> bool:
    """§5.1 及格线：越线即淘汰（与归一化分数独立）。"""
    _, _, _, bare, kind = SPEC[dim]
    x = float(value)
    if kind == "binary":
        return x == 1.0
    if kind == "ratio":
        return x >= bare
    return x <= bare


def to_scoring_unit(dim: str, value: float) -> float:
    """dims 里的 D6 是 nVrms；§5.1 的 D6 阈值以 LSB 计。"""
    return float(value) / LSB_NV if dim in NV_DIMS else float(value)


# ------------------------------------------------------------------ 数据装载
def load_result(key: str) -> dict:
    with open(os.path.join(HERE, f"r5_results_{key}.json"), encoding="utf-8") as fh:
        return json.load(fh)


def unify_d5(res: dict) -> dict:
    """D5 口径统一（**三案现有 results 的 D5 不一致**，A/C 取全候选最大值，B 只取了 V9c）。

    spec §5.1 D5 要求「最坏角 + 覆盖高源阻抗（600 kΩ）」，parse_r5.py 的既定规则是
    取 D5_candidates_us 全集的**最大值**。B 的 dims 里 D5=34.68 µs（V9c），但其
    V4b（600 kΩ 未自举上界）=51.18 µs 更大 → 按同一规则应取 51.18 µs。
    两值均 ≤500 µs，**归一化分不变（=1.0）**，仅报告口径需对齐。
    """
    c = res.get("D5_candidates_us") or {}
    if not c:
        return {"as_recorded": res["dims"]["D5"], "adopted": res["dims"]["D5"],
                "candidates": {}, "rule": "无候选分解"}
    mx = max(c.values())
    return {"as_recorded": res["dims"]["D5"], "adopted": mx, "candidates": c,
            "rule": "max(D5_candidates_us) — parse_r5.py 既定规则",
            "changed": abs(mx - res["dims"]["D5"]) > 1e-9}


def verify_from_raw(key: str, res: dict) -> list:
    """从 .raw 反算 AC 四维，核对 results.json 的 dims 有无转录/口径错误。"""
    import parse_r5 as P
    ns = res.get("n_stages") or len(res["stages"])
    out = []
    try:
        tags = {"V1": ("D1", "D3", "D4", "D10"), "V2": ("D2",), "V3": ("D8",)}
        got = {}
        for tag in tags:
            path = (res["raw"][tag] if tag in res.get("raw", {}) else res["raw_files"][tag])
            r = P.Raw(_resolve(path))
            if tag == "V1":
                v = P.d1_d3_d4_d10(r, ns)
                got.update({"D1": v["D1_A_dm_db"], "D3": v["D3_A_mclk_db"],
                            "D4": v["D4_dG_16k_db"], "D10": v["D10_dtau_us"]})
            elif tag == "V2":
                got["D2"] = P.d2(r, ns)["D2_A_cm_db"]
            else:
                got["D8"] = P.d8(r, ns)["D8_CMRR_db"]
        for d in ("D1", "D2", "D3", "D4", "D8", "D10"):
            rec = float(res["dims"][d])
            out.append({"dim": d, "json": rec, "raw": got[d], "delta": got[d] - rec})
    except Exception as exc:
        out.append({"error": f"{type(exc).__name__}: {exc}"})
    return out


def score_case(key: str, res: dict) -> dict:
    # 评分严格用 results.json 记录的 dims（= 任务下发的实测值）；
    # D5 的候选分解另列，供报告说明口径（不改分：见 main 中的敏感性打印）
    dims = dict(res["dims"])
    d5 = unify_d5(res)
    rows = {}
    for d in DIMS:
        raw = float(dims[d])
        x = to_scoring_unit(d, raw)
        rows[d] = {
            "measured_raw": raw,
            "measured": x,
            "unit": SPEC[d][1],
            "score": normalize(d, x),
            "pass": passes(d, x),
            "stored_score": (res.get("scores") or {}).get(d),
        }
    total = min(rows[d]["score"] for d in DIMS)
    worst = [d for d in DIMS if abs(rows[d]["score"] - total) < 1e-12]
    return {
        "candidate": key,
        "n_stages": res.get("n_stages"),
        "rows": rows,
        "total": total,
        "short_board": worst,
        "gate_pass": all(rows[d]["pass"] for d in DIMS),
        "fail_dims": [d for d in DIMS if not rows[d]["pass"]],
    }


# ------------------------------------------------------------------ CH 群延迟专项
def _resolve(path: str) -> str:
    """results 里的 raw 路径三种风格（相对 r5_work/rs0、相对仓库根、绝对），统一解析。"""
    if os.path.isabs(path) and os.path.exists(path):
        return path
    base = os.path.basename(path.replace("\\", "/"))
    cands = [
        path, os.path.join(HERE, path), os.path.join(HERE, base),
        os.path.join(HERE, "r5_work", "rs0", base),
        os.path.join(HERE, "..", "..", "..", path),
    ]
    for c in cands:
        if os.path.exists(c):
            return os.path.abspath(c)
    raise FileNotFoundError(path)


def _raw_cols(path: str):
    from parse_r5 import Raw
    r = Raw(path)
    f = np.asarray(r.f, dtype=float)
    return r, f


def _tau(f: np.ndarray, col: np.ndarray) -> np.ndarray:
    ph = np.unwrap(np.angle(np.asarray(col, dtype=complex)))
    return -np.gradient(ph, 2 * math.pi * f)


def ch_delay(key: str, res: dict) -> dict:
    """线间群延迟差（p−n），取自既有 V1/V3。返回 ns。"""
    from parse_r5 import Raw
    ns = res.get("n_stages") or len(res["stages"])
    pa, na = f"V(pa{ns})", f"V(na{ns})"
    out = {"note": "单通道内 p/n 两线的延迟差（不是 CH1 vs CH2）"}
    for tag in ("V1", "V3"):
        try:
            p = _resolve(res["raw"][tag] if "raw" in res and tag in res["raw"]
                         else res["raw_files"][tag])
        except (KeyError, FileNotFoundError, TypeError):
            out[tag] = None
            continue
        r = Raw(p)
        f = np.asarray(r.f, dtype=float)
        cp = np.asarray(r.col(pa), dtype=complex)
        cn = np.asarray(r.col(na), dtype=complex)
        m = (f >= max(0.1, float(f[0]))) & (f <= 16e3)
        ff = f[m]
        tp = _tau(ff, cp[m])
        tn = _tau(ff, cn[m])
        out[tag] = {
            "raw": p,
            "tau_p_16k_us": float(tp[-1] * 1e6),
            "tau_n_16k_us": float(tn[-1] * 1e6),
            "diff_16k_ns": float((tp[-1] - tn[-1]) * 1e9),
            "max_abs_diff_ns": float(np.max(np.abs(tp - tn)) * 1e9),
        }
    return out


# ------------------------------------------------------------------ CH1 vs CH2 专项（真四线）
def gen_ch_net(x, y, nominal: bool = True) -> str:
    """四线 = 两套独立标准单元（CH1 = AIN1P/AIN1N，CH2 = AIN2P/AIN2N），AC 差分激励。

    spec §5.1a：「通道间（CH1 vs CH2）的群延迟匹配」—— 相位是 V_sample 与 V_Rsense
    两通道的相对值。既有 V1/V3 只有**一个**差分通道的两条腿，给不出这个量。
    这里按 §4「四线统一全配」把同一个标准单元摆两份：
      nominal=True  ：两通道同为标称值
      nominal=False ：CH2 的 R/C 各 ×1.01，CH1 标称（1% 通道间失配，最坏角）
    y = stages 列表 [(R, C_gnd, C_diff), ...]
    """
    ns = len(x)
    L = ["* CH1 vs CH2 group delay (four wires = two standard cells)",
         "* generated by score_r5.py (spec sec 5.1a)"]
    L += ["Vp1 p1 0 DC 2 AC 0.5", "Vn1 n1 0 DC 2 AC -0.5",
          "Vp2 p2 0 DC 2 AC 0.5", "Vn2 n2 0 DC 2 AC -0.5"]

    def line(tag, src, st):
        out, prev = [], src
        for i, (r, cg, _cd) in enumerate(st, 1):
            out.append(f"R{tag}{i} {prev} {tag}{i} {r:.10g}")
            out.append(f"C{tag}{i} {tag}{i} 0 {cg:.10g}")
            prev = f"{tag}{i}"
        return out

    # CH1：p1/n1；CH2：p2/n2
    L += line("a", "p1", x)
    L += line("an", "n1", x)
    L += line("b", "p2", y)
    L += line("bn", "n2", y)
    for tag, st in (("a", x), ("b", y)):
        n = len(st)
        if st[-1][2] > 0:
            L.append(f"C{tag}d {tag}{n} {tag}n{n} {st[-1][2]:.10g}")
        L += [f"R{tag}in {tag}{n} {tag}n{n} 130000",
              f"C{tag}p {tag}{n} 0 5e-12", f"C{tag}pn {tag}n{n} 0 5e-12"]
    L += [".ac dec 400 0.1 200Meg",
          ".options plotwinsize=0 reltol=1e-6 abstol=1e-12 vntol=1e-9 chgtol=1e-15 trtol=1",
          ".end"]
    return "\n".join(L) + "\n"


def ch1_ch2(key: str, res: dict, workdir: str = "") -> dict:
    """跑四线网表，取两通道各自差分输出 @16 kHz 群延迟，报差值。"""
    import subprocess
    from parse_r5 import Raw
    try:
        import shutil
    except ImportError:                       # pragma: no cover
        shutil = None
    st = [(float(r), float(c), float(cd)) for r, c, cd in res["stages"]]
    st2 = [(r * 1.01, c * 1.01, cd) for r, c, cd in st]
    d = workdir or os.path.join(HERE, "r5_work", "ch")
    os.makedirs(d, exist_ok=True)
    out = {}
    for tag, y in (("nominal", st), ("mismatch1pct", st2)):
        net = os.path.join(d, f"ch_{key}_{tag}.net")
        with open(net, "w", encoding="ascii", newline="\n") as fh:
            fh.write(gen_ch_net(st, y, nominal=(tag == "nominal")))
        raw = net[:-4] + ".raw"
        if os.path.exists(raw):
            os.remove(raw)
        p = subprocess.run([LTSPICE, "-b", "-ascii", os.path.basename(net)],
                           cwd=d, capture_output=True, text=True, timeout=120)
        if not os.path.exists(raw):
            out[tag] = {"error": f"LTspice rc={p.returncode}; {p.stderr[:200]}"}
            continue
        r = Raw(raw)
        f = np.asarray(r.f, dtype=float)
        m = (f >= float(f[0])) & (f <= 16e3)
        ff = f[m]
        ns = len(st)
        def tau(t):
            dp = np.asarray(r.col(f"V({t}{ns})"), dtype=complex)[m] \
                - np.asarray(r.col(f"V({t}n{ns})"), dtype=complex)[m]
            return _tau(ff, dp)
        t1, t2 = tau("a"), tau("b")
        out[tag] = {
            "raw": raw,
            "tau_ch1_16k_us": float(t1[-1] * 1e6),
            "tau_ch2_16k_us": float(t2[-1] * 1e6),
            "diff_16k_ns": float((t1[-1] - t2[-1]) * 1e9),
            # 带内最大差（0.1 Hz~16 kHz 全频段最坏）
            "max_abs_diff_ns": float(np.max(np.abs(t1 - t2)) * 1e9),
        }
    return out


# ------------------------------------------------------------------ 交叉验证表
XC_LABEL = {
    "A_dm": "D1 A_dm@fMOD", "A_cm": "D2 A_cm@fMOD", "A_mclk": "D3 A_mclk@MCLK",
    "dG_16k": "D4 ΔG@16k", "CMRR": "D8 CMRR@通带", "dtau_us": "D10 Δτ",
    "Vn_nv": "D6 噪声", "D7_sigma": "D7 σ", "t_settle": "D5 建立",
}


def xcheck_rows(res: dict) -> list:
    """把 A/C（ac_rows 列表）与 B（扁平字典）两种 xcheck schema 归一成同一张表。"""
    x = res.get("xcheck") or {}
    rows = []
    if "ac_rows" in x:                       # A / C
        for r in x["ac_rows"]:
            rows.append({"item": r["item"], "theory": r["theory"], "ltspice": r["ltspice"],
                         "diff": r["abs_diff"], "kind": "abs", "limit": 0.5,
                         "pass": bool(r["pass"])})
        if "settle" in x:
            s = x["settle"]
            rows.append({"item": "D5 建立", "theory": s["theory_us"], "ltspice": s["ltspice_us"],
                         "diff": s["rel_diff"] * 100, "kind": "rel%", "limit": 5.0,
                         "pass": bool(s["pass"])})
        if "noise" in x:
            s = x["noise"]
            rows.append({"item": "D6 噪声(LSB)", "theory": s.get("theory_lsb", s.get("theory")),
                         "ltspice": s.get("ltspice_lsb", s.get("ltspice")),
                         "diff": s["rel_diff"] * 100, "kind": "rel%", "limit": 5.0,
                         "pass": bool(s["pass"])})
    else:                                     # B
        for k, v in x.items():
            if not isinstance(v, dict) or "lt" not in v:
                continue
            if "delta" in v:
                is_rel = "rel_pct" in v
                rows.append({"item": XC_LABEL.get(k, k), "theory": v["th"], "ltspice": v["lt"],
                             "diff": v["rel_pct"] if is_rel else v["delta"],
                             "kind": "rel%" if is_rel else "abs",
                             "limit": 5.0 if is_rel else 0.5,
                             "pass": bool(v.get("pass_0p5", v.get("pass_5pct", v.get("pass_stat", False))))})
            elif "z_score" in v:
                rows.append({"item": XC_LABEL.get(k, k), "theory": v["th"], "ltspice": v["lt"],
                             "diff": v["rel_pct"], "kind": "σ(rel%)", "limit": 5.0,
                             "pass": bool(v.get("pass_stat"))})
    return rows


def audit_scores(key: str, case: dict) -> list:
    """审计 results.json 里自带的 scores 是否与 §5.1 公式一致（C 案曾出现不一致）。"""
    bad = []
    for d in DIMS:
        st = case["rows"][d]["stored_score"]
        if st is None:
            continue
        if abs(st - case["rows"][d]["score"]) > 2e-3:
            bad.append((d, st, case["rows"][d]["score"]))
    return bad


# ------------------------------------------------------------------ 输出
def fmt(x, nd=4):
    return f"{x:.{nd}f}"


def print_case(c: dict) -> None:
    print(f"\n=== 方案 {c['candidate']}（{c['n_stages']} 级）  总分 = min = {c['total']:.6f} ===")
    print(f"{'维':<4}{'维度':<20}{'实测':>12}{'单位':>6}{'归一化':>10}{'及格':>6}  说明")
    for d in DIMS:
        r = c["rows"][d]
        print(f"{d:<4}{SPEC[d][0]:<20}{fmt(r['measured'], 6):>12}{r['unit']:>6}"
              f"{r['score']:>10.4f}{'✓' if r['pass'] else '✗':>6}  {'' if r['pass'] else '越线'}")
    print(f"  短板维 = {','.join(c['short_board'])}；全维及格 = {c['gate_pass']}"
          f"；未及格维 = {','.join(c['fail_dims']) or '无'}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Round 5 十维评分（spec §5.1）")
    ap.add_argument("--cand", default="A,B,C")
    ap.add_argument("--json", default="")
    ap.add_argument("--no-raw", action="store_true", help="跳过 .raw 反算/CH 线间差")
    ap.add_argument("--no-ch-sim", action="store_true", help="跳过 CH1/CH2 四线仿真")
    args = ap.parse_args(argv)

    cases = []
    for key in [s.strip() for s in args.cand.split(",") if s.strip()]:
        res = load_result(key)
        c = score_case(key, res)
        c["d5"] = unify_d5(res)
        c["xcheck_rows"] = xcheck_rows(res)
        c["audit"] = audit_scores(key, c)
        if not args.no_raw:
            try:
                c["verify"] = verify_from_raw(key, res)
            except Exception as exc:
                c["verify"] = [{"error": f"{type(exc).__name__}: {exc}"}]
            try:
                c["ch_delay"] = ch_delay(key, res)
            except Exception as exc:          # 缺 .raw 不应阻断评分
                c["ch_delay"] = {"error": f"{type(exc).__name__}: {exc}"}
            if not args.no_ch_sim:
                try:
                    c["ch1_ch2"] = ch1_ch2(key, res)
                except Exception as exc:
                    c["ch1_ch2"] = {"error": f"{type(exc).__name__}: {exc}"}
        cases.append(c)

    for c in cases:
        print_case(c)
        d5 = c.get("d5") or {}
        if d5.get("changed"):
            print(f"  ⚠ D5 口径：results.json 记 {d5['as_recorded']:.3f} µs，"
                  f"但候选分解最大值为 {d5['adopted']:.3f} µs（{d5['rule']}）；"
                  f"两值均远优于 500 µs，归一化分不变")
        bad = c["audit"]
        if bad:
            print("  ⚠ results.json 自带 scores 与 §5.1 公式不一致："
                  + "；".join(f"{d}: {s:.4f} → {n:.4f}" for d, s, n in bad))
        ver = [v for v in c.get("verify") or [] if "error" in v or abs(v["delta"]) > 1e-3]
        if ver:
            print("  ⚠ .raw 反算与 JSON dims 相差 >1e-3：" + "；".join(
                v.get("error") or f"{v['dim']} json={v['json']:.6f} raw={v['raw']:.6f}"
                for v in ver))
        else:
            mx = max((abs(v["delta"]) for v in c.get("verify") or [] if "dim" in v),
                     default=0.0)
            print(f"  ✓ D1/D2/D3/D4/D8/D10 已由 .raw 反算复核，与 JSON dims 一致"
                  f"（max|Δ|={mx:.2e}；B 案 JSON 只存 3 位小数）")
        ch = c.get("ch_delay") or {}
        if ch.get("V1"):
            s = f"  CH 线间群延迟差 @16k：标称 {ch['V1']['diff_16k_ns']:+.3f} ns" \
                f"（带内最大 {ch['V1']['max_abs_diff_ns']:.3f} ns）"
            if ch.get("V3"):
                s += (f"；1% 失配 {ch['V3']['diff_16k_ns']:+.3f} ns"
                      f"（带内最大 {ch['V3']['max_abs_diff_ns']:.3f} ns）")
            print(s)
        elif ch.get("error"):
            print(f"  CH 专项未算：{ch['error']}")
        cc = c.get("ch1_ch2") or {}
        if cc.get("nominal") and "diff_16k_ns" in cc["nominal"]:
            n, m = cc["nominal"], cc.get("mismatch1pct") or {}
            print(f"  CH1 vs CH2 群延迟差（真四线）：标称 {n['diff_16k_ns']:+.4f} ns"
                  f"（带内最大 {n['max_abs_diff_ns']:.4f} ns）"
                  + (f"；1% 通道失配 {m['diff_16k_ns']:+.3f} ns"
                     f"（带内最大 {m['max_abs_diff_ns']:.3f} ns）" if "diff_16k_ns" in m else ""))
        elif cc.get("error"):
            print(f"  CH1/CH2 四线仿真未完成：{cc['error']}")

    rank = sorted(cases, key=lambda c: -c["total"])
    print("\n=== 按总分（min 短板制）降序 ===")
    for i, c in enumerate(rank, 1):
        print(f"  {i}. {c['candidate']}: {c['total']:.6f}"
              f"  短板 {','.join(c['short_board'])}  全维及格={c['gate_pass']}")

    if args.json:
        payload = []
        for c in rank:
            payload.append({
                "candidate": c["candidate"], "n_stages": c["n_stages"],
                "total": c["total"], "gate_pass": c["gate_pass"],
                "short_board": c["short_board"], "fail_dims": c["fail_dims"],
                "rows": {d: {"measured": c["rows"][d]["measured_raw"],
                             "unit": c["rows"][d]["unit"],
                             "score": c["rows"][d]["score"],
                             "pass": c["rows"][d]["pass"]} for d in DIMS},
                "ch_delay": c.get("ch_delay"),
                "ch1_ch2": c.get("ch1_ch2"),
                "xcheck_rows": c["xcheck_rows"],
                "scores_json_inconsistent": c["audit"],
            })
        with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
        print(f"\n→ {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
