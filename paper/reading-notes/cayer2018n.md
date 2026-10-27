# 精读笔记 · Çaycı 2018《An Improved Mobile Calibration Standard for Transformer Loss Measurement Systems》（CPEM 2018）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> CPEM 2018 摘要文（2 页，bib 记 pages 1–2），页码按 PDF 页 1–2 记。
> ⚠️ 题录勘误：bib/文件名作 "cayer2018n / Cayer, H."，**正文署名实为 H. Çaycı（土耳其 TÜBİTAK UME）**——引用时应用 Çaycı，文件名沿用 bib key 不动。

## 出处
- H. Çaycı, B. Ayhan, T. Kefeli, "An Improved Mobile Calibration Standard for Transformer Loss Measurement Systems", 2018 Conference on Precision Electromagnetic Measurements (CPEM 2018), Paris, pp. 1–2. doi:10.1109/cpem.2018.8500822.
- 本地：`H7-比率与电阻计量/cayer2018n.pdf`（2 页）。bib key：`cayer2018n`（literature.bib L1129，作者字段拼法待修）。

## 核心命题（原文）

1. **升级要点：主从源架构改为外触发同步，系统稳定度 <50 ppm；相位设定分辨率提至 1 m°**（p.1，Abstract）：
   > "Master-slave configuration of programmable power sources is replaced with the external triggering and synchronization method which ensures the system stability below 50 ppm. Resolution in phase-settings between voltage and current generation is now improved about 2-digits down to 1 m°. And, measurement results are automatically evaluated with the corrected calibration values of system components."（p.1）
   中文：变压器损耗测量系统（TLMS）现场校准用移动标准——工程升级报告，核心在低功率因数下有功功率的稳定度与相位分辨率。

2. **系统构成：24-bit 双通道发生器 + 两台相同线性功放 + 已表征功率分析仪；电压/电流分辨率 1 mV / 0.1 mA，相位 ±180° 内 1 m° 步进**（p.1–2）：
   > "a programmable 24 bits two-channel signal generator in connection with two identical linear power amplifiers form the generation part while a well-characterized wattmeter/power analyzer takes place in the measurement part of the setup."（p.1）
   > "Voltage and current values can be set with the resolution of 1 mV and 0.1 mA, respectively … any phase angle between them can be adjusted within ±180º with a resolution of 1 mº."（p.1–2，跨页句）
   > "Any ratio and phase errors from the reference transformers and power measurement errors of power analyzer are automatically corrected during the measurements."（p.1）

3. **量程与总不确定度量级：2000 A / 36 kV，任意功率因数可编程，系统不确定度 ≈70 µW/VA**（p.1）：
   > "the improved mobile standard is configured for up to 2000 A to cover customer requirements. And, operating voltage is up to 36 kV … Any power factor can be programmed within mº steps regardless of applied values. And, estimated system uncertainty in the measurement of active power for any power factor is estimated around 70 μW/VA [4]."（p.1）

4. **低功率因数下有功功率稳定度 <50 ppm（实测）**（p.2）：
   > "Stability is the most important parameter for the accuracy in active power measurements when testing very low power factors. Short-and-long-term measurement results showed that the stability in the active power measurements at low power factors is less than 50 ppm regardless of the applied voltage and current values. Fig. 3 shows an example for 0.5 and 0.01 power factors when 36 kV and 1 kA are generated."（p.2）
   中文：低 PF（0.01）是大变压器损耗测试的难点工况，本文把"稳定度"列为第一指标。

5. **分量校准值与不确定度预算表（含灵敏度系数）**（p.2）：
   > "The two-stage voltage transformer and the precise current transformer are calibrated against to TÜBİTAK UME standards. Uncertainties in the ratio error and phase displacement measurements are 50 μV/V and 50 μrad for voltage transformer and 35 μA/A and 35 μrad for current transformer, respectively."（p.2）
   > "The power analyzer is calibrated using the digital sampling wattmeter with the uncertainty of 20 μW/VA."（p.2）
   > Table 1（36 kV, 1 kA, PF=0.01）：Repeatability 10 ppm（c=1）；Phase cal. of PA 10 ppm × c=−0.99 → 99.99 ppm²；Ratio cal. of VT 25 ppm × 0.01 → 0.07 ppm²；**Phase cal. of VT 25 ppm × c=−0.99 → 624.9 ppm²**；Ratio cal. of CT 17.5 × 0.01；Phase cal. of CT 17.5 × 0.99 → 306.2 ppm²；**Expanded Uncertainty (k=2) = 67 ppm**。（p.2）
   中文：低 PF 下**相位项灵敏度系数 ≈ ±0.99、比率项 ≈ 0.01**——同量级的相位误差贡献是比率误差的 ~100 倍（方差），这是"误差传播系数随工况（PF）切换主导项"的干净范例。

6. **接地纪律与容性负载补偿**（p.1）：
   > "A capacitor unit is used to compensate the reactive load of the current path by calculating the required combination of capacitor values for each test point during the calibration. All components used in the calibration setup are connected to the ground potential avoiding any ground loops."（p.1）

## 关键数值（原文）
- 范围：电流 ≤**2000 A**、电压 ≤**36 kV**、任意 PF 可编程（m° 步进）（p.1）。
- 分辨率：电压 1 mV、电流 0.1 mA、相位 **1 m°**；发生器 24-bit 双通道（p.1–2）。
- 稳定度：低 PF 有功功率 <**50 ppm**（PF=0.5 与 0.01、36 kV/1 kA 实测）（p.2）。
- 分量校准：VT（两级）比差 **50 µV/V** / 角差 **50 µrad**；CT 比差 **35 µA/A** / 角差 **35 µrad**；功率分析仪（经数字采样瓦特计）**20 µW/VA**（p.2）。
- 系统不确定度：≈**70 µW/VA**（p.1）；预算表合成 **67 ppm (k=2)** @36 kV/1 kA/PF=0.01（p.2 Table 1）。
- 灵敏度系数：相位项 −0.99 / +0.99，比率项 0.01（PF=0.01 时）（p.2 Table 1）。

## 对 P1/P2/P3 的对照
- **P1（消去条件）**：相关度 **无**。无差分/共模/电桥消去内容。killRisk：**无**。
- **P2（Kelvin 地板）**：相关度 **无/低**。仅一句"single-point grounding avoiding ground loops"的接地纪律，无引线电阻/结构地板讨论。
- **P3（平坦度约束衰减上界）**：相关度 **无**。无滤波器/匹配界内容。
- **方法学（门槛化）**：相关度 **低**。Table 1 的**灵敏度系数不确定度预算**是干净范例——低 PF 工况使相位项系数 ≈±1、比率项 ≈0.01，误差主导项随工况切换；P1 的误差预算/门槛化章节若需"传播系数决定主导项"的引用支撑，可引此文（但属功率计量域，非电路理论域）。
- **killRisk 总评：无**（换领域工程报告，对 P1/P2/P3 无威胁、无支撑）。

## 没读到的
- Fig.2 系统原理图的电路细节（互感器两级结构、跨导放大器实现）。
- 稳定度测试的原始数据曲线（Fig.3 只有示意）。
- 70 µW/VA 的完整推导（引 TÜBİTAK 内部质量体系文件 [4]，不可得）。
- 数字采样技术升级（Future Work，未实现）。
