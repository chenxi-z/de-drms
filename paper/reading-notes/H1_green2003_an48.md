# 精读笔记 · Steven Green (Cirrus Logic) 2003《Design Notes for a 2-Pole Filter with Differential Input》(AN48 REV2, MAR '03)

> 格式标准（全组沿用）：出处 → 核心命题（原文引用）→ 关键数值（原文）→ 对 P1/P2/P3 的对照 → 没读到的。
> 读法：pdftotext 全文逐节读（正文 p.1–4，PDF 共 6 页含封面/封底），引用一律原文加页码；不转述成模糊话。
> 文件实名 `H1_green2003_an48.pdf`（任务单写 an048，以磁盘名为准）。

## 出处

Cirrus Logic Application Note AN48REV2, "Design Notes for a 2-Pole Filter with Differential Input", by Steven Green, Copyright © Cirrus Logic, Inc. 2003, MAR '03（p.1 页脚）。6 页 PDF，正文 4 页 + 全文法律声明。参考书仅 3 本教科书（Lindquist / Williams / Reference Data for Radio Engineers，p.4），无任何期刊/会议引文。

## 核心命题（原文）

1. **"镜像配方"的直接原话（本次精读的核心证据句）**——p.1：
   > "The differential input function is accomplished by **simply duplicating the component values generated in the filter design**"
   （上下文：该电路"includes a differential input and a two-pole analog filter"，即差分功能 = 把单端 MFB 滤波器算出的元件值**原样复制**一份。）

2. 同页方法论：差分输入滤波器"easily designed using the design equations for the multiple-feedback low-pass filter"——直接套 MFB（多反馈）单端设计方程（p.1）。

3. **复制对象明确到元件清单**——Step 8，p.3：
   > "The conversion from the singled-ended circuit to the differential circuit requires **duplicating the values of R1, C2, R3, R4 and C5 in the non-inverting input**, as shown in Figure 1."
   （即五个元件 R1/C2/R3/R4/C5 全部在同相输入侧再画一份，见 Fig.1 与 Fig.5。）

4. 工程纪律只有"标称值选取"层面：Step 6 要求电容取值" sufficiently large to minimize the effects of stray capacitance"、R1 ≥ 最小输入阻抗（p.3）；Step 7 说 2.5% 金属膜电阻就近取标准值 "should not create a large change in the filter characteristics"，并建议用选定值回算验证（p.3）。**全篇没有任何一句讨论两侧取值不等（失配）会发生什么。**

## 关键数值（原文）

- 设计例（§3 Design Example，p.3）：Ho = −1；最小输入阻抗 10 kΩ；Butterworth，Fc = 50 kHz（"attenuates the signal at 20 kHz by approximately 0.1 dB and has nearly ideal phase linearity within the audio band"）；C5 = 220 pF、C2 = 1000 pF；算得 R1 = 13.77 kΩ、R3 = 3.343 kΩ、R4 = 13.77 kΩ，取标准值 **R1 = 13.7 kΩ、R3 = 3.32 kΩ、R4 = 13.7 kΩ**（p.3）。
- 归一化极点表（Table 1, p.2）：Butterworth α=β=0.7071；Bessel 1.1030/0.6368；0.01 dB Chebyshev 0.6743/0.7075；0.1 dB Chebyshev 0.6104/0.7106。
- 设计方程（p.2）：ζ = α/√(α²+β²)；ωo = 2πFc·√(α²+β²)；K = C5/C2；R1 = R4/(−Ho)；R3 = 1/{ωo·C2·[ζ ± √(ζ²−K(1−Ho))]}；R4 = [ζ ± √(ζ²−K(1−Ho))]/(ωo·C5)。
- Fig.5（p.4）差分成品图两侧元件值完全相同：R1 13.7 kΩ ×2、C2 1000 pF ×2、R3 3.32 kΩ ×2、R4 13.7 kΩ、C5 220 pF。

## 对 P1/P2/P3 的对照

- **P1（失配消去条件）**：本文是"镜像配方"谱系的**原始出处级证据**——差分化 = "simply duplicating"元件值，全文（grep 全文）**零次出现** mismatch / tolerance / tracking / CMRR 字样；唯一的 common-mode 字样是引言里"will remove common-mode errors"（p.1）这种能力宣称，无任何机理或定量分析。**这是"厂商镜像配方不含失配分析"的最强正面引文**：如果镜像配方背后有失配→共模转化的定量论证，不会在给出"复制元件值"操作指令的应用笔记里一字不提。
- **P2（Kelvin 地板）**：无涉及（本文是滤波器综合，不做测量）。
- **P3（AAF 衰减上界）**：无涉及（只给 Fc=50 kHz Butterworth 的单点例，未讨论衰减上界）。
- **引文价值**：p.1 "simply duplicating the component values generated in the filter design" + p.3 Step 8 可作"镜像配方无失配分析"论断的直接引文；Fig.5 两侧逐元件同值的图可作对照图引用。

## 没读到的

- 失配/容差/CMRR/共模转化：**完全没有**（连词都没出现）。预期得到验证。
- 没有测量数据、没有仿真、没有 THD+N 数字（纯设计方法笔记）。
- 参考文献 3 本均为滤波器综合教科书，无平衡接口/失配方向的延伸文献可追。
