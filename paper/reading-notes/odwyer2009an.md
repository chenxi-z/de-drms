# 精读笔记 · O'Dwyer 2009《An enhanced model for thin film resistor matching》（IEEE ICMTS 2009, pp. 45–49）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> 说明：PDF 5 页对应刊页 45–49（PDF p.1 = 刊 p.45）。文本层 OCR 有上标丢失（10 的幂次），下文两处常数已用文中「22 squares」判据交叉验证还原，注明于关键数值节。

## 出处
O'Dwyer, T. G., Kennedy, M. P. "An enhanced model for thin film resistor matching", 2009 IEEE International Conference on Microelectronic Test Structures (ICMTS), pp. 45–49. DOI: 10.1109/icmts.2009.4814608.（Analog Devices Inc. / University College Cork, Tyndall）
全文：`fulltext/H2-差分CMRR/odwyer2009an.pdf`

## 核心命题（原文）
1. **匹配仍是技术性能瓶颈（动机）**（p.45）：
   > "Matching of transistors, capacitors and resistors is still a technology performance limit in applications such as Nyquist analog-to-digital converters (ADCs), and digital-to-analog converters (DACs) for level setting applications, as well as precision gain and attenuation circuits."
   （P1 主张的"精确消去依赖元件匹配"所处的工艺现实背景：匹配精度受限于工艺，校准/修调代价高。同页："calibration and trimming techniques … tend to be relatively expensive compared to non-calibrated circuits in terms of silicon area, device calibration time, and the use of expensive equipment such as laser trimmers."）

2. **增强失配模型：长度刻蚀项 + 面积（Pelgrom）项**（p.47）：
   > "Thus, we have derived a mismatch model (7) for rectangular resistors which depends on six process parameters, as well as the chosen geometry parameters, L and W."
   > "In effect, the linear model [4] only accounts for variations in film uniformity, while the model in (7) also takes account of the effects of etching on the length and width edges."
   （式 (7)：σRm² = (σL)²/[L+ΔL]² + (σW)²/[W+ΔW]² + (σpu)²/[ρp²(L+ΔL)(W+ΔW)]，因子 2 来自"对失配取标准差而非绝对值"。即失配由三项构成：长度刻蚀、宽度刻蚀、薄膜电阻率均匀性。）

3. **长度项主导时宽度不影响匹配——与朴素 Pelgrom 相反**（p.48）：
   > "Thus, the dominance of one term over the other simply depends on the target resistance value. For resistances significantly beyond that defined in (12), the length term can be neglected, and (10) reduces to the conventional Pelgrom relationship. Conversely, if the resistance is significantly less than shown in (12), the Pelgrom term can be neglected and (10) reduces to a linear relationship with the reciprocal of length. Note that under this latter condition, the width has no effect on matching, which runs contrary to what one would expect with the simple Pelgrom model."
   （判据 L/W > 22 squares：电阻（方块数）大 → 面积项主导（经典 Pelgrom 1/√WL）；电阻小 → 长度刻蚀项主导（1/L），加大宽度不再改善匹配。）

4. **测试方法：Kelvin 四线制消除接触电阻影响**（p.45）：
   > "To reduce the effect of contact resistance, pairs of bond pads are used to implement a standard four-terminal (Kelvin) configuration at each measurement point, as shown in Fig. 2."
   （Kelvin 结构在此是**测量夹具**用途——把接触电阻从失配测量中剔除；与 P2 的"Kelvin 结构 CMRR 地板"不是同一对象，但可作为 Kelvin 四线消除寄生影响的独立旁证。）

5. **面向设计的图形/解析方法学**（p.48–49）：
   > "To achieve the required mismatch target, any combination of W and L above the locus will suffice. … the optimum combination of W and L is located at the intersection of the constant resistance line and the required maximum mismatch locus."
   > "The model fit, which has terms that depend on 1/L², as well as 1/WL, yields better agreement with measured data than the simple area model described in [4]."（p.49，结论）
   （给定目标失配（0.4%/0.2%/0.1% ≈ 8/9/10 bit）与目标阻值，可直接图解或解析求最优几何。）

## 关键数值（原文）
- 数据规模（p.46）："approximately three hundred test dice across ten wafers"，归一化基准最小几何 3 µm × 1.9 µm；12 种宽长组合（Table I，p.46）。
- 简化模型（p.47，式 (10)，L、W 单位 µm，归一化数据）：σRm² = 1.02×10⁻³/L² + 4.58×10⁻⁵/(LW)。（原文 OCR 上标缺失，"1.02x103""4.58x10-5"；由 p.48 判据式 (11) "4.58x10⁻⁵/LW > 1.02x10⁻³/L² ⟺ L/W > 22 squares" 交叉验证，两常数应为 10⁻³ 与 10⁻⁵，内部自洽。）
- 项主导判据（p.48，式 (12)）："L/W > 22 squares"。
- 主导误差源结论（p.47）："The estimated ΔL and ΔW terms turned out to be negligible compared to practical geometries in use, and the σW term was also very small."；"the two most significant contributors to the standard deviation of the mismatch error are (a) the statistical variation in the length etching, σL, and (b) the fractional variation in the film thickness or uniformity, σpu/ρ."
- 解析设计式（p.49，式 (13)–(14)）：L = (100/σRm)·sqrt(1.02×10⁻³ + 4.58×10⁻⁵·R) µm，W = L/R µm（R 为方块数，σRm 为目标失配百分数）。
- 目标失配档位（p.48）："only a limited number of target mismatches are required, for example, 0.4% (8 bit), 0.2% (9 bit), 0.1% (10 bit), etc."（Fig. 6 画到 8–12 bit 匹配等高线。）
- 宽度饱和点（p.48）："as the width is increased beyond approximately 0.6 units, the length required to achieve the target matching remains almost constant and is largely independent of width."

## 对 P1/P2/P3 的对照
- **P1（消去条件）**：**中度相关（支撑性，非预占）**。本文不涉及 G_DC(s)=H_N−H_P 或任何差分滤波消去条件的代数结构；但它给出 P1 赖以成立的**工艺统计事实**——R 匹配残差 σRm 的定量模型（1/L² + 1/LW 双项），可直接用于估算"P1 精确匹配条件在真实工艺下偏离多少 → 残余 G_DC 地板多大"。特别是"宽度对匹配饱和"的结论意味着**不能靠无脑加大器件面积换匹配**，这强化 P1 论证里"多级网络交叉项失配不可用面积缩放消除"的现实性。无任何多级网络/交叉项表述，killRisk = 无。
- **P2（Kelvin 结构地板 ≈56 dB）**：低相关。Kelvin 四线制在本文是测量夹具（p.45，剔除接触电阻），不涉及差分结构 CMRR 地板数值；可作"Kelvin 结构用途谱系"的测量侧引用。
- **P3（平坦度约束衰减上界）**：无。本文无滤波器响应/衰减–平坦度内容。
- **方法学（D1–D10）**：可借用其"误差项分解 → 各项物理溯源 → 图解设计区间（等高线 + 定阻线交点）"的门槛化设计方法；与增量四同构之处在于把抽象指标（失配 %）翻译成几何可执行区间。
- **killRisk 判断：无**（不触及全频段精确消去条件；反而是 P1 论证可引用的统计支柱）。

## 没读到的
- 无电容匹配数据（纯电阻对）；P1 需要的 R·C 乘积（时间常数）跨器件类相关失配（R 与 C 失配是否相关）完全未涉及。
- 未给出温度系数失配/长期漂移——P1 残余地板的另两个自由度。
- 工艺细节（薄膜材料、方块电阻绝对值）因"to protect proprietary information"归一化隐去（p.46），绝对数值不可直接迁移（原文自述归一化到 3 µm × 1.9 µm 最小几何）。
- 未见 SPICE/电路级应用实例，模型止步于几何设计。
