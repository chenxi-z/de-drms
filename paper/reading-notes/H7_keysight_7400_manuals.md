# 精读笔记 · Keysight《Impedance Measurement Handbook》4th Ed. + QuadTech 7400 Precision LCR Meter 手册

> 格式标准（全组沿用）：出处 → 核心命题（原文引用）→ 关键数值（原文）→ 对 P1/P2/P3 的对照 → 没读到的。
> 读法：pdftotext 全文提取 + 目录定位后精读相关章节全文（符号丢失处按页图逐字核对），引用一律原文加页码。

## 出处与读法

- **[KS]** Agilent *Impedance Measurement Handbook — A guide to measurement technology and techniques*, 4th Ed.（`paper/literature/H7__impedanc.pdf`，140 页）。
  精读：§2.1–2.4（测量方法与自动平衡电桥）、§3.1–3.4（端子结构/夹具/电缆/guard）、§4.1–4.6（误差与补偿）、附录 A（夹具附加误差）、§5.1.2/5.9–5.10（高低阻技巧、平衡器件）；RF 章节（2.5–2.7、3.5–3.7、4.7）与 §5.2–5.8/5.11–5.15 浏览。
  **页码约定**：引用写「printed 章-页 / PDF 页」（如 printed 2-7 / PDF p.28；正文页脚为 1-1…5-41、A-1…、B-1…）。
- **[QT]** QuadTech *7400 Precision LCR Meter Model B* Instruction Manual（`paper/literature/H7_1997_7400.pdf`，118 页，1997 型号、2013 归档版）。
  精读：Specifications、§2.3–2.4（接线/清零）、§2.6.2.8/.10/.11（精度/平均/接触检查）、§2.6.4.5–.6（失真检测/负载校正）、§2.6.5.4（开短路清零）、§2.8（全部夹具附件）、§3.2（理论）；IEEE-488/RS232/打印/软盘/维护章浏览。
  **页码约定**：页脚 "Page N of 118" 与 PDF 页相同，引用写「p.N」。

## 四问直答

### ① 自动平衡电桥："零值检波 + 反馈置零"如何消解 Kelvin 不对称（P2 产业逃生门证据）

**[KS] 零值检波 + 反馈置零的原文链**（这是最完整的一段）：

- 原理图（Fig 2-2 (b)）：I-V converter 取代电流表——"The operational amplifier of the I-V converter makes the same current as Ix flow through the resistor (Rr) on the negative feedback loop. Since the feedback current (Ir) is equal to the input current (Ix) flows through the Rr and **the potential at the Low terminal is automatically driven to zero volts. Thus, it is called virtual ground.**"（printed 2-5 / PDF p.26）
- "**The Rr is called the range resistor and is the key circuit element, which determines the impedance measurement range.**"（printed 2-5 / PDF p.26）
- 置零机构（§2.3.2）："The auto-balancing bridge section **balances the range resistor current with the DUT current while maintaining a zero potential at the Low terminal**."；"If the range resistor current is not balanced with the DUT current, **an unbalance current that equals Ix – Ir flows into the null detector at the Lp terminal.**"；"**The null detector detects the unbalance current and controls both the magnitude and phase angle of the OSC2 output so that the detected current goes to zero.**"；高频实现（null detector + 0°/90° phase detectors + vector modulator）后："Even if the balancing control loop has phase errors, the unbalance current component, due to the phase errors, is also detected and fed back to cancel the error in the range resistor current. **Consequently, the unbalance current converges to exactly zero, ensuring Ix = Ir over a broad frequency range up to 110 MHz.**"（printed 2-7 / PDF p.28）

**消解 Kelvin 不对称的具体条款**（虚地三优点，原文 Note）：

- "(1) The input impedance of ammeter (I-V converter) becomes virtually zero and does not affect measurements. (2) **Distributed capacitance of the test cables does not affect measurements because there is no potential difference between the inner and outer shielding conductors of (Lp and Lc) cables.** (At high frequencies, the test cables cause measurement errors as described in Section 4.5.) (3) Guarding technique can be used to remove stray capacitance effects…"（printed 2-6 / PDF p.27）
- 低侧接触电阻直接被"置零"作废：4T 接触电阻分析中 "**Rlp may cause the auto-balancing bridge to be unstable, but generally its effect is negligible.**"（printed 4-9 / PDF p.70）——Lp 是虚地检测脚、无电流，其 Rc 自然不产生误差项。
- **[QT] 同一架构的旁证**：7400 的 PL 脚 "**can't be detected [for contact failure] since it is at virtual ground potential, internal to the instrument**"（p.40）；电流通道是 "a **transadmittance amplifier with an internal standard in the feedback path**. This arrangement causes a voltage to be generated across the standard resistor proportional to the current."（p.112）——即反馈标准电阻（= Rr）+ 虚地的同一机构，只是不叫 null detector。

**给 P2 的用法**：产业逃生门 = 不靠两侧无源对称，而靠**反馈把负端钉死在 0 V**（虚地）+ **零值检波强制 Ix=Ir**。不对称（接触电阻、线阻、分布电容）不是被"匹配"掉的，是被**工作点**作废的。这与 P2"两线结构类不同/无源负端 Kelvin"的对照正中要害：手册里唯一消解负端不对称的手段是**有源置零**（与 4TP 同轴几何对消），从不指望无源网络自对称。

### ② 4TP 定义 vs. Kelvin 无源负端结构（P2 计量原型）

- **4T = Kelvin**："The four-terminal (4T) configuration can reduce the effects of lead impedances (wLL and RL) and contact resistances (Rc) **because the signal current path and the voltage sensing leads are independent**… **The 4T configuration is also called Kelvin connection configuration.**"（printed 3-4 / PDF p.45）；"In a 4T connection, the voltage and current terminals are separate. Since the voltmeter has high input impedance, no current flows into the voltage terminals. Hence, the voltage that is applied across the DUT can be accurately detected without being affected by the contact resistance."（App. A.3.2, printed A-4 / PDF p.131）
- **4TP 定义原文**："The four-terminal pair (4TP) configuration solves the mutual coupling between the leads by employing the following technique. The 4TP measurement circuit is similar to the shielded 4T configuration, but the outer conductors of instrument's Hc, Hp, Lp, and Lc terminals are isolated. **By connecting the outer shielding conductors to each other at the ends of the coaxial cables, the current loop is formed**… The test signal current flows through the inner conductor of the Hc cable, to the DUT, and the inner conductor of Lc cable, and then **returns to signal source through the outer shielding conductors of the Lc and Hc cables. Since the same current flows in opposite directions through the inner and outer conductors of the coaxial cables, the magnetic flux generated by the inner conductor is canceled** by that of the outer shielding conductor… As a result, the mutual coupling problem is eliminated. **The 4TP configuration can improve the impedance measurement range to below 1 mΩ. The measurement range achieved by this configuration depends on how well the 4TP configuration is strictly adhered to up to the connection point of the DUT.**"（printed 3-6 / PDF p.47）
- **端子纪律**：Fig 3-8 (b) 图注 "**Do not interconnect the outer shielding conductors of the cables at UNKNOWN terminals side**"（printed 3-6 / PDF p.47）；"If the shielding conductors of coaxial test cables are not interconnected properly at the ends of the cables, accurate loop current does not flow through the cables and, as a result, the measurement range will be limited, or in some cases, measurements cannot be made."（同页）
- **[QT] 端子命名**：面板 "Four terminal (BNC) with Guard"（Specifications, p.10）；端子 = Ground / IH / PH / PL / IL，"For guarded measurements connect to DUT shield"（Fig 2-1/2-2, p.22）；"The 7400 instrument employs a **four terminal measurement configuration** that permits easy, accurate and stable measurements and **avoids mutual inductance, interference from measurement signals, noise and other factors inherent with other types of connections**."（p.21）——注意 7400 **没有** 4TP：四根独立屏蔽 BNC，无同轴对回流约定，互感靠接线几何而非同轴对消。

**给 P2 的用法**：4TP 就是"Kelvin 无源负端结构"的**计量端规范**——负端（Lc/Lp）的电流返回路径被强制改走同轴外导体（与芯电流等值反向、磁通对消），Kelvin 的"独立电压感测"再叠加"定义好的回流几何"。它解决的是互感/残差，不是两端失配；其精度边界是 "**how well the 4TP configuration is strictly adhered to up to the connection point of the DUT**"——即无源结构在 DUT 处必须严格成立，这正是 P2 计量原型要引用的结构约束。

### ③ P1 反例搜索：有无"无源 RC 差分网络失配→共模转换"理论？

**两本手册均无，搜索为阴性**（全文词频检索 + 相关章节精读）：

- `common mode / common-mode / CMRR`：**[KS] 0 命中、[QT] 0 命中**。LCR 表是单端仪器，全书无共模指标。
- `mismatch`：[KS] 0 命中；[QT] 仅 1 命中且是错误信息表 "PRI & SEC MISMATCH, SET TO AUTO"（p.109），与电路失配无关。
- `differential`：[KS] 仅 1 命中——"a balanced DUT (such as balanced cable or the balanced input impedance of **a differential amplifier**)"（§5.10, printed 5-29 / PDF p.115），处理方式是整体外包给 balun："it is necessary to connect a 'balun' (balance-unbalance) transformer between the instrument and the DUT"（同页），**没有任何差分网络失配→CM 转换的推导**。
- **最接近的误差模型也到不了 P1**：① 开/短/负载补偿把残差建模为线性二端口——"the open/short/load compensation **models the test fixture residuals as a four-terminal network circuit represented by the ABCD parameters**"（printed 4-6 / PDF p.67）——是串/并联残差盒，不含差分对失配项；② 4T 接触电阻误差是单端 RC 低通："Rhp and Chp (distributed capacitance of the coaxial test cable) form a **low-pass filter**, which causes attenuation and phase shift of the Hp input signal… the resultant dissipation factor error is proportional to **–ωRhp × Chp and –ωRlc × Clc**"（printed 4-9 / PDF p.70）；③ stray C 误差机理是漏电流旁路（printed 3-15 / PDF p.56），guard 消除的是电位差不是失配。

**结论**：这两本产业手册的误差谱系里**不存在**"无源 RC 差分网络失配→共模转换"条目，引作 P1 反例不成立；反过来，其"沉默"本身可作 P1 的定位证据——工业补偿体系（open/short/load + ABCD 盒）默认单端残差可分离修正，P1 的失配致 G_DC≠0 是该体系外的新命题。

### ④ ADC 前端 / 抗混叠相关内容

**有 ADC 叙述，无抗混叠内容**（`alias` 在两本 PDF 均 0 命中；无 AA 滤波器设计、无 RC 差分滤波网络——与同库 H2 系 TI AAF 文档成对比）：

- **[KS] VRD 采样链**：单矢量电压表分时测 Vx/Vr——"**In order to avoid tracking errors between the two voltmeters**, most of the impedance measuring instruments measure the Vx and Vr with a single vector voltmeter by **alternately selecting them** as shown in Figure 2-3."（printed 2-5 / PDF p.26）；框图 = Buffer → 开关 S → phase detector → ATT → **A/D**（Fig 2-6 (b), printed 2-8 / PDF p.29）。
- **[KS] 采样式 ADC 与精度**："modern impedance measurement instruments use a **high speed sampling A-D converter**, in place of the previous technique, which used a phase detector and a dual-slope A-D converter. **Measurement time is proportional to the number of sampling points** taken to convert the analog signal (Edut or Err) into digital data for each measurement cycle… Theoretically, random noise (variance) in a measured value proportionately decreases inversely to the square root of the A-D converter operating time."（printed 2-12 / PDF p.33）
- **[KS] RF 段的下变频代替 AA**："the mixer circuit **down-converts** the frequency of the Edut and Etr signals to an IF frequency **suitable for the A-D converter's operating speed**."（printed 2-16 / PDF p.37）
- **[QT] 7400 的 ADC 前端**（p.112）："There are five major parts to this board: sine wave generator, voltage detector channel, current detector channel, **A/D converter**, and Digital Signal Processor."；"This voltage Ex is measured by the PH and PL leads, **is filtered and amplified according to its level**, and presented to one channel of the Dual A/D converter."（滤波器存在但**未命名、未给特性**，不能当抗混叠引）；"The two signals… are digitized by a **dual 18 bit A/D converter. A key concept of this conversion is that the samples are taken synchronously with the digital generation of the sine wave so that phase information may be obtained.**"；"a mathematical algorithm (**similar to a Fast Fourier Transform**) is used to extract the in phase and quadrature portions of the signal."
- **[QT] 相干采样约束**："**One complete cycle of stimulus voltage is required for measurement.** For example: at 10 Hz, 100 ms (1 cycle) is required just to collect data."（p.39）——整周期 + 同步采样 + DFT，是这套仪器对"混叠/泄漏"的实际答案（数字域相干化），而非无源 AA 网络。

## 核心命题（原文）

1. **方法谱系**："Considering only measurement accuracy and ease of operation, the **auto-balancing bridge method is the best choice for measurements up to 110 MHz**."（[KS] printed 2-1 / PDF p.22）；宽频实现靠 null detector + 相敏 + 矢量调制器，"the unbalance current converges to exactly zero, ensuring Ix = Ir"（printed 2-7 / PDF p.28）。
2. **量程由 Rr 定**：range resistor 决定量程，换档 = 换 Rr + 改 VRD 增益——"Range changes are generally accomplished by changing the gain multiplier of the vector ratio detector, and by switching the range resistor… maximum accuracy is obtained when the measured impedance is close to the full-scale value of the range"（[KS] printed 2-11 / PDF p.32）。
3. **端子结构 = 误差机理的分类法**（[KS] §3.1）：2T 吃 lead L/R + 接触电阻 + stray C（"the typical impedance measurement range (without doing compensation) is limited to **100 Ω to 10 kΩ**"，printed 3-2）；3T/5T 用 guard 外导体压 stray C；4T/Kelvin 用电压电流分离消接触电阻；4TP 用同轴回流消互感——每级结构解决一类误差，**残余误差逐级换项**。
4. **补偿不是校准**："Compensation, however, can not always completely remove the error… **Compensation is not the same as calibration and can not replace calibration.**"（[KS] printed 4-3 / PDF p.64）；开/短补偿假设残差 = 简单 L/R/C/G 盒（Fig 4-4, printed 4-4），复杂残差需 ABCD 三条件（开/短/负载）法（printed 4-6）。
5. **[QT] 清零即存数修正**："The zeroing process automatically measures stray parameters and retains the data, which is used to correct measurements so that results represent parameters of the DUT alone without test lead or fixture capacitance. Measurement accuracy is specified at the end of the QuadTech one meter cable (7000-01)."（p.72）；"It is not necessary to re-zero if the test frequency is changed."（p.22，注意 [KS] 侧则强调补偿随频率变化）。

## 关键数值（原文）

- **各端子结构可用量程**（[KS] Fig 3-2/3-3/3-5/3-6/3-8）：2T 无补偿 **100 Ω–10 kΩ**（printed 3-2）；3T "**extended above 10 kΩ**"（3-2）；4T "improved typically **down to 10 mΩ**"，<10 mΩ 则互感 M 致误差（3-4）；5T "**10 mΩ to 10 MΩ**, but the mutual coupling problem still remains"（3-5）；4TP "**below 1 mΩ**"（3-6）。
- **电缆伸长界**：F (MHz) × L (m) ≤ **15**（printed 3-12 / PDF p.53；4.5 重述于 printed 4-11）；无端接伸长误差 "**Error = k × ∆L × f² (%)**，k: –1 to +1"，"Using the open/short compensation will not reduce this error. Only the open/short/load compensation can minimize this error."（printed 4-13 / PDF p.74）。
- **补偿适用界**（printed 4-9 / PDF p.70）："(1) Measured open impedance (Zom) must be more than **100 times** the measured impedance of the DUT. (2) Measured short impedance (Zsm) should be less than **1/100** of the measured impedance of the DUT."；短路条残差 "**20 nH and 1 mΩ**… not suitable for low impedance measurement"（printed 4-5）。
- **低阻误差地板（夹具重复性）**：Ze = ±{ A + (Zs/Zx + Yo × Zx) × 100 } (%)（printed A-2 / PDF p.129）；"if the test fixture's short repeatability is **±100 mΩ**, then the additional error of an impedance measurement under 100 mΩ will be **more than 100 percent**"（A-2）；16034G 实例：proportional 0.5×(f/10)² %、open 5+500×(f/10) nS、short 10+13×(f/10) mΩ（A-6）。
- **高/低阻技巧**："High-value capacitance measurement is categorized in the **low impedance** measurement. Therefore, contact resistance and residual impedance… must be minimized. Use a 4T, 5T, or 4TP"（printed 5-4）；"Low-value capacitance measurement is categorized in the **high impedance** measurement. Stray capacitance… is a significant error factor… Proper guarding techniques and the open/short compensation can minimize the effects"（printed 5-5）。
- **[QT] 精度/速度/清零**：Basic 0.5% / 25 ms、Enhanced 0.25% / 125 ms、Extended 0.05% / 1 s（p.9, p.39）；负载校正后 "0.25 x (normal accuracy)" 仅在 "**3Ω ≤ Z ≤ 80kΩ**, 100mV ≤ programmed V ≤ 1V"（p.9；⚠ p.66 写 "between 3Ω and **800kΩ**"，两处上限不一致，疑手册笔误，引用时注明）；平均 √N、中值 √3 提升精度（p.40, p.65）；清零在 1 V @ "50, 100Hz, 1, 10, 50, 100, 250, 500kHz"（p.72）；源阻抗随量程 25 Ω/400 Ω/6.4 kΩ/100 kΩ（p.10；Z_RANGE 表 p.71）；接触检查 "likely to be unreliable when measuring devices of **less than 100 mΩ**"（p.40）；最低 20 mΩ 满量程时短路线自身电阻即误差（p.102）；"Best accuracy requires **geometric consistency** between that utilized during open/short zeroing and that utilized on fixtures and cables during the actual measurement process. This consistency may be especially difficult to achieve when using **unshielded Kelvin clip and tweezer type connections**."（p.9）。

## 对 P1/P2/P3 的对照

- **P1（失配消去条件）**：反例搜索**阴性**（见四问③）——两手册无"无源 RC 差分网络失配→共模转换"理论，连 common-mode 一词都不存在。可引的对照件是 [KS] printed 4-6 的 **ABCD 四端口残差盒**（工业补偿体系的"完备误差模型"上限）：P1 的失配致 G_DC≠0 落在该模型之外，Discussion 里可写"产业 LCR 误差谱系（串/并残差 + 二端口盒 + open/short/load）不含此项"。另 [KS] §5.10 把平衡 DUT 整体交给 balun 也佐证：手册把"对称/失配"问题视为仪器外问题，不做失配分析。
- **P2（Kelvin 地板/两线结构类）**：本笔记是 P2 的主粮。①的"零值检波+反馈置零"原文链（virtual ground / null detector / Ix=Ir 收敛）= **产业逃生门证据**：不对称由有源置零作废而非匹配消除；②的 4TP 定义 + "严格遵守到 DUT 连接点" = **计量原型**的端子级规范；[QT] p.40"PL at virtual ground potential"是第二台独立仪器的旁证。Kelvin（4T）与 4TP 的关系按 ② 引文写：4T=电流/电压路径独立（消接触电阻），4TP=再加同轴回流几何（消互感），两者都不承诺"无源对称"。
- **P3（AAF 衰减上界）**：无直接内容（两手册不涉抗混叠滤波器设计）。可作背景对照的只有：[QT] 相干采样（整周期 + 同步 DDS + 类 FFT，p.39/p.112）与 [KS] RF 下变频至 IF "suitable for the A-D converter's operating speed"（printed 2-16）——即两条"不用无源 AA 网络"的产业路线；若 P3 要论"AAF 是唯一前端防护"，这两条可作反面对照（数字域/变频域处理替代）。
- **引文价值**：[KS] printed 2-7（null detector 收敛段）与 printed 3-6（4TP 定义段）是 Intro/理论节最硬的两段产业引文；[KS] printed A-2 的 Ze 公式 + ±100 mΩ 例是低阻误差的定量锚；[QT] p.112 是"反馈标准电阻 + 同步双 ADC"的独立实现证据（引 1997 年量产仪器佐证该架构非 Keysight 独有）。

## 没读到的

- [KS] null detector/环路滤波/矢量调制器的**电路级实现与环路参数**（只到 Fig 2-5 (b)(c) 框图）；Rr 的温度系数/校准溯源不在正文（在各仪器手册）。
- **抗混叠**：两本均无（"alias" 0 命中）；[QT] p.112 的 "filtered and amplified" 滤波器无名无参数，不能引作 AA 证据。
- **共模/CMRR/差分对失配**：两本均无（见③），P1 反例在此闭环为零。
- [QT] 无 4TP、无 service 级电路图（§3.2 只到板级方块）；load correction 在 p.9/p.66 的量程上限 80 kΩ vs 800 kΩ 自相矛盾，未在 errata 解决（引用需注明）。
- [KS] 4294A/4284A 等具体机型的精度表达式、fixture 附加误差全表（散于各操作手册，本手册只给方法论与 16034G 一例）。
- 两手册都未讨论"两端子无源负端"结构类问题（那是 P2 自己的命题）；[QT] 对 <100 mΩ 接触检查失效只报告不给补救。
