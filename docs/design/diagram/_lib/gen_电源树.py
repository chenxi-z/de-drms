#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_电源树.py — DE-DRMS 电源树（SCI/A4 单栏 800×800 重绘）

依据 docs/design/diagram/电源树.svg（原 1500×900）重排，遵循：
  - 附录 E.8（电源）+ pin-assignment.md（2026-10-21 三排 + 2026-10-22 BQ 链三改）
  - scistyle.T()/rich() 逐段拆 run；字号下限 11
  - 配色：3.3V_A 红 #DC2626、3.3V_D 橙 #EA580C、电池/充电绿 #059669、控制紫虚线 #7C3AED

布局（顶 → 底）：
  y 86–150    源层：USB Type-C（左） | 1S 锂电（右）
  y 180–252   充电层：BQ24040（左下）
  y 280–344   分配层：电池节点 VBAT（垂直母线）
  y 344–432   LDO 层：数字 TPS7A0233（左） | 模拟 TPS7A2033（右）
  y 446       3.3V_D 输出横向母线（向 TF 卡分支）
  y 468–600   负载层：数字负载（左） | 模拟负载（中） | TF 卡 3V3_SD（右）
  y 620–716   监测层：ADC1 电压监测（左） | 电源域说明（右）
  y 736–790   图注
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from scistyle import T, rich, INK, PURPLE  # noqa: E402

W = H = 800

C_VD = "#EA580C"   # 3.3V_D 数字轨（橙）
C_VA = "#DC2626"   # 3.3V_A 模拟轨（红）
C_BAT = "#059669"  # 电池/充电（绿）
C_CTL = PURPLE     # 控制线（紫虚线 #7C3AED）
C_FRAME = INK      # 框 #1a1a1a
C_FILL = "#f1f5f9" # 器件填充
C_TXT = "#111827"
C_MUT = "#475569"
C_SUB = "#64748b"
C_SD = "#0284c7"   # 3V3_SD 支路蓝
C_SD_D = "#0c4a6e"
C_SD_F = "#e0f2fe"

parts = []
add = parts.append

add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
add(f'<rect x="0" y="0" width="{W}" height="{H}" fill="#ffffff"/>')

# ---------------- 头部 ----------------
add(T(30, 36, "电源树", 22, C_TXT, w="bold"))
add(T(30, 60, "1S 锂电 + BQ24040 + 双 LDO（数字 TPS7A0233 常开 / 模拟 TPS7A2033 EN 受控）",
     13, C_MUT))
add(T(770, 36, "附录 E.8 · 2026-10-22", 11, "#94a3b8", "end"))

# ---------------- 源层 ----------------
# USB Type-C（左上）
add(f'<rect x="60" y="86" width="170" height="64" rx="2" fill="{C_FILL}" stroke="{C_FRAME}" stroke-width="1.3"/>')
add(T(145, 110, "USB Type-C", 13, C_TXT, "middle", "bold"))
add(T(145, 130, "5V VBUS 输入", 11, C_MUT, "middle"))

# 电池（右上）
add(f'<rect x="570" y="86" width="170" height="64" rx="2" fill="{C_FILL}" stroke="{C_FRAME}" stroke-width="1.3"/>')
add(T(655, 108, "1S 锂电", 13, C_TXT, "middle", "bold"))
add(T(655, 126, "3.0–4.2 V · 103450", 11, C_MUT, "middle"))
add(T(655, 142, "带保护板", 11, C_SUB, "middle"))

# ---------------- 充电层 ----------------
add(f'<rect x="60" y="186" width="170" height="72" rx="2" fill="{C_FILL}" stroke="{C_FRAME}" stroke-width="1.3"/>')
add(T(145, 208, "BQ24040", 13, C_TXT, "middle", "bold"))
add(T(145, 226, "充电管理", 12, C_MUT, "middle"))
add(T(145, 244, "固定 500 mA", 11, C_SUB, "middle"))

# USB → BQ24040
add(f'<line x1="145" y1="150" x2="145" y2="186" stroke="{C_BAT}" stroke-width="2.5"/>')

# BQ24040 → 电池（横向 + 竖向）
add(f'<line x1="230" y1="222" x2="490" y2="222" stroke="{C_BAT}" stroke-width="2.5"/>')
add(f'<line x1="490" y1="222" x2="490" y2="118" stroke="{C_BAT}" stroke-width="2.5"/>')
add(f'<line x1="490" y1="118" x2="570" y2="118" stroke="{C_BAT}" stroke-width="2.5"/>')
add(T(360, 214, "充电路径", 11, C_BAT, "middle"))

# BQ24040 状态（PG → PB5、CHG → PC2）—— 紫色虚线，从 BQ24040 下方出
# 注意：虚线不可穿过自己的文字 → 虚线在左，文字在右；虚线终点避开文字包围盒
add(f'<line x1="90" y1="258" x2="90" y2="292" stroke="{C_CTL}" stroke-width="1.3" stroke-dasharray="5,4"/>')
add(T(96, 274, "PG → PB5", 11, C_CTL))
add(T(96, 290, "CHG → PC2", 11, C_CTL))

# ---------------- 分配层：电池节点 ----------------
# 电池底部下行
add(f'<line x1="655" y1="150" x2="655" y2="316" stroke="{C_BAT}" stroke-width="3"/>')

# VBAT 母线（横向，y=316）
add(f'<line x1="280" y1="316" x2="655" y2="316" stroke="{C_BAT}" stroke-width="2.5"/>')
# 结点
add(f'<circle cx="655" cy="316" r="4" fill="{C_BAT}"/>')
add(f'<circle cx="490" cy="316" r="3.5" fill="{C_BAT}"/>')
add(f'<circle cx="280" cy="316" r="3.5" fill="{C_BAT}"/>')
add(T(666, 310, "VBAT", 12, C_BAT, w="bold"))

# ---------------- LDO 层 ----------------
# 数字 LDO（左）
add(f'<line x1="280" y1="316" x2="280" y2="344" stroke="{C_VD}" stroke-width="2.5"/>')
add(f'<rect x="180" y="344" width="200" height="88" rx="2" fill="#fdf2e3" stroke="{C_VD}" stroke-width="1.6"/>')
add(T(280, 366, "TPS7A0233", 13, C_VD, "middle", "bold"))
add(T(280, 384, "3.3V_D 数字域", 12, C_VD, "middle", "bold"))
add(T(280, 402, "Iq 25 nA · 常开", 11, C_MUT, "middle"))
add(T(280, 420, "200 mA · ±1.5%", 11, C_SUB, "middle"))

# 模拟 LDO（右）
add(f'<line x1="490" y1="316" x2="490" y2="344" stroke="{C_VA}" stroke-width="2.5"/>')
add(f'<rect x="390" y="344" width="200" height="88" rx="2" fill="#fde8e8" stroke="{C_VA}" stroke-width="1.6"/>')
add(T(490, 366, "TPS7A2033", 13, C_VA, "middle", "bold"))
add(T(490, 384, "3.3V_A 模拟域", 12, C_VA, "middle", "bold"))
add(T(490, 402, "Iq 6.5 µA · 7 µVrms", 11, C_MUT, "middle"))
add(T(490, 420, "300 mA · ±1.5%", 11, C_SUB, "middle"))

# ANA_EN 控制线
add(f'<line x1="590" y1="388" x2="622" y2="388" stroke="{C_CTL}" stroke-width="1.3" stroke-dasharray="5,4"/>')
add(T(626, 382, "EN = PC3", 11, C_CTL))
add(T(626, 398, "(ANA_EN)", 11, C_CTL))

# ---------------- 负载层 ----------------
# 数字 LDO → 数字域负载
add(f'<line x1="280" y1="432" x2="280" y2="446" stroke="{C_VD}" stroke-width="2.5"/>')
# 3.3V_D 输出横向母线（含 TF 卡分支）
add(f'<line x1="170" y1="446" x2="705" y2="446" stroke="{C_VD}" stroke-width="2.5"/>')
add(f'<circle cx="280" cy="446" r="3.5" fill="{C_VD}"/>')
add(f'<circle cx="170" cy="446" r="3.5" fill="{C_VD}"/>')
add(f'<circle cx="705" cy="446" r="3.5" fill="{C_VD}"/>')
add(T(585, 440, "3.3V_D", 11, C_VD, w="bold"))
# 母线下行到数字负载框
add(f'<line x1="170" y1="446" x2="170" y2="468" stroke="{C_VD}" stroke-width="2.5"/>')
# TF 卡分支下行
add(f'<line x1="705" y1="446" x2="705" y2="468" stroke="{C_VD}" stroke-width="2.5"/>')

# 数字域负载框
add(f'<rect x="60" y="468" width="220" height="132" rx="2" fill="#fdf2e3" stroke="{C_VD}" stroke-width="1.3"/>')
add(T(170, 488, "数字域负载", 13, C_VD, "middle", "bold"))
add(T(70, 510, "MCU STM32U545", 11, C_TXT))
add(T(70, 528, "  13.5 mA @160 MHz", 11, C_MUT))
add(T(70, 546, "ADS131A02 IOVDD 0.6 mA", 11, C_TXT))
add(T(70, 564, "TMP117+USB+LED ~30 mA", 11, C_TXT))
add(T(70, 582, "TMUX SEL (漏电 ≤50 pA)", 11, C_TXT))
add(T(170, 596, "总 < 50 mA", 12, C_VD, "middle", "bold"))

# 模拟 LDO → 模拟域负载
add(f'<line x1="490" y1="432" x2="490" y2="468" stroke="{C_VA}" stroke-width="2.5"/>')
add(f'<rect x="380" y="468" width="220" height="132" rx="2" fill="#fde8e8" stroke="{C_VA}" stroke-width="1.3"/>')
add(T(490, 488, "模拟域负载", 13, C_VA, "middle", "bold"))
add(T(390, 510, "ADS131A02 AVDD 3.2 mA", 11, C_TXT))
add(T(390, 528, "OPA388 ×3 (1.7–2.6 mA/颗)", 11, C_TXT))
add(T(390, 546, "OPA333 恒流源 0.017 mA", 11, C_TXT))
add(T(390, 564, "TMUX 模拟侧 + VSET", 11, C_TXT))
add(T(390, 582, "R_top / R_b 偏置", 11, C_TXT))
add(T(490, 596, "总 < 15 mA", 12, C_VA, "middle", "bold"))

# TF 卡支路框
add(f'<rect x="640" y="468" width="130" height="132" rx="2" fill="{C_SD_F}" stroke="{C_SD}" stroke-width="1.3"/>')
add(T(705, 488, "3V3_SD 支路", 12, C_SD_D, "middle", "bold"))
add(T(705, 506, "(TF 卡)", 11, C_TXT, "middle"))
add(T(650, 526, "高边开关", 11, C_TXT))
add(T(650, 542, "TPS22917", 11, C_TXT))
add(T(650, 560, "默认断电", 11, C_MUT))
add(T(650, 578, "卡待机 50–100", 11, C_MUT))
add(T(650, 594, "µA → 0", 11, C_MUT))

# SD_PWR_EN 控制线（从 TF 框底向下，文字紧随其后）
add(f'<line x1="705" y1="600" x2="705" y2="604" stroke="{C_CTL}" stroke-width="1.3" stroke-dasharray="3,2"/>')
add(T(705, 614, "SD_PWR_EN = PA8", 11, C_CTL, "middle"))

# ---------------- 监测层 ----------------
# VBAT / VBUS 监测：两条虚线沿左边缘下行，路径上不标（监测框内已说明）
# VBAT：从 VBAT 母线 y=316 左延至 x=42，再下行至监测框顶
add(f'<line x1="42" y1="316" x2="280" y2="316" stroke="{C_BAT}" stroke-width="1.5" stroke-dasharray="3,3"/>')
add(f'<line x1="42" y1="316" x2="42" y2="660" stroke="{C_BAT}" stroke-width="1.5" stroke-dasharray="3,3"/>')
add(f'<line x1="42" y1="660" x2="60" y2="660" stroke="{C_BAT}" stroke-width="1.5" stroke-dasharray="3,3"/>')
# VBUS：从 USB 框左边 (x=60) 向左到 x=18，下行至监测框顶
add(f'<line x1="60" y1="118" x2="18" y2="118" stroke="#374151" stroke-width="1.5" stroke-dasharray="3,3"/>')
add(f'<line x1="18" y1="118" x2="18" y2="678" stroke="#374151" stroke-width="1.5" stroke-dasharray="3,3"/>')
add(f'<line x1="18" y1="678" x2="60" y2="678" stroke="#374151" stroke-width="1.5" stroke-dasharray="3,3"/>')
# 路径端点小标签：紧跟框顶上方 y=612 空隙（监测框 y=620 起，上方有 y=600-618 空 18px）
# 数字负载框 y=468-600 占 x=60-280；此带 x=285-400 空白
add(T(285, 612, "VBAT→PC0 / VBUS→PC1", 11, C_MUT))

# 监测框
add(f'<rect x="60" y="620" width="340" height="96" rx="2" fill="{C_FILL}" stroke="{C_FRAME}" stroke-width="1.3"/>')
add(T(75, 640, "电压监测（内部 ADC1）", 12, C_TXT, w="bold"))
add(T(75, 660, "PC0 = VBAT_MON：2×1 MΩ 分压，常通 ~2 µA", 11, C_TXT))
add(T(75, 678, "PC1 = VBUS_MON：1 MΩ / 1 MΩ 分压，阈值 3.70 V", 11, C_TXT))
add(T(75, 696, "采样 ≥64 周期（100 nF 电荷池合法）", 11, C_MUT))

# 电源域说明
add(f'<rect x="420" y="620" width="350" height="96" rx="2" fill="{C_FILL}" stroke="{C_FRAME}" stroke-width="1.3"/>')
add(T(435, 640, "电源域划分", 12, C_TXT, w="bold"))
add(rich(435, 658, [("3.3V_D", ""), ("：MCU、IOVDD、USB、LED、TMP117、TF(开关)", "")], 11, C_VD))
add(rich(435, 676, [("3.3V_A", ""), ("：AVDD、OPA388×3、OPA333、TMUX 模拟侧", "")], 11, C_VA))
add(T(435, 694, "待机 ~10.8 µA · 测量窗口模拟域 +15 mA", 11, C_MUT))

# ---------------- 图注 ----------------
add(T(30, 736, "图注与自查要点：", 12, C_TXT, w="bold"))
add(T(30, 754, "1. 数字轨常开（Iq 25 nA）；模拟轨 EN=PC3 受控（Iq 6.5 µA），仅测量窗口上电", 11, C_TXT))
add(T(30, 770, "2. 充电固定 500 mA（R6=2 kΩ 挂 ISET1、ISET2 直连 GND）；PG/CHG 开漏入 PB5/PC2", 11, C_TXT))
add(T(30, 786, "3. TF 卡供电由 SD_PWR_EN=PA8 高边开关控制，默认断电（卡待机 50–100 µA 归零）", 11, C_TXT))

add('</svg>')

out = os.path.join(os.path.dirname(HERE), "电源树.svg")
with open(out, "w", encoding="utf-8") as f:
    f.write("\n".join(parts))
print(f"written {out}")
