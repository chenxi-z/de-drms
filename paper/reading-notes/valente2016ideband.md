# 精读笔记 · Valente 2016《Wideband Fully-Programmable Dual-Mode CMOS Analogue Front-End for Electrical Impedance Spectroscopy》（Sensors 16(8):1159）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。

## 出处
- V. Valente, A. Demosthenous, "Wideband Fully-Programmable Dual-Mode CMOS Analogue Front-End for Electrical Impedance Spectroscopy," *Sensors*, vol. 16, no. 8, p. 1159, 2016. DOI: 10.3390/s16081159. UCL（EPSRC EP/K031953/1）。
- PDF 20 页 = 刊页 "N of 20"（MDPI 排版，文字层完整；公式上标/根号有排版粘连，引用时以文字句为准）。
- 定位：**H7 宽带阻抗测量（CMOS 集成 EIS 双模前端）**——双极（电流读出 CR）+ 四极（电压读出 VR）双模 AFE 芯片。按计量轴标准读：四端结构的片上实现、CMRR 实测、噪声-带宽权衡、对商品阻抗分析仪的定标比对与误差归因。

## 核心命题（原文）
1. **总命题：双极 + 四极双模片上前端，并行测电极/界面阻抗与介质阻抗（p.1, Abstract）**：
   > "The chip, implemented in a 180-nm CMOS technology, combines two current-readout (CR) channels and four voltage-readout (VR) channels suitable for both bipolar and tetrapolar electrical impedance spectroscopy (EIS) analysis. … Measurements show close matching with results obtained using a commercial impedance analyser."
2. **★双极构型的混杂问题：两电极测得阻抗=介质+电极/界面之和（p.1, §1）**：
   > "Most impedance methods measure only the conductivity of the medium using a pair of electrodes at a fixed frequency using a bipolar configuration. However, the measured impedance is the result of contributions from both the medium impedance and the electrode/interface impedance [15]."
   （两线/双极的固有混杂——正是四端结构要消除的对象。）
3. **★四极结构的功能定义：介质电导独立于电极阻抗（p.2, §1）**：
   > "In order to increase the flexibility of the impedance measurement, dual-mode EIS, based on both bipolar and tetrapolar configurations, can be exploited to measure the medium conductivity independently of the electrode impedance [17–19]."
   > 图 1 注（p.3）："The solution impedance can be measured using a tetrapolar configuration by injecting a differential current, IEXT, through an electrode and measuring the differential voltage across a second electrode. Electrode/interface impedance can be measured by exciting an electrode with a voltage source, VEXT, and reading the current flowing through the electrode."
   （**Kelvin 四端在集成 EIS 的标准落地形态**：电流注入对与差分电压读出对分离；引 [17–19] 为谱系。）
4. **误差预算的显式方法（p.4–11）：稳定性、噪声、失调三线分析**
   - 稳定性（p.6）：
     > "The stability of the amplifier depends on the magnitude of the total input capacitance, CIN, of the amplifier, which generates a zero in the noise gain, GN(f), given by: …"
     > "The compensation capacitor, CC, can be adjusted in order to introduce a pole and flatten the noise gain response before the crossover frequency."
   - 噪声-增益权衡（p.7）：
     > "Equation (9) shows how the total equivalent noise of the TIA is inversely proportional to the feedback resistor, RF. Maximising RF, therefore, will decrease the input-referred noise at the cost, however, of the TIA bandwidth."
   - 1/f 转角频率设计（p.8）：
     > "The device sizes and bias current of the op-amp can be selected to set fc below the lowest frequency of interest."
   - 失调修剪（p.11）：
     > "Due to the large gain range that the VR AFE provides, an offset trimming unit was included. … The offset calibration unit is designed to compensate for input offsets as high as ±20 mV."
   - 低频对策（p.4）：
     > "In this case, chopper-stabilized op-amps switching at a frequency of 100 kHz are used to allow for low-noise measurements to be performed."
5. **★实测 CMRR 与带宽（p.14, §3.2）**：
   > "The bandwidth of the buffer was measured to be approximately 8 MHz and is substantially independent of the amplifier gain. The amplifier measured CMRR is shown in Figure 15b for a gain of 20 dB. At low frequencies below 1 kHz, the CMRR is greater than 84 dB."
   （**集成 INA 的 CMRR 实测 = 84.4 dB @<1 kHz（Table 1, p.15），随频率滚降（Fig.15b）**——片上差分前端的共模抑制量级与频变行为的一手数据。）
6. **★★定标与误差归因：对商品阻抗分析仪逐频比对，误差归因到 1/f 与带宽（p.16, §3.3）**：
   > "System calibration was performed by measuring the impedance magnitude and phase of known resistor and capacitor values and correcting for gain and phase factors during post-processing."（p.16）
   > "The maximum discrepancies between the bare IDE cell measurements were 6% a 100 Hz and 9% at 400 Hz in pH 5.0 and DI water, respectively. For the polymer IDE cell, the largest error was estimated to be 17.4% at 100 kHz and 20.2% at 500 Hz pH 5.0 and DI water, respectively. The large error at low frequencies can be attributed to the 1/f noise of the front-end, whereas the error at high frequencies is due to the bandwidth of the CR AFE, which was set to 159 kHz. Within the frequency range of 10 kHz–100 kHz, measurement accuracy is within 5% with errors as low as 0.2% in the case of bare IDE in pH 5.0 buffer solution."（p.16）
   （**计量学姿态的样板**：已知 R/C 定标 + 幅相校正 + 逐频误差 + 物理归因（低频→1/f、高频→带宽）+ 分频段精度口径。）
7. **四极电导率提取（p.17, §3.3）**：
   > "A differential 1-mA current was applied to one IDE, and the voltage, VSOL, was measured differentially across the second IDE. The resulting voltages at 10 kHz were measure to be 0.74 mV, 1.2 mV and 13.5 mV for conductivities of 0.3 S/m, 8.4 S/m and 40 S/m, respectively. The ratio between IEXT and VSOL was calculated with values measured at a frequency of 10 kHz and resulted in extracted conductivity values of 0.34 S/m 8.8 S/m and 37 S/m, respectively."
8. **设计取舍自白（p.18, §4）**：
   > "The use of small values for the feedback resistor in the TIA (Figure 4) was required to accommodate large currents flowing through the IDE (>100 nA). This, however, results in larger input-referred current noise as compared to alternative structures [33,35]. Nevertheless, given the relatively large input currents, a more power-efficient architecture was preferred."

## 关键数值（原文）
- CMRR：**84.4 dB**（Table 1, p.15；正文 p.14 "greater than 84 dB" @<1 kHz，随频率下降）。
- 噪声底（p.15，100 kHz 处，最大增益档）：TIA **450 fA/√Hz**（@100 kΩ 档）；INA **10 nV/√Hz**（@42 dB 档）。运放仿真输入噪声 98 nV/√Hz @10 kHz、35 nV/√Hz @100 kHz（p.5–6）。
- CR（p.12）：TIA 增益 10/50/100 kΩ，对应带宽 **1.59 MHz / 310 kHz / 159 kHz**（CF=10 pF）；线性范围 **10 nA–100 µA = 80 dB**（1 dB 判据）；PGA 实测 1–13.8 V/V 与 5.7–55 V/V。
- VR（p.14）：HF 带宽 **≈8 MHz**（增益 −6~22 dB，"substantially independent of gain"）；BW 通道 30–80 kHz（步进 ~800 Hz，增益 12–42 dB）；总增益范围 −6~42 dB。
- 频响陷阱（p.12）：CF 下限 10 pF，1.5 pF 时高频出现**增益峰起（gain peaking）**。
- 阻抗比对（p.16）：对商品分析仪（Wayne Kerr 6220B[原文如此，型号待核]）最大误差：裸 IDE 6%@100 Hz / 9%@400 Hz；聚合物 IDE 17.4%@100 kHz / 20.2%@500 Hz；**10 kHz–100 kHz 内精度 <5%，最好 0.2%**。
- 干电极电容：芯片测 **2.05 pF** vs 分析仪 **2.23 pF**（p.16–17）；被测 IDE 阻抗 @20 kHz ≈ **1 kΩ–1 MΩ**，10 mV 激励下电流 **10–20 nA 至 10 µA**（p.2）。
- 芯片：0.18 µm CMOS、1.8 V、530 µA（CR）/690 µA（VR）每通道、有源面积 4.2 mm²、2×10-bit SAR ADC @200 kS/s、SPI 11 寄存器；实测频率窗口 100 Hz–100 kHz（p.4, p.15, p.16）。
- 器件级（p.10–11）：尾电流 120 µA、1/gm=700 Ω、开关导通电阻 ~20 Ω（比最低 RS=200 Ω 低 10 倍——**开关电阻失配预算**）；失调修剪 4-bit 粗（750 nA）+6-bit 细（10 nA）。

## 对 P1/P2/P3 的对照
- **P1（消去条件，G_DC≡0）**：**低-中**。无消去结构命题；但低频/直流误差的对策谱系齐备：斩波（100 kHz）稳零运放（p.4）、失调修剪 DAC ±20 mV（p.11）、1/f 转角频率设计法（p.8）、低频测量误差归因于 1/f（p.16）——可作为 P1 讨论直流/低频通道误差形态（失调、1/f、极化混杂）的应用侧对照物。
- **P2（Kelvin 结构地板 ≈56 dB）**：**中-高（对照物）**。四端结构是本文的功能主干（命题 3），且给出**集成 INA 的 CMRR 实测 84.4 dB@<1 kHz、随频率滚降**（p.14, p.15）——这是"片上 Kelvin 电压读出"的共模抑制量级锚点。**口径警示**：放大器 CMRR ≠ 系统级结构地板（四端对比率臂电桥的比率精度）；84 dB 不直接反驳 56 dB 地板，但说明**若 P2 的 56 dB 以"前端 CMRR 量级"表述，集成 CMOS 前端可越此线**——P1 论文引用本文时必须先对齐口径（CMRR vs 比率/失配地板），否则会被反例戳穿。
- **P3（衰减可达上界）**：**低**。无滤波衰减上界命题；相关仅有：噪声-带宽权衡（RF↑噪声↓带宽↓，p.7）、CF≥10 pF 防增益峰起（p.12）、BW 通道 30–80 kHz 可编程——均为增益带宽约束，非衰减可达上界。
- **方法学（门槛化/增量四）**：**中-高（正面样板）**。四步法：①已知 R/C 定标 + 幅相后处理校正（p.16）；②对商品基准（阻抗分析仪）逐频比对；③误差逐频量化（6%/9%/17.4%/20.2%）；④物理归因（低频→1/f、高频→带宽）并给出有效频段口径（10 kHz–100 kHz 内 <5%）。这是"先把误差归因再定判据"的可引用范式；缺统计（无重复性/不确定度展开）。
- **killRisk 判断：低（对 P2 有一处口径风险）**。本文不主张任何"地板/极限"，是数据源而非竞争命题；唯一风险是**P2 若把 56 dB 说成"前端共模抑制的地板"，本文 84.4 dB 即为反例**——引用时须把 P2 的地板严格限定在结构级（比率/失配转换），不能泛化为 CMRR。

## 没读到的
- Figures 11–19 曲线本体（CMRR-频率曲线的滚降形状、阻抗谱比对图；数值以正文与 Table 1/2 为准）。
- Fig.15b 中 CMRR 随频率下降的具体轨迹值（正文只给 <1 kHz 的 84 dB 与 Table 1 的 84.4 dB）。
- 双模 EIS 谱系原始文 [17] Ha 2014 / [18] Ma & Nathan 2015（双极 vs 四极电池常数研究）/ [19] Felice 1992 未读——四极独立性论断的出处链。
- 对照系统 Wayne Kerr "6220B" 型号（原文如此；与常见 6420/6500 系列记法不合，型号待核）。
- 后续全集成平台文 [40] Valente & Demosthenous 2015 EMBC（含波形发生器与数字阻抗处理单元）未读。
