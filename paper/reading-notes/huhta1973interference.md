# 精读笔记 · Huhta & Webster 1973《60-Hz Interference in Electrocardiography》（IEEE Trans. Biomedical Engineering, BME-20(2):91–101）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。

## 出处
- Huhta, J. C.; Webster, J. G., "60-Hz Interference in Electrocardiography," *IEEE Trans. Biomedical Engineering*, vol. BME-20, no. 2, pp. 91–101, Mar. 1973. DOI: 10.1109/TBME.1973.324169。
- PDF：`fulltext/H2-差分CMRR/huhta1973interference.pdf`（11 页，正文 pp. 91–101；末页拼有下一篇 Samaun et al. 文章开头，勿混入）。bibkey：`huhta1973interference`。
- 主题：ECG 记录中 60 Hz 干扰的来源分类（磁感应 / 位移电流入导线 / 位移电流入人体 / 设备互连与缺陷）、逐项"描述–测试–对策"流程、放大器设计准则（输入阻抗、CMRR、频响）。

## 核心命题（原文）
1. **干扰换算成差模的统一判据是"电极阻抗不平衡 × 位移电流"，纯共模本身无害**（p.93）：
   > "VA - VB = Z1lDI  Z2ID2 -            (6)   If ZJID1 = Z2ID2, the interference from this factor will be zero.   Either an electrode impedance unbalance or unequal values of displacement current into the leads can cause interference."
   （即 V_A−V_B = Z1·I_D1 − Z2·I_D2；乘积配平则该因素干扰为零——这是**单频点、电阻性**的消去条件，不是滤波器传递函数的消去。）
2. **等位移电流近似下，干扰正比于阻抗差 Z1−Z2**（p.94）：
   > "Making the valid assumption that ID, = ID2 = ID (except when an ac source is very near one lead and not the other), we can calculate the interference potential assuming a 5000-Q elec-trode impedance unbalance:  Vac = VA - VB = ID(Z1 - Z2)                (7)"
   （6 nA × 5000 Ω = 30 µV ≈ ECG（1 mV）的 3%。）
3. **共模电位经输入阻抗分压器转化为差模（"potential divider effect"），等效 CMRR 由系统决定而非仅放大器**（p.97–98）：
   > "A severe unbalance in the electrode impedances or the input impedances will cause this potential to be higher at one input than the other. We will call this phenomenon the potential divider effect [13]."（p.97）
   > "It should be obvious that we must specify the input imped-ance   and the CMRR of an amplifier. Any unbalance in the electrode impedances will reduce the "effective" CMRR because of the potential divider effect, but we will treat these variables independently."（p.98）
4. **输入阻抗不是无穷时，即使电极阻抗平衡、输入阻抗不平衡也会转换**（p.97）：
   > "Even if Z1 = Z2 = 10 kQ. (electrode impedances balanced) we can have problems. If Zi'n = 5 MQ and Zi'n = oa (input impedances un-balanced), we can calculate how much interference will result with a VCM of 10 mV:  VA - VB = VCM [ I]VCMO.O2.    (19)"
   （一对 5 MΩ/∞ 失衡输入阻抗 + 10 kΩ 源阻抗 → 2% 干扰；即 Zin 需 ≫ 源阻抗。）
5. **前置跟随器自身的增益失配本身就是新的 CM→DM 途径**（p.99）：
   > "could introduce more interference than they eliminate if the potential gain of one were slightly different than the other. Assuming a CM potential of 10 mV, a pair of these preampli-fiers mounted at the electrodes or on the equipment should be matched to 0.1 percent to meet our 1-percent interference criteria."
   （双通道缓冲增益须配到 0.1%——与 P1 关心的"两条支路传递函数之差"是同一物理量 H_N−H_P 的单频幅度版本。）
6. **总干扰=五项线性叠加的总结式（磁感应 + 导线位移电流 + 体内位移电流 + CMRR 项 + 分压器项）**（p.100）：
   > "Interference can be described by the equation  Vtot= [KBS +ID1Zl - 1D2Z2 +K'IDZI + DG -  +   in , -i    (27)"
   （式中各项分别标注 magnetic induction / ID in leads / ID in body / CM potential ac CMRR factor / potential divider effect——本文的"系统性 CMRR 框架"总纲。）

## 关键数值（原文）
- 判据：ECG ≈ 1 mV，1% 容限 = 10 µV（p.91："One percent of 1 mV is 10 pV."，原文扫描版 µ 作 p）；EEG 50 µV → 容限 0.5 µV（p.92）。
- 磁感应：峰值感应电位 = K·B·M·S；实测斜率约 120 µV/m² 环路面积，B ≈ 3.2×10⁻⁷ Wb/m²；容限环路面积 <0.1 m²（约 30 cm×30 cm）（p.92–93）。
- 位移电流：3 m 长 20 号未屏蔽导线最差拾取 6 nA；接地体靠近可降 80–90%（p.93–94）。
- 电极–皮肤阻抗 60 Hz 下 1 kΩ–100 kΩ，干扰来自两者**不平衡**（p.94）。
- 共模电位：VCM = I_D·Z_G，最大 1 µA×100 kΩ = 0.1 V（AHA 同值），典型 1–10 mV（p.95）。
- 体内阻抗：躯干约 20 Ω，肩–指最高 400 Ω；V_ac = Z_I·I_D，0.1 µA 时 Z_I = 100 Ω 即达 10 µV 容限（p.95）。
- 输入阻抗要求：Zin ≥ 5 MΩ @60 Hz（ZCM = Zin/2 = 2.5 MΩ），对 10 mV VCM 与 5000 Ω 不平衡；威尔逊中心端平均网络情形需 >111 MΩ（p.97–98）。
- AHA 1967 规格：输入阻抗 500 kΩ；CMRR 1000:1（45–65 Hz、5000 Ω 失衡）；频响 ±0.5 dB 0.14–50 Hz 等（p.96）。
- 放大器最小规格建议：差分输入 400 kΩ / CM 输入 2.5 MΩ / CMRR 60 dB @60 Hz 含 5000 Ω 失衡（p.98，式 25：10×10⁻³/10×10⁻⁶ = 1000 → 60 dB）。
- 380 pF 并联电容把 7 MΩ 输入电阻在 60 Hz 降到 5 MΩ 有效值（p.97）。

## 对 P1/P2/P3 的对照
- **P1（消去条件）**：相关度 **中**。给出的是**单频（60 Hz）、准静态电阻性**的消去条件（Z1·I_D1 = Z2·I_D2；分压器比相等），无 s 域传递函数、无频率响应、无多级网络——**不触及"多级无源网络全频段精确消去"**。可作 P1 的历史引言级引用（"CM→DM 转换 = 两支路不平衡"这一表述的系统级源头之一）。
- **P2（Kelvin 结构地板）**：相关度 **低**。无 Kelvin/四线结构讨论；其"把电极靠近放置以减小体内阻抗差"与"驱动右腿降低 VCM"属系统层对策，非引线结构地板。
- **P3（平坦度–衰减上界）**：相关度 **无**。全文无滤波器综合/频响权衡的积分约束内容；频响仅作为放大器规格（0.05–100 Hz）出现。
- **方法学（D1–D10 增量四）**：相关度 **中低**。其"描述–测试–对策"三分流程与式(27)五项分解是经典的"机制分桶归因"方法，与增量四的逐项对照思路形式同构，但无参数增量实验。
- **killRisk 判断**：**无威胁**。1973 年临床仪表教程式论文，无 s 域 G_DC(s)=H_N−H_P 表述、无多级梯形消去条件、无 Scd21 之类形式化；仅提供"不平衡即转换"的共同出发点。

## 没读到的
- 无任何频域/复频域（s 或 jω）网络分析——全文只在 60 Hz 单频点讨论。
- 无差分滤波器/抗混叠滤波器的 CMRR 退化分析（输入电容只作为输入阻抗退化因素提及）。
- 无 CMRR 随频率变化的定量曲线（仅一句"The frequency at which the CMRR is measured must be specified because it is a function of frequency."，p.98）。
- 式(14)(18)(26)等在扫描版中数学排版残缺，数值结论以文字叙述为准；如需精确式子须核对 IEEE Xplore 重排版。
