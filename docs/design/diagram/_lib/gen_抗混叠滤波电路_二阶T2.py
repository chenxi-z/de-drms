#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_抗混叠滤波电路_二阶T2.py — 800×800 SCI/A4 单栏规格
二阶 T2（均衡 · 推荐）：R1 100Ω + C_G1 10nF → R2 120Ω + C_G2 10nF + C_d 820pF
每差分通道 9 件全 0402；数据源 hardware/sim/signalchain/aaf_pkg_review/REPORT.md
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
parts.extend(head("抗混叠滤波电路（二阶 T2 · 均衡 · 推荐）",
                  "100Ω+10nF → 120Ω+10nF（对地 C0G）+ 820pF 差分 · 9 件/通道 · 全 0402 · 真实 OPA388 模型实测",
                  date="2026-10-24"))

# ---------- 布局参数 ----------
# 左侧：跟随器 (x: 14~124)；中间：二阶 RC 梯形 (x: 124~500)；右侧：ADC (x: 535~780)
# 主线 y：上 190，下 360
fo_x, fo_w, fo_h = 14, 110, 60
fo_y1, fo_y2 = 160, 330
line_y1, line_y2 = 190, 360

r1_cx, r2_cx = 215, 375      # 两级电阻中心
n1_x, n2_x = 295, 455        # 节点 1（C_G1）/ 节点 2（C_G2 + C_d）
r_w, r_h = 60, 18
gnd_y1, gnd_y2 = 130, 420    # 上/下接地母线

adc_x, adc_y, adc_w, adc_h = 535, 130, 245, 320

# ---------- 跟随器框 ----------
for y, label, sub in [(fo_y1, "OPA388 跟随器", "T 线支路 · CH0:P"),
                      (fo_y2, "OPA388 跟随器", "M 线支路 · CH0:N")]:
    parts.append(f'<rect x="{fo_x}" y="{y}" width="{fo_w}" height="{fo_h}" class="box" rx="3"/>')
    parts.append(T(fo_x + fo_w/2, y + 22, label, 11, "#111827", "middle", "bold"))
    parts.append(T(fo_x + fo_w/2, y + 40, sub, 9, "#64748b", "middle"))
    parts.append(T(fo_x + fo_w/2, y + 54, "R1 兼任容性负载隔离", 8, "#94a3b8", "middle"))

# ---------- 主线（差分对）----------
for y in (line_y1, line_y2):
    # 跟随器 → R1
    parts.append(f'<line x1="{fo_x+fo_w}" y1="{y}" x2="{r1_cx-r_w/2}" y2="{y}" class="wg"/>')
    # R1 → 节点1
    parts.append(f'<line x1="{r1_cx+r_w/2}" y1="{y}" x2="{n1_x}" y2="{y}" class="wg"/>')
    # 节点1 → R2
    parts.append(f'<line x1="{n1_x}" y1="{y}" x2="{r2_cx-r_w/2}" y2="{y}" class="wg"/>')
    # R2 → 节点2
    parts.append(f'<line x1="{r2_cx+r_w/2}" y1="{y}" x2="{n2_x}" y2="{y}" class="wg"/>')
    # 节点2 → ADC
    parts.append(f'<line x1="{n2_x}" y1="{y}" x2="{adc_x}" y2="{y}" class="wg"/>')
    # 端子白底圆
    parts.append(f'<circle cx="{fo_x+fo_w}" cy="{y}" r="3" fill="#ffffff" stroke="{INK}" stroke-width="1.5"/>')
    parts.append(f'<circle cx="{adc_x}" cy="{y}" r="3" fill="#ffffff" stroke="{BLUE}" stroke-width="1.5"/>')

# ---------- 电阻 ----------
parts.append(f'<rect x="{r1_cx-r_w/2}" y="{line_y1-r_h/2}" width="{r_w}" height="{r_h}" class="box"/>')
parts.append(T(r1_cx, line_y1 - r_h/2 - 6, "R1 100Ω", 11, "#374151", "middle", "bold"))
parts.append(f'<rect x="{r1_cx-r_w/2}" y="{line_y2-r_h/2}" width="{r_w}" height="{r_h}" class="box"/>')
parts.append(T(r1_cx, line_y2 + r_h/2 + 14, "R1′ 100Ω", 11, "#374151", "middle", "bold"))
parts.append(f'<rect x="{r2_cx-r_w/2}" y="{line_y1-r_h/2}" width="{r_w}" height="{r_h}" class="box"/>')
parts.append(T(r2_cx, line_y1 - r_h/2 - 6, "R2 120Ω", 11, "#374151", "middle", "bold"))
parts.append(f'<rect x="{r2_cx-r_w/2}" y="{line_y2-r_h/2}" width="{r_w}" height="{r_h}" class="box"/>')
parts.append(T(r2_cx, line_y2 + r_h/2 + 14, "R2′ 120Ω", 11, "#374151", "middle", "bold"))


def gnd_symbol(seg, x, gy, down=True):
    """在 (x,gy) 母线上画接地符号（三横杠向 down 方向展开）。"""
    d = 1 if down else -1
    seg.append(f'<line x1="{x-9}" y1="{gy+8*d}" x2="{x+9}" y2="{gy+8*d}" stroke="{INK}" stroke-width="1.8"/>')
    seg.append(f'<line x1="{x-6}" y1="{gy+13*d}" x2="{x+6}" y2="{gy+13*d}" stroke="{INK}" stroke-width="1.4"/>')
    seg.append(f'<line x1="{x-3}" y1="{gy+18*d}" x2="{x+3}" y2="{gy+18*d}" stroke="{INK}" stroke-width="1.2"/>')


def shunt(seg, x, y, up, label, side="right"):
    """在 (x,y) 结点挂一颗对地电容：up=True 经极板向上接 gnd_y1 母线。
    side: 标签方位 right(x+18 起) / left(x-18 止)。"""
    if up:
        p1, p2, gy = y - 20, y - 28, y - 60
    else:
        p1, p2, gy = y + 20, y + 28, y + 60
    seg.append(f'<line x1="{x}" y1="{y}" x2="{x}" y2="{p1}" class="w"/>')
    seg.append(f'<line x1="{x-11}" y1="{p1}" x2="{x+11}" y2="{p1}" stroke="{INK}" stroke-width="1.8"/>')
    seg.append(f'<line x1="{x-11}" y1="{p2}" x2="{x+11}" y2="{p2}" stroke="{INK}" stroke-width="1.8"/>')
    seg.append(f'<line x1="{x}" y1="{p2}" x2="{x}" y2="{gy}" class="w"/>')
    seg.append(f'<circle cx="{x}" cy="{y}" r="3.2" fill="{INK}"/>')
    seg.append(f'<circle cx="{x}" cy="{gy}" r="3.2" fill="{INK}"/>')
    gx = x - 36
    seg.append(f'<line x1="{x}" y1="{gy}" x2="{gx}" y2="{gy}" class="w"/>')
    seg.append(f'<line x1="{gx}" y1="{gy}" x2="{gx}" y2="{gy+8}" class="w"/>')
    gnd_symbol(seg, gx, gy, down=True)
    if side == "right":
        seg.append(T(x + 18, y - 40 if up else y + 46, label, 11, PURPLE, "start", "bold"))
    else:
        seg.append(T(x - 18, y - 40 if up else y + 46, label, 11, PURPLE, "end", "bold"))


shunt(parts, n1_x, line_y1, True, "C_G1 10nF", "right")
shunt(parts, n1_x, line_y2, False, "C_G1′ 10nF", "right")
shunt(parts, n2_x, line_y1, True, "C_G2 10nF", "right")
# C_G2′ 标签放右下（其接地符号左侧），避免与 C_G1′ 标签连成一串
x_n2, y_n2 = n2_x, line_y2
p1b, p2b = y_n2 + 20, y_n2 + 28
parts.append(f'<line x1="{x_n2}" y1="{y_n2}" x2="{x_n2}" y2="{p1b}" class="w"/>')
parts.append(f'<line x1="{x_n2-11}" y1="{p1b}" x2="{x_n2+11}" y2="{p1b}" stroke="{INK}" stroke-width="1.8"/>')
parts.append(f'<line x1="{x_n2-11}" y1="{p2b}" x2="{x_n2+11}" y2="{p2b}" stroke="{INK}" stroke-width="1.8"/>')
parts.append(f'<line x1="{x_n2}" y1="{p2b}" x2="{x_n2}" y2="{gnd_y2}" class="w"/>')
parts.append(f'<circle cx="{x_n2}" cy="{y_n2}" r="3.2" fill="{INK}"/>')
parts.append(f'<circle cx="{x_n2}" cy="{gnd_y2}" r="3.2" fill="{INK}"/>')
gx_b = x_n2 - 36
parts.append(f'<line x1="{x_n2}" y1="{gnd_y2}" x2="{gx_b}" y2="{gnd_y2}" class="w"/>')
parts.append(f'<line x1="{gx_b}" y1="{gnd_y2}" x2="{gx_b}" y2="{gnd_y2+8}" class="w"/>')
gnd_symbol(parts, gx_b, gnd_y2, down=True)
parts.append(T(x_n2 + 8, y_n2 + 58, "C_G2′ 10nF", 11, PURPLE, "start", "bold"))

# 左列接地符号配 GND 文字（右列省略避免拥挤）
gx0 = n1_x - 36
parts.append(T(gx0 - 14, gnd_y1 + 12, "GND", 9, GRAY, "end"))
parts.append(T(n1_x + 8, gnd_y1 - 5, "（3V3_A 参考地，同网络）", 8, "#94a3b8"))

# ---------- C_d 差分电容（跨节点 2 的 AINxP/AINxN）----------
cd_mid = (line_y1 + line_y2) / 2
parts.append(f'<line x1="{n2_x}" y1="{line_y1}" x2="{n2_x}" y2="{cd_mid-14}" class="w"/>')
parts.append(f'<line x1="{n2_x}" y1="{cd_mid+14}" x2="{n2_x}" y2="{line_y2}" class="w"/>')
parts.append(f'<line x1="{n2_x-13}" y1="{cd_mid-14}" x2="{n2_x+13}" y2="{cd_mid-14}" stroke="{INK}" stroke-width="1.8"/>')
parts.append(f'<line x1="{n2_x-13}" y1="{cd_mid+14}" x2="{n2_x+13}" y2="{cd_mid+14}" stroke="{INK}" stroke-width="1.8"/>')
parts.append(T(n2_x + 20, cd_mid - 4, "C_d", 12, PURPLE, "start", "bold"))
parts.append(T(n2_x + 20, cd_mid + 12, "820pF", 11, PURPLE, "start", "bold"))

# ---------- ADC 框 ----------
parts.append(f'<rect x="{adc_x}" y="{adc_y}" width="{adc_w}" height="{adc_h}" class="adcbx" rx="4"/>')
parts.append(T(adc_x + adc_w/2, adc_y + 22, "ADS131A02", 13, "#1d4ed8", "middle", "bold"))
parts.append(T(adc_x + adc_w/2, adc_y + 40, "ΣΔ 24bit · 128 kSPS · OSR=32", 10, "#64748b", "middle"))

parts.append(T(adc_x + 10, line_y1 + 4, "AIN0P", 11, BLUE, "start", "bold"))
parts.append(T(adc_x + 10, line_y2 + 4, "AIN0N", 11, BLUE, "start", "bold"))

adc_notes = [
    ("内部：sinc³ + C_S = 3.5 pF", 10, "#334155"),
    ("fMOD = 4.096 MHz 吞吐", 10, "#334155"),
    ("", 6, "#334155"),
    ("实测（T2，aaf_pkg_review）：", 10, "#334155"),
    ("fc 50.4 kHz · D4 0.412 dB", 10, "#64748b"),
    ("D1 62.33 · D2 61.05 ✓ · D3 94.74 dB", 10, "#64748b"),
    ("（D2 唯一跨线；D1/D3 线 80/100）", 9, "#94a3b8"),
    ("PM 96.3°@4.6 MHz · C9 +0.33 dB", 10, "#64748b"),
    ("建立最坏 32.0 µs · D9 余量充足", 10, "#64748b"),
    ("宽带噪声 2758 nV（9.5 LSB）", 10, "#64748b"),
    ("折回 318 LSB@100 mV（二阶优）", 10, "#64748b"),
    ("", 6, "#94a3b8"),
    ("采样开关 S1/S2 180° 反相", 9, "#94a3b8"),
    ("各占 50%（SBAS590E）", 9, "#94a3b8"),
]
for i, (note, fs, col) in enumerate(adc_notes):
    if note:
        parts.append(T(adc_x + adc_w/2, adc_y + 62 + i*16, note, fs, col, "middle"))

# ---------- 中部注释 ----------
parts.append(T(34, 90, "通道 0（AIN0P − AIN0N）示意；通道 1 同参数，其 AIN1N 为 Kelvin 无源 RC 直连（无跟随器）", 12, "#111827", "start", "bold"))

# ---------- 底部：优缺点面板 ----------
panel_y = 490
panel_h = 130
parts.append(f'<rect x="20" y="{panel_y}" width="760" height="{panel_h}" class="panel" rx="4"/>')
parts.append(T(34, panel_y + 22, "方案优缺点（六案 Pareto：最优电气折中 · 任务书 §2 标注「优先」）", 12, "#111827", "start", "bold"))

pro_x, pro_y, pro_w, pro_h = 34, panel_y + 32, 360, 88
parts.append(f'<rect x="{pro_x}" y="{pro_y}" width="{pro_w}" height="{pro_h}" class="pro" rx="3"/>')
parts.append(T(pro_x + 10, pro_y + 18, "优", 11, "#047857", "start", "bold"))
pro_lines = [
    "D2 61.05 dB 跨线且与 D4 余量平衡最好",
    "抑制比一阶强 22–24 dB（D1 62.3 vs 40.7）",
    "真实占地 32.62 mm²/通道，比一阶省 16.5%",
    "宽带噪声 2758 nV，低于一阶（3301 nV）",
    "D5–D10 / C9 / PM 全 PASS",
]
for i, t in enumerate(pro_lines):
    parts.append(T(pro_x + 10, pro_y + 34 + i*11, t, 10, "#047857"))

con_x, con_y, con_w, con_h = 406, panel_y + 32, 360, 88
parts.append(f'<rect x="{con_x}" y="{con_y}" width="{con_w}" height="{con_h}" class="con" rx="3"/>')
parts.append(T(con_x + 10, con_y + 18, "缺", 11, "#b91c1c", "start", "bold"))
con_lines = [
    "D1 62.3 / D3 94.7 dB 仍未过线（80/100）",
    "D4 容差角 0.461 dB，距 0.5 淘汰线仅 0.039",
    "D8 免配对 32.9 / 逐级各自配 51.1 dB FAIL",
    "须「整线同 m」四元件选配 → 90.5 dB PASS",
    "D6a 正交口径 44.6% 超 30%（线性口径 9.5%）",
]
for i, t in enumerate(con_lines):
    parts.append(T(con_x + 10, con_y + 34 + i*11, t, 10, "#b91c1c"))

# ---------- 底部：适用边界 ----------
bnd_y = 640
parts.append(f'<rect x="20" y="{bnd_y}" width="760" height="120" class="panel" rx="4"/>')
parts.append(T(34, bnd_y + 20, "配对工序与设计要点", 12, "#111827", "start", "bold"))
bnd_lines = [
    "1. 二阶梯形每线 R1→C_G1→R2→C_G2，C_d 跨节点 2；每差分通道 9 件（4R+4C_G+C_d）全 0402，两通道 18 件。",
    "2. D8 配对必须「整线同 m」：R1/R2 同向同偏 + C_G1/C_G2 同向同偏，LCR 实测分档——逐级各自配不保持",
    "    R1·C2 交叉乘积项（51.1 dB FAIL 实证）；配对后 CMRR 90.5 dB PASS（≥80）。",
    "3. 布局：C_d 紧靠 ADC AIN 脚、P/N 对称、对地电容接完整地平面；4.096/16.384 MHz 时钟远离模拟区。",
    "4. 对照：一阶 S0/S1 D2 差 ~20 dB 出局；T4 抑制更高但 D4 距线仅 0.027 dB；D1≥80 需三阶/有源/数字合成。",
]
for i, t in enumerate(bnd_lines):
    parts.append(T(34, bnd_y + 38 + i*13, t, 10, "#334155"))

# ---------- 底部图注 ----------
parts.append(T(34, 786, "图注自查：结点实心圆 / 端子白底圆；C_d 跨 AIN0P/AIN0N；对地电容接 GND 母线；绿色 = 差分测量路径。",
               8, "#94a3b8"))

parts.append('</svg>')

out_path = "/media/anning/data/Project/DE-DRMS/docs/design/diagram/抗混叠滤波电路_二阶T2.svg"
with open(out_path, "w", encoding="utf-8") as f:
    f.write("\n".join(parts))
print(f"written: {out_path}")
