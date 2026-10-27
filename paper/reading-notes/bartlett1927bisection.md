# 精读笔记 · Bartlett 1927《An Extension of a Property of Artificial Lines》（Philosophical Magazine, S.7, vol.4 no.24, pp.902–907）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。

## 出处
- A. C. Bartlett, "LXXXIV. An Extension of a Property of Artificial Lines," *The London, Edinburgh, and Dublin Philosophical Magazine and Journal of Science*, Series 7, vol. 4, no. 24, pp. 902–907, Nov. 1927. DOI: 10.1080/14786441108564396.（Communication from the Research Staff of the General Electric Co., Wembley；由 C. C. Paterson 转交）
- 扫描件 7 页：PDF p.1 为 T&F 出版商封面（无印刷页码），PDF pp.2–7 = 印刷页 902–907。1927 年扫描件，OCR 多处把 θ 识作 ~、θ/2 识作 8，公式损处已标 [OCR损]。
- 注意：T&F 元数据把作者拼作 "Baetlett"（bib note 已核实系库方笔误，实为 Bartlett）；文章编号 LXXXIV。

## 核心命题（原文）
1. **特例表述——等分半段阻抗 = 全段短路/开路阻抗（p.902）**：
   > "of any artificial line section having input and output terminals T1 T2, T1' T2' has within it a pair of terminals ~1 ~T~t, so that it may be represunted, as in fig. 1, by two equal asymmetrical networks placed back to back, then, if the second half be removed, the impedance of the network remaining, measured at the terminals T1T2, is Z0tanh ~ if Tt' T~' be short-circuited, and Z0coth ~ if T11 T~' be open-circuited, where Z0 and 0 are the characteristic impedance and prop,gation constant of the artificial line section."
   （[OCR损]：两处 "~" 实为 θ/2，"prop,gation"=propagation。即：凡人工线节内部存在一对端子、可表示为**两个相等的不对称网络背靠背**，则去掉后半后，前半在平分端子**短路**下阻抗 = Z0·tanh(θ/2)、**开路**下 = Z0·coth(θ/2)——短路/开路半段阻抗之积 = Z0²。）
2. **一般定理 n 端子表述（p.903）——本文标题所指"推广"，也是 Bartlett 平分定理的首次刊出定型表述**：
   > "It will be shown that this is a special case of a more general theorem which may be stated thus:—If an artificial lille [OCR损, line] section has within it n terminals T1' T2' ... Tn', such that, if these terminals are open, the artificial line section is cat [OCR损, cut] into two exactly similar halves, the impedance of onehalf measured at th6 [OCR损, the] terminals T~ T~ with T1', T2'/ . . . T~/ free is Z0coth~, and with TI', T2' ... T~' all connected together is Zo tanh 2"
   （[OCR损]：末两式实为 Z0·coth(θ/2) 与 Z0·tanh(θ/2)。即：平分端子**全自由（开路）→ coth(θ/2)**、**全部连在一起（短接）→ tanh(θ/2)**。这正是现代偶/奇模（共模/差模）分解的古典源头：对称面开路 = 共模半电路，对称面短接 = 差模半电路。）
3. **定理证明基于轴对称行列式分解（pp.904–905）**：
   > "This determinant, which is partially centre-symmetric, can be simplified in the following way:—To the first row add the last row, to the second row add the last but one row, and similarly for the third and fourth rows. Next, in the resulting determinant:—From the last column subtract the first column, ..."（p.904）
   > "breaks up into the product of two other determinants giving A = 2~A'A ~' [OCR损，应为 A = 2^s·A'·A'']"（p.905）
   > "But / ~au is seen to be the impedance of the first half of the network of fig. 5 with all the terminals T~' T2' Ta' T4' connected together, while A" ... is the impedance of the same network with T1' T~I Ta/ T4t all free. Since their product is equal to Zo~ [OCR损, Z0²], ... may be written as Zotanh~ and Zocoth~-2 [OCR损, Z0·tanh(θ/2) 与 Z0·coth(θ/2)]"（p.905）
   （证明是纯代数的：轴对称（centre-symmetric）行列式可分解为两个行列式之积，恰对应两种平分端子状态的半网络阻抗；并引前文 "* (/. J. I. E. E. pp. 223-22' 6 Feb. 1927. Equation (20)" [OCR损, 应为 J.I.E.E.] 为依据。）
4. **证明完备性声明 + 四条系论（p.906）**：
   > "the theorem is proved for this case. The method, however, is quite general, and therefore the general theorem holds."（p.906）
   > "A number of simple corollaries follow for artificialline sections that can be bisected in the manner above:—1. An exactly equivalent bridge section can be constructed. 2. By making bridge sections in which for one pair of arms any ladder network made up of any numerical multiples of Z0 tanh ~ and Z0 coth ~ [OCR损, θ/2] is used, while for the other pair of arms the reciprocal of this network with respect to Zo is used, an indefinite number of bridge sections can be constructed having the same Zo as the original section hut [OCR损, but] different propagation constants."（p.906）
   （系论 1–2：任何可平分线节都有**精确等价的格形（bridge/lattice）节**——这是 Forte 1959 对称格形综合乃至全部对称滤波器设计的古典根据。）
5. **系论 3–4：在平分端子上插阻抗仍保持半边阻抗不变性（p.906）**：
   > "3. If the original section is modified by opening an)" [OCR损, any] "of the terminals TI', T2'... Tn' and inserting any series impedances, then, if Z01 [OCR损, Z0'] and 6' [OCR损, θ'] are the constants of the modified section, 6' [θ'] Zo coth ~ = Zo' coth ~ •"（即 Z0·coth(θ/2) = Z0'·coth(θ'/2)）
   > "4. If the original section is modified by connecting any pairs of the terminals TI', T s / . . . T,' by any impedances, then, if Z o' and 6' are the constants of the modified section, Zo tanh ~ = Z0' tanh ~-."（即 Z0·tanh(θ/2) = Z0'·tanh(θ'/2)）
   （注意：系论 3/4 的"修改"是**对称地**在平分端子处插/连阻抗——修改后网络仍可平分，定理不变性保持；**不是**两半失配。）
6. **三元件节算例 + 方法论价值（p.907）**：
   > "Thus for this artificial line section it can be seen from inspection that Z0 coth 2 = A + 2B, Z0tanh ~ = 1/(...) [OCR损，原式损，按图 6 三元件节可复原为 1/(1/A + C/2)] ... and therefore Z°~-- AC(A+2B) / (2A + C)." 
   > "This theorem for any artificial line to which it applies usually affords the simplest method of obtaining the constants in terms of the elements of the section."（p.907）
   > "From any artificial line section of the type considered, another can be derived by taking the two half-sections and connecting T~' of one half-section to T~' of the other half, T~' to T';,_~, etc. For this derived section the determinant A is completely centre-symmetric. The application, however, of the theorem that any centre-symmetric determinant is the product of two determinants does not appear to lead to any simple physica! [OCR损, physical] interpretation, though it does simplify the calculation of the constants."（p.907）

## 关键数值（原文）
- 本文为纯定理 + 电路代数证明，**无任何实测数值、无容差/失配统计**。仅有的"数值"是符号式：Z0·coth(θ/2) = A + 2B、Z0·tanh(θ/2) = 1/(1/A + C/2) [式 OCR 损，按上下文复原]、Z0² = AC(A+2B)/(2A+C)（p.907，fig.6 三元件节）；以及 Z0² = (短路半边阻抗)×(开路半边阻抗)（p.905）。

## 对 P1/P2/P3 的对照
- **P1（消去条件）**：**高（正交定位，非竞争）**。Bartlett 1927 给出的是**精确对称**网络 DM/CM 分解的原始定理——其全部前提是 "two **equal** asymmetrical networks placed back to back"（p.902）、"cut into two **exactly similar** halves"（p.903）。对称 ⇒ 平分端子开路半边（共模）与短接半边（差模）各自独立、行为完全解耦。P1 所问的恰是**破坏这一前提后**（元件失配 ⇒ H_N ≠ H_P ⇒ G_DC ≠ 0）共模→差模转换的条件：Bartlett 定理在"两半相等"处止步，失配摄动是其定理域之外的第一步。P1 定位为"失配摄动伴随"与原文完全自洽。
- **P2（Kelvin 结构地板 ≈56 dB）**：**无**。1927 年文无 CMRR 概念、无任何 dB 数值；其"对称即完全解耦"的理想结论恰是 P2 要用失配统计打破的零级模型。
- **P3（平坦度约束衰减上界）**：**无**。不涉及幅频响应/衰减与平坦度约束。
- **方法学（D1–D10）**：**中**。示范了"从几何/结构对称性（centre-symmetric determinant）推出精确电路不变量"的古典范式——P1 把同一对称性当作零阶基准、再对破坏项做一阶展开，方法论上是同一谱系的延伸；系论 1–2（等价格形节）是后续对称格形综合（Forte 1959 / Weinberg）的出典。
- **killRisk 判断：无**。全文无一处触及"对称性破坏/失配 → 共模差模转换的条件"；最接近的表述也仅是系论 3–4 的"对称修改不改变半边阻抗"（p.906），方向恰好相反（强调不变性保持而非破坏后果）。对 P1 不构成任何优先权/重合威胁，反而是 P1 引用的正统源头。

## 没读到的
- 1930 年成书 *The Theory of Electrical Artificial Lines and Filters* §15（定型表述）、§16–17（格形节）、Ch.V（Line Balances §34–37）中的扩展与线平衡内容——本文只有 1927 首刊的 6 页正文（bib 另有 bartlett1930bisection 条目待读）。
- p.904 行列式 A 的完整 7×7 排版与 p.905 A'、A'' 子行列式的完整元素表（OCR 基本全损，只能确认结构：A = 2^s·A'·A'' 与 Δa11/Δall 型阻抗表示）；如需逐元素核对须回看扫描图。
- p.902 顶部的上一篇文章通信（Dubois/Taylor 火花电位讨论）与本文无关，未读。
- 本文引用的前作 "J.I.E.E. pp. 223–22?, Feb. 1927, Equation (20)"（[OCR损] 页码末位不清）未取。
