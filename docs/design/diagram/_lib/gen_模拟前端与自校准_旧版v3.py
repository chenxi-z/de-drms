#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_模拟前端与自校准_旧版v3.py — 800×800 SCI 版式重绘（旧版 v3 留档）

历史留档：本图对应 2026-10-18 版（v3），与现行 v4 终案并存。
v3 与 v4 的关键差异：
  - 无 Cff（消振荡电容 v4 才引入）
  - 切换网络为分立 SPST 方案：K1(NO)/K2(NC)/K3(NO)/K4(NC)/K5(NC)，
    各自由 SEL_SENSE(PB2) 或 SEL4(PB0) 控制；v4 整合为单颗 TMUX1134 SPDT。
  - Rsense 在源极路径（同 v4），但本图未画 AAF/双档 ISET。

布局（800×800）：
  左区 x 28–430 ：偏置 R_top/R_b、T 总线、样品、R_ref、K1/K2/K3/K4/K5、低边恒流源
  中区 x 430–560：跟随器 V_P/M/B（OPA388 ×3）
  右区 x 560–798：ADS131A02 框 + 顶部 MCU GPIO 摘要
  底部 y 700–790：图注 4 行
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from scistyle import T, rich, head, INK, GREEN, ORANGE, PURPLE, BLUE, GRAY  # noqa

OUT = Path("/media/anning/data/Project/DE-DRMS/docs/design/diagram/模拟前端与自校准_旧版v3.svg")

svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="800" height="800" viewBox="0 0 800 800"',
       '     font-family="\'Noto Serif CJK SC\',\'Noto Serif SC\',serif">',
       '<rect width="800" height="800" fill="#ffffff"/>']

svg += head("模拟前端与自校准电路（旧版 v3 留档）",
            "低边恒流 7.86 µA · 分立 SPST 开关 K1–K5 · 无 Cff · 主图=校准态（全控制脚低）")

# ============================================================
# 顶部 MCU GPIO 摘要条（横贯右区，不占主图）
# ============================================================
svg.append(f'<rect x="430" y="80" width="368" height="56" fill="#faf5ff" stroke="{PURPLE}" stroke-width="1.2"/>')
svg.append(T(440, 98, "MCU GPIO", 11, PURPLE, w="bold"))
svg.append(T(500, 98, "SEL_SENSE=PB2 → K1/K3/K5 同沿", 11, INK))
svg.append(T(440, 114, "SEL4=PB0 → K2", 11, INK))
svg.append(T(560, 114, "K4 由 PB2 同沿（原图如此）", 11, GRAY))
svg.append(T(440, 130, "CURR_DIS=PB10（拉低 VSET = 零电流）", 11, INK))
svg.append(T(680, 130, "主图=校准态", 11, GRAY))

# ============================================================
# 上区 y 150–370：偏置 + T 总线 + 样品 + R_ref
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
svg.append(f'<line x1="40" y1="240" x2="440" y2="240" stroke="{INK}" stroke-width="2.2"/>')
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

# ---- K5·NC（V_P 并回 T，x=440 处 V_P 下至 T）—— v3 用 K5 编号
svg.append(f'<line x1="440" y1="180" x2="440" y2="196" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<circle cx="440" cy="196" r="3" fill="#ffffff" stroke="{INK}" stroke-width="1.6"/>')
svg.append(f'<circle cx="440" cy="240" r="3" fill="#ffffff" stroke="{INK}" stroke-width="1.6"/>')
# 刀臂默认 NC（合）
svg.append(f'<line x1="440" y1="196" x2="440" y2="237" stroke="{INK}" stroke-width="1.7"/>')
svg.append(T(448, 218, "K5·NC", 11, PURPLE, w="bold"))
# 控制线
svg.append(f'<line x1="460" y1="240" x2="444" y2="240" stroke="{PURPLE}" stroke-width="1.3" stroke-dasharray="3,3"/>')
svg.append(f'<circle cx="443" cy="240" r="2.2" fill="#ffffff" stroke="{PURPLE}" stroke-width="1.2"/>')
svg.append(T(464, 244, "PB2", 11, PURPLE))

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
svg.append(f'<line x1="300" y1="240" x2="300" y2="258" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<rect x="290" y="258" width="20" height="50" fill="#f1f5f9" stroke="{INK}" stroke-width="1.4"/>')
svg.append(T(314, 272, "R_ref", 11, INK, w="bold"))
svg.append(T(314, 288, "100 kΩ", 11, INK, w="bold"))
svg.append(T(314, 302, "0.01%", 11, GRAY))
svg.append(f'<line x1="300" y1="308" x2="300" y2="392" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<circle cx="300" cy="392" r="3.6" fill="#111827"/>')
svg.append(T(292, 386, "F", 12, INK, "end", "bold"))

# ---- K3·NO（V_N → M，v3 分立方案：独立 SPST）----
svg.append(f'<line x1="230" y1="370" x2="270" y2="370" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<circle cx="270" cy="370" r="3" fill="#ffffff" stroke="{INK}" stroke-width="1.6"/>')
svg.append(f'<circle cx="310" cy="370" r="3" fill="#ffffff" stroke="{INK}" stroke-width="1.6"/>')
# 刀臂默认开
svg.append(f'<line x1="310" y1="370" x2="278" y2="362" stroke="{INK}" stroke-width="1.7"/>')
svg.append(T(258, 352, "K3·NO", 11, PURPLE, w="bold"))
# 控制线
svg.append(f'<line x1="290" y1="370" x2="290" y2="344" stroke="{PURPLE}" stroke-width="1.3" stroke-dasharray="3,3"/>')
svg.append(f'<circle cx="290" cy="370" r="2.2" fill="#ffffff" stroke="{PURPLE}" stroke-width="1.2"/>')
svg.append(T(254, 340, "PB2", 11, PURPLE, "end"))
# K3 右端继续到 M 节点
svg.append(f'<line x1="310" y1="370" x2="370" y2="370" stroke="{INK}" stroke-width="2"/>')

# ---- K4·NC（F → M，v3 分立方案：独立 SPST，与 K3 并联到 M）----
# F 节点向下延至 y=420 走 K4
svg.append(f'<line x1="300" y1="392" x2="300" y2="420" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<line x1="300" y1="420" x2="330" y2="420" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<circle cx="330" cy="420" r="3" fill="#ffffff" stroke="{INK}" stroke-width="1.6"/>')
svg.append(f'<circle cx="370" cy="420" r="3" fill="#ffffff" stroke="{INK}" stroke-width="1.6"/>')
# 刀臂默认合（NC 闭合）
svg.append(f'<line x1="330" y1="420" x2="367" y2="420" stroke="{INK}" stroke-width="1.7"/>')
svg.append(T(336, 408, "K4·NC", 11, PURPLE, w="bold"))
# 控制线（标签放线右侧，y 与刀臂平齐，避开 K2 的 PB0）
svg.append(f'<line x1="350" y1="420" x2="350" y2="444" stroke="{PURPLE}" stroke-width="1.3" stroke-dasharray="3,3"/>')
svg.append(f'<circle cx="350" cy="420" r="2.2" fill="#ffffff" stroke="{PURPLE}" stroke-width="1.2"/>')
svg.append(T(356, 440, "PB2", 11, PURPLE))
# K4 右端上行汇到 M
svg.append(f'<line x1="370" y1="420" x2="370" y2="370" stroke="{INK}" stroke-width="2"/>')

# ---- M 节点 ----
svg.append(f'<circle cx="370" cy="370" r="3.6" fill="#111827"/>')
svg.append(T(376, 366, "M", 12, INK, w="bold"))
# M 向右到跟随器
svg.append(f'<line x1="370" y1="370" x2="430" y2="370" stroke="{INK}" stroke-width="2"/>')

# ---- K1·NO（S → X，v3 编号）----
svg.append(f'<line x1="140" y1="392" x2="140" y2="424" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<circle cx="140" cy="424" r="3" fill="#ffffff" stroke="{INK}" stroke-width="1.6"/>')
svg.append(f'<circle cx="140" cy="458" r="3" fill="#ffffff" stroke="{INK}" stroke-width="1.6"/>')
# 刀臂默认开
svg.append(f'<line x1="140" y1="458" x2="152" y2="428" stroke="{INK}" stroke-width="1.7"/>')
svg.append(T(108, 442, "K1·NO", 11, PURPLE, "end", "bold"))
svg.append(f'<line x1="180" y1="442" x2="152" y2="442" stroke="{PURPLE}" stroke-width="1.3" stroke-dasharray="3,3"/>')
svg.append(f'<circle cx="150" cy="442" r="2.2" fill="#ffffff" stroke="{PURPLE}" stroke-width="1.2"/>')
svg.append(T(184, 446, "PB2", 11, PURPLE))
svg.append(f'<line x1="140" y1="458" x2="140" y2="480" stroke="{INK}" stroke-width="2"/>')

# ---- K2·NC（F → X，v3 编号；注意 F 同时进 K4 与 K2，v3 拓扑如此）----
# 从 F (300,392) 再向下另一路到 K2（y=460 处）
svg.append(f'<line x1="300" y1="420" x2="300" y2="446" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<circle cx="300" cy="446" r="3" fill="#ffffff" stroke="{INK}" stroke-width="1.6"/>')
svg.append(f'<circle cx="300" cy="480" r="3" fill="#ffffff" stroke="{INK}" stroke-width="1.6"/>')
# 刀臂默认合
svg.append(f'<line x1="300" y1="446" x2="300" y2="477" stroke="{INK}" stroke-width="1.7"/>')
svg.append(T(316, 454, "K2·NC", 11, PURPLE, w="bold"))
svg.append(f'<line x1="348" y1="464" x2="304" y2="464" stroke="{PURPLE}" stroke-width="1.3" stroke-dasharray="3,3"/>')
svg.append(f'<circle cx="303" cy="464" r="2.2" fill="#ffffff" stroke="{PURPLE}" stroke-width="1.2"/>')
svg.append(T(352, 468, "PB0", 11, PURPLE))
svg.append(f'<line x1="300" y1="480" x2="300" y2="500" stroke="{INK}" stroke-width="2"/>')

# ---- X 汇合（恒流源顶端入口）----
svg.append(f'<line x1="140" y1="480" x2="140" y2="500" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<line x1="140" y1="500" x2="300" y2="500" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<circle cx="220" cy="500" r="3.6" fill="#111827"/>')
svg.append(T(228, 496, "X", 12, INK, w="bold"))

# ============================================================
# 下区 y 500–680：低边恒流源（与 v4 相同拓扑）
# ============================================================
# X → BSS138 漏极
svg.append(f'<line x1="220" y1="500" x2="220" y2="520" stroke="{INK}" stroke-width="2"/>')
# BSS138 符号
svg.append(f'<line x1="220" y1="520" x2="220" y2="530" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<line x1="214" y1="530" x2="214" y2="556" stroke="{INK}" stroke-width="2.4"/>')
svg.append(f'<line x1="226" y1="530" x2="226" y2="536" stroke="{INK}" stroke-width="2.4"/>')
svg.append(f'<line x1="226" y1="542" x2="226" y2="546" stroke="{INK}" stroke-width="2.4"/>')
svg.append(f'<line x1="226" y1="552" x2="226" y2="556" stroke="{INK}" stroke-width="2.4"/>')
svg.append(f'<line x1="206" y1="534" x2="206" y2="554" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<line x1="206" y1="544" x2="188" y2="544" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<line x1="220" y1="556" x2="220" y2="566" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<polygon points="217,542 221,546 217,550" fill="{INK}"/>')
svg.append(T(232, 548, "BSS138", 11, INK, w="bold"))

# OPA333 三角形
svg.append(f'<polygon points="100,518 100,570 156,544" fill="#ffffff" stroke="{INK}" stroke-width="1.6"/>')
svg.append(T(114, 536, "+", 13, INK, w="bold"))
svg.append(T(114, 562, "−", 13, INK, w="bold"))
svg.append(T(128, 582, "OPA333", 11, GRAY, "middle"))
svg.append(f'<line x1="156" y1="544" x2="188" y2="544" stroke="{INK}" stroke-width="2"/>')
# VSET
svg.append(f'<line x1="100" y1="532" x2="70" y2="532" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<rect x="28" y="518" width="42" height="30" fill="#f8fafc" stroke="{INK}" stroke-width="1.3"/>')
svg.append(T(49, 531, "VSET", 11, INK, "middle", "bold"))
svg.append(T(49, 544, "1.18V", 11, GRAY, "middle"))
# CURR_DIS
svg.append(f'<line x1="49" y1="548" x2="49" y2="564" stroke="{PURPLE}" stroke-width="1.3" stroke-dasharray="3,3"/>')
svg.append(T(49, 576, "PB10", 11, PURPLE, "middle", "bold"))

# B 节点
svg.append(f'<circle cx="220" cy="566" r="3.6" fill="#111827"/>')
svg.append(T(228, 562, "B", 12, INK, w="bold"))
svg.append(f'<polyline points="220,566 170,566 170,556 156,556" fill="none" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<line x1="220" y1="566" x2="220" y2="588" stroke="{INK}" stroke-width="2"/>')
# Rsense
svg.append(f'<rect x="210" y="588" width="20" height="46" fill="#f1f5f9" stroke="{INK}" stroke-width="1.4"/>')
svg.append(T(234, 604, "Rsense", 11, INK, w="bold"))
svg.append(T(234, 620, "150 kΩ·0.1%", 11, GRAY))
svg.append(f'<line x1="220" y1="634" x2="220" y2="658" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<circle cx="220" cy="658" r="3.6" fill="#111827"/>')
svg.append(T(212, 654, "E", 12, INK, "end", "bold"))
svg.append(f'<line x1="220" y1="658" x2="220" y2="672" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<line x1="208" y1="672" x2="232" y2="672" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<line x1="213" y1="677" x2="227" y2="677" stroke="{INK}" stroke-width="1.6"/>')
svg.append(f'<line x1="217" y1="682" x2="223" y2="682" stroke="{INK}" stroke-width="1.6"/>')
svg.append(T(28, 600, "低边恒流源", 11, INK, w="bold"))
svg.append(T(28, 616, "I=VSET/Rsense", 11, GRAY))

# ============================================================
# 跟随器区（x 480–620）：V_P/M/B 三颗 OPA388
# ============================================================
# 跟随器 T：V_P 继续向右
svg.append(f'<line x1="500" y1="180" x2="540" y2="180" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<polygon points="540,160 540,200 596,180" fill="#ffffff" stroke="{INK}" stroke-width="1.6"/>')
svg.append(T(556, 184, "×1", 12, INK, w="bold"))
svg.append(T(568, 212, "OPA388(V_P)", 11, GRAY, "middle"))
svg.append(f'<line x1="596" y1="180" x2="700" y2="180" stroke="{INK}" stroke-width="2"/>')

# 跟随器 M
svg.append(f'<line x1="430" y1="370" x2="480" y2="370" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<line x1="480" y1="370" x2="480" y2="290" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<line x1="480" y1="290" x2="540" y2="290" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<polygon points="540,270 540,310 596,290" fill="#ffffff" stroke="{INK}" stroke-width="1.6"/>')
svg.append(T(556, 294, "×1", 12, INK, w="bold"))
svg.append(T(568, 322, "OPA388(M)", 11, GRAY, "middle"))
svg.append(f'<line x1="596" y1="290" x2="700" y2="290" stroke="{INK}" stroke-width="2"/>')

# 跟随器 B
svg.append(f'<line x1="220" y1="566" x2="480" y2="566" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<line x1="480" y1="566" x2="480" y2="400" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<line x1="480" y1="400" x2="540" y2="400" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<polygon points="540,380 540,420 596,400" fill="#ffffff" stroke="{INK}" stroke-width="1.6"/>')
svg.append(T(556, 404, "×1", 12, INK, w="bold"))
svg.append(T(568, 432, "OPA388(B)", 11, GRAY, "middle"))
svg.append(f'<line x1="596" y1="400" x2="700" y2="400" stroke="{INK}" stroke-width="2"/>')

# ---- AIN1N：E 直连 ----
svg.append(f'<line x1="220" y1="658" x2="640" y2="658" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<line x1="640" y1="658" x2="640" y2="490" stroke="{INK}" stroke-width="2"/>')
svg.append(f'<line x1="640" y1="490" x2="700" y2="490" stroke="{INK}" stroke-width="2"/>')
svg.append(T(430, 650, "AIN1N ← E（Kelvin 直连）", 11, BLUE))

# ============================================================
# ADS131A02 框（右区 x 700–798，y 150–530）
# ============================================================
svg.append(f'<rect x="700" y="150" width="98" height="380" fill="#eff6ff" stroke="{BLUE}" stroke-width="1.6"/>')
svg.append(T(749, 168, "ADS131A02", 11, "#1d4ed8", "middle", "bold"))
svg.append(T(749, 184, "24 bit ΣΔ", 11, "#1e3a8a", "middle"))
svg.append(T(749, 198, "内部基准 2.442 V", 11, "#1e3a8a", "middle"))
svg.append(T(696, 172, "AIN0P", 11, "#1e3a8a", "end", "bold"))
svg.append(T(696, 282, "AIN0N", 11, "#1e3a8a", "end", "bold"))
svg.append(T(696, 392, "AIN1P", 11, "#1e3a8a", "end", "bold"))
svg.append(T(696, 482, "AIN1N", 11, "#1e3a8a", "end", "bold"))
svg.append(T(749, 220, "通道 0（样品）", 11, "#1e3a8a", "middle"))
svg.append(T(749, 440, "通道 1（Rsense）", 11, "#1e3a8a", "middle"))
svg.append(T(749, 510, "16.384 MHz", 11, "#1e3a8a", "middle"))
svg.append(T(749, 524, "SPI → MCU", 11, "#1e3a8a", "middle"))

# ============================================================
# 图注（底部 y 700–790）
# ============================================================
svg.append(f'<rect x="28" y="700" width="770" height="92" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1"/>')
svg.append(T(38, 718, "图注（旧版 v3 留档）", 12, INK, w="bold"))
svg.append(T(38, 734, "① T 共用顶端（R_top/R_b 偏置 ~3.0 V）；恒流源在低边，Rsense 在 BSS138 源极路径；校准/零点样品回线断开=零电流", 11, INK))
svg.append(T(38, 750, "② 分立 SPST：K1(S→X, NO)、K2(F→X, NC)、K3(V_N→M, NO)、K4(F→M, NC)、K5(V_P↔T, NC)；K1/K3/K5=PB2，K2/K4=PB0/PB2", 11, INK))
svg.append(T(38, 766, "③ 主图=校准态（全控制脚低）：K2/K4/K5 闭合、K1/K3 断开 → V_P=T、M=F（R_ref 接入）；测量=PB2/PB0 高", 11, INK))
svg.append(T(38, 782, "④ 跟随器仅缓冲 V_P/M/B（距轨 ≥0.15 V），AIN1N 直连 E（Kelvin）；本图无 Cff、无 AAF 分级、无双档 ISET（v4 才引入）", 11, INK))

svg.append("</svg>")

OUT.write_text("\n".join(svg), encoding="utf-8")
print("written", OUT)
