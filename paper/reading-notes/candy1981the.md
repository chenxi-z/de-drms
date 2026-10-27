# 精读笔记 · Candy 1981《The Structure of Quantization Noise from Sigma-Delta Modulation》（IEEE Trans. Communications, COM-29(9), pp.1316–1323）

> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> 页码口径：**期刊印刷页码**（PDF 第 1–8 页 = 印刷 p.1316–1323，逐页对应已核对）。
> 文件：`fulltext/H2-差分CMRR/candy1981the.pdf`；bib key `candy1981the`（bib 注记归 H3·时间线，ΣΔ 量化噪声结构正典）。

## 出处

- James C. Candy, O'Connell J. Benjamin（Bell Laboratories, Holmdel, NJ）, "The Structure of Quantization Noise from Sigma-Delta Modulation," *IEEE Trans. Communications*, vol. COM-29, no. 9, pp. 1316–1323, Sep. 1981. DOI 10.1109/tcom.1981.1095151.
- 主题：高过采样 ΣΔ 调制器在**直流/缓变输入**下量化噪声的结构——谱线位置（输入幅度的有理数分点）、每峰功率、净基带噪声与 SNR 的代数式，并与实物面包板测量对照。

## 核心命题（原文）

1. **过采样 ΣΔ 的调制噪声与输入幅度强相关，可用简单代数式描述**（p.1316, Abstract）：
   > "When the sampling rate of a sigma-delta modulator far exceeds the frequencies of the input signal, its modulation noise is highly correlated with the amplitude of the input. We derive simple algebraic expressions for this noise and its spectrum in terms of the input amplitude. The results agree with measurements taken on a breadboard circuit."
   （解释：ΣΔ 噪声白化假设在安静输入下失效的定量正典——为"前端噪声结构依赖工作点"提供源头出处。）

2. **静态输入下噪声高度有色、呈离散谱线，失真临界地取决于电路条件**（p.1316, §I）：
   > "When the input is steady the noise is highly colored, its spectrum appears as sets of distinct lines and the signal distortion is critically dependent on circuit conditions that determine whether or not strong lines lie in baseband."
   （解释：ΣΔ 本征谱线结构——P1 论文讨论调制器频率处差模/共模残余（D1/D3 门槛）时的上游事实来源：即使前端正交理想，调制器自身也产生落带谱线。）

3. **噪声峰成对出现在动态范围小整数比分点旁，过采样比越大越突出**（p.1316, §II）：
   > "These graphs show that noise is largest when the modulator is biased near the ends of its range and next largest near the center. Indeed, most of the circuit's noise occurs in peaks adjacent to bias values that divide the dynamic range in small whole number ratios. Peaks of noise occur in pairs and are most prominent when the sampling rate is large compared to baseband."
   （解释：对准静态电阻测量这类近直流应用，偏置点若落在 m/n 分点附近会遭遇噪声峰——是"门槛化方法学"为 ΣΔ 前端定差模/噪声底线时必须引用的结构性事实。）

4. **应把调制器偏置到安静态以获得低静态噪声**（p.1316, §II）：
   > "For applications in communications it is advantageous to have low noise in the quiescent state; therefore, modulators should be biased to a quiet state away from the large peaks of noise."
   （解释：工作点选择作为噪声管理手段——对 DE-DRMS 式准直流测量的直接工程含义。）

5. **环增益在 0.7–1.3 内变化对噪声结构影响微弱**（p.1322, §VII）：
   > "Measurements on a real circuit indicate that changes of loop gain near unity have a weak effect on the noise. Indeed, modulators with gains in the range 0.7 – 1.3 all have similar noise structures."
   （解释：ΣΔ 对环增益失配（±30%）的一阶钝感——与 P1 关心的"失配敏感性"形成对照：调制器内部增益失配被反馈稀释，而无源差分滤波器的元件失配直接进入 G_DC。可用于 P1 论证"失配后果因结构而异"。）

6. **多电平量化下同一分析适用条件 = 环净增益为 1 且步长归一**（p.1322, §VII）：
   > "The analysis presented applies to such multilevel quantization provided that the net gain in the feedback loop [8] is unity and that signal amplitudes are scaled to make the step size unity."
   （解释：分析成立的精确前提——"何值/何条件下成立"式表述的范例，但对象是量化噪声结构非滤波消去。）

## 关键数值（原文）

- p.1316–1317（Fig. 2 图注）：实测 rms 基带噪声 vs 直流输入电平 X（0<X<1，正常交流工作偏置 X=0.5）；采样率 64/256/512 kHz；基带 3.5 kHz。p.1317（Fig. 3 图注）：1.02 kHz 正弦、256 kHz 采样，偏置中心与 11/20 两态的 SNR 对比。
- p.1319（式(19)–(21)）：噪声峰半宽 u_max = f0·T/n（f0 基带、T 采样周期、x = m/n 分点）。
- p.1320：实际基带滤波器（非理想截止）使峰的尖角变圆（Fig. 8b vs 8a）；由图 10 斜率反推 f0 = 3.0 kHz，与滤波器拐角一致。
- p.1321（式(28)）：单个噪声峰总功率 = 0.8·u_max³；"Eighty-three percent of this noise is contributed by the primary component for which i_l = 1 (i.e., l = n)."
- p.1321（Example 1 讨论）：A = u_max 时 rms 信噪幅度比 = √(π/8)，20·log10(√(π/8)) = −4.06 dB，与采样率无关（2026-10-27 回看印刷 p.1321 核正；旧记 `6/8` 是 OCR 错误，不是原文公式）。
- p.1322（Example 2）：256 kHz 采样、3 kHz 基带、−9 dB（A≈1/6）正弦：u_max = 13/256，算得 SNR = 35.8 dB，实测 37 dB。
- p.1322（Appendix）：白噪声模型下噪声峰总和 ≈ N0²；"About [OCR损，约为 2/3] of this total is contained in the two peaks at the ends of the range. The two peaks at the center have about 0.1 of the total."
- **无 CMRR/共模数据，无滤波器消去条件**。

## 对 P1/P2/P3 的对照

- **P1（消去条件）**：相关度**低**。全文无差分网络、无传递函数消去问题；唯"环增益 0.7–1.3 钝感"（p.1322）可反衬无源差分滤波器失配直接显形的敏感性差异。
- **P2（Kelvin 地板 ≈56 dB）**：**无**。
- **P3（平坦度约束衰减上界）**：**无**。非理想低通滤波器仅作为"峰形圆化"的实验事实出现（p.1320），无衰减-平坦度定量界。
- **方法学（D1–D8 门槛化）**：相关度**中**。ΣΔ 量化噪声谱线结构（m/n 分点成对峰、83% 集中于主分量、峰功率 0.8·u_max³、SNR 35.8 dB vs 实测 37 dB）是设定调制器侧噪声/差模底线（如 D1@fMOD）时上游结构性依据；对准直流测量还提示偏置点须避开分点峰。
- **killRisk：无**。与"多级无源网络全频段精确消去条件"零接触；属 ΣΔ 噪声结构地基。

## 没读到的

- 差分/共模通道、CMRR、无源滤波器消去条件——完全未涉及。
- 式 (5)–(9)、(24)–(26)、(33)、Appendix 中 N(f) 的逐字符细节：OCR 对上下标/系数重排严重（如 "P_l(u) = 2/π²·l²u²" 无法逐字核实），引用时以"文字判语+结果编号"为准；逐字符引用须回看扫描图（标 [OCR损]）。
- Fig. 2/3/8/10 曲线内部读数（描点图，OCR 不可提取，仅图注可引）。
- "About # of this total"（p.1322）中的分数 OCR 损毁——疑为 2/3，标待核。
