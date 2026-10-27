# 精读笔记 · Mayes 2015《Easy Drive delta-sigma analog-to-digital converters cancel input current errors》（Analog Circuit Design Vol.3, LTC 设计札记）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。

## 出处
- Mayes, Mike（Linear Technology），"Easy Drive delta-sigma analog-to-digital converters cancel input current errors", *Analog Circuit Design Volume Three: Design Note Collection*, Elsevier/LTC, 2015, Chapter 338, book pp. 727–728（DOI 10.1016/B978-0-12-800001-4.00338-0）；PDF 物理页 1–2。LTC248x 家族（16/24 bit）。
- 文件：`/home/anning/Documents/Obsidian Vault/20-硬件工程/10-项目设计/p1-文献谱系/fulltext/H5-kickback/mayes2015.pdf`

## 核心命题（原文）
1. **总命题：大 RC 网络直挂 ΣΔ 输入而不损 DC 精度**（p.727）：> "It is now possible to place large RC networks directly in front of high resolution ΔΣ analog-to-digital converters without degrading their DC accuracy (see Figure 338.1). The LTC248x family of converters solves this problem with Easy Drive technology, a fully passive sampling network that automatically cancels the differential input current."（"fully passive"指片内采样网络无缓冲器，靠开关图形算法消差分输入电流。）
2. **kickback 机理：SC 输入开关至 10 MHz，欠建立 RC 造成大 DC 误差**（p.727）：> "The problem is that the input structure of ΔΣ converters is a switched capacitor network. Capacitors are rapidly switched (up to 10MHz) between the input, reference and ground as a function of the final output code. Each time these capacitors are switched to the ADC input, a current pulse is generated. ... External RC networks that do not completely settle during each sample period cause large DC errors."（H5 轴的教科书式表述：踢回 = SC 电容开关电流脉冲；R 选择约束 = 每采样周期内完全建立。）
3. **消去条件落在"外接电阻平衡"上**（p.728）：> "Since the average differential input current is zero, the total error introduced by the external RC network is zero if the resistance tied to the plus/minus inputs of the ADC is balanced."（**元件条件**：正负输入端外接电阻平衡 ⇒ 外部 RC 网络引入总误差为零——与 P1 的"消去条件 = 元件条件"同构，但实现位置在片内算法 + 一个外部平衡条件。）进一步：> "no errors are introduced even if the external resistances are not balanced, as long as the common mode input voltage is equal to the common mode reference voltage."（替代条件：CM 输入 = CM 基准。）
4. **残差归属：共模电流不消、留偏置可校**（p.727）：> "When summed over the entire conversion cycle, the total differential input current is zero, independent of the differential input voltage, common mode input voltage, reference voltage or output code. The common mode input current is constant and proportional to the difference between the input common mode voltage and reference common mode voltage."（消去仅及**差分**电流；共模电流≠0，且 > "the common mode input current results in an offset voltage which may be removed through system calibration"（p.728）。）
5. **否决片内缓冲与粗/细采样两条路线**（p.728）：缓冲器——> "the fact is data converters using on-chip buffers suffer from the limitations of those amplifiers. The common mode input range can no longer swing rail-to-rail. Input signals need to be shifted at least 50mV above ground and a volt or more below VCC. Amplifier offset errors, offset drift, PSRR, CMRR and noise are combined directly with the input signal"（并 > "most manufacturers of ΔΣ ADCs using this technology offer a mode to shut off and bypass on-chip amplifiers"）；粗/细采样——> "While this decreases the magnitude of the spikes seen at the input of the ADC, it results in nonlinear settling errors as a function of op amp offset voltage, CMRR, input signal level and external RC time constants."（两种缓冲式方案的失效模式均被点名：这正是"外置无源网络 + 无缓冲直驱"路线的产业动机证据，直接支撑 P1 的问题设定。）
6. **运放与 ADC 之间用大电阻隔离稳定**（p.728）：> "The addition of a large resistor between the amplifier output and the ADC input isolates the amplifier from the large bypass capacitor, thus improving its stability."（R 值选择的另一约束面：隔离运放容性负载。）

## 关键数值（原文）
- **20 ppm vs 100,000 ppm 对比**（p.728）：> "Resistances up to 100k, combined with capacitors up to 10μF, may be placed in front of the ADC with less then 0.002% full-scale error (20ppm), while conventional ΔΣ ADCs with the same input network have greater than 10% full-scale errors (100,000ppm)."（R≤100 kΩ + C≤10 µF；Easy Drive ≤0.002% FS；常规 ΣΔ 同网络 >10% FS——三个数量级差。原文 "less then" 系排印之误。）
- **RC 上限**（p.727）：> "maintains 0.002% full-scale error with input RC networks up to 100kΩ and 10μF."
- **kickback 尖峰衰减**（p.728）：> "An external 1μF capacitor reduces a 1V spike to 18μV."（1 V → 18 µV，≈95 dB 电荷分压；反推单次采样等效电荷 ≈1 V×18 pF 量级——推算值，原文未给 C_SC。）
- SC 开关频率上限（p.727）：> "up to 10MHz"。
- 粗/细采样弃用区（p.728）：> "bypass coarse/fine sampling for input signal levels below 100mV."
- 缓冲器输入摆幅损失（p.728）：> "at least 50mV above ground and a volt or more below VCC"。

## 对 P1/P2/P3 的对照
- **P1（消去条件 = 元件条件）**：**最近缘的商业先例**。Easy Drive 的消去 = 片内开关图形算法（专有）使平均差分输入电流为零 + 外部条件（R 平衡 或 CM_in=CM_ref）。与 P1 的 G_DC=H_N−H_P≡0 纯外置无源网络条件**实现位置不同**（片内电荷域 vs 片外传输函数域），但"平衡元件条件 ⇒ DC 误差为零"的命题形状相同。P1 必须显式划界：Easy Drive 只保证 DC（平均电流为零），不给出外部网络的 AC/抗混叠设计方法与衰减定量上界，其共模残差需系统校准兜底。
- **P2（Kelvin 结构地板 ≈56 dB）**：未涉 Kelvin/地板；其"balanced R"是单端对称电阻条件，非四线制地板结构。无威胁。
- **P3（衰减可达上界）**：文中只有点值（1 V→18 µV）与工程上限（100 k/10 µF @20 ppm），**没有**"衰减可达上界"的一般化论证；反而是 P3 可引用的产业数据点（外部 RC 的尖峰衰减实测口径）。
- **增量四（门槛化方法学）**：提供了业界口径的门槛证据——"外部 RC 须在每采样周期内完全建立，否则大 DC 误差"（p.727）+ R/C 允许值上限表（100 k/10 µF）。可作为"R 过大→kickback 残留"的定量锚点，但无建立时间/回稳时间的显式公式。
- **killRisk：须划界**。理由：①这是与 P1 命题形状最接近的既有技术（passive + 消去 + 元件条件 + 外置 RC），若 P1 不点名划界，审稿人必问与 Easy Drive 的差别；②但它消去发生在片内采样图形（专有算法、DC 域、差分通道），P1 主张外置无源差分网络的传输函数级消去条件 + AC 衰减上界 + 噪声地板，属可划清的不同层与不同主张集合；③若 P1 文中把"完全无源消去"说成首创而不引 Easy Drive，则构成撞车风险——引用并划界即可消解。

## 没读到的
- Easy Drive 消去算法的内部结构（开关图形如何保证周期和为零）未展开（原文明说 "An innovative front-end sampling architecture controls the switching pattern of the capacitor array"，p.727，无细节）；相关专利未读——待核。
- Figure 338.1/338.2 为框图照片，未逐字核（题注已录）。
- "0.002% FS" 的条件口径（未说明是否含温漂/线性度；按上下文指 DC 误差）——待核 LTC248x 手册。
