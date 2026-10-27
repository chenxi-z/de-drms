# 精读笔记 · Director 1993《Statistical Integrated Circuit Design》（IEEE Journal of Solid-State Circuits 28(3):193–202）

> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> H8 轴定位：**统计电路设计主脉综述**（Director 一作，即 Director–Rohrer 1969 伴随网络灵敏度一脉的本人）。重点检验：①元件/扰动偏差→性能偏差如何建模；②匹配与相关性如何处理；③滤波器多指标是否出现。

## 出处

- Director, S.W., Feldmann, P., Krishna, K. (1993). Statistical Integrated Circuit Design. *IEEE JSSC*, 28(3):193–202. DOI 10.1109/4.209985.
- PDF 10 页 = 期刊页 193–202（PDF 第 1 页 = p.193，一一对应；下文页码为期刊页码）。
- 已通读全文（§I 引言 / §II 参数良率最大化 / §III VLSI 优化表述 / §IV 统计设计议题 / §V 良率最大化方法论[随机扰动法、TI 法、边界积分法] / §VI 电路实例 / §VII 结论 / 参考文献）。

## 核心命题（原文）

1. **良率损失二分：局部缺陷→功能失效；全局扰动→参数失效；统计设计的对象是后者**（p.193）：
   > "Yield of less than 100% is due to two types of disturbances: local and global. Local disturbances, caused by spot defects in the manufacturing process, are the primary cause of catastrophic failures or functional failures which often cause a change in the basic functionality of the circuit. Global disturbances, primarily caused by phenomena that affect most devices on a chip (e.g., mask misalignment, variations in diffusion temperatures, or implant doses), are the primary cause of parametric failures. Parametric failures result when the chip is 'functional' but specifications on such quantities as speed and power are not met."

2. **良率 = 性能落入可接受区域 A_φ 的概率；性能是标称参数与随机扰动的函数 φ=φ(p₀,ξ)**（p.194）：
   > "We can now formally state the yield of a design as the probability that a manufactured circuit has acceptable performance, i.e., that the vector φ belongs to the acceptability region A_φ: y = Prob{φ ∈ A_φ}."（p.194）
   > "it is convenient to express circuit performances as functions of the deterministic nominal parameter values p₀, and the random vector ξ: φ = φ(p₀, ξ)."（p.194）
   （这是「元件偏差→传递函数/性能偏差」的标准统计建模框架：性能向量而非单条传递函数。）

3. **匹配（matching）在统计设计中的处理方式：作为确定性等式约束压缩设计变量维数，而不是统计相关建模**（p.194）：
   > "Although there are 24 transistors and consequently 48 widths and lengths that are designable, only 12 of the widths and lengths are independent designables, due to matching constraints, e.g., M1 and M2 should have identical dimensions. The designable part of the p₀ vector of this circuit therefore has 13 elements: 12 widths and lengths and a bias current."
   （即"匹配=尺寸完全相同"的确定性理想化；残余失配的统计（Pelgrom 式）只以引文 [27] 出现，正文未展开。）

4. **性能间的相关性使总良率 ≠ 边际良率之积——统计设计中相关性的核心命题**（p.200）：
   > "Since the performances are not independent of each other, the overall parametric yield is not equal to the product of the marginal yields."
   > "performances are usually competing against each other (e.g., an increase in gain usually causes an decrease in bandwidth), may cause the circuit to have low parametric yield even though it may seem to have good nominal performances and good marginal yields."（p.200）
   （对 P1 的方法论对照点：P1 的 G_DC=H_N−H_P 正是「两个高度相关性能之差」；本文提供的是"相关性能不能按独立乘积处理"的一般论据，但没有做差值随机变量的方差分析。）

5. **边界积分法：用 Stokes 定理把良率体积分化为可接受域边界的面积分，良率、良率梯度、良率对规格/扰动分布参数的灵敏度共用同一组边界样本**（p.198–199）：
   > "the boundary integral method is unique in the sense that through the application of Stokes' theorem it reformulates yield itself as a surface integral on the boundary of the acceptability region in this disturbance space."（p.198）
   > "yield and derivatives of yield, with respect to deterministic nominal parameters, parameters of the disturbance distribution, and performance constraints, can all be expressed as surface integrals on the acceptability region boundary, and can be computed through Monte Carlo based on the same set of sample points."（p.198）
   > "The derivative values are the sensitivities of the yield to various constraint specifications."（p.198）
   （「良率对规格的灵敏度」＝门槛化方法学的直接先例：哪个规格该放松、哪道工艺该收紧。）

6. **良率优化的代价是标称性能的权衡交换**（p.199）：
   > "These figures show the trade-off that has been achieved between the gain and unity gain frequency (ugf) specs, and the phase margin spec. The final spreads of all three performance measures have been reduced. However, the nominal gain and the nominal ugf have been reduced and a corresponding increase in the nominal phase margin has been obtained."

7. **公差与规格本身也可作设计变量（tolerancing / specification assignment 问题表述）**（p.195）：
   > "one can identify parameters for which relaxing the tolerance has only minor effects on the variability of performances. This may allow the use of a less expensive processing step, or a simpler circuit topology, thus reducing manufacturing cost."（p.195）
   > "The problem here is to identify specification constraints responsible for significant yield loss and to predict to what extent yield can be improved by relaxing them."（p.195）

## 关键数值（原文）

- **滤波器实例（五极点电流模式滤波器，175 只 MOS 管）**（p.200）：规格 dc gain ≥ −1.5 dB、bandwidth ≥ 35 MHz、passband ripple ≤ 0.5 dB、rolloff ≥ 100 dB/decade；初值良率 42%，**仅用 288 次电路仿真**优化后升到 98%：
  > "The desired specifications for this circuit are dc gain ≥ -1.5 dB, bandwidth ≥ 35 MHz, passband ripple ≤ 0.5 dB, rolloff ≥ 100 dB/decade."（p.200）
  > "Upon optimization, which required only 288 circuit simulations, the yield of this circuit was increased to 98%."（p.200）
- 初始点边际良率（Table I，p.200）：Bandwidth 88%、DC gain 100%、**Ripple 54%**、Roll-off 100%。
- 良率对扰动方差的归一化灵敏度（Table II，p.200）：n 管 tox 变化 −0.9938（危害最大）；n 管长度 +0.060、p 管 tox −0.058、p 管长度 −0.059、n 管宽度 −0.0092、p 管宽度 +0.026、n 管平带电压 +0.0075、p 管平带电压 +0.031。原文判读：
  > "variance of the oxide thickness variation of the n-type devices has the most detrimental effect on the yield."（p.200）
- 设计变量改动（Table III，p.200）：Width 3 +50.76%、Width 5 +95.53%（"has almost doubled"），Width 4 仅 +2.21%。
- 优化后边际良率（Table IV，p.201）：四项均 99–100%。
- 全差分折叠共源共栅放大器（§VI 例 1）：良率 **39% → 100%**（p.199）；§VI 例 2：维持 Ymin=80% 约束下把 ugf 规格从 45 MHz 提到 **55 MHz**，末态良率 98%（初始 100%）（p.200）。
- TI 法经验：MOSFET 电流/电容主要敏感于 4 个统计变量（p.197）：
  > "both current and capacitance in MOSFET's are primarily sensitive to four variables [5]-[7]: width reduction, length reduction, oxide capacitance, and flat-band voltage… Since these parameters are determined by different steps in the manufacturing process, they can, to first order, be assumed to be independent of each other."
  （统计独立性是"一阶近似"假设——相关性处理的第一道简化。）

## 对 P1/P2/P3 的对照

- **P1（失配→G_DC、τ 匹配）**：方法学中相关。本文无差分路径/极点匹配概念，但 p.200「性能相关→总良率≠边际良率积」正是 P1 类命题（两相关量之差的统计特性不能由各自边际统计推出）在良率语境的同构表述。可作为「相关性必须显式处理」的引证。相关度：中（仅方法学）。
- **P2（Kelvin 结构地板 ≈56 dB）**：低。匹配只以「M1/M2 尺寸相同」的理想化约束出现（p.194），无残余失配统计→地板的链条（Pelgrom 仅列引文 [27]）。相关度：低。
- **P3（平坦度约束衰减可达上界 / Bode-Fano）**：中低。滤波器例含 passband ripple ≤ 0.5 dB 与 rolloff ≥ 100 dB/decade 的多指标权衡（p.200），证明「平坦度类指标参与统计权衡」；但这是数值良率优化，**不含任何解析匹配界/带宽积分约束**，与 Bode-Fano 可达上界无接触。相关度：中低。
- **方法学（增量四·门槛化）**：高。良率对规格的灵敏度（derivative of yield w.r.t. φ_B，p.198）、对扰动方差的灵敏度（Table II）给出了「哪个门槛/哪道工艺主导损失」的量化判据——门槛化论证的标准工具箱。
- **killRisk**：**无**。不冲击 P1/P2/P3 任何主张；其「加权/标称设计不现实、统计波动才是常态」的立场反而与 P1 的失配敏感性立场同向。

## 没读到的

- **伴随网络灵敏度（Director–Rohrer 1969）仅以参考文献 [21] 出现**（"S. W. Director and R. A. Rohrer, 'The generalized adjoint network and network sensitivities,' IEEE Trans. Circuit Theory, vol. CT-16, pp. 318-323, Aug. 1969"），正文未展开伴随法；本文的"sensitivity"全部是**良率对参数的灵敏度**，不是传递函数对元件的灵敏度。
- **匹配的统计模型**（Pelgrom AV/面积律）未展开，只有引文 [27]。
- 传递函数层面的灵敏度（Orchard 一脉、Sₓ 对 H(s)）完全缺席——本文只有性能标量。
- Bode-Fano/匹配界/平坦度-衰减解析界。
- 差分结构 CMRR/结构地板。
- 待核：Table II 中 "n-device r,, variation" 疑为 OCR 失真（结合上下文四变量应为 tox/oxide thickness 变化，原文排版无法从本 PDF 文本层完全确认，图版待核）。
