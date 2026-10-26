# 精读笔记 · Burdett, R. 2008《Specifying Lock-in Amplifiers》（SIGNAL RECOVERY Technical Note TN 1001, V5.01/08UK © 2008 AMETEK Advanced Measurement Technology）

> 格式标准（全组沿用）：出处 → 核心命题（原文引用）→ 关键数值（原文）→ 对 P1/P2/P3 的对照 → 没读到的。
> 读法：pdftotext 全文逐节读，引用一律原文加页码；不转述成模糊话。
> 注：作者名取自 PDF 元数据（Author: Burdett_Richard）；页码 = TN 印刷页（1–4，p.1 无页码，p.2–4 页脚编号）。

## 核心命题（原文）

**② 锁相差分输入的对称假设 + CMRR 单频规格——原话（p.2）**

1. 对称假设（"两根电缆完全相同→拾噪相等"）："A differential input (figure 2) has two connectors and amplifies the difference in voltage between them. **If the two cables used to connect them to the signal source are identical, then any spurious noise pick-up will affect both cables equally and be rejected by the common mode rejection capability of the differential input amplifier.**"（p.2）
2. CMRR 规格（单频单点）："The quality of this rejection is specified by the Common Mode Rejection Ratio or C.M.R.R.; **a figure of at least 100 dB at 1 kHz should be expected, corresponding to the ability to measure a 10 µV signal in the presence of 1 volt of common mode interference.**"（p.2）——注意规格只给"at 1 kHz"一个频点，无频率降额曲线。
3. 单端输入的地环路对策（与差分并列的另一输入形态）："The single-ended input (figure 1) is the most commonly used configuration, in which the lock-in amplifier amplifies the difference between the signal at the inner and outer conductors of the input connector. The outer connector, or shield, is not forced to ground potential but is instead connected via a resistor of typically 100 to 1000 ohms. This avoids possible "ground loops" between the source and the instrument, due to differing ground potentials, by allowing the shield to "float" so that the lock-in amplifier can sense the signal source ground."（p.2）
4. 输入阻抗前提："Voltage inputs offer the highest possible impedance to the signal to be measured so that they do not affect its level. Good lock-in amplifiers will present an input impedance of at least 10 MΩ."（p.2）
5. 文档定位（是术语科普而非机理论文）："This Technical Note discusses the reasons why users choose lock-in amplifiers for their measurements and defines the terms used to describe the instruments' performance."（p.1）

## 关键数值（原文）

- CMRR：≥100 dB @ 1 kHz（差分输入）；换算口径 = 10 µV 信号 / 1 V 共模干扰（p.2）
- 电压输入阻抗 ≥10 MΩ（p.2）；单端屏蔽经 "resistor of typically 100 to 1000 ohms" 浮地（p.2）
- 电流输入转换增益 "typically of 10^8 or 10^6 V/A"（p.3）
- 动态储备 "Commercially available lock-in amplifiers offer dynamic reserves up to 130 dB"（p.3）；"60 dB of dynamic reserve is not available at a 1 V full-scale sensitivity"（p.3）
- 漂移最差档 "say 500 ppm/ºC, a 10 ºC temperature drift results in an error of less than 0.5 % of full-scale"（p.4）；常规环境按 10 °C 温变评估（p.3）
- 灵敏度示例链（文中假设性算例，非某型号规格）：20 nV @50 kHz、输入噪声 ≤4 nV/√Hz、1 MHz 带宽、增益 1000 → 锁相等效带宽 0.125 Hz（1 s 时间常数、12 dB/oct）→ 噪声 1.4 µV、约 5 s 稳定（p.1）
- 相位噪声算例：10 m° r.m.s. @100 ms 时间常数 → 同相向正交"breakthrough" 174 nV（p.3）
- 输出滤波 "the same response as a resistor-capacitor (RC) filter, which shows a 6 dB/octave roll-off"，可叠 12/18/24 dB/oct（p.3）

## 对 P1/P2/P3 的对照

- **P1（失配消去条件）——P1 反例检索结论：无"无源 RC 差分网络失配→共模消去条件"的推导；但 p.2 那句是该命题所批判的"无条件对称假设"的最干净原始出处**。原文的逻辑链是"identical → pick-up 相等 → 被 CMRR 拒掉"，条件（identical）只作前提一句话，**没有给失配容差、没有给失配→差分转换量、没有给频率相关性**（CMRR 只有 1 kHz 单点）。这正好构成 P1 的靶子引文：业界规格书以"两根电缆完全相同"为前提，而 P1 要给出失配下共模消去失效的定量条件。与 Whitlock 2004 对照：Whitlock 说"balance of common-mode impedances"才决定拒噪（p.2），Burdett 的表述停留在信号对称/拾噪相等层面——两者合引可显出"对称假设 vs 阻抗平衡"的表述分歧。
- **P2（Kelvin 地板）**：无直接内容（锁相放大器输入级规格，不涉两线/四线传感结构）。
- **P3（AAF 衰减上界）**：无（输出低通是锁相解调后的 DC 低通，6 dB/oct RC 型，不是抗混叠滤波器；p.3）。
- **引文价值**：p.2 "If the two cables … are identical, then any spurious noise pick-up will affect both cables equally and be rejected" + "at least 100 dB at 1 kHz" 一对引文，用于 Intro 指出"对称假设无条件、CMRR 单频"的业界口径；"10 µV in 1 V" 的换算可直接复用。

## 没读到的

- **CMRR 随频率的行为**：全文只有 "at 1 kHz" 一点，无降额曲线/公式；被引到的 TN1000/1002/1003（p.4 清单）本地无档。
- 电缆失配（长度/电容/屏蔽转移阻抗）对共模转差分的定量——文中完全不涉。
- 平衡变压器/主动平衡（Whitlock 谱系）内容无；本文是单端 vs 差分的术语概览，不与 AES 文献交叉。
- 各项规格是"好仪器应达到"的行业口径，未绑定具体型号的实测数据（p.2 "should be expected"）。
