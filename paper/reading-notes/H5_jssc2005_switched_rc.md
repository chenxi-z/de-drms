# 精读笔记 · Ahn/Chang/Brown/Ozaki/Youra/Yamamura/Hamashita/Takasuka/Temes/Moon 2005《A 0.6-V 82-dB Delta-Sigma Audio ADC Using Switched-RC Integrators》（IEEE JSSC 40(12), pp.2398–2407, DOI 10.1109/JSSC.2005.856286）

> 格式标准（全组沿用）：出处 → 核心命题（原文引用）→ 关键数值（原文）→ 对 P1/P2/P3 的对照 → 没读到的。
> 读法：pdftotext 全文逐节读，引用一律原文加页码；不转述成模糊话。
> 注：PDF 文本层数学符号（R1、CS1、RON、φ1/φ2 等）丢失，本文引用的符号已逐页对照渲染图核回，页码用期刊印刷页（PDF 页 = 印刷页−2397）。

## 核心命题（原文）

**① switched-RC 采样如何避开浮动开关（"电荷注入"）——机理原文（p.2399，PDF p.2）**

1. 拓扑替换（根本机理：把注入电荷的浮动采样开关整个拿掉）："The basic concept is illustrated in Fig. 2. As shown, the input SC branch of the conventional structure is replaced by a switched-RC branch, in which the floating switch of the conventional integrator is replaced by a resistor R1. This modification results in two advantages. First, it obviates the need for the floating switch, and second, the linearity of the input sampling is improved."（p.2399）
2. 工作相位与分压式衰减："During the φ1 phase, the signal is sampled into the capacitor CS1 through resistor R1. During the following φ2 phase, the signal charge is transferred to the integrating capacitor CI1 by connecting the bottom plate of CS1 to ground through switch MS. During this phase, the voltage VX at node X is determined by the ratio of the ON resistance RON of the MS switch and the resistor R1"，式(1)：`VX(n+1/2) = RON/(R1+RON) · VIN(n+1/2)`（p.2399）
3. 非线性源唯一化 + 衰减机制（这是"避开"的定量核心）："In (3), RON is the only nonlinear term, and hence the sole source of nonlinearity. Its value is given in (4), which shows that RON is a function of VDS = VX"，式(4)：`RON = 1/(µn·COX·(W/L)·((VGS−VTH)−VDS))`（p.2399）；"Even though VX changes with the input signal, the signal variation at node X is attenuated by the ratio of R1 and RON [see (1)], and hence, the change in RON is small compared to that of a floating switch. Both the nonlinearity of the input sampling and the gain error can be reduced by making the linear resistor R1 much larger than the variable ON resistance of the reset switch MS."（p.2399）——**机理一句话：浮动开关的信号相关 RON 是采样非线性的来源；换成 R1 后，残余开关 MS 的 VDS 被 R1/RON 分压压到很小，RON 调制随之变小，且 R1≫RON 时增益误差与非线性同降**。增益误差式(3)：`Gain Error = (CS1/CI1)·(RON/(R1+RON))`（p.2399，积分电容为 CI1，放大图核回），高 OSR 下 "For sufficiently high oversampling ratio (OSR), VIN(n+(1/2)) will be very close to VIN(n), and the error can then be approximated by"（p.2399）。
4. 设计折中（R1 不能无限大）："However, there is a tradeoff. Larger R1 results in improved gain accuracy and lower distortion during the φ2 phase, but during the φ1 phase, a large R1CS1 time constant degrades the sampling accuracy. Thus, R1 should be small enough to satisfy the settling requirement during the sampling phase."（p.2399）
5. **"charge injection"一词在本文只出现在共模语境**（p.2401–2402）："Such use of two different input CM voltages resulted in a large amount of common-mode charge injection. Thus, the input or inter-stage branches of all integrators should also perform a level shifting operation, in addition to sampling and transfer/amplification of the input signal."（p.2401）旧方案代价："A level-shifting capacitor C_LS is used to cancel the common-mode charge injection, by providing an opposite polarity charge. However, this added SC branch adds more kT/C noise and also increases the opamp noise gain."（p.2402）本文方案（split branch，靠对称消共模注入）："In our implementation, a split input switched-RC branch is used to keep constant CM level of the integrator, as shown in Fig. 5(b). During the integrating phase, one half of the sampling capacitor is connected to VDD, while the other half is connected to VSS. This results in a constant input common-mode level of VDD/2 for the integrator during both phases, obviating the need for an additional level-shifting capacitor without any noise penalty."（p.2402）
6. 伪差分 + 开关电容共模反馈（低压下不做经典 CMFB）："A pseudo-differential architecture is used to circumvent challenging design issues associated with low-voltage common-mode feedback circuit design. Capacitors CM1s, connected to the switched-RC branches of the next stage, are used for the common-mode feedback."（p.2402）
7. 架构级失真压制（低失真前馈 + 非线性局部反馈）："under ideal conditions, the loop filter processes only the shaped quantization noise and so there is no distortion introduced by the integrator. Hence, the linearity requirements on the opamps are relaxed."（p.2400）；"The local feedback continuously monitors the integrator output and restricts the signal swing range by feeding back a quantized error signal to the input of the second integrator."（p.2400）

## 关键数值（原文）

- 整机：0.6 V 供电、1 mW、82-dB DR、81-dB peak SNDR（A 计权）、OSR=64、时钟 3.072 MHz、2.9 mm²（0.35-µm CMOS）（摘要 p.2398；p.2405）
- 实测频谱：1 kHz、0.57-Vpp 差分输入下 "79-dB SNDR and 103-dB SFDR is achieved over the audio band"（p.2405）；SNDR 曲线 "linear operation, up to a 1-dBFS input level"（p.2405）；供电 0.6→1.8 V "The performance is unaffected"（p.2405）
- 采样支路实装值："To insure less than 85-dB kT/C noise level, a total of 4.8-pF input sampling capacitance is used and 8-kΩ R1 is used to guarantee linear input signal sampling."（p.2402）
- 运放："more than 60-dB SFDR with full-scale output swing (0.8-Vpp fully differential) under 0.6-V supply voltage"（p.2404）
- 行为仿真（失配相关）："Behavioral simulations performed by modeling amplifiers with 50-dB DC gain, 50-dB SFDR, and 0.4% capacitor matching indicate higher than 100-dB SFDR of the complete converter. More than 1.5-dB improvement in the permissible peak input signal due to local feedback is also observed."（p.2400–2401）
- 时序代价：SRC 级间相位错开半拍，"there is a delay between the input and the output of the integrator, where [T/2] is the clock period"（p.2399）；级联需补 z^-1/2 同步（p.2400）

## 对 P1/P2/P3 的对照

- **P1（失配消去条件）——P1 反例检索结论：全文无"无源 RC 差分网络失配→共模消去条件"**。最接近的三处均不是该命题：
  ① split branch 的共模恒定靠"一半接 VDD、一半接 VSS"的对称假设（p.2402 原文如上），**两半失配会怎样论文没有给条件**；
  ② 系数失配是另一个域："Inaccurate matching of gain coefficients of the modulator due to non-ideal parameters also causes residual input signal component in the loop filter. These signal terms propagating through the integrator path will cause distortion and limit the linearity of the system."（p.2400）——这是 ΔΣ 增益系数失配致环内残余信号，非 RC 差分网络的共模→差分转换；
  ③ 0.4% 电容匹配只是行为仿真的输入参数（p.2400），文中未从它推出任何 CMRR/共模消去式。
  → 价值是**阴性记录 + 机理借喻**：它的"误差不靠校准、靠结构把非线性衰减掉"（RON 被 R1/RON 分压衰减）与 P1"失配致 G_DC≠0"是同一族"结构决定残余"的论证型。
- **P2（Kelvin 地板）**：无直接内容（片上 SC/ΔΣ 架构，不涉两线/四线传感结构）。型比可用：式(1) 的分压衰减是"地板由结构比值决定"的又一实例（与 P2 同型不同域，慎引）。
- **P3（AAF 衰减上界）**：无（本文采样为 SC 采样保持，未讨论片外抗混叠滤波器的衰减指标）。
- **引文价值**：①"floating switch is replaced by a resistor R1 … obviates the need for the floating switch"（p.2399）可作"开关非线性由结构移除而非由校准补偿"的出处；②式(1)(3)(4) 的 RON 分压衰减链是讲"残余开关也被压住"的标准引文；③p.2401–2402 的 common-mode charge injection → split branch 段落是"共模电荷注入靠对称支路消"的出处（但注意其对称无失配条件——正好是 P1 的靶子）。

## 没读到的

- **MS 开关本身的沟道电荷注入（Qch）未做定量**：论文把非线性唯一归于 RON(VDS) 调制（"RON is the only nonlinear term, and hence the sole source of nonlinearity", p.2399），φ2 处 MS 关断的电荷注入对 CS1/CI1 的影响未单列分析；"避开电荷注入"的严格表述应是"移除浮动采样开关 + 分压衰减残余开关的 RON 非线性"，共模电荷注入另由 split branch 对称消。
- Table I（运放仿真参数）与 Table II（性能汇总）是图形表格，文本层取不到数值；正文已给 60-dB SFDR / 85-dB kT/C 等关键项。
- [5]–[12] 的 switched-opamp / ORST 细节、[14] Silva 低失真前馈拓扑、[15] Fujimori 1.5-bit 局部反馈原文均未读（在参考清单）。
- 芯片版图/键合（Fig.11 die photo）无数据；ΔΣ 数字噪声对消在片外 MATLAB 完成（p.2400），对消逻辑细节只给了框图 Fig.4(b)。
