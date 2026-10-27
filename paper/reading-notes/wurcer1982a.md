# 精读笔记 · Wurcer & Counts 1982《A Programmable Instrumentation Amplifier for 12b Resolution Systems》（ISSCC 1982 Digest, WPM 8.3, pp.84–85）

> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> 读法：pdftotext -layout 逐页；PDF 3 页 = 刊印 pp.84–85（PDF p.1 = p.84 正文+表 1；PDF p.2–3 = p.85 图版）。ISSCC Digest 为扫描重排件，OCR 符号（±、µ、√Hz）有损，引文按原样照录、明显 OCR 损耗以 [ ] 标注。

## 出处

- Scott A. Wurcer、Lewis Counts，Analog Devices Semiconductor（Wilmington, MA），"A Programmable Instrumentation Amplifier for 12b Resolution Systems"，1982 IEEE International Solid-State Circuits Conference, Digest of Technical Papers，SESSION VIII: DATA ACQUISITION AND CONVERSION，WPM 8.3，pp. 84–85，DOI 10.1109/isscc.1982.1156396。
- 器件即 AD524（脚注原文："*Analog Devices - AD524"，p.84）。
- bib key：`wurcer1982a`（H2 轴——三运放仪表放大器的**激光修调比值匹配 → 共模抑制地板**制造级锚点）。

## 核心命题（原文）

1. **减法器电阻比值匹配 = 共模抑制的制造实现方式（本文核心句，p.84）**：
   > "R52, R53, R54, and R55 are laser trimmed to ratio match within ±0.01%; this insures over 80dB attenuation of common mode signals and unity gain accuracy of ±0.02%."
   （±0.01% 比值匹配 ⇒ **80 dB 共模衰减地板**——失配 1×10⁻⁴ 与 80 dB（20·log₁₀(1/ε)=80 dB）严丝合缝的定量对应，是"匹配精度 ↔ 结构地板"最经典的制造级证据。）

2. **自动调零消除不了的误差类别（方法学锚点，p.84）**：
   > "Errors that cannot be eliminated by automatic zeroing and scale factor adjust, such as nonlinearity, noise and settling time, are reduced to low levels."
   （校准能消的与不能消的误差分类法——P1/D 系"门槛化"论证中"哪类误差可校、哪类只能压"的 1982 年先声；比值失配类误差属于"必须靠修调/结构"的类别。）

3. **拓扑：前置放大 + 经典三运放结构，差模增益由 RG 编程（p.84）**：
   > "This configuration might also be recognized as a classical three amplifier in-amp (A1, A2, A3) preceded by a preamp. … the unity gain subtractor (A3, and R52 to R54) amplifies the difference between the outputs of A1 and A2, Vo is just the differential portion of the input voltage times the programmed gain. Three pin-selectable RGs are provided for gains of 10, 100, and 1000."
   > "Figure 1 is a simplified representation of an alternative approach. It should be clear that feedback will keep the collector currents of Q1, Q2, Q3, and Q4 constant and, as a result, the input voltage is impressed across RG."

4. **CMRR 随增益档变化的实测（表 1，p.84）**：CMRR 列 "Gain of 1: >8OdB；Gain of 1000: >120dB"——同一组修调电阻，RTO 口径下 CMRR 随差模增益 G 抬升（≈80+20·log₁₀G），与电阻失配主导机理一致。

5. **与既有方案的对比基线（p.84）**：
   > "Previous monolithic in-amps reported in the literature have relied upon some form of wide range controlled current sources as feedback elements. These schemes have inherently large output errors. Referred to output (RTO) noise levels of 500-1000nV/[√Hz·G], drifts as high as 1mV/°C, and gain of 1 nonlinearities in the 0.05% to 0.1% range are all typical of current feedback in-amps."

## 关键数值（原文）

- 修调指标（p.84）：R52–R55 比值匹配 ±0.01%；由此 ">80dB" 共模衰减、单位增益精度 ±0.02%。
- 表 1（Fabricated device results，p.84；OCR 损耗以 [ ] 注）：
  - Offset Voltage：G=1 250 µV / G=1000 25 µV（原文 "250pV/25pV" 系 OCR，按量级判读为 µV，**待核**原刊）；
  - Offset Voltage Drift：G=1 "lO[@]V/°C"（判读 10 µV/℃，**待核**）/ G=1000 "0.zµV/℃"（**待核**）；
  - **CMRR：G=1 ">80 dB"、G=1000 ">120 dB"**（本表唯一两档均清晰可读的关键行）；
  - Nonlinearity of Gain：G=1 "<0.005%"、G=1000 "<0.01%"；
  - Bias Current："<±25 nA"；Settling Time to 0.01%：G=1 15 µs、G=1000 75 µs（原文 "15ps/75ps" 系 µ 之 OCR）；Bandwidth：G=1 1 MHz、G=1000 25 kHz；Supply Current 3.5 mA。
- 噪声（p.84，OCR 部分损耗）：输入对发射结散粒噪声理论值 "2.8nV/[√Hz]"；RG=4 kΩ 约翰逊噪声 "en = 8nV/[√Hz]"；RTI 噪声 G=10 "<10nV/[√Hz]"、G=1000 "7nV/[√Hz]"；输入噪声底实测 "4nV/[√Hz]"（不含可选输入保护器件），富余 "1.2nV/[√Hz]" 归因输入对基极电阻。
- 其他（p.84）：开环增益 G=1000 时 3×10⁸；GBP 25 MHz；G=1 非线性 ±0.0015% @ ±10 V 满摆；总芯片电容 75 pF；Early 电压 >1000 V 的电流源；输入保护至 36 V（BVDG）。
- 版图热对称（p.84 图 5 题注，p.85）："Al, A2, and A3 are interdigitated to achieve complete thermal symmetry."

## 对 P1/P2/P3 的对照

- **P1（消去条件 G_DC(s)=H_N−H_P≡0）**：高相关（历史锚点）。三运放减法器的共模消去正是"匹配条件成立 ⇒ 精确消去"的原型：理想 R52/R53=R54/R55 ⇒ 差分减法共模增益严格为零；本文给出制造实现（激光修调到 ±0.01%）与由此达到的**有限地板（>80 dB）**——即消去条件在工程上只以"失配精度"的倒数程度成立。P1 的"τ 匹配充要 vs 多级梯形不再充分"讨论可直接引此为"单级差分结构靠匹配、地板=失配精度"的史实锚点（含于 killRisk 条目所指"单级差分 RC 失配-CMRR 公式"谱系的器件实现端）。
- **P2（Kelvin 结构地板 ≈56 dB）**：高相关（对标数据）。本文 80 dB 地板来自**激光修调后** 0.01% 匹配；若修调退到 ≈0.16%（≈56 dB 对应失配量级）则地板即落到 56 dB 附近——为 P2"结构地板由结构+可获匹配工艺共同决定"提供同轴对标：结构（三运放减法）给定后地板随工艺匹配精度平移，56/80 dB 是同一坐标系的两个工艺点。引用时注明本文无 56 dB 字样，对标为推算口径（待核 P2 原文对 56 dB 的出处链）。
- **P3（平坦度约束衰减上界）**：低。无滤波器/平坦度内容；间接可用点：CMRR 地板即"衰减上界"思想在共模通道的体现。
- **方法学（D1–D10）**：中。①"可校（失调、增益）vs 不可校（失配、噪声、非线性、建立）"的误差二分法（命题 2 原文）是 D 系门槛划分的历史先例；②表 1 按增益档列误差（G=1 与 G=1000 双列）= 误差随工作点分档上报的表式模板。
- **killRisk 判断**：低风险、高价值。本文**不是** killRisk 条目（单级差分 RC 失配-CMRR 公式的出处是 TI 2015 博客），但它给出该公式所描述现象的最早单片实现锚点（AD524，1982）；引用时防止反向误归——80 dB/±0.01% 属 Wurcer & Counts，勿写成 TI 博客内容。

## 没读到的

- 表 1 失调漂移两格的精确数值（OCR 损耗，判读待核原刊 p.84）。
- 完整电路图 Figure 5 中的元件明细（图为扫描位图，R52–R55 具体阻值未在正文出现，**待核** AD524 数据手册对照）。
- 参考文献 [1]–[3]（Krabbe 1971、Brokaw & Timko 1975、Nelson 1980）原件未读。
