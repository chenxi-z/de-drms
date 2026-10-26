# 精读笔记 · Cutkosky 1961《Evaluation of the NBS Unit of Resistance Based on a Computable Capacitor》（J. Res. NBS 65A(3), 147–158）

> 格式标准（全组沿用）：出处 → 核心命题（原文引用）→ 关键数值（原文）→ 对 P1/P2/P3 的对照 → 没读到的。
> 读法：pdftotext 全文逐节读，引用一律原文加页码；不转述成模糊话。
> 页码 = 期刊页（147–158）＝ PDF 页 1–12。本件为扫描 OCR 本（Acrobat Paper Capture），
> 引用时仅合并 OCR 断词空格、把 O/0 还原为 C/G 等明显字符噪声，词句未改；
> 公式区 OCR 噪声重处照实标注。

## 核心命题（原文）

1. 可计算电容（Thompson–Lampard 交叉电容）使 C 只依赖单一长度测量："This relationship allows C to be calculated from a single measured length L."（p.148）
   且两次不同接地组合的测量取平均可消端部不对称："The difference between the two cross capacitances so measured is not affected by irregularities or lack of perfect centering of the bars near the insulated gap, provided that the end sections are not rotated or otherwise disturbed when the 10-in. bars are removed or replaced."（p.149）
2. **杂散/泄漏处理（①的核心证据）**——三处独立机制：
   - **几何守卫 + 外屏蔽（绕开）**："Additional shields not shown in figure 2 eliminate capacitive coupling between electrodes around the outside of the grounded electrodes. This is essential, since (1) deals only with the capacitance associated with the region in the interior of the electrode system."（p.148）
   - **共地引线电感误差项的消去 + 外推**："Thompson [5] has shown that if the capacitor is treated as a four-terminal network as in figure 5 with a high permeability core linking one ground lead with one active electrode lead, the troublesome error term is eliminated. … It is impossible with the NBS cross capacitor to completely eliminate all common ground lead inductance in this way, and a small inductance L1′ remains … We have found it necessary to measure Ceff as a function of frequency and extrapolate to zero frequency under the assumption that the error is proportional to ω²."（p.149–150）——**先消后外推**：主项用高导磁芯（四端接法）消掉，残留项按 ω² 外推到零频。
   - **泄漏路径重排到无效点（绕开）**：Wien 桥的死因是 "If this arm is shielded, leakage currents from their common point to the shield produce errors which are difficult to evaluate with high accuracy."（p.151）；改用双桥（fig.7/8）后 "leakage paths to ground are either across the detector, which at balance has no voltage on it, or across one of the generators, which is assumed to have a very low impedance."（p.151）——泄漏不是被匹配掉，而是被拓扑赶到零电位检测器 / 低阻源上。
3. **屏蔽把测量定义成"直接电容"（三端定义绕开连接问题）**："Shielding completely surrounds each of the capacitors in the circuit in such a way that the measurement compares the direct capacitances C1 and C2."（p.150）
4. **双替换对称消泄漏（消去，靠结构不靠匹配）**：直流比较电路 fig.17 "shows the provision for eliminating the effect of leakage resistances R3 and R4 to the shield. The bridge is balanced first with point (1) grounded … and then with point (2) grounded … Neither balance depends upon R4, and a large R3 affects the two balances equally with opposite sign; hence the average balance gives the ratio"（p.155）；并强调 "measurements are made between the same junctions used in the a-c measurement"（p.155）——交流/直流在**同一物理接点**间定义，端面一致性即误差控制。
5. **残余参数入方程后取平均**：fig.8 明列 "the residual leakage conductances g1 and g2 of the main capacitors C1 and C2, and the stray capacitances [of] the main conductance standards G1 and G2"（p.151，OCR 电容符号噪声），近似式 (2)(3) "where bars over letters signify the average of the two values involved"（p.152）——不对称残余不求"匹配消去条件"，而是**两次测量平均一阶相消**。
6. **传输标准的守卫环＝电场不被被测件扰动（绕开）**："Since the wire does not change the electric field within the resistor assembly, we may expect no capacitance contribution to the resistor phase angle and a-c-d-c resistance difference."（p.156）；且实证校核 "even with all of the guard rings grounded, the measured a-c resistance is equal to the a-c resistance with all guards connected properly … the phase angle change between the two guard arrangements is less than 3 microradians."（p.156）

## 关键数值（原文）

- 最终值："ΩNBU = 1.000002 3 ohms ± 2.1 ppm"（摘要 p.147，OCR 作 "flB U= l.000002 3 ohms ± 2.1 ppm"）；结论节 "the NBS unit of resistance is 1.0000023 ohms"（p.157）；不确定度口径 "an estimated 50 percent error … c = 2.997925 × 10^10 cm/sec"（p.147）
- 三端高对地电容的误差项："the important error, expressed as an additive term, is −ω²L1C2C3; which is independent of C1 and hence relatively more important for a very small C1"（p.149）
- 10:1 变压器步进总不确定度 <1 ppm 要求比例已知 "to an accuracy of about two parts in 10^8"（p.150）；实测加载比例 α″ ≈ +17×10⁻⁶、β″ ≈ −16×10⁻⁶（p.152）
- 频率测量 "better than 5 parts in 10^8"（p.154）；检测灵敏度 "one part in 10^7 in magnitude or 10^-7 radians in phase angle"（p.154）
- 谐波滤波器："second and third harmonic signal levels are attenuated 140 db with respect to the fundamental, and all higher harmonics by at least 95 db"；"stray pickup to the filters cannot produce an error as large as one part in 10^7"（p.154）
- 传输标准：直丝 0.0008 in. 径 × 9.5 in. 长 = 1000 Ω；L = 1.1 µH → 相角 11 µrad；守卫环验证相角变化 <3 µrad（p.156）
- a-c–d-c 差："G1 and G2 have identical a-c-d-c differences and that their a-c resistances are 0.85 ppm higher than their d-c resistances"；相角两法 16.6 vs 15.0 µrad，差 1.6 µrad（p.157）
- Table 3 不确定度（p.157）：可计算电容 2.0 / 基准不稳 0.3 / 10:1 步进×5 0.1 / 频桥 0.3 / 电阻频响 0.3 / 直流步进 0.3 ppm → 合计 2.1 ppm；"The estimates are in most cases little more than guesses"（p.157）
- Table 4（p.158）：Thomas 0.999997、Rayner 1.000004、Romanowski & Olson 0.999996、本文 1.0000023

## 三问专项

① **杂散电容/泄漏/不对称——消去还是绕开？** 两者都用、分层处置：(a) 几何守卫 + 外屏蔽 + 三端"直接电容"定义把杂散**定义到测量之外**（绕开）；(b) 泄漏重排到零电位检测器/低阻源（绕开）；(c) 直流双替换 "equally with opposite sign" 平均**精确消去**泄漏项（消去，靠对称结构）；(d) 共地电感 ω²L1C2C3 主项用四端 + 高导磁芯消、残留项按 ω² 外推（消 + 标定补偿）。**没有任何一处靠"元件匹配"救场。**
② **P1 反例搜索（无源 RC 差分网络失配→共模转差模的消去条件推导）**：**没有**。最接近的三处：双替换平均消泄漏（p.155）、ω² 外推消共地项（p.150）、式 (2)(3) 对 g1/g2/𝒞1/𝒞2 残余取平均（p.151–152）——都是"对称测量相消/外推"，不是"RC 网络失配条件使 CM→DM 转换为零"的推导。Wien 桥一节（p.151）描述的正是 R–C 串臂屏蔽后共模泄漏转差模误差，但 NBS 的答案是**换拓扑绕开**，未给匹配条件。
③ **四端对 ↔ Kelvin**：本文是前身而非四端对——三端"直接电容"定义（p.150）+ Thompson 四端接法处理引线（p.149）+ 六角桥心把结点物理定死 "capacitance and conductance between segments arises only from external elements that are connected between pairs of coaxial connectors"（p.152）+ "measurements are made between the same junctions used in the a-c measurement"（p.155）= 计量级"定义端面一致性"原型。四端对的系统化在 1970 文（H7_cutkosky1970）。

## 对 P1/P2/P3 的对照

- **P1（失配消去条件）**：本文给的是**"消去/绕开二分法"的正史证据链**——NBS 传统里失配从来不靠匹配消，靠 (i) 定义（三端直接电容）、(ii) 对称双替换、(iii) 高导磁芯 + 外推。写 Discussion 时可引 p.151 Wien 桥段作"共模泄漏→差模误差在串联 RC 臂上不可评估"的历史判例，正好支撑 P1"须显式给消去条件、否则只能绕开"的立论。
- **P2（Kelvin 无源负端）**：p.149 四端接法消共地电感项 + p.155"同一结点测交流/直流"是 Kelvin 定义端面思想在电容侧的体现；与 1970 文的 "yoke and lead balancing in Kelvin double bridges"（1970 文 p.64）连成谱系。
- **P3（AAF 衰减上界）**：p.154 滤波器定量（2/3 次谐波 −140 dB、高次 ≥−95 dB）+ "two or more harmonics may mix in the nonlinear first stages of the amplifiers to produce apparent fundamental frequency signals"（p.154）＝ 无源滤波衰减不足→非线性混叠回基带的经典定量判例；滤波器去耦实验 "removing … balance change was less than one part in 10^7"（p.154 末）。

## 没读到的

- 式 (1)（交叉电容定理闭式）与式 (2)(3)、式 (5) 的具体系数：OCR 噪声未读清（上下文语义可辨，逐符号不敢照抄）。
- [5] Thompson, "The precise measurement of small capacitances," IRE Trans. Instr. I-7 (Dec. 1958)——共地电感四端消去法的原始推导处，无本地。
- [7] Cutkosky & Shields 1960（变比 2×10^-8 校准法）、[6] McGregor et al.（桥元件详述）均只引未附。
- 正文未讨论任何"RC 差分/平衡网络匹配条件"（故 ② 的结论是"全文确无"，非"没找到段落"）。
