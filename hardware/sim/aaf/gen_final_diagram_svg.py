# -*- coding: utf-8 -*-
"""gen_final_diagram_svg.py — B 案定版《抗混叠滤波电路.svg》生成器
三级无源阶梯：每线 R1(6.19)+C(68n) → R2(6.04)+C(68n) → R3(13.7)+C(27n) + C_diff(12n)
主干分段画（电阻接在段间断口），避免导线穿过器件；结点实心圆，端子白底圆。
"""
from __future__ import annotations
import io, sys

W, H = 1600, 1200
OUT: list[str] = []
push = OUT.append

# ---------- 坐标 ----------
yP, yN = 300, 520          # P/N 主干 y
GND = 640                  # 地母线 y
R1x, R2x, R3x = 380, 600, 820
RES_W, RES_H = 64, 26
srcX = 230                 # 跟随器框右缘
outX = 1060                # 差分电容后的出口点
pinX = 1140                # ADC 框左缘
CDx = 990                  # C_diff x

def res_h(cx: int, y: int, label: str, val: str):
    """水平电阻：主干在 y 处断开 [cx-RES_W/2, cx+RES_W/2]，电阻矩形接上"""
    hw = RES_W // 2
    push(f'<line x1="{{L}}" y1="{y}" x2="{cx-hw}" y2="{y}" class="w"/>')
    push(f'<rect x="{cx-hw}" y="{y-RES_H//2}" width="{RES_W}" height="{RES_H}" class="box"/>')
    push(f'<line x1="{cx+hw}" y1="{y}" x2="{{R}}" y2="{y}" class="w"/>')
    push(f'<text x="{cx}" y="{y-16}" font-size="12.5" font-weight="bold" fill="#374151" text-anchor="middle">{label} {val}</text>')

GND_TOP = 208   # P 线电容的接地母线（上方）
def cap_g(x: int, y_top: int, label: str, val: str, up: bool = False):
    """对地电容：up=False 从主干向下接底母线 GND；up=True 向上接顶母线 GND_TOP"""
    if up:
        b1, b2 = y_top - 44, y_top - 36   # 板对（上负下正序不影响无源电容）
        push(f'<line x1="{x}" y1="{b2}" x2="{x}" y2="{y_top}" class="w"/>')  # 板下引线到主干
        push(f'<line x1="{x-16}" y1="{b1}" x2="{x+16}" y2="{b1}" stroke="#374151" stroke-width="2.6"/>')
        push(f'<line x1="{x-16}" y1="{b2}" x2="{x+16}" y2="{b2}" stroke="#374151" stroke-width="2.6"/>')
        push(f'<line x1="{x}" y1="{b1}" x2="{x}" y2="{GND_TOP}" class="w"/>')
        push(f'<circle cx="{x}" cy="{GND_TOP}" r="4" fill="#111827"/>')
        push(f'<text x="{x+22}" y="{b1+16}" font-size="12" font-weight="bold" fill="#7c3aed">{label} {val}</text>')
    else:
        b1, b2 = y_top + 36, y_top + 44
        push(f'<line x1="{x}" y1="{y_top}" x2="{x}" y2="{b1}" class="w"/>')
        push(f'<line x1="{x-16}" y1="{b1}" x2="{x+16}" y2="{b1}" stroke="#374151" stroke-width="2.6"/>')
        push(f'<line x1="{x-16}" y1="{b2}" x2="{x+16}" y2="{b2}" stroke="#374151" stroke-width="2.6"/>')
        push(f'<line x1="{x}" y1="{b2}" x2="{x}" y2="{GND}" class="w"/>')
        push(f'<circle cx="{x}" cy="{GND}" r="4" fill="#111827"/>')
        push(f'<text x="{x+22}" y="{b1+8}" font-size="12" font-weight="bold" fill="#7c3aed">{label} {val}</text>')

def cap_d(x: int, y_t: int, y_b: int, label: str, val: str):
    """差分电容：跨 y_t 与 y_b"""
    mid = (y_t + y_b) // 2
    push(f'<line x1="{x}" y1="{y_t}" x2="{x}" y2="{mid-22}" class="w"/>')
    push(f'<line x1="{x}" y1="{mid+22}" x2="{x}" y2="{y_b}" class="w"/>')
    push(f'<line x1="{x-16}" y1="{mid-22}" x2="{x+16}" y2="{mid-22}" stroke="#374151" stroke-width="2.6"/>')
    push(f'<line x1="{x-16}" y1="{mid+22}" x2="{x+16}" y2="{mid+22}" stroke="#374151" stroke-width="2.6"/>')
    push(f'<text x="{x-24}" y="{mid-8}" font-size="12.5" font-weight="bold" fill="#7c3aed" text-anchor="end">{label}</text>')
    push(f'<text x="{x-24}" y="{mid+10}" font-size="12" font-weight="bold" fill="#7c3aed" text-anchor="end">{val}</text>')

# ---------- 头部 ----------
push(f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"
     font-family="'Noto Sans CJK SC','Noto Sans SC','Source Han Sans SC','PingFang SC','Microsoft YaHei',sans-serif">
<style>
  .w   {{ stroke:#374151; stroke-width:2;   fill:none }}
  .wg  {{ stroke:#059669; stroke-width:3.5; fill:none }}
  .box {{ fill:#f1f5f9; stroke:#374151; stroke-width:1.8 }}
  .adcbx {{ fill:#eff6ff; stroke:#2563eb; stroke-width:2 }}
  .panel {{ fill:#ffffff; stroke:#cbd5e1; stroke-width:1.4 }}
</style>
<defs>
  <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
    <path d="M20,0 L0,0 0,20" fill="none" stroke="#eef2f7" stroke-width="1"/>
  </pattern>
</defs>
<rect width="{W}" height="{H}" fill="#ffffff"/>
<rect width="{W}" height="{H}" fill="url(#grid)"/>
<text x="40" y="56" font-size="27" font-weight="bold" fill="#111827">抗混叠滤波电路（B 案定版 · 三级无源阶梯）</text>
<text x="40" y="84" font-size="12.5" fill="#64748b">每线 6.19Ω+68nF → 6.04Ω+68nF → 13.7Ω+27nF（对地）+ 末级 12nF 差分 · 真实 OPA388 模型口径 · 规格 v4</text>
<text x="{W-40}" y="56" font-size="12" fill="#94a3b8" text-anchor="end">R5 第4轮定档 · 2026-10-19</text>
<text x="{W-40}" y="84" font-size="12" fill="#94a3b8" text-anchor="end">抗混叠锚点 fMOD = 4.096 MHz · MCLK = 16.384 MHz</text>''')

# ---------- 跟随器源 ----------
push(f'''<text x="60" y="{yP-88}" font-size="12.5" font-weight="bold" fill="#111827">低阻源（跟随器输出）</text>
<text x="60" y="{yP-70}" font-size="11" fill="#94a3b8">高阻节点止于跟随器输入（E.2），</text>
<text x="60" y="{yP-54}" font-size="11" fill="#94a3b8">本段全部工作在低阻世界。</text>
<rect x="60" y="{yP-40}" width="{srcX-60}" height="80" class="box" rx="4"/>
<text x="{(60+srcX)//2}" y="{yP-10}" font-size="13" font-weight="bold" fill="#111827" text-anchor="middle">OPA388 跟随器</text>
<text x="{(60+srcX)//2}" y="{yP+10}" font-size="11" fill="#64748b" text-anchor="middle">V_P 支路（T 点）· U5:A</text>
<text x="{(60+srcX)//2}" y="{yP+28}" font-size="10" fill="#94a3b8" text-anchor="middle">详见《模拟前端与自校准》</text>
<rect x="60" y="{yN-40}" width="{srcX-60}" height="80" class="box" rx="4"/>
<text x="{(60+srcX)//2}" y="{yN-10}" font-size="13" font-weight="bold" fill="#111827" text-anchor="middle">OPA388 跟随器</text>
<text x="{(60+srcX)//2}" y="{yN+10}" font-size="11" fill="#64748b" text-anchor="middle">M 线支路 · U5:B</text>
<text x="{(60+srcX)//2}" y="{yN+28}" font-size="10" fill="#94a3b8" text-anchor="middle">详见《模拟前端与自校准》</text>''')

# ---------- 主干（分段：源→R1→R2→R3→C_diff→出口） ----------
xs = [srcX, R1x, R2x, R3x, CDx, outX, pinX]
hw = RES_W // 2
push(f'<text x="{(srcX+R1x)//2}" y="170" font-size="15" font-weight="bold" fill="#111827">通道 1（CH1 = AIN1P − AIN1N；CH2 同构，见表）</text>')
for y in (yP, yN):
    for a, b in zip(xs[:-1], xs[1:]):
        # 段终点若在电阻上，截断到电阻边沿
        ax, bx = a, b
        if b in (R1x, R2x, R3x):
            bx = b - hw
        if a in (R1x, R2x, R3x):
            ax = a + hw
        cls = "wg" if y == yP or True else "w"
        push(f'<line x1="{ax}" y1="{y}" x2="{bx}" y2="{y}" class="wg"/>')
    push(f'<circle cx="{outX}" cy="{y}" r="4" fill="#ffffff" stroke="#374151" stroke-width="2"/>')

# 电阻（画在主干之上）
res_h(R1x, yP, "R1", "6.19Ω"); res_h(R1x, yN, "R4", "6.19Ω")
res_h(R2x, yP, "R2", "6.04Ω"); res_h(R2x, yN, "R5", "6.04Ω")
res_h(R3x, yP, "R3", "13.7Ω"); res_h(R3x, yN, "R6", "13.7Ω")

# 结点（级间三路交汇：主干 + 电容支路）
for x in (R1x, R2x, R3x):
    for y in (yP, yN):
        push(f'<circle cx="{x}" cy="{y}" r="4.5" fill="#111827"/>')

# 电容
CP1, CP2, CP3 = R1x + 36, R2x + 36, R3x + 36   # P 电容错开电阻 x（避开标签）
# P 电容分支需先在主干上补一段水平线从电阻出口到电容 x，再向上
for cpx, rx, lb, vv in ((CP1, R1x, "C1", "68nF"), (CP2, R2x, "C2", "68nF"), (CP3, R3x, "C3", "27nF")):
    push(f'<line x1="{rx+RES_W//2}" y1="{yP}" x2="{cpx}" y2="{yP}" class="wg"/>')
    push(f'<circle cx="{cpx}" cy="{yP}" r="4.5" fill="#111827"/>')
    cap_g(cpx, yP - RES_H//2 - 2, lb, vv, up=True)
cap_g(R1x, yN + RES_H//2 + 2, "C4", "68nF"); cap_g(R2x, yN + RES_H//2 + 2, "C5", "68nF"); cap_g(R3x, yN + RES_H//2 + 2, "C6", "27nF")
cap_d(CDx, yP, yN, "C7", "12nF")
# C_diff 分支结点
push(f'<circle cx="{CDx}" cy="{yP}" r="4.5" fill="#111827"/>')
push(f'<circle cx="{CDx}" cy="{yN}" r="4.5" fill="#111827"/>')

# 顶部地母线（P 电容用）
push(f'<line x1="{R1x-40}" y1="{GND_TOP}" x2="{R3x+40}" y2="{GND_TOP}" class="w"/>')
gxt = R2x + 150
push(f'''<line x1="{gxt-22}" y1="{GND_TOP}" x2="{gxt+22}" y2="{GND_TOP}" stroke="#374151" stroke-width="2.2"/>
<line x1="{gxt-14}" y1="{GND_TOP+6}" x2="{gxt+14}" y2="{GND_TOP+6}" stroke="#374151" stroke-width="2"/>
<line x1="{gxt-6}" y1="{GND_TOP+12}" x2="{gxt+6}" y2="{GND_TOP+12}" stroke="#374151" stroke-width="1.8"/>
<text x="{R1x-40}" y="{GND_TOP-10}" font-size="11" fill="#94a3b8">GND（3V3_A 参考地，同网络）</text>''')

# 地母线 + 单一地符号
push(f'<line x1="{R1x-40}" y1="{GND}" x2="{R3x+40}" y2="{GND}" class="w"/>')
gx = R2x + 150
push(f'''<line x1="{gx-22}" y1="{GND}" x2="{gx+22}" y2="{GND}" stroke="#374151" stroke-width="2.2"/>
<line x1="{gx-14}" y1="{GND+6}" x2="{gx+14}" y2="{GND+6}" stroke="#374151" stroke-width="2"/>
<line x1="{gx-6}" y1="{GND+12}" x2="{gx+6}" y2="{GND+12}" stroke="#374151" stroke-width="1.8"/>''')
push(f'<text x="{R1x-40}" y="{GND+30}" font-size="11" fill="#94a3b8">GND（3V3_A 参考地）</text>')

# ---------- ADC ----------
push(f'''<rect x="{pinX}" y="180" width="220" height="470" class="adcbx" rx="6"/>
<circle cx="{pinX}" cy="{yP}" r="4" fill="#ffffff" stroke="#2563eb" stroke-width="2"/>
<circle cx="{pinX}" cy="{yN}" r="4" fill="#ffffff" stroke="#2563eb" stroke-width="2"/>
<text x="{pinX+110}" y="212" font-size="15" font-weight="bold" fill="#1d4ed8" text-anchor="middle">ADS131A02</text>
<text x="{pinX+110}" y="232" font-size="11" fill="#64748b" text-anchor="middle">ΣΔ 24bit · 128 kSPS · OSR=32</text>
<text x="{pinX+14}" y="{yP-10}" font-size="12" font-weight="bold" fill="#2563eb">AIN1P</text>
<text x="{pinX+14}" y="{yN+22}" font-size="12" font-weight="bold" fill="#2563eb">AIN1N</text>
<text x="{pinX+110}" y="380" font-size="11.5" fill="#334155" text-anchor="middle">内部：sinc³ 数字滤波器</text>
<text x="{pinX+110}" y="400" font-size="11.5" fill="#334155" text-anchor="middle">−3dB ≈ 33.5 kHz @OSR=32</text>
<text x="{pinX+110}" y="420" font-size="11.5" fill="#334155" text-anchor="middle">C_S = 3.5 pF（采样电容）</text>
<text x="{pinX+110}" y="440" font-size="11.5" fill="#334155" text-anchor="middle">fMOD = 4.096 MHz 吞吐</text>
<text x="{pinX+110}" y="480" font-size="11" fill="#94a3b8" text-anchor="middle">采样开关：S1/S2 180°反相</text>
<text x="{pinX+110}" y="498" font-size="11" fill="#94a3b8" text-anchor="middle">各占 50%（SBAS590E Fig.37/38）</text>''')

# ---------- 右侧信息面板 ----------
PX = 1388
push(f'''<rect x="{PX-20}" y="180" width="212" height="470" class="panel" rx="6"/>
<text x="{PX-4}" y="208" font-size="13.5" font-weight="bold" fill="#111827">两级采样抗混叠分工</text>
<text x="{PX-4}" y="232" font-size="11" fill="#334155">① 无源阶梯（本图）</text>
<text x="{PX-4}" y="250" font-size="10.5" fill="#64748b">守 k·fMOD 折叠 + 开关噪声</text>
<text x="{PX-4}" y="266" font-size="10.5" fill="#64748b">+ 电荷桶 + 噪声带宽</text>
<text x="{PX-4}" y="290" font-size="11" fill="#334155">② 片内 sinc³（OSR=32）</text>
<text x="{PX-4}" y="308" font-size="10.5" fill="#64748b">守 64k～fMOD 折叠带</text>
<text x="{PX-4}" y="324" font-size="10.5" fill="#64748b">−3dB ≈ 33.5 kHz（M1）</text>
<text x="{PX-4}" y="352" font-size="11" fill="#334155">通带：DC ~ 16 kHz（扫频）</text>
<text x="{PX-4}" y="370" font-size="10.5" fill="#64748b">模拟 fc ≈ 80 kHz</text>
<text x="{PX-4}" y="386" font-size="10.5" fill="#64748b">D4 = 0.185 dB @16 kHz</text>
<text x="{PX-4}" y="414" font-size="11" fill="#334155">本段口径（真实 OPA388）：</text>
<text x="{PX-4}" y="432" font-size="10.5" fill="#64748b">跟随器只缓冲不进环路；</text>
<text x="{PX-4}" y="448" font-size="10.5" fill="#64748b">R1 兼容性负载隔离（C9 修复）</text>
<text x="{PX-4}" y="464" font-size="10.5" fill="#64748b">peaking 10.7 → 4.8 dB</text>
<text x="{PX-4}" y="492" font-size="11" fill="#334155">关键衰减（LTspice 实测）：</text>
<text x="{PX-4}" y="510" font-size="10.5" fill="#64748b">DM@fMOD −84.6 dB（线 80）</text>
<text x="{PX-4}" y="526" font-size="10.5" fill="#64748b">CM@fMOD −79.2 dB（线 60）</text>
<text x="{PX-4}" y="542" font-size="10.5" fill="#64748b">DM@MCLK −132.6 dB</text>
<text x="{PX-4}" y="560" font-size="10.5" fill="#64748b">CMRR(配对1%) 95.5 dB</text>
<text x="{PX-4}" y="578" font-size="10.5" fill="#64748b">建立最坏 30.1 µs（全量程）</text>''')

# ---------- 底部：通道表 + 图注 ----------
TB = 690
push(f'''<rect x="60" y="{TB}" width="{W-120}" height="460" class="panel" rx="6"/>
<text x="80" y="{TB+32}" font-size="15" font-weight="bold" fill="#111827">四线全配通道分配表（比值/相位测量靠两线对称；CH2 与 CH1 同构）</text>
<g font-size="12" fill="#334155">
<text x="80" y="{TB+62}">通道</text><text x="300" y="{TB+62}">P 线来源</text><text x="600" y="{TB+62}">N 线来源</text><text x="920" y="{TB+62}">阶梯（P 线 = N 线镜像）</text><text x="1360" y="{TB+62}">差分电容</text>
<line x1="80" y1="{TB+70}" x2="{W-90}" y2="{TB+70}" stroke="#cbd5e1" stroke-width="1.2"/>
<text x="80" y="{TB+94}">CH1 = AIN1P−AIN1N</text><text x="300" y="{TB+94}">V_P（T 点跟随器）</text><text x="600" y="{TB+94}">M（Rsense 顶跟随器）</text><text x="920" y="{TB+94}">6.19+6.04+13.7 Ω / 68+68+27 nF</text><text x="1360" y="{TB+94}">C7 = 12 nF</text>
<text x="80" y="{TB+118}">CH2 = AIN2P−AIN2N</text><text x="300" y="{TB+118}">B（Rsense 底跟随器）</text><text x="600" y="{TB+118}">AIN1N 参考经 RC 直连*</text><text x="920" y="{TB+118}">同 CH1（四线统一全配）</text><text x="1360" y="{TB+118}">12 nF</text>
</g>
<text x="80" y="{TB+144}" font-size="10.5" fill="#94a3b8">* E.2：地参考为低阻，可不加跟随器；统一全配是为 CH1/CH2 对称（比值与相位精度），通带增益均为 1。</text>

<text x="80" y="{TB+180}" font-size="14" font-weight="bold" fill="#111827">设计与验收要点（R5 第4轮定档 · 真实 OPA388 模型口径）</text>
<g font-size="11.5" fill="#334155">
<text x="80" y="{TB+206}">1. 拓扑：三级无源 RC 低通（fc ≈ 80 kHz）。无源是 fMOD=4.096 MHz 频段唯一可靠滤波手段；跟随器只缓冲、不进反馈环路（GBW=10 MHz 在 4 MHz 环路增益不足，有源拓扑阻带翘曲判死）。</text>
<text x="80" y="{TB+230}">2. 元件：R 全 E96 1%（6.19 / 6.04 / 13.7 Ω）；C 全 C0G/NP0（68 / 68 / 27 + 12 nF）。ΣR = 25.93 Ω ≪ 5 kΩ（C2）；单电容 ≤68 nF，SRF &gt; fMOD 已核（C3）；有源谐振 peaking 4.8 dB ≤ 6 dB（C9）。</text>
<text x="80" y="{TB+254}">3. R·C 乘积配对（D8 关键，BOM 加工序）：两线按「R×(1+m) 配 C×(1−m)」异向配对，1% 单体失配下 CMRR = 95.5 dB；不配对仅 48.5 dB（+47 dB 收益）。每对 R/C 实测后按乘积配对贴片。</text>
<text x="80" y="{TB+278}">4. C9 修复：R1 2.74→6.19 Ω 使跟随器节点 peaking 10.66→4.77 dB（278.6 kHz 处，限 6 dB）。该峰源于 OPA388 闭环输出阻抗中频负实部与阶梯电容的谐振——手册曲线不可见，须用 TI 模型实测输出阻抗。</text>
<text x="80" y="{TB+302}">5. D5 建立时间：73 Ω–600 kΩ 十六点全建立（最坏 30.1 µs @220 kΩ，0.01% 带，含 600 kΩ∥8.5 pF 高阻工况与 R×1.01/C×1.05 容差角）；三种数值设置交叉验证一致。</text>
<text x="80" y="{TB+326}">6. 噪声：无源网络增量 D6a = 0.64%（限 10%）；总噪声 D6b = 12.0 LSB ≈ 3.5 µVrms（跟随器 9.9 nV/√Hz 主导，砖墙极限 4.3 LSB），对最小信号 80 mV 折 0.004%，软参考项不淘汰。</text>
<text x="80" y="{TB+350}">7. 温度：−20 / +85 ℃ 全维复测 D4/D10/D1 漂移 &lt; 0.001 dB（C0G ±30 ppm/℃），免温度补偿。CH1/CH2 群延迟匹配由四线统一全配保证；扫频相位为两通道相对值。</text>
<text x="80" y="{TB+374}">8. 评分（规格 v4 十槽位 min 制）：min = 0.700，短板 D4（0.185 dB vs 满分线 0.05 dB；及格线 0.5 dB 已过，16 kHz 扫频幅值偏差 ≈2.1%）。用户 2026-10-19 按「能力包线内最优」定档。</text>
<text x="80" y="{TB+398}">9. 采集页待修提醒：ADS131A02 的 CAP 脚电容与 IOVDD 解耦电容必须接 GND（现图误接 VCC，即 C34/C35）。</text>
</g>
<text x="80" y="{TB+436}" font-size="11" fill="#94a3b8">图注自查：级间三路交汇均实心结点；器件端子与 ADC 引脚白底圆；C7 跨 AIN1P/AIN1N；六颗对地电容统一接 GND 母线；绿色主干 = 差分测量路径。</text>
</svg>''')

svg = "\n".join(OUT)
path = sys.argv[1] if len(sys.argv) > 1 else "抗混叠滤波电路.svg"
io.open(path, "w", encoding="utf-8", newline="\n").write(svg)
print("written", path, len(svg), "bytes")
