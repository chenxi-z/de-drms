# 精读笔记 · Brinson 1995《New approaches to measurement of operational amplifier common-mode rejection ratio in the frequency domain》（IEE Proc.-Circuits Devices Syst.）

> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> 页码口径：所引页码为**期刊印刷页码**（PDF 第 1–7 页 = 印刷 p.247–253，已按页脚逐页核对）。
> 文件：`fulltext/H2-差分CMRR/brinson1995meas.pdf`；bib key `brinson1995meas`。扫描版 OCR：µ→p（μA741 误作 pA741）、下标/公式多处损，引文中已按上下文复原并在标 [OCR损] 处注明。

## 出处
- M.E. Brinson and D.J. Faulkner, "New approaches to measurement of operational amplifier common-mode rejection ratio in the frequency domain," *IEE Proceedings - Circuits, Devices and Systems*, vol. 142, no. 4, pp. 247–253, Aug. 1995. DOI 10.1049/ip-cds:19952031. 作者单位 School of Electronic and Communications Engineering and Applied Physics, University of North London；1995-01-26 收稿、1995-05-01 修回。
- 主题：四种运放 CMRR **频域**测试电路（匹配电阻差放 / 电源伺服 / 差值放大 / 求和放大）的误差分析与 μA741 实测；重点是电阻失配、输入电容失配与测量电路自身 CMRR 对 f_CMZ（共模增益零点频率）测量的限制。

## 核心命题（原文）
1. **总命题：四种 CMRR 频域测试电路 + 两新电路，可测高性能运放（p.247, Abstract）**：
   > "Four test circuits for measuring operational amplifier common-mode rejection ratio (CMRR) are described and analysed. Sample results are presented for the μA741 [OCR损：原作 pA741], characterising the variation of CMRR with frequency. Two new test circuits and a variation on an existing technique offer significant improvements over previous methods and are capable of accurate measurements on high-performance operational amplifiers."
   （解释：论文贡献在**测量方法学**，非消去理论。）
2. **CMRR 频变的机理 = 尾电流源输出电容在共模增益里引入零点（p.247, §1）**：
   > "Its frequency dependence can be accounted for principally by a zero introduced into the common-mode gain by the output capacitance of the current source in the tail of the input differential pair [1, 2]."
   （解释：共模增益 = 同极点 + 单零点 A_CM(f) = A_CM(0)(1+jf/f_CMZ)/(1+jf/f_pD)（p.251 Appendix 式），f_CMZ 由尾电流源寄生电容决定——**器件内部差分对的复数差零点**，与 Koide 1997 谱系同一物理层；但它属有源器件内机理，非外部无源网络失配。）
3. **测量有效性判据：激励必须是真共模，微小差模分量即致大误差（p.247, §1）**：
   > "Test circuits must ensure that the parameter that is measured is dependent on a true common-mode signal, since large errors can be introduced by even a small differential-mode component, and should allow the frequency of the common-mode zero to be extracted."（标点按行合并复原 [OCR损：句号系换行伪迹]）
   （解释：门槛化方法学先声——测 CMRR 先要保证"测到的是共模"，等 P1 论文做 G_DC 实测验证时的第一条设计判据。）
4. **经典差放的测量瓶颈 = 电阻对匹配，失配同时决定直流通项与零点频率（p.247, §2.1）**：
   > "Fig. 1a is a classic differential amplifier configuration using closely matched resistors (R₁ = R₃ and R₂ = R₄) [OCR损：下标佚失，按 Table 1 复原]. The principal measurement problem with this circuit is the need for very close matching of the resistor pairs [1, 4, 6]. Table 1 shows that both V_OUT(0)/V_IN and f_z are dependent on the degree of resistor mismatch."
   > （p.248）"The resistors in the test circuit were 0.1%, tolerance high stability components with R₁ = R₃ = 10 Ω, R₂ = R₄ = 100 kΩ ..., so the resulting error is small for CMRR(0) below 120 dB."
   （解释：**失配 → CMRR 地板**的直接定量表述：0.1% 电阻在该增益配置下把测量电路地板压在 120 dB。与 P2"Kelvin 结构地板"同型——地板由无源失配决定、与待测器件无关。）
5. **互换电阻对取平均 = 一阶消去电阻失配误差的校准手法（pp.247–248, §2.1）**：
   > "To provide a further correction for resistor mismatch errors a simple but effective measurement technique has been developed: two sets of common-mode voltage transfer function measurements are made where resistor pairs R₁, R₂ and R₃, R₄ are interchanged and the resulting data are averaged at each measurement frequency. The analysis shows that, to a good first approximation, the error terms cancel."
   > （p.252, §6.1.1）"The effect of resistor tolerance may be taken into account by setting R₂ = R₁(1+ε₁) and R₄ = R₃(1+ε₂) where ε₁, ε₂ ≪ 1. ... Neglecting second-order small quantities, the average of the two transfer functions is [式 OCR损]"
   （解释：交换-平均把 ε 的一次项消掉、只剩二阶小量——**"结构性操作消去一阶失配"的测量版**；P1 若谈单级 τ 匹配充要性，此处是测量域的平行证据，但对象是两只电阻、非多级网络传递函数。）
6. **输入电容失配 + 源阻抗也抬 f_z 误差地板（p.248, §2.1）**：
   > "The magnitude of the source resistance and mismatches in input capacitance also affect f_z. To minimise these effects, the source resistance should be low. Assuming a source resistance of 10 Ω and C_P − C_N = 1 pF, the error for a device such as the μA741 will not be significant unless CMRR(0) exceeds 120 dB."
   （解释：容性失配地板与阻性失配地板同量级（均 ≈120 dB）——地板是**多机制叠加**的，P2 写"结构地板"时值得并列引用。）
7. **测量电路自身 CMRR（K）的频变是伺服法的极限（p.249, §2.2）**：
   > "The effect on f_z becomes significant if K < CMRR(0). This situation may arise if K is not constant, as assumed in the Appendix, but reduces with frequency: behaviour typical of conventional instrumentation amplifiers above 100 Hz. The device used in the test circuit has a typical K of 100 dB, maintained over a bandwidth of 100 kHz [12]."
   （解释：仪放 K 随频率滚落 → 高频测量被测量仪器自身地板封顶；任何 G_DC/CMRR 实测方案都要核这一条。）
8. **共模增益非线性：不同测试电平给出不同 CMRR(0)（p.250, §4）**：
   > "The analyses treat common-mode gain as linear, but in real devices it can be notably nonlinear [7]. The differences between results using V_IN = 1 V and V_IN = 5 V in Table 2 probably reflect this observation. It is noticeable that manufacturers test CMRR using the full common-mode voltage range [3–7]."
   （解释：CM 通道非线性 → "CMRR"不是单一传递函数的标量，随工作点变——P1 用 LTI 框架谈 G_DC(s) 时的适用边界素材。）

## 关键数值（原文）
- 四电路交叉验证（p.249, Fig.3 + Table 2，样管 R4）：CMRR(0) ≈ **103 dB**、f_CMZ ≈ **900 Hz**（"all the data being consistent with CMRR(0) of about 103 dB and f_CMZ at about 900 Hz"）；分电路 (a)–(e)：5 V/5 V/1 V/1 V/5 V RMS → 103.8 / 103.1 / 102.3 / 101.7 / 103.4 dB，f_CMZ 920 / 1098 / 980 / 1041 / 873 Hz（**低测试电压使 CMRR(0) 偏低、f_CMZ 偏高**，归因共模非线性）。
- μA741 手册典型值（p.247, §1）：DC CMRR 90 dB，300 Hz 以上下降。
- 测试电路地板（p.248）：电阻 0.1%、R₁=R₃=10 Ω、R₂=R₄=100 kΩ → **CMRR(0) < 120 dB 时失配误差可忽略**；源阻 10 Ω、C_P−C_N=1 pF → 同样 120 dB 门槛。
- 伺服测量仪放 AD830：K typ 100 dB @ 100 kHz 带宽内维持（p.249）；AD830 最大差分输入 ±2 V → 差值放大电路共模测试电压限 ~1 V RMS（p.248）。
- 十只 μA741 跨厂商实测（p.250, Table 3，Fig.1d 电路）：CMRR(0) **93.2–118.0 dB**、f_CMZ **80–1095 Hz**、CMRR(0)×f_CMZ 50.1–156 MHz·Hz [列名 OCR损，量纲待核]、A_d(0) 106–133 dB、GBW 833–1076 kHz；趋势："there is a tendency for high CMRR(0) to be associated with a relatively low f_CMZ"。
- 方法极限（p.250）：求和放大电路原理上可分辨 **CMRR(0) ≥ 140 dB**；精心设计测试夹具下 100 dB 器件的 f_CMZ 可测至 **30 kHz 以上**。

## 对 P1/P2/P3 的对照
- **P1（消去条件）**：**低-中**。触及两点同型素材：① 电阻失配 → 差放 CMRR 地板的闭式（ε₁,ε₂ 进 V_OUT(0)/V_IN 与 f_z，Table 1/§6.1.1）；② 互换-平均消一阶失配（"the error terms cancel"）。但对象始终是**测量电路的两对电阻 + 单只有源运放**，无多级、无网络综合、无"全频段精确消去"命题化。不构成 killRisk，但 P1 实验章节（若做 G_DC 实测）应引其"真共模激励"判据。
- **P2（Kelvin 结构地板 ≈56 dB）**：**中**。给出"无源失配决定地板"的定量样例：0.1% 电阻 + 1 pF 容失配 → 测量域地板 ~120 dB（注意这是高增益比 α 下的测量电路，与 P2 信号链地板数量级不同，仅作**机制旁证**：地板由失配对决定、可被结构性操作（交换-平均）压低一阶）。
- **P3（平坦度约束衰减上界）**：**无**。全文无通带平坦度/衰减上界权衡；频域内容限于 f_CMZ 提取与曲线拟合。
- **方法学（增量四）**：**中-高**。四电路交叉验证、最小二乘 dB 域拟合、误差项逐项归因（失配/输入容差/K 频变/非线性）、以及"测试电平本身改变被测量"的发现——是 CMRR/G_DC 类参数**实测方法学门槛化**的直接范本。
- **killRisk 判断：无**。未触及"多级无源网络全频段精确消去条件"；最近处仅 §6.1.1 两电阻失配公式（且公式本身 [OCR损]）。

## 没读到的
- **全部公式（Table 1 与 Appendix §6.1.1–6.1.3 的传递函数闭式）OCR 严重受损**：V_OUT(0)/V_IN、f_z、f_p 的显式表达式不可靠，只引了文字结论；若需精确公式须看扫描图或找重印版。
- Fig.1 四电路与 Fig.2/3 曲线的图形细节（图不进 OCR）；Table 1 各列与行（电路 a–d）对应关系靠正文文字推断，未能逐格核对。
- Table 3 "CMRR(0) × f_CMZ" 列的单位（OCR 作 "MHr"/"Hr" 混排，量纲 MHz·Hz?）待核。
- 其引文 [10] Schoenfeld 1970（CMRR 两种定义等价性的原始讨论，IEEE Trans. BME-17）未读——P1 若用"输入失调电压定义 vs 增益比定义"的区别，应溯源到它而非本文。
