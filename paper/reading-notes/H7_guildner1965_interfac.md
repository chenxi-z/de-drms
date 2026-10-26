# 精读笔记 · Guildner & Edsinger 1965《NBS 气体温度计 II：用变压器比例臂桥测量对地电容》（J. Res. NBS 69C(1): 13–18）

> 格式标准（全组沿用）：出处 → 核心命题（原文引用）→ 关键数值（原文）→ 对 P1/P2/P3 的对照 → 没读到的。
> 读法：pdftotext 全文逐节读，引用一律原文加页码；不转述成模糊话。
> 页码说明：PDF 1–6 页 = 期刊印刷页 13–18；下引页码为**印刷页**。原文是 1965 年扫描件，OCR 双栏交错/断词多；**全部关键引文已逐句与 150 dpi 页面图像核对**（OCR 误识如 "creatcs"→"creates" 按印刷件改正），措辞以印刷件为准。

## 核心命题（原文）

1. **【答①·匝比给电压比】** "it has a special elegance in the ability to produce voltages in ratios which are very precisely the turns ratios of the transformer secondary windings. Thus a decade system or any other ratio of integral numbers within the limits of a practical number of turns may readily be established."（p.13，印刷件为 "turns ratios"）
2. **【答①·比例精度来源=紧耦合绕组】** "The special construction of the transformer gives two voltages at E1 and E2, opposite in phase and of a fixed voltage ratio within a part per million of the turns ratio. This is accomplished by the use of tightly coupled secondary turns wound on a large toroidal core of high permeability tape."（p.14）
3. **【答①·匝比=阻抗比？】** 本文不写显式平衡方程（无 Zx/Zs = N2/N1 之类印刷公式），平衡以**等值替代**操作给出："For equal ratio arm voltages two nominally equal and highly stable standard capacitors are then placed in the arms of the bridge. The capacitance value of one is decreased to be equal within 1×10⁻⁵ pF of the value of the other by removal of a small area of the plate of the capacitor. A check of both the equality of the ratio arms and the equality of the capacitors is made by interchanging the capacitors in the arms."（p.17）即：臂电压比=匝比 ⇒ 零位时 C1=C2（ω 在桥方程里两边同因子约掉），但**这一步推理是读者补的，原文只给操作**。
4. **【答①·与频率无关的证据句】** 全文**没有** "independent of frequency" 字样。可引的证据只有三句：①比值由匝数几何决定（上 #1/#2）；②固定单频工作："The transformer is operated at a frequency of 1000 Hz with 40 V on the primary, which gives approximately 12 V across the secondary windings in series."（p.14）；③精度锚在匝比而非元件："The ratio of the secondary voltages of the transformer used in the configuration described by Thompson is equal to the turns ratio within 1 or 2 parts in 10⁷. The modified bridge configuration loses this desirable feature because of the voltage produced on the secondary shield."（p.16）——注意失真源是**屏蔽层感应电压**，不是频率。真正的"频率无关/相关"对照句在 Hall 通史（Wien 桥 "the balance equation of Wien's bridge is frequency dependent"，p.10），两篇合看才成证据链。
5. 三引线电容+拓扑消寄生（不靠匹配）："The properties of 3-lead capacitors [5,6] made it possible to define precisely small changes of capacitance (1×10⁻⁵ pF) in this system. The bridge circuit, shown in figure 1, eliminates the detection of parasitic capacitance, so that additional capacitors can be switched into the circuit in parallel with a reproducible and calculable effect."（p.14）
6. **【答④·全文最接近 P1 的先例】屏蔽层交叉电容失配 → 检流计净电流 → 几何微调消去**："Because of equal voltage between A and C and between B and D, only those capacitances between A and D and between B and C are important. A difference in the value of these capacitances creates a net current through the detector. A provision to reduce the current flow to zero by adjustment of these capacitances was made by the construction of a threaded ring attached to the inner wall of the primary shield."（p.15）失配产生寄生信号、匹配/调对称使其归零——**机理同族，但对象是桥内屏蔽寄生电容，不是 RC 差分梯形，也没有 CM→DM 语言**。
7. **【答④·对称负载电容部分补偿】** "The capacitances, C3 and C4, between this shield and the transformer leads, are shunts which load both the leads and the ratio-arms, but are not detected as part of the measured capacitance. These capacitances are kept small external to the transformer and of approximately equal value so that the voltage drop in the lead of either secondary ratio arm, because of this additional loading, is less than 1 part in 10⁷, and is partially compensated as well by a similar shunting capacitance on the lead of the other ratio arm."（p.14）——"两臂对称寄生互相抵一部分"的显式表述。
8. 电导（损耗）也要配平："In almost all a-c bridges, means must be provided to balance out the resistive component of the system as well as the capacitive component in order to obtain a true null."（p.15，配平网络系 Thompson [6]，本文只取 1 kHz 简化版）
9. **谱系锚点**：本文把 3-lead 变压器比例臂直接溯源到 Blumlein 专利——"the recognition of the value of transformer ratio-arm bridges using 3-lead capacitors. [1,2,3,4]"（p.13），参考文献 [1] = "A. D. Blumlein, British Patent No. 323037"（p.18）。变换器设计"based on a suggestion by R. D. Cutkosky"（p.14）。

## 关键数值（原文）

- 工作点：**1000 Hz、初级 40 V、次级串联合计约 12 V**（p.14）
- 匝比：次级 1:1，附加抽头给第二比例 4:3（p.14）；Thompson 接法下次级电压比=匝比 **1–2 parts in 10⁷**（p.16）；本改型因屏蔽电压损失该精度（p.16）
- 绕组/铁芯：初级 132 匝 AWG15 铜线；次级各 20 匝、0.025 in 铜片铆焊螺旋、0.0075 in Teflon 匝间绝缘；铁芯 0.002 in Supermalloy 3 带绕环，4.5 in 外径 / 3 in 内径 / 1.5 in 高（p.14）
- 负载容差：C3 与 C4 相差 ≤1000 pF 仍保电压恒定（p.14）；单臂附加负载压降 **< 1 part in 10⁷**（p.14）
- 分辨与标准：电容变化可定义到 **1×10⁻⁵ pF**（p.14）；标准电容 **8.205 pF**（熔石英镀金膜），靠去除非极小面积把两电容配到 1×10⁻⁵ pF 内，互换检验比例臂（p.17 及脚注 4）
- 屏蔽问题量级：每道屏蔽缝隙电压 ≈ 初级电压的 **0.8%**（p.15）
- 稳定性："over a period of several months... the standard capacitors have remained equal in value (within 1×10⁻⁵ pF), and the shield cross capacitances have not changed sufficiently to introduce a significant error."（p.17）
- 应用精度：水银气压计——上池极间距约 800 µm、桥零位时下池间距差 ≤1 µm，上池间距变化 <2 µm 则压力对应一致到 **5 mµ（millimicron）**，检测系统总压力误差 "in the millimicron range"（p.17–18）；金属管内径测量：标称 0.8 mm、不确定度 **6×10⁻⁵ cm**（p.18）

## 对 P1/P2/P3 的对照

- **P1（失配消去条件）**：④ 结论 = **三篇中无**"无源 RC 差分梯形失配→CM 转 DM 消去条件"（本文 grep mismatch/common-mode/ladder 零命中）。本文 #6/#7 是历史最近邻：**寄生电容失配→检零电流→对称化/几何微调归零**，且 #7 明文"两臂近似等值 + 对称寄生部分补偿"。P1 写作时可作"前 P1 时代消差手段"引用，但必须点名差异：桥臂寄生失配（集总、单频、无共模概念）≠ 差分 RC 网络失配致 CM→DM 转换（分布、频率相关）。
- **P2（Kelvin 地板/结构类）**：整篇就是端子结构问题——被观测水银面/金属管**必须接地**，于是三引线电容、三轴电缆、双屏蔽、内屏蔽实心化（"The use of a solid inner shield was found to be necessary to eliminate errors caused by the detection of parasitic capacitance"，p.14）成为主题。寄生由**拓扑**（3-lead + guard）解决而非元件匹配，与 P2"结构类不同则匹配救不了"同族，是 P2 的好引文。
- **P3（AAF 衰减上界）**：无。

## 没读到的

- Thompson 1958（IRE Trans. I-7, 245，ref [6]）的电导平衡网络原文——本文只写 "described by Thompson [6] and others"（p.15）；
- Blumlein 专利 323037 原文（仅见于参考文献表，p.18）；
- 可计算 1 pF 电容核查美国电学单位的细节（ref [6][7] McGregor et al. 1958，正文一句带过，p.13）；
- 显式平衡方程与图 1 等效电路各寄生电容（C3–C6）的数值——原文均未给；
- 论文发表/收稿日期细节仅 "(September 4, 1964)" 收稿标注（p.13）。
