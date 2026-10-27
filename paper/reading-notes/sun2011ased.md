# 精读笔记 · Sun 2011《Based on Rotating Machinery Data Acquisition System Anti-Aliasing Filter Design and Application》（Adv. Mater. Res. 2011）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> H1 轴"配方线"样本（开关电容滤波器路线）：旋转机械监测 DAQ 的 AAF——
> 用 MAX297（8 阶椭圆开关电容滤波器 SCF）实现"截止频率随采样频率自调"，
> 给出安置规则 **fs ≥ 3·fm**（由 W=fr/fc=1.5 + Shannon 推出）；失配/共模零讨论。
> 原文为非母语英语写作（多处语法与笔误），引用一律照录并注明。

## 出处
- Haiyan Sun, Chunliang Zhang, Sen Li（广州大学）, "Based on Rotating Machinery Data Acquisition System Anti-Aliasing Filter Design and Application," *Advanced Materials Research*, Vols. 328–330 (2011), pp. 2328–2332. DOI: 10.4028/www.scientific.net/AMR.328-330.2328（Trans Tech Publications）。
- 本地文件 `fulltext/H1-ΣΔ-AAF/sun2011ased.pdf`，正文 5 页（PDF p.1–p.5 = pp.2328–2332，p.6 为刊物尾页）。

## 核心命题（原文）
1. **配方本体：MAX297（8 阶椭圆 SCF）内置到 AD 侧，截止频率随采样频率自调**（p.2328, Abstract）：
   > "adopt the integrated with AD module based on the 8th -order low pass elliptic switched-capacitor filter MAX297 for filtering, thereby proposes a portable data acquisition system."
   > "In this work the anti-aliasing filter with unique design which is that the cutoff frequency of the filter can be automatically adjusted basing on the sampling frequency of AD."（p.2329）
2. **AAF 必须在模拟域（采样之前）——配方线的共同前提**（p.2328, Introduction）：
   > "The most primitive consideration to solve the problem is from the digital domain, apparently it is unadvisable. Once the signal sampling is accomplished, some signal aliasing into the frequency band of interest, it can not be removed from the signal. Anti-aliasing filter must be in the analog domain, before the signal is sampled."
   > "we must learn the highest frequency, and the sampling frequency is must to be higher than 2 to 10 times of the highest frequency."
3. **SCF 机理：截止频率由时钟决定（等效电阻 R=1/(fc·C)）——把截止频率精度从元件匹配转嫁给时钟精度**（p.2329, Switched-Capacitor Filters）：
   > "The switched-capacitor of the switched-capacitor filter which driving by clock frequency, can be equivalent to an equivalent resistance R=1/fc.C, which is related to clock frequency, and C is the capacitance of switched-capacitor group, fc is the clock frequency of the switched-capacitor filter. As external clock altering fc, equivalent resistance R will change, time constant of filters and transmission bands in low pass filter will further change."
   （对 P1 有对照意义：SCF 是"用时钟比定截止频率"的技术路线，**回避了 RC 时间常数匹配问题**——但引入 SCF 自身的采样性混叠新问题，本文未察觉，见"没读到的"。）
4. **MAX297 规格引用（配方理由 = 手册参数）**（p.2329）：
   > "The design of the anti-aliasing filter was to adopt the integrated with AD module based on the 8th -order low pass elliptic switched-capacitor filter MAX297 [3]he ratio of Clock frequency fclk and cut-off frequency fc is 100:1. The range of variation of cut-off frequency is from 0.1 kHz to 25 kHz. Stop band attenuation Rs is 80dB. The elliptic filter with the best belt of transition attenuation character compare with the same order Butterworth filter, Bessel filter, Chebyshev filter, which is approach to ideal low-pass filter."
   （"[3]he" = 原文笔误（"[3]. The"）。**Rs = 80 dB 与 P1 方法学 D1 的 ≥80 dB 数值相同**——但这是器件手册规格，非推导需求；引用时可作"80 dB 是货架 SCF 的典型阻带能力"佐证。）
5. **安置规则推导：W=fr/fc=1.5 + Shannon → fc ≤ fs/3，取 fc=fm → fs ≥ 3·fm**（p.2330–2331, 式(1)–(5)）：
   > "According to Shannon's sampling theorem, in order to achieve the facticity of sampling for the analysis of signal, should meet the following condition: fs≥2fr (1) suppose: W= fr /fc (2)"
   > "As shown in Fig.4 = fr/fc= w/wc=1. 5 of MAX293; From the eqution of (1) and (2) we can get: fc ≤ fs/3; (3)"
   > "Usually when we design the filter, will suppose that: fc=fm. so we can get that: (4) fs≥3fm (5)"
   （"MAX293"为原文笔误（应为 MAX297），照录；fr = 衰减带边频（阻带边），由 MAX297 归一化频响曲线读出 fr/fc = 1.5。）
6. **应用数值实例（风机监测）与硬件**（p.2331, The accomplishment of hardware）：
   > "The portable data acquisition system mentioned in the paper constitutes of USB 2.0 interface controller chip, CY7C68013A, twelve site A/D converter MAX197 and MAX297."
   > "the rotate speed of the blower is 1000r/min, and the working frequency is 16.7 Hz. The fault diagnosis system should execute the analysis of the harmonic component in the range of five times of the frequency, and get the biggest analysis frequency fm=100Hz. According to the equation (4) and (5), we know that as long as fc=100Hz, fs=300Hz, then can guarantee the facility of signal sampling. And the self-adapting feature of filter is to reflect by fclk=100fc=10 kHz"
   （CY7C68013A 48 MHz、内部定时器最小周期 83.3 ns 双定时器合成 fclk 与采样时钟；MAX197 为 12 bit ADC——"twelve site" = 12-bit 之误。）
7. **效果断言（无实测数据支撑）**（p.2332）：
   > "It is noted that, for the achievement of self-adjustment anti-aliasing filter of the data acquisition system, the signal with any frequency will not aliasing, and can make sure the facticity of the frequency component in the range of one third times frequency."
   （"任意频率都不会混叠"的断言显然过强——SCF 时钟混叠、通带波纹等均未计及；配方文风的典型夸大，照录存疑。）

## 关键数值（原文）
- MAX297：8 阶椭圆低通 SCF；fclk:fc = 100:1；fc 范围 0.1–25 kHz；阻带衰减 Rs = 80 dB（p.2329）。
- 安置规则：fs ≥ 2fr（Shannon）+ fr/fc = 1.5 → **fc ≤ fs/3**；设计取 fc = fm → **fs ≥ 3fm**（p.2330–2331 式(1)–(5)）。
- 实例：风机 1000 r/min（16.7 Hz）、5 次谐波分析 → fm = 100 Hz → fc = 100 Hz、fs = 300 Hz、fclk = 10 kHz（p.2331）。
- 硬件：CY7C68013A（USB 2.0，48 MHz，定时器最小 83.3 ns）、MAX197（12 bit ADC）、MAX297；USB 总线供电（p.2331）。
- 全文无 Rp（通带波纹）数值（Fig.3 图例中仅作为符号出现）、无元件容差、无实测频响或混叠抑制数据。

## 对 P1/P2/P3 的对照
- **P1（G_DC=H_N−H_P≡0 消去条件）**：相关度 **低（技术路线旁支）**。单端单通道、无两路匹配议题；但 SCF 路线本身对 P1 有叙事价值：**截止频率精度由时钟比（100:1）而非 RC 匹配决定**，等价于用"时钟精度"替代"元件匹配"来固定 τ——可作为 P1 讨论"为什么选分立 RC 而非 SCF"时的对照点（SCF 代价：自身为采样系统、时钟馈通、需要预滤波；本文恰未讨论这些，见下）。
- **P2（Kelvin 结构地板）**：相关度 **无**。
- **P3（平坦度约束下衰减可达上界）**：相关度 **低**。给了"过渡带比率 W=1.5 → fs ≥ 3fm"的安置规则（与 zamaruiev2019 的 0.05·fco、20·fco 规则同族：**都是频率安置规则，非能力上界**）；无平坦度数值（Rp 只出现符号），80 dB 是器件规格不是设计推导。
- **方法学（D1–D4/D8）**：Rs = 80 dB 与 D1 数值巧合（但性质不同：货架规格 vs 工程需求推导）；fs ≥ 3fm 的"3"来自椭圆响应 fr/fc=1.5，与 OSR 类比时可作参照（本文 OSR=3，极低，对应信号带宽极窄的场景）；无共模内容（D8 不适用）。
- **killRisk**：**无**。不冲击 P1/P2/P3；引用价值：①SCF 自调截止频率这条"避开 RC 匹配"的路线存在但文献同样不讨论其代价；②"any frequency will not aliasing"式断言是配方线可信度的自曝。

## 没读到的
- **SCF 自身的混叠机制**：开关电容滤波器内部以 fclk（=100·fc）采样，fclk 附近的干扰会混叠回带内——MAX297 手册要求前置连续时间低通预滤波，本文**完全未讨论**（这是该配方能否成立的要害缺口）。
- 时钟馈通（clock feedthrough）、SCF 噪声底、时钟抖动对等效截止频率的影响——零讨论。
- 通带波纹 Rp 数值、实际频响曲线测量、混叠抑制实测——零数据（结论"apply successfully"无实测支撑）。
- 元件容差/通道间匹配/共模——零讨论。
- 式(3) 推导只取"MAX297 归一化曲线 fr/fc=1.5"单点，未考虑 fc 全范围（0.1–25 kHz）内响应一致性；"MAX293"笔误（应为 MAX297）与"twelve site"（=12-bit）笔误均照录待核。
- 与传感器输出（4–20 mA / 0–5 V 标准工业信号，p.2329）之间的阻抗/驱动匹配——未讨论。
