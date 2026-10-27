# 精读笔记 · Kidambi 2019《Noise transfer function design for delta-sigma modulators using the Gegenbauer polynomial》（Signal Processing）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> H3 轴定位：NTF 综合方法文献（ΣΔ 域的滤波器综合）。表面与抗混叠无关，但含一条**对 P3 直接可引的经典权衡陈述**：通带允许小纹波可比单调通带换来更高阻带衰减（Gegenbauer/Chebyshev 族 vs Butterworth 式）——这正是"平坦度约束 ↔ 衰减上界"在 NTF 设计域的镜像。另外它证明 Schreier 零点布设法在低 OSR 下**因分母多项式不再带内恒定而失优**——理想化假设失效的又一例。

## 出处
- Kidambi, Sunder (Cirrus Logic, Austin TX), "Noise transfer function design for delta-sigma modulators using the Gegenbauer polynomial," *Signal Processing* (Elsevier), vol. 159, pp. 49–52, 2019. DOI: 10.1016/j.sigpro.2019.01.023. Short communication。
- PDF 第 1–4 页 = 期刊页 **49–52**（页码直接印在页眉，引用页码即期刊页码）。文件：`fulltext/H3-CT-ΣΔ/kidambi2019oise.pdf`。

## 核心命题（原文）
1. **经典零点布设法（Schreier DST）的失效条件：低 OSR 下分母多项式侵入通带**（p.49 摘要）：
   > "The limitation of this method is that when the oversample ratio (OSR) of the DSM is low, the 3-dB cutoff frequency of the denominator polynomial of the NTF may approach the edge of the passband of the NTF. This causes the zeros to no longer be optimal."
   > "These zero locations are optimal only if the denominator polynomial is constant in the band of interest. In other words, it is assumed that the denominator of the NTF does not significantly affect the in-band noise power."（p.49）
   （"零点最优"依赖**分母带内恒定**的理想化假设——一旦 OSR 低、3dB 拐点逼近带边，假设破产。与 P1/P3 的共同叙事：教科书方法的 optimality 附带隐含前提。）

2. **纹波换衰减（对 P3 最直接可引的一句）**（p.49）：
   > "A small ripple in the passband provides a higher stopband attenuation than a passband that is monotonic."
   （同阶下，通带等纹波（Gegenbauer/Chebyshev 族）比单调（Butterworth 式）买到更高阻带衰减——**平坦度是被消耗的资源**：要求通带"平坦"（单调/最大平坦）就自动压低可达衰减。P3 的"平坦度约束衰减上界"在 NTF 综合域的成文先例。）

3. **NTF 设计 = 带稳定性约束的高通滤波器设计**（p.50）：
   > "||HNTF(z)||∞ = max|HNTF(ejΩ)| ≤ γ"（式 (5)），且 "A typical value of γ is 1.5 [1]."
   （可综合性/稳定性约束 = 带外增益上限 γ；设计即在"带内能量最小 + γ 约束 + 通带纹波 Ap"三方之间做受约束优化。）

4. **方法本体：Gegenbauer 特征函数 + 虚轴零点对 + 双线性变换**（p.50）：
   > "The stopband response of the lowpass filter can be improved by introducing a pair of imaginary-axis zeros at ±ωz in the transfer function [7]."
   （全部设计自由度 = (ε, Ap, Ωc)；带内能量 Ein（式 19）与稳定性约束 Eγ（式 20）组成复合目标 η = Ein + Eγ（式 21），Nelder-Mead 求解（p.51）。）

5. **实测增益：5 阶 ~5dB SQNR 改善，且纹波收益会饱和**（p.52）：
   > "For e.g., the SQNR obtained by a 5th-order NTF using the GEGEN method for Ap = 0.5 dB is 58.2 dB while that obtained by the DST method is 53.47 dB, an improvement of approximately 5 dB. It must be mentioned that increasing Ap beyond a certain level does not improve the SQNR."
   > "the stopband attenuation provided by the GEGEN method is higher than that provided by the DST method. Consequently the SQNR is improved."
   （**纹波超过某水平后 SQNR 不再改善**——"花平坦度买衰减"这条交易本身有饱和上界；与 P3"两阶理想 ≈76dB<80dB"的封顶逻辑同形。）

## 关键数值（原文）
- 表 1（OSR=24、γ=1.5、零频对 Ωb=π/OSR 归一）SQNR 对比（p.52）：
  - N=3：GEGEN 44.622/44.763/44.736 dB（Ap=0.125/0.25/0.5 dB）vs DST **42.419 dB**；
  - N=4：52.309/52.573/52.783 vs **49.078**；
  - N=5：57.749/58.025/**58.280** vs **53.472**（零点 0, ±0.5253, ±0.9218 @Ap=0.5dB；DST 为 0, ±0.5385, ±0.9062）；
  - N=6：61.624/61.872/62.109 vs **56.110**；
  - N=7：64.370/64.574/64.773 vs **57.313**。
- 改善幅度随阶数增大：N=3 约 +2.2 dB → N=7 约 **+7.5 dB**（由表 1 差值算得）。
- SQNR 定义（式 23，p.52）：−20log₁₀[∫₀^Ωb |HNTF(ejΩ)|dΩ / Ωb]；γ 典型 1.5（p.50）；Gegenbauer 递推式 (8) 与高通平方幅频式 (10)–(11)：ε=1/√(10^(0.1As)−1)。
- Fig. 2：5 阶 NTF 幅频（OSR=24, γ=1.5，GEGEN vs DST）；Fig. 3：SQNR 随 OSR **20–64** 扫描，GEGEN 全程显著更高（p.51–52；曲线逐点值在图中，文本未列）。

## 对 P1/P2/P3 的对照
- **P1（G_DC=H_N−H_P≡0 元件条件）**：相关度**无**。纯单环 NTF 综合，无对消结构。
- **P2（Kelvin 结构地板 ≈56dB）**：相关度**无**。
- **P3（平坦度约束衰减上界 ≈76dB<80dB）**：相关度**中-高**。两个可直接引用点：① p.49 "small ripple … higher stopband attenuation than … monotonic"——**平坦度与衰减的交换是滤波器综合的教科书事实**，P3 把该交换解释为"约束平坦即封顶衰减"有了 NTF 域成文出处；② p.52 "increasing Ap beyond a certain level does not improve the SQNR"——**花资源买性能的交易存在饱和**，与 P3 的 <80dB 不可达叙事同构。注意：本文是 DT/NTF 域、单位是 SQNR 不是混叠抑制 dB，引用时须注明域不同、仅取其权衡原则。
- **方法学（门槛化、D3）**：相关度**中低**。复合目标 η=Ein+Eγ + Nelder-Mead 的**受约束优化综合**框架，以及"表 1 全阶扫描 + 图 3 全 OSR 扫描"的对比呈现方式可借鉴；但无统计/工艺角/实测层级的门槛概念。
- **killRisk**：**低**。唯一反向解读风险：对手可能引它说"放开纹波就能涨衰减，所以平坦度约束不是硬约束"——回应：这正是 P3 的前提（场景要求平坦）而非反驳；且 Kidambi 自己证明纹波收益饱和（p.52），交换有尽头。

## 没读到的
- Fig. 2 幅频曲线与 Fig. 3 SQNR-OSR 曲线的逐点数值（文本仅给结论性描述）。
- 与 Butterworth/Legendre/逆切比雪夫等其他族的横向数值对比（本文只比 Schreier DST [5]）。
- 电路级可实现性（系数 a(n)、b(n) 的灵敏度/量化效应未讨论——短文篇幅所限）。
- Schreier DST 原始文献 [5]（1993）零点布设推导本身——本文只作方法对比的基线引用。
