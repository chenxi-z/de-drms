# 精读笔记 · Wang 2004《Calibration Theory and Measurement Method of Four-Terminal-Pair Standard Capacitor Frequency Characteristic》（CPEM 2004, pp. 376–377）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> 期刊页码 376–377 印于页脚；PDF 页 1–2 对应 376/377。**PDF 文本层为扫描 OCR，字符错误率高**（"1000pF"→"lOOOpF" 等），引用已按上下文校正并标注；公式 (2) 文本层不可靠，未逐字引。

## 出处
- Xiaochao Wang, Yongshun Ruan, Dongxue Dai, Qi Wang, "Calibration Theory and Measurement Method of Four-Terminal-Pair Standard Capacitor Frequency Characteristic", 2004 Conference on Precision Electromagnetic Measurements (CPEM 2004), London, pp. 376–377. doi:10.1109/cpem.2004.305622.
- 本地：`H7-比率与电阻计量/wang2004alibrati.pdf`（2 页）。bib key：`wang2004alibrati`（literature.bib L1120）。
- 机构：中国计量科学研究院（NIM）。首引 Cutkosky 1964（[1]）——与已读 `H7_cutkosky1961_evaluati.md` 同谱系。

## 核心命题（原文）

1. **任务定位：4TP 标准电容频率特性校准（至 13 MHz），支撑 LCR 电桥/表的高频校准**（p.376，Abstract）：
   > "The calibration theory and measurement of four-terminal-pair (4TP) standard capacitor (STD CAP) frequency characteristic are studied for frequencies up to 13MHz. And frequency characteristic of 4TP air-dielectric standard capacitor 1000pF, 100pF, 10pF, 1pF and measurement uncertainty is provided."（p.376，OCR 校正）
   > "At present, many LCR meters are claimed to able to measure impedance up to tens of megahertz with an accuracy of better than 0.02%. The calibration of LCR bridges requires the knowledge of 4TP impedance standards frequency characteristic."（p.376）
   中文：标准件本身的频率非线性成为高频阻抗校准的瓶颈——"名义理想的标准件，其可用性受结构寄生限制"这一命题的数据来源。

2. **方法：高频段测驱动点阻抗 → 算串联电感（6.9 nH）→ 回归预测 100 kHz–13 MHz 特性**（p.376）：
   > "In the paper, we makes use of impedance analyzer measuring the driving point impedance values at high frequencies (1000pF, 10MHz-30MHz), and program is developed to calculate series inductance (6.9nH) of standard capacitor. Finally, a regression analysis is performed to predict standard capacitor frequency characteristic at frequencies from 100 kHz to 13MHz."（p.376，OCR 校正）
   中文：路线是**表征 + 修正**寄生（测出 6.9 nH 串感再回归外推），不是消除寄生——与 P1 的"元件条件消去"路线形成对照（表征派 vs 消去派）。

3. **4TP 导纳定义（Cutkosky 1964）：I₂=I₃=0、V₃=0**（p.376）：
   > "According to definition for 4TP admittance: I2=I3=0, V3=0[1],"（p.376）
   > "Zii is the driving-point impedance at port i with all other ports left open, and Ziisj is the driving-point impedance at port i with port j shorted and all other ports left open."（p.376，OCR 中下标粘连已校正；原文 [1] = Cutkosky 1964）
   中文：4TP 定义即"电流路径与电位测量解耦"的 Kelvin 思想在高频阻抗标准的延伸——P2 谱系的定义级引文（但本文未讨论 CMRR/地板）。

4. **测量流程（4 步）与仪器**（p.376–377）：
   > "Step 1: Radiofrequency impedance/material analyzer HP4291A is calibrated using open, short and 50 Ω load devices. Step 2: On the base of resonance frequency Agilent 16380A 1000pF standard capacitor, measurements (Zii, Ziisj) are made in the frequency range of 10MHz-30MHz."（p.376，频率下限 OCR 含混，**待核**：文本层作 "0OMHz-30MHz"，引言作 "10MHz-30MHz"）
   > "Step 3: According to equation (2), program is developed for computing series inductance of 1000pF standard capacitor by Visual C++. And 6.9nH is obtained. Step 4: Regression analysis is performed to predict the standard capacitor frequency characteristic at frequencies from 100 kHz to 13MHz."（p.377）

5. **【核心数据】1000 pF 标准电容的频率增量：100 kHz 才 3 ppm，10 MHz 已 27500 ppm**（p.377，Table 1）：
   > Table 1 "Increment of 1000pF STD CAP"：100 kHz → **3 ppm**；1 MHz → **275 ppm**；10 MHz → **27500 ppm**。（p.377）
   中文：串感 6.9 nH 与 1000 pF 在 ωL 逼近 1/ωC 时脱离——同一标称值器件，频率跨 2 个 decade，偏差跨 4 个 decade。**"结构寄生决定可用频率上限"**的定量例证。

6. **不确定度预算与总表**（p.377，Table 2/3）：
   > Table 2（1000 pF）不确定度来源：series inductance 拟合散布（A 类）；STD CAP 1 kHz 溯源（B 类，5/√3 ×10⁻⁶）；短期稳定性（B 类，1/√3）；4291A 测量不确定度（B 类）；温度（ignore）。（p.377）
   > Table 3 "Expand uncertainty of STD CAP"（×10⁻⁶）：100 kHz：1000pF/100pF/10pF/1pF = **6/6/6/6**；1 MHz = **30/6/6/60**；10 MHz = **2840/130/200/5800**。（p.377）
   中文：10 MHz 下 1000 pF 的扩展不确定度 2840×10⁻⁶（≈0.28%）——高频段标准件自身不确定度比 LCR 表声称的 0.02% 还差一个数量级，校准链条倒挂。

## 关键数值（原文）
- 对象：Agilent 16380A 空气介质 4TP 标准电容 1000/100/10/1 pF；频率 100 kHz–13 MHz（预测），实测 10–30 MHz（**下限待核**）（p.376–377）。
- 1000 pF 串联电感：**6.9 nH**（式 (2) + Visual C++ 程序计算）（p.376–377）。
- 1000 pF 频率增量：**3 ppm @100 kHz；275 ppm @1 MHz；27500 ppm @10 MHz**（p.377 Table 1）。
- 扩展不确定度（×10⁻⁶）：100 kHz 全部 **6**；1 MHz：30/6/6/60；10 MHz：**2840/130/200/5800**（1000/100/10/1 pF）（p.377 Table 3）。
- LCR 表声称精度参照：**0.02% @ 数十 MHz**（p.376）。

## 对 P1/P2/P3 的对照
- **P1（消去条件）**：相关度 **无**。无差分/共模/消去条件内容。killRisk：**无**。
- **P2（Kelvin 结构地板）**：相关度 **中低**。4TP 定义（I₂=I₃=0, V₃=0）是 Kelvin 解耦思想在阻抗标准的定义级延伸；本文贡献是**定量数据**：即便 4TP 结构，高频下结构寄生（6.9 nH 串感）仍以 27500 ppm 主导——可用带宽由结构寄生地板决定，需逐频点表征。P2 若主张"Kelvin 结构给出 ≈56 dB 地板"，本文是**同族不同量**的旁证（结构限制可用范围的实例），不是地板值本身。
- **P3（平坦度约束衰减上界）**：相关度 **无/低**。无匹配界内容；仅"频率特性偏离随 f² 增长"的现象学（ωL/1/ωC 之比 ∝ f²，与 3→275→27500 ppm ≈ ×f² 的趋势一致——本文未明说此标度律，**不要引为原文论断**）。
- **方法学（门槛化）**：可借鉴的是"寄生表征 + 回归外推 + 不确定度按频点列表"的报告范式；对 P1 的对照价值是**表征派**（测出寄生再修正）与**消去派**（结构条件使寄生不进入读数）的方法学分野。
- **killRisk 总评：无**（表征派计量实践，对 P1/P2/P3 无威胁）。

## 没读到的
- 式 (1)(2) 的完整可靠形式（文本层 OCR 严重失真；需回看 PDF 原版公式区域**待核**）。
- 回归分析的具体模型（几阶、拟合优度、外推误差如何进预算）。
- Z 测量的具体接法图（Fig.1 仅有框图）与 4291A 夹具寄生处理。
- 10–30 MHz 实测频率下限（"0OMHz"OCR 含混，待核）。
- 100/10/1 pF 各自的串感值与增量曲线数值（Fig.2 仅图形）。
