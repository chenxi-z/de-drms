#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""run_r3_C.py — 方案 C 第 3 轮 LTspice 批处理（全部 .net，带 _r3 文件名）

只跑 `r5_work/r3_C/` 下的 r5_C_r3_*.net；每个网表 `-b -ascii`，超时 600 s。
输出 .raw/.log 落在同目录。
"""
import glob, os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
LT = r"C:\Users\chenx\AppData\Local\Programs\ADI\LTspice\LTspice.exe"
D = os.path.join(HERE, "r5_work", "r3_C")

def main(only=None):
    nets = sorted(glob.glob(os.path.join(D, "r5_C_r3_*.net")))
    if only:
        nets = [n for n in nets if any(o in os.path.basename(n) for o in only)]
    print(f"{len(nets)} 个网表")
    fails = []
    t_all = time.time()
    for i, net in enumerate(nets, 1):
        base = net[:-4]
        for ext in (".raw", ".log", ".op.raw"):
            if os.path.exists(base + ext):
                os.remove(base + ext)
        t0 = time.time()
        try:
            p = subprocess.run([LT, "-b", "-ascii", os.path.basename(net)], cwd=D,
                               capture_output=True, text=True, timeout=600)
            rc = p.returncode
        except subprocess.TimeoutExpired:
            print(f"[{i}/{len(nets)}] TIMEOUT {os.path.basename(net)}", flush=True)
            fails.append((os.path.basename(net), "TIMEOUT"))
            continue
        dt = time.time() - t0
        ok = os.path.exists(base + ".raw")
        err = ""
        if os.path.exists(base + ".log"):
            txt = open(base + ".log", encoding="ascii", errors="replace").read()
            bad = [l for l in txt.splitlines() if "Error" in l or "FAIL" in l or "Singular" in l]
            err = " | ".join(bad[:2])
        print(f"[{i}/{len(nets)}] {'OK ' if ok else 'FAIL'} {os.path.basename(net):34s} "
              f"{dt:7.2f}s {err[:70]}", flush=True)
        if not ok:
            fails.append((os.path.basename(net), err or f"rc={rc}"))
    print(f"\n总耗时 {time.time()-t_all:.1f}s；失败 {len(fails)}")
    for f in fails:
        print("  ✗", f)
    return 1 if fails else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or None))
