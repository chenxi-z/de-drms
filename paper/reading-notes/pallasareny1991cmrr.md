# 精读笔记 · Pallàs-Areny & Webster 1991《Common Mode Rejection Ratio in Differential Amplifiers》（IEEE TIM 40(4):669–676）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> 页码用期刊页（669–676）；PDF 页 1–8 与之差 668。**差分测量主线起点**：四增益矩阵（GDD/GCC/GcD/GDC）与"减法结构共模增益"概念在此定型。

## 出处
- Pallàs-Areny, R., Webster, J.G., "Common Mode Rejection Ratio in Differential Amplifiers", IEEE Trans. Instrum. Meas., vol. 40, no. 4, pp. 669–676, Aug. 1991. doi:10.1109/19.85332.
- 本地：`H2-差分CMRR/pallasareny1991cmrr.pdf`（8 页）。bib key：`pallasareny1991cmrr`（literature.bib L669）。
- 同期姊妹篇：`pallasareny1991cascaded`（TIM 40:677–681，级联级 CMRR，本批未含原文）。

## 核心命题（原文）

1. **单运放 DA 的 CMRR = 电阻失配与运放 CMRR 的倒数和，容差 t 造成硬地板 (k+1)/4t**（p.670，PDF p.2）：
   > "1/CMRRD = 1/CMRRR + 1/CMRROA  (8) … For example, 0.1 % resistors can result on a CMRRR of only 54 dB when k = 1 and 69 dB when k = 10."（p.670）
   > "CMRRR = [k(1−t²)+1+t²]/(4t)  (10) … This means that when relying on high-precision resistors to obtain a high CMRR, we must consider not only t but also the actual value for k."（p.670）
   中文：容差路线的 CMRR 有闭式最坏值地板——P2"结构地板"数值论证的最直接历史基线（54 dB@k=1, 0.1%）。
2. **两级差分系统四增益矩阵定义（GDC 概念的出生地）**（p.671，PDF p.3）：
   > "The first stage has a differential output, and is best described by four transfer functions: GDD, GCC, GcD, and GDC [6]. … GDC is the common mode to differential gain, that is, the output differential signal due to the input common mode signal. Therefore, we have VD = GDDVd + GDCVc (15a), VC = GCDVd + GCCVc (15b)."
   中文：P1 的 G_DC(s) 术语与定义直接承自此式；两式合成 uo = ud(GdGDD+GcGcD) + uc(GdGDC+GcGcc) (16)。
3. **非耦合缓冲级的 GDC = H₂(s)−H₁(s)：P1 减法方程的直系原型**（p.671–672，PDF p.3–4）：
   > "GDC = [H2(s) − H1(s)]…  (24c) … Gcc = |H1(s) + H2(s)|/2.  (24d)"
   > "For unity gain buffers the condition H2(s) = H1(s) depends only on the op amps, and, therefore, is feasible. For buffers with gain it depends on passive components, whose tolerances make it very difficult to achieve this condition, unless trimpots are added."（p.672）
   中文：**精确消去条件 H1(s)≡H2(s)** 在此首次成文——全频段恒等要求两条传递函数全等；有增益的缓冲要靠无源件，容差使恒等"very difficult"。P1 的"G_DC=H_N−H_P≡0"即此条件的 RC 滤波器版本。
4. **符号相消可实现无穷 CMRR（直流），但只在 ωc 以下有效**（p.670，PDF p.2）：
   > "if we can achieve CMRRR = −CMRROA, then we have an infinite CMRRD."（p.670）
   > "A method to overcome the need for low-tolerance resistors is by using a potentiometer to trim the value for one of them, usually R6."（p.670）
   中文：调零/符号对消是"消去条件"思想的第二形态（两误差源对消）；但受 CMRROA 单极点滚降限制，ω>ωc 后失效——**频率依赖的可达边界**思想的原型（见 §IV "will not allow us to improve CMRRT at frequencies higher than ωc, as given by (35)"，p.674）。
5. **输入级对管必须匹配的是 Ad、Ac 绝对值而非比值**（p.673，PDF p.5）：
   > "This shows that in order to achieve a high value for CMRRF, input op amps must be matched not only for their CMRR [1], but also for both differential and common mode gains. In other words, it is not the ratio Ad/Ac what should be matched, but the absolute values for Ad and Ac."（p.673）
   > "Equation (33) shows that both the open-loop differential gain and the CMRR must be matched for the input op amps. The first of these conditions is difficult to meet because … Ad usually starts to decrease at frequencies well below the CMRR corner frequency."（p.673–674）
   中文：增益带宽积失配是 20 dB/dec 劣化的根（Eq.34–35，p.674）——与 Hornero 2021 的 tG/tω 框架同源（Hornero 正是本文作者的后续）。
6. **结论：耦合缓冲 + 前级集中增益是最优拓扑，但高频仍受第二级限制**（p.676，PDF p.8）：
   > "The best approach for obtaining a high-CMRR broadband instrumentation amplifier is to use two well-matched op amps as coupled input buffers, and design this stage with a high differential gain … No matter how well matched the input op-amp pair is, at high frequencies the CMRR will decrease because of the limited CMRR for the differential (second) stage. Values higher than 80 dB for a differential gain of 1 at 25 kHz are feasible although difficult to measure."（p.676）
   中文：给出可达上界量级（80 dB@25 kHz，难测）——P2/可达边界引用的实证锚点。

## 关键数值（原文）

- CMRRR 最坏值闭式：(k+1)/4t；0.1% 电阻 → 54 dB (k=1) / 69 dB (k=10)（p.670, p.676 结论重述 "less than (k + 1)/4t"）。
- 实测 Table I（0.1% 电阻，Fig.1 电路，p.675）：LM741C Gd=1 时 Gc≈−61.6 dB@1 Hz（0°）→−60.1 dB@25 kHz（57°）；调电位器后 <−100 dB@1–10 Hz（180°相位），92°@10 kHz——实测验证"调零只在 ωc≈1 kHz 以下有效 + 90° 固定相移"（p.674, p.675）。
- 实测 Table II（p.675）：非耦合缓冲 G=2 → −53.4 dB@1 Hz（比耦合差 46 dB：原文 "noncoupled buffers resulted in a 46 dB increase in low-frequency common mode gain (from −100 dB to about −54 dB)"，p.675）；耦合缓冲 LM1458 G=2 → −91.2 dB@1 Hz → −63.0 dB@25 kHz；G=21 → −90.0 dB@1 Hz（−130° 相移@25 kHz）。
- 换电阻位置可测到 −38.1 dB@1 Hz（"By interchanging two resistors in the input stage, we obtained a common mode gain of −38.1 dB at 1 Hz and −30.3 dB at 25 kHz. This underlines the importance of input stage matching"，p.675）。
- G=10（k=10）实测 82 dB（"From (10), the minimal CMRRR is now 69 dB; we obtained about 82 dB (19.6 dB + 62.6 dB)"，p.674）。
- 测量手段：HP 3582A 频谱分析仪，0.1 Hz–25 kHz；低频端只能给 CMRR 下限（p.674）。

## 对 P1/P2/P3 的对照

- **P1（失配消去条件）**：相关性**高（概念直系源头）**。GDC 术语（Eq.15a）、GDC=[H2−H1] 结构（Eq.24c）、"H2(s)=H1(s) 才是无共模转换"的恒等条件、"CMRRR=−CMRROA 对消"均在本文；但**对象是运放缓冲/仪表放大器，不是 RC 滤波器**——无 τ=R·C 匹配充要性讨论，无多级梯形，无 R1·C2 交叉项。P1 引用时应把本文定位为"G_DC=H₂−H₁ 减法结构与四增益矩阵的定义出处"，增量划界清晰（Hornero 2021 是单级解析、P1 是多级消去定理）。
- **P2（Kelvin 结构地板 ≈56 dB）**：相关性**中**。本文无 Kelvin 四线结构；但 (k+1)/4t 容差地板（54 dB@0.1%, k=1）与"调零只到 ωc、高频被 CMRROA 压死"的两段式边界，是 P2"结构地板"数值论证最重要的历史对照组——P2 的 56 dB 若与 54 dB 同量级，需在论文里显式说明与本文 0.1% 地板的区别（结构性地板 vs 容差最坏值）。
- **P3（平坦度约束衰减上界）**：无。全文无滤波器/平坦度内容。
- **方法学（D1–D10 门槛化）**：无。但"相位测量暴露 CMRR 符号"（"the phase for Gc gives the explanation: it happened that CMRROA had an opposite sign to CMRRR…"，p.674）提示门槛化方法学中应包含相位核查项——可作 D 项的动机引文。
- **killRisk 判断**：非 killRisk（killRisk 仅 Hornero 2021）；但作为主线起点，P1 的术语与方程必须回溯引用本文，避免"重复发明 GDC"的审稿风险。

## 没读到的
- 级联两级以上的 CMRR 闭式（在姊妹篇 pallasareny1991cascaded，TIM 40:677–681，本批无原文——Hornero 2021 p.14 指出其"假设 CMRR 为实数"在通带内失效）；
- RC 滤波器/τ 匹配内容（对象是运放电路）；
- Kelvin 四线/引线电阻；
- 数字域内容；ΣΔ；
- Fig.2(a) 耦合缓冲的完整 Eq.(28) 四个传递函数在 PDF 中公式区渲染缺失（(28a–d) 仅存文字描述，具体闭式"待核"——若 P1 引用需回对纸质版或 IEEE Xplore 版）。
