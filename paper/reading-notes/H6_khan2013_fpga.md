# 精读笔记 · Khan, Borsic, Manwaring, Hartov, Halter 2013《FPGA Based High Speed Data Acquisition System for Electrical Impedance Tomography》（J. Phys.: Conf. Ser. 434 (2013) 012081, doi:10.1088/1742-6596/434/1/012081）

> 格式标准（全组沿用）：出处 → 核心命题（原文引用）→ 关键数值（原文）→ 对 P1/P2/P3 的对照 → 没读到的。
> 读法：pdftotext 全文逐节读，引用一律原文加页码；不转述成模糊话。
> 注：页码 = 文内印刷页（1–4，PDF 第 2–5 页；PDF p.1 为 IOP 封面）。XV Int. Conf. on Electrical Bio-Impedance & XIV Conf. on Electrical Impedance Tomography；NIH/NCI 1R01CA14302001A1、NIH/NIBIB 1R21EB011568-01 资助（p.1）。

## 核心命题（原文）

**③ 恒流源/激励拓扑与失真处理（EIT 应用）**

1. 激励-测量基本形态（P2 同构旁证的锚句）："Traditional EIT instruments apply AC current and measure induced potentials on a number of electrodes in contact with a specific tissue or body region of interest."（p.1）
2. 激励源是通用信号发生器 + AFE 板上的切换矩阵，**不是论文级恒流源电路**："Signal Generator (SigGen): This module generates the AC signals. SigGen module also generates a trigger pulse synchronized with the start of the waveform cycle."（p.2，NI 5406）；"Analog Front End (AFE): We designed an AFE board with filters, multiplexers for signal switching, Programmable Gain Arrays (PGA), shield drivers, relays for power control etc. on it for appropriate analog conditioning of the signal."（p.2）。Fig.1 框图（p.2）给出 Source Mux / Sink Mux / "Current to Voltage Converter" / LPF / PGA 的链路，电极经前连接器进 AFE。
3. 源/沉侧增益与电流检测电阻（全文唯一电流路径数值）："The net gain on the source and sink side was 0.28 and 1.11 respectively (current sense resistor is 499 Ω). With input signal set to 2Vpp sine wave at 100 KHz, Vpp at the ADC input was 0.56 V."（p.4）——注意：**恒流源拓扑（Howland 与否）、输出阻抗、合规电压、电流精度均未给**；"current to voltage converter's virtual ground"（p.4）说明接收侧是跨阻（I/V）结构。
4. **失真处理 = 在线 THD 监测**（不是失真消除）："We define the Total Harmonic Distortion (THD) of the signal by (1). In this equation, the numerator is the sum of squared magnitude of higher order harmonics, and the denominator is the magnitude squared of the input signal's dominant harmonic."（p.3，式(1) 公式体在文本层丢失，文字定义完整）；"We compute the numerator on the FPGA itself and use it to analyze the transient abnormalities or signal quality deterioration. Division is a computationally expensive operation to perform on the FPGA thus the THD is computed on the PC. Calculation of the numerator on FPGA allows us to keep the throughput low, while having a metric to ensure that the signal quality is satisfactory"（p.3）。
5. 频谱特征与降噪手段：FPGA 上 512 点 FFT（"This block computes 512-point FFT on the input samples, x, collected from 8 channels and returns X, the real and imaginary component of the FFT output." p.3）；"Averaging block … can average at a user-selectable factor up to 64 waveform cycles."（p.3）；"It can be observed that: 1) Increasing the number of averages improved the SNR (by reducing the Gaussian noise power); 2) With the AFE connected, SNR dropped by about ~4 dBs."（p.4）
6. 宽带指标（摘要）："Our system is wideband, and capable of acquiring data for input signal frequencies ranging from 100 Hz to 12 MHz."（p.1）；实测口径："we are able to record a full spectrum of data (with FFT and spectral characterization, for 47 discrete frequencies spaced logarithmically from 100 Hz to 11.25 MHz, 8 Million samples) within 14 seconds."（p.4）

## 关键数值（原文）

- 系统：32 通道模块化 DAQ（现配置用 8 通道），NI PXI + FlexRIO 7952R（FPGA）+ NI 5751（14-bit ADC，SPI 读取）+ NI 5406（SigGen）+ NI 6674t（TSync/DDS）+ NI 6341（继电器与电源监控）（p.1–2）
- 激励扫描：28 组 source/sink 模式交替注入/沉放（"a set of 28 source/sink patterns to alternate injecting and sinking electrodes", p.4）
- 帧率："At a fixed signal frequency of 100 KHz, to acquire data from 12 channels for 100 patterns with no signal averaging, the system takes nearly 13ms … With 28 patterns per frame (or image), this translates to roughly 274 frames (or images) per second, with averaging factor 4; this number drops to 188 frames/sec."（p.4）
- 吞吐压缩："we were able to reduce the required throughput between the PC and the FPGA by a factor of 32:1"（p.4；摘要 p.1 同）
- SNR 测试条件："For the ADC test, a 2Vpp sinusoidal signal (ADC full-scale) at 100 KHz was applied at the ADC input. For the AFE test, a 2KΩ resistor was connected between a channel and current to voltage converter's virtual ground."（p.4，Ω 经渲染图核回）；Fig.3 两幅 SNR-vs-averaging 曲线（ADC 单独约 88–104 dB、接 AFE 约 75–100 dB，6 个频点 100 Hz–10 MHz，平均因子 None/2/4/8/16/32，图上可读）
- FPGA 时钟：采集块 "clocked using a clock frequency within 30-50 MHz range"、流水优化 "ranging from 50 MHz to 95 MHz"（p.3）；采集半并行（一次 4 通道，p.3）

## 对 P1/P2/P3 的对照

- **P2（Kelvin 地板）——同构系统旁证（本文主要价值）**：EIT 与 DE-DRMS 同属"已知电流激励 + 电位差测量"族（p.1 锚句），且是宽频（100 Hz–12 MHz）生物阻抗场景；其工程口径值得对照：①激励质量用 THD 在线监测把关（p.3）而非假设理想恒流；②AFE 串入后 SNR 掉 ~4 dB 是实测认账的（p.4）；③激励/接收两侧分开给净增益（0.28/1.11）与检测电阻（499 Ω，p.4）。**旁证的是"结构同型、指标同族"，不是失真机理**：它没给恒流源输出阻抗/合规/精度，恒流到底多"恒"无从引用。
- **P1（失配消去条件）——P1 反例检索结论：无**。全文无差分 RC 网络、无 CMRR、无失配→共模转差分条件；多通道差异只体现为 SNR 曲线（Fig.3，位图）。
- **P3（AAF 衰减上界）**：无。AFE 有 "filters" 与框图 LPF（p.2），但无衰减/截止指标。
- **引文价值**：p.1 锚句作 EIT=恒流激励+电位测量的同构出处；p.3 THD 在线监测段作"激励失真是被监测指标"的旁证；p.4 增益/499 Ω/AFE 掉 4 dB 作工程量级对照。引用时须注明其恒流源拓扑未披露。

## 没读到的

- **恒流源电路本体**：无 Howland/改进型 Howland/电流镜等任何拓扑名、无输出阻抗、无合规电压、无电流精度/温漂——只能确认"源侧净增益 0.28、电流检测电阻 499 Ω"（p.4）。若需 EIT 恒流源电路细节，须另找（如参考 [3] Halter 2008 IEEE TBME 宽带 EIT、[5] Saulnier 2005 IOP 章）。
- 式(1) 的 Σ 公式体文本层丢失（文字定义在，p.3）；Fig.3 的精确数据点不可提取（坐标轴与曲线经渲染图可读近似范围，已录于「关键数值」）。
- "Data calibration"（p.2 软件功能 f 项）只列名，无校准方法。
- 参考文献 [1]–[6] 原文未读；屏蔽驱动（shield driver）电路细节无。
