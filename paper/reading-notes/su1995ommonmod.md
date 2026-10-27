# 精读笔记 · Su 1995《Common-Mode Rejection Ratio in Current-Mode Instrumentation Amplifiers》（Analog Integrated Circuits and Signal Processing, 7:257–260）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。

## 出处
- W. J. Su and F. J. Lidgey, "Common-Mode Rejection Ratio in Current-Mode Instrumentation Amplifiers," *Analog Integrated Circuits and Signal Processing*, vol. 7, pp. 257–260, 1995. DOI: 10.1007/bf01250805. Oxford Brookes University（Analog Devices-PMI 资助）。
- 扫描件 4 页，PDF pp.1–4 = 印刷页 257–260。OCR 把下标/希腊字母搞乱（α→"o/"或"cq"、λ→"~-"/")~"），受损处标 [OCR损] 并按上下文复原。

## 核心命题（原文）
1. **命题定位：CMIA 的 CMRR 由有源器件参数失配决定（p.257, Abstract）**：
   > "The CMIA is studied in detail and the CMRR expression is derived in terms of op-amp and transistor parameters. A good CMRR is shown to depend upon several factors, including the power-supply rejection ratio of the op-amps used in the CMIA."
   > （同页引言）"Current-mode instrumentation amplifiers (CMIAs) feature high CMRR without requiring well matched resistors [1,2]. ... The CMIA has a balanced structure which is relative parasitic insensitive, and the rejection to the input common-mode voltage mainly takes place in the voltage to current converter..."
2. **DM/CM 分解 + 交叉跨导矩阵——失配→共模差模转换的显式框架（p.257，式 (1)(2)）**：
   > "The input voltages V1 and V2, and the output currents I01 and I02 of the input stage can be separated into differential mode and common-mode components and can be expressed as, I01 − I02 = gdd·Vid + gdc·Vic; Ioc = (I01 + I02)/2 = gcd·Vid + gcc·Vic (2) where Vid and Vic are the input differential and common-mode voltages respectively, gdd and gcc are the differential and common-mode transconductance respectively, gcd is the differential to common-mode transconductance, and gac [OCR损, gdc 之排印] is the common mode to differential-mode transconductance."
   （2×2 跨导矩阵含非对角项 gdc（CM→DM）：这就是 P1 的 G_DC 在有源电路里的对应物；P1 的「失配→G_DC≠0」在此被显式参数化。）
3. **失配项被逐项归因（p.258）**：
   > "Assuming the input is common-mode voltage only, then the output current I01 and I02 comprise two components. One is the current Ioc1 which is induced by the mismatching between OA1 and OA2 and is approximately equal to the current through R1."
   （式 (9)(10)：I01 ≈ Ioc1 + (λ1−λ2)Is1，I02 ≈ −Ioc1 + (λ11−λ22)Is2 [OCR损，λ 系电流镜传输比]。）
4. **gdc 显式含失配差与 psrr 差（p.259，式 (11)）**：
   > "the parameters gdc and gcc are given by [式 (11)，OCR 多处损] gdc = Id/Vic|Vid=0 = (I01 − I02)/2Vic ≈ [α1(λ1−λ2)(1+sC1r1)⁻¹ ... − α2(λ11−λ22)(1+sC2r2)⁻¹ ... + psrr 项] ..."（原式排版复杂、OCR 大面积损，可靠可引的部分：分子只含差值项 (α1R1−α2)...、(λ1−λ2)、(λ11−λ22)、psrr1/psrr2 差项 [OCR损]）
   （结构上：每个失配差项 ×(1+sCiri)⁻¹ 频率因子——失配→CM-DM 转换是**频变的**，寄生 Ciri 使 gdc 随频率上升。）
5. **匹配条件组——"满足哪些等式可消掉失配通道"（p.259）**：
   > "we can assume the balancing condition α3R2 = α4R22 is met and the CMRR in (3) reduces to gdd/gac [gdd/gdc]. Based on this, we can obtain one set of the matching conditions, namely α1 = α2 (13a), λ1 − λ2 = λ11 − λ22 (13b)[(13c)], r1 = r2 (13d). The condition that λ1 − λ2 should be equal to λ11 − λ22 is easier to obtain in practice than λ1 to be directly equal to λ2."
   （**这是本文最接近 P1「消去条件」的表述**：给出一组等式（13a–d），满足则失配驱动的 gdc 分量相消、CMRR → gdd/gdc。但这是**元件参数恒等式**（直流/参数域匹配），不是 P1 那种**传递函数域全频段**充要条件，也没有多级结构"不再充分"的问题。）
6. **结构地板论——CMRR 不可能无穷（p.259）★最接近 P2 的表述**：
   > "Both psrr1 and psrr2 are statistic variables and the matching condition between the psrrs is impossible to realize, which means the CMRR cannot be infinite."
   （**killRisk 级接近**：与 P2「Kelvin 结构地板 ≈56 dB」同型论证——存在**统计性不可匹配参数**⇒匹配条件永远差一项⇒CMRR 有与失配统计绑定的上限。区别：Su 的地板来自有源器件 psrr 统计，且**未给数值地板**、未做灵敏度传播定量模型。）
7. **结论重申 + 频率行为（p.260）**：
   > "Unlike the conventional 3-op-amp instrumentation amplifiers, the CMRR in CMIAs is still finite even if all of the matching conditions are met. A good CMRR mainly depends on the matching conditions between the implementing devices including the op-amps and the current-mirrors, but not as critically on the device performance."
   > （p.259）"Fig. 3 shows that although the psrr of the op-amps has less effects on the CMRR at low frequencies than the mismatching between α1 and α2, it introduces a low pole to the CMRR and has the same effects as (α1 − α2) at higher frequencies."
   （psrr 失配给 CMRR 引入**低频极点**——CMRR 随滚降；与 P3 的"衰减-平坦度频域折衷"不同向，但同为频率结构约束。）

## 关键数值（原文）
- 仿真/计算条件（p.259, Examples）：741 运放；Fig.2(a)：α1−α2 = 1 ppm，Ad1 = 10⁵，Ad2 = 5.24×10⁵，cmrr1 = 10⁴，cmrr2 = 1.1×10⁴；Fig.2(b)：α1−α2 = 10 ppm，Ad1 = 2.3×10⁵，cmrr1 = 4.4×10⁴，cmrr2 = 1.02×10⁵；公共：R1 = 2 k，R2 = R22 = 10 k，λ1−λ2 = λ11−λ22 = 20 ppm，C1 = C2，r1 = r2。
- Fig.3：λ1−λ2 = λ11−λ22 = 20 ppm，α1−α2 < 10⁻⁹，|psrr1|⁻¹−|psrr2|⁻¹ = 800 ppm，其中 |psrr1| = 10³，|psrr2| = 5×10³。
- 定律性结论（p.259）："the CMRR is proportional to 1/(α1 − α2)"。
- Fig.2/3 纵轴刻度 OCR 可见 20–120 dB / 40–140 dB（具体曲线读数图上量取，文本未给数）。

## 对 P1/P2/P3 的对照
- **P1（消去条件）**：**高（同族异构）**。Su 的式 (2) 交叉跨导分解与 P1 的 G_DC = H_N − H_P 同一形式；式 (13a–d) 给出"哪些参数相等⇒失配通道消去"的**参数域**匹配条件。差异（P1 的护城河）：① Su 条件是无源/有源**参数恒等式**，不含复频率 s，未处理"全频段精确消去"；② 无多级级联（梯形）情形；③ 无充要性证明（只给"一组"充分性匹配条件，未证必要）。P1 的"单级 τ=R·C 充要、多级不再充分"命题不受触碰。
- **P2（Kelvin 结构地板）**：**高（同型论证，异源异值）**。"psrr 统计不可匹配 ⇒ CMRR cannot be infinite"（p.259）与 P2 的"结构地板"同型；但 Su 的地板由**有源器件 psrr 统计**产生、无数值、无传播公式，P2 的 ≈56 dB 地板来自 Kelvin 无源结构失配统计——数值与机构均不同，P2 增量仍成立，但**写作时应在 P2 相关工作里点名 Su 1995 的这句**，作为"统计不可匹配⇒CMRR 有地板"思想的先例。
- **P3（平坦度约束衰减上界）**：**低**。仅有"psrr 失配引入低频极点"（p.259）这一频域退化观察，无衰减/平坦度折衷。
- **方法学（D1–D10）**：**中**。示范了"把 CMRR 拆到器件参数级、逐失配源归因、再给匹配条件组"的分析流程；其"匹配条件应写成**差值相等**（λ1−λ2 = λ11−λ22）而非逐项相等更易实现"（p.259）对 D 系列门槛化判据有直接启发（差值配对放宽条件的思想）。
- **killRisk 判断：低**（对 P2 有思想先例压力，无数值/机构重合；对 P1 无充要条件/无多级问题、无全频段条件，无实质威胁）。最接近表述已逐字引于核心命题 5、6。建议 P1/P2 论文相关工作节引用并划清：参数域匹配组 vs 传递函数域全频段充要条件；有源 psrr 统计地板 vs 无源 Kelvin 结构失配地板。

## 没读到的
- 式 (3)（CMIA 总 CMRR 表达式）与式 (11)(12) 的完整排版（OCR 严重损毁，只可靠引出分子为差值项的结构性结论）；具体曲线值（Fig.2/3 图中读数）。
- 引文 [1] Toumazou–Lidgey 1989、[2] Zhu–Lidgey–Su 1993、[3] Smither 1977、[4] Pallas-Areny–Webster 1991（H2 谱系另有 pallasareny1991cmrr 待读）、[5] Su 等 1994 未读。
- 本文只分析两级 CMIA 一种拓扑；其对偶/推广（如第二代 CMIA）在引文 [2]，未读。
