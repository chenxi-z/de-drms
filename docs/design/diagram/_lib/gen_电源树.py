#!/usr/bin/env python3
"""直流首板说明图；依据主文档附录F，非EDA修改。"""
from scistyle import PrototypeDiagram

d=PrototypeDiagram('电源树','BQ24074 + 双 LDO · 保留输入防倒灌 · OUT 不串二极管')
d.box(35,115,270,['USB 原始 VBUS','D1：阳极接 USB，阴极向 IN'])
d.box(35,255,270,['外部受限 5 V','D16：阳极接外5 V，阴极向 IN'])
d.line(305,155,355,155);d.line(305,295,355,295);d.line(355,155,355,295)
d.node(355,225);d.line(355,225,405,225)
d.box(405,175,245,['BQ24074 IN','BAT ↔ 1S 电池','OUT → VOUT'])
d.box(735,115,330,['数字 TLV75533 → VCC','MCU / ADC IOVDD / TF 直接供电'])
d.box(735,295,330,['原磁珠 → TPS7A2033 → AVCC','模拟前端；ANA_EN = PC3'])
d.line(650,225,695,225);d.node(695,225);d.line(695,155,695,335)
d.line(695,155,735,155);d.line(695,335,735,335)
d.box(35,440,490,['USB 原始 VBUS（D1之前）→100 kΩ→NPN B','B→1 MΩ→GND；E→GND','C→PC13；C→10 kΩ→VCC；低=VBUS存在'])
d.box(580,440,485,['NPN参考：MMBT3904，具体厂牌/脚序待核','BQ_PG=PB5，BQ_CHG=PC2，均输入上拉VCC','BQ_EN=PC1；PG不能区分USB和外部5 V'])
d.notes([
'外5 V可以供电，也可能给电池充电；采用已接受的简单共用输入方案。',
'不把调试器3.3 V与VCC并联；不在BQ OUT增加串联二极管。',
'检测仅表示USB供电存在，不是精密阈值监控；BQ限流、USB授权和描述符仍需闭环。',
'低电、充电与写卡峰值下须验证LDO压差、稳定性与测量噪声。'
],660)

d.save(__file__)
