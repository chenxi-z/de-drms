#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_四线制前端接法.py — 800×800 SCI/A4 单栏版
原图 1400×780 重排：样品 → 4×SMA → J5–J8 板内去向 + 接法要点。
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from scistyle import T, rich, head, INK, GREEN, BLUE, ORANGE, GRAY, GRID  # noqa

OUT = Path("/media/anning/data/Project/DE-DRMS/docs/design/diagram/四线制前端接法.svg")

GREEN_L = "#059669"
BLUE_L  = "#2563eb"
ORANGE_L = "#ea580c"

svg = [
    '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="800" viewBox="0 0 800 800"',
    "     font-family=\"'Noto Serif CJK SC','Noto Serif SC',serif\">",
    '<rect width="800" height="800" fill="#ffffff"/>',
]
svg += head(
    "四线制模拟前端接法",
    "J5–J8 → 偏置 / 跟随器 / 切换网络 · 感线在内、力线在外 · 绿=力线（走电流）· 蓝=感线（不走电流）",
    date="E.9 / E.3 · 2026-10-23",
)

# ============================================================
# 布局：
#   y 78–90     标题区（head()）
#   y 96–360    主图区
#     左列  x 20–110    样品（板外，宽 90）
#     中列  x 110–260   电缆 + 4×SMA + JP1/JP2
#     右列  x 260–780   J5–J8 去向框（宽 520，四块）
#   y 380–790   接法要点面板
# ============================================================

# ---------- 样品 ----------
SMP_X, SMP_Y, SMP_W, SMP_H = 24, 148, 92, 190
svg.append(f'<rect x="{SMP_X}" y="{SMP_Y}" width="{SMP_W}" height="{SMP_H}" rx="4" '
           f'fill="#fffbeb" stroke="#d97706" stroke-width="1.6" stroke-dasharray="6,4"/>')
svg.append(T(SMP_X + SMP_W/2, SMP_Y + 78, "被测", 13, "#92400e", "middle", "bold"))
svg.append(T(SMP_X + SMP_W/2, SMP_Y + 96, "样品", 13, "#92400e", "middle", "bold"))
svg.append(T(SMP_X + SMP_W/2, SMP_Y + 114, "板外", 11, "#b45309", "middle"))

# 样品两端子
A_X, A_Y = SMP_X + SMP_W, 172          # 上端 A
B_X, B_Y = SMP_X + SMP_W, 296          # 下端 B
svg.append(f'<circle cx="{A_X}" cy="{A_Y}" r="5" fill="#111827"/>')
svg.append(f'<circle cx="{B_X}" cy="{B_Y}" r="5" fill="#111827"/>')
svg.append(T(A_X - 10, A_Y - 8, "A", 11, "#94a3b8", "end"))
svg.append(T(B_X - 10, B_Y - 8, "B", 11, "#94a3b8", "end"))

# ---------- 4 只 SMA（中列）----------
SMA_X = 220
SMA_POS = [("J5", A_Y - 26, GREEN_L), ("J6", A_Y + 26, BLUE_L),
           ("J7", B_Y - 26, GREEN_L), ("J8", B_Y + 26, BLUE_L)]
# SMA y 位置：146/198, 270/322
SMA_Y = {"J5": 146, "J6": 198, "J7": 270, "J8": 322}
for j, _, c in SMA_POS:
    svg.append(f'<circle cx="{SMA_X}" cy="{SMA_Y[j]}" r="6" fill="#ffffff" stroke="{c}" stroke-width="2"/>')
# J5/J7 标签放 SMA 上方；J6/J8 标签放 SMA 右下方，避开 JP 竖虚线
svg.append(T(SMA_X, SMA_Y["J5"] - 14, "J5", 11, GREEN_L, "middle", "bold"))
svg.append(T(SMA_X, SMA_Y["J7"] - 14, "J7", 11, GREEN_L, "middle", "bold"))
svg.append(T(SMA_X + 14, SMA_Y["J6"] - 4, "J6", 11, BLUE_L, "start", "bold"))
svg.append(T(SMA_X + 14, SMA_Y["J8"] - 4, "J8", 11, BLUE_L, "start", "bold"))

# ---------- 样品 → 端子的 Kelvin 汇合 ----------
MIX_X = 170   # 电缆汇合列
# A 端：力线绿从 A 到 J5，感线蓝从 A 到 J6
svg.append(f'<line x1="{A_X}" y1="{A_Y}" x2="{MIX_X}" y2="{A_Y}" stroke="{GREEN_L}" stroke-width="2.6"/>')
svg.append(f'<line x1="{MIX_X}" y1="{A_Y}" x2="{MIX_X}" y2="{SMA_Y["J5"]}" stroke="{GREEN_L}" stroke-width="2.6"/>')
svg.append(f'<line x1="{MIX_X}" y1="{SMA_Y["J5"]}" x2="{SMA_X-6}" y2="{SMA_Y["J5"]}" stroke="{GREEN_L}" stroke-width="2.6"/>')
svg.append(f'<line x1="{MIX_X}" y1="{A_Y}" x2="{MIX_X}" y2="{SMA_Y["J6"]}" stroke="{BLUE_L}" stroke-width="2.6"/>')
svg.append(f'<line x1="{MIX_X}" y1="{SMA_Y["J6"]}" x2="{SMA_X-6}" y2="{SMA_Y["J6"]}" stroke="{BLUE_L}" stroke-width="2.6"/>')
svg.append(f'<circle cx="{MIX_X}" cy="{A_Y}" r="4" fill="#111827"/>')

# B 端：力线绿从 B 到 J7，感线蓝从 B 到 J8
svg.append(f'<line x1="{B_X}" y1="{B_Y}" x2="{MIX_X}" y2="{B_Y}" stroke="{GREEN_L}" stroke-width="2.6"/>')
svg.append(f'<line x1="{MIX_X}" y1="{B_Y}" x2="{MIX_X}" y2="{SMA_Y["J7"]}" stroke="{GREEN_L}" stroke-width="2.6"/>')
svg.append(f'<line x1="{MIX_X}" y1="{SMA_Y["J7"]}" x2="{SMA_X-6}" y2="{SMA_Y["J7"]}" stroke="{GREEN_L}" stroke-width="2.6"/>')
svg.append(f'<line x1="{MIX_X}" y1="{B_Y}" x2="{MIX_X}" y2="{SMA_Y["J8"]}" stroke="{BLUE_L}" stroke-width="2.6"/>')
svg.append(f'<line x1="{MIX_X}" y1="{SMA_Y["J8"]}" x2="{SMA_X-6}" y2="{SMA_Y["J8"]}" stroke="{BLUE_L}" stroke-width="2.6"/>')
svg.append(f'<circle cx="{MIX_X}" cy="{B_Y}" r="4" fill="#111827"/>')

# ---------- JP1 / JP2 跳线（橙虚线，竖向短接 J5↔J6 / J7↔J8）----------
for jp, y1, y2 in [("JP1", SMA_Y["J5"] + 6, SMA_Y["J6"] - 6),
                   ("JP2", SMA_Y["J7"] + 6, SMA_Y["J8"] - 6)]:
    svg.append(f'<line x1="{SMA_X}" y1="{y1}" x2="{SMA_X}" y2="{y2}" '
               f'stroke="{ORANGE_L}" stroke-width="2" stroke-dasharray="5,4"/>')
    svg.append(T(SMA_X - 12, (y1 + y2)/2 + 4, jp, 11, ORANGE_L, "end", "bold"))

# ---------- 右列：J5–J8 去向框 ----------
BOX_X, BOX_W = 270, 510
BOX_H, BOX_GAP = 56, 20
BOX_Y0 = 116   # 首块顶

DESTS = [
    ("J5", "J5 · T（力线节点）",
     "R_top/R_b 偏置 + R_ref 顶端；样品与 R_ref 共用，顶端不经开关",
     GREEN_L, "#f0fdf4", "#065f46"),
    ("J6", "J6 · V+（感线）",
     "1 kΩ + 10 nF → OPA388(T) 同相端 → AIN0P（含 BAV199 钳位）",
     BLUE_L, "#eff6ff", "#1e40af"),
    ("J7", "J7 · I−（力线回线）",
     "K1 / K2 → X（BSS138 → Rsense → GND 低边电流沉）",
     GREEN_L, "#f0fdf4", "#065f46"),
    ("J8", "J8 · V−（感线）",
     "K3 / K4 → M → 1 kΩ + 10 nF → OPA388(M) → AIN1N",
     BLUE_L, "#eff6ff", "#1e40af"),
]
BOX_CENTERS = {}
for i, (j, title, sub, sc, fill, tcol) in enumerate(DESTS):
    by = BOX_Y0 + i * (BOX_H + BOX_GAP)
    BOX_CENTERS[j] = by + BOX_H / 2
    svg.append(f'<rect x="{BOX_X}" y="{by}" width="{BOX_W}" height="{BOX_H}" rx="5" '
               f'fill="{fill}" stroke="{sc}" stroke-width="1.5"/>')
    svg.append(T(BOX_X + 14, by + 22, title, 13, tcol, "start", "bold"))
    svg.append(T(BOX_X + 14, by + 42, sub, 11, "#374151"))

# 端子 → 去向框的导线
for j, _, c in SMA_POS:
    svg.append(f'<line x1="{SMA_X+6}" y1="{SMA_Y[j]}" x2="{BOX_X-2}" y2="{BOX_CENTERS[j]}" '
               f'stroke="{c}" stroke-width="2.4"/>')

# ---------- 图注（接法要点） ----------
NOTE_X, NOTE_Y, NOTE_W, NOTE_H = 20, 400, 760, 336
svg.append(f'<rect x="{NOTE_X}" y="{NOTE_Y}" width="{NOTE_W}" height="{NOTE_H}" rx="6" '
           f'fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.2"/>')
svg.append(T(NOTE_X + 14, NOTE_Y + 24, "接法要点", 13, "#111827", "start", "bold"))

NOTES = [
    "① 力/感只在样品端子汇合：样品上端 A 接 J5（I+ 力）与 J6（V+ 感）；下端 B 接 J7（I− 力）与 J8（V− 感）。",
    "   四个夹子时，感线夹必须夹在力线夹与样品之间（感线在内、力线在外），力线夹的接触电阻才被排除。",
    "② 为什么四线制：误差 = (引线+接触电阻)/R_sample。0.5 Ω 引线在 120 kΩ 处 4 ppm ✓，",
    "   但在 10 kΩ 处 50 ppm = 吃光 0.005% 全部预算、73 Ω 处 0.68% ×。四线制下感线无电流，该误差 ≈ 0。",
    "③ 切换网络不变：K1/K2 选力线回线（样品 / R_ref）、K3/K4 选感线对（样品 / R_ref）；",
    "   零点模式全断 + CURR_DIS = 1；T 到样品与 R_ref 顶端不经开关。",
    "④ 两线制兼容：JP1 焊上（J5↔J6）、JP2 焊上（J7↔J8），只用 J5、J7 两根线；四线制时两只跳线都不焊。",
    "⑤ 屏蔽：4 只 SMA 外壳在仪器侧单端接 AGND；电缆 4 芯屏蔽（I+/I− 与 V+/V− 各双绞）。",
    "⑥ 与两线制图的关系：本图是原理级接法（J5–J8 的板内去向 + 样品处的 Kelvin 汇合）；",
    "   物理接线示意见 diagram/两电极四线制接法.svg。",
]
ny = NOTE_Y + 50
for n in NOTES:
    svg.append(T(NOTE_X + 18, ny, n, 11, "#374151"))
    ny += 21

svg.append(T(NOTE_X + 18, ny + 8,
             "注意：四线制时 OPA388(T) 的输入来自 J6（V+），不再取自 T 力线节点；OPA388(M) 仍取自 K3/K4 汇合点 M。",
             11, "#94a3b8"))
svg.append(T(NOTE_X + 18, ny + 28,
             "校准 R_ref 时靠「样品仍接、无电流 → J6 电位 = T」保证读数正确。",
             11, "#94a3b8"))
svg.append(T(NOTE_X + 18, ny + 52,
             "若要求「不接样品也能校准」，需再加一只切换开关把 T 力线接到 V+ 感线输入（K5，选配）。",
             11, "#94a3b8"))

svg.append("</svg>")
OUT.write_text("\n".join(svg), encoding="utf-8")
print("written", OUT)
