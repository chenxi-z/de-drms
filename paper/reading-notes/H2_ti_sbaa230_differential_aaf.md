# 精读笔记 · TI SBAA230《Digital Filter Types in Delta-Sigma ADCs》（Pisani，SBAA230A 2017/2023，9 页）

> 格式标准（全组沿用）：出处 → 核心命题（原文引用）→ 关键数值（原文）→ 对 P1/P2/P3 的对照 → 没读到的。
> 读法：pdftotext 全文逐节读，引用一律原文加页码；不转述成模糊话。
> 出处：TI Application Report SBAA230A – MAY 2017 – REVISED MARCH 2023，Brian Pisani，"Digital Filter Types in Delta-Sigma ADCs"，正文 8 页 + 免责声明。
> **文件名勘误提示**：本地文件名 `H2_ti_sbaa230_differential_aaf.pdf` 名不副实——文档实际标题是"ΔΣ ADC 中的数字滤波器类型"，**通篇是数字滤波器口径，与差分（differential）无关**（对照 AGENTS.md "ad779x.pdf 名不副实"先例）。归档/引用时以标题为准。

## 核心命题（原文）

1. 摘要定对象（p.1）："This application report discusses digital filters which are a ubiquitous feature in delta-sigma analog to digital converters (ADCs). Digital low-pass filters are essential to the functionality of a delta-sigma ADC, which relies on oversampling and noise shaping to push quantization noise out of band."
2. ③ **数字滤波器口径的原文证据**——目录即证据：全文仅 4 个技术节 "1 Introduction / 2 Digital Filters in Delta-Sigma ADCs / 3 Sinc Filter / 4 Wideband Filters"，参考文献仅两本 ADC 数据手册（"ADS124S08 data sheet (SBAS660)"、"ADS127L01 data sheet (SBAS607)"，p.8）。对象全部是片内 sinc/wideband FIR 数字滤波器；模拟滤波器仅在"为何数字滤波器更好"处顺带出现。
3. OSR 与 AAF 简化的口径（p.2）："The digital filters in delta-sigma ADCs serve another function – decimation. … fDR = fMOD / OSR. The OSR and filter type combined determine the output bandwidth of the digital filter and overall frequency response of the ADC. Large OSRs produce small filter bandwidths, which translates to very good noise performance, **simplified anti-aliasing circuitry**, and reduced digital interface speeds for the host controllers."
4. sinc3 会放进更多带外噪声（p.3）："The sinc3 filter, on the other hand, attenuates signals to –3 dB at 0.262 x fDR and transitions slowly even after fDR / 2, **which would enable more out-of-band noise to fold into the bandwidth of interest**."
5. 频域/时域权衡（p.3）："The wideband filter is a very high-order filter, meaning it takes a long time to settle to a final value upon receiving a step input. In the wideband filter of the ADS127L01, it will take 84 conversions to receive a settled output. A sinc3 filter settles in three conversions after a step at the input, enabling quick cycling through multiple input channels."
6. **全文唯一涉模拟 AAF 的句子（p.6）**："For ADCs without integrated digital filters, options are limited for achieving such a steep anti-aliasing response. **High-order analog anti-aliasing filters with steep roll-offs are notoriously difficult to design and are subject to component tolerances and temperature.** Alternatively, it is possible to oversample the converter and digitally filter in the processor, but this comes at the cost of instruction cycles … A wideband filter in a delta-sigma ADC truly solves this problem with its built-in 'oversample, low-pass filter, then decimate' topology."
7. wideband 滤波器指标（p.6-7）："Note how steep the transition band of the filter is around fDR / 2 – the frequency where signals begin to alias into the passband. This serves to drastically limit unwanted signals or noise from folding over. The stopband magnitude never exceeds –116 dB until the response of the filter repeats around the modulator frequency, fMOD, of the ADC."；"For this filter, the group delay is 42 output data samples."（p.7）

## 关键数值（原文）

- sinc3：−3 dB @ 0.262·fDR；sincN 阶数 = 建立所需样本次数（"the order of the sinc filter matches the number of samples it takes to settle"，p.4-5）
- ADS127L01 wideband：fDR = 512 kHz，阻带 "never exceeds –116 dB" 直到 fMOD 重复镜像，建立 84 转换、群延迟 42 样本（p.3, 6-7）
- ADS124S08 low-latency 滤波器（fDR = 20 SPS）："this filter simultaneously rejects both 50 Hz and 60 Hz. A normal sinc filter would require a data rate at some integer divisor of 10 SPS to achieve this, since filter notches would occur at multiples of 10 Hz."（p.5）

## 对 P1/P2/P3 的对照

- **③ 确认"数字滤波器口径、无失配内容"的证据链**：(a) 摘要/目录/参考文献（上引 p.1、p.8）；(b) 关键词检索全文 mismatch/CMRR/common-mode **零命中**——仅有的两个近似命中是 p.5 "the order of the sinc filter matches the number of samples it takes to settle"（无关）和 p.6 "subject to component tolerances and temperature"（唯一容差句，且只说模拟 AAF 难做，无任何失配→转换机理）；(c) 全文无差分电路、无 RC 匹配讨论。可作为"TI 数字滤波器类应用笔记不含 P1 内容"的硬证据。
- **P1（失配消去条件）**：无（见上）。P1 反例搜索的负样本。
- **P2（Kelvin 地板）**：无直接内容。
- **P3（AAF 衰减上界）**：p.6 "notoriously difficult to design and are subject to component tolerances and temperature" 是 P3 立论（模拟 AAF 有衰减上界/容差墙）的最好应用笔记引文之一；p.3 "–3 dB at 0.262 x fDR … enable more out-of-band noise to fold into the bandwidth of interest" 给出数字侧放宽 AAF 的条件。注意层次：本文 −116 dB/0.262 fDR 都是**数字**滤波器口径，与 P3 的模拟 AAF 上界分属两层，引用勿混。

## 没读到的

- 任何模拟 RC/差分/匹配内容（预期中"differential aaf"内容并不存在于本文）；
- ADS124S08/ADS127L01 手册原件（SBAS660/SBAS607）未附。
