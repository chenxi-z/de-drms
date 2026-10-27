# 精读笔记 · McCreary & Gray 1975《All-MOS Charge Redistribution A/D Conversion Techniques—Part I》（IEEE JSSC SC-10(6):371–379）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> 页码用期刊页（371–379）；PDF 页 1–9 与之差 370。注意：本地 PDF 末页（p.379 起）还附有姊妹篇 Part II（Suarez/Gray/Hodges，pp.379–385）的首页，bib 题录只登记 Part I。

## 出处
- McCreary, J.L., Gray, P.R., "All-MOS Charge Redistribution Analog-to-Digital Conversion Techniques—Part I", IEEE Journal of Solid-State Circuits, vol. SC-10, no. 6, pp. 371–379, Dec. 1975. doi:10.1109/jssc.1975.1050629.
- 本地：`H2-差分CMRR/mccreary1975allmos.pdf`（9 页；第 9 页含 Part II 首页）。bib key：`mccreary1975allmos`（literature.bib L1515）。
- 姊妹篇 Part II：Suarez, Gray, Hodges, 同期 pp. 379–385（双电容法，"inherently monotonic in the presence of capacitor ratio errors"，见本地 PDF 末页摘要）。

## 核心命题（原文）

1. **用电容不用电阻：匹配精度由版图几何决定（电荷域精度思维的开山）**（p.371）：
   > "In contrast to its utilization as a current switch, the MOS device, used as a charge switch, has inherently zero offset voltage and as an amplifier has very high input resistance. In addition, capacitors are easily fabricated in metal gate technology. Therefore, one is led to use capacitors rather than resistors as the precision components, and to use charge rather than current as the working medium."（p.371）
   中文：精度来源从"元件绝对值"迁到"元件比值"——一切后续匹配极限讨论的起点。
2. **结构性消错先例①：端点对电容失配免疫（比值误差不产生增益/失调误差）**（p.373）：
   > "In this technique a mismatch in the binary ratios of capacitors in the array causes nonlinearity. It cannot cause a gain error because the end points of the transfer function curve, Vout versus Vin, are not dependent on capacitor matching. This results from the fact that no net charge redistribution between capacitors occurs for either zero or full-scale input since all capacitors are either fully discharged or fully charged, respectively. For the same reason no offset error can arise from capacitor mismatch since the mismatch cannot be manifested unless a charge redistribution exists in the final configuration."（p.373）
   中文：**拓扑使特定误差项恒等消失**——与 P1"G_DC≡0 的消去条件"同一种论证结构（某些工作点上失配数学上无法表现）；P1 可引此作为"结构性消错"传统的集成电路源头。
3. **灵敏度分层：线性度对大电容失配敏感、对小电容失配迟钝（配对不变量的先例）**（p.373, Fig.5）：
   > "The plot of sensitivity, also shown in Fig. 5, shows that linearity is very sensitive to a fractional change in the large capacitors, but not very dependent upon similar fractional changes in the smaller capacitors. Therefore, the smaller capacitors have great allowable tolerances. It should be pointed out that actually all capacitors have simultaneous deviations which cause ratio errors and the worst case combination of these must always be considered."（p.373）
   中文：逐元件灵敏度分析（ΔVT/VR 对 ΔCN/CN）——"哪些元件的失配才要命"正是 P1 配对不变量分析（哪些 R·C 乘积项进入 G_DC）的方法学前身。
4. **结构性消错先例②：单位单元并联 + 共心版图对抗侧蚀与氧化层梯度**（p.374, Fig.6/7）：
   > "This problem can be circumvented by a geometry such that the perimeter lengths as well as the areas are ratioed. This can be done, as seen in Fig. 6, by paralleling identical size plates to form the larger capacitors. Thus the capacitor ratios are not affected by undercut."（p.374）
   > "Error from this source can be minimized by improved oxide growth techniques and by a common centroid geometry. This is done in Fig. 7 by locating the elements of the capacitors in such a way that they are symmetrically spaced about a common center point. In this way the capacitor ratios may be maintained in spite of first-order gradients."（p.374）
   中文：版图级"不变量工程"——把比值做成单位单元计数比（一阶侧蚀不变）、把一阶梯度做进对称性（共心）而恒等抵消；P1 的匹配策略若含版图措施，此为必引经典。
5. **寄生电容免疫（采样-回归零点结构）**（p.373）：
   > "Hence, the charge on this parasitic is the same in the final configuration as it was in the sample mode. Therefore, the error charge contributed by this parasitic is very near zero. For the 10-bit converter the parasitic capacitance at the top plate can be 100 times the value of the smallest capacitor and still cause only 0.1 bit offset error."（p.373）
   中文：结构使 100× 寄生只表现为 0.1 bit 失调——又一个"结构性消错"实例（且可再被失调存储电路消掉）。
6. **匹配是产率问题：10 bit 只有 45% 良率（匹配极限的定量基线）**（p.378）：
   > "Assume for a moment that capacitor ratio error were the only factor affecting yield. Then from these data the yield for ±½ LSB linearity for 8, 9, and 10 bits resolution would be 98 percent, 94 percent, and 45 percent, respectively, for this sample of 47 functional arrays."（p.378）
   中文：匹配路线的精度天花板以统计产率形式给出——P1 论证"容差路线有地板"时可引此作跨域旁证（匹配精度不是确定性承诺而是分布）。

## 关键数值（原文）

- 电容匹配统计（Fig.14, p.378）：47 个 10-bit 阵列、3 片晶圆；±½ LSB 线性度良率 8/9/10 bit = 98%/94%/45%。
- 实测性能（Table I, p.378）：分辨率 10 bit、线性度 ±½ LSB、输入 0–10 V、输入失调 2 mV、增益误差 <0.05%（外基准）、采样建立 2.3 µs、总转换时间 22.8 µs（≈44 kHz 采样率）。
- 版图参数（p.377）：电容阵列共 240 pF；大电容由 3×3 mil 小方单元并联而成；芯片实测 75×58 mils，含数字控制估计 90×90 mils；拐角圆化用 90°/270° 拐角等数一阶相消。
- 温度/电压系数（p.374–375）：SiO₂ 介质电容温度系数 ≈20 ppm/°C（扩散电阻 ≈2000 ppm/°C、薄膜/注入电阻数百 ppm/°C）；MOS 电容电压系数 <24 ppm/V（10-bit 下可忽略）；氧化层梯度实测 10–100 ppm/mil。
- 寄生容限：顶板寄生达最小电容 100× 仅 0.1 bit 失调（p.373）。
- 开关误差（p.376）：0.1% 误差、10 µm 沟长 N 管 → 最小采集时间 ≈3 µs（"3 ps"为 OCR 误识，量级按上下文为 µs，待核）。

## 对 P1/P2/P3 的对照

- **P1（失配消去条件）**：相关性**中（方法论先例，非对手）**。本文无差分滤波器/共模内容，但它是"匹配作为精度来源 + 结构性消错"两大思想的奠基文献：①端点免疫（失配在特定配置下数学上无法表现）与 P1 的恒等消去同构；②逐元件灵敏度分层与 P1 配对不变量分析同构；③单位单元/共心版图是"用结构换匹配"的极致。P1 引用定位：说明"结构性消错"谱系（McCreary 电荷域端点免疫 → P1 频域 G_DC 恒等消去），并强调 P1 的增量在**频域全带消去条件与多级梯形**，而非匹配工程本身。
- **P2（Kelvin 地板）**：无直接内容；但"45% 良率@10 bit"是"匹配路线统计地板"的经典数据点，可作 P2 数值论证的跨域对照（引用时注明域不同：电容比值 vs 差分滤波器）。
- **P3（平坦度约束衰减上界）**：无（无滤波器内容）。
- **方法学（D1–D10）**：无正式方法学；但"所有电容同时偏差、必须考虑最坏组合"（p.373）与灵敏度分层（Fig.5）可作 D 项"最坏组合 vs 敏感子集"的设计核查项素材。
- **killRisk 判断**：非 killRisk（1975 年集成电路域，与 P1/P2/P3 无主张冲突）。

## 没读到的
- 差分/共模/CMRR/滤波器内容（全文无）；
- Part II 双电容法正文（本地 PDF 只有其首页摘要——"inherently monotonic in the presence of capacitor ratio errors"这一结构性鲁棒性结论值得后续补读，题录待核：Suarez/Gray/Hodges 1975）；
- Kelvin 结构、引线电阻；
- OCR 噪声处：Fig.5 纵轴灵敏度数值、式(1)电荷表达式、µs/ps 单位个别处（引用前对 IEEE Xplore 原版核验）。
