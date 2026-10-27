# 精读笔记 · Wen, Wang & Chung 2000《Piezoresistivity in continuous carbon fiber polymer-matrix and cement-matrix composites》（J. Mater. Sci. 35:3669–3675）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> 页码用期刊页（3669–3675）；PDF 页 1–7 与之差 3668。材料学论文（碳纤维复合材料压阻自传感），落在 H2 批内属**应用域证据**：四探针（Kelvin）结构对电阻传感的必要性。

## 出处
- Wen, S., Wang, S., Chung, D.D.L., "Piezoresistivity in continuous carbon fiber polymer-matrix and cement-matrix composites", Journal of Materials Science, vol. 35, pp. 3669–3675, 2000. doi:10.1023/a:1004842303468.
- 本地：`H2-差分CMRR/wen2000piezore.pdf`（7 页）。bib key：`wen2000piezore`（literature.bib L1548）。

## 核心命题（原文）

1. **总发现：连续碳纤维水泥基/聚合物基复合材料的压阻方向相反，机理不同**（p.3669 摘要）：
   > "The DC electrical resistance in the fiber direction increased upon tension in the fiber direction for the cement-matrix composite, due to fiber-matrix interface degradation, but decreased upon tension for the polymer-matrix composite due to increase in the degree of fiber alignment."（Abstract, p.3669）
   中文：同一物理量（纤维向电阻）在两种基体下符号相反——测量构型与机理强耦合，应变传感不能脱离材料体系谈。
2. **四探针优于两探针：接触电阻从被测电阻中剔除（P2 Kelvin 动机的核心引文）**（p.3669–3670）：
   > "The four-probe method [1, 2, 4] is in general better than the two-probe method [5–12], due to the elimination of the contact resistance from the measured resistance."（p.3669）
   > "the four-probe method (Figs 1 and 2) yields the volume resistance, whereas the two-probe method (Figs 3 and 4) yields mainly the contact resistance. Therefore, for use of the composite as a strain sensor, the four-probe method is necessary."（p.3672）
   中文：**"四探针必要"是本文的硬结论**——两探针测到的主要是接触电阻而非体电阻；这是 P2（Kelvin 结构地板）在传感材料端的经典支撑文献。
3. **两探针的伪压阻：接触电阻随应变变化，甚至翻转应变系数符号**（p.3671–3672）：
   > "For both two-probe configurations (Figs 3 and 4), the resistance increased upon tension, in contrast to the opposite trend for both four-probe configurations (Figs 1 and 2)."（p.3671）
   > "Because the resistance increase in Figs 3 and 4 is not due to a change in volume resistivity, but a change in contact resistivity, the phenomenon of Figs 3 and 4 is not true piezoresistivity. … this effect is not suitable for use in strain sensing, because the quality of an electrical contact is hard to control in practice (especially in a real structure) and the gage factor associated with this phenomenon depends on the contact quality, which is reflected by the contact resistance before loading."（p.3672）
   中文：非 Kelvin 构型不仅精度差，还会把接触劣化伪装成传感信号（+9.6 vs −22 的符号翻转）——P2 论证"结构决定可达下限"时最有力的实证反例。
4. **接触电阻占实测值的定量拆解**（p.3672）：
   > "Based on the resistivity of the composite in the fiber direction (4.1 × 10⁻³ Ω·cm), the volume resistance of the whole sample of Fig. 4 in the fiber direction was calculated to be 0.74 Ω. This means that the high resistance in Fig. 4 [6.79 Ω] is almost all due to the contact resistance. … the resistance in Fig. 3 is dominated by the contact resistance."（p.3672）
   中文：两探针端接 6.79 Ω vs 体电阻 0.74 Ω——接触电阻近 9 倍于信号载体；无 Kelvin 结构时误差不是百分比而是量级问题。
5. **水泥基压阻机理：低应变=界面可逆松脱（大应变系数），高应变=纤维断裂（突变）**（p.3673–3674）：
   > "The abrupt increase in resistance at high strains is accompanied by a decrease in modulus (Fig. 6), so it is attributed to fiber breakage. The smaller increase in resistance at low strains is not accompanied by any change in modulus (Fig. 6), so it is attributed to fiber-matrix interface degradation."（p.3674）
   > "The large gage factor means that the resistance increase cannot be explained by the dimensional change, which would have resulted in a gage factor of 2 only."（p.3674）
   中文：纯尺寸效应的应变系数只有 2；实测 17–60 全部来自微观机理——电阻法结构健康监测的信号来源界定（与 DE-DRMS 的 MWCNTs 导电网络"结构损伤分级"同谱系）。

## 关键数值（原文）

- 聚合物基（58 vol% 纤维，[0]₈ 层合板）：实测电阻率 4.1×10⁻³ Ω·cm（混合定律计算 3.8×10⁻³）；应变系数：四探针全周向 **−22**、四探针混合（端部电流+周向电压）**−3.8**、两探针周向 **+5.5**、两探针端接 **+9.6**（p.3671–3672）；加载前电阻 0.243/0.206/0.774/6.79 Ω（Fig.1–4 顺序，p.3671–3672）；45 mm 段体电阻计算值 0.19 Ω、整样 0.74 Ω（p.3672）。
- 水泥基（2.57–7.37 vol%）：应变系数达 **+60**（结论 p.3675）；Table IV（p.3674）：2.60% 纤维 32.6±7.9/24.6±6.9/16.3±1.3（50/100/150 lb 三循环），5.14% 为 57.6±2.8/41.7±2.6/40.9±1.7，7.24% 为 33.7±6.5/24.0±2.0/23.4±3.6；Fig.7 首三循环 28/21/17（p.3673）；应力-应变线性至 0.2% 应变后电阻突增（p.3673）；断裂时 12% 纤维破断（p.3675）。
- 电阻率（水泥基，Table V，p.3674）：实测 (1.10±0.11)×10⁻¹ / (8.40±0.94)×10⁻² / (4.56±1.32)×10⁻² Ω·cm，均高于混合定律计算值（5.91/2.83/1.86 ×10⁻²）。
- 测量条件：Keithley 2001（聚合物）/2002（水泥）万用表，银导电工胶四探针，MTS 810 液压机循环拉伸，位移速率 0.5 mm/min（p.3671, 3673）。
- 碳纤维参数：聚合物基 T-300(6K) 电阻率 2.2×10⁻³ Ω·cm、直径 7 µm（Table I，p.3670）；水泥基 Thornel P-25 电阻率 1.3×10⁻⁴ Ω·cm、直径 11 µm（Table II，p.3672）；水泥浆电阻率 ~10⁵ Ω·cm（p.3670）。

## 对 P1/P2/P3 的对照

- **P1（失配消去条件）**：相关性**无**。全文无差分滤波器/共模/CMRR/RC 匹配内容（四探针的"消除接触电阻"是直流通路选择问题，不是 G_DC=H_N−H_P 的频域消去问题——引用时勿混淆两个"消除"）。
- **P2（Kelvin 结构地板 ≈56 dB）**：相关性**中高（应用域支撑）**。本文是"四探针必要性"的标准材料学引文：两探针测接触电阻（伪压阻、符号翻转、量级污染），四探针测体电阻——P2 主张"Kelvin 结构是测量系统精度地板"时，本文提供传感端动机与失效模式实证；但注意本文无任何 dB/CMRR 口径，不能直接给出 56 dB 数值，地板数值仍需 P2 自证。
- **P3（平坦度约束衰减上界）**：无（无滤波/频率响应内容，纯直流电阻测量）。
- **方法学（D1–D10）**：无正式方法学；但"接触构型改变被测物理量本身"（four-probe vs two-probe 测的是不同量）可作为 D 项"测量构型定义被测对象"的警示案例。
- **killRisk 判断**：非 killRisk（应用域文献，与 P1/P2/P3 无主张冲突）。

## 没读到的
- 差分测量/共模/滤波器内容（全文无）；
- 交流/频率依赖的电阻测量（纯 DC，Keithley 万用表四探针）；
- Kelvin 引线电阻的定量误差预算（只论证接触电阻主导，未给引线电阻分解）；
- 温度效应/温度系数（全文未涉）；
- MWCNTs 体系（对象是连续碳纤维束复合材料，非碳纳米管网络——与 DE-DRMS 传感层同谱系但材料不同）。
