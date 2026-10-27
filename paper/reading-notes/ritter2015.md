# 精读笔记 · Ritter 2015《Anti-Aliasing Filter Improvement in Continuous-Time Feedback Sigma-Delta Modulators》（IEEE ISCAS 2015）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> H3 轴定位：**P0 级**。Ortmanns 组（与 Keller 2007 同一脉）首次给出 CT 反馈补偿型 ΣΔ **隐式 AAF 的阶数×OSR 结构性上限**，并提出"STF 加陷波"的逃逸法。对 P1 最有价值的一点：陷波深度靠**双积分器与旁路的平行路径对消**实现，其退化条件（增益误差→陷波频移、附加极点→"incomplete cancellation"）与 P1 的 G_DC=H_N−H_P 残余是**同一数学结构**。

## 出处
- Ritter, Rudolf; Lorenz, Matthias; Ortmanns, Maurits, "Anti-Aliasing Filter Improvement in Continuous-Time Feedback Sigma-Delta Modulators," *2015 IEEE International Symposium on Circuits and Systems (ISCAS)*, 2015. DOI: 10.1109/iscas.2015.7168636. 印刷页 325–328（bib 无页码，可补）。
- 文件：`fulltext/H3-CT-ΣΔ/ritter2015.pdf`；4 页会议文，本篇引用页码 = 会议印刷页码（PDF 第 1–4 页 = p.325–328）。

## 核心命题（原文）
1. **CTFB ΣΔ 的隐式 AAF 有阶数×OSR 结构性上限（该组首次表述）**（p.325 摘要+引言）：
   > "The continuous-time feedback compensated (CTFB) Σ∆-modulator is a good choice for strong alias rejection, but the suppression is fundamentally limited by the modulator's order and OSR, which is described for the first time in this paper."
   > "If a strong alias rejection is required, commonly used continuous-time feedback compensated sigma-delta modulators would need some pre-filtering or a large oversampling ratio."
   （「逃生门」的第一性限制：抑制量 = f(阶数, OSR)，不随调参改善——强抑制需求下 CT-ΣΔ 自己也得回头加前置滤波。）

2. **AAF 的机理定义：fs 倍频附近的折叠无法数字去除**（p.325）：
   > "Signals in the range around multiples of the sampling frequency are aliased into the band of interest and they cannot be removed digitally. For this reason the suppression in this band has to be very strong, which is also called the anti aliasing filter (AAF)."

3. **20dB/dec/阶 的量化缩放规律**（p.326）：
   > "Additionally to the suppression of the NTF, a 20dB suppression per frequency decade and modulator order in a CTFB-Σ∆-modulator is achieved, due to the series connection of integrators represented in H1(s)."
   （隐式 AAF = NTF 带内抑制 × 串联积分器 20dB/dec/阶；与 Keller 2007 的"阶数封顶"结论互补，这里给出显式斜率。）

4. **AAF 与系数选择无关——极点移高时两效应恰好对消**（p.326）：
   > "This implies that the AAF quality is independent of the coefficient choice."
   > "if one pole of the Σ∆-modulator is shifted to 10 times higher frequencies, the analog filtering of H1(s) becomes 20dB worse. In contrast, the NTF in-band is improved by 20dB, which leads to a cancellation of these effects for the AAF."
   （结论：想靠挪极点/调系数救 AAF 是死路——改善恰好被抵消。）

5. **低阶（一/二阶）CTFB 的 AAF 不够用**（p.326）：
   > "It can be observed that the AAF for 3rd and 4th order is already very strong and that in many cases an additional pre-filtering stage can be avoided for large OSRs. But for first and second order CTFB Σ∆-modulators the AAF is not that powerful."
   （低阶逃生门天然弱——对 P1 场景（低功耗、低阶、无大 OSR）是直接约束。）

6. **陷波法 = 双积分器与旁路的平行路径对消**（p.327）：
   > "The feed-in or feed-forward path has to bypass two integrators. The integrators have a 40dB decreasing amplitude per frequency decade and a phase shift of 180°, while the bypass has a constant amplitude over the frequency and no phase shift. If these signals are added, a cancellation at a certain frequency occurs, and the 40dB drop per frequency decade gets lost at higher frequencies."
   > "To improve the AAF, this notch has to be placed at fs, because there is the alias band, which is typically most critical."
   （STF 陷波不是滤波器深度的自然延伸，而是**两条平行传函的零点对消**——这正是 P1 消去条件的 CT-ΣΔ 版。）

7. **残余条件 ①：增益误差 → 陷波频移（灵敏度 √ε）**（p.327）：
   > "One non-ideality is a gain error between the double integrator and the bypass, which can result from device mismatch or integrator gain error. This leads to a shift in the notch frequency, which is not very critical, because the frequency error is only proportional to the square root of the gain error."

8. **残余条件 ②：积分器附加极点 → 不完全对消、陷波退化**（p.327，**对 P1 最关键的一句**）：
   > "In a real Σ∆-modulator the integrators have additional poles [5], which, e.g., result from a finite unity gain frequency of the amplifier in an active RC implementation. Thereby the phase of the double integrator is shifted away from 180°. This non-ideality has to be regarded, as it reduces the quality of the notch, arising from an incomplete cancellation."
   （理想 180° 相位对消在真实放大器有限 GBW 下失配——**对消深度受元件非理想性封顶**，与 P1 的 G_DC 残余完全同构。）

9. **结论：上限不可调参绕过，只能加 OSR 或加陷波**（p.328）：
   > "A limitation of the anti-aliasing filter of feedback compensated continuous-time Σ∆-modulators is pointed out. It has been shown, that it cannot be improved by adjusting the modulators coefficients, but only by increasing the OSR."

## 关键数值（原文）
- 陷波深度改善（理想）：二阶 modulator、OSR=16、4bit 量化器下 **AAF ideally improved by 24dB**（p.328）。
- 蒙特卡洛稳健性：**50000 次**运行；系数标准差 2%（引用自动修调后水平 [8]）、GBW 与补偿极点标准差 10%；改善均值 **−19.3dB**（即改善 19.3dB）、标准差 3.3dB；**99.8% 的结果改善 >10dB，无一差于原架构**（p.328）。
- 最坏情形选取：MC 中最差改善 **12dB**；瞬态仿真：带内信号 + 下混叠带边沿信号均 −3dBFS，原始 SNDR=67.9dB → 改进 72.9dB；混叠分量 **−69.5dB → −81.6dB**（p.328，改善 12dB）。
- 例系数：c1=c2=1, b1=1.25, a1=−1.23, a2=−1.8, 谐振器 e21=−0.016；两积分器单位增益频率 1×fs 与 2×fs（fs 归一 1Hz）；b3 为低通、DC 增益 0.026、拐角 fx=1.2Hz（p.328）。
- Fig. 3（AAF vs OSR，1–4 阶、含/不含谐振器）：纵轴约 −50 至 −200dB、横轴 OSR 6–60——具体曲线数值在图中，文本未列（**待核**）。

## 对 P1/P2/P3 的对照
- **P1（G_DC=H_N−H_P≡0 元件条件）**：相关度**高**。本文陷波 = 双积分器路径 H_N 与旁路 H_P 的平行对消；其残余条件两条（增益误差→√ε 频移；附加极点→相位偏离 180°→"incomplete cancellation"削减陷波深度）就是 P1 消去条件的**同构实例与文献锚点**。P1 写作时可直接引 p.327 作为"对消型陷波的深度受元件条件限制"的已发表证据。
- **P2（Kelvin 结构地板 ≈56dB）**：相关度**无**。无 Kelvin/结构地板内容。
- **P3（平坦度约束衰减上界 ≈76dB<80dB）**：相关度**高**。"suppression is fundamentally limited by the modulator's order and OSR"+"cannot be improved by adjusting the coefficients, but only by increasing the OSR" = **有限资源下衰减上界的又一实例**（此处资源=阶数×OSR，P3 处资源=无源两阶平坦度）；且低阶（一/二阶）AAF "not that powerful" 与 P3 "两阶理想 ≈76dB<80dB" 数量级叙事互证。
- **方法学（门槛化、D3@16.384MHz≥100dB）**：相关度**中**。MC（50000 runs、2%/10% σ、99.8% 分位 >10dB、"无一更差"）是**统计化验收门槛**的干净范例，可移植为 P1 论文对任何对消型方案的稳健性报告口径。
- **killRisk**：**低**。本文不否定"对消受限"论点，反而是其证据源；需注意的反向引用角度：若对手以"陷波法 24dB 改善 + MC 稳健"论证逃生门可补强到任意深，回应点 = 陷波只加在 fs 单点（带宽内混叠带其余频率仍受阶数×OSR 上限约束，Fig. 7 深度仅 ~−120dB 且依赖相位补偿 RxCx），且深度本身就是不完全对消的函数（第 8 条引文）。

## 没读到的
- Fig. 3 各阶 AAF-OSR 曲线与 Fig. 7/9 图中具体 dB 数值（仅能从图轴估计，未逐一读数）。
- Fig. 6 电容输入 Cx 实现的具体元件取值（正文只给 fx=1/(2πRxCx) 与 b3 参数）。
- 引文 [2] Philips 2004"increased immunity to interferers"（环路内附加滤波器路线）的细节——本文仅一句带过，若 P1 需要该路线的退化分析须另行精读。
