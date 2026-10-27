# 精读笔记 · Moschytz《Trade-Offs in Sensitivity, Component Spread and Component Tolerance in Active Filter Design》（Trade-Offs in Analog Circuit Design, Kluwer 2002, Ch.11）

> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。

## 出处
- Moschytz, George. "Trade-Offs in Sensitivity, Component Spread and Component Tolerance in Active Filter Design." Chapter 11, in C. Toumazou et al. (eds), *Trade-Offs in Analog Circuit Design: The Designer's Companion*, Kluwer Academic Publishers, 2002, pp. 315–339. DOI: 10.1007/0-306-47673-8_11（bib 条目 moschytz0radeffs 年份字段为 "0"，[bib 待补：应为 2002]）。
- PDF：`/home/anning/Documents/Obsidian Vault/20-硬件工程/10-项目设计/p1-文献谱系/fulltext/H8-灵敏度与统计电路设计/moschytz0radeffs.pdf`（25 页，印刷页 315–339；下文页码 = PDF 物理页，印刷页 = 物理页 + 314）。
- ⚠️ 抽取质量：本 PDF 公式与 Table 11.1 的符号在 pdftotext 中大量丢失（行内数学全部为空缺），下文引用中以 [OCR损] 标出公式空缺处；散文部分逐字可靠。

## 核心命题（原文）
1. **三环 vicious cycle：灵敏度 ↔ 元件比（spread）↔ 元件容差**（p.1/印315）：> "In active-RC filter design, for example, insensitive circuits do exist, but often a satisfactory degree of tolerance insensitivity is paid for by an increase in component spread. An increase in component spread, however, generally increases component tolerance, which in turn decreases functional accuracy and performance, thus closing a typical vicious cycle so often encountered in analog circuit design."（全章的总纲：低灵敏度要用大元件比买，大比又抬容差降精度——典型的模拟设计权衡闭环。）
2. **无源 RC 网络的结构性极限定理：极点只能在负实轴且单极点 ⇒ 极点 Q<0.5**（p.11–12/印325–326）：> "This theorem states that the poles of an RC network are restricted to being single and on the negative-real axis in the complex frequency plane."（无源 RC 的经典不可能性定理——与 P3"无源网络衰减可达上界"同属一类"无源结构上界"，是 P1 最有亲缘性的经典引文。）由此（p.7/印321）：> "In fact, the pole Q of any pole pair realized by a passive RC network is always less than 0.5." [OCR损：Q_p 符号与上下文公式]。
3. **逼近上界 = 逼近双极点 = 付出元件比代价**（p.12/印326）：> "This, of course, demands a non-realizable spread of the resistors and/or capacitors. How large a spread of these components is acceptable in order to minimize [OCR损] and to approach a double pole (or, in other words, to permit [OCR损] to approach 0.5) is a question of the technology used. It represents one of the fundamental trade-offs of low-sensitivity active RC filter – and oscillator – design."（上界不可达、只能以元件比换逼近度——与 Bode-Fano"匹配界 + 带宽/复杂度代价"同构的权衡叙事。）
4. **图优值（figure-of-merit）框架：Q_p→0.5 上界 + spread 预算**（p.18/印332）：> "we have introduced a type of figure-of-merit, namely [OCR损：Q_p] which must approach its upper bound of 0.5 in order to minimize sensitivity and maximize selectivity. Approaching this upper bound always entails an increase in component spread by impedance scaling."（把灵敏度最小化归约为单一解析图优值的最大化，代价显式计入——这正是 P3"约束下可达上界"叙事的 2002 年范本。）
5. **增益-灵敏度积（GSP）纠正直觉：正反馈 biquad 反而更常用**（p.9–10/印323–324）：> "which is the gain–sensitivity product (GSP) of [OCR损] with respect to [OCR损] This changes the conclusion from above quite drastically. If we consider the GSP, which we must, rather than the sensitivity, then instead of (11.28), we now have:"（p.9）> "If we consider the open-loop gain of an op-amp to be in the order of 100 to 1000, it readily follows that the GSP for positive feedback is certainly comparable to, if not considerably smaller than, that of negative feedback. This explains why the positive-feedback biquads are, in fact, more frequently used than their negative-feedback counterparts."（p.10；单看灵敏度会误判，须连同工作点的增益一起看乘积——对 P1 评估"元件条件"时"哪个量才是正确目标函数"是个方法论提醒。）
6. **低灵敏度 ⇒ 低输出热噪声（附带收益）**（p.24–25/印338–339）：> "It has long been suspected (but never undisputedly proved) that low-sensitivity active RC filters are also low in output thermal noise. A recent publication substantiates this assumption [2]."（p.24）> "The improvement in output thermal noise reduction is considerable, and comes free of charge, in that, as we have seen above, it requires simply the selection of appropriate component values to implement impedance tapering."（p.25；灵敏度最小化与噪声最小化在阻抗渐变下同向。）
7. **实现手段：单位增益缓冲去耦 / 阻抗渐变（impedance tapering）/ 潜在对称（twin-T、bridged-T）**（p.15/印329）：> "The task of the unity-gain buffer is to prevent the second RC ladder section from loading the first."> "Similar decoupling of the individual L-sections of an RC ladder network can be achieved by impedance scaling upwards (or \"impedance tapering\" , as we shall call it), the second L-section by a factor [OCR损]"（渐变使 Q_p→0.5；p.18 补充：> "The degree of mismatch attainable through impedance tapering depends on the degree of component spread permissible for a given technology."）

## 关键数值（原文）
- 带通算例（p.7/印321）：中心频率 500 Hz、3 dB 带宽 50 Hz ⇒ Q=10；> "It follows from the example above that with a passive RC second-order bandpass filter, the attainable 3 dB bandwidth will always be larger than 1000 Hz."（无源 RC 二阶带通选择性"essentially useless"。）
- 极点 Q 硬上界（p.7/印321）：无源 RC 极点对 Q 恒 < 0.5；双极点（Q=0.5）需无穷元件比、实际不可实现（p.12/印326、p.15/印329）。
- 运放开环增益量级（p.10/印324）：> "in the order of 100 to 1000"（用于正/负反馈 GSP 对比的取值口径）；正反馈闭环增益限制在"generally between unity and two"（p.10/印324）。
- 高阶滤波器极点分解不可行时改用系数灵敏度（p.10/印324）：> "The problem is that for higher order filters, breaking the corresponding polynomials N (s) and D (s) into these roots and root pairs becomes quite intractable, so that the quantities cannot be analytically obtained."（但最大化 Q_p 的渐变步骤对高阶仍有效。）
- 三阶 Chebyshev 设计例（p.22/印336）：> "This corresponds to a filter with a maximum ripple of 0.5 dB in the passband up to 75 kHz, and a minimum attenuation of 38 dB in the stopband above 300 kHz."；Monte Carlo 用 5% 元件容差对比渐变/非渐变电路（p.22/印336；二阶例 p.20/印334 用渐变因子 4 与非渐变对比）。
- 极点变差 vs 零点变差的分工（p.4/印318）：> "In general, the pole variation plays a more important role than the zero variation because it is also responsible for the filter (or system) stability, and because the pole variations will effect the filter passband in contrast to the zero variations which effect primarily the filter stopband."（通带精度由极点变差主导——抗混叠通带平坦度对元件容差的敏感面在极点。）
- 参考文献：[1] Moschytz, "Low-sensitivity, low-power active-RC allpole filters using impedance tapering" IEEE TCAS 46(8) 1999, pp.1009–1026 及 "Realizability constraints for third-order impedance-tapered allpole filters" pp.1073–1077；[2] Jurisic & Moschytz, MELECON 2000, vol.II, pp.591–594。

## 对 P1/P2/P3 的对照
- **P1（消去条件 G_DC=H_N−H_P≡0）**：中。亲缘在"无源 RC 结构界限"这一文体：Moschytz 的"极点单根且限于负实轴 ⇒ Q<0.5"是教科书级无源 RC 不可能性定理，与 P1"无源差分网络直流增益消去的元件条件"同属"从网络结构推性能上界/恒等式"的传统；但对象不同（极点选择性与增益 vs 直流共模/差分增益消去），本文不含任何差分结构或消去恒等式内容。是 P1 有利的经典背景引文，非撞车。
- **P2（Kelvin 结构地板 ≈56dB）**：无。全章单端有源 RC 滤波器，不涉共模抑制/接地结构/四线 Kelvin。
- **P3（平坦度约束衰减可达上界 = Bode-Fano 亲缘）**：高。本批重点②的正面答案：本章给出"性能上界（Q_p→0.5）× 元件比代价 × 技术容差"的解析权衡范式与图优值方法，且 Chebyshev 算例直接是"通带纹波 0.5 dB + 阻带 38 dB 衰减"的频响指标——与 P3"平坦度约束下的衰减可达上界"问题形态最接近的先例；但其上界来自 RC 极点定理而非 Bode-Fano 匹配理论（全章未提 Bode-Fano、未做匹配网络理论），须如此划界。灵敏度理论工具箱（相对/半相对灵敏度、根灵敏度=留数、幅相灵敏度=传递灵敏度的实虚部，Table 11.1）正是 P3"理论工具=灵敏度/统计设计"的教科书来源。
- **方法学（D1–D10 门槛化）**：中-高。"vicious cycle 权衡闭环 + 单一图优值 + 容差 Monte Carlo 验证"的章节组织，与 P1 门槛化方法学"每级给解析判据 + 统计验证"高度同构；GSP 教训（正确目标函数是乘积而非单因子）可作 D1–D10 论证"门槛量必须选对"的历史注脚。
- **killRisk**：无威胁，反而是可引援。唯一须划界处：若 P1/P3 行文出现"首次给出无源 RC 网络性能上界"类表述，必须先引本定理（及其溯源文献 [1] Moschytz 1999 TCAS）并把首创性收窄到"差分抗混叠网络的直流消去条件/平坦度-衰减联合界"上。

## 没读到的
- **全部公式本体**：式 (11.1)–(11.57) 的符号与 Table 11.1（灵敏度关系表）在 PDF 文本层中丢失（行内数学空白），本文引用只能锚定散文与编号；如需逐式核对须回看 PDF 版面或原书。
- Figure 11.7（渐变因子 x 对 Q_p 的曲线）的数值刻度未从图上提取（正文只有"already for a value of [OCR损]"）。
- 参考文献 [1]（Moschytz 1999 TCAS 两篇渐变全极点滤波器，含三阶可实现性约束）与 [2]（Jurisic/Moschytz 2000 MELECON 低噪声版）未读原文——"低灵敏度⇒低噪声"的证明在 [2]/其后期刊版中，本章仅演示两个算例。
- 二阶低通设计例（p.20/印334）的具体元件值与式 (11.56)(11.57) 数值在抽取中丢失，只有"tapering factor 4 vs 1"与 Monte Carlo 定性结论。
