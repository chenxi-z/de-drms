# 精读笔记 · Denisenko 2020《Low Pass Anti-Alias Filter for ADC with Differential Input on Base Op-Amp with Differential Output with a Minimum Number of Capacitors》（IOP Conf. Ser.: Mater. Sci. Eng. 862）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
## 出处
- Denisenko, D. Yu.; Prokopenko, N. N.; Butyrlagin, N. V.（顿河国立技术大学 / 南联邦大学 / 俄罗斯科学院 IPPM）
- IOP Conference Series: Materials Science and Engineering 862 (2020) 032073, doi:10.1088/1757-899X/862/3/032073（MIP: Engineering-2020 会议）
- PDF 共 7 物理页（第 1 页为封面页，正文及参考文献 p.2–7）。全文已读。

## 核心命题（原文）
1. **全差分运放三阶低通滤波器、比经典结构少一颗频率设定电容**（p.2，摘要）：> "The developed circuit contains one capacitor less than in classical LPF."（拓扑创新点是省电容数、降低元件失配敏感面，不是共模误差解析。）
2. **对称工作需通道元件成对匹配**（p.4）：> "Under a number of conditions R1 = R2, R3 = R4, R5 = R6, R7 = R8, C2, = C3, which in the circuit (figure 1) it is necessary to provide for the symmetrical operation of the filter channels, the transfer function coefficients (1) are found using the following expressions"（把 R、C 成对相等作为前提假设直接代入系数推导，未分析失配量→CM 误差的映射，也没给全频段消去条件。）
3. **滤波器阶数↑→元件失配敏感性↑**（p.2，引言）：> "the filter becomes very sensitive to the spread of the nominal values of its elements and requires precise precision tuning [4-17]."（定性承认失配敏感性，与 P1 的动机同向，但止于定性。）
4. **用途定位 = 差分输入 ADC 的抗混叠滤波**（p.6，结论）：> "The developed low-pass filter is recommended as an anti-aliasing filter to limit the spectrum of signals at the input of an ADC with a differential input."（场景与 P1 相同——差分 AAF 前置于 ADC——但为有源全差分运放方案。）

## 关键数值（原文）
- 三阶 LPF，4 颗频率设定电容（经典三阶为 5 颗）（p.4–5）：> "the low-pass filter circuit (figure 2) provides (curve 1) close to ideal (theoretical) amplitude-frequency response (curve 2) with four frequency-limiting capacitors"。
- 仿真工具/模型：Micro-Cap 12 + TI THS4130 全差分运放模型（p.4）：> "Computer simulation of the LPF circuit (figure 2) was run in Micro-Cap environment [23-26] (figure 3) on based on models of THS4130 Op-Amp [27] by Texas Instruments."
- 传函形式（p.3）：F(p)=a0/(p³+a2p²+a1p+a0)，系数式 (2)–(5)（M=R5/R1 等，全部在 R、C 成对相等假设下）。
- 无任何 CMRR/失配数值、无实测数据（仅 Micro-Cap 仿真，THS4130 曲线 vs 理论曲线对比）。

## 对 P1/P2/P3 的对照
- **P1（无源差分网络失配→CM 误差解析条件）**：低。有源全差分 AAF 拓扑简化文献；对称条件仅是「令两通道系数相等」的工程假设，无失配→CM 误差解析式、无消去条件、无 τ=R·C 匹配充要性讨论。属 P1 相关工作里的「有源 AAF 现状」脚注，谱系层无位置。
- **P2（Kelvin 结构地板 ≈56dB）**：无。全文无共模抑制、无结构地板概念。
- **P3（平坦度约束衰减上界）**：低。它给的是三阶有源 LPF 的平坦通带设计，未讨论「平坦度⇄阻带衰减上界」的权衡定理。
- **方法学（D1–D10 门槛化）**：无。设计流程是系数式+仿真验证，无门槛化方法学。
- **killRisk 判断**：无威胁。与 P1 四主张无解析重叠；可在 P1 相关工作里作为「差分 AAF 的有源路线（省元件数）」引用一句，说明其对称条件是假设而非被分析的失配通道。
- 谱系定位：不属于四层谱系（Bartlett/Forte → Gasulla → Koide → Zhang 2020）任一层；是与谱系平行的俄系有源滤波线（Prokopenko 组）。

## 没读到的
- 图 1/图 2 电路细节仅见图题与系数式，未逐元件核对（图形未 OCR 出网络拓扑）；THS4130 仿真的具体频率坐标/衰减数值在图 4 内，文字未给数值，无法引用具体 dB 数。
