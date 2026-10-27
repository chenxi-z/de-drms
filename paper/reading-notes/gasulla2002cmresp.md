# 精读笔记 · Gasulla 2000/2002《On the Common Mode Response of Fully Differential Circuits》（IEEE IMTC 2000, pp.1045–1049）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。

## 出处
- M. Gasulla, O. Casas, R. Pallàs-Areny, "On the Common Mode Response of Fully Differential Circuits," *Proc. 17th IEEE Instrumentation and Measurement Technology Conference (IMTC)*, pp. 1045–1049. 版权行 "0-7803-5890-2/00/$10.00 © 2000 IEEE"。bib 键 gasulla2002cmresp、年份记 2002、DOI 10.1109/imtc.2000.848900——**DOI 与版权行均为 IMTC 2000，bib 年份 2002 待核**（会议为 2000-05 巴尔的摩；不排除另有 2002 期刊版）。
- Universitat Politècnica de Catalunya, Barcelona；西班牙 CICYT TAP99-0742 资助。
- 扫描件 5 页，PDF pp.1–5 = 印刷页 1045–1049。OCR 把 µF 误识为 pF、下标/单位多处损，标 [OCR损]；页码按页脚 1045/1046/1047/1048/1049 核对。

## 核心命题（原文）
1. **总命题：CMRR 不完全描述共模响应，须用 G_DC 与 G_CC（p.1045, Abstract）**：
   > "Differential circuits are often described by their differential gain and common mode rejection ratio (CMRR). This approach, however, neglects the effect that the common mode signal has on the transient response and stability of the circuit. This work shows that the actual behavior of differential circuits in front of common mode voltages is completely described by the common-to-differential mode gain and the common-mode gain. The CMRR is useful to assess common mode errors in the frequency domain, but some circuits that achieve a large CMRR have long transients or are unstable."
2. **G_DC 框架与理想消去目标（p.1045）**：
   > "Because the information is embedded in the differential voltage, we ideally wish GDC = 0. Having GCC = 0 is also convenient, but it is less important if the following stage rejects common mode signals. In practice, however, GDC ≠ 0 and we define the CMRR as CMRR = GDD/GDC (2)"
   （全差分电路四传递函数描述；CMRR 只覆盖 G_DD/G_DC 一个比值。）
3. **★失配→G_DC(s) 闭式——单级差分 RC 高通的容差分析（p.1045，式 (4)(5)）——本批最接近 P1 的公式**：
   > "Considering component tolerances in a worst case situation, R1 = R(1+α), C1 = C(1+β), R1' = R(1−α), C1' = C(1−β) (4) ... yields GDC = ± 2(α+β)RCs / [(1+RCs)(1+(R+2Rc)Cs)] (5) where we have assumed Rc >> R."
   （**失配和 (α+β) 线性进入 G_DC 分子**——即一阶近似下 G_DC ≡ 0 ⟺ α+β = 0（互补容差），这就是单级"τ 匹配"型消去条件的一阶形态；本文只把它当误差公式用，**未当消去条件定理展开、无充要性讨论、无多级级联**。Rc = 0（去耦）时另有式 (7)，排版 [OCR损]。）
4. **大 Rc 抬 CMRR 的代价：慢瞬态尾（p.1045）**：
   > "Increasing Rc reduces Ap and increases CMRR, both of which are desirable, but also lengthens tp and the decaying exponential tail, which are undesirable."
   > "Therefore, the CMRR has improved at the cost of a slower transient response."（p.1045 末）
   （共模阶跃下差分输出不是 G_DD 的阶跃响应而是 G_DC 的带通响应（Fig.3）；Rc→∞ 虽使频域 CMRR→∞，但尾时间常数 2RcC1 拖长建立。）
5. **★★结构性 G_DC = 0：浮容高通（p.1046, Figure 4）——拓扑消去先例**：
   > "Figure 4 shows a differential filter that does not need any grounded resistor to provide a bias path for the following amplifier. The input common mode voltage yields an output common mode voltage with the same amplitude (GCC = 1) and cannot yield any differential output voltage. Hence, GDC = 0 and CMRR = ∞. The frequency response for the differential voltage can be designed to be the same as in Figure 2. Therefore, circuits with the same differential response can have quite different common mode response."
   > （p.1046 实验）"The filter in Figure 4 yields a zero output, as expected."
   （**与 P1「消去条件」直接同域**：存在一类拓扑（浮容/不对称高通，出典其引文 [2] 浮容差分单元）使 G_DC **与元件值无关地恒为零**——参数匹配路线之外的第二条精确消去路线。注意代价：G_CC = 1（共模全透传），靠后级再抑。）
6. **G_CC 致不稳 + 稳定性-CMRR 折衷（p.1046，式 (10)）**：
   > "Some circuits with high CMRR are unstable. Da Cunha [5] built a fully differential, second-order, low-pass filter based on a common Sallen and Key circuit that revealed to be oscillation-prone. We have analyzed that circuit and traced its instability to GCC. The CMRR would not explain that oscillation. Splitting capacitors and adding a small capacitance to ground (CC in Figure 5) stabilizes the circuit at the cost of a reduced CMRR."
   > "which has resonance with amplitude M ≈ √(C/(2CC)) [OCR损，按上下文复原] at f = 1/(2πR√(CCc/2)) [OCR损]. If CC is close to zero, M tends to infinite, thus rendering the circuit unstable. Increasing CC reduces M (and f) but also the CMRR at low frequencies."
   > （p.1047）"Hence, there is a trade off between stability and CMRR, as anticipated by the theoretical analysis."
7. **结论（p.1048）**：
   > "The common mode response of differential circuits is not fully described by the CMRR but by the common-to-differential mode gain (GDC) and the common mode gain (GCC). Their analysis reveals shortcomings such as long transient response and potential instability. Equation (3) is still useful to assess common mode errors in the frequency domain, but some circuits that achieve a large CMRR have long transients or are unstable."

## 关键数值（原文）
- 理论算例（p.1045）：R = 100 kΩ，C = 1 µF [OCR损 µF→pF，由 1.59 Hz 与 100 ms 反推]，A = 1 V，α = 5%，β = 10% → 去耦滤滤 Ap = 110 mV、tp = 100 ms；t = 1 s 时输出仅 163 pV。Rc = 1 MΩ：CMRR 提升 26 dB、Ap ≈ 15 mV、tp = 300 ms；但尾由 2RcC1 决定，1 s 后输出 9.3 mV（**为去耦滤的 57 倍**）；输出降到 163 pV 需 Rc = 1 MΩ 时 t = 9.5 s、Rc = 10 MΩ 时 t = 45 s。
- 实验（p.1046–1047）：Fig.2 电路 R1 = R1' = 100 kΩ、C1 = C1' = 1 µF [OCR损同上]；INA114 增益 100。实测：去耦 Ap = 3.56 V、tp = 100 ms → 按式 (8) 反推 **α+β = 4.8%**；Rc = 1 MΩ 时 Ap = 0.35 V、tp = 320 ms，t = 1 s 输出仍 0.27 V；**Fig.4 滤波器输出为零**。
- 二阶 LPF（Fig.5, p.1047）：TL072，R1 = R1' = R2 = R2' = 1.6 kΩ，C = 100 pF [OCR损"1 pF"，按 −3 dB 角频 1 MHz 与 1.6 kΩ 反推为 100 pF，待核]，Cc = 100 nF / 10 nF / 100 pF 三档；Fig.8/9：Cc 大→G_cc 谐振峰与频率都降，但低频 CMRR 也降。
- Fig.7：高频段实测 CMRR 由 INA114 自身决定（其值低于前级滤滤时）。

## 对 P1/P2/P3 的对照
- **P1（消去条件）**：**高（本批最接近者之一）**。① 式 (5) 即单级差分 RC 高通在容差下的 G_DC(s) 闭式——失配 (α+β) 线性入分子，一阶消去条件即 α+β = 0，与 P1"单级 τ 匹配"同型；② **Figure 4 给出拓扑级精确消去（G_DC ≡ 0 与元件值无关）的先例**。P1 未被杀的原因与增量：Gasulla 未把消去条件命题化（无充要性、无"多级梯形不再充分"、无全频段精确性讨论；式 (5) 只到一阶容差近似且用于误差估计）；P1 若主张"参数匹配路线"的充要条件与多级不可充分性，须把 Gasulla 式 (5) 作为单级一阶基线引用、把 Fig.4 浮容拓扑作为"拓扑消去"对照路线点名。**killRisk：中**（不是证伪风险，是"必须引用并划界"的风险）。
- **P2（Kelvin 结构地板）**：**低**。无失配统计→CMRR 地板的定量模型；仅 Fig.2 数例给出 α+β=4.8% 的实测失配与 26 dB/十倍 Rc 的 CMRR 改善量级，可作 P2 的旁证素材（失配决定一切、加大 Rc 只换得慢尾）。
- **P3（平坦度约束衰减上界）**：**中-低**。本文折衷是"稳定性(Cc) ↔ CMRR"（p.1047）与"CMRR ↔ 瞬态尾长（2RcC1）"（p.1045），同为频域受限的共模性能折衷，但不是"衰减上界 vs 通带平坦度"那条轴；可作为 P3 写作中"差分滤滤频域折衷谱系"的邻居引用。
- **方法学（D1–D10）**：**中**。示范了"不要只报 CMRR 标量、要报 G_DC 与 G_CC 两个传递函数 + 瞬态/稳定性后果"的评测观——与 D 系门槛化方法学（把指标拆成可判据化的子量）同方向；其"频域 CMRR 好 ≠ 时域行为好"结论是门槛化设计判据的直接论据。
- **killRisk 判断：中（P1 轴）**。最接近表述 = 式 (5)（逐字见核心命题 3）与 Figure 4 段（核心命题 5）。二者都未触及 P1 的核心定理内容（充要条件 + 多级不可充分 + 全频段精确消去），但**任何 P1 论文不引 Gasulla 2000 将构成相关工作缺口**。

## 没读到的
- 式 (6)(7)(8)（共模阶跃响应 v_od(t)、峰值 Ap、峰时 tp 的完整表达式）OCR 排版严重受损，仅可靠引出数值与结论；式 (10) 完整形式 [OCR损]。
- Figure 2/3/4/5 的电路拓扑细节（图不进 OCR）：Fig.4"asymmetrical high-pass filter"的精确连接方式（浮容如何摆）未能从文本复原，需看图核对——**这决定其 G_DC=0 是否真与元件值无关**（文本声称 "cannot yield any differential output voltage"，且实验零输出，倾向成立，仍待核图）。
- bib 年份 2002 vs 版权行 2000 的差异未决（可能有期刊版或 bib 错记，待核）。
- 引文 [5] Da Cunha 1994（HP Journal）、[6] White 1987（三运放仪放相位补偿）、[7] Casas & Pallas-Areny 1996 "Basics of analog differential filters"（库中已有 casas1996basics.pdf，待另读）未读。
