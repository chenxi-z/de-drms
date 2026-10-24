#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_整体方案框图.py — 800×800 SCI/A4 单栏版"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scistyle import T, rich, head, INK, GREEN, ORANGE, PURPLE, GRAY, BLUE

W = H = 800
out = []
out.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
out.append('<style>'
           '.w{stroke:#1a1a1a;stroke-width:1.6;fill:none}'
           '.p{stroke:#7C3AED;stroke-width:1.6;fill:none;stroke-dasharray:5,3}'
           '.ow{stroke:#EA580C;stroke-width:2.2;fill:none}'
           '.gw{stroke:#059669;stroke-width:2.2;fill:none}'
           '.gd{stroke:#9ca3af;stroke-width:1.2;fill:none;stroke-dasharray:4,3}'
           '</style>')
out.append('<defs>'
           '<marker id="arrK" markerUnits="userSpaceOnUse" markerWidth="10" markerHeight="9" refX="9" refY="4.5" orient="auto"><path d="M0,0 L9,4.5 L0,9 z" fill="#1a1a1a"/></marker>'
           '<marker id="arrG" markerUnits="userSpaceOnUse" markerWidth="10" markerHeight="9" refX="9" refY="4.5" orient="auto"><path d="M0,0 L9,4.5 L0,9 z" fill="#059669"/></marker>'
           '<marker id="arrO" markerUnits="userSpaceOnUse" markerWidth="10" markerHeight="9" refX="9" refY="4.5" orient="auto"><path d="M0,0 L9,4.5 L0,9 z" fill="#EA580C"/></marker>'
           '<marker id="arrP" markerUnits="userSpaceOnUse" markerWidth="10" markerHeight="9" refX="9" refY="4.5" orient="auto"><path d="M0,0 L9,4.5 L0,9 z" fill="#7C3AED"/></marker>'
           '</defs>')
out.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="#ffffff"/>')

# ============ 标题 ============
out += head("DE-DRMS 整体方案框图",
            "双电极直流电阻测量仪 · 1S 锂电 + 双 LDO + STM32U545 + ADS131A02",
            date="附录 E · 2026-10-22")

# ============================================================
# 布局：
#   y 80–96    标题
#   y 90–520   主图区
#     左列 x 20–130      电源树（5 框，宽 110）
#     中央 x 190–420     MCU 大框（宽 230）
#     右列 x 500–780     外设（宽 280）
#     左间隙 130–190    60 px（3.3V_D/3.3V_A 标签空间）
#     右间隙 420–500    80 px（SPI1/I2C1/USB/SDMMC 标签空间）
#   y 540–580  SWD
#   y 600–660  电源域
#   y 680–790  图注
# ============================================================

def box(x, y, w, h, fill, stroke, lw_=1.4):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="2" fill="{fill}" stroke="{stroke}" stroke-width="{lw_}"/>'

# ============ 左列：电源树 ============
LX, LW = 20, 110
PY0, PH, PGAP = 90, 44, 60
titles = ["USB Type-C", "BQ24040", "1S 锂电", "TPS7A0233", "TPS7A2033"]
subs   = ["5 V VBUS", "充电管理", "3.0–4.2 V", "3.3V_D 常开", "3.3V_A EN 受控"]
fills  = ["#fef3c7", "#fef3c7", "#fef3c7", "#dbeafe", "#d1fae5"]
strokes= [INK, INK, INK, "#2563eb", "#059669"]
tcols  = ["#111827", "#111827", "#111827", "#2563eb", "#059669"]
for i, (t, s, fl, st, tc) in enumerate(zip(titles, subs, fills, strokes, tcols)):
    y = PY0 + i*PGAP
    out.append(box(LX, y, LW, PH, fl, st))
    out.append(T(LX+LW/2, y+18, t, 13, tc, "middle", "bold"))
    out.append(T(LX+LW/2, y+34, s, 11, "#475569", "middle"))

# 电源链箭头（竖）
for i in range(4):
    y1 = PY0 + i*PGAP + PH
    y2 = PY0 + (i+1)*PGAP
    cx = LX + LW/2
    out.append(f'<line x1="{cx}" y1="{y1}" x2="{cx}" y2="{y2-2}" class="w" marker-end="url(#arrK)"/>')

# VBAT_MON 旁注 —— 放到左列下方（锂电框下方空白），避免与框重叠
vbat_y = PY0 + 4*PGAP + PH + 14
out.append(T(LX, vbat_y, "PC0=VBAT_MON", 11, BLUE, "start", "bold"))
out.append(T(LX, vbat_y+14, "PC1=VBUS_MON", 11, BLUE, "start", "bold"))
out.append(T(LX, vbat_y+28, "1 MΩ/1 MΩ 分压", 10, "#64748b"))

# ============ MCU 大框（x 190–420, y 90–520）============
MX, MY, MW, MH = 190, 90, 230, 430
out.append(box(MX, MY, MW, MH, "#f8fafc", INK, 1.6))
out.append(T(MX+MW/2, MY+20, "STM32U545RET6Q", 14, "#111827", "middle", "bold"))
out.append(T(MX+MW/2, MY+36, "Cortex-M33 160 MHz", 11, "#475569", "middle"))
out.append(T(MX+MW/2, MY+50, "512 KB Flash · 274 KB SRAM", 11, "#475569", "middle"))
out.append(T(MX+MW/2, MY+64, "LQFP-64", 11, "#475569", "middle"))

# MCU 内单栏排列（避免左右两栏重叠）
ly = MY + 88
MCU_L = [
    ("USB OTG FS", "PA11/PA12", "#111827", "#475569"),
    ("SWD 调试", "PA13/PA14 · PB3", "#111827", "#475569"),
    ("USART1 调试", "PA9/PA10 · AF7", "#111827", "#475569"),
    ("按键 ×2", "PA0 · PB1", "#111827", "#475569"),
    ("LED ×4 + 状态", "PB13/14/15 · PC6 · PC7", "#111827", "#475569"),
    ("BQ 状态监测", "PB5(PG) · PC2(CHG)", "#111827", "#475569"),
    ("SPI1 → ADC", "PA5/6/7 · PA4(nCS)", PURPLE, "#475569"),
    ("ADC 控制", "PA1(DONE) · PA2(nRST) · PA3(DRDY)", PURPLE, "#475569"),
    ("I2C1 → TMP117", "PB6/PB7", PURPLE, "#475569"),
    ("TMUX SEL", "PB2(SENSE) · PB0(K2)", PURPLE, "#475569"),
    ("门控", "PB10(CURR_DIS) · PC3(ANA_EN)", PURPLE, "#475569"),
    ("SDMMC1 4-bit", "PC8–PC12 · PD2", PURPLE, "#475569"),
    ("TF 卡控制", "PA8(SD_PWR_EN) · PA15(SD_CD)", PURPLE, "#475569"),
]
for k, v, ck, cv in MCU_L:
    out.append(T(MX+10, ly, k, 12, ck, "start", "bold"))
    out.append(T(MX+10, ly+14, v, 11, cv))
    ly += 27

# ============ 右列外设 ============
RX, RW = 500, 280

# ADS131A02 (y 90–172)
ax, ay, ah = RX, 90, 84
out.append(box(ax, ay, RW, ah, "#eff6ff", INK, 1.4))
out.append(T(ax+RW/2, ay+18, "ADS131A02", 14, "#111827", "middle", "bold"))
out.append(T(ax+RW/2, ay+34, "24-bit ΣΔ · 128 kSPS · 2-ch 同步", 11, "#475569", "middle"))
out.append(T(ax+RW/2, ay+50, "AVDD→3.3V_A · IOVDD→3.3V_D", 11, GREEN, "middle"))
out.append(T(ax+RW/2, ay+66, "内部 2.442 V · 119.5 dB @1 kSPS", 11, "#475569", "middle"))

# 模拟前端（y 196–318）
fx, fy, fh = RX, 196, 122
out.append(box(fx, fy, RW, fh, "#f0fdf4", GREEN, 1.4))
out.append(T(fx+RW/2, fy+18, "模拟前端（3.3V_A 域）", 13, "#065f46", "middle", "bold"))
out.append(f'<line x1="{fx+10}" y1="{fy+26}" x2="{fx+RW-10}" y2="{fy+26}" class="gd"/>')
fe = [
    ("3× OPA388 跟随器", "T/M/B · Iq 1.7–2.6 mA/颗"),
    ("恒流源 OPA333+BSS138", "8 µA · Rsense 150 kΩ · CURR_DIS 关断"),
    ("TMUX1134 ×1", "K1–K4 整合 · ≤50 pA@25 ℃"),
]
fy2 = fy + 46
for k, v in fe:
    out.append(T(fx+12, fy2, k, 12, "#065f46", "start", "bold"))
    out.append(T(fx+12, fy2+14, v, 11, "#475569"))
    fy2 += 28

# 样品连接器（y 340–384）
sx, sy, sh = RX, 340, 44
out.append(box(sx, sy, RW, sh, "#fef3c7", INK, 1.4))
out.append(T(sx+RW/2, sy+18, "样品连接器 J5–J8", 13, "#111827", "middle", "bold"))
out.append(T(sx+RW/2, sy+34, "T/S/M/B → 被测件 · SMA×4 Kelvin", 11, "#475569", "middle"))

# TMP117（y 406–450）
tx, ty, th = RX, 406, 44
out.append(box(tx, ty, RW, th, "#fef3c7", INK, 1.4))
out.append(T(tx+RW/2, ty+18, "TMP117 温度探头", 13, "#111827", "middle", "bold"))
out.append(T(tx+RW/2, ty+34, "外置 4 线 · I2C1 · 4.7 kΩ 上拉", 11, "#475569", "middle"))

# USB 数据（y 472–516）
ux, uy, uh = RX, 472, 44
out.append(box(ux, uy, RW, uh, "#fef3c7", INK, 1.4))
out.append(T(ux+RW/2, uy+18, "USB OTG FS（数据）", 13, "#111827", "middle", "bold"))
out.append(T(ux+RW/2, uy+34, "Type-C → 上位机", 11, "#475569", "middle"))

# TF 卡（y 538–608）
dx, dy, dh = RX, 538, 70
out.append(box(dx, dy, RW, dh, "#eff6ff", "#2563eb", 1.4))
out.append(T(dx+RW/2, dy+16, "TF 卡记录（SDMMC1 4-bit）", 13, "#1e3a8a", "middle", "bold"))
out.append(T(dx+RW/2, dy+32, "33 Ω 串阻 · CMD 上拉 10 kΩ · FatFS", 11, "#374151", "middle"))
out.append(T(dx+RW/2, dy+46, "3V3_SD ← TPS22917 · SD_PWR_EN=PA8", 11, "#374151", "middle"))
out.append(T(dx+RW/2, dy+60, "SD_CD=PA15 · 待机断电省 50–100 µA", 11, GREEN, "middle"))

# ============ 连接线 ============
# 电源 → MCU
vdd_y = PY0 + 3*PGAP + PH/2    # 3.3V_D 框中心
out.append(f'<line x1="{LX+LW}" y1="{vdd_y}" x2="{MX-2}" y2="{vdd_y}" class="w" marker-end="url(#arrK)"/>')
out.append(T((LX+LW+MX)/2, vdd_y - 6, "3.3V_D", 11, "#2563eb", "middle", "bold"))
vaa_y = PY0 + 4*PGAP + PH/2
out.append(f'<line x1="{LX+LW}" y1="{vaa_y}" x2="{MX-2}" y2="{vaa_y}" class="w" marker-end="url(#arrK)"/>')
out.append(T((LX+LW+MX)/2, vaa_y - 6, "3.3V_A", 11, GREEN, "middle", "bold"))

# MCU → ADS131A02 (SPI1)
spi_y = ay + ah/2   # 132
out.append(f'<line x1="{MX+MW}" y1="{spi_y}" x2="{RX-2}" y2="{spi_y}" class="p" marker-end="url(#arrP)"/>')
out.append(T((MX+MW+RX)/2, spi_y - 6, "SPI1", 11, PURPLE, "middle", "bold"))

# ADS131A02 → 模拟前端 (AIN0/1) —— 竖线
ainx = RX + RW - 30
out.append(f'<line x1="{ainx}" y1="{ay+ah}" x2="{ainx}" y2="{fy-2}" class="p" marker-end="url(#arrP)"/>')
out.append(T(ainx - 6, (ay+ah+fy)/2, "AIN0/1", 11, PURPLE, "end", "bold"))

# MCU → 模拟前端 —— 水平，标签写在线上但缩短避免压右列框
ctl_y = fy + 50
out.append(f'<line x1="{MX+MW}" y1="{ctl_y}" x2="{RX-2}" y2="{ctl_y}" class="p" marker-end="url(#arrP)"/>')
out.append(T((MX+MW+RX)/2, ctl_y - 6, "SEL·EN", 11, PURPLE, "middle", "bold"))

# 模拟前端 → 样品（绿色）
smpx = RX + RW - 30
out.append(f'<line x1="{smpx}" y1="{fy+fh}" x2="{smpx}" y2="{sy-2}" class="gw" marker-end="url(#arrG)"/>')
out.append(T(smpx - 6, (fy+fh+sy)/2, "T/S/M/B", 11, GREEN, "end", "bold"))

# MCU → TMP117 (I2C1)
i2c_y = ty + th/2
out.append(f'<line x1="{MX+MW}" y1="{i2c_y}" x2="{RX-2}" y2="{i2c_y}" class="p" marker-end="url(#arrP)"/>')
out.append(T((MX+MW+RX)/2, i2c_y - 6, "I2C1", 11, PURPLE, "middle", "bold"))

# MCU → USB (DM/DP)
usb_y = uy + uh/2
out.append(f'<line x1="{MX+MW}" y1="{usb_y}" x2="{RX-2}" y2="{usb_y}" class="ow" marker-end="url(#arrO)"/>')
out.append(T((MX+MW+RX)/2, usb_y - 6, "USB DM/DP", 11, ORANGE, "middle", "bold"))

# MCU → TF 卡 (SDMMC)
sd_y = dy + dh/2
out.append(f'<line x1="{MX+MW}" y1="{sd_y}" x2="{RX-2}" y2="{sd_y}" class="p" marker-end="url(#arrP)"/>')
out.append(T((MX+MW+RX)/2, sd_y - 6, "SDMMC1", 11, PURPLE, "middle", "bold"))

# MCU 下方 SWD 调试口
swx, swy, sww, swh = MX + 5, MY + MH + 12, 220, 40
out.append(box(swx, swy, sww, swh, "#f1f5f9", INK, 1.2))
out.append(T(swx+sww/2, swy+16, "SWD 调试口 J3 · 8P", 12, "#111827", "middle", "bold"))
out.append(T(swx+sww/2, swy+31, "PA13/14 · PB3 · PA9/10(USART1)", 10, "#475569", "middle"))
out.append(f'<line x1="{swx+sww/2}" y1="{MY+MH}" x2="{swx+sww/2}" y2="{swy}" class="w"/>')

# ============ 电源域划分面板 ============
px, py, pw, ph = 20, 640, 760, 60
out.append(box(px, py, pw, ph, "#f8fafc", INK, 1.2))
out.append(T(px+12, py+18, "电源域划分", 13, "#111827", "start", "bold"))
out.append(T(px+120, py+18, "3.3V_D 数字·常开：MCU / USB / LED / TMP117 / ADC IOVDD / TF（PA8）", 11, "#2563eb"))
out.append(T(px+120, py+38, "3.3V_A 模拟·EN 受控：ADC AVDD / OPA388×3 / OPA333 / TMUX / VSET", 11, GREEN))
out.append(T(px+12, py+54, "双 LDO 隔离数模；模拟域仅测量窗口上电，待机 ≈10.8 µA", 11, "#475569"))

# ============ 图注 ============
nx, ny = 20, 722
out.append(T(nx, ny, "图注与自查要点", 13, "#111827", "start", "bold"))
notes = [
    "1. 电源树：USB 5 V → BQ24040 → 电池 → 双 LDO（数字常开 + 模拟 EN 受控 ANA_EN=PC3）。",
    "2. ADC 双通道同步采样，恒流波动在 R=V/I 除法中抵消；TMP117 外置探头贴近被测件。",
    "3. 校准三模式：测量（K1 通）/ 校准（K2 通）/ 零点（K1/K2 均断 + CURR_DIS=1）。",
]
for i, n in enumerate(notes):
    out.append(T(nx, ny + 18 + i*16, n, 11, "#374151"))

out.append('</svg>')

svg = "\n".join(out)
dst = "/media/anning/data/Project/DE-DRMS/docs/design/diagram/整体方案框图.svg"
with open(dst, "w", encoding="utf-8") as f:
    f.write(svg)
print(f"written {dst}")
