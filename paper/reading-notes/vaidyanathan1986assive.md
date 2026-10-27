# 精读笔记 · Vaidyanathan 1986《Passive Cascaded-Lattice Structures for Low-Sensitivity FIR Filter Design, with Applications to Filter Banks》（IEEE Trans. CAS-33, No.11）

> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。

## 出处
- bib：`vaidyanathan1986assive`，P. P. Vaidyanathan, "Passive cascaded-lattice structures for low-sensitivity FIR filter design, with applications to filter banks," *IEEE Transactions on Circuits and Systems*, vol. CAS-33, no. 11, pp. 1045–1064, Nov. 1986. DOI: 10.1109/tcs.1986.1085867。
- 全文：pdftotext 读自 `H8-灵敏度与统计电路设计/vaidyanathan1986assive.pdf`，PDF 共 20 物理页（物理页 1–20 = 期刊页 1045–1064，下文页码均指 PDF 物理页）。
- 主旨：把 IIR 领域的"结构无源性（structural passivity）→ 低通带灵敏度"思想移植到 FIR：用无损（LBR）2×2 平面旋转格形节级联，实现任意 M 分量 FIR 全通向量（功率互补滤波器组），并证明自动 L² 内部定标、舍入噪声增益 = 阶数 N、系数灵敏度有界。

## 核心命题（原文）
1. **结构无源性的定义与低灵敏度判据（本文的地基，p.2）**：
   > "An implementation is said to be structurally passive or structurally bounded [24] if, regardless of the multiplier values (as long as they are in a well-defined range such as - 1~ mk < l), the transfer function satisfies (1)." [OCR 损：`- 1~ mk < l` 应为 −1 ≤ m_k < 1；(1) 即 |H(e^jω)| ≤ 1]
   （只要乘法器取值在给定范围内、**无论具体数值**，传输函数都保持有界——这是"拓扑级保证"，不依赖参数匹配。）紧接其后的低灵敏度判据：
   > "If the multiplier values in a structurally passive implementation are such that ]H(ejw)| attains the upper bound of unity in the passband( then the structure has low passbandsensitivity [14], [24]." [OCR 损：括号为排版残缺]
   （结构无源 + 通带内幅度触及上界 1 ⇒ 低通带灵敏度——与经典无源双端接网络"达到最大功率传输界 ⇒ 一阶灵敏度为零"的 Bode/Orchard 论证同构。）

2. **无损互补（功率互补）等式是结构性质而非参数性质（p.2 定理陈述，p.14 结构论证）**：
   > "lG(ejw)12 + JH(ej”)J2 =l,             for all w.      (2)" [OCR 损：|G(e^jω)|² + |H(e^jω)|² = 1]
   以及第 VII-C 节的关键句：
   > "In view of this, ... the equality IPNml(e@)12 + lQ,,-l(ejw)12 + ... + IS,+l(ejw)12 =l holds for all w, regardless of the actual values of k,. In other words, each component of G,-,(z) is structurally bounded, and according to the discussions in Section II, we expect low passband sensitivity."
   （|P|²+|Q|²+…=1 对**任意**系数取值都成立——"互补性"由无损性结构地保证，不需要元件间匹配。）

3. **灵敏度偏导本身有界（p.14）**：
   > "which shows that each variational term in (100) is bounded above by unity. This gives us additional insight concerning low-sensitivity behavior of the cascaded-lattice structure. The partial derivatives with respect to k, also satisfy a relation similar to (100)."
   （∂G/∂k_m 的各变分项被 1 界住——因为偏导传输函数是 LBR 级联的子阵，灵敏度自机地被结构压住。）

4. **摘要级总结论（p.1）**：
   > "The structures can be used for the synthesis of any scalar FIR transfer function H(z) with no restriction onWhen implementing FIR digital filters..." [OCR 损，应为 "with no restriction on the location of zeros"]
   > "The structures have excellent passband sensitivity because of inherent passivity, and are automatically internally scaled, in an L, sense." [OCR 损：`L,` 应为 L²]
   （低灵敏度的原因被明确归因于**固有无源性**，定标也是自动的。）

5. **与连续时间经典网络理论的显式桥接（p.5）**：
   > "Since each building block in our structure of Fig. 3 is lossless, it is possible, in principle, to find a counterpart of our structures in the continuous-time domain. This can be done by employing the bilinear transformation and the wave-to-immittance transformations."
   （作者自己把该结构挂回经典无损网络/波数字滤波器谱系——H8 轴"经典网络理论"在数字域的直接后裔。参考文献 [1] 即 Fettweis "Digital filter structures related to classical filter networks"。）

6. **量化实验对照（p.6、p.19）**：
   > "Even though the direct form has somewhat better stopband performance, the passband details shown in Fig. 6(a) clearly demonstrate the excellent passbandbehavior of the lattice structure." （p.6）
   > "The 5-bit direct-form was found to have a performance comparable to the 3-bit lattice (Fig. 32)." （p.19）
   （3 bit 量化的格形 ≈ 5 bit 量化的直接型——低灵敏度优势的实测体现。）

## 关键数值（原文）
- 结构资源：一对 (N−1) 阶 FIR 传输函数需 "4(N - 1) + 2 multipliers, i.e., (2N - 1) per transfer function"（归一化格形）；去归一化节 "requires N + 1 multipliers per transfer function"（p.4）。
- 系数界：k_m² ≤ 1 且 k_m² + k̃_m² = 1（式 (13)(14)(23)，p.3–4）；线性相位时格形系数对称 k_m² = k²_{N−2−m}（式 (36)，p.5）。
- 舍入噪声：总输出噪声方差 σ²_total = N·σ_e²（式 (92)，p.14），与直接型相同（"the noise variance is given precisely by (92)"）。
- 例 1（p.5）：ωp = 0.1967π，ωs = 0.27π，δp < 0.0013，As > 32 dB，阶数 N−1 = 60；格形系数以 3 bit（canonic sign-digit，3 个 2 的幂之和）量化（p.5–6）。
- 例 2（p.9–10）：30 阶线性相位低通，带边 ωp = 0.04·2π、ωs = 0.10·2π，调制带通 ω₀ = 0.43·2π；4 bit/系数量化后响应接近理想（p.10）。
- 例 3（QMF，p.17–19）：2(N−1) = 38 阶零相位低通，ωp = 0.45π、ωs = 0.65π；整个分析滤波器组去归一化格形仅 20 个乘法器（p.19）；Table IV 给出 "Denormalised Lattice  20  3  60  10"（20 乘法器 × 3 bit = 60 bit-乘法器积，p.19，列名 OCR 损）。
- QMF 完全重构条件：|H₀(e^jω)|² + |H₁(e^jω)|² = 1（式 (120)，p.17）；偶数格形节无乘法器：k_m² = k̃_m² = 1/2，k_{2m} = 1（式 (127)，p.18）。

## 对 P1/P2/P3 的对照
- **P1（消去条件 / τ=R·C 匹配）**：无关。本文的"互补恒等式 |P|²+|Q|²=1"由无损性**结构地**成立、对任意系数成立，恰是"不靠元件匹配"的极端范例；与 P1 的"单级 τ 匹配充要、多级不充分"这类元件级消去条件无交集。相关度：低。
- **P2（Kelvin 结构地板 ≈56 dB）**：无关。全文无接地/共模/Kelvin 内容。相关度：无。
- **P3（平坦度约束下的衰减可达上界 = Bode-Fano/经典灵敏度理论）**：**中等相关（同族论证的数字域堂亲，非竞争者）**。本文给出了经典灵敏度论证最清晰的现代离散形式："结构无源 + 通带触及上界 ⇒ 低通带灵敏度"（p.2）与"偏导传输函数 LBR ⇒ 每个灵敏度项 ≤ 1"（p.14）。这正是 P3 引经典灵敏度理论的论证骨架在 FIR 格形上的翻版：**达到界 ⇒ 一阶灵敏度归零/受限**。但本文不提供任何模拟 RC 双端接网络的 Bode-Fano 型衰减–平坦度可达上界，也不涉及差分 RC 网络的失配条件，因此不构成对 P3 的先占；反而可作为 P3 论证普适性的跨域旁证引用。killRisk：**无威胁**（域不同：数字 FIR 格形 vs 模拟无源差分 AA 网络；引用时应划界说明"同一'无源+触界⇒低灵敏'原理的数字实例"）。
- **方法学（增量四 · D1–D10 门槛化）**：中等有用。本文示范了"把性能保证上收到**结构/拓扑层**（structural boundedness 对任意参数取值成立），从而把元件匹配问题消解掉"的论证范式，并附 3-bit vs 5-bit 的量化对照实验作为门槛化验证样例——可类比 P1 论文"结构层证明 + 数值实验门槛"的写法。

## 没读到的
- 全文 20 页已读（含全部定理、式 (1)–(127) 文本、三个设计例与结论）；Table I/II/III/IV 的完整列头与部分表体因 OCR 损无法逐字核对（不影响命题）。
- 参考文献列表仅扫读，未逐条核 [14][24]（Vaidyanathan–Mitra 两篇低灵敏度论文）原文——它们是"结构无源性→低灵敏度"命题的更早源头，若需追溯 P3 论证谱系应另行精读。
- 图 5/6/16/29/31/32 的曲线读数未做（OCR 无法还原图中数值），量化对比只引正文文字结论。
