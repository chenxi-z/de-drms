# 精读笔记 · Lyu 2018《Multi-objective Bayesian Optimization for Analog/RF Circuit Synthesis》（DAC 2018，IEEE 双录版）

> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。

## 出处
- Lyu, Wenlong; Yang, Fan; Yan, Changhao; Zhou, Dian; Zeng, Xuan. "Multi-objective bayesian optimization for analog/RF circuit synthesis." *Proceedings of the 55th Annual Design Automation Conference*, 2018, pp. 1–6. DOI: 10.1145/3195970.3196078（bib 条目 lyu2018ultiobje2；同文另一条目 lyu2018ultiobje 标 IEEE DOI 10.1109/dac.2018.8465872）。
- PDF：`/home/anning/Documents/Obsidian Vault/20-硬件工程/10-项目设计/p1-文献谱系/fulltext/H8-灵敏度与统计电路设计/lyu2018ultiobje2.pdf`（6 页；PDF 元数据 Title 与正文首页题名一致，Creator: "Certified by IEEE PDFeXpress at 04/10/2018 10:40:55 AM"，Producer pdfTeX-1.40.16）。
- **核查结论：与 lyu2018ultiobje.pdf 为同一篇论文的两份拷贝**。两份 pdftotext 全文经去连字符+空白归一化后逐词比对，12 处 opcode 差异全部是双栏抽取顺序伪差（"where Λ = diag…"段与"3.1"节标题位置漂移），词袋差异仅 `Rm9` 被拆成 `R m9` 一处——**内容零差异**。bib 中两条 DOI（ACM 10.1145/3195970.3196078 与 IEEE 10.1109/dac.2018.8465872）是同一 DAC'18 论文的出版方双录，建议后续整理时合并条目（保留 ACM 版为主）。

## 核心命题（原文）
（内容与 lyu2018ultiobje.md 完全一致，此处仅摘两条用于版本比对锚定；完整命题清单见该笔记。）
1. **多目标总纲**（p.1）：> "Instead of optimizing a single objective and seeking for the single best design, multi-objective optimization methods try to find a set of uniformly distributed Pareto-optimal design to approximate the Pareto Front(PF) [15], which represents the most ambitious trade-off of the conflicting performances."（与 ACM 版逐字一致。）
2. **LCB 前沿收敛直觉**（p.3）：> "If the GP models are accurate, the Pareto front of the LCB functions would be same with the Pareto front of the problem (1), if the GP models are still inaccurate, the Pareto-optimal points of the LCB functions will reside in areas where the uncertainties are high."（与 ACM 版逐字一致。）

## 关键数值（原文）
- 与 lyu2018ultiobje.md 完全相同（κ=3；ZDT1/ZDT2：MOBO 300 vs GPMOOG 1800 / MOEA/D 3600 次评估；三级运放 SMIC 55nm 24 变量 400 vs 800 次仿真，Gain 98.93 dB/UGF 4.03 MHz/PM 131.15°；60 GHz 变压器 300 vs 350 次，PTE 84.34%/Area 64.27 µm²；2.5 GHz 功放 300 vs 500 次，Eff 65.12%/THD 5.90 dB/Pout 26.55 dBm；各 p 值 0.0016/0.0001/2.43e-12/5.70e-12/8.01e-11/3.78e-9）。

## 对 P1/P2/P3 的对照
- **P1/P2/P3/方法学**：判定与 lyu2018ultiobje.md 完全相同（P1 无、P2 无、P3 中——触及通用多目标 Pareto 框架但不做滤波器/无源网络、方法学中——昂贵黑箱仿真下的 MOBO 工具箱引用）。
- **killRisk**：无威胁。额外一条文献管理风险：**bib 双条目双 DOI 会造成引用计数/查重虚高**，P1 若同时引两条会被视为重复引用，应在 bibliography 阶段合并。

## 没读到的
- 无新增：全文与 lyu2018ultiobje.pdf 逐词一致，无独立新内容可读。未读项同该笔记（参考文献 [4] LCB 遗憾界、[21] Stehr/Graeb NBI、图 3/6 散点逐点数值）。
