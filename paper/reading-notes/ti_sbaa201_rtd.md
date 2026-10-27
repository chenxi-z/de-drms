# 精读笔记 · Chioye 2013/Rev.A 2023《RTD Ratiometric Measurements and Filtering Using the ADS1148 and ADS1248 Family of Devices》（TI SBAA201A, Application Report）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> **killRisk 登记件**：SC 输入 ΣΔ 单级差分/共模 RC 滤波正典（C_DIFF≥10×C_CM + 信号/基准角频率匹配）。

## 出处
- TI Application Report SBAA201A，2013-03 初版，2023-03 Rev.A；作者 Luis Chioye（High-Performance Analog）。
- 全文 13 物理页（正文页码 1–12 与 PDF 物理页一致，第 13 页为免责声明）。
- 对象器件：ADS1148（16 bit）/ADS1248（24 bit）ΔΣ ADC，内置 IDAC 电流源 + PGA + 数字滤波器；RTD 比率式测温。

## 核心命题（原文）
1. **比率式消去激励漂移/噪声是结构性收益**（p.1 Abstract）：
   > "The ratiometric operation has an advantage because the errors due to the excitation current source drift and noise tend to cancel. In order to maintain good noise cancellation over the input signal range, make sure that the analog-to-digital converter (ADC) external input filter is matched to the filter at the reference input."
   （比率式结构令激励源漂移与噪声趋于对消；但对消的维持条件是**输入外部滤波器与基准滤波器匹配**——本文全部内容就是这一条件。）
2. **时间常数匹配 = 失配退化判据（单级 τ 匹配正典句）**（p.3）：
   > "However, it is important that the input filter and the reference filter have matched time constants or the cancellation of current source noise can degrade, leading to increasing noise with increasing signal level."
   （输入/基准滤波器时间常数须匹配，否则电流源噪声对消退化为"噪声随信号增大而增大"——失配误差与信号幅度成比例，这正是 H_N≠H_P 残差按比值放大的表现。）
3. **消去的精确表述：误差须"同等地"反映在两条路径**（p.3 §2）：
   > "In order for effective ratiometric cancellation to occur, the errors due to the excitation source drift and noise must be equally reflected at the inputs of the ADC, and at the reference inputs of the device."
   （"equally reflected" = 两路径传递函数相等的物理表述；随后给出操作准则："make sure to balance the corner frequency of the reference low-pass filter to the corner frequency of the input low-pass filter."）
4. **C_DIFF≥10×C_CM 启发式及其机理（正典原句）**（p.3）：
   > "The differential capacitor value is typically chosen to be at least 10 times larger than the common-mode voltage capacitors."
   且（p.4）：
   > "Providing this ratio of capacitors helps to mitigate the effects due to the mismatch of the common-mode capacitors, where the asymmetric noise attenuation caused by the commonmode capacitor mismatch is attenuated to insignificant levels."
   （10× 比例使差分角频率比共模低约 20×，共模电容失配导致的不对称衰减被压到"不显著"——**这是用比值压制而非元件条件消去** CM 失配，比 P1 的 G_DC≡0 元件条件弱一档。）
5. **RTD 阻值随温度变化 → 差分角频率漂移 + CM 角频率失配，但影响有主次**（p.5）：
   > "The resistance of the RTD sensor changes with temperature measurement, and thus changes the frequency response of the differential filter. It also causes a mismatch on the corner frequencies of the input common-mode filters, but the impact of noise cancellation caused by the common-mode filters is not as significant as the differential filters. Scale the R1 and R2 resistors to be larger than the RTD sensor in order to help mitigate this effect."
   （缓解手段是让串联电阻远大于传感器——把网络"拉回"以固定电阻为主的时间常数。）
6. **承认无法全匹配 → 差分路径优先**（p.5）：
   > "Although it is not always possible to exactly match the corner frequencies of all the filters, a good compromise is to attempt to balance the corner frequencies of the input path differential filter and the reference path differential filter because these filters have a dominant effect in the performance."
   （**TI 自己承认"不可能精确匹配所有滤波器"**——工程正典的实际判据是"主导项匹配 + 次要项压制"，不是全频段 G_DC≡0。）
7. **失配实验机理（噪声不对称 → 对消失效）**（p.7）：
   > "There is no filter in the ADC input path; therefore, the noise produced by the excitation source is reflected at the ADC inputs. However, the RC filter at the reference path attenuates noise components seen at the reference inputs. The noise signals seen by the reference inputs and the ADC are not attenuated equally; therefore, ratiometric noise cancellation is not effective."
   及：
   > "The ADC output conversion results are proportional to VIN / VREF. As the input signal increases, uncorrelated noise present on either VIN or VREF results in increased measurement noise. When the filters are matched, the noise is correlated and the measurement noise remains constant."
   （"not attenuated equally"/"uncorrelated → correlated" 是对 H_N(ω) vs H_P(ω) 相等条件的经验版陈述：匹配时噪声相关、残差恒定；失配时不相关、残差随信号增长。）
8. **匹配实验结论（噪声不随信号增长）**（p.9）：
   > "The reference path and input path filter corner frequencies are closely matched; therefore, the input-referred noise remains constant as the differential voltage increases."
   （注意措辞是 "closely matched" 而非 "exactly matched"——工程正典容忍残差，靠的是残差量级足够小。）
9. **角频率公式（零值时间常数法）**（p.4 引用 [1]）：
   > "In order to analyze the circuit in Figure 2-2, a zero-value time constant technique approach[1] may be used to obtain an estimate of the differential and common-mode corner frequencies involved."
   （[1] = Gray/Hurst/Lewis/Meyer《Analysis and design of analog integrated circuits》4th ed. §7.3.2 pp.517–520。）

### 公式（pdftotext 将斜体/下标打碎，按字形还原，还原处标〔按字形还原〕）
- Eq.1 差分角频率（p.3）原文碎片：`BF3@$ = 1 / 2è:41 + 42;(%+0 + %%/)2`
  〔按字形还原：f_DIFF = 1/(2π(R1+R2)·(C_IN_DIFF + C_IN_CM/2))——待核；该式与"10×时差分角频率低20×"自洽：2R×10.5C vs R×C → 21×≈20×〕
- Eq.2 共模角频率（p.3）碎片：`BF3@$ = 1 / 2è:41%%/;`〔按字形还原：f_CM = 1/(2π·R1·C_IN_CM)——待核〕
- Eq.3 输入差分（p.5）：`1 / 2è%+0_&+(( :46& + 41 + 42;` = f = 1/(2π·C_IN_DIFF·(R_TD+R1+R2))〔C_IN_DIFF 与 R_TD 为下标还原，待核〕
- Eq.4/5 输入共模（p.5）：f = 1/(2π·C_IN_CM1·(R1+R_TD+R_BIAS))、f = 1/(2π·C_IN_CM2·(R2+R_BIAS))
- Eq.6 基准差分（p.5）：f = 1/(2π·C_REF_DIFF·(R_BIAS+R3+R4))；Eq.7/8 基准共模：f = 1/(2π·C_REF_CM1·(R3+R_BIAS))、f = 1/(2π·C_REF_CM2·(R4))
- "20×" 结论原句（p.4）：
  > "When the CDIFF capacitor value is chosen to be 10 times larger than the common-mode capacitors, the resulting differential filter provides a corner frequency that is 20 times lower than the common-mode filter corner frequency."

## 关键数值（原文）
- 实验配置（p.6）：IDAC = 1000 µA；RBIAS = 2 kΩ → VREF = 2 V；PGA = 8 V/V @ 20 SPS → 满量程 250 mV；传感器用电阻箱模拟，0–250 Ω 扫描。
- 失配基准滤波器角频率（p.6）："corner frequencies of 130 Hz, 13 Hz, and 1.3 Hz"（CREF_DIFF = 10 µF / 1 µF / 0.1 µF）。
- ADS1248 本底噪声（p.7）："approximately 350 nVrms when the device is configured with a PGA gain of 8 V/V at 20 SPS"。
- 失配最严重情形（p.7）："The input referred noise changes from 350 nVrms to 1 µVrms as the differential input voltage approaches the full-scale range."（350 nV→1 µV ≈ 2.9×，且**随信号增长**——失配残差的定量画像）。
- 匹配例（p.8）：R1=R2=6.04 kΩ、CIN_DIFF=51 nF、CIN_CM=5 nF（10.2×）；输入差分角频率随 RTD 0→250 Ω 仅从 258 Hz 变到 253 Hz；基准差分角频率 ≈260 Hz（p.8）："The differential mode filter corner frequency at the reference path is approximately 260 Hz."
- 三线制接法（p.10）：IDAC 从 IEXC1/IEXC2 引脚注入，"the series resistors of the low-pass filter are outside the excitation current path"（避免滤波电阻进激励路径造成压头与漂移误差；IDAC=500 µA×2）。
- 建立时间（p.11）："when performing a 20-bit resolution measurement, after initially biasing the sensor, the user must wait up to 14 RC filter time constants for the measurement to settle within ½ an LSB."；Table 3-1：16 bit→11.78、18→13.17、20→14.56、22→15.94、24→17.33 个时间常数。
- 元件选择（p.6）："Use 1% resistors with resistances below 20 kΩ to make the dc errors due to the differential input bias current negligible."；"the thermal noise contribution of the resistors is negligible when the resistor values are kept below 20 kΩ"；电容首选 "COG (NPO)"（"provides the most stable electrical properties over voltage, frequency, and temperature changes"）。
- 滤波器阶数（p.3）："This passive filter provides a first-order 20-dB/decade roll-off characteristic."

## 对 P1/P2/P3 的对照
- **P1（消去条件）**：相关度**高**。本文就是"单级 τ=R·C 匹配"工业正典的完整陈述：单级一阶 RC 下，输入/基准两条路径各为一个纯一节 τ，匹配角频率 ⟺ 两路径传递函数全频段相等（1/(1+jωτ_N)=1/(1+jωτ_P)），即 P1 的"单级 τ 匹配充要"在工程上成立并被 TI 依赖。但注意三点划界材料：①TI 判据是"角频率（τ）匹配"，比 P1 的元件级 G_DC≡0 条件粗（同 τ 可由不同 R·C 组合达成，此时两路径 R 分压比不同——但 TI 场景信号为近直流、基准/输入同为纯电阻性分压，未暴露该差异）；②TI 明言"not always possible to exactly match the corner frequencies of all the filters"，CM 路径靠 10× 比值压制而非消去；③全文**只处理单级一阶网络、近直流信号、20 SPS**，没有任何多级梯形网络或全频段分析。
- **P2（Kelvin 结构地板）**：相关度**中**。比率式连接（同一激励电流同时流过传感器与 RBIAS 基准）是"结构性比率"的最简形态，本文给出其失效面：结构上共用电流**不能**自动保证比率保持——两腿传递函数失配时，输入参考噪声从 350 nV 涨到 1 µV（≈9 dB）且随信号增长。可作为 P2 论证"结构性比率只是消去了激励源自身的慢漂移，网络失配仍需元件条件兜底"的工业例证。
- **P3（衰减可达上界）/增量四（门槛化方法学）**：相关度**低**。无衰减上界讨论；但 §3.1 的"失配→噪声随信号增长"实验曲线是门槛化证据的现成范式（固定本底 350 nVrms + 失配残差项与信号成比例）。
- **killRisk 判断：须划界（非撞车）**。理由：本文是 P1"单级 τ 匹配充要"的正典工业背书（应引用），但其范围严格限于**单级一阶 RC + 直流/近直流 + CM 靠 10× 比值压制**；它既不支持也不反驳 P1 的"多级梯形不再充分"主张（从未分析多级）。P1 主张多级/全频段时须显式声明超出本文范围，并把本文的"closely matched/20× 压制"作为工程容忍残差的实际做法引用；同时 P1 若声称"τ 匹配 = 元件条件"须注意 TI 的 τ 匹配判据本身比元件匹配弱（见上 P1 条①）。无 app note 代码示例（本篇为叙述+公式，无代码注释段）。

## 没读到的
- Figure 3-2/3-4 的数值点（曲线图，pdftotext 只剩轴刻度文字，无法逐点引用）；具体噪声谱或频域失配数据（全部为直流测量）。
- Eq.1/2 的精确分母形式（pdftotext 打碎下标，按字形还原并自洽性验证，仍标待核）。
- ADS1248 内部数字滤波器/SC 采样对输入 RC 的相互作用（本文不涉及——其 SC 输入细节在器件手册与 SBAA230 类文献中）。
- Rev.A 相对初版的实质技术改动（修订记录仅称"Updated the numbering format"，p.12，待核——bib 记录称初版 10 页、本次 13 页，差异或仅排版）。
