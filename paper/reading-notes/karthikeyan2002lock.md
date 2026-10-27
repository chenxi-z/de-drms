# 精读笔记 · Karthikeyan 2002《Clock duty cycle adjuster circuit for switched capacitor circuits》（Electronics Letters）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。

## 出处
- Karthikeyan, S.（Texas Instruments, Dallas），"Clock duty cycle adjuster circuit for switched capacitor circuits", *Electronics Letters*, Vol. 38 No. 18, 2002-08-29（收稿 2002-05-28），journal pp. 1008–1009；PDF 物理页 1–2（第 2 页与 Al-Sarawi 施密特触发器论文同版面）。
- **题录定位警示**：bib key 作 "karthikeyan2002lock"，"lock" 指 pulse-width **locked loop**（PWLL），本文**不是**馈通/kickback 补偿论文，而是时钟占空比调整电路论文。
- 文件：`/home/anning/Documents/Obsidian Vault/20-硬件工程/10-项目设计/p1-文献谱系/fulltext/H5-kickback/karthikeyan2002lock.pdf`

## 核心命题（原文）
1. **SC 电路需要精确 50% 占空比的机理：每相相等的建立时间**（p.1）：> "Having on-chip clocks with 50% duty cycle is becoming increasingly important because of higher operating frequencies, particularly for switched capacitor-based circuits. One such example is a pipelined analogue-to-digital converter (ADC), where each stage operates on alternate phases of a single clock. Making the input clock to be 50% duty cycle, without affecting the jitter of the sampling edge, would ensure each stage to have an equal amount of time to settle."（这是本文与 H5"半周期建立"约束唯一相关的论点：建立预算 = 相位宽度，且采样沿 jitter 不得被时钟链破坏。）
2. **传统 PLL/DLL 无法同时满足高精度 jitter 规格**（p.1）：> "With the traditional approach using a PLL, a delay locked loop [1], it would be impossible to achieve the jitter spec for high precision designs."
3. **PWLL 结构：粗+细延迟线、脉宽检测、F/V 变换、高增益运放负反馈**（p.1）：> "This consists of two delay lines, two pulse shapers, one pulse width detector, two frequency to voltage converters and a high-gain operational amplifier, all connected in a negative feedback loop."（占空比由 FVC 电容比设定：> "The ratio C1/(C1+C2) determines the duty cycle at the output"，p.1。）
4. **实验：占空比调整器 ON 时 ADC 性能对输入占空比不敏感**（p.2）：> "It can be seen that the SFDR and the THD remain flat as the input duty cycle is varied from 30 to 70% with the duty cycle adjuster ON. Conversely, when it is OFF, the performance drops drastically, even with 45% duty cycle."（原文同段先把指标写作 "(SNRD and THD)"——"SNRD" 系原文排印之误，图 4 题注亦作 "a SNRD"。）

## 关键数值（原文）
- 验证平台（p.2）：> "a PWLL was designed as a duty cycle adjuster for the input clock of a 10 bit, 40 MS/s pipelined analogue-to-digital converter in a 0.18µ CMOS process at 1.8 V."（10 bit、40 MS/s 流水线 ADC、0.18 µm CMOS、1.8 V。）
- 功耗（p.2）：> "The power consumption is < 1 mW at 1.8 V."
- 测试条件（p.2）：> "at fs = 40 MHz and fin = 19 MHz"（fs=时钟 40 MHz，fin=输入信号 19 MHz。）
- 平坦区与失稳点（p.2）：占空比 30–70% 内 SFDR/THD 平坦；DCA 关断时 **45% 占空比即性能骤降**（Fig. 4a 读图：DCA off 在 ~40% 处 ENOB 跌至 ≈2.4，DCA on 全程 ≈9.1 ENOB——读图值，非正文数字）。
- 占空比可调范围（摘要与结论，p.1/p.2）：> "a wide range of duty cycle (25 to 75%) precisely, from a single-ended input clock with any duty cycle (25 to 75%)"。

## 对 P1/P2/P3 的对照
- **P1（消去条件）**：无涉。本文处理时钟产生，不处理输入网络/馈通消去。
- **P2（Kelvin 地板）**：无涉。
- **P3（衰减上界）**：无涉。
- **增量四（门槛化方法学）**：唯一可借的语义是"每级建立时间 = 相位宽度"这一约束表述（"equal amount of time to settle"），与 H5 的"外置 RC 必须在半周期内回稳"同向但**不讨论**输入 RC、kickback 幅值或运放稳定条件，未提供任何可引用的建立时间数值门槛。
- **killRisk：无威胁**。理由：主题是占空比与时钟链 jitter，与 P1 三条主张（消去条件/衰减上界/Kelvin 地板）零交集；归入 H5-kickback 目录属谱系放置偏差，笔记已标注。

## 没读到的
- Fig. 4 的曲线数值只有读图估计（ENOB ≈9.1 / 跌落点 ≈2.4），原图无网格数值标注，正文亦未给具体 dB/ENOB 数字——待核。
- "Experimental results" 段在 pdftotext -layout 输出中缺失（该段系第 2 页左栏），笔记中的逐字引用来自 300 dpi 渲染图逐字转录；"SNRD"vs"SFDR"原文自身不一致，照录。
- Reference 1（US Patent 5,317,202 延迟锁相 50% 占空比）未读。
