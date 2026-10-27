# 精读笔记 · Kumngern 2011《Voltage-Controlled Floating Resistor Using Differential Difference Amplifier》（ICEEI 2011）

> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。

## 出处

- 一作：Montree Kumngern（KMITL, Bangkok）。会议：2011 International Conference on Electrical Engineering and Informatics（Bandung, Indonesia），pp. 1–4，DOI 10.1109/iceei.2011.6021811。
- PDF：`H2-差分CMRR/kumngern2011oltageco.pdf`，4 页，pdftotext 清晰（作者英文多有语法瑕疵，引用一律原样保留并标[原文如此]）。
- 主题：用 1 个 DDA（Sackinger 型）+ 4 管 MOS 实现电压控制浮地电阻：非饱和区 MOS 做浮地线性电阻，DDA 求和 + MOS 二极管分压（MD1–MD2 cascode）消去非饱和 I/V 的二次项 (K/2)(VDS)²，控制电压 VC（由电流源 IC 经 PMOS 源跟随生成）调阻值。

## 核心命题（原文）

1. **消去的对象是非线性项，手段是对称求和+半压分压**（p.1 摘要 / p.2 正文）：
   > "The DDA and the MOS transistor voltage divider are used for canceling the nonlinear component term of MOS transistor in the non-saturation region to obtain a linear current/voltage relationship."
   （p.2 给出消去的代数条件：）
   > "From equation (2), the component term Kn{(VD1+VS1)/2} should be eliminated to obtain a linear current/voltage (I/V) relationship."
   （式(3)要求栅压精确等于两端电压均值加控制量：VGS1 = (VD1+VS1+VB)/2 + VC——**对称平均驱动 → 项消去**，与 P1 的 H_N−H_P 对称对消在结构上同型，但对象是器件非线性项而非网络 DC 增益。）
2. **元件条件的表述（全文最接近「元件条件」的一句）**（p.3）：
   > "Note that the MOS transistors in the voltage divider MD1–MD2 do not need to have specified conditions, but only the same characteristics."
   （分压管无需指定值、只需**同特性**——即匹配充分性主张，但只对分压器这一级；此外式(13)推导默认 NMOS/PMOS 跨导参数相等：）
   > "Letting Kn=Kp=K, equation (12) can be rewitten as"（p.3，[原文如此]"rewitten"）
3. **温度消去主张与其残余**（p.2 / p.3 / p.4）：
   > "Also, it can see from equation (5) that the circuit can be realized the resistance without temperature effect in term of the threshold voltage."（p.2，[原文如此]；VB=2VTn 使 VTn 从式(5) R_DS1=1/(Kn·VC) 中约掉）
   > "the temperature effect that includes in term of threshold voltage (VTp) is slightly changed the resistance value."（p.3；控制电压生成管 MD 侧的 VTp 经式(11) VC=2IC/Kp+VTp 重新进入式(13) R_DS=1/(2K·IC+K·VTp)）
   > "evaluates that the resistance error is about 15.9% when the temperature change from 0°C to 100°C. It is the effect of the transconductance parameter (K=μCoxW/L) that dominant parameters of the circuit which appears in equation (12)."（p.4；残余温漂归因于 K，非解析灵敏度推导、仅为归因断言+仿真数值）
4. **线性度与动态范围的前代局限**（p.1）：
   > "The limitation of these reported circuits is suffered from the narrow input voltage range (≈26mV)."
   （对 OTA/本征电阻类 VCR 的 ≈26 mV 线性范围批评——本文卖点是非饱和 MOS+消去后线性范围扩大到 VDS 扫至 2 V。）
5. **线性工作区的解析门槛**（p.3 式(6)(7)）：
   > "VGS1 > VDS1 − VTn"（式(6)，非饱和判据）→ 由此得最低控制电压 VC(min)=VDS1/2（式(7)）、最大等效电阻 R_DS1(max)=2/(Kn·VDS)（式(8)）——一个明确的"线性区成立条件→参数下限"解析链。

## 关键数值（原文）

- 工艺/电源：PSPICE，0.5 μm CMOS（MIETEC 模型），±2.5 V（p.3）。
- 管子尺寸：MR 25 μm/6 μm（"The effective channel length of MR is 6μm to avoid the channel length modulation effect [6]"，p.3）；MD1/MD2 各 2 μm/2 μm；MC 25 μm/10 μm；DDA 内 M1–M4 1.6 μm/1 μm、M5/M6 8 μm/1 μm、M7 20 μm/1 μm；偏置 IQ1=72 μA、IQ1=145 μA（p.3，[原文如此]两处均写 IQ1）；偏置电压 0.65 V。
- 仿真点：VDS 扫 0–2 V；VC(min)=1 V；IC(min)≈80 μA（K≈161 μA/V²）；最大线性度误差 13.5% @ IC=100 μA（p.3）。
- 温漂：IC=600 μA、VDS=1 V，0 ℃→100 ℃ 电阻 0.9 kΩ→1.12 kΩ，电阻误差 ≈15.9%（p.4）。
- 晶体管总数：11 管（"the proposed circuit consists of 11 transistors and can be fully integrated in CMOS technology"，p.3）；对比文献[8][9]分别 20、17 管（p.1）。

## 对 P1/P2/P3 的对照

- **P1（消去条件 G_DC=H_N−H_P≡0 的元件条件；单级 τ=R·C 匹配充要）**：不构成占位。本文有「理想消去需要元件条件」这一**同属模式**（分压管"only the same characteristics"、Kn=Kp 假设、式(3)精确均值驱动），但①消去对象是 MOS 器件二次非线性项，不是差分无源网络的 DC 增益；②**没有失配→误差的解析灵敏度式**（只有理想条件+仿真误差数值）；③无采样/开关电容/AAF 语境。P1 的空缺主张（元件失配→共模/误差的解析条件，及单级匹配的充要性证明）**未被本文触及**。写 P1 时可将本文作为"消去-条件模式在连续时间有源电路的又一例证"引用以示普遍性，属低威胁。killRisk：**无威胁**。
- **P2（Kelvin 结构地板 ≈56dB）**：无交集——"floating"指电阻两端皆浮动，全文无共模定义、无 CMRR、无噪声地板。killRisk：无威胁。
- **P3（平坦度约束衰减上界）**：无交集（无滤波器幅频/衰减讨论；其"linear"指 I/V 线性度非幅频平坦度）。killRisk：无威胁。
- **方法学（D1–D10 门槛化）**：弱相似点仅有式(6)→(7)→(8)的"成立条件→参数门槛"解析链（线性区判据推出 VC 下限），与 D 系列的门槛化精神同向但对象为器件工作区，非仪器指标方法学。killRisk：无威胁。

## 没读到的

- 全部结果为 PSPICE 仿真，无实测、无芯片；失配情形（如 Kn≠Kp、MD1≠MD2）从未被单独仿真或解析——这正是 P1 想填的空缺，本文侧面印证其空缺真实存在。
- 式(1)(2) 的来源标注为 [11]（Razavi 教材）、DDA 定义 [10]（Sackinger & Guggenbühl 1987，本库 H 系已有相关脉络），原始推导未在本文展开。
- Fig. 1–7 为矢量图，pdftotext 无法提取曲线数值（仅有正文给出的 13.5%/15.9%/0.9–1.12 kΩ 等点值）。
