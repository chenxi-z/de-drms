# 精读笔记 · Paleari 2021《Structural Monitoring of Glass Fiber/Epoxy Laminates by Means of Carbon Nanotubes and Carbon Black Self-Monitoring Plies》（Nanomaterials, MDPI）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> H6 轴定位：CNT-SHM 应用域 C 级证据。要点 = 测量硬件（一台 Keithley DMM 2700 台式万用表，两线接法）+ 零前端误差讨论。页码 = PDF 页（MDPI 排版"N of 14"，PDF 页与文页一致）。

## 出处
- Paleari, Bragaglia, Fabbrocino, Nanni. "Structural Monitoring of Glass Fiber/Epoxy Laminates by Means of Carbon Nanotubes and Carbon Black Self-Monitoring Plies." Nanomaterials 2021, 11(6), 1543. doi:10.3390/nano11061543。PDF 14+1 页。
- bib key：`paleari2021laminates`。

## 核心命题（原文）
1. **自监测原理 = 压阻（电阻随应变/损伤变化），传感与结构合体**（p.1 摘要）：
   > "Self-monitoring materials can provide both the structural and monitoring functionality in one component and exploit their piezoresistive behavior, namely, the variation of electrical resistivity with an applied mechanical strain."
2. **测量硬件：初始电阻与机械/冲击全程均用同一台数字万用表（两线制商品仪表）**（p.5）：
   > "The initial electrical resistance of the self-monitoring plies was measured using a digital multimeter (Keithley DMM 2700)."
   > "During mechanical and impact tests the electrical resistance variation was measured by means of a digital multimeter (Keithley DMM 2700, Keithley Instruments, Solon, OH, USA)."
   （单台 6½ 位 DMM 直读，无专用前端、无激励电流/采样率/分辨率任何说明。）
3. **电极制式 = 铜线+导电银胶，条带两端各一处（典型两线、无电流/电压分离）**（p.4）：
   > "An electrical connection was provided at each end of the conductive strips with thin solid copper wires and conductive silver paint. The plies are henceforth referred to as 'self-monitoring plies' (SMP)."
4. **灵敏度结论：CB 远高于 CNT**（p.1 摘要；p.7 正文同）：
   > "A higher sensitivity was found for the CB-based systems (Gauge Factor 6.1), while MWCNTs (0.55 and 1.04) ensure electrical percolation at lower filler contents, as expected."
5. **"校准"只发生在电阻–损伤系统级映射层面，与电气前端无关**（p.11，冲击能量平衡讨论）：
   > "...it could be possible to calibrate the system to establish a correlation between measured residual electrical resistance and the damage caused to the laminate, with the latter evaluated by means of image analysis techniques."
   （即：calibrate 的是 R_residual→损伤的经验对应，不是测量通道的增益/失调校准。）

## 关键数值（原文）
- 填料：CB 6 wt%；MWCNT 0.75 与 1 wt%（p.1）。
- Gauge Factor：CB6 ≈ 6.1；CNT0.75_1 = 0.55；CNT1_1 = 1.04（p.1 摘要 / p.7–8）。
- SMP 初始电阻 R0 以 kΩ 计（表 3，p.6；具体行值在 PDF 表格提取中错位，标称量级 kΩ——逐值待核原表）。
- 机械测试：Instron 5569，50 kN 载荷 cell，十字头 2 mm/min；循环三角波每圈幅值 +2 mm（p.5）。
- 落球冲击：550 g 钢球、70 cm 落高、3.77 J，按 ASTM F736 自制装置（p.5）。
- 层合板 30 层，SMP 1 或 2 层内嵌；SMP 条带 200×15 mm（p.4–5）。
- 树脂 E'（25 ℃）1.45–2.08 GPa（p.5）。

## 对 P1/P2/P3 的对照
- **P1（G_DC≡0 元件条件）**：无任何前端传递函数/直流通路分析——应用文献把 DMM 当黑箱理想表使用，P1 类误差根本不在讨论集合内（空白侧证成立）。
- **P2（Kelvin 结构地板 ≈56 dB）**：无。铜线+银胶两端引出 = 事实两线制；接触电阻/引线电阻未被提及，也未被论证可忽略（kΩ 级 R0 下两线误差确实小，但文中无此论证——待读者自行推断，不能归为原文观点）。
- **P3（衰减可达上界）**：无。DMM 2700 采样慢（原文未提速率），冲击 3.77 J 事件的"电阻变化"只能捕捉残余/准静态分量；原文未讨论带宽/动态。
- **方法学（门槛化）**：给出 Eimpact = Erel + Eabs + Ef 能量平衡框架（式 1，p.11）并设想用残余电阻预测损伤/剩余寿命，但明确"新实验尚未做"——阈值化仅停留在概念。
- **killRisk**：无（不触碰 P1/P2/P3 任何主张；反而是"应用域全靠商品仪表"的直接证据）。

## 没读到的
- DMM 2700 的量程/精度/采样率设置：原文未给。
- 表 3 各体系 R0 逐值（PDF 表格文本错位，量级 kΩ 确认，逐值待核）。
- 接触电阻、极化、温漂、引线电阻等任何电气误差讨论：无（已 grep conductive/calibrat/wire 等）。
- 四线制字样：无（全文无 four-wire/4-wire）。
