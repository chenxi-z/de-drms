# 精读笔记 · TI Precision Labs《Driving SAR and Delta-Sigma ADC Inputs》（SPRPEO2，Seminar 幻灯，54 页）

> 格式标准（全组沿用）：出处 → 核心命题（原文引用）→ 关键数值（原文）→ 对 P1/P2/P3 的对照 → 没读到的。
> 读法：pdftotext 全文逐节读，引用一律原文加页码；不转述成模糊话。
> 出处：TI Precision Labs Seminar "Driving SAR and Delta-Sigma ADC Inputs"，无文档编号（文件名 SPRPEO2）；
> 封底 "Last updated 10/2025"、© 2026。**幻灯页码 = PDF 页码**（下引 p.N 均为幻灯页脚数字）。
> 技术注记：pdftotext 丢 4 处数学字形（p.42 分子、p.43 除数、p.29 表格数字、p.40 公式），已逐处页面渲染目视核回，下文括注"渲染核回"。

## 核心命题（原文）

### ① RC 电荷桶 / 驱动 / kickback 定量口径（对 T08）

**SAR 侧——kickback 与电荷桶：**

1. 建立判据总纲（p.7）："The ADC's sample-hold capacitor (CSH) needs to be settled to ½ LSB within the ADC's acquisition time (tacq). where tacq = 1/fsmpl − tconv_max"
2. kickback 的成因与对策（p.23）："SAR capacitor array switching during conversion ➢ Creates transient input currents (kickback) ➢ Driver must quickly settle these transients"；"Input impedance varies with conversion phase"；缓冲型则 "Buffer isolates capacitor array from input pins ➢ Eliminates kickback to driver circuit ➢ Simplifies anti-aliasing filter design"。
3. 缓冲/无缓冲对照表（p.22）：kickback 一栏 "Minimal (isolated by buffer)" vs "Significant charge injection"；输入阻抗 "High, constant impedance" vs "Time-varying (switching)"。
4. **双滤波器分工定义（p.26）**："Anti-Aliasing Filter • Main purpose: Low-pass filter to block frequencies above Nyquist frequency Nyquist = fs/2"；"Charge-Bucket Filter • Main purpose: handle the 'kickback' current when a SAR ADC sampling switch closes, quickly charge, and must be optimized for settling time."；"Ideal goal (Traditional SAR): Find a balance between both"；"Charge bucket filter might not effectively stop aliasing • Pure anti-aliasing filter might not be fast enough to settle the input. → For buffered ADCs charge bucket not needed."
5. RC 免驱动判据（p.13）："CEXT = 20 x CSH"；"Calculate the max Rsource that may be interfaced with a given n-bit ADC: 1. l = ln 2^n 2. τ = tacq/l 3. Rsource ≤ τ/CEXT"（原式为分数 τ/CEXT）。
   ⚠ **印刷口径分歧（精读发现）**：p.14 例题把分母代成 CSH："Calculate max Rsource using Rsource ≤ 2.61∗10−8 / 55∗10−12 ≤ 475.4 Ω"（CSH = 55 pF，tacq = 290 ns，n = 16，"l = ln 2^16 = 11.09"，"τ = 290∗10−9/11.09 = 2.61 ∗ 10−8"）。按 p.13 公式分母 CEXT=1.1 nF 应得 23.7 Ω，例题按 CSH 得 475.4 Ω；p.15 结论沿用例题（"Rsource ≤ 475.4 Ω"）。引用时须注明哪一口径。
6. 驱动器选型（p.17）："CEXT = 20 × 𝐶𝑆𝐻"；"𝐾 = 𝑙𝑛 2𝑁+1 / (𝐶𝐸𝑋𝑇/𝐶𝑆𝐻 + 1)"（排版分数：分子 2^(N+1)、分母 CEXT/CSH+1；p.18 例 "= ln 2^16+1 / (1.1𝑛𝐹/55𝑝𝐹 + 1) = 8.74" 与 ln(131072/21)=8.739 吻合，分数结构由此确认）；"𝑓𝑍 = 𝐾/(2𝜋×𝑡𝐴𝐶𝑄)"；"𝑓𝑈 ≥ 4 ∗ 𝑓𝑍"；"𝑅𝐸𝑋𝑇 = 1/(2𝜋×𝐶𝐸𝑋𝑇×𝑓𝑍)"；"𝑅𝑂 ≤ 9 × 𝑅𝐸𝑋𝑇"。p.18 例：fZ = 4.8 MHz，fU ≥ 19.2 MHz，REXT = 30.1 Ω，RO ≤ 270.9 Ω；p.19 选 OPA836："𝑓𝑈 = 10 × 19.2 𝑀𝐻𝑧 = 192 𝑀𝐻𝑧"。
7. 带宽经验式（p.25）："Rule of Thumb: For N-bit accuracy: 𝐵𝑊 ≈ ln 2𝑁/(2𝜋∗𝑡𝑠𝑒𝑡𝑡𝑙𝑒)"；"For 16-bit: 𝐵𝑊 ≈ 11/(2𝜋∗𝑡𝑠𝑒𝑡𝑡𝑙𝑒)"；"For 5 MSPS with 70ns acquisition: Required closed-loop B ≈ 25 MHz min"；"*simulating RC combo still recommended"。
8. **电荷桶配方（p.27，ADS9327 无缓冲）**："Priority: charge reservoir + anti-kickback"；"Pick 𝐶𝐹𝐿𝑇 ≥ 20 ∗ 𝐶𝑆𝐻 ≥ 20 ∗ 18𝑝𝐹 ≥ 360𝑝𝐹 – 470pF standard value"；"Practical 𝑡𝐹𝐿𝑇𝑠𝑒𝑡𝑡𝑙𝑒 = 𝑡𝐴𝐶𝑄 = 12 ∗ 𝜏𝐹𝐿𝑇"；"𝑅𝐹𝐿𝑇 = 𝑡𝐴𝐶𝑄/(12∗𝐶𝐹𝐿𝑇) ≅ 12Ω*"；脚注 "*confirming RC combination + driver in simulation recommended … *After simulation 10Ω & 1nF were found as best combination for driving and anti-aliasing"；"Output filter 𝑓−3𝑑𝐵 = 1/(2𝜋𝑅𝐹𝐿𝑇𝐶𝐹𝐿𝑇) ≅ 16𝑀𝐻𝑧"；"Minimum driver 𝐺𝐵𝑊 > 4 ∗ 1/(2𝜋𝑅𝐹𝐿𝑇𝐶𝐹𝐿𝑇) → ≈ 60𝑀𝐻𝑧"。
   同页缓冲型（ADS9227）："Priority: Anti-Aliasing"；"𝑁𝑦𝑞𝑢𝑖𝑠𝑡 𝑓𝑟𝑒𝑞𝑢𝑒𝑛𝑐𝑦 𝑓𝑠/2 = 2.5𝑀𝐻𝑧"；"𝐶𝑑𝑖𝑓𝑓 = 1/(2𝜋𝑓𝑁𝑦𝑞∗2𝑅𝐹𝐿𝑇) = 1/(2𝜋∗2.5𝑀𝐻𝑧∗2∗50) ≈ 646𝑝𝐹 – 470pF standard value"；"𝐶𝑐𝑚 = 𝐶𝑑𝑖𝑓𝑓/10 = 470𝑝𝐹/10 = 47𝑝𝐹"。
9. 全参数对照表（p.29，数字经渲染核回）：Series R "10-22 Ω (limits kickback)" vs "22-50 Ω (flexible)"；Source Z "<10 Ω (critical)" vs "<50 Ω (relaxed)"；Filter Cutoff "15 - 33 MHz (compromise)" vs "5-10 MHz (better AA)"；Min Driver BW "25-30 MHz (critical)" vs "20-25 MHz (relaxed)"；Shunt C "470 pF - 1 nF (limited)" vs "470 pF - 2.2 nF (flexible)"；SNR "~91 dB" vs "~90 dB"。

**ΔΣ 侧——RC 平均电流→电阻负载：**

10. AAF 需求口径（p.36）："Input signal aliasing occurs for any input frequency greater than fDATA/2 (Nyquist frequency)"；"The digital filter in a Delta-sigma ADC will attenuate the aliased signal frequency up to fmod-fDATA/2."；"Any signal in the range of fmod±fDATA/2 will have little or no attenuation by the digital filter."；"An external anti-alias filter is required to attenuate signals greater than fmod-fDATA/2"（图注："Digital filter attenuates signal by 100dB"、"Analog Anti-Alias filter attenuates signal by 100dB at fmod-fDATA/2"）。
11. 等效输入模型（p.37）："CIN, ADC sampling capacitor ✓ S1 closed during the acquisition period Tacq, CIN = VDIFF ✓ S2 closed during the conversion period Tconv, CIN = 0V"；"Average Input Circuit Model (CDIFF ≥ 100 x CIN)"；"Delta Sigma ADC input can be modeled as an input resistance Req = 1/(CIN·fmod)"。
12. 驱动口径（p.38）："Using recommended values for the external RC input filter averages current transients required to charge the input sampling capacitor, resulting in a resistive amplifier load. The amplifier only needs to drive the input filter and the ADC resistive load, allowing use of lower bandwidth amplifiers. Many amplifiers in the 5MHz to 40MHz range can be used."；"A fully settled input driver design can be used but requires an input amplifier bandwidth approximately 20 times greater than the input sample rate. Typical wideband delta-sigma ADC input sample rate is 10MHz, requiring an input amplifier bandwidth of 200MHz or higher to fully settle."
13. 大 RC 的代价——增益误差（p.39）："The disadvantage of using a large RC value to average the input current is a steady state gain error. This error results from the average current flow through RFLT."；"The input filter resistors, RFLT create a voltage divider with Req"；"Gain Error = [1 - Req/(Req + 2∗RFLT)] * 100%"。
14. 预充电缓冲（p.40）："These buffers quickly charge the input capacitor CIN to approximately 0.999 of the input value (coarse switch closed)"；"After this pre-charge phase, the buffers are switched off, and the inputs are directly connected to the input capacitor (fine switch closed)"；"This reduces the amount of average input current needed to charge the input capacitor CIN by approximately 1000x"；"Precharge Buffers Enabled" 框内 "Req = 1000/(CIN·fmod)"（公式经渲染核回）。
15. C 选型（p.41）："CDIFF should be in the range of 100·Cin up to 22nF"；"22nF is a maximum practical limit to ensure amplifier stability"；"High value capacitors result in better low frequency performance (<10kHz) but cause amplifier distortion at high frequencies due to low impedance loading on amplifier outputs"；"Higher amplifier load current also results in higher power consumption"。
16. R 选型（p.42）："RFLT should be in the range of 1/(π·fMOD·CDIFF) up to 100Ω maximum"（分子 1 经渲染核回）；"Maximum 100Ω RFLT ✓ Minimizes offset voltage due to ADC input leakage current ✓ Minimizes linearity errors due to nonlinear ADC input current flowing through RFLT"；"Minimum RFLT value sets the input RC filter corner frequency at a maximum of ¼· fMOD frequency"。
   ⚠ 精读发现：R=1/(π·fMOD·CDIFF) 代入 fc=1/(2πRC) 得 fc=fMOD/2，与该行"¼·fMOD"有 2 倍张力（若按 ¼ fMOD 应 R≥2/(π fMOD C)）。两处均照录，以原文为准。
17. 运放带宽（p.43）："The minimum bandwidth of the input amplifier should be GBW ≥ fmod/2"（除数 2 经渲染核回）；"Higher amplifier bandwidth will support better THD performance"；"Higher bandwidth amplifiers will typically require lower RFLT values to maintain stability, resulting in improved linearity and THD"；"Simulate input amplifier, RC filter, and simplified ADC input impedance using SPICE to verify stability and proper settling"（"Most amplifiers have a complex, multi-order open loop output impedance making simple calculations for stability inaccurate"）。

### ⑥ 失配/共模相关（P1 反例搜索）——全部命中如下

18. 电阻建议（p.44）："Resistor Recommendations • Rg, Rf, Riso and Rflt metal film • 0.1% or better tolerance for good matching • Rf and Rg set gain of input stage • Riso used to improve amplifier stability"；电容建议："Low tc C0G/NP0 ceramic capacitors • High-quality film capacitors • 1% or better tolerance • Optional common mode CCM capacitors ✓ CCM = 1/10 × CDIFF"。
19. 共模噪声抑制配方（p.46）："Ccm: ✓ CCM scale to 1/10 of Cdiff for best common-mode noise rejection"。**这是全文唯一涉及 CM 抑制机理的句子——只给比例配方，无失配→共模-差模转换条件、无 CMRR 数值。**
20. THP210 + ADS127L11 例（p.45-46，与 H4 互引）：MFB 部分 "Use MFB filter Equations — Design Methodology for MFB Filters in ADC Interface Applications"（即 SBOA114，H4）；关键指标 "BW: f(-3dB) = 150kHz, f(-0.2dB) = >20kHz • Attenuation: -90dB at fMOD= 12.8MHz • Noise/SNR: 106-dB"；"ADC RC filter at the ADC inputs serves two purposes: • Provides a third pole, increases filter roll-off. • Charge reservoir to filter the sampled input of the ADC"；"ADS1x7Lxx CIN = 7.4pF ✓ Minimum Cdiff 740pF up to 22nF ✓ This example, Cdiff = 2.2nF"；"Rflt are outside the feedback loop, and works as an isolation resistor for amplifier to remain stable"；"Rflt <100Ω to avoid non-linearities and settling errors."；"Riso: Inside the loop improves stability: Typical range of 20Ω to 100Ω"（渲染核回）；"Riso resistors inside FB loop help further isolate the amplifier outputs, to improve filter phase margin"。
21. 稳定性/噪声/建立（p.48-51）："Allow a conservative >55° of phase Margin for MFB filters • In this Example: Phase Margin = 67°"（p.48）；"ADC noise only (Wideband Filter, 400ksps) ✓ 10.6uVrms, Effective Resolution 19.5b"、"Total system noise (including THP210) ✓ 14.3uVrms, Dynamic Range 106.1dB ✓ Noise limited by wideband filter at 175kHz"、SINC4 "9.3uVrms, Effective Resolution 19.7b"（p.49）；"f-3dB = 157.9kHz"、"-89.7dB at 12.8MHz"（p.50）；"SINC4 filter settles in about 4 data cycles"、"400ksps SINC4 latency (settling) time of 10.63µs"、"Tsettling(1/2LSB) = 51 microseconds"、"Total settling time ✓ THP210 AAF + ADS1x7Lxx SINC4 ✓ 51µs + 10.63µs = 61.63µs"（p.51）。

## 关键数值（原文）

- CEXT = 20×CSH；Rsource 判据 475.4 Ω（ADS8860 例，p.13-15）；fZ = 4.8 MHz、fU ≥ 19.2 MHz、REXT = 30.1 Ω、RO ≤ 270.9 Ω（p.18）
- 电荷桶：CFLT ≥ 20·CSH（≥360 pF→470 pF）、tACQ = 12·τFLT、RFLT ≈ 12 Ω（仿真实选 10 Ω & 1 nF）、fc ≈ 16 MHz、GBW > 4·fc ≈ 60 MHz（p.27）
- ΔΣ：Req = 1/(CIN·fmod)（预充电缓冲后 = 1000/(CIN·fmod)，p.37/40）；CDIFF 100·CIN…22 nF；RFLT 1/(π·fMOD·CDIFF)…100 Ω；GBW ≥ fmod/2；CCM = CDIFF/10（p.41-44）
- 增益误差 = [1 − Req/(Req+2RFLT)]·100%（p.39）；THP210 例：PM 67°、14.3 µVrms/106.1 dB、f−3dB 157.9 kHz、−89.7 dB @12.8 MHz、建立 61.63 µs（p.48-51）

## 对 P1/P2/P3 的对照

- **T08（RC 电荷桶/驱动/kickback 定量口径）**：本文是该口径最完整的"配方型"出处——电荷桶容量（CFLT≥20·CSH）、限流建立（RFLT=tACQ/(12·CFLT)）、驱动带宽（fU≥4·fZ、GBW≥fmod/2、"20 times greater than the input sample rate"）、Ro≤9·REXT 全部成体系。但注意其性质：**经验系数配方（20×、12τ、4×、9×、1/10）+ 仿真确认**，无解析误差预算；kickback 只有定性描述（"transient input currents"、"Significant charge injection"），**未给 kickback 电流/电荷注入绝对值**。引用作 T08 对照时应如实标注"配方口径"而非"机理推导"。
- **P1（失配消去条件）**：差分 RC 网络（2×RFLT + CDIFF + 2×CCM）贯穿 ΔΣ 全节，但失配仅 p.44 一句 "0.1% or better tolerance for good matching"，共模仅 p.46 一句 "CCM scale to 1/10 of Cdiff for best common-mode noise rejection"——**给比例、不给失配→共模-差模转换条件**，是 P1"配方掩盖机理"的直接反例证据。p.39 增益误差式只含对称平均量（Req、RFLT），不含失配项；共模抑制与失配的耦合完全缺席。
- **P2（Kelvin 地板）**：无直接内容。
- **P3（AAF 衰减上界）**：p.36 的分工口径可引——数字滤波器在 fmod−fDATA/2 内给 100 dB，模拟 AAF 只需在 fmod−fDATA/2 处再给 100 dB；p.45 例题给实物锚点（−90 dB @12.8 MHz、f−3dB 150 kHz）。

## 没读到的

- kickback 电流/电荷注入的绝对数值（全文只有定性词）；
- p.13/p.14 的 Rsource 分母 CEXT vs CSH 分歧原文未自洽（见上，引用需双口径并存）；
- p.42 "¼·fMOD" 与 RFLT 下限公式的 2 倍张力原文未解释；
- 参考资料 [e2e 论坛 SAR_OPA.pdf] 未核对；ADS9227/ADS9327（2025-2026 新器件）手册未附。
