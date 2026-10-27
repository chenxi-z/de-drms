# 精读笔记 · Cage 1985《A Test of the Quantum Hall Effect as a Resistance Standard》（IEEE Trans. Instrum. Meas. IM-34）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
## 出处
- Cage, Marvin E.; Dziuba, Ronald F.; Field, Bruce F.（NBS 电学分部，Gaithersburg）
- IEEE Transactions on Instrumentation and Measurement, Vol. IM-34, No. 2, June 1985, pp. 301–303, doi:10.1109/tim.1985.4315329
- PDF 为期刊扫描版共 3 物理页（=期刊页 301–303；p.1 前半是上一篇热转换器论文的尾部）。全文已读。

## 核心命题（原文）
1. **量子霍尔电阻可作实验室电阻单位的监测标准**（p.1，摘要）：> "This paper demonstrates that the quantum Hall effect can be used to monitor a laboratory unit of resistance."（主题是 QHE 计量基准，不是差分滤波/CMRR。）
2. **测量方法 = 电位计式（零值法）差分比较**（p.2）：> "The first part of the experiment consisted of making potentiometric comparisons of the quantum Hall voltage VH with the voltage drop VR across a series-connected room temperature reference resistor using the measurement circuit indicated in Fig. 2."（与本仓库 H7 测量线同源的经典零值比较法；这是它被归入 H2 差分轴的可能原因，但「差分」在此指电压差检测，非差分滤波器。）
3. **零检测器与电流反转消漂移**（p.2）：> "An electronic detector, D, with an input current less than 10-15 A, amplifies the difference-voltage signal. (Note that the potentiometer does not require calibration in this arrangement.) The current source, potentiometer, and electronic detector are all battery operated. Thermally induced voltages and linear drifts in the current source and the potentiometer are cancelled by reversing the current through the device and the reference resistor."（高阻检测+反转取平均的系统误差消去手段，属测量方法学而非共模抑制。）
4. **系统偏移误差需另行校出**（p.2）：> "was corrected for a measurement system offset error [3] which was sometimes as large as (0.025 ± 0.013) ppm. This offset error was determined by replacing the Hall device by a second room temperature 6453.2 Ω resistor and then intercomparing the two resistors with the measurement system."（用替换法分离系统偏移——与 P1 的元件失配误差无对应。）

## 关键数值（原文）
- RH(i=4) ≈ 6453.2 Ω；测量电流 25.5 µA；温度 1.2 K；GaAs/AlGaAs 异质结（p.1–2）。
- 每 1 h 测量周期不确定度 0.017 ppm (1σ)（p.1 摘要）：> "calibrated relative to two quantum Hall effect devices with a 0.017-ppm (1 σ) uncertainty for each 1 h measurement period."
- Hall 台阶平坦度（p.2）：> "This Hall step is flat to within ±0.01 ppm over a range in magnetic field that is 2 percent of the central field value."
- 全链条（QHE→NBS 欧姆）总不确定度 ±0.047 ppm；参考电阻年漂移 (0.066 ± 0.017) ppm/year（p.1、p.3）。
- Hamon 串并联网络：两个 6453.2→100 Ω 网络，各由 8×800 Ω + 53.2 Ω 串联构成（p.3）。

## 对 P1/P2/P3 的对照
- **P1（无源差分网络失配→CM 误差解析条件）**：无。全文无差分滤波器、无共模、无元件失配→CM 误差映射。最接近的只是「电位差检测+误差修正」的测量思想。
- **P2（Kelvin 结构地板）**：无。虽用四端电位引出（Hall bar potential probes），但未讨论共模抑制或结构地板。
- **P3（平坦度约束衰减上界）**：无（其"flat"指磁场上 Hall 台阶的平台平坦度，与滤波器通带平坦度无关，不可混淆）。
- **方法学（D1–D10）**：无直接关系；其「替换法分离系统偏移 + 电流反转消热电势」与 DE-DRMS 项目自校准线（H7）同属计量方法学参考，非 P1 门槛化方法学。
- **killRisk 判断**：无威胁。与 P1 四主张完全不相交；在 P1 论文中至多作为 H7 计量谱系的旁支，不必引用于差分滤波轴。
- 谱系定位：四层谱系之外（计量标准史线）。

## 没读到的
- 图 2 测量电路细节（扫描图未 OCR 出元件连接）；检测器 D 的型号与 CMRR/隔离指标未在文字中给出。
