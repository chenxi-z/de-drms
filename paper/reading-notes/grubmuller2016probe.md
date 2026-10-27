# 精读笔记 · Grubmüller 2016《Development of a Differential Voltage Probe for Measurements in Automotive Electric Drives》（IEEE Trans. Industrial Electronics）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。

## 出处
- Grubmüller M., Schweighofer B., Wegleiter H., IEEE Transactions on Industrial Electronics, DOI 10.1109/TIE.2016.2626374（early access 排版，未定稿页码）。
- PDF 共 8 物理页，全文页码 = 物理页。
- 内容：1 kV 差分电压探头 = 两路相同 RC 补偿分压器 + 滞后校正电路 + 差分放大器；用于 PWM 电驱功率测量。

## 核心命题（原文）
1. **探头架构 = 双分压器匹配 + 差分放大**（p.1 Abstract）：
   > "The main parts of the probe are two input voltage dividers with a further frequency compensation circuit and a difference amplifier. … The probe has a very flat frequency response up to 1 MHz, a bandwidth of 20 MHz and a linearity better than 250 ppm up to the maximum differential input voltage of 1 kV."
2. **平直传递函数 = 元件级匹配条件（补偿分压器的 RC 匹配，P1 式元件条件的经典形态）**（p.3）：
   > "For a flat transfer function GA(f) = GA(0) = 1/500 has to be valid. For the circuit shown in Fig. 5 (A), this dependence can be approximated by choosing R2/(N1 R1 + R2) = (C1/N1)/(C1/N1 + C2 + CLP), (2) where the adjustment is done by changing the capacitor C2."
   （电阻分压比 = 电容分压比，即 R·C 时间常数跨支路匹配——与 P1 的"元件条件使两路径传递函数恒等"完全同构，只是对象是分压器而非抗混叠滤波器。）
3. **残差再校正：滞后网络逐频点抵消分压器残差**（p.4）：
   > "The input divider is then followed by a lag circuit, see (B) in Fig. 5. This circuit has a DC gain of one and attenuates signals at high frequencies… Choosing values for R3 R4 and C4 to reach GB(f) = GA(0)/GA(f), (5) … results in a flat overall gain up to a few MHz"
   实际实现（p.6–7）：
   > "are calculated, so that GB(f) = GA(0)/GA(f), (10) by solving the optimization problem min GB(f, R4, C4) − GA(0)/GA(f), (11)"
   > "It shows the nominal attenuation of 40 dB and the bandwidth of 20 MHz." … "The probe has a frequency response flatness of ±0.1 % up to 1 kHz and ±0.2 % up to 2 MHz."（p.7）
   （第一级故意欠补偿 2 dB（p.4："the input divider is left undercompensated by about 2 dB"），C2 = 0.7·C1·R1/R2 "which is empirically determined and confirmed by a circuit simulation"（p.4）——工程上不追求单级元件条件一次到位，而是留残差给第二级网络吸收。）
4. **CMRR 由失配决定（引用 Pallas-Areny & Webster 1991 公式——本谱系已读件）**（p.5）：
   > "To reach a high common-mode rejection ratio (CMRR), a quad resistor array with a very low matching tolerance (tR = 0.025 %) is used for the resistors R5 to R8; the capacitors are standard tC = 5 % tolerance types. The contribution of the resistor mismatch to the CMRR of the amplifier is calculated with CMRRR = ½·(R6R8 + R6R7 + R5R8)/(R5R8 − R6R7) (6) which is derived in [26]."
   电容并入后（p.5）：
   > "To consider the capacitors, R6 is substituted by Z6 , which is the parallel circuit of R6 and C6 ; R8 is substituted by Z8 … This results in the CMRR RC (7) contributed by the resistors and capacitors."
   （CMRR 直接由差分网络的元件失配算出——把电阻失配公式扩展到复阻抗即得频变 CMRR，这就是"失配 → 频域 CMRR"的标准链条。）
5. **实测算得 CMRR ≈59 dB，且由两腿增益匹配残差主导——分频段归因于两步校准**（p.8）：
   > "It can be seen that the CMRR has a constant value of 59 dB up to 10 kHz, increases by a few dB and stays constant up to 1 MHz before it rolls off to 28 dB at 20 MHz. The change of the CMRR at 10 kHz is caused by the two-step calibration procedure; the CMRR up to 10 kHz is dominated by the DC gain calibration, the CMRR at higher frequencies is dominated by the AC gain calibration."
   （**59 dB ≈ P2 的 56 dB 地板量级**：放大器本身算出 80 dB，整机 CMRR 却被两路分压器增益匹配残差压到 59 dB——CMRR = 两腿传递函数失配的直接读数。）
6. **杂散电容用接地屏蔽定形**（p.3）：
   > "Thus it is very difficult to predict a value for CSTRAY . To reach a constant and predictable capacitance CSTRAY a metal shield, which is connected to ground, is assembled around the divider."
   （把不可控寄生变成确定几何量——比例网络稳定性的结构化手段。）

## 关键数值（原文）
- 需求（p.2）："Attenuation flatness – ±0.1 % up to 1 kHz – ±0.2 % up to 100 kHz – ±1 % up to 1 MHz – −3 dB bandwidth of at least 10 MHz"；差分 1 kV、共模 >1 kV、DC 输入阻抗 ≥4 MΩ、衰减 40 dB（100×）。
- 商用探头实测（p.2）："they have a gain flatness of 1 % up to only 50 kHz"；"the SI-51 which is classified as a high-accuracy probe, shows the worst behavior; the probe's gain changes about 0.5 % over the whole input voltage range"；Tek P5205A "has a gain error of 1 % at 50 kHz and a non-linearity of 0.3 % up to 1 kV"。
- 商用探头 CMRR 表（p.2 Table I）：SI-9001 86 dB@50 Hz / 66 dB@20 kHz；SI-9002 80@50 / 60@20 k；SI-51 90@60 / 55@1 M；SI-9110 80@60 / 50@1 M；P5205A 80@DC / 60@100 k。
- 分压器（p.3）：N1 = 4 块；R1 = 1 MΩ 金属膜 ±5 ppm/K；"This results in a maximum linearity error of 81 ppm due to self-heating at the maximum input voltage."；分压器按 54 dB 衰减设计（放大器前留裕量）；>50 MHz 由 RDAMP+RLP/CLP 低通阻挡。
- 杂散（p.3）：矩形同轴近似公式（Eq.3，Chen 1960）算得比杂散电容 "a specific stray capacitance C′ of 105 pF/m"。
- 差分放大器（p.5）：增益 GC = 5；"The calculation results in a worst case CMRR for the difference amplifier of 80 dB up to 10 kHz. Further the CMRR decreases to 77 dB at 100 kHz, 64 dB at 1 MHz and 44 dB at 10 MHz."（Eq.8：1/CMRR ≈ 1/CMRR_RC + [1/CMRR_OPAMP(0)]·(1 + f/fc)）
- 实验结果（p.6–8）：非线性 250 ppm（50 V–1000 V 满量程）；校准装置 "60 ppm gain flatness and less than 1◦ phase shift up to 20 MHz"（三电阻串联替代 5 kΩ 降寄生）；上升时间 19 ns（0–500 V 阶跃，Eq.13）；噪声 E_PROBE = 582.1 µV（20 MHz 带宽），SNR = 81.7 dBFS；CMRR 59 dB@≤10 kHz → 28 dB@20 MHz；单通道物料成本约 600 $。
- 降额（p.8）："the maximum input voltage of 1.5 kV may be applied up to 700 kHz, 1 kV may be applied at 1 MHz and finally a 20 MHz signal must not exceed 80 V."（限 C1 温升 20 K、RDAMP 0.25 W）

## 对 P1/P2/P3 的对照
- **P1（消去条件）**：相关度**中**。全文不涉 SC ΣΔ/抗混叠，但给出了两条 P1 同构机制的一级工程证据：①补偿分压器的平直条件 Eq.2 = 跨支路 R·C 元件匹配（τ 匹配）的充要形态；②频变 CMRR 由复阻抗失配（Eq.6→7）给出——把 Pallas-Areny 电阻失配 CMRR 公式换成 Z=R∥C 即覆盖全频段，说明"失配 → CMRR"链条在频域天然成立，与 P1 的 H_N−H_P≠0 残差框架一致。另一可引点：单级补偿后仍余 0.1 dB（≈1%）@10 kHz（p.4："It can be seen that there is still a deviation of −0.1 dB (approximately 1 % gain flatness) at 10 kHz in case of compensation"），必须引入第二级校正网络逐频抵消——**多级串联时单级元件条件不足以达成总链路平坦**，与 P1"多级梯形不再充分"的方向一致（此处是增益平坦而非共模消去，论证时须注明对象差异）。
- **P2（Kelvin 结构地板）**：相关度**中高**。整机 CMRR 59 dB 落在 P2 的 ≈56 dB 地板量级：放大器级 80 dB（0.025% 阵列电阻）却救不回两腿分压器 ±0.1% 增益匹配残差（0.1% ≈ 60 dB）——**CMRR 被"两腿各自传递函数的匹配精度"封顶**，且实测明确分频段归因于 DC/AC 两步校准。这是"结构（差分对）给定后，地板由匹配工艺决定"的定量实例。注意其结构是双分压器+差放（有源），不是 Kelvin 四端连接，引用时应作为"匹配地板"旁证而非 Kelvin 结构本体。
- **P3（衰减可达上界）**：相关度**低**。仅有输入电压降额曲线（功率限制），与 P3 的衰减上界无关。
- **killRisk 判断：无威胁**。对象（PWM 电驱差分探头）与 P1 主张域（SC ΣΔ 输入网络消去条件）不重叠；其"多级校正才达平坦"现象方向上支持 P1 多级主张，不构成竞争。

## 没读到的
- Fig.5 电路图中 R3–R8、C4/C6/C8 的具体取值（图 pdftotext 不可读，正文未列全）。
- CMRR 实测曲线的中间频点数值（Fig.18 仅题注文字）。
- [26] Pallas-Areny & Webster 1991 的推导细节（本文只引公式）；IEEE 定稿版的页码（本 PDF 为 early access 版，页码待核）。
