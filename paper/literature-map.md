# 文献联系与划界表 v2（2026-10-27 · 审查后修订）

> 当前研究问题见 `research-focus.md` v5；本表区分“原文引用关系”“方法相近”“本项目类比”。并列不表示承继，出版先后不证明引用关系。已读笔记的阴性结论只覆盖该篇及所述命题，不自动升级为全领域不存在。
> 术语采用 G_DC、CMRR、RC ladder、network synthesis 等既有名称。“配对不变量/结构地板/四条边界”等旧工作词的限制见 research-focus §八。

## 一、核心差分谱系：按问题对照，不预画无证据承继箭头

| 工作 | 笔记锚点 | 已核内容 | 与 N1 的边界/待办 |
| --- | --- | --- | --- |
| Bartlett 1927 | [核心命题](reading-notes/bartlett1927bisection.md#核心命题原文) | 对称网络分解工具 | 不是失配元件解集；是否使用其定理须由实际推导决定 |
| Weinberg 1953 | [核心命题](reading-notes/weinberg1953lattice.md#核心命题原文) | 格形综合与两个网络函数之差 | 早于 Forte 1959；不能写成承继后者 |
| Forte 1959 | [出处与定理](reading-notes/forte1959lattice.md#出处) | 对称格形可实现性条件，笔记记录其引 Weinberg | 与消去条件是不同问题；仅由已核引文确认这条联系 |
| Pallàs-Areny 1991 两篇 | [CMRR 定义](reading-notes/pallasareny1991cmrr.md)、[级联](reading-notes/pallasareny1991cascaded.md) | 四增益描述、级联条件和失配解析 | 定义/级联基线；不能重新发明 G_DC 或把级联问题称全无先例 |
| Casas 1996 | [核心命题 2–5](reading-notes/casas1996basics.md#核心命题原文) | 非耦合 H1=H2；浮地耦合免容差消去；多阶推广表述 | **高优先划界**：明确对地梯形与全耦合网络的区别，不能泛称多阶精确消去无人提出 |
| Koide 1997 | [P1/killRisk](reading-notes/koide1997redef.md#对-p1p2p3-的对照) | 复数消去、低频调零、级联附加项 | 单频补偿与全频恒等不同，但“多级条件更复杂”已有先例 |
| Gasulla 2000 | [核心命题 3、5](reading-notes/gasulla2002cmresp.md#核心命题原文) | 一阶失配及浮容拓扑 G_DC=0 | 旧 key 保留 2002，出版年为 2000；不能只概括成“α+β=0”而漏结构消去 |
| Serrano-Finetti 2019 | [核心命题 3、5](reading-notes/serranofinetti2019cmnoise.md#核心命题原文) | 一阶完美 CMRR 条件与共模随机噪声区别 | 单级条件为已有结果；噪声不能全部由确定性 CMRR 判断 |
| Hornero 2021 | [全文笔记](reading-notes/hornero2021cm.md) | G_DC 解析、共模带通及级联警示 | 最近前作；以实际完成的元件解集/端接分析逐项比较，不预称“四增量成立” |

Thomas 1948 的比率匹配是 DC 类比（[原文锚点](reading-notes/H7_thomas1948_precisio.md)），不是本文 AC 命题的证明。

## 二、补检主线：经典 RC 综合与灵敏度

2026-10-27 新入 bib 的六篇见下。题录来自 Crossref/出版方；全文获取状态逐项见下载清单。**未取得并阅读正文前，这些条目不设 killRisk=无，不伪造精读笔记。**

| key | 工作 | 核查问题 |
| --- | --- | --- |
| fialkow1951rcladder | Fialkow–Gerst 1951, DOI 10.1002/sapm195130149 | RC 梯形传函与可实现性，哪些系数/元件约束早已得到 |
| fialkow1952rcnetworks | Fialkow–Gerst 1952, DOI 10.1090/qam/49081 | 一般 RC 两端口理论怎样限制电压比与实现自由度 |
| guillemin1949rcsynthesis | Guillemin 1949, DOI 10.1002/sapm194928122 | 经典 RC 综合工具；防止将旧综合结果改名为新“配对不变量” |
| wang2017rcladder | Wang 等 2017, DOI 10.1002/cta.2328 | 指定增益 RC 梯形实现；必须逐式比较，不能仅凭不同应用域判无竞争 |
| moschytz1999tapering | Moschytz 1999, DOI 10.1109/82.782042 | 阻抗渐变/灵敏度与拟议稳健设计族的关系 |
| moschytz1999realizability | Moschytz 1999, DOI 10.1109/82.782054 | 三阶可实现性条件；N3 不能声称无源/RC 性能界首次出现 |

已读的 [Moschytz 2002 书章](reading-notes/moschytz0radeffs.md)可提供散文层基线，公式层 OCR 缺件仍需核版面。Director→Spoto 的引用关系有 [Spoto 笔记](reading-notes/spoto1986tatistic.md)支撑；其余统计工具按方法相近并列：[Pan](reading-notes/pan1993a.md)、[Graeb](reading-notes/graeb2007areto.md)、[Stein](reading-notes/stein1986n.md)。不再将 Spoto 1986→Stapper 1989→Stein 1986 写成历史承继链。

2026-10-28：上述四篇核心综合全文已归档**并完成逐命题精读**（75 印刷页，关键定理回版面核对）：[Guillemin 1949](reading-notes/guillemin1949rcsynthesis.md#一论文结构与核心结果带页码)、[Fialkow–Gerst 1951](reading-notes/fialkow1951rcladder.md#一问题设定与拓扑假设对照的第一步)、[Fialkow–Gerst 1952](reading-notes/fialkow1952rcnetworks.md#一问题设定)、[Wang–Chen–Chen 2017](reading-notes/wang2017rcladder.md#一问题设定)。**判定结论**（详见[逐命题对照矩阵](manuscript/reviews/2026-10-28-classical-prior-art-comparison.md)）：递推/提取=①经典；同传函实现族=②现象经典（FG51 pp.59–60 连续族、Wang 数值例）；端接/口径匹配维数与双负载辨识=③四篇外的新装配（文献只有"端接压低 K_max"注记，FG51 p.62/FG52 p.120）；归一化匹配的增益自由=②指定增益理论（FG51 Thm 2→Paige–Kuh 1960→Wang Thm 1）可读出，**其 CMRR 后果（16.26 dB 例）为本稿内容**；动态线=④四篇静态不覆盖，全文献首次性仍由 Xin/Gervasoni 划界承担。到货验收见[归档记录](fulltext-archive-2026-10-28.md)。

## 三、killRisk / 必须划界清单

“须划界”表示已有结果与本文主张相邻，不等同于推翻；“待全文”也不等同于无威胁。

| 对象 | 原文证据锚点 | 写作时必须限定 |
| --- | --- | --- |
| **四篇经典综合（2026-10-28 已精读销号）** | [对照矩阵](manuscript/reviews/2026-10-28-classical-prior-art-comparison.md) §〇 | 引用分层：方法=经典（Guillemin 式30–36）；同传函多实现=经典现象（FG51 pp.59–60）；端接匹配维数/双负载/归一化口径=本稿装配；指定增益=Paige–Kuh 1960+Wang Thm 1 背景；**新缺题录 Paige–Kuh、Ali–Kim** |
| Casas 1996 | 核心笔记 §核心命题 2–5 | 非耦合/浮地耦合；多阶精确消去已有表述，本文究竟新增哪些元件条件 |
| Gasulla 2000 | §核心命题 3、5 | 一阶近似失配与拓扑消去不同；不得漏 Fig.4 |
| Pallàs-Areny 1991 / Koide 1997 | 上表笔记 | 复数级联、单级条件及单频调零均为已有工具 |
| Serrano-Finetti 2019 | §核心命题 3、5 | 增益/带宽条件已有；确定性消去不等于所有噪声消失 |
| Hornero 2021 | 全文笔记 | 差别须建立在已完成结果上，不能用研究计划对比前作结论 |
| Petkovšek 2021 | [P1/killRisk](reading-notes/petkovsek2021cmv.md#对-p1p2p3-的对照) | 两级有源 DC 元件条件为先例；与外置 RC 频域对象不同 |
| Endres 1992 | [核心命题 2](reading-notes/endres0ensitivi.md#核心命题原文) | PLL 有源瞬态条件为旁系；不提供本文必要性证明 |
| ADI Smith 2025（adi_emifilter） | [官网](https://www.analog.com/en/resources/technical-articles/gettin-in-tune-emi-filter.html)，文字段落已核，公式图片待核 | 常规无源 CM-to-DM 传函及差分电容缓解已存在；必须将新增限定于实际完成的多级/端接/稳健条件 |
| TI SBAA201A | [范围与条件](reading-notes/ti_sbaa201_rtd.md) | 单级配方/端接与角频率匹配；不能充当多级必要性证明 |
| Easy Drive | [P1/killRisk](reading-notes/mayes2015.md#对-p1p2p3-的对照) | 片内平均电荷/外部 DC 平衡，不是外置连续时间传函恒等 |
| Whitlock | [匹配与 Zcm](reading-notes/H2_whitlock2004_new.md#核心命题原文) | 完美匹配滤波元件下仍有源端失衡；不是无失衡时载荷凭空产生差模 |
| Smither 1982 | DOI 10.1190/1.1441316，当前仅摘要 | 无源不平衡致共模退化建模已有先例；全文未到，禁止作正文阴性 |
| Bockelman 1995 | [混模笔记](reading-notes/bockelman1995mixed.md) | 混合模描述及模式转换已有，本文不是新定义 |
| Moschytz / RC 综合六篇 | §二；缺件清单 | 可实现性、同传函实现族与灵敏度的关系，待全文逐式核查 |
| Zhang 2024 / Cini 2015 / Prokopenko 2020 | [Zhang](reading-notes/zhang2024highcmv.md)、[Cini](reading-notes/cini2015.md)、[Prokopenko](reading-notes/prokopenko2020cmrr.md) | DC/有源条件是注脚域，不借“领域不同”跳过条件内容核对 |

## 四、其他轴的证据角色

- H1 工业配方：Cirrus/TI 文档表明实际使用及约束，但 THD+N 劣化不能在无归因证据时都算成失配造成。
- H3 替代架构：Keller/Pavan/Ranjbar 是 CT-ΣΔ；[Koh](reading-notes/koh2004.md)的内置滤波与 [Wu](reading-notes/wu2015.md)的非均匀采样/数字 AAF 单独并列。不能将它们画成同一 CT 继承链。
- H4 方法类比：[SBOA114](reading-notes/H4_ti_sboa114_mfb_methodology.md)含噪声、失真、极点和稳定性方法；[Li 2018](reading-notes/mdpi2018_filterselection.md)研究光学滤光片，只作跨域类比，不能证明电路 AAF 选型空白。
- H5 开关行为：Martin、Ogawa、Willingham 等只在各自时序/观察点下给条件，不自动转化为连续时间 G_DC 恒零。
- H6 应用：Augustin 的 TUHH 博士论文与 Augustin 2018 scarfed-joints 期刊文相联系；[Sánchez-Romate 2021](reading-notes/sanchezromate2021cfrp.md)为 URJC 的平行/后续工作，**不是同组期刊版**；其测量接线未声明二线/四线，不能自行补定。
- H7 计量：换向、guard、主动平衡与 4TP 定义是不同误差处理方法；不能概括整个计量界“无一靠无源元件匹配”。[Barber](reading-notes/barber1984applied.md)的电极接触问题与本论文的板内 Kelvin 路径也要分开。

## 五、覆盖与异常

笔记数量、文件数量不等于独立论文数量。当前精确库存与本轮获取结果以 README/下载清单当日盘点为准；已获取未精读、正文缺件、仅摘要、文件错配分别登记。

- `pliquett2011ront.pdf` 已知内容错配，**不计作目标论文可用全文**；旧文件保留，求正确目标原文。
- `nimeroff1972recision` 所得为 SP300 色度卷，不能替代目标电学卷；目标电学卷 SP300 v3（1968）/v4（1970）本轮已从 NIST 补齐，前置题录已核，待定位目标篇并重读，不再请求重复代下。
- Lyu 同文双 DOI 已在正式 bib 去重，统一 key `lyu2018ultiobje`；旧笔记保留。
- T3 `chen2026dsmod` 已从正式 bib 移出，PDF/笔记不删。此操作不代表对先行工作作负面判定。
- 中文检索只构成有限题录/摘要筛查，限制见 `cnki-scan.md`；不再写“136 篇正文全阴性”或“中英文献双重确认不存在”。

## 六、2026-10-27 扩展考察证据矩阵

本节是原始出处到研究问题的逐项联系，不把“可支持工具”误作“已证明本文首创”，也不虚构文献互引边。A/B/C 定义见 research-focus §11.1。新条目尚未另建精读笔记；本节明确保存实际核查段落，防止题录入库被误读为全文精读。

| 证据及定位 | 核查状态 | 可支撑的内容 | 不能据此声称 |
| --- | --- | --- | --- |
| Casas 1996 [笔记](reading-notes/casas1996basics.md)，核心命题 2–5；Gasulla 2000 [笔记](reading-notes/gasulla2002cmresp.md)，原文 pp.1045–1049 相关段落 | B / Gasulla A，核拓扑与瞬态相关段落 | 非耦合双路径相等、浮地拓扑与端接/瞬态限定 | 多级精确消去此前完全无人提及 |
| Hornero 2021 [笔记](reading-notes/hornero2021cm.md)，原文关于失配、共模带通及级联的相关段落；Endres 1992 [笔记](reading-notes/endres0ensitivi.md)，原文有限时间窗建立相关页 | A，指定段落回查 | I1 最近前作；故意失配/建立时间作为 I2/I3 对照 | 故意不对称或缩短某一时间窗建立时间本身是新意 |
| Serrano-Finetti 2019 [勘误及原图定位](reading-notes/serranofinetti2019cmnoise.md#2026-10-27-原图复核与适用范围勘误优先于下方历史解读)，pp.208–210 Eq.(12)、Fig.3、p.210 有色谱限制 | A，p.210 已渲染目视 | 相关性噪声预算；白噪声闭式的适用界；内部源与外部端口分开 | 同一外部源因随机性而绕过 Gdc 恒零；单篇不足以证明高阶/有色谱全局空白 |
| Director [笔记](reading-notes/director1969the.md)、Spoto [笔记](reading-notes/spoto1986tatistic.md)、Pan [笔记](reading-notes/pan1993a.md)、Graeb [笔记](reading-notes/graeb2007areto.md) | B | 伴随灵敏度、制造相关性、性能与良率目标区别，支持 I2 方法选择 | JΣJᵀ、Monte Carlo/Pareto/minimax 首次提出；无实测依据的协方差 |
| TI SBAA201A [笔记](reading-notes/ti_sbaa201_rtd.md)、[原文](https://www.ti.com/lit/an/sbaa201a/sbaa201a.pdf)，输入/REF 滤波与 R 变化相关段落 | A，相关段落 | 比率消去需要路径匹配；参数随传感阻值变化 | 两个同步被测电压通道与 ADC 信号/REF 架构完全相同 |
| **gervasoni2017switchedratio**：Gervasoni, Carminati, Ferrari, RSI 88(10),104704 (2017), [DOI](https://doi.org/10.1063/1.4996423)；[作者存档](https://re.public.polimi.it/bitstream/11311/1037033/4/pdf_archiveRSINAKvol_88iss_10104704_1_am.pdf) | **C**：题录/原始摘要可核；存档及出版方 PDF 直取 403，正文未取得，须代下 | 双 ADC 交替获取刺激与被测响应以补偿增益漂移是已有方法，I3 必须划界 | 两通道取比/交换采集消漂为本文首创；未拿全文时断言它不覆盖某动态情形 |
| **xin2022systemratio**：Xin, Baltus, Cantatore, Harpe, TCAS-I 69(2),506–517 (2022), [DOI](https://doi.org/10.1109/TCSI.2021.3119541)，原文 **p.509 §III-A Eq.(4)–(7)、Fig.4** | **A 指定段落**：机构版本已获取，13 物理页含机构前置页，PDF 第 5 页对应 p.509 | 参考/传感器分时测量，激励和 ADC 增益误差留下时差残差；一阶差分抑制慢漂；用于 I3b 最近前作 | 标题 All-Dynamic 表示已研究任意动态 R 波形；或“时差残差”是本文新发现。本文 all-dynamic 指电路运行方式 |
| **kincl2013testfrequency**：Kincl, Kolka, *Advances in Electrical and Electronic Engineering* 11(6) (2013), [DOI](https://doi.org/10.15598/aeee.v11i6.912)；[出版方原文入口](https://advances.vsb.cz/data/articles/2013/Vol%2011%2C%20No%206/Electrical%20and%20Electronic%20Engineering/Test%20Frequency%20Selection%20Using%20Particle%20Swarm%20Optimization.pdf) | **C**：Crossref 题录与出版方摘要/首页正文片段已核；本地 PDF 未取成，机构镜像返回非 PDF，不算到货 | 模拟线性电路多频参数诊断、灵敏度矩阵条件数选频与 active-RC 例子已有，直接替代单靠 DeBrunner 数字滤波类比 | 选几个频点/换优化器就是 I5 创新；参数识别准确即意味着整带误差有保证 |
| **tadeusiewicz2017diagnostictests**：Tadeusiewicz, Hałgas, *J. Electronic Testing* 33(2),147–156 (2017), [原文](https://link.springer.com/article/10.1007/s10836-017-5650-4)，pp.147–148 目标/测量精度问题、§4 测试安排 | **A 指定段落**：出版方 PDF 已获取，10 页；未将四个案例逐个复算 | 模拟 DC/AC 测试的激励/测点设计与可观测灵敏度、测量精度约束，是 I5 直接近缘 | 普通测点选择首次提出；该文已经给出本文目标网络整带验收界 |
| **kundert2006scfilters**：Ken Kundert, *Simulating Switched-Capacitor Filters with SpectreRF*, Version 6c, 28 July 2006，[作者原文](https://designers-guide.org/analysis/sc-filters.pdf)，**pp.13–17、21–22 §3.2–3.4** | **A 指定段落**：25 页已取得；日期按版次 2006，脚注版权 2019 分开记 | 连续输出与采样输出不同、边带至基带转换及采样噪声折叠；I4 方法基础 | LPTV/周期噪声分析为本文发明；此文等同 ADS131A02 内部模型 |

### 6.1 本次补入 killRisk 划界簿

- Gervasoni 2017：比率噪声消去与双 ADC 获取架构直接相邻；**优先补全文**，未读正文不得降风险。
- Xin 2022：传感器/参考切换、时差漂移与系统比率校正有明确方程；I3b 必须说明同步滤波误差与分时漂移之间的实质区别。
- Kincl 2013、Tadeusiewicz 2017：I5 的模拟电路直接近缘已经存在，I5 优先降为验证工具，若要独立贡献须增加本网络整带误差保证及不确定度验证。
- Kundert：I4 的采样观察点/边带工具已有，不能把工具链新增算作科学贡献。

### 6.2 仍缺的证据

I1 的六篇经典/近代综合与灵敏度论文、两本综合专著相关章节、Smither/Whitlock 上游原文，仍按 P0 清单处理。I3 新缺 Gervasoni 正文；I5 新缺 Kincl 可解析 PDF。即便这些题录暂缺正文，竞争关系也不能抹去。广义“尚有空白”判断保持待定，下一步用逐命题对照与小算例证伪。

## 七、2026-10-28 接续补入：连分式综合与热噪声来源

| 条目 | 笔记锚点与证据层级 | 对本稿的作用与待核边界 |
|---|---|---|
| Lee 1978，`doi:10.1016/0016-0032(78)90050-9` | [摘要核对](reading-notes/lee1978chain.md#摘要核对与本稿使用边界)；出版方摘要，未取得全文 | 传输矩阵分解、连分式梯形综合属于已有工具；加入killRisk划界簿。全文中的存在性条件与本文系数参数化、负载核计数的包含关系待核。 |
| Johnson 1928，`doi:10.1103/PhysRev.32.97` | [摘要核对](reading-notes/johnson1928thermal.md#摘要核对与本稿使用边界)；出版方摘要 | 热噪声实验与阻抗实部关系的历史来源；不承担本项目特定梯形的数值结论。 |
| Nyquist 1928，`doi:10.1103/PhysRev.32.110` | [摘要核对](reading-notes/nyquist1928thermal.md#摘要核对与本稿使用边界)；出版方摘要 | 热平衡噪声理论来源；特定网络噪声积分和输出端量化跨度由本稿明确定义。 |

三条均不登记为精读全文。原四篇核心综合文献及本轮新增条目的获取状态见[本稿文献缺口](manuscript/LITERATURE_GAPS.md)。
