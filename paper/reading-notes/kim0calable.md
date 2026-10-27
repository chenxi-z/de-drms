# 精读笔记 · Kim 2006《Scalable Delta-Sigma Modulator Readout Architecture for Array-based Sensor System》（ISCAS 2006, pp.1925-1928）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> **H5 轴判定先行**：本文是 **ΔΣ 阵列的数字后端（并行位串行 FIR 抽取滤波器）架构**论文，不含输入采样结构、踢回电流/电荷、外部 RC 或建立时间的任何内容——对 H5 轴（输入踢回/开关电容负荷/建立）**基本不相关**，疑归档错轴；仅有"模拟/数字电路地理隔离防数字噪声耦合"一句沾边。

## 出处
- Daeik D. Kim (IBM Semiconductor R&D Center), Martin A. Brooke (Duke University), "Scalable Delta-Sigma Modulator Readout Architecture for Array-based Sensor System", *Proc. IEEE ISCAS 2006*, pp. 1925–1928. DOI 10.1109/iscas.2006.1692987。
- bibkey: `kim0calable`；全文 PDF：`fulltext/H5-kickback/kim0calable.pdf`（4 页，会议页 1925–1928，下引页码=会议页）。
- 主题：面向大规模 ΔΣ 调制器阵列的一对一位串行 FIR 抽取滤波器阵列（0.18 µm CMOS）。

## 核心命题（原文）
1. **位串行 FIR 一对一映射到 ΔΣ 阵列，转换与读出同时进行、帧率翻倍**（p.1925）：
   > "The proposed architecture provides a simultaneous readout and conversion, and it doubles effective frame rate of the data conversion system by eliminating the two-step conversion then readout phases."（架构主张：省去"先转换后读出"两相交替，靠系数移位让相邻滤波模块流水。）
2. **位串行是压缩面积/可模块化的必要选择，代价是位时钟复杂与字处理速率下降**（p.1926）：
   > "The bit-serial arithmetic design is an indispensable choice to reduce the filter layout size and to make it modular and scalable, while it has several disadvantages, such an increase in bit-clock signal complexity and a reduction in maximum operation speed with regard to the word-processing rate."（数字后端权衡，无模拟内容。）
3. **模拟/数字地理分离、防数字噪声耦合是阵列传感器系统的普遍做法**（p.1926，全文唯一与 H5 沾边处）：
   > "It also assumes that sensors and the delta-sigma modulators, or analog circuits are geographically separated from digital filters, or protected from digital noise coupling by several design measures [2], [13]."（仅为假设条件陈述，未给耦合量/隔离度数值。）
4. **面积效率对比：位串行在 N=256 时帧率/面积优于字并行复用**（p.1926，Table I）：
   > "As the array size increases, the readout frame rate of the single multiplexed word-parallel filter decreases with the same circuit area. The proposed bit-serial design maintains the same readout frame rate, while the circuit size increases."（N=256 时 Eb=1.34×10¹² vs Ep=8.51×10¹¹ F/s·µm²。）
5. **原型实测口径（版图提取+HSpice 全电路仿真）**（p.1928）：
   > "A prototype filter array and coefficient generator was demonstrated in 0.18,um CMOS technology, and the maximum sample rate was about 95MSamples/sec with 1.45MHz bit clock rate."（注意：正文 IV 节写 fb=1.45 GHz，此处"1.45MHz"疑为原文笔误或 OCR 误读，**待核**；95 MS/s 与 W=15 位字率 96.7 MHz 一致。）

## 关键数值（原文）
- 255 抽头 FIR；最大 95 MSamples/s；256 模块阵列 377 kFrames/s；模块尺寸 145 µm × 7.45 µm、约 290 晶体管（p.1925/1928）；系数发生器约 720 晶体管、<90 µm × 60 µm（p.1928）。
- fb = 1.45 GHz（位时钟）、W = 15 bits、字率 fw = fb/W = 96.7 MHz；加器进位传播延迟 <2 nsec，字周期约 10 nsec（p.1928）。
- 抽取器 SNR（L=255，一阶 ΔΣ 样本，Table II，p.1927）：二阶梳状 60.42 dB / 9.74 bit；理想次优 62.07 dB / 10.02 bit；量化次优（256 级）61.98 dB / 10.00 bit；非线性解码器 72.94 dB / 11.82 bit。设计 ADC SNR 60.53 dB = 9.74 bit（p.1928）。
- 面积对比（Table I，p.1926）：字并行 Ap = 180×140 µm²；位串行 Ab·N+Ac = 145×7.45×N+90×60 µm²；N=256 时面积 21.2×10³ vs 281.9×10³ µm²，帧率 377.9×10³（位串行）等。

## 对 P1/P2/P3 的对照
- **P1（消去条件）**：无任何讨论（纯数字后端）。相关度：无。
- **P2（Kelvin 结构地板）**：无。相关度：无。
- **P3（衰减可达上界）**：无滤波器衰减上界理论（梳状滤波器仅作资源/性能取舍的对象）。相关度：无。
- **方法学（D9/D5/C9）**：**无-低**。唯一可引用点：阵列传感器系统中"模拟前端与数字电路地理分离/防数字开关噪声耦合"是公认设计措施（p.1926，引 [13] Blalack & Wooley ISSCC'95 关于开关噪声对过采样 ADC 的影响）——若 P1 增量四需要文献支撑"数字翻转噪声不能耦合进模拟前端"，可把本文引用的 [13] 作为线索，但本文本身无数值。
- **killRisk**：无。本文不涉及 P1/P2/P3 任何主张的边界。**建议：此篇在 H5-kickback 轴下价值极低，归档时或应移入"H-数字后端/阵列读出"类目。**

## 没读到的
- **完全没有**：输入采样结构、踢回电流/电荷数值、外部 RC 取值、建立时间口径——H5 轴四个关注点全部缺席。
- 模拟前端（ΔΣ 调制器本身）的设计细节全部略过（"simple 1st- or 2nd-order modulators have been adopted due to the circuit size restriction"仅一句带过，p.1927）。
- 无芯片实测（硅实测）数据，性能均为版图提取后 HSpice 仿真；Table I 中字并行帧率一栏 OCR 损（"4i3"），**待核**。
