# 挖掘简报（第十二轮工作流用 · 2026-10-26）

## 任务背景（一句话）
为 P1 论文《无源差分抗混叠网络的极限》穷尽前人工作：核心主张是"多级无源 RC 梯形在开关电容 ΣΔ 负载下的全频段共模消去条件（P1）、Kelvin 无源负端结构地板（P2）、平坦度约束下的衰减可达界（P3）未见于任何谱系"——你的任务是**找反例**：任何一族文献若已给出等价结果，立即标记 killRisk。

## 已挖谱系（勿重复，只做增量）
电话纵向平衡（bell1978/IEEE820）、音频阻抗平衡（muncy1995）、生物电电极失衡（huhta1973 + Webster 教材单频式）、RF 混模 S 参数（bockelman1995）、EMC 不平衡因子 h（keller2022）、TI/ADI 配方（three_guidelines/sbaa230/sboa114/AN699/sprpeo2）、经典灵敏度（orchard1966/director1969）、SC 电容比设计（gregorian1986）、Bartlett 平分定理（fujishiro2017 扩展）、Blumlein TRA 电桥（guildner1965/magerlein1975）、自动平衡电桥（Keysight 手册）、Wenner 1912/NBS 文集、Hornero2021/Pallàs-Areny1991×2/Casas1996、CT-ΣΔ（pavan2011/keller2007/breems2023/ritter2015/manivannan2018）、DT 近邻（kumar2021/denisenko2020）。
**已试查询黑名单**（换措辞）："differential anti-aliasing filter mismatch CMRR"、"cascaded passive differential filter matching"、"Bartlett bisection"、"auto-balancing bridge impedance"、"EMI filter imbalance factor"、"switched capacitor ladder capacitor ratio"、"longitudinal balance telephone"、"CTSD alias rejection"、"Muncy noise susceptibility"、"Huhta Webster 60-Hz"。

## 已有 bib（去重用）
读 `paper/literature.bib`（约 190 条，含全部 key 与 DOI）。凡 DOI/题名已存在 = duplicate，不报。

## 输出格式（每条 find）
axis(H1-H8)/title/authors/year/venue/doiOrUrl/oneLine(一句话内容及与本论文的关系)/tier(A 核心·B 支撑·C 现状)/killRisk(空 或 威胁哪条主张+证据 URL)。
**每路书架最多 8 条**，宁缺毋滥；查不到就如实返回空 finds + queriesTried。

## 铁律
题录不得凭记忆编造：每条必须有可核实的 DOI/URL；正文全文拿不到时给摘要级证据；付费墙标"仅摘要"。发现 killRisk 级条目时在该条 killRisk 字段里写明"为何威胁 + 证据链接"，不要自行下结论放弃任务。
