#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_抗混叠滤波电路_k3b三级.py — 800×800 SCI/A4 单栏规格重绘（k3b 三级 · BOM 简化备选）"""
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
  .pro {{ fill:#ecfdf5; stroke:#059669; stroke-width:1.2 }}
  .con {{ fill:#fef2f2; stroke:#DC2626; stroke-width:1.2 }}
"""

parts = []
parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
parts.append(f'<style>{CSS}</style>')
parts.append(f'<rect width="{W}" height="{H}" fill="#ffffff"/>')

# ---------- 标题 ----------
parts.extend(head(
    "抗混叠滤波电路（k3b 三级 · BOM 简化备选）",
    "每线 7.5Ω+82nF → 6.04Ω+56nF → 13.7Ω+22nF（对地 C0G）+ 末级 12nF 差分",
    date="2026-10-22 · aaf_k3b_c9hard"))
parts.append(T(766, 64, "fMOD = 4.096 MHz · MCLK = 16.384 MHz", 11, "#94a3b8", "end"))

# ---------- 布局 ----------
# 左：跟随器 (x 14~110)；阶梯 (x 110~510)；Cd (x 510)；ADC (x 560~786)
# 上/下主线 y = 165 / 335；GND 母线 y = 100 / 400
fo_x, fo_w, fo_h = 14, 96, 64
fo_y1, fo_y2 = 125, 305

line_y1, line_y2 = 165, 335
r_x = [170, 265, 360]         # 三级电阻中心
r_w, r_h = 56, 16
c_x = [218, 313, 408]         # 三级对地电容节点（电阻间）
cd_x = 470                    # 差分电容
adc_x, adc_y, adc_w, adc_h = 560, 100, 226, 340

gnd_y1, gnd_y2 = 100, 400

# ---------- 跟随器框 ----------
for y, sub in [(fo_y1, "T 点 · U5:A"),
               (fo_y2, "M 线 · U5:B")]:
    parts.append(f'<rect x="{fo_x}" y="{y}" width="{fo_w}" height="{fo_h}" class="box" rx="3"/>')
    parts.append(T(fo_x + fo_w/2, y + 20, "OPA388", 12, "#111827", "middle", "bold"))
    parts.append(T(fo_x + fo_w/2, y + 36, "跟随器", 11, "#111827", "middle"))
    parts.append(T(fo_x + fo_w/2, y + 52, sub, 10, "#64748b", "middle"))
# R1 兼任说明
parts.append(T(fo_x + fo_w/2, fo_y1 + fo_h + 12, "R1 兼任容性负载隔离", 9, "#94a3b8", "middle"))
parts.append(T(fo_x + fo_w/2, fo_y2 - 8, "R4 同左", 9, "#94a3b8", "middle"))

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
r_labels  = ["R1 7.5Ω",  "R2 6.04Ω",  "R3 13.7Ω"]
r_labels_b = ["R4 7.5Ω", "R5 6.04Ω",  "R6 13.7Ω"]
for x, lab, lab_b in zip(r_x, r_labels, r_labels_b):
    parts.append(f'<rect x="{x-r_w/2}" y="{line_y1-r_h/2}" width="{r_w}" height="{r_h}" class="box"/>')
    parts.append(T(x, line_y1 - r_h/2 - 5, lab, 11, "#374151", "middle", "bold"))
    parts.append(f'<rect x="{x-r_w/2}" y="{line_y2-r_h/2}" width="{r_w}" height="{r_h}" class="box"/>')
    parts.append(T(x, line_y2 + r_h/2 + 14, lab_b, 11, "#374151", "middle", "bold"))

# ---------- 对地电容（上排向上、下排向下） ----------
c_labels   = ["C1 82nF", "C2 56nF", "C3 22nF"]
c_labels_b = ["C4 82nF", "C5 56nF", "C6 22nF"]

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
parts.append(T(cd_x - 15, cd_mid - 2, "Cd", 12, PURPLE, "end", "bold"))
parts.append(T(cd_x - 15, cd_mid + 14, "12nF", 11, PURPLE, "end", "bold"))

# ---------- ADC 框 ----------
parts.append(f'<rect x="{adc_x}" y="{adc_y}" width="{adc_w}" height="{adc_h}" class="adcbx" rx="4"/>')
parts.append(T(adc_x + adc_w/2, adc_y + 22, "ADS131A02", 13, "#1d4ed8", "middle", "bold"))
parts.append(T(adc_x + adc_w/2, adc_y + 40, "ΣΔ 24bit · 128 kSPS · OSR=32", 11, "#64748b", "middle"))

parts.append(T(adc_x + 8, line_y1 - 8, "AIN0P", 11, BLUE, "start", "bold"))
parts.append(T(adc_x + 8, line_y2 - 8, "AIN0N", 11, BLUE, "start", "bold"))

# 实测数据（放在两条引脚线之间，避开引脚标签）
adc_notes = [
    (11, "#334155", "bold",   "实测（k3b FIN · OPA388）"),
    (11, "#334155", "normal", "fc 78.4 kHz · D4 0.190 dB"),
    (11, "#334155", "normal", "D1 83.9 · D2 77.6 dB"),
    (11, "#334155", "normal", "D3 131.7 dB · D8 95.4 dB"),
    (11, "#334155", "normal", "PM 57.0° · C9wc 4.85 dB"),
    (11, "#334155", "normal", "D5 28.4 µs（600 kΩ）"),
    (11, "#334155", "normal", "D7 σ 0.006 dB（MC30）"),
    (11, "#64748b", "normal", "C_S = 3.5 pF（采样电容）"),
    (11, "#64748b", "normal", "fMOD = 4.096 MHz 吞吐"),
]
ny = adc_y + 92
for fs, col, wt, txt in adc_notes:
    parts.append(T(adc_x + adc_w/2, ny, txt, fs, col, "middle", wt))
    ny += 18
parts.append(T(adc_x + adc_w/2, adc_y + adc_h - 30, "采样开关 S1/S2 180°反相", 11, "#94a3b8", "middle"))
parts.append(T(adc_x + adc_w/2, adc_y + adc_h - 14, "各占 50%（SBAS590E）", 11, "#94a3b8", "middle"))

# ---------- 通道 1 同构镜像说明 ----------
parts.append(T(adc_x + 8, adc_y + adc_h + 18, "通道 1 同构镜像（四线全配）", 11, GRAY))

# ---------- 优点/缺点面板 ----------
pnl_y = 480
pnl_h = 110
parts.append(f'<rect x="14" y="{pnl_y}" width="376" height="{pnl_h}" class="pro" rx="4"/>')
parts.append(T(24, pnl_y + 20, "优（对比 lad4r 四级定案）", 12, "#047857", "start", "bold"))
pro_lines = [
    "· 13 件/通道对，比定案少 4 件",
    "· C9 余量全场最好（最坏 4.85 dB，余 1.15 dB）",
    "· 配对 CMRR 95.4 dB 略高",
    "· 建立 28.4 µs 与四级相当 · PM 57.0° 过门",
]
for i, s in enumerate(pro_lines):
    parts.append(T(24, pnl_y + 40 + i*17, s, 11, "#047857"))

parts.append(f'<rect x="404" y="{pnl_y}" width="382" height="{pnl_h}" class="con" rx="4"/>')
parts.append(T(414, pnl_y + 20, "缺（进 BOM 前必须清）", 12, "#b91c1c", "start", "bold"))
con_lines = [
    "· D1 83.9 dB 裕量薄（线 80，余 3.9 dB）",
    "· R−1%/C−5% 负角 fc 出窗 3.6%",
    "· C1 82 nF 超 47 nF，SRF 未核",
    "  须改 0603 或 10n∥68n 后方可进 BOM",
]
for i, s in enumerate(con_lines):
    parts.append(T(414, pnl_y + 40 + i*17, s, 11, "#b91c1c"))

# ---------- 设计要点 ----------
pt_y = 606
parts.append(f'<rect x="14" y="{pt_y}" width="772" height="150" class="panel" rx="4"/>')
parts.append(T(24, pt_y + 20, "设计要点（k3b FIN · 全部 ltspice-sim 实测）", 12, "#111827", "start", "bold"))
pt_lines = [
    "1. 三级无源 RC 阶梯 + 末级差分 Cd；跟随器只缓冲不进环路；R1 兼任容性负载隔离。",
    "2. 件数口径：每线 3R+3C、两线 + Cd = 13 件/通道对；R 全 E96，C 82/56/22 nF 全 E12。",
    "3. R·C 乘积配对同定案（不配对 CMRR 掉到 48 dB）；Cd=12 nF 是 D4 杠杆（22→12 使 0.285→0.190）。",
    "4. 十维全过线：D1 83.9 / D2 77.6 / D3 131.7 / D4 0.190 / D5 28.4 / D8 95.4 / PM 57.0°。",
    "5. 回退关系：定案 = lad4r 四级（《抗混叠滤波电路》）；本图为 BOM 简化备选。",
]
for i, s in enumerate(pt_lines):
    parts.append(T(24, pt_y + 42 + i*18, s, 11, "#334155"))

# ---------- 图注自查 ----------
parts.append(T(24, 780, "图注自查：级间三路交汇实心结点；器件端子/ADC 引脚白底圆；Cd 跨 AIN0P/AIN0N；六颗对地电容统一接 GND 母线；绿色主干 = 差分测量路径。", 11, "#94a3b8"))

parts.append('</svg>')

out_path = "/media/anning/data/Project/DE-DRMS/docs/design/diagram/抗混叠滤波电路_k3b三级.svg"
with open(out_path, "w", encoding="utf-8") as f:
    f.write("\n".join(parts))
print(f"written: {out_path}")
