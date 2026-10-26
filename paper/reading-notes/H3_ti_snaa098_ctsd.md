# 精读笔记 · National/TI SNAA098《Continuous-Time Sigma-Delta ADCs》（Kulchycki 2008，10 页）

> 格式标准（全组沿用）：出处 → 核心命题（原文引用）→ 关键数值（原文）→ 对 P1/P2/P3 的对照 → 没读到的。
> 读法：pdftotext 全文逐节读，引用一律原文加页码；不转述成模糊话。
> 出处：Literature Number SNAA098，"Continuous-Time Sigma-Delta ADCs"，Scott D. Kulchycki, National Semiconductor，January 2008（TI 收购后重发，尾页 © 2011）；正文 8 页（页脚页码 = PDF 页码）+ 免责声明。器件对象：ADC12EU050（12-bit CT-ΣΔ）。

## 核心命题（原文）

### ⑤ CT-ΣΔ 内在抗混叠的原文主张

1. 首页特性总纲（p.1）："**An essentially alias-free Nyquist band** that is made available by exploiting inherent over-sampling, an internal lowpass CT loop filter, and on-chip digital filtering."；"A purely resistive input with no switching, which is easier to drive and couples less noise to the overall system than the switching input capacitors of a sampled-input ADC"；收益清单："**Eliminating the need (or reducing the requirements) for an external anti-aliasing filter.**"
2. 对 DT-ΣΔ 的比较主张（p.5）："although a DT∑Δ would allow signals around its loop sampling rate, MfS, to fold down inband, **the inherent anti-aliasing filtering in a CT∑Δ ADC precludes this from happening.**"；"interest in CT∑Δ modulators has been renewed because of some of the benefits, such as employing lower-power integrator amplifiers and including inherent anti-aliasing filtering versus sampled-input ADCs [7]"
3. **机制双效应（p.6，全文最核心主张）**："The anti-aliasing performance of the CT∑Δ is a result of its implementation as both a ∑Δ modulator and a CT circuit. … **Because the CT∑Δ ADC samples at the output of the forward loop filter, the signal is first lowpass filtered by the loop before sampling, which attenuates signals around the modulator loop sampling rate (MfS) that can alias down in-band. Furthermore, because these aliased signals are then injected at the input of the internal quantizer, they are noise-shaped by the loop in the same manner quantization noise is shaped. These two effects enable the CT∑Δ to offer significant anti-aliasing filtering versus the DT∑Δ** in addition to the benefits of over-sampling and digital filtering versus a pipeline design."（Fig.4 标注：pipeline "Requires External Anti-Aliasing Filter" vs CT∑Δ "Includes Anti-Aliasing Filter"）
4. 强度与诚实口径（p.6）："The CT∑Δ ADC architecture **eliminates the need for stringent input filtering** because of its inherent anti-aliasing filtering. In the ADC12EU050, many of the performance characteristics of the anti-aliasing filter are set in the digital domain, allowing for a very high level of passband flatness and steep roll-off (high effective order)."；"This significant inherent anti-aliasing filtering **greatly reduces the requirements on or may reduce the need for** an external AAF."；随即限定："the anti-aliasing requirements are dependent upon the application and can be a significant system challenge both in terms of design complexity and overall system form factor and cost."
5. 采样点位差异的总括（p.5）："CT∑Δ ADCs differ from sampled-input ADCs … in two important ways: • A CT∑Δ modulator uses CT integrators rather than DT integrators or circuits. … • **The sampling operation in a CT∑Δ modulator occurs at the output of the forward loop filter, before the quantizer. In contrast, for a sampled-input ADC, the sampling occurs at the input of the ADC.**"
6. 代价/限制（p.5）："The input bandwidth of a ∑Δ is also limited to the ADC's first Nyquist band. … in a ∑Δ ADC, because of the lowpass decimation filtering, signals outside the first Nyquist zone will be removed from the output spectrum. Therefore, input signals must be mixed down into the first Nyquist zone to be digitized by a CT∑Δ ADC."；"the dynamics of the CT∑Δ are set by the RC or C/gm product of its component integrators; therefore, **the integrator time constants must be tunable to allow for process variation** [2]"（全文唯一"元件变化"句——工艺偏差调谐，非差分失配）。
7. 输入静谧性（p.6-7）："CT∑Δ technology instead presents a constant, resistive input … Because the input of a CT∑Δ is not sampled, there are no switching capacitors and it is easier to drive the input … without any switches at the input to restrict the input voltage swing, the allowable input voltage range can be higher … indeed, the input voltage can even exceed the supply rails."

## 关键数值（原文）

- ADC12EU050（p.7）："an alias-free sample bandwidth of 20 to 25 MHz and a conversion rate of 40 MSPS to 50 MSPS. The device features 68 dB of signal-to-noise and distortion (SINAD) and a signal-to-noise ratio (SNR) of 70 dB full scale (dBFS). Operating from a 1.2V supply, it consumes 44 mW per channel at 50 MSPS for a total power consumption of only 350 mW, 30% lower than currently available competitive pipeline products"
- SNR 公式（p.4）：flash "SNR = 1.76 + 6N"；过采样 "SNR = 1.76 + 6N + 10log10 (M)"；ΣΔ "SNR = 1.76 + 6N + (2L + 1) 10 log10 (M) + 10 log10 (2L + 1) - (2L)10 log10 (π)"；"the SNR increase due to the over-sampling ratio is multiplied by (2L+1)"
- 过载恢复（p.7）："When this instant overload recovery (IOR) circuitry is enabled, the ADC maintains signal integrity in the event of an input overload condition"（一般 ΣΔ 过载 "may require the loop to be reset, losing data previously stored in the loop"）
- 时钟（p.7）："an on-chip clock conditioner, comprising a PLL and VCO … The system designer needs simply to provide a moderate-quality, low-cost crystal at the desired output sampling rate (40-50 MSPS)"

## 对 P1/P2/P3 的对照

- **⑤ 用途**：CT-ΣΔ"内在抗混叠"三段式主张的权威原文库——(a) 采样在环路滤波器之后（先 LP 再采样）；(b) 残余混叠分量进量化器再被噪声整形；(c) 结论强度是"greatly reduces the requirements on or **may** reduce the need for an external AAF"（不是"无需 AAF"）。凡写 CT-ΣΔ 免 AAF 论述，引 p.6 双效应句 + 其限定句，勿引成绝对免滤。
- **P3（AAF 衰减上界）**：p.3 "Steep filter attenuation characteristics are hard to achieve"（"Input Filtering and Sampling Clock Requirements"节，pipeline 难题处）与 p.6 "The design of an analog anti-aliasing filter possessing a steep cut-off characteristic and a very flat passband is a challenging task demanding high-order, potentially high insertion-loss filter networks, which may necessitate additional gain in the signal path to compensate for that loss."——与 AN699 p.2 砖墙段同谱系，可作 P3 双引文。
- **⑥ P1 反例搜索**：mismatch/CMRR/common-mode **零命中**（关键词检索）；"differential" 仅出现在数字接口（p.8 "industry-standard low-voltage differential signaling (LVDS)"），与模拟失配无关。无源 RC 差分失配→共模消去条件**缺席**（负样本）。
- **P2（Kelvin 地板）**：无直接内容。

## 没读到的

- NTF/抗混叠抑制的定量曲线数值（Fig.3/4 只有示意）；
- 失配/容差/CMRR 内容（全文无）；
- [2] Mitteregger JSSC 2006、[7] van der Zwan ESSCIRC 1996 等 8 篇引文原件未核；作者博士论文 [3]（Stanford 2007）未附。
