# 精读笔记 · Hornero 2021《Common Mode Response Effects in Differential Measurements》（AEU 128:153510）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> **本文是 P1 的 killRisk 最近前作**（P1 四增量划界基线），逐节精读；页码 = PDF 页（与排版页码一致，共 20 页）。

## 出处
- Hornero, G., Casas, Ó., Pallàs-Areny, R., "Common Mode Response Effects in Differential Measurements", AEU – International Journal of Electronics and Communications, vol. 128, 2021, 153510. doi:10.1016/j.aeue.2020.153510.
- 本地：`H2-差分CMRR/hornero2021cm.pdf`（20 页，含 Fig.1–4 与 Table I–IV）。
- bib key：`hornero2021cm`（literature.bib L594）。

## 核心命题（原文）

1. **摘要即立论：共模响应=元件容差的函数，可呈带通+峰化+正相移，且容差压到 ±0.01% 也躲不掉 +90° 相移**（p.1）：
   > "In this paper we demonstrate that the common-mode response depends on component tolerance and can be band-pass with gain peaking and positive phase shifts inside differential signal passband. Tolerances as low as ±0.01% cannot prevent phase shifts close to +90º."（摘要）
   中文：这是全文总命题——GDC 不是"小直流偏置"而是容差塑形的动态传递函数；峰化由容差比决定，与绝对精度级别无关。
2. **P1 的同构方程：GDC(s)=G2(s)−G1(s)，两支路传递函数相减**（p.4）：
   > "hence the common-mode-to-differential gain is [4]
   > GDC ( s ) = G2 ( s ) − G1 ( s ) = G2 ω2/(s + ω2) − G1 ω1/(s + ω1)  (5)
   > and GDC(0) = G2 – G1 = ∆G."
   中文：与 P1 的 G_DC(s)=H_N−H_P 完全同构（减法结构）；但 Hornero 只做**单级一阶模型**，未触及多级梯形。
3. **失配产生左半平面零点 ωzc，位置由 tG/tω 比值决定、与直流增益无关**（p.5）：
   > "ωzc = ωa (tG/(tG+tω))(1−tω²)  (10) … Therefore, ωzc will be different from zero whenever tG ≠ 0 and proportional to the average corner frequency but independent from the dc gain."
   > "the mismatch between two first-order low-pass systems leads to a band-pass response for GDC that at ωzc raises by 3 dB with respect to GDC(0) = ∆G"（p.5）
   中文：GDC 带通化的机理=失配在分子造出一个零点；ωzc 落在差分通带内（"it will fall well inside the differential circuit passband"，p.5）。
4. **峰化判据 tω>(√2−1)tG≈0.4tG；峰值 GDCmax≈Ga(tG+tω)（两种容差相加）**（p.6）：
   > "Solving for tω yields … that for tG << 1 can be simplified into tω > (√2 – 1)tG ≈ 0.4tG, meaning that GDC peaking is determined by corner frequency mismatch relative to dc gain mismatch."（p.6）
   > "If ωzc is small enough, then the maximal gain is GDC max ≈ Ga ( tG + tω )  (13) meaning that dc gain and corner frequency tolerance effects add each other."（p.6）
5. **两个特例= P1「消去条件」的直接证据**（p.7–8）：
   - 直流增益匹配（tG=0）时 Eq.(17)：GDC = Ga(ω2−ω1)s/((s+ω1)(s+ω2))，
     > "which implies a positive phase response from dc up to frequencies above ω1, which is a wider range than that when tG ≠ 0."（p.7）
     中文：只配平增益（调 R 比值）不配 τ → 零点移到原点、带通、通带内全域正相移——**更糟**。
   - 转角频率匹配（tω=0，即单级 τ 匹配）时 Eq.(18)：GDC=(G2−G1)·ωa/(s+ωa)，
     > "which is a low-pass response hence has negative phase shift."（p.7）
     中文：τ 匹配把动态劣化压成一阶低通（无峰化无正相移），残余只剩直流失配 ∆G——单级内"τ 匹配消除全部动态效应"的原文依据。
   - 增益带宽积匹配（tG=tω=t）Eq.(22)：
     > "which is an overdamped second-order low-pass response hence shows negative phase shift and no gain peaking."（p.8）
     中文：G1ω1=G2ω2（GBW 匹配）也压平，给出第二种配对不变量雏形（乘积不变量），但 Hornero 未把它叫"不变量"也未推广到多级。
6. **反向容差（ω1>ωa>ω2）产生右半平面零点、最多 270° 相移**（p.7–8）：
   > "Now, whenever tG < tω, GDC(s) will be negative and have a positive zero in the complex plane, which added to the two negative poles in the denominator amount to a maximum 270° phase shift."（p.8）
   中文：增益高的支路转角反而低 → 分子零点变正实部，相位劣化最烈——容差的**符号组合**决定性态（Table I 三分法的依据）。
7. **CMRR 不是传递函数，级联 CMRR 公式在通带内失效（级联警示=定性）**（p.14）：
   > "As a result, CMRR calculations for cascaded differential stages that assume that this parameter is a real number within the frequency band of the differential signal being amplified [11] [12] cannot be directly applied inside all the differential amplifier passband."（p.14）
   中文：对级联（引 Pallàs-Areny 1991 cascaded TIMS 40:677 与 Koide 1997）只给出"不能直接套用"的定性警告；**没有多级 GDC 闭式、没有配对不变量条件**。
8. **结论=明确"应避免该拓扑"（避免依赖无源匹配的分离信号链）**（p.15）：
   > "high-performance differential signal conditioners should not involve separate signal chains for each of the two signals to be processed and eventually subtracted, like the circuit in Fig. 1."（p.15）
   > "Multi-channel systems, in particular, wherein component tuning is unfeasible, should avoid circuit topologies that make the common-mode response to depend on passive component matching."（p.15）
   > "designing a corner frequency much higher than the signal bandwidth could alleviate the problem but at the cost of increased noise bandwidth."（p.15）
   中文：处方是拓扑规避（不要用减法双链）或抬高转角换噪声带宽——**没有给出"如何在减法拓扑内达到可达最佳"的边界**，这正是 P3/可达边界增量的空档。

## 关键数值（原文）

- INA121P 实测共模增益（p.10）：Gc = 1.4×10⁻⁴ @1 Hz（CMRR≈92 dB）→ 5.4×10⁻³ @10 kHz（≈60 dB）；相位 90°(<3 kHz)→85°@10 kHz→0°@320 kHz；1 V 共模输入时贡献 150 µV(<100 Hz)–5.4 mV @10 kHz。
- 实验四案例（Table II/III，p.19–20）：Case 2（tω/tG=2.50）实测 GDC(max)/GDC(0)=1.75（4.87 dB）对理论 1.82（5.23 dB），fmax≈100 Hz 对理论 96 Hz；Case 1（tω/tG=0.055）为低通无峰化；Case 3/4（tω/tG≈62）GDC(0)=−50 dB 但 fzc≈1.5 Hz、fmax=90 Hz、峰值抬升 ≈25–30 dB。
- **Table IV（外推，全部 tG=0.01%）**（p.20）：
  - Case A：Ga=10, tω=10% → fzc=0.99 Hz, GDC(0)=−54 dB, GDC(max)=0 dB, φDC(max)=85°@21 Hz, CMRR 74 dB(dc)→**17 dB @1 kHz**，φCMRR(max)=−86°@30 Hz；
  - Case B：Ga=100, tω=10% → GDC(0)=−34 dB, GDC(max)=**20 dB**（共模增益超过 1！）；
  - Case C：tω=1% → CMRR 37 dB @1 kHz, φDC(max)=74°@76 Hz；
  - Case D：tω=0.1% → CMRR **56 dB @1 kHz**，φDC(max)=43°@191 Hz。
  原文判词（p.12–13）："yields a zero in GDC near 1 Hz that makes it to increase from -54 dB to 0 dB at 21 Hz … CMRR decreases from 74 dB at dc to 17 dB at 1 kHz"；"Therefore, CMRR can be considered a real number only well below 1 Hz!"
- 峰化判据数值链（p.6, p.9）：tω > 0.4·tG 带通+峰化；tω < 0.4·tG 低通；ωmax ≈ (ω1ω2)^1/2（几何平均，Eq.11 小 ωzc 近似）。
- GCD = GDC/4（全差分、分离支路，p.14 引 [4]）。

## 对 P1/P2/P3 的对照

- **P1（失配消去条件）**：相关性**最高（正面对手）**。Hornero 的 GDC=G2−G1 就是 P1 方程的**单级一阶版本**，且 Eq.(17)/(18)/(22) 已给出单级消去/压平的三种配对方式（tG=0、tω=0、GBW 匹配）——**已覆盖**：单级失配解析、带通化/峰化/正相移机理、tω>0.4tG 判据、270° 相移、GDD 与 CMRR 闭式（Eq.23–26）、INA121 实测校核、外推 Table IV。**未覆盖（P1 增量所在）**：①多级梯形（R1·C2 交叉项）——全文只有单级一阶模型，级联只有 p.14 一句定性警告；②"τ 匹配充要性"的定理化表述（Hornero 只枚举特例，未给"何值使 GDC≡0 全频段恒等"的充要命题）；③任何**恒等消去**（GDC≡0）讨论——注意 Hornero 框架里 GDC≡0 要求 tG=0 且 tω=0 同时成立，即"增益比与 τ 双匹配"，这与 P1 单级充要条件可互推，但 Hornero 未以"消去条件"立论；④Kelvin 地板、可达边界、门槛化流程全部没有。
- **P2（Kelvin 结构地板 ≈56 dB）**：无。全文无 Kelvin 四线结构讨论；Table IV Case D 的"56 dB @1 kHz"只是 0.01%/0.1% 容差外推数字，与 P2 的结构性地板不同源，引用时**不得**混同（但可作"容差路线 56 dB"的对照组旁证）。
- **P3（平坦度约束衰减上界）**：弱相关。p.15 "designing a corner frequency much higher than the signal bandwidth could alleviate the problem but at the cost of increased noise bandwidth" 是"用带宽换平坦"的权衡原声，可作 P3 的动机引文；但无衰减上界/平坦度定量约束。
- **方法学（D1–D10 门槛化）**：无。全文是解析建模+四案例实测，无门槛化/增量登记流程。
- **killRisk 判断**：**不构成 kill，但严格限定 P1 表述边界**——P1 必须把自己写成"多级配对不变量 + Kelvin 地板 + 可达边界 + 门槛化"的**组合增量**：单级一阶失配解析部分 Hornero 已发表，P1 若只写单级即被本文覆盖；P1 的差异化必须落在（a）多级梯形 G_DC 中 R1·C2 交叉项使"τ 匹配"不再充分、（b) Kelvin 结构地板、（c）可达边界定理、（d）D1–D10 方法论四点上，且引用本文时须把 Eq.(17)/(18)/(22) 作为单级基线明确致谢。

## 没读到的
- 多级/梯形 RC 网络的 GDC 解析（全文唯一多级痕迹是 p.14 引 [7] Gasulla 2000 "lengthy transient responses due to GDC … for some fully differential filters" 与 [11] 级联 CMRR 失效警告，均定性）；
- Kelvin 四线/引线电阻效应；任何"结构地板"概念；
- 主动共模控制（无 CMFB 内容——见 duque1993）；
- 数字侧/ΣΔ 内容；传感器材料内容；
- Fig.2 电路为 TL072 双运放 + INA121 减法的低通（R1/R2/C 每路一阶），即**实验对象本身也只有一阶**。
