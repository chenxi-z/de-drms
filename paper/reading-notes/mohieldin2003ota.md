# 精读笔记 · Mohieldin, Sánchez-Sinencio & Silva-Martínez 2003《A Fully Balanced Pseudo-Differential OTA With Common-Mode Feedforward and Inherent Common-Mode Feedback Detector》（IEEE JSSC 38(4):663–668）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> 页码用期刊页（663–668）；PDF 页 1–6 与之差 662。注意：JSSC 双栏公式全部嵌图，**文本层公式
> （eq.1–9）完全丢失**，本笔记只引用文本层可靠的散文与实测数值；失真 dB 原文按正数印刷（疑为
> 负值约定，已标待核）。

## 出处
- Mohieldin, A.N., Sánchez-Sinencio, E., Silva-Martínez, J., "A Fully Balanced Pseudo-Differential OTA With Common-Mode Feedforward and Inherent Common-Mode Feedback Detector", IEEE J. Solid-State Circuits, vol. 38, no. 4, pp. 663–668, Apr. 2003. doi:10.1109/JSSC.2003.809520.
- 本地：`H2-差分CMRR/mohieldin2003ota.pdf`（6 页）。bib key：`mohieldin2003ota`（literature.bib L1356）。

## 核心命题（原文）

1. **伪差分 OTA 去尾电流源 → 共模增益失控，必须靠 CMFF/CMFB 补**（p.663）：
   > "In general, a fully differential structure has an improved dynamic range over its single-ended counterpart. This is due to the properties of any differential structure, namely, better common-mode noise rejection, better distortion performance, and increased output voltage swing."（p.663）
   > "Removing the tail current source, however, results in poor common-mode gain, which will lead to significant variations at the OTA outputs unless a fast and strong CMFB is used."（p.663）
   中文：差分结构 CMR 的动机陈述与伪差分的代价——共模稳定是有源差分链的额外工程负担（无源网络无此负担，P1 背景对照）。

2. **CMFF 只压交流共模、稳不住直流工作点；两技术合流靠"级联下一个 OTA 充当检测器"**（p.664）：
   > "Using a common-mode feedforward (CMFF) technique [1], as shown in Fig. 1, reduces [the common-mode gain] at low frequency to the order of unity…"（p.663）
   > "Although CMFF improves the rejection to the common-mode signal components at the output, it is incapable of properly fixing the dc common-mode output voltage."（p.664）
   > "In fact, the same effect (CMFB) can be obtained by judiciously connecting at least two of the proposed OTAs. The connection at the output stage is taken from [the output] of the next stage, which is now sensing the common-mode level of the output (input of the next stage)."（p.664）
   中文：级联 OTA 的共模控制分工——每级 CMRR 不必各自完美，链级可以共享检测/稳定（系统级 CM 管理的编排规则）。

3. **共模抑制与失真耦合：环路失配与 CM×DM 交叉项直接产偶次失真**（p.665）：
   > "The nonlinear characteristic of the transistors together with any unbalance in the common-mode loop gain, due to mismatches, results in second- and third-order harmonic distortions at the differential output signal [3]."（p.665）
   > "Additional differential harmonic distortion components can also appear, even neglecting all mismatches, due to the cross product of differential and common-mode signals; hence, the common-mode signals have to be suppressed as much as possible [1]."（p.665）
   > "…the linearization of the output current relies on the cancellation of the quadratic components of the individual currents. Due to transistor mismatches, this cancellation is not perfect and some second-order harmonic distortion components will result."（p.665）
   中文：**"依赖对消的线性化会被失配破坏"**——与 P1 的主题句（结构性对消 ≠ 实际精确）同向，但对象是晶体管二次项而非无源 RC 传递函数。

4. **实测 CMRR 定义与数值**（p.667）：
   > "The measured CMRR, defined as the ratio of the differential-mode gain to the common-mode gain [5], of the OTA is 58 dB at low frequencies, and the measured input referred noise spectral density is 9.8 nV/√Hz at 50 MHz."（p.667）
   > "HD2 is small (≥37 dB) due to the even-order harmonic cancellation of the CMFF, and HD3 is measured around 43 dB."（p.667）
   > "The measured filter's CMRR, PSRR+, and PSRR− at 10 MHz (50 MHz) is 45 dB (32 dB), 26 dB (21 dB), and 35 dB (28 dB), respectively, and its current consumption is 26 mA."（p.667–668）

## 关键数值（原文）
- OTA/工艺：0.5 µm AMI CMOS（MOSIS）；1.65 V 供电；42.9 mW 每复极点对（Abstract, p.663）；芯片面积 450×350 µm²（**待核**，文本层残缺"450 350 m"）；电流 26 mA（p.668）。
- 失真：HD3 = 43 dB @ 900 mVpp、30 MHz（p.663）；HD2 ≥37 dB、HD3 ≈43 dB（p.667）；IM3 ≈40 dB @99/101 MHz 双音 350 mV（p.667）。（dB 按原文正数印刷，疑为低于载波的分贝数，**符号约定待核**。）
- 滤波器：100 MHz 四阶线性相位 Bessel–Thomson OTA-C；群时延纹波 3%（≤100 MHz）；DR 45 dB @THD 46 dB；输出总噪声 ~700 µV（100 MHz 带内）（p.663, 667）。
- **CMRR：OTA 58 dB @低频；滤波器 45 dB @10 MHz → 32 dB @50 MHz**（p.667–668）——高频 CMRR 随频率约 −20 dB/dec 量级退化。

## 对 P1/P2/P3 的对照
- **P1（消去条件）**：相关度 **低**。有源共模控制（CMFF/CMFB），无无源网络消去条件；"cancellation is not perfect due to mismatches"是同主题不同机制。killRisk：**无**。
- **P2（Kelvin 地板 ≈56 dB）**：相关度 **低-中**。OTA 实测 CMRR 58 dB @LF 与 P2 的 ≈56 dB 数值巧合（机制完全不同：有源器件失配 vs 无源结构地板）——只可作"实测差分链 CMRR 普遍落在 50–60 dB 区"的外部参照，**不可**引作 Kelvin 结构先例。滤波器级 45 dB@10 MHz→32 dB@50 MHz 的高频退化形态与 P2 的频率依赖地板讨论可互为背景。
- **P3（平坦度约束衰减上界）**：相关度 **无/低**。群时延纹波 3% 是实测指标，非权衡界。
- **方法学（D1–D10）**：可取之处是系统级共模编排规则（"The output common-mode level needs to be fixed only once for any number of OTAs sharing the same output" p.667）与"CM 残留→偶次失真"的误差传播清单；对无源 AAF + ΣΔ 场景只是背景。
- **killRisk 总评：无**。

## 没读到的
- **全部公式 eq.(1)–(9)**（文本层丢失，未渲染核对；引用公式须回原刊）。
- 任何无源差分网络/AAF 内容、消去条件或失配→CM 误差解析。
- CMRR 58 dB 的成因分解（器件失配多大贡献、CMFF 余项多大）。
- P1/P2/P3 相关的滤波器平坦度-衰减权衡。
