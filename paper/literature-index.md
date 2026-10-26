# 文献总账（P1 论文 · 2026-10-25 首轮文献侦察）

> 索引与 `docs/design/2026-10-25-信号链论文构思.md` §H 六轴对应。
> 状态：**本地 PDF** = `paper/literature/` 已落盘（不入 git，`*.pdf` 全局忽略）；**仅链接** = 反爬/付费墙/HTML，只留 URL 与摘要级信息。
> 元数据凡标 **[待核]** 的，在 Scholar 深扫（构思文档 §G 步骤 0）时补齐作者全名/卷期页。

## H1 · ΣΔ 前端抗混叠设计（现状=应用笔记层，gap 靶子）

| # | 标题 | 作者/年份 | 类型 | 状态 | 位置/链接 | 用途 |
|---|---|---|---|---|---|---|
| H1-1 | Understanding the Aliasing Effects of Delta-Sigma ADCs | Rogillio, 2007 [待核] | OSTI 技术报告 | 仅链接（purl 反爬） | https://www.osti.gov/servlets/purl/1137235 | 唯一学术侧近邻；Intro 引用+引文链锚点 |
| H1-2 | Anti-Aliasing, Analog Filters for Data Acquisition Systems (AN699) | Microchip | 应用笔记 | **本地 PDF** | `H1_microchip_an699_antialias.pdf` | 代表"配方式"app note 现状 |
| H1-3 | FAQ: Delta-sigma ADC anti-aliasing filter component selection | TI E2E, 2020 | 论坛FAQ | 仅链接 | https://e2e.ti.com/.../955466 | "单极 RC 够用"共识出处之一（Intro 靶子，不进 bib） |

## H2 · 差分 RC 失配 → CMRR（经验法则层，SQ2 真空区）

| # | 标题 | 作者/年份 | 类型 | 状态 | 位置/链接 | 用途 |
|---|---|---|---|---|---|---|
| H2-1 | Basics of Analog Differential Filters | IEEE 老文 [待核] | 期刊 | 仅链接（iel1 死链） | http://ieeexplore.ieee.org/iel1/19/10302/00481347.pdf | 经典基础文，Scholar 深扫找 DOI |
| H2-2 | Understanding and Designing Differential Filters | ADI | 技术文章 | 仅链接(HTML) | https://www.analog.com/.../understanding-and-designing-differential-filters... | 工程口径对照 |
| H2-3 | THP210: Fully Differential LPF CMRR / Two-pole differential LPF | TI E2E、EEVblog | 论坛 | 仅链接 | 见构思文档 §H | 经验法则证据（不进 bib） |

## H3 · CT-ΣΔ 内在抗混叠（学术热点，芯片层，相关工作锚点）

| # | 标题 | 作者/年份 | 类型 | 状态 | 位置/链接 | 用途 |
|---|---|---|---|---|---|---|
| H3-1 | High-Speed and High-Performance Continuous-Time ΣΔ ADCs（综述） | Breems 等, 2023 [待核] | IEEE 综述 | 仅链接（付费） | https://ieeexplore.ieee.org/iel7/8782712/10019316/10268251.pdf | 热点锚点：CT 内在抗混叠综述；引文链必扫 |
| H3-2 | On the Implicit Anti-Aliasing Feature of CT Cascaded ΣΔ Modulators | [待核] | 期刊 | 仅链接（RG 反爬） | https://www.researchgate.net/publication/3451736 | 隐式抗混叠机理 |
| H3-3 | Continuous-Time Sigma-Delta ADCs (snaa098) | TI | 应用笔记 | **本地 PDF** | `H3_ti_snaa098_ctsd.pdf` | CT vs DT 架构口径 |
| H3-4 | CTSD Precision ADC Mini Tutorial | ADI | 教程 | **本地 PDF** | `H3_adi_ctsd_tutorial.pdf` | 电荷注入机理 + CTSD 宣传口径 |
| H3-5 | CTSD Precision ADCs Part 3: Inherent Alias Rejection | ADI | 技术文章 | 仅链接(HTML) | https://www.analog.com/.../ctsd-precision-adcs-part-3.html | 同上 |
| H3-6 | US20120139764A1 等 CT-ΣΔ 专利 | — | 专利 | 仅链接 | https://patents.google.com/patent/US20120139764A1/en | 产业动向佐证 |

## H4 · 多目标滤波器选型方法学（AAF 域空白）

| # | 标题 | 作者/年份 | 类型 | 状态 | 位置/链接 | 用途 |
|---|---|---|---|---|---|---|
| H4-1 | Selection of Optimal Filters for Multispectral Imaging | Styles 等, 2008 | Applied Optics 47(30) | 仅链接（付费） | https://opg.optica.org/abstract.cfm?uri=ao-47-30-5585 | 跨域 MO 选型先例（证明方法学形态成立） |
| H4-2 | Filter Selection for Optimizing Spectral Sensitivity | MDPI Sensors 2018, 18(5):1455 | 期刊 | 仅链接（MDPI 反爬） | https://www.mdpi.com/1424-8220/18/5/1455 | 同上 |
| H4-3 | Design Methodology for MFB Filters in ADC Interface (SBOA114) | TI | 应用笔记 | **本地 PDF** | `H4_ti_sboa114_mfb_methodology.pdf` | app note 里最接近"方法学"的一篇 |

## H5 · 输入 kickback / 建立时间

| # | 标题 | 作者/年份 | 类型 | 状态 | 位置/链接 | 用途 |
|---|---|---|---|---|---|---|
| H5-1 | Driving SAR and Delta-Sigma ADC Inputs (sprpeo2) | TI | 应用笔记 | **本地 PDF** | `H5_ti_sprpeo2_driving_inputs.pdf` | kickback/建立的主流口径 |
| H5-2 | A 0.6-V 82-dB Delta-Sigma Audio ADC Using Switched-RC | JSSC 2005 [作者待核] | 期刊 | **本地 PDF**（OSU 镜像） | `H5_jssc2005_switched_rc.pdf` | 芯片级避开电荷注入的先例 |
| H5-3 | Reducing non-linear kick-back in SC networks (WO2013074188A1) | 专利 | 专利 | 仅链接 | https://patents.google.com/patent/WO2013074188A1/en | 产业侧佐证 |
| H5-4 | Maximize the Performance of Your Sigma-Delta ADC Driver | ADI | 技术文章 | 仅链接(HTML) | https://www.analog.com/.../maximize-the-performance-of-your-sigma-delta-adc-driver.html | 输入阻抗/滤波口径 |

## H6 · CNT-SHM 应用与测量硬件（P2/P3 定位）

| # | 标题 | 作者/年份 | 类型 | 状态 | 位置/链接 | 用途 |
|---|---|---|---|---|---|---|
| H6-1 | SHM of CFRP via electrical resistance measurement | Augustin, 2018 | 博士论文(TUHH) | **本地 PDF** | `H6_augustin2018_tuhh_diss.pdf` | 应用域最全单卷；测量硬件现状证据 |
| H6-2 | SHM of a CFRP structural bonded joint（scarfed joints） | Sánchez-Romate 等, 2021 | Composites [刊名待核] | 仅链接（SD 付费） | https://www.sciencedirect.com/science/article/pii/S0263822321005535 | CNT 改性胶膜 SHM 代表作 |
| H6-3 | MWCNT–Epoxy Nanocomposite Sensors for SHM | MDPI Electronics 2018, 7(8):143 | 期刊 | 仅链接（反爬） | https://www.mdpi.com/2079-9292/7/8/143 | MWCNT 阻胶传感 |
| H6-4 | Structural Monitoring of Glass Fiber/Epoxy Laminates | Paleari 等, 2021 | Sensors [待核] | 仅链接（PMC 反爬） | https://pmc.ncbi.nlm.nih.gov/articles/PMC8230951 | 压阻表征 |
| H6-5 | MCU-Based Wireless Sensor Network Nodes: A Review | Khalifeh, 2022 | Sensors 22(22):8937 | 仅链接（反爬） | https://www.mdpi.com/1424-8220/22/22/8937 | 平台侧现状 |
| H6-6 | A customizable, low-power, wireless, embedded sensing platform | Nedelcu 等, 2022 | Sensors | 仅链接（PMC 反爬） | https://pmc.ncbi.nlm.nih.gov/articles/PMC8760339 | 最接近"自建电阻采集硬件"的先例 |

## 下载失败原因备忘（重试策略）

- **OSTI purl / PMC / IEEE iel1**：curl 直连被拒（反爬/死链）→ 深扫时换浏览器或机构代理；OSTI 有公开记录页 https://www.osti.gov/biblio/1137235。
- **MDPI ×3**：`/pdf` 端点返回 HTML 挑战页 → 浏览器手动下载即可（开放获取，无版权障碍）。
- **ScienceDirect / IEEE / Optica**：付费墙 → 摘要级引用已够 P1 使用；正文待机构访问。

---

## 第二轮 · CrossRef API 批量检索（2026-10-25 夜，+22 条，题录已核）

| # | DOI | 轴 | 一句话 | 用途 |
|---|---|---|---|---|
| R1 | doi:10.1109/iscas.2015.7168636 | H3 | CT 反馈型 ΣΔ 的 AAF 改进（Ritter/Ortmanns） | CT 锚点 |
| R2 | doi:10.1109/cicc.2004.1358877 | H3 | 片内集成 AAF 的 ΣΔ（蓝牙接收机） | 片上 AAF 先例 |
| R3 | doi:10.1007/s11767-002-0057-4 | H1 | ΣΔ ADC 的抗混叠滤波器（中国电子科学） | H1 学术近邻 |
| R4 | doi:10.1109/iscas51556.2021.9401336 | H1 | 离散时间 ΣΔ：放宽驱动+改进抗混叠 | **最近邻**：DT 域输入驱动+AAF |
| R5 | doi:10.1109/tcsi.2018.2826443 | H3 | 弱环路非线性致 CT 混叠抑制退化 | CT 混叠机理 |
| R6 | doi:10.1109/tcsi.2010.2071930 | H3 | SC 反馈 DAC 的 CT 混叠抑制（Pavan） | CT 高引文锚点 |
| R7 | doi:10.1109/cicc.2015.7338381 | H3 | 非均匀采样 ADC 的数字 AAF | 数字 AAF 出路 |
| R8 | doi:10.1109/iscas.2019.8702763 | H3 | CT 带通 ΣΔ 混叠抑制退化（会） | 同 2018 期刊版 |
| R9 | doi:10.1007/3-540-28473-7_5 | H3 | CT ΣΔ 专著·滤波器非理想章（Breems 书） | CT 系统参考 |
| R10 | doi:10.1016/b978-0-12-800001-4.00338-0 | H5 | Easy Drive ΔΣ 消输入电流误差 | 输入电流先例 |
| R11 | doi:10.3390/electronics13112090 | H1 | ΣΔ 级联抽取滤波器设计 | sinc³ 数字侧 |
| R12 | doi:10.1109/ieee-iws.2013.6616742 | H2 | 差分带通滤波器高 CMRR（RF） | 差分 CMRR 他域证据 |
| R13 | doi:10.1109/mwsym.2015.7166741 | H2 | 平衡滤波器差模选择性与 CMR（RF） | 同上 |
| R14 | doi:10.1007/s00034-016-0449-6 | H2 | FPAA CMRR 消除与低失配敏感 | 失配敏感性处理 |
| R15 | doi:10.3390/eng2020013 | H6 | 聚合物复合材料压阻 SHM 综述（74引） | H6 综述锚点 |
| R16 | doi:10.1177/1475921719863062 | H6 | GA 压阻自感知纳米复合材料的失效预测 | 自感知方法 |
| R17 | doi:10.1016/j.compscitech.2015.08.014 | H6 | MWCNT/PMMA 柔性膜压阻行为 | MWCNT 材料侧 |
| R18 | doi:10.1177/1475921714560071 | H6 | 纳米复合水泥基传感器机电建模 | 应用域扩展 |
| R19 | doi:10.1088/1361-665x/ae2a83 | H6 | 压阻聚合物纳米复合传感器监测混凝土梁（2025） | 最新应用 |
| R20 | doi:10.1007/s10853-025-12088-7 | H6 | 纤维增强复合压阻应变监测（2026） | 最新应用 |
| R21 | doi:10.1115/smasis2016-9234 | H6 | 纳米复合压阻损伤多尺度建模 | 建模侧 |
| R22 | doi:10.1109/apscon60364.2024.10465920 | H6 | 石墨烯压阻压力传感器 SHM（2024） | 近邻传感 |

下载备注：10.3390/eng2020013 与 10.3390/electronics13112090 为 MDPI 开放获取，curl 仍被挑战页拦——浏览器手补即可。
---

## 第三轮 · 近年研究脉络（2019–2026，CrossRef 相关度排序 + 领域过滤，+18 条）

| 年 | 一作 | 轴 | 题名 | DOI |
|---|---|---|---|---|
| 2022 | Catania | H5 | A 150 mV, Sub-1 nW, 0.75%-Full-Scale INL Delta-Sigma ADC for… | doi:10.1109/esscirc55480.2022.9911235 |
| 2020 | Basu | H5 | Delta-sigma modulator based compact sensor signal acquisitio… | doi:10.1016/j.mejo.2020.104732 |
| 2021 | Couriol | H5 | A 12-pA Resolution Sigma Delta ADC Topology for Chemiresisti… | doi:10.1109/vlsi-soc53125.2021.9606996 |
| 2022 | Zhang | H5 | A High Resolution Chemical Sensing Front-end with Integrated… | doi:10.1109/iscas48785.2022.9937843 |
| 2023 | Mounika | H5 | A 1.4mW Sigma Delta ADC with Configurable Filter for Sensor … | doi:10.1109/icufn57995.2023.10200609 |
| 2022 | Xiong | H3 | A Continuous-Time Sigma-Delta Modulator With Continuous-Time… | doi:10.1109/tcsii.2021.3127024 |
| 2023 | Wolfer | H3 | Performance and Stability Characterization of a 3rd Order Co… | doi:10.1109/newcas57931.2023.10198152 |
| 2025 | Lozada | H3 | Continuous-Time Delta-Sigma Modulator with SAR-Assisted Digi… | doi:10.1109/cicc63670.2025.10983245 |
| 2023 | Konno | H5 | 1-b Delta-Sigma ADC-Based Power Side-Channel Attack Detectio… | doi:10.1109/lsens.2023.3259301 |
| 2020 | Lee | H5 | Low Power CMOS-Based Hall Sensor with Simple Structure Using… | doi:10.3390/s20185285 |
| 2021 | Dinesh | H6 | Self-sensing cement-based sensor with carbon nanotube: Fabri… | doi:10.1016/j.matpr.2021.02.722 |
| 2024 | Qiu | H6 | Monitoring damage of concrete beams via self-sensing cement … | doi:10.1177/1045389x231221129 |
| 2022 | Qhobosheane | H6 | Smart Self-Sensing Piezoresistive Composite Materials for St… | doi:10.3390/ceramics5030020 |
| 2022 | Fu | H6 | Insight into dynamic compressive response of carbon nanotube… | doi:10.1016/j.cemconcomp.2022.104471 |
| 2024 | Dong | H6 | High performing piezoresistive MoS2/epoxy strain sensors for… | doi:10.1016/j.polymer.2024.127449 |
| 2025 | Vairagade | H6 | Artificial intelligence-driven predictive modeling of multi-… | doi:10.1007/s11709-025-1219-y |
| 2021 | Tragazikis | H6 | Monitoring the Hydration Process in Carbon Nanotube Reinforc… | doi:10.3390/app11041720 |
| 2025 | Preto | H6 | Nanocomposite sensors with indium tin oxide nanowires in a p… | doi:10.1177/14759217251322998 |

**脉络判读**：①电子线（H3/H5）近七年热点在**芯片级**——CT-ΣΔ 新结构（Xiong22 TCAS-II / Lozada25 CICC / Wolfer23）与**传感节点集成**（Catania22 亚-1nW、Basu20 紧凑前端、Couriol21 12pA 化阻式、Zhang22/Mounika23）；板级无源 AAF 选型方法学在 2019–2026 检索面内仍空白。
②应用线（H6）从材料表征走向**嵌入式组网与智能化**：自感知综述（Nauman21/Dinesh21/Qhobosheane22）→ 结构验证（Fu22/Qiu24/Dong24）→ IoT 嵌入+AI（Vairagade25、GALVEZ26）——测量硬件仍是短板，P2 仪器定位踩在趋势上。

---

## 第四轮 · SQ2 前置工作核查（2026-10-26，新颖性校准，+4 条）

| # | 来源 | 轴 | 状态 | 意义 |
|---|---|---|---|---|
| R19 | TI SBAA230《Designing an Anti-Aliasing Filter for Differential ADC Inputs》 | H2 | 仅链接（TI 可直接下） | **单级**差分 RC 失配→CMRR 退化公式的出处——SQ2 的单级层不新，须正面引用并划界 |
| R20 | Hornero Ocaña 2021, AEU《Common mode response effects in differential measurements》(doi:10.1016/j.aeue.2020.153470) | H2 | 仅链接（SD 付费/upcommons 被反爬） | **SQ2 最接近的学术前作**：容差致共模响应带通化/峰化；多级配对不变量是否覆盖待读原文 |
| R21 | TI Precision Hub《Three guidelines for designing anti-aliasing filters》 | H2 | 仅链接 | 工程口径三条准则（含失配退化提示） |
| R22 | ADI《Gettin' In Tune with the EMI Filter》 | H2 | 仅链接 | CM/DM 分解与不平衡量化的他域处理 |

**新颖性校准结论**：SQ2 需改写为——单级失配公式已有（SBAA230）、差分网络共模响应已有定性/带通分析（Hornero 2021）；
本项目的增量收窄为：①多级梯形**配对不变量**（逐级 vs 整线同 m 的机理与 MC 实证）；②**Kelvin 无源负端结构地板**；
③同时约束下的**可达性边界**；④门槛化比较流程 + 真实占地。**写作必须以 ①–④ 领衔**，SBAA230/Hornero 为最近前作；
go/no-go 门槛 = 精读 Hornero 原文与 SBAA230 全文及其引文链（若 ① 已被覆盖，P1 降级为短文或并入 P2）。


---

## 第五轮 · 纵深扩展（2026-10-26，14 轴 CrossRef + Hornero 引文链，+79 条）

新增两条纵深轴：**H7 比率与电阻计量**（ratiometric/阻抗前端/精密电阻测量）、**H8 灵敏度与统计电路设计**
（滤波器灵敏度/容差统计/Pareto 多目标模拟设计）——它们是 SQ2/SQ4 的理论地基，此前检索面过窄未覆盖。
另：原 ieeebasicsdiff 悬案破案 = **Casas 1996《Basics of analog differential filters》**（IEEE TIM，48 引），
Hornero 引文链还带出 Pallàs-Areny 1991 两篇经典（差分/级联 CMRR，98+44 引）、教材《Sensors and Signal
Conditioning》（366 引）、Serrano-Finetti 2019 共模噪声、Gasulla 2002 全差分共模响应等。
明细两批：纵深 68 条（depth，题录全核）+ 引文链 11 条（refs）。全表见 bib 第五轮段落（含轴标注释）。
**库总量：68 → 147 条**；Zotero 目录树同步扩展 H7/H8。


---

## 第六轮 · 时间线回填（2026-10-26，经典地基 1963–2012，+20 条）

> 目标：把库的时间跨度从 1998–2026 拉到 **1963–2026**，经典题录逐条经 CrossRef 确认（未凭记忆录入）。

| 年 | 一作 | 轴 | 里程碑 | 引 | DOI |
|---|---|---|---|---|---|
| 1963 | inose | H3 | A unity bit coding method by negative feedback | 170引 | 10.1109/proc.1963.2622 |
| 1966 | orchard | H8 | Inductorless filters | 297引 | 10.1049/el:19660190 |
| 1969 | director | H8 | The Generalized Adjoint Network and Network Sensitivitie | 420引 | 10.1109/tct.1969.1082965 |
| 1971 | nesbitt | H8 | The synthesis and analysis of active RC ladder networks  | 1引 | 10.1049/ree.1971.0019 |
| 1975 | mccreary | H5 | All-MOS charge redistribution analog-to-digital conversi | 602引 | 10.1109/jssc.1975.1050629 |
| 1976 | x | H8 | Stability analysis of laser trimmed thin-film resistors | 0引 | 10.1016/0026-2714(76)90124-4 |
| 1977 | caves | H5 | Sampled analog filtering using switched capacitors as re | 121引 | 10.1109/jssc.1977.1050966 |
| 1981 | candy | H3 | The Structure of Quantization Noise from Sigma-Delta Mod | 191引 | 10.1109/tcom.1981.1095151 |
| 1982 | wurcer | H2 | A programmable instrumentation amplifier for 12b resolut | 3引 | 10.1109/isscc.1982.1156396 |
| 1984 | barber | H7 | Applied potential tomography（EIT 起源） | 630引 | 10.1088/0022-3735/17/9/002 |
| 1985 | cage | H7 | A Test of the Quantum Hall Effect as a Resistance Standa | 30引 | 10.1109/tim.1985.4315329 |
| 1985 | candy | H3 | A Use of Double Integration in Sigma Delta Modulation | 441引 | 10.1109/tcom.1985.1096276 |
| 1986 | gregorian | H5 | Analog MOS ICs for Signal Processing（教材） | 0引 |  |
| 1989 | gray | H3 | Quantization noise in single-loop sigma-delta modulation | 94引 | 10.1109/26.35376 |
| 1996 | norsworthy | H3 | Delta-Sigma Data Converters | 598引 | 10.1109/9780470544358 |
| 1998 | chung | H6 | Self-monitoring structural materials | 230引 | 10.1016/s0927-796x(97)00021-1 |
| 2000 | wen | H6 | Piezoresistivity in continuous carbon fiber polymer-matr | 43引 | 10.1023/a:1004842303468 |
| 2004 | dharap | H6 | Flexural strain sensing using carbon nanotube film | 21引 | 10.1108/02602280410545399 |
| 2009 | odwyer | H8 | An enhanced model for thin film resistor matching | 5引 | 10.1109/icmts.2009.4814608 |
| 2012 | lee | H7 | Stochastic model and drift dependence of long term stabi | 0引 | 10.1109/arftg.2012.6422436 |

### 时间线判读（写 Intro 的骨架素材）

- **1963 Inose**：ΣΔ 调制诞生（unity bit coding）；**1966 Orchard / 1969 Director**：无感滤波器与伴随网络灵敏度理论——SQ2/SQ4 的理论源头；
- **1975 McCreary / 1977 Caves / 1986 Gregorian 教材**：电荷再分配与开关电容体系——"采样 kicking 进无源网络"问题的历史起点；
- **1981/1985 Candy、1989 Gray、1996 Norsworthy 书**：ΣΔ 量化噪声→数据转换器体系——SQ1 的 STF/sinc³ 理论出处；
- **1982 Wurcer**：程控仪放（ADI 谱系）；**1984 Barber（EIT 起源，630 引）**：电流激励+边界电压成像的测量系统原型——与本仪器恒流+差分采样同构；
- **1985 Cage**：量子霍尔电阻标准——电阻计量链的锚点；
- **1998 Chung / 2000 Wen / 2004 Dharap**：自感知结构材料→碳纤维压阻→CNT 膜应变——H6 应用的前三步，补齐到 Nauman 2021 综述之前的谱系；
- **2009 O'Dwyer / 2012 Lee**：薄膜电阻匹配模型与长期漂移——R_ref（±0.01%/10ppm）配对与漂移声明的文献支撑。


---

## 第七轮 · "值不值得研究"尽调（2026-10-26，四柱证据）

| 柱 | 结论 | 证据 |
|---|---|---|
| 空白 | **确认无人接理论火炬** | 2023–2025 无 combines 差分AAF×匹配×CMRR 的论文（检索引擎自证）；Hornero 施引仅 3 篇：2026 生物电医疗综述 / 2022 开关电源差分电流测量 / Petkovšek 2021 汽车负 CMV 运放级调参（已取摘要核实：非无源网络理论）——无一篇做消去条件 |
| 需求 | **跨域存在且实践层持续在问** | Hornero 引用者横跨生物电医疗/功率电子/汽车三域；StackExchange 2021/2024 差分 AAF 帖持续活跃；ADI EMI 文仅给"失配每翻倍 −6 dB"经验规则 |
| 趋势 | **CTSD 动能真实但不会杀死问题** | ADI AD4134 家族+TI 推广定位"新设计的未来"；但 DT ΣΔ 仍主导超低功耗/存量/抖动敏感场景（2025 Sci Reports 生物医学仍大量 DT）；CTSD 6 kΩ 阻性输入对高阻传感器（10–120 k 样品）强制外加缓冲 → 高阻场景外部网络问题以温和版存续 |
| 理论 | **桥电容对称性零转换仅存在于 EMC 教学直觉** | LearnEMC（learnemc.com）有平衡网络无 DM↔CM 转换的定性讨论——EMC 语境、非 AAF/计量语境、无形式化、不涉 SC 负载与源不对称 → T2 家族(b)的推导仍无人做 |

**判定：GO 维持**，附三条边界：① 论文显式讨论 CTSD 逃生门与适用域（已在 outline D3 门一）；
② LearnEMC 定性直觉可引为"对称性直觉存在但未形式化"；③ 价值排序 P2（最普适）>P1（最深）>P3（教科书式有用）。


---

## 第八轮 · 经典谱系复核（2026-10-26，用户质询"基础问题必须查老文献"驱动，+5 条经典）

| 发现 | 对论文的影响 |
|---|---|
| **电话族**：纵向→金属转换（=CM→DM 的电话学名），BSTJ 1937→W.N. Bell 1978（纵向/金属电路可分性）→IEEE Std 820 | 不杀死——传输线/标准层，无梯形网络消去条件；**I1 的谱系起点推到 90 年前** |
| **音频族**：Muncy 1995（JAES 圣典）"共模阻抗平衡决定噪声抑制" | P1 的静态/电阻性前身——本文 P1 是其**电抗梯形+SC 负载的频变推广**；必引并划界 |
| **生物电族**：Huhta & Webster 1973（IEEE TBME，DOI 已核）电极失衡→CM→DM、CMRR 无能为力 | P2 机理级前身——本文形式化为函数类论证+量化地板；必引 |
| **P3 地基**：Bode 1945 衰减积分关系 | T4 挂靠古典（专项化而非首提）；避免"重新发明积分约束"之讥 |
| **中文面**：仅 TI/ADI 应用文 + DigiKey 论坛直觉（"差分两路不可能完全一致，跨 Cdiff 解决"）+ 微波学报 PCB 混模 S 参数（异域）；无理论论文 | 中文空白确认 |
| **AD4134 残余**：阻性输入仍建议 AIN 外部 RC/EMI | CTSD 门后残余网络坐实——失配理论对其温和版依旧适用 |
| 引文计数口径 | OpenAlex 记 Hornero 被引 3（S2 记 4，Scholar 或更高）——"无人接续"结论基于施引内容核查而非计数 |

**复核结论**：五条经典全部"加固而非杀死"——问题是九十年跨四域的老问题（这本身是最好的立题理由），
历代只走到"机理/经验/标准"层，**网络理论级的消去条件从未被给出**；P1/P2/P3 的定位句全部升级为
"对 X 族的推广/形式化/专项化"。新增 A 级经典 5 条（bell1978/muncy1995/huhta1973/bode1945/ieee820 归 H2/H8）。


---

## 第九轮 · "为什么没人做"的解释（2026-10-26，知识社会学核查）

**五机制，全部有本库证据**：

1. **历代问的都是窄版本，解到够用就停**：电桥时代（Blumlein 1920s 变压器比例臂）用匝比**结构性**实现与频率无关的
   平衡——用"换网络类"回避匹配问题（guildner1965tra/magerlein1975tra；一百年后 CT-ΣΔ 是同一招重演）；
   电话/音频只要统计级 dB 指标（bell1978/muncy1995）；生物电只要单频 ω 公式（huhta1973 + Webster 教材
   (Z₁−Z₂)/Z_in 式，经查教材确为单频）；TI/ADI 只要单极 τ 规则 + 跨 Cdiff 补丁。**无一族需要过全频段精确恒零的代数条件**。
2. **宽带精确版的需求是新生事物**：数字比值计算 + 扫频/同步双通道 + 计量级精度 + 无源梯形，四条交集只在
   2000s 后的 ΣΔ 比值仪器出现（本机即全中）。
3. **知识生产结构错位**：受害者（仪器工程师）写成 app note/论坛直觉（单极公式至今只活在 TI 博客，已证实）；
   有工具者（灵敏度社区 Director 1969 一脉）问良率不问消去不变量；芯片学术圈让问题片上消失。四词汇族互不引用
   （bell1978 不引音频、hornero2021 只回溯至 1991）。
4. **经济逃生梯反复短路需求**：单极规则→跨 Cdiff 民间补丁（用了"结构性零"定理而不陈述之——DigiKey 中文论坛
   原话"差分两路不可能完全一致，跨接 Cdiff 解决"）→买 CTSD/仪放。理论总在被需要之前被绕过。
5. **发表形状孤儿**：纯理论对 TCAS 太小、对仪器期刊太数学——落在 app note 与论文之间的缝里，folklore 因此再生产。

**剩余未扫书架（T1–T4 前定向补扫）**：电桥计量学文献（NBS/NPL 报告全系列、Cal Lab 期刊）、Weinberg《Network
Analysis and Synthesis》格形网络章。单频/静态层定量结果在那里很可能存在（Webster 教材已有单频式）；
宽带梯形+SC 负载不变量仍为本项目主张。


---

## 第十轮 · 形式化谱系终扫（2026-10-26，用户断言"不可能没人做过"驱动，+3 条）

**六族形式化谱系地图（每族解到自己够用的深度）**：

| 族 | 形式化成果 | 深度 | 问过 P1 吗 |
|---|---|---|---|
| 电话（1937–78） | longitudinal balance 规范与测量（dB 指标） | 规范级 | 否 |
| 音频（1995） | Muncy 静态阻抗平衡原理 | 规则级（电阻性） | 否（无频变） |
| 生物电（1973–教材） | Webster 单频失衡式 (Z1−Z2)/Zin | 单频定量 | 否（单频） |
| **RF/微波（1995，1028 引）** | **混模 S 参数（Bockelman & Eisenstadt）：Sdc/Scd 形式化 CM↔DM 转换** | **描述/测量形式体系** | 否（量化"转多少"，不给"何时恒零"） |
| **EMC/电力（2022 教材+综述）** | **不平衡因子 h=Z1/(Z1+Z2) 定量预测转换** | **预测公式（给定失衡算转换）** | 否（静态比值，无多级电抗梯形） |
| 精密 DAQ（TI/ADI） | 单极 τ 规则 + 跨 Cdiff 民间补丁 | 配方级 | 否 |

最近的差分 AAF 学术近邻 = Denisenko & Prokopenko 2020（IOP MSE，2 引）：主动滤波器最少电容**合成**路线，
不涉匹配/消去条件——问题域相邻、问题本体不同。

**修正后的"为什么没人做"终答案**：不是"没人碰过现象"——六族各自把现象形式化到其应用所需的深度；
**没有任何一族需要过"多级无源电抗梯形在 SC 负载下全频段精确消去的代数条件"**——需要这个交集
（比值式 ΣΔ + 计量级 + 无源梯形 + 宽带）的应用 2000s 后才出现。P1 的措辞必须改为：
"描述与预测的形式体系已有（混模 S 参数/不平衡因子/单频失衡式），梯形类的精确消去条件未见于任何谱系"。


---

## 第十一轮 · 四排深挖（2026-10-26，+4 条；用户"肯定有很多，记得保留"驱动）

| 挖出 | 内容 | 对框架的作用 |
|---|---|---|
| **Bartlett 平分定理谱系**（1930 教材 → Fujishiro & Yamamoto 2017 群论扩展） | 对称二端口网络可切分为 DM/CM 两个半电路——半电路分析的正统理论基础 | **T1 的正统祖先**：本文 P1 定位为其"失配摄动伴随"——对称分解古典，不对称消去条件缺位 |
| **自动平衡电桥**（Keysight E4980A/4294A；Impedance Measurement Handbook 140 页） | 低端虚地+零值检波 0°/90° 分解+反馈置零——产业界对 Kelvin 不对称的主动解法 | **P2 的产业级逃生门**（此前未编目）：商用阻抗分析仪不用无源对称，用主动虚地绕开结构地板 |
| **SC 滤波器电容比设计**（Gregorian 1986 在库；common-centroid 布局 ~0.1–0.5% 比精度） | IC 世界的匹配解法=比值化设计+版图匹配——传递函数只依赖电容比 | **"为什么没人做"新机制**：IC 世界内部解决了匹配（比值+版图），板级离散世界继承了问题却继承不了解法；我们的"整线同偏"正是比值守恒的离散版表亲 |
| **NBS 谱系**（Wenner 1912 保护原理；Precision Measurement and Calibration 文集） | 守卫/屏蔽/电桥计量经典汇编 | H7 加深；与 Blumlein TRA 并列的计量学第二支柱 |

**净效果**：谱系地图从六族扩到八族半（+Bartlett 分解谱系 +NBS 计量谱系）；P2 多一扇产业逃生门（自动平衡电桥）；
"为什么没人做"多一条机制（IC 内部解决 vs 板级继承）。P1 消去条件在所有谱系中的缺位依然成立。
