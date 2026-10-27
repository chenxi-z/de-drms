# 精读笔记 · Qhobosheane 2022《Smart Self-Sensing Piezoresistive Composite Materials for Structural Health Monitoring》（Ceramics）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> 本篇为 H6 应用域（C 级）证据：重点查「测量硬件、前端误差/校准、四线/两线制」。**本篇是 H6 抽样里唯一带自制前端细节的**。

## 出处
- Qhobosheane, R.G.; Rabby, M.M.; Vadlamudi, V.; Reifsnider, K.; Raihan, R.（UT Arlington），"Smart Self-Sensing Piezoresistive Composite Materials for Structural Health Monitoring", *Ceramics* 2022, 5, 253–268（MDPI，DOI 10.3390/ceramics5030020）；16 页，PDF 物理页 1–16 = journal pp. 253–268。
- 文件：`/home/anning/Documents/Obsidian Vault/20-硬件工程/10-项目设计/p1-文献谱系/fulltext/H6-CNT-SHM/qhobosheane2022.pdf`（**该 PDF 为带 "FOR PEER REVIEW" 水印的审稿版，双文字层重影，部分段落被重复抽取**）。

## 测量环节现状证据（本篇核心，H6 专查项）
- **电阻测量 = 商用阻抗分析仪 + 两电极法**（journal p.257）：> "The sample was sandwiched between the two electrodes, which were wired into an alpha analyzer (broadband dielectric spectroscopy) that measured the sample's resistivity. The impedance of the sample was measured after it was subjected to an AC electric field. The resistance component R of the impedance Z* = R + iX, where X = reactance, was then isolated and plotted against the crack opening length."（核心测量全部交给商品化 alpha analyzer。）
- **两电极制式明示，无四线、无引线/接触电阻处理**（journal pp.258–259）：> "the electrical resistance R was measured using the two-electrode method at the 100 Hz frequencies."（归一化定义 ∆R/R₀ = (R − R₀)/R₀，式(1)。）
- **自制前端只出现在 EM 检测通道，且为应用级粗设计**（journal p.257）：> "To amplify the signal, JFET amplifier was connected to this system. A common source amplifier was designed with a self-biasing scheme that could pick up a signal with a target voltage gain of 6 amplifying signal."（器件参数靠扫描定 Q 点，无噪声/误差预算：> "a voltage gate to source was swept in 50 mV steps to determine the drain current at each step. This therefore led to the trans conductance (𝑞𝑚) plot where the q point was set from mid low to high current and both 𝑞𝑚 and source resistance Rs were calculated from the slopes"，原文把 gm 排成 "𝑞𝑚"。）
- **校准：grep `calibrat` 全文零命中**；无前置误差讨论、无引线补偿。基线即"加载前初值 R₀"，属应用级归一而非仪器校准。

## 核心命题（原文）
1. **电极选材逻辑=应用需求（柔性+高导电）**（journal p.257）：> "The design and selection of the electrode material used to measure the electrical property [26] was based on the application requirements. The electrode was required to be flexible and possess high electrical conductivity. Copper (Cu) was selected for the electrode because of its excellent properties, which include direct current electrical conductivity of 5.96 × 107 Sm−1 [27]."
2. **贯穿厚度测量的几何理由**（journal pp.258–259）：> "it should also be noted that the measurement is through-thickness, which means that the setup is similar to a parallel plate capacitor ... This setup was used because we are attempting to measure change in resistivity with propagation of an interlaminar crack, which is a through thickness effect that is more sensitive to changes than in-plane measurements."（I 型层间裂纹 DCB 试验 + 平行板式两电极。）
3. **结论主张：R 变化 + EM 电荷双通道检测裂纹扩展**（journal p.267）：> "The relation between electrical resistance and separation during mode I tests identified together with the detection of electromagnetic charge emitted from the composite specimens as crack propagates. It was observed that specimens without nanotubes embedded have less resistivity change and emitted less charge during the damage development and morphological change."

## 关键数值（原文）
- 铜电极电导率：> "5.96 × 107 Sm−1"（journal p.257）。
- 测量频率：> "at the 100 Hz frequencies"（journal pp.258–259）。
- JFET 放大器目标增益：> "a target voltage gain of 6"（journal p.257）；Vgs 扫描步长 "50 mV steps"。
- CNT 掺量参照（引言引他文）：> "the addition of CNT (in the range of 0.1–0.3% wt.) to the resin system increases the electrical conductivity"（journal p.256）；> "0.1% wt. of MWCNTs ... a 32.8% increase of the maximum flexural strength"（journal p.256）。

## 对 P1/P2/P3 的对照
- **P1**：C 级侧证（含一个反例样本）——应用文献的核心电阻测量依赖商品化 alpha analyzer，两电极直测无前端理论；自制前端（JFET×6 增益）只服务 EM 通道且无误差预算。说明该领域前端"够用即可"，精度链论证缺席，支撑 P1 的空白判断。
- **P2**：无关（Kelvin/地板无涉；两电极与四线制的差别恰是应用域不讨论的话题）。
- **P3**：无关。
- **方法学**：其"扫 Vgs 定 Q 点"属器件偏置流程，非门槛化方法学。
- **killRisk：无威胁**。理由：材料/SHM 应用论文，测量链为商品仪器 + 粗前端，与 P1 的电路理论主张零交集。

## 没读到的
- Figure 2（JFET 电路图）元件值未逐字核（图内文字在双水印层下难辨；若需引用电路细节需看原图——待核）。
- "alpha analyzer" 具体型号/厂商未写明（原文只给通用名）。
- 页码归属因双水印层重影有 ±1 页不确定（2.2 节归属 p.257、两电极段归属 pp.258–259、结论 p.267，按页脚就近判定）。
- EM 电荷检测的定标与量纲（"emitted charge" 如何定量）未读——文中未展开数值。
