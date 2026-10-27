# 精读笔记 · Lee 2012《Stochastic Model and Drift Dependence of Long Term Stability of Type N Precision Coaxial Terminations》（80th ARFTG, pp.1–5）

> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> 读法：pdftotext -layout 全文逐节；会议论文无连续刊印页码，页码 = PDF 页（p.1–p.5，p.4–5 为图版）。公式为嵌入图形，符号在文本层缺失处以 [符号缺失] 标注。

## 出处

- Yeou Song (Brian) Lee，Anritsu Company（Morgan Hill, CA），80th ARFTG Microwave Measurement Conference，2012，pp. 1–5，DOI 10.1109/arftg.2012.6422436（IEEE 目录页码 1–5，与 PDF 页一致）。
- bib key：`lee2012stochas`（H2 轴尾——精密电阻性元件（50 Ω 精密同轴负载）长期漂移的随机模型与校准间隔判据）。

## 核心命题（原文）

1. **精密端接（本质是精密电阻负载）的漂移用线性二阶随机过程经验拟合，用于确定校准间隔**（p.1 摘要）：
   > "This paper discusses a stochastic model fitting process for the determining the calibration interval of precision Type N coaxial terminations. The measurements were taken weekly and over a six month period. … The observed drift rate is computed using linear regression. A second-order drift was observed."
   （匹配/标准元件的值不是常数而是随机过程——校准间隔本身成为被设计量。）

2. **对象定位：长稳性是其作为标准的资格**（p.1）：
   > "A precision termination is a 50 [Ω] fixed load. Because of its long-term stability, it is often used as a calibration standard for the vector network analyzers and to help measure various microwave quantities such as noise floor. Therefore, it is important to evaluate the performance of the precision termination over its calibration interval in the sense of drift over time."

3. **十只样品、二阶导数法提取漂移率**（p.1、p.3）：
   > "This study took a group of ten precision terminations and routinely measured their performance over time. Their behavior fits empirically a linear second-order stochastic process."（p.1）
   > "Figure 3 shows the second derivatives of two precision terminations. The two graphs have shown a similar matching pattern in frequency response. This support the suggested approach of taking the second derivative of measured reflection coefficient will give rise to a constant drift rate."（p.3）

4. **温控与温度系数实测：排除温度作为漂移主因**（p.2）：
   > "During the measurement of ten precision terminations, the temperature of the room was kept within ± 1°C. The temperature gradient of reflection coefficient magnitude of the Anritsu precision termination 28N50-2 is empirically determined at 0.0001/°C. Therefore, the impact on all ten units in a measurement cycle is negligible since the total calibration/measurement time lasts less than 10 minutes."

5. **漂移呈随机性、且频域上有四个特征区（指向制造工艺）**（p.3）：
   > "Figure 4 … It clearly indicates that a possible stochastic process does exist for precision termination. It also shows four distinguished zones in the frequency responses, which may be related to the making of precision termination."

6. **结论：漂移可带置信度预测**（p.3）：
   > "In this paper, a stochastic equation for the drift-over-time of precision terminations, 28N50-2, is derived. Subsequently, the empirical data suggest that a stochastic behavior exists among the ten precision terminations based on the derived equation. Thus, the drift of precision termination over its calibration interval can be determined with good confidence."

## 关键数值（原文）

- 样本与周期：10 只 28N50-2 精密端接；每周测一次、共 6 个月（178 天，Fig.1 标题 "Raw data of measured VSWR of one precision termination over 178 days"，p.4）。
- 温度：室温 ±1 ℃；反射系数幅度温度梯度 0.0001/℃（28N50-2 实测，p.2）；单轮校准/测量 <10 min。
- VNA：Anritsu Lightning 37347C（或 Vector Star 等效）；滑动负载单端口校准（OSL 类），"A sliding termination can emulate the performance of a high quality matched load…"（p.2）。
- 数学框架：SDE（"A stochastic differential equation (SDE) is a differential equation in which one or more of the terms are a stochastic process…"，p.1）；误差模型 ED/ERT/ES 单端口 12 项中的三项（Eq.1–2，p.2）；假设实际反射系数变化率为常数，二阶导数为常数（Eq.3–5，p.2）。
- 频域四个特征区（Fig.4 标题 "…with four distinguished zones"，p.5）。

## 对 P1/P2/P3 的对照

- **P1（消去条件 G_DC(s)=H_N−H_P≡0）**：中相关（时间维证据）。精密电阻元件的漂移是**随机过程**（非确定性、逐只不同），意味着任何在 t₀ 时刻建立的匹配/消去条件会随时间统计性退化，消去残余无解析上界、只能给置信区间——支持 P1"精确消去只在标称点成立"的时间维推论。但注意：本文测的是单只元件 vs 自身历史，**不是差分对两元件间的相对漂移**；把"个体随机漂移"直接当"配对失配漂移"引用需外推（待核：无配对样本数据）。
- **P2（Kelvin 结构地板 ≈56 dB）**：低。无 CMRR/结构地板内容；唯一弱关联是"作为校准标准的精密负载自身要定期校"——Kelvin 结构中参考/采样元件同理需再校，但本文未讨论。
- **P3（平坦度约束衰减上界）**：无。无滤波/衰减内容。
- **方法学（D1–D10 / 门槛化）**：中高。①"随机模型 + 置信度 → 校准间隔"是把误差预算门槛化的标准范式（D 系直接可引的方法学先例）；②二阶导数法把缓变趋势与随机涨落分离的信号处理手法可借鉴到 G_DC(s) 残余的漂移监测；③"先控温排除温度、再归因工艺"的排除法设计与 D 系逐门验证同构。
- **killRisk 判断**：无风险。与 killRisk 条目（ti_threeguidelines2015 出处勘误）无交集；本文不含失配-CMRR 公式，不构成任何误引源头。

## 没读到的

- Eq.(1)–(5) 的符号与系数（嵌入图形，文本层缺失）；Fig.1–4 的纵轴刻度与四个特征区的具体频点（仅图注文字可引）。
- 原始数据表（178 天×10 只×扫频）与随机模型参数（漂移率常数、方差）——正文未给出数值，只有定性结论"good confidence"。
- 28N50-2 与 Anritsu 校准件手册（外部资料，不入库）。
