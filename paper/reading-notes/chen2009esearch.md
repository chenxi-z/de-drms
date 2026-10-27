# 精读笔记 · Chen 2009《Research and Design of Multi-channel Programmable Anti-Aliasing Filter Circuit》（IJCAI 2009）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> H1 轴"配方线"典型样本：**给全 R/C 取值配方（四阶 Butterworth + CD4051 切换 8 档截止频率），理由只有定性一句"带内要平坦"，零失配分析、零 dB 级混叠抑制预算**。
> 原文为中式英语写作（语法多处不通），引用一律照录。

## 出处
- CHEN Yu（郑州航空工业管理学院）, "Research and Design of Multi-channel Programmable Anti-Aliasing Filter Circuit," *2009 International Joint Conference on Artificial Intelligence (JCAI)*, pp. 845–848. DOI: 10.1109/jcai.2009.134。
- 本地文件 `fulltext/H1-ΣΔ-AAF/chen2009esearch.pdf`，4 页。**页码换算**：PDF p.1–p.4 = 期刊 pp.845–848。

## 核心命题（原文）
1. **配方本体：多通道可编程四阶有源 Butterworth 低通（数据采集卡发控制信号切截止频率），200 Hz–15 kHz 可调**（p.1, Abstract）：
   > "This paper design a multi-channel four-step active Butterworth low-passing filter, which can realize multi-channel cutoff frequency adjustable anti-aliasing design by data collection card sending controlling signal, and effectively improve monitor precision. This circuit has good application in electric power quality monitor and can complete 200Hz~15kHz cut-off frequency programmable adjusting"
   （用途 = 电力质量监测的 VI 虚拟仪器系统；"four-step" = fourth-order。）
2. **选 Butterworth 的全部"理由"：带内平坦 + 过渡带尽快下降（定性一句话）**（p.2, III）：
   > "Aiming to the system for harmonic power needs, the requirements in the band width should be flat with the characteristics; frequency should decrease as soon as possible when it higher than w0. Therefore, the system selected Butterworth-type low-pass filter design."
   > "Butterworth filter can be achieved similar to the ideal characteristics, which has flat amplitude, that is to say, their amplitude-frequency characteristics is almost completely flat until 3dB cut-off frequency wc. But in cut-off frequency nearly to the peak since there on the step response overshoot and ringing, medium pace of decline in the transitional zone a drop of 6ndB/octave (where n is the order of filter), applicable to the general filter."
   （"6ndB/octave" 即 6n dB/倍频程；四阶 = 24 dB/oct。选型理由止步于教科书特性描述——没有任何量化权衡。）
3. **截止频率定值依据 = 国标谐波测量范围（0–2500 Hz，50 次谐波）**（p.2, III）：
   > "Power quality in accordance with national standards is \"the number of harmonic measurement in general for the first 2 to the 19th\", \"A-class range of frequency measurement apparatus 0~2500Hz\", 50 times during the design of harmonic anti-aliasing filter cut-off frequency of 2.5kHz, higher frequency signal components of the content is very small, caused by the phenomenon of spectrum-aliasing is not sufficient for measuring impact."
   （2.5 kHz = 50 Hz × 50 次；"更高频率分量含量少、混叠不足以影响测量"是**无量化支撑的断言**——典型配方文风。）
4. **归一化设计公式与取值链：C 定 0.1 µF → Z=C0/(C1·2πfp) → R=Z·R0 → 四只电阻按标称值圆整**（p.3, IV-C）：
   > "When we set C1 = C2 = C3 = C4 = 0.1uF (103), by the formula (3): ... =636.62Ω. By the formula of R=Z·R0, and we will get Ra1=636.62×1.3065=831.74Ω, Ra2=636.62×0.7654=487.27Ω, Ra3=636.62×0.5411=344.48Ω, Ra4=636.62×1.848=1176.47Ω. According to the nominal value of resistor capacitor selection: Ra1=820Ω，Ra2=470Ω，Ra3=330Ω，Ra4=1.2kΩ."
   （归一化极点对：Hn1(s)=1/(s²+0.7654s+1)、Hn2(s)=1/(s²+1.848s+1)，p.2；增益 k1=k2=2，Rg=1 Ω。**标称圆整后对截止频率/Q 的影响零分析**——这是 P1 所要补的"匹配条件缺失"的原文级实例。）
5. **可编程实现：采集卡 3 根地址线控 CD4051 八选一电阻网络 + ADG409 双通道多路器解决 6 路(三相 V/I)同步采样**（p.3–4, V）：
   > "From the data acquisition card drawn 3 Address Line 4 programming to control the election of eight analog switches in a chip CD4051, by changing the resistor Ra1, Ra2, Ra3, Ra4 value, in order to achieve eight-way adjustable cut-off frequency of anti-aliasing filter circuit design ."
   > "Dual-channel multi-way selector switch is based on Analog Devices of the ADG409. ADG409 has two sets of a total of four pairs of inputs, two outputs."（p.3, V-A）
   （八档 fp：200, 400, 600, 1.25k, 2.5k, 5k, 10k, 20 kHz，p.4, Table II。）
6. **验证方式仅为一次谐波分析演示（无滤波器实测频响、无混叠抑制量测）**（p.4, VI）：
   > "through the anti-aliasing filter circuit, out of cut-off frequency's high-order harmonic and noise interference can be effectively filtered."
   （Table III：采样 10000 Hz、30000 点，测得 3/5/7 次谐波，THD 38.44%——**只在 2.5 kHz 档做了一次演示**。）

## 关键数值（原文）
- 拓扑：四阶 Butterworth = 两个二阶节级联（Sallen-Key 型有源，图 3/图 4），带内增益 k=2（p.2–3）。
- 归一化参数：1/R1=0.7654、1/R3=1.848、R2=1/R1、R4=1/R3、C1=C2=C3=C4=1 F（归一化）（p.3）。
- 反归一化：C=0.1 µF、fp=2.5 kHz → Z=636.62 Ω；Ra1=820 Ω、Ra2=470 Ω、Ra3=330 Ω、Ra4=1.2 kΩ（p.3）。
- 8 档电阻表（p.4, Table II，标称值）：如 200 Hz 档 Ra1=10 kΩ/Ra2=6.2 kΩ/Ra3=4.3 kΩ/Ra4=15 kΩ；10 kHz 档 220/120/82/300 Ω；15 kHz 档 150/82/51/200 Ω（Z 值列 7957.75/3978.87/2652.58/1273.24/636.62/318.31/159.15/106.1 Ω）。
- 验证例：fp=2.5 kHz、采样率 10000 Hz、30000 点；50 Hz 基波 499.92 V、3 次 164.97 V、5 次 200.20 V（表 III 数值列排版错乱，幅度归属**待核**）、THD 38.44%（p.4）。
- Butterworth 过渡带斜率 6n dB/oct（四阶 24 dB/oct）（p.2）。

## 对 P1/P2/P3 的对照
- **P1（G_DC=H_N−H_P≡0 消去条件）**：相关度 **低（反面样本）**。单端逐通道链路，本文根本不存在"两路匹配"问题意识；6 路通道（三相 V/I）之间的通道间匹配（同步采样、增益/相位一致性）本是该应用的关键，**全文零讨论**——恰证明配方线文献不覆盖失配条件，P1 的空白真实存在。
- **P2（Kelvin 结构地板）**：相关度 **无**。
- **P3（平坦度约束下衰减可达上界）**：相关度 **低（定性起点）**。选型理由"带内平坦 + 尽快下降"就是平坦度—衰减权衡的定性表述，且 6n dB/oct 给了斜率量级；但无任何"给定平坦度求衰减上界"或纹波预算数值（Butterworth 阶数 4 的选择只说 "can meet those requirements"，无指标推导）。
- **方法学（D1–D4/D8）**：无 dB 级混叠抑制要求、无平坦度数值（D4 的 0.5 dB 无对应物）、无共模内容（D8 不适用）；其"抗混叠有效性"验证仅一次谐波谱演示。另注意内部矛盾：八档含 5/10/20 kHz，而演示采样率仅 10 kHz（fs/2=5 kHz）——**若选 >5 kHz 档则直接违反奈奎斯特，文中未置一词**（配方自洽性缺陷的实例）。
- **killRisk**：**无**。纯配方样本，对 P1/P2/P3 无冲击；引用价值在"配方线长什么样"的举证。

## 没读到的
- 元件容差/失配、标称圆整（831.74→820 Ω 等）对 fc 与 Q 的影响分析——完全缺失。
- 混叠抑制的 dB 量化、AAF 后残余混叠噪声预算——完全缺失（只有"effectively filtered"的定性话）。
- 运放型号、供电、噪声、建立时间——未给（图 3/4 中运放无型号）；CD4051 导通电阻（典型 ~125 Ω 量级）串入 RC 网络对截止频率的影响——未讨论。
- 通道间（三相 V/I 六路）增益/相位一致性、同步采样误差——未讨论。
- 实测滤波器幅频/相频曲线——没有（仅系统级谐波谱一张）。
- 摘要称 200 Hz–15 kHz，Table II 实列到 20 kHz——口径不一致（照录，待核）。
