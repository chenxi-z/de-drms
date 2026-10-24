#!/usr/bin/env python3
"""直流首板说明图；依据主文档附录F，非EDA修改。"""
from scistyle import PrototypeDiagram

d=PrototypeDiagram('模拟前端与自校准','直流首板连接目标 · 修正 U10 SEL 分组与 17/18 脚 · 以网络表表达切换关系')
d.box(35,115,480,['T：AVCC经10 kΩ供电，150 kΩ到AGND','T → 样品 Force+；样品 Force− → AFE_S','T → Rref 100 kΩ → F；F为参考下端','X → Q2 D；Q2 S → Rsense → AGND'])
d.box(575,115,490,['U10 TMUX1134：PB2 → SEL1/3/4','PB0 → SEL2；不是旧图的SEL4','测量0/0；参考1/1；过渡1/0；禁止0/1','状态顺序为PB2/PB0，器件真值表待最终核验'])
d.box(35,300,480,['U10 D1(3)→T；S1B(4)→V_P；S1A不接','D2(8)→X；S2B(7)→F；S2A不接','D3(13)→X；S3A(12)→AFE_S；S3B不接','D4(18)→AFE_M；S4A(19)→V_N；S4B(17)→F'])
d.box(575,300,490,['V_P → OPA388 → T2 → AIN1P','AFE_M → OPA388 → T2 → AIN1N','AFE_B → OPA388 → T2 → AIN2P','Rsense底端Kelvin地 → T2 → AIN2N'])
d.box(35,485,1030,['测量→参考：抑制激励，PB2置1，再PB0置1；参考→测量：PB0置0，再PB2置0','切换/建立期间标记数据无效；两条回流断开不是已验证的有效零点模式'])
d.notes([
'用户已在本地修正17/18脚；GitHub的V1.2工程未包含该修改，需同步后复查。',
'Rref的库元数据±0.05%与旧标注±0.01%冲突，确认料号或实测校准后再定准确度。',
'不把F对地100 pF台架电容画成已安装；其存在会改变交流参考阻抗。',
'R32/R33：四线不贴、二线可贴0 Ω。采样参考地不加运放，不与数字回流共用细线。'
],660)

d.save(__file__)
