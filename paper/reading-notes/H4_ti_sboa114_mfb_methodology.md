# 精读笔记 · TI SBOA114《Design Methodology for MFB Filters in ADC Interface Applications》（Steffes 2006，32 页）

> 格式标准（全组沿用）：出处 → 核心命题（原文引用）→ 关键数值（原文）→ 对 P1/P2/P3 的对照 → 没读到的。
> 读法：pdftotext 全文逐节读，引用一律原文加页码；不转述成模糊话。
> 出处：TI SBOA114 – February 2006，Michael Steffes (High-Speed Products)；正文 8 节 20 页 + 附录 A–E（噪声推导/R3·C1 解/等 C/噪声增益零点），PDF 共 32 页。页脚页码 = PDF 页码。
> 附带：本文即 H5（sprpeo2 p.45）MFB 设计步骤点名引用的方法学文档，构成"应用笔记互引链"。

## 核心命题（原文）

1. 定位（摘要 p.1）："While the Multiple FeedBack (MFB) filter topology is well-known, its application to very high dynamic range analog-to-digital converter (ADC) interfaces requires a careful consideration of component value selection. This application report develops the ideal transfer function, then introduces a component selection methodology and discusses its impact on noise and distortion. The impact of amplifier Gain Bandwidth Product on final pole locations is also included."
2. 元件选择方法学的出发点——自由度问题（p.3）："there are more passive elements to be resolved than filter characteristics. Here, there are five elements and only three targets. This situation often leads to the very common equal-R assumption to reach a design where that is a somewhat arbitrary way to eliminate one degree of freedom. There should be a more rational way to select component values for these filters."
3. 方法学第①步——噪声预算定 R2（p.4）："the op amp noise voltage (squared) is targeted to be equal to the total noise power contribution of the R2 and R3 resistors at the output"（Eq.7）→ 二次方程解出 R2（Eq.9）；"This formula gives an initial suggested value for R2 (note that embedded in this solution is the assumption that R3 will then be set equal to R2). Both R2 and R3 may be set lower to improve noise."（p.4）
4. 方法学第②步——积分器极点位置（p.5）："(1 / ωoR2C2) is physically the ratio of the Integrator pole to the target ωo. Equation 12 sets a minimum limit for that ratio, while moving above that limit is essentially moving the Integrator pole out relative to ωo"；范围结论（Eq.23/24，p.8）："the (1 / ωoR2C2) target should be set within the range indicated in Equation 23"——"Setting 1/R2C2 = ωoQ(2AV+1) gives R3 = R2"，"while setting 1/R2C2 = ωoQ(AV+1) gives C1 = ∞ and R3 = 0"（下限=C1 有解的临界，上限=R3=R2 噪声控制点；Q=0.707、AV=2 例题代入分别得 2.12/3.53，p.8 与公式吻合）。
5. 噪声增益机理（p.5-7）："Any peaking in the noise gain will, of course, peak up the gain to the output for the total equivalent input voltage noise"；"Noise gain peaking will also reduce the loop gain. All other things being equal, reduced loop gain will show up as higher output harmonic distortion."；零点性质（p.7）："The noise gain zeroes are always two real zeroes."；"For Q > 1, it will necessarily be the case that one of the zeroes will fall below the target ωo. This observation says that higher Q targets in the MFB filter have an added peaking in the noise gain beyond just the desired filter pole peaking"；QC 上限 "the maximum possible value for QC is one-half … for any combination of desired AV and Q that sets Q • √(1 + Av) = 1. The most common condition … Q = 0.707 (Butterworth target) and AV = 2."（p.7）
6. 机理→失真实证（p.11）："The loop gain at 600kHz for Figure 5 is 42.8dB while that of Figure 7 is 37.4dB. The 5.4dB loss in loop gain as a result of noise peaking should show up directly in harmonic distortion."；Table 2（600kHz、2VPP、RL=100Ω）："Figure 4 −83.9 / Figure 6 −78.7"（HD3 dBc）；"The different noise gain shapes have indeed produced a 5.2dB drop in distortion performance—very nearly equal to the predicted 5.4dB drop from the difference in loop gains at 600kHz."
7. 非单位增益稳定运放的 CT 抬噪声增益法（p.12-14）："since the basic MFB circuit shapes the noise gain to be a unity gain feedback at high frequencies, a bit of additional work is needed"；"the noise gain can be raised at high frequencies by adding CT on the inverting node. Targeting a gain of 2 at high frequencies requires CT = C2 = 31.8pF"；效果："This results in an improved phase margin of 52 degrees"（CT=3pF 时仅 33°，p.13-14）。
8. 差分版与**全文唯一共模机理句**（p.16）："One critical implementation choice made in Figure 14 is to keep separate grounded capacitors on each side of the differential circuit. The same differential frequency response would result if these grounded capacitors were each replaced by a single differential capacitor across the two circuit halves at one-half the values shown, eliminating the ground connection. There are advantages and drawbacks to each approach. One of the attractions for the implementation of Figure 14 is that this circuit also acts to filter any common-mode signal at high frequencies. Single capacitors across the two circuit halves, on the other hand, will give a wideband, gain of 2 stage for any common-mode input signal or noise."
   另差分偏置（p.15）："If the best output DC precision is desired, the source impedance looking out of each noninverting input should again match the total DC impedance looking out of the inverting input of each channel as described in Figure 2."（=RP=R2+R1||R3 的 DC 偏置电流补偿，输出误差缩到 "IOS • R1"，p.3——**是偏置口径，不是差分失配口径**）
9. GBW 极点灵敏度（p.17-19）："the MFB filter is desirable in that the root loci, as amplifier gain bandwidth reduces, is in the direction of more stability"（"higher ωo and lower Q"）；Table 4（Target 200kHz Q=0.707 / Target 2MHz Q=3，GBW 220→8.8MHz）："Even at 220MHz GBW (100 times over the target FO), the actual Q is 5% lower than targeted."；"Table 4 suggests that the MFB filter is very robust to amplifier bandwidth variations in lower-Q designs."；"higher-Q designs will be very sensitive to the amplifier bandwidth, and thus quite a bit of GBW margin should be provided"；Q 校正："R3 is an independent tune for Q (Equation 5), R3 can be used to tune in the Q after a nominal design to account for the finite GBW of the amplifier. The Q equation has a positive derivative to R3, so increasing R3 increases the Q"。
10. 结论（p.20）："The nature of the MFB filter usually demands widely different capacitor values for implementation. Equal R on the two input resistors (R3 and R2 in Figure 1) is, however, a very reasonable design point with the feedback R1 then set to achieve the desired gain."；"In general, it seems that the MFB filter is more suited to lower-Q filter requirements."；"Higher-Q designs will suffer from noise gain peaking … This effect suggests that the higher-Q designs should be followed by a real pole (RC)"。

## ② 元件选择方法学有无失配/CMRR 内容（H4 方法学谱系对照）——结论：无

- **"matching" 全文仅两处，均非差分失配语义**：
  (a) p.5 等 C 设计："One option considered for many active filter designs is to set the two capacitors equal. This solution is sometimes considered preferable to get better matching in order to minimize the sensitivity functions."——指**滤波器参数灵敏度**（且随后 Eq.13–15 证明等 C 在 MFB 上要求 Q<0.353、"not particularly useful"）；
  (b) p.15 非反相端阻抗 "match the total DC impedance"——**偏置电流补偿**（Eq.A-2）。
- **共模内容仅 p.16 一句**（grounded vs floating 电容对 CM 信号的滤波/增益 2 放大），无 CMRR 数字、无容差→CMRR 退化、无失配消去条件。
- 方法学的全部自由度消去手段 = 噪声预算（Eq.9）+ 积分器极点比（Eq.12/21/23）+ R3 调 Q + CT 整形噪声增益 + GBW 余量/Q 预偏置；评价量 = 输出噪声、loop gain、HD3、相位裕度、极点轨迹。**谱系定位：Budak（Ref.4, 1974）一路的"噪声/失真预算 + 灵敏度"方法学，与 P1 的"失配消去条件"正交。**
- tolerance/temperature 零命中（对比：SBAA230 p.6 有一句 "subject to component tolerances and temperature"，本文连这句都没有）。

## 关键数值（原文）

- OPA820 例（1MHz Butterworth，Q=0.707，AV=2，p.8-9）：Eq.9 建议 R2 = 366.38Ω → 选 250Ω；C2 = 180pF，C1 = 1130pF，R3 = 250Ω，R1 = 500Ω；积分器/ωo 比 2.12（C1=∞ 下限）~ 3.53（R3=R2 上限）；噪声增益零点 707kHz/4.24MHz；PM 51°。反例（比值取 10，p.10-11）：C2 = 63.7pF，C1 = 571pF，R3 = 1.39kΩ，零点 268kHz/10.7MHz，PM 54°，HD3 −78.7 dBc（对照 −83.9）。
- OPA2614 例（3rd-order Bessel 5MHz 差分，p.12-16）：实极点 5.76MHz、FO = 7.24MHz、Q = 0.691（FilterPro 取极点）；R2 = 200Ω，C2 = 31.8pF，C1 = 189pF，R3 = 201Ω，R1 = 402Ω；CT = 3pF → PM 33°，CT = 31.8pF(=C2) → PM 52°、crossover 回落 100MHz；"20Log(290/125) = 7.3dB more loop gain"（OPA2614 vs OPA2613）；5V 单供 "10.5mA total supply current (53mW)"，400Ω 负载 2VPP "approximately 90dBc"。
- GBW 预偏置例（p.19）：FO = 5MHz、Q = 1.5 → 实际 Q = 1.4220；"(1.42 / 1.50) = 0.948 ratio, invert this ratio and target the Q at 1.056 times the target" → 重定 Q = 1.58 得实际 Q = 1.4938。

## 对 P1/P2/P3 的对照

- **P1（失配消去条件）**：H4 是"元件选择方法学"的最强文本，但精读确认**其方法学不含失配/CMRR 维度**——这本身是 P1 谱系对照的关键论据：连最讲究元件选择的 MFB 方法学都只做噪声/失真/稳定性预算，失配→共模转换在应用笔记层整体缺席。P1 若要引 H4，只能引 p.16 共模滤波句（grounded 电容滤 CM vs 浮接电容"gain of 2 stage for any common-mode input signal or noise"）作"拓扑选择影响 CM 传输"的旁证，**不得**把 Eq.9/Eq.23 的元件选择称为"失配设计"。
- **P2（Kelvin 地板）**：无直接内容。
- **P3（AAF 衰减上界）**：p.15 有一句结构性呼应："The real pole is implemented as the RC filter that often appears between the amplifier and the ADC."；p.20 "higher-Q designs should be followed by a real pole (RC)"——MFB+后置 RC 的三阶结构（Fig.13/14，5.76MHz 实极点）可作 P3 的拓扑实例，但无衰减上界讨论。
- **与 H5 互证**：H5 p.45 "Use MFB filter Equations — Design Methodology for MFB Filters in ADC Interface Applications" + p.48 ">55° phase margin for MFB filters"，正是本文 CT/相位裕度方法学的下游应用。

## 没读到的

- 任何失配、容差、温度漂移对 CMRR/滤波器对称性的影响（全文无）；
- Ref.1 = SLOA049、Ref.4 = Budak 1974、Ref.5 = FilterPro 原件未核；
- 随文 spreadsheet（5 个 worksheet）未下载核验。
