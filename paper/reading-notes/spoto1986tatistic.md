# 精读笔记 · Spoto 1986《Statistical Integrated Circuit Design and Characterization》（IEEE TCAD）

> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> 本 PDF 第 2–14 页为扫描件无文本层，pdftotext 不可用；以下引文均经 300 dpi 页图目视逐字核对（页码 = PDF 物理页）。

## 出处
- Spoto, James P.; Coston, W. Terry; Hernandez, C. Paul（Harris Corporation, Semiconductor Sector, Melbourne, FL）. "Statistical Integrated Circuit Design and Characterization." *IEEE Transactions on Computer-Aided Design*, vol. CAD-5, no. 1, pp. 90–103, Jan. 1986. DOI: 10.1109/tcad.1986.1270180.
- PDF：`/home/anning/Documents/Obsidian Vault/20-硬件工程/10-项目设计/p1-文献谱系/fulltext/H8-灵敏度与统计电路设计/spoto1986tatistic.pdf`（14 页，印刷页 90–103）。

## 核心命题（原文）
1. **worst-worst case 之所以过度设计，正因其无视参数相关性**（p.1 脚注 2，印刷页 90）：> "Worst-worst case is defined here as the condition where the varying parameters are each set to a maximum or minimum (whichever is more degrading to performance) allowable or observed value without regard to the particular parameter correlations."（开篇立论：各参数独立取最坏角点的传统方法导致 "many overly designed products"（p.1）——这是 H8 轴②"统计设计替代角点法"的经典动机陈述。）
2. **mismatch 与 process 两类统计变量在概念上显式分离**（p.2 右栏 + 脚注 3，印刷页 91）：> "The chips are deployed and recovered in such a way as to allow inference over device-to-device "mismatches," as well as chip-to-chip, wafer-to-wafer, and lot-to-lot "process" variations."；脚注 3：> "The "mismatch" variations are segregated from those over the "process" since they require each device to maintain its own set of statistical varying parameters, whereas "process" varying parameters can be commonly applied to all like devices of the circuit."（mismatch = 每器件独立抽样；process = 同类器件共享——与 P1"共模分量消去、失配分量残留"是同一分解。）
3. **共置电阻的建模实例：共享工艺参数 + 独立刻蚀失配**（p.4，印刷页 93）：> "Sheet resistance is fairly constant across adjacent resistors, whereas lithography variations create a "mismatch" in the their values (which are the cause of many analog circuit offset errors)."（原文即印作 "in the their values"，排版笔误照录。）建模代码（逐字）：
   > "RL1  3  7  RHOS*GAUSS(LR,DEL,2)/
   > GAUSS(WR,DEL,2)
   > RL2  3  8  RHOS*GAUSS(LR,DEL,2)/
   > GAUSS(WR,DEL,2)"
   其中 > "GAUSS(x, y, I) is a Gaussian random number generator "RNG", and the arguments x = mean value, y = standard deviation, and I is an integer designating different independent generators. When Monte Carlo is active (i.e., the parameter MONTE = 1), the GAUSS function generates a new random number every time it is evaluated."（RHOS 由脚本层每轮抽一次、对两电阻同值——> "Note that the random value RHOS is used as a constant in the calculation of the resistor values demonstrating what is sometimes termed hierarchical random number generation [3]."（p.5）——分层随机数：工艺分量公共、刻蚀分量逐电阻独立。）
4. **Sensitivity-Based（Method of Moments）统计法：失配项与工艺项分开进方差**（p.5，印刷页 94）：> "V_OUT = V̄_OUT + ∂V_OUT/∂P ΔP"（截断泰勒近似）；方差公式 > "σ²V_OUT = S_M Λ_M S_M^T + S_P Λ_P S_P^T"（下标标注 "mismatch term process variation term"），> "where S_M and S_P are the sensitivity vector w.r.t. the "matched" parameters P_M and "process" parameters P_P, respectively."；> "In this way, the differing effects of parameter "mismatch" and "process" variations can be analyzed separately."（灵敏度向量 × 协方差矩阵的二次型，失配/工艺两项并列——H8 轴①×②的交点。）
5. **失配间相关性显式进交叉项**（p.5）：> "Except for IDSS mismatch which is highly correlated to the V_p mismatch, all mismatches are assumed to be statistically independent. No "process" parameter sensitivities were found to be significant."，对应 HA-5170 失调电压算例：> "σ²V_OS = (1.33)²(0.0038)² + (0.138)²(0.01)² + (0.07)²(0.007)² + 2(1.33)(0.07)(2.5 × 10⁻⁵) = (5.7 mV)²."（末项 2·S₁·S₂·cov 即相关失配的交叉项。）
6. **灵敏度计算用伴随网络法**（p.10，印刷页 99）：> "Both dc and ac sensitivities are determined by the adjoint network approach [13]."，参考文献 [13] = "S. W. Director and R. A. Rohrer, "A generalized adjoint network and network sensitivities," IEEE Trans. Circuit Theory, vol. CT-16, Aug. 1969."（p.14，印刷页 103）——本文的灵敏度引擎正是 Orchard/Director 伴随网络一脉（与已有笔记 director1969the.md 同源）。
7. **良率计算区分"独立良率"与"总良率"**（p.11–12，印刷页 100–101）：> "The "INDEPENDENT YIELD" is simply the product of all the individual yields assuming no correlation between them."（HA-5104 例：TOTAL YIELD = 31.00 percent，INDEPENDENT YIELD = 14.88 percent——参数间相关使真实良率约为独立假设的 2 倍。CORL8 命令列出 TCN–TCP 相关系数 0.9863 等高相关对，并用其做探针筛选用 VIO 限值替代难以在片测的 TCN/TCP。）

## 关键数值（原文）
- SB 法 vs Monte-Carlo 验证（p.6 Table I，300 samples）：失调电压 5.7 mV（Sens）vs 5.6 mV（MC）；−55 ℃→125 ℃ 失调漂移 1.48 mV vs 1.5 mV。
- 失调漂移 SB 算例（p.6）：> "σ²ΔV_I0 = (0.32)²(0.0038)² + (0.061)²(0.01)² + (0.02)²(0.007)² + 2(0.32)(0.02)(2.5 × 10⁻⁵) = (1.48 mV)²."
- HA-5170 失调敏感度表（p.6 Fig.7）：J1/J2 V_P 失配 0.38% 1σ、归一化敏感度 1.33（25 ℃）；R3/R4 1.0%、0.138；J1/J2 IDSS 0.7%、0.07。
- SPADS 运行规模（p.3）：100 次外环 × 6 次内环，Harris 800 超级小型机，总 CPU 2 h；SAMPLE→SUPREM3→MINIMOS→SPICE2 链。
- HA-5330 采样保持（200+ 晶体管）100 样本 MC（p.7）：dc 结果 5 h / ac 3 h / 瞬态 10 h CPU（脚注 7）；Fig.9 直方图：CMRR 仿真 95 dB σ10 dB vs 实测 99 dB σ5 dB；电源电流 18.7 mA σ1.24 vs 17.6 mA σ1.18；失调 σ0.24 mV vs 0.21 mV（p.8）。
- 触发器延迟 t_D 与工艺参数相关系数（p.9 Fig.12）：K_PP：R = −0.75；K_PN：R = −0.5；V_TP：R ≈ 0；V_TN：R = −0.1；T_OX：R = 0.03。 settling time：mean 370 ns，σ 74.7 ns（Fig.10）。
- STORE/RESTORE 加速（p.9）：dc 收敛迭代 15–50 → 2–5 次，> "factors of 10X improvement in a dc and ac Monte Carlo analysis are typical."
- 探针筛选成本（p.12）：die $0.25、封装 $0.30/die；VIO 排序限 1 mV 使封装总成本最小（Fig.17）。

## 对 P1/P2/P3 的对照
- **P1（消去条件/失配→G_DC）**：高（方法学同构，非内容撞车）。本文是"process 公共分量 + mismatch 独立分量"分层统计模型的电路级实用范本（式 σ²V = S_M Λ_M S_Mᵀ + S_P Λ_P S_Pᵀ），且其灵敏度引擎明确引用 Director–Rohrer 伴随网络（即 P1 理论工具的源头文献）。P1 的"共模增益消去、失配残差决定 G_DC"在数学上正是把 S_P 项置零、只留 S_M 项的极限情形——可引作"失配/工艺分解的工业标准做法"佐证。但本文只做一阶方差传播与 MC，无消去条件的充要性讨论。
- **P2（Kelvin 结构地板）**：无。全文无接地结构/共模抑制物理内容（CMRR 只作为被统计的输出指标出现）。
- **P3（平坦度衰减上界/Bode-Fano）**：无。不涉无源网络频域综合或匹配界。
- **方法学（D1–D10）**：高。H8 轴②的核心文献：相关性在良率中的处理（TOTAL vs INDEPENDENT YIELD）、worst-worst 角点法因无视相关而过度设计的论断、失配/工艺分层抽样——都是门槛化方法学"区分共模与差模、按相关性合并判据"的直接先例。
- **killRisk**：无威胁。本文是统计 CAD 工具论文，不给出任何无源网络传递函数恒等式或衰减上界；与 P1 四主张为"工具/方法供给"关系而非"优先权竞争"。

## 没读到的
- 参考文献 [3]（SPADS 前身/hierarchical random number generation 出处）、[12]（Calahan《Computer-Aided Network Design》pp.179-180，"Method of Moments" 术语来源）、[20]–[26]（design centering 文献簇，含 Bandler/Brayton/Director）未读——如需追溯"分层随机数"与"统计设计中心化"的原典须另行精读。
- Fig.5 直方图的 V_T0 统计精确数值（AVG/STD DEV 标注在图内小字，150 dpi 下仅辨 AVG ≈ 6.73、STD ≈ 0.24 量级）未逐位核对，未写入正文引证。
- HA-5104 的 20 参数 spec 表全表（p.11 Table，IVCC/IV_EE/…/GBW 上下限）只作背景，未逐项抄录。
- SAM 命令语言完整语义（LMSEN/DELVAR/SENVAR 的具体算式）文中只述功能，未给出内部公式——如引用其算法须查 Harris 内部文档/后续论文。
