#!/usr/bin/env python3
"""直流首板说明图；依据主文档附录F，非EDA修改。"""
from scistyle import PrototypeDiagram

d=PrototypeDiagram('四线制前端接法','测量通道与电流通道 · 物理AIN1/2与仿真CH0/1对应')
d.box(35,145,340,['样品 Sense+：V_P','样品 Sense−：经U10选AFE_M','两路分别经过OPA388缓冲'])
d.box(665,145,400,['T2差分AAF → ADS131A02','AIN1P / AIN1N = 样品电压','对应仿真 CH0'])
d.line(375,195,665,195)
d.box(35,335,340,['Rsense顶端：AFE_B → OPA388','Rsense底端：Kelvin地直连RC','低阻地端不增加运放'])
d.box(665,335,400,['T2差分AAF → ADS131A02','AIN2P / AIN2N = 电流检测电压','对应仿真 CH1'])
d.line(375,385,665,385)
d.box(35,530,1030,['直流：去除有效偏置后的 Vsample / Vsense × Rsense，再应用有效的参考校准系数','两通道同步采样；校准/切换/恢复/过载期间的数据必须标记无效'])
d.notes([
'两通道负载结构并非完全相同；不能从RC镜像直接宣称整机高共模抑制或交流相位匹配。',
'T2元件和两线连接见抗混叠滤波电路图；板上寄生与ADC真实负载仍需验证。',
'图示为连接说明，未替代最终EDA网表、PCB检查与实物校准。'
],675)

d.save(__file__)
