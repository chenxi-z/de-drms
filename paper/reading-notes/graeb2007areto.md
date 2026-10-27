# 精读笔记 · Graeb 2007《Pareto Optimization of Analog Circuits considering Variability》（ECCTD 2007）

> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。

## 出处
- Graeb, Helmut; Mueller, Daniel; Schlichtmann, Ulf. "Pareto optimization of analog circuits considering variability." *2007 18th European Conference on Circuit Theory and Design (ECCTD)*, pp. 28–31. DOI: 10.1109/ecctd.2007.4529528.
- PDF：`/home/anning/Documents/Obsidian Vault/20-硬件工程/10-项目设计/p1-文献谱系/fulltext/H8-灵敏度与统计电路设计/graeb2007areto.pdf`（4 页，印刷页 28–31；下文页码 = PDF 物理页 1–4）。

## 核心命题（原文）
1. **变差必须内生于 Pareto 前沿，而不是把良率当第三个目标**（p.1）：> "Certainly the circuit yield, i.e. the percentage of manufactured circuits that satisfy the performance specification, can be included as an additional objective in the Pareto optimization. But this is not sufficient. Instead, a Pareto front of the original performance features is required that inherently includes yield and robustness figures."（论文立意：单纯把 yield 加为目标列不够，要在性能目标自身的 Pareto 前沿上"内嵌"良率/鲁棒性。）
2. **Pareto 最优的形式定义 = 不存在支配它的次要性能向量**（p.2）：> "M ( f * ) = f f ≤ f * = f ∀i f i ≤ f i* ∧ ∃i f i ≠ f i*"（式(7) 定义 minor performance vectors 集合 M），> "f * ∈ F is Pareto optimal ⇔ M ( f * ) ∩ F = { }"（式(8)：无任何更优向量落在可行区内即 Pareto 最优）。
3. **每个 Pareto 点对应一条目标射线，用加权 l∞ 范数求解**（p.2）：> "min max wi ⋅ ( f i ( x d ) − f RP,i )"（式(10)，goal attainment 型 min-max 公式；经式(12)(13) 化为对 α 的带约束最小化，参考点 fRP + 方向 v 的射线撞击前沿）。
4. **在每个 Pareto 点做基于线性性能模型的 realistic worst-case 分析**（p.4）：> "f ( x s ) = f ( x d , x s, 0 ) + S ⋅ ( x s − x s, 0 )"（式(16) 一阶泰勒线性化），> "The matrix element Sij contains the sensitivity of perfor-mance feature fi with respect to statistical parameter xs,j."（灵敏度矩阵 S 就是"统计参数→性能特征"的一阶传递——这正是 H8 轴要的"元件偏差→函数偏差"数学，不过是 IC 工艺参数版）。
5. **线性化后性能特征服从正态分布，包络出 σ 级 Pareto 前沿**（p.4）：> "f ~ N ( f ( x d , x s ,0 ) , S ⋅ C ⋅ S T )"（式(17)：均值取额定值，协方差 = S·C·Sᵀ；由此在每个 Pareto 点画 3σ/6σ 等密度线，包络得到 3σ/6σ Pareto 前沿）。
6. **worst-case distance βw 直接换算良率**（p.3）：> "βw is also called worst-case distance. It determines the yield that can be achieved if fw,i is taken as a performance constraint (3) in the sense of a βw -sigma design [9]"。

## 关键数值（原文）
- βw 与良率换算表（p.3）：βw = 1 → Yield 84.1%；2 → 97.7%；3 → 99.9%。
- 验证算例：压控环形振荡器（11 级反相器，Fig.4），目标 Kvco vs I_vco；Monte-Carlo 验证 100 个采样（p.4）：> "we have performed a Monte-Carlo analysis with 100 sample elements. Fig. 6 shows the result at one Pareto point. We can see that the true distribution is non-normal, but the accuracy of the linear approach in this case is very good."
- 总 CPU 时间（p.4）：> "The overall CPU time for the computations was 3.5 hours."
- 前沿覆盖三性质（p.3）：> "The Pareto front is captured completely, i.e. including its boundaries. / The computed discrete points of the Pareto front are evenly spread. / All target rays hit the Pareto front."

## 对 P1/P2/P3 的对照
- **P1（消去条件/失配→G_DC）**：低-中。本文的 S 矩阵是"统计参数一阶偏差→性能偏差"，与 P1"元件失配→G_DC 残差"同为一阶泰勒传递的数学，但 P1 关心的是**结构性恒等消去**（G_DC≡0 对元件不敏感的充要条件），本文只做**一阶线性化+正态传播**，不处理失配恒等式；无敏感度理论（Orchard 伴随网络）一脉的器件级推导。引用时只能作"现代灵敏度→统计传播"对照，不能当理论支撑。
- **P2（Kelvin 结构地板 ≈56dB）**：无。全文不涉共模/CMRR/接地结构。
- **P3（平坦度约束衰减可达上界 = Bode-Fano 亲缘）**：中。这是 H8 轴"滤波器多目标优化是否触及 Pareto 框架"的正面样本：它给出 Pareto 前沿的严格定义（式(7)(8)）与确定性射线法（式(10)–(13)），并演示"性能目标 × 变差"二维权衡。但它是 IC 尺寸综合（VCO），不做频域响应平坦度、不触匹配界/Bode-Fano，也不做 RC 网络衰减上界——对 P3 是**方法学引用**（Pareto 权衡框架的权威定义来源），非内容撞车。
- **方法学（D1–D10 门槛化）**：中。其"在每个工作点附带变差评估"的思路与门槛化方法学"逐点给失配裕度"精神同源，可作背景引用。
- **killRisk**：无威胁。本文不声称平坦度-衰减界、不涉无源 RC 网络消去条件，与 P1 四主张无重叠；是安全的 Pareto 框架定义引用源。

## 没读到的
- 参考文献 [6]（Mueller/Graeb DATE 2007 goal attainment + SQP 细节）、[9]（Graeb《Analog Design Centering and Sizing》Springer 2007 全书）未读——worst-case 距离 βw 的严格定义在其中，本文只引用。
- 式(15) 的等密度轮廓具体数值网格、Fig.6 的 Monte-Carlo 散点数值未从图上提取（图内数字轴只有 Kvco 1200–2200 MHz/V、I 400–800 µA 量级，正文未给误差百分比）。
- 100 采样 Monte-Carlo 只在"一个 Pareto 点"验证（p.4），整条前沿的线性化精度无系统统计——如需引用其精度主张，须注明该局限。
