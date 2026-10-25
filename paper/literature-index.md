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
