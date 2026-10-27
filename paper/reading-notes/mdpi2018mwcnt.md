# 精读笔记 · Sam-Daliri 2018《MWCNT–Epoxy Nanocomposite Sensors for Structural Health Monitoring》（Electronics, MDPI）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> H6 轴定位：CNT-SHM 应用域 C 级证据，但**是 7 篇中唯一"自制前端+校准"的一篇**（Zangl 传感器系统组）。关键在于：面对两线制 DC 缺陷，其出路是**改用 AC 中频阻抗**而非 Kelvin 结构/前端条件分析——恰好从反面支持 P1/P2 的空白。页码 = PDF 页（MDPI"N of 14"，PDF 页与文页一致）。

## 出处
- Sam-Daliri, Faller, Farahani, Roshanghias, Oberlercher, Mitterer, Araee, Zangl. "MWCNT–Epoxy Nanocomposite Sensors for Structural Health Monitoring." Electronics 2018, 7(8), 143. doi:10.3390/electronics7080143。PDF 14+1 页。
- bib key：`mdpi2018mwcnt`。

## 核心命题（原文）
1. **主张 AC 阻抗测量比 DC 电阻更灵敏（全文核心 novelty）**（p.1 摘要）：
   > "The equivalent parallel resistance of the specimens is first measured by applying an alternating voltage at different frequencies. ... Using alternating voltage, a higher sensitivity of the impedance reading can be achieved."
   （p.2 再申："This AC impedance measurement can provide higher sensitivity by considering, also, the electrostatic properties of the material. ... This presents a novelty compared to aforementioned studies, where direct current (DC) measurement is employed."）
2. **测量硬件两套，均非通用 DMM**（p.3–4）：
   > "The first step was to determine the frequency-dependent initial equivalent parallel resistance Rp of the specimens using an LCR measurement bridge by Extech Instruments."（p.3，渗阈扫描）
   > "These measurements are done using a high-speed, high-resolution measurement platform [34,35]. It is based on an FPGA system with a customized analog front-end to enable high-speed, high-resolution measurements. For series production, the components can be integrated into a system which, in terms of size and costs, is well suited for the application of commercial structural health monitoring in buildings."（p.4，拉伸在线测量）
3. **前端拓扑 = 数字正弦源 + 50 Ω 分压（shunt）+ 输入放大链 + 数字下变频**（p.4–5）：
   > "...on one side, is connected to the input analog amplifier chain as part of the impedance measurement hardware. The other side is connected to the output, which supplies a digitally generated sine signal."（p.4）
   > "Via the shunt resistance of 50 Ω, which incorporates a voltage divider with the measurement impedance (see Figure 2), a voltage reading is recorded, which is proportional to the resistance of the sample."（p.5）
4. **校准 = 单点已知电阻定比例因子（增益校准，无失调/直流通路分析）**（p.5）：
   > "To determine the impedance as illustrated in the result diagrams, first a calibration measurement using a known resistance is done. Using this calibration measurement, and a proportionality factor (to relate the voltage at the measurement impedance to the voltage at the shunt resistance), the recorded voltage reading can be corrected to give the equivalent impedance."
5. **两线 vs 四线的显式表态：明知两线 DC 有缺点，用 AC 中频"让两线够用"，免做四线**（p.8，对 P2 最关键）：
   > "The majority of previous studies used the two-probe method to measure the electrical resistance changes during the tensile test [38–40], which may provide disadvantages for the DC measurements. Here, we use an AC measurement setup at an intermediate frequency, therefore, the two-probe method is sufficient, and the cumbersome preparation of two additional connections per specimen can be avoided."
6. **电极 = 银胶粘金属丝 + 表面环形接触以"最小化接触电阻"**（p.3）：
   > "...two metallic wires were applied close to the necking end parts at a specific distance of 7.5 cm. The wires are fixed using conductive silver adhesive. The surface-ring contact was used to minimize electrical contact resistance (see Figure 1b)."
7. **结论：3 wt% + 10 min 分散综合最佳**（p.11–12）：
   > "It was observed that dispersion times longer than 10 min provide no significant improvement in the equivalent parallel resistance of the nanocomposite. Although the maximum tolerated forces of these nanocomposite sensors were achieved with 1 wt % MWCNT content, the nanocomposite sensors fabricated with 3 wt % MWCNTs and a dispersion time of 10 minutes showed better self-damage sensing capabilities..."（p.11–12）

## 关键数值（原文）
- MWCNT 1 / 1.5 / 2 / 3 wt%；分散 5 / 10 / 15 min；固化 25 ℃（p.1、p.3）。
- 渗阈判定频率扫描用 LCR 表；拉伸在线测量选固定频率 **100 kHz**（p.8："R0 is the equivalent parallel resistance value at the chosen measurement frequency (here 100 kHz)"）。
- Shunt 电阻 50 Ω（p.5）；电极间距 7.5 cm（p.3）。
- 拉伸机 Zwick/Roell Z020，十字头 1 mm/min，ASTM D638 哑铃形（p.3）。
- 灵敏度定义：∝ ΔR/R0（p.8）；SEM 团聚区尺寸 10–20 µm（p.7）。
- 力学：表 2（p.11）列各配比机械性能（逐值未摘，待核表 2）。

## 对 P1/P2/P3 的对照
- **P1（G_DC≡0 元件条件）**：部分擦边但不冲突。该文根本退出 DC 域（AC 100 kHz + 数字下变频），其前端误差处理仅"已知电阻单点比例校准"；无直流通路/失调/CM 抑制条件讨论。→ 不是 P1 反例；反而显示应用侧遇到 DC 问题时第一反应是换 AC，而非元件级 DC 条件（P1 空白侧证，且是 7 篇中"最接近前端"的一篇）。
- **P2（Kelvin 结构地板 ≈56 dB）**：直接相关——论文显式承认两线 DC 缺点（"may provide disadvantages for the DC measurements"），但结论是"AC 中频下两线足够、免做四线"。**未给出任何量化论证**（无接触电阻/引线电阻比值、无地板概念）；P2 若成立，恰好补上这段被跳过的量化论证。killRisk：无（该文未测 DC、未比四线，不能证伪 P2）。
- **P3（衰减可达上界）**：无。AC 锁定式测量 + 下变频，无 DC 漂移/衰减模型。
- **方法学（门槛化）**：无损伤分级阈值；输出是 ΔR/R0–应变曲线与渗阈/分散工艺参数选优。
- **killRisk**：无（最坏也只是"有人已经用 AC 绕开 DC 前端问题"——这是工程侧证而非理论冲突；P1 主张的对象是 DC 链）。

## 没读到的
- 前端平台 [34,35] 的噪声/分辨率/线性度指标：未给（引 Faller 等 2017/2018 两文，本库未收——待核）。
- 接触电阻被"最小化"的量化效果（表面环形接触 vs 其他接触方式的差值）：无数据。
- 四线制实测对照：无（只是免做声明）。
- Table 2 机械性能逐值、ΔR/R0 曲线具体数值：图中曲线，未摘。
