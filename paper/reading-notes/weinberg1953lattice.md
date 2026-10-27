# 精读笔记 · Weinberg 1953《RLC Lattice Networks》（Proceedings of the I.R.E.）

> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> 页码口径：所引页码为**期刊印刷页码**（PDF 第 1–6 页 = 印刷 p.1139–1144，已按页眉逐页核对；**PDF 第 6 页下半起混入下一篇论文 Mason "Feedback Theory–Some Properties of Signal Flow Graphs" 的开头，不属于本文**）。
> 文件：`fulltext/H2-差分CMRR/weinberg1953lattice.pdf`；bib key `weinberg1953lattice`。1953 扫描件但 OCR 质量意外地好；个别下标/数字损处已标 [OCR损]。

## 出处
- Louis Weinberg, "RLC Lattice Networks," *Proceedings of the I.R.E.*, vol. 41, no. 9, pp. 1139–1144, Sep. 1953. DOI 10.1109/jrproc.1953.274448。作者时为 Hughes Aircraft Co. Research Physicist；论文基于其 MIT RLE Technical Report No. 201 一章，Guillemin 指导，1953-01-30 收稿、1953-06-01 修回（p.1139 脚注）。
- 主题：**任意（最小相位或非最小相位）RLC 转移阻抗的综合方法**——部分分式展开 + 留数分配，把 Z₁₂ 实现为开路格形（lattice）两臂 Za、Zb 之差；特点是无互感、无理想电感（每个 L 串 R）、可控制线圈 Q。这是**综合（synthesis）**方向：给定想要的 Z₁₂，造出格形。

## 核心命题（原文）
1. **总命题：任意物理可实现的转移阻抗都可实现为开路格形（p.1139, Summary）**：
   > "A method is presented for the realization of a general transfer impedance as an open-circuited lattice. The method is a simple one based on a partial-fraction expansion of the given function. No restriction other than that of physical realizability is placed on the function to be realized; thus both minimum-phase and nonminimum-phase functions are realizable by this method. A part of the method allows control over the Q's of the coils used in the final network. The achieved lattice has the significant features of requiring no mutual inductance and no perfect coils, that is, every inductance appears with an associated series resistance so that in building the network low-Q coils may be used."
   （解释：格形综合的完备性——除物理可实现性外无限制。这是"理想对称格形"谱系（Bartlett 二等分 → Forte → Weinberg 系统化）的期刊锚点。）
2. **★格形恒等式：转移阻抗 = 两个策动点函数之差（p.1139, 式 (2)）——与 P1 的 G_DC = H_N − H_P 同一代数形式**：
   > "For such a lattice it may easily be shown that the open-circuit transfer impedance is given by the difference of two driving-point functions, namely, Z₁₂ = ½(Zb − Za). (2)" [OCR损：原文为分式 ½，OCR 将分数线吞掉只余 "2(Zb−Za)"；Fig.1 图注 OCR 同样将 ½ 损成 "1"，½ 形状按上下文与格形标准结果复原，待核扫描图]
   （解释：**全文与 P1 最相关的一句**。格形的差分转移天生是"两个单端网络函数之差"——精确对称下 Z₁₂ 由结构保证等于 (Zb−Za)/2，无需任何匹配条件；Za≡Zb 时 Z₁₂≡0。P1 的 G_DC=H_N−H_P 是同一"差式"代数在**失配非对称多级梯形**上的化身。但 Weinberg 用此恒等式做**正向综合**（把给定 Z₁₂ 拆成两个正实函数），不做**消去条件分析**（何时差式在全频段恒零），两方向互为逆问题。）
3. **RC 格形部分分式法的先例溯源（p.1139）**：
   > "Though the procedure as applied to RC networks has been well known¹,² for a number of years, no one has yet shown its applicability to RLC networks."
   （解释：RC 网络的部分分式格形综合**早已有之**——脚注 ¹ = Guillemin "RC-Coupling Networks," MIT Rad. Lab. Report No. 43, 1944-10-11；² = Bower & Ordung, Proc. I.R.E., pp.263–269, 1950-03。P1 若引 RC 谱系，这两个脚注是最早锚点；本文的贡献仅是推广到 RLC 多重极点。）
4. **留数分配定理：总可把 Z₁₂ 的留数分配得两臂各自正实（p.1140）**：
   > "It is shown below, however, that it is possible to distribute the residues in the simple poles of a given Z₁₂ so that the partial-fraction components of Za and Zb are separately positive real."
   （解释：差式分解存在性的核心引理——任意可实现 Z₁₂ 都能拆成两个正实函数之差。）
5. **Guillemin 电阻库（reservoir of resistance）+ Bode（p.1140）**：
   > "Guillemin³ pointed out that the form of (2), namely, the difference of two positive real functions, allows sufficient resistance to be added to each impedance so that both become positive real. This reservoir of resistance, as Bode⁴ first demonstrated, is all that is necessary to make the partial-fraction terms of an RLC driving-point function separately realizable."
   （解释：差式形式自带"可加电阻冗余"——两臂同时加同值电阻，差 Z₁₂ 不变。这是格形差式的自由度来源。）
6. **极点-留数夹角的正实判据（p.1140, 式 (3)(4)）**：
   > "In words, (4) states that the condition for the existence of a positive real partial-fraction component z₁ is that α₁ be positive and the angle of the pole to the imaginary axis be greater than or equal to the angle of its residue."
   （解释：留数分配的可行域几何判据（Fig.2–4 用初等几何证明式 (11) 恒可满足）。）
7. **线圈 Q 可控：最靠近 j 轴的极点决定 Q 下限（p.1141）**：
   > "It is often of practical importance to control the Q's of the coils used in the synthesis of the partial-fraction components. ... The pole closest to the j-axis will determine the minimum value of Q₁ that will satisfy every partial-fraction realization, where the definition is used Q₁ = ω₁/2α₁ ... In order to use coils with as low Q as possible, it is necessary that the value of d₁ be as close as possible to its maximum value 2α₁."
   （解释：**有损元件（低 Q 线圈）下的可实现性约束**——极点几何决定 Q 下限，式 (13)–(16) 给 Q_max 约束下留数角须满足的不等式。这是"实际非理想元件下的网络可实现性"谱系素材，但对象是线圈损耗、非元件失配。）
8. **多重极点：预畸变 (s−d) 代换（p.1142）**：
   > "To make such a form possible in all cases, we predistort the function,⁸ that is, we substitute (s−d) for s, where d represents the desired R/L ratio. It is important to note that d must be less than the distance of the multiple order pole from the j-axis."
   （解释：多重极点项一般不正实 → 预畸变 + Bott-Duffin/Brune 实现，最后每 L 串 Ld Ω、每 C 并 Cd S 修正回原函数。）
9. **结论（p.1144）**：
   > "A simple method has been demonstrated for the realization of any minimum-phase or nonminimum-phase transfer impedance as an open-circuited lattice. The arms of the lattice are of a simple form and contain no mutual inductance. Any inductance used in the lattice always appears with an associated series resistance so that low-Q coils may be used in building the network."

## 关键数值（原文）
- 数值例（p.1143，非最小相位函数）：Z₁₂ = (s⁴−4s³+7s²−24s+36)/((s²+2s+5)(s²+4s+13)(s+4))；留数 k₁ = −0.05621+j0.43491、k₂ = −1.68047+j0.20020、k₃ = −4.47337；一种满足正实性的分配 k₁(a) = 2.05621−j0.93491、k₁(b) = 2.00−j0.50，k₂(a) = 4.68047−j2.20020、k₂(b) = 3.00−j2.00，k₃(a) = 0、k₃(b) = 4.47337；两臂 Za = 8.22484(s+1.90935)/(s²+2s+5) + 18.72188(s+3.41024)/(s²+4s+13) [Zb 行式 OCR 有缺，p.1144]。
- 复数点求多项式值的两种简化手续（p.1143，综合除法 + 余数定理）；示例 s=−1+j2 处分子 = −12−j44。
- 本文无数值实验（纯方法论文，无测量数据）。

## 对 P1/P2/P3 的对照
- **P1（消去条件）**：**低（但有一个必须点名的形式锚点）**。① 式 (2) Z₁₂ = ½(Zb−Za)（p.1139，逐字见核心命题 2）是"转移 = 两网络函数之差"的经典恒等式，与 G_DC = H_N − H_P 同代数形式；② 精确对称格形里该差式**由结构保证、无需匹配条件**——属已知谱系第一层（Bartlett/Forte 精确对称）的期刊版系统化。**不构成 killRisk**：Weinberg 不谈失配、不谈多级梯形、不谈"何时差式恒为零"的元件条件；其方向是综合（给定 Z₁₂ 拆 Za、Zb），与 P1 的分析问题（给定失配网络求 G_DC≡0 条件）互逆。P1 写作时引它定位"差式恒等式的经典出处"即可。killRisk：无。
- **P2（Kelvin 结构地板）**：**无**。无失配统计、无地板概念；"低 Q 线圈可用"是损耗约束非失配地板。
- **P3（平坦度约束衰减上界）**：**无**。无衰减-平坦度权衡；最接近的只有 Q 约束（极点离 j 轴最近者定 Q 下限，p.1141），属"元件品质 → 可实现极点几何"约束，非通带指标权衡。
- **方法学（增量四）**：**低-中**。示范"把一个不可实现的量分解为两个物理可实现分量之差 + 留数分配满足正实约束"的标准综合手续；对 P1 的可借鉴点是**用留数/极点几何表述元件级条件**（式 (4)(11)(16) 都是"元件参数须落在某几何区域"的判据形式），与门槛化方法学同型。
- **killRisk 判断：无**。理想对称格形综合，与失配多级梯形全频段共模消去正交（与 bib note 预判一致）；最近处仅式 (2) 差式恒等式。

## 没读到的
- Fig.6（最终格形电路的元件数值图）与 Fig.1–5 的图形细节（图不进 OCR）；Zb 的完整表达式 p.1144 首行 OCR 有缺 [OCR损："[8.00(s+1.5)+12.00(s+…)/(s²+4s+13)] + 4.47337/(s+4)" 形状可辨但系数未逐字核实]。
- 式 (13)–(16) 中 Q 与留数角不等式的完整排版（OCR 中 (15)(16) 角标混乱），只引了文字结论；需精确公式时看扫描图。
- PDF 第 6 页混入的下一篇 Mason 信号流图论文开头**未读**（不属本文，不计入本笔记；若 H2 轴需要信号流图谱系另行立卷）。
- 其引文链 Guillemin 1944 MIT Rad Lab Report 43（RC 格形部分分式法最早出处）与 Bower & Ordung 1950 未读——**P1 若追溯"RC 网络差式综合"最早锚点，这两个是下一步**（报告类，可能无开放全文，待核）。
