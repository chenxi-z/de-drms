# -*- coding: utf-8 -*-
"""verify_edacap_against_B.py — 采集页网表 vs B 案定版 + ADS131A02 必接脚 断言
输入：check_edacap_r5.py 的网表（直接 import 其逻辑会重复执行，这里复制度解析）
"""
from __future__ import annotations
import json, io, sys
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")

res = json.load(io.open("r5_edacap_extract.json", encoding="utf-8"))["result"]

# ---- 重建网表（与 check_edacap_r5.py 相同算法）----
parent: dict = {}
def find(a):
    parent.setdefault(a, a)
    while parent[a] != a:
        parent[a] = parent[parent[a]]; a = parent[a]
    return a
def union(a, b):
    ra, rb = find(a), find(b)
    if ra != rb: parent[ra] = rb
def P(x, y): return f"pt:{x},{y}"

pins, wires, flags = res["pins"], res["wires"], res.get("flags", [])
wire_segs = []
for i, w in enumerate(wires):
    pts = w["pts"] or []
    flat = [(pts[j], pts[j+1]) for j in range(0, len(pts)-1, 2)]
    for a, b in zip(flat[:-1], flat[1:]):
        if a[0] != b[0] and a[1] != b[1]:
            continue
        wire_segs.append((a[0], a[1], b[0], b[1], i))
    for pt in flat:
        union(P(*pt), f"wire:{i}")
endpoint_index = defaultdict(list)
for i, w in enumerate(wires):
    pts = w["pts"] or []
    for j in range(0, len(pts)-1, 2):
        endpoint_index[(pts[j], pts[j+1])].append(i)
for i, w in enumerate(wires):
    pts = w["pts"] or []
    flat = [(pts[j], pts[j+1]) for j in range(0, len(pts)-1, 2)]
    for (ex, ey) in flat:
        for (x1, y1, x2, y2, j) in wire_segs:
            if j == i: continue
            if x1 == x2 and ex == x1 and min(y1,y2) <= ey <= max(y1,y2): union(f"wire:{i}", f"wire:{j}")
            elif y1 == y2 and ey == y1 and min(x1,x2) <= ex <= max(x1,x2): union(f"wire:{i}", f"wire:{j}")
pin_nodes = []
for p in pins:
    des = p.get("des") or "NP"
    key = f"pin:{des}:{p['pin']}@{p['x']},{p['y']}"
    x, y = p["x"], p["y"]
    hit = False
    for (ex, ey) in list(endpoint_index.keys()):
        if ex == (x, y):
            union(key, P(x, y)); hit = True; break
    if not hit:
        for (x1,y1,x2,y2,j) in wire_segs:
            if x1 == x2 and x == x1 and min(y1,y2) <= y <= max(y1,y2): union(key, f"wire:{j}"); hit=True; break
            elif y1 == y2 and y == y1 and min(x1,x2) <= x <= max(x1,x2): union(key, f"wire:{j}"); hit=True; break
    pin_nodes.append((key, p))
bycoord = defaultdict(list)
for key, p in pin_nodes:
    bycoord[(p["x"], p["y"])].append(key)
for keys in bycoord.values():
    for k in keys[1:]:
        union(keys[0], k)
for f in flags:
    nm, fx, fy = f["nm"], f["x"], f["y"]
    union(f"net:{nm}", P(fx, fy))
    for (x1,y1,x2,y2,j) in wire_segs:
        if x1 == x2 and fx == x1 and min(y1,y2) <= fy <= max(y1,y2): union(f"net:{nm}", f"wire:{j}")
        elif y1 == y2 and fy == y1 and min(x1,x2) <= fx <= max(x1,x2): union(f"net:{nm}", f"wire:{j}")

nets = defaultdict(set)
for key, p in pin_nodes:
    des = p.get("des") or "NP"
    nets[find(key)].add(f"{des}.{p['pin']}")
for nm in {f["nm"] for f in flags}:
    nets[find(f"net:{nm}")].add(f"NET:{nm}")

def net_of(ref: str) -> set:
    for members in nets.values():
        if ref in members:
            return members
    return set()

def has(members: set, *refs) -> bool:
    return all(r in members for r in refs)

ok, bad = [], []
def check(name, cond, detail=""):
    (ok if cond else bad).append((name, detail))

# ---- 值表（从 EDA 提取）----
VAL = {
    "R22":"6.19R","R23":"6.19R","R24":"6.04R","R25":"6.04R","R34":"13.7R","R35":"13.7R",
    "R36":"6.19R","R37":"6.19R","R38":"6.04R","R39":"6.04R","R40":"13.7R","R41":"13.7R",
    "C29":"68nF","C30":"270nF","C36":"68nF","C42":"68nF","C43":"68nF","C45":"27nF",
    "C46":"27nF","C47":"12nF","C48":"68nF","C49":"68nF","C50":"68nF","C51":"68nF",
    "C52":"27nF","C53":"27nF","C54":"12nF",
}

# ---- CH1 阶梯（P 线 = AIN1P = U7.2，N 线 = AIN1N = U7.1）----
# 期望：R22(6.19)-R24(6.04)-R34(13.7) 末级到 U7.1/2 之一；对地 C29/C43/C45 或 C36/C42/C46；差分 C47
check("CH1 P末级: U7.1 ← R34.2+C47.2+C46.1(27nF)", has(net_of("U7.1"), "R34.2", "C47.2", "C46.1"),
      str(net_of("U7.1")))
check("CH1 N末级: U7.2 ← R35.2+C47.1+C45.2(27nF)", has(net_of("U7.2"), "R35.2", "C47.1", "C45.2"),
      str(net_of("U7.2")))
check("C47=12nF 差分跨 U7.1-U7.2", VAL.get("C47") == "12nF")
check("中间级: R34.1-R24.2+C43.1", has(net_of("R34.1"), "R24.2", "C43.1"), str(net_of("R34.1")))
check("中间级: R35.1-R25.2+C42.2", has(net_of("R35.1"), "R25.2", "C42.2"), str(net_of("R35.1")))
check("首级: R24.1-R22.2+C29.1", has(net_of("R24.1"), "R22.2", "C29.1"), str(net_of("R24.1")))
check("首级: R25.1-R23.2+C36.2", has(net_of("R25.1"), "R23.2", "C36.2"), str(net_of("R25.1")))
check("R22.1 悬空=跟随器P输出入口(应连U5输出)", True, str(net_of("R22.1")))
check("R23.1 悬空=跟随器N输出入口", True, str(net_of("R23.1")))

# ---- CH2 阶梯（U7.3/4 = AIN2N/AIN2P）----
check("CH2 末级: U7.3 ← R40.2+C54.2+C53.1", has(net_of("U7.3"), "R40.2", "C54.2", "C53.1"), str(net_of("U7.3")))
check("CH2 末级: U7.4 ← R41.2+C54.1+C52.2", has(net_of("U7.4"), "R41.2", "C54.1", "C52.2"), str(net_of("U7.4")))
check("CH2 中间级: R40.1-R38.2+C51.1", has(net_of("R40.1"), "R38.2", "C51.1"), str(net_of("R40.1")))
check("CH2 中间级: R41.1-R39.2+C50.2", has(net_of("R41.1"), "R39.2", "C50.2"), str(net_of("R41.1")))
check("CH2 首级: R38.1-R36.2+C48.1", has(net_of("R38.1"), "R36.2", "C48.1"), str(net_of("R38.1")))
check("CH2 首级: R39.1-R37.2+C49.2", has(net_of("R39.1"), "R37.2", "C49.2"), str(net_of("R39.1")))

# ---- 对地电容真的到地？----
agnd = net_of("NET:AGND")
check("C29 对地", "C29.2" in agnd or "C29.2" in net_of("NET:AGND"), str(net_of("C29.2")))
for c in ["C29","C36","C43","C42","C45","C46","C48","C49","C50","C51","C52","C53"]:
    other = {"C29":".2","C36":".2","C43":".2","C42":".2","C45":".2","C46":".2",
             "C48":".2","C49":".1","C50":".1","C51":".2","C52":".1","C53":".2"}[c]
    members = net_of(f"{c}{other}")
    grounded = ("NET:AGND" in members) or ("NET:GND" in members)
    check(f"{c}{other} 接地(AGND/GND)", grounded, str(members))

# ---- U7 必接脚（手册 SBAS590E + AGENTS 硬约束）----
# 5-8 NC(悬空或AVSS); 9=AVDD; 10=AVSS; 11=VNCP→AVSS; 12=REFP; 13=REFN; 14=REFEXT; 15=IOVDD;
# 16=RESV→IOVDD; 17=RESET; 24=NC(悬空或10k下拉); 25=XTAL1; 26=XTAL2; 27=GND; 28=CAP→1uF到GND
check("U7.9(AVDD)=AVCC 网络", "NET:AVCC" in net_of("U7.9") and "U5.8" in net_of("U7.9"), str(net_of("U7.9")))
check("U7.10(AVSS)=AGND", "NET:AGND" in net_of("U7.10"), str(net_of("U7.10")))
check("U7.11(VNCP)→AGND", "NET:AGND" in net_of("U7.11"), str(net_of("U7.11")) + " （手册：VNCP 不用接 AVSS）")
check("U7.15(IOVDD)=VCC", "NET:VCC" in net_of("U7.15"), str(net_of("U7.15")))
check("U7.16(RESV)→IOVDD(=与15同网)", net_of("U7.16") == net_of("U7.15"), f"16:{sorted(net_of('U7.16'))} vs 15:{sorted(net_of('U7.15'))}")
check("U7.28(CAP)→1uF(C35)→GND", has(net_of("U7.28"), "C35.2") and net_of("C35.1") != net_of("U7.28"), str(net_of("U7.28")))
c35g = net_of("C35.1")
check("C35.1 接地", "NET:AGND" in c35g or "NET:GND" in c35g, str(c35g))
check("U7.27(GND)=", str(net_of("U7.27")), "")
# 12/13/14 REFP/REFN/REFEXT（内部基准时 REFEXT 接 AVSS? 手册 E.4.2：内置基准下 REFEXT 接 AVSS 或跟随内部）
check("U7.12(REFP)", str(net_of("U7.12")), "")
check("U7.13(REFN)", str(net_of("U7.13")), "")
check("U7.14(REFEXT)", str(net_of("U7.14")), "")
# 25/26 晶振
check("U7.25(XTAL1)=X3.3? ", str(net_of("U7.25")), "")
check("U7.26(XTAL2)", str(net_of("U7.26")), "")
# 数字脚
for pn in ["17","18","19","20","21","22","23","29","30","31","32"]:
    print(f"  U7.{pn}: {sorted(net_of(f'U7.{pn}'))}")

# ---- U5/U9 跟随器单元 ----
print()
print("U5.1-8:", [sorted(net_of(f"U5.{i}")) for i in range(1, 9)])
print("U9.1-8:", [sorted(net_of(f"U9.{i}")) for i in range(1, 9)])

# ---- 悬空清单 ----
singles = []
for key, p in pin_nodes:
    if len(nets[find(key)]) < 2:
        des = p.get("des") or "NP"
        singles.append(f"{des}.{p['pin']}")
print()
print("单引脚（悬空）:", " ".join(sorted(singles)))

print()
print(f"===== PASS {len(ok)} / FAIL {len(bad)} =====")
for name, detail in bad:
    print(f"  [FAIL] {name}  → {detail}")
for name, detail in ok:
    print(f"  [ok] {name}")
