# 精读笔记 · Giustolisi 2000《CMRR Frequency Response of CMOS Operational Transconductance Amplifiers》（IEEE Trans. Instrum. Meas. 49(1): 137–143）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> 说明：PDF 7 页对应刊页 137–143（PDF p.1 = 刊 p.137）。**公式 (1)–(16) 均为嵌入图片，未入文本层**，故本笔记只逐字引用文字论述句；涉及公式符号处以「〔符号缺失〕」标注，不猜写。

## 出处
Giustolisi, G.; Palmisano, G.; Palumbo, G. "CMRR Frequency Response of CMOS Operational Transconductance Amplifiers", IEEE Transactions on Instrumentation and Measurement, 2000, 49(1): 137–143. DOI: 10.1109/19.836324.（Università di Catania）
全文：`fulltext/H2-差分CMRR/giustolisi2000cmrr.pdf`

## 核心命题（原文）
1. **主论点：CMRR 频响由共模增益的零点（= CMRR 的极点）决定，且有两个**（p.137，摘要与引言）：
   > "The analysis shows that the CMRR of these circuits is highly affected by two poles which are caused by the zeros of the common-mode gain."
   > "We show that the CMRR of these circuits is highly affected by two poles: the first one due to the non ideal differential-to-single conversion and the second one due to the source-coupled pair. This pole is the only one that is usually considered [4], but we will show that the first one can make a dominant contribution too."
   （对偶视角：P1 分析 G_DC(s)=H_N−H_P 的零点/消去，本文分析共模增益 A_cm 的零点如何反过来在 CMRR=Ad/Acm 中变成极点——同一数学对象（共模路径的零点）的镜像表述。）

2. **文献缺口声明（与 P1 的增量定位同款句式）**（p.137）：
   > "However, despite its importance, literature does not provide a complete and clear analysis of the frequency-behavior of the common-mode gain."
   > "However, even for the simple source-coupled pair, which generally determines the input stage of OTA's, an accurate frequency analysis is not provided."

3. **失配参数（系统性+随机）进入电流镜传递函数，并决定 CMRR 直流值与带宽**（p.139，式 (10) 处；p.140，式 (16) 处）：
   > "…where parameter 〔符号缺失〕 takes into account both systematic and random errors, the latter being due to process tolerances."（p.139）
   > "The effect of term 〔符号缺失〕 determines the CMRR dc value and often also the CMRR bandwidth. In this case, since the CMRR gain-bandwidth product is not affected by term 〔符号缺失〕, the CMRR at high frequencies does not depend on the current mirror nonidealities."（p.140）
   （失配项既定直流地板又定带宽——与 P1「失配 → 残余 G_DC 随频率的行为」同构；且给出上限性质：CMRR-GBW 积与失配无关 → 高频段 CMRR 不再依赖镜失配，属「带限依赖」结构。）

4. **共模增益的零点结构**（p.137，Sec. II；p.140）：
   > "The transfer function 〔符号缺失〕 is affected by a pole and a zero which are due to capacitances at the source nodes of 〔M1〕 and 〔M2〕."（p.137）
   > "The common-mode gain has the same dominant pole of the differential gain and two zeros. Note that one of the zeros is determined by parameter 〔符号缺失〕."（p.140）
   （源极节点电容造成 A_cm 的极点-零点对；其中一个零点由失配参数决定——即失配「制造」了 CMRR 的极点。）

5. **结论复述（双极点归因）**（p.142）：
   > "We have found that the CMRR frequency response is basically determined by two poles which correspond to the two zeros of the common-mode gain. More specifically, one of these two poles arises in the source-coupled pair and the other in the current mirror that performs the differential-to-single conversion."
   > 开篇句（p.142）："In this paper, a detailed analysis of the CMRR for OTA circuits has been proposed which accounts for high-frequency effects due to the frequency limitations of transistors and to mismatch tolerances."

## 关键数值（原文）
- 源耦对极点位置（p.141）："the pole due to the source-coupled pair is located at frequencies from 4 to 7 MHz"（基于 Table II 参数）。
- 失配/拓扑对比（p.141）："Since simple current mirrors exhibit values of 〔参数〕 that are 5–40 times greater than that of cascode current mirrors, for the circuits in Fig. 1(a) and (b), the two poles are very close, while for the circuits in Fig. 1(c) and (d) (where the differential-to-single conversion is performed by a cascode current mirror) the dominant pole is that caused by the source-coupled pair."（句子跨 p.141→p.142。）
- 验证范围（p.137 摘要；p.141）："using the Spice simulator and the models of a 1.2-µm CMOS process"；"a very good agreement between the two plots for frequencies up to 100 MHz, higher than the respective gain-bandwidth products."
- 分析对象：四种 OTA 拓扑（p.138，Fig. 1）——两级 OTA、简单堆叠镜、改进堆叠镜、折叠共源共栅；元件尺寸见 Table I（p.139）、工作点提取参数见 Table II（p.140）。
- 文中未给出 CMRR 的绝对 dB 数值（曲线在 Fig. 4–7，纵轴数值不可从文本层提取，待核）。

## 对 P1/P2/P3 的对照
- **P1（消去条件）**：**高相关（H2 轴核心参照，但对象不同域）**。本文是「共模增益零点 ↔ CMRR 极点」对偶框架的经典出处之一：P1 的 G_DC(s)=H_N−H_P 消去分析可在写作中直接借这面镜子——差动结构里「共模路径的零点」同时是 CMRR 频响的极点，失配参数决定零点位置与直流值。**但不构成 killRisk**：① 对象是含电流镜的有源 OTA，非无源 RC 差分网络；② 无「全频段精确消去条件」命题，失配只以单一参数进入一阶近似（式 10），无多级梯形/R·C 交叉项；③ 其结论方向（CMRR-GBW 积与失配无关、高频不依赖镜失配）反而支持 P1 论证中「失配影响是带限的」这一谱系（与 Zhang 2020 带限复制呼应）。
- **P2（Kelvin 结构地板 ≈56 dB）**：中低相关。无 Kelvin 接法、无绝对 dB 地板数值；但「失配参数决定 CMRR 直流值」（p.140）是「结构地板」概念在 OTA 域的标准表述，可作 P2 论证的域外旁证。
- **P3（平坦度约束衰减上界）**：无。无滤波器衰减/平坦度权衡内容。
- **方法学（D1–D10）**：可借用其论证链：文献缺口声明 → 半电路对称分析 → 开路时间常数法求极点 → 设计方程铅笔可算 → SPICE 验证至 100 MHz。特别是「先声明既有文献只考虑单极点，再证明第二极点可主导」的增量写法与 P1 的增量四定位一致。
- **killRisk 判断：无/低**。最接近表述为 p.140「失配项决定 CMRR 直流值与带宽」+ 摘要「两极点由共模增益零点引起」——均为有源 OTA 一阶模型，未触及无源多级网络全频段精确消去条件。

## 没读到的
- 公式细节全部不可逐字引用（式 (1)–(16) 为图片）：失配参数的确切符号（疑为 ε，**待核**）、A_cm 两零点的显式表达式、式 (16) CMRR 完整形式。
- CMRR 绝对 dB 值与曲线数值（Fig. 4–7 纵轴）文本层不可提取，待核。
- 附录（p.142–143）cascode 电流镜高频小信号模型推导的公式细节（文字已读，公式为图）。
- 未涉及无源差分滤波器、抗混叠或传感器前端（应用语境是 OTA 实现 analog filters/sample-and-holds，p.137 引言一笔带过）。
- 与其所引 Pallas-Areny & Webster [8][9]（本级/级联差放 CMRR，已在笔记库）的定量衔接未展开。
