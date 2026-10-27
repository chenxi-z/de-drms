# 精读笔记 · Candy 1985《A Use of Double Integration in Sigma Delta Modulation》（IEEE Trans. Commun. COM-33(3):249–258）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> 页码用期刊页（249–258）；PDF 页 1–10 与之差 248。**ΣΔ 量化噪声理论正典**（任务简报定位：Candy 1981/1985）。注意：本文是 1985 扫描版，OCR 噪声大，以下引文均选自清晰段；上下标丢失处以「（OCR 待核）」标注。

## 出处
- Candy, J.C., "A Use of Double Integration in Sigma Delta Modulation", IEEE Transactions on Communications, vol. COM-33, no. 3, pp. 249–258, March 1985. doi:10.1109/tcom.1985.1096276.
- 本地：`H2-差分CMRR/candy1985a.pdf`（10 页）。bib key：`candy1985a`（literature.bib L1460）。
- 姊妹正典：Candy 1981（`candy1981the.pdf`，同库但不在本批任务单内）。

## 核心命题（原文）

1. **总命题：双积分 + 两电平量化的 ΣΔ 易实现、抗参数失配，1 MHz 采样即达 16 bit 等效分辨率**（p.249 摘要）：
   > "A modulator that employs double integration and two-level quantization is easy to implement and tolerant of parameter variation. At sampling rates of 1 MHz it provides resolution equivalent to 16 bit PCM for voiceband signals."（Abstract, p.249）
   中文：ΣΔ 路线的核心卖点——分辨率靠过采样+噪声整形买来，而非靠元件精度；这是与 P1（靠 RC 匹配消去共模）正交的"另一条精度来源"。
2. **三阶以上反馈环会锁死在坏模式（设计边界）**（p.249 摘要 + p.253/255）：
   > "but when three or more loops are used the circuit can latch into undesirable overloading modes."（Abstract, p.249）
   > "The possible use of triple integration has been rejected because it can latch into noisy modes of operation."（X. Conclusion, p.255）
   中文：环阶数存在"两阶最优"的稳定性边界——高阶噪声整形的收益被稳定性风险吃掉；与 P1"多级梯形不再充分"形成跨域同构（多级化在高阶处失效）。
3. **量化噪声整形闭式：双环把噪声谱按 |1−z⁻¹|⁴ 抬升**（p.251, Appendix A p.256）：
   > "Y(z) = z⁻¹X(z) + (1−z⁻¹)²E(z)"（Appendix A, p.256，Eq.11 附近；OCR 下标待核）
   > "The noise in this signal has spectral density N_M(f) = [2(1−cos ωT)]²e₀²"（p.256, Eq.12）
   中文：二阶噪声整形标准式；带内噪声按 (2f₀T)^{5/2} 标度衰减（Appendix B Eq.14，指数 5/2 清晰、系数 OCR 待核）。
4. **两电平量化的自稳定：信号电平自动把有效环路增益调回 1（增益容差免疫）**（p.252–253）：
   > "We find by experiment that signal levels adjust themselves so that the effective gain of the quantizer compensates for changes in the values of circuit gains G,. … signal levels in the circuit automatically adjust themselves to make the effective loop gains unity."（p.252）
   > "the change in the attenuation of the signal Y(ω)/X(ω) is less than ±0.05 dB for values of gain 0.5 < G, < 2."（p.252，Fig.8 随文）
   中文：非线性反馈提供"自校准"——增益在 0.5–2 倍范围内漂移，信号传输几乎不变；**容差被结构吸收而非被匹配**，与 P1 的匹配路线构成方法论对照。
5. **稳定增益边界：双环两电平时 G<2、多电平时 G<1.23**（p.253）：
   > "When two feedback loops are used, however, the contents of the integrators always decay to a small value when excitations are removed, provided that the gains G, are less than 1.23 for multilevel quantization and less than 2 for two-level quantization."（p.253, §VII）
   中文：可量化的稳定域（多电平 1.23 / 两电平 2；三环多电平 1.087，见 Fig.6 图注 p.252）。
6. **连续时间实现的 RC 时间常数容差 ±20% 只损 1 dB**（p.254, §VIII）：
   > "There is … the need to set the time constant RC with sufficient precision. … Time constants changing in the range 1.2τ to 1.8τ give less than 1 dB variation in noise level; this should satisfy most applications."（p.254；OCR 将 τ 误识为"7"，按 Fig.11 图注 (a)1.5τ/(b)2τ/(c)τ 与上下文校读）
   中文：τ 在 0.8×–1.2× 标称值内变化几乎不影响噪声——**τ 失配在此架构中无害**，恰是 P1 想证明"τ 失配在减法滤波器中有害"的最佳反衬文献。
7. **CT ΣΔ 固有 sinc 前馈滤波提供抗混叠（P3 相关）**（p.254, §VIII）：
   > "This low-pass filter, inherent to the circuit of Fig. 10, is useful for reducing aliasing distortion. For example, when 3.5 kHz signals are being modulated at 512 kHz, any spurious signals in the range 508–516 kHz alias into band. But the distortion is small because |G(508)| < −40 dB."（p.254）
   中文：G(ω) = sinc(fτ)·(2−e^{−jωτ})（Eq.8, p.254，OCR 部分待核）——过采样使 AAF 需求被固有滤波+频距稀释；Table I 给出各采样率下对 (fs/2−3.5 kHz) 处镜像的衰减。

## 关键数值（原文）

- 分辨率收益：单环 "reduces the noise e₀ by 96 dB"（3.5 kHz @16 MHz，p.251）；双环 "increases the resolution by 95 dB for a sampling rate of only 1 MHz and 3.5 kHz baseband"（p.251）；16 bit 等效 @1 MHz（摘要 p.249）。
- 设计目标口径（p.249）："> idle channel noise more than 80 dB below peak signal"、"moderate sampling rates (less than 1 MHz for 4 kHz telephone signals)"、"simple robust circuits (tolerances no tighter than ±3 percent)"。
- 稳定域：两环两电平 G<2；两环多电平 G<1.23；三环多电平 G<1.087（Fig.6 图注 "These circuits become unstable at gains 2, 1.236, and 1.087"，p.252）；三环两电平仅 G₂,G₃<0.55 可测（p.253）。
- 增益免疫：0.5<G<2 时 |ΔY/X|<±0.05 dB（p.252）；τ 1.2–1.8τ 内噪声变化 <1 dB（p.254）。
- AAF/抽取衰减要求（p.254–257）：固有滤波 |G(508 kHz)|<−40 dB；Table I：fs=64/128/256/512/1024/2048/4096/8192 kHz 时 (fs/2−3.5 kHz) 处增益 −23.9/−30.8/−37.1/−43.2/−49.3/−55.3/−61.?(−6 I .J)/−67.4 dB（最后第二行 OCR 待核）；末级抽取低通 "at least 25 dB of attenuation is needed"（p.255）；"requires R < −25 dB … easier than the requirement for antialiasing filters in D-channel banks, R < −32 dB"（p.257）。
- 空载噪声峰（两电平）：N_max 公式 Eq.5、峰宽 σ=πf₀τ Eq.6（p.253，符号 OCR 待核）。

## 对 P1/P2/P3 的对照

- **P1（失配消去条件）**：相关性**低（跨轴正典）**。全文无差分滤波器/共模/CMRR 内容；唯一概念接口是"容差被结构吸收 vs 容差被匹配消去"的方法论对照——P1 论证 τ 匹配必要性时可引本文 §VIII（τ±20% 无害）作反衬：同一物理量（RC 失配）在不同拓扑中的危害完全不同，凸显"消去条件是拓扑性质而非元件性质"。多环失稳边界（3 环锁死）与 P1"多级梯形不再充分"是**类比不是同构**，引用须谨慎。
- **P2（Kelvin 地板）**：无。
- **P3（平坦度约束衰减上界）**：相关性**中低**。给的是"过采样路线的 AAF 需求被稀释"的原始定量：固有 sinc 滤波 −40 dB@镜像点、末级抽取 ≥25 dB、D 通道 bank AAF 基准 −32 dB。P3 若主张"模拟 AAF 衰减上界受平坦度约束"，本文提供"换到 ΣΔ 域则 AAF 需求本身塌缩"的参照系（但注意：这是语音 codec 域，fs/带宽比与电阻测量域不同）。
- **方法学（D1–D10）**：无。但"两电平量化自增益稳定"（§VI）是"用非线性/反馈换容差免疫"的经典案例，可作 D 项讨论的对照组。
- **killRisk 判断**：非 killRisk（与 P1/P2/P3 无覆盖冲突；属量化噪声轴背景正典）。

## 没读到的
- 差分滤波器、共模、CMRR、Kelvin 结构（全文无）；
- 多级 RC 梯形匹配；
- 混叠抑制以外的滤波器平坦度/纹波内容；
- Candy 1981（一阶 ΣΔ 理论，姊妹篇，本批未读）；
- OCR 不可靠处：Eq.3/4/12/13/14 的系数与上下标（引用公式级内容前需对 IEEE Xplore 原版核验，标"待核"）。
