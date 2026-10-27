# 精读笔记 · Akbari 2017《Design and Analysis of an Ultra-Low-Power Second-Order Asynchronous Delta–Sigma Modulator》（Circuits, Systems, and Signal Processing）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> H3 轴定位：**无时钟异步 ΔΣ（ADSM）= 逃生门的极端形态**——连采样器都删掉（比较器连续时间工作，输出 PWM 脉宽流），原理上无"采样折叠"可言。本文（超低功耗二阶 ADSM，30 nW/0.25 V）的价值在于展示这条极端逃生门**自己的残余机制**：中心频率附近的冗余谐波会随输入幅度滑向基带、比较器延迟压低中心频率、OTA 有限增益使虚地残余电压振荡。对 P1 是外围佐证：每一种"绕开采样"的方案都带着自己的退化条件。

## 出处
- Akbari, Meysam; Hashemipour, Omid; Moradi, Farshad, "Design and Analysis of an Ultra-Low-Power Second-Order Asynchronous Delta–Sigma Modulator," *Circuits, Systems, and Signal Processing*, vol. 36, pp. 4919–4936, 2017. DOI: 10.1007/s00034-017-0658-7.
- 所读 PDF 为 Springer 在线版的作者手稿样式（页眉 "Circuits Syst Signal Process"，无印刷页码）；本篇引用页码 = **PDF 页 1–18**；与终版 pp.4919–4936 的逐页对应**待核**。
- 文件：`fulltext/H3-CT-ΣΔ/akbari2017esign.pdf`。Shahid Beheshti Univ. + Aarhus Univ.。

## 核心命题（原文）
1. **无时钟 = 量化噪声免疫的原理与代价**（p.2）：
   > "Compared to the conventional ADCs, ADSMs are quantization-noise free due to their clock-less configuration [11]. Nonetheless, redundancy harmonics around the center frequency must be moved to higher frequencies in order to achieve required effective number of bits (ENOB)."
   （删掉采样钟确实免了混叠折叠，但噪声/失真转移到自由振荡中心频率附近的"冗余谐波"上——新形态的残余。）

2. **残余谐波随输入幅度滑入基带（幅度条件）**（p.4，式 (1) 语境）：
   > "According to the analysis in [26], large distortions around the center frequency will influence through the baseband of the modulator and destroy its linearity for large input amplitude."
   （式 (1)：距基带最近的中心频率谐波位于 ωc(1−u²/2)，u 为归一化输入幅度——**输入越大，谐波越往基带里掉**；这是无采样逃生门的幅度依赖退化条件。）

3. **提高中心频率 = 提高输入带宽/线性度的资源交换**（p.6）：
   > "Therefore, the best way to increase the center frequency is to decrease the size of the capacitor in the second integrator, which is available in a second-order ADSM."
   （二阶结构把中心频率从依赖第一积分器（受线性度牵制）改为依赖第二积分器电容 C₂——用"阶数"换"中心频率余量"的资源交换逻辑。）

4. **比较器延迟 = 环路延迟残余条件**（p.7，式 (17) 语境）：
   > "Equation (17) shows that the center frequency of the modulator will decrease for higher delay of the comparator, which degenerates the input bandwidth and linearity of the modulator."
   （延迟 τ 直接进 Tc≈4(HC₂/I_F+τ)——延迟越大，中心频率越低，谐波离基带越近。）

5. **OTA 有限增益 → 虚地残余电压振荡 → 基带失真与噪声**（p.2 引言与 p.7 §2.2 两处）：
   > "This non-ideality behavior increases the oscillation of residual voltage at virtual ground nodes of an active-RC integrator, which leads to a larger distortion and noise in the baseband of the modulator."（p.2）
   > "According to the considerations in [14], finite DC gain increases oscillation of the residual voltage at the virtual ground nodes of the integrator, which results in larger distortion and noise."（p.7）
   （与 Manivannan 2018/2019 的"虚地节点"是同一个物理观察点：**虚地不'虚'，残余电压就是失真源**——不同机理（有限增益 vs 非线性×寄生），同一节点。）

6. **单端结构 → 偶次谐波出现（结构形态决定失真谱）**（p.14）：
   > "The even harmonics are appeared in the output power spectrums of both ADSMs because of single-ended architecture that can be controlled by VCM between the integrators and the comparator."
   （结构选择（单端/差分）直接决定失真谱形貌——与 P2"结构决定地板"的思路弱同构。）

7. **工艺角/温度下性能大幅退化**（p.15，表 3 语境）：
   > "The results are worse than the normal case (TT @ 27 °C) because of high sensitivity of the weak inversion region to the temperature and threshold voltage."

## 关键数值（原文）
- 总体（p.1 摘要）：TSMC 130 nm、中心频率 **1.73 kHz**、电源 **250 mV**、**SNDR 67.3 dB**、功耗 **30 nW**。
- 模块功耗：改进型 OTA **10 nW**、比较器 **6 nW**（p.10）。
- OTA 性能（p.10–11）：DC 增益 75 dB、GBW 2.68 kHz、PM 59°、SR 2.25 V/ms；输入参考噪声 **342 nV/√Hz @ 10 Hz**；负载/补偿/浮栅电容 15/5/1 pF。
- 比较器：迟滞 ±H≈**2.5 mV**（抗工艺角取值）、最坏延迟 **123 µs**（其中 13% 来自迟滞）（p.11）。
- 环路参数（p.12）：DAC 电流 I_F1=I_F2=**10 nA**；R₁=R₂=**12 MΩ**；C₁=**200 pF**、C₂=**40 pF**（C₂ 取 C₁ 的 1/5 以抬中心频率）；"matching of passive components is not critical for accuracy"→ 可外置。
- 一阶 vs 二阶对照（p.12–13、表 4 p.16）：中心频率 0.75→1.73 kHz；输入带宽 25.5→**70.2 Hz**；SNDR 61.5→67.3 dB；SFDR 62.2→**68.12 dB**（100 mVpp @10 Hz 输入）；二阶 SNDR 峰值点 64.3 dB @70.2 Hz（图 7）。
- 稳健性（表 2 p.12、表 3 p.15）：MC 均值 GBW 2.58 kHz/σ=0.13；**工艺角下 DR 67.31→52.8 dB（SS）、SNDR 67.3→54.4 dB；温度 −10/+90 ℃ 下 SNDR 55.5/57.9 dB**——退化 >10 dB。
- 结论量化（p.17）：二阶化带来 **2.6× 带宽、5.8 dB SNDR**；改进 OTA 带来 **9.9 dB SNR、5.8 dB DR**，仅多花 2 nW。

## 对 P1/P2/P3 的对照
- **P1（G_DC=H_N−H_P≡0 元件条件）**：相关度**低**。本文无平行路径对消结构；但其"残余"框架同型——中心频率谐波位置 ∝ (1−u²/2)（幅度条件）、中心频率 ∝ 1/(HC₂)·I_F 且被延迟 τ 拖低（延迟/元件条件）。可作 P1 相关工作段的一句带过例证：**删除采样器的极端逃生门同样存在幅度/延迟依赖的退化**，不构成反例。
- **P2（Kelvin 结构地板 ≈56dB）**：相关度**低**（仅第 6 条"单端→偶次谐波"的结构决定失真谱思想弱同构）。
- **P3（平坦度约束衰减上界）**：相关度**低-中**。"谐波距基带的间距由 ωc(1−u²/2) 决定、抬 ωc 需要功耗或电容/阶数筹码"是一个**带宽-资源-失真间距**的三方约束，叙事形状与 P3 的"平坦度资源→衰减上界"相似，但无衰减 dB 上界内容。
- **方法学（门槛化、D3）**：相关度**中**。表 2/表 3 的"MC 均值/σ + 四角 + 温度 + 电源 ±15%"全维度报告口径，以及"公平对比基准（一阶 ADSM 同工艺重设计）"的做法可借鉴；但本文是纯仿真（Cadence/130 nm 模型），无流片实测。
- **killRisk**：**无**。与 P1/P2/P3 主张无冲突；仅作 H3 轴谱系补全（无时钟分支）。

## 没读到的
- 终版页码对应（PDF 无印刷页码，与 pp.4919–4936 的映射待核）。
- **任何混叠/抗混叠的定量讨论**——全文未出现 alias rejection 数值（无时钟架构无 fs 倍频折叠问题；其"混叠等价物"是中心频率谐波，但本文未给谐波抑制的 dB 值，只给 SFDR）。
- 硅后实测（全部为晶体管级仿真结果）；FoM 对比表 4 中他引数据未溯源核验。
- 式 (2)–(17) 推导细节的独立复算（本笔记只核对了式 (1)/(17) 的物理解释与正文陈述一致性）。
