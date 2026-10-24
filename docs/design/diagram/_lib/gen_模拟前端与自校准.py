#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_模拟前端与自校准.py — 800×800 SCI 版式重绘（v4：C3 双档 + Cff + TMUX1134 + AAF lad4r）

布局（800×800 严格分栏）：
  左区 x 30–430 ：偏置 R_top/R_b、T 总线、样品、R_ref、Cff、CH1–CH4、低边恒流源（VSET/OPA333/BSS138/Rsense）
  中区 x 430–560：跟随器 T/M/B（OPA388 ×3）
  右区 x 560–780：ADS131A02 框 + 顶部 MCU GPIO 摘要
  底部 y 730–790：图注 3 行
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from scistyle import T, rich, head, INK, GREEN, ORANGE, PURPLE, BLUE, GRAY  # noqa

OUT = Path("/media/anning/data/Project/DE-DRMS/docs/design/diagram/模拟前端与自校准.svg")

svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="800" height="800" viewBox="0 0 800 800"',
       '     font-family="\'Noto Serif CJK SC\',\'Noto Serif SC\',serif">',
       '<rect width="800" height="800" fill="#ffffff"/>']

svg += head("模拟前端与自校准电路（v4 终稿）",
            "低边恒流 7.86/1.06 µA 双档 · TMUX1134 单颗 · Cff=100pF · AAF lad4r · 主图=校准态")

# ============================================================
# 顶部 MCU GPIO 摘要条（横贯右区，不占主图）
# ============================================================
svg.append(f'<rect x="430" y="80" width="368" height="56" fill="#faf5ff" stroke="{PURPLE}" stroke-width="1.2"/>')
svg.append(T(440, 98, "MCU GPIO", 11, PURPLE, w="bold"))
svg.append(T(500, 98, "SEL_SENSE=PB2 → CH1/2/3 同沿", 11, INK))
svg.append(T(440, 114, "SEL4=PB0 → CH4", 11, INK))
svg.append(T(580, 114, "CURR_DIS=PB10 · ANA_EN=PC3", 11, INK))
svg.append(T(440, 130, "ISET_HI=PC2 · RNG 独立 GPIO", 11, INK))
svg.append(T(640, 130, "PB5=BQ_TS（不再用于开关）", 11, GRAY))

# ============================================================
# 上区 y 150–370：偏置 + T 总线 + 样品 + R_ref + Cff
# ============================================================

# ---- 3.3V_A ----
svg.append(f'<line x1="40" y1="160" x2="40" y2="148" stroke="{INK}" stroke-width="1.5"/>')
svg.append(f'<line x1="30" y1="148" x2="50" y2="148" stroke="{INK}" stroke-width="2"/>')
svg.append(T(56, 152, "3.3V_A", 11, INK, w="bold"))
svg.append(f'<line x1="40" y1="160" x2="40" y2="178" stroke="{INK}" stroke-width="2"/>')

# ---- R_top（纵向）----
svg.append(f'<rect x="30" y="178" width="20" height="40" fill="#f1f5f9" stroke="{INK}" stroke-width="1.4"/>')
svg.append(T(56, 192, "R_top", 11, INK, w="bold"))
svg.append(T(56, 208, "10 kΩ·1%", 11, GRAY))
svg.append(f'<line x1="40" y1="218" x2="40" y2="240" stroke="{INK}" stroke-width="2"/>')

# ---- T 总线（y=240）----
svg.append(f'<line x1="40" y1="240" x2="420" y2="240" stroke="{INK}" stroke-width="2.2"/>')
for cx in (140, 300, 380):
    svg.append(f'<circle cx="{cx}" cy="240" r="3.6" fill="#111827"/>')
svg.append(T(200, 232, "T ~3.0 V", 12, INK, w="bold"))

# ---- R_b（接 T → GND）----
svg.append(f'<line x1="380" y1="240" x2="380" y2="258" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<rect x="370" y="258" width="20" height="38" fill="#f1f5f9" stroke="{INK}" stroke-width="1.4"/>')
svg.append(T(396, 272, "R_b", 11, INK, w="bold"))
svg.append(T(396, 288, "150 kΩ·1%", 11, GRAY))
svg.append(f'<line x1="380" y1="296" x2="380" y2="306" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<line x1="368" y1="306" x2="392" y2="306" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<line x1="373" y1="311" x2="387" y2="311" stroke="{INK}" stroke-width="1.6"/>')
svg.append(f'<line x1="377" y1="316" x2="383" y2="316" stroke="{INK}" stroke-width="1.6"/>')

# ---- 样品（板外）----
svg.append(f'<rect x="60" y="280" width="160" height="58" fill="#fffbeb" stroke="#d97706" stroke-width="1.4" stroke-dasharray="5,4"/>')
svg.append(T(140, 298, "被测样品 R_x", 12, "#92400e", "middle", "bold"))
svg.append(T(140, 314, "10–120 kΩ（板外）", 11, "#b45309", "middle"))
svg.append(T(140, 330, "J5/J6 高端 · J7/J8 低端", 11, "#b45309", "middle"))
# 高端力线 J5 下 T→样品
svg.append(f'<line x1="140" y1="240" x2="140" y2="280" stroke="{INK}" stroke-width="2"/>')
svg.append(T(134, 268, "J5·I+", 11, GREEN, "end", "bold"))
# 高端感线 J6 从 V_P 总线下来（绕过 T 总线）
svg.append(f'<line x1="260" y1="180" x2="260" y2="280" stroke="{INK}" stroke-width="2"/>')
svg.append(T(256, 258, "J6·V+", 11, BLUE, "end", "bold"))
# JP1 跳线（虚线橙）
svg.append(f'<line x1="140" y1="272" x2="260" y2="272" stroke="{ORANGE}" stroke-width="1.6" stroke-dasharray="3,3"/>')
svg.append(T(200, 264, "JP1", 11, ORANGE, "middle", "bold"))

# ---- V_P 总线（y=180）----
svg.append(f'<line x1="260" y1="180" x2="500" y2="180" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<circle cx="260" cy="180" r="3.6" fill="#111827"/>')
svg.append(T(350, 172, "V_P", 12, INK, w="bold"))
# V_P 继续向右到跟随器 T

# ---- CH2·NC（V_P 并回 T，x=420 处 V_P 下至 T）----
svg.append(f'<line x1="420" y1="180" x2="420" y2="196" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<circle cx="420" cy="196" r="3" fill="#ffffff" stroke="{INK}" stroke-width="1.6"/>')
svg.append(f'<circle cx="420" cy="240" r="3" fill="#ffffff" stroke="{INK}" stroke-width="1.6"/>')
# 刀臂默认 NC（合）
svg.append(f'<line x1="420" y1="196" x2="420" y2="237" stroke="{INK}" stroke-width="1.7"/>')
svg.append(T(428, 218, "CH2·NC", 11, PURPLE, w="bold"))
# 控制线（短，标 PB2 简化）—— 下移避免穿 CH2 标签
svg.append(f'<line x1="440" y1="240" x2="424" y2="240" stroke="{PURPLE}" stroke-width="1.3" stroke-dasharray="3,3"/>')
svg.append(f'<circle cx="423" cy="240" r="2.2" fill="#ffffff" stroke="{PURPLE}" stroke-width="1.2"/>')
svg.append(T(444, 244, "PB2", 11, PURPLE))

# ---- 样品低端 ----
# J7·I− → S 节点
svg.append(f'<line x1="140" y1="338" x2="140" y2="392" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<circle cx="140" cy="392" r="3.6" fill="#111827"/>')
svg.append(T(132, 386, "S", 12, INK, "end", "bold"))
svg.append(T(132, 360, "J7·I−", 11, GREEN, "end", "bold"))
# J8·V− → V_N 节点（向右行）
svg.append(f'<line x1="180" y1="338" x2="180" y2="370" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<line x1="180" y1="370" x2="230" y2="370" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<circle cx="180" cy="370" r="3.6" fill="#111827"/>')
svg.append(T(186, 358, "J8·V−", 11, BLUE, w="bold"))
svg.append(T(234, 366, "V_N", 12, INK, w="bold"))
# JP2 跳线
svg.append(f'<line x1="140" y1="354" x2="180" y2="354" stroke="{ORANGE}" stroke-width="1.6" stroke-dasharray="3,3"/>')
svg.append(T(160, 348, "JP2", 11, ORANGE, "middle", "bold"))

# ---- R_ref 支路（T=300 → R_ref → F）----
# 注意 T 上 260 已被 J6 用、340 已被 R_b 用。R_ref 放在 x=300
svg.append(f'<line x1="300" y1="240" x2="300" y2="258" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<rect x="290" y="258" width="20" height="50" fill="#f1f5f9" stroke="{INK}" stroke-width="1.4"/>')
svg.append(T(314, 272, "R_ref", 11, INK, w="bold"))
svg.append(T(314, 288, "100 kΩ", 11, INK, w="bold"))
svg.append(T(314, 302, "0.01%", 11, GRAY))
svg.append(f'<line x1="300" y1="308" x2="300" y2="392" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<circle cx="300" cy="392" r="3.6" fill="#111827"/>')
svg.append(T(292, 386, "F", 12, INK, "end", "bold"))

# ---- Cff（F → GND，必装）----
# 从 F 向左 x=270 短接
svg.append(f'<circle cx="270" cy="392" r="3.6" fill="#111827"/>')
svg.append(f'<line x1="270" y1="392" x2="300" y2="392" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<line x1="270" y1="392" x2="270" y2="404" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<line x1="258" y1="404" x2="282" y2="404" stroke="{INK}" stroke-width="2.2"/>')
svg.append(f'<line x1="258" y1="410" x2="282" y2="410" stroke="{INK}" stroke-width="2.2"/>')
svg.append(f'<line x1="270" y1="410" x2="270" y2="420" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<line x1="260" y1="420" x2="280" y2="420" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<line x1="264" y1="424" x2="276" y2="424" stroke="{INK}" stroke-width="1.6"/>')
svg.append(f'<line x1="267" y1="428" x2="273" y2="428" stroke="{INK}" stroke-width="1.6"/>')
svg.append(T(254, 408, "Cff 100 pF", 11, PURPLE, "end", "bold"))

# ---- CH1 SPDT（COM=M 在右，NO=V_N 上，NC=F 下）----
# NO 掷（V_N）：触点 (270,370)
svg.append(f'<line x1="230" y1="370" x2="270" y2="370" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<circle cx="270" cy="370" r="3" fill="#ffffff" stroke="{INK}" stroke-width="1.6"/>')
# NC 掷（F）：触点 (330,392)
svg.append(f'<line x1="300" y1="392" x2="330" y2="392" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<circle cx="330" cy="392" r="3" fill="#ffffff" stroke="{INK}" stroke-width="1.6"/>')
# COM（M）：触点 (390,382)；默认 NC → 合到 F
svg.append(f'<circle cx="390" cy="382" r="3" fill="#ffffff" stroke="{INK}" stroke-width="1.6"/>')
svg.append(f'<line x1="390" y1="382" x2="333" y2="391" stroke="{INK}" stroke-width="1.7"/>')
svg.append(T(346, 376, "CH1 SPDT", 11, PURPLE, w="bold"))
# 控制线
svg.append(f'<line x1="360" y1="370" x2="360" y2="348" stroke="{PURPLE}" stroke-width="1.3" stroke-dasharray="3,3"/>')
svg.append(f'<circle cx="360" cy="370" r="2.2" fill="#ffffff" stroke="{PURPLE}" stroke-width="1.2"/>')
svg.append(T(364, 344, "PB2", 11, PURPLE))
# M 节点右行
svg.append(f'<line x1="390" y1="382" x2="430" y2="382" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<circle cx="430" cy="382" r="3.6" fill="#111827"/>')
svg.append(T(434, 378, "M", 12, INK, w="bold"))

# ---- CH3·NO（S → X）----
svg.append(f'<line x1="140" y1="392" x2="140" y2="424" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<circle cx="140" cy="424" r="3" fill="#ffffff" stroke="{INK}" stroke-width="1.6"/>')
svg.append(f'<circle cx="140" cy="458" r="3" fill="#ffffff" stroke="{INK}" stroke-width="1.6"/>')
# 刀臂默认开
svg.append(f'<line x1="140" y1="458" x2="152" y2="428" stroke="{INK}" stroke-width="1.7"/>')
svg.append(T(108, 442, "CH3·NO", 11, PURPLE, "end", "bold"))
svg.append(f'<line x1="180" y1="442" x2="152" y2="442" stroke="{PURPLE}" stroke-width="1.3" stroke-dasharray="3,3"/>')
svg.append(f'<circle cx="150" cy="442" r="2.2" fill="#ffffff" stroke="{PURPLE}" stroke-width="1.2"/>')
svg.append(T(184, 446, "PB2", 11, PURPLE))
svg.append(f'<line x1="140" y1="458" x2="140" y2="480" stroke="{INK}" stroke-width="2"/>')

# ---- CH4·NC（F → X）----
svg.append(f'<line x1="300" y1="392" x2="300" y2="424" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<circle cx="300" cy="424" r="3" fill="#ffffff" stroke="{INK}" stroke-width="1.6"/>')
svg.append(f'<circle cx="300" cy="458" r="3" fill="#ffffff" stroke="{INK}" stroke-width="1.6"/>')
# 刀臂默认合
svg.append(f'<line x1="300" y1="424" x2="300" y2="455" stroke="{INK}" stroke-width="1.7"/>')
svg.append(T(316, 432, "CH4·NC", 11, PURPLE, w="bold"))
svg.append(f'<line x1="348" y1="450" x2="304" y2="450" stroke="{PURPLE}" stroke-width="1.3" stroke-dasharray="3,3"/>')
svg.append(f'<circle cx="303" cy="450" r="2.2" fill="#ffffff" stroke="{PURPLE}" stroke-width="1.2"/>')
svg.append(T(352, 454, "PB0", 11, PURPLE))
svg.append(f'<line x1="300" y1="458" x2="300" y2="480" stroke="{INK}" stroke-width="2"/>')

# ---- X 汇合（恒流源顶端入口）----
svg.append(f'<line x1="140" y1="480" x2="300" y2="480" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<circle cx="220" cy="480" r="3.6" fill="#111827"/>')
svg.append(T(228, 476, "X", 12, INK, w="bold"))

# ============================================================
# 下区 y 480–680：低边恒流源
# ============================================================
# X → BSS138 漏极
svg.append(f'<line x1="220" y1="480" x2="220" y2="500" stroke="{INK}" stroke-width="2"/>')
# BSS138 符号（纵向，漏上进，源下出，栅右出）
# 漏极
svg.append(f'<line x1="220" y1="500" x2="220" y2="510" stroke="{INK}" stroke-width="2"/>')
# 沟道（3 段，分段表 N-MOS 增强型）
svg.append(f'<line x1="214" y1="510" x2="214" y2="536" stroke="{INK}" stroke-width="2.4"/>')
svg.append(f'<line x1="226" y1="510" x2="226" y2="516" stroke="{INK}" stroke-width="2.4"/>')
svg.append(f'<line x1="226" y1="522" x2="226" y2="526" stroke="{INK}" stroke-width="2.4"/>')
svg.append(f'<line x1="226" y1="532" x2="226" y2="536" stroke="{INK}" stroke-width="2.4"/>')
# 栅极（在沟道左，竖线）
svg.append(f'<line x1="206" y1="514" x2="206" y2="534" stroke="{INK}" stroke-width="2"/>')
# 栅连接
svg.append(f'<line x1="206" y1="524" x2="188" y2="524" stroke="{INK}" stroke-width="2"/>')
# 源极下出
svg.append(f'<line x1="220" y1="536" x2="220" y2="546" stroke="{INK}" stroke-width="2"/>')
# 箭头（体内二极管方向）
svg.append(f'<polygon points="217,522 221,526 217,530" fill="{INK}"/>')
svg.append(T(232, 528, "BSS138", 11, INK, w="bold"))

# OPA333 三角形（左侧）
svg.append(f'<polygon points="100,498 100,550 156,524" fill="#ffffff" stroke="{INK}" stroke-width="1.6"/>')
svg.append(T(114, 516, "+", 13, INK, w="bold"))
svg.append(T(114, 542, "−", 13, INK, w="bold"))
svg.append(T(128, 562, "OPA333", 11, GRAY, "middle"))
# 输出 → BSS138 栅
svg.append(f'<line x1="156" y1="524" x2="188" y2="524" stroke="{INK}" stroke-width="2"/>')
# 同相端 ← VSET
svg.append(f'<line x1="100" y1="512" x2="70" y2="512" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<rect x="28" y="498" width="42" height="30" fill="#f8fafc" stroke="{INK}" stroke-width="1.3"/>')
svg.append(T(49, 511, "VSET", 11, INK, "middle", "bold"))
svg.append(T(49, 524, "1.18V", 11, GRAY, "middle"))
# CURR_DIS
svg.append(f'<line x1="49" y1="528" x2="49" y2="544" stroke="{PURPLE}" stroke-width="1.3" stroke-dasharray="3,3"/>')
svg.append(T(49, 556, "PB10", 11, PURPLE, "middle", "bold"))

# BSS138 源极 → B 节点
svg.append(f'<circle cx="220" cy="546" r="3.6" fill="#111827"/>')
svg.append(T(228, 542, "B", 12, INK, w="bold"))
# B 反馈回 OPA333 反相端
svg.append(f'<polyline points="220,546 170,546 170,536 156,536" fill="none" stroke="{INK}" stroke-width="2"/>')
# B → Rsense
svg.append(f'<line x1="220" y1="546" x2="220" y2="568" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<rect x="210" y="568" width="20" height="46" fill="#f1f5f9" stroke="{INK}" stroke-width="1.4"/>')
svg.append(T(234, 584, "Rsense", 11, INK, w="bold"))
svg.append(T(234, 600, "150 kΩ·0.1%", 11, GRAY))
# Rsense → E
svg.append(f'<line x1="220" y1="614" x2="220" y2="638" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<circle cx="220" cy="638" r="3.6" fill="#111827"/>')
svg.append(T(212, 634, "E", 12, INK, "end", "bold"))
# E → GND
svg.append(f'<line x1="220" y1="638" x2="220" y2="652" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<line x1="208" y1="652" x2="232" y2="652" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<line x1="213" y1="657" x2="227" y2="657" stroke="{INK}" stroke-width="1.6"/>')
svg.append(f'<line x1="217" y1="662" x2="223" y2="662" stroke="{INK}" stroke-width="1.6"/>')
svg.append(T(28, 580, "低边恒流源", 11, INK, w="bold"))
svg.append(T(28, 596, "I=VSET/Rsense", 11, GRAY))

# ============================================================
# 跟随器区（x 480–620）：T/M/B 三颗 OPA388
# ============================================================
# 跟随器 T：V_P 继续向右 → OPA388 → AIN0P
svg.append(f'<line x1="500" y1="180" x2="540" y2="180" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<polygon points="540,160 540,200 596,180" fill="#ffffff" stroke="{INK}" stroke-width="1.6"/>')
svg.append(T(556, 184, "×1", 12, INK, w="bold"))
svg.append(T(568, 212, "OPA388(T)", 11, GRAY, "middle"))
svg.append(f'<line x1="596" y1="180" x2="700" y2="180" stroke="{INK}" stroke-width="2"/>')

# 跟随器 M：M → 上行 → OPA388 → AIN0N
svg.append(f'<line x1="430" y1="382" x2="480" y2="382" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<line x1="480" y1="382" x2="480" y2="290" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<line x1="480" y1="290" x2="540" y2="290" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<polygon points="540,270 540,310 596,290" fill="#ffffff" stroke="{INK}" stroke-width="1.6"/>')
svg.append(T(556, 294, "×1", 12, INK, w="bold"))
svg.append(T(568, 322, "OPA388(M)", 11, GRAY, "middle"))
svg.append(f'<line x1="596" y1="290" x2="700" y2="290" stroke="{INK}" stroke-width="2"/>')

# 跟随器 B：B → 右行 → 上行 → OPA388 → AIN1P
svg.append(f'<line x1="220" y1="546" x2="480" y2="546" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<line x1="480" y1="546" x2="480" y2="400" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<line x1="480" y1="400" x2="540" y2="400" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<polygon points="540,380 540,420 596,400" fill="#ffffff" stroke="{INK}" stroke-width="1.6"/>')
svg.append(T(556, 404, "×1", 12, INK, w="bold"))
svg.append(T(568, 432, "OPA388(B)", 11, GRAY, "middle"))
svg.append(f'<line x1="596" y1="400" x2="700" y2="400" stroke="{INK}" stroke-width="2"/>')

# ---- AIN1N：E 直连 ----
svg.append(f'<line x1="220" y1="638" x2="640" y2="638" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<line x1="640" y1="638" x2="640" y2="490" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<line x1="640" y1="490" x2="700" y2="490" stroke="{INK}" stroke-width="2"/>')
svg.append(T(430, 630, "AIN1N ← E（Kelvin 直连）", 11, BLUE))

# ============================================================
# ADS131A02 框（右区 x 700–798，y 130–560）
# ============================================================
svg.append(f'<rect x="700" y="150" width="98" height="380" fill="#eff6ff" stroke="{BLUE}" stroke-width="1.6"/>')
svg.append(T(749, 168, "ADS131A02", 11, "#1d4ed8", "middle", "bold"))
svg.append(T(749, 184, "24 bit ΣΔ", 11, "#1e3a8a", "middle"))
svg.append(T(749, 198, "内部基准 2.442 V", 11, "#1e3a8a", "middle"))
# 引脚（左侧，文本上移到导线之上）
svg.append(T(696, 172, "AIN0P", 11, "#1e3a8a", "end", "bold"))
svg.append(T(696, 282, "AIN0N", 11, "#1e3a8a", "end", "bold"))
svg.append(T(696, 392, "AIN1P", 11, "#1e3a8a", "end", "bold"))
svg.append(T(696, 482, "AIN1N", 11, "#1e3a8a", "end", "bold"))
# 右侧说明
svg.append(T(749, 220, "通道 0（样品）", 11, "#1e3a8a", "middle"))
svg.append(T(749, 440, "通道 1（Rsense）", 11, "#1e3a8a", "middle"))
svg.append(T(749, 510, "16.384 MHz", 11, "#1e3a8a", "middle"))
svg.append(T(749, 524, "SPI → MCU", 11, "#1e3a8a", "middle"))

# AAF lad4r 标注
svg.append(T(648, 172, "AAF", 11, GREEN, "middle", "bold"))
svg.append(T(648, 282, "AAF", 11, GREEN, "middle", "bold"))
svg.append(T(648, 392, "AAF", 11, GREEN, "middle", "bold"))

# ============================================================
# 图注（底部 y 700–790）
# ============================================================
svg.append(f'<rect x="28" y="700" width="770" height="92" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1"/>')
svg.append(T(38, 718, "图注与自查要点", 12, INK, w="bold"))
svg.append(T(38, 734, "① T 共用顶端（R_top/R_b 偏置 ~3.0 V），恒流源在低边；校准/零点样品回线断开=零电流；主图=校准态（全控制脚低）", 11, INK))
svg.append(T(38, 750, "② CH1 SPDT：COM=M · NO=V_N · NC=F；CH2/CH4 为 NC 默认合；零点=CH3/CH4 双断+CURR_DIS=1；Cff=100 pF 必装消 147 kHz 振荡", 11, INK))
svg.append(T(38, 766, "③ 跟随器仅缓冲 V_P/M/B（距轨 ≥0.15 V），AIN1N 直连 E；AAF lad4r 四级阶梯见《抗混叠滤波电路》；虚线框=板外器件", 11, INK))
svg.append(T(38, 782, "④ 测量时：SEL_SENSE=1（CH1→V_N，CH2 断，CH3 合）、SEL4=1（CH4 断）、CURR_DIS=0；双档切换仅在测量窗口外", 11, INK))

svg.append("</svg>")

OUT.write_text("\n".join(svg), encoding="utf-8")
print("written", OUT)
