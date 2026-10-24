#!/usr/bin/env python3
"""直流首板说明图；依据主文档附录F，非EDA修改。"""
from scistyle import PrototypeDiagram

d=PrototypeDiagram('抗混叠滤波电路','直流首板候选 T2 · 每通道两根线同构 · 本图为替换目标，原工程尚未修改')
for y,label in [(200,'P 输入'),(420,'N 输入')]:
    d.text(35,y+5,label)
    d.line(110,y,180,y)
    d.resistor(180,y,'100 Ω')
    d.line(260,y,470,y)
    d.shunt_cap(330,y,'10 nF')
    d.resistor(470,y,'120 Ω')
    d.line(550,y,930,y)
    d.shunt_cap(640,y,'10 nF')
    d.text(945,y+5,'ADC AIN P' if y==200 else 'ADC AIN N')
d.node(825,200);d.node(825,420)
d.line(825,200,825,300);d.line(812,300,838,300,kind="sym")
d.line(812,308,838,308,kind="sym");d.line(825,308,825,420)
d.text(845,310,'820 pF',14)
d.notes([
'本图复制到两通道：共 8 颗串联电阻、8 颗 10 nF、2 颗 820 pF；全部电容 C0G/NP0。',
'电容下端均接 AGND。通道1：缓冲 V_P / AFE_M；通道2：缓冲 AFE_B / Kelvin 地。',
'通道2负端没有运放，Kelvin 地从 Rsense 底端独立引出，不借用数字回流走线。',
'T2 台架：D1=62.33 dB、D3=94.74 dB 均未达门槛；不能标注“全部通过”。',
'普通容差贴装不保证 80 dB 匹配；理想整线选配结果不等于实物量产性能。',
'替换原 RC 群；末级贴近 ADC，两线镜像，远离 SPI/SDMMC；实际布线与 DRC 尚未完成。'
],590)

d.save(__file__)
