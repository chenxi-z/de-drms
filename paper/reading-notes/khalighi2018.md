# 精读笔记 · Khalighi 2018《A floating wide-band current source for electrical impedance tomography》（Review of Scientific Instruments）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> H6 轴定位：虽归档在 H6-CNT-SHM 目录，实为 **EIT 电流源（VCCS）硬件设计论文**——正因如此它测的全是"前端"指标（输出阻抗、合规电压、SNR），但全部在 **AC/EIT 语境**，与 DC 电阻前端条件（P1）不同构。页码 = 正文页（085107-N；PDF 页 = 正文页+1，首篇 PDF p.2 即 085107-1）。

## 出处
- Khalighi, Mikaeili. "A floating wide-band current source for electrical impedance tomography." Review of Scientific Instruments 89, 085107 (2018). doi:10.1063/1.5028435。正文 10 页。
- bib key：`khalighi2018`。

## 核心命题（原文）
1. **主张：EIT 图像质量取决于注流/测压硬件精度，浮地（source+sink 对称）电流源输出阻抗高于单端**（p.1 摘要）：
   > "The quality of reconstructed images in Electrical Impedance Tomography (EIT) depends on two essential factors: first, precision of the EIT hardware in current injection and voltage measurement and second, efficiency of its image reconstruction algorithm. ... Floating-load current sources constructed using sink and source drivers have better performance and higher output impedance than grounded-load (single-ended) current sources."
2. **误差机制清单：Howland 输出阻抗受三因素限制——反馈路径失配、有限开环增益、有限带宽；电阻桥平衡是提高输出阻抗的条件**（p.4）：
   > "There are three factors that affect this model's output impedance: imbalance in negative and positive feedback paths, the finite open-loop gain of OPAMP, and the finite bandwidth of OPAMP. ... Therefore to maximize the output impedance, related to the first and second factors, the resistor bridge of the Howland must be balanced as much as possible, and hence, high precision resistors must be used."
   （失配条件 R4/R3 = R2/R1，式 (5)，p.4——"失配→误差"以电桥平衡条件形式出现，是 H2 语境内最接近的一条。）
3. **新设计 DTOA（双 TOA 浮地 Howland）：合规电压与输出阻抗均翻倍**（p.5）：
   > "Expression (8) shows that the voltage compliance of the DTOA floating model is twice as much as that of the TOA and EH. ... The other main advantage of this model is that if (5) would be satisfied for both parts, the output impedance of DTOA is two times of the TOA output impedance."
4. **浮地结构的 CM 收益与失配风险（结论里成对出现）**（p.9，CONCLUSION）：
   > "The terminals of these current sources are not connected to the ground directly but via a large impedance. This results in common-mode voltage to be reduced."
   > "The main disadvantage of this group is that if the both parts of the floating VCCS would not be balanced symmetrically, then a terminal injects the current value of I1 to the load, and the other one sinks the value of I2; hence the difference value (I1 − I2) is sank from (or injected to) the ground via the unwanted impedances connected to the load, which can cause error in the measurements."
   （两半失配 → 差值电流经对地寄生阻抗泄漏——差分结构失配敏感性的电流版表述。）
5. **实测与仿真差距大：1 MHz 处仿真 317 kΩ vs 实测 ≈150 kΩ**（p.7，表 I/II）：
   > "The measured output impedances of all converters, at a frequency of 1 MHz, are shown in the Table II."（表 II：EH ≈34 kΩ；TOA ≈48 kΩ；DEH ≈80 kΩ；DTOA ≈150 kΩ；表 I 仿真 DTOA @1 MHz = 317.45 kΩ）
6. **工艺细节：驱动屏蔽同轴电缆 + 电流走线下不铺地平面以降寄生电容；GIC/NIC 增阻抗尝试使 DTOA 失稳被弃用**（p.8）：
   > "In all practical experiments, the electrodes ... were connected to the EIT system (current source part) via driven-shield coaxial cables which were so effective and useful to reduce the stray and parasitic capacitances. In addition, to reduce the stray capacitance of the PCB, the ground plane has not been put under the current-carrier tracks. The GIC ... and NIC ... methods were also tested ...; however, the results were not good, and they made the DTOA unstable."

## 关键数值（原文）
- 仿真输出阻抗 @≈300 kHz / 1 MHz / ≈3 MHz（Ω，表 I，p.7）：EH 302.08 K / 90.94 K / 30.092 K；TOA 523.24 K / 157.49 K / 52.064 K；DEH 604.94 K / 182.12 K / 60.261 K；DTOA 1.0624 M / 317.45 K / 104.236 K。
- 实测 Zout @1 MHz（表 II，p.7）：EH ≈34 kΩ、TOA ≈48 kΩ、DEH ≈80 kΩ、DTOA ≈150 kΩ。
- SNR：仿真 ≈90 dB；实测 70 dB（1 MHz、1 kΩ 负载，R&S FS315 频谱仪，p.8–9）。
- 器件：AD844（66 MHz，电流反馈）、AD845（12.8 MHz）；R1–R4 = 1 kΩ（0.1% 精度）、R5 1–5 kΩ（p.6–7）。
- EIT 常用电流 0.1–5 mA 正弦（p.2）；仿真/实测输出电流 1 mA；幻象成像 2 MHz/1.5 mA 与 2.5 MHz/1 mA；在体胸腔 100 kHz 与 1 MHz（p.7–8）。
- 幻象：16 电极胸廓形盐水槽，目标铝棒 Ø4.3 mm（p.7）。
- TOA 桥臂最佳值：R1–R4 = 1 kΩ，R5 = 1–3 kΩ（引文 [30]，p.4）。

## 对 P1/P2/P3 的对照
- **P1（G_DC≡0 元件条件）**：**低-中**。同族电路（Howland/VCCS）、同款"失配条件+元件精度"话语（命题 2），但目标物理量不同：EIT 关注 **AC 输出阻抗随频率跌落**（寄生电容 Cs 主导，p.3），P1 关注 DC 直流通路增益条件。无 DC 条件推导，不构成 P1 的既有答案；其"实测远低于仿真（150 kΩ vs 317 kΩ）"恰好支持"前端误差必须落地实测"的 P1 立场。
- **P2（Kelvin 结构地板 ≈56 dB）**：无。无四线/接触电阻议题（EIT 电极阻抗另行由 CEM 建模吸收，本文不涉）。
- **P3（衰减可达上界）**：无。无 DC 漂移/衰减模型；其"输出阻抗随频率降"是 AC 现象。
- **方法学（门槛化）**：无（图像重建非分级阈值）。
- **killRisk**：无。注意与 AGENTS.md 既定否决项的关系：本设计是 Howland 家族用于 **EIT AC 注流**，与本工作区"改进型 Howland 用于 DC 恒流激励被否"（旁路电流破坏同一电流前提）不冲突——对象与频率域都不同，引用时不构成反例。

## 没读到的
- 输出阻抗测量法引文 [32] 的细节（式 10 用 RT=100 Ω、RP=2.9 kΩ 两态开关法，具体来源待核）。
- 测压通道（voltage measurement module）的设计与误差：本文只做电流源，测压部分引其他文献。
- 频谱仪截图（Fig. 12）中的谐波逐值：未摘。
- 0.1% 电阻失配对 Zout 的敏感度定量（只有"必须用高精度电阻"的定性要求）。
