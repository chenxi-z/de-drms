#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_抗混叠滤波电路_旧B案三级.py — 800×800 SCI/A4 单栏规格重绘
旧 B 案三级 · 留档（6.19+6.04+13.7 Ω / 68+68+27 nF + Cd 12 nF，零改动回退档）
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scistyle import T, rich, head, INK, GREEN, BLUE, GRAY, PURPLE, F_LAT, F_CJK

W = H = 800

CSS = f"""
  .w   {{ stroke:{INK}; stroke-width:1.6; fill:none }}
  .wg  {{ stroke:{GREEN}; stroke-width:2.4; fill:none }}
  .box {{ fill:#f1f5f9; stroke:{INK}; stroke-width:1.2 }}
  .adcbx {{ fill:#eff6ff; stroke:{BLUE}; stroke-width:1.6 }}
  .panel {{ fill:#ffffff; stroke:#cbd5e1; stroke-width:1.0 }}
  .archive {{ fill:#fafaf9; stroke:#94a3b8; stroke-width:1.0 }}
"""

parts = []
parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
parts.append(f'<style>{CSS}</style>')
parts.append(f'<rect width="{W}" height="{H}" fill="#ffffff"/>')

# ---------- 标题 ----------
parts.extend(head(
    "抗混叠滤波电路（旧 B 案三级 · 留档）",
    "每线 6.19Ω+68nF → 6.04Ω+68nF → 13.7Ω+27nF + 末级 12nF 差分",
    date="R5 第4轮定档 · 2026-10-19"))
parts.append(T(766, 64, "fMOD = 4.096 MHz · MCLK = 16.384 MHz", 11, "#94a3b8", "end"))

# ---------- 布局 ----------
# 左：跟随器 (x 14~110)；阶梯 (x 110~510)；Cd (x 470)；ADC (x 560~786)
# 上/下主线 y = 175 / 325；GND 母线 y = 108 / 392
fo_x, fo_w, fo_h = 14, 96, 64
fo_y1, fo_y2 = 135, 295

line_y1, line_y2 = 175, 325
r_x = [170, 265, 360]         # 三级电阻中心
r_w, r_h = 56, 16
c_x = [218, 313, 408]         # 三级对地电容节点（电阻间）
cd_x = 470                    # 差分电容
adc_x, adc_y, adc_w, adc_h = 560, 108, 226, 314

gnd_y1, gnd_y2 = 108, 392

# ---------- 跟随器框 ----------
for y, sub in [(fo_y1, "T 点 · U5:A"),
               (fo_y2, "M 线 · U5:B")]:
    parts.append(f'<rect x="{fo_x}" y="{y}" width="{fo_w}" height="{fo_h}" class="box" rx="3"/>')
    parts.append(T(fo_x + fo_w/2, y + 20, "OPA388", 12, "#111827", "middle", "bold"))
    parts.append(T(fo_x + fo_w/2, y + 36, "跟随器", 11, "#111827", "middle"))
    parts.append(T(fo_x + fo_w/2, y + 52, sub, 10, "#64748b", "middle"))
parts.append(T(fo_x + fo_w/2, fo_y1 - 8, "低阻源", 10, GRAY, "middle"))
parts.append(T(fo_x + fo_w/2, fo_y2 + fo_h + 14, "R1 兼任容性负载隔离", 9, "#94a3b8", "middle"))

# ---------- 阶梯主线 ----------
for y in (line_y1, line_y2):
    parts.append(f'<line x1="{fo_x+fo_w}" y1="{y}" x2="{r_x[0]-r_w/2}" y2="{y}" class="wg"/>')
    for i in range(2):
        x1 = r_x[i] + r_w/2
        x2 = r_x[i+1] - r_w/2
        parts.append(f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" class="wg"/>')
    parts.append(f'<line x1="{r_x[2]+r_w/2}" y1="{y}" x2="{cd_x}" y2="{y}" class="wg"/>')
    parts.append(f'<line x1="{cd_x}" y1="{y}" x2="{adc_x}" y2="{y}" class="wg"/>')
    parts.append(f'<circle cx="{fo_x+fo_w}" cy="{y}" r="3" fill="#ffffff" stroke="{INK}" stroke-width="1.5"/>')
    parts.append(f'<circle cx="{adc_x}" cy="{y}" r="3" fill="#ffffff" stroke="{BLUE}" stroke-width="1.5"/>')

# ---------- 电阻 ----------
r_labels   = ["R1 6.19Ω", "R2 6.04Ω", "R3 13.7Ω"]
r_labels_b = ["R4 6.19Ω", "R5 6.04Ω", "R6 13.7Ω"]
for x, lab, lab_b in zip(r_x, r_labels, r_labels_b):
    parts.append(f'<rect x="{x-r_w/2}" y="{line_y1-r_h/2}" width="{r_w}" height="{r_h}" class="box"/>')
    parts.append(T(x, line_y1 - r_h/2 - 5, lab, 11, "#374151", "middle", "bold"))
    parts.append(f'<rect x="{x-r_w/2}" y="{line_y2-r_h/2}" width="{r_w}" height="{r_h}" class="box"/>')
    parts.append(T(x, line_y2 + r_h/2 + 14, lab_b, 11, "#374151", "middle", "bold"))

# ---------- 对地电容（上排向上、下排向下） ----------
c_labels   = ["C1 68nF", "C2 68nF", "C3 27nF"]
c_labels_b = ["C4 68nF", "C5 68nF", "C6 27nF"]

for x, lab in zip(c_x, c_labels):
    parts.append(f'<line x1="{x}" y1="{line_y1}" x2="{x}" y2="{line_y1-16}" class="w"/>')
    parts.append(f'<line x1="{x-9}" y1="{line_y1-16}" x2="{x+9}" y2="{line_y1-16}" stroke="{INK}" stroke-width="1.8"/>')
    parts.append(f'<line x1="{x-9}" y1="{line_y1-23}" x2="{x+9}" y2="{line_y1-23}" stroke="{INK}" stroke-width="1.8"/>')
    parts.append(f'<line x1="{x}" y1="{line_y1-23}" x2="{x}" y2="{gnd_y1}" class="w"/>')
    parts.append(f'<circle cx="{x}" cy="{line_y1}" r="3" fill="{INK}"/>')
    parts.append(f'<circle cx="{x}" cy="{gnd_y1}" r="3" fill="{INK}"/>')
    parts.append(T(x + 14, line_y1 - 32, lab, 11, PURPLE, "start", "bold"))

for x, lab in zip(c_x, c_labels_b):
    parts.append(f'<line x1="{x}" y1="{line_y2}" x2="{x}" y2="{line_y2+16}" class="w"/>')
    parts.append(f'<line x1="{x-9}" y1="{line_y2+16}" x2="{x+9}" y2="{line_y2+16}" stroke="{INK}" stroke-width="1.8"/>')
    parts.append(f'<line x1="{x-9}" y1="{line_y2+23}" x2="{x+9}" y2="{line_y2+23}" stroke="{INK}" stroke-width="1.8"/>')
    parts.append(f'<line x1="{x}" y1="{line_y2+23}" x2="{x}" y2="{gnd_y2}" class="w"/>')
    parts.append(f'<circle cx="{x}" cy="{line_y2}" r="3" fill="{INK}"/>')
    parts.append(f'<circle cx="{x}" cy="{gnd_y2}" r="3" fill="{INK}"/>')
    parts.append(T(x + 14, line_y2 + 40, lab, 11, PURPLE, "start", "bold"))

# ---------- GND 母线与符号 ----------
for gy in (gnd_y1, gnd_y2):
    parts.append(f'<line x1="{c_x[0]}" y1="{gy}" x2="{c_x[2]}" y2="{gy}" class="w"/>')
gx = c_x[0] - 18
parts.append(f'<line x1="{c_x[0]}" y1="{gnd_y1}" x2="{gx}" y2="{gnd_y1}" class="w"/>')
parts.append(f'<line x1="{gx}" y1="{gnd_y1}" x2="{gx}" y2="{gnd_y1+7}" class="w"/>')
parts.append(f'<line x1="{gx-8}" y1="{gnd_y1+7}"  x2="{gx+8}" y2="{gnd_y1+7}"  stroke="{INK}" stroke-width="1.8"/>')
parts.append(f'<line x1="{gx-5}" y1="{gnd_y1+11}" x2="{gx+5}" y2="{gnd_y1+11}" stroke="{INK}" stroke-width="1.4"/>')
parts.append(f'<line x1="{gx-2}" y1="{gnd_y1+15}" x2="{gx+2}" y2="{gnd_y1+15}" stroke="{INK}" stroke-width="1.2"/>')
parts.append(T(gx + 20, gnd_y1 - 6, "GND（3V3_A 参考地，同网络）", 10, GRAY))

parts.append(f'<line x1="{c_x[0]}" y1="{gnd_y2}" x2="{gx}" y2="{gnd_y2}" class="w"/>')
parts.append(f'<line x1="{gx}" y1="{gnd_y2}" x2="{gx}" y2="{gnd_y2+7}" class="w"/>')
parts.append(f'<line x1="{gx-8}" y1="{gnd_y2+7}"  x2="{gx+8}" y2="{gnd_y2+7}"  stroke="{INK}" stroke-width="1.8"/>')
parts.append(f'<line x1="{gx-5}" y1="{gnd_y2+11}" x2="{gx+5}" y2="{gnd_y2+11}" stroke="{INK}" stroke-width="1.4"/>')
parts.append(f'<line x1="{gx-2}" y1="{gnd_y2+15}" x2="{gx+2}" y2="{gnd_y2+15}" stroke="{INK}" stroke-width="1.2"/>')
parts.append(T(gx + 20, gnd_y2 + 22, "GND（3V3_A 参考地）", 10, GRAY))

# ---------- Cd 差分电容 ----------
cd_mid = (line_y1 + line_y2) / 2
parts.append(f'<line x1="{cd_x}" y1="{line_y1}" x2="{cd_x}" y2="{cd_mid-13}" class="w"/>')
parts.append(f'<line x1="{cd_x}" y1="{cd_mid+13}" x2="{cd_x}" y2="{line_y2}" class="w"/>')
parts.append(f'<line x1="{cd_x-11}" y1="{cd_mid-13}" x2="{cd_x+11}" y2="{cd_mid-13}" stroke="{INK}" stroke-width="1.8"/>')
parts.append(f'<line x1="{cd_x-11}" y1="{cd_mid+13}" x2="{cd_x+11}" y2="{cd_mid+13}" stroke="{INK}" stroke-width="1.8"/>')
parts.append(f'<circle cx="{cd_x}" cy="{line_y1}" r="3" fill="{INK}"/>')
parts.append(f'<circle cx="{cd_x}" cy="{line_y2}" r="3" fill="{INK}"/>')
parts.append(T(cd_x - 15, cd_mid - 2, "C7", 12, PURPLE, "end", "bold"))
parts.append(T(cd_x - 15, cd_mid + 14, "12nF", 11, PURPLE, "end", "bold"))

# ---------- ADC 框 ----------
parts.append(f'<rect x="{adc_x}" y="{adc_y}" width="{adc_w}" height="{adc_h}" class="adcbx" rx="4"/>')
parts.append(T(adc_x + adc_w/2, adc_y + 22, "ADS131A02", 13, "#1d4ed8", "middle", "bold"))
parts.append(T(adc_x + adc_w/2, adc_y + 40, "ΣΔ 24bit · 128 kSPS · OSR=32", 11, "#64748b", "middle"))

parts.append(T(adc_x + 8, line_y1 - 8, "AIN1P", 11, BLUE, "start", "bold"))
parts.append(T(adc_x + 8, line_y2 - 8, "AIN1N", 11, BLUE, "start", "bold"))

# ADC 内部说明（放在两条引脚线之间，避开引脚标签）
adc_notes = [
    (11, "#334155", "bold",   "内部：sinc³ 数字滤波器"),
    (11, "#334155", "normal", "−3dB ≈ 33.5 kHz @OSR=32"),
    (11, "#334155", "normal", "C_S = 3.5 pF（采样电容）"),
    (11, "#334155", "normal", "fMOD = 4.096 MHz 吞吐"),
    (11, "#64748b", "normal", "采样开关 S1/S2 180°反相"),
    (11, "#64748b", "normal", "各占 50%（SBAS590E Fig.37/38）"),
]
ny = adc_y + 70
for fs, col, wt, txt in adc_notes:
    parts.append(T(adc_x + adc_w/2, ny, txt, fs, col, "middle", wt))
    ny += 18

# 分工面板（嵌入 ADC 框下部）
div_y = adc_y + 200
parts.append(f'<line x1="{adc_x+10}" y1="{div_y}" x2="{adc_x+adc_w-10}" y2="{div_y}" stroke="#cbd5e1" stroke-width="0.8"/>')
parts.append(T(adc_x + adc_w/2, div_y + 16, "两级采样抗混叠分工", 11, "#111827", "middle", "bold"))
div_lines = [
    ("① 无源阶梯（本图）", 11, "#334155", "bold"),
    ("守 k·fMOD 折叠 + 开关噪声", 10, "#64748b", "normal"),
    ("+ 电荷桶 + 噪声带宽", 10, "#64748b", "normal"),
    ("② 片内 sinc³（OSR=32）", 11, "#334155", "bold"),
    ("守 64k～fMOD 折叠带", 10, "#64748b", "normal"),
    ("通带 DC ~ 16 kHz · fc ≈ 80 kHz", 10, "#64748b", "normal"),
]
ny2 = div_y + 34
for txt, fs, col, wt in div_lines:
    parts.append(T(adc_x + adc_w/2, ny2, txt, fs, col, "middle", wt))
    ny2 += 15

# ---------- 通道分配表 ----------
tb_y = 460
parts.append(f'<rect x="14" y="{tb_y}" width="772" height="92" class="panel" rx="4"/>')
parts.append(T(24, tb_y + 20, "通道分配（CH2 与 CH1 同构，四线全配）", 12, "#111827", "start", "bold"))
# 表头
head_y = tb_y + 40
parts.append(T(24,  head_y, "通道", 11, "#475569", "start", "bold"))
parts.append(T(150, head_y, "P 线来源", 11, "#475569", "start", "bold"))
parts.append(T(310, head_y, "N 线来源", 11, "#475569", "start", "bold"))
parts.append(T(510, head_y, "阶梯（P = N 镜像）", 11, "#475569", "start", "bold"))
parts.append(T(720, head_y, "差分电容", 11, "#475569", "start", "bold"))
parts.append(f'<line x1="24" y1="{head_y+5}" x2="776" y2="{head_y+5}" stroke="#cbd5e1" stroke-width="0.8"/>')
# CH1
r1_y = head_y + 22
parts.append(T(24,  r1_y, "CH1 = AIN1P−AIN1N", 11, "#334155"))
parts.append(T(150, r1_y, "V_P（T 点跟随器）", 11, "#334155"))
parts.append(T(310, r1_y, "M（Rsense 顶跟随器）", 11, "#334155"))
parts.append(T(510, r1_y, "6.19+6.04+13.7 Ω / 68+68+27 nF", 11, "#334155"))
parts.append(T(720, r1_y, "C7 = 12 nF", 11, "#334155"))
# CH2
r2_y = r1_y + 18
parts.append(T(24,  r2_y, "CH2 = AIN2P−AIN2N", 11, "#334155"))
parts.append(T(150, r2_y, "B（Rsense 底跟随器）", 11, "#334155"))
parts.append(T(310, r2_y, "AIN1N 参考经 RC 直连*", 11, "#334155"))
parts.append(T(510, r2_y, "同 CH1（四线统一全配）", 11, "#334155"))
parts.append(T(720, r2_y, "12 nF", 11, "#334155"))

# ---------- 设计要点 ----------
pt_y = 566
parts.append(f'<rect x="14" y="{pt_y}" width="772" height="160" class="panel" rx="4"/>')
parts.append(T(24, pt_y + 20, "设计要点（旧 B 案三级 · R5 第4轮定档口径，LTspice 实测）", 12, "#111827", "start", "bold"))
pt_lines = [
    "1. 拓扑：三级无源 RC 阶梯（fc ≈ 80 kHz）+ 末级差分 C7=12 nF；跟随器只缓冲、不进环路。",
    "2. 元件：R 全 E96 1%（6.19/6.04/13.7 Ω）；C 全 C0G/NP0（68/68/27+12 nF）；ΣR=25.93 Ω≪5 kΩ。",
    "3. R·C 乘积配对：两线异向配对，1% 单体失配下 CMRR=95.5 dB（不配对 48.5 dB）。",
    "4. C9 修复：R1 2.74→6.19 Ω，跟随器节点 peaking 10.66→4.77 dB（278.6 kHz，限 6 dB）。",
    "5. D5 最坏 30.1 µs @220 kΩ（0.01% 带）；D6a 0.64%（限 10%）；D6b 12.0 LSB ≈ 3.5 µVrms。",
    "6. DM@fMOD −84.6 / CM@fMOD −79.2 / DM@MCLK −132.6 dB；−20/+85 ℃ 漂移小于 0.001 dB。",
]
for i, s in enumerate(pt_lines):
    parts.append(T(24, pt_y + 42 + i*18, s, 11, "#334155"))

# ---------- 留档说明 ----------
ar_y = 736
parts.append(f'<rect x="14" y="{ar_y}" width="772" height="36" class="archive" rx="3"/>')
parts.append(T(24, ar_y + 20, "留档：本图为已冻结回退档，零改动；现行定案见《抗混叠滤波电路》（lad4r 四级版）。", 11, "#556070"))

# ---------- 图注自查 ----------
parts.append(T(24, 784, "图注自查：级间三路交汇实心结点；器件端子/ADC 引脚白底圆；C7 跨 AIN1P/AIN1N；六颗对地电容统一接 GND 母线。", 10, "#94a3b8"))

parts.append('</svg>')

out_path = "/media/anning/data/Project/DE-DRMS/docs/design/diagram/抗混叠滤波电路_旧B案三级.svg"
with open(out_path, "w", encoding="utf-8") as f:
    f.write("\n".join(parts))
print(f"written: {out_path}")
