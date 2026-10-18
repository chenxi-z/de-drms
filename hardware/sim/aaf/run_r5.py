#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""run_r5.py — Round 5 批量复测驱动器（LTspice `-b -ascii`，全 .net）

计划 Task 5 Step 1：
  * 遍历方案 × V1–V9，逐个 `LTspice.exe -b -ascii <file.net>`，**超时 300 s/个**；
  * **锁屏检测**：先试跑一个 .net，60 s 无 `.raw` 产出即中止并提示用户解锁。

用法：
    python run_r5.py --cand C            # 方案 C 全量
    python run_r5.py --cand C --only v1,v2,v3
    python run_r5.py --cand C --no-mc    # 跳过 V5/V6 的 60 个蒙特卡洛
"""
from __future__ import annotations

import argparse
import glob
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
LTSPICE = r"C:\Users\chenx\AppData\Local\Programs\ADI\LTspice\LTspice.exe"
TIMEOUT_S = 300
LOCK_PROBE_S = 60


def run_one(net: str, timeout=TIMEOUT_S, workdir: str = HERE) -> dict:
    """跑一个网表，返回 {net, ok, secs, raw, log_err}。"""
    base = net[:-4] if net.lower().endswith(".net") else net
    raw = base + ".raw"
    log = base + ".log"
    for p in (raw, log):
        if os.path.exists(p):
            os.remove(p)
    t0 = time.time()
    try:
        p = subprocess.run([LTSPICE, "-b", "-ascii", net],
                           cwd=workdir, capture_output=True, text=True,
                           timeout=timeout)
        rc = p.returncode
    except subprocess.TimeoutExpired:
        return {"net": net, "ok": False, "secs": time.time() - t0,
                "raw": None, "log_err": f"TIMEOUT > {timeout}s"}
    dt = time.time() - t0
    err = ""
    if os.path.exists(log):
        txt = open(log, "r", encoding="ascii", errors="replace").read()
        bad = [ln.strip() for ln in txt.splitlines()
               if "FAIL" in ln or "Error" in ln or "error" in ln]
        err = " | ".join(bad[:3])
    ok = os.path.exists(raw) and os.path.getsize(raw) > 1000 and rc == 0
    if not ok and not err:
        err = f"rc={rc}, raw={'yes' if os.path.exists(raw) else 'no'}"
    return {"net": os.path.basename(net), "ok": ok, "secs": round(dt, 2),
            "raw": os.path.basename(raw) if os.path.exists(raw) else None,
            "log_err": err}


def check_lock() -> bool:
    """锁屏检测：清单里第一个 .net 试跑，LOCK_PROBE_S 内无 .raw 即判挂。"""
    probe = sorted(glob.glob(os.path.join(HERE, "r5_*_v1.net")))
    if not probe:
        return True
    net = probe[0]
    raw = net[:-4] + ".raw"
    if os.path.exists(raw):
        os.remove(raw)
    try:
        subprocess.run([LTSPICE, "-b", "-ascii", net], cwd=HERE,
                       capture_output=True, timeout=LOCK_PROBE_S)
    except subprocess.TimeoutExpired:
        print(f"⚠ 锁屏检测失败：{lock_probe_msg()}")
        return False
    if not os.path.exists(raw):
        print(f"⚠ 锁屏检测失败：{lock_probe_msg()}")
        return False
    return True


def lock_probe_msg() -> str:
    return (f"LTspice 在 {LOCK_PROBE_S}s 内未产出 .raw —— 可能锁屏/无 GUI 会话。"
            "请解锁屏幕后重跑 run_r5.py。")


def collect(key: str, only=None, no_mc=False, d: str = HERE) -> list:
    pats = [f"r5_{key}_v*.net"]
    nets = []
    for pat in pats:
        nets += glob.glob(os.path.join(d, pat))
    nets = sorted(set(nets))
    if no_mc:
        nets = [n for n in nets if "_v5mc" not in n and "_v6mc" not in n]
    if only:
        want = {s.strip().lower() for s in only.split(",") if s.strip()}
        nets = [n for n in nets
                if any(f"_{w}" in os.path.basename(n).lower() or
                       os.path.basename(n).lower().startswith(f"r5_{key}_{w}")
                       for w in want)]
    return nets


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cand", default="C")
    ap.add_argument("--only", default="")
    ap.add_argument("--no-mc", action="store_true")
    ap.add_argument("--skip-lock-check", action="store_true")
    ap.add_argument("--dir", default=HERE, help="网表所在目录（默认当前目录）")
    args = ap.parse_args(argv)

    if not os.path.exists(LTSPICE):
        print("✗ 找不到 LTspice:", LTSPICE)
        return 2
    if not args.skip_lock_check and not check_lock():
        return 3

    d = os.path.abspath(args.dir)
    nets = collect(args.cand, args.only or None, args.no_mc, d)
    if not nets:
        print("✗ 无网表可跑（先执行 gen_netlists_r5.py）")
        return 4
    print(f"方案 {args.cand}: {len(nets)} 个网表，逐个 LTspice -b -ascii（超时 {TIMEOUT_S}s）")
    rows, t0 = [], time.time()
    for i, n in enumerate(nets, 1):
        r = run_one(n, workdir=d)
        rows.append(r)
        flag = "✓" if r["ok"] else "✗"
        print(f"  [{i:2d}/{len(nets)}] {flag} {r['net']:28s} {r['secs']:6.2f}s"
              + (f"  {r['log_err']}" if r["log_err"] else ""))
    bad = [r for r in rows if not r["ok"]]
    print(f"\n完成 {len(rows)-len(bad)}/{len(rows)}，用时 {time.time()-t0:.1f}s")
    if bad:
        print("失败清单：")
        for r in bad:
            print("  ✗", r["net"], "-", r["log_err"])
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
