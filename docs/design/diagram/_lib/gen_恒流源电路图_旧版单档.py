#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_恒流源电路图_旧版单档.py — 800×800 SCI/A4 单栏（旧版单档 · 留档）

布局分区：
  y  20–70   标题
  y  85–310  偏置区：R1/VSET/R2 竖排 + VSET 总线（Cf、RNG·NO+Rx、Q2 关断）
  y 310–650  回路区：X → Q1 → B → Rsense → E/GND；U10 环路；U11 跟随 + AAF → AIN1P/AIN1N
  y 660–790  图注（6 条 + 位号）

绘图纪律（svg_schematic_check 门禁）：
  · 所有标签避让导线与彼此（水平/垂直估宽对齐）
  · 结点实心圆、器件端子白底圆
  · 每条导线正交，不斜穿画布
"""
from __future__ import annotations
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from scistyle import GREEN, PURPLE, T

OUT = os.path.join(HERE, "..", "恒流源电路图_旧版单档.svg")

WIRE = "#374151"
FILL_BOX = "#f1f5f9"
FILL_OP = "#eff6ff"
NOTE = "#64748b"
DIM = "#94a3b8"
TXT = "#111827"

parts: list[str] = []
add = parts.append


def L(x1, y1, x2, y2, cls="w", w=2.0):
    if cls == "gw":
        a = f'stroke="{GREEN}" stroke-width="3.0" fill="none"'
    elif cls == "p":
        a = f'stroke="{PURPLE}" stroke-width="1.6" fill="none" stroke-dasharray="5,4"'
    elif cls == "sym":
        a = f'stroke="{WIRE}" stroke-width="1.7" fill="none" stroke-linejoin="round"'
    else:
        a = f'stroke="{WIRE}" stroke-width="{w}" fill="none"'
    add(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" class="{cls}" {a}/>')


def R(x, y, w, h, fill=FILL_BOX, lw=1.7, rx=2):
    add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" '
        f'fill="{fill}" stroke="{WIRE}" stroke-width="{lw}"/>')


def dot(x, y, r=3.6):
    add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{TXT}"/>')


def term(x, y, r=4.0, stroke=WIRE, lw=1.6):
    add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="#ffffff" stroke="{stroke}" stroke-width="{lw}"/>')


def gnd(x, y, s=1.0):
    L(x, y, x, y + 7 * s, "sym")
    L(x - 9 * s, y + 7 * s, x + 9 * s, y + 7 * s, "sym")
    L(x - 5 * s, y + 12 * s, x + 5 * s, y + 12 * s, "sym")
    L(x - 2 * s, y + 16 * s, x + 2 * s, y + 16 * s, "sym")


def res_v(x, y_top, h=40, w=24):
    R(x - w / 2, y_top + 3, w, h)
    L(x, y_top, x, y_top + 3)
    L(x, y_top + 3 + h, x, y_top + 6 + h)
    return y_top + 6 + h


def res_h(x_left, y, w=36, h=18):
    R(x_left + 3, y - h / 2, w, h)
    L(x_left, y, x_left + 3, y)
    L(x_left + 3 + w, y, x_left + 6 + w, y)
    return x_left + 6 + w


def cap_v(x, y_top, plate=9, gap=6):
    L(x, y_top, x, y_top + 4)
    L(x - plate, y_top + 4, x + plate, y_top + 4, "sym")
    L(x - plate, y_top + 4 + gap, x + plate, y_top + 4 + gap, "sym")
    L(x, y_top + 4 + gap, x, y_top + 8 + gap)
    return y_top + 8 + gap


def opamp(cx, cy, size=76):
    x0, x1 = cx - size / 2, cx + size / 2
    y0, y1 = cy - size / 2, cy + size / 2
    add(f'<polygon points="{x0:.0f},{y0:.0f} {x0:.0f},{y1:.0f} {x1:.0f},{cy:.0f}" '
        f'fill="{FILL_OP}" stroke="{GREEN}" stroke-width="1.9"/>')
    return {
        "in_pos": (x0, cy - size * 0.26),
        "in_neg": (x0, cy + size * 0.26),
        "out": (x1, cy),
        "L": x0, "R": x1, "T": y0, "B": y1, "cx": cx, "cy": cy,
    }


def nmos(xc, yc, s=1.0):
    """立式增强型 NMOS（标准画法）：三段沟道短竖线 + 左侧栅极竖线；
    D 自上段端部向右侧引出再向上，S 自下段端部向右侧引出再向下（带 N 沟道箭头）。
    返回 D/S 引脚（x = xc + 16s）与 G 引脚（x = xc - 5s - 12s）。"""
    ch, gap = 7.0 * s, 3.5 * s
    r = ch + gap                       # 相邻沟道段中心距
    y_top_seg = yc - 2 * r
    y_bot_seg = yc + 2 * r
    dx = 16 * s
    for y0 in (y_top_seg, yc, y_bot_seg):
        add(f'<line x1="{xc:.1f}" y1="{y0 - ch:.1f}" x2="{xc:.1f}" y2="{y0 + ch:.1f}" '
            f'stroke="{TXT}" stroke-width="{4.0 * s:.1f}" stroke-linecap="butt"/>')
    # 栅极竖线（覆盖全部沟道段）+ 栅极引脚
    gy0, gy1 = y_top_seg - ch, y_bot_seg + ch
    add(f'<line x1="{xc - 5 * s:.1f}" y1="{gy0:.1f}" x2="{xc - 5 * s:.1f}" y2="{gy1:.1f}" '
        f'stroke="{TXT}" stroke-width="{1.9 * s:.1f}"/>')
    add(f'<line x1="{xc - 17 * s:.1f}" y1="{yc:.1f}" x2="{xc - 5 * s:.1f}" y2="{yc:.1f}" '
        f'stroke="{TXT}" stroke-width="{1.9 * s:.1f}"/>')
    # D 引出：上段顶端 → 右 → 上
    yd = y_top_seg - ch
    add(f'<line x1="{xc:.1f}" y1="{yd:.1f}" x2="{xc + dx:.1f}" y2="{yd:.1f}" stroke="{TXT}" stroke-width="{1.9 * s:.1f}"/>')
    add(f'<line x1="{xc + dx:.1f}" y1="{yd:.1f}" x2="{xc + dx:.1f}" y2="{yd - 20 * s:.1f}" stroke="{TXT}" stroke-width="{1.9 * s:.1f}"/>')
    # S 引出：下段底端 → 右 → 下（箭头指向沟道）
    ysv = y_bot_seg + ch
    add(f'<line x1="{xc:.1f}" y1="{ysv:.1f}" x2="{xc + dx:.1f}" y2="{ysv:.1f}" stroke="{TXT}" stroke-width="{1.9 * s:.1f}"/>')
    add(f'<line x1="{xc + dx:.1f}" y1="{ysv:.1f}" x2="{xc + dx:.1f}" y2="{ysv + 20 * s:.1f}" stroke="{TXT}" stroke-width="{1.9 * s:.1f}"/>')
    am = 4.6 * s
    add(f'<polygon points="{xc + 2:.1f},{ysv:.1f} {xc + 2 + am:.1f},{ysv - am * 0.72:.1f} '
        f'{xc + 2 + am:.1f},{ysv + am * 0.72:.1f}" fill="{TXT}"/>')
    return {
        "G": (xc - 17 * s, yc),
        "D": (xc + dx, yd - 20 * s),
        "S": (xc + dx, ysv + 20 * s),
        "xc": xc, "yc": yc,
    }


def sw_no_v(x, y_top, y_bot):
    """立式 NO 开关：上下触点白底圆，刀臂抬起（缺口 = 断）。"""
    term(x, y_top, r=3.2)
    term(x, y_bot, r=3.2)
    L(x, y_bot, x - 11, y_top + 5, "sym")


# ============================================================ 画布 + 标题
add('<rect x="0" y="0" width="800" height="800" fill="#ffffff"/>')
add(T(28, 36, "恒流源电路图（旧版单档 · 留档）", 20, "#111827", w="bold"))
add(T(28, 58, "Cf = 1 nF 单档（无 RNG/Rx 双档）· OPA333 + BSS138 + Rsense · 低边恒流", 12, "#475569"))
add(T(772, 36, "2026-10-23", 11, DIM, "end"))

# ============================================================ A. 偏置
VX = 60
term(VX, 102, r=4.2, stroke=GREEN, lw=1.7)
add(T(VX + 10, 106, "3.3V_A", 11.5, GREEN, w="bold"))
L(VX, 106, VX, 116)

y_r1b = res_v(VX, 116, h=40, w=24)          # → 162
add(T(VX + 14, 132, "R1 360 kΩ · 1%", 11, TXT))
L(VX, y_r1b, VX, 180)

VSET_Y = 180
dot(VX, VSET_Y)
add(T(VX + 14, 172, "VSET = 1.179 V", 11, GREEN, w="bold"))

y_r2b = res_v(VX, 188, h=40, w=24)          # → 234
add(T(VX + 14, 210, "R2 200 kΩ · 1%", 11, TXT))
L(VX, y_r2b, VX, 290)

# VSET 总线
L(VX, VSET_Y, 700, VSET_Y)

# ---- Cf 支路（x=170）
CFX = 170
L(CFX, VSET_Y, CFX, 196)
dot(CFX, VSET_Y)
y_cf = cap_v(CFX, 196)                      # → 210
L(CFX, y_cf, CFX, 290)
add(T(CFX + 14, 204, "Cf", 11.5, TXT, w="bold"))
add(T(CFX + 14, 218, "1 nF", 11, NOTE))
add(T(CFX + 14, 232, "C0G", 10.5, NOTE))

# ---- Q2 关断管（x=430）
Q2X = 430
dot(Q2X, VSET_Y)
q2 = nmos(Q2X - 24, 246, s=1.15)
L(Q2X, VSET_Y, Q2X, q2["D"][1])
L(Q2X, q2["D"][1], q2["D"][0], q2["D"][1])
L(q2["S"][0], q2["S"][1], q2["S"][0], 290)
add(T(Q2X + 26, 240, "Q2", 11, TXT, w="bold"))
add(T(Q2X + 26, 254, "BSS138L", 10, NOTE))

# Q2 栅极：CURR_DIS 自左（紫虚线）
L(q2["G"][0], q2["G"][1], 352, 240)
L(306, 240, 352, 240, "p")
add(T(306, 226, "CURR_DIS（PB10）", 11, PURPLE, w="bold"))
# Rg 1 MΩ 下拉
dot(360, 240)
y_rg = res_v(360, 244, h=24, w=20)          # → 274
L(360, y_rg, 360, 290)

# ---- GND 母线
L(60, 290, 430, 290)
for _gx in (170, 360, 424):
    dot(_gx, 290)
gnd(Q2X, 290, s=1.0)

# ============================================================ B. 回路
X_Y = 290
QX = 700
term(QX, X_Y, r=4.2, stroke=GREEN, lw=1.7)
add(T(QX - 14, X_Y - 14, "X → 链路底端（J7 样品回线）", 11, GREEN, "end", "bold"))

q1 = nmos(QX - 34, 340, s=1.15)
L(QX, X_Y, QX, q1["D"][1], "gw")
L(QX, q1["D"][1], q1["D"][0], q1["D"][1], "gw")
L(q1["S"][0], q1["S"][1], QX, q1["S"][1], "gw")
L(QX, q1["S"][1], QX, 396, "gw")
dot(QX, 396)
add(T(QX + 14, 392, "B", 12, TXT, w="bold"))
add(T(QX + 14, 330, "Q1", 11, TXT, w="bold"))
add(T(QX + 14, 344, "BSS138L", 10, NOTE))

# Rsense
y_rsb = res_v(QX, 400, h=44, w=24)           # → 448
L(QX, y_rsb, QX, 466, "gw")
add(T(QX + 34, 418, "R_sense", 11, TXT, w="bold"))
add(T(QX + 34, 432, "150 kΩ", 11, NOTE))
add(T(QX + 34, 446, "0.1%", 10.5, NOTE))

# E 节点
E_Y = 470
dot(QX, E_Y)
gnd(QX, E_Y, s=1.0)
add(T(QX - 14, E_Y + 4, "E", 12, TXT, "end", "bold"))

# ---- U10 环路
U10 = opamp(600, 340, size=76)               # +IN y=320, −IN y=360, out (638,340)
# +IN ← VSET（自总线 x=500 下沉）
L(500, VSET_Y, 500, U10["in_pos"][1])
L(500, U10["in_pos"][1], U10["in_pos"][0], U10["in_pos"][1])
dot(500, VSET_Y)
add(T(556, 314, "+IN", 10, NOTE, "end"))
# OUT → Q1 栅
L(U10["out"][0], U10["out"][1], q1["G"][0], q1["G"][1])
# −IN ← B（反馈，绕 Q1 下方走廊）
L(QX, 396, 540, 396)
L(540, 396, 540, U10["in_neg"][1])
L(540, U10["in_neg"][1], U10["in_neg"][0], U10["in_neg"][1])
add(T(556, 376, "−IN", 10, NOTE, "end"))
add(T(552, 428, "U10 OPA333", 11, TXT, "end", "bold"))

# ---- B → U11 跟随器
L(QX, 396, 730, 396)
L(730, 396, 730, 486)
L(730, 486, 520, 486)
L(520, 486, 520, 500)
U11 = opamp(600, 520, size=76)               # +IN (562,500), −IN (562,540), out (638,520)
L(520, 500, U11["in_pos"][0], U11["in_pos"][1])
add(T(556, 494, "+IN", 10, NOTE, "end"))
# 跟随器反馈
L(U11["out"][0], U11["out"][1], 650, 520)
dot(650, 520)
L(650, 520, 650, 545)
L(650, 545, 556, 545)
L(556, 545, 556, U11["in_neg"][1])
L(556, U11["in_neg"][1], U11["in_neg"][0], U11["in_neg"][1])
add(T(600, 570, "U11 OPA388(B)", 11, TXT, "middle", "bold"))

# ---- AAF → AIN1P
L(650, 520, 668, 520)
y_a1 = res_h(668, 520, w=30, h=16)           # → 704
add(T((668 + y_a1) / 2, 506, "R1A 10Ω", 10.5, TXT, "middle", "bold"))
dot(720, 520)
L(y_a1, 520, 720, 520)
add(T(720 + 8, 516, "AIN1P", 11, GREEN, w="bold"))
y_c1 = cap_v(720, 526)
gnd(720, y_c1, s=0.85)
add(T(736, 560, "AAF 四级", 10, NOTE))

# ---- E → AIN1N（Kelvin 直连）
L(QX, E_Y, 760, E_Y, "gw")
L(760, E_Y, 760, 600)
L(760, 600, 739, 600)
y_a2 = res_h(700, 600, w=30, h=16)          # 电阻在 703..733，右引线到 739
add(T((700 + y_a2) / 2, 586, "R1A 10Ω", 10.5, TXT, "middle", "bold"))
L(700, 600, 690, 600)
dot(690, 600)
add(T(682, 596, "AIN1N", 11, GREEN, "end", "bold"))
add(T(682, 612, "Kelvin 直连", 10, NOTE, "end"))
y_c2 = cap_v(690, 606)
gnd(690, y_c2, s=0.85)
add(T(710, 618, "AAF", 10, NOTE))

# ============================================================ C. 双档与指标（左下）
PX, PY, PW2, PH2 = 40, 330, 420, 250
add(f'<rect x="{PX}" y="{PY}" width="{PW2}" height="{PH2}" rx="5" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.1"/>')
add(T(PX + 14, PY + 24, "单档与关键指标", 12, TXT, w="bold"))
_rows = [
    ("激励电流", "VSET 1.179 V → I = 7.86 µA；量程 215 kΩ", TXT),
    ("Cf 取值", "1 nF C0G 单档（无 Rx 并入支路）", PURPLE),
    ("使能建立", "0.093 ms（预算 1 ms 的 10.8× 余量）", NOTE),
    ("环路 PM", "66.9–79.8°（288 步扫描），fc 258–297 kHz", NOTE),
    ("关断残流", "0.195 nA typ（≤0.6 nA @max-Rds），净省 ≈10.6 µA", NOTE),
    ("合规栈", "0.94 + 1.18 + 0.2 = 2.32 V ≤ 2.97 V − 0.5 V ✓", NOTE),
]
for i, (k, v, c) in enumerate(_rows):
    yy = PY + 48 + i * 27
    add(T(PX + 14, yy, k, 10.5, TXT, w="bold"))
    add(T(PX + 112, yy, v, 10.5, c))
add(T(PX + 14, PY + 224, "留档：本图为旧版单档（无 RNG 开关与 Rx 支路）；现行定案见《恒流源电路图》双档版", 9.5, DIM))

# ============================================================ D. 图注
NY = 642
add(f'<rect x="20" y="{NY}" width="760" height="142" rx="6" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.1"/>')
add(T(34, NY + 18, "图注与自查要点（照抄原理图时逐条核）", 11.5, TXT, w="bold"))

notes = [
    "① VSET = 3.3V_A·R2/(R1+R2) = 1.179 V → I = VSET/Rsense = 7.86 µA（单档，量程 215 kΩ）",
    "② 关断：Q2 D→VSET、S→GND，栅极 CURR_DIS(PB10) + R_g 1 MΩ 下拉；复位默认 Q2 关（激励开）；CURR_DIS=1 → VSET≈0 → I=0",
    "③ 环路：U10(+IN=VSET, −IN=B) → Q1 栅 → Rsense，I = VSET/Rsense（与 R_sample 无关）；fc 258–297 kHz、PM 66.9–79.8°、使能 0.093 ms",
    "④ 引脚：U10 = 1:OUT 2:V− 3:+IN 4:−IN 5:V+（SOT-23-5）；Q1/Q2 = 1:G 2:S 3:D（SOT-23）；V+ 接 3.3V_A，V− 接 GND",
    "⑤ ADC 侧：B → U11 跟随 → AAF → AIN1P；E → 同构 AAF → AIN1N（Kelvin，不经跟随器）；详图见《抗混叠滤波电路》",
    "⑥ 合规栈：V_sample(120 kΩ) 0.94 V + V_Rsense 1.18 V + Q1 ≈0.2 V = 2.32 V ≤ T 点(≥2.97 V) − 0.5 V ✓；关断净省 ≈10.6 µA",
]
for i, n in enumerate(notes):
    add(T(34, NY + 36 + i * 14, n, 10.5, "#374151"))
add(T(34, NY + 36 + 6 * 14 + 6,
      "位号：U10=OPA333 · Q1=恒流管 BSS138L · Q2=关断管 BSS138L · R_sense=150 kΩ 0.1% · Cf=1 nF C0G（单档）",
      10, DIM))

svg = (
    f'<svg xmlns="http://www.w3.org/2000/svg" width="800" height="800" '
    f'viewBox="0 0 800 800" font-family="\'Noto Serif CJK SC\',\'Noto Serif SC\',serif">\n'
    + "\n".join(parts) + "\n</svg>\n"
)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(svg)
print("OK ->", OUT)
