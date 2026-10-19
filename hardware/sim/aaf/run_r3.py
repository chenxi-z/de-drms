#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""run_r3.py — 方案 A 第 3 轮复测驱动器（LTspice `-b -ascii`，全 .net）

按 ask 要求：
  * V1–V9 全部用 `.net` 批处理（不用 `.asc`，锁屏时不挂）；
  * 主评分口径 = 真实 OPA388 模型（v9*），0 Ω 理想源（v1–v8）仅作对照；
  * 单个网表超时保护 + 失败清单，跑完写 `r5_work/r3/run_manifest.json`。

用法::

    python run_r3.py                 # 跑全部
    python run_r3.py --only v9a,v9b  # 只跑匹配的
    python run_r3.py --no-mc         # 跳过 v5mc/v6mc/v9m 的 90 个蒙特卡洛
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import subprocess
import time

HERE = os.path.dirname(os.path.abspath(__file__))
LTSPICE = r"C:\Users\chenx\AppData\Local\Programs\ADI\LTspice\LTspice.exe"
D = os.path.join(HERE, "r5_work", "r3")
TIMEOUT_S = 300

# 真实模型瞬态/开关类网表：给更长超时（TI 模型内部 1F 电容咬步长）
LONG = {"v9c": 420, "v9f": 420, "v9k": 200}


def classify(base: str) -> int:
    for tag, t in LONG.items():
        if f"_{tag}" in base:
            return t
    return TIMEOUT_S


def run_one(path: str) -> dict:
    base = os.path.basename(path)[:-4]
    for ext in (".raw", ".log"):
        q = os.path.join(D, base + ext)
        if os.path.exists(q):
            try:
                os.remove(q)
            except OSError:
                pass
    t0 = time.time()
    to = classify(base)
    try:
        p = subprocess.run([LTSPICE, "-b", "-ascii", base + ".net"], cwd=D,
                           capture_output=True, text=True, timeout=to)
        rc = p.returncode
    except subprocess.TimeoutExpired:
        return {"net": base, "ok": False, "secs": round(time.time() - t0, 1),
                "raw_mb": None, "err": f"TIMEOUT >{to}s"}
    dt = time.time() - t0
    raw = os.path.join(D, base + ".raw")
    log = os.path.join(D, base + ".log")
    err = ""
    if os.path.exists(log):
        txt = open(log, "r", encoding="ascii", errors="replace").read()
        bad = [ln.strip() for ln in txt.splitlines()
               if ("FAIL" in ln or "Error" in ln or "error" in ln
                   or "not defined" in ln or "Singular" in ln)]
        err = " | ".join(bad[:3])
    size = os.path.getsize(raw) / 1e6 if os.path.exists(raw) else None
    ok = size is not None and size > 0.01 and rc == 0
    return {"net": base, "ok": ok, "secs": round(dt, 1),
            "raw_mb": round(size, 1) if size else None,
            "err": err or ("" if ok else f"rc={rc}")}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--no-mc", action="store_true")
    ap.add_argument("--cand", default="A")
    args = ap.parse_args(argv)
    if not os.path.exists(LTSPICE):
        print("✗ 找不到 LTspice:", LTSPICE)
        return 2
    nets = sorted(glob.glob(os.path.join(D, f"r5_{args.cand}_r3_*.net")))
    if args.no_mc:
        nets = [n for n in nets if "mc" not in os.path.basename(n)]
    if args.only:
        want = {s.strip() for s in args.only.split(",") if s.strip()}
        nets = [n for n in nets
                if any(w in os.path.basename(n) for w in want)]
    if not nets:
        print("✗ 无网表（先跑 gen_netlists_r3.py）")
        return 4
    print(f"方案 {args.cand}: {len(nets)} 个网表")
    rows, t0 = [], time.time()
    for i, n in enumerate(nets, 1):
        r = run_one(n)
        rows.append(r)
        print(f"  [{i:3d}/{len(nets)}] {'✓' if r['ok'] else '✗'} {r['net']:28s} "
              f"{r['secs']:7.1f}s {str(r['raw_mb'] or ''):>8s}"
              + (f"  {r['err']}" if r["err"] else ""), flush=True)
    bad = [r for r in rows if not r["ok"]]
    print(f"\n完成 {len(rows)-len(bad)}/{len(rows)}，用时 {time.time()-t0:.0f}s")
    for r in bad:
        print("  ✗", r["net"], "-", r["err"])
    with open(os.path.join(D, "run_manifest.json"), "w", encoding="utf-8",
              newline="\n") as fh:
        json.dump({"candidate": args.cand, "rows": rows,
                   "n_ok": len(rows) - len(bad), "n_fail": len(bad)},
                  fh, ensure_ascii=False, indent=2)
    return 0 if not bad else 1


if __name__ == "__main__":
    raise SystemExit(main())
