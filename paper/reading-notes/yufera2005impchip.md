# 精读笔记 · Yúfera 2005《A Tissue Impedance Measurement Chip for Myocardial Ischemia Detection》（IEEE TCSI 52(12):2620–2628）

> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> 读法：pdftotext 逐页；印刷页码 2620–2628 = PDF p.1–9。⚠️ 文本层数学符号（Z、I、f、µ、Ω、±值）大量丢失，引用中以「[符号丢失]」标注缺口，数值凡能从上下文/图注核回的均注明，不能的写「待核」。
> 定位：H5 轴（阻抗测量芯片）——**ADC 为连续时间 OTA-C 增量型（非开关电容输入）**，是 H5「输入结构」分类的对照型样本；**P2 域价值最高**：四电极结构「电极界面效应靠设计消去」的早期（2005）完整实现。

## 出处

- Alberto Yúfera, Adoración Rueda, José Maria Muñoz, Ricardo Doldán, Gildas Leger, Esther O. Rodríguez-Villegas（IMSE-CNM-CSIC / 塞维利亚大学 / Imperial College）, "A Tissue Impedance Measurement Chip for Myocardial Ischemia Detection," *IEEE Trans. Circuits and Systems I: Regular Papers*, vol. 52, no. 12, pp. 2620–2628, Dec. 2005. DOI: 10.1109/TCSI.2005.857542（EU MicroCard 项目 IST-1999-33485）。
- 本地全文：`fulltext/H5-kickback/yufera2005impchip.pdf`（9 页）。

## 核心命题（原文）

1. **核心主张：四电极结构「靠设计」消去电极界面效应（P2 域直接证词）**（摘要，p.2620）："The designed chip will be used in a four-electrode based setup where the effect of electrode interfaces are cancelled by design."（四电极布置下，**电极界面效应被设计本身消去**——Kelvin 结构的卖点以"cancelled by design"表述）
2. **四线方案接线**（p.2621；Fig.2(b) 图注）："A reference current [符号丢失] is injected through two electrodes to stimulate the tissue sample (SUT) of unknown impedance [符号丢失]. The other two electrodes take out the SUT voltage response [符号丢失], whose value is related to the magnitude and phase of [符号丢失]."；图注 "Four-wire scheme for Z impedance measurement. (Terminals 1 and 4 are for excitation and terminals 2 and 3 are for measure.)"（外对 1/4 注流、内对 2/3 取压——标准 Kelvin 四线）
3. **电极接触电位失配 → 共模输入范围（P1 域旁证）**（p.2621）："Mismatch in contact potential of the electrode model ([符号丢失]) could occur but this has been considered in the values taken for the [±][符号丢失]-mV range for the four wire electrodes model [Fig. 4(b)]. This range will define the common-mode input range of the IA."（**四个电极接触电位的失配决定 IA 共模输入范围**——失配不产生测量误差而是转嫁为 CM 范围需求，四线结构下接触电位不以差模误差出现）
4. **IA 规格由电极接触电位主导（失配后果的量化语境）**（p.2623）："The dc levels imposed by contact potentials are in the [符号丢失]-mV range, and they are significantly larger than the signals to be amplified (from 0.5 to 50 mV as maximum). We have selected a 20-dB gain for the amplifier, and a dynamic range of 74 dB. The CMRR required is of 110 dB."（**接触电位直流水平显著大于待测信号（0.5–50 mV）；CMRR 要求 110 dB**）
5. **正交时钟失配 → 幅相误差的泰勒展开定量（P1 域最接近的解析式）**（p.2624）："The accuracy in the generation of the in-quadrature signals [符号丢失] and [符号丢失] is affected by the mismatches between the highpass filters and the comparators. Considering a [符号丢失] deviation of the nominal value and making a Taylor series approximation, the real and imaginary parts of the impedance will be given as (5)(6)… for a maximum phase angle of [符号丢失], the errors are of a 1.08% in magnitude and 2.11[°] in phase (for [符号丢失], 2.5% and 4.14[°] are obtained, respectively). Errors in clock signals below [符号丢失] should be obtained by design."（**失配→幅相误差有泰勒一阶定量式与预算阈值（时钟误差须低于某限值）**——是「门槛化」思想的域内先例，但域为解调时钟失配而非无源 RC 网络）
6. **ADC = 连续时间 OTA-C 一阶增量型（H5 域输入结构对照样本）**（p.2624–2625）："A first-order incremental ADC [17] has been chosen because it gives good accuracy for low frequency conversion rates. A continuous-time implementation was realized, in which the integration function is performed by using the OTA-C technique [18], [19."（**CT 积分器、无 SC 输入采样 → 无开关电容输入踢回问题**；片内开关仅在 mux/INV（选通输入/参考与极性反转）与 RES（复位），"Both blocks are implemented with CMOS analog switches, whose on-resistance must be optimized", p.2625）；"An implicit advantage of continuous time implementations is the good frequency scaling behavior since the clock drives the conversion time but not the ADC resolution."（p.2626）
7. **激励缓冲器的高通型输出阻抗（电流源 + 直流低阻防失调爆表）**（p.2622）："Considering a [符号丢失] load composed by the series of two electrodes and the tissue to be measured, the buffer we propose has a high-pass output impedance. That is, it has a low output impedance at low frequencies (near dc and below the band of interest) and a high and constant output impedance in the 1- to 20-kHz frequency band. This allows to minimize the effects of any offset in the differential signal."（带内高阻=恒流、直流低阻=避免电极失调电压被高阻电流源顶出界——**驱动网络按频段塑形输出阻抗**的罕见实例）
8. **滤波器阶数由误差预算定（H4/P3 型比）**（p.2623）："A fourth-order low-pass filter (40-dB/dec attenuation), with low cutoff frequency around 200 Hz is necessary to select these dc signals and maintain the ripple errors below 1% at 2-kHz frequency."（四阶 LPF @200 Hz → 2 kHz 处纹波误差 <1%——**衰减指标 ← 误差预算**的直接换算）

## 关键数值（原文）

- 系统（p.2621）："For safety conditions, the excitation current must be always below 5 µA, with frequency in the range 1 to 20 kHz"；量程 "from 100 Ω to 10 kΩ"（Ω 系从上下文核回，原文符号丢失），相位 "[0, 30°]"；"the main objective is not to obtain precise values of these parameters, but to detect large changes"
- 缺血动力学（p.2620，Fig.1）："The occlusion starts in [符号丢失]， and after one hour, the magnitude of impedance becomes 100% higher than the initial value."（冠脉结扎 1 小时 → 阻抗幅度 +100%）
- SCO（p.2621–2622）：三频率 1/8/16 kHz（2-bit 字选电容库）；OTA 弱反型，偏置 10 nA 输入对；gm ≈ 100 nS 量级（"a [符号丢失] of around 100 nS for each OTA is required", p.2622）
- IA（p.2623）：增益 20 dB、DR 74 dB、CMRR 110 dB（要求值）；实测 CM 范围 586 mV、差分直流范围 524 mV、带宽 980 Hz–19.7 kHz（带通型——同时滤电极直流差分电平）
- 解调（p.2623）：两相参考相干解调；四阶 LPF（两个双二阶级联）、fc≈200 Hz、纹波误差 <1% @2 kHz；为省电容面积 "bias currents of 2 nA have been used to obtain low transconductance to capacitance ratios"
- 正交误差（p.2624）：幅值 1.08% / 相位 2.11°（另一组 2.5% / 4.14°）——对应偏差量的符号已丢失，**待核**
- ADC（p.2624–2626）：12-bit、50 kHz 时钟、输入范围 ±[0.5] V（Fig.17 图注 "V[ref] = 500 mV" 核回）；积分器最大输入 [0.5] V、[符号丢失] pF 电容（正文数值丢失，**待核**）；同一原型在 2 MHz 时钟 "with equal performance"
- 整机（p.2626）：0.8 µm CMOS、3 V（电池供电目标）、core 6.95 mm²、总电流 700 µA
- 标定流程（p.2626）：以 100 Ω 电阻为参考 → 测 Re/Im → 取与理想 (100 Ω, 0°) 偏差为失调 → 后续全部扣除 → 每个工作频率重复
- 实测（p.2626–2627）：体外 0.9% NaCl 基准 ≈200 Ω、稀释 1:1–1:40 五档、三频率；体内大鼠肾 60 min 缺血："The impedance module increases according to the severity of the ischemic damage while the phase decreases."（电极阵列插入深度 5 mm）

## 对 P1/P2/P3 的对照

- **P1（失配消去条件，G_DC≡0）——相关性：低（同族思想、异域实现）**。本文的「失配→误差」处理有三处但都非 P1 命题：① 电极接触电位失配 → 不产生差模误差、只决定 CM 输入范围（p.2621）——**四线结构把失配移出信号路径**的思想与 P1 同向；② 正交时钟失配 → 幅相误差的泰勒定量 + 设计阈值（p.2624）——「失配→误差有解析式、有门槛」的域内先例（时钟域）；③ IA 失配靠选 CMRR 110 dB 压（规格化处理）。killRisk：无。
- **P2（Kelvin 结构地板 ≈56 dB）——相关性：中高（P2 前提的四电极域内权威实现，但无地板量化）**。本文是**四线消去电极界面效应**的完整单片实现（p.2620 摘要 + p.2621 接线），且工程链完整（电极模型→CM 范围→IA 规格→标定扣除残余）。但**无「四线相对两线改善多少 dB」的地板分析**——两线模式根本未讨论。引用价值：①"cancelled by design"（p.2620）可作 P2 前提（结构消去而非校准消去）的域内出处；② CMRR 110 dB 要求 + 接触电位大于信号（p.2623）说明四线结构下的残余误差主导项是共模抑制而非引线电阻。killRisk：无（其 CMRR 110 dB 规格与 P2 的 ≈56 dB 地板是不同量（前者为 IA 部件规格、后者为结构地板），不构成冲突，但引用时必须区分口径）。
- **P3（平坦度约束衰减上界）——相关性：低**。无 AAF 议题（系统为 1–20 kHz 激励 + 相干解调 + 200 Hz LPF；LPF 阶数由纹波误差 <1% 预算定，p.2623——是「误差预算→阶数」换算的又一实例，无平坦度概念）。killRisk：无。
- **方法学（D1–D10，H5 域）——相关性：中（对照型样本）**：
  - **输入结构**：CT OTA-C 增量 ADC + 相干解调——**无 SC 输入采样、无输入缓冲踢回问题**；开关仅用于 mux/极性反转/复位，唯一开关要求是 "on-resistance must be optimized"（p.2625，定性）。在 H5 轴「输入结构（开关电容/阻性/缓冲）」分类中，这是**连续时间阻性输入**代表——恰好说明「踢回是否成为问题取决于输入结构」，是 P1 论文 H5 章可以做结构分类的第三人证；
  - **D5/D9**：无建立时间预算（50 kHz 时钟极慢）；无 kickback 内容（全文无该词）；
  - **激励驱动**：高通型输出阻抗缓冲器（p.2622）是「驱动网络按频段塑形阻抗」的独特样本，与外置 RC 选值的思路形成对照。
- killRisk 总判：**无**。

## 没读到的

- **符号丢失严重的段落需对照原刊核对**：式(1)（振荡频率）、式(2)（带通函数）、式(3)–(8)（解调输出与失配误差）、电极接触电位具体 mV 数（p.2621 的 ±[符号丢失] mV 范围）、ADC 积分器电容值与跨导值（p.2626）——文本层全部缺符号，**待核**（建议对照 IEEE Xplore 正式版或纸本）。
- 四电极「消去」的机理分析无公式推导（未给出电极阻抗在两线 vs 四线下的误差表达式；电极模型 Fig.4 的元件值在正文未列全）。
- ADC 的 DNL/INL 具体数值（Fig.18 为图）正文未给数；12-bit 精度与阻抗测量的误差贡献分解（IA/解调/ADC 各占多少）未做误差预算总表。
- 参考文献 [9]（Pallás-Areny & Webster《Analog Signal Processing》——两相参考相干解调法出处）、[13]（Yúfera & Rueda 电流驱动器）、[17]（Robert/Temes 一阶增量 ADC）、[18]（Krummenacher-Joehl 线性化 OTA）未读——其中 [9] 是测量方法学根基。
- 体内实验只做了 1 kHz 单点（Fig.22），1/8/16 kHz 全频段体内数据未见；大鼠肾 60 min 之后的恢复期数据未见。
