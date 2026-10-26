# 精读笔记 · Microchip AN699《Anti-Aliasing, Analog Filters for Data Acquisition Systems》（Baker，DS00699B，13 页）

> 格式标准（全组沿用）：出处 → 核心命题（原文引用）→ 关键数值（原文）→ 对 P1/P2/P3 的对照 → 没读到的。
> 读法：pdftotext 全文逐节读，引用一律原文加页码；不转述成模糊话。
> 出处：Microchip AN699，Bonnie C. Baker，DS00699B（©1999，印次 2002）；正文 10 页（页脚 "DS00699B-page N" = PDF 页码）+ NOTES/版权/销售页。配套工具 FilterLab。

## 核心命题（原文）

1. 混叠与折返公式（p.4）："If there is a portion of the input signal that resides in the frequency domain above fS/2, that portion will fold back into the bandwidth of interest with the amplitude preserved. The phenomena makes it impossible to discern the difference between a signal from the lower frequencies (below fS/2) and higher frequencies (above fS/2)."；"f ALIASED = f IN – NfS"；例（fS = 100 kHz，p.5）："fOUT(2) = |82kHz - 1 x 100kHz| = 18kHz" 等 5 音折返（41/18/19/6/53 kHz）。
2. ④ **AAF 选型规则原文（"配方类"证据）**（p.5）："The affects of this error can be minimized by moving the corner frequency of the filter lower than fS/2 or increasing the order of the filter. In both cases, **the minimum gain of the filter, ASTOP, at fS/2 should less than the signal-to-noise ratio (SNR) of the sampling system.**"；紧接着的定量化配方（p.5）："For instance, if a 12-bit A/D Converter is used, the ideal SNR is 74dB. The filter should be designed so that its gain at fSTOP is at least 74dB less than the pass band gain. Assuming a 5th order filter is used in this example:
   fCUT-OFF = 0.18fS /2 for a Butterworth Filter
   fCUT-OFF = 0.11fS /2 for a Bessel Filter
   fCUT-OFF = 0.21fS /2 for a Chebyshev Filter with 0.5dB ripple in the pass band
   fCUT-OFF = 0.26fS /2 for a Chebyshev Filter with 1dB ripple in the pass band"
   ——**SNR 判据 + fCUT-OFF/fS 配方比值 + 滤波器类型表**，是典型的"配方类"文档：给比值不给推导。
3. 砖墙不可行（p.2）："Ideally, a low-pass, anti-aliasing filter should perform with a 'brick wall' style of response, where the transition band is designed to be as small as possible. Practically speaking, this may not be the best approach for an anti-aliasing solution. With active filter design, every two poles require an operational amplifier. For instance, if a 32nd order filter is designed, 16 operational amplifiers, 32 capacitors and up to 64 resistors would be required to implement the circuit. Additionally, each amplifier would contribute offset and noise errors into the pass band region of the response."
4. 滤波器类型分工（p.3）："a 5th order Butterworth response is required if it is to meet the transition band width of a 3rd order Chebyshev"；Bessel："produces a constant time delay with respect to frequency"、"best step response … very little overshoot or ringing"（p.3）。
5. 无源滤波器口径（p.5-6）："The output impedance of a passive low pass filter is relatively high … For instance, a 1kHz low pass filter which uses a 0.1µF capacitor in the design would require a 1.59kΩ resistor … This value of resistor could create an undesirable voltage drop or **make impedance matching difficult**. Consequently, passive filters are typically used to implement a single pole."（全文唯一 matching 命中——源负载语境，非差分失配）；"It is very common to use a single pole, low pass, passive filter at the input of a Delta-Sigma A/D Converter. In this case, the high output impedance of the filter does not interfere with the conversion process."（p.6）
6. 设计例三参数（p.7）："1. Cut-off frequency for filter must be 1kHz or higher. 2. Filter attenuates the signal to -74dB at 10kHz. 3. The analog signal will only be filtered and not gained or inverted."；系统设定（p.7）："The low pass filter segment will be followed by a 12-bit SAR A/D Converter. The sampling rate of the A/D Converter will be 20kHz, making 1/2 of Nyquist equal to 10kHz."；三实现："A 5th order filter that has a cut-off frequency of 1kHz … two Sallen-Key filters plus a passive low pass filter … attenuates the analog input signal 79dB from the pass band region to 10kHz"（Bessel，p.7）；"a 3rd order filter is required … attenuated to -70dB at 10kHz … has a 4dB ripple in the pass band"（Chebyshev，p.8）；"a 4th order filter … Two Sallen-Key filters … attenuates the pass band signal 80dB at 10kHz"（Butterworth，p.9）。
7. 4 dB 之差的后果（p.8）："The difference between -70dB and -74dB attenuation in a 12-bit system will introduce little less than 1/2 LSB error. This occurs as a result of aliased signals from 10kHz to 11.8KHz. Additionally, a 4dB gain error will occur in the pass band."

## 关键数值（原文）

- 判据链：A_STOP(fS/2) ≤ 系统 SNR（12 bit → 74 dB）；5 阶时 fCUT-OFF = 0.11–0.26 × fS/2（视类型，p.5）
- Table 4（p.9）："Theoretical frequency response at 10kHz of various filter designs versus filter order. Each filter has a cut-off frequency of 1kHz"（列：Butterworth / Bessel / Chebyshev 1dB / Chebyshev 4dB）：
  M=3：60 / 51 / 65 / 70 dB；M=4：80 / 66 / 90 / 92；M=5：100 / 79 / 117 / 122；M=6：120 / 92 / 142 / 144；M=7：140 / 104 / 169 / 174
- 定义（p.2）："AMAX = APASS − ASTOP"；"The cut-off frequency (fCUT-OFF) of a low pass filter is defined as the -3dB point for a Butterworth and Bessel filter or the frequency at which the filter response leaves the error band for the Chebyshev."
- 例题实测衰减：Bessel 5th 79 dB@10kHz、Chebyshev 3rd −70 dB@10kHz（4dB 纹波）、Butterworth 4th 80 dB@10kHz（p.7-9）

## 对 P1/P2/P3 的对照

- **④ "配方类"证据定位**：AN699 是 AAF 选型配方的教科书式样本——SNR 判据 + fCUT-OFF 比值表 + 阶数-衰减表（Table 4），设计例用 FilterLab 直接出元件值。**全篇无一处从元件容差推衰减恶化/共模转换**；容差维度在本文缺席（对比 SBAA230 p.6 "subject to component tolerances and temperature" 仅一句话）。
- **⑥ P1 反例搜索**：mismatch/CMRR/common-mode/differential **全部零命中**；唯一 "matching"（p.5）是单端源阻抗语境（"make impedance matching difficult"）。电路实例全部单端（MCP601 单端 Sallen-Key/MFB）。→ 无源 RC 差分失配→共模消去条件**完全缺席**，是 P1 的又一负样本。
- **P2（Kelvin 地板）**：无直接内容。
- **P3（AAF 衰减上界）**：p.2 砖墙段（"16 operational amplifiers, 32 capacitors and up to 64 resistors … each amplifier would contribute offset and noise errors"）与 p.8 的 "-70dB vs -74dB → <1/2 LSB" 是 P3"衰减上界有代价、差几分贝有后果"的最好引文；Table 4 给出上界量级表。

## 没读到的

- 元件容差/温度对衰减与共模的影响（全文无）；
- 差分结构（全文单端）；
- FilterLab 算法细节（外部工具）；参考文献 Valkenburg、Huelsman 两书未核。
