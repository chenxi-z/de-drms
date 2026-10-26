# 精读笔记 · Cutkosky 1970《Techniques for Comparing Four-Terminal-Pair Admittance Standards》（J. Res. NBS 74C(3&4), 63–78）

> 格式标准（全组沿用）：出处 → 核心命题（原文引用）→ 关键数值（原文）→ 对 P1/P2/P3 的对照 → 没读到的。
> 读法：pdftotext 全文逐节读，引用一律原文加页码；不转述成模糊话。
> 页码 = 期刊页（63–78）＝ PDF 页 1–16。扫描 OCR 本；引用仅合并断词空格，
> 公式区 OCR 噪声重处（式 (1)(2)、桥平衡式 (3)–(7)、(8)–(12)）照实标注。

## 核心命题（原文）

1. **四端对定义**：标准是 "a device in which the ratio of current in pair 3 to the open circuit voltage at pair 2, subject to the condition that both the voltage and current at pair 4 are zero, is the parameter of interest."（p.63，式 (1) 符号 OCR 噪声未读清）；其价值 "their relative insensitivities to variations in series impedances and shunt admittances in the leads as is implicit in (2)"（p.64，式 (2) 未读清）；另有互易定理 "P1[2] = P[34] for any four-pair network"（p.64，OCR 作 "P1~ = Pg"，下标未读清）。
2. **零净电流 = 定义的物理基础（绕开磁耦合）**："exactly the same current but with reversed sign in the inner wire of each cable as there is in the surrounding coaxial shield, and therefore the magnetic field exterior to both cables is zero. This eliminates possible mutual inductive couplings"（p.64）；并点名否决单地五端："the practice of dealing with five terminal standards having a single, common ground connection cannot be recommended."（p.64）
3. **比较时不必满足定义条件（与 Kelvin 直接同源，③核心）**："it is not necessary when comparing two such standards to satisfy any of the defining conditions; it is merely required that the same result be obtained for the ratio … as would have been obtained if the conditions had all been satisfied. … The Kelvin bridge for comparing four-terminal dc resistors also makes use of this principle, since currents exist in the potential leads of the resistors, but cause no errors."（p.65）；且辅助平衡与经典结构同构："the similarities between many of the auxiliary balance systems used here and common classical techniques, such as yoke and lead balancing in Kelvin double bridges, and the use of Wagner and conjugate Wagner arms in ac bridges, can be readily seen."（p.64）——但警告 "any attempt actually to construct a circuit without proper attention to the details of the shield return circuits would result in large and erratic errors dependent upon the accidental arrangement of the leads."（p.64–65）
4. **不对称/杂散的处置 = 逐项测出后修正（绕开 + 标定），不求匹配条件**：
   - 共轴扼流圈残余净电流："(Coaxial chokes) are effective in attenuating the net currents in the cables by a factor of several hundred. Unfortunately the net currents are not completely suppressed"（p.64）；用 voltage insertion transformer 逐个测误差，"An algebraic addition of the individual errors then gives the total error, which is applied as a correction to the raw results of the measurement."（p.66）
   - 隔离变压器的**绕组电容不对称**是实例："net currents can then result from unbalanced interwinding capacitances. If the interwinding capacitances are very poorly balanced, the effective ground loop voltage can be quite high, and the accurate measurement of the errors due to the resultant ground loop current is rather difficult. In such cases it is usually best to measure the current directly"（p.67）——失配致共模地环流，NBS 的对策是**直测修正**，不是推导失配消去条件。
   - 联结网络的设计要求最接近"匹配"语言："the admittances shunting the cables from the standards are **small, equal, and measurable**"（p.65，着重为引者）——是设计指标，无"失配→CM→DM 转换为零"的推导。
   - defining transformer 内屏蔽："Capacitance between the 100-turn winding and the connection between the inner connectors of A and B could cause substantial errors. An internal shield with a thin air gap as shown eliminates this problem. Incomplete shielding can be detected by interchanging A and B."（p.66）——消去 + 交换检测残余。
5. **变比误差靠换向平均一阶相消**：正桥式 (3) 后 "A repeat measurement is made with the connections interchanged at points A and B, and with the connections between T4 and the defining transformers T5 and T9 interchanged. This reverses the sign of δ to first order … Averaging (3) and (4) we have [(5)]"（p.68，式 (3)–(5) OCR 噪声未读清）；"The approximations made in deriving (6) and (7) cause no errors exceeding 2 parts in 10^10"（p.68）。
6. **定义端面（reference plane）语言**："The critical leads to the standards P1 and P2 are terminated at the reference planes of the defining transformers T7, T8, and T9, and the leads between these transformers and the standards are treated as part of the standards."（p.74）；星形接头同理："The admittances under test are considered to terminate at the internal junction points of the star connectors, rather than at the ends of the coaxial cables leading to the standards."（p.71）——**可复现端面 + 归属划分**是四端对的核心工程化。
7. 变压器误差机理定论："the key to achieving highly accurate and stable ratios … is to make generous use of multi-stage transformers with magnetic shielding between stages. The principal errors in such transformers are due to capacitive loading effects working on their output impedances. … The optimum number of turns on a shielded two-stage transformer … is believed to be less than 100 turns"（p.73–74）。

## 关键数值（原文）

- 全链目标："uncertainties must be kept smaller than 1 part in 10^8 over a large range of impedances at audiofrequencies"（p.63）
- 联结导线效应上限："unlikely to exceed a few parts in 10^7 at audiofrequencies, unless interconnecting cables longer than several meters are used"；长线无差条件是 "these cables are treated as part of the standard"（p.65）
- 正交桥：两只 10^4 Ω 四端对电阻 + 两只 1 nF 四端对电容，ω = 10^4 rad/s ≈ 1592 Hz（p.67）
- 25 只共轴扼流圈："The largest individual error was found to be 1 part in 10^10, and the total error … about 2 parts in 10^11."（p.70）；声耦合（磁致伸缩）消音/退磁后 "reduced to a few parts in 10^10"（p.67）
- 互调失真：撤滤波器 "apparent change in the bridge balance of several parts in 10^6"，加滤波器后 "less than 1 part in 10^9"（p.70）；"can be used to detect distortion products … up to at least the 15th harmonic"，但 "gives only an upper bound"（p.70）
- 滤波/噪声权衡（③P3 用）：单节 6 dB/oct 与双节 12 dB/oct 传递函数式 (9)(10)（OCR 噪声未读清）；"two cascaded filters with time constants of 0.3 s makes the portion of the detector noise due to oscillator noise about equal to that due to thermal agitation noise … Filters with 3-s time constants are normally employed"（p.71）；FM 噪声落实通道、AM 噪声落相位通道（p.71）
- 温控："P1, P2, P3, and P4 … maintained at 25±0.001 °C in an oil bath"；"The sum of all other errors, including that due to thermal agitation noise, is believed to be less than 1 part in 10^9."（p.71）
- DRRS：1592 Hz 分辨 "1 part in 10^10"，其余频点 "1 part in 10^9"；全盘线性 "within an estimated uncertainty of 3 parts in 10^10"；偏离 "never greater than 5 parts in 10^9"（p.74）；正交调节范围 159.2 Hz ±5×10^-5、15920 Hz ±5×10^-3（p.74）
- 等功率 100:1 桥：每电阻耗散 4×10^-3 W（20 V 于 P1）灵敏度可分辨 1 part in 10^9（p.77）；T14 200 匝并联电导 1.8×10^-5 S vs 被测 2×10^-5 S（p.77）
- 结论："all of the comparisons necessary for this work can be made with an overall uncertainty of a few parts in 10^8 … the largest source of uncertainty results from instabilities in the admittance standards"（p.77）

## 三问专项

① **杂散/泄漏/不对称——消去还是绕开？** 体系性"绕开 + 逐项修正"，辅以少量结构性消去：(a) 四端对定义本身把引线串阻/并导"定义掉"（式 (2)，exact 网络定理层面，非匹配）；(b) 零净电流靠共轴结构与扼流圈，残余误差**逐个测量、代数相加、作为修正项**（p.66）——"绕开不完就标定"；(c) defining transformer 内屏蔽、T4 换向平均、辅助检测器短接（"shorted to reduce the effect on the main detector of a slight error in these auxiliary balances", p.69）属消去/压低；(d) **绕组电容不对称→地环流**（p.67）被明文当作失配后果处理，对策是直测电流修正，**没有匹配条件推导**。
② **P1 反例搜索**：**全文没有**"无源 RC 差分网络失配→共模转差模"的消去条件推导。两个最接近的文本证据：p.65 "small, equal, and measurable"（匹配作为设计要求而非推导结论）；p.67 unbalanced interwinding capacitances（失配致共模误差的实例，处置=测量修正）。1964 理论文 [1]（四端对网络理论）可能含定义层面的严格性论证，但不在本文内。
③ **四端对 ↔ Kelvin（P2 计量级原型论证核心）**：本文是**最直接的权威引文**——(i) "The Kelvin bridge … also makes use of this principle, since currents exist in the potential leads … but cause no errors."（p.65）：Kelvin 四端是"比较时不需满足定义条件"原理的直流特例；(ii) 四端对把 Kelvin 的"电流端/电位端分离"推广为"四对同轴 + 各对零净电流"，并以互易定理保证定义无歧义（"no ambiguity in the definition as there would be if a single ground connection of unspecified placement were used", p.64）；(iii) 辅助平衡 ↔ "yoke and lead balancing in Kelvin double bridges" + Wagner 臂（p.64）；(iv) 星形接头 = Hamon 直流结点加地电位屏蔽（p.71）；(v) 与 Hall 的对比句明写 **"four-terminal (but not four-pair)"**（p.76）——四端与四端对的区别被作者自己点名。Kelvin 无源负端结构可据此论证"计量级同源、定义端面可复现"。

## 对 P1/P2/P3 的对照

- **P1（失配消去条件）**：本文是"反例检索的阴性对照"——NBS 四端对体系把失配处理到"定义免疫 + 换向平均 + 测量修正"三级，唯独没有 RC 差分网络匹配条件；可与 Whitlock 2004（匹配非充分、Zcm 载荷独立通道）并引，说明失配消去条件在计量界同样缺位。
- **P2（Kelvin 无源负端）**：p.64–65 两段是**计量级原型论证的主引文**；再加 p.71 星形接头"terminate at the internal junction points"、p.74 参考面归属，构成"定义端面可复现 ⇒ 比较与使用状态一致 ⇒ 无残余项"的完整证据链。
- **P3（AAF 衰减上界）**：§3 的单/双节滤波传递函数与噪声积分（式 (8)–(12)，p.70–71）+ "The advantage of using a two-section filter is obvious from figures 7 and 8 and from (11) and (12), and in addition the very strong dependence of [noise] on the filter bandwidth can be seen."（p.71）是无源滤波"衰减-带宽-噪声"权衡的原始定量；互调混叠回基带（p.70）与 1961 文 p.154 同判例，可作 P3 的历史对照。

## 没读到的

- 式 (1)(2)（四端对导纳定义与其引线免疫定理）符号层 OCR 噪声未读清；互易定理式下标未读清；桥平衡式 (3)–(7)、滤波传递函数 (8)–(12) 逐符号未读清（语义在正文可辨）。
- [1] Cutkosky 1964《Four-terminal-pair networks as precision admittance and impedance standards》Commun. and Electronics 70, 19–22——**四端对定义的理论原文**（P2 论证的上一级引文），无本地。
- [4] Thompson 1964 IEEE T-IM 13(4), 189–197（三端导纳交流桥、twin-tee 耦合网、多平衡理论）；[12] Cutkosky & Shields 1960（变比置换法）；Hall 1970 CPEM 等功率四端桥（脚注 2，IEEE T-IM 待刊）——均只引未附。
- DRRS 完整电路："a complete circuit of the existing bridge would be more exposing than revealing, and therefore no such circuit appears in this paper."（p.73）——作者故意不给。
