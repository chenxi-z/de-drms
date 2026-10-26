# 精读笔记 · ADI《Continuous-Time Sigma-Delta (CTSD) Precision ADC Minitutorial》

> 格式标准（全组沿用）：出处 → 核心命题（原文引用）→ 关键数值（原文）→ 对 P1/P2/P3 的对照 → 没读到的。
> 读法：pdftotext 全文逐节读，引用一律原文加页码；不转述成模糊话。
> 出处：ADI Minitutorial，5 章合订（Kawle/Shaikh/Choudhury/Maurino/Ren/Anvekar），32 页，
> 各章原发表于 analog.com（2021 前后），本地 PDF = `paper/literature/H3_adi_ctsd_tutorial.pdf`。
> 页码 = PDF 页码 = 页脚印刷页码（1:1）。全文逐页读毕。

## 核心命题（原文）

1. **开关电容输入的两重扰动（④ 机理原话，p.5）**："In conventional SAR, DTSD ADCs, the input structure is known as the switched capacitor sample-and-hold circuit… At every sampling clock edge when the sample switch changes its ON/OFF state, finite current demand needs to be supported to charge or discharge the hold capacitor to a new sampled input value. This current demand needs to be supplied by the input source… Additionally, the switch itself has some on-chip parasitic capacitors that inject some charge back onto the source, which is called charge injection kickback."（p.5）
2. **kickback 是输入相关的误差（p.5）**："The charge injection current is a function of input and this current causes an input dependent voltage drop across the sensor impedance. As shown in Figure 4a, the input of the ADC is then in error."（p.5）——即失真通道，不只是噪声通道。
3. **CTSD 的对照答案（p.5）**："CTSD ADCs address this challenge by providing an easy to drive resistive input instead of a switched capacitor input. This shows that there are no hard requirements of high bandwidth, large slew rate amplifiers."（p.5）；"the signal input and reference input purely resistive. This results in an almost nonsampling ADC, making a class of its own."（p.8）；时域证据："With the CTSD ADC, the input current is observed to be continuous, which maintains signal continuity."（p.21，Fig.4 对比 DTSD kickback 波形）
4. **抗混叠的机理表述（p.17–19）**："sampling occurs not directly at the input of the modulator but after the loop filter, H(f)"（p.17）；"The transversal of a signal through a loop filter creates a low-pass filter profile before it is sampled. This profile leads to the inherent alias rejection of a CTSD modulator."（p.19）；"Alias from around fs is attenuated by the inherent alias rejection property of a CTSD while intermediate interferers are attenuated by a digital filter."（p.19）
5. **CTSD 的代价（时钟，p.13）**："a CTSD modulator is tuned for a fixed MCLK clock frequency and cannot support varying MCLK."＋"any error in the sampling clock time period in the form of jitter would affect the performance of the modulator loop."（p.13）

## 关键数值（原文）

- **输入阻抗（①）**："in the AD4134… the input impedance is 6 kΩ differential. This indicates that when a full-scale 8 V p-p differential input signal is applied to the ADC, the peak current requirement is 1.3 mA p-p. If the sensor can support the input current VIN/RIN, then it can be directly interfaced to the ADC."（p.21）
- **AAREJ 实测口径（②）**："Figure 11 shows the alias rejection of AD4134 for out-of-band frequencies in the performance bandwidth of 160 kHz with a sampling frequency of 24 MHz. For a frequency of 23.84 MHz (fs – 160 kHz), alias rejection is –85 dB, which is the alias rejection specification of the ADC. It can also be observed that the rejection is better than –100 dB for other intermediate frequencies."（p.19）
- **相位匹配（③）**："the phases between channels need to be accurately matched with a requirement of 0.05° at 20 kHz."（p.19）；RC AAF 的失配代价："A second-order Butterworth filter designed for –80 dB rejection at 16 MHz (sampling frequency) and f3dB of 160 kHz (input bandwidth) could have phase mismatch of ±0.15° at 20 kHz with error tolerance of as low as 1% on the absolute values of RC. The availability of lesser error tolerance RC passives is limited and increases the bill of material (BOM)."（p.19）；CTSD 的失配下限："The phase mismatch is limited by on-chip mismatches of analog modulator loop design, which could be as low as ±0.02° at 20 kHz."（p.19）
- **时钟要求**：SNRj 公式 "SNRj = –20 × log10(2πσj fsin)"（p.27，σj = rms jitter）；CTSD MCLK 需求量级："the order of requirements would be like ±100 ppm accuracy in frequency and rms jitter of 10 ps."（p.31）
- **参考端简化**：片内 20 Ω + REFCAP 电容成一阶 RC；"this extended range limits the resistor value to a maximum of 25 Ω"（p.24）；VREF=4.096 V、IADC=6 mA、R=20 Ω 时 VREFADC=3.967 V（p.24）。

## 对 P1/P2/P3 的对照

- **P1（失配消去条件 + "CTSD 门后残余网络"）**：本文给了残余网络存在的**直接书面证据**——外部串联电阻 Rs 与片内 RIN 构成分压："In scenario 4 and 5, there would be a voltage drop across the extra external resistor Rs, which indicates a signal loss at the ADC input. This leads to gain errors for the signal chain and drift of errors with temperature… The temperature gain drift is caused by the different temperature coefficients of the external resistance and internal resistance."（p.22）。
  这正是 P1 反例的形态：CTSD 门（纯阻输入）之后**唯一允许的残余网络是分压器**，且增益误差无法用匹配消掉、只能靠"isolate the extra external resistance"（加放大器，p.22）或数字增益校正。本文**没有**任何"无源差分网络失配→共模→差模"的消去条件公式（⑤：负结果，见下）。
- **P2（Kelvin 地板）**：p.22 的 Rs 分压与"sensor has a large output impedance"（p.21 列为必须加放大器的场景 4/5）与 P2 的"源阻抗吃掉分辨率"同构；CTSD 把输入做成 6 kΩ 固定电阻，等于把 P2 的不确定源阻抗换成**已知分压比**（可校正，但需温度跟踪）。
- **P3（AAF 衰减上界）**：p.19 的 AAF 阶数对比图（Fig.4："for –80 dB rejection at the sampling frequency vs. the input signal bandwidth… CTSD ADCs don't require an external AAF"）+ Fig.11 是"内在抗混叠也有边界"的最好引文：**guarantee 只到 fs±160 kHz 窗口 −85 dB**，窗口外靠数字滤波器与"better than –100 dB"的典型值，不是无限衰减。
- **引文价值**：p.5 的 charge injection 双机理段（充电电流 + 开关寄生电容回注）是 P1 论文里"开关电容输入 vs 连续时间输入"对比的最佳权威引文；p.19 的 ±0.15°(1% RC) vs ±0.02°(片内) 是"无源 RC 失配→相位失配"的唯一定量件（注意：它给的是**通道间相位**失配，不是共模消去条件）。

## 没读到的

- **⑤ 无源差分网络失配→共模消去条件：全文没有。** 检索 mismatch/matched/common-mode/balance 全命中已列：p.19 只涉相位；p.20 的 common-mode 讲的是 in-amp 隔离高压共模（"the common-mode (CM) signal of the sensor can be very high, up to 10s of volts"），p.22 的匹配要求仅 "the impedance of the sensor should be matched with the amplifier input impedance"（源阻抗匹配，非桥平衡）。Whitlock 式 Zcm/桥平衡条件在本文不存在。
- 参考文献 [5] "Newest Sigma-Delta ADC Architecture Averts Disrupted Data Flow When Synchronizing Critical Distributed Systems"（Analog Dialogue 53(3), 2019，PLL 同步方案）本地无；[6] AN-1388（AD7779 SRC）本地无。
- ASRC 细节本文只到概念级（"keep a lookout for the follow-up article"，p.31），无 ASRC 噪声底/失真数据。
