# 精读笔记 · Chung 1998《Self-monitoring structural materials》（Materials Science and Engineering: R 22:57–78）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。

## 出处
- Chung, D.D.L., "Self-monitoring structural materials," *Materials Science and Engineering: R: Reports*, vol. 22, pp. 57–78, 1998. DOI: 10.1016/S0927-796X(97)00021-1。
- PDF：`fulltext/H2-差分CMRR/chung1998selfmon.pdf`（22 页，Elsevier 扫描版带 OCR 文本层；OCR 噪声多，引用以能辨认的原文为准）。bibkey：`chung1998selfmon`。
- 主题：**自监测结构材料综述**（短切碳纤维水泥基 / 连续碳纤维聚合物基 / 碳-碳复合材料），电阻随应变（可逆）与损伤（不可逆）变化。**注意：全文无 CMRR、无差分滤波器内容**——放在 H2 文件夹属背景文献（P1 论文应用侧：电阻法损伤监测的测量对象），非 H2 轴正文。

## 核心命题（原文）
1. **自监测的物理量是电阻，应变→可逆变化、损伤→不可逆变化**（p.57, Abstract）：
   > "Each material is capable of tnonitoring its own reversible strain and damage through the effects of these on the electrical resistance of the material."
   （P1 论文应用背景的标准表述：损伤分级监测 = 电阻变化监测。）
2. **测量一律用四探针（Kelvin）法，接触用银浆**（p.64）：
   > "The resistance was measured by using the four-probe method, with silver paint for the electrical contacts."
   （连续碳纤维聚合物基复合材料的电阻测量即 Kelvin 四线——把接触/引线电阻从被测电阻中剔除；**只作为既定方法使用，未分析四线结构自身的共模地板**。）
3. **可逆/不可逆分解 + 方向选择（纤维向测纤维断裂、厚度向测分层）**（p.70）：
   > "the sensing of damage in the form of fiber damage should be performed by measuring the resistance in the fiber (stress) direction and the sensing of damage in the form of delamination should be performed by measuring the resistance in the through-thickness direction."
   （损伤机理与测量方向配对——增量归因方法学的"分桶"思想在材料侧的对应。）
4. **疲劳损伤可实时渐进监测（峰值 R 跟踪 + 断纤分数定量）**（p.66, 67）：
   > "Thus, by following the increase in the peak R, the degree of damage can be monitored progressively in real time. Moreover, progressive warning of the impending fatigue failure is provided in real time, so disasters due to fatigue failure can be avoided."（p.66）
   > "fraction of fibers broken = Q/(1+Q')  (1)  where Q = ( (R-R,' ) / ( Ro') ) - 4.0 X lo-'"（p.67，OCR 残损，式意：由不可逆 ΔR/R₀ 反推断纤分数，扣除单丝损伤贡献 4.0×10⁻³）
5. **AC 与 DC 的取舍：AC 无额外信息、设备更贵，推荐 DC**（p.63）：
   > "Similar results were obtained under AC condition [ 91. The fractional increase in reactance can be larger than the fractional increase in resistance under the same load. However, the difference is not very large and AC measurement requires more expensive equipment than DC measurement. Therefore, DC operation is recommended, unless data acquisition using wireless methods is desired."
   （对 DE-DRMS 式恒流直流电阻测量路线的材料侧背书。）
6. **多探针可扩展为电阻率层析**（p.63）：
   > "the placement of more than two voltage probes allows measurement of the resistivity distribution. Resistivity tomography may be used to obtain a two-dimensional resistivity distribution."

## 关键数值（原文）
- 应变灵敏度（gage factor）：水泥基最高 **700**（拉），压 560；未臭氧处理纤维 625（拉）/500（压）（pp.61–62）；聚合物基纤维向最高约 **38**（量级），厚度向最高 **49**；碳-碳 **1.2–2.4**（pp.69, 76, Table 1 p.76）。常规电阻应变片 ≈2（p.59）。
- 疲劳寿命可感知区间（Table 1, p.76）：水泥基 0–10%；聚合物基 50–100%；碳基 0–100%。
- 碳纤维掺量低至 0.24–0.5 vol%（低于渗流阈值）即有效（pp.59, 61–62）；裂纹高度由 ~100 µm 压到 <1 µm（p.59）。
- 聚合物基疲劳细节：>218,277 循环（55% 寿命）出现峰值 R 阶跃式上升；>353,200 循环（89%）转为逐周上升；396,854 循环断裂；18% 纤维断裂时灾难性失效；最小阶跃 0.006 ≈ 1020 根纤维（束 6000 根）（pp.65–67）。
- 单丝在 83% 断裂应力下：可逆 ΔR/R₀=18.4×10⁻³（尺寸效应），不可逆 4.0×10⁻³（损伤）（p.66）。
- 分层：33% 寿命起始，62% 时达 4.3% 截面积（p.68）。
- 体内方向性：[0] 复拉时纤维向电阻可逆**下降**（对齐度↑+预应力释放各贡献约 10% 纤维电阻变化），厚度向可逆**上升**（p.64–65, 68）。

## 对 P1/P2/P3 的对照
- **P1（消去条件）**：相关度 **无**。全文无共模/差模、无滤波器、无传递函数匹配的任何内容。
- **P2（Kelvin 结构地板）**：相关度 **低-中**。四探针法作为既定测量手段出现（p.64），证明 Kelvin 结构在电阻法损伤监测中是**标准前提**（支撑 P2 的"结构前提普遍成立"），但**完全不讨论四线结构自身的共模抑制地板或残余误差**——不构成对 P2 主张（地板存在性与数值）的威胁或支撑细节。
- **P3（平坦度约束下衰减可达上界）**：相关度 **无**。无滤波器综合内容。
- **方法学（增量四 D1–D10）**：相关度 **低**。其"可逆/不可逆分解""损伤分桶归因（纤维断裂 vs 分层 vs 基体开裂）"与增量归因思想同构，但无仪器增量实验设计。
- **killRisk 判断**：**无威胁**。材料综述，与 H2 轴（差分滤波器与 CMRR）零交集；建议在谱系表中改挂应用背景轴（H6 侧）或标注"应用对象侧背景"。

## 没读到的
- 无任何仪表/电路层内容（激励源、前端放大、CMRR、滤波器一概未提）——四探针的**电气实现细节**（电流注入与电压检测如何隔离、共模如何处理）完全缺失。
- 未讨论四线法的误差地板（引线感抗、共模转换、开关泄漏等）。
- 碳纳米管（CNT）网络不在本综述范围（只覆盖碳纤维水泥/聚合物/碳-碳三类）——MWCNT 传感层需另找文献。
- OCR 质量差，式(1)与部分数字（如 "lo-'"）残损，精确数值若要引用须核对原刊 PDF。
