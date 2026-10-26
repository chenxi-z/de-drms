# 精读笔记 · Augustin 2018《Structural health monitoring of CFRP and CNT modified adhesive joints via electrical resistance measurement》（TUHH Dr.-Ing. 博士论文，Schriftenreihe Band 32）

> 格式标准（全组沿用）：出处 → 核心命题（原文引用）→ 关键数值（原文）→ 对 P1/P2/P3 的对照 → 没读到的。
> 读法：pdftotext 全文逐节读，引用一律原文加页码；不转述成模糊话。
> **页码约定**：引文页码 = 论文正文印刷页码；PDF 页 = 印刷页 + 12（正文首页 p.1 = PDF p.13，已逐页核对）。

**出处**：Till Augustin, *Structural health monitoring of carbon fiber reinforced polymers and carbon nanotube modified adhesive joints via electrical resistance measurement*, Technisch-Wissenschaftliche Schriftenreihe Band 32, TU Hamburg, 2018（17.07.2018 口试通过）。全文 139 PDF 页，正文英德混排（摘要德/英各一，正文英文）。章节：1 引言 / 2 背景 / 3 材料（快读）/ 4 CFRP SHM / 5 胶接 SHM / 6 CNT/epoxy 纤维 / 7 结论 / 8 展望。

---

## ① 电阻测量链：到底用什么仪器/电路（原文 + 页码）

**总判**：全文**没有任何自研测量电路**——全部是台面仪器直连试件（铜丝 + 导电银漆电极），
DC 二线电阻测量为主，唯一一次四线在第 6 章单纤维测试；**无恒流源设计**（"constant current" 一词只出现在背景章描述他人"电位法"时）。

仪器清单（原文逐条）：

| 章节/用途 | 仪器（原文） | 原文关键句 | 页码 |
| --- | --- | --- | --- |
| §4.2.1 电导率表征 | Keithley 2601A | "Four channel measurements were carried out to determine the conductivity of the UD CFRP specimens in three directions by using a digital multimeter (Keithley 2601A)."；"On each specimen, one continuous electrical measurement was carried out." | p.31 |
| 同上·银漆线路电导率 | Keithley 2601A | "one continuous electrical measurement was carried out by connecting the digital multimeter (Keithley 2601A) with the ends of the conductive paths." | p.31 |
| §4.2.2 三点弯曲·沿线测 | Keithley 2000 | "To measure the direct current (DC) resistance over the length of the conductive paths the ends of the paths are connected with a digital multimeter (Keithley 2000)." | p.32 |
| §4.2.2 穿透测量 | Keithley 2000 | "The DC resistance is measured from the top electrode to each of the four electrodes on the bottom side of the specimen." | p.32 |
| §4.2.3 板冲击试验 | Peaktech 2170 | "Electrical resistance measurements were conducted using a digital LCR meter (Peaktech 2170). The resistances of all possible electrode combinations were measured for the through-thickness measurements." | p.34 |
| §4.2.4 Ω 长桁 32 通道 | 自制多路器 | "a device that is able to measure the electrical resistance of all possible combinations of up to 32 channels with multiplexing capabilities was designed and produced by the Forschungswerkstatt Elektrotechnik at Hamburg University of Technology."（"Twenty-nine channels of the measuring device were connected with the copper wires"，p.37） | p.37 |
| §5.2.2 胶接 GFRP 冲击 | Voltcraft 91 | "Through-thickness as well as in-plane continuous electrical resistance measurements were conducted using a digital multimeter (Voltcraft 91)."（交叉设计 160 种电极组合全测，p.70） | p.70 |
| §5.2.3 scarf 疲劳 | Keithley 2000 | "DC electrical resistance measurements during fatigue testing were conducted using a digital multimeter (Keithley 2000). Four resistance combinations, namely A to 1, A to 2, B to 2, and B to 3, were measured successively with a measurement duration of 1 second (five cycles) per channel." | p.72 |
| §6.2 单纤维拉伸 | Keithley 2601A | "A digital multimeter (Keithley 2601A) is connected to both ends of the fiber for measuring the DC electrical resistance during the test." | p.93 |
| §6.2 纤维分段电阻 | Keithley 2601A·**四线** | "**Four-wire resistance measurement is conducted with a constant voltage of 1 V.** The chosen voltage value results in low scatter of the measured resistance when compared with lower voltages." | p.94 |

要点：

1. **激励是恒压不是恒流**：全文唯一写明激励条件的是第 6 章四线测量 "with a constant voltage of 1 V"（p.94）；
   CFRP/胶接各章**未给激励幅值、频率、量程、采样率**。"constant current" 唯一出现处在背景章描述别人的方法：
   "in the electrical potential method a constant current is always applied between two electrodes and the electrical potential is measured at two or more other points than on the electrodes, where the current is injected"（p.16）。
2. **二线为主、四线仅一次**：CFRP/胶接全部测量为二线（含 0.14 MΩ–3.3 MΩ 的 scarf 通道，p.85）；
   全文 "four-wire" 只在 p.94 出现一次（单纤维、DUT 两端引线独立）。
3. **"digital multimeter (Keithley 2601A)"** 系原文用词（2601A 实为 SMU/源表，此为我们的注，非原文）；
   "Four channel measurements"（p.31）措辞含混（原文未说明是 4 线还是 4 通道），照录不猜。
4. 测量是**准静态扫查**：冲击类试验都是"测前全组合 → 冲击 → 测后再测"（"After the impact event, the resistances of all electrode pairs were measured again"，p.35）；
   连续测量只在疲劳试验里出现，且是 **1 s/通道轮询**（p.72）。无高速采样、无同步采样需求。

## ② 接触电阻 / 引线 / 温度漂移的处理（对照本项目 Kelvin/温度补偿设计）

- **接触方式**：一切电极都是银漆手涂 + 多股铜丝粘接——"To enable reliable contacting with the system for resistance measurements, stranded copper wires were connected with the printed conductive paths using conductive silver paint."（p.27；p.68 同句再现于 scarf 试样）
- **引线机械固定**："As a last step, the copper wires were fixed with adhesive tape to avoid rupture at the connection points."（p.30）——只有防断，**无引线电阻/热电势处理**。
- **接触电阻仅作建模元件，无实测/无消去**：等效电路 "It comprises the electrical resistance of the printed path (RP), **the contact resistance between printed path and CFRP (RC)**, the resistance in thickness direction for each layer (Rt)…"（p.51）；
  且用粗假设定值："**The contact resistance between printed path and the neighboring layer is half of the resistance as the one between two neighboring layers**, because the resin rich inter-laminar layer between path and surface is half the size compared to the inter-laminar layer between two adjacent layers."（p.52）。
- **唯一一处"误差通路"处理**（第 6 章）："Insulation of the wires to the contacts with the fiber on the paper assures that exclusively the resistance of the fiber is measured and **avoids any close circuit via the testing machine**."（p.94）——防试验机并联旁路，不是 Kelvin。
- **温度漂移：不做补偿，靠三招回避**：
  ① 试样状态控制——"the specimens were dried for 5 h at 40 °C in a vacuum oven and stored in a desiccator until testing **to keep the specimen conditions constant**"（p.27）；
  ② 实验室恒温恒湿——"Ambient conditions were kept constant with temperature and relative humidity of 23 °C and 50 %, respectively."（p.72）；
  ③ **信号大到不需要**——"The measured resistance changes of 40 % and 78.6 % are relatively high. Therefore, **other parameters with an influence on the measured resistance like temperature or measuring device and measuring technique do not hinder the damage localization potential.**"（p.80）
  展望里自认是遗留问题："…it might be necessary to consider the environmental conditions because **temperature and humidity have an influence on the electrical resistance of CFRP and CNT modified polymers**. To determine an accurate damage location over a changing temperature/humidity profile it is necessary to know the influence of these parameters on the electrical resistance of the considered structure."（p.109–110）
- **对照片段**（本项目 P2 双电极电阻仪）：我们把接触电阻归入被测 R（两端子器件不可拆）→ 用 R_ref 自检锚定绝对精度 + 零点模式；温度用 TMP117 外置探头实测补偿（AGENTS.md："温度补偿是能否达到 1% 精度的决定性环节"）。Augustin 全链条里**没有对应物**——他既不锚定绝对精度（只看 ΔR/R₀），也不测温度，回避手段（恒温房 + 大信号）在野外 SHM 不可复制，他自己在 p.109 也承认。

## ③ 测量精度与分辨率要求的原话（P2/P3 应用背景引文）

**该文的"精度/分辨率"几乎全指空间分辨率（电极间距）与检测下限（损伤尺寸），不是仪器电气精度**——这本身就是给 P2/P3 写应用背景的最好引文：

1. **空间分辨率 = 电极间距**："Hence, **the interspace distance of the conductive paths determines the threshold for the smallest impact damages that are detectable.**"（p.77）；
   "the size of the impact damage can be approximated with **an accuracy that is determined by the distance between the conductive paths**."（p.79）；
   "For a more precise damage localization of the head impact (H1) **more conductive paths would be necessary to improve the resolution of the monitored area**. Hence, the electrode design determines the localization potential significantly."（p.64）
2. **插值分辨率**："To define suitable zones of influence, the scaling factor β was set to 3 mm. **For smaller values, no significant increase in the resolution was seen.** Points of a pattern of 5 mm x 5 mm were chosen as locations to calculate P(x,y,z)."（p.37）
3. **检测下限由损伤尺寸定，不由仪器定**："All failures detected by the measured force, exceeding a certain amount of energy release, can be detected by resistance changes. … Thus, **all failures exceeding a certain size and therefore being relevant for the integrity of the specimen as well as the final fracture can be detected reliably.**"（p.42）
4. **仪器侧唯一下限表述**（第 6 章）："For CB and FLG modified epoxy fibers, the electrical conductivity is **below the geometry and device determined measuring limit**."（p.94）
5. **实际要分辨的信号量级（原文数值）**：首个损伤事件 "the resistance increases 4.1 %"（p.44；Fig.4.15 表列逐步 4.12/6.85/7.13/7.21/12.43 %，p.45）；
   无损区基线 "the relative resistance change is in the range of ±2.5 % until final fracture"（p.46）；
   疲劳早期 "the resistance change stays in the range of ±10 % for all channels"（p.85）、"small resistance changes of ±15 % for all channels"（p.88）；
   压阻峰值 "a maximum of ∆R/R0 = 5 ± 1 % for all tested specimens"（p.99）。
   → **应用背景可引结论**：CNT-SHM 阻测的有用信号在 **ΔR/R₀ 百分之几到几十 %**，判读靠分档/定位而非绝对精度；这与 P2 仪"1% 分档（绿/黄/橙/红）"同量级，而比 P2 的 0.005% 线性/4½ 位指标**宽松约两个数量级**——P2 的高指标是通用仪器定位，不是该应用逼出来的。

## ④ 前端滤波 / 共模处理（预期无 → 如实记录：**无**）

- 全文 grep（filter / amplifier / ADC / common-mode / differential / guard / shield / gain / noise）**无一条关于测量前端信号调理的正文内容**：
  唯一 "full bridge" 是冲击机测力的应变片电桥（"the head of the impactor is equipped with a strain gauge full bridge"，p.35/p.71），与电阻链无关；
  唯一 "Differential" 是 DSC（Differential scanning calorimetry，缩写表 p.XII）；唯一 "noise" 是超声背景噪声（p.14，"may suffer from background noise"，指声学方法）。
- 测量链即"仪器 → 铜丝 → 银漆电极"，**无放大、无滤波、无共模设计、无屏蔽/双绞描述**。
- 信号处理只在数字域：损伤指数插值 P(x,y,z)（Eq. 4.2–4.4，pp.36–37）与幅值归一化（"the resistance change … is normalized by setting each local maximum value to 100 %"，p.63）。
- **对 P1 论文的 killRisk 判定：无**——该文不触碰 P1/P2/P3 任何命题（无 RC 梯形、无 SC 负载、无共模消去问题），只能作 H6 轴"应用域 + 测量硬件现状"证据（与 literature-index H6-1 定位一致）。

## ⑤ 与 P2"双电极电阻仪"最可类比 / 最不可类比

**最可类比**：

1. **同类被测对象**：都是"材料自身即传感器"的两端子阻性传感层——他测 CNT 改性胶膜/银漆线路（"no sensors have to be embedded…the material itself acts as a sensor"，p.1），
   我们测两端 MWCNTs 导电网络损伤分级层；都是**两端子**测量（接触电阻天然含在 R 里），都不可能在被测件上开尔文。
2. **同类读出范式**：ΔR/R₀ 相对变化 + 分档判读（他的 heat map/归一化 vs 我们的绿/黄/橙/红 R/R₀ 分档）；损伤事件对应的 ΔR 量级（几个 %）与我们 1% 分档阈值同量级。
3. **同一环境痛点**：温度/湿度对阻值的影响被点名为走向实用的**头号未解问题**（p.109–110）——正是我们把 TMP117 温补列为"决定性环节"的依据链。
4. **同一接触难题**：电极-材料接触的稳定性/重复性决定测量成败（他的银漆+铜丝 vs 我们的夹具电极），他的 R₀ 离散（273–480 Ω，p.79；1–210 Ω，p.63）实证了接触/几何散布会盖过仪器误差。

**最不可类比**：

1. **仪器层级完全不同**：他是"拿台面表测"（Keithley 2601A/2000、Peaktech 2170、Voltcraft 91、自制 32 通道多路器），我们是**自研专用仪**（8 µA 恒流 + Rsense 150 kΩ + ADS131A02 24 bit 同步采 + R_ref 自检 + TF 记录）；他对测量链零设计，我们的 P2 命题（Kelvin 无源负端结构地板）在他那里根本不存在。
2. **精度需求差两个量级**：他的信号是 4–285 % 级 ΔR/R₀（p.79 "maximum of 78.6 %"；p.63 "285 % and 126 %…154 %"），明确说仪器误差不碍事（p.80）；
   我们要 1% 分档、设计量程内 ≤0.005% 线性、4½–5½ 位。**他是"粗信号 + 空间分辨率"问题，我们是"细信号 + 电气分辨率"问题。**
3. **激励与拓扑**：他唯一写明的是恒压 1 V 四线（p.94，还只是单纤维）；我们是恒流 8 µA、双通道同步实测（恒流测电阻、不做电桥），且合规栈/漏电 <1 nA 等硬约束在他的场景里毫无对应。
4. **时序需求**：他最快是 1 s/通道轮询（p.72）+ 冲击前后静态对比；我们按 E.4.3 冲击全程 128 kSPS 采满、按需降采样——他的"冲击后测电阻"范式替代不了我们的动态跟踪。

## 关键数值（原文）

- 初始电阻散布：沿线 R₀ = 2.1 Ω（p.41）；穿透 R₀ = 2.47 ± 0.24 Ω（p.55）；
  胶膜穿透 273–480 Ω（lined，p.79）/ 65–286 Ω（crossed，p.80）；长桁 1–210 Ω（p.63）；
  scarf 通道 0.14 MΩ–3.3 MΩ（p.85）与 1.4–2.1 MΩ（p.88）；单纤维 R₀ = 6.85·10⁶ Ω（p.98 图注）、23.7 mm 段 7.5 MΩ（p.96）→ **仪器需跨 ~1 Ω–10 MΩ**（比我们 73 Ω–600 kΩ 更宽，但无精度要求）。
- 损伤信号：首个 IFF +4.1 %（p.44）；穿透通道 +26 % / +17.5 %（有损区）vs ±2.5 %（无损区）（p.46）；
  冲击后最大 +78.6 %（p.79）/+40 %（p.80）；长桁冲击 +285 % / +126 % / +154 %（p.63）；疲劳至破坏前 +171 %（p.85）。
- 电极几何：冲击板 16 点圆电极 ⌀5.5 mm、间距 25 mm（p.28）；胶膜路径间距 8.75 mm（p.67）；scarf 路径间距 8.75 mm（p.68）。
- 胶层厚度-阻值线性：R = 78.7 Ω + 0.43x Ω，x = bond line thickness in µm，R² = 0.90（p.81 图 5.12）。
- 电导率（Table 4.1，p.39）：纤维向 3.7·10³、面内横向 1.5·10¹、厚向 1.4·10⁰ S/m；烧结银墨 4.9·10⁵ S/m。

## 对 P1/P2/P3 的对照

- **P1（论文一 · ΣΔ 前端抗混叠极限）**：本文零相关内容（见④），**无 killRisk**；引用价值仅限 H6 应用域背景（"SHM 阻测用商用台面表即够、学术界不设计前端"这一现状证据）。
- **P2（双电极电阻仪）**：应用侧最强背书 + 需求侧反衬——背书：两端子阻性传感层 SHM 确实只需 ΔR/R₀ 百分位判读（③⑤）；反衬：他用 2 线台面表配大信号就够，我们仪器的高指标（4½ 位、0.005% 线性、温补）是**超出该应用需求的通用化设计**，写引言时要老实说，不要拿他证明"必须 24 bit"。
  可引痛点句：p.80（仪器/温度不碍事是因为信号大）与 p.109–110（温湿度影响是走向实用的未解问题）——后者直接支持我们温补路线的必要性。
- **P3（电阻测量仪器/ERT 应用线）**：③的"空间分辨率 = 电极间距"系列原话（p.37/p.64/p.77/p.79）是"电极网络设计决定定位分辨率、仪器决定电气分辨"分工论述的现成引文；
  其 32 通道多路器扫查（p.37）与逐通道 1 s 轮询（p.72）是 ERT 式多路测量的朴素先例，可作对照引用。

## 没读到的

- 激励参数（幅值/频率/量程/采样率）除 p.94 的"恒压 1 V 四线"外全缺；Keithley 2601A 在 CFRP 各章的接线（2 线/4 线、是否 SMU 源表模式）未写，"Four channel measurements"（p.31）语义含混。
- Peaktech 2170 LCR 表的测试频率/电平未给（用 LCR 表测 DC 语境的 R，AC 参数却没写）。
- 自制 32 通道多路器的电路/精度/开关接触电阻特性零描述（只说 Forschungswerkstatt 制造，p.37）。
- 接触电阻无实测值（只有 p.52 的建模假设）；无热电势/零点/电流反向/校准溯源内容；无重复性/不确定度分析。
- 引文中未到手者：正文提及但未展开测量硬件的外部对照（如 Xia et al. [161] 损伤深度敏感性、Todoroki et al. [168] 负阻变化解释），未核查原文。
