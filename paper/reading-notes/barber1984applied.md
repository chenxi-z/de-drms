# 精读笔记 · Barber & Brown 1984《Applied potential tomography》（J. Phys. E: Sci. Instrum. 17, 723）

> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。

## 出处

- 一作：D C Barber（与 B H Brown，Sheffield 大学/皇家 Hallamshire 医院医学物理系）。
- 期刊：Journal of Physics E: Scientific Instruments 17 (1984) 723–733，**REVIEW ARTICLE**（EIT/applied potential tomography 奠基综述之一，Sheffield 系统出处）。DOI 10.1088/0022-3735/17/9/002。
- PDF：`H2-差分CMRR/barber1984applied.pdf`，12 页（PDF p.1 为 IOP 封面页，p.2–12 = 期刊页 723–733；下文页码用 **PDF 物理页**，括注期刊页）。扫描版 pdftotext 有系统性格式损：Ω→R、μ→p/,u、π→n/R、⁻²→-*、下标丢失，引用处逐一标注。
- 结构：§1 引言；**§2 电阻率测量（2.1 两电极制 / 2.2 四电极制）**；§3 体积导体场（Laplace/Poisson 解析+数值+FEM+电阻网络模型）；§4 图像重建（ART/线性化/三维/唯一性）；§5 组织电性质（生物效应/线性/电阻率表）；§6 采集系统（保护电极/多电极数据集/速度与噪声）；§7 在体图像重建；§8 结论。**不是**数值方法教材，也非滤波器文献；§2/§6 与电阻测量硬件直接相关。

## 核心命题（原文）

1. **两电极制的根本缺陷：电极阻抗不可忽略**（p.2，期刊 723，§2.1）：
   > "All two-electrode systems suffer from the disadvantage that electrode impedance cannot be neglected. Conductivity cells utilising only two electrodes have been used for measurements on body fluids such as blood and urine but very great care has to be taken in the cleaning and preparation of the electrodes. A very much more satisfactory system is to use four electrodes where a constant current is applied between the outer pair of electrodes and the resultant electrical potential is recorded between the inner electrodes."
   （两电极被测阻抗里混入电极-组织换能阻抗；四电极（恒流外对+内对测压）为"满意得多"的方案——**两端器件物理上无法四线的场合，此句是必须正面回应的经典论断**。）
2. **电极阻抗的频率特性与测量窗口**（p.2，§2.1）：
   > "Because at low frequencies the resistivity of tissue is constant, the significance of electrode contact impedance can be reduced by making the measurements at the highest possible frequency. At frequencies above about 200 kHz measurement difficulties arise from the effect of stray wiring capacitance and tissue can no longer be regarded as purely resistive. Most tissue resistivity measurements are made at frequencies between 20 kHz and 100 kHz but no systematic study has been published to justify an 'optimum' frequency."
   （接触阻抗随频率下降 → 提频压制其影响；>200 kHz 杂散电容毁掉纯阻性——低频/直流电阻测量恰处接触阻抗最不利端，**与 DE-DRMS 直流恒流方案形成张力，是 P2 类论文必须划界的点**。）
3. **四电极也非免疫：杂散电容旁路与相移**（p.3，期刊 724，§2.2）：
   > "Probably the greatest uncertainty in attaching significance to resistivity values occurs because of electrode impedance. Even with a four-electrode system current flow through stray capacitances and the electrode contact impedances can cause very large errors and apparent phase shifts. Unfortunately very few publications indicate that workers have fully appreciated the problems."
   及（p.3）：
   > "However, stray capacitances of only a few picofarads can give a significant current path a, g, c. d. h. f."
   （几 pF 的杂散电容即可形成显著旁路电流路径（Fig. 1）——Kelvin 结构自身也有地板/误差来源的最早系统陈述之一，**P2（Kelvin 结构地板）主张的域内思想先声，但无任何分贝级量化**。）
4. **接触阻抗是文献电阻率值离散的主因**（p.3）：
   > "Electrode contact impedance probably accounts for the greater part of the differences in published tissue resistivity values."
5. **线性化的成立条件（反问题小扰动假设，非元件消去条件）**（p.4，期刊 725，§3.3）：
   > "The condition for this to occur is that V , is small or equivalently that V R is small, i.e. deviations of conductivity from uniformity are small."［"V ,"="V_p"、"V R"="V_R"，下标提取损］
   （§3.3 对式(6)线性化得 V²V_p=∇V_u·∇V_R，其成立条件是电导偏离均匀为小量；Yamashita & Takahashi 1981 给出 ≤30% 电导变化内线性可用的经验界。**这是"近似成立的解析条件"，与 P1 的元件级恒等消去条件 G_DC=H_N−H_P≡0 不同层**。）
6. **组织线性区的电流密度门槛**（p.6，期刊 727，§5.2）：
   > "Tissue impedance measurements made at frequencies below 100 kHz and at current densities less than 100 A m-2 show no evidence for any significant nonlinearity of resistivity."［"m-2"="m⁻²"提取损］
   另：Witsoe & Kinnen 1967 称肺组织 100 kHz、800 A m⁻² 仍线性；Geddes 1976 除颤放电 16 kA m⁻² 出现电阻率小幅下降；本文结论（p.6）："current densities used in applied potential tomography are less than 1 kA m-* so the assumption of tissue linearity is probably valid."［"m-*"="m⁻²"］
7. **保护电极（guarding）的符号反转陷阱**（p.7，期刊 728，§6.1）：
   > "confirmed that whilst guarding gives an increased sensitivity to resistivity changes within the guarded volume, resistivity changes elsewhere can give an output of opposite sign."
   （Plonsey & Collin 1977 批评 + Smith 1983 电解槽实证：保护区外电阻率变化可致**反号输出**——任何"用约束场来划定敏感区"的测量设计的经典反例。）
8. **唯一性警告**（p.5，期刊 726，§4.3）：
   > "Bates et a1 (1980) and Schneider (1979) have both argued that for configurations similar to those proposed by Pryce (1 979) and Schomberg (1978) for certain patterns of applied voltage there are a variety of conductivity distributions which can give rise to the same pattern of currents flowing through the electrodes."
9. **噪声/建立/采集时间预算方法学**（p.8，期刊 729，§6.3）：
   > "Now the Johnson noise for a 1 kn source impedance (typical for surface electrodes of area 4 mm') and a 50 kHz bandwidth is 0.9,uV."［"1 kn"=1 kΩ、"4 mm'"=4 mm²、"0.9,uV"=0.9 μV，提取损］
   > "If we allow seven time constants for the dwell time, which will allow for settling to 0.1%. then the dwell time is 7QT/n."［"n"=π，提取损；谐调电路带宽 1/Q、对数衰减率 n/Q、时间常数 QT/π——**"7τ→0.1% 建立"门槛的原文出处级表述**］
   > "Seagar concludes that profiles must be defined to an accuracy of 0.2% if a single pixel in the centre of a 1000-pixel image is to be visible."
   （三者合起来是"物理预算→显式数值门槛"的完整范例：噪声预算、建立门槛、精度-可见度门槛。）

## 关键数值（原文）

- 四电极点电极公式（p.2 式(1)）：pdftotext 作 "p = 2RSv/I."——应为 **ρ = 2πS·V/I**（ρ/π 提取损；Wenner 型，S=等间距，I=驱动电流，V=内对电压）；圆盘电极类似式出自 Witsoe 1966（p.2–3，公式本体在提取中丢失，仅存 "where a is the radius of the disc electrodes..." 残句，待核）。
- 频率窗口：常规 20–100 kHz；>200 kHz 杂散电容/位移电流问题（p.2）。
- 生物效应门槛（p.5–6，期刊 726–727）：感知阈 "Currents as low as 100pA can be felt."［μ→p 提取损，按上下文应为 100 μA，待核］；>0.1 Hz 出现电解刺感；>10 Hz 神经刺激主导；>约 10 kHz 加热主导。
- Table 1 电阻率（Ω·m，pdftotext 作 "R m"）：脑脊液 0.65、血浆 0.66、血液 1.5（50% 血细胞比容）、肝 3.5（灌注）/5.5（结扎）、人臂 2.40（纵向）/6.75（横向）、骨骼肌 1.25–1.50（纵）/18.0–23.0（横）、肺 7.27–23.63、脂肪 20.6–27.2、骨 166；表注："note that factors of two or more difference in published values are common."（p.6）。流动血液电阻率随流速 +约 15%（p.7）。
- 肺组织相位角 13°（50–100 kHz）→ 传导/位移电流比 4.3:1 → >50 kHz 不宜视为纯阻性（p.7）。
- Table 2（128 电极圆阵规格，p.8）：50 kHz、带宽 5 kHz（Q=10）、衰减时间常数 QT/π=64 μs、驻留 7QT/π=446 μs、采集时间 57 ms、Johnson 噪声（1 kΩ 源）0.29 μV、最小信号 20 μV、最大信号 ≈100 mV、驱动 1 mA、介质平均电阻率 5 Ωm、直径 100 mm、驱动对张角 11.25°。
- 独立测量数：互易性使 N 电极相邻驱动的独立测量数为 **N(N−1)/2**（p.8）；16 电极 → 120 独立测量（p.8）；128 电极 → 8128 像素 → 分辨率约阵列直径的 1%（p.8）。
- 最小信号标度：相邻驱动下电位梯度 ∝ N⁻²（pdftotext "W 2" 提取损）——实测 32 电极 1 mA 人臂 ≈80 μV，128 电极预期 5 μV；恒定张角驱动下 ∝ N⁻¹，128 电极 11.25° 张角时 20 μV（p.8）。
- 采集速度实例：Jossinet 1981 128 电极 20 s；Brown 1982 16 电极 0.5 s；理论下限 N/f=2.56 ms（128 电极@50 kHz，p.8）。
- 线性化适用界：电导变化 ≤30%（Yamashita & Takahashi 1981，p.4）。

## 对 P1/P2/P3 的对照

- **P1（消去条件 G_DC=H_N−H_P≡0 元件条件；单级 τ=R·C 匹配充要）**：无直接交集。本文的"条件"均属反问题/测量链假设层（小扰动线性化条件、各向异性比相等条件下四电极法可用的结论、唯一性反例），无任何差分网络元件级恒等消去内容，无开关电容/AAF 语境。killRisk：**无威胁**。
- **P2（Kelvin 结构地板 ≈56dB）**：无量化交集（全文无分贝级地板数字），但 §2.1/§2.2 是"两电极制受电极阻抗之害、四电极制更满意、且四电极仍受杂散电容/接触阻抗限制"的**经典域内证言**——对 P1 论文的 P2 主张只提供思想背景不构成占位；对我们**双电极电阻仪论文（P2 双电极）则是必引的划界文献**：两端 MWCNT 电阻条物理上无法四线（同"无法成桥"），必须以电极工艺/校准/相对测量回应本文第 1、2 条论断（尤其低频下接触阻抗最不利的张力）。killRisk：**无威胁（高价值背景文献）**。
- **P3（平坦度约束衰减可达上界）**：无交集（无滤波器幅频/衰减内容；"resolution"是空间分辨率非频率响应）。killRisk：无威胁。
- **方法学（D1–D10 门槛化）**：§6.3 是"物理预算→显式数值门槛"的早期范例（Johnson 噪声预算、7τ→0.1% 建立、0.2% 精度→单像素可见度、N⁻²/N⁻¹ 信号标度），与 D 系列精神同向而对象不同（EIT 采集系统 vs 仪器指标论证），可作方法学先例引用。killRisk：无威胁。

## 没读到的

- 式(2)（圆盘电极 Witsoe 公式）与式(15)(16) 等在 pdftotext 中丢失/残缺，只存变量说明残句——具体形式待核原刊。
- "100pA"（p.5）按上下文疑为 100 μA（μ→p 提取损），待核原刊；Pethig 1979 的介电线性场强 "10' V m-'"（p.6）上标丢失（疑 10⁵ 或 10⁶ V/m，待核）。
- Fig. 1–5 图像内容（Fig. 1 杂散路径示意、Fig. 2 各向异性角依赖曲线、Fig. 3–5 前臂/双目标 EIT 图）无法从文本提取。
- 引用文献全文未读（尤其 Brown 1983 教程章节——式(1)的推导出处、Bates 1980 唯一性论证、Seagar 1983 博士论文的噪声-重建分析）。
- 1984 年后 Sheffield 系统的演进与 56 dB 类量化指标（本文时点尚无）。
