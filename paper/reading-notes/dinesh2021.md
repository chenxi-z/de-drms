# 精读笔记 · Dinesh 2021《Self-sensing cement-based sensor with carbon nanotube: Fabrication and properties – A review》（Materials Today: Proceedings）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。

## 出处
- A. Dinesh, S.T. Sudharsan, S. Haribala, "Self-sensing cement-based sensor with carbon nanotube: Fabrication and properties – A review," *Materials Today: Proceedings*, 2021. DOI: 10.1016/j.matpr.2021.02.722. Sri Ramakrishna Engineering College, Coimbatore。
- PDF 7 页 = 预印版页 1–7（Elsevier 排版，文字层完整；**「≤」「Ω」等符号多处被排版丢弃**，涉处已标待核）。
- 定位：**H6 应用域（CNT-水泥基自传感）综述**——材料/工艺为主，测量链只有一段方法论综述（两线或四线 + AC 电源 + 万用表）。对本轴价值：①"极化→改用 AC"是域内标准对策的综述级表述；②测量仪器口径为"power supply + digital multimeter"级商品化通名。

## 核心命题（原文）
1. **总命题：CNT 掺入使水泥复合材料成为压阻自传感器，综述材料-工艺-性能链（p.1, Abstract）**：
   > "Cement composite is converted to a cement-based sensor due to its piezoresistive property. Thus, the paper examines the use of carbon nanotubes (CNT) in the development of cement-based sensors. … This review gives a detailed insight into the material properties, sensor fabrication, mechanical, conductive and piezoresistive properties of the developed cement-based sensor."
2. **★测量方法综述：两线或四线 + AC 电源 + 数字万用表（p.2, Methods）**：
   > "To test the current and voltage of the composite, two or four-probe techniques are used. A power supply unit is used to supply the composite with AC. To measure the voltage simultaneously, a digital multimeter is used."
   （全领域方法论被压缩成一句"两探针或四探针 + 交流电源 + 万用表"——**H6"测量环节商品化/方法学匿名化"的典型文本**：无型号、无误差预算、无四线两线的适用性辨析。）
3. **★★直流极化是域内公认障碍，标准对策 = 改 AC 或烘干试样（p.4, §5.2）**：
   > "When current is supplied to the cement composite to measure its conductivity, polarization occurs, affecting composite conductivity. To eliminate the effect of polarization, either AC is applied [15,25], or the specimen was oven-dried before testing for three days [11,14]."
   （**对 P1 语境最直接的一条**：水泥基 CNT 传感的直流电测受极化干扰是域内共识，通行出路是换成 AC 激励——即应用域从材料侧"逃离直流"，与 P1 讨论直流通道消去条件形成对照背景。）
4. **压阻三阶段 + 失效突变：损伤分级物理（p.4, §5.3.1）**：
   > "Stage 1 – Resistivity decrease – due to matrix compaction / Stage 2 – Resistivity balance – due to crack generation / Stage 3 – Resistivity Increase – due to crack propagation"
   > "When the compressive load exceeds the capacity of the cement composite, the composite fails. This results in a sudden increase in resistance of the composite. Thus, CNT embedded cement composite can alert the users regarding the failure of the structure under compression."
   （三段式电阻率响应 + 失效突增——**结构损伤分级监测的应用域叙事模板**。）
5. **渗流三区：绝缘/渗流/导电（p.4, §5.2）**：
   > "[the paste] shows the insulation phase if CNT is < 1.3 vol%. The cement paste was in the percolation zone when CNT is > 1.3 vol% and < 1.7 vol %. When CNT is > 1.7 vol%, the cement paste was in the conductive phase."
6. **灵敏度来源：接触导电 + 隧穿导电（p.1, Abstract）**：
   > "The cement-based conductive properties increase with an increase in CNT content due to contact conduction and tunnelling conduction."

## 关键数值（原文）
- 应变计系数：**"The CNT embedded cement-based sensor shows the gauge factor (sensitivity) up to 200 [4]."（p.1）**；NiNF/CNT 复合 **"good repeatability (11.61%) and sensitivity (1500)"（p.5, 引 [30]）**。
- FCR：**"The maximum value of FCR was 19.31% under a compressive stress of 10 MPa when CNT alone is added. But FCR is increased to 24.24% when both NiNF and CNT is added"（p.5）**。
- 工艺增益：**"The fabrication procedure can increase the conductivity from 10⁻⁶ S/m to 1 S/m [20]."（p.2，指数为原文 10-6 记法）**；处理后 CNT 电阻率 **149 Ωcm** vs 未处理 **130 Ωcm**（p.4，"Xcm"系 Ωcm 丢字[待核]）。
- 掺量最优：**约 66.6% 既往研究 CNT 剂量 ≤0.4%**[符号疑丢，原文应含 ≤，待核]，力学电学性能优于更高掺量（p.2）；抗折强度增益 73%/87%/52%/46% @ 0.08/0.1/0.3/0.5 wt%（p.2, 引 [14]）。
- 极化对策时长：**烘干 3 天**（p.4）。
- **无任何测量仪器型号、CMRR、精度、噪声指标。**

## 对 P1/P2/P3 的对照
- **P1（消去条件）**：**中**。综述级证据：直流电测的极化障碍 + 域内以 AC 激励回避（p.4）——即**应用域从未在直流域内解决测量纯度问题，而是换激励制式**；这为 P1 的"直流通道若要成立必须满足消去条件"提供应用域背景（域内用 AC 绕开而非电路消去）。
- **P2（Kelvin 结构地板）**：**低**。仅"two or four-probe techniques"一笔带过（p.2），无四线结构误差、无共模、无地板概念——四线在域内是"知道但匿名"的选项。
- **P3（衰减可达上界）**：**无**。
- **方法学（门槛化）**：**低**。三阶段电阻率响应（p.4）是定性分级叙事（压密/裂纹萌生/裂纹扩展），无阈值判据、无统计。
- **killRisk 判断：无**。综述文，零电路分析；对 P1 是背景支持（极化→AC 是域内现状），对 P2 仅取证"四线匿名化"，对 P3 无接触。

## 没读到的
- Figures 1–8 曲线本体（图不进 OCR）。
- 综述所引关键原始文未读：[15] Azhari & Banthia 2012、[25]、[11] Dalla 2016、[14] Danoglidis 2016（极化对策 AC/烘干的原始出处）；[30] Yin 2020（sensitivity 1500 出处）；[4] Hierold 2006（GF 200 出处）。
- "两线 vs 四线"的选用判据与引线电阻量级讨论——本综述未给。
