# 精读笔记 · Bockelman & Eisenstadt 1995《Combined Differential and Common-Mode Scattering Parameters: Theory and Simulation》（IEEE Trans. MTT 43(7):1530–1539）【killRisk 必对照】
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。

## 出处
- Bockelman, D.E.; Eisenstadt, W.R., "Combined Differential and Common-Mode Scattering Parameters: Theory and Simulation," *IEEE Transactions on Microwave Theory and Techniques*, vol. 43, no. 7, pp. 1530–1539, Jul. 1995. DOI: 10.1109/22.392911。
- PDF：`fulltext/H2-差分CMRR/bockelman1995mixed.pdf`（10 页）。bibkey：`bockelman1995mixed`。
- 主题：**混模 S 参数理论的原始文献**——把二端口差分电路的 4×4 S 矩阵划分为差模（Sdd）、共模（Scc）与**模式转换/交叉模（Sdc、Scd）**四个子块；给出测量系统实现（180°/0° 功分 + 标准 VNA 结点波换算）与对称/不对称耦合微带线仿真。killRisk 登记：**只量化"转多少"、不给"何时恒零"——P1 的正面划界对象**。

## 核心命题（原文）
1. **混模 S 参数四分块的形式化定义（CM↔DM 转换的度量衡）**（p.1533）：
   > "The following names are used: Call [Sdd] the differential s-parameters, [Scc] the common-mode s-parameters, and [Sdc] and [Scd] the mode-conversion or cross-mode s-parameters. In particular, [Sdc] describes the conversion of common-mode waves into differential-mode waves, and [Scd] describes the conversion of differential-mode waves into common-mode waves. These four partitions are analogues to four transfer gains (Acc, Add, Acd, Adc) introduced by Middlebrook [2]."
   （这正是 killRisk 登记的核心：**定义了转换的度量**（转多少），并自认承继 Middlebrook 的四个传输增益；**全文没有一处给出"Scd/Sdc 何时恒等于零"的一般条件定理**。）
2. **消去（零转换）在文中唯一出现的形式 = 结构对称的观测性陈述，非定理、非元件条件**（p.1535, 仿真一）：
   > "Note the cross-mode s-parameters are zero for the symmetric coupled pair indicating no conversion between propagation modes."
   （仅针对"等宽对称耦合线"这一**几何对称**情形的仿真观察（式 27 中 Sdc=Scd=0）；既无必要性论证，也无推广到一般网络/集总梯形的"充要条件"。这是全文**最接近 P1 空缺主张的表述**，P1 论文划界时必须逐字引用并区分：对称（结构性条件，分布参数耦合线）≠ 元件值匹配（P1 的 τ=R·C 类条件，集总梯形）。）
3. **不对称 ⇒ 转换非零且随频率增大（只量化、不消去）**（p.1536）：
   > "shows significant conversion between propagation modes, particularly in transmission parameters Sdc21 and Scd21. Note these two sub-matrices are equal indicating equal conversion from differential to common-mode and from common to differential-mode."
   > "Mode conversion accounts for the remaining reduction in the differential-mode, and hence Sdd21 is reduced."（p.1536）
   > "This is consistent with the increasing ripple in Sdd21 with increasing frequency since the mode conversion (Sdc21 and Scd11) increases with frequency."（p.1537）
4. **模式转换的损耗归因分解式（定量归因的样板）**（p.1537, 式 29）：
   > "In a low loss transmission line case, the insertion loss due to mode conversion and miss-match can be shown to be approximately  LOSS (dB) M -1olOg[l - ((Sddll(' +  |S~d21(~(Scdll12)].   (29)"
   （插入损耗 = 反射 + DM→CM 传输 + DM→CM 反射三通道的能量守恒分解——把"转多少"精确记账；但仍是量化，不是消去条件。）
5. **测量系统的模式生成/重构误差 = 幅相不平衡（增量方法学的测不准项）**（p.1535）：
   > "any successful calibration algorithm must correct both magnitude and phase imbalances in the splitterkombiners and signal paths, since any such imbalances will represent errors in the generation and reconstruction of the mixed-mode waves."
   （与 Huhta 1973 的"两缓冲增益失配即新干扰源"同构：测量机构的失配本身产生伪转换。）
6. **混模波可由非耦合参考线测量（Ze=Zo=Z0 特例）**（p.1534）：
   > "Enforcing equal even and odd-mode Characteristic impedances is equivalent to the conditions of uncoupled transmission lines. As has been shown in the literature [7], the condition Z, = 2, results in the mutual impedances and admittances being zero (2, = 0, ym = 0)."（p.1534）
   > "A special case of the theory allows the use of uncoupled transmission lines to measure the coupled-mode waves."（Abstract, p.1530）
   （测量可行性条件，非消去条件。）

## 关键数值（原文）
- 仿真一（对称耦合微带，p.1535）：线宽 100 µm/间距 100 µm、25 mil 氧化铝基板 εr=9.6、tanδ=0.001、铜电导 ~5.8×10⁷ S/m、长 1 英寸、5 GHz。混模 S 矩阵（式 27）：Sdd11=0.001∠−141°、Sdd21=0.972∠9.53°、**Sdc=Scd=0**、Scc11=0.341∠−60.4°、Scc21=0.915∠−26.4°。奇模阻抗 50 Ω（差模 100 Ω），偶模 140 Ω（共模 70 Ω）。
- 仿真二（不对称，p.1535–1536）：线宽 100 µm 与 170 µm、间距 65 µm、余同上。式 28 @5 GHz：**|Sdc21|=|Scd21|=0.031∠80.7°**（≈−30.2 dB）、Scd11=0.005∠−177°、Scc11=0.502∠48°、Scc21=0.844∠−40.2°、Sdd21=0.956∠1.8°。奇模 ~49 Ω，偶模 152 Ω。
- 频率行为（1–21 GHz, Figs. 7–10, p.1536–1537）：Scc21 纹波示共模端口失配；Sdd21 纹波最大 0.2 dB；差模回损 >20 dB（对应最坏 ~0.04 dB 损耗），其余差额归于模式转换；Sdd21 的极小值与 Sdd21/Scd11/Scd21 相对相位最坏点对应（p.1537）。
- 测量条件：低损耗 + 偶/奇模特性阻抗相等（=50 Ω）⇒ 非耦合参考线；180°（差模）/0°（共模）3 dB 混合环激励（pp.1534–1535）。

## 对 P1/P2/P3 的对照
- **P1（消去条件）**：相关度 **高**（作为**正面划界对象**，非撞车）。killRisk 登记核实成立：
  ① 全文给出的是 CM↔DM 转换的**度量与记账**（Sdc/Scd + 式 29 能量分解），不含"何时恒零"的一般条件；
  ② 唯一"零转换"表述是对称耦合线的**结构对称观测**（p.1535，逐字已录），属分布参数几何对称，不是集总元件值条件，更不是多级网络充要性；
  ③ 对象是耦合传输线/微波结构，非集总多级无源梯形滤波器，无 H_N−H_P 传递函数差的表达；
  ④ 无"单级充分/多级不充分"的任何命题。
  **P1 引用策略**：作为"转换可测、可量化"的奠基引文，然后划界——Bockelman 回答 *how much*，P1 回答 *when exactly zero*（含多级充要性）；注意其对称性零转换观测应被 P1 纳入"结构性消去"类（与 Blumlein 变压器比例臂同类：用结构而非匹配），与 P1 的"匹配型消去"并列。
- **P2（Kelvin 结构地板）**：相关度 **低**。无开尔文/四线内容；但其"测量机构不平衡会产生伪模式转换"（校准段, p.1535）与 P2 的"结构地板=测量结构自身残余"在思想上同型。
- **P3（平坦度约束下衰减可达上界）**：相关度 **无**。无滤波器综合/积分约束。
- **方法学（增量四 D1–D10）**：相关度 **低-中**。式(29) 的"反射+转换"能量归因分解、以及"纹波极小值对应三参数相对相位最坏点"的相位敏感观测，是**归因分解**的好样板；但无增量实验设计。
- **killRisk 判断**：**维持登记结论 = 须划界，非撞车**。本精读未发现任何"多级无源网络全频段精确消去条件"的表述或逼近；最接近表述已逐字锁定（p.1535 对称耦合线零转换 + p.1533 四分块定义），均不构成对 P1 空缺主张的覆盖。**风险等级不升级**。

## 没读到的
- 一般网络的 Sdc≡0 充要条件（全文不存在——这正是 P1 的空间）。
- 集总元件网络/滤波器的混模分析（只有分布参数耦合线；无 RC/RLC 梯形）。
- CMRR 一词未出现（其框架是 S 参数，CMRR 是其集总域对应物；换算关系本文未建立——P1 可自建"Scd21 ↔ G_DC"对应并注明本文未做）。
- 校准理论明确推迟："Detailed calibration discussion is beyond the scope of this paper, but will be the subject of future work."（p.1535）。
- 式(29)在扫描版有字符残损（"S&l"等），引用前建议核对 IEEE Xplore 重排版；数值结论以文字与矩阵式 27/28 为准。
