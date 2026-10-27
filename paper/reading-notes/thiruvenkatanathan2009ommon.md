# 精读笔记 · Thiruvenkatanathan 2009《Common mode rejection in electrically coupled MEMS resonators utilizing mode localization for sensor applications》（IEEE FCS+EFTF 2009）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> 本篇是 H2 轴的"跨域近亲"：机械域（模态局域化传感器）的共模抑制，关键词是 first-order cancellation——注意它只主张一阶抵消，且以"两谐振器完全相同"为对称前提，与 P1 的全频段精确消去条件有本质区别。

## 出处
- Thiruvenkatanathan, P., Yan, J., Seshia, A. A., "Common mode rejection in electrically coupled MEMS resonators utilizing mode localization for sensor applications", *2009 IEEE Int. Frequency Control Symposium Joint with the 22nd European Frequency and Time Forum*, pp. 358–363, 2009. DOI: 10.1109/freq.2009.5168201。
- 本地 PDF：`fulltext/H2-差分CMRR/thiruvenkatanathan2009ommon.pdf`（6 页；PDF 页 1–6 = 印刷页 358–363，原生数字文本）。
- 单位：University of Cambridge, Department of Engineering。

## 核心命题（原文）
1. **模态局域化传感的两大卖点之一就是"内禀共模抑制"**（p.358, Abstract）：
   > "Measuring shifts in eigenstates due to vibration localization in an array of weakly coupled resonators offer two distinct advantages for sensor applications as opposed to the technique of simply measuring resonant frequency shifts: (1) orders of magnitude enhancement in parametric sensitivity and (2) intrinsic common mode rejection."
   （P1 论文若引用此篇，只能作为"对称结构共模抑制是跨域通用思想"的证据，不是电路域消去条件。）

2. **共模/差模的机理表述——只主张一阶抵消**（p.359）：
   > "any effects on the stiffness due to ambient environmental fluctuations (e.g.: temperature) would affect both the identical resonators to the same extent thereby leading to a common mode cancellation of these effects to the first order. However, any changes in the stiffness on one of the resonators relative to the other (differential mode), leads to significant shifts in the eigenstates under conditions of weak internal coupling as expressed in equation (1)."
   （关键限定词 "to the first order"：该域的"共模抑制"是微扰一阶效应，非精确恒等；与 P1 的 G_DC(s)≡0 全频段条件不在同一层级。）

3. **对称前提 = 两谐振器完全相同**（p.359）：
   > "When the two resonators are perfectly identical (m1= m2 = m; k1= k2 = k) the system is symmetric about the coupling spring and the vibrations propagate evenly throughout the system. Any structural perturbation on one of the resonators however, disturbs the symmetry of the system thereby inducing a localization of the vibration modes."
   （与差分滤波器的"理想匹配才有无穷 CMRR"同构；失配后果是"对称被破坏"，但文中未给失配→误差的解析式。）

4. **灵敏度解析式（一阶微扰）**（p.359，式 (1)(2)）：
   > "(u_n − u0_n)/u0_n ≅ Δk/(4k_c) ; (n = 1,2)."（式 1，本征态相对漂移）
   > "(f − f0)/f0 ≅ Δk/(2k)"（式 2，谐振频率相对漂移）
   > "it can be noticed that for any value of kc < k/2, the relative shifts in the eigenstates are more sensitive than those in frequency."
   （弱耦合 kc 越小灵敏度越高——本征态灵敏度以 1/(4k_c) 计，频率灵敏度以 1/(2k) 计。）

5. **温度实验结论：本征态输出对温度漂移的相对不敏感约一个量级**（p.361）：
   > "It can be observed that while the shift in the resonant frequency (first eigenvalue) decreases with increasing temperature (for the same induced stiffness variation), the shifts in the measured eigenstate yield a relative insensitivity of nearly one order of magnitude."

6. **气压实验结论：本征态漂移对气压/Q 不敏感**（p.362）：
   > "It can be observed that while the relative shifts in the resonant frequency remain relatively constant up to about 100mTorr, they change at higher ambient pressure. However, the relative shifts in the eigenstates remain relatively unaffected by fluctuations in the ambient pressure."
   > "This suggests that the sensor resolution is no longer limited to the Q factor thereby providing an important advantage for sensor design."

## 关键数值（原文）
- 灵敏度增强："over three orders of magnitude greater than corresponding resonant frequency variations"（Abstract p.358；正文 p.360 重述，且引 [8] 说 electrical coupling 已实测 "exceeding two orders of magnitude"）。
- 施加刚度扰动：".232N/m on resonator 2"（p.361, 温度实验）。
- 温度扫描："300K (+/-0.5K) up to 340K (+/-0.5K) in steps of 20K"，气压 "20μTorr"（p.361）。
- 气压扫描："10mTorr to 1 Torr"，温度 295K ±0.5K（p.362, DETF 结构）。
- 直流偏置：环结构 +20V/−20V，resonator 2 从 −20V 增到 −5V（步进 5V）；DETF +5V/−5V，扰动时 resonator 2 升到 +6V（p.360/362）。
- 器件几何：DETF 臂 25μm 厚 × 300μm 长 × 6μm 宽、臂间隙 6μm；环内/外径 190/220μm、厚 10μm（p.360）。
- 无任何 dB 形式的 CMRR 数值、无频域传递函数、无失配灵敏度解析式。

## 对 P1/P2/P3 的对照
- **P1（消去条件）**：中低相关。跨域提供"结构对称→共模一阶抵消"的同类思想（差分滤波器共模路径对称→CMRR），但其抵消明确限定 "to the first order"，且理想对称前提写成 "perfectly identical (m1=m2=m; k1=k2=k)"——**没有**给出任何"何参数组使共模响应在全频段精确为零"的条件，也没有多级/级联结构分析。最接近的表述即上面第 2 条引文，距离 P1 的 τ 匹配充要性/交叉项命题很远。
- **P2（Kelvin 结构地板 ≈56 dB）**：无。无 Kelvin 接法、无引线/结构电阻地板概念（其"耦合间隙"是电学负弹簧，非引线电阻）。
- **P3（平坦度约束衰减上界）**：无。无滤波器平坦度/阻带衰减内容。
- **方法学（D1–D10）**：低相关，但"共模=两臂同受环境、差模=单臂受载"的分解语言与差分滤波器 CM/DM 分解同构，可在相关工作里作为"跨域（机械域）同型思想"一笔带过；引用时务必注明其只为一阶近似主张。
- **killRisk 判断：无**。不含多级无源网络精确消去条件或失配→CM 误差解析条件；不存在动摇 P1 优先权的表述。

## 没读到的
- 图 6/7/10/11/14/15（各实验数据图）只读到正文描述，图形纵轴刻度未能核对（"over three orders"与"nearly one order"为正文自述，未见图上数值）。
- 引文 [8]（Transducers 2009, in press）是同组灵敏度增强前作，本文未展开其推导。
- 失配（两谐振器不完全相同）情形的解析处理完全缺失——文章只有"对称被破坏→模态局域化"的定性说法，未给 δk/k 与本征态漂移的失配传播公式。
- 未读到任何 CMRR 的 dB 定量定义或测量方法。
