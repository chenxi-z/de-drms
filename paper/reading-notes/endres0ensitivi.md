# 精读笔记 · Endres 1992《Sensitivity of Fast Settling PLLs to Differential Loop Filter Component Variations》（IEEE Frequency Control Symposium 1992）

> 2026-10-27 复核更新：bib 年份已核正为 1992，旧 key 不变。 历史摘录中的待修状态保留作溯源，以本条为准。

> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。

## 出处
- Endres, Thomas J.; Kirkpatrick, James B.（Hughes Aircraft Company, Space and Communications Group）. "Sensitivity of fast settling PLLs to differential loop filter component variations." *Proceedings of the 1992 IEEE Frequency Control Symposium*, pp. 213–224. DOI: 10.1109/freq.1992.270011.（bib 中 year=0 为缺省，实为 1992。）
- PDF：`/home/anning/Documents/Obsidian Vault/20-硬件工程/10-项目设计/p1-文献谱系/fulltext/H8-灵敏度与统计电路设计/endres0ensitivi.pdf`（12 页，印刷页 213–224；下文页码 = PDF 物理页 1–12）。公式区 OCR 大量损毁，引用取自正文文本完整处。

## 核心命题（原文）
1. **理想模型假设完全配对，失配引入附加瞬态项**（p.2）：> "The ideal model assumes a perfectly balanced op amp, i.e., all like components are exactly equal. This model does not account for a transient term associated with the non-inverting leg of the op-amp due to mismatches in like components. A more rigorous loop filter model is needed."（差分运放环路滤波器：同相腿元件失配在输出端产生指数瞬态。）
2. **共模输入下"输出为零 ⇔ 元件精确匹配"——与 P1 消去条件同构的充要条件**（p.3）：> "For the ideal model. the output is zero for equal inputs V I and V2. For the practical model presented above with equal inputs VI and V2, the output can be non-zero. ... Inspection shows the output is zero for equal inputs if and only if the loop filter components are exactly matched. That is, for Rl=R3, R2=R4, and C1=C2, the output is zero. Else, an exponential term is introduced at the loop filter's output (see Figure 4)."（V1=V2 的共模激励下，输出恒零的充要条件是三对元件 R1=R3、R2=R4、C1=C2 全部匹配——这就是 P1 主张一"共模/差模消去条件的元件表述"在 PLL 域的独立同构实例。）
3. **只有相对差（失配）驱动误差项，绝对值无关**（p.4）：> "Note that it is only the relative difference of the components that drives the transient term."；随后举例：> "if the nominal value capacitance is 1000 pF, a set of components C1=990 pF and C2=1010 pF has essentially the same effect as the set of components C1=1OOO pF and C2=1020 pF."（±1% 与 0/±2% 两种绝对偏置、相对差同为 2% 时效果相同——P1"失配而非绝对偏差"论点的另一域表述。）
4. **失配瞬态时间常数远长于理想响应，高环增益下被放大**（p.3, p.5）：> "However, for sufficiently high loop gain, the transient is greatly amplified for component mismatches well within the device tolerances, such that the effect on phase error must be considered."（p.3）；> "this time constant z is much longer than the ideal PLL transient response time constant ... Thus, the transient response due to loop filter mismatch will swamp the ideal response term and cause settling times much longer than that predicted by the ideal equation."（p.5，z = b = C2(R3+R4)，理想项时间常数 a = C1(R1+R2)。）
5. **建模方法：把失配瞬态当作叠加在理想二阶响应上的扰动**（p.5）：> "By assuming a linear system and employing superposition principals, a convenient way to theoretically model the loop filter transient is as a disturbance introduced at the loop filter's output (see Figure 6)."（失配 → 等效输出端扰动源 → 与理想二阶响应叠加；PSpice 与实测三方吻合。）
6. **结论与三种解决方案**（p.11）：> "Phase settling is shown to be sensitive to small variations in the loop filter components, well within the device tolerances."。方案一配对挑选（p.8）：> "the option exists to handpick these parts. They can be chosen at beginning-of-life such that no undesired loop filter transient is introduced (that is, exactly match the components to 0 percent). ... optimally mismatch the components toward a negative percent mismatch, thus minimizing settling time."（欠阻尼系统按 ±6° 判据最优失配偏负）。方案二单端化（p.9）：> "a single-ended scheme eliminates the undesired term by forcing the non-inverting input to zero."（代价：K_d 减半/杂散恶化）。方案三两级化（p.9）：> "Note that for equal inputs (V,=V2), the difference amplifier's transfer function is iden tical to the combined loop filter's transfer function with C1 = C2 = ...; that is, the exponential term reduces to a simple gain offset so that it is not critical to match the difference amplifier's components."（**结构重构使第一级失配退化为无害的增益偏置**——与 P1"通过结构选择改变元件条件的约束范围"思路同型。）

## 关键数值（原文）
- 1% 容差元件 → ±2% 失配（p.8）：> "For 1 percent tolerance parts, a ±2 percent mismatch is feasible. These small variations, well within device tolerances, can degrade phase setting time."（OCR：settling）
- 环路参数（p.5）：ωn = 290 krad/sec、ζ = 0.9、+2% 失配；Δf_REF = 92 kHz、A = 150 mV（p.6 Fig.7 标注）；K_d = 0.636 V/rad、K_v = 150 MHz/V（V_t = 5 v）、N = 654（OCR "8=654"，待核）；斜坡斜率 ≈ 4.5 V/µs 近似为阶跃。
- Fig.5 失配元件值（p.4 图注）：R1=11,185 Ω、R3=10,900 Ω、R2=63,240、R4=62,001、C1=1020 pF、C2=1000 pF。
- 判据示例（p.2）：> "settle to within a finite error window in a given time, e.g., +6 degrees in 50 psec"（OCR：±6°、50 µs）。
- 失配方向效应（p.6）：> "a negative percent mismatch may add destructively with the ideal second-order-system phase error, while a positive percent mismatch may add constructively."；Fig.14 显示 PSpice 与实际环路的最小整流时间不在 0% 处（判据 ±6° 所致），理论扰动模型在 0% 有零点（p.8）。

## 对 P1/P2/P3 的对照
- **P1（消去条件/失配→G_DC）**：**高（同构旁证，非竞争）**。本文的数学骨架与 P1 主张一逐条对应：①共模（等输入）输出为零的**充要元件条件**（R1=R3 ∧ R2=R4 ∧ C1=C2）↔ P1 的 G_DC=H_N−H_P≡0 元件条件；②误差幅值只依赖**相对差** ↔ P1 的失配（而非绝对偏差）决定残余；③失配项时间常数由元件积（C2(R3+R4)）决定 ↔ P1 的 τ=R·C 匹配；④两级重构把匹配要求降为"非关键" ↔ P1 的结构级消去。差异：对象是 PLL 环路滤波器的时域瞬态（指数项），非抗混叠网络的频响/G_DC；未给出一般性定理或证明框架，是工程案例。引用方式：作"失配→共模转差分误差的跨域独立实例"支撑 P1 普遍性，**不能**引作 P1 数学本身的来源。
- **P2（Kelvin 结构地板）**：低。全文讨论差分结构失配误差但无接地/共模抑制物理层内容。
- **P3（平坦度衰减上界）**：无。不涉频响平坦度或匹配界。
- **方法学（D1–D10）**：中。"1% 容差 → ±2% 最坏失配"、"±6° 窗口判据下最优失配不在零点"、"BOL 匹配不保证 EOL（老化方向不定，p.8）"——都是门槛化判据可用的小节。
- **killRisk**：无威胁。领域不同（PLL 整定 vs ΣΔ 抗混叠），无重叠主张；反而其"iff 匹配"充要条件为 P1 提供独立佐证。需划界的一点：本文解法之一是"故意最优失配"（利用判据窗口），P1 若声称"失配越小越好"须注意该判据依赖性只在有限窗口指标下成立。

## 没读到的
- 实用模型完整传递函数推导（p.3 式区块在 OCR 中损毁，V_out = A_v·Z2(Z4−Z1)/(…) 诸式只可辨片段），引用其模型公式前须回原 PDF 核对。
- 时间常数 z 与失配百分比之间的定量曲线（Fig.4/6/14 的坐标数值大多在图内，OCR 未拾取；Fig.14 横轴 −3%~+3% 可辨但纵轴刻度未辨）。
- N=654 的确认（OCR 印作 "8=654"）；Fig.12/13 示波器截图中的具体整流时间未提取。
- Egan [4] 的频率步等效变换、Gardner [7] 未读（背景理论来源）。
