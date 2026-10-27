# 精读笔记 · Koide 1997《Common-Mode Rejection Ratio Redefined》（IEEE Trans. Instrum. Meas., 46(3):737–739, Correspondence）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。

## 出处
- F. T. Koide, "Common-Mode Rejection Ratio Redefined," *IEEE Transactions on Instrumentation and Measurement*, vol. 46, no. 3, pp. 737–739, June 1997（Correspondence 栏）。DOI: 10.1109/19.585444. 1995-04-30 投稿、1997-02-11 修回；University of Hawaii。
- 扫描件 3 页，PDF pp.1–3 = 印刷页 737–739。OCR 把负号"−"大量识作"0"、把数字吃成":"，公式与例题数值多处受损，标 [OCR损] 并按代数自洽复原（复原处均已注明，不确定者标待核）。

## 核心命题（原文）
1. **总命题：把相位并入 CMRR 定义后，电路 CMR 可超过器件 CMR——靠故意失配（p.737, Abstract）**：
   > "Redefining the common-mode rejection ratio (CMRR), a set of equations is derived for the common-mode gain and the CMRR of differential amplifiers. The results, which are consistent with practice and simulation, show that an amplifier's CMR may exceed the CMR of the active device(s) by intentional unbalancing of the circuit."
2. **经典公式的局限：只取幅值 ⇒ CMRR ≤ min(CMRRr, CMRRd)（p.737）**：
   > "In op-amps, the common-mode rejection ratio (CMRR) is the result of the device's CMRR, CMRRd, and the CMRR due to the passive components external to the device, or CMRRr as defined by the following equation [1], [2]: CMRR = CMRRr·CMRRd/(CMRRr + CMRRd) (1). According to the classical definition of CMRR, CMRRd and CMRRr are both positive quantities and the CMRR is at best equal to the lesser of the two rejection figures."
   > "In actual practice it is known that the CMRR can exceed the device's CMRR, however. Instead of tweaking the resistors for maximum CMRRr, the resistance ratio is slightly unbalanced such that CMRRr = [OCR损，按式(8)应为 CMRRr ≈ CMRR'd 之复数相等]. The inconsistency is resolved by not restricting the definition of CMRR to magnitude only."
   （经典和式（Garrett 1981、Pallas-Areny & Webster 1991）与实测矛盾；解法 = CMRR 用**复数增益比**（含相角）定义。）
3. **★新公式：分母是两个复数 CMRR 之差——精确零点的来源（p.737，式 (8)）**：
   > "Rewriting (5), the amplifier's common-mode rejection ratio is CMRR = CMRRr·CMRR0d [CMRR'd] / (CMRR0d [CMRR'd] 0 [OCR损,−] CMRRr) (8) ... Compare (8) with (1). When CMRRd0 [CMRR'd] ≈ CMRRr the amplifier's CMR exceeds the device's common-mode rejection, the result of defining the CMRR as the ratio of the complex differential to common-mode gains (5)–(7) and not as a ratio of just the magnitudes."
   （**与 P1 的 G_DC = H_N − H_P 同一数学结构**：总 CM 增益是两个复数贡献之**差**；当外电阻比值产生的 CMRRr 与器件 CMRR'd 复数相等时，差→0、总 CMRR→∞。P1 的消去条件是"参数匹配使差恒为零"，Koide 的消去条件是"可调电阻比使两复数贡献相消"——一个是结构对称问题、一个是桥式调零问题，但"差→零即消去"的核心机制相同。）
4. **消去条件的显式解（p.737–738，式 (10)(11)）**：
   > "To maximize the CMRR for real devices, let Acm ... = 0. From (4), (1 + R2/R1)(R4/R3) = (1 + 2/CMRRd)(R4/R3) [OCR损，结构如左] (10), or r = [OCR损，式 (11) 排印全损，按例题反推为 r ≈ 1 − 1/((1+R2/R1)·CMRR'd) 型的微失配解]"
   （令总共模增益 = 0 解出所需电阻比 r = R4/R3——一个**显式消去条件**，但为纯阻网络、单一（低频）点，非全频段。）
5. **★级联复合：多级 CMRR 不再是简单乘积（p.738，式 (18)(19)）——与 P1"多级不再充分"同型**：
   > "CMRR = CMRR1·CMRR2 + CMRR'1 [式 (18) 的近似形：1/CMRR ≈ 1/(CMRR1·CMRR2) + 1/CMRR'1，OCR损]. It should be noted that CMRR = CMRR1·CMRR2 only if CMRR'1 >> CMRR1·CMRR2, or Acma ≈ Acmb."
   > "D. Maximum CMRR: The amplifier's CMRR is maximized by equating the right side of (18) to zero. Therefore, let CMRR2 = 0 [OCR损,−] 1/(CMRR1·CMRR'1) (19)."
   > （3 运放仪放）"Since there is always a small but finite imbalance in the common-mode gains of the first stage, however, the conclusion from the analysis is that the second stage should be adjusted not in isolation but coupled to the first stage with a common-mode voltage applied to the input of the first stage; a standard procedure."
   （级联引入**附加泄漏项 1/CMRR'1**（第一级共模→共模路径），总 CMRR 由乘积项与泄漏项**相加**——要消去须让第二级取特定（负/反相）值抵消第一级泄漏：这正是"多级系统中单级匹配不再充分、须联合调零"的有源版先例。）
6. **结论（p.739）**：
   > "The study shows that, by redefining the common-mode rejection ratio to include the phase angle, the theoretically derived CMRR is consistent with practice and simulation; that an amplifier's CMR may exceed the CMR of the device(s) or the external components. The improved CMR is achieved by the unbalancing of the components external to the device."

## 关键数值（原文）
- 数值例题（p.738, Example，多数数字被 OCR 吃掉 [OCR损]，可自洽复原的）：差分增益 R2/R1 = 99；CMRR'd = 31500（≈90 dB）；所需电阻比失配 0.3%（r 使 R4/R3 比 1.00301）；结果总 CMR = 114 dB，"which exceeds the device's CMR by 24 dB"（原文可引）。
- 实验（p.739）：LM747CN，平衡电阻 r = 1，差分增益 500，10 Hz 实测共模增益 7.00×10⁻³ V/V [OCR损，由 500/(7.00×10⁻³) = 71430 复原]，CMRRd = 71430 = 97.07 dB，"which agrees with the published data"；调 R4 故意失配到总共模增益极小后，"the common-mode gain decreases to :×10⁻⁴ [OCR损] ... or a CMR of 115.1 dB, an improvement of 18.0 dB over the device's common-mode rejection"（115.1 与 18.0 dB 为原文可引数）；理论 r = 0.993，"The measured R4 is equal to the expected theoretical value"。
- 所有数值均为**低频单点**（10 Hz 量测），无频率扫描数据。

## 对 P1/P2/P3 的对照
- **P1（消去条件）**：**高（机制先例，域不同）**。Koide 的三点与 P1 深度共鸣：① CMRR 必须按**复数增益比**（含相角）定义，幅值定义会掩盖"差→零"的消去点（p.737）——与 P1 把 G_DC 当复频函数 s 的差来处理同立场；② 分母取差（式 8）⇒ 存在**精确零点**（CMRRr = CMRR'd 时总 CMRR→∞）——一个显式、可解（式 10–11）、实验证实（115.1 dB > 97.07 dB）的**调零型消去条件**；③ 级联式 (18) 表明**多级复合时出现附加泄漏项、乘积关系失效**，单级独立调整不再充分、须耦合调零（p.738）——P1"单级 τ 匹配充要、多级梯形不再充分"在有源级联域的先例。**P1 未被杀**：Koide 全部为纯阻网络 + 低频单点复数相等，无 τ=R·C 频率结构、无全频段恒等要求、无充要性定理、无无源梯形；但 P1 写作必须在"复数消去 + 多级失效"谱系里引 Koide 并划清（阻性调零 vs 频变 τ 匹配充要条件）。
- **P2（Kelvin 结构地板）**：**中**。"CMR may exceed the CMR of the active device(s)" 表明地板可被**主动调零推低**——对 P2"结构地板 ≈56 dB"是重要对照：P2 的地板若来自**随机失配统计**（不可调），Koide 的增益来自**可调元件的确定性补偿**；二者兼容（调零是对统计地板的工程对策），但 P2 需要说明"调零后地板由什么决定"（残余漂移/温漂——Koide 未讨论）。
- **P3（平坦度约束衰减上界）**：**无**。纯共模增益分析，无衰减-平坦度内容。
- **方法学（D1–D10）**：**中-高**。"指标定义本身错了会导致设计目标错"（幅值 CMRR 定义隐藏消去点）是 D 系门槛化方法学的经典案例：判据必须是复数/全频段量，标量幅值判据会系统性错过最优解；级联"耦合调零而非孤立调零"（p.738）是 D 系多级联合判据的直接先例。
- **killRisk 判断：中**。最接近表述 = 核心命题 3（复数差分母 + 精确零点）与 5（级联泄漏项 + 耦合调零）。不含 P1 的充要条件定理、τ 频率结构、全频段恒等、无源梯形多级问题——不构成证伪，但**属 P1 相关工作必须引用并划界的最近邻**（比 Su 1995 更近：Koide 直接讨论"消去条件"本身）。

## 没读到的
- 式 (3)–(7)、(10)–(20) 的完整排版（OCR 负号→"0"、数字→":"，式 (11)(17)(19) 全损）；例题与实验中被吃掉的阻值（R1–R4 具体千欧值、Acm 极小值的具体数字）——已用代数自洽复原处均标 [OCR损]，未能复原处标待核。
- Fig. 1（单运放差分放大器）、Fig. 2（差分入差分出放大器）、Fig. 3（两级差分放大器）的电路图细节（不进 OCR）。
- 引文 [1] Garrett 1981 教材、[2] Pallas-Areny & Webster 1991（库中 pallasareny1991cmrr.pdf 待读）未读；末尾另附 Papay 更正启事一则，与本文无关。
