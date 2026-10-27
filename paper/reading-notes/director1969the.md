# 精读笔记 · Director 1969《The Generalized Adjoint Network and Network Sensitivities》（IEEE Trans. Circuit Theory, CT-16(3): 318–323）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> 本篇是 H8 灵敏度理论在 H2 批内的锚点：读它的目的是确认「伴随网络法」能/不能直接给出 P1 的多级无源网络全频段精确消去条件。
> 底稿为扫描件 OCR，个别单词有识别噪声（引文尽量选 OCR 干净段，明显噪声处以 [...] 标出）。

## 出处
- Director, S. W. & Rohrer, R. A., "The Generalized Adjoint Network and Network Sensitivities", *IEEE Transactions on Circuit Theory*, vol. CT-16, no. 3, pp. 318–323, Aug. 1969. DOI: 10.1109/tct.1969.1082965。
- 本地 PDF：`fulltext/H2-差分CMRR/director1969the.pdf`（6 页；PDF 第 1 页 = 印刷 p.318，同页上缘是上一篇论文的参考文献，本篇正文从 p.318 中部起；末页 p.323 下缘接下一篇 Kishi & Kajitani 论文标题）。页码按印刷页 318–323 记。
- 收稿 1968-10-04，修回 1969-02-12（p.318 脚注）。

## 核心命题（原文）
1. **伴随网络法把"任意网络函数对全部参数的灵敏度"压缩为两次网络分析**（p.318）：
   > "These algorithms rely on two network analyses, one on the original network and the other on a related "adjoint" network, to ascertain branch voltages and branch currents. The network sensitivities are found to be simply products of the corresponding branch voltages and/or branch currents so obtained."
   （这是 P1 论文 H8 理论地基的原始表述：灵敏度 = 原网络与伴随网络对应支路电压/电流的乘积。）

2. **本文的贡献是把适用域推广到"一切可参数化表示的元件"**（p.318, Abstract）：
   > "The present paper derives a related adjoint network representation and sensitivity coefficients for networks con[t]aining a very broad class of elements : those that admit a parametric representation."
   （比早期只处理线性时不变电阻网络的结果更一般；原文摘要，OCR 把 containing 识别作 "conthing"。）

3. **推导工具 = Tellegen 定理，且原/伴随网络只需同拓扑、不要求同元件类型**（p.318–319）：
   > "We impose the requirement that both [N] and [N̂] have the same topology, but not necessarily the same element types in corresponding branches. This requirement is made so that Tellegen's theorem can be applied."（p.318–319）
   > "Since Tellegen's theorem is independent of element values, ..."（p.319）
   （消去 Δv、Δi 项的关键一步——伴随元件关系是人为选出来让 Tellegen 和式与全部非源支路扰动无关。）

4. **线性时不变电容的伴随元件 = 同值电容（时间反转 τ = t₀+t_f−t 下）**（p.320）：
   > "Observe that if the capacitive element is linear and time-invariant, so that [f_C = C·v_C, g_C = C·v_C] then the adjoint branch relation becomes [q̂_C(τ) = C·v̂_C(τ)] where C is incremental capacitance, which is in agreement with previous results."
   （对 P1 直接相关：对 RC 网络，伴随网络仍是同一 RC 网络——因此"单级/多级梯形 RC 的 G_DC(s) 对每个 R、C 的偏导"原则上一次伴随分析即可全部拿到。）

5. **受控源的伴随规则：控制支路与受控支路角色互换**（p.321）：
   > "...which describes a current-controlled current source of current amplification ratio −p. Note that the roles of controlling and dependent branch in the original network are reversed in the adjoint network in this case (as with all two-branch controlled source models)."
   （实现多级有源/含受控源差分结构灵敏度时必须用这条；本文只举了一个例子，未展开。）

6. **灵敏度系数总式与"任意网络函数"的两次分析结论**（p.321）：
   > "The sensitivity of any "network function" with respect to all the parameters can be obtained by appropriate application of unity and zero-valued sources to the original and adjoint networks, i.e., only two networks analyses are required. The coefficients of the Δp terms of (14) can be calculated and are indeed the desired sensitivities."

## 关键数值（原文）
- 无任何数值实验/算例数据：全文是纯理论推导 + Table I（p.322，伴随支路关系与灵敏度系数分类表：Resistive / Capacitive / Inductive / Coupling 四类），OCR 下公式大多不可逐字恢复。
- 唯一半数值的说明是二极管例（p.319）：MOS 型表面电导指数 "1 ≤ n ≤ 4 depending on the surface channel current"，参数向量 P_R = (n, T, I_s, R_b)——仅为参数化表示举例，非测量值。

## 对 P1/P2/P3 的对照
- **P1（消去条件）**：完全不涉及。全文没有差分结构、共模/差模、CMRR、G_DC(s)=H_N−H_P 等概念；它给的是"如何高效算 ∂(网络函数)/∂p_k"的通用机器，不是"何组元件值使某函数恒为零"的综合条件。对 P1 的价值是**工具性**：P1 主张"多级梯形 τ 匹配不再充分、R1·C2 交叉项存在"，本文的伴随法正是把这类交叉项（∂²/∂R₁∂C₂ 或 ∂H/∂R₁ 中的 C₂ 依赖）系统化算出的手段——但本文本身一步也没走到那里。
- **P2（Kelvin 结构地板 ≈56 dB）**：无。无任何结构/布局/引线电阻内容。
- **P3（平坦度约束衰减上界）**：无。无频域指标讨论（频域版在其引用 [4] Rohrer "Automated network design—The frequency domain case", this issue, pp. 330-337——**那是另一篇**，本篇是时域参数化推广）。
- **方法学（D1–D10 门槛化）**：中度相关——"两次分析得全参数灵敏度"是把 P1 的失配→误差条件从逐元件手推升级为可验证命题的标准方法学依据；引用时定位为 sensitivity-analysis 地基，不作为消去条件的出处。
- **killRisk 判断：无**。本文不含任何"多级无源网络全频段精确消去/失配→CM 误差解析条件"的表述，最接近的也只是通用灵敏度框架，距 P1 的具体命题有本质差距。

## 没读到的
- Table I（p.322）四类元件的伴随关系与灵敏度公式因扫描件公式 OCR 全毁，未能逐字核对（P1 引用时应改引教科书或 Director/Rohrer 后续频域论文的排版版本）。
- 非线性/时变情形的完整推导细节（式 (7)–(13) 的时间反转与横截条件处理）只在电容支路完整给出，电感"omitted"、耦合元件只举一例。
- 未读到任何与"对称网络/平衡结构/共模抑制"相关的字句——确认此篇与 H2 主题（差分 CMRR）仅通过"灵敏度方法"间接相连。
- 待核：p.320 式 (9) 附近 OCR 噪声较大，q̂_C(τ)=C·v̂_C(τ) 的符号方向建议对照 IEEE Xplore 排版原文再核一次。
