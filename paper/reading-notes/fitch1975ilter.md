# 精读笔记 · Fitch 1975《Filter Selection Based on Component Sensitivity Analysis》（SAE 750847）

> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> **⚠️ 领域判读：这是一篇液压/流体动力（fluid power）污染控制论文**——"filter" = 油液过滤器，"component sensitivity" = **液压泵对颗粒污染物的敏感度**，与电路/网络滤波器的元件灵敏度分析**无关**。题名极易误读，收录 H8 轴属题名匹配的内容错位，本笔记如实记录。

## 出处
- Fitch, E. C.（Fluid Power Research Center, Oklahoma State University）. "Filter Selection Based on Component Sensitivity Analysis." SAE Technical Paper 750847, *1975 SAE Off-Highway Vehicle Meeting*, Milwaukee, Wisconsin, September 8–11, 1975. DOI: 10.4271/750847.
- PDF：`/home/anning/Documents/Obsidian Vault/20-硬件工程/10-项目设计/p1-文献谱系/fulltext/H8-灵敏度与统计电路设计/fitch1975ilter.pdf`（10 页 = 封面 + 版权页 + 正文 7 页 + SAE 声明页；正文自印页码 1–7，下文页码 = PDF 物理页 1–10）。文字层完整（下载水印行除外）。

## 核心命题（原文）
1. **方法立意：由两项测试标准催生的"按应用严重度 + 组件敏感度 + 过滤器捕获能力"三要素选型法**（p.3 摘要）：> "As a result of the advancement of two significant test procedures - the Multi-Pass Test for Filters and the Contaminant Sensitivity Test for Components, a totally new filter selection method has evolved. This method considers the severity of the application, the sensitivity of the components, and the particle capturecapability of a filter."（两测试 = ISO Multi-Pass Filter Performance Test 与 NFPA Pump Contaminant Sensitivity Procedure，p.3。）
2. **泵的"敏感度"定义为流量退化曲线/生存率百分位**（p.3）：> "The flow degradation ratio is the flow rate of the pump after exposure to the corresponding dust size range divided by its rated or initial flow rate. A given survival line on a pump survivability graph represents the flow degradation curve which is exceeded by the indicated percent of all pumps tested under rated operating conditions."（敏感度图 = 按粉尘粒径的流量退化比 + 生存率分位数——"sensitivity" 在此处是统计分位意义，非电路灵敏度函数。）
3. **选型不应听销售员，须先定四要素**（p.3）：> "Selecting a filter to protect a given pump should not be done by polling the filter salesman. There are four fundament al factors which must be ascertained before anyone can help."（四要素：泵对污染物的固有敏感度、运行条件、运行环境与机器状态、服役寿命判据。）
4. **压力升高显著恶化污染物敏感度**（p.4）：> "The study in Ref. [5] showed that, even where pumps were specifically designed for higher operating pressures, their contaminant sensitivity increased markedly with an increase in pressure."（叶片泵例：2000 psi 时为 50% 生存单元，2500 psi 恶化为 70%，3000 psi 恶化为 83%——p.4。）
5. **80% 流量退化比作为工业判据 + 选型图族**（p.5）：> "Based upon the views of system designers and users, a value of 80% has been used normally as an industrial guide. Hence, throughout this paper, an 80% reference ratio is used with respect to service life estimates."；> "To illustrate such charts, three filters are used which exhibit Beta ten ratings of 2.0, 10, and 100, as defined in Ref. [5]."（β₁₀ = 2/10/100 三档过滤器在压力 × 污染侵入率平面上的选型图。）
6. **结论与精度自评**（p.9）：> "This paper has advanced a totally new approach for making a filter selection to protect a hydraulic pump."；> "Although the author feels that the graphs presented in this paper are as accurate as statistical data permit, they cannot be as precise as those which the manufacturer can develop for his specific products."

## 关键数值（原文）
- 生存率示例（p.3）：> "70% of all pumps on the market today (a 70% survivability pump) will not de grade more than 0.1% under the standard test conditions when 0-10 micrometre dust is injected or more than 2.0% when 0-20 micrometre dust is injected."
- 压力档（p.4）：1500 / 2250 / 3000 psi（柱塞泵 50% 生存线对比，Fig.4）；叶片泵 2000/2500/3000 psi → 50%/70%/83% 生存单元。
- 测试油温（p.4）：Mil-L-2104 油、150 °F（>200 °F 为严酷、120 °F 为温和之间的折中）。
- 侵入率（p.5）：> "A value for ingression (R1) of 10⁸ particles greater than 10 micrometres per minute is an average for con struction type machinery."（OCR 印 "10*"，按上下文为 10⁸。）
- 参考服役寿命（p.5）：1000 小时污染物寿命（Figs.11–13、19–21）。
- 工业判据：80% 流量退化比（p.5）。

## 对 P1/P2/P3 的对照
- **P1（消去条件/失配→G_DC）**：**无**。全文无电路、无传递函数、无元件容差→响应偏差的数学；"sensitivity" 一词的语义（泵对颗粒污染的统计耐受分位）与电路灵敏度（∂T/∂x）完全不同源。
- **P2（Kelvin 结构地板）**：无。
- **P3（平坦度约束衰减上界）**：**无**。"Filter" 全指油液过滤器（β₁₀ 额定、Multi-Pass 测试），不涉任何频率响应/衰减/平坦度。
- **方法学（D1–D10）**：极低。唯一可类比处：其"组件敏感度统计分位 + 应用严重度 → 选型图"的图表化选型思路，形似器件降额曲线/门槛判据表，但属不同工程领域的平行物，引用价值近零。
- **killRisk**：无威胁。**反向风险仅在于误引**：若 P1/P3 行文按题名把它当"电路滤波器元件灵敏度选型"文献引用即成错误——正确处置是在文献谱系中标注为"题名误导的液压域离群项"，不作任何理论引用。
- **H8 轴定位修正建议**：该篇不构成 H8 轴③"滤波器设计"的成员，建议在谱系图中降权或移出（由主代理定夺，本文笔记只做如实记录）。

## 没读到的
- 全部 15 张图（Fig.1 生存率图至 Fig.22 定压泵特图）只有文字转述，未从图上提取曲线数值（p.6 为整页图版，扫描分辨率下曲线刻度不可辨）。
- 参考文献 [1]–[5]（ISO B93.31-1973、Fitch 1974 多篇、Fitch & Tessmann 1975 Tribology 会议）未读——β₁₀ 额定与生存率方法的原始定义在其中。
- NFPA 泵污染物敏感度程序的完整测试流程（文中仅述要点）。
