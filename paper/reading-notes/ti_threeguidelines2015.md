# 精读笔记 · Andrews 2015《Three Guidelines for Designing Anti-Aliasing Filters》（TI Precision Hub Blog, 2015-03-24）

> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> ⚠️ **文档形态与读法声明**：本地 PDF 为**无文本层的网页打印扫描版**（7 页）。按图片版流程处理：`pdftoppm -png -r 110` 渲染 → 视觉模型逐页转录。**短句引文为逐字；跨行长句为视觉转录重建（文字可能与原件有微小出入，落论文引用前建议对照线上原件核对一次）**。页码 = PDF 页（网页打印无刊印页码）。p.7 近空白（仅页脚）。
> **killRisk 条目本体**：本文即"单级差分 RC 失配-CMRR 公式"的真实出处（此前误归 SBAA230 已勘误）——失配机理句与差分/共模截止公式均在 p.4，已逐字提取于下。

## 出处

- Ryan Andrews（TI 应用工程师，precision ADC 方向），"Three Guidelines for Designing Anti-Aliasing Filters"，TI Precision Hub Blog，发表于 **2015 年 3 月 24 日**（p.1 署名行："Posted by Andrews, Ryan on 24 Mar 2015"）。
- 线上原件：e2e.ti.com Precision Hub 博客存档（bib `ti_threeguidelines2015` 的 url 字段）。
- bib key：`ti_threeguidelines2015`（H2 轴——**killRisk 登记**：单级差分 RC 失配-CMRR 论述的真实出处）。

## 核心命题（原文）

1. **三条准则总纲（p.1 引言）**：
   > "In this series I'll discuss three guidelines that you can use to avoid [these] anti-aliasing filter design pitfalls."
   （p.6 "Summary and Conclusions" 重申版——三条并列、逐字转录：**"1. Filter as close to the ADC as possible. 2. Attenuation ≥ the system's resolution at f_s. 3. Use the lowest-order topology that can meet the requirements."**〔视觉转录〕）

2. **准则一（p.2，节标题 "Filter in the wrong place"）**：
   > "If possible, filter as close to the signal chain's ADC as possible."
   （AAF 尽量靠近 ADC 放置，防止 ADC 前的支路再捡噪声。）

3. **准则二（p.3，节标题 "Not enough filtering"）**：
   > 问句形式："How much attenuation is needed at the sampling frequency?"
   > 答案句〔视觉转录〕："attenuation equal to or greater than the ADC's resolution at that frequency, so that the aliased signal will be less than 1 LSB … e.g. a 16-bit ADC needs >96 dB."
   （衰减判据 = 混叠残余 < 1 LSB，数值上 ≈ 位分辨率 dB 数；16 bit ↔ >96 dB。）

4. **准则三（p.4，节标题 "Using an inappropriate filter topology"）**：
   > "Select the anti-aliasing filter topology appropriate for the system requirements."

5. **★ killRisk 核心：差分 RC 的两个截止频率公式（p.4，差分输入 ADC 段）**〔视觉转录，公式逐字〕：
   > 差分截止："f_3dB(differential) = 1 / (2πR·(C1 + C2))"
   > 共模截止："f_3dB(common-mode) = 1 / (2πR·C)，其中 C ≈ C1 ≈ C2"（两只对地电容情形）。
   （即：对地双电容结构中，差分模看到的等效电容是 **C1+C2（串联跨接视角）**，共模看到的是每边各自的对地 C——两种截止频率由 C1、C2 取值关系**分别**设定。）

6. **★ killRisk 核心：失配-CMRR 机理句（p.4）**〔视觉转录〕：
   > "Capacitor mismatch will couple common-mode noise into the differential signal, reducing CMRR."
   > 对照优点句：单个（跨接在两输入间的）差分电容器 "is inherently self-matched"（天然自匹配——不存在两元件失配问题）。
   （**这就是 P1 消去条件在单级差分 RC 上的失配机理出处**：两侧对地 RC 不匹配 ⇒ 共模→差分转换 ⇒ CMRR 受损；单个跨接 C 则结构上免失配。注意：**博客只给出机理句与截止公式，未给出显式 CMRR(dB) = f(失配%) 解析式**——若 P1 论文中出现 ε→CMRR 的定量公式，其出处需另行溯源，勿再引本文〔见 killRisk 判断〕。）

7. **示例选型（p.5 "Examples"，视觉转录）**：示例覆盖 LP Sallen-Key、MFB（多路反馈）与差分滤波器三类；**最终设计选用差分 RC 滤波器、配置为每边一只对地电容（two capacitors to ground, one per input line）**——与 p.4 "单跨接电容自匹配"论点形成取舍：双对地电容可独立设定共模截止频率，代价是引入失配敏感。

## 关键数值（原文）

- 16-bit ADC 在 f_s 处需要 **>96 dB** 衰减（准则二示例，p.3/p.6）。
- f_3dB(differential) = 1/(2πR(C1+C2))；f_3dB(common-mode) = 1/(2πRC)，C≈C1≈C2（p.4）。
- 其余具体 R/C 取值、示波图刻度：未逐项转录（见"没读到的"）。

## 对 P1/P2/P3 的对照

- **P1（消去条件 G_DC(s)=H_N−H_P≡0）**：高相关（killRisk 本体）。本文提供 P1 讨论单级差分 RC 失配的**业界共识级出处**：①差分/共模两个截止由 C1、C2 分别设定（p.4 公式）——单级情形两截止解耦、可独立配平；②失配 ⇒ 共模→差分转换 ⇒ CMRR 退化（p.4 机理句）；③结构替代方案存在：单跨接差分电容 "inherently self-matched"（免失配的结构解，与 Ranjbar "降阶分子"、Pavan "隔离泄漏通道"同属'改结构优于拼匹配'谱系）。**边界必须写清**：本文止于机理句，无 ε→CMRR 定量公式、无频率依赖（s 域）展开——P1 若需"G_DC(s) 全频段"层面的公式，本文只能作动因引文，不能作数学出处。
- **P2（Kelvin 结构地板 ≈56 dB）**：中相关。失配-CMRR 机理句是 Kelvin/差分结构地板论的博客级共识背书（结构给定后，地板由两侧元件失配决定）；但本文无数值地板、无 56 dB 字样。
- **P3（平坦度约束衰减上界）**：中相关。准则二给出**衰减需求判据的原型**（混叠残余 < 1 LSB ⇒ 衰减 ≥ 位分辨率 dB）与准则三"最低阶拓扑满足要求"——P3 上界论证的判据句可引此处（注意它是需求侧判据，不是可达性上界证明）。
- **方法学（D1–D10）**：中高。三条 guidelines 本身即"门槛化清单"形态（位置门槛 / 衰减门槛 / 阶数门槛），D 系文献综述可用作工业实践基线；16 bit↔96 dB 的换算示例是门槛数值化的现成模板。
- **killRisk 判断**：**部分解除、部分新开**。(a) 已解除：单级差分 RC"失配⇒CMRR 退化"机理与双截止公式的出处确认为本文 p.4（非 SBAA230——SBAA230 实为数字滤波器口径，见 `H2_ti_sbaa230_differential_aaf.md` 勘误）。(b) **新开待办**：若 P1 论文正文写有"失配百分比 → CMRR dB"的**定量公式**，该公式出处**不是**本文（本文只有机理句）——需继续溯源（候选：TI Precision Labs 讲义、SBAA 系列、或 Pallas-Areny 学派 CMRR 解析），防止二次误归。(c) 引文风险：本文为博客（非同行评审），P1 论文引用时建议标注为应用工程实践来源，与期刊证据链并用。

## 没读到的

- 原件全文字级校对（本文引文经视觉转录，长句可能有微小措辞差；线上原件可核对——待核）。
- p.5 示例电路的具体 R/C 数值与仿真曲线读数；p.2 中间论述细节（为何靠近 ADC 的完整论证段落）——受转录预算限制未逐句提取。
- 网页版可能的评论区讨论（打印版未含或未转录；TI 博客评论区常含勘误与追问，**待核**）。
