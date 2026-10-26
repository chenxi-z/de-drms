# P1 论文研究框架 v3（2026-10-26 · 命题驱动重构，取代 v2）

> **重构原则**：主角是问题结构（文献揭示的矛盾），不是我们的工程动作。全部仿真/占地数据降格为
> 命题验证证据；仪器本身只作 case context 一段带过。引用 key 与 bib 逐一对齐（幽灵门禁 PASS）。

## 〇、研究框架（从文献矛盾中导出）

**矛盾**（文献两端各说各话，中间空着）：

- 差分测量主线（Pallàs-Areny 1991 → Casas 1996 → Hornero 2021）：共模抑制由无源件匹配决定，
  带内即恶化、级联更糟；**终审忠告 = 回避**——"避免使共模响应依赖无源匹配的拓扑"；
- COTS 开关电容 ΣΔ 现实（TI/ADI 手册配方线）：芯片输入端**必须**外挂无源 RC（抗混叠 +
  kickback 缓冲），即**回避不可行**；sinc³ 只在 fMOD 邻域兜底，"单极通常够用"是未经定量检验的共识。

**回避不可行时，工程没有理论可用**。由此导出三个命题（本文的全部内容）：

- **P1（消去条件）**：何时元件选择能使 G_DC(s) = H_N(s) − H_P(s) 恒等于零？
  ——单级：τ=R·C 匹配充要；梯形：传递函数是系数向量，逐级 τ 匹配**不再充分**
  （R1·C2 交叉项暴露二阶系数失配；实测逐级配 51 dB vs 整线同偏 90.5 dB）。
  **写作任务：符号推导（sympy）系数匹配条件，MC/LTspice 角点作验证。**
- **P2（结构地板）**：拓扑不对称（负端 Kelvin 无源直连、正端缓冲）时，H_N 与 H_P
  是**结构不同类**的函数，任何元件取值都不能使 G_DC≡0——共模抑制存在与配对无关的
  拓扑地板（实测 ≈56 dB，六案相同）。**含义：凡负端无源直连的比值式双通道系统皆受限。**
- **P3（可达边界）**：通带平坦度约束把 f_c 钉死（D4≤0.5 dB ⇒ f_c≲70 kHz @16 kHz 带宽点），
  则 N 阶无源梯形在 f_MOD 的衰减存在解析上界（两阶理想 ≈76 dB < 80；实测 62–64 贴限）。
  **即 D1≥80 与 D4≤0.5 在无源 N≤2 联合不可行——no-go 结果。**

**贡献四条（与题名锁定）**：P1/P2/P3 三命题 + 门槛化验证方法学（含真实占地口径）。

## 题名（理论先行，候选三则）

1. *Limits of passive differential anti-aliasing networks at switched-capacitor ΣΔ inputs: cancellation conditions, structural floors, and a reachability bound*
2. *When matching cannot save you: common-mode and attenuation limits of passive RC ladders in ratiometric ΣΔ measurement*（口语化，备用）
3. *A quantitative limit theory for board-level passive anti-aliasing networks of COTS ΣΔ converters*（最保守）

推荐 **1**。

## Introduction（六段漏斗，现在时；每段一个文献动作）

| 段 | 文献动作 | 引用槽 |
|---|---|---|
| I1 | 差分/比值测量为何 Everywhere（传感、仪器、成像），共模是其共同敌人 | **pallasareny1991cmrr**、**casas1996basics**、wurcer1982a、barber1984applied（成像同构） |
| I2 | 已知结论：共模增益来自失配、带内恶化、级联累积——谱系陈述 | **pallasareny1991cascaded**、**hornero2021cm**（G_DC=G₂−G₁ 解析）、gasulla2002cmresp、serranofinetti2019cmnoise、giustolisi2000cmrr |
| I3 | 学术界的回答 = 回避（引 Hornero 结论原句）；但灵敏度理论只给了"最坏情况"工具，没给"消去条件"答案 | **hornero2021cm**、**orchard1966inducto**、**director1969the**（工具谱系）、odwyer2009an、lee2012stochas |
| I4 | 现实约束端：COTS SC-ΣΔ 强制无源 RC（配方文献群 + "单极够用"共识）；SC 负荷与 kickback 的历史（McCreary/Caves 起） | ti_threeguidelines2015、ti_sprpeo2、microchip2001an699、mccreary1975allmos、caves1977sampled、gregorian1986mos、mayes2015；CT-ΣΔ 出路预告 **breems2023ctsd**、**pavan2011** |
| I5 | 缺口命题化：回避不可行 ⇒ 需要定量极限理论（P1/P2/P3 三问）；现有传感接口 ΣΔ 均片上解决、不覆盖板级 | **kumar2021**、catania2022、basu2020、couriol2021、koh2004、**norsworthy1996deltasi**、inose1963a（谱系起） |
| I6 | 本文：三命题 + 验证方法学 + 六网络案例作为证据；组织结构 | （无引用） |

## Theoretical framework（新增主节，符号层）

T1 系统模型：无源差分梯形 + 开关电容等效负荷；G_DM 与 G_DC 定义（沿 Hornero 记号）。
T2 P1 推导：**理论家族覆盖三类网络**——(a) 对地电容梯形（本文案例族）、(b) 纯桥电容（大 C_d/无 C_cm：理想对称源下
  G_DC≡0 结构性成立，即 TI Three Guidelines 准则的理论依据）、(c) 混合（大 C_d + 小 C_cm：失配敏感性按 C_cm 权重回归，
  系数匹配条件给出量化）。τ-匹配 vs 系数-匹配的包含关系；"整线同偏"充分条件。（sympy 推导，细节入附录）
T3 P2 推导：缓冲支路 H(s) 与无源直连支路 H(s) 的函数类差异 ⇒ G_DC 结构非零；
给出地板的量级式并与实测对照。
T4 P3 推导：平坦度约束 → f_c 上界 → N 阶衰减上界（含级间负荷损耗项）；两阶数值例。

## Validation methodology（原 Methods，全部降格为"验证工具"）

V1 门槛化判据（D1–D10/C9，Table 1）；V2 三层验证（L1 解析/MC、L2 宏模型 LTspice、L3 sinc³ 离线）
+ T00 锚定回归；V3 配对协议三模式（未配对/逐级 τ/整线同偏；n=1000 MC + ≥30 角点）；
V4 kickback/注入协议（Ron 声明假设扫值）；V5 真实占地口径（EDA 实画 + 读回断言）。
仪器 case context：恒流+双通道比值一段带过（不展开工程细节，引数据目录即可）。

## Case study & results（证据层；表图同 v2）

R1 基线回归；R2 六网络判定总表（Table 2）；R3 **P1 证据**：配对矩阵（Table 3 + Fig.5 核心图）；
R4 **P2 证据**：Kelvin 地板六案恒定（叙事框架：省一颗缓冲的"经济性选择"之代价量化，成本敏感设计常见）；R5 Pareto（占地反转——工程价值点，一段即可）；
R6 **P3 证据**：实测衰减贴理想上界曲线（Fig.4 叠界线）；R7 混叠有界风险（sinc³ 合成不足以替代）。

## Discussion（四段）

D1 对 Hornero 的建设性接续（"回避不可能时的消去条件"——P1+P2 合并陈述）；
D2 设计规则外推：凡负端无源直连的比值式双通道系统（含 EIT/ERT 一族）受 P2 约束——
仪放差分链不受此限（对照 wurcer1982a、zhang2020237）；
D3 **三扇逃生门与各自残余**（2026-10-26 质询后重写）：
  门一 CT-ΣΔ 芯片（adi_ad4134/AD7134：阻性输入+内在抗混叠+4 通道同步——P3/D9 在需求层消失；
  残余：6 kΩ 输入重负载仍需缓冲、Kelvin 源不对称 P2 不随 ADC 消失、单源/成本；breems2023ctsd、pavan2011 谱系）；
  门二 纯桥电容网络（TI 准则本身：对称缓冲源下结构性零 CM→DM；残余：引脚 CM 无防护、Kelvin 源不对称
  使极点结构失配回归、加回 C_cm 即失配回归——量化由 P1 家族(c)给出）；
  门三 片上缓冲/有源/数字合成（ADS1262 类缓冲只隔离 kickback 不消 fMOD AAF；三阶无源 +7–8 mm²/通道；
  sinc³ 合成实测不足；wu2015、kumar2021、lozada2025）。
  立场句：**逃生门各管一段，门后的缝正是本理论划定的**；
D4 局限四条如实（仿真-only、宏模型温度窗、Ron/vcm 假设、板内落位未验证）。

## 图表（同 v2 规划；新增 Fig.7：文献矛盾示意——回避忠告 vs 手册强制，框架图）

## 写作顺序与门禁

**先 T1–T4（符号推导，本文真正的新东西）→ 验证节 → 案例/结果 → 讨论 → Intro → 摘要/题名**；
每段 lint + L/G/F 面板 A/B 放行；推导代码入 `paper/derivations/`（sympy，可复核）。
