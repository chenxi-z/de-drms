# 精读笔记 · Zou 2017《Sigma-delta ADC based adaptive readout ASIC for digital audio sensor》（Analog Integr Circ Sig Process 92:383-392）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> H5 轴视角：SC ΣΔ 调制器输入采样结构（C1 取值）、基准缓冲建立时间口径（1/4 时钟周期）、AAF 取值依据（带内 0.1 dB / 0.5Fs 处 15 dB）。

## 出处
- Zou, Rocca, De Blasi, Grassi, Malcovati, Baschirotto, "Sigma-delta ADC based adaptive readout ASIC for digital audio sensor", *Analog Integrated Circuits and Signal Processing*, vol. 92, pp. 383–392, 2017. DOI 10.1007/s10470-017-1002-7。
- bibkey: `zou2017igmadelt`；全文 PDF：`fulltext/H5-kickback/zou2017igmadelt.pdf`（10 页，期刊页 383–392，下引页码=期刊页）。
- 主题：MEMS 数字麦克风自适应读出 ASIC（PGA+AAF+SC ΣΔ+DSP AGC），0.18 µm CMOS。

## 核心命题（原文）
1. **自适应读出链解决"高 SNR 与宽输入范围不可兼得"**（p.383）：
   > "Clearly, a wide input range and an excellent system SNR cannot be achieved simultaneously in the existing static readout ASICs for digital sensors."（静态增益链要么低增益噪声差、要么高增益早削波；故用 AGC 反馈随信号电平切换 PGA 增益 Ga，数字域再等量补偿。）
2. **AAF 取值依据是两条衰减判据而非深阻带**（p.385）：
   > "The AAF is a first-order low-pass filter built by poly resistors and MOS capacitors. The low-pass filter has a cutoff frequency at 237 kHz. The selection of the cutoff frequency is based on two concerns. Firstly, the attenuation over the input signal bandwidth (20–20 kHz) is less than 0.1 dB. Secondly, the attenuation at 0.5*Fs (Fs is the sampling clock frequency of 3.6 MHz) is about 15 dB."（一阶 RC 反混叠只要求带内平坦 0.1 dB + 0.5Fs 处约 15 dB，不追求深衰减，理由见下条。）
3. **换能器自身已衰减高频，AAF 无需深衰减；AAF 还兼抑增益切换毛刺**（p.385）：
   > "In fact, the transducer itself attenuates frequency components above certain bandwidth. So, the AAF is not required to provide deep attenuation for frequencies beyond 0.5*Fs. In addition, the AAF also helps to reduce the glitches generated at PGA output during its gain switching."（这是"外部 RC 取值依据"的一个直接范例：AAF 依据=信号源特性+采样折叠点，且 RC 同时承担毛刺平滑。）
4. **采样电容 C1 由 kT/C 噪声预算定出，125 fF**（p.386）：
   > "The capacitors in the integrators generate kT/C noise and the sampling cap C1 is the main noise contributor. In order to estimate the size of C1, we can firstly assume the OTA is noiseless, and then use the following equation [10]" —— "For giving SNR, OSR and the full-scale input voltage VFS, 125 fF is chosen as the minimal capacitor for implementation the coefficients."（SC 输入级的开关电容负荷即 C1=125 fF，按 kT/C≈量化噪声底这一经典口径选取。）
5. **拒绝双采样积分器（路径失配/噪声折叠）**（p.386）：
   > "Although the double-sampled SC integrator reduces half of the necessary size of C1 for the same SNR, this technique introduces path mismatch, extra noise folding and more switches."（本文 H5 视角下值得记：双采样省一半 C1 但引入路径失配与噪声折叠，被明确弃用。）
6. **基准电压缓冲的建立时间口径 = 1/4 采样时钟周期，压摆率下界公式**（p.388）：
   > "The slew rate of the amplifier is the key parameter to support settling time of V+ − V− within 1/4 of the sampling clock period [16]. The necessary slew rate can be estimated by (8), slew rate ≥ 4Fs(V+ − V−)."（驱动 SC 负载的缓冲放大器，其建立预算被明确限定在采样周期的 1/4 内——这是"建立时间口径"的文献实例；与 P1 增量四 D5「建立 ≤900 µs」同属"缓冲驱动容性负荷须给建立指标"的方法学。）

## 关键数值（原文）
- AAF：一阶，fc = 237 kHz；带内（20–20 kHz）衰减 < 0.1 dB；0.5Fs（Fs = 3.6 MHz）处约 15 dB（p.385）。
- SC ΣΔ：二阶单环 1-bit，OSR = 90，理论 SNR 上限 92 dB（式 5：SNR = 50log(OSR) − 5.12）；采样电容 C1 = 125 fF（kT/C 预算，式 6）（p.385–386）。
- 实测：调制器峰值 SNR（A 加权）84 dB（含器件噪声的晶体管级仿真）；系统 SNR/SNDR = 68 dB(A) @1 kHz 94 dB SPL；AOP 136 dB SPL；正常模式 600 µA，睡眠模式 <20 µA（p.386, p.389–390）。
- 基准缓冲：压摆率 ≥ 4Fs(V+ − V−)；V+−V− 噪声折入带内=全谱积分/OSR，计入后调制器 SNR 变化 <0.25 dB（p.388）。
- PGA：仪表放大器拓扑，Ga = 1 + 2R1/R2（式 4），增益步进含 30→24→18 dB 切换点（106/112 dB SPL）；输入折算噪声约 2.55 µVrms（高增益档）（p.385, p.389）。
- 电源：电池 1.62–3.6 V（标称 1.8 V）；PSR 100 dB；LDO Vdropout <50 mV（p.388–390）。

## 对 P1/P2/P3 的对照
- **P1（消去条件）**：无直接讨论。本文是系统级自适应链，不涉及双通道消去条件。相关度：无。
- **P2（Kelvin 结构地板）**：未涉及 Kelvin/四线结构。PGA 输入为仪表放大器高阻输入（"very high input impedance"），无引线电阻地板话题。相关度：无。
- **P3（衰减可达上界）**：仅提供一阶 AAF 的取值判据实例（0.1 dB 带内 / 15 dB @0.5Fs），可作为"外部 RC 取值依据"的旁证文献，但不涉及衰减上界理论。相关度：低。
- **方法学（D9/D5/C9）**：**中-高**。三处直接可用：① SC 输入级电容负荷由 kT/C 定尺寸（C1=125 fF）；② 驱动 SC 负载的缓冲放大器建立时间口径 = 1/4 采样周期、SR ≥ 4Fs·ΔV（p.388，对 D5「建立 ≤900 µs」的"给口径"式支撑）；③ AAF 取值依据=源特性+0.5Fs 折叠点+毛刺平滑（p.385，对 P1 前端 RC 取值叙述的对照文献）。
- **killRisk**：无。本文不与 P1/P2/P3 任何主张冲突；其"建立预算=1/4 时钟周期"与"AAF 不追求深衰减"的口径反而与 P1 增量四的门槛化方法学相容（fMOD=4.096 MHz 半周期 122 ns 回稳 0.01% 是更严的口径，本文 1/4 周期 @3.6 MHz ≈ 69 ns 仅约束压摆段）。

## 没读到的
- **踢回电流/电荷数值**：全文未出现 input kickback / charge injection 的量化（无 pC/µA 数量级数字）；H5 轴要的"踢回电流/电荷数值"此篇没有。
- PGA 前端对换能器（容性源）的充电瞬态、源阻抗与 AAF R 的分压误差未量化。
- 基准缓冲的建立精度（回稳到多少位/百分比）未给，只给压摆率下界与"1/4 周期内建立"的定性口径——0.01% 级回稳口径此篇没有。
- 版图/版图寄生对采样开关电荷注入的影响未讨论。
