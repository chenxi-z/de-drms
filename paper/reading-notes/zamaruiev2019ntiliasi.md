# 精读笔记 · Zamaruiev 2019《Anti-Aliasing Filter in Digital Control System for Converter with Active Power Filter Function》（ELNANO 2019）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> H1 轴"配方线"定位：电力变换器数字控制系统（DCS）场景下的 AAF 选参**规则**文献——
> 给出"一阶 RC 可用作 AAF 的频率安置条件（信号频率 ≤ 截止频率的 5–10%）"，理由是**带内幅相偏差预算**；
> 但通篇无元件失配、无共模讨论。

## 出处
- V. Zamaruiev, V. Ivakhno, B. Styslo（乌克兰哈尔科夫理工学院）, "Anti-Aliasing Filter in Digital Control System for Converter with Active Power Filter Function," *2019 IEEE 39th International Conference on Electronics and Nanotechnology (ELNANO)*, pp. 797–801. DOI: 10.1109/elnano.2019.8783951。
- 本地文件 `fulltext/H1-ΣΔ-AAF/zamaruiev2019ntiliasi.pdf`，5 页。**页码换算**：PDF p.1–p.5 = 期刊 pp.797–801（下文引用标 PDF 页码并括注期刊页）。

## 核心命题（原文）
1. **配方文化实证：开发者直接照抄微控制器厂商推荐的滤波器参数、不做设计**（p.1, Introduction）：
   > "In the simplest DC/DC converters, the DCS developers often did not develop an AAF, but used the filter parameters recommended by the microcontroller manufacturer."
   （这正是 P1/H1 轴要批判的"给配方不给理论"生态的应用侧证据；本文动机即此类照抄在宽谱反馈信号（APF）下失效。）
2. **按"截止频率准则"设计的 AAF 会带来重大控制误差，提高阶数反而更糟**（p.1, Introduction）：
   > "The use of AAFs, calculated by the cut-off frequency criterion, also leads to incomplete harmonic suppression. Increasing the filter order only makes things worse."
   （"更糟"指高阶滤波器非线性相位/群时延失真加剧——见命题 5。）
3. **用幅相复合偏差 ΔU 度量滤波器非理想性：信号恰在截止频率处 → 70% 偏差**（p.3, III + 式(6)(7)；期刊 p.799）：
   > "The voltage at the output of the filter is ULPF = 0.707*Utest, the phase shift between the voltages – ϕ = -45°. The voltage at the control system input is ΔU = 0.707* Utest, which will result in a 70% deviation of the controlled parameter from the nominal value."
   > "ΔU / Utest = (|KLPF|² – 2|KLPF| cosϕ + 1)^0.5, (7)"
   （原式印为上标/根号形式，此处按 PDF 排版复原：ΔU/Utest=(|K_LPF|²−2|K_LPF|·cosϕ+1)^0.5。ΔU 是理想输出与实际输出的**矢量差**，同时计及增益与相移——比纯幅度纹波口径更严。）
4. **一阶 RC 用作 AAF 的安置配方：信号带宽压到截止频率的 5–10% 以内**（p.4, III-B；期刊 p.800）：
   > "At frequencies below the cut-off frequency (ωr < 1), the voltage deviation drops at a rate of 20 dB per decade. Thus, to obtain an accuracy of 10%, the signal frequency ω should not exceed 0.1ωco, etc. To obtain regulation accuracy no worse than 5%, the follow condition must be met: fc<0.05 fco. (8)"
   > "The RC filter can be used as an anti-aliasing filter by the DCS in the case of a narrow-band low-frequency feedback signal with a maximum frequency fс not exceeding (5-10)% of the cut-off frequency fco of the filter."
   （配方的"理由"链完整：偏差随相对频率 20 dB/十倍频下降 → 反推 f 信号/f 截止比。另一侧约束为式(9) "20 fco < fPWM"——PWM 开关频率须高于 20×fco，混叠残余才 <5%。）
   又（原文记号疑有排印错误，照录）：
   > "Up to a frequency of 0,05ωr the filter is close to the ideal low-pass filter with an added distortion less than 5%. At frequencies above 20ωr the filter gain is less than 5%, which limits the signals in the case of spectra aliasing at the appropriate level."（p.4）
   （按上下文，此两句的 "ωr" 应为 "ωco"（0.05ωco / 20ωco）——**原文排版笔误，引用时注明待核**。）
5. **高阶模拟滤波器的相位/群时延失真是 DCS 适用性的关键限制**（p.4, III-C；期刊 p.800）：
   > "However, the synthesis of these filters does not impose requirements on the phase response or users of DSP systems formulate own requirements. High-order analog filters have a non-linear phase response and, as a result, non-permanent group delay. This property of filters determines the phase distortion of the signal that passes through the filter."
   （对 2、5、9 阶椭圆滤波器给出增益与 ΔU 曲线（Fig. 9），结论：阶数↑→过渡带陡但相位失真↑，"Increasing the filter order only makes things worse" 的机理所在。）
6. **结论重申：截止频率特性导致最高 70% 控制误差，替代法 = 双边界频率图解法**（p.5, Conclusion；期刊 p.801）：
   > "It was demonstrated that the use of a cut-off frequency as a characteristic of the bandwidth of the anti-aliasing filter in converter systems leads to significant control errors (up to 70%)."
   > "The maximum signal frequency is the one on which the distortions introduced by the filter not exceed the desired ones. The minimum frequency is the lowest signal frequency (in high-frequency components) on which, in the case of spectra aliasing, the influence on the control system will be no more than specified."

## 关键数值（原文）
- 一阶 RC：fco 处 |K|=0.707、φ=−45°、ΔU/Utest=0.707（=70% 误差）；ωr<1 区间偏差以 **20 dB/十倍频**下降（p.3–4）。
- 精度判据链：10% 精度 → f ≤ 0.1·fco；**5% 精度 → fc < 0.05·fco（式(8)）**；混叠残余 <5% → **20·fco < fPWM（式(9)）**（p.4）。
- 考察阶数：1 阶（RC）、2/5/9 阶（椭圆/Cauer），另提及 Butterworth、Chebyshev（p.4）。
- 硬实时约束：tsum = ΔtLPF + ΔtDSP + ΔtC = nT（式(2)，p.2）——AAF 时延必须并入控制回路总时延且凑整到系统特征周期 T 的整数倍；反例 tsum=1.5T 时反馈反相、误差加倍（p.2, Fig. 2）。
- 全文无量化的元件容差/温度数据；无具体 R、C 取值（配方是"频率比"层面，不是元件值层面）。

## 对 P1/P2/P3 的对照
- **P1（G_DC=H_N−H_P≡0 消去条件）**：相关度 **低（配方线旁证）**。本文的条件是**频率安置条件**（f 信号 vs fco 的比例），完全不涉及两路滤波器传递函数匹配或元件失配——它的"理论"止步于单只滤波器的幅相偏差预算，正是"配方有理由但理由不覆盖失配"的 H1 典型样本。
- **P2（Kelvin 结构地板）**：相关度 **无**。无差分/四线/引线电阻内容。
- **P3（平坦度约束下衰减可达上界）**：相关度 **中**。本文实质是"带内偏差预算约束下如何安置/选择 AAF"：其 ΔU（幅相复合）随 20 dB/dec 下降的定量关系，等价于给出一阶 RC 的"平坦度—抑制"联合工作区（带内精度定 fc/fco 上比，带外抑制定 fPWM/20·fco 下比）；但未形成"给定平坦度约束求衰减上界"的一般化命题，且其口径含相位（比 P3 若只看幅度更严）。与 D4（≤0.5 dB@16 kHz ≈ 5.9% 幅度）对照：本文 5% 矢量偏差判据与 D4 同量级，可互为佐证口径选择的行业惯例。
- **方法学（D1–D4/D8）**：无共模/CMRR 内容（D8 不适用）；其混叠抑制量化只有"增益 <5% 即混叠影响 <5%"一级近似（p.4），远粗于 D1/D3 的 dB 级门槛。
- **killRisk**：**无**。不触及 P1/P2 的任何主张；P3 方向它给出的是"安置规则"而非"上界"，不冲突。

## 没读到的
- 元件失配（R/C 容差）对偏差的影响——零讨论；两路/差分结构的匹配话题零讨论。
- 共模/CMRR、传感器（电流/电压互感器）前端——零讨论（图 1 方框里仅一个 LPF 方块）。
- 式(4)(5) 正文未印出（"frequency response and phase response"公式编号在文中但表达式以图形式呈现——式(3) |K|=(1+(ωRC)²)^−0.5 有印出）；Fig. 7/9 为对数刻度示意曲线，无数值表。
- 采样频率 fs 与 fco 的显式关系式（只隐含在 Nyquist 条件(1)与图 4 中）；"0,05ωr / 20ωr" 记号疑误（见命题 4）。
- 未与 ΣΔ ADC 场景关联（对象是 PWM 变换器硬实时控制，AAF 时延是主角；ΣΔ 场景中 AAF 时延问题不同——引用时勿平移）。
