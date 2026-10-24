#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_抗混叠滤波电路.py — 800×800 SCI/A4 单栏规格重绘"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scistyle import T, rich, head, INK, GREEN, BLUE, GRAY, PURPLE, F_LAT, F_CJK

W = H = 800

# ---------- 样式 ----------
CSS = f"""
  .w   {{ stroke:{INK}; stroke-width:1.6; fill:none }}
  .wg  {{ stroke:{GREEN}; stroke-width:2.4; fill:none }}
  .box {{ fill:#f1f5f9; stroke:{INK}; stroke-width:1.2 }}
  .adcbx {{ fill:#eff6ff; stroke:{BLUE}; stroke-width:1.6 }}
  .panel {{ fill:#ffffff; stroke:#cbd5e1; stroke-width:1.0 }}
  .gnd {{ stroke:{INK}; stroke-width:1.6; fill:none }}
"""

parts = []
parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
parts.append(f'<style>{CSS}</style>')
parts.append(f'<rect width="{W}" height="{H}" fill="#ffffff"/>')

# ---------- 标题 ----------
parts.extend(head("抗混叠滤波电路", "lad4r 四级无源阶梯 · 整链 R1A = 10 Ω · 2026-10-23"))

# ---------- 布局参数 ----------
# 左侧：跟随器 + 阶梯电路（x: 20~500）
# 右侧：ADC + 说明面板（x: 520~780）
# 底部：通道分配表（y: ~640~790）

# 跟随器框
fo_x, fo_w, fo_h = 14, 110, 70
fo_y1, fo_y2 = 110, 300   # 上/下跟随器

# 阶梯主线 y 坐标
line_y1, line_y2 = 155, 325

# 电阻位置（中心 x）— 拉开间距避免与电容标签冲突
r_x = [160, 245, 330, 415]
r_w, r_h = 58, 16

# 电容位置（在电阻右侧节点，即两颗电阻中点）
c_x = [202, 287, 372, 457]

# Cd 位置
cd_x = 480

# ADC 框
adc_x, adc_y, adc_w, adc_h = 520, 100, 260, 240

# ---------- 跟随器框 ----------
for y, label, sub in [(fo_y1, "OPA388 跟随器", "V_P 支路（T 点）· U5:A"),
                      (fo_y2, "OPA388 跟随器", "M 线（K3/K4）· U5:B")]:
    parts.append(f'<rect x="{fo_x}" y="{y}" width="{fo_w}" height="{fo_h}" class="box" rx="3"/>')
    parts.append(T(fo_x + fo_w/2, y + 22, label, 11, "#111827", "middle", "bold"))
    parts.append(T(fo_x + fo_w/2, y + 42, sub, 9, "#64748b", "middle"))
    parts.append(T(fo_x + fo_w/2, y + 58, "详见前端图", 8, "#94a3b8", "middle"))

# ---------- 阶梯主线 ----------
for y in (line_y1, line_y2):
    # 跟随器到 R1
    parts.append(f'<line x1="{fo_x+fo_w}" y1="{y}" x2="{r_x[0]-r_w/2}" y2="{y}" class="wg"/>')
    # R1-R2, R2-R3, R3-R4
    for i in range(3):
        x1 = r_x[i] + r_w/2
        x2 = r_x[i+1] - r_w/2
        parts.append(f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" class="wg"/>')
    # R4 到 Cd 节点
    parts.append(f'<line x1="{r_x[3]+r_w/2}" y1="{y}" x2="{cd_x}" y2="{y}" class="wg"/>')
    # Cd 到 ADC
    parts.append(f'<line x1="{cd_x}" y1="{y}" x2="{adc_x}" y2="{y}" class="wg"/>')
    # 端子白底圆
    parts.append(f'<circle cx="{fo_x+fo_w}" cy="{y}" r="3" fill="#ffffff" stroke="{INK}" stroke-width="1.5"/>')
    parts.append(f'<circle cx="{adc_x}" cy="{y}" r="3" fill="#ffffff" stroke="{BLUE}" stroke-width="1.5"/>')

# 输出标签（放在跟随器框内部右下角，避开电阻标签）
parts.append(T(fo_x + fo_w - 6, fo_y1 + fo_h - 6, "输出", 9, "#64748b", "end"))
parts.append(T(fo_x + fo_w - 6, fo_y2 + fo_h - 6, "输出", 9, "#64748b", "end"))

# ---------- 电阻 ----------
r_labels = ["R1A 10Ω", "R2 4.3Ω", "R3 8.2Ω", "R4 45.3Ω"]
r_labels_b = ["R1B 10Ω", "R2B 4.3Ω", "R3B 8.2Ω", "R4B 45.3Ω"]
for i, (x, lab, lab_b) in enumerate(zip(r_x, r_labels, r_labels_b)):
    # 上排
    parts.append(f'<rect x="{x-r_w/2}" y="{line_y1-r_h/2}" width="{r_w}" height="{r_h}" class="box"/>')
    parts.append(T(x, line_y1 - r_h/2 - 5, lab, 10, "#374151", "middle", "bold"))
    # 下排
    parts.append(f'<rect x="{x-r_w/2}" y="{line_y2-r_h/2}" width="{r_w}" height="{r_h}" class="box"/>')
    parts.append(T(x, line_y2 + r_h/2 + 12, lab_b, 10, "#374151", "middle", "bold"))

# ---------- 电容（对地）----------
c_labels = ["C1 33nF", "C2 33nF", "C3 33nF", "C4 22nF"]
c_labels_b = ["C5 33nF", "C6 33nF", "C7 33nF", "C8 22nF"]

# 上排电容（向上）
gnd_y1 = 95
for i, (x, lab) in enumerate(zip(c_x, c_labels)):
    # 垂直线：主线 → 电容 → GND 母线
    parts.append(f'<line x1="{x}" y1="{line_y1}" x2="{x}" y2="{line_y1-18}" class="w"/>')
    # 电容符号（两条横线）
    parts.append(f'<line x1="{x-10}" y1="{line_y1-18}" x2="{x+10}" y2="{line_y1-18}" stroke="{INK}" stroke-width="1.8"/>')
    parts.append(f'<line x1="{x-10}" y1="{line_y1-26}" x2="{x+10}" y2="{line_y1-26}" stroke="{INK}" stroke-width="1.8"/>')
    # 电容到 GND
    parts.append(f'<line x1="{x}" y1="{line_y1-26}" x2="{x}" y2="{gnd_y1}" class="w"/>')
    # 结点
    parts.append(f'<circle cx="{x}" cy="{line_y1}" r="3" fill="{INK}"/>')
    parts.append(f'<circle cx="{x}" cy="{gnd_y1}" r="3" fill="{INK}"/>')
    # 标签（放在电容符号右上方，与电阻标签垂直错开，避开垂直线）
    parts.append(T(x + 18, line_y1 - 45, lab, 10, PURPLE, "start", "bold"))

# 上排 GND 母线
parts.append(f'<line x1="{c_x[0]}" y1="{gnd_y1}" x2="{c_x[3]}" y2="{gnd_y1}" class="w"/>')
# GND 符号
gx = c_x[0] - 16
parts.append(f'<line x1="{c_x[0]}" y1="{gnd_y1}" x2="{gx}" y2="{gnd_y1}" class="w"/>')
parts.append(f'<line x1="{gx}" y1="{gnd_y1}" x2="{gx}" y2="{gnd_y1+8}" class="w"/>')
parts.append(f'<line x1="{gx-8}" y1="{gnd_y1+8}" x2="{gx+8}" y2="{gnd_y1+8}" stroke="{INK}" stroke-width="1.8"/>')
parts.append(f'<line x1="{gx-5}" y1="{gnd_y1+13}" x2="{gx+5}" y2="{gnd_y1+13}" stroke="{INK}" stroke-width="1.4"/>')
parts.append(f'<line x1="{gx-2}" y1="{gnd_y1+18}" x2="{gx+2}" y2="{gnd_y1+18}" stroke="{INK}" stroke-width="1.2"/>')
parts.append(T(gx - 24, gnd_y1 + 12, "GND", 9, GRAY, "end"))
parts.append(T(c_x[0] + 4, gnd_y1 - 5, "（3V3_A 参考地，同网络）", 8, "#94a3b8"))

# 下排电容（向下）
gnd_y2 = 385
for i, (x, lab) in enumerate(zip(c_x, c_labels_b)):
    parts.append(f'<line x1="{x}" y1="{line_y2}" x2="{x}" y2="{line_y2+18}" class="w"/>')
    parts.append(f'<line x1="{x-10}" y1="{line_y2+18}" x2="{x+10}" y2="{line_y2+18}" stroke="{INK}" stroke-width="1.8"/>')
    parts.append(f'<line x1="{x-10}" y1="{line_y2+26}" x2="{x+10}" y2="{line_y2+26}" stroke="{INK}" stroke-width="1.8"/>')
    parts.append(f'<line x1="{x}" y1="{line_y2+26}" x2="{x}" y2="{gnd_y2}" class="w"/>')
    parts.append(f'<circle cx="{x}" cy="{line_y2}" r="3" fill="{INK}"/>')
    parts.append(f'<circle cx="{x}" cy="{gnd_y2}" r="3" fill="{INK}"/>')
    parts.append(T(x + 18, line_y2 + 50, lab, 10, PURPLE, "start", "bold"))

# 下排 GND 母线
parts.append(f'<line x1="{c_x[0]}" y1="{gnd_y2}" x2="{c_x[3]}" y2="{gnd_y2}" class="w"/>')
parts.append(f'<line x1="{c_x[0]}" y1="{gnd_y2}" x2="{gx}" y2="{gnd_y2}" class="w"/>')
parts.append(f'<line x1="{gx}" y1="{gnd_y2}" x2="{gx}" y2="{gnd_y2+8}" class="w"/>')
parts.append(f'<line x1="{gx-8}" y1="{gnd_y2+8}" x2="{gx+8}" y2="{gnd_y2+8}" stroke="{INK}" stroke-width="1.8"/>')
parts.append(f'<line x1="{gx-5}" y1="{gnd_y2+13}" x2="{gx+5}" y2="{gnd_y2+13}" stroke="{INK}" stroke-width="1.4"/>')
parts.append(f'<line x1="{gx-2}" y1="{gnd_y2+18}" x2="{gx+2}" y2="{gnd_y2+18}" stroke="{INK}" stroke-width="1.2"/>')
parts.append(T(gx - 24, gnd_y2 + 12, "GND", 9, GRAY, "end"))
parts.append(T(c_x[0] + 4, gnd_y2 + 14, "（3V3_A 参考地）", 8, "#94a3b8"))

# ---------- Cd 差分电容 ----------
cd_y_top, cd_y_bot = line_y1, line_y2
cd_mid = (cd_y_top + cd_y_bot) / 2
parts.append(f'<line x1="{cd_x}" y1="{cd_y_top}" x2="{cd_x}" y2="{cd_mid - 14}" class="w"/>')
parts.append(f'<line x1="{cd_x}" y1="{cd_mid + 14}" x2="{cd_x}" y2="{cd_y_bot}" class="w"/>')
# 电容符号（水平）
parts.append(f'<line x1="{cd_x-12}" y1="{cd_mid-14}" x2="{cd_x+12}" y2="{cd_mid-14}" stroke="{INK}" stroke-width="1.8"/>')
parts.append(f'<line x1="{cd_x-12}" y1="{cd_mid+14}" x2="{cd_x+12}" y2="{cd_mid+14}" stroke="{INK}" stroke-width="1.8"/>')
# 结点
parts.append(f'<circle cx="{cd_x}" cy="{cd_y_top}" r="3" fill="{INK}"/>')
parts.append(f'<circle cx="{cd_x}" cy="{cd_y_bot}" r="3" fill="{INK}"/>')
# 标签
parts.append(T(cd_x - 16, cd_mid - 4, "Cd", 11, PURPLE, "end", "bold"))
parts.append(T(cd_x - 16, cd_mid + 10, "820pF", 10, PURPLE, "end", "bold"))

# ---------- ADC 框 ----------
parts.append(f'<rect x="{adc_x}" y="{adc_y}" width="{adc_w}" height="{adc_h}" class="adcbx" rx="4"/>')
parts.append(T(adc_x + adc_w/2, adc_y + 22, "ADS131A02", 13, "#1d4ed8", "middle", "bold"))
parts.append(T(adc_x + adc_w/2, adc_y + 38, "ΣΔ 24bit · 128 kSPS · OSR=32", 10, "#64748b", "middle"))

# ADC 引脚标签
parts.append(T(adc_x + 8, line_y1 + 4, "AIN0P", 11, BLUE, "start", "bold"))
parts.append(T(adc_x + 8, line_y2 + 4, "AIN0N", 11, BLUE, "start", "bold"))

# ADC 内部说明
adc_notes = [
    "内部：sinc³ 数字滤波器",
    "−3dB ≈ 33.5 kHz @OSR=32",
    "C_S = 3.5 pF（采样电容）",
    "fMOD = 4.096 MHz 吞吐",
    "采样开关：S1/S2 180°反相",
    "各占 50%（SBAS590E Fig.37/38）",
]
for i, note in enumerate(adc_notes):
    parts.append(T(adc_x + adc_w/2, adc_y + 62 + i*16, note, 9, "#334155" if i < 4 else "#94a3b8", "middle"))

# ---------- 右侧说明面板 ----------
panel_x, panel_y, panel_w, panel_h = 520, 360, 260, 190
parts.append(f'<rect x="{panel_x}" y="{panel_y}" width="{panel_w}" height="{panel_h}" class="panel" rx="4"/>')
parts.append(T(panel_x + 10, panel_y + 20, "两级采样抗混叠分工", 12, "#111827", "start", "bold"))

panel_lines = [
    ("① 无源阶梯（本图）", 10, "#334155", "bold"),
    ("守 k·fMOD 折叠 + 开关噪声", 9, "#64748b", "normal"),
    ("+ 电荷桶 + 噪声带宽", 9, "#64748b", "normal"),
    ("② 片内 sinc³（OSR=32）", 10, "#334155", "bold"),
    ("守 64k～fMOD 折叠带", 9, "#64748b", "normal"),
    ("−3dB ≈ 33.5 kHz（M1）", 9, "#64748b", "normal"),
    ("通带：DC ~ 16 kHz（扫频）", 9, "#334155", "normal"),
    ("模拟 fc = 74.6 kHz", 9, "#64748b", "normal"),
    ("D4 = 0.195 dB @16 kHz", 9, "#64748b", "normal"),
]
for i, (txt, fs, col, wt) in enumerate(panel_lines):
    parts.append(T(panel_x + 10, panel_y + 38 + i*15, txt, fs, col, "start", wt))

# ---------- 底部通道分配表 ----------
tbl_y = 580
parts.append(f'<rect x="20" y="{tbl_y}" width="760" height="170" class="panel" rx="4"/>')
parts.append(T(34, tbl_y + 22, "四线全配通道分配表", 12, "#111827", "start", "bold"))
parts.append(T(34, tbl_y + 38, "（比值/相位测量靠两线对称；通道 1 与通道 0 同构镜像）", 9, "#64748b"))

# 表头
hdr_y = tbl_y + 56
cols = [("通道", 34), ("P 线来源", 160), ("N 线来源", 320), ("阶梯（两线同构镜像）", 480), ("差分电容", 690)]
for txt, x in cols:
    parts.append(T(x, hdr_y, txt, 10, "#334155", "start", "bold"))
parts.append(f'<line x1="34" y1="{hdr_y+5}" x2="766" y2="{hdr_y+5}" stroke="#cbd5e1" stroke-width="1"/>')

# 数据行
row1_y, row2_y = hdr_y + 20, hdr_y + 38
parts.append(T(34, row1_y, "通道 0 = AIN0P−AIN0N", 10, "#334155"))
parts.append(T(160, row1_y, "V_P（T 点跟随器 U5:A）", 10, "#334155"))
parts.append(T(320, row1_y, "M（K3/K4，U5:B）", 10, "#334155"))
parts.append(T(480, row1_y, "10+4.3+8.2+45.3 Ω / 33+33+33+22 nF", 10, "#334155"))
parts.append(T(690, row1_y, "820 pF", 10, "#334155"))

parts.append(T(34, row2_y, "通道 1 = AIN1P−AIN1N", 10, "#334155"))
parts.append(T(160, row2_y, "B（Rsense 顶 U5:C）", 10, "#334155"))
parts.append(T(320, row2_y, "E（Rsense 底直连*）", 10, "#334155"))
parts.append(T(480, row2_y, "同通道 0（四线统一全配）", 10, "#334155"))
parts.append(T(690, row2_y, "820 pF", 10, "#334155"))

# 脚注
parts.append(T(34, row2_y + 20, "* E 为低阻地参考，不加跟随器（E.2）；统一全配为通道间对称，通带增益均为 1。", 8, "#94a3b8"))

# ---------- 底部图注 ----------
parts.append(T(34, 790, "图注自查：级间三路交汇均实心结点；器件端子与 ADC 引脚白底圆；Cd 跨 AIN0P/AIN0N；八颗对地电容统一接 GND 母线。", 8, "#94a3b8"))

parts.append('</svg>')

# ---------- 输出 ----------
out_path = "/media/anning/data/Project/DE-DRMS/docs/design/diagram/抗混叠滤波电路.svg"
with open(out_path, "w", encoding="utf-8") as f:
    f.write("\n".join(parts))
print(f"written: {out_path}")
