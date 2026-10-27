# 精读笔记 · Dharap 2004《Flexural strain sensing using carbon nanotube film》（Sensor Review, 24(3):271–273）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。

## 出处
- P. Dharap, Z. Li, S. Nagarajaiah, E. V. Barrera, "Flexural strain sensing using carbon nanotube film," *Sensor Review*, vol. 24, no. 3, pp. 271–273, 2004. DOI: 10.1108/02602280410545399. Rice University（NASA NCC-1-02038 资助）。
- 扫描件 3 页，PDF pp.1–3 = 印刷页 271–273。Emerald 排版，正文文字层完整；个别单位符号疑似误印/误识处标注待核。
- 定位：**材料/传感器实证短文**（CNT 薄膜宏观应变传感），非电路分析文——与本批其余 6 篇不同域，属 P1 的**应用对象侧**背景（MWCNT 导电网络传感层的宏观应变感知先例）+ Kelvin 四线测量的实务先例。

## 核心命题（原文）
1. **总命题：随机取向 SWCNT 薄膜可在宏观尺度作应变传感器，四点探针实测近线性（p.271, Abstract）**：
   > "Strain sensing characteristic of carbon nanotubes has been established in the past at nanoscale. In this study, it is shown that the carbon nanotube film sensors, made up of randomly oriented carbon nanotubes, can be used as strain sensors at macro level. A nearly linear trend between the change in voltage, measured using a movable four point probe, and strains, measured using conventional electrical strain gage, indicates the potential of such carbon nanotube films for measuring flexural strains at macro level. Isotropic strain sensing capability of the carbon nanotube film sensors, due to randomly oriented carbon nanotubes, allows multidirectional and multi-location measurements."
2. **薄膜制备（p.272）**：
   > "The carbon nanotube films used in this study are produced by mixing SWCNTs with 0.25 mg/ml N,N-Dimethylformamide (DMF) and filtering the mixture through a 0.2 mm teflon membrane. Freestanding carbon nanotube film (Buckypaper) is peeled from the filter after rinsing and drying of the remaining material. The carbon nanotube film is further dried for 24 h under vacuum." [OCR损/待核：膜厚印作 ", 15 mm thickness"，与滤膜 "0.2 mm" 同疑似 µ 误作 m——buckypaper 常见厚度为 µm 量级，具体数值待核]
3. **★四点探针（Kelvin）测量法——P2 语境下的实务先例（p.272）**：
   > "The corresponding change in voltage across the carbon nanotube film is measured using four-point probe measurement (Smits, 1958). Input voltage across two outer probes is kept constant during the measurement and change in voltage across the two inner probes is recorded. Strain measurements are also made using conventional strain gage."
   （恒压激励外探针、内探针测压降——正是两端口 Kelvin/四线制结构；出典 Smits 1958 四探针方块电阻测量。**本文只使用该结构、未分析其共模/失配极限。**）
4. **电阻变化由电阻率主导，而非几何尺寸（p.272）**：
   > "The change in voltage is proportional to the change in resistivity of the film (Dharap et al., 2004). The change in voltage due to the change in dimensions of the film is small as compared to the change in voltage due to the change in resistivity of the film (Li et al., 2003)."
   （与金属应变计（几何效应主导）机理相反：CNT 网络传感是**导电网络本身调制**——这正是 P1/DE-DRMS 传感层"网络损伤→电阻跳变"物理机制的文献支点之一。）
5. **结果：近线性 + 偏离与干扰源（p.272）**：
   > "As the strain measured by the conventional strain gage increases from 0 to ,600 mm/m [OCR损/待核：单位应为 µm/m（=600 微应变），µ 误作 mm] the voltage change measured across the two outer probes increases from 0 to ,200 mV [注：此处原文写 outer probes，与 p.272 测量设定（内探针测压）不一致，疑原文笔误]. A nearly linear trend between the change in voltage and the strain is evident; although, deviation from the linear trend exists. Further study is needed to establish causes for deviation from linear trend such as temperature and gas exposure history (Bezryadin et al., 1998; Collins and Avouris, 2000; Hone et al., 2002)."
   （**温度与气体暴露史是线性偏离的候选原因且未解决**——与 DE-DRMS 硬约束"温度补偿是 1% 精度的决定性环节"同向的早期证据；但本文无定量温漂数据。）
6. **结论：各向同性 ⇒ 多向多位测量（p.273）**：
   > "It is evident from the experimental study that the carbon nanotube film can be used for measuring flexural strains at the macroscale. Carbon nanotube films are made up of randomly oriented SWCNTs; hence, their electronic properties are independent of direction. Hence taking measurement along different directions provides corresponding strains. Carbon nanotube films can also be integrated into composites to simultaneously act as strong structural material and sensor. Such composites may find application in smart structures."
   > 另（p.272）："The change in voltage is measured by moving the four-point probe to several parallel locations on a single carbon nanotube film, which also yielded a similar linear trend."

## 关键数值（原文）
- 应变范围 0 → ~600 µε [单位待核，见上]，对应电压变化 0 → ~200 mV（p.272, Figure 4）——近线性，斜率量级 ≈ 0.33 mV/µε（由两端点自算，非原文给出，仅供规模感）。
- 试样：0.25 × 2 × 24 in. 黄铜梁，两点加载纯弯；CNT 膜厚 "~15 mm" [待核，疑 µm]；SWCNT 浓度 0.25 mg/ml DMF；滤膜 0.2 mm [待核，疑 µm]；真空干燥 24 h。
- **无 CMRR/失配/灵敏度温度系数等任何数值**——全文无电路指标。

## 对 P1/P2/P3 的对照
- **P1（消去条件）**：**无**。纯材料实证，无差分滤波、无传递函数、无失配分析。仅"电阻率变化主导电阻变化"（p.272）为 P1/DE-DRMS 传感层物理机制（网络导电调制）提供材料学支点。
- **P2（Kelvin 结构地板）**：**低**。四点探针（Smits 1958）确证 Kelvin 四线是 CNT 薄膜电阻测量的**标准实务**（p.272），即 P2 所论结构在应用域已是通行做法；但本文对该结构零误差分析、零 CMRR 讨论、零失配统计——不触地板问题。
- **P3（平坦度约束衰减上界）**：**无**。
- **方法学（D1–D10）**：**低**。可取的一点：作者把"近线性"与"偏离原因（温度、气体暴露史）"明确分离并列为待研究项（p.272）——与 D 系"先把误差源归因再定判据"的姿态一致，但无判据化内容。
- **killRisk 判断：无**。与「对称性破坏/失配→共模差模转换」毫无接触；本批中最安全的一篇。其价值在应用侧（CNT 薄膜宏观应变传感 + 四线测量实务 + 温度是未解干扰源）。

## 没读到的
- Figure 4（电压-应变曲线）的具体数据点与拟合斜率（图不进 OCR；正文只给两端点 ~600 µε/~200 mV）。
- 引文 Dharap et al. 2004 *Nanotechnology* 15(3):379-82（同组早期系统文）与 Li et al. 2003 *Advanced Materials*（"Carbon nanotube film sensor"）未读——电阻率主导结论的原始出处在这两篇。
- 膜厚、滤膜孔径、应变单位的原文准确值（µ/m 疑云，见上待核）。
- Smits 1958 四探针原始文未读（P2 若要追溯 Kelvin 四线测量的经典出处，可补）。
