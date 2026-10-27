# 文献结论书 v2（2026-10-26 · 29 篇正文精读后的修订版，取代 v1）

> **历史底稿提示（2026-10-27）**：本文件的包络/普适地板/首创性判断未经本轮审查后重新证明，不能作为当前研究结论。当前框架以 `research-focus.md`、`outline.md` v5 为准；当前谱系与全文状态见 `literature-map.md` 和 `paywall-download-list.md`。

> v1 是摘要级提炼，已被用户批评并推翻。本版基于 **29 篇 PDF 正文逐节精读**（本人精读 Whitlock 2004，
> 其余 28 篇由精读员全文读毕，笔记在 `paper/reading-notes/` 15 份，全部原文引用+页码）。
> 纪律：每条结论落正文原文位置；正文没有的不写；与 v1 冲突处以正文为准并记录更正。

---

## 〇、正文精读对 v1 的更正与新发现（先读这节）

| # | v1 说法 | 正文事实 | 影响 |
|---|---|---|---|
| 1 | **【重大更正】**"CTSD 逃生门残余：AD4134 数据手册仍建议 AIN 外部 RC/EMI" | **误**。AD4134 全书无 AIN 引脚外部滤波推荐；唯一 "RC circuit is required at the ADC input"（p.32）是**离散时间 ADC 对比电路**（Fig.63）注解。门后残余仅 Rs/RIN 分压（6.25 kΩ typ）+ 源阻抗 | D3 门一的"残余网络"表述必须改写为"残余是分压/温漂，不是必装滤波"——逃生门比 v1 说的更干净 |
| 2 | v1 只讲"失配致 CM→DM 转换"一条机理 | **Whitlock 2004 p.4 第二机理**：对地电容 **"even if the capacitors are perfectly matched"** 仍把 Zcm 拉到 ~16 kΩ@10kHz、恶化 HF CMRR——匹配不救 Zcm 载荷 | P1 理论必须显式分双通道：失配转换（系数条件管）+ Zcm 载荷（高共模阻抗/自举管）；T2 的 C_G 属后者 |
| 3 | "整线同偏"是全新发明 | **DC 谱系有先例**：Thomas 1948 eq(11)——引线电阻项 "can be made zero by making a/b = A/B, irrespective of the value of the link resistance"（印刷 p.17）；比率匹配的 DC 版 | P1 措辞改为"AC 梯形版的比率匹配定理"（DC 先例正面引用，划界在 AC 多级/复频） |
| 4 | "与频率无关"是 Blumlein 公认性质 | **无一句明文**。Guildner 只证匝比精度 "1 or 2 parts in 10⁷"（p.16）；"频率无关"是 Guildner 固定 1kHz + Hall 对比句（"Wien's bridge is frequency dependent", Hall p.10）拼出的证据链 | 引用时不得写成"明文定理"，按证据链表述 |
| 5 | NBS SP300 三卷=电学计量文集 | **卷册张冠李戴**：实为 Vol2《Temperature》/Vol6《Heat》/Vol9《Colorimetry》；真正的电学卷是 Vol3/4，本库没有 | 三卷降级为温度/热学背景（其中 Vol2 恒温/温度比对内容反而支持我们温补路线）；电学卷待补 |
| 6 | SHM 应用"需要"高精度测量仪 | Augustin 2018：信号是**百分之几**量级（ΔR/R₀ +4.1%），无自研前端，温度靠恒温回避 | 引言不得夸大需求——我们的仪器是通用化平台，应用拉不动精度论据；诚实改写 |

---

## A. 文献确立的事实（正文级，带页码）

### A1. 现象八谱系（升级版：每谱系的"已解深度"有正文证据）

| 谱系 | 已达深度（正文证据） | 精读笔记 |
|---|---|---|
| 电话 | balance dB 规范+测量法；"转换仅由不平衡决定"（Bell 1978 摘要级，正文未到手） | — |
| 音频 | **电桥等效+Zcm 框架**：平衡接口=Wheatstone 桥（Whitlock p.2）；1Ω 源失衡→CMRR 120→80 dB（p.3）；**完美匹配电容仍伤 HF CMRR**（p.4）；解法=自举抬 Zcm>10 MΩ、0.005% 电阻匹配→90 dB（p.5） | H2_whitlock2004_new.md |
| 生物电 | 单频失衡式（Webster 教材，正文未到手） | — |
| 射频 | 混模 S 参数形式体系（Bockelman 1995，付费墙正文未到手） | — |
| EMC | 不平衡因子 h（Keller 2022，付费墙） | — |
| 地震 | 系统退化建模先例（Smither 1982，付费墙） | — |
| 计量学 | **"消去术"五件套全部正文证实**：守卫等电位（Dunfee p.3 shield 同电位使泄漏驱动电压为零）、比例臂匝比（Guildner p.14 "within a part per million of the turns ratio"；Hall p.33 "Ideally N1/N2 = Zx/Zs"）、四端对定义免疫（Cutkosky1970 p.65-66，引线串阻免疫+共轴零净电流）、双替换/换向平均（Cutkosky1961 p.155 "equally with opposite sign" 精确消泄漏）、自动平衡电桥虚地（Keysight §2.3.2 "the unbalance current converges to exactly zero"）——**全部靠结构/定义/主动置零，无一靠无源元件匹配** | H7_cutkosky*、H7_dunfee*、H7_guildner*、H7_hall_a、H7_keysight_7400_manuals |
| 调制器 | 臂失配→载漏定量（Tucker 1955，付费墙） | — |

### A2. 工程配方的正文实锤（"配方掩盖机理"直接引文）

- TI sprpeo2：**p.44 "0.1% or better tolerance for good matching" + p.46 "CCM scale to 1/10 of Cdiff for best common-mode noise rejection"**——给比例不给转换条件（P1 靶子引文）；
- Cirrus AN048 **p.1 原话**："The differential input function is accomplished by **simply duplicating the component values** generated in the filter design"——全文无 mismatch/tolerance/CMRR 字样；
- Cirrus AN0556 p.16：无源差分滤波 "THD+N performance is degraded by approximately 10 dB"（无机理无归因）；
- AK5578 Fig.76 两臂镜像 68µF→NJM5534→10Ω+100pF+15nF 跨接；S/(N+D) 随偏置劣化 ~6dB（p.69）；
- ES9038PRO：**片内 THD 补偿**（p.11 "inverse second and third harmonic components matching the target system distortion profile"）——厂商用事后补偿兜底，从不对外置臂失配建模；
- **跨 22 年（2003–2025）四厂商文档复证**：镜像配方零失配分析（H1_* 四份笔记）。

### A3. 逃生门与代价的正文实锤

- **CTSD 门（AD4134）比 v1 认为的干净**：AIN 无强制外部滤波（勘误见〇-1）；AAREJ=85.4/102.5 dB（MCLK±160kHz 窗，p.8）；四通道相位匹配 1.57/3.3ns（p.6）；残余=Rs/6.25kΩ 分压与温漂（tutorial p.22）；
- **但相位口径已有定量对照**：tutorial p.19——RC AAF 1% 容差→±0.15°@20kHz，CTSD 片内 ±0.02°@20kHz（P1 的 P/N 幅相议题在 CTSD 下转移到通道间）；
- **反相测量法的代价**（Ji 2016 p.12/p.76-77）：DPDT 极性反转+两次测量消 CMR，代价=测量时间 7s→14s（×2）、要求两测间信号平稳——**恰是我们"测量窗口内不切换"硬约束买不起的**（P1 必要性论证的最佳正文引文）；
- **电桥法代价**：自动平衡电桥需要整套零值检波+反馈（Keysight §2.3.2）；4TP 严格遵守到 DUT 端才有 <1mΩ 能力（printed 3-6）；
- **IC 法代价**：0.005% 激光修调薄膜电阻+自举电路（Whitlock p.5）。

### A4. 计量谱系的深层定理（新发现，P1 的 DC 祖先）

- **Thomas 1948 eq(11) 比率匹配消去**：X = S·A/B + [b(A/B−a/b)/(a+b+L)]·L——"That last term can be made zero by making **a/b = A/B, irrespective of the value of the link resistance, L**"（印刷 p.17）；引线比=臂比则 "balance would be independent of the actual values of the lead resistances"（p.23）。
- Stimson（SP300 Vol2 印刷 pp.131–132）：比率臂失配 10⁻³ 经正反换向合计误差 10⁻⁶（换向链）。
- Hall p.13："a resistance bridge with a Wagner balance is **the topological dual of the Kelvin bridge**"——守卫与四端的对偶性正文定论。
- **P1 反例搜索（全部 28 篇正文）：阴性**。无一处给出"无源 RC 差分梯形失配→CM 转 DM 消去条件"的推导。最近邻两类：Thomas 的 DC 比率匹配（〇-3 划界）、sprpeo2/AN048 的单级配方（〇-2/A2 划界）。

---

## B. 空位矩阵 v2（正文级划界）

| 主张 | 最近前人（正文引文） | 缺口 | 写作红线 |
|---|---|---|---|
| **P1 消去条件** | Thomas 1948 DC 比率匹配（p.17）；sprpeo2 单级容差/比例（p.44/46）；AN048 镜像复制（p.1）；Whitlock Zcm 框架（p.2-4）；Hornero G_DC=G₂−G₁+"应避免" | **AC 多级梯形的复频系数匹配条件**（逐级 τ 不充分、整线同偏充分；配对矩阵 51 vs 90.5 dB 实证）+ **与 Zcm 载荷通道的分离** | 不得说"单级无处理"（sprpeo2 有）；不得说"匹配条件无先例"（Thomas DC 版有）；必须分双机理 |
| **P2 结构地板** | 4TP/Kelvin 结构正文（Cutkosky1970 p.65-66、Keysight printed 3-4/3-6）；Ji 的 120dB 不够（p.12） | 函数类论证+量化地板（56 dB 恒定实证） | 不得说"失配退化无建模"（Smither 1982 有） |
| **P3 可达界** | an699 阶数-衰减配方表（p.5/9）；sprpeo2 电荷桶配方（p.27） | (D4∧D1) 约束对的解析边界（76dB<80 实证） | 专项化表述，挂 Bode 积分谱系 |
| 方法学 | sboa114 噪声预算路线（p.5 Eq.9）——正文证实无失配/CMRR | 门槛化 AAF 比较+真实占地 | — |

---

## C. 结论 v2（每条落正文/CSV 证据）

1. **P1（修订版）**：N 阶无源差分 RC 梯形有两条独立退化通道——(a) 失配致 G_DC≠0，消去条件=两线传递函数**系数全等**（单级退化为 Thomas 1948 式比率匹配，多级含 R1·C2 交叉项故逐级 τ 不充分；实证 51 vs 90.5 dB）；(b) **Zcm 载荷**（Whitlock 机理）：对地 C_G 即使完美匹配也拉低共模阻抗、放大源失配敏感度——T2 的 C_G 属此通道，须靠布局/自举/高 Zcm 缓解。**匹配只治 (a) 不治 (b)**。
2. **P2**：Kelvin 无源负端使 H_N/H_P 函数类不同，地板 ≈56 dB（六案恒定）；计量界的 4TP/自动平衡电桥以结构定义或主动置零绕开（正文证实），低成本双电极方案逃不掉。
3. **P3**：D4≤0.5dB 钉死 fc → 无源 N≤2 衰减上界 76dB<80；(D1∧D4) 联合不可行有解析边界（an699 配方表反证其只在阶数轴上枚举，无约束对论证）。
4. **必要性引文链**（正文级）：反相消 CM 代价=时间×2（Ji p.76-77）→ 测量窗口内不可用；电桥/IC 代价=整套有源/工艺（Keysight §2.3.2、Whitlock p.5）→ 成本敏感场景不可用；**剩给板级无源网络的正是 P1 的条件**。
5. **CTSD 门**（勘误后）：AIN 无强制滤波（干净），但 Rs 分压温漂+通道间相位议题仍在（tutorial p.19/22）；对高阻样品仍需缓冲。
6. **应用需求诚实化**：SHM 原型（Augustin）信号 % 级、无前端——我们仪器是通用平台，精度论据不引应用拉。
7. **知识社会学解**（正文加固）：各谱系"结构消去/定义免疫/主动置零/配方复制"四类解法各自够用；28 篇正文 P1 反例全阴性——空白是需求结构的产物。

---

## 附：精读笔记索引（15 份，全部原文+页码）

`paper/reading-notes/`：H2_whitlock2004_new（我读）、H7_cutkosky1961/1970、H7_dunfee1963、H7_guildner1965、H7_thomas1948、H7_hall_a、H7_keysight_7400_manuals、H2_ji2016、H6_augustin2018、H5_ti_sprpeo2、H4_ti_sboa114、H2_ti_sbaa230、H1_microchip_an699、H3_ti_snaa098、H1_green2003/H1_2025_an0556/H1_2022_ak5578en/H1_2021_es9038pr、H3_ad4134、H3_adi_ctsd_tutorial、H5_jssc2005、H2_burdett2008、H6_khan2013、H7_nbs_sp300_v2v6v9。

**未读到正文的**（诚实声明）：TI 三指南（纯扫描件）、Hornero（已读）以外的全部付费墙条目（P0 20 篇在 unfetched-papers.csv）；SP300 真电学卷 Vol3/4 不在库（卷册勘误见〇-5）。
