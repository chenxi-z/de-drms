#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_抗混叠滤波电路_一阶.py — 800×800 SCI/A4 单栏规格重绘
一阶紧凑备选：47 Ω + 47 nF + Cd 820 pF（5 件/通道对）
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scistyle import T, rich, head, INK, GREEN, BLUE, GRAY, PURPLE, RED, F_LAT, F_CJK

W = H = 800

CSS = f"""
  .w   {{ stroke:{INK}; stroke-width:1.6; fill:none }}
  .wg  {{ stroke:{GREEN}; stroke-width:2.4; fill:none }}
  .box {{ fill:#f1f5f9; stroke:{INK}; stroke-width:1.2 }}
  .adcbx {{ fill:#eff6ff; stroke:{BLUE}; stroke-width:1.6 }}
  .panel {{ fill:#ffffff; stroke:#cbd5e1; stroke-width:1.0 }}
  .pro {{ fill:#ecfdf5; stroke:{GREEN}; stroke-width:1.0 }}
  .con {{ fill:#fef2f2; stroke:{RED}; stroke-width:1.0 }}
"""

parts = []
parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
parts.append(f'<style>{CSS}</style>')
parts.append(f'<rect width="{W}" height="{H}" fill="#ffffff"/>')

# ---------- 标题 ----------
parts.extend(head("抗混叠滤波电路（一阶 · 布局最紧凑）",
                  "47Ω + 47nF（对地 C0G）+ 820pF 差分 · 5 件/通道对 · 真实 OPA388 模型实测"))

# ---------- 布局参数 ----------
# 左侧：跟随器 (x: 14~124)
# 中间：一阶 RC (x: 124~500)
# 右侧：ADC (x: 510~780)
# 主线 y: 上 190，下 360

fo_x, fo_w, fo_h = 14, 110, 60
fo_y1, fo_y2 = 160, 330
line_y1, line_y2 = 190, 360

# 一阶 RC：一颗电阻 + 一颗对地电容
r_cx = 250          # 电阻中心 x
r_w, r_h = 60, 18
c_cx = 360          # 电容节点 x
cd_x = 470          # 差分 Cd 位置

# ADC 框
adc_x, adc_y, adc_w, adc_h = 520, 130, 260, 320

# ---------- 跟随器框 ----------
for y, label, sub in [(fo_y1, "OPA388 跟随器", "V_P 支路 · U5:A"),
                      (fo_y2, "OPA388 跟随器", "M 线 · U5:B")]:
    parts.append(f'<rect x="{fo_x}" y="{y}" width="{fo_w}" height="{fo_h}" class="box" rx="3"/>')
    parts.append(T(fo_x + fo_w/2, y + 22, label, 11, "#111827", "middle", "bold"))
    parts.append(T(fo_x + fo_w/2, y + 40, sub, 9, "#64748b", "middle"))
    parts.append(T(fo_x + fo_w/2, y + 54, "R 兼任容性负载隔离", 8, "#94a3b8", "middle"))

# ---------- 主线（差分对）----------
for y in (line_y1, line_y2):
    # 跟随器 → R
    parts.append(f'<line x1="{fo_x+fo_w}" y1="{y}" x2="{r_cx-r_w/2}" y2="{y}" class="wg"/>')
    # R → C 节点
    parts.append(f'<line x1="{r_cx+r_w/2}" y1="{y}" x2="{c_cx}" y2="{y}" class="wg"/>')
    # C 节点 → Cd 节点
    parts.append(f'<line x1="{c_cx}" y1="{y}" x2="{cd_x}" y2="{y}" class="wg"/>')
    # Cd → ADC
    parts.append(f'<line x1="{cd_x}" y1="{y}" x2="{adc_x}" y2="{y}" class="wg"/>')
    # 端子白底圆
    parts.append(f'<circle cx="{fo_x+fo_w}" cy="{y}" r="3" fill="#ffffff" stroke="{INK}" stroke-width="1.5"/>')
    parts.append(f'<circle cx="{adc_x}" cy="{y}" r="3" fill="#ffffff" stroke="{BLUE}" stroke-width="1.5"/>')

# ---------- 电阻 ----------
parts.append(f'<rect x="{r_cx-r_w/2}" y="{line_y1-r_h/2}" width="{r_w}" height="{r_h}" class="box"/>')
parts.append(T(r_cx, line_y1 - r_h/2 - 6, "R1 47Ω", 11, "#374151", "middle", "bold"))
parts.append(f'<rect x="{r_cx-r_w/2}" y="{line_y2-r_h/2}" width="{r_w}" height="{r_h}" class="box"/>')
parts.append(T(r_cx, line_y2 + r_h/2 + 14, "R2 47Ω", 11, "#374151", "middle", "bold"))

# ---------- 上排对地电容 C1 ----------
gnd_y1 = 130
parts.append(f'<line x1="{c_cx}" y1="{line_y1}" x2="{c_cx}" y2="{line_y1-20}" class="w"/>')
parts.append(f'<line x1="{c_cx-11}" y1="{line_y1-20}" x2="{c_cx+11}" y2="{line_y1-20}" stroke="{INK}" stroke-width="1.8"/>')
parts.append(f'<line x1="{c_cx-11}" y1="{line_y1-28}" x2="{c_cx+11}" y2="{line_y1-28}" stroke="{INK}" stroke-width="1.8"/>')
parts.append(f'<line x1="{c_cx}" y1="{line_y1-28}" x2="{c_cx}" y2="{gnd_y1}" class="w"/>')
parts.append(f'<circle cx="{c_cx}" cy="{line_y1}" r="3.2" fill="{INK}"/>')
parts.append(f'<circle cx="{c_cx}" cy="{gnd_y1}" r="3.2" fill="{INK}"/>')
parts.append(T(c_cx + 18, line_y1 - 40, "C1 47nF", 11, PURPLE, "start", "bold"))

# 上排 GND 符号
gx = c_cx - 36
parts.append(f'<line x1="{c_cx}" y1="{gnd_y1}" x2="{gx}" y2="{gnd_y1}" class="w"/>')
parts.append(f'<line x1="{gx}" y1="{gnd_y1}" x2="{gx}" y2="{gnd_y1+8}" class="w"/>')
parts.append(f'<line x1="{gx-9}" y1="{gnd_y1+8}" x2="{gx+9}" y2="{gnd_y1+8}" stroke="{INK}" stroke-width="1.8"/>')
parts.append(f'<line x1="{gx-6}" y1="{gnd_y1+13}" x2="{gx+6}" y2="{gnd_y1+13}" stroke="{INK}" stroke-width="1.4"/>')
parts.append(f'<line x1="{gx-3}" y1="{gnd_y1+18}" x2="{gx+3}" y2="{gnd_y1+18}" stroke="{INK}" stroke-width="1.2"/>')
parts.append(T(gx - 14, gnd_y1 + 12, "GND", 9, GRAY, "end"))
parts.append(T(c_cx + 8, gnd_y1 - 5, "（3V3_A 参考地，同网络）", 8, "#94a3b8"))

# ---------- 下排对地电容 C2 ----------
gnd_y2 = 420
parts.append(f'<line x1="{c_cx}" y1="{line_y2}" x2="{c_cx}" y2="{line_y2+20}" class="w"/>')
parts.append(f'<line x1="{c_cx-11}" y1="{line_y2+20}" x2="{c_cx+11}" y2="{line_y2+20}" stroke="{INK}" stroke-width="1.8"/>')
parts.append(f'<line x1="{c_cx-11}" y1="{line_y2+28}" x2="{c_cx+11}" y2="{line_y2+28}" stroke="{INK}" stroke-width="1.8"/>')
parts.append(f'<line x1="{c_cx}" y1="{line_y2+28}" x2="{c_cx}" y2="{gnd_y2}" class="w"/>')
parts.append(f'<circle cx="{c_cx}" cy="{line_y2}" r="3.2" fill="{INK}"/>')
parts.append(f'<circle cx="{c_cx}" cy="{gnd_y2}" r="3.2" fill="{INK}"/>')
parts.append(T(c_cx + 18, line_y2 + 46, "C2 47nF", 11, PURPLE, "start", "bold"))

# 下排 GND 符号
parts.append(f'<line x1="{c_cx}" y1="{gnd_y2}" x2="{gx}" y2="{gnd_y2}" class="w"/>')
parts.append(f'<line x1="{gx}" y1="{gnd_y2}" x2="{gx}" y2="{gnd_y2+8}" class="w"/>')
parts.append(f'<line x1="{gx-9}" y1="{gnd_y2+8}" x2="{gx+9}" y2="{gnd_y2+8}" stroke="{INK}" stroke-width="1.8"/>')
parts.append(f'<line x1="{gx-6}" y1="{gnd_y2+13}" x2="{gx+6}" y2="{gnd_y2+13}" stroke="{INK}" stroke-width="1.4"/>')
parts.append(f'<line x1="{gx-3}" y1="{gnd_y2+18}" x2="{gx+3}" y2="{gnd_y2+18}" stroke="{INK}" stroke-width="1.2"/>')
parts.append(T(gx - 14, gnd_y2 + 12, "GND", 9, GRAY, "end"))

# ---------- Cd 差分电容 ----------
cd_mid = (line_y1 + line_y2) / 2
parts.append(f'<line x1="{cd_x}" y1="{line_y1}" x2="{cd_x}" y2="{cd_mid-14}" class="w"/>')
parts.append(f'<line x1="{cd_x}" y1="{cd_mid+14}" x2="{cd_x}" y2="{line_y2}" class="w"/>')
parts.append(f'<line x1="{cd_x-13}" y1="{cd_mid-14}" x2="{cd_x+13}" y2="{cd_mid-14}" stroke="{INK}" stroke-width="1.8"/>')
parts.append(f'<line x1="{cd_x-13}" y1="{cd_mid+14}" x2="{cd_x+13}" y2="{cd_mid+14}" stroke="{INK}" stroke-width="1.8"/>')
parts.append(f'<circle cx="{cd_x}" cy="{line_y1}" r="3.2" fill="{INK}"/>')
parts.append(f'<circle cx="{cd_x}" cy="{line_y2}" r="3.2" fill="{INK}"/>')
parts.append(T(cd_x - 18, cd_mid - 4, "Cd", 12, PURPLE, "end", "bold"))
parts.append(T(cd_x - 18, cd_mid + 12, "820pF", 11, PURPLE, "end", "bold"))

# ---------- ADC 框 ----------
parts.append(f'<rect x="{adc_x}" y="{adc_y}" width="{adc_w}" height="{adc_h}" class="adcbx" rx="4"/>')
parts.append(T(adc_x + adc_w/2, adc_y + 22, "ADS131A02", 13, "#1d4ed8", "middle", "bold"))
parts.append(T(adc_x + adc_w/2, adc_y + 40, "ΣΔ 24bit · 128 kSPS · OSR=32", 10, "#64748b", "middle"))

# ADC 引脚标签
parts.append(T(adc_x + 10, line_y1 + 4, "AIN0P", 11, BLUE, "start", "bold"))
parts.append(T(adc_x + 10, line_y2 + 4, "AIN0N", 11, BLUE, "start", "bold"))

# ADC 内部说明（一阶实测数据）
adc_notes = [
    ("内部：sinc³ + C_S = 3.5 pF", 10, "#334155"),
    ("fMOD = 4.096 MHz 吞吐", 10, "#334155"),
    ("", 6, "#334155"),
    ("实测（FO1 47Ω/47nF）：", 10, "#334155"),
    ("fc 72.3 kHz · D4 0.230 dB", 10, "#64748b"),
    ("D1 −40.7 · D2 −46.4 dB", 10, "#64748b"),
    ("D3 −62.7 dB（均未过线）", 10, "#64748b"),
    ("PM 98.6°@2.8 MHz · C9 +1.4 dB", 10, "#64748b"),
    ("建立 ≈ 21 µs（全场最快）", 10, "#64748b"),
    ("", 6, "#94a3b8"),
    ("采样开关 S1/S2 180° 反相", 9, "#94a3b8"),
    ("各占 50%（SBAS590E）", 9, "#94a3b8"),
]
for i, (note, fs, col) in enumerate(adc_notes):
    if note:
        parts.append(T(adc_x + adc_w/2, adc_y + 62 + i*17, note, fs, col, "middle"))

# ---------- 中部注释：通道 0 说明 ----------
parts.append(T(34, 90, "通道 0（AIN0P − AIN0N）；通道 1 同构镜像", 12, "#111827", "start", "bold"))

# ---------- 底部：优缺点面板 ----------
panel_y = 490
panel_h = 130
parts.append(f'<rect x="20" y="{panel_y}" width="760" height="{panel_h}" class="panel" rx="4"/>')
parts.append(T(34, panel_y + 22, "方案优缺点（对比 lad4r 四级定案 / k3b 三级 / B 案三级）", 12, "#111827", "start", "bold"))

# 优点子面板
pro_x, pro_y, pro_w, pro_h = 34, panel_y + 32, 360, 88
parts.append(f'<rect x="{pro_x}" y="{pro_y}" width="{pro_w}" height="{pro_h}" class="pro" rx="3"/>')
parts.append(T(pro_x + 10, pro_y + 18, "优", 11, "#047857", "start", "bold"))
pro_lines = [
    "5 件/通道对（定案 17 件）",
    "布局面积约 1/3 · 免配对工序",
    "建立 21 µs 全场最快",
    "PM 98.6° 全场最厚 · C9 仅 +1.4 dB",
    "D4 0.230 dB 与定案相当",
]
for i, t in enumerate(pro_lines):
    parts.append(T(pro_x + 10, pro_y + 34 + i*11, t, 10, "#047857"))

# 缺点子面板
con_x, con_y, con_w, con_h = 406, panel_y + 32, 360, 88
parts.append(f'<rect x="{con_x}" y="{con_y}" width="{con_w}" height="{con_h}" class="con" rx="3"/>')
parts.append(T(con_x + 10, con_y + 18, "缺", 11, "#b91c1c", "start", "bold"))
con_lines = [
    "D1 −40.7 dB（线 80）",
    "D2 −46.4 dB（线 60）",
    "D3 −62.7 dB（线 100）三项全不过线",
    "fMOD 折叠带防护弱",
    "Cd 加大到 12n 也仅 −44 dB（物理上限 ≈−45 dB）",
]
for i, t in enumerate(con_lines):
    parts.append(T(con_x + 10, con_y + 34 + i*11, t, 10, "#b91c1c"))

# ---------- 底部：适用边界 ----------
bnd_y = 640
parts.append(f'<rect x="20" y="{bnd_y}" width="760" height="120" class="panel" rx="4"/>')
parts.append(T(34, bnd_y + 20, "适用边界与设计要点", 12, "#111827", "start", "bold"))
bnd_lines = [
    "1. 适用：准静态/低频测量（信号带宽 ≤ kHz 级）且布局极端受限时；",
    "    16 kHz 扫频相位/幅值仍可用（D4 0.230 dB），但 fMOD 折叠防线只剩 sinc³。",
    "2. 一阶衰减天花板 ≈ −45 dB：FO2（33Ω+68n）D1 −42.3；FO3（22Ω+100n）D1 −44.3；",
    "    FO1c（Cd 12n）D1 −44.0 但 D4 → 0.469 dB 贴 0.5 线——加容不解决。",
    "3. R·C 配对可免（比值抵消）；R=47Ω ≥ 10Ω 阻尼门；C 47nF 免 SRF 专项核查。",
]
for i, t in enumerate(bnd_lines):
    parts.append(T(34, bnd_y + 38 + i*13, t, 10, "#334155"))

# ---------- 底部图注 ----------
parts.append(T(34, 786, "图注自查：结点实心圆 / 端子白底圆；Cd 跨 AIN0P/AIN0N；对地电容接 GND 母线；绿色 = 差分测量路径。",
               8, "#94a3b8"))

parts.append('</svg>')

out_path = "/media/anning/data/Project/DE-DRMS/docs/design/diagram/抗混叠滤波电路_一阶.svg"
with open(out_path, "w", encoding="utf-8") as f:
    f.write("\n".join(parts))
print(f"written: {out_path}")
