# 精读笔记 · Nauman 2021《Piezoresistive Sensing Approaches for Structural Health Monitoring of Polymer Composites—A Review》（Eng）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> 本篇为 H6 应用域（C 级）证据：按主代理要求重点查「测量环节用什么硬件、是否讨论前端误差/校准、四线/两线制」，其余快读。

## 出处
- Nauman, S.（Institute of Space Technology, Islamabad），"Piezoresistive Sensing Approaches for Structural Health Monitoring of Polymer Composites—A Review", *Eng* 2021, 2, 197–226（MDPI，DOI 10.3390/eng2020013）；30 页，PDF 物理页 1–30 = journal pp. 197–226。
- 文件：`/home/anning/Documents/Obsidian Vault/20-硬件工程/10-项目设计/p1-文献谱系/fulltext/H6-CNT-SHM/nauman2021.pdf`

## 测量环节现状证据（本篇核心，H6 专查项）
- **全文 30 页对"电阻/阻抗怎么测"零硬件描述**。用 `multimeter / Keithley / Agilent / electrometer / ohmmeter / impedance analyzer / data acquisition / LabVIEW / two-probe / four-probe` 等关键词 grep 全文抽取文本，**全部零命中**。测量被当作黑盒处理。
- 测量模态仅到"AC 还是 DC"的层面（哪类损伤由哪类测量检出），不再往下到仪器/前端：
  > "It has been concluded by the authors that DC electrical measurements can be used to detect fiber-dominated failure modes whereas AC measurements are more suitable for monitoring matrix-dominated failure modes such as delamination, interfacial debonding and transverse cracks."（p.205，评 Abry et al. 的 CFRP 自感知。）
- 电极仅一句定性提及，无接线制式（两线/四线）、无接触电阻/引线电阻处理：
  > "Moreover, a network of electrodes is also needed so that the area of interest may be monitored through them."（p.207）
- **前端误差/校准零讨论**：全篇无 lead resistance、接触噪声、激励方式（恒流/恒压）、采样/滤波的论述。

## 核心命题（原文）
1. **压阻是可实时检测的属性（测量黑盒化的总纲）**（p.197，摘要）：> "Among other properties, piezoresistance is the one that can be detected in composites in real-time as a function of strain."（"can be detected"一笔带过——测什么有了，怎么测不在综述范围。）
2. **自感知的电学读出定义**（p.205）：> "These changes in electrical properties can be measured as resistance or impedance change and serve as a non-invasive way of monitoring the state of health or integrity of the composite system."（"measured as resistance or impedance change" 是全文对"测量环节"最深的一句。）
3. **全局 R/C 测量的局限（唯一与测量能力沾边的批判）**（p.207）：> "Even then this global approach of resistance or capacitance measurement may not be able to fully capture all the microscale damage mechanisms and identify the source of failure."（局限归于"空间分辨/机理解读"，仍不触及测量链误差。）
4. **选型准则只看敏感度/工艺/检测能力**（p.1197 行起，p.221–222）：> "It is reported that these techniques have their own merits and demerits and can be compared on the basis of sensitivity, manufacturing methodology and detection capability."（结论章的三维比较框架里没有测量硬件维度。）

## 关键数值（原文）
- C/C 复材面内电阻率：> "The in-plane electrical resistivity at room temperature was 2.4 × 10−5 Ωm."（p.206，Xi et al. 工作。）
- C/C 复材压阻 Gauge factor：> "The in-plane gauge factor owing to piezoresistivity was reported to be negative (−7804 ± 429)"；碳纤维参照 "gauge factor: −1830 ± 47"（p.206–207）。
- 某填充体系的敏感度：> "parameters such as sensitivity and gauge factor were also reasonable (0.0086 Ω/ppm and ..."（p.204，句被抽文本截断——待核）。
- （其余数值均为材料/力学性能：拉伸强度 +70%、弯曲 +18.7% 等，与测量环节无关，略。）

## 对 P1/P2/P3 的对照
- **P1**：C 级空白侧证——材料界综述把"电阻测量"视为免费能力（商品化仪器理所当然），全文无一字涉及前端理论（激励、引线、kickback、校准）。P1 的空白侧（应用文献不关心前端理论）在本篇成立。
- **P2**：无关。
- **P3**：无关。
- **方法学**：其"选型准则三维框架"（灵敏度/工艺/检测能力）是应用域框架，与 P1 的门槛化方法学（建立/回稳/峰值门槛）无重叠。
- **killRisk：无威胁**。理由：领域（材料与集成策略）与 P1（测量前端电路理论）零交集；其测量环节沉默恰恰是 P1 立题的侧证。

## 没读到的
- p.204 "0.0086 Ω/ppm" 所在句在文本抽取中被截断，对应文献编号与完整表述——待核。
- Figure 1/2 及各图表内容未逐幅核（综述图表均为材料组织与 GF 曲线，与测量硬件无关，按 H6 快读原则略过）。
