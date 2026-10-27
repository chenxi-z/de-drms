# 精读笔记 · DeBrunner 1992《Choosing a Filter Structure: Component Sensitivity and Design-for-Testability》（ISCAS 1992）

> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。

## 出处
- DeBrunner, V.E. (The University of Oklahoma). "Choosing a filter structure: component sensitivity and design-for-testability." *[Proceedings] 1992 IEEE International Symposium on Circuits and Systems (ISCAS)*, vol. 1, pp. 240–243. DOI: 10.1109/iscas.1992.229969.
- PDF：`/home/anning/Documents/Obsidian Vault/20-硬件工程/10-项目设计/p1-文献谱系/fulltext/H8-灵敏度与统计电路设计/debrunner0hoosing.pdf`（4 页，印刷页 240–243；下文页码 = PDF 物理页 1–4）。OCR 质量差（公式与表格大面积缺失），引用均逐字照录 OCR 文本。

## 核心命题（原文）
1. **中心论点：低灵敏度与可测性并不矛盾，可以兼得**（p.1 摘要）：> "We show that low sensitivity filter designs are possible that are also good candi-dates for parametric characterization in circuit test."（打破"要可测就必须对元件敏感"的直觉对立。）
2. **对立的传统论证**（p.1）：> "The usual argument goes that it is not possible because a system must be sensitive to its components in order for those components to be easily "seen" from inputloutput data"（OCR：input/output；随后作者引 Denman 等人的话）> "These two goals are diametrically opposed to each other, as succinctly put in the follow-ing"。
3. **作者前序工作的核心分解：灵敏度 S(θ) 与参数互联度 K(θ) 是两个独立因素**（p.1）：> "We have noted previously [4,5,6,71 that pa-rameter sensitivity S(0) is only one of two mod-el dependent factors which affect parameter con-vergence in inputloutput measurement identification"（OCR：S(θ)、[4,5,6,7]；第二个因素 = parameter interconnectedness K(θ)，"a measure of the parameter independence"）。关键结论引文：> "Structures need not be highly sensitive for fast and accurate identification if these structures exhib-it low component interconnects."
4. **互联度 = Fisher 信息矩阵的条件数**（p.2）：> "The interconnectednessof the system param-eters is determined by examining the (%-norm) conditioning of the parameter Fisher Informa-tion matrix F"（OCR：(%-norm) 应为 (κ-norm/条件数)，公式(3) 本身在 OCR 中缺失；文内说明其中 I 为 F 的最大/最小特征值）；灵敏度定义（p.2，式(2)）：> "S(8) = trace(F)"（即 S(θ)=trace(F)，可由确定性摄动理论或随机过程理论两条途径导出——与 H8 轴①"灵敏度理论的两种数学视角"直接相关）。
5. **警示：可辨识 ⇏ 高敏感——这正是可测性鲁棒设计的钥匙**（p.2）：> "a caution is in order here - the reverse as-sumption should not be made, i.e. parameters which are easy to identify are not necessarily highly sensitive. It is precisely this assumption which we seek to demonstrate as incorrect, and which allows robust designs-for-testability!"（引 [1] Catelani 等只证明了"高敏感→易辨识"，本文论证反向不成立。）
6. **反例：低敏感结构反而收敛慢**（p.3）：> "has a lattice realization sensitivity of 745 and a direct form I1 realization sensitivity of 3,165. However, the parameter interconnectedness is such that the direct form 11 realization has a relative structure-algorithm time constant of 17.3 versus the 745.2 of the lattice structure."（4 阶系统：lattice 灵敏度 745 远低于 DF-II 的 3165，但时间常数 745.2 vs 17.3——敏感度与互联度必须分开度量。）

## 关键数值（原文）
- 3 阶低通系统、5 种结构对比（p.3，Table 1）：> "the lat-tice structure is the least sensitive by a factor of 5 times."（lattice 灵敏度最低约 5 倍；且 > "the lattice structure has the next-to-low-est relative time constant 2"——OCR：τ，次低）。Table 1 数值本体在 OCR 中几乎全失（仅余 "5.50×10⁷ⁿ…9.8×10⁻¹⁴.50" 之类的残行），具体数值待核原 PDF。
- 4 阶系统 Monte-Carlo（p.3）：> "Monte-Carlo simulations show that the lattice structure model consistently converges faster than any other model structure when gradient-based algorithms are used."
- 反例数值（p.3）：lattice S=745、DF-II S=3165；τ=745.2 vs 17.3（见命题 6）。

## 对 P1/P2/P3 的对照
- **P1（消去条件/失配→G_DC）**：中。概念上与 P1 同族但数学不同族：本文把"对元件变化的灵敏度"与"参数可辨识性"解耦成两个正交度量（S=trace(F) 与 K=cond(F)），结论"低敏感≠不可辨识"——这与 P1 的"网络对元件绝对值不敏感（G_DC≡0）但对失配敏感（τ=R·C 匹配）"是同一直觉的两个领域版本。但本文处理的是**数字滤波器系数结构**（Fisher 信息/梯度辨识），不是 Orchard/Director 伴随网络的无源 RC 灵敏度，也未给出任何元件级充要条件——可作"P1 消去条件的跨域类比"引用，不构成理论支撑或撞车。
- **P2（Kelvin 结构地板）**：无。全文无共模/接地内容。
- **P3（平坦度约束衰减上界）**：低-中。主题是"按元件灵敏度选滤波器结构"，属 H8 轴③"滤波器设计的结构选择"支线；但只涉及数字结构（cascade/lattice/parallel/DF-II/Hessenberg）的系数量化与辨识，不涉无源网络频响平坦度-衰减权衡，更不触 Bode-Fano 型界。引用面仅限"结构选择对元件容差的稳健性"背景。
- **方法学（D1–D10）**：低。"两个度量分开评估"的思想与门槛化"逐项单列判据"精神同源，可作旁证。
- **killRisk**：无威胁。未给出任何无源网络消去条件、匹配界或衰减上界；与 P1 四主张正交。需注意的唯一边界：若 P1 行文声称"低灵敏度与可观测性天然矛盾已被本文打破"，属过度引用——该文仅是数字滤波器域的类比。

## 没读到的
- 式(1)(3)(4) 的完整数学（Fisher 信息矩阵元素、条件数定义、时间常数 τ 公式）在 OCR 中全部缺失，只有正文转述；引用这三个定义时必须回原 PDF 读图。
- Table 1（5 结构灵敏度数值）与 Table 2（4 结构数值）正文数值失真，仅能引用正文给出的两处对比（5 倍因子、745/3165/17.3/745.2）。
- 参考文献 [3]（作者 ICASSP'92 多准则优化低灵敏度数字滤波器）未读——"低灵敏度设计"的构造性方法在那里。
- 作者称反例系统 "may be obtained from the author"（p.3），无法复核该 4 阶系统具体参数。
