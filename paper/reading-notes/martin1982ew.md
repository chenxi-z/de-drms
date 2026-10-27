# 精读笔记 · Martin 1982《New clock feedthrough cancellation technique for analogue MOS switched-capacitor circuits》（Electronics Letters）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。

## 出处
- Martin, K. (UCLA), "New clock feedthrough cancellation technique for analogue MOS switched-capacitor circuits", *Electronics Letters*, Vol. 18 No. 1, 1982-01-07（收稿 1981-11-10），journal pp. 39–40；PDF 物理页 1–2（第 1 页与 Cohen 光纤论文同版面，Martin 文在右栏）。
- 文件：`/home/anning/Documents/Obsidian Vault/20-硬件工程/10-项目设计/p1-文献谱系/fulltext/H5-kickback/martin1982ew.pdf`

## 核心命题（原文）
1. **提出依靠匹配与运放 CMRR 的时钟馈通消去技术**（p.1，摘要）：> "A new technique for minimising DC offsets caused by clock feedthrough in switched-capacitor circuits is presented. Unlike some techniques presented in the past, the clock feedthrough cancellation is dependent only on matching and the common mode rejection ratio of the op-amps."（馈通消去只依赖元件匹配与运放共模抑制比，不依赖时钟波形/阈值电压的精确预测——这是"消去条件 = 元件条件"思想在 SC 领域的早期表述。）
2. **机制：在差分运放正输入端注入等量反号电荷**（p.1）：> "It essentially consists of adding a network to the positive input of the differential op-amps to cancel the signal injected at the negative terminal, by clock feedthrough."（在正输入端加一个补偿网络，抵消负输入端被时钟馈通注入的电荷。）
3. **踢回的物理来源 = 复位管关断时栅漏寄生电容从积分电容抽走电荷**（p.2）：> "When it is shut off the parasitic capacitor between its gate and the inverting op-amp input pulls some charge out of C1 and C2 causing offset errors."（其余开关 M1–M4 的馈通因被低阻节点快速充放电而无害，唯独接在虚地点的复位管 M5 造成净误差——kickback 危害性取决于节点阻抗的判据。）
4. **替代方案（Fig. 1c）把消去条件写成元件相等条件**（p.2）：> "In order to guarantee that the charge injected is identical at both nodes M6 should be matched to M5. Also the capacitor C3 should be equal to the total capacitance connected to the inverting op-amp input so that the voltage change is the same at both nodes."（M6 与 M5 匹配 + C3 = 反相输入端总电容，两个元件相等条件即保证两节点电压变化相同；且"same at both nodes"依赖运放高 CMRR 前提：> "assuming an infinite common mode rejection ratio"（p.2）。）
5. **代价：电容面积加倍**（p.1）：> "Its major drawback is that it doubles the total amount of capacitance required unless the capacitors can be scaled down (which will often be the case)."

## 关键数值（原文）
- SPICE 三方案对比（p.2）：> "The changes in the differential input voltages of the op-amps (V of Fig. 1) due to clock feedthrough were -2.7 mV, 0.20 mV and -0.017 mV for the circuits of Figs. 1a, b and c, respectively."（无补偿 −2.7 mV → 哑管补偿 0.20 mV（约 13.5×改善）→ 正输入网络 −0.017 mV（约 159×改善）；作者自己提醒 > "The accuracy of the simulation should be treated with caution"（p.2）。）
- 仿真条件（p.2）：C1 = 1 pF；单级 NMOS 运放输入管 400 µm×4 µm；开关 4 µm×4 µm。
- 哑管比例（p.2）：> "the (W/L) ratio of M5 to M6 should not be exactly 2:1 but somewhat less. The ratio required for perfect cancellation is dependent on the clocking signals and the threshold voltage of the transistors and is therefore difficult to predict."（哑管法的 2:1 比例不可预测、依赖时钟斜率与 Vth——对比 Fig.1c 方案"very nearly equal independent of the clocking waveforms and transistor threshold voltages"（p.2）。）
- 改善量级为作者自报仿真值，无实测数据（Electronics Letters 短文）。

## 对 P1/P2/P3 的对照
- **P1（消去条件 = 元件条件）**：本篇是"用结构化元件条件实现馈通消去"的鼻祖级表述——Fig.1c 的消去条件就是两条元件匹配式（M6≡M5、C3≡C_inv 总电容），并显式依赖 CMRR→∞ 理想化。P1 的 G_DC=H_N−H_P≡0 思想与此同构，本篇提供历史锚点而非威胁。但注意域差异：Martin 在**片内 SC 电路**里做电荷域补偿，P1 处理的是**外置 RC 无源网络**驱动 SC ΣΔ 输入，属不同层面。
- **P2（Kelvin 结构地板 ≈56dB）**：未涉及 Kelvin/四线地板，无相关。
- **P3（衰减可达上界）**：未涉及衰减上界概念；但"feedthrough 只能被匹配消去、被 CMRR 限制"的思路与 P3 的"衰减有上界"精神一致（非定量）。
- **增量四（门槛化方法学）**：无建立时间/kickback 回稳门槛讨论；其"低阻节点馈通无害、高阻虚地点有害"的定性判据可视作 kickback 危害性门槛的原始直觉，但无任何数值化。
- **killRisk：无威胁**。理由：①域不同（片内 SC 滤波/ADC 内部补偿 vs 外部 RC 网络设计）；②其消去是主动添加补偿网络，P1 是无源差分网络的传输函数条件；③时间（1982）与场景（单端 SC 放大器）均不构成对 P1 三条主张的覆盖。

## 没读到的
- Fig.1/2 图形细节仅从题注与正文推断（a/b/c 三电路拓扑），未逐管核图；Reference 8（Gray et al. 全差分 SC 方案）未读，文中自承其抑制度优于本文单端方案（> "It is not expected that the rejection of the clock feedthrough will be as good as the totally differential SC circuits proposed in Reference 8"，p.2）。
