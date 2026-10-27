# 精读笔记 · Forte 1959《A New Synthesis Procedure for Two-Terminal-Pair Networks Using the Symmetrical Lattice Structure》（Proc. IEE Part C: Monographs, No.326 R, 106(9):112–114）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。

## 出处
- S. S. Forte, "A New Synthesis Procedure for Two-Terminal-Pair Networks Using the Symmetrical Lattice Structure," IEE Monograph No. 326 R, Jan. 1959, *Proceedings of the IEE Part C: Monographs*, vol. 106, no. 9, p. 112（bib 页码 112，实占印刷页 112–114）。DOI: 10.1049/pi-c.1959.0019.
- 1955-11-26 首投、1958-11-10 终稿；作者时在 Marconi's Wireless Telegraph Co., Ltd.；系 Leeds 大学 1955 年博士论文一部分。
- 扫描件 3 页：PDF pp.1–3 = 印刷页 [112]、113、114。OCR 中等质量，公式下标与个别分式结构受损处标 [OCR损]。

## 核心命题（原文）
1. **本文目标——无理想变压器的对称格形综合充要条件（p.112, SUMMARY）**：
   > "A new synthesis procedure for the realization of 2-terminal-pair networks without ideal transformers is given. A new theorem is formulated concerning the necessary and sufficient conditions to be satisfied by a prescribed set of impedance or admittance functions for it to be realized as a symmetrical lattice network with series impedances (or shunt admittances) at either end of the structure, without ideal transformers."
   （为给定 z 矩阵给出"能否实现为对称格形 + 两端串臂/并臂"的**充要条件**，避免 Gewertz 综合中的理想变压器。）
2. **从非对称函数集到对称格形的路线：先提取端部串联阻抗/并联导纳（p.112）**：
   > "In order to realize a symmetrical network from an unsymmetrical set of functions, it is necessary to extract series impedances in the case of an impedance family, or shunt admittances in the case of an admittance family, at either end of the network, so that the resultant set of functions is symmetrical."
   （注意：这里的"unsymmetrical"指**端口函数集不对称**（z11 ≠ z22），靠端部提取元件把它补成对称——这是综合前的补偿手段，不是对"格形两臂失配后果"的分析。）
3. **格形实现的必要条件（p.112，式 (2)–(4)）**：
   > "necessary conditions for the realization of the lattice are ± [OCR损，据 p.113 定理可复原为 z11 ± z12 与 z22 ± z12] must be p.r. ... This implies that, for all real frequencies, to [ω], ± [OCR损] 0 (3) and that at any pole on the boundary the residues satisfy Pn ±Pn > 0 [OCR损，应为 μ11 ± μ12 > 0], P22 ±Pl2>0 (4)"
   （格形四臂阻抗 = z11 ± z12、z22 ± z12，故它们必须正实（p.r.）；边界极点留数同号。这组条件是"±格形臂函数必须 p.r."的原始形式。）
4. **新定理（p.113）——本文核心贡献，充要条件**：
   > "Theorem.—The necessary and sufficient conditions for a set of driving-point and transfer impedance or admittance functions /11 /22 and/12 [OCR损, f11, f22, f12] to be realizable as a 2-terminal pair network without ideal transformers, consisting of a symmetrical lattice network with series reactances or shunt susceptances at either end of the structure, are /11 ±/12 [f11 ± f12] must be p.r., /22 ± /12 [f22 ± f12] must be p.r."
   （对"任意给定 z/y 矩阵 → 端部加串臂/并臂的对称格形（无理想变压器）"给出充要条件：两组和差函数都 p.r.。证明思路：任选辅助函数 Z（其实部 R 满足 r11−R>0, r22−R>0, R−r12>0, R+r12>0，式 (5)），即 R 介于曲线族之间，p.113 式 (6)：|r12| ≤ R ≤ min(r11, r22) 型上下界。）
5. **R 的存在性构造（p.113，式 (6)）**：
   > "a value of R can always be found to lead to a realizable network if, for all real frequencies, (6) [OCR损，式本身排印损；按上下文为 |r12| ≤ R ≤ r11 且 R ≤ r22 的联立不等式] where |r 12 | is defined as the magnitude of rl2 over the frequency range."
   > "After plotting r, j [r11], r22 and |rX2| as functions of to2 [ω²], the arbitrary function R can be represented by any curve lying between the limits given by conditions (6), and can be determined as a rational function of to2 by any suitable method of approximation."
   （用图解带（Fig. 2）在 r11、r22、|r12| 三条曲线之间选 R(ω²)，再经 Gewertz 法还原 p.r. 函数 Z，边界极点按 pz = |p12| 添加使留数条件 (7) 满足。）
6. **元件级收尾——Bott–Duffin 去互感（p.113, CONCLUSION）**：
   > "A new synthesis procedure has been described for prescribed impedance or admittance matrices, leading to a realizable structure without ideal transformers. Use of the Bott and Duffin synthesis procedure, for example, for the driving-point impedances of the component branches of the structure will lead finally to a realization entirely free of mutual coupling."

## 关键数值（原文）
- 数值算例（p.113–114）：给定
  z11 = (6λ³+15λ²+15λ+6)/(λ²+2λ+2)，z22 = (9λ³+24λ²+24λ+3)/(λ²+2λ+2)，z12 = (4λ³+10λ²+10λ−2)/(λ²+2λ+2)；
  实部 r11 = (3ω⁴−6ω²+12)/(ω⁴+4)，r22 = 12/(ω⁴+4) [OCR损，r12 = (2ω⁴+2ω²−4)/(ω⁴+4)]；
  选 R(ω²) = 6/(ω⁴+4)（p.114，Fig. 2 虚线，落在带内）；
  Z' = 3(7λ²+7λ+8)/(8λ²+2λ+2) [OCR损，结构如左]，唯一边界极点按 pz = |p12| = 4λ 添加；组件二端网络 Z3、Z4 之分式见 p.114（OCR 部分受损），"Z{-Z4 are readily shown to be p.r. functions"（应为 Z3 − Z4 或 Z3、Z4 皆 p.r.，[OCR损]）。
- 全文**无失配/容差/灵敏度数值**——纯精确综合。

## 对 P1/P2/P3 的对照
- **P1（消去条件）**：**中**。本文与 P1 共享"**充要条件**"的表述范式（necessary and sufficient conditions 反复出现），且格形结构正是 P1 所论对称差分结构的原型——格形的 CM 抑制完全依赖两对臂精确相等（Bartlett 系论 2 的"等价格形节"）。但本文条件是**可实现性**充要条件（f11±f12 p.r.），不是**消去/CMRR**充要条件；全文在"精确对称"前提下综合，未触碰失配。P1 的"单级 τ 匹配充要、多级梯形不再充分"与之互补：P1 问的是同一结构**做坏了**会怎样。
- **P2（Kelvin 结构地板）**：**无**。无 CMRR 数值、无结构地板概念。
- **P3（平坦度约束衰减上界）**：**无**。不涉及衰减函数与平坦度折衷。
- **方法学（D1–D10）**：**低-中**。可借鉴的是"先判充要条件、再动手综合"的门控流程（SUMMARY 明言 "readily applied ... to determine whether or not a realizable solution exists, before any lengthy computation need be undertaken"）——与 P1 用充要条件判"能否精确消去"的方法学姿态同构。
- **killRisk 判断：无**。全文无对称性破坏→共模差模转换的任何表述；最接近的只有"从非对称函数集提取端部元件凑成对称"（p.112），方向是**修复**不对称而非分析不对称后果，与 P1 命题不重合。

## 没读到的
- Fig. 1（2-terminal-pair schematic）与 Fig. 2（r11/r22/|r12| 曲线带）为图，OCR 不出曲线细节；式 (3)、(6) 排印在 OCR 中损毁，我按上下文复原并已标注 [OCR损]。
- Gewertz 1933、Darlington 1939、Fialkow–Gerst 1954、Talbot 1953、Weinberg 1953、Bott–Duffin 各引文原文未读（Bott–Duffin 年份印刷为 1929，疑为 1949 之误——待核，不改动原文）。
- Forte 1955 Leeds 博士论文（引文 7）未取。
- bib 注明本文只有 1 页（p.112），实际扫描件含算例两页（113–114），已在出处节说明。
