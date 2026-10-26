# P1 论文 IMRaD 大纲 v2（2026-10-26 · 按文献终盘 168 条重排）

> 取代 `docs/design/2026-10-25-信号链论文构思.md` §C（该节保留为 v1 历史）。
> 引用槽位：**粗体 = A 级 19 条**（必须引用并划界）；普通 = B 级择用；C 级只在"现状证据"段。
> 数据来源：`hardware/sim/signalchain/aaf_pkg_review/`（主）+ `fo1_rc_review/`（一阶基线与先行轮）。

## 题名（候选三则）

1. *Gated selection of passive anti-aliasing networks for switched-capacitor ΣΔ front ends: pairing invariants, structural limits, and a reachability bound*
2. *Reachability and matching limits of passive anti-aliasing RC networks in ratiometric ΣΔ measurement systems*
3. *Anti-aliasing network selection under simultaneous flatness, attenuation, CMRR, and footprint constraints: a gated multi-objective evaluation*（备用，最保守）

推荐 **1**：题名即三贡献（配对不变量/结构地板/可达界），label 式无废词。

## 摘要（四步，≤250 词，写作期最后定稿）

目标 → 方法（门槛化三层验证 + EDA 实画占地）→ 结果（六案总表 + 配对矩阵 + 56 dB 地板 + 76 dB 可达界 + 占地反转）→ 结论（无源一/二阶 D1/D3 与 D4 互斥；整线同 m 恢复 CMRR；Kelvin 通道结构受限）。

## Introduction（漏斗六段，~350 词，现在时）

| 段 | 内容（move） | 引用槽位 |
|---|---|---|
| I1 | 压阻纳米复合 SHM 的测量需求与应用热度（钩子） | chung1998selfmon（起点）→ **nauman2021**（综述）→ wen2000piezore / dharap2004flexura（前三步）→ razbin2025 / singh2026（最新）；测量硬件短板：dinesh2021、khalifeh2022mcu、nedelcu2022platform |
| I2 | 比值式双通道 ΣΔ 测量仪的谱系（本文仪器所属 lineage） | **inose1963a** → candy1981the/1985 → **norsworthy1996deltasi**；仪放/差分链 wurcer1982a；成像同构 barber1984applied；比率计量 cage1985a |
| I3 | COTS 开关电容 ΣΔ 的板级 AAF 现状 = 配方化 | C 级靶子组：ti_threeguidelines2015（正面引，单级公式出处）、ti_sprpeo2、microchip2001an699、ti_sbaa230；"单极通常够用"共识点名 |
| I4 | 学术侧已有三层，均不覆盖板级无源多目标选型 | 失配-CMR 定性层：**hornero2021cm**、**pallasareny1991cmrr**、**pallasareny1991cascaded**、**casas1996basics**；CT-ΣΔ 芯片层：**pavan2011**、ct_cascaded_implicit_aa(ct_cascaded)、manivannan2018、breems2023ctsd；片上集成/放宽驱动：koh2004、**kumar2021**；传感接口 ΣΔ：catania2022、basu2020、couriol2021 |
| I5 | 缺口：三个未答之问（= SQ2/SQ3/SQ1 的缺口化表述）+ 理论地基缺席 | 灵敏度/统计设计谱系：**orchard1966inducto**、**director1969the**、odwyer2009an、lee2012stochas（配对与漂移有理论无板级结论） |
| I6 | 本文贡献四条 + 组织 | （无引用；贡献句与题名三件套一一对应） |

四贡献（与题名锁定，全文不再增减）：
1. 门槛化多目标评估流程（D1–D10/C9 + 三层验证 + T00 回归锚定 + EDA 实画占地）；
2. 多级差分 RC 的**配对不变量**（整线同 m ⇒ G_DC≡0；逐级配 51 dB vs 整线 90.5 dB 实证）；
3. Kelvin 无源负端通道的**共模结构地板**（≈56 dB，与配对无关，拓扑决定）；
4. 通带平坦度约束下无源一/二阶衰减的**可达性边界**（两阶理想 ≈76 dB < 80 dB，D4–D1/D3 互斥）。

## Methods（子节与 Results 一一镜像；过去时）

| 子节 | 内容 | 引用槽位 |
|---|---|---|
| M1 装置背景 | 恒流激励 + 双通道同步比值（一段带过，指向 P2） | （引 P2 占位）；**norsworthy1996deltasi**（sinc³/OSR 口径） |
| M2 门槛定义 | D1–D10/C9 表（Table 1）；门槛不降原则 | ti_threeguidelines2015（D 口径的工程前身） |
| M3 三层验证架构 | L1 解析/线性 MC → L2 真实宏模型 LTspice（OPAx388 + Kelvin 真实接线 + ADC 等效负载/采样开关）→ L3 离线 sinc³；T00 锚定回归 | **hornero2021cm**（G_DC(s)=G₂−G₁ 解析式出处，L1 用其式）；ti_sprpeo2 / mccreary1975allmos / caves1977sampled（kickback/SC 口径） |
| M4 容差与配对协议 | 模式 A 未配对（n=1000 MC + ≥30 LTspice 角点）/ 模式 B 逐级各自配 / **整线同 m**；R±1%、C±5%/±1% | **director1969the**、**orchard1966inducto**（灵敏度谱系）；odwyer2009an（薄膜匹配模型）、lee2012stochas（漂移）、lasertrim1976 |
| M5 CMRR 双口径 | RC 自身（CH0）vs 整链 Kelvin（CH1 负端无源直连）；求解器数值底不作证据 | **casas1996basics**、**pallasareny1991cascaded**（级联 CMRR 组合的既有结论及失效条件）、gasulla2002cmresp、serranofinetti2019cmnoise |
| M6 kickback 与高频注入 | 3.5 pF 双相 50% 采样开关、Ron∈{1,100,1000}Ω 声明假设扫值；4.096/16.384 MHz ±{1,8,16}k 注入 | mccreary1975allmos / caves1977sampled / gregorian1986mos（SC 谱系）；mayes2015（输入电流先例） |
| M7 真实占地测量 | EasyEDA 工程副本实画 + 逐件读回断言；本体面积 vs 铜包围框双口径 | （方法自含，无先例=可写一句"至我们所知无先例"） |
| M8 案例设定 | 六方案 S0/S1/T1–T4（含首板采纳背景）+ 四级/三级历史案作参照锚 | （数据自引仓库；不引外文） |

## Results（与 M2–M8 镜像；过去时；每小节一个表或图）

R1 基线回归（T00 六锚定值全中）；R2 六案判定总表（Table 2，D1–D10/C9 PASS/FAIL/NOT VERIFIED 全列）；R3 配对矩阵（Table 3 + Fig.5 箱线：未配对 33 / 逐级 51 / 整线 90.5 dB——**全文核心图**）；R4 Kelvin 地板 56.08–56.31 dB（六案相同）；R5 占地 Pareto（Fig.6：二阶全 0402 反小于一阶含 0805，32.62 vs 39.05 mm²）；R6 可达界推导与实测印证（两阶理想 76 dB；实测 62–64 dB 贴限）；R7 混叠有界风险（sinc³ 合成 −61~−64 dB；16.384M 瞬态 1.65–8.5×）。

## Discussion（四段）

| 段 | 论点 | 引用槽位 |
|---|---|---|
| Dsc1 | 配对不变量的机理层：对 Hornero"避免该拓扑"的建设性接续——"若必须保留，消去条件是什么" | **hornero2021cm**（正面划界）；**pallasareny1991cascaded** |
| Dsc2 | Kelvin 地板对比值式双通道系统的普适含义（凡负端无源直连即受限；仪放差分链不受此限——对照 wurcer1982a、zhang2020237（130dB CMRR IA）） | zhang2020237、wurcer1982a |
| Dsc3 | 可达性之外的四条出路：三阶无源（+7–8 mm²/通道）/ 有源（Q>0.5）/ AAF+sinc³ 合成口径 / CT-ΣΔ 芯片 | breems2023ctsd、lozada2025、wu2015（数字 AAF）、kumar2021 |
| Dsc4 | 局限（如实四条）：仿真-only；宏模型温度窗 25–27℃；Ron/vcm 无手册值；板内落位未验证 | （无引用，NOT VERIFIED 纪律直译） |

## 图表规划（DRAW 轨道，全部英文 Times New Roman）

Fig.1 测量架构与 Kelvin 非对称标注（schematic 重绘）；Fig.2 候选拓扑族（一阶/二阶梯形/参照四级）；Fig.3 验证流程图（三层+T00+门槛）；Fig.4 六案 DM/CM Bode 矩阵（t01/t02 CSV）；**Fig.5 配对模式箱线图（核心图，t06 CSV）**；Fig.6 占地–电气 Pareto（layout 数据）；Table 1 门槛定义；Table 2 六案判定总表；Table 3 配对矩阵。

## 写作顺序与门禁（howtoSCI 流程）

Methods（M2–M8，最易）→ Results → Discussion → Introduction（引文槽位照上表填）→ Abstract/Title 收尾；
每段过 `scripts/lint_contract.py`（slots → grade → min-a=90）+ 三专家面板 L/G/F，A/B 放行；
图走 DRAW 轨道（`figure-style.md` §11 门禁 + 目视）。
