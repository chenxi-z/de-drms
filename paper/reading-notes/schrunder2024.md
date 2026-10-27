# 精读笔记 · Fernandez Schrunder 2024《A Bioimpedance Spectroscopy Interface for EIM Based on IF-Sampling and Pseudo 2-Path SC Bandpass ΔΣ ADC》（IEEE TBioCAS 18:1001–1013）

> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> 读法：pdftotext 逐页；PDF 是 author's version（页眉占位 "VOL. 14, NO. 8, NOVEMBER 2023" 有误，正式版 = TBioCAS vol.18, 2024, pp.1001–1013）；页码 = PDF p.1–13。
> 定位：**H5 轴头（2024 最新）**——开关电容 BP ΔΣ 输入的驱动/建立完整工程链：SC 负载 10 pF → TIA 输出级供电建立 → 采样伪影用 charge bucket filter 压。⚠️ 任务简报称其为「2024 大综述」，**实为 KTH 的芯片实现论文**（180 nm 流片 + 人体实测），非综述——引用时按芯片论文对待。

## 出处

- Alejandro D. Fernandez Schrunder, Yu-Kai Huang, Saul Rodriguez, Ana Rusu（KTH 皇家理工学院）, "A Bioimpedance Spectroscopy Interface for EIM Based on IF-Sampling and Pseudo 2-Path SC Bandpass ΔΣ ADC," *IEEE Trans. Biomedical Circuits and Systems*, vol. 18, 2024, pp. 1001–1013. DOI: 10.1109/TBCAS.2024.3370399（CC-BY author's version）。
- 本地全文：`fulltext/H5-kickback/schrunder2024.pdf`（13 页）。

## 核心命题（原文）

1. **输入结构总链（H5 核心语境）**（p.3–4）："The interface consists of two subsystems: i) a sinusoidal signal generator (SSG)… ii) a quadrature IF-sampling readout, comprised by the I and Q channels, which contain a double-balanced passive mixer, a current-balancing IA, and a pseudo 2-path BP ΔΣ modulator."（p.2 末）输入端为**片外无源 HPF（500 Hz 交流耦合）→ 无源混频器 → 电流平衡 IA → 电荷桶滤波器（charge bucket filter）→ 开关电容 BP ΔΣ**（Fig.3, p.3）——ADC 输入是**开关电容型**，需要驱动与建立设计。
2. **驱动/建立约束的完整表述（本文对 D9/H5 域最有价值的一段）**（p.6–7）："The TIA output stage, driving the sampling capacitor at the input of the ADC (10 pF, as detailed in section III.C) and CTIA, should supply enough current to settle the signal within a sampling period, Ts of 16 µs. An output biasing current, Ibias,out of 10 µA, was chosen to achieve a slew rate of 0.3 V/µs, sufficient to drive a full-scale sinusoid within Ts. Additionally, to reduce the amplitude of sampling artifacts, charge bucket filters are used at the output of the TIA."（**TIA 输出级驱动 10 pF 采样电容，须在一个采样周期 Ts=16 µs 内建立；设计给出了偏流 10 µA → 压摆率 0.3 V/µs 的换算；采样伪影（sampling artifacts，即 SC 输入踢回的时域表现）用「电荷桶滤波器」压幅**——这是「外置网络 vs 片内驱动」分工的一个完整实例）
3. **AAF 由 TIA 反馈电容兼任（一阶）**（p.6）："Additionally, CTIA adds a low frequency pole, which acts as a first-order anti-aliasing filter, with a low-pass corner fc = 1/(2πRTIA CTIA) ≈ 31.25 kHz."（RTIA=210 kΩ、CTIA=24 pF；AAF 不再是独立级——"no additional active circuitry is required after the IA, since the TIA stage acts as an anti-aliasing filter and buffer before the ADC", p.6）
4. **采样电容取值的权衡**（p.8）："The sampling capacitor in the first resonator, 22Cs1 ≈ 10 pF, was chosen as a trade-off between kT/C noise, area and power consumption. Since the impact of kT/C noise of the following stages is suppressed by the loop, the sampling capacitors in the second and third resonators were reduced by a factor of 2 and 3, respectively to save area and power. Although these capacitors could theoretically be reduced further, the gain-compensation capacitor (Ch = 1 pF) sets the lower boundary, as it needs to be around x10 smaller than the sampling capacitor, and x10 larger than the parasitic capacitance of the OTAs input pair."（首谐振器采样电容 10 pF = kT/C/面积/功耗折中；后级被环路噪声整形压掉可缩小；下界由增益补偿电容 Ch 的 10 倍上下关系锁定）
5. **电荷注入的对策组合（非定量）**（p.8）："To reduce charge injection into the resonators, delayed versions of the non-overlapping clocks (ϕ1,d and ϕ2,d) are used. Switches are implemented with CMOS transmission gates to improve linearity. Additionally, dummy switches are added to reduce charge injection."（延迟不交叠时钟 + 传输门 + 虚拟开关——**三项全是标准定性对策，全文无 kickback 幅度/建立误差的定量数**）
6. **四电极 EIM = Kelvin 结构的应用域平行（P2 域）**（p.1）："EIM measures the impedance of muscle using four surface electrodes, as shown in Fig. 1. The outer electrodes deliver a low-amplitude sinusoidal current… while the inner electrodes capture the voltage response (Vin) from tissues"；"Assuming that the readout used for this measurement has a large enough input impedance, no current flows into the inner electrodes, so the captured Vin can be simply expressed as: Vin = ZEIM × |Ipk|e^{jωSG t}"（外对注流、内对取压、高输入阻抗下无流入电流——**Kelvin 四线的教科书式实现，但无「两线 vs 四线地板」的分析**）
7. **混频镜像/谐波折叠的系统级预算（噪声域，非 RC AAF 域）**（p.4）："These harmonics have decaying amplitude by a factor 1/(k1k2)^2… the down-converted harmonic to IF will have an amplitude of 107.96 dBc, thus it will introduce an error of 0.0004%"（XNOR 时钟混频的谐波折叠按 1/(k1k2)² 衰减逐项折算到误差——**这是一套「折叠项→误差%」的解析预算方法**，可作 P3 论述风格的型比）

## 关键数值（原文）

- 应用需求（p.1）：EIM 频段 1 kHz–2 MHz；基线 bio-Z "ranging from 1 Ω up to 10 kΩ"；波动 "10 mΩ to 1 Ω"；要求 "low noise (Zn,rms < 10 mΩrms) and large signal-to-noise ratio (SNR > 100 dB)"、"bio-Z errors below 1%"
- 最小信号与噪声预算（p.5）："the minimum required time-varying bio-Z signal is Zbio-Z,min × Ipk = 10mΩ × 150µA = 1.5 µV (−116.47 dBV), the integrated noise was set to 316 nVrms over a 61 Hz bandwidth (−130 dBV), to ensure a ~14 dBV margin"（**10 mΩ × 150 µA = 1.5 µV 是 H5/H2 域罕见的最小可测信号显式换算**）
- ADC（p.5, p.7–8）：fs = 4·fIF = 62.5 kHz（Ts=16 µs）；OSR=256，噪声止带 2fBW=122 Hz；6 阶 BP 单比特前馈；增益补偿伪 2 路 SC 谐振器；Cs1=444.4 fF（22Cs1≈10 pF）、Cs2=222.2 fF、Cs3=158.7 fF、Ch=1 pF
- IA（p.6）：Gm 核 FVF+CG；RDEG=15 kΩ（下界由饱和条件 Vin,max=2·Ibias·RDEG 决定，Vin,max=1 kΩ×150 µA=150 mV）；噪声 43.62 nV/√Hz → 340.68 nVrms @61 Hz；RTIA=210 kΩ、CTIA=24 pF、AAF 角 31.25 kHz
- TIA 输出级（p.6–7）：Ibias,out=10 µA → SR 0.3 V/µs，驱动 10 pF 采样电容 + CTIA 在 Ts=16 µs 内建立
- 整机（p.8）：180 nm CMOS、1.8 V（数字 IO 3.3 V）、5.4 mm²；读出功耗 339.8 µW（TCA 2×45.5 + TIA 2×36.9 + ΔΣ 2×87.5 µW）、SSG 4.5–139.5 µW；总 344.3–479.3 µW（摘要）
- 实测（摘要 p.1、p.9–10）：0.7 mΩ/√Hz 灵敏度 @15.625 kHz；SNRmax 105.8 dB @4 Hz BW（线性区从 68.1 dB 升至 105.8 dB，>2.2 kΩ 饱和于 100–105 dB）；FoM 146.5 dB；**线性质检**："achieves errors below 3% as compared to the reference [LCR] readings, from 10 Ω to 4.7 kΩ. The higher errors (>1%), under 400 Ω, might be due to larger contact resistance relative to the measured resistor."（p.10）
- 激励（p.3, p.5）：64 抽头正弦、6-bit IDAC + DEM，SFDR 36 dBc、SNR 55.94 dB；Ipk 编程 1–150 µA（16 档 0–23.52 dB）

## 对 P1/P2/P3 的对照

- **P1（失配消去条件，G_DC≡0）——相关性：无直接**。全文无差分 RC 网络失配→共模转换内容；伪 2 路 SC 谐振器的卖点恰是"the Q-factor and resonant frequency are independent of component mismatch"（p.5）——**失配不敏感性在谐振器域由结构（电荷转移而非 LC 调谐）获得**，是「结构免疫失配」论证的又一域外实例。killRisk：无。
- **P2（Kelvin 结构地板 ≈56 dB）——相关性：中（应用域平行，无地板分析）**。EIM 是四电极 Kelvin 测量的活例（p.1 原文见上）：外注流内取压 + 高输入阻抗假设；且给出「10 mΩ 变化 vs 10 kΩ 基线」的 10⁻⁶ 相对检测需求与 105.8 dB SNR 实测。但论文**未讨论两线法的误差地板**，也无「结构决定地板 dB 数」的推导——P2 主张不被触碰。引用价值：四线结构在生物阻抗域是标配（可作 P2 的域外必要性佐证），且 "large enough input impedance, no current flows into the inner electrodes" 是引线电流≈0 假设的标准表述。killRisk：无。
- **P3（平坦度约束衰减上界）——相关性：低**。AAF 只有一阶（CTIA 极点 31.25 kHz，p.6），抗混叠主力是低 IF + 数字域镜像抑制（"the noise folded from the spectral images can be rejected in digital domain", p.4）；无 RC AAF 阶数/平坦度/衰减上界讨论。型比：其「谐波折叠 1/(k1k2)² → 误差%」预算（p.4）是**逐项解析到误差的预算风格**，与 P3 想做的「衰减不足→误差」同型。killRisk：无。
- **方法学（D1–D10，H5 域）——相关性：高（对 D9/D5/C9 的最新工程参照）**：
  - **D9（kickback 回稳）**：SC 输入 10 pF、Ts=16 µs 慢采样 → 建立容易（SR 0.3 V/µs @10 µA 即可）；**踢回对策 = TIA 输出端加 charge bucket filter**（p.6–7）——即「在驱动器与 SC 负载之间插无源电荷缓冲网络」，与外置 RC 的思路同族，但**幅度与回稳时间无数值**；
  - **D5（建立）**：给出了完整的「负载电容 → 电流 → 压摆率 → 周期内建立」换算链（p.6–7），可直接作为 P1 论文 D5 判据的对照格式；
  - **C9（运放峰值）**：TIA 用 Miller 补偿 + CTIA 极点稳定（"CMC and RMC to achieve stability", p.6），无峰值/相位裕度数值。
  - 注意其 fs=62.5 kHz 与 P1 场景（128 kSPS 级）慢 500 倍以上，**其建立余量结论不能直接外推到快采样场景**。
- killRisk 总判：**无**。不触碰 P1/P2/P3 任何主张。

## 没读到的

- **kickback/charge injection 全文零定量**：无「kickback」或「kick-back」字样；采样伪影只有一句对策（charge bucket filter, p.6–7），无伪影幅度、无 bucket 电容取值、无回稳时间数。Charge bucket filter 的元件值文中未给（Fig.3 里只有框图）——**待核**（若有版图/附录）。
- ΔΣ ADC 的 SNDR 峰值（Fig.16 SNDR vs 幅度曲线）文本层无数值，只有 "no significant distortions are observed within the signal band… out-of-band distortions are within 10 dB of the noise level"（p.9）；"increased in-band noise that limits…" 一句在 p.9 被截断，后续解释在 p.9–10 交界（正文引述见 p.10 的 ADC 带宽/吞吐段）。
- 2 电极 vs 4 电极 bio-Z 的对比讨论只有一句立场（"Previous works, focusing on 2-electrode bio-Z measurements, propose cancelling the large baseline impedance… However, in EIM, the baseline bio-Z contains information regarding tissue composition, so it should be measured together with the time-varying bio-Z", p.5）——无两线误差地板分析。
- Table I（与 [24][25][27][30] 的对标表）是图形表，文本层取不到逐项数值；正文只给了 SNRmax/FoM 的结论性比较（p.10）。
- 参考文献 [33]（gain-compensated 伪 2 路谐振器原始出处）、[34]（CT 单运放谐振器对比）未读。
