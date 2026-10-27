# 精读笔记 · Sánchez-Romate 2021《Structural health monitoring of a CFRP structural bonded repair by using a carbon nanotube modified adhesive film》（Composite Structures 270:114091）

> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。

## 出处

- 一作：Xoan F. Sánchez-Romate（Universidad Rey Juan Carlos, Madrid；合作者含 Airbus Operations S.L.）。
- 期刊：Composite Structures, Vol. 270 (2021), 文章号 114091，DOI 10.1016/j.compstruct.2021.114091。开放获取（CC BY-NC-ND）。
- PDF：`H6-CNT-SHM/sanchezromate2021cfrp.pdf`，10 页，pdftotext 全文清晰（少数连字 ﬁ/ﬂ 为排版连字，非 OCR 损）。
- 主题：CNT 掺杂胶膜（FM300 k 环氧胶膜喷洒 MWCNT）用于 CFRP 胶接修理（scarf patch repair）的结构健康监测（SHM）：标准件（SLS 单搭接 / Mode-I I 型断裂）→ 400×400 mm² 修理板剪切试验，电阻监测 vs 应变片 vs 声级计 vs 超声 C 扫四路对照。
- 与本库关系：本文引用 Augustin 等 2018 两篇（[13] 印刷电路 + CNT 胶膜冲击检测、[21] scarfed CFRP 接头疲劳电阻监测）——即本库已有 Augustin 2018 博士论文的 TUHH 同主题期刊工作；本文是 URJC 组的平行/后续工作（并宣称自己的新颖点是共固化 autoclave 工艺 + 整体修理板验证）。

## 核心命题（原文）

1. **两端电极电阻测量即 SHM 的基本手段**（p.1）：
   > "the SHM techniques with carbon nanoparticles are based in the measurement of the electrical conductivity between two electrodes. In fact, the presence of a damage promotes the breakage of electrical pathways, which is reﬂected in a sudden increase of the electrical resistivity of the material [11–13]."
   （CNT/纳米粒子 SHM 的统一原理：两电极间测导电网络电阻，损伤断路 → 电阻突增。这与 DE-DRMS 的两端 MWCNT 传感层场景同构。）
2. **测量硬件：台式 6½ 位 DMM + 铜线银墨电极，未声明 2 线/4 线**（p.2）：
   > "Simultaneously, the electrical resistance was measured by using an Agilent 34,410 A module. The electrodes were placed on the outer skin of the CFRP substrates, made of copper wire and attached with silver ink to ensure a proper electrical contact."
   （"34,410 A" 为 pdftotext 对 34410A 的分词产物。全文仅此一句测量硬件描述；接触处理=银墨，无任何接触电阻量化、无温补、无四线制讨论。）
3. **电阻增大的双机理：隧穿距离（可逆形变）+ 通路断裂（不可逆损伤）**（p.5）：
   > "Therefore, and based on the tunnelling transport mechanisms, the electrical resistance due to tunnelling effect, which is the dominating mechanism, increases in a linear‐exponential way with the increasing applied displacement, according to G. Simmons formula [32]."
   （机理依据 Simmons 1963 隧穿公式；对 DE-DRMS 的 R–应变/损伤单调性假设是同一理论根基。）
4. **Mode-I 试件的 stick–slip 电阻台阶特征**（p.6）：
   > "this increase of the electrical resistance is characterized by the alternation of sharp increases followed by arrest phases. The sharp increases are correlated to rapid crack propagation, which promotes a sudden breakage of the electrical pathways [25]."
   （电阻阶梯状上升对应裂纹失稳扩展/止裂交替——分级监测中"突变事件"特征的原文出处级描述。）
5. **载荷门槛的定义方式 = 电阻变化检测阈值**（p.7）：
   > "Here, the load threshold is deﬁned as the minimum value of the load at which a change in the electrical resistance is detected by the electric sensors."
   （门槛=「检测到电阻变化」的最小载荷——典型的"变化检测"式定义，不涉及电阻绝对精度。）
6. **电阻先于声发射发现裂纹萌生（灵敏度优势主张）**（p.9）：
   > "Furthermore, the electrical resistance increase measured before the initial sound level peak in both E1 and E3 sensors between 200 and 282 kN can be explained by the crack nucleation taking place before the initial debonding."

## 关键数值（原文）

- 电阻测量仪表：Agilent 34410A（p.2，仅此一件；未给采样率/量程/接线制式）。
- 电极：铜线 + 银墨（silver ink）；修理板试验为 5 电极网络 E1–E5，"Electrical measurements were done through the thickness of the panel"（p.3）——贯穿厚度方向测量。
- 应变片：LY41-6-350，标称 350 Ω，8 片（p.2）。
- 胶膜：FM300 k（Cytec），标称厚 0.2 mm；MWCNT NC7000（Nanocyl），平均直径 9.5 nm，长至 1.5 μm；分散液 0.1 wt% CNT + 0.25 wt% SDS，超声 20 min，1 bar 喷涂（p.2）。
- 固化：180 ℃、8 h、0.9 MPa autoclave 共固化（p.2）。
- 力学：SLS 0.5 mm/min、Mode-I 10 mm/min，Zwick 10 kN 力传感器；修理板 500 kN 力传感器、0.5 mm/min（p.2–3）。
- 力学性能不劣化（Table 1, p.4）：LSS 新鲜胶 39.7±1.1 MPa vs CNT 胶 39.9±0.7 MPa；G_IC 768.0±106.7 vs 775.8±41.3 J/m²。
- 声级计 PCE-353：30–120 dB，分辨率 0.1 dB；超声 TRITON 8000 TT 5 MHz（p.3）。
- 通道载荷门槛：E1/E3 ≈200 kN、E4 250 kN、E5 ≈300 kN（p.7）。
- 声发射基线 70 dB → 282 kN 时 79 dB → 297 kN 时 80 dB → 332/337/334 kN 时 83/90/110 dB；E1 电阻峰在 282、337、344 kN，E3 在 282、344 kN（p.8）。
- 超声复检缺陷：上角 10 mm 边等边三角形脱粘 + 下角 61×10 mm 脱粘（p.7）。

## 对 P1/P2/P3 的对照

- **P1（消去条件 G_DC=H_N−H_P≡0）**：无交集。本文无差分采样网络、无开关电容 ΣΔ、无任何 AAF 结构。killRisk：**无威胁**。
- **P2（Kelvin 结构地板 ≈56dB）**：无交集（本文无 Kelvin/四线结构、无地板/噪声底量化）。但作为「我们 P2 双电极电阻仪」的**领域背景最可类比文献**：①最可类比——同为两端电极贯穿 CNT 导电网络测电阻、以 ΔR 及突变为损伤指标、银墨/铜线电极工艺、准静态加载下"变化检测"即可定级；②最不可类比——其仪表为台式 6½ 位 DMM、无需电池功耗约束、无需 1% 绝对精度与温度补偿（材料 TC、接触电阻均未处理、环境为室温实验室）、数据率近乎静态；即"实验室 SHM 可用两线 + 相对变化检测"这一事实**不削弱反而衬托**双电极仪器在嵌入式/绝对精度/温度维度的增量空间。killRisk：**无威胁（领域支撑）**。
- **P3（平坦度约束衰减上界）**：无交集，无滤波器/衰减论述。killRisk：无威胁。
- **方法学（D1–D10 门槛化）**：仅弱类比——其"load threshold = 电阻变化被检测到的最小载荷"（p.7）与门槛化思想同形，但对象是力学载荷而非仪器指标，不构成方法学重叠。killRisk：无威胁。

## 没读到的

- **接线制式未声明**：2 线还是 4 线（34410A 两者皆可），5 电极网络 E1–E5 的激励/检测对拓扑（对测谁、是否共回线）全文未给，仅 Fig. 3(b) 示意——无法确认其电阻值是否含引线/接触电阻贡献。
- 电阻绝对量程与初始阻值：全文只给 ΔR 趋势曲线（Fig. 5/6/8），未给出各通道初始电阻数值与总变化倍数（Fig. 6/8 为图，pdftotext 无数值）。
- 采样率、激励方式（DMM 欧姆档电流大小）、是否温度记录/补偿：均未提及（仅"at room temperature"，p.2）。
- 引用文献 [25][26][27][28]（同组前作：准静态、疲劳、skin-stringer）全文未读，其测量链细节可能更全（尤其 [26] 疲劳动态测量）。
