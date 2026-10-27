# 精读笔记 · Gray, Chou & Wong 1989《Quantization Noise in Single-Loop Sigma-Delta Modulation with Sinusoidal Inputs》（IEEE Trans. Communications 37(9):956–968）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。

## 出处
- Gray, R.M.; Chou, W.; Wong, P.W., "Quantization noise in single-loop sigma-delta modulation with sinusoidal inputs," *IEEE Transactions on Communications*, vol. 37, no. 9, pp. 956–968, Sep. 1989. DOI: 10.1109/26.35376。
- PDF：`fulltext/H2-差分CMRR/gray1989quantiz.pdf`（13 页）。bibkey：`gray1989quantiz`。
- **归档勘误**：bib（literature.bib 行 1470 附近）把本文标为 **[H3·时间线]**（Σ-Δ 时间线），并非 H2；fulltext 却放在 H2 文件夹——本批按 H2 读了，结论是**与差分滤波器/CMRR 零交集**，建议谱系表挂回 H3 时间线。
- 主题：单环 Σ-Δ 调制器（离散积分器 + 1-bit 量化器）在正弦输入下二进制量化噪声的**精确**非线性差分方程解、样本矩与谱。

## 核心命题（原文）
1. **Σ-Δ 白噪声建模假设被根本违反**（p.956, §I）：
   > "It was shown in [8] that the conditions required for the use of the white noise assumptions are violated in a fundamental way in C A modulators."
   （[8]=Gray 1987；Σ-Δ 量化噪声不是信号独立白噪声。）
2. **量化噪声是输入与初态的确定性函数，原则上可精确解出**（p.958, §II）：
   > "In most treatments of EA modulation the binary quantizer error sequence E,, is assumed to be independent of the signal, uniformly distributed, and white. In fact, the noise is a deterministic function of the input signal and system initial state and in principle it can be derived exactly from the input sequence."
   （本文路线：不建模噪声、直接解系统——与"增量四"方法学"实测优先于假设"的哲学同构。）
3. **系统可分解为"仿射运算（带偏置积分）+ 无记忆非线性（取小数部分）"**（p.956, Abstract；p.959, §III）：
   > "It is shown that the system can be represented as an affine operation (discrete-time integration of a biased input) followed by a memoryless nonlinearity."（Abstract, p.956）
   > "The sequence y, is formed by a combination of a simple affine operation with memory followed by a memoryless nonlinearity."（p.959, Property 3 的 Comment）
4. **大过采样比极限下边缘矩表现如均匀分布，但谱既非白也非常连续**（p.956, Abstract）：
   > "In the limit of large oversampling ratios, the marginal moments behave as if the quantization noise had a uniform distribution. The spectrum is neither white nor continuous, however, even in the limit of large oversampling ratios."
5. **正弦输入下谱纯离散、含全部谐波及其搬移**（p.963, §V）：
   > "the spectrum of y , is purely discrete and has amplitude s/at the frequency Al. This spectrum is extremely nonwhite since it is not continuous and not flat. The output frequencies depend on the input frequency w and comprise all harmonics of the input frequency w as one might expect with a nonlinear device."
   （谱线由 Bessel 函数加权和给出，式 5.28；这就是 Σ-Δ ADC 噪声结构第一性来源。）
6. **一阶矩恰为均匀分布值**（p.962）：
   > "holds. Observe also that since Bessel ... exactly that M { y n } = 1/2!"（p.962，含 OCR 噪声；归一化误差序列样本均值 = 1/2、方差 ≈ 1/12）

## 关键数值（原文）
- 仿真参数：1024 样本、全幅正弦、频率在 [0,1] 均匀随机取（Fig. 2, p.957）；样本均值 ~1e-4~2.5e-2、方差 0.077–0.095（≈1/12=0.0833，Fig. 2 图注, p.957）。
- 自相关/谱：式 (5.22)(5.26)–(5.28)（p.963）以 J_m(2πa·i) Bessel 权重给出；谱幅度对输入频率极敏感："Note the sensitivity of amplitude to frequency."（p.964）
- 有限样本：FFT 谱与 Bohr-Fourier 谱都只是近似，1024 样本下偏差可观（p.964）。

## 对 P1/P2/P3 的对照
- **P1（消去条件）**：相关度 **无**。全文无共模/差模、无滤波器匹配、无 CMRR（关键词检索 0 命中）。
- **P2（Kelvin 结构地板）**：相关度 **无**。
- **P3（平坦度约束下衰减可达上界）**：相关度 **无**（唯一形似处："spectrum is not flat" 是噪声谱平坦性，不是滤波器通带平坦度-阻带衰减权衡）。
- **方法学（增量四 D1–D10）**：相关度 **无-低**。方法论气质相近（对强非线性系统做精确解析而非线性化假设、以时间平均逼近矩），但对象与增量实验无关。
- **killRisk 判断**：**无威胁**。Σ-Δ 时间线经典文献，不触及 P1 空缺主张。价值仅在仪器背景：DE-DRMS 的 ADS131A02 是 Σ-Δ ADC，若 P1 论文要谈 ADC 噪声模型可引本文作为"白噪声假设不成立的原始证据"。

## 没读到的
- 与 H2 轴相关的任何内容（共模、差分、平衡、滤波器失配）——本文在 H2 文件夹属归档错位。
- 多环/多级 Σ-Δ 仅在参考文献层面出现（[27][28] 两级/多级 Σ-Δ），正文未展开。
- 附录的极限交换证明（Bochner/Bohr 几乎周期函数论）未细读——与本批判断无关。
- 增量型 ADC（incremental Σ-Δ）未被讨论——"增量四"方法学需要的增量 ADC 文献须另找。
