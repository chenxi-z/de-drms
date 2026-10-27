# 精读笔记 · Lee 2020《Low Power CMOS-Based Hall Sensor with Simple Structure Using Double-Sampling Delta-Sigma ADC》（Sensors 20(18):5285）

> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> 读法：pdftotext -raw 逐页取**正式发表层**（本 PDF 内嵌 "Sensors 2020, 20, x FOR PEER REVIEW" 预印本水印层，同一内容重复 2–3 遍；引用均自正式层 "Sensors 2020, 20, 5285"）；页码 = 期刊页 "X of 13"。
> 定位：H5 域——**传感器（霍尔器件）不经任何放大/滤波、直连双采样 SC ΔΣ ADC 输入**的极简结构；「直接连接的代价」与「双采样换建立时间」两段是 H5 素材。

## 出处

- Ju Yong Lee, Younggyun Oh, Sein Oh, Hyungil Chae（建国大学 / 国民大学，首尔）, "Low Power CMOS-Based Hall Sensor with Simple Structure Using Double-Sampling Delta-Sigma ADC," *Sensors*, 2020, 20(18), 5285. DOI: 10.3390/s20185285. Received 2020-08-03 / Accepted 2020-09-11（Letter 类文章）。
- 本地全文：`fulltext/H5-kickback/lee2020hall.pdf`（13 页，含预印本水印层）。

## 核心命题（原文）

1. **极简主张：整个霍尔传感系统 = 霍尔器件 + 一个高分辨率 ΔΣ ADC，中间什么都不放**（p.1, p.4）："we propose a simple Hall sensor architecture composed of only a Hall device and an ADC avoiding the use of many complicated signal processing blocks such as an amplifier and a filter."（p.4）摘要（p.1）："The tiny magnetic signal from Hall device could be detected by a high-resolution delta-sigma ADC in presence of offset and flickering noise."——**输入结构 = 传感器直接被 SC 采样开关采样，无缓冲、无 IA**。
2. **直接连接的具体接线（H5 核心语境）**（p.5–6）："the sampling switches (SSPA, SSPB) at the ADC input are turned on and off accordingly. Then, the sampled input signal is integrated by common integration switches (SINT)."（p.5）；"The two sets of outputs of the Hall device only need to be each connected to the sampling switches (SSPA, SSPB), and no additional circuitry is necessary to isolate the offset and noise."（p.6）——霍尔器件输出对直接接采样开关；**直接连接的代价**："The detectable range is reduced by a small bit due to the direct connection of the Hall device and the ADC, but accurate measurement is possible with a minimized hardware not using any complicated calibration technique."（p.11）
3. **双采样 = 用采样相数换建立时间/功耗（D5 域直接素材）**（p.5）："In a double sampling system, the input is sampled at every phase of the sampling clock, and the sampling frequency becomes doubled compared to that with conventional sampling. In other words, the sampling clock speed could be halved for a given signal bandwidth… Speed of a discrete-time delta-sigma ADC is mostly limited by the settling time of an integrator that dominates the whole power consumption, and effectively doubled settling time of integrators is allowed in the double sampling scheme."（**DT ΔΣ 的速度瓶颈 = 积分器建立时间（功耗大头）；双采样让有效建立时间翻倍**——即同一建立预算下时钟减半）
4. **双采样 T/H 与自旋电流的合流**（p.5–6）："The ADC includes two sets of track-and-hold (T/H) circuits, and in Phase φ1, the Hall voltage is sampled on CSA while the previously sampled signal on CSB is integrated by the first integrator. In the next phase (Phase φ2), CSB now samples the Hall voltage, and at the same time, the signal on CSA gets integrated. This parallel sampling-integration process by the two T/H circuits is repeated, and the first integrator output is passed to the next integrator every half clock phase (TS/2)."（p.6）
5. **输入开关不用自举（线性化取舍）**（p.9）："A bootstrapping switch is used at the front end in conventional ADCs, however the output voltage of a Hall device is mostly tiny and the offset is also further reduced by a careful layout design [27]. Therefore, a transmission gate is used for the input switch instead of a bootstrapping one for simplicity without affecting linearity."（霍尔信号小 → 传输门即可，不必自举开关）
6. **惠斯登桥失配 → 失调，自旋电流对消（P1 域同族问题）**（p.4）："If there is any asymmetry in a Hall device caused by non-idealities, the four-resistor model will have different resistances and it can be modeled with a small resistance (∆R) as in Figure 5. This difference generates offset voltage at the output, but it can be cancelled out by switching the current direction. The offset voltage alternates its polarity depending on the current direction… while VHALL remains the same."（**四电阻桥失配 ΔR 产生直流失调；解法不是修匹配，而是周期性反转激励方向把失调搬到高频**——与 P1「失配致 G_DC≠0」同族问题、不同对消机制）
7. **本域噪声折叠的边界条件（一句话，无展开）**（p.5）："This configuration is advantageous to achieve high SNR as long as the oversampling ratio is high enough to prevent noise folding problem."

## 关键数值（原文）

- ADC（p.7, p.9）：3 阶 CIFF、1-bit 量化；NTF = (1−z⁻¹)³ / (1 − 49/20 z⁻¹ + 163/80 z⁻² − 177/320 z⁻³)，极点 (0.5822, 0.934±j0.2792)；"The simulation shows an SNDR of 92 dB when the oversampling ratio is 128"（p.7）；"The sampling frequency is 2 MHz, and the power consumption is 4.5 mW."（p.9，独立 ADC 仿真）；NTF 斜率 60 dB/decade（p.10）
- 放大器（p.8–9）：反相器型伪差分（两个互补源耦对）；增益式 (2)：(gmn1,2+gmp1,2)(ron1,2//rop1,2)；"The input devices have length of >10 µm to achieve DC gain over 60 dB"；输入等效噪声 "from 100 Hz to 7.81 KHz is simulated to be 5.24 µVrms, which corresponds to 0.508 µT in our system"；"noise from the amplifier is low enough not to affect the overall system resolution, and the thermal noise from the Hall device becomes the main noise source"
- 求和比较器（p.9）："A multi-input comparator in Figure 13 not only performs the single-bit quantization, but also replaces a summing amplifier… The gain of each integrator is set to 1/4… to keep the summing factors of the three paths to unity. Therefore, the comparator input devices are sized exactly the same, and the mismatch effect can be minimized."（**等尺寸消失配的又一结构手法**）
- 整机实测（p.10–11；Table 1 p.11–12）：0.18 µm CMOS、2.2 V；有源区 1400 µm × 500 µm = 0.7 mm²；总功耗 4.9 mW（ADC+霍尔器件）；灵敏度 110 µV/mT；线性 >99% 的量程 ±150 mT（>200 mT 饱和）；失调 16 µT；对标 [28]（0.5 µm, 21 mW, ±10.8 mT, 3.65 µT）与 [29]（0.8 µm, 20 mW, ±175 mT, 0.48 mT）
- 面积构成（p.10）："Most of the area is occupied by the switched capacitors that are designed for high resolution."

## 对 P1/P2/P3 的对照

- **P1（失配消去条件，G_DC≡0）——相关性：中低（同族问题、域外机制）**。p.4 的四电阻桥 ΔR 失配→失调是「**无源失配产生直流误差**」的标准模型，与 P1 的「RC 差分网络失配→G_DC」同族；但其对消机制是**调制搬运**（自旋电流把失调搬出带外），不是 P1 式「元件条件下的结构性消去」。引用价值：证明「失配→DC 误差」在传感域普遍存在且存在**非匹配路线**的对消先例（激励极性反转）；P1 若给出的是"匹配条件下的消去"，两者互补不冲突。killRisk：无。
- **P2（Kelvin 地板）——相关性：无**。无引线/两线四线结构。killRisk：无。
- **P3（平坦度约束衰减上界）——相关性：无/极低**。AAF 未讨论（只有 p.5 一句「OSR 足够高避免噪声折叠」；传统链路的 LPF 在本方案中被整体省掉，p.1 Figure 1 vs Figure 2）。killRisk：无。
- **方法学（D1–D10，H5 域）——相关性：中**：
  - **输入结构**：传感器直连 SC 采样（无缓冲）——**H5 轴「输入结构」分类的第 4 型：阻性源（霍尔桥 ≈ kΩ 级电阻网络）直连开关电容**；其代价被明确承认（量程略缩，p.11），但**无踢回幅度/建立误差定量**；全文无 "kickback" 字样；
  - **D5（建立）**：双采样把积分器有效建立时间翻倍（p.5）是「建立预算 ↔ 采样方案」的直接权衡素材；
  - **D9（kickback 回稳）**：无显式内容（未讨论采样开关电荷注入对霍尔桥的扰动）。
- killRisk 总判：**无**。

## 没读到的

- **采样电容 CSA/CSB 数值未给**（Fig.7 图内标注，文本层取不到）；kT/C 噪声预算未讨论（分辨率核算只给了放大器噪声 5.24 µVrms 与「霍尔器件热噪声为主」的结论，p.9）。
- **直接连接为何缩量程**（p.11 "detectable range is reduced by a small bit due to the direct connection"）未解释机理（估计与霍尔器件输出阻抗/负载效应有关，原文无分析——**待核**）。
- 实测 SNDR/SNR 未给出（只有仿真 92 dB；实测仅给灵敏度、线性、量程、失调）。
- 霍尔器件灵敏度、偏置电流/电压数值在正文未见（HHD 版图 p.7 只有结构）；分辨率「>15-bit」为设计目标表述（p.7），实测折算位数的口径未给。
- 参考文献 [18]（double sampling scheme 出处）、[27]（layout offset reduction）、[28][29]（对标两篇霍尔传感系统）未读。
- 预印本水印层与正式层个别措辞不同（如 φ1A/φ1B vs φ1A, φ1B 记法），引用以正式层为准；式(1) NTF 分式在文本层为竖排分号拼接，已按分母多项式系数核对无歧义。
