# 精读笔记 · Stapper 1989《Simulation of Spatial Fault Distributions for Integrated Circuit Yield Estimations》（IEEE TCAD）

> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。

## 出处
- Stapper, C.H. "Simulation of spatial fault distributions for integrated circuit yield estimations." *IEEE Transactions on Computer-Aided Design of Integrated Circuits and Systems*, vol. 8, no. 12, pp. 1314–1318, Dec. 1989. DOI: 10.1109/43.44511.（IBM General Technology Division, Essex Junction, VT）
- PDF：`/home/anning/Documents/Obsidian Vault/20-硬件工程/10-项目设计/p1-文献谱系/fulltext/H8-灵敏度与统计电路设计/stapper1989imulatio.pdf`（5 页，印刷页 1314–1318；下文页码 = PDF 物理页 1–5）。

## 核心命题（原文）
1. **良率分析必须考虑缺陷的空间成簇分布，而非均匀随机**（p.1）：> "It, therefore, is becoming increasingly more important in yield analysis to study the effect of the spatial dispersion of the defects and faults within the in-tegrated circuits."（OCR 断词连字符原样；立论：随芯片规模增大，缺陷不再可假设随机均匀分布，需模拟其空间聚集。）
2. **两类成簇故障模拟器**（p.1 摘要）：> "Two methods used in fault simulation for integrated cir-cuit yield modeling are described. Both methods simulate clustered fault locations on a map."（方法一 = 径向对称双变量高斯生成对称簇 + 簇形变（拉伸/划痕/旋转/平移）；方法二 = 负二项式样簇生成器，按时间步、依赖邻域故障数逐个加故障。）
3. **故障引入概率线性依赖已有故障数**（p.3，式(3)）：> "p ( A t 1 k ) = c + bk"（OCR：p(Δt|k) = c + b·k），> "The quantity c is referred to here as the susceptibility parameter, and the coefficient b as the cluster factor."（c = 敏感度参数，b = 簇因子；对 Stapper 旧模型的三点改造之一。）
4. **邻域相关是本模型的核心机制**（p.3–4）：> "The probability in that formula is no longer assumed to be solely dependent on the number of faults k that occur within a given area, but also on the number of faults li that occur in neighboring circuit areas."（式(4) 引入邻近区域故障数 lᵢ；随后）> "This neighboring circuit dependence forces a correlation between the number of faults in adjacent circuit areas. It results in clusters that spread outside the circuit area boundaries."（相关性由邻域耦合强制产生——注意这是**缺陷空间相关**，不是电路元件匹配相关。）
5. **旧解析模型无法评估容错方案，本方法突破**（p.3）：> "This, however, made it impossible to use those models for the evaluation of fault-tolerance schemes that can handle these types of fault patterns. The approach described here overcomes those limitations."（旧模型把空间变化折叠进 gross yield Y₀，丢掉了故障模式信息。）

## 关键数值（原文）
- 网格取值（p.2）：> "In actual use of the program, val-ues of N = 256 have usually been used."（网格 N=256，对应 100–200 µm 间距——原文印 "100-200 mm"，按上下文应为 µm，OCR/原文待核）；高斯簇 σ "typically is 0.3 or less"；示例参数 N = 256, C = 0.02, a = 0.2（p.2）。
- 划痕簇概率（p.2）：> "with scratches usually made to occur with a probability less than 0.1."
- 统计检验（p.4–5）：> "using simulations of 10 000 chips, the resulting fault distributions were compared with negative binomial distributions using a Kolmogorov-Smimov test. In almost all cases, the results produced significance lev-els exceeding 0.2."（10 000 芯片模拟，K-S 检验显著性水平 >0.2，即负二项分布不被拒绝；且作者明言该法"does not produce pure negative binomial distributions"，p.4。）
- 4×4 电路块分组匹配簇参数 a = 2 的广义负二项分布（p.4）。

## 对 P1/P2/P3 的对照
- **P1（消去条件/失配→G_DC）**：无实质关联。本文的"统计"是**制造缺陷的空间点过程**（成簇、划痕、邻域相关），对象是硬故障/缺陷而非元件参数容差；与 P1 的"元件微小偏差→传递函数直流增益残差"（灵敏度一阶泰勒/恒等消去）不属同一数学。文中"correlation"一词均指缺陷计数相关性，不可引作"元件匹配相关性"依据。
- **P2（Kelvin 结构地板）**：无。全文无共模/接地/屏蔽内容。
- **P3（平坦度衰减上界/Bode-Fano）**：无。无频域、无网络综合内容。
- **方法学（D1–D10）**：低。H8 轴②"统计设计中匹配/相关性的处理"里，本文属于 yield simulation 分支（Monte-Carlo/统计良率）的**IC 制造端**文献——可在综述中作"统计设计的良率端源头之一"背景，但对 D1–D10 门槛化方法学无直接输入。
- **killRisk**：无威胁。主题（晶圆缺陷成簇与容错良率）与 P1 四主张完全不相交；唯一共享词是"yield/统计"，无理论撞车。

## 没读到的
- 式(1)(2)（对称双变量高斯的完整公式）在 pdftotext 中为图片/公式乱码（p.2 "described mathematically as" 后公式缺失），只能从正文转述 C、a 的角色；引用公式时须回看原 PDF 图形。
- 式(4) 的完整分母/系数结构在 OCR 中残缺（p.4 "p(Atlk, ... 12, ... = c(x, y ) * , 4,)"），指数与邻域求和的确切形式待核。
- 参考文献 [8]（Stapper/Armstrong/Saji, Proc. IEEE 1983 "Integrated circuit yield statistics"）与 [4]（block alignment 论文）未读——负二项统计的原始推导在其中。
- 文中 "100-200 mm" 疑为 "µm" 之误（OCR 或原文排版），未核对原图。
