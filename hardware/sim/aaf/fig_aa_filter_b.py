# -*- coding: utf-8 -*-
"""Fig_aa_filter_b — 抗混叠滤波电路（B 案定版）SCI 风格重绘
house style: Times New Roman + SimSun, 细线 0.75 pt, 白底, 无面栅格,
零白边导出 (bbox tight + pad 0 + ink crop), SVG(fonttype=none) + PNG(600 dpi)
"""
import sys
from pathlib import Path

SKILL = Path(r"C:\Users\chenx\.agents\skills\howtoSCI\templates")
sys.path.insert(0, str(SKILL))

from style_utils import apply_style, plt  # noqa: E402
import matplotlib as mpl  # noqa: E402

apply_style()
# 中文：宋体接在 Times 之后（matplotlib ≥3.6 按列表逐字回退）
mpl.rcParams["font.serif"] = ["Times New Roman", "SimSun", "DejaVu Serif"]
CJK_LIST = ["Times New Roman", "SimSun"]

def T(x, y, s_, **k):
    """统一文本入口：显式字体回退列表（Times 优先、宋体补 CJK）"""
    k.setdefault("fontfamily", CJK_LIST)
    return ax.text(x, y, s_, **k)
mpl.rcParams["axes.linewidth"] = 0.75

OUT = Path(r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf")

LW = 0.75          # house line width
LW_SIG = 1.0       # 信号主干（对应 zero-line 宽度档）
FS_LBL = 6.5       # 元件标号
FS_BLK = 7.5       # 块标题
INK = "#000000"
RED = "#e01b1b"
BLUE = "#1f4fd8"

fig = plt.figure(figsize=(7.48, 2.75))          # 190 mm × 70 mm（双栏宽）
ax = fig.add_axes((0.005, 0.01, 0.99, 0.98))
ax.set_xlim(0, 210)
ax.set_ylim(-8.5, 78)
ax.set_aspect("equal")
ax.axis("off")


# ---------- 元件基元（IEC） ----------
def wire(x1, y1, x2, y2, lw=LW, color=INK, z=2):
    ax.plot([x1, x2], [y1, y2], color=color, lw=lw, solid_capstyle="butt", zorder=z)


def resistor(x, y, w=7.2, h=2.6, horizontal=True):
    """IEC 矩形电阻，中心 (x,y)，返回两端接线点"""
    if horizontal:
        ax.add_patch(plt.Rectangle((x - w / 2, y - h / 2), w, h, fill=False,
                                   lw=LW, ec=INK, zorder=3))
        return (x - w / 2, x + w / 2)
    ax.add_patch(plt.Rectangle((x - h / 2, y - w / 2), h, w, fill=False,
                               lw=LW, ec=INK, zorder=3))
    return (y - w / 2, y + w / 2)


def cap_to_gnd(x, y_top, y_gnd, label, value):
    """对地电容：竖直，极板在中间，下引线到地母线"""
    pl = 1.9          # 极板半宽
    gap = 0.75        # 极板间距一半
    mid = (y_top + y_gnd) / 2
    wire(x, y_top, x, mid + gap)
    wire(x, mid - gap, x, y_gnd)
    for yy in (mid + gap, mid - gap):
        ax.plot([x - pl, x + pl], [yy, yy], color=INK, lw=LW, zorder=3)
    T(x + 1.1, mid, f"{label}\n{value}", fontsize=FS_LBL, va="center", ha="left")


def cap_diff(x, y_t, y_b, label, value):
    """差分电容：竖直跨 y_t..y_b，标签居右（与其余电容一致）"""
    mid = (y_t + y_b) / 2
    gap, pl = 0.9, 2.2
    wire(x, y_t, x, mid + gap)
    wire(x, mid - gap, x, y_b)
    for yy in (mid + gap, mid - gap):
        ax.plot([x - pl, x + pl], [yy, yy], color=RED, lw=LW, zorder=4)
    T(x + 2.9, mid, f"{label} = {value}", fontsize=FS_LBL, va="center",
      ha="left", color=RED)


def ground(x, y, s=1.5):
    for i, hw in enumerate((s, s * 0.66, s * 0.33)):
        ax.plot([x - hw, x + hw], [y - i * 0.62, y - i * 0.62], color=INK, lw=LW, zorder=3)


def junction(x, y, r=0.42):
    ax.add_patch(plt.Circle((x, y), r, color=INK, lw=0, zorder=5))


def opamp_follower(x, y, tag, sub, src):
    """单位增益跟随器：+ 在下 1/3（信号输入），− 在上 1/3（反馈绕上方）"""
    w, h = 9.0, 8.0
    yp_in, yn_fb = y - h * 0.30, y + h * 0.30
    ax.add_patch(plt.Polygon([(x, y - h / 2), (x, y + h / 2), (x + w, y)],
                             fill=False, lw=LW, ec=INK, zorder=3))
    T(x + 0.8, yp_in, "+", fontsize=FS_LBL, va="center")
    T(x + 0.8, yn_fb, "\u2212", fontsize=FS_LBL, va="center")
    xin = x - 3.4
    # 输入端口（+ 高度）：信号源节点 + 引线
    wire(xin, yp_in, x, yp_in)
    ax.add_patch(plt.Circle((xin, yp_in), 0.55, facecolor="white", ec=INK, lw=0.6, zorder=5))
    T(xin, yp_in + 1.0, src, fontsize=FS_LBL, ha="center", va="bottom")
    # 反馈：输出向上绕回 −端
    yfb = y + h / 2 + 1.6
    ax.plot([x + w, x + w], [y, yfb], color=INK, lw=LW, zorder=2)
    ax.plot([x + w, xin], [yfb, yfb], color=INK, lw=LW, zorder=2)
    ax.plot([xin, xin], [yfb, yn_fb], color=INK, lw=LW, zorder=2)
    wire(xin, yn_fb, x, yn_fb)
    T(x - 1.2, yfb + 0.8, tag, fontsize=FS_BLK, va="bottom", ha="left")
    T(x - 1.2, y - h / 2 - 1.1, sub, fontsize=FS_LBL, va="top", ha="left", color="#444444")
    return (x + w, y)


# ---------- 布局 ----------
yP, yN = 56.0, 22.0
GND_Y = 6.0
R1x, R2x, R3x = 62.0, 96.0, 130.0
CDx = 158.0
ADCx = 176.0
RW = 7.2

# 跟随器（左）
outP = opamp_follower(16, yP, "U5:A  OPA388", "T 点跟随器（V_P 支路）", "T")
outN = opamp_follower(16, yN, "U9:A  OPA388", "M 线跟随器（AIN1N 支路）", "M")

# 主干（信号线）
wire(outP[0], yP, R1x - RW / 2, yP, lw=LW_SIG)
wire(outN[0], yN, R1x - RW / 2, yN, lw=LW_SIG)
for rx in (R1x, R2x, R3x):
    for yy in (yP, yN):
        resistor(rx, yy)
        if rx != R3x:
            wire(rx + RW / 2, yy, (rx + 34) - RW / 2, yy, lw=LW_SIG)
wire(R3x + RW / 2, yP, CDx, yP, lw=LW_SIG)
wire(R3x + RW / 2, yN, CDx, yN, lw=LW_SIG)
wire(CDx, yP, ADCx - 0.6, yP, lw=LW_SIG)
wire(CDx, yN, ADCx - 0.6, yN, lw=LW_SIG)

# 对地电容（P 上型：极板在主干上方 → 全部走主干下方统一到地母线）
# 为保持期刊常见的单侧地布置：P 线电容向下、N 线电容向下，共用底部地母线高度差由引线体现
capP = [(R1x, "C1", "68 nF"), (R2x, "C2", "68 nF"), (R3x, "C3", "27 nF")]
capN = [(R1x, "C4", "68 nF"), (R2x, "C5", "68 nF"), (R3x, "C6", "27 nF")]
gnd_bus_top = 38.5          # P 线电容地母线（P、N 之间）
for (rx, lb, vv) in capP:
    cap_to_gnd(rx, yP - 1.3, gnd_bus_top, lb, vv)
    junction(rx, yP)
for (rx, lb, vv) in capN:
    cap_to_gnd(rx, yN - 1.3, GND_Y, lb, vv)
    junction(rx, yN)
# P 电容地母线 + N 电容地母线
wire(R1x - 6, gnd_bus_top, R3x + 6, gnd_bus_top)
ground((R1x + R3x) / 2 + 12, gnd_bus_top, 1.6)
wire(R1x - 6, GND_Y, R3x + 6, GND_Y)
ground((R1x + R3x) / 2 + 12, GND_Y, 1.6)
T(R1x - 6.6, gnd_bus_top + 0.2, "AGND", fontsize=FS_LBL, ha="right", va="center")
T(R1x - 6.6, GND_Y + 0.2, "AGND", fontsize=FS_LBL, ha="right", va="center")

# 差分电容
cap_diff(CDx, yP, yN, "C7", "12 nF")
junction(CDx, yP)
junction(CDx, yN)

# ---------- ADC ----------
adc_w = 24.0
adc_y0, adc_y1 = yN - 28.0, yP + 8.0
ax.add_patch(plt.Rectangle((ADCx, adc_y0), adc_w, adc_y1 - adc_y0,
                           fill=False, lw=LW, ec=BLUE, zorder=3))
for yy, nm, dy in ((yP, "AIN1P", 2.2), (yN, "AIN1N", -2.6)):
    ax.add_patch(plt.Circle((ADCx, yy), 0.55, facecolor="white", ec=BLUE, lw=0.6, zorder=5))
    T(ADCx + 1.7, yy + dy, nm, fontsize=FS_LBL, color=BLUE, va="center")
T(ADCx + adc_w / 2, yP + 5.2, "ADS131A02", fontsize=FS_BLK,
        ha="center", va="center", color=BLUE)
T(ADCx + adc_w / 2, 34.6, "24-bit \u03a3\u0394, 128 kSPS", fontsize=FS_LBL, ha="center", va="center")
T(ADCx + adc_w / 2, 31.4, r"sinc$^3$, OSR = 32", fontsize=FS_LBL, ha="center", va="center")
T(ADCx + adc_w / 2, 12.6, r"$C_\mathrm{S}$ = 3.5 pF", fontsize=FS_LBL, ha="center", va="center")
T(ADCx + adc_w / 2, 9.4, r"$f_\mathrm{MOD}$ = 4.096 MHz", fontsize=FS_LBL, ha="center", va="center")

# ---------- 阶梯注释 ----------
ax.annotate("", xy=(R3x + RW / 2 + 1.5, yP + 4.6), xytext=(R1x - RW / 2 - 1.5, yP + 4.6),
            arrowprops=dict(arrowstyle="-|>", lw=0.5, color="#666666"))
T((R1x + R3x) / 2 + 7.0, yP + 5.6, r"$f_\mathrm{c} \approx 80\ \mathrm{kHz}$",
        fontsize=FS_LBL, ha="center", va="bottom")
T((R1x + R3x) / 2 + 21.5, yP + 5.6, "（三级无源低通）",
        fontsize=FS_LBL, ha="center", va="bottom")
ax.annotate("", xy=(CDx, yP + 1.6), xytext=(R3x + RW / 2, yP + 1.6),
            arrowprops=dict(arrowstyle="-|>", lw=0.5, color="#666666"))
T((CDx + R3x) / 2, yP + 2.4,
        r"$-$84.6 dB @ $f_\mathrm{MOD}$", fontsize=FS_LBL, ha="center", va="bottom")
T(2.0, 2.0,
        "两级采样分工：无源阶梯守 k·fMOD 折叠与电荷桶；片内 sinc³ 数字滤波（−3 dB ≈ 33.5 kHz）守 64 kHz 以上至 fMOD 折叠带",
        fontsize=FS_LBL, ha="left", va="bottom", color="#444444")

# ---------- 零白边导出 ----------
svg = OUT / "Fig_aa_filter_b.svg"
png = OUT / "Fig_aa_filter_b.png"
fig.savefig(svg, bbox_inches="tight", pad_inches=0)
fig.savefig(png, dpi=600, bbox_inches="tight", pad_inches=0)

# QA: ink-crop 后 measure_border == (0,0,0,0)
from PIL import Image
import numpy as np
im = Image.open(png).convert("L")
a = np.asarray(im)
ink = a < 250
rows = np.where(ink.any(axis=1))[0]
cols = np.where(ink.any(axis=0))[0]
cropped = im.crop((cols[0], rows[0], cols[-1] + 1, rows[-1] + 1))
cropped.save(png)
b = np.asarray(cropped) < 250
border = (int((~b[0]).all()), int((~b[-1]).all()), int((~b[:, 0]).all()), int((~b[:, -1]).all()))
print("size:", cropped.size, "border(t,r,b,l):", border, "OK" if border == (0, 0, 0, 0) else "FAIL")
