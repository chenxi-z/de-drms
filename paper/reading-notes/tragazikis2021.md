# 精读笔记 · Tragazikis 2021《Monitoring the Hydration Process in Carbon Nanotube Reinforced Cement-Based Composites Using Nonlinear Elastic Waves》（Applied Sciences, MDPI）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> H6 轴定位：CNT-SHM 应用域 C 级证据（笔记可短）。本文极端案例：**CNT 在场但传感通道根本不是电阻**——用非线性超声+激光测振监测水化，测链 100% 商品化。页码 = PDF 页（MDPI 排版"N of 15"，PDF 页与文页一致）。

## 出处
- Tragazikis, Kordatou, Exarchos, Dalla, Matikas. "Monitoring the Hydration Process in Carbon Nanotube Reinforced Cement-Based Composites Using Nonlinear Elastic Waves." Applied Sciences 2021, 11(4), 1720. doi:10.3390/app11041720。PDF 15+1 页（末页为广告页）。
- bib key：`tragazikis2021`。

## 核心命题（原文）
1. **监测对象是水泥水化过程，方法是非线性弹性波高次谐波，不是 CNT 电阻**（p.1 摘要）：
   > "This methodology is based on the use of nonlinear elastic waves. To achieve this goal, a combination of contact ultrasonics with noncontact optical detection was used."
   （传感原理与 DC 电阻测量无关；CNT 只是纳米增强相。）
2. **材料非线性比线性声学指标更敏感，且随 CNT 掺量增大更明显**（p.1 摘要）：
   > "It was observed that the material nonlinearity changes significantly during the hardening process, compared to velocity or attenuation measurements which are based on linear acoustics. These changes were more noticeable as the concentration of carbon nanotubes in the cement matrix increases, indicating that higher harmonics are more susceptible to minute microstructural changes."
3. **测量链全部商品化仪器**（p.5，Methods）：Ritec RPR-4000-VHP 高功率脉冲发生/接收器 + Polytec PSV-400 激光多普勒测振仪 + NI PXI 机箱采集，LABVIEW 控制：
   > "The scanning vibrometry system used in this study was PSV-400 by Polytec, equipped with a digital velocity decoder, with 8 velocity ranges from 1 mm/s/V to 50 mm/s/V and a maximum bandwidth of 350 KHz..."（p.4）
   > "Data were collected via PXIe-1071 chassis by National Instruments, consisting of a PXIe-8360 card (PXI Remote Control Module)... while a PXI-8430/2 card (PXI Serial Interface Module) was connected with the Ritec-4000. For the data and waveforms recording, an 8-channel 12-Bit 60 MS/s PXI-5105 (PXI Oscilloscope) was used."（p.5）
4. **唯一一处"前端误差"意识：靠买"绝对线性"仪器保证谐波非材料伪影，而非分析/设计**（p.5，对 P1 最有价值的一条）：
   > "For generating nonlinear ultrasonic oscillations an absolute linear pulser, RPR-4000-VHP High Power Pulser Receiver system by Ritec was used. This way, it was ensured that the received nonlinear signals were due to the material's nonlinear behavior and not due to the measuring device itself."
   （应用文献处理"仪器自身引入误差"的方式 = 采购级解决，无任何误差预算/公式/验证。）
5. CNT 的"传感"角色只出现在引用他人的综述性表述里（p.2）：
   > "Carbon-based additives, such as multiwalled carbon nanotubes in cementitious materials are admixtures that play the role of strain and damage sensors inside the matrix and improve plenty of properties like flexural and compressive strength..."（引 [7–13]，非本文工作。）

## 关键数值（原文）
- MWCNT 掺量 0.2 / 0.4 / 0.6 wt.% of cement；w/c = 0.5；净浆与砂浆各 9 组、共 18 组配比（p.4）。
- MWCNT 规格：长 5–15 µm、径 20–40 nm、纯度 ≥97%（表 1，p.5）。
- 换能器峰值频率 0.20 MHz，距玻璃 50 mm；玻璃厚 1 mm（p.5）。
- 水化前 48 h 内每 4 min 记录一次（p.4）。
- 超声速度三阶段：起始近空气声速 340 m/s → 升至近水中 1500 m/s → 1500–3000 m/s（p.6）。
- 采集卡 PXI-5105：8 通道、12 bit、60 MS/s（p.5）。

## 对 P1/P2/P3 的对照
- **P1（G_DC≡0 元件条件）**：无。全文无电阻/电导测量、无电极、无激励源设计；不构成 P1 反例，属"前端理论空白"的应用侧证（连仪器线性性这种最接近"前端误差"的问题都用商品仪器规格背书解决）。
- **P2（Kelvin 结构地板 ≈56 dB）**：无。无引线/接触电阻议题，无两线/四线之分（物理上就不是电阻测量）。
- **P3（衰减可达上界）**：无。信号是超声谐波幅度，无 DC 衰减/漂移概念。
- **方法学（门槛化）**：无损伤分级/阈值设定；输出是 β2/β3 非线性参数随水化时间的曲线（p.4 公式 4–5）。
- **killRisk**：无（与 P1/P2/P3 无冲突，仅作应用域"测量环节商品化"现状证据）。

## 没读到的
- 任何 DC 电阻/压阻测量（全文无 Keithley/万用表/源表/欧姆计字样）——已 grep 确认。
- 前端误差预算、校准流程、引线制式：无。
- β 参数的具体数值结果（正文以曲线图呈现，文中未给 β2/β3 数表；如需数值待核图 5–8 数据点）。
