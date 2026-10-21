# -*- coding: utf-8 -*-
"""check_edacap_r5.py — 采集页网表重建 + B 案验证（只读审查）
数据源：r5_edacap_extract.json（EDA API 提取的 168 引脚 + 71 导线）
方法：并查集按坐标合并（引脚落点 ↔ 导线端点/折线段），网络标志名经导线连通传播
"""
from __future__ import annotations
import json, sys, io
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")

DATA = io.open("r5_edacap_extract.json", encoding="utf-8").read()
res = json.loads(DATA)["result"]
pins, wires = res["pins"], res["wires"]

# ---------- 并查集 ----------
parent: dict = {}
def find(a):
    parent.setdefault(a, a)
    while parent[a] != a:
        parent[a] = parent[parent[a]]
        a = parent[a]
    return a
def union(a, b):
    ra, rb = find(a), find(b)
    if ra != rb:
        parent[ra] = rb

def P(x, y):
    return f"pt:{x},{y}"

# 导线端点 + 逐段注册
wire_segs = []   # (x1,y1,x2,y2, wireIdx)
for i, w in enumerate(wires):
    pts = w["pts"] or []
    flat = []
    for j in range(0, len(pts) - 1, 2):
        flat.append((pts[j], pts[j + 1]))
    for a, b in zip(flat[:-1], flat[1:]):
        if a[0] != b[0] and a[1] != b[1]:
            continue  # 对角线段=同一wire对象内的独立子线跳变，丢弃
        wire_segs.append((a[0], a[1], b[0], b[1], i))
    for pt in flat:
        union(P(*pt), f"wire:{i}")

# 端点索引（导线端点吸附）
endpoint_index = defaultdict(list)
for i, w in enumerate(wires):
    pts = w["pts"] or []
    flat = [(pts[j], pts[j + 1]) for j in range(0, len(pts) - 1, 2)]
    for pt in flat:
        endpoint_index[pt].append(i)

# T 形搭接：导线端点落在另一条导线的线段中间 → union
for i, w in enumerate(wires):
    pts = w["pts"] or []
    flat = [(pts[j], pts[j + 1]) for j in range(0, len(pts) - 1, 2)]
    for (ex, ey) in flat:
        for (x1, y1, x2, y2, j) in wire_segs:
            if j == i:
                continue
            if x1 == x2 and abs(ex - x1) < 0.5 and min(y1, y2) - 0.5 <= ey <= max(y1, y2) + 0.5:
                union(f"wire:{i}", f"wire:{j}")
            elif y1 == y2 and abs(ey - y1) < 0.5 and min(x1, x2) - 0.5 <= ex <= max(x1, x2) + 0.5:
                union(f"wire:{i}", f"wire:{j}")

# 引脚落点：在导线端点上，或落在导线段中间（T 接）
pin_nodes = []
for p in pins:
    des = p.get('des') or 'NP'
    key = f"pin:{des}:{p['pin']}@{p['x']},{p['y']}"
    x, y = p["x"], p["y"]
    hit = False
    for (ex, ey) in endpoint_index.keys():
        if ex == (x, y):
            union(key, P(x, y))
            hit = True
            break
    if not hit:
        for (x1, y1, x2, y2, j) in wire_segs:
            if x1 == x2 and x == x1 and min(y1, y2) <= y <= max(y1, y2):
                union(key, f"wire:{j}")
                hit = True
                break
            elif y1 == y2 and y == y1 and min(x1, x2) <= x <= max(x1, x2):
                union(key, f"wire:{j}")
                hit = True
                break
    pin_nodes.append((key, p, hit))

# 网络标志：同名的所有标志 + 落在该坐标导线上的节点，全部并入一个虚拟网络
res_flags = res.get("flags", [])
flag_roots = {}
for f in res_flags:
    nm, fx, fy = f["nm"], round(f["x"], 6), round(f["y"], 6)
    virt = f"net:{nm}"
    flag_roots.setdefault(nm, virt)
    union(virt, P(fx, fy))
    # 标志坐标可能落在导线段中间
    for (x1, y1, x2, y2, j) in wire_segs:
        if x1 == x2 and fx == x1 and min(y1, y2) <= fy <= max(y1, y2):
            union(virt, f"wire:{j}")
        elif y1 == y2 and fy == y1 and min(x1, x2) <= fx <= max(x1, x2):
            union(virt, f"wire:{j}")

# 同坐标引脚直连（两引脚直接对接、无导线）
bycoord = defaultdict(list)
for key, p, hit in pin_nodes:
    bycoord[(p["x"], p["y"])].append(key)
for keys in bycoord.values():
    for k in keys[1:]:
        union(keys[0], k)

# ---------- 输出网络 ----------
nets = defaultdict(list)
for key, p, hit in pin_nodes:
    nets[find(key)].append(f"{(p.get('des') or 'NP')}.{p['pin']}")

print(f"引脚 {len(pin_nodes)} 个，其中 {sum(1 for _,_,h in pin_nodes if h)} 个落在导线上（其余 {sum(1 for _,_,h in pin_nodes if not h)} 个未连导线——检查是否同坐标直连或悬空）")
print()
out = []
for root, members in sorted(nets.items(), key=lambda kv: -len(kv[1])):
    if len(members) < 2:
        continue
    out.append(sorted(set(members)))
print(f"共 {len(out)} 个多引脚网络：")
for members in out:
    print("  ", "  ".join(members))

singles = [f"{(p.get('des') or 'NP')}.{p['pin']}" for key, p, hit in pin_nodes if len(nets[find(key)]) < 2]
print(f"\n悬空/单引脚网络 {len(singles)} 个：", "  ".join(sorted(singles)))
