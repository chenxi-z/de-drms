# 精读笔记 · QuadTech 1997《7400 Precision LCR Meter Model B Instruction Manual》（厂商仪器手册，Form 150262/A5，118 页）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> PDF 页 = 手册页脚页码（"Page N of 118"）。定位：**P2 的产业级逃生门**。⚠️ 核心发现：7400 的测量机构是**跨导放大器（I-V）+ 反馈内标准 + 虚地低端**——这是自动平衡电桥的实现形态，但**手册全文不使用 "auto-balancing bridge" 术语**（"bridge" 全册仅 1 次，p.32 直流偏压节的口语"connecting the bridge"指仪器本体）；没有"平衡条件↔失配"的定量章节。本手册与已有合并笔记 `H7_keysight_7400_manuals.md`（Keysight handbook + 本手册）部分重叠，本笔记为 bibkey 独立精读，专注于本手册自身页级证据。

## 出处
- QuadTech, Inc., *7400 Precision LCR Meter Model B Instruction Manual*, Form 150262/A5, 1997（版权页 "QuadTech, Inc., 1997"；IET Labs 托管档案）。118 页。
- 结构：Specifications (p.9) / Operation §2（p.21 起：接线 2.3、清零 2.4、精度 2.6.2.8、平均 2.6.2.10、接触检查 2.6.2.11、负载校正 2.6.4.6、开/短路 2.6.5.4、附件 2.8）/ Theory §3（p.111–114）。
- 读取：pdftotext 全文 + 目录定位精读；AutoAcc 公式区 OCR 损毁处标 [OCR损]。

## 核心命题（原文）
1. **四端子 + 保护端接口定义（规格表原句，bib 注记所引）**（p.10）：
   > "Front Panel Test Terminals: Four terminal (BNC) with Guard"
   （端子命名 = Ground / IH / PH / PL / IL，Fig 2-1/2-2，p.21–22："For guarded measurements connect to DUT shield"。）

2. **四端子测量的理由——避开互感/串扰/噪声，而非处理共模**（p.21）：
   > "The 7400 instrument employs a four terminal measurement configuration that permits easy, accurate and stable measurements and avoids mutual inductance, interference from measurement signals, noise and other factors inherent with other types of connections."
   （产业四端子的动机清单里没有"共模/失配"条目——四端子解决的是引线阻抗与互感。）

3. **测量机构 = 电压/电流双通道比值测量，电流通道是反馈内标准的跨导放大器（自动平衡电桥的实现形态）**（p.112）：
   > "The current flowing through the unknown is applied to a transadmittance amplifier with an internal standard in the feedback path. This arrangement causes a voltage to be generated across the standard resistor proportional to the current."
   （配合电压通道："This voltage Ex is measured by the PH and PL leads, is filtered and amplified according to its level, and presented to one channel of the Dual A/D converter."——Z = Ex/Ix 比值测量，精度锚定到反馈标准电阻。）

4. **低端虚地——负端被有源钉死在 0 V（P2 逃生门的机构证据）**（p.40，接触检查注记）：
   > "A contact check is possible on three of the four Kelvin connections by a loss of voltage detecting technique, a failure on the PL connection can't be detected since it is at virtual ground potential, internal to the instrument."
   （PL 检测脚无电流、电位恒 0——负端不对称不是被"匹配"掉，而是被工作点作废。Kelvin 一词在此出现："the four Kelvin connections"。）

5. **同步过采样 + DSP 相量提取**（p.112）：
   > "The two signals representing voltage across and current through the unknown are digitized by a dual 18 bit A/D converter. A key concept of this conversion is that the samples are taken synchronously with the digital generation of the sine wave so that phase information may be obtained."
   > "a mathematical algorithm (similar to a Fast Fourier Transform) is used to extract the in phase and quadrature portions of the signal."

6. **开/短路清零 = 残差校正体系（精度指定在电缆端头）**（p.22）：
   > "Before making measurements, the 7400 should be zeroed to correct for test lead and/or fixture errors. During the zeroing process corrections are calculated and stored in instrument memory and applied to subsequent measurements. Measurement accuracy is specified at the end of the QuadTech one meter cable (7000-01). Open and short circuit zeroing should be done at the end of this cable."
   （规格表脚注 p.9："Best accuracy requires geometric consistency between that utilized during open/short zeroing and that utilized on fixtures and cables during the actual measurement process."——几何一致性本身就是门槛。）

7. **精度是相对校准标准的相对精度，总精度须加校准件不确定度**（p.72 注记）：
   > "Accuracy given by the equations is the measurement accuracy relative to calibration standards, total accuracy equals the relative measurement accuracy plus the calibration uncertainty of the calibration standards."

## 关键数值（原文）
- **精度三档（速度-精度权衡，p.9 与 p.39 一致）**：Basic ±0.5%（25 ms）、Enhanced ±0.25%（125 ms）、Extended ±0.05%（1 s）；DF 档 ±0.0050 / ±0.0025 / ±0.0005。脚注：* "At optimum test signal levels, optimum DUT value and without calibration uncertainty error."
- **平均改善精度（p.40）**："Divide the primary accuracy by the square root of the number to average"（下限 "never less than 0.05% for primary parameter or 0.0005 for secondary parameter"）。
- **负载校正（p.9 与 p.65–66）**："Measurement accuracy is 0.25 x (normal accuracy) with Load Correction implemented and compared to user supplied standard"，有效域 "DUT's with impedance (Z) between 3Ω and 800kΩ, with programmed voltage from 100mV to 1V"（p.9 写 80kΩ，p.66 写 800kΩ——**两处不一致，待核**，疑一处排版丢零）。
- **频率（p.9）**：10 Hz–500 kHz，分辨率 0.1 Hz（≤10 kHz），准确度 ±(0.002% + 0.02 Hz)。
- **源阻抗/量程电阻（p.9 + p.71 ZRANGE 表）**："25Ω, 400Ω, 6.4 kΩ or 100 kΩ, measurement range dependent"；电压模式 ZRANGE 按 Zm 与 Fm 分档（如 "100kΩ for Zm ≥ 25kΩ … 25Ω for Zm < 100Ω"）。
- **量程（p.9）**：|Z|, R, X 从 "000.0001 mohm to 99.99999 Mohm"。
- **精度边界判据（p.71）**："For I * Zm > 3, accuracy is not specified"。
- **接触检查可靠域（p.40）**："The contact check is likely to be unreliable when measuring devices of less than 100 mΩ of impedance."
- **预热（p.21）**："For optimum measurement results at specified accuracy a 30-minute instrument warm-up period is highly recommended."
- **AutoAcc 计算精度公式（p.70–72）**：A% 依 Vs（测试电压）、Zm、Fm（频率）、D/Q 展开的解析式，如 "For C, X, and B, with D > 0.1, multiply A% by √(1+D²)"（p.70）；主公式与 D/Q/θ/ESR 派生式（p.70–72）**[OCR损——公式排版被压坏，系数结构不可靠，用前须按页图逐字核对]**。

## 对 P1/P2/P3 的对照
- **P1（G_DC=H_N−H_P≡0 消去条件）**：无内容。全文无 common-mode/CMRR 概念（grep "common mode/CMRR" 0 命中）；唯一的 "mismatch" 命中是错误信息表 "PRI & SEC MISMATCH, SET TO AUTO"（p.109），与电路失配无关。仪器是单端比值测量架构，其误差谱系（开/短/负载残差、接触电阻、杂散电容）不含"差分对失配→共模转换"条目。
- **P2（Kelvin 结构地板 ≈56 dB）**：**中高**。产业逃生门的机构证据链齐备：(a) 四端子 + Guard 接口（p.10/21）；(b) 负端虚地由内部反馈放大器强制（p.40）；(c) 电流由反馈内标准电阻量化（p.112）；(d) 残差靠开/短路清零 + 负载校正剥离（p.22/65）；(e) 最优精度 ±0.05%（≈66 dB 相对精度）在 Z 3Ω–800kΩ、100 mV–1V 域内达成。**对 P2 的含义**：产业方案的"负端不对称"消解 = 有源置零 + 校正，而非无源网络自对称——支持"无源 Kelvin 负端存在地板、逃生靠架构"的论证方向。
- **P3（平坦度约束下 N 阶无源梯形衰减解析上界）**：无内容（无滤波器综合内容）。
- **方法学（D1–D10 门槛化）**：中相关——"精度分档（Basic/Enhanced/Extended）+ 平均/中值 + AutoAcc 按测试条件现算精度 + 负载校正收窄到 0.25×"是产业界"精度指标可预算、可降档"的完整样板；其精度边界判据（I×Zm>3 不指定、几何一致性要求）就是门槛声明。
- **killRisk：低**，但有一处**引用措辞风险**：若 P1/P2 把 7400 称作"自动平衡电桥（auto-balancing bridge）仪器"，本手册自身无此措辞——手册只描述 transadmittance + 虚地机构（p.112/p.40）；"自动平衡电桥"的零差检波表述在 Keysight *Impedance Measurement Handbook* §2.3.2（见 `H7_keysight_7400_manuals.md`）。引 7400 时宜写"I-V（跨导）式、虚地低端、反馈内标准"或以手册 p.112 原句为准。另 p.9 (80kΩ) 与 p.66 (800kΩ) 负载校正域不一致，引用前待核。

## 没读到的
- AutoAcc 主公式与 D/Q/θ/ESR 精度式的完整系数（p.70–72 公式区 OCR 损毁 [OCR损]，未按页图逐字重建）。
- IEEE-488.2 / RS-232 / handler / binning / 打印/软盘各接口章（p.41–96）与错误信息表全表（p.107–110）——浏览未精读。
- 校准程序（§2.6.5.6, p.74）与维护章（Section 4, p.115–118）未读。
- 高压/低阻夹具细节（§2.8, p.97–106）只读了 Kelvin 夹子颜色/端子定义表（p.98）。
- 7400 与经典 ABF（如 HP 4284A 零差检波闭环）的严格等价性——手册不含此对比，需 Keysight handbook 交叉印证（已由合并笔记覆盖）。
