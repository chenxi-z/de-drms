# 精读笔记 · Nesbitt 1971《The Synthesis and Analysis of Active RC Ladder Networks using the Recurrent-Continuant Method》（Radio and Electronic Engineer 41(2)）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
## 出处
- Nesbitt, Norman R. S.（University of Southampton 背景，致谢 Bloodworth & Holbrook）
- The Radio and Electronic Engineer, Vol. 41, No. 2, February 1971, pp. 65–72, doi:10.1049/ree.1971.0019
- PDF 为扫描版共 8 物理页（期刊页 65–72）。全文已读（OCR 矩阵数字有噪声，正文文字完整）。

## 核心命题（原文）
1. **由传函多项式经 recurrent（循环行列式）→ continuant（连分式行列式）两步变换完成有源 RC 梯形网络综合**（p.1，摘要）：> "Given the polynomial in s which describes the reciprocal of the transfer function of the circuit to be synthesized, the recurrent determinant may be determined. The continuant determinant is evaluated by a logical sequence of operations on the recurrent determinant."（这是单端有源 RC 梯形网络的行列式综合法，与差分/共模概念无关。）
2. **分析方向可逆：网络→continuant→recurrent→传函**（p.1）：> "The reverse procedure of producing the recurrent from the continuant is also described and from the recurrent the reciprocal of the transfer function of the network may be obtained."（双向算法是论文卖点。）
3. **元件变化下的电路分析是该法的主要应用**（p.8）：> "The problem of synthesizing and then analysing the performance of a circuit when its component values vary becomes no more difficult for a tenth-order filter than for a first-order filter."（有「元件变化→性能」的敏感性分析意识，但只是改一个增益系数重算传函的数值演示——A1 增加 10% 后重得 F(s)=1.001s³+2.998s²+…（p.5、p.7），非差分失配→CM 误差解析。）
4. **综合对象限定低通**（p.1）：> "The synthesis of low-pass filters only is considered since it has been shown that the other filter networks may be derived from these."

## 关键数值（原文）
- 三阶二项式（binomial）低通例：RC 元件值 R1=6 Ω, C1=5 F, R2=4 Ω, C2=3 F, R3=2 Ω, C3=1 F（p.2）。
- 合成增益解（p.4）：A1 = 0.908, A2 = 0.993, A3 = 0.9986（OCR：> "X 1 = - ( - 4 - 5 4 ) / 5 = 0-908" 等，首个表达式数字有 OCR 噪声）。
- 增益 +10% 扰动实验（p.5）：> "To illustrate this procedure, the gain of amplifier At is increased by 10%." → 新传函首行系数 1.001, 2.998, …（p.7）：> "F(s) = 1-001S 3 +2-998S 2"（OCR 截断，后项未引全）。
- Algol 60 程序清单：RECCON / CONREC / CONMAT / RECMAT / CIRCUIT（p.7）。

## 对 P1/P2/P3 的对照
- **P1（无源差分网络失配→CM 误差解析条件）**：无。全篇为单端有源 RC 梯形网络综合，无差分结构、无共模、无失配→CM 误差解析式；其「元件变化→传函重算」是数值敏感性演示，与 P1 的解析消去条件（G_DC=H_N−H_P≡0 元件条件）不构成任何竞争。
- **P2（Kelvin 结构地板）**：无。
- **P3（平坦度约束衰减上界）**：无（二项式低通是最大平坦响应的选取，未讨论平坦度与阻带衰减上界的定量约束）。
- **方法学（D1–D10）**：无。其计算机辅助综合/分析流程（1960s Algol 程序）与门槛化方法学无对应。
- **killRisk 判断**：无威胁。归入 H2 轴大概率因「梯形 RC 低通」关键词，实际与差分滤波/CMRR 无内容交集；P1 论文中不必引用。
- 谱系定位：四层谱系之外（经典网络综合线，Holbrook 1969 的续篇）。

## 没读到的
- 矩阵元素数字受扫描/OCR 噪声影响较大（连续页大量行列式数值不可靠），仅正文文字与结论性数值可信；Fig.1/Fig.2 电路拓扑细节未逐元件核对。
