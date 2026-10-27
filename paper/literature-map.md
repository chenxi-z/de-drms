# 文献联系图谱 v1（2026-10-27 · 165 份精读笔记收齐后的谱系综合）

> **术语说明**：本篇及项目文档中"P1 消去条件""多级梯形精确消去""配对不变量/整线同偏""Kelvin 结构地板""四条边界"等均为**本项目自造的工作用语**，非文献既有概念。文献既有概念 = G_DC / common-mode-to-differential gain（Hornero 2021 eq.(5)、Gasulla 2002）、RC ladder network、mixed-mode S-parameters（Bockelman 1995）等。论文写作时自造词要么改为平实描述、要么显式声明为本文命名。

> **本篇是什么**：`paper/reading-notes/` 全部 165 份精读笔记之间的**联系结构**——谱系链、三命题证据矩阵、killRisk 划界簿 v2、跨轴同构对照、库务勘误。它是 `literature-conclusions.md`（v2，29 篇版）的联系侧补全，不取代其结论；写作取材时两份对照使用。
> **纪律**：每条联系落笔记锚点（`reading-notes/<bibkey>.md`）；笔记里没有的不写；链上"承继/同构/对照"的定性以笔记原文引用为据，不凭题名臆测。基于 2026-10-27 补跑四波（39 篇）+ 既有 125 份（批 1–20 + 杂项波次 + 本人精读 Whitlock）。

---

## 一、八轴谱系链（节点 = 笔记，边 = 联系类型）

### H2 消去条件核心轴（P1 的正面战场）

```
Bartlett 1927 平分定理（对称网络 DM/CM 分解古典源头）
  └承继→ Forte 1959 对称格形综合 → Weinberg 1953 格形综合
Tucker 1955（臂失配→载漏定量，调制器域）
Thomas 1948（DC 比率匹配祖先：a/b=A/B ⇒ 引线项恒零, eq.11 p.17）
  └同构(AC版)→ [P1 本体：AC 多级梯形系数全等条件]
Gasulla 2002（单级一阶失配公式 α+β=0；浮容拓扑 G_DC≡0 先例）
Koide 1997（复数差零点消去 + 级联泄漏项）
Zhang 2020（有源复制，带限）
hornero2021cm（最近前作：G_DC=G₂−G₁ 单级解析 + "应避免"结论）
Whitlock 2004（第二机理：Zcm 载荷——完美匹配电容仍伤 HF CMRR）
bockelman1995（混模 S 参数：只量化"转多少"，不给"何时恒零"）
```

- **P1 措辞红线**（notes 全体阴性 + 上链）：不得说"失配处理无先例"（Thomas/sprpeo2 有）；不得说"单级无处理"（Gasulla/Hornero/SBAA201A 有）；只能主张 **AC 多级梯形全频段精确消去条件**（配对不变量）。
- 本会话新增近缘（均"无威胁但须划界"，见 §三）：`zhang2024highcmv`（DC 四电阻解析式 CMRR_R=(k+1)/4t + 激光修调）、`cini2015`（有源电流模"CMRR independent of resistor mismatches"，域为增益路径）、`kumngern2011oltageco`（对称平均消去需器件匹配，无失配解析）。

### H5 踢回/建立轴（消去母题的时域变体）

```
Martin 1982（SC 馈通补偿鼻祖：消去=元件匹配(M6≡M5, C3≡C_总)+CMRR→∞ 理想化）
  └承继→ ogawa1991lockfeed（双电容相消：匹配 + 快速关断时序条件）
kawahito1999 → minkyusong1993 → willingham → parsan2008 → zhou2010 → zou2017（SC 输入负荷/建立口径链）
mayes2015（LTC248x Easy Drive：片内开关图形使平均差分输入电流为零 + 外部 R 平衡条件）★须划界
schrunder2024（2024 大综述）/ basu2020 / lee2020hall（现行驱动口径）
```
- 链内教训（笔记已标）：**低阻节点馈通无害、虚地点有害**（martin1982ew）——与 P2 的 Kelvin 负端直连理由同构。
- `karthikeyan2002lock` 是占空比调整器、非 kickback 文献，**不得入本链**（目录错配，见 §五）。

### H3 逃生门轴（CT-ΣΔ 内在抗混叠）

```
ct_cascaded_implicit_aa（Keller 2007，P0 隐式抗混叠正典）
  → pavan2011 / ranjbar2011（CT-ΣΔ 混叠抑制正典 P0）→ ritter2015 / manivannan2018/2019 / kidambi2019 / saberinia / akbari2017 / koh2004 / wu2015
AD4134 + adi_ctsd_tutorial（产业实证：AAREJ 85.4/102.5 dB；AIN 无强制外置滤波——v2 〇-1 勘误）
```
- 逃生门代价（笔记原文）：Rs/6.25 kΩ 分压温漂（tutorial p.22）；通道间相位 ±0.02°@20kHz vs 外置 RC 1% 容差 ±0.15°（tutorial p.19）；环路延迟/分数阶保持折叠残留（Keller/Manivannan）。
- **对 P1 的用法**：逃生门不完美处 = P1 必要性证据；但 AD4134 勘误后不得再写"CTSD 门后仍需 RC"。

### H7 计量轴（P2 的产业级原型库）

```
NBS SP300 分卷：swindells1968（换向消引线差："引线电阻差在 N/R 两换向态不变才完全消去" p.152）
  + ginnings1970（guard 术语锚点 + volt-box 自比 0.6 ppm）
Cutkosky 1961/1970（双替换换向平均"equally with opposite sign"；4TP 定义免疫引线串阻）
Dunfee 1963（守卫等电位=泄漏驱动电压为零）→ Guildner 1965（匝比 1–2×10⁻⁷）→ Thomas 1948 → Hall 通史（Wagner 对偶 Kelvin, p.13）
Keysight/QuadTech 7400（自动平衡电桥："unbalance current converges to exactly zero"）
  → marzano2022（PTB Josephson 桥 1×10⁻⁸ 现役顶级）+ grubmuller2016（1 kV 探头 CMRR 59 dB 实证 ≈ P2 地板量级）★
ti_sbaa201_rtd（工业单级配方正典：C_DIFF≥10×C_CM + τ 匹配）★须划界
```
- 共性判语（H7 笔记全体）：计量界全部靠**结构/定义/主动置零**消去，无一靠无源元件匹配——P2"结构地板"的计量级对应。
- `nimeroff1972recision`：Vol 9 为色度学卷，目标论文不在其中（真目标 Vol3/4 电学卷库未收），引用改投 Vol3/4 待补（§五）。

### H8 理论地基轴（P1/P3 的数学工具箱）

```
Orchard 1966（无电感滤波经典）→ director1969（伴随网络灵敏度）
  └下游→ spoto1986tatistic（工业统计设计范本：mismatch/process 分层协方差；引 Director–Rohrer）★P1 高
     → stapper1989（缺陷成簇良率模型）→ stein1986（混合密度方差缩减：Mahalanobis ≈2 有效 >4 失效）
     → pan1993a（"性能最优点≠良率最优点" p.1；灵敏度分级筛选容差门槛——D1–D10 同构先例）★方法学高
director1993tatistic（统计设计教材）→ graeb2007areto（Pareto 支配 + worst-case 线性化定义源）
lyu2018ultiobje（MOBO：通用多目标框架，算例全晶体管级，无滤波器算例）
moschytz0radeffs（2002）★P3 高：RC 极点单根负实轴⇒Q<0.5 不可能性定理 + 元件比(tapering)换性能权衡范式
debrunner0hoosing（灵敏度 S 与可辨识度 K 解耦：低敏感≠不可辨识）
vaidyanathan1986（结构无源性+触界⇒低灵敏度，数字格形域堂亲）
```
- 本轴对 P1 的两大支援：**endres0ensitivi**（PLL 差分环路滤波器共模零输出 **iff** R1=R3∧R2=R4∧C1=C2——"消去 iff 元件匹配"的独立域同构，含充要条件表述）与 **spoto1986tatistic**（失配→性能的统计分解怎么做的工程范本）。
- `das2009`：进化拓扑综合（运放/VCO benchmark），与本轴理论无内容重叠；其参考文献 [8] Das & Vemuri ISCAS 2008"无源模拟电路 GA 综合"是潜在待读新条目。
- `fitch1975ilter`：**题名错位**——实为液压污染控制论文，严禁按题名误引为电路滤波器灵敏度文献（§五）。

### H1 配方线（"学术界说别用、厂商逼你用"现状证据）

```
green2003_an048（"simply duplicating the component values"，零失配分析）
  → 2025_an0556（无源差分滤波 THD+N 劣化 ~10 dB）→ ak5578en / es9038pr（片内 THD 补偿兜底）
zamaruiev2019 / chen2009 / xu2014 / xu2002 / gao2010 / sun2011 / ye2024（AAF 现状综述线）
kumar2021（P0：DT ΔΣ 放松驱动）+ microchip_an699（阶数-衰减配方表）
```
- 跨 22 年四厂商镜像配方零失配分析（四份 H1 笔记原文证实）——P1 引言现状段的证据束。

### H4 选型方法学轴

```
ti_sboa114（MFB 方法学：噪声预算路线 Eq.9，无失配/CMRR）+ mdpi2018_filterselection（多目标选型无解析框架=空白靶子）
```

### H6 应用域轴（"测量环节商品化"空白侧证）

```
barber1984（EIT 奠基综述：两电极必受接触阻抗之害 "All two-electrode systems suffer…" p.2）★P2 必引划界
  → augustin2018（TUHH 博士论文：信号 % 量级、无自研前端）→ sanchezromate2021（同组期刊版：测量链一句带过，Agilent 34410A 两电极）
nauman2021（压阻 SHM 综述：测量零硬件讨论）→ qhobosheane2022（唯一带自制前端=JFET 增益级，无误差预算）
khan2013（FPGA EIT 恒流源，P2 同构系统旁证）
```
- 本轴定性（笔记全体）：应用文献不关心前端理论——P1 空白的需求侧证明；同时 **精度论据不得引应用拉**（Augustin %级信号，v2 C-6）。

---

## 二、三命题 × 证据矩阵（节点→命题：支援/划界/反例/无涉）

| 命题 | 正面支援（引援） | 必须划界（非撞车但近） | 反例搜索阴性（覆盖面） |
|---|---|---|---|
| **P1 消去条件** | gasulla2002、koide1997、endres0ensitivi（iff 同构）、martin1982ew、thomas1948（DC 祖先）、bartlett1927/forte1959（对称分解工具） | hornero2021cm、ti_sbaa201_rtd、mayes2015、zhang2024highcmv、cini2015、kumngern2011 | 165 份笔记覆盖全部在库正文，无一处给出"多级无源梯形全频段精确消去条件"推导（各批精读汇报逐篇阴性） |
| **P2 结构地板** | cutkosky1961/1970、dunfee1963、guildner1965、keysight_7400、swindells1968、ginnings1970、grubmuller2016（59 dB 实证）、marzano2022、lee2000owvoltag（有源伪差分 43 dB 对照）、barber1984（两电极接触阻抗） | smither1982（仅摘要，付费墙：无源失衡→CMRR 20 dB 建模先例）、bockelman1995 | — |
| **P3 可达边界** | moschytz0radeffs（RC 极点 Q<0.5 + tapering 权衡）、an699（阶数配方表反证）、vaidyanathan1986（跨域旁证）、graeb2007/lyu2018（Pareto 框架）、jiang2015（另一机理家族无上界定理） | — | 无任何一篇给出平坦度-衰减解析上界或 Bode-Fano 型约束对论证 |
| **增量四（门槛化方法学）** | sboa114（噪声预算）、pan1993a（分级容差门槛）、spoto1986tatistic（mismatch/process 分层）、stein1986（MC 效率边界）、graeb2007（worst-case） | das2009（启发式分摊反衬解析路线必要） | — |

---

## 三、killRisk 划界簿 v2（在 MOC §五基础上新增/更新 7 条）

| 条目 | 定级 | 划界要点（锚点） |
|---|---|---|
| hornero2021cm | 最近前作（MOC 已录） | 四增量 ①配对不变量 ②Kelvin 地板 ③可达边界 ④门槛化流程领衔行文 |
| smither1982commonmode | 非 kill·须划界（MOC 已录） | "无源失衡→CMRR 退化建模无先例"不可说 |
| ti_sbaa201_rtd | 非 kill·边缘对照·**须划界（本会话全文证实）** | 范围=单级一阶 RC+直流+10× 比值压制（"not always possible to exactly match…" p.5）；失配实验 350 nVrms→1 µVrms 随信号增长；τ 匹配判据**弱于**元件条件（同 τ 可不同 R·C 组合）；从未分析多级梯形 → P1 多级/全频段主张显式声明超出其范围 |
| **mayes2015**（新增） | 非 kill·最近缘商业先例·**须划界** | Easy Drive"平衡条件⇒外 RC 零 DC 误差"与 G_DC=H_N−H_P≡0 形状相同：片内专有算法、DC 域、共模残差靠校准，无 AC 衰减上界/Kelvin 地板/网络综合——P1 引用并显式区分"片内电荷域 DC 消去"与"外置无源传输函数条件" |
| **endres0ensitivi**（新增） | 佐证非竞争·划界 | "共模消去 iff 元件匹配"独立域同构是 P1 的强力旁证；但其"故意最优失配"解法依赖 ±6° 窗口判据，引用时注明适用域 |
| **zhang2024highcmv / cini2015**（新增） | 注脚级·划界 | 均在 DC 减法器/有源电流模域：可作 P1 引言"现状=DC 解析+修调补救"注脚；cini2015 摘要句"CMRR independent of resistor mismatches"适用域为增益路径非无源网络频域 |
| **barber1984applied**（新增） | P2 必引·划界 | "两电极必受接触阻抗之害 + 四电极仍受 pF 级杂散电容之害"（p.2–3）是 P2 双电极论文的必引划界文献：低频直流恰处接触阻抗最不利端 |

---

## 四、跨轴同构对照（"消去"母题的四域变体——P1 讨论节的现成结构）

| 域 | 消去手段 | 条件形态 | 锚点笔记 |
|---|---|---|---|
| H2 无源 RC（P1 本体） | 系数全等（单级退化为 τ 匹配） | 频域、传输函数条件 | gasulla2002 / koide1997 / hornero2021cm |
| H5 片内 SC | 馈通补偿/双电容相消 | 元件匹配 **+ 时序条件**（非纯元件条件） | martin1982ew / ogawa1991lockfeed |
| H8 PLL 环路滤波 | 共模（等输入）输出为零 | **iff** R1=R3 ∧ R2=R4 ∧ C1=C2（充要） | endres0ensitivi |
| H7 计量 | 换向/替换/结构比率/主动置零 | 操作序列条件（结构性，非元件匹配） | cutkosky1961 / swindells1968 / keysight_7400 |
| H8 统计设计 | 匹配/工艺分层进协方差 | 统计条件（yield 视角） | spoto1986tatistic / pan1993a |

---

## 五、库务勘误清单（本会话精读核出）

**已在 bib 修复（literature.bib，本会话）：**
1. `khalifeh2022mcu` 第 4 作者 Nyathi → **Nyambo, Benny Munyaradzi**（原文逐字核对）；
2. `lyu2018ultiobje2` 与 `lyu2018ultiobje` 为同一 DAC'18 论文双录（ACM/IEEE 双 DOI，全文零差异）——bib 加注释，**引用一律用 lyu2018ultiobje**；
3. `moschytz0radeffs` year 0 → **2002**（Kluwer 书章；严格应为 @incollection，bib 注释已标）。

**待用户/Obsidian 库务会话处理（本仓不碰库内文件）：**
4. `pliquett2011ront.pdf` **内容错配**：库内文件实为 Kado 2004 等离子体物理论文；目标论文（Physiol. Meas. 32, DOI 10.1088/0967-3334/32/7/s15）为付费墙未到货（paywall-download-list 第 64 项）。异常登记笔记已在 `reading-notes/pliquett2011ront.md`；到货后须重跑精读。
5. `nimeroff1972recision`：SP300 Vol 9 为色度学卷，目标电学论文在 **Vol 3（低频电学）/Vol 4（射频电学）**，库未收——补卷后重读（引用暂改投 Vol3/4 待补）。
6. 目录归类错配（内容与轴目录不符，笔记已标注）：`karthikeyan2002lock`（实为占空比调整器，非 kickback，**不得按题名引**）、`fitch1975ilter`（实为液压污染控制，**不得按题名引**）、`khalifeh2022mcu`（WSN 平台综述，非 CNT-SHM 本体）。
7. 旧合卷笔记 `H7_nbs_sp300_v2v6v9.md` 两处存疑（"computable/compensable"存疑词、锗电阻篇引文）已由新分卷笔记复核处理，以三份分卷笔记为准。
8. `pan1993a` 数值出入（正文 68.34% vs Table VI 68.73%）与 `zhang2024highcmv` 中英文摘要 98.1%/98.4% 矛盾——均已在笔记「没读到的/待核」登记，引用时避开或回原文核对。
9. `das2009` 参考文献 [8]（Das & Vemuri ISCAS 2008 无源模拟电路 GA 综合）是潜在新条目，是否入库待用户定。

---

## 六、中文文献反例搜索（2026-10-27 补充）

知网扫描（方法与全记录见 `paper/cnki-scan.md`）：中文"抗混叠"题名文献 136 篇逐条判读（97 题过目）+ 差分滤波器/仪表放大器 CMRR/无源灵敏度等定向查询——**四条缺口在中文文献同样无占位**。直域命中《一种ADC前端无源差分抗混叠滤波器设计》（武媛媛 2023，电子与封装）为配方级应用文，按中文文献质量标准（T3 普刊）**不入库**，记录存 cnki-scan.md §三。域外邻居与假朋友清单（RF 平衡滤波器、电力 LC 多目标、图像"差分"）见 cnki-scan.md §四。**库内中文条目定级**：T1 `jiang2004chebyshev`（电子与信息学报，EI）/ T2 `zhang2024highcmv`（微电子学与计算机，引用前复核摘要矛盾）/ T3 `chen2026dsmod`（普刊，默认不引）。

## 七、精读覆盖统计（2026-10-27 收口）

- 笔记总量 **165 份**（`paper/reading-notes/`），对库内 167 份全文（164 PDF + 3 txt）：**全部可读正文已覆盖**。
- 未覆盖正文仅两类，均为**库外缺件**：pliquett2011（付费墙未到货+库内错配）、SP300 Vol3/4 电学卷（未收集）。
- 本会话补跑 40 篇处置记录：38 篇完整笔记 + 2 篇如实异常登记（pliquett2011ront、nimeroff1972recision）；防御性重发（orchard1966、shi2013）写盘前查重跳过。
- P1 反例搜索终态：**全部已读正文阴性**——"多级无源梯形全频段精确消去条件"在八轴谱系内无占位者，P1 空缺主张维持成立。
