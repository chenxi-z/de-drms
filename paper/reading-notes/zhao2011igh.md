# 精读笔记 · Zhao 2011《High output-impedance current source for electrical impedance tomography》（2011 4th Int. Conf. BMEI, pp.1106–1109）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。

## 出处
- Dechun Zhao, "High output-impedance current source for electrical impedance tomography," *2011 4th International Conference on Biomedical Engineering and Informatics (BMEI)*, pp. 1106–1109. DOI: 10.1109/bmei.2011.6098486. 重庆邮电大学生物信息学院。
- PDF 4 页 = 印刷页 1106–1109（IEEE 版式，文字层完整；公式区排版有粘连，仅引用文字部分）。
- 定位：**测量链自研文（EIT 恒流源输出阻抗分析）**——改进 Howland 电路的解析 + 仿真 + 三运放实测。归 H6 批但实为仪表硬件文；**有真实的前端误差分析**（失调电压/偏置电流/输出阻抗频跌/GBW/SR），与 H6 材料文形成对照。

## 核心命题（原文）
1. **总命题：改进 Howland 电路的输出电流/输出阻抗由运放与外围电阻决定，选对器件可满足 EIT（p.1106, Abstract）**：
   > "This paper emphasized on analyzing the frequency-domain and the time-domain characteristic of the enhanced Howland circuit for electrical impedance tomography, and studied the influencing factor in depth. … Simulation and experiment indicated that it could improve the performance by selecting the suitable amplifier, peripheral components to meet requirements of electrical impedance tomography."
2. **域内谱系：四种 EIT 电流源，频响是主要短板（p.1106, §I）**：
   > "K. G. Boone reported that there were four current sources in EIT [6], including single op-amp circuits, multiple op-amp circuits, supply-sensing current source and Howland circuit. Much of the problem is the restricted frequency response."
   （EIT 恒流源设计谱系的索引句；Boone & Holder 1996 是原始综述。）
3. **理想极限：理想运放下输出阻抗无穷大，实际受失调/偏置限制（p.1107, §II）**：
   > "If the offset voltage and bias current are negligible in the ideal amplifier model, the current value in Equ.1 equals to −R2vs/R1R4b, and the output impedance is infinity."
   （解析把输出阻抗与失调电压 Voff、偏置电流 ib± 显式挂钩——**误差源进传递函数**的正面示范，但只到解析式、无统计。）
4. **电阻取值窗口（p.1107, §II）**：
   > "the value range of R is often between kilos of Ohm and hundred kilos of Ohm. When the value of R is over a million Ohm, output impedance falls rapidly. Consequently, the output current is easily impacted by the load."
5. **频域指标与运放选择（p.1107, §III + p.1108, §III）**：
   > "Gain-bandwidth (GBW) and slew-rate (SR) are both general and useful indexes to represent the frequency response and performance of the amplifier. In high frequency application, the amplifier would perform better with higher GBW and faster SR."（p.1107）
   > "The output current of the circuit can keep constant in the case of frequency under 1MHz and the load from 500 Ohm to 2000 Ohm. And the current sources using THS4021 as the amplifier has a widest bandwidth in the three amplifiers."（p.1108）
6. **★★实测输出阻抗随频率坍缩：仿真远大于实测（p.1109, §IV）**：
   > "the output impedance of the simulation was much larger than the actual output impedance. Especially, as the working frequency increases, the phenomenon has become more obvious. And the actual output impedance decreased along with the rise of frequency. At the frequency less than 1 MHz, the output impedance using THS4021 can be over 175 kilos Ohm. At the frequency of 1.5 MHz, the output impedance is only 20 kilos Ohm."
   （**"纸面输出阻抗≫实测、且随频率坍缩"的定量实据**——恒流源有效性与频率强相关，仿真不能代替实测。）
7. **方法学命题：多频系统里相对精度重于绝对精度（p.1109, §V）**：
   > "In a multi-frequency EIT system, this relative precision of the current sources is much more important than the accuracy of the current sources."
   （比值/相对测量的方法学主张——与比例式/相对测量谱系同声，但无展开。）

## 关键数值（原文）
- 输出阻抗（THS4021，实测）：**<1 MHz 时 >175 kΩ；1.5 MHz 时仅 20 kΩ**（p.1109）。
- 输出电流稳定性（THS4021）：**数 kHz–约 1 MHz 电流从 0.95 mA 变到 0.89 mA；<300 kHz 电流误差 <0.5%**（p.1109）；负载范围 500–2000 Ω（p.1106）。
- 失真：THS3061（电流反馈型）**>100 kHz 输出波形严重失真**（p.1108, 两处：仿真段与实测段）；THS4631 在负载/频率上升时输出电压快速下降（p.1108）。
- 电阻窗口：R 取 **kΩ–百 kΩ**，>1 MΩ 输出阻抗骤降（p.1107）；R4b 通常数百欧（p.1107）。
- 三运放：THS4021（高速电压反馈）、THS4631（高速高输入阻抗 FET）、THS3061（高转换率电流反馈）（p.1108）。
- **无 CMRR、噪声密度、温度漂移指标；无四线/两线讨论（纯电流源侧论文）。**

## 对 P1/P2/P3 的对照
- **P1（消去条件）**：**无**。交流恒流源设计，无直流通道路径、无差分/消去结构。
- **P2（Kelvin 结构地板）**：**无**（主题是电流源输出阻抗，非电压测量结构地板）。
- **P3（衰减可达上界）**：**低**。输出阻抗随频率坍缩（175 kΩ→20 kΩ）是"性能上限由器件物理决定且仿真高估"的个例，可作为**"可达上界需实测锚定"**的旁证，但与滤波衰减上界不同题。
- **方法学（门槛化）**：**中低**。两个可取姿态：①误差源（Voff、ib±）显式进解析式（p.1107）；②"仿真输出阻抗≫实测"点名并给实测修正（p.1109）；③"相对精度>绝对精度"的多频系统方法学命题（p.1109）。但均无判据化/统计化。
- **killRisk 判断：无**。对 P1/P2/P3 无威胁；对 DE-DRMS 的 Howland 否决也不构成翻案（本文实测恰证明 Howland 输出阻抗随频率坍缩，且 EIT 无"同一电流"比值前提）。价值：EIT 恒流源误差分析范式 + 输出阻抗频跌定量数据。

## 没读到的
- Figures 2–5 曲线本体（输出电流-R 关系、频域性能、实测电流、输出阻抗曲线；数值以正文为准）。
- Equ.1/Equ.4 的完整排版（PDF 公式区粘连；解析结论以正文文字引用为准，如需逐项推导须对照原文图版）。
- 引文 [6] Boone & Holder 1996（EIT 模拟仪表设计综述，四类电流源谱系原始出处）、[7] Chen 2010（三电流源比较：Howland/增强 Howland/双运放，输出阻抗最大结论出处）、[9] Hong 2009（CMOS 集成电流源 vs 改进 Howland）未读——若深挖恒流源谱系应补 [6][7]。
