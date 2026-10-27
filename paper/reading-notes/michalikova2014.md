# 精读笔记 · Michalikova 2014《A Hybrid Device for Electrical Impedance Tomography and Bioelectrical Impedance Spectroscopy Measurement》（IEEE CCECE 2014）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。

## 出处
- Michalikova M., Prauzek M., 2014 IEEE 27th Canadian Conference on Electrical and Computer Engineering (CCECE), pp. 1–4，DOI 10.1109/ccece.2014.6900984。
- PDF 共 4 物理页，页码 = 物理页。
- 内容：Freescale Tower 模块化 BIS/EIT 混合测量装置，1 kHz–1 MHz，幅值比+相位差检测法（MRPDD），16 电极四端复用。

## 核心命题（原文）
1. **测量原理：串联参考电阻 + 幅值比/相位差检测**（p.2）：
   > "Magnitude Ratio and Phase Difference Detection method (as described in [10]) is based on comparison of two signals - one measured from unknown impedance Zx , the second one is measured from reference resistor Rs connected in series with unknown impedance. Current sine–wave excitation signal of constant amplitude 100 µAPP is applied by two electrodes to Zx and appropriate voltage drop is measured with two measurement electrodes."
   阻抗计算（Eq.1，p.2）：Z = (|A1|/|A2|)·RS·|K|·e^{jΦ}
2. **通道等增益假设：比率项"被假设消去"而非被结构强制**（p.2）：
   > "Assuming that IAs are identical and have the same gain the member with gain ratio equals 1 so it does not influence calculation of unknown impedance and can be left out from equation."
   及（p.2）：
   > "It is important to keep the same gain settings of both IAs in order to preserve right amplitude ratio of the signals."
   （两条测量通道的放大器增益相等是"假设"出来的消去条件——与 P1 的元件条件视角相对照：这里没有任何结构或校准保证它，最终 ±5% 误差正是这条假设链弱点的体现。）
3. **Kelvin 四端连接的常规理由**（p.2）：
   > "Two identical wideband instrumentation amplifiers INA163 are used for the signal detection, which have high input impedance 60 M Ω k 2 pF. IAs are used to eliminate influence of measurement electrode impedance to total measured impedance."
   （60 MΩ∥2 pF 高输入阻抗 + 四电极配置消除测量电极阻抗——Kelvin 结构的教科书式动机，无地板量化。）
4. **系统误差来源：引线间杂散电容 → 必须三点自校准**（p.3）：
   > "While measuring impedance the systematic error caused by stray capacitances between signal leads on input of instrumental amplifiers occures, so the calibration is required. We used the Quadratic Interpolation Self-calibration algorithm for nonlinear measuring systems proposed in [11]. There are needed three reference quantities of impedance, so we constructed three different RC circuits with the same cut-off frequency of 100 kHz (as used in [10])and used them as the three reference points which determine the correlation between the real value of impedance and the measured value."
5. **相位校准未能完成：噪声淹没 GPD 输入（1 MHz 低通也不够）**（p.1 Abstract / p.3）：
   > "Calibration on the phase shift has not been done yet, since both input signals to GPD are highly disturbed with the noise, although they pass through a low-pass filter with cut-off frequency of 1 MHz. The superposed noise confuses GPD, so it cannot give the correct results."
   （p.4 归因）："The noise is produced mostly by Tower elevators, which proves the Tower usage approach as a not good solution for the bioimpedance measurements and will not be used in future realization of the device."

## 关键数值（原文）
- 频率范围（p.1 Abstract）："Frequency range available for measuring is from 1 kHz to 1 MHz."
- 校准后误差（p.1 Abstract / p.4）："The relative error of impedance measurement after calibration ranges from -4.52 % to 5.98 % with mean value of -0.02 %."；"The most significant relative errors occur on high frequencies."（p.4）
- 信号链（p.2）：AD9833 DDS（扫频至 12.5 MHz，20 MHz 外部振荡器，频率分辨率 "up to 0.07 Hz"，输出幅度固定 0.6 VPP）；Howland 电流泵（LMP7717）转 100 µAPP，"fulfills the condition of the maximal current output 0.8 mA"；INA163 增益 G = 4 ×2；THS3062 双运放跟随器作阻抗隔离（跟随器配置 "up to 300 MHz"）。
- AD8302 GPD（p.2）："GPD measures magnitude (ratio of the amplitudes) in range −30 dB to +30 dB and phase difference from 0◦ to 180◦."；"Output VMAG is scaled to 30 mV/dB and VPHS is scaled to 10 mV/◦."；中心点 900 mV 对应幅度比相等/相差 90°；两输出范围 30 mV–1.8 V DC。
- 滤波（p.3）："We used LTC1560 lowpass elliptic filters with cut-off frequency set to 1 MHz. Filters are placed in both signal processing channels just before the voltage divider, which matches the input impedance of GPD."；p.4 补充为 "5th order low-pass elliptic filters"。
- 电极复用（p.3）：ADG1606 十六通道复用器 ×4，"ultra-low on-resistance"，四电极配置（两激励+两测量）。
- 对比件（p.1）："There also exists the fully integrated circuit AD5933 intended to measure bioimpedance … but this chip allows frequency measurement to 100 kHz"（故自建至 1 MHz 以覆盖 β 色散）。

## 对 P1/P2/P3 的对照
- **P1（消去条件）**：相关度**低**。可引的对照点是方法学两极：MRPDD 把两通道增益比"假设为 1 而消去"（p.2），且系统误差（杂散电容）靠三点二次插值自校准压回——与 P1 的"元件条件使 G_DC=H_N−H_P≡0 严格成立"相比，本文展示的是无元件条件、靠假设+后校准的路线，其代价是 ±5% 精度与相位链完全失效。可作为 P1 论证"假设式消去 vs 条件式消去"差距的低成本反面例（引用时注意其误差主要源头是 Tower 平台噪声而非比率假设本身）。
- **P2（Kelvin 结构地板）**：相关度**低**。有标准四电极 Kelvin 连接动机表述（高输入 IA 消电极阻抗），无任何地板量化或失配分析。
- **P3（衰减可达上界）**：相关度**无**。
- **killRisk 判断：无威胁**。学生会议论文，工程完成度低（相位链未工作），与 P1/P2/P3 无主张冲突，也不构成有分量的证据。

## 没读到的
- Fig.3–7 的曲线/箱线图数值（图不可读，正文只有极值摘要）。
- Rs 参考电阻取值、RC 参考电路具体元件值（正文未列）。
- 误差 −4.52%~+5.98% 的频率–阻抗分布细节（仅在图 6/7 中）。
- MRPDD 原始文献 [10]（Yang et al. 2006 Physiol. Meas.）与自校准算法 [11]（Liu et al. 1999）的原文内容。
