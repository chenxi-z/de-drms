# 精读笔记 · Prokopenko 2020《The Method of Increasing of CMRR for CJFET Dual Differential Input Stages…》（IEEE EWDTS 2020, pp. 1–5）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> 说明：PDF 5 页即刊页 1–5。公式在下文中用普通字符转写（σ/Σ 等符号按 PDF 文本层）。

## 出处
Prokopenko, N.; Zhuk, A.; Pakhomov, I.; Budyakov, P.; Titov, A. "The Method of Increasing of CMRR for CJFET Dual Differential Input Stages for the Tasks of Processing Sensor Signals Under Conditions of Cryogenic Temperatures and Penetrating Radiation", 2020 IEEE East-West Design & Test Symposium (EWDTS), pp. 1–5. DOI: 10.1109/EWDTS50664.2020.9225016.（顿州国立技术大学等；俄罗斯科学基金会 16-19-00122-P 资助）
全文：`fulltext/H2-差分CMRR/prokopenko2020cmrr.pdf`

## 核心命题（原文）
1. **共模跨导精确置零条件（本文最接近 P1 命题的表述，逐字引用）**（p.2，跨页句的条件部分在 p.2）：
   > "On the base of the first Kirchhoff's law, it can be found that the output current of adder Σ1 in the scheme of Fig. 1, due to the change in the input common-mode signal vc=0.5(vc1+vc2) will be zero, if: (2K3-K1)gcm.1 = (K2-2K4)gcm.2, (1)"
   （这是差分输入级输出节点上共模电流的**代数精确消去条件**：系数 (2K3−K1) 与 (K2−2K4) 分别配 gcm.1/gcm.2。式中 gcm.1=i1/vc、gcm.2=i2/vc 为两条支路对共模的跨导，K1–K4 为输出电流加法器的电流传输比。）

2. **充分实现：每支路自消零，规避 gcm 失配**（p.2）：
   > "In the general case, gcm.1≠gcm.2. Therefore, to reduce the influence of the current-stabilizing one-port devices consisting of elements R1 and M3, as well as R2 and M6, on the transconductance vc to the output node Out.1, it is necessary to provide the following current ratios using the circuitry of adder Σ1: K3=0.5K1, K4=0.5K2. (2)"
   （取 K3=K1/2、K4=K2/2 时式 (6) gcm=gcm.1(K1−2K3)+gcm.2(K2−2K4) 的两个括号**各自为零**，共模输出与 gcm.1/gcm.2 是否相等无关——参数失配免疫的**结构性消去**，思路与 Gasulla 2002 浮容 G_DC≡0 同谱系，但这是有源跨导域实现。）

3. **系数化综合方法学**（p.2）：
   > "Thus, the synthesis of practical analog circuits with the architecture of Fig. 1 is reduced to providing the required numerical values of modules K1, K2, K3, K4, as well as their signs, which provide the increased CMRR: CMRR = gd/gcm, (5)"
   （把 CMRR 提升归结为加法器电流比系数的取值与符号设计；符号约束另有式 (3) signK1=signK2、式 (4) signK3=signK4。）

4. **CMRR 极限（地板）由静态工作点对称性决定——频率相关**（p.3）：
   > "The results of computer simulation (Fig.3) of common-mode signal transconductances of the circuit of Fig. 2 in the frequency range are shown, that the limiting values of CMRR depend on the symmetry of the static mode with respect to the gate-drain voltage of the transistors of differential pairs M1–M2, M4–M5, as well as the non-identity of the static voltages at the drains of the composite transistors M3 and M6."
   （消去后的残余地板来自静态偏置对称性——概念上与 P2「结构地板」平行：残余由结构/偏置非理想决定而非名义增益；但文中只以仿真曲线呈现频率依赖（Fig. 3/5/7/9），未给解析式。）

5. **结论：误差降 2–3 个数量级**（p.4）：
   > "The computer simulation results show that the considered options for constructing a dual differential input stage based on inverted cascodes and current mirrors reduce by 2–3 orders of magnitude the error from the input common-mode signal, brought to the input of the amplifier."

## 关键数值（原文）
- 精确置零条件（p.2，式 (1)）：(2K3−K1)gcm.1 = (K2−2K4)gcm.2；充分条件（式 (2)）：K3=0.5K1、K4=0.5K2。
- 共模跨导合成式（p.2，式 (6)）：gcm = gcm.1(K1−2K3) + gcm.2(K2−2K4)。
- CMRR 增益倍数（p.2）：补偿后相对 K3=K4=0 的提升 "reaches one or two orders"，即式 (10) N = 2/(K1−2K3+K2−2K4) >> 1（gcm.1≈gcm.2≈gcm、K1≈K2≈1 时）。
- 误差下降（p.4，结论）："reduce by 2–3 orders of magnitude the error from the input common-mode signal"。
- 两种实现取值：折叠共源共栅版 K3=K4=0.5（p.3，Fig. 4）；双输入电流镜版 A1=K1=K2=−1、A2=K3=K4=−0.5（p.3，Fig. 6）。
- 仿真条件：LTspice + CJFET 模型，温度点 t=27°C 与 −197°C（p.4，Fig. 9 图题："The frequency dependence of the conductivity transmission gcm of the input common-mode signal to the DDS output Fig. 8 at t=27°C (a) and -197°C (b)."）；共模跨导随频率的曲线见 Fig. 3/5/7/9（**曲线上具体 dB/西门子数值在文本层不可提取，待核**）。
- 应用定位（p.1，摘要）："low-noise analog interfaces of sensors of various physical quantities applied in medicine, high-energy physics, and space instrument engineering"。

## 对 P1/P2/P3 的对照
- **P1（消去条件）**：**中高相关——同构不同域**。式 (1) 是货真价实的「输出共模响应精确为零」代数条件，且式 (2) 展示了「让每个失配敏感项各自为零」的免疫化设计——与 P1 的单级 τ=R·C 匹配（参数消去）vs 多级交叉项（参数消去失效）形成鲜明对照：Prokopenko 走的是**系数由电路结构（电流镜精确除 2）锁定**的结构性消去，类似 Gasulla 浮容拓扑在有源域的镜像。**关键差异（不构成 killRisk 的理由）**：① 其条件是静态跨导域的代数等式，无 s 域多项式、无 RC 交叉项、无「多级梯形」对象；② 全频段行为只以仿真曲线给出，未讨论精确消去条件随频率失效的解析机制；③ 器件为 CJFET 有源结构而非无源网络。可在 P1 论证中作为「结构性消去 vs 参数性匹配」谱系的有源域旁证引用。
- **P2（Kelvin 结构地板 ≈56 dB）**：低相关。无 Kelvin 接法、无 dB 地板数值；但 p.3「CMRR 极限取决于静态模式对称性」与 P2 的「残余由结构决定、不随名义增益改善」在概念上同构，可作地板论证的引用点（数值不可比）。
- **P3（平坦度约束衰减上界）**：无。
- **方法学（D1–D10）**：可借用其「消去条件 → 系数符号/模值约束（式 2–4）→ 电路实现（两方案）→ 仿真验证（含温度轴）」链条；温度轴（27 °C / −197 °C）对 D 系列的环境敏感性维度有参考价值。
- **killRisk 判断：低**。最接近表述为 p.2 式 (1)（已逐字引用）；因其为有源跨导域静态条件、无 s 域多级结构，不预占 P1 的「多级无源网络全频段精确消去不再充分」命题。

## 没读到的
- 共模跨导/CMRR 的**绝对 dB 数值**：正文只给「1–2 个数量级」「2–3 个数量级」，图 3/5/7/9 纵轴数值在文本层缺失，待核。
- 消去条件随频率失效的解析表达（寄生电容如何进入 K 系数或 gcm）——只有仿真曲线，无公式。
- 对消去后残余噪声/失调的温度漂移定量数据（−197 °C 曲线只有图）。
- 差模增益 gd 的具体数值与 CMRR 绝对值换算。
- 未涉及任何无源 RC 差分滤波器或抗混叠场景。
