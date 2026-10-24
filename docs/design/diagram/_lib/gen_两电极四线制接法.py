#!/usr/bin/env python3
"""直流首板说明图；依据主文档附录F，非EDA修改。"""
from scistyle import PrototypeDiagram

d=PrototypeDiagram('两电极四线制接法','四根引线、两个电极 · 电极接触阻抗仍属于被测系统')
d.box(35,180,280,['仪器 CN4','1：I_OUTPUT / Force+','2：V_P / Sense+','3：V_N / Sense−','4：I_INPUT / Force−'])
d.box(775,180,290,['样品两个电极','正电极：Force+与Sense+','在电极根部独立汇合','负电极：Sense−与Force−','在另一电极根部独立汇合'])
for y in (230,255,280,305): d.line(315,y,775,y)
d.box(35,420,1030,['四线模式：板上Force/Sense短接电阻R32/R33不贴，四条独立引线直到样品电极根部','二线模式：R32/R33可贴0 Ω，只引两根线；引线压降进入测量值'])
d.notes([
'Kelvin接法减小Force引线压降影响，不能消除两电极本身与样品的界面阻抗。',
'高阻Sense线避开数字时钟、写卡与SMPS回流；漏电、清洁度、屏蔽接法均需实物验证。',
'未来CPE扫频测得的是偏置点附近整个两电极系统的复阻抗，不能直接等同材料本征参数。'
],625)

d.save(__file__)
