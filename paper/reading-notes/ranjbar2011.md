# 精读笔记 · Ranjbar & Oliaei 2011《A Multibit Dual-Feedback CT ΔΣ Modulator With Lowpass Signal Transfer Function》（IEEE TCSI-I, 58(9):2083–2095）

> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> 读法：pdftotext -layout 全文逐节；刊印页码 2083–2095（PDF 页 N = 刊印页 2082+N）。数学公式内嵌为图形，公式内数值在文本层缺失（下文标「[式值缺失]」），均已核对正文可读数值。

## 出处

- Mohammad Ranjbar (Student Member, IEEE) 与 Omid Oliaei (Senior Member, IEEE)，IEEE Transactions on Circuits and Systems—I: Regular Papers, Vol. 58, No. 9, Sept. 2011, pp. 2083–2095，DOI 10.1109/TCSI.2011.2162464。
- 单位：University of Massachusetts, Amherst（成文时作者已分别赴 Cirrus Logic / Fujitsu Semiconductor Wireless Products）。
- bib key：`ranjbar2011`（H3-CT-ΣΔ 轴，P0 级正典——CT-ΣΔ 混叠抑制的结构性证据）。

## 核心命题（原文）

1. **CT-ΣΔ 的隐式抗混叠是架构级属性，可放宽对前置 AAF 的要求**（p.2083）：
   > "An interesting feature of CT-ΣΔ modulators is their implicit anti-aliasing [7] which relaxes the requirements of the A/D prefilter and thereby, reduces the overall system cost."
   （这是 D3 门"逃生门"论证的期刊正典表述：抗混叠由环内连续时间滤波完成，不是靠外部匹配 RC。）

2. **实测样机：70 dB 抗混叠、STF 无带外峰化**（p.2083 摘要）：
   > "a third-order delta-sigma modulator has been implemented and tested which achieves 76 dB dynamic range over 5 MHz signal bandwidth while consuming 6 mW from a 1.2 V supply. The prototype chip, fabricated in a 130 nm CMOS process, provides 70 dB anti-aliasing with no out-of-band peaking in the signal transfer function."

3. **前馈结构抗混叠差且峰化的根源 = 前向路径传函 FF(s) 的分子零点；无峰化的充要结构条件是 FF 为全极点**（p.2085）：
   > "These zeros limit the high frequency role-off of FF, and when combined with the NTF's out-of-band gain, they cause the STF to exhibit out-of-band peaking."（p.2085）
   > "In summary, comparing (6), (7), and (8) reveals that the key to a peaking-free STF is to make the forward path transfer function FF an all-pole filter."（p.2085）
   （与 P1 同构的"传函级精确条件"思维：不是靠元件配对，而是靠把分子非常数项整体约束为零——一种**结构性消零**。）

4. **消零靠系数精确成立、而非极零对消；系数一旦偏离即同时劣化峰化与抗混叠**（p.2086）：
   > "It should be emphasized that the goal here is to eliminate the zeros of FF by nulling out the nonconstant terms in (10) rather than pole-zero cancellation."（p.2086）
   > "any deviation of the coefficients that violates (11) will cause peaking in the STF and also degradation in anti-aliasing. Therefore, the STF of such a feedforward structure is sensitive to random and systematic component variation [26]."（p.2086）
   （**P1 命题的 CT-ΣΔ 镜像**：单点精确成立的消去条件对元件随机/系统失配敏感——这正是 P1"匹配只在标称点成立"论断的领域内证据。）

5. **双反馈结构把 FF 分子阶数从 N 阶压到低阶，从而结构性降低 STF 对系数失配的敏感度**（p.2086–2087）：
   > "In an Nth order modulator with dual-feedback structure the order of the numerator FF is in general [式值缺失]. Thus, one can immediately expect lower STF sensitivity to coefficient inaccuracy compared with a feedforward structure that the numerator of its FF is of Nth order (see (7))."（p.2086）
   > "the worst case STF of the dual-feedback and feedback modulators stay quite close to the ideal STF whereas the feedforward modulator shows significantly more deviation, particularly at higher frequencies."（p.2087）
   （方法论范式：**降低对匹配的依赖靠拓扑（降低失配增益），不靠提高匹配精度**——与 D1–D10 方法学同向。）

6. **反馈拓扑天然全极点、单一路径，抗混叠比低摆幅前馈多 55 dB**（p.2084）：
   > "In contrast, (6) indicates that FF in the case of the feedback modulator is an all-pole transfer function. This interesting property stems from the fact that there exists a single path between the input and the output of the modulator. … Consequently, not only does the STF become free of peaking, but it achieves 55 dB additional anti-aliasing near the sampling frequency."（p.2084–2085）

7. **实测失真根因 = 输入电阻失配 + CMFB 版图不对称**（p.2093，对 P1/P2 的直接呼应）：
   > "Postfabrication study has identified the input resistor mismatch combined with CMFB issues due to asymmetrical layout parasitics as the root cause."（p.2093，解释实测二阶谐波主导）

## 关键数值（原文）

- 样机性能（p.2093–2094）：76 dB DR / 5 MHz BW；fs = 160 MHz（p.2089）；峰值 SNDR 69.5 dB、峰值 SNR 74.5 dB；SFDR 74 dB（由 HD2 决定）；0.56 mm² 有源面积、0.13 µm CMOS、1.2 V 单电源、6 mW（p.2094）；FOM "0.123/0.246 pJ/conversion, based on the measured DR/SNDR respectively"（p.2094）。
- 抗混叠实测（p.2094）："maximum out-of-band gain of 0.1 dB at 10 MHz and a minimum anti-aliasing of 70 dB at 165 MHz"，测试法 = −? dBFS 带内 1.1 MHz 音 + 155–170 MHz 带外强音（数值部分在文本层缺失，方法在）。
- 架构对比（p.2084）：前馈 STF 带外峰化 11 dB；反馈-前馈混合比前馈多 30 dB 抗混叠、少 5 dB 峰化；反馈比低摆幅前馈多 55 dB 抗混叠。
- 蒙特卡洛（p.2087，Fig.6/7）：σ = 2% 系数失配、1000 次 MC：抗混叠从预期 100 dB 退化——反馈 1.5 dB、双反馈 3 dB、**前馈 33 dB**；除 STF 凹口频点外全程（dc 至 fs）STF 幅度标准差 < 1 dB。
- RC 时间常数容差（p.2090）：极点半径上限 0.75 对应 RC 变化窗口"[式值缺失] to 11%"；全系数量增加中值 4.5% 换稳定裕度，代价 SQNR 降 1.8 dB，调后 SQNR 极值 87.7/83.3 dB；RC 失配可用 4-bit 修调电容阵列吸收（"a 4-bit trimmed integration capacitor"，p.2090）。
- 放大器：两级米勒式，dc 增益 60 dB，GBW = 0.5/1.0/1.5 × fs（第 1/2/3 积分器，p.2089–2091）；第二积分器 kz2∈[2,8] 扫描，抗混叠最多改善 14 dB，稳定下限 kz2=[式值缺失]，选 4–5（p.2090）。

## 对 P1/P2/P3 的对照

- **P1（消去条件 G_DC(s)=H_N−H_P≡0）**：高度相关（镜像证据）。本文给出 P1 的"结构性解"范式：与其要求元件两两匹配（对失配敏感的**参数化消去**，如 (11) 系数精确成立——p.2086 明言偏离即劣化），不如改变拓扑使失配增益本身变小（FF 分子降阶、单一路径全极点）。P1 若主张"多级梯形下 τ 匹配不再充分"，本文第 5 条是该主张在 CT-ΣΔ 域的平行实证：前馈（多路径、N 阶分子）σ=2% 失配 → 33 dB 退化 vs 双反馈 3 dB。**但注意口径差异**：本文失配作用于 STF/抗混叠（幅度响应），不是 P1 的 G_DC(s)（差分到共模转换）——引用时须声明"同构证据，非同对象"。
- **P2（Kelvin 结构地板 ≈56 dB）**：间接。p.2093"输入电阻失配 + CMFB 版图不对称 = HD2 根因"是差分结构中电阻失配直接决定性能地板的又一实测证据（但这里是 THD 口径，非 CMRR 地板）。70 dB 抗混叠实测地板与 56 dB 量级同区间，但机制不同（环滤波 vs 结构泄漏），不可混引。
- **P3（平坦度约束衰减上界）**：相关。p.2084–2085 给出"STF 带外峰化 ↔ 前向传函分子零点"的解析闭环，且峰化上限由 NTF 带外增益决定（"A higher SQNR corresponds to … a larger peaking in the STF"，p.2085）——即**响应上界由结构参数锁死**的思想，与 P3"衰减上界受平坦度约束"同型；本文实测 OOB 增益 0.1 dB @ 10 MHz 即"平坦度代价"数值样本。
- **方法学（D1–D10 / 门槛化）**：直接可用。①σ=2% + 1000 MC + 只报 worst-case（p.2087）= D 系门槛化实验的期刊级模板；②"全极点 FF"是可判定的结构判据（非数值拟合），对应门槛法"先判结构后算数值"；③4-bit 电容修调吸收 RC 失配（p.2090）= 失配预算→修调位数的量化路径模板。
- **killRisk 判断**：无风险。本文与 killRisk 条目（ti_threeguidelines2015 误归勘误）无关，且作为 CT-ΣΔ 隐式抗混叠正典恰好是 **D3 门逃生门**的核心支撑文献（P0 定级成立）。注意它不提供任何"单级差分 RC 失配-CMRR 公式"，不能替代 killRisk 条目文献。

## 没读到的

- 公式内数值（(7)(8)(10)(11)(14)–(19)、MC 失配施加方式、kz2 稳定下限、RC 下限百分比、抗混叠测试信号电平）：PDF 数学符号未入文本层，仅图注/正文文字数值可用；如需精确复算须对照原刊图版（待核）。
- 参考文献 [7][18][26]（隐式抗混叠与鲁棒 STF 的上游出处：Shoaei & Snelgrove、Keller 等、Ranjbar ISCAS 2008）原件未读，若 P1 行文引用需另行精读。
- Table II 性能对比表的具体对手行数值（排版为表格，文本层仅残行）。
