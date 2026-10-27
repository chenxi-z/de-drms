# 文献筛选总账（P1 · 2026-10-26 · go/no-go 判定与全库定级）

> **历史筛选记录（2026-10-27）**：本文件的 GO/四增量判断反映当时证据，不是当前新颖性放行。审查后重构见 `research-focus.md` v5，最近前作逐项划界见 `literature-map.md`；待全文条目不作阴性结论。

> 评价流程：构思文档 §H/§G 步骤 0——精读最近前作 → 新颖性判定（go/no-go）→ 全库定级 → 机械门禁。
> 本轮关键动作：**精读 Hornero 2021 全文**（本地 `H2_hornero2021_aeu_cmr_differential.pdf`）、
> **证伪并更正 SBAA230 误归属**、确认单级公式真实出处（TI Three Guidelines 博客 2015）。

## 一、go/no-go 判定：**GO（P1 按收窄后的四增量写）**

### Hornero 2021（AEU 128:153510，Hornero/Casas/Pallàs-Areny）覆盖了什么
- 双单端链相减结构（与我们 T2 拓扑同族）的共模→差模增益解析式 **GDC(s)=G2(s)−G1(s)**，含直流增益失配 ΔG 与角频失配 tω 的最坏情形；
- 共模响应**带通化/增益峰化/正相位**现象学（一阶链失配 → 二阶带通），含实验；
- **级联的定性警示**：前级 GCD(s) 把差模转成共模喂给后级 → 后级共模负担更大；引用 Pallàs-Areny & Webster 的级联 CMRR 经典文并指出"CMRR 当实数用的级联算法在带内不可用"；
- 结论（负面路线）：高性能差分调理**应避免**依赖无源件匹配的拓扑；调 DC 补偿有害 AC。

### Hornero 没有覆盖的（= 我们的增量，逐条核实）
1. **无源 RC 梯形（无运放）的配对不变量**：Hornero 只说"避免这种拓扑"，未回答"若保留该拓扑，配对到什么条件共模增益精确消去"——我们的**整线同 m**（R1/R2 同偏 + C1/C2 同偏 → GDC≡0）正是这个充分条件的发现与 MC 实证（逐级 51 dB vs 整线 90.5 dB）；
2. **Kelvin 无源负端的 CMRR 结构地板**（~56 dB，与配对无关）——全文无此概念；
3. **D4 平坦度约束下的衰减可达性边界**（两阶理想 ~76 dB<80）——无此分析；
4. 门槛化比较流程（D1–D10/C9 + 三层验证 + 真实占地 Pareto）。

### 定位句（写作纲领）
> Hornero 等（2021）证明该拓扑的共模响应由失配决定且"应避免"；我们回答其遗留问题：**在必须保留该拓扑时**，共模增益精确消去的配对不变量、负端无源直连的抑制地板、以及平坦度-衰减的物理边界——三者合并为无源一/二阶 AAF 的完整可行域描述。

风险登记：Hornero 引文链（Pallàs-Areny 级联文 [11]、其施引文献）尚未穷尽——深扫第二轮沿 [11] 展开；若发现配对不变量已被覆盖，降级预案不变。

## 二、全库定级（67 条 + 论坛帖）

| 级 | 定义 | 条目（bib key） | 数量 |
|---|---|---|---|
| **A 核心**（必须引用并正面划界） | | hornero2021cm · pavan2011 · ritter2015 · kumar2021 · xu2002 · ti_threeguidelines2015 · ti_sprpeo2 · adi_ctsd_tutorial · nauman2021 · sanchezromate2021cfrp · augustin2018shim · augustin2018scarfed | 12 |
| **B 支撑**（背景/对照，择用） | | ti_snaa098 · adi_ctsd_part3 · adi_difffilters · manivannan2018 · manivannan2019 · wolfer2023 · lozada2025 · xiong2022 · koh2004 · wu2015 · mayes2015 · jssc2005_switchedrc · ti_sboa114 · microchip2001an699 · ye2024 · breems2023ctsd · ct_cascaded_implicit_aa · breems_book_filternonid · dinesh2021 · qhobosheane2022 · fu2022 · qiu2024 · dong2024 · vairagade2025 · razbin2025 · singh2026 · dalessandro2014 · makireddi2015 · tragazikis2021 · preto2025 · nedelcu2022platform · khalifeh2022mcu · mdpi2018mwcnt · paleari2021laminates · styles2008filters · mdpi2018_filterselection | 36 |
| **C 现状证据**（只证"现状=配方/论坛/专利"，正文不引或脚注） | | rogillio2007aliasing · ti_sbaa230（改判 H1 数字滤波口径）· ieeebasicsdiff（题录未破案，深扫项）· adi_sd_driver · adi_emifilter · patent_ctsd_lpf · patent_kickback · konno2023 · lee2020hall · couriol2021 · basu2020 · catania2022 · zhang2022 · mounika2023 · talamadupula2016 · rajalekshmi2024 · hassan2019 | 17 |
| **D 剔除**（出圈：RF 平衡滤波器/FPAA/NeRF 域） | | shi2013 · jiang2015 · szczesny2016 | 3 |

计数核对：A12 + B36 + C17 + D3 = 68 = bib 全部条目 ✓（论坛帖仅 index 记录，不入 bib）。

计数核对：A12 + B29 + C17 = 58 篇目条目 + 论坛/专利/URL-only 记录 ≈ 总账一致（index 含 9 条仅链接记录未入 bib）。

## 三、机械门禁

- 核心引用元数据完整性：**12/12 完整**（2026-10-26 CrossRef 逐条核实；@manual/@misc 类 app note 豁免 author/doi 字段）；
- `[待核]` 残余：仅 B/C 级 3 处（breems2023ctsd 卷期、rogillio 报告号、ieeebasicsdiff 题录）——不阻塞写作；
- 每条 A/B 均有用途归属（本表 + index）；bib ↔ index ↔ Zotero 三处同步（导入器防重，重跑即增量）；
- 全库 67 条已入 Zotero 六轴目录树（2026-10-26 确认 quick_check ok）。

## 四、误归属更正记录

1. **SBAA230 误归属**：初轮检索摘要称其含差分失配-CMRR 公式，全文核实后内容为 sinc/宽带**数字**滤波器（H1 口径）——已在 bib/index 更正，单级公式真实出处为 TI《Three Guidelines》博客（2015，扫描版 PDF 在库）；
2. **Sánchez-Romate 归属混淆**：初轮把 "scarfed joints" 文章归 Sánchez-Romate 2021，CrossRef 核实该文实为 **Augustin/Karsten/Kötter 2018 Composites Part A**（即本库 TUHH 博士论文的期刊版，已入库 augustin2018scarfed）；Sánchez-Romate 2021 真身为 Composite Structures 270:114091（bonded repair）；
3. **Paleari/Nedelcu 刊名**：实为 Nanomaterials 11(6):1543 与 Microsystems & Nanoengineering 8（非 Sensors）。

## 四·五、第五轮纵深扩展定级（2026-10-26，+79 条后的增量）

- 新增理论纵深轴：**H7 比率与电阻计量**（13 条）、**H8 灵敏度与统计电路设计**（18 条）——SQ2/SQ4 的地基；
- **A 级提升 4 条**（原作谱系必引）：`casas1996basics`（差分滤波器基础，48 引）、
  `pallasareny1991cmrr`（差分 CMRR 经典，98 引）、`pallasareny1991cascaded`（级联 CMRR，44 引，
  即 Hornero [11]）、`pallas1993book`（《Sensors and Signal Conditioning》教材，366 引）——A 级共 16 条；
- 其余 75 条默认 B/C（纵深支撑/现状证据），定级依据 bib 第五轮段落轴标；
- 悬案销号：`ieeebasicsdiff` → Casas 1996 破案（IEEE TIM，10.1109/19.481347）；
- 库终量 **147 条**（bib）/Zotero 九轴 153 件（含轴内重复 6 件：一稿多版本）。

## 四·六、第六轮时间线回填定级（+20 条，库终量 168）

- 时间跨度 1998–2026 → **1963–2026**；经典题录逐条 CrossRef 确认（含 Inose 1963 ΣΔ 诞生、
  McCreary 1975 电荷再分配 602 引、Barber 1984 EIT 起源 630 引、Norsworthy 1996 ΔΣ 圣经书 598 引）；
- **A 级提升 3 条**（理论源头必引）：`norsworthy1996deltasi`（ΔΣ 数据转换器体系，SQ1 出处）、
  `orchard1966inducto`（无感滤波器灵敏度定理）、`director1969the`（伴随网络灵敏度，
  420 引）——**A 级共 19 条**；
- 其余 17 条 B/C（ Candy×2/Gray/Caves/McCreary/Gregorian 教材/Wurcer/Cage/Wen/Dharap/Chung/
  O'Dwyer/Lee/lasertrim1976/Nesbitt 等）；时间线判读已写入 index 第六轮节（Intro 骨架素材）；
- 书评类污染两次拦截（Schmalzel/Sedra）——规则：**book review 一律不入库**。

## 五、结论

**评价过关**：新颖性门槛（GO，定位句已立）+ 库内质量（A 级仅 1 条待核、全库定级完成、三处同步）。P1 可进入英文 Methods 起草；
下一步：①深扫第二轮沿 Hornero 引文链 [11]（Pallàs-Areny & Webster 级联 CMRR）与 breems2023 补全；②Methods 起草（每段 lint + 三专家面板）。
