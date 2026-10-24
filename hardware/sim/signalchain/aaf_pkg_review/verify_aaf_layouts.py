#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""读回验证 v2：副本 PCB1_1 上 AAF 布局逐件比对、镜像断言、碰撞检查与包围面积。

关键事实（v1 教训）：
- EasyEDA 落盘时把焊盘坐标/尺寸舍入到 0.1 mil → 匹配容差取 0.06 mil；
- 过 Cd 三通的行尾线被编辑器自动拆分为两段 → 线匹配按「同网络端点覆盖」而非一一线段相等；
- GND 焊盘/GND 线网络名不带 AAF_ 前缀 → 按 x>8200 的评测区几何范围纳入。
"""
import json, subprocess

BRIDGE = "http://127.0.0.1:49620/execute"
MIL2MM = 0.0254
OUT = "/media/anning/data/Project/DE-DRMS/hardware/sim/signalchain/aaf_pkg_review"
TOL = 0.06

def post_js(code, timeout=120):
    p = subprocess.run(["curl", "-s", "--max-time", str(timeout), "-X", "POST", BRIDGE,
                        "-H", "Content-Type: application/json", "-d", json.dumps({"code": code})],
                       capture_output=True, text=True)
    return json.loads(p.stdout)

CODE = r"""
const pads = await eda.pcb_PrimitivePad.getAll();
const vias = await eda.pcb_PrimitiveVia.getAll();
const lines = await eda.pcb_PrimitiveLine.getAll();
const silks = await eda.pcb_PrimitiveString.getAll();
const padOut = pads.filter(p => p.getState_X() > 8200).map(p => {
  const s = p.getState_Pad() || [];
  return {x: p.getState_X(), y: p.getState_Y(), net: p.getState_Net(), shape: Array.isArray(s)? s.map(v=>v): s, layer: p.getState_Layer()};
});
const preEdge = Math.max(...pads.filter(p=>p.getState_X() <= 8200).map(p=>{const s=p.getState_Pad()||[]; return p.getState_X() + (Array.isArray(s)&&s.length>1? s[1]/2 : 0);}));
const viaOut = vias.filter(v => v.getState_X() > 8200).map(v => ({x: v.getState_X(), y: v.getState_Y(), d: v.getState_Diameter(), h: v.getState_HoleDiameter(), net: v.getState_Net()}));
const lineOut = lines.filter(l => Math.min(l.getState_StartX(), l.getState_EndX()) > 8200).map(l => ({x1: l.getState_StartX(), y1: l.getState_StartY(), x2: l.getState_EndX(), y2: l.getState_EndY(), w: l.getState_LineWidth(), net: l.getState_Net(), layer: l.getState_Layer()}));
const silkOut = silks.filter(s => s.getState_X() > 8200).map(s => ({x: s.getState_X(), y: s.getState_Y(), t: s.getState_Text()}));
return {pads: padOut, vias: viaOut, lines: lineOut, silks: silkOut, preExistingMaxEdgeX: preEdge,
        totals: {pads: pads.length, vias: vias.length, lines: lines.length}};
"""

def close(a, b):
    return abs(a - b) <= TOL

def main():
    resp = post_js(CODE)
    if not resp.get("success"):
        print("readback failed:", json.dumps(resp)[:600]); raise SystemExit(1)
    rb = resp["result"]
    json.dump(rb, open(f"{OUT}/aaf_layout_readback.json", "w"), ensure_ascii=False, indent=1)
    plan = json.load(open(f"{OUT}/aaf_layout_plan.json"))
    VIA_DIA = plan["via"]["dia"]

    pads, vias, lines = rb["pads"], rb["vias"], rb["lines"]
    checks, perScheme = {}, {}

    # ---- 1) 焊盘逐件比对（net + 坐标 + 尺寸）----
    used = [False] * len(pads); unmatched = []
    for sp in plan["plans"]:
        for ch in ("ch1", "ch2"):
            for p in sp[ch]["pads"]:
                hit = -1
                for i, q in enumerate(pads):
                    if used[i] or q["net"] != p["net"] or not close(q["x"], p["x"]) or not close(q["y"], p["y"]):
                        continue
                    if len(q["shape"]) >= 3 and close(q["shape"][1], p["w"]) and close(q["shape"][2], p["h"]):
                        hit = i; break
                if hit < 0: unmatched.append((sp["id"], ch, p))
                else: used[hit] = True
    leftover = [pads[i] for i in range(len(pads)) if not used[i]]
    checks["pads"] = dict(planned=sum(len(sp[c]["pads"]) for sp in plan["plans"] for c in ("ch1","ch2")),
                          placed=len(pads), unmatched=len(unmatched), leftover=len(leftover))

    # ---- 2) 过孔逐件比对（坐标）----
    usedv = [False] * len(vias); unmatchedv = []
    for sp in plan["plans"]:
        for ch in ("ch1", "ch2"):
            for v in sp[ch]["vias"]:
                hit = next((i for i, q in enumerate(vias) if not usedv[i] and close(q["x"], v["x"]) and close(q["y"], v["y"])), -1)
                if hit < 0: unmatchedv.append((sp["id"], ch, v))
                else: usedv[hit] = True
    leftoverv = [vias[i] for i in range(len(vias)) if not usedv[i]]
    checks["vias"] = dict(planned=sum(len(sp[c]["vias"]) for sp in plan["plans"] for c in ("ch1","ch2")),
                          placed=len(vias), unmatched=len(unmatchedv), leftover=len(leftoverv))

    # ---- 3) 线比对：同网络「端点覆盖」（编辑器允许在 Cd 三通处拆段）----
    unmatchedl = []
    for sp in plan["plans"]:
        for ch in ("ch1", "ch2"):
            for l in sp[ch]["lines"]:
                segs = [q for q in lines if q["net"] == l["net"]]
                ends = set()
                for q in segs:
                    ends.add((round(q["x1"], 1), round(q["y1"], 1))); ends.add((round(q["x2"], 1), round(q["y2"], 1)))
                ok = any(close(e[0], l["x1"]) and close(e[1], l["y1"]) for e in ends) and \
                     any(close(e[0], l["x2"]) and close(e[1], l["y2"]) for e in ends)
                if not ok: unmatchedl.append((sp["id"], ch, l))
    leftoverl = [l for l in lines if not l["net"].startswith("AAF_")]
    checks["lines"] = dict(planned=sum(len(sp[c]["lines"]) for sp in plan["plans"] for c in ("ch1","ch2")),
                           placed=len(lines), placedAaf=len(lines)-len(leftoverl),
                           placedGnd=len(leftoverl), unmatchedEndpoints=len(unmatchedl))

    # ---- 4) 每通道包围框（从已放置铜重算）+ 镜像断言 ----
    # 所有通道中心先收集（GND 件按最近通道中心归属，窗口法会把邻通道件吸进来）
    all_centers = [(sp["id"], k, sp[f"ch{k}_yc"]) for sp in plan["plans"] for k in (1, 2)]
    def owner(y):
        return min(all_centers, key=lambda t: abs(t[2] - y))
    for sp in plan["plans"]:
        sid = sp["id"]; per = {}
        for ch, k in (("ch1", 1), ("ch2", 2)):
            tag = f"AAF_{sid}_CH{k}_"
            yc = sp[f"ch{k}_yc"]
            ycr = round(yc, 1)                     # 放置坐标被舍入到 0.1 mil，镜像轴同取整
            pb = sp[ch]["bbox"]
            pads_c = [p for p in pads if p["net"].startswith(tag)]
            gndpads_c = [p for p in pads if p["net"] == "GND" and pb["x1"] - 60 <= p["x"] <= pb["x2"] + 60
                         and owner(p["y"])[0] == sid and owner(p["y"])[1] == k]
            vias_c = [v for v in vias if pb["x1"] - 60 <= v["x"] <= pb["x2"] + 60
                      and owner(v["y"])[0] == sid and owner(v["y"])[1] == k]
            lines_c = [l for l in lines if l["net"].startswith(tag)]
            gndlines_c = [l for l in lines if l["net"] == "GND"
                          and owner((l["y1"] + l["y2"]) / 2)[0] == sid and owner((l["y1"] + l["y2"]) / 2)[1] == k]
            xs, ys = [], []
            for p in pads_c + gndpads_c:
                xs += [p["x"] - p["shape"][1] / 2, p["x"] + p["shape"][1] / 2]
                ys += [p["y"] - p["shape"][2] / 2, p["y"] + p["shape"][2] / 2]
            for v in vias_c:
                xs += [v["x"] - v["d"] / 2, v["x"] + v["d"] / 2]; ys += [v["y"] - v["d"] / 2, v["y"] + v["d"] / 2]
            for l in lines_c + gndlines_c:
                xs += [l["x1"], l["x2"]]; ys += [l["y1"], l["y2"]]
            x1, y1, x2, y2 = min(xs), min(ys), max(xs), max(ys)
            L = (x2 - x1) * MIL2MM; H = (y2 - y1) * MIL2MM
            pool = [(p["x"], p["y"]) for p in pads_c + gndpads_c] + [(v["x"], v["y"]) for v in vias_c]
            symfail = [(x, y) for (x, y) in pool
                       if not any(abs(qx - x) <= TOL and abs(qy - (2 * ycr - y)) <= 0.11 for (qx, qy) in pool)]
            per[ch] = dict(bboxMil=[round(x1,3), round(y1,3), round(x2,3), round(y2,3)],
                           Lmm=round(L, 3), Hmm=round(H, 3), Amm2=round(L * H, 2),
                           nPads=len(pads_c) + len(gndpads_c), nVias=len(vias_c),
                           nLines=len(lines_c) + len(gndlines_c), symFail=len(symfail),
                           symFailDetail=symfail[:4])
        gap = per["ch1"]["bboxMil"][1] - per["ch2"]["bboxMil"][3]      # ch1 在上：ch1最低铜缘 - ch2最高铜缘
        stackH = (per["ch1"]["bboxMil"][3] - per["ch2"]["bboxMil"][1]) * MIL2MM
        Lg = (per["ch1"]["bboxMil"][2] - per["ch1"]["bboxMil"][1 + 1]) * MIL2MM
        Lg = (per["ch1"]["bboxMil"][2] - per["ch1"]["bboxMil"][0]) * MIL2MM
        perScheme[sid] = dict(
            ch1=per["ch1"], ch2=per["ch2"], H=sp["H"],
            perChannelAmm2=per["ch1"]["Amm2"],
            totalSum2ch=round(per["ch1"]["Amm2"] + per["ch2"]["Amm2"], 2),
            combinedBboxAmm2=round(Lg * stackH, 2), combinedLmm=round(Lg, 3), combinedHmm=round(stackH, 3),
            interChannelCopperGapMil=round(gap, 3))

    # ---- 5) 与既有铜碰撞 ----
    newMinX = min([p["x"] - p["shape"][1] / 2 for p in pads] +
                  [v["x"] - v["d"] / 2 for v in vias] +
                  [min(l["x1"], l["x2"]) for l in lines])
    checks["collision"] = dict(newCopperMinEdgeX=round(newMinX, 2), preExistingMaxEdgeX=round(rb["preExistingMaxEdgeX"], 2),
                               clearanceMil=round(newMinX - rb["preExistingMaxEdgeX"], 1))
    checks["totals"] = rb["totals"]
    checks["silks"] = [s["t"] for s in rb["silks"]]

    out = dict(checks=checks, perScheme=perScheme)
    json.dump(out, open(f"{OUT}/aaf_layout_verify.json", "w"), ensure_ascii=False, indent=1)
    print(json.dumps(checks, ensure_ascii=False, indent=1))
    for sid, r in perScheme.items():
        print(f"{sid}: per-ch={r['perChannelAmm2']}mm2({r['ch1']['Lmm']}x{r['ch1']['Hmm']}) 两通道和={r['totalSum2ch']} "
              f"合围={r['combinedBboxAmm2']}mm2({r['combinedLmm']}x{r['combinedHmm']}) 通道铜净距={r['interChannelCopperGapMil']}mil "
              f"sym={r['ch1']['symFail']}/{r['ch2']['symFail']} pads={r['ch1']['nPads']}+{r['ch2']['nPads']} vias={r['ch1']['nVias']}+{r['ch2']['nVias']}")
        if r['ch1']['symFail'] or r['ch2']['symFail']:
            print("   sym detail:", r['ch1']['symFailDetail'], r['ch2']['symFailDetail'])
    for u in unmatched[:5]: print("unmatched pad:", u)
    for u in unmatchedv[:5]: print("unmatched via:", u)
    for u in unmatchedl[:5]: print("unmatched line endpoints:", u)

if __name__ == "__main__":
    main()
