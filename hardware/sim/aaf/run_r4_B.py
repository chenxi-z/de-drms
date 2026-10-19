#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""run_r4_B.py — 第 4 轮方案 B 的 LTspice 批处理（全部 `.net`，`-b -ascii`）

只跑 `r5_work/r4_B/r5_B_r4_*.net`（由 gen_netlists_r5_r4.py 生成），
每个网表超时 600 s，结果 `.raw/.log` 落在同目录。

用法
----
    python run_r4_B.py                      # 全跑
    python run_r4_B.py --only v9f_s        # 只跑匹配子串的
    python run_r4_B.py --skip mc           # 跳过含 mc 的（蒙特卡洛 60 个）
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
LT = r"C:\Users\chenx\AppData\Local\Programs\ADI\LTspice\LTspice.exe"
D = os.path.join(HERE, "r5_work", "r4_B")
TIMEOUT_S = 600


def run_one(net):
    base = net[:-4]
    for ext in (".raw", ".log", ".op.raw"):
        q = base + ext
        if os.path.exists(q):
            try:
                os.remove(q)
            except OSError:
                pass
    t0 = time.time()
    try:
        p = subprocess.run([LT, "-b", "-ascii", os.path.basename(net)], cwd=D,
                           capture_output=True, text=True, timeout=TIMEOUT_S)
        rc = p.returncode
    except subprocess.TimeoutExpired:
        return {"net": os.path.basename(base), "ok": False,
                "secs": round(time.time() - t0, 1), "raw_mb": None,
                "err": f"TIMEOUT >{TIMEOUT_S}s"}
    dt = time.time() - t0
    raw = base + ".raw"
    log = base + ".log"
    err = ""
    if os.path.exists(log):
        txt = open(log, "r", encoding="ascii", errors="replace").read()
        bad = [ln.strip() for ln in txt.splitlines()
               if ("FAIL" in ln or "Error" in ln or "Singular" in ln
                   or "not defined" in ln)]
        err = " | ".join(bad[:3])
    size = os.path.getsize(raw) / 1e6 if os.path.exists(raw) else None
    ok = size is not None and size > 0.001 and rc == 0
    return {"net": os.path.basename(base), "ok": ok, "secs": round(dt, 1),
            "raw_mb": round(size, 2) if size else None,
            "err": err or ("" if ok else f"rc={rc}")}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--skip", default="")
    args = ap.parse_args(argv)
    if not os.path.exists(LT):
        print("找不到 LTspice:", LT)
        return 2
    nets = sorted(glob.glob(os.path.join(D, "r5_B_r4_*.net")))
    if args.only:
        want = [s for s in args.only.split(",") if s]
        nets = [n for n in nets if any(w in os.path.basename(n) for w in want)]
    if args.skip:
        bad = [s for s in args.skip.split(",") if s]
        nets = [n for n in nets if not any(b in os.path.basename(n) for b in bad)]
    if not nets:
        print("无网表（先跑 gen_netlists_r5_r4.py）")
        return 4
    print(f"{len(nets)} 个网表 -> {D}", flush=True)
    rows, t0 = [], time.time()
    for i, n in enumerate(nets, 1):
        r = run_one(n)
        rows.append(r)
        print(f"[{i:3d}/{len(nets)}] {'OK  ' if r['ok'] else 'FAIL'} "
              f"{r['net']:34s} {r['secs']:7.1f}s {str(r['raw_mb'] or ''):>7s}"
              + (f"  {r['err'][:70]}" if r["err"] else ""), flush=True)
    bad = [r for r in rows if not r["ok"]]
    print(f"\n完成 {len(rows)-len(bad)}/{len(rows)}，用时 {time.time()-t0:.0f}s")
    for r in bad:
        print("  FAIL", r["net"], "-", r["err"])
    man = os.path.join(D, "run_manifest_r4_B.json")
    with open(man, "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"rows": rows, "n_ok": len(rows) - len(bad), "n_fail": len(bad)},
                  fh, ensure_ascii=False, indent=2)
    print("→", man)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
