# 精读笔记 · Nicosia 2008《An evolutionary algorithm-based approach to robust analog circuit design using constrained multi-objective optimization》（Knowledge-Based Systems 21:175–183）

> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> H8 轴定位：统计设计 + 多目标 Pareto 交汇点。**含一个真正的滤波器（五阶 leapfrog）多目标 Pareto + 良率案例**——直接回答 H8 ③「滤波器多目标 Pareto 是否被触及」：是，但全部是数值/统计方法，无解析界。

## 出处

- Nicosia, G., Rinaudo, S., Sciacca, E. (2008). An evolutionary algorithm-based approach to robust analog circuit design using constrained multi-objective optimization. *Knowledge-Based Systems*, 21:175–183. DOI 10.1016/j.knosys.2007.11.014.
- PDF 9 页 = 期刊页 175–183 一一对应（PDF p.1 = 刊页 175；下文页码为刊页）。
- 已通读全文（§1 引言 / §2 标称设计 vs 良率设计 / §3 约束多目标框架 / §4 A-NSGAII 算法 / §5 RF LNA / §6 Leapfrog 滤波器 / §7 UWB LNA / §8 结论）。

## 核心命题（原文）

1. **IC 设计 = 混合整型/离散/连续域上的约束多目标问题；多目标间「强非线性相互依赖」**（p.175，摘要）：
   > "Typical analog integrated circuit optimization problems are computationally hard and require the handling of multiple, conflicting, and non-commensurate objectives having strong nonlinear interdependence. This paper tackles the problem by evolutionary algorithms to produce tradeoff solutions on the Pareto Front."
   > "In this research work Integrated Circuit (IC) design has been formulated as a constrained multi-objective optimization problem defined in a mixed integer/discrete/continuous domain."（p.175）
   （离散性来自光刻分辨率，p.176："each optimization variable is related to physical dimensions of components placed in the circuit layout, whose resolution is defined by photolithography."）

2. **标称设计与良率设计二分；良率定义与扰动分类**（p.176）：
   > "Two types of specifications have to be met in the step of circuit sizing: (1) performance, i.e., fulfilment of the specifications imposed by a given application, and (2) robustness, i.e., insensitiveness to parametric and environmental variations. To simplify the design, these two specifications are commonly treated separately."（p.176）
   > "The term yield in the framework of the microelectronics industry denotes the ratio between the number of chips that have acceptable performance over those that have been manufactured. There are two classes of causes by which the performance of a circuit can be classified as unacceptable: (1) local perturbation (silicon crystal defects that cause the malfunctioning of a single chip in a wafer) and (2) global perturbations (process imprecision like mask misalignment, temperature and/or implantation dose variations involving all the chips in a wafer)."（p.176）

3. **Pareto 前沿边缘的解良率低、靠近理想点的解良率高——「单目标极值点在统计涨落下失效」的实证**（p.179）：
   > "solutions with minimum noise or minimum current (placed at the edge of the Pareto Front of Fig. 1 (right plot) and thus farthest from the 'ideal' point), exhibit lower values of yield. In fact, statistical fluctuations around the nominal point cause either the current or noise performance to jump out of the feasible set, making the whole circuit faulty. On the other hand, the point selected according to the 'optimality' criterion (i.e., placed closest to the 'ideal' solution) performs 100% yield"
   （方法论要点：把良率作为「高阶信息」叠加在 Pareto 前沿上做最终选择——yield-aware Pareto；引文 [1] 即 Tiwary 等 "Generation of yield-aware Pareto surfaces"。）

4. **滤波器案例：五阶 leapfrog 滤波器（4 运放 + 18 电阻 + 8 电容），16 项性能约束含通带波纹、阻带衰减、群时延波纹/斜率**（p.180）：
   > "The circuit block employed as test case, i.e. a fifth-order leapfrog filter, is depicted in Fig. 2 (left plot). Four leapfrog loops are realized through 4 (equal) differential opamps (OA1–OA4), 18 resistances (two times R1–R9), and 8 capacitances (two times C1–C4)."
   > "Dc gain, pass-band ripples and stop-bands are directly related to the frequency mask of the filter, whereas network delay is assessed using the group delay (ripple and slope)."（p.180）
   （20 个设计变量 k1–k4、m1–m4、Vn1–Vn4、w0、wrp、Ra、C、C1、L2、C3、L4——含 4 个运放的等效输入噪声变量与频率搬移变量。）

5. **确定性最优化在滤波器问题上全部失败，A-NSGAII 找到可行解且良率 69.5%**（p.180–181）：
   > "None of the investigated deterministic algorithms is able to find feasible solutions, moreover the best solutions found by such algorithms violates more than one constraint."（p.180）
   > "A-NSGAII finds feasible solutions also providing a considerable amount of over-achievement in most performance metrics producing high yield values."（p.180）
   > "the algorithm provides 36 non dominated points. Moreover, the degree of coverage and distribution across the objective space is satisfactory."（p.180，30000 次迭代、3 目标 13 约束）

6. **UWB LNA 中明确出现「增益谱平坦度」作为设计目标**（p.181）：
   > "The capacitor CP and the primary winding of the load transformer T1 should be designed to resonate at the frequency of 4 GHz, while the shunt resistance RP was inserted to lower the quality factor of the resonator. Such a shunted resonant load allows an adequate gain spectral flatness to be achieved."
   （平坦度在此以「降 Q 展宽」的电路手段达成，不是解析约束。）

7. **亚阈值区工作以「对电压/温度/工艺变化灵敏度大幅升高」为代价**（p.182）：
   > "The benefits achievable by sub-threshold operation are paid at the price of much higher sensitivity of ICs to variations in supply voltage, temperature, and fabrication process. This in turn contributes to lower circuit robustness because large deviations from nominal operating conditions are more likely to take place."

## 关键数值（原文）

- RF LNA 各候选点良率（Table 1，p.179；Monte Carlo **200 样本、mismatch-only 模式**）：Min NF 解 64.5%、Min IC 解 68%、Min S11 解 85.5%、Max S21 解 70%、Min S22 解 94%、**Opt. Nom.（最近理想点）100%**、Designer（手工）99.5%。性能行：|S11|<−14 dB、|S21|>8 dB、|S22|<−6 dB、NF<4.7 dB、IC<4 mA（Opt. Nom. 实测 −16.673/9.402/−28.223 dB、NF 4.377 dB、IC 3.076 mA）。
- Leapfrog 滤波器对比（Table 2，p.181）：全局误差 NEWUOA **85.95%**、DIRECT **289.1%**、A-CRS **43.9%**、Designer **7.8%**、**A-NSGAII 0%**；良率行仅 A-NSGAII 有值 = **69.5%**（其余 n.a.）。
- A-NSGAII 滤波器关键性能（Table 2，p.181）：通带波纹 9.1/9.7 MHz 两点均 0.55 dB；阻带 22.5 MHz ≥25 dBc 规格实测 36.84 dBc、34.2 MHz ≥56 dBc 实测 56.23 dBc；群时延波纹 16.17/24.18（单位待核，见下）；等效输入噪声 42.14（约束 ≤44，单位待核）；直流电流 34.47（约束 ≤40，单位待核）；硅面积 14622 µm²（约束 ≤18000 µm²，此行可读）。
  ⚠ 待核：Table 2 约束列的 ≥/≤ 符号在 PDF 文本层被 OCR 吃掉（"60.8 dBPP"、"620 ns"、"63 fs/Hz"、"P12.2 kX"、"62.8 V"、"6 44 nV=Hz2"、"640 mA" 等应为 ≤0.8 dBpp / ≤20 ns / ≤3 fs/Hz / ≥12.2 kΩ / ≥2.8 V / ≤44 nV/√Hz / ≤40 mA，从数值对比反推，**引用前须对照图版核实**）。
- 算法规模：RF LNA 5000 次迭代得 664 个不同非支配解（p.178–179）；1000/2500 次迭代的中间前沿已接近最终前沿（"reducing the computational load by a large amount (up to 5) does not degrade algorithm performance so much"，p.179）；Leapfrog 30000 次迭代、36 个非支配点（p.180）。
- UWB：中心 4 GHz、最小带宽 1 GHz（"an UWB signal centred at 4 GHz would have a minimum bandwidth of 1 GHz"，p.181）；脉冲宽度 <1 ns。

## 对 P1/P2/P3 的对照

- **P1（失配→G_DC、τ 匹配）**：无涉。无差分路径/极点匹配内容；仅亚阈值「灵敏度升高→鲁棒性下降」的一般陈述（p.182）。相关度：低。
- **P2（Kelvin 结构地板 ≈56 dB）**：无涉。无结构/比失配地板讨论。相关度：无。
- **P3（平坦度约束衰减可达上界 / Bode-Fano）**：中。**这是 H8 轴中滤波器多目标 Pareto 的正面实例**：通带波纹、阻带衰减、群时延波纹、噪声、电流、面积同表约束（Table 2），证明「平坦度类指标与衰减类指标存在于同一权衡面」；但其平坦度-阻带关系是**数值搜索的经验权衡**，无 Bode-Fano 型解析可达界；增益平坦度另以降 Q 展宽处理（p.181）。对 P3 可作「指标共存性」佐证，不构成界。相关度：中。
- **方法学（增量四·门槛化）**：高。良率作为 Pareto 前沿上的后验筛选准则（理想点最近≠良率最优的边缘陷阱）、16 项规格逐项量化超裕量——与「门槛化」直接同构。
- **killRisk**：**无**。数值 Pareto/良率方法与 P1/P2/P3 的解析主张不冲突。

## 没读到的

- 任何**解析灵敏度/伴随网络**方法（全文 sensitivity 仅指亚阈值电路对环境变化的敏感度，非 S^H_x）。
- **Bode-Fono/匹配界**类解析可达上界（无）。
- 差分结构路径失配/CMRR/结构地板（无）。
- 良率估计的方差/置信区间（200 样本 MC 的统计误差未讨论）。
- 运放级晶体管级细节（"Expressions relating resistance and capacitance values to these quantities are quite complex and will not be reported in the following."，p.180）。
- 待核：Table 2 约束符号与单位（见上）；群时延波纹单位（ns）与群时延斜率单位（fs/Hz）的 OCR 反推值。
