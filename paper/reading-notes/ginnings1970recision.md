# 精读笔记 · Ginnings 1970《Precision Measurement and Calibration: Selected NBS Papers on Heat》（NBS SP 300 Vol. 6）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> 页码口径：**卷印刷页（PDF 物理页）**，印刷页以各页页脚双页码（卷页-原刊页）核实；PDF 页 ≈ 印刷页 + 16~17（中段有漂移，逐页以页脚为准）。

## 出处
- NBS Special Publication 300, Vol. 6, "Selected NBS Papers on **Heat**", Defoe C. Ginnings, Editor, issued 1970。DOI: 10.6028/nbs.sp.300v6。
- 扉页（PDF p.5）："Precision Measurement and Calibration / Selected NBS Papers on / Heat / Defoe C. Ginnings, Editor … NBS Special Publication 300 — Volume 6"。
- PDF 共 401 页；正文为量热学论文原样重印（本卷主体：§1 量热原理与设计、§3 低温 PVT、§4 高温滴定量热、§5 燃烧热、§6 热导/电阻率）。
- Preface（PDF p.8）同列 SP300 十二卷，"Electricity—Low Frequency, F. L. Hermach and R. F. Dziuba" 为独立卷（本库未收）——**本卷不是电学卷**，电气内容仅是量热计的电气测量链（电位计、标准电阻、分压箱、检流计、屏蔽）。
- OCR 质量中等：Ω→"fl/Q"、µ→"^/ti/^a"、下标/公式受损常见；以下引用逐字照录并标 [OCR损]。

## 核心命题（原文）
1. **guard/shield/jacket 是同一「围护」角色的同义词（术语学锚点句，P2 谱系）**（p.5 / PDF p.21，§1.1 Introduction）：
   > "As pointed out earlier, a large part of the effort in accurate calorimetry is usually devoted to either minimizing and/or measuring the heat transfer between the calorimeter and its surroundings. The terminology for the immediate surroundings varies considerably among different laboratories. Among the various names for the surroundings are shield, jacket, guard, envel- ope, thermostat, etc."
   （NBS 明示 guard/shield/jacket/thermostat 都是"围护 surroundings"的同义角色；职能 = 最小化**和/或测量**与环境的交换。下句原文："The term shield will be used in this introduction to describe the calorimeter surroundings."）
2. **滤波器前置防饱和 vs 低阻抗 vs 工频拾取的三难（P3 的 1960s 同构权衡句）**（p.28 / PDF p.44，§1.2 Principles of Calorimetric Design）：
   > "In most sensitive electronic amplifiers (d.c), the effects of 60 c/s pickup are attenuated by an electrical filter in the early stages of the amplifier. **To be completely free from first stage amplifier 'saturation', the filter should precede the amplifier. However, this location of the filter requires it to have a low impedance when used with a low impedance signal source in order to avoid increased 60 c/s pickup in the signal circuit.** Most commercial electronic amplifiers do not have this low-imp [OCR损，跨栏=impedance input filter…]"
   （前句铺垫："When a typical galvanometer is used with a low-impedance signal source, not only is the 'pickup' relatively small, but the inertia of the galvanometer serves as a high frequency filter which attenuates 60 c/s pickup."——检流计惯性即天然低通。）
3. **检流计有限灵敏度 = 平衡误差信号有限（失衡→误差的显式表达）**（p.21 / PDF p.37，§1.2 图 1 讨论）：
   > "At ideal balance, the current, /, is zero and E 2 — Ei [OCR损，=E₂=E₁]. The actual balance occurs at some finite current, Ii, representing the smallest current which the galvanometer can detect. In this actual case, this error signal is (E 2 — E\) = h {R\ + ^2) [OCR损，=(E₂−E₁)=I₁(R₁+R₂)]. If R 2 ^> Ri [OCR损，=R₂≫R₁], then an increase in Ri, the thermocouple resistance, does not …"
   （理想平衡 vs 实际平衡的差 = 可检最小电流×回路电阻；R₂≫R₁ 时误差信号对 R₁ 不敏感——**源阻抗选择的失衡钝化逻辑**。）
4. **「比率对比率」的日常核查（结构性比率的自洽闭环）**（p.78 / PDF p.94，§1.3 Calorimetry of Saturated Fluids）：
   > "A check was made at least twice a day for any change in the potentiometer factor. This check consisted essentially of comparing a given potentiometer reading (which is effectively a ratio) with the ratio of two standard resistors."
   （电位计读数本质是比率，用两个标准电阻之比核查——比率链内部互证，不依赖绝对单位。）
5. **volt-box 比率链的精密度/不准度分层**（p.277 / PDF p.293，§5.4 Churney & Armstrong 弹式量热电气标定）：
   > "In calculating the volt-box ratio, use is made of the fact that, because of the close matching of the 10,000-fl [OCR损=Ω] resistors, the ratio of series to parallel resistance of the 10,000-fl resistor set is equal to 100 1 [OCR损，=100:1] within 1 ppm"
   > "The imprecision of the volt-box ratio in 9 determina- tions made during the course of the electrical calibra- tions was 0.6 ppm (standard deviation of a single determination). This is approximately the a priori estimated precision of a measurement. The inaccuracy was estimated to be between 2 and 10 ppm."
   （同串电阻测串/并比 → 比率自校准 1 ppm；不精密 0.6 ppm vs 不准度 2–10 ppm 分层给出。）
6. **铁屏蔽箱 + 铁导管 + 重铜接地 + 浮地输入的成套抗扰实践（P2 谱系）**（p.167 / PDF p.183，§3.2 Goodwin 低温 PVT 装置）：
   > "the continuous copper wires from the pipet in the cryostat are joined by a special solder [45] to un- turned, copper cable wires near the cryostat on copper lugs in an iron-shielded, heavy aluminum box. The cryostat wires and shielded cables run in iron con- duits. The cryostat and all electrical instruments are interconnected and grounded to the earth with heavy copper conductors."
   > "Microvolt galvanometer ampli- fiers with floating input circuits are coupled to 50-^a [OCR损=µA] panel galvanometers in suitable damping and range- changing circuits."
7. **换向甄别寄生电势：与电流无关者判为寄生（p.167–168 / PDF p.183–184，同篇）**：
   > "When the cryostat is cooled with liquid hydrogen, a 0.35-^v [OCR损=µV] spurious potential, which is nearly independent of pipet tem- peratures up to 40 °K and increases with higher temperatures, appears across the thermometer po- [OCR损，跨栏]"
   > "Potential measurements with reversed thermometer currents show the effect to be independent of current."
   （正反向电流测量 → 与测量电流无关的残差 = 寄生热电势，**换向不消去但可识别**。）
8. **guard 接地、加热器隔离（电气化 guard 用法）**（p.340 / PDF p.356，§6.4 Flynn & O'Hagan）：
   > "The guard was electrically grounded but the heaters were isolated."
9. **共有误差在差分读数中相消（消去句式，对象为热电势）**（p.343 / PDF p.359，§6.4）：
   > "…due to possible inhomogeneities in the thermocouple leads or to stray thermal emfs w ould [OCR损跨栏=would], for the most part, cancel since they were common to q„ and q'n [OCR损，=qn and q'n] (i.e., corresponding to Q and Q')."
10. **加热丝电阻稳定性目标（功率测定 0.001%）**（p.110 / PDF p.126，§1.7 Furukawa, Reilly & Saba 摘要）：
    > "The goal is to achieve regularly an accuracy of 0.001% in the determination of power."
    同页："the resistance of Evanohm and Karma wires changed by only about 0.9%. When ap- plied to heat capacity measurements with the usual heat- ing rate of one degree per minute, these newer heaters will change in resistance on the average only about 0.002% to 0.003% per min."（对照组：6%/10% for constantan and manganin。）

## 关键数值（原文）
- volt-box：10,000 Ω 电阻组串/并比 = 100:1 within **1 ppm**；9 次测定不精密 **0.6 ppm**（单次标准差）；不准度 **2–10 ppm**（p.277 / PDF p.293）。
- 电位计辨率："Potential measurements were made to 0.03 tiV [OCR损=µV] with a six-dial double potentiometer"（p.277 / PDF p.293）。
- 热噪声地板："With circuits having resistance of about 100 Q [OCR损=Ω] and with detectors having time constants about one second, the thermal noise equivalent (root mean square voltage) in the signal source at room temperature is about 0-001 [xV [OCR损=0.001 µV]"（p.28 / PDF p.44）。
- 寄生电势甄别：0.35 µV（液氢冷凝段，与 pipet 温度近乎无关 ≤40 K）；反向电流测法判"与电流无关"（p.167–168 / PDF p.183–184）。
- 加热丝：Constantan/Manganin 10–380 K 全程阻值变 **6%/10%**；Evanohm/Karma 仅 **~0.9%**；1 °C/min 升温时 **0.002%–0.003% per min**（p.110 / PDF p.126）。
- 试样加热器恒压 **±0.01%**（p.340 / PDF p.356）。

## 对 P1/P2/P3 的对照
- **P1 消去条件**：本卷全文关键词审计（pdftotext 全文）：`common mode/common-mode/CMRR/stray capacitance/capacitance mismatch/ground loop/guard electrode/current comparator/Kelvin-Varley/Wagner` 全部 **0 命中**；`mismatch` 仅 1 处且为**热学**语义（p.17 / PDF p.113："a temperature mismatch and an exchange of heat between the calorimeter and the shield"）；`unbalance` 2 处均为检流计电桥失衡（p.365-366 / PDF p.381-382）。**不存在 RC 差分网络失配→共模转差模内容**。可引的消去范式有二：命题 3（平衡误差信号=可检最小电流×回路电阻，R₂≫R₁ 钝化）与命题 9（common-to-both → cancels，但对象是热电势）；命题 5 的「同一电阻组串/并自比」是最接近"结构性比率自校准"的原型。
- **P2 结构地板**：命题 1（guard/shield/jacket 同义术语句）+ 命题 6（铁屏蔽箱/铁导管/重铜共地/浮地输入）+ 命题 8（guard 电气接地）是 P2「守卫屏蔽谱系」可直接引用的 NBS 原句；量热 guard 与电学 guard 的角色同构（隔离+测量泄漏），可作 Discussion 的跨域类比。
- **P3 可达边界**：命题 2 的"滤波器前置防饱和 vs 低阻抗 vs 60 c/s 拾取"三难是 AAF 衰减权衡的历史同构（对象是直流放大器工频，不是采样抗混叠）；命题 3 的热噪声地板（0.001 µV @100 Ω/1 s）可作噪声下限引证。
- **killRisk 判断**：无威胁。全卷无 P1 反例、无 P3 上界断言；对 P2 有正面谱系价值。

## 没读到的
- 真正的电学卷 SP300 Vol 3《Electricity—Low Frequency》不在本库（Preface 12 卷目录为证，PDF p.8）。
- 本卷仅精读上列页段；§2 冰点纯度测定、§4 高温滴定量热、§5 燃烧热各篇仅扫关键词，未逐字读。
- 命题 3 的公式（E₂−E₁=I₁(R₁+R₂)）OCR 下标受损，语义按上下文复原，引用公式本身前宜核纸本。
- 命题 9 的 "q„ and q'n"（=q_n 与 q'_n）OCR 损，符号复原待核。
- §1.2 原理篇的量热设计方程（热漏系数等）多为公式排版，OCR 断行严重，未逐式核对。
