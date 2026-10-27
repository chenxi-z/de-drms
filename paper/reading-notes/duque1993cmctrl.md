# 精读笔记 · Duque-Carrillo 1993《Control of the Common-Mode Component in CMOS Continuous-Time Fully Differential Signal Processing》（Analog Integrated Circuits and Signal Processing 4:131–140）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> 页码用期刊页（131–140）；PDF 页 1–10 与之差 130。主题 = **主动共模控制（CMFB）**：与 P1 的无源匹配消去路线相对的"另一条路线"及其自身失配地板。

## 出处
- Duque-Carrillo, J.F., "Control of the Common-Mode Component in CMOS Continuous-Time Fully Differential Signal Processing", Analog Integrated Circuits and Signal Processing, vol. 4, pp. 131–140, 1993. doi:10.1007/bf01254864.
- 本地：`H2-差分CMRR/duque1993cmctrl.pdf`（10 页）。bib key：`duque1993cmctrl`（literature.bib L1380）。
- 注：bib 著者写 "Francisco Duque-Carrillo, Juan"，刊名页署名 "J.E Duque-Carrillo"（作者全名 Juan Francisco Duque-Carrillo，见 p.140 作者简介）。

## 核心命题（原文）

1. **FD 电路为何需要 CMFB：差分反馈只稳定 DM，共模仍是开环**（p.131）：
   > "From a design point of view, the only conceptual difference between double- and single-ended signal processing resides, indeed, in the extra feedback required to control the output common-mode component in FD amplifiers. This need arises from the fact that feedback around the amplifier just provides stabilization for the output differential-mode (DM) component, while the common-mode (CM) is still operating in open-loop mode."（p.131）
   中文：共模失控不是失配问题而是**结构性开环**问题——主动路线（CMFB）的立论起点，与 P1 的无源消去路线构成路线级分野。
2. **FD 收益口径：偶次谐波相消（即便失配仍在）+ 共模抑制，SNR 提升一个量级**（p.131）：
   > "A cancellation of even harmonics, even under the presence of the unavoidable mismatching in the devices, as well as the suppression of all undesirable common-mode signals by the differential circuitry, improves over one order of magnitude the signal-to-noise in FD circuits with regard to the single-ended counterparts."（p.131）
   中文：差分结构的核心收益宣言——注意"即使存在不可避免失配"的措辞（偶次谐波相消对失配一阶稳健，与共模相消需要匹配形成对照）。
3. **CM 检测器失配产生转换项 α₂：三系数模型**（p.133, Eq.1）：
   > "the small-signal output vs of CM detector can be expressed as Vs = α1·Vo,cm + α2·Vo,dm + α3·Vo²,dm  (1) where the first term, α1·Vo,cm, would be the only output if the CM signal detector were ideal, the term proportional to the DM output component, α2·Vo,dm, arises as a consequence of the unavoidable mismatches in the CM sense components, and the last and nonlinear term, α3·Vo²,dm, appears due to nonlinear I-V characteristic of MOS transistors."（p.133）
   中文：把检测器非理想分解为 α₁（理想检测）/α₂（失配→线性模式转换）/α₃（非线性→谐波交互）三通道——α₂ 就是 P1 关心的"失配→转换"在主动路线里的形态。
4. **CMFB 对 CMRR 影响不大，但检测器失配给出可观的转换增益（主动路线自己的失配地板）**（p.133）：
   > "For typical values, the impact of CMFB loop on the amplifier CMRR is not significant since CMRR* = A*DD/A*DC ≈ CMRR. However, mismatching on the CM detector can lead to appreciable DM-CM conversion gain (A*DC), mainly for high α2/α1 and ADD values. Hence, we denominate conversion-gain factor to the ratio α2/α1."（p.133）
   中文：CMFB 环路本身不救 CMRR；**残余转换由检测器失配决定**——主动控制不能免除匹配需求，只是把它搬进检测器。
5. **CM 环路速度/精度规格：环路增益与 GBW 不得低于 DM 环（设计判据）**（p.135, Eq.5）：
   > "Recall that for most of the applications, minimum design specifications for CM loops usually are LGcM ≥ LGDM,ex (5a) LGBWcM ≥ LGBWDM,ex (5b)"（p.135）
   中文：共模控制要"追平"差模控制的带宽与精度——这是主动路线的代价声明（面积/功耗/稳定性）。
6. **统计消错：元件越多随机失配越被平均**（p.137）：
   > "in spite of the larger spreads between the best-case and the theoretical worst-case A*DC values in CMFB loops based on current injection, in practice these spreads are narrower than in resistive source degeneration loops. This fact is a consequence of the higher numbers of transistors involved in the first ones. Thus, each transistor has a minor impact on the performance of the whole circuit, and therefore, random parameter deviations are averaged out."（p.137）
   中文：失配均值化效应（元件数→方差稀释）——P1 若讨论"多级梯形失配统计"可引此对照。

## 关键数值（原文）

- Monte Carlo 口径（p.135–136）：75 次试验，Δβ 与 ΔVT 扩散 1% 和 5 mV，随机无关逐管变化；无源电阻间 1% 相对变化；SPICE level 2，2 µm 标准 CMOS；被控放大器规格 {Ad, GBW, SR, φm} ≥ {70 dB, 5 MHz, 8 V/µs, 70°}，负载 6 pF、5 V 电源。
- **转换增益 A*DC（mean/σ/WC，dB）**：源极退化电流镜 III.1：11.5/10.9/**23.6**（WCtheo 17.9 dB）；电流注入 IV.1：21.6/8.9/**35.3**（WCtheo 32.7 dB）、IV.2：7.2/7.1/21.7、IV.3：5.5/7.8/18.5；电流转向 V.1：8.2/11.1/21、V.2：20/9.5/33、V.3：22.1/9.6/**36.2**、V.4：9.4/8.5/23（Table 3–5, p.136–138）。
- 相对性能 ACM/ADM：源极退化仅 **0.08**（"very insufficient GBWCM << GBWDM"，p.135–136 表 3）；注入/转向类 0.82–1.3。
- THD（±1 Vp-p @100 kHz）：0.025%（退化）～0.22%（V.2）；所提低失真电流转向环 "THD was kept below 0.007% for a 2-Vp-p 100-kHz input signal"（p.139）。
- 转换增益因子（p.136）：源极退化 Δβ/β；注入 IV.1 为 Δβ/β + ΔVT/VDSat（WCtheo 32.7 dB）；IV.2/4.3 为 δIB/IB = δβ/β + ΔVT/(4VDSat)（Eq.7）。

## 对 P1/P2/P3 的对照

- **P1（失配消去条件）**：相关性**中（路线级对照，非对手）**。本文不涉差分 RC 滤波器与 τ 匹配；其 α₂=检测器失配→模式转换与 P1 的 H_N−H_P 同族，但解法相反——**主动反馈**而非无源消去。P1 引用定位：related work 中"主动共模控制路线"的代表，并指出其局限（CMFB 不改善 CMRR 本身、残余转换仍由检测器匹配决定——p.133 原话），反衬 P1 无源消去条件的价值。注意 Duque 的转换增益口径是开环增益比（正 dB 数值），与 P1 的 G_DC 幅值口径不同，引用勿直接换算成 CMRR 而不注明。
- **P2（Kelvin 结构地板 ≈56 dB）**：相关性**中低（旁证）**。无 Kelvin；但 Monte Carlo 的 A*DC 地板（mean 5.5–22.1 dB、WC 18.5–36.2 dB）配 ADD≈70 dB 即隐含 CMRR 残余 ~34–65 dB 量级——"主动路线同样被失配地板限住"的跨域数据点；P2 写地板时可用作第二证据线，但须注明域（CMOS CMFB 检测器）与口径（Monte Carlo WC）差异。
- **P3（平坦度约束衰减上界）**：无。
- **方法学（D1–D10）**：无正式方法学；但"三个品质因数"（线性转换增益 / CM-DM 相对性能 / 非线性交互 THD）的**比较框架**（Abstract p.131 与 §5）是门槛化方法学的同型物——D 项可借鉴其"用统一 FoM 给候选结构排名"的做法。
- **killRisk 判断**：非 killRisk（主动控制域，与 P1/P2/P3 无主张冲突）。

## 没读到的
- 差分 RC 滤波器/τ 匹配/AAF（全文无——对象是连续时间 FD 放大器的输出共模，不是输入滤波）；
- Kelvin 四线结构；引线电阻；
- 频域 CMRR 相位特性（Hornero 2021 批评的那种"只看模"）；本文 A*DC 只给增益幅值（Monte Carlo mean/σ/WC），无相位；
- Table 1 的 8 种 CM 检测器与 Table 2 的注入方式在 PDF 中为双栏压缩扫描，公式与图细节多处不可读（OCR 缺失，引用具体检测器结构前需对 Springer 原版核验，标"待核"）；
- 所提低失真环（Fig.5）的完整电路参数。
