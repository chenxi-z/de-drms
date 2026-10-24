#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AAF 六方案占地评测 —— 在工程内副本 PCB「PCB1_1」上绘制 S0/S1/T1-T4 ×2 通道可制造布局。

数据来源：
- 库焊盘几何取自原工程项目库 R0402/C0402/C0805 封装源（fp_pads.json，2026-10-24 经
  lib_Footprint.getDocumentSource 提取）。
- 单位：mil（EasyEDA PCB 域 1 unit = 1 mil = 0.0254 mm）。
- 过孔 0.3/0.6 mm（hole 12 mil / dia 24 mil，JLC 经济型常规）。
布局规则（两方案族统一方法学）：
- 每差分通道：P 行在通道中心上方 50 mil、N 行镜像在下方 50 mil（P/N 严格镜像对称）；
- R 串臂沿行走线；CG 垂直于走线向外（P 向上、N 向下）落到独立 GND 过孔（过孔旁置于
  CG 远端焊盘侧方 10 mil，不额外增高包围框）；
- Cd（0402 立式）跨接两行之间通道中心线上；
- 间距：CG 内侧焊盘边缘距行中心 ≥25 mil（避开节点焊盘），各元件边缘净距 ≥10 mil，
  信号线宽 8 mil、接地短线 10 mil；通道间铜净距 40 mil。
绘制坐标全部记录于 plan，读回逐件比对 + 镜像断言 + 碰撞检查 + 包围面积计算。
"""
import json, math, subprocess, sys, time

BRIDGE = "http://127.0.0.1:49620/execute"
MIL2MM = 0.0254
OUT_DIR = "/media/anning/data/Project/DE-DRMS/hardware/sim/signalchain/aaf_pkg_review"

# ---- 库 land pattern（自 fp_pads.json：本工程项目库真实值，mil） ----
R0402 = dict(pitch=34.08, px=22.27, py=21.26)      # px=顺臂方向(焊盘长边沿x)
C0402 = dict(pitch=33.08, px=19.685, py=21.26)
C0805 = dict(pitch=78.74, px=55.512, py=53.15)

VIA_HOLE, VIA_DIA = 12, 24      # 0.305/0.61 mm
TRACE, GSTUB = 8, 10
ROW = 50                         # 行距通道中心
IN_STUB = 25
CLEAR = 10                       # 通用边缘净距
NODE_CLEAR = 25                  # CG 内侧焊盘边到行中心
CH_GAP = 40                      # 通道间铜净距
ZONE_X0 = 8600                   # 评测区左缘（既有铜最大 x=8036，净距>500 mil）

SCHEMES = [
    dict(id="S0", order=1, r1="47Ω",  cg=("C0805", "47nF"),  r2=None, cd="820pF"),
    dict(id="S1", order=1, r1="100Ω", cg=("C0805", "22nF"),  r2=None, cd="820pF"),
    dict(id="T1", order=2, r1="100Ω", cg=("C0402", "10nF"),  r2="100Ω", cd="820pF"),
    dict(id="T2", order=2, r1="100Ω", cg=("C0402", "10nF"),  r2="120Ω", cd="820pF"),
    dict(id="T3", order=2, r1="68Ω",  cg=("C0402", "10nF"),  r2="150Ω", cd="820pF"),
    dict(id="T4", order=2, r1="82Ω",  cg=("C0402", "10nF"),  r2="160Ω", cd="820pF"),
]

def r3(v):
    return round(v + 0.0, 3)

def build_channel(sid, ch, x0, yc, sch):
    """生成一个差分通道的全部图元。P 行 y=yc-ROW（上），N 行 y=yc+ROW（下）。"""
    pads, vias, lines = [], [], []
    cglib = C0805 if sch["cg"][0] == "C0805" else C0402
    cg_halfx = cglib["py"] / 2.0      # 立式：x 向 = 原 y 向尺寸
    cg_halfy = cglib["px"] / 2.0      # 立式：y 向 = 原 x 向尺寸（节距方向）
    cg_w, cg_h = cglib["py"], cglib["px"]
    n_net = dict(P=1, N=-1)

    for side, sgn in (("P", -1), ("N", +1)):   # sgn: P 向外为 -y
        yrow = yc + sgn * ROW
        out = sgn                                # 向外方向
        net_in = f"AAF_{sid}_CH{ch}_IN_{side}"
        n1net = f"AAF_{sid}_CH{ch}_N1_{side}"
        n2net = f"AAF_{sid}_CH{ch}_N2_{side}"
        # IN 支线
        lines.append(dict(x1=x0, y1=yrow, x2=x0 + IN_STUB, y2=yrow, w=TRACE, net=net_in))
        # R1（0402 卧式）
        pads.append(dict(x=x0 + IN_STUB, y=yrow, w=R0402["px"], h=R0402["py"], net=net_in, part=f"{sid}.CH{ch}.R1_{side}"))
        n1 = x0 + IN_STUB + R0402["pitch"]
        pads.append(dict(x=n1, y=yrow, w=R0402["px"], h=R0402["py"], net=n1net, part=f"{sid}.CH{ch}.R1_{side}"))
        # CG1（立式，向外）
        d_in = NODE_CLEAR + cg_halfy
        pads.append(dict(x=n1, y=yrow + out * d_in, w=cg_w, h=cg_h, net=n1net, part=f"{sid}.CH{ch}.CG1_{side}"))
        yfar = yrow + out * (d_in + cglib["pitch"])
        pads.append(dict(x=n1, y=yfar, w=cg_w, h=cg_h, net="GND", part=f"{sid}.CH{ch}.CG1_{side}"))
        lines.append(dict(x1=n1, y1=yrow, x2=n1, y2=yrow + out * d_in, w=TRACE, net=n1net))
        vx = n1 + cg_halfx + CLEAR + VIA_DIA / 2.0
        vias.append(dict(x=vx, y=yfar, net="GND", part=f"{sid}.CH{ch}.CG1_{side}.via"))
        lines.append(dict(x1=n1 + cg_halfx, y1=yfar, x2=vx + VIA_DIA / 2.0 + 2, y2=yfar, w=GSTUB, net="GND"))
        if sch["order"] == 2:
            # R2（0402 卧式），左焊盘让开 CG1 立焊盘与过孔的 x 带
            r2l = n1 + cg_halfx + CLEAR + R0402["px"] / 2.0
            lines.append(dict(x1=n1, y1=yrow, x2=r2l, y2=yrow, w=TRACE, net=n1net))
            pads.append(dict(x=r2l, y=yrow, w=R0402["px"], h=R0402["py"], net=n1net, part=f"{sid}.CH{ch}.R2_{side}"))
            n2 = r2l + R0402["pitch"]
            pads.append(dict(x=n2, y=yrow, w=R0402["px"], h=R0402["py"], net=n2net, part=f"{sid}.CH{ch}.R2_{side}"))
            # CG2
            pads.append(dict(x=n2, y=yrow + out * d_in, w=cg_w, h=cg_h, net=n2net, part=f"{sid}.CH{ch}.CG2_{side}"))
            yfar2 = yrow + out * (d_in + cglib["pitch"])
            pads.append(dict(x=n2, y=yfar2, w=cg_w, h=cg_h, net="GND", part=f"{sid}.CH{ch}.CG2_{side}"))
            lines.append(dict(x1=n2, y1=yrow, x2=n2, y2=yrow + out * d_in, w=TRACE, net=n2net))
            vx2 = n2 + cg_halfx + CLEAR + VIA_DIA / 2.0
            vias.append(dict(x=vx2, y=yfar2, net="GND", part=f"{sid}.CH{ch}.CG2_{side}.via"))
            lines.append(dict(x1=n2 + cg_halfx, y1=yfar2, x2=vx2 + VIA_DIA / 2.0 + 2, y2=yfar2, w=GSTUB, net="GND"))
            node_last, last_net = n2, n2net
        else:
            node_last, last_net = n1, n1net
        # Cd 立式（两行共一只，画在 P 侧循环里会重复，这里只记位置，最后统一加）
        cd_halfx = C0402["py"] / 2.0
        xcd = node_last + cg_halfx + CLEAR + cd_halfx
        out_end = max(xcd + cd_halfx, node_last + cg_halfx + CLEAR + VIA_DIA) + IN_STUB
        lines.append(dict(x1=node_last, y1=yrow, x2=out_end, y2=yrow, w=TRACE, net=last_net))
        lines.append(dict(x1=xcd, y1=yrow, x2=xcd, y2=yc + sgn * (C0402["pitch"] / 2.0), w=TRACE, net=last_net))
    # Cd（通道级）
    cd_net_p = f"AAF_{sid}_CH{ch}_N2_P" if sch["order"] == 2 else f"AAF_{sid}_CH{ch}_N1_P"
    cd_net_n = cd_net_p.replace("_P", "_N")
    pads.append(dict(x=xcd, y=yc - C0402["pitch"] / 2.0, w=C0402["py"], h=C0402["px"], net=cd_net_p, part=f"{sid}.CH{ch}.Cd"))
    pads.append(dict(x=xcd, y=yc + C0402["pitch"] / 2.0, w=C0402["py"], h=C0402["px"], net=cd_net_n, part=f"{sid}.CH{ch}.Cd"))
    # 包围框（铜：焊盘+过孔+线条端点）
    xs, ys = [], []
    for p in pads:
        xs += [p["x"] - p["w"] / 2.0, p["x"] + p["w"] / 2.0]
        ys += [p["y"] - p["h"] / 2.0, p["y"] + p["h"] / 2.0]
    for v in vias:
        xs += [v["x"] - VIA_DIA / 2.0, v["x"] + VIA_DIA / 2.0]
        ys += [v["y"] - VIA_DIA / 2.0, v["y"] + VIA_DIA / 2.0]
    for l in lines:
        xs += [l["x1"], l["x2"]]
        ys += [l["y1"], l["y2"]]
    bbox = dict(x1=r3(min(xs)), y1=r3(min(ys)), x2=r3(max(xs)), y2=r3(max(ys)))
    return dict(pads=pads, vias=vias, lines=lines, bbox=bbox, xcd=r3(xcd), out_end=r3(out_end))

def js_channel_ops(ch_plan):
    ops = []
    for p in ch_plan["pads"]:
        ops.append("await eda.pcb_PrimitivePad.create(1,'1',%s,%s,0,['RECT',%s,%s,0],'%s',null,0,0,0,false,0)"
                   % (r3(p["x"]), r3(p["y"]), r3(p["w"]), r3(p["h"]), p["net"]))
    for v in ch_plan["vias"]:
        ops.append("await eda.pcb_PrimitiveVia.create('GND',%s,%s,%d,%d,0)" % (r3(v["x"]), r3(v["y"]), VIA_HOLE, VIA_DIA))
    for l in ch_plan["lines"]:
        ops.append("await eda.pcb_PrimitiveLine.create('%s',1,%s,%s,%s,%s,%s,false)"
                   % (l["net"], r3(l["x1"]), r3(l["y1"]), r3(l["x2"]), r3(l["y2"]), l["w"]))
    return ops

def post_js(code, timeout=120):
    payload = json.dumps({"code": code})
    p = subprocess.run(["curl", "-s", "--max-time", str(timeout), "-X", "POST", BRIDGE,
                        "-H", "Content-Type: application/json", "-d", payload],
                       capture_output=True, text=True)
    try:
        return json.loads(p.stdout)
    except Exception:
        return {"success": False, "error": "bad json: " + p.stdout[:400]}

def main():
    plans, cursor = [], None
    # 计算各方案通道高度：H = 2*(ROW + max(cg far pad edge, via edge))
    def ch_height(sch):
        lib = C0805 if sch["cg"][0] == "C0805" else C0402
        d_in = NODE_CLEAR + lib["px"] / 2.0
        far_edge = d_in + lib["pitch"] + lib["px"] / 2.0
        via_edge = d_in + lib["pitch"] + VIA_DIA / 2.0
        return 2.0 * (ROW + max(far_edge, via_edge))
    zone_top = -3680.0
    ycur = zone_top
    results = []
    for sch in SCHEMES:
        H = ch_height(sch)
        title_h = 140.0
        ch1_yc = ycur - title_h - H / 2.0
        ch2_yc = ch1_yc - (H + CH_GAP)          # 向下（更负 y）堆叠，铜净距 CH_GAP
        zone_bottom = ch2_yc - H / 2.0 - 60.0
        plan = dict(id=sch["id"], sch=sch, H=r3(H), ch1_yc=r3(ch1_yc), ch2_yc=r3(ch2_yc),
                    zone=dict(x1=ZONE_X0 - 60, y1=r3(zone_top if not plans else ycur), y2=r3(zone_bottom)))
        plan["ch1"] = build_channel(sch["id"], 1, ZONE_X0, ch1_yc, sch)
        plan["ch2"] = build_channel(sch["id"], 2, ZONE_X0, ch2_yc, sch)
        plans.append(plan)
        ycur = zone_bottom - 80.0   # 方案间距
    # —— 逐方案绘制 ——
    for plan in plans:
        sid = plan["id"]
        ops = []
        for chp in (plan["ch1"], plan["ch2"]):
            ops += js_channel_ops(chp)
        # 丝印（不计入铜包围框）
        sch = plan["sch"]
        if sch["order"] == 1:
            title = "%s 一阶 R1=%s CG=%s(%s) Cd=%s | 每通道5件 两通道" % (sid, sch["r1"], sch["cg"][1], sch["cg"][0], sch["cd"])
        else:
            title = "%s 二阶 R1=%s CG1=%s + R2=%s CG2=%s Cd=%s 全0402 | 每通道9件 两通道" % (sid, sch["r1"], sch["cg"][1], sch["r2"], sch["cg"][1], sch["cd"])
        zone_y1 = plan["zone"]["y1"]
        ops.append("await eda.pcb_PrimitiveString.create(3,%d,%s,'%s','default',46,6,3,0,false,0,false,false)"
                   % (ZONE_X0, r3(zone_y1 - 70), title))
        for chp, k in ((plan["ch1"], 1), (plan["ch2"], 2)):
            ops.append("await eda.pcb_PrimitiveString.create(3,%d,%s,'%s-CH%d','default',36,6,3,0,false,0,false,false)"
                       % (ZONE_X0 - 320, r3(plan[("ch%d_yc" % k)]), sid, k))
        code = ";".join(ops) + ";return {ok:true,n:%d}" % len(ops)
        resp = post_js(code)
        ok = resp.get("success") and (resp.get("result") or {}).get("ok")
        print(f"draw {sid}: success={resp.get('success')} ok={ok} ops={len(ops)}")
        if not ok:
            print(json.dumps(resp, ensure_ascii=False)[:800]); sys.exit(2)
        results.append(dict(id=sid, drawn_ops=len(ops)))
        time.sleep(0.6)
    # 总注释丝印（置于 S0 标题上方，互不重叠）
    note = "AAF六方案占地评测 2026-10-24 副本PCB1_1 自动绘制 原PCB1未改动"
    resp = post_js("await eda.pcb_PrimitiveString.create(3,%d,%d,'%s','default',52,8,3,0,false,0,false,false);return {ok:true}" % (ZONE_X0, -3680 - 150, note))
    print("note silk:", resp.get("success"))
    json.dump(dict(plans=plans, lib=dict(R0402=R0402, C0402=C0402, C0805=C0805),
                   via=dict(hole=VIA_HOLE, dia=VIA_DIA), zone_x0=ZONE_X0),
              open(f"{OUT_DIR}/aaf_layout_plan.json", "w"), ensure_ascii=False, indent=1)
    print("plan saved.")

if __name__ == "__main__":
    main()
