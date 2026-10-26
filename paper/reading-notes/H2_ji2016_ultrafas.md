# 精读笔记 · Ji 2016《Ultra-fast ACPD measurement system ... and precision impedance analyzer for eddy current measurement》（Iowa State 博士论文，167 页）

> 格式标准（全组沿用）：出处 → 核心命题（原文引用）→ 关键数值（原文）→ 对 P1/P2/P3 的对照 → 没读到的。
> 读法：pdftotext 全文逐章读，引用一律原文加页码；不转述成模糊话。
> **页码约定**：正文引文页码 = 论文印刷页码（arabic），PDF 页 = 印刷页 + 5（例：文 p.12 = PDF p.17）。
> **提取缺陷声明**：该 PDF 的内嵌公式符号字体未渲染——pdftotext 提取与页面渲染里行内符号均为空白
> （例："the output current is ␣"）。引用遇缺符号处以 ▯ 标注，不猜符号内容。
> 原文另有两处编号瑕疵：Figure 1.9 一号两图（比较图 + 软件界面图）；Table 2.3/2.4 混用。

## 出处

- Yuan Ji, "Ultra-fast alternating current potential drop measurement system for materials
  characterization and precision impedance analyzer for eddy current measurement",
  PhD dissertation, Iowa State University, 2016（导师 John Bowler；委员会含 Nicola Bowler、Degang Chen）。
- 两条产品线：**APS1006**——ACPD（交流电位降）四点探针材料表征仪（Ch1–5，重点在硬件 Ch2 + 校准 Ch3）；
  **Ch6**——锁相放大器式精密阻抗分析仪（涡流检测）。
- 本地文件：Obsidian 库 `20-硬件工程/10-项目设计/p1-文献谱系/fulltext/H2-差分CMRR/ji2016ultra.pdf`。

## 核心命题（原文）

1. **共模误差是 ACPD 小信号测量的主矛盾**："The common mode voltage can be as high as 500 mV in amplitude,
   while the differential pick-up voltage is within range of several micro volts in amplitude."（文 p.12；PDF p.17）
2. **CMRR 指标本身不够，靠极性反转 + 软件两次测量相消**（详下 §五问问①②）。
3. **系统架构 = 驱动侧/拾取侧半独立双分区、共享时钟、同时采集**："in order to obtain normalized potential drop,
   it is imperative to make two measurements, one for drive current and the other for pick-up voltage.
   In this design, these two tasks are handled simultaneously, saving 50% of measurement time instantly."（文 p.19；PDF p.24）
4. **最终输出是比值**（拾取电压/驱动电流参考）+ 校准数据修正："Calibration data characterizes the transfer function
   of the amplifier and filter involved in previous signal conditioning, and can be used to retrieve the actual
   ratio between pick-up voltage and reference voltage from uncalibrated version."（文 p.93；PDF p.98）
5. **精度锚定在精密电阻上**："the accuracy of current sampling resistor and resistor divider determine the quality
   and reliability of calibration."（文 p.95；PDF p.100）——与我们 Rsense/R_ref 锚定是同一方法论。

## 五问专项回答（原文 + 页码）

### ① "即使 120 dB CMRR 也不够"的语境

**原文（文 p.12；PDF p.17，§1.3 商用 SR830+Kepco 分立系统的缺陷分析）**：

> "In reality, the small differential pick-up voltage is of interest. But the common mode voltage due to
> contact resistance of connectors and resistance of cables make it very difficult for the LIA input analog
> front end to completely reject the common mode signal. The common mode voltage can be as high as 500 mV
> in amplitude, while the differential pick-up voltage is within range of several micro volts in amplitude.
> **Even for an instrumentation amplifier that has common mode rejection ratio (CMRR) of 120 dB, it is still
> not enough to give a CMR error free measurement result.**"

**语境要点**：

- 共模源 = **连接器接触电阻 + 电缆电阻上的压降**（不是天线耦合），随驱动电流流过而产生；CM 高达 500 mV，差模信号仅几 µV（差共比 ~10^5）。
- 120 dB = 电压比 10^6，500 mV → 残余 0.5 µV（此换算为笔者算术核对，论文未列式），对几 µV 的信号仍是百分之几到几十的误差——故"not enough to give a CMR error free measurement result"。
- 紧接着的实测佐证（文 p.13；PDF p.18）："Figure 1.9 demonstrates that with SR830 LIA's CMRR of 100 dB [10],
  **the CMR error is actually on par with desired pick-up signal**."（Fig 1.9 两条曲线——differential mode / common mode
  的 RefPD 均在 ~3 µV 量级，肉眼同量级。）
- **注意语境边界**：这是对**旧分立系统**（SR830 单通道 LIA + 开关箱 + 长电缆）的批判，是他做 APS1006 的动机段；
  不是对自家新机的指标声明。

### ② DPDT 极性反转 + 两次测量软件消 CM：方法与残余误差

**方法原文（文 p.12；PDF p.17）**：

> "Another DPDT relay is used to toggle the polarity of pick-up input voltage, **eliminating CMR error in
> software by measuring the pick-up voltage twice**."

**机制**：共模误差不随输入极性翻转而翻转，差模信号翻转；两次测量相消（论文只给这一句，**未列公式**，
未说明是 (a−b)/2 还是分别归一后相减）。硬件落点：

- 前置放大器盒内："**K5 is a DPDT relay for common mode cancellation.** Since it is a mechanical relay and the
  insertion resistance is minimal, it will not introduce measureable noise."（文 p.65；PDF p.70）
- 前置盒定位："a pre-amplifier ... is inserted between the four-point probe and the input port of pick-up side,
  **providing polarity toggling (common mode cancellation) and about 67 dB gain**."（文 p.20；PDF p.25）——
  即共模消去做在**电缆之前**，配合长电缆噪声问题一起解决（Table 2.1 item 20："Gain = 67 dB. Differential output
  for better noise rejection"，文 p.22）。
- 开关箱里还有**另一只 DPDT**（与消 CM 无关）：因 SR830 单输入，"a DPDT mechanical relay mounted in the switch box
  is used to select which of the two ▯▯ signals is connect to the differential input of LIA"（文 p.12；PDF p.17）——
  缺失符号据 Fig 1.6（文 p.8；PDF p.13）为 **Ref Voltage（标准电阻上的驱动电流参考）与 Pick-up Voltage** 二选一。

**残余误差**：**论文未给任何定量残余误差、未给相消公式、未分析继电器接触重复性/两次测量间源漂移**。
唯一相关表态是插入电阻"minimal ... will not introduce measureable noise"（文 p.65）。定量事实只有相消前的：
500 mV CM、SR830 100 dB 时 CMR 误差与信号同量级（①）。

**代价（对我们的对照点）**：两次测量使低频耗时翻倍——"Data accusation of 1 Hz signal takes up to 7 seconds to complete,
**if you take into consider of common mode cancellation by toggling input polarity, 1 Hz alone will cost about
14 seconds**."（跨页句，文 p.76–77；PDF p.81–82）。

**共模电压的源头治理（消 CM 的另一半）**：恒流放大器三拓扑比较里，配置二被否的一条理由是
"One inconspicuous drawback is that the common mode voltage seen by the pre-amplifier on pick-up side equals ▯,
which increases overall common mode error."（文 p.40；PDF p.45）；选中配置三的理由之二：
"**Common mode error is reduced to minimum** compared with configuration two. The source of common voltage of
this configuration comes from the finite resistance of cables only. Common mode voltage seen by pre-amplifier
on pick-up side is minimized."（文 p.41；PDF p.46）——先把共模电压本身压到最低，再用反转相消治残余。

### ③ AAF / 前端滤波怎么做

**结构（§2.2.7，文 p.53–60；PDF p.58–65）**：拾取链 = 前置差分缓冲（gain 21，LME49990×2）→ 四级放大共 66.5 dB、
3 dB 带宽 195 kHz（文 p.53）→ **三路滤波器组 + 模拟 4:1 MUX**，按测量频段选路：

> "Item No.18 in Table 2.1 is a filter bank composed of three unity gain low-pass filters. ... The low-pass filter
> bank is followed by an analog 4:1 multiplexer which selects appropriate filter depending on measurement frequency."（文 p.54）

**Table 2.4（文 p.54）原文**：

| 滤波器 | 频段 | 3 dB 带宽 | 构成 |
| --- | --- | --- | --- |
| LP_1 | DC–100 Hz | 159 Hz | "Third order passive RC filter" |
| LP_2 | 100 Hz–10 kHz | 15.0 kHz | "Fourth order active RC filter with Bessel response" |
| LP_3 | 10 kHz–100 kHz | 219 kHz | "Fourth order active RC filter with Bessel response" |

**所以不是"单端一阶"**：最低的是三阶无源 RC，其余是四阶有源 Bessel。明确当 AAF 用：
"fourth order low pass filter LP_2 in Table 2.3 is used as **anti-aliasing filter**. LP_2 has a 3 dB bandwidth of
15 kHz, thus its equivalent noise bandwidth is 15.375 kHz."（文 p.68；PDF p.73）

**失配分析：无**。全部关注点是**电容介质**而非差分匹配：

> "MLCC's dc voltage dependence makes it not usable for precision filtering application. Also note that MLCC is
> piezoelectric, thus mechanical stress exerted on the circuit board changes the response of this MLCC filter as well."（文 p.59；PDF p.64）

→ 解法："The LP_1 low-pass filter used in APS1006 uses **10 nF PPS film capacitors**"（文 p.60；PDF p.65）。
滤波器设计方法整节外推给教科书 [26]（Williams & Taylor《Electronic Filter Design Handbook》）：
"The design approach of the three filters are not in the scope of this this dissertation"（文 p.58；PDF p.63）。
拓扑上滤波在前置差分缓冲**之后**（前置盒输出"for better noise rejection"，见②），论文未交代滤波器组是差分还是单端实现。

**另有（§2.2.8，文 p.61–62；PDF p.66–67）**：多音模式用 MAX7490 开关电容带通组（8 通道，时钟:中心频率 = 100:1）。
它自带两类失真——时钟馈通与混叠（文 p.79–81）；对 SC 滤波器加前置 AAF 被明确否掉，因为频带太宽：
"For 1 Hz center frequency, the filter clock frequency is 100 Hz and the internal sampling frequency is 200 Hz,
which is also a frequency of interest in APCD measurement. **The proposed anti-aliasing filter for 1 Hz will
attenuate other useful frequencies.**"（文 p.82；PDF p.87）最终多音方案整体弃用（§3.2.2 结论）。

**Ch5 的滤波器表征（文 p.135–136）**：为瞬态对比，把 LPF 传函用 MFLI 测出并回归成标量传递函数（式 5-5）
参与数值反演——仍是**单变量传函表征，无差分失配**。

### ④ 全文有无"无源 RC 差分网络失配 → 共模消去条件"（P1 反例检索）

**没有。阴性检索结论**：全文（含参考文献标题）检索 `mismatch / balance / imbalance / bridge / Wheatstone /
tracking / matched` 均**无命中**（"match" 仅出现于"两组数据吻合"义，文 p.131）。没有任何一处推导或讨论
无源 RC（或任何）差分网络的元件失配 → 共模到差模转换 / 共模消去成立条件。

**这是"绕开"而非"反例"**：该设计从不指望模拟 CM 消去的匹配条件成立，其共模对策是三件套——
(a) 源头压低共模电压（恒流 config 3，文 p.41）；(b) DPDT 反相两次测量软件相消（文 p.12）；
(c) 电缆前置差分缓冲（文 p.20/65）。三者都没有做失配 → 残余 CM 的误差传播分析。
对 P1 的价值：**这是"不满足/不依赖 P1 条件时的工程替代路线"的实证样本**——机械+软件相消可以完全回避匹配条件，
但代价是测量时间 ×2、且要求两次测量间系统平稳（这恰是我们冲击测量硬约束"测量窗口内不切换"所禁止的）。
可进 Discussion 当对照：P1 条件之所以要在我们方案里显式成立，正是因为我们的场景买不起反转法的时空代价。

### ⑤ 与双通道比值测量可类比的结构

1. **双通道同时采集消激励波动**：驱动侧测电流参考（采样电阻差分电压）、拾取侧测信号，"these two tasks are
   handled simultaneously"（文 p.19）；两分区"share the same clock source"（文 p.19）——对应我们
   V_sample / V_Rsense 双通道同步实测、比值消激励幅度（ADS131A02 同源时钟）。
2. **归一化输出 = 复相量比值**：最终量为拾取/参考两相量之比（Table 3.2/3.3 直接列 "Ratio between pick-up and
   reference"，文 p.76/89）；校准数据本身也是**同一比值在标定配置下的取值**："the ratio between pick-up voltage
   and reference voltage in this configuration is the calibration data"（文 p.94；PDF p.99），修正式 3-6 把原始比值
   乘/除校准量还原真值——与我们"Rsense 在 k 校准中约掉、绝对精度锚 R_ref"同构。
3. **误差预算锚定精密电阻 + 按频段选型**（§3.3.2，文 p.95–102）：Table 3.6——DC–1 kHz 电流采样用电阻用
   bulk metal foil、1 kHz–100 kHz 用精密薄膜、100 kHz–10 MHz 用高频精密薄膜；寄生电感误差有量化：
   "the internal inductance is approximately 5 nH, which gives rise to **3 % error for a 100 mΩ current sampling
   resistor at 100 kHz**"，而 1 Ω 采样电阻在 100 kHz 仅 "0.047% error"（文 p.99–100）。对应我们 Rsense 150 kΩ
   0.1% + R_ref 100 kΩ 0.01% 的误差预算论证。
4. **Ch6 阻抗分析仪 = 又一个 V/I 双相量比值机**（文 p.148–149；PDF p.153–154）：U42/U43 缓冲 DUT 电压、U45
   减法器输出 DUT 电压；U41+R20 转阻测电流；"Lock-in amplifier measures the voltage and current complex phasor
   **in a time division multiplexing fashion**. The DUT impedance can be calculated using those two phasor and R20."（式 6-1）
   "**R20 behaves as a reference resistor in the system**, thus R20 must have low temperature coefficient and very
   high precision rating."（文 p.149）——比值锚定参考电阻，与我们如出一辙；但它两路是**时分复用**（单锁相输入），
   我们是真同步双通道，这是它比我们弱的一环，也是它需要"repeatability 256 次"来补的。
   实测（Table 6.1，文 p.153）：锁相式 100.015 Ω / STD 2.61 mΩ，胜 Agilent 4294A 最佳档
   （BW=5：100.036 Ω / 4.77 mΩ）。
5. **前置放大越靠前越好**：把 67 dB 增益和极性切换放进探针侧前置盒（文 p.20），弱信号不走长电缆——
   对我们高阻节点（源阻抗最高 150 kΩ）保护与就近缓冲是同类教训。
6. **滤波/增益切换产生校准曲线不连续**："two factors contribute to the discontinuity of the calibration data:
   transconductance amplifier change and pick-up signal filter change"（文 p.103；PDF p.108）——
   对应我们量程/滤波档切换处的分段校准问题。

## 关键数值（原文）

- 共模电压可达 **500 mV**，差模拾取 **几 µV**；SR830 CMRR **100 dB** 时 CMR 误差与信号同量级；
  仪放 **120 dB** 仍"not enough to give a CMR error free measurement result"（文 p.12–13）
- 前置盒：**gain 67 dB**（四级总增益 66.5 dB），3 dB 带宽 **195 kHz**；一级差分缓冲 gain **21**；
  LME49990 **0.88 nV/√Hz**、1/f 拐角 **43 Hz**；实测输入折算噪声 **2.036 nV/√Hz**（计算值 2.034）（文 p.53、65–67）
- AAF 组：LP_1 三阶无源 RC / **159 Hz**；LP_2 四阶有源 Bessel / **15.0 kHz**；LP_3 四阶有源 Bessel / **219 kHz**；
  LP_1 用 **10 nF PPS** 薄膜电容（弃 MLCC：直流偏压 + 压电效应）（文 p.54、60）
- ADC：LTC2328-16，16 bit、**1.5 LSB INL**、**93.5 dB SNR**、真双极输入（文 p.63）
- 重复性（128 次，实部 CV）：10 Hz **0.058%**（SNR 64.7 dB）～ 10 kHz 0.030% ～ 100 kHz **0.629%**（SNR 44.0 dB）（Table 4.4，文 p.109）
- 速度：1 Hz–100 kHz、41 点扫频 **14.5 s**；反相消 CM 使 1 Hz 点从 7 s 变 **14 s**（文 p.76–77、107）
- 一周期直接计算 vs FFT（Table 3.4）：幅度 CV **0.0845% vs 0.948%**，相位 RMS 0.0517° vs 0.531°，采集 10 ms vs 1000 ms（文 p.92）
- 校准电阻寄生电感：bulk metal foil ~**5 nH** → 100 mΩ @100 kHz **3% 误差**；1 Ω @100 kHz 0.047%；Vishay FC 系列 **0.0267 nH**（文 p.99–101）
- Ch6 阻抗分析仪：100 Ω 标准件 256 次——锁相式 100.015 Ω / **2.61 mΩ**；4294A 最佳 100.036 Ω / 4.77 mΩ；工作频率上限 **500 kHz**（假设运放理想）（文 p.149、153）

## 对 P1/P2/P3 的对照

- **P1（失配消去条件）**：全文零命中（见④）——本篇是 **P1 非出现 + 替代路线样本**：不依赖匹配条件，靠
  极性反转两次测量软件相消。其代价（低频时间 ×2、需两测间平稳）反证了 P1 条件在"单次窗口内不可切换"
  的场景（我们冲击测量）里必须靠电路自身成立。可引文 p.12 那句 120 dB 语录作 Intro 动机。
- **P2（Kelvin 地板/结构类）**：ACPD 本身就是四点 Kelvin 结构（外两针注流、内两针测压，文 p.1），
  与我们双电极两端被测的差异可对照；其 CM 源"connectors 接触电阻 + 电缆电阻"是串在共模路径上的实体电阻，
  对应 P2 框架里"结构类不同带来的共模载荷"。
- **P3（AAF 衰减上界）**：其 AAF 是**按频段切换的三档滤波器组**（159 Hz/15 kHz/219 kHz），且明确因频带过宽
  否掉 SC 滤波器前置 AAF（文 p.82）；无失配分析、无衰减上界推导。对 P3 无正面素材，但"滤波档切换使校准
  曲线不连续"（文 p.103）可作分段校准的工程注脚。
- **引文价值**：文 p.12（120 dB 不够 + 500 mV/几 µV + DPDT 两次测量）是一句话能同时支撑"CM 误差主矛盾"和
  "软件相消路线"的最佳引文；文 p.41（共模电压源头治理）配 Fig 2.27；Table 2.4（AAF 三档）与
  Table 3.6（电阻选型/寄生电感误差）都是可直接对照引用的表。

## 没读到的

- 两次测量相消的**公式与残余误差**（继电器接触重复性、两测间漂移）——全文没有，只有"insertion resistance
  is minimal, it will not introduce measureable noise"一句定性（文 p.65）。
- 前置放大/AAF 的**完整电路参数与差分-单端转换细节**（Fig 2.50/2.51 是原理图截图，正文只给增益与噪声折算；
  滤波器组的差分/单端实现未写明）。
- 滤波器设计方法（外推 [26] Williams & Taylor《Electronic Filter Design Handbook》4th ed.）；
  SC 滤波器设计（外推 [30] MAX7490 数据手册）；寄生电感表征与并入校准（外推 [47] Agilent 2-port 应用笔记）。
- 内嵌公式符号在 PDF 里未渲染（提取为空白）：式 3-4/3-5/3-6 的具体符号定义、config 二共模电压表达式
  （"equals ▯"）等只能靠上下文推断，本笔记一律留 ▯ 不猜。
