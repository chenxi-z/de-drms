#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_两电极四线制接法.py — 800×800 SCI 版式重绘"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from scistyle import T, rich, head, frame, INK, GREEN, BLUE, ORANGE, GRAY, GRID  # noqa

OUT = Path("/media/anning/data/Project/DE-DRMS/docs/design/diagram/两电极四线制接法.svg")

svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="800" height="800" viewBox="0 0 800 800"',
       '     font-family="\'Noto Serif CJK SC\',\'Noto Serif SC\',serif">',
       '<rect width="800" height="800" fill="#ffffff"/>']
svg += head("两电极测量：两线制 / 四线制兼容接法（4 × SMA）",
            "① 四线制（推荐）：4 根线 + 2 只 Kelvin 夹，JP1/JP2 不焊；② 两线制：2 根线，JP1/JP2 焊上把感线并在力线上")

GREEN_L, BLUE_L, ORANGE_L = "#059669", "#2563eb", "#ea580c"

def panel(x, y, w, h, title):
    svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.2"/>')
    svg.append(T(x + 14, y + 24, title, 13, "#111827", w="bold"))

def board(x, y):
    svg.append(f'<rect x="{x}" y="{y}" width="150" height="232" rx="5" fill="#eff6ff" stroke="#2563eb" stroke-width="1.4"/>')
    svg.append(T(x + 75, y + 20, "仪器板（俯视）", 11.5, "#2563eb", "middle", "bold"))

def term(x, y, label, color):
    svg.append(T(x - 8, y + 4, label, 11, color, "start", "bold"))
    svg.append(f'<circle cx="{x+138}" cy="{y}" r="6" fill="#ffffff" stroke="{color}" stroke-width="1.8"/>')

def sample(x, y):
    svg.append(f'<rect x="{x}" y="{y}" width="60" height="250" rx="4" fill="#fffbeb" stroke="#d97706" stroke-width="1.6" stroke-dasharray="6,4"/>')
    svg.append(T(x + 30, y + 118, "样", 12, "#92400e", "middle", "bold"))
    svg.append(T(x + 30, y + 134, "品", 12, "#92400e", "middle", "bold"))

# ================= ① 四线制 =================
panel(20, 92, 370, 348, "① 四线制（推荐）")
board(36, 130)
term(48, 168, "J5 · I+（力线）", GREEN_L)
term(48, 218, "J6 · V+（感线）", BLUE_L)
term(48, 288, "J7 · I−（力线）", GREEN_L)
term(48, 330, "J8 · V−（感线）", BLUE_L)
sample(310, 150)

# 力线/感线到 Kelvin 夹
svg.append(f'<line x1="186" y1="168" x2="270" y2="168" stroke="{GREEN_L}" stroke-width="2.6"/>')
svg.append(f'<line x1="270" y1="168" x2="270" y2="200" stroke="{GREEN_L}" stroke-width="2.6"/>')
svg.append(f'<line x1="186" y1="218" x2="270" y2="218" stroke="{BLUE_L}" stroke-width="2.6"/>')
svg.append(f'<line x1="270" y1="218" x2="270" y2="200" stroke="{BLUE_L}" stroke-width="2.6"/>')
svg.append('<circle cx="270" cy="200" r="5" fill="#111827"/>')
svg.append(f'<line x1="270" y1="200" x2="310" y2="200" stroke="{INK}" stroke-width="2"/>')
svg.append(T(270, 148, "Kelvin 夹 A", 10.5, "#b45309", "middle"))

svg.append(f'<line x1="186" y1="288" x2="270" y2="288" stroke="{GREEN_L}" stroke-width="2.6"/>')
svg.append(f'<line x1="270" y1="288" x2="270" y2="320" stroke="{GREEN_L}" stroke-width="2.6"/>')
svg.append(f'<line x1="186" y1="330" x2="270" y2="330" stroke="{BLUE_L}" stroke-width="2.6"/>')
svg.append(f'<line x1="270" y1="330" x2="270" y2="320" stroke="{BLUE_L}" stroke-width="2.6"/>')
svg.append('<circle cx="270" cy="320" r="5" fill="#111827"/>')
svg.append(f'<line x1="270" y1="320" x2="310" y2="320" stroke="{INK}" stroke-width="2"/>')
svg.append(T(270, 268, "Kelvin 夹 B", 10.5, "#b45309", "middle"))

svg.append(T(36, 386, "绿=力线（走电流）；蓝=感线", 11, "#374151"))
svg.append(T(36, 404, "同一端两线在夹子里汇合", 11, "#374151"))
svg.append(T(36, 422, "夹 A 夹一端：I+ 与 V+ 汇合；夹 B 夹另一端：I− 与 V− 汇合", 11, "#b45309"))

# ================= ② 两线制 =================
panel(410, 92, 370, 348, "② 两线制")
board(426, 130)
term(438, 168, "J5 · I+", GREEN_L)
term(438, 218, "J6 · V+", BLUE_L)
term(438, 288, "J7 · I−", GREEN_L)
term(438, 330, "J8 · V−", BLUE_L)
sample(700, 150)

# JP1/JP2 跳线
for jy, jn in [(168, "JP1"), (288, "JP2")]:
    svg.append(f'<line x1="576" y1="{jy}" x2="620" y2="{jy}" stroke="{ORANGE_L}" stroke-width="2.6"/>')
    svg.append(f'<line x1="620" y1="{jy}" x2="620" y2="{jy+50}" stroke="{ORANGE_L}" stroke-width="2.6"/>')
    svg.append(f'<line x1="620" y1="{jy+50}" x2="576" y2="{jy+50}" stroke="{ORANGE_L}" stroke-width="2.6"/>')
    svg.append(f'<ellipse cx="620" cy="{jy+25}" rx="9" ry="6" fill="{ORANGE_L}"/>')
    svg.append(T(620, jy + 66, jn, 10.5, ORANGE_L, "middle", "bold"))

svg.append(f'<line x1="576" y1="168" x2="660" y2="168" stroke="{GREEN_L}" stroke-width="2.6"/>')
svg.append(f'<line x1="660" y1="168" x2="660" y2="200" stroke="{GREEN_L}" stroke-width="2.6"/>')
svg.append(f'<line x1="660" y1="200" x2="700" y2="200" stroke="{INK}" stroke-width="2"/>')
svg.append('<circle cx="660" cy="200" r="5" fill="#111827"/>')
svg.append(T(660, 148, "夹 A", 10.5, "#b45309", "middle"))
svg.append(f'<line x1="576" y1="288" x2="660" y2="288" stroke="{GREEN_L}" stroke-width="2.6"/>')
svg.append(f'<line x1="660" y1="288" x2="660" y2="320" stroke="{GREEN_L}" stroke-width="2.6"/>')
svg.append(f'<line x1="660" y1="320" x2="700" y2="320" stroke="{INK}" stroke-width="2"/>')
svg.append('<circle cx="660" cy="320" r="5" fill="#111827"/>')
svg.append(T(660, 268, "夹 B", 10.5, "#b45309", "middle"))

svg.append(T(426, 386, "只接 J5/J7；J6/J8 空置", 11, "#374151"))
svg.append(T(426, 404, "误差 = 引线电阻 / R样", 11, "#b45309"))

# ================= 对照表 =================
panel(20, 456, 760, 330, "板内连接（端子接到哪里）与两种模式对照")
COL = [34, 130, 320, 560]
svg.append(T(COL[0], 492, "端子", 11.5, "#374151", w="bold"))
svg.append(T(COL[1], 492, "板内接到", 11.5, "#374151", w="bold"))
svg.append(T(COL[2], 492, "四线制（JP1/JP2 不焊）", 11.5, "#374151", w="bold"))
svg.append(T(COL[3], 492, "两线制（JP1/JP2 焊上）", 11.5, "#374151", w="bold"))
svg.append(f'<line x1="30" y1="500" x2="770" y2="500" stroke="{INK}" stroke-width="1"/>')

ROWS = [
    ("J5 · I+", GREEN_L, "T 节点（偏置 + 恒流源顶端）", "接样品 A 端（力）", "接样品 A 端（力 + 感）"),
    ("J6 · V+", BLUE_L, "10 nF → OPA388(T) → AIN0P", "接样品 A 端（感，与 I+ 同夹）", "空置（JP1 已并联到 J5）"),
    ("J7 · I−", GREEN_L, "K1/K2 → X（电流沉）", "接样品 B 端（力）", "接样品 B 端（力 + 感）"),
    ("J8 · V−", BLUE_L, "K3/K4 → M → OPA388(M)", "接样品 B 端（感，与 I− 同夹）", "空置（JP2 已并联到 J7）"),
]
for i, (t, c, b, f4, f2) in enumerate(ROWS):
    ry = 524 + 28 * i
    svg.append(T(COL[0], ry, t, 11, c, w="bold"))
    svg.append(T(COL[1], ry, b, 11, "#374151"))
    svg.append(T(COL[2], ry, f4, 11, "#374151"))
    svg.append(T(COL[3], ry, f2, 11, "#374151"))
    if i < len(ROWS) - 1:
        svg.append(f'<line x1="30" y1="{ry+8}" x2="770" y2="{ry+8}" stroke="{GRID}" stroke-width="1"/>')

svg.append(T(34, 654, "精度：两线制误差 = 引线+接触电阻 / R_sample —— 0.5 Ω 引线在 73 Ω 处 0.68%、10 kΩ 处 0.005%、120 kΩ 处 0.0004%；", 11, "#64748b"))
svg.append(T(34, 674, "四线制该误差 ≈ 0（感线无电流）。", 11, "#64748b"))
svg.append(T(34, 698, "K1–K4 切换网络与三种模式（测量 / 校准 / 零点）完全不受影响：K1/K2 选力线回线（样品 / R_ref），K3/K4 选感线对（样品 / R_ref）。", 11, "#64748b"))
svg.append(T(34, 722, "4 只 SMA 屏蔽层：仪器侧单端接 AGND；电缆用 4 芯屏蔽（I+/I− 双绞、V+/V− 双绞）。", 11, "#94a3b8"))
svg.append("</svg>")

OUT.write_text("\n".join(svg), encoding="utf-8")
print("written", OUT)
