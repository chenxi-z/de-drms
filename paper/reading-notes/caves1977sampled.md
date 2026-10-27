# 精读笔记 · Caves 1977《Sampled Analog Filtering Using Switched Capacitors as Resistor Equivalents》（IEEE J. Solid-State Circuits, SC-12(6), pp.592–599）

> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> 页码口径：**期刊印刷页码**（PDF 第 1–8 页 = 印刷 p.592–599，逐页对应已核对）。
> 文件：`fulltext/H2-差分CMRR/caves1977sampled.pdf`；bib key `caves1977sampled`（bib 注记归 H3·时间线，实为 H2/H3 交叉）。

## 出处

- J. T. Caves, M. A. Copeland, C. F. Rahim, S. D. Rosenbaum, "Sampled Analog Filtering Using Switched Capacitors as Resistor Equivalents," *IEEE J. Solid-State Circuits*, vol. SC-12, no. 6, pp. 592–599, Dec. 1977. DOI 10.1109/jssc.1977.1050966.
- 作者单位：Bell-Northern Research（Caves, Rosenbaum）与 Carleton University（Copeland, Rahim）。开关电容电阻等效的实验正典（Fried 1972 概念先行，本文 + 同期 Hosticka/Gray 为三大独立工作之一）。

## 核心命题（原文）

1. **开关电容与电阻的平均电流等效：R = T/C_R**（p.592, §II-A）：
   > "As this delivery occurs at every sampling interval T, this represents an average current flow of CR (U1 − U2)/T. The network shown in Fig. 1(a), therefore, simulates a resistor R of value R = T/CR. … An alternate version (parallel-switched capacitor) shown in Fig. l(b) also simulates a resistor as defined."
   （解释：SC 电阻等效的基石公式——后续"匹配的时间常数在 SC 域=匹配的电容比+共享时钟"即源于此。）

2. **SC 精度由开关频率与电容比决定，可做到极高精度——与绝对 RC 值的失配形成对照**（p.592, §I）：
   > "In contrast, the precision of switched capacitor circuits is governed by the switching frequency and by the capacitor ratios, which can be controlled to extremely high precision in MOS-type integrated-circuit technologies."
   （解释：**全文对 P1 最相关的一句**。RC 时间常数匹配受制于绝对 R、C 双重失配；SC 把"τ 匹配"降维成"电容比匹配 + 共时钟"，从工艺结构上逼近精确匹配——这是 P1"单级 τ 匹配充要"在实现层的对偶参照，但本文并未把它表述为任何差分消去条件。）

3. **等效电阻公式随互连拓扑复杂化——无源互连下逐元件等效不再简单**（p.593, §II-C）：
   > "Similarly, if two resistors are connected to a capacitive node … the resistive equivalents are modified to include terms in all three capacitances connected to the node. As the degree of interconnection rises, the complexity of the resistive equivalence expression increases."
   （解释：元件级 RC↔SC 等效在多元件互连（梯形）时表达式按节点电容耦合膨胀——与 P1"多级梯形消去条件不再由单级匹配充分"在"级联/互连破坏简单条件"的方向上同构，但本文只谈等效精度，不谈消去。）

4. **差放可抑制电源/地共模干扰（本文用单端放大器+电路措施压到随机噪声主导）**（p.594, §III-A）：
   > "A differential amplifier would be preferable for many applications, to reject possible common-mode interference from the dc power supply and ground connections. However, in this experiment, we were able to reduce such effects to levels where random noise became dominant by circuit precautions."
   （解释：全文唯一的共模语境——工程定性陈述，无 CMRR 数值、无频率特性。）

5. **有限脉宽使等效电阻增大 1/(1−e^{−Δ/τc}) 量级**（p.594, §II-D-3）：
   > "Comparing (10) with (5), we observe that one effect of finite pulsewidth is to increase the resistive value of the switched capacitor by the proportion 1/(1 − e^{−Δ/τcS}). For example, if Δ is four times τC', the resistive value of the series-switched capacitor increases by 1.86 percent."
   （解释：非理想性对等效 R 的系统偏差 1.86%@Δ=4τ——P1 讨论实现层失配时的可用参照量级。OCR：Δ/τcS 下标略有重排，公式形状无误。）

6. **连续域 RC 设计方法可直接沿用，z 变换作精确修正**（p.598, §IV Conclusions）：
   > "The conventional theory and design methods normally used for active RC filters may be directly applied in many practical situations without significant change, or used as a design aid along with more exact z-transform analysis."
   （解释：SC 滤波器设计=RC 知识库的映射——P1 若扩展到 SC 实现的差分 AAF，其 s 域消去条件可先在连续域建立再经 z 域修正，本文提供了这一映射合法性的出处。）

## 关键数值（原文）

- p.592：R = T/CR（式 1）；p.593：等效时间常数以时钟周期计 = (C′+CR)/CR ≈ C/CR（式 7 讨论）。
- p.594：SC 噪声"about 20 dB lower than the input noise in present MOS operational amplifiers"；非线性结电容使标称阻值缩减比 2CD/(CR+2CD)。
- p.594：Δ = 4τC′ 时串联 SC 等效电阻增大 1.86%。
- p.595（Fig. 6 图注）：无源一阶 LP：C = 151 pF（负载），采样间隔 T = 10 µs（OCR "10 M"），CR = 4 pF（标称）/4.27 pF（含杂散估计）；−3 dB 电平与 6 dB/octave 斜率标注。
- p.595：1 V rms 输出下二次谐波失真低于信号 50 dB。
- p.597：泄漏/馈通：平均输出失调 2.5 mV（衬底 −5 V）；衬底 −7 V 时增至 11 mV；时钟馈通幅度 6 mV（50 Hz 低钟频下）。
- p.597：噪声谱 @100 Hz 带宽平均 −130 dB；10 Hz–10 kHz rms 噪声 7 µV（OCR "7 BV"）；"possible to attain a signal-to-noise ratio of over 100 dB for audio filtering, assuming a 1-V dynamic range"。
- p.598：二阶带通实测 Q = 7.07 对理论 Q = 8；主钟 f0 = 125 kHz，带通中心 ≈500 Hz。
- **无 CMRR/dB 口径共模抑制数据**（共模仅出现 1 次，见命题 4）。

## 对 P1/P2/P3 的对照

- **P1（消去条件）**：相关度**中**。未给出任何 G_DC(s)≡0 型差分消去条件；但其"精度由电容比+共时钟决定"（p.592）与"互连抬升等效表达式复杂度"（p.593）为 P1 提供两条实现层论据：(a) SC 工艺天然把 τ 匹配变成可高精度控制的电容比匹配；(b) 多元件互连使逐级简单等效失效。方向与 P1 一致（支持"多级条件复杂化"），**不构成 kill**。
- **P2（Kelvin 地板 ≈56 dB）**：**无**。无 Kelvin 结构、无共模抑制地板数值。
- **P3（平坦度约束衰减上界）**：**无**。无衰减-平坦度权衡；最接近的是奈奎斯特频率附近差分方程解发散的讨论（p.595："a significant divergence occurs"，仅指 SC 与连续解之差）。
- **方法学（D1–D8 门槛化）**：相关度**低**。可借用的门槛参照：SNR >100 dB（p.597）、失真 −50 dB（p.595）、SC 噪声比运放低 20 dB（p.594）——均为噪声/失真口径，非 D1–D8 的差模/共模抑制口径。
- **killRisk：无**。全文无差分滤波器、无 CMRR 定义式、无全频段消去条件；属 ΣΔ/SC 谱系地基而非 P1 反例。

## 没读到的

- 差分（全差分/伪差分）SC 滤波器的共模传递或消去条件——仅一句"差放更适合抑制共模"（p.594）。
- 任何 CMRR 数值、Kelvin 结构、平衡-不平衡变换。
- 多级 SC 梯形 AAF 的差模/共模分离分析（本文二阶例子是单端 biquad）。
- 式 (2)–(10) 的 OCR 细节：变量下标（τcS、C:c 等）有重排痕迹，引用公式形状已核对，逐字符引用需回看扫描图（标 [OCR损] 处理）。
- Fig. 8/10/12 曲线内部读数（描点图，OCR 不可提取）。
