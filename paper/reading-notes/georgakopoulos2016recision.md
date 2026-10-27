# 精读笔记 · Georgakopoulos 2016《Precision Measurement System for the Calibration of Phasor Measurement Units》（CPEM 2016）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> CPEM 2016 摘要文（2 页，无期刊页码），页码按 PDF 页 1–2 记。文本层度符号丢失处已标待核。

## 出处
- D. Georgakopoulos and S. Quigg, "Precision Measurement System for the Calibration of Phasor Measurement Units", 2016 Conference on Precision Electromagnetic Measurements (CPEM 2016), Ottawa, July 2016. doi:10.1109/cpem.2016.7540662.
- 本地：`H7-比率与电阻计量/georgakopoulos2016recision.pdf`（2 页）。bib key：`georgakopoulos2016recision`（literature.bib L1082）。
- 机构：澳大利亚国家计量院 NMIA。

## 核心命题（原文）

1. **系统定位：PMU 稳态校准、溯源到国家计量标准**（p.1）：
   > "At the National Measurement Institute Australia, we have developed a measurement system for the calibration of PMUs under steady state conditions. This paper describes the operation and calibration of the system, with emphasis on traceability to national standards of measurement."（p.1，Abstract）
   中文：本文是计量院级 PMU 校准装置论文——电压/电流/相位/频率四量溯源链描述，与电阻比率无直接关系。

2. **【方法学上唯一可借用点】同一台 DSVM 复用测电压与电流——共享仪器的代换/共模消去思路**（p.1）：
   > "For the current waveform, the output of AWG2 is converted to current by a transconductance amplifier and at the same time the current is measured by a current shunt and a DSVM. The same DSVM is used for the current and voltage measurements. The switches shown in Fig. 1 are not physically present and are only drawn to demonstrate the principle; in practice the connections are hardwired."（p.1）
   中文：电流（经分流器）与电压共用同一 DSVM——仪表自身误差在两通道测量中强相关、可相消，这是比率测量/代换法的弱形态；对 P1 只是方法学远亲，非证据。

3. **时间基准与不确定度口径**（p.2）：
   > "The synchronization is based on a 10 MHz clock signal and a 1 PPS timing signal. The 10 MHz clock and the 1 PPS timing signal are obtained from a cesium primary standard (Symmetricom 5071A) that is designated as the National Frequency Standard (NFS)."（p.1–2）
   > "The 1 PPS signal is connected to the external trigger input of the DSVM by a cable introducing a time delay of (662.8 ± 0.5) ns. All the uncertainties given in this paper are expanded uncertainties with a coverage factor k = 2.0."（p.2）
   中文：铯钟 10 MHz + 1 PPS 作时基；触发电缆延迟逐项修正（662.8 ± 0.5 ns）；不确定度口径 k=2.0——注意引用其数值时勿与 k=1 混淆。

4. **校准结果：四量不确定度均优于 IEEE C37.118.1 要求**（p.2）：
   > "The system was calibrated for voltage magnitude by means of a transfer standard (Fluke 5790A) of known ac-dc difference. The expanded uncertainty of the calibration was better than 65 µV/V."（p.2）
   > "The resulting uncertainty of current magnitude was better than 76 µA/A."（p.2）
   > "The estimated uncertainty of phase is better than 0.002 at 50 Hz."（p.2，文本层度符号丢失，应为 0.002°，**待核原 PDF**）
   > "The estimated uncertainty was better than 22 µHz/Hz."（p.2，频率）
   > "The uncertainty of the rate of change of frequency is estimated to be better than 1.6 mHz/s."（p.2）
   > "The expanded uncertainties (k = 2.0) for the relevant quantities are significantly lower than those specified in IEEE Std C37.118.1."（p.2，Conclusion）

## 关键数值（原文）
- 电压通道：AWG 峰值 ≤10 V；正弦 THD < 0.02%（p.1）。
- 采样：Agilent 3458A DSVM，18-bit、50 kS/s（p.2）。
- 时基：Symmetricom 5071A 铯钟（NFS）；1 PPS 电缆延迟 (662.8 ± 0.5) ns（p.2）。
- 不确定度（全部 k=2.0 展开不确定度）：电压幅值 <**65 µV/V**（经 Fluke 5790A ac-dc 传递）；电流幅值 <**76 µA/A**（经分流器 + ac-dc 传递）；相位 <**0.002° @50 Hz**（含 DSVM 内部时延变化分量；经 Clarke-Hess PM5500 相位传递标准）；频率 <**22 µHz/Hz**；ROCOF <**1.6 mHz/s**（p.2）。
- 电流分流器：NMIA 自制（引 Budovsky 2007/2009），相位修正参照可计算微电位计电阻（p.2）。

## 对 P1/P2/P3 的对照
- **P1（消去条件）**：相关度 **无**。全文无差分/共模/CMRR/电桥消去内容；唯一弱关联是"同一 DSVM 测两通道"的共享仪器思路（见核心命题 2），属代换法远亲，不构成 P1 的证据或反例。killRisk：**无**。
- **P2（Kelvin 地板）**：相关度 **无**。分流器四线细节未展开（只引用 [8][9]），无引线电阻/地板讨论。
- **P3（平坦度约束衰减上界）**：相关度 **无**。无滤波器/频域界内容。
- **方法学（门槛化）**：可借用的只有**不确定度报告口径**——所有数值标 k=2.0、逐项列传递标准链（AWG→传递标准→NFS）；P1 写实验章节时的计量报告规范可参照此文风格。
- **killRisk 总评：无**（换领域文献，对 P1/P2/P3 均无威胁、无支撑）。

## 没读到的
- 分流器本体设计（ac-dc 差、相位角误差细节）——在引文 [8][9]（Budovsky 2007/2009），不在本文。
- TVE/FE/RFE 的算法误差分析（只给结果性不确定度，无推导）。
- 系统框图 Fig.1 之外的电路细节（放大器、滤波、隔离）。
- 相位不确定度 0.002° 的度符号（文本层丢失，待核 PDF 原版）。
