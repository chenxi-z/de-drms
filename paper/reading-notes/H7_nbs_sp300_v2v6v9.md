# 精读笔记 · NBS SP300 三卷合体（Swindells 1968 / Ginnings 1970 / Nimeroff 1972）

> 格式标准（全组沿用）：出处 → 核心命题（原文引用）→ 关键数值（原文）→ 对 P1/P2/P3 的对照 → 没读到的。
> 读法：pdftotext 提取全文与目录（三卷均为 Internet Archive 扫描件 + OCR 文字层），按主题定位篇章后精读，
> 其余浏览；引用一律原文加页码（卷内印刷页 + PDF 页双标注，便于回查）。
> **OCR 噪声如实标注**：三卷 OCR 质量中等，个别处有断词/错字（如 Ω 被识为 "fl/n"、µ 识为 "^/pt"），
> 引用时以 [OCR] 标注存疑处，不代为改写。

## ⚠ 卷册身份勘误（先读这条）

任务描述中的卷册主题与实物**不符**，精读前必须更正（依据各卷扉页与 Abstract，逐字核实）：

| 文件 | 实际内容（扉页/Abstract 原文） | 页数（PDF/印刷） | 任务描述所称 |
| --- | --- | --- | --- |
| `H7_swindells1968_precisio.pdf` | SP300 **Vol 2, "Selected NBS Papers on Temperature"**, J. F. Swindells 编, 1968-08 | 536 / 520 | "卷2 电阻/电容/电感" ❌ |
| `H7_ginnings1970_precisio.pdf` | SP300 **Vol 6, "Selected NBS Papers on Heat"**, D. C. Ginnings 编, 1970-02 | 400 / 387 | "卷6 电学与电子学" ❌ |
| `H7_nimeroff1972_precisio.pdf` | SP300 **Vol 9, "Selected NBS Papers on Colorimetry"**, I. Nimeroff 编, 1972-06 | 468 / 460 | "卷9 相关专题"（实为色度学） |

真正的电学卷是 **Vol 3 "Electricity—Low Frequency"（Hermach & Dziuba 编）**与 **Vol 4 "Electricity—Radio Frequency"（Estin 编）**——
见 Vol9 卷首系列目录（PDF p.2："SP300, Vol. 3, Electricity—Low Frequency… SP300, Vol. 4, Electricity—Radio Frequency…"），
**本库不收**。故本笔记只能给出三卷中与电阻比较/电桥/守卫屏蔽**实际存在**的内容（温度、量热两卷有真金；色度卷几乎为空），
以及对四个重点问题的如实（含否定）回答。系列全目另见 Vol2 卷首 Preface（PDF p.8，列 12 卷规划）。

## 精读篇章定位表（引文出处对照）

**Vol 2（温度）**——"Resistance Thermometry" 章（印刷 pp.121–212）为主：
| 篇 | 作者 | 印刷页 | PDF 页 |
| --- | --- | --- | --- |
| Precision Resistance Thermometry and Fixed Points | H. F. Stimson（转载自 Temperature 1955, Vol.II, pp.141–168） | 121–148 | 133–160 |
| Notes to Supplement Resistance Thermometer Reports | NBS（1963-08-01 报告） | 149–158 | 161–170 |
| A Study of Stability of High Temperature Platinum Resistance Thermometers | J. P. Evans, G. W. Burns | 163–168 | 175–180 |
| Calibration of Germanium Resistors at Low Temperatures (2–20°K) | （低温组，作者名 OCR 不清） | 178–187 | 190–199 |
| Reproducibility of Germanium Resistance Thermometers at 4.2°K | [OCR 首页作者名不清] | 188–197 | 200–209 |
| Cerous Magnesium Nitrate: A Magnetic Temperature Scale 0.002–2°K（Hartshorn 电桥） | — | 99–120 | 111–132 |
| Establishment of a Temperature Scale… between 14° and 83°K | — | 33–55 | 45–67 |
| The NBS Photoelectric Pyrometer…（动态响应） | — | 391–403 | 403–415 |

**Vol 6（热学）**——量热电气替代/电气测量链为主：
| 篇 | 作者 | 印刷页 | PDF 页 |
| --- | --- | --- | --- |
| §1.1 Introduction, Calorimetry of Non-reacting Systems | D. C. Ginnings | 1–13 | 18–30 |
| §1.2 Principles of Calorimetric Design | Ginnings & West | 15–61 | 31–77 |
| §1.3 Calorimetry of Saturated Fluids | Ginnings & Stimson | 62–87 | 78–103 |
| §1.7 Electrical Resistances of Wires of Low TC… (10°–380°K) | Furukawa, Reilly, Saba | 110 | 126 |
| §2.1 Cryoscopic Determinations of Purity of Benzene… | Glasgow 等 | 127–152 | 143–168 |
| §3.2 Apparatus… PVT of Hydrogen to 350 atm | R. D. Goodwin | 162–174 | 178–190 |
| §4.1 High Temperature Drop Calorimetry | Douglas & King | 181–219 | 197–235 |
| §4.3 Dynamic Heat Capacity…(Abstract) | Cezairliyan & Beckett | 226 | 239–242 |
| §5.1 Precise Measurement of Heat of Combustion… | R. S. Jessup | 237–261 | 253–277 |
| §5.4 Studies in Bomb Calorimetry… in Terms of Electrical Units | Churney & Armstrong | 275–287 | 291–303 |
| §5.5 Constant Pressure Flame Calorimetry with Fluorine II | King & Armstrong | 288–308 | 304–323 |
| §6.4 Thermal Conductivity and Electrical Resistivity of Platinum 100–900 °C | Flynn & O'Hagan | 334–357 | 350–373 |

**Vol 9（色度学）**——仅核对与滤光片设计/术语相关篇：§4.4 A Colorimeter for Pyrotechnic Smokes（印刷 307–311 / PDF 325–329）、
§4.5 Development of Filters for a Thermoelectric Colorimeter（印刷 312–318 / PDF 330–336）、§1.1 玻璃滤光片检定（印刷 1–19）、
§5.3 Degree of Metamerism（印刷 337+）；其余章节（色视觉、色空间、光泽）与本课题无关，浏览即止。

## ① 匹配条件的表述（比率匹配 / a/b=A/B）

**结论：三卷没有任何一处写出 "a/b = A/B 式" 的比率匹配定理**；但 Vol 2 与 Vol 6 有三条**功能等价**的比率/失衡消去条件，逐字如下。

1. **换向消引线电阻的成立条件（最接近 P1 的"消去条件"句式）**——Vol2《Notes to Supplement Resistance Thermometer Reports》印刷 p.152（PDF p.164）：
   "The function of the commutator is to interchange the thermometer leads in such a way that the average of the resistances measured with the commutator in the N (normal) position and in the R (reverse) position is the resistance of the resistor of the thermometer. **The resistance of the leads is completely eliminated by this technique only if the difference in the resistance of the two leads appearing in the arms of the bridge is the same when measurements are made in the N as when measurements are made in the R position.** By making a series of four measurements, at equal time intervals, in the order N R R N, any change of the difference of the lead resistance is computable and the average value of the four measurements is independent of any linear drift in this difference."（"computable" 系 OCR 原样，原文或为 compensated，未核对原件）
   ——这是显式的**等值条件**（两引线电阻差在 N/R 两态下不变 → 完全消去）+ **N-R-R-N 等间隔四读消线性漂移**（一阶漂移在平均中抵消）。

2. **比率臂失衡经同步反向被压制 10³ 倍**——Vol2 Stimson "Bridge Developments" 印刷 pp.131–132（PDF pp.143–144），
   记 Mueller 退休后设计的电桥（Hoge 建议的换向开关改进）：
   "One new feature in the commutator switch is the addition of an extra pair of mercury-contact links which serve to reverse the ratio coils simultaneously with the thermometer leads. This feature was suggested by Hoge… **This feature automatically makes the combined error of the normal and reverse readings only one in a million, for example, when the ratio arms are unequal by as much as a part in a thousand, and thus practically eliminates an error from lack of balance in the ratio-arms.** It does not eliminate any systematic error in the contact resistance at the end of the ratio arms on the decades, however, because the mercury reversing switch has to be in the arms."
   ——注意它**不**是"匹配到零"，而是"失配 10⁻³ 时正反合计残差 10⁻⁶"的**对称反向消差**；残余项（十进盘端接触电阻）不在消去范围。

3. **比率测量使单位误差共模约去**——Vol2 同篇印刷 p.153（PDF p.165）：
   "The accuracy of temperatures determine[d] from values of Rt/R0 obviously is not limited by the uncertainty of the resistance units if the values of Rt and R0 are determined in the same units… **Since only ratios of resistances are required to determine temperature, the units may be absolute ohms, international ohms, or any arbitrary unit; but the calibrated bridge (or potentiometer) must be self-consistent.**"
   ——"同单位/同仪器测分子分母 → 比值中约掉"就是本谱系里的 a/b=A/B 消去逻辑；Stimson 印刷 p.121（PDF p.133）开宗明义：
   "Precision resistance thermometry with a standard resistance thermometer, therefore, depends upon the precision and accuracy with which **these ratios** can be determined."

4. **比率对比率的核对（Vol6）**——§1.3 印刷 p.78（PDF p.94），每日核查电位计因子：
   "A check was made at least twice a day for any change in the potentiometer factor. **This check consisted essentially of comparing a given potentiometer reading (which is effectively a ratio) with the ratio of two standard resistors.**"
   另有 §5.4 印刷 p.277（PDF p.293）的分压箱（volt-box）比率链："The heater current is determined by measuring the voltage across a Reichsanstalt-type, 0.01-Ω standard resistor. The potential drop across the heater is determined [by a] 1000 nominal voltage divider or volt-box… The imprecision of the volt-box ratio in 9 determinations… was **0.6 ppm** (standard deviation of a single determination)… The inaccuracy was estimated to be between **2 and 10 ppm**."（同篇另有 "volt-box ratio of 1:1000 … within 1 ppm"，OCR 断行处字迹受损 [OCR]）

5. 辅助：比率臂调平是校准前提——Vol2 印刷 p.156（PDF p.168）："**Before beginning the bridge calibration the ratio arm should be adjusted to equality.**"
   以及比率臂阻值放大稀释接触电阻——Vol2 印刷 p.131（PDF p.143）："He has made the resistances of the ratio arms 3000 ohms so that the uncertainty of contact resistance, 0.0001 ohm, produces an uncertainty of only one part in 30,000,000. With 30 ohms… in each of the other arms… these two ratio-arm contacts should produce an uncertainty of resistance measurement of 1.41 microhms."

   另有两条"平衡/失配"相关散见句：**零示器有限灵敏度的平衡误差**——Vol6 §1.2 印刷 p.21（PDF p.37）：
   "**At ideal balance, the current, I, is zero and E2 = E1. The actual balance occurs at some finite current, I1, representing the smallest current which the galvanometer can detect. In this actual case, this error signal is (E2 − E1) = I1(R1 + R2).** If R2 >> R1, then an increase in R1, the thermocouple resistance, does not [change the error signal]…"（[OCR] 式中下标受损，语义清楚）；
   **共有误差在差分读数中相消**——Vol6 §6.4 印刷 p.343（PDF p.359）："Errors in the temperature drop across the neck due to possible inhomogeneities in the thermocouple leads or to stray thermal emfs **would, for the most part, cancel since they were common to qn and q'n** (i.e., corresponding to Q and Q')."——"common to both readings → cancels" 的消去句式，但对象是热电势/引线不均，非 RC 网络。

**电桥名录（三卷实见）**：Wheatstone–Mueller（带换向器，Vol2 印刷 p.152："The Wheatstone bridge and commutator of Mueller's design are commonly used in this country"）、
Smith bridge（NPL 改进型，Vol2 印刷 p.131 一句带过）、Kelvin 双电桥（Vol2 印刷 p.152 提名 "a Kelvin-type double bridge"，无电路细节）、
G-2 Mueller bridge + 光电检流计（Vol6 §5.4/§5.5，印刷 pp.277、292）、Wenner/White/Wolff-Diesselhorst 电位计链（Vol6 各篇）、
**Hartshorn 互感电桥**（Vol2 CMN 磁温度计，印刷 p.101，PDF p.113：感应线圈 "plus symmetrically disposed bucking coils… bridge turns, n… The minimum detectable bridge unbalance was 0.002 turn"——变压器/互感比例臂一类，仅此一处）。
**Kelvin-Varley 分压器、电流比较仪（current comparator）、Wagner 接地**：三卷均无（"wagner" 仅 Vol9 PDF p.115 命中，是人名 H. G. Wagner，金鱼视网膜论文，无关）。

## ② 守卫/屏蔽技术的原理句（P2 计量谱系）

1. **术语学句（P2 谱系可直接引用）**——Vol6 §1.1 印刷 p.4（PDF p.21）：
   "The terminology for the immediate surroundings varies considerably among different laboratories. **Among the various names for the surroundings are shield, jacket, guard, envelope, thermostat, etc.** … The term shield will be used in this introduction to describe the calorimeter surroundings."
   ——NBS 明示 guard/shield/jacket 是**同一角色**（量热计的"围护"），其职能是最小化/测量与环境的热交换（同页："a large part of the effort in accurate calorimetry [is] usually devoted to either minimizing and/or measuring the heat transfer between the calorimeter and its surroundings"）。

2. **电屏蔽+接地+浮地输入的成套实践**——Vol6 §3.2（Goodwin 低温 PVT 装置）印刷 pp.166–167（PDF p.183）：
   "To minimize spurious effects in the thermometer and thermocouple potential circuits, the continuous copper wires from the pipet in the cryostat are joined by a special solder to unturned, copper cable wires near the cryostat **on copper lugs in an iron-shielded, heavy aluminum box. The cryostat wires and shielded cables run in iron conduits. The cryostat and all electrical instruments are interconnected and grounded to the earth with heavy copper conductors.**"
   配套"微伏放大器浮地输入"："Microvolt galvanometer amplifiers with **floating input circuits** are coupled to 50-μa panel galvanometers…"，以及**换向法甄别寄生电势**：
   "…a **0.35-μV spurious potential** … appears across the thermometer potential leads in the absence of thermometer current. **Potential measurements with reversed thermometer currents show the effect to be independent of current.**"（即：与测量电流无关者判为寄生热电势，换向不消失）

3. **双层铜屏笼接地、消 RF 焦耳热**——Vol2《Reproducibility of Germanium Resistance Thermometers at 4.2°K》印刷 p.189（PDF p.201）：
   "**A lead from one of the [copper] sheets is connected to a surrounding screen cage which is at earth potential. The double-wall, copper-screen cage completely encloses the d-c measuring apparatus and eliminates a-c joule heating that is caused by signals which emanate from nearby commercial transmitters** [ref 14]."
   ——守卫的目的被表述为：**外来 RF 在电阻里整流/发热 → 直流测量漂移**；屏蔽比匹配更根本。

4. **等温结对消热电势**——Vol2 Evans & Burns 印刷 p.163（PDF p.175）：
   "The copper to platinum junctions are located side by side in a small piece of four-hole porcelain tubing which is surrounded by a close-fitting copper sleeve. **In this manner the junctions are kept at nearly the same temperature, thereby reducing thermal emf in the thermometer.**"

5. **漏电/绝缘是高阻节点的专门威胁**——Vol2 Stimson 印刷 p.130（PDF p.142）：
   "**At the sulfur point, however, the glass seals become conducting and increase the difficulty and uncertainty of the calibrations at that temperature.** The electrical conduction in the glass insulation of these resistance thermometers has been discussed by H. J. Hoge."
   又 Vol2 锗电阻标定篇印刷 p.184（PDF p.196）：绝缘电阻日常用便携 Wheatstone 电桥量（"Insulation resistances of 10 MΩ — the limit of a portable Wheatstone bridge — are commonly measured."）。

6. **屏蔽/双绞的教科书式一句**——Vol6 §1.2 印刷 p.28（PDF p.44）：
   "…suitable steps should be taken to avoid using a.c. (60 c/s) close to any component leading to the input to the amplifier and to **follow the usual precautions of shielding, twisted leads, etc.**"
   同篇 guard 的电气化用法：§6.4 印刷 p.340（PDF p.356）"**The guard was electrically grounded but the heaters were isolated.**"（热 guard 接地、加热器隔离）。

## ③ P1 反例搜索：无源 RC 差分网络失配 → 共模转差模的消去条件

**预期无 → 确认无。** 三卷全文关键词审计（pdftotext 全文）：`common mode / common-mode` **0 命中**（三卷皆然）、
`CMRR` 0、`stray capacitance` 0、`capacitance mismatch` 0、`differential network` 0、`ground loop` 0、`guard electrode` 0。
`mismatch` 命中全部是**光学/色度语义**（Vol2 印刷 p.370 光学高温计 "a noticeable color mismatch may exist"；Vol9 色度学 metamerism 全篇），无一电气。
`unbalance` 命中全是**电桥不平衡**（如 Vol2 印刷 p.132 Johnson 噪声段 "an unbalance of 1 microhm in the measuring arm of a bridge"）。

因此：**SP300 这三卷不构成 P1（RC 差分失配→共模转差模及其消去条件）的出处，也不能当反例引用**；
最接近的只有 §①-1 那句"引线差在 N/R 两态不变才完全消去"——它是**引线电阻差**的消去条件，不是 RC 网络的共模转换条件。
P1 若需要 NBS 谱系的失配句，只能去 Vol 3《Electricity—Low Frequency》（本库缺）或 Cutkosky 电流比较仪谱系（本库有单行本，另读）。

## ④ AAF/滤波器衰减权衡（P3 历史对照）

**三卷无任何抗混叠/电子滤波器衰减-带宽权衡内容**（`attenuat*` 仅 7 处，全为热屏蔽衰减或光衰减）。可作历史对照的最近材料：

1. **输入滤波器位置-饱和-拾取三难（最接近 P3 的"衰减权衡"句）**——Vol6 §1.2 印刷 p.28（PDF p.44）：
   "When a typical galvanometer is used with a low-impedance signal source, not only is the 'pickup' relatively small, but **the inertia of the galvanometer serves as a high frequency filter which attenuates 60 c/s pickup.** In most sensitive electronic amplifiers (d.c), the effects of 60 c/s pickup are attenuated by an electrical filter in the early stages of the amplifier. **To be completely free from first stage amplifier 'saturation', the filter should precede the amplifier. However, this location of the filter requires it to have a low impedance when used with a low impedance signal source in order to avoid increased 60 c/s pickup in the signal circuit.** Most commercial electronic amplifiers do not have this low-impedance input filter so that they are most susceptible to large 60 c/s pickup than galvanometers having the same time constant."
   同页给热噪声下限："With circuits having resistance of about 100 Ω and with detectors having time constants about one second, the thermal noise equivalent… is about 0.001 μV."——即**滤波衰减 50 Hz 干扰 vs 前置饱和 vs 源阻抗**的三方权衡，语境虽是直流放大器而非 AAF，权衡结构同型。

2. **时间响应 vs 噪声平均**——Vol2《NBS photoelectric pyrometer》印刷 p.393（PDF p.405）：
   "Fig. 4 shows these in comparison to a 0.2 deg C change in radiance temperature… **using various electrical time responses.** … the higher frequency fluctuations or noise can be averaged fairly well by a straight line through the trace. The effect of longer period fluctuations is reduced by averaging 4 to 8 consecutive radiance matches… **A standard deviation of 0.02 deg C, largely independent of the electrical time re[sponse]**…"（[OCR]：该句与图注 "VOLTAGE DIVIDER TIME CONSTANTS NETWORK" 交错断行，尾词拼合；引前建议核纸本）。
   另印刷 p.400（PDF p.412）："The difference would be explained if the **electronic response times (1/6 sec)** were not brief enough to record a spectral line faithfully. Slower scans were limited by the burning time of the arc…"——响应时间 vs 扫描速度的历史权衡。

3. **光学滤光片逼近目标函数的设计权衡（P3 的光学同构物）**——Vol9 §4.5 印刷 p.313（PDF p.331）：
   "**The only parts of a colorimeter over which the designer can exercise much control are the filters used to modify the detector response to obtain the x, y, and z functions of the CIE standard observer.** The x function is bimodal and therefore two filters are used…"
   §4.4 印刷 p.307（PDF p.325）："**The filter design is accomplished by determining the proper combination of colored glasses.** Where the transmittance T0 of a glass of stock thickness d0 is to be changed to a transmittance T1, the following equation must be solved for the new thickness, d1…"（Beer–Lambert + Fresnel 反射修正 k）；
   §4.5 印刷 p.312（PDF p.330）给出"探测器非选择性才值得做滤片逼近"的前提：
   "…because of the variation in spectral response of these detectors from one to the other, **it has not been worthwhile to attempt to achieve the best possible duplication of the CIE tristimulus functions. In the case of a thermoelectric detector, however, the response is so nonselective that the same filter designs can be used with any thermopile.**"
   ——逼近误差（desired/expected/actual 三曲线对比，§4.4 Fig.3）是"滤波器形状匹配误差"的历史形态，但**与衰减上界无关**。

## 关键数值（原文）

- 电桥噪声地板：Vol2 印刷 p.132（PDF p.144）："dV = 1.12 × 10⁻⁹ √(Rτ)… the magnitude of the Johnson noise in a circuit including an instrument having a one-second period would be of the same order of magnitude as **an unbalance of 1 microhm** in the measuring arm of a bridge when one milliampere was flowing in a 25-ohm thermometer." 实测："a standard deviation of a single determination of about **8 microhms**"（1.5/2.5 ma 外推零电流，三点水三相点瓶）——与理论地板的差距 "remains one of the unsolved problems"。
- Mueller 电桥：比率臂 3000 Ω、接触电阻不确定度 0.0001 Ω → **1/3×10⁷**；第七十进盘一步 ≈ 10 µΩ；汞接触 <1 µΩ；量程 0–422 Ω、步进 1 µΩ（Evans & Burns 印刷 p.164）。Johnson 噪声句中 25 Ω 传感器。
- 换向消差：比率臂失配 10⁻³ → 正反合计误差 **10⁻⁶**（Vol2 印刷 pp.131–132）。
- 标准电阻/比率链（Vol6 §5.4 印刷 p.277）：0.01 Ω Reichsanstalt 型标准电阻测电流、volt-box 比率 1:1000、比率不精密 **0.6 ppm**、不准度 **2–10 ppm**、电位计比率恒定 **1 ppm**（11 次核查）；G-2 Mueller 电桥 + 光电检流计：**1 µΩ ≈ 10⁻⁵ °C**（2 mA 桥流，印刷 p.277）。
- 加热丝稳定性（Vol6 §1.7 印刷 p.110）：目标 "an accuracy of **0.001%** in the determination of power"；Constantan/Manganin 在 10–380 K 全程变 **6%/10%**，Evanohm/Karma 仅 **~0.9%**；后者升温率 1 °C/min 时阻值变化 "only about **0.002% to 0.003% per min**"，分钟间内插优于 0.001%。
- PRT 稳定性判据（Vol2 印刷 p.164）："The constancy of the ratio R100/R0 … is taken as an indicator of thermometer stability… **the ratio R100/R0 is independent of purely dimensional changes in the platinum wire**." 附：R0 变化与最大温差估计式（印刷 p.153–154）；三相点内熔化复现性 "within about **0.00008 °C**"（印刷 p.135）。
- 零电流外推（Vol2 印刷 p.127）：双电流外推消自热，"it is necessary to control carefully **the ratio of the currents**"，最优观测数比 n1/n2 ∝ √(功率比)；2 ma 下 ΔR0 = 460/125 µΩ 两例。
- 低温锗电阻标定（Vol2 印刷 pp.184–185）：双库六盘电位计 + 外部换向开关，"the thermal emfs may be detected and their effect on the measurements [is] eliminated"；1,000/10,000 Ω 标准电阻串联定流 1–2 µA（印刷 p.188–189，两支 50 kΩ 分压器并联供电）。
- Flynn & O'Hagan（Vol6 印刷 pp.336、343）：多电流档测阻值外推零电流；R_ice/R_He = 393 作纯度/结构判据；正反向电流测电势消引线 IR 降（印刷 p.339）。

## 对 P1/P2/P3 的对照

- **P1（失配消去条件）**：本组没有 a/b=A/B 定理，也没有 RC 差分网络失配→共模转差模。但 §①-1（N/R 换向消引线差的等值条件 + N-R-R-N 消线性漂移）与 §①-2（比率臂失配 10⁻³→10⁻⁶）提供了 NBS 谱系的两类消去范式：**对称反向平均**与**同链比率约去**。论文若写"计量学传统中失配靠 X 消去"，可引此二者并注明条件（引线差换向不变性；正反读组合）。
- **P2（Kelvin 地板 / 守卫屏蔽谱系）**：§②-3 的"双层接地铜屏笼消 RF 焦耳热"与 §②-2 的"铁屏蔽箱+铁导管+重铜接地+浮地输入"是 P2 谱系中可直接引用的 NBS 原句；§②-1 的 guard/shield/jacket 同义术语句可用来锚定"守卫=围护角色"的计量语义。与 Whitlock 的 Zcm 路线互补：这里是"屏蔽+接地+换向"三件套，同样不靠元件匹配。
- **P3（AAF 衰减权衡）**：无直接内容。§④-1 的"滤波器前置防饱和 vs 低阻要求 vs 50 Hz 拾取"是结构性同型的历史权衡句，可在 Discussion 中作 1960s 年代的"衰减-代价"先例引用，但须注明其对象是直流放大器工频拾取，不是采样抗混叠。
- **引文价值**：Vol2 印刷 p.152 的引线消去条件、pp.131–132 的比率臂换向消差、Vol6 印刷 p.28 的滤波三难、p.21 的 guard/shield 术语句、p.78 的"比率对比率"核查——这五条是三卷中最可引用的原句。

## 没读到的

- **真正的电学卷 Vol 3《Electricity—Low Frequency》（Hermach & Dziuba）与 Vol 4《Electricity—Radio Frequency》不在本库**——Kelvin-Varley 分压器、Wagner 接地、guard 电极、变压器比例臂的系统 treatment 应在 Vol 3，需另找（H7_cutkosky1961/1970、H7_dunfee1963 单行本可能覆盖电流比较仪/阻抗测量谱系，未在本笔记范围内）。
- Vol2 内未逐字精读者：《Interpolation of Platinum Resistance Thermometers, 10°–273.15°K》（印刷 169–177，仅查 Mueller 电桥使用段）、光学/光谱测温各篇（仅取动态响应两页）、两篇 1953–1965 温度测量书目（447–510，仅核对关键词命中）。
- Vol2 印刷 p.131 提及的 NPL 改进 Smith bridge（Barber, Gridley, Hall, J. Sci. Instrum. 32, 213 (1955)）与 Evans "An Improved Resistance Thermometer Bridge"（Temperature 1962 Vol.3）均只引未载；Dauphinee "An isolating potential comparator"（Can. J. Phys. 31, 577 (1953)）同。
- Vol2《Reproducibility of Germanium Resistance Thermometers at 4.2°K》作者名 OCR 首页残损未认出，引用时用篇名。
- 《Notes to Supplement Resistance Thermometer Reports》无期刊出处（NBS 1963-08-01 报告），"computable/compensable" 一词 OCR 存疑，引用前建议核对纸本。
