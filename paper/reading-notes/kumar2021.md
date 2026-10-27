# 精读笔记 · Kumar 2021《A Discrete-Time Delta-Sigma Modulator With Relaxed Driving Requirements And Improved Anti-Aliasing》（ISCAS 2021）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> **本篇为 P0 级文献（H1 轴）**：证明「DT ΔΣ 的驱动与抗混叠缺陷可以在调制器内部用采样拓扑解决」——
> 即 DT ΔΣ 对前端缓冲与外部 AAF 的需求是**可被电路技术放松的工程痛点**，而非不可动摇的物理必然。

## 出处
- R. S. Ashwin Kumar (IIT Madras), "A Discrete-Time Delta-Sigma Modulator With Relaxed Driving Requirements And Improved Anti-Aliasing," *2021 IEEE International Symposium on Circuits and Systems (ISCAS)*, DOI: 10.1109/ISCAS51556.2021.9401336。
- 全文 5 页（双栏会议论文），本地文件 `fulltext/H1-ΣΔ-AAF/kumar2021.pdf`；180 nm CMOS 设计、原理图级仿真（非流片实测）。

## 核心命题（原文）
1. **DT ΔΣ 的两大公认缺陷 = 功耗大的输入缓冲器 + 需要外加抗混叠滤波器**（p.1，Introduction）：
   > "On the downside, a DTDSM requires a power-hungry input buffer and an anti-alias filter [4]. In this paper, we propose a technique that addresses these two deficiencies in a DTDSM."
   （这是 H1 轴的核心出发点：业界明确承认 DT ΔΣ 需要前端缓冲与 AAF，本文同时缓解两者。）
2. **两相交错采样把输入电容对半分摊，缓冲器瞬态电流降为 1/4**（p.1 摘要 + p.2–3 分析）：
   > "The proposed integrator samples the input in two non-overlapping phases instead of sampling it in a single phase. This way, the input capacitance can be equally distributed among the two phases, resulting in a 2× reduction in the switched capacitor load that needs to be driven by the input buffer."（p.1, Abstract）
   > "Thus, even though the input is sampled twice in a clock period of Ts, the instantaneous value of the current demanded by the proposed circuit will be u[n]/(4Ron), which is two times smaller than variant-2 (assuming that a reset phase is added to variant-2 as well) and four times smaller than the variant-1."（p.3, III-B）
   （噪声不变（式(3) = 式(2)）前提下，开关电阻可加倍 × 电容减半 = 电流需求 u[n]/Ron → u[n]/4Ron。）
3. **交错采样隐式实现 sinc 型预滤波，STF 在 fs 奇数倍处出现陷波，从而天然抑制这些频点的混叠**（p.3, III-C）：
   > "Thus, the proposed circuit implicitly filters the input by a transfer function H(f ) = 0.5 (1 + exp(−jπf Ts)) (4) This transfer function has notches at odd multiples of the sampling frequency, as shown in Fig. 7. Thus, with the proposed circuit, the DTDSM will inherently prevent aliasing from odd multiples of the sampling frequency."
   （注：该陷波机制是**时钟相位结构**给出的（两个错开 Ts/2 的采样相加），不是靠元件匹配——与 P1 讨论的 RC 时间常数匹配完全是两类机制。）
4. **白噪声输入时带内混叠噪声功率减半 → 前置 AAF 要求随之放松**（p.4）：
   > "Hence, the in-band aliased noise power [8], i.e., total noise power that will alias into the signal band, when a white noise is present at the input, will be reduced by a factor of two with the proposed technique. This, in turn, will relax the requirements on the anti-alias filter needed upfront."
   （作者明确表述其贡献是**放松**（relax）前置 AAF，而非取消——外部模拟 AAF 仍然存在。）
5. **实测（仿真）陷波深度量级：fs 附近 ±fs/44 带宽内抑制 > 40 dB**（p.4, IV）：
   > "It is clear that with the proposed technique, in a bandwidth of fs /22 around fs (i.e., an oversampling ratio greater than 22), the alias rejection of the DSM is more than 40 dB."
   （40 dB 远低于 P1 方法学 D1 的 ≥80 dB 差模要求——说明纯靠 DT ΔΣ 片内隐式陷波达不到 P1 门槛，外部 AAF 不可省。）

## 关键数值（原文）
- 采样率 **6.144 MHz**、OSR **128**（信号带宽对应 fs/256，音频段）；输入电容 C1 = C2 = 1 pF（p.4）。
- 峰值 SNR **97.9 dB**（proposed）vs 97.7 dB（shared-cap 常规）vs 94.8 dB（separate-cap 常规）；总功耗 **0.86 mW** @1.8 V、0.48 mA；180 nm CMOS；4 阶 CIFF + 单 bit 量化（p.1 摘要 / p.4）。
- 驱动对比表（Table I, p.4）：待驱电容 C1 → C2=0.5C1 → C3=0.25C1；开关电阻 Ron → 2Ron → 4Ron；瞬态开关电流 u[n]/Ron → u[n]/2Ron → u[n]/4Ron；片上电容 2C1 → 0.5C1 → 0.75C1；STF 奇数 fs 陷波：No → No → **Yes**。
- 噪声：三变体带内噪声方差式(1)(2)(3)分别为 2kT(1+γ)/(MC1)、kT(1+γ)/(MC2)、kT(1+γ)/(MC2)——proposed 与 shared-cap 噪声相同（p.3 式(3)）。
- 隐式滤波器：H(f)=0.5(1+exp(−jπf·Ts))，陷波在 (2k+1)·fs（p.3 式(4)）；验证：0–2fs 扫频，fs/22 带宽内抑制 >40 dB（p.4, Fig. 9）。

## 对 P1/P2/P3 的对照
- **P1（G_DC=H_N−H_P≡0 消去条件）**：相关度 **中（支撑性而非对抗性）**。本文的陷波由采样时钟结构保证（延迟 Ts/2 的两采样相加，纯时域确定性），**不依赖任何 RC 匹配**——反衬出 P1 研究的外部 RC AAF 中 H_N/H_P 失配问题在 DT ΔΣ 片内拓扑里被"结构性"绕开；但陷波只覆盖 fs 奇数倍，偶数倍（含 DC 附近的低频折返、fs 附近之外频段）仍需外部 AAF——P1 的匹配消去条件仍有不可替代的适用域。
- **P2（Kelvin 结构地板）**：相关度 **无**。全文不涉及四线/Kelvin 连接或引线电阻。
- **P3（平坦度约束下衰减可达上界）**：相关度 **低**。隐式滤波 |H|=|cos(πfTs/2)| 在带内 OSR=128 处幅度 ≈cos(π/512)≈1−4.7e-6，通带平坦度天然无虞（文中未展开讨论平坦度，只在 fs 附近讨论抑制）；未给出"平坦度—衰减"权衡的任何定量上界。
- **方法学（D1–D4/D8 门槛）**：其片内抑制量级 40 dB << D1 的 80 dB（差模@4.096 MHz）与 D3 的 100 dB（@16.384 MHz）——**直接证据：片内隐式抗混叠不足以满足 P1 门槛，外部 AAF 及其失配分析（P1）不可被此类技术取代**。
- **killRisk**：**无**。本文不讨论外部 RC AAF 的 R/C 取值配方、也不讨论元件失配或共模抑制；它是 P0 语境文献（DT ΔΣ 放松驱动/放松 AAF 的代表性技术），不会推翻 P1 的任何主张，反而为其"外部 AAF 仍必需"的前提提供佐证。

## 没读到的
- 无硅片实测（仅 schematic 级瞬态噪声仿真）；无实测陷波深度曲线以外的失配敏感性分析（时钟相位误差 φ21/φ22 非理想时陷波深度如何退化——文中完全未讨论，属"待核"空白）。
- 未讨论共模/差模区分、未讨论混叠来源中除 fs 奇数倍以外的路径（如采样开关电荷注入、缓冲器非线性混叠）。
- 未给出缓冲器本身（本文只谈"缓冲器电流需求减半"，缓冲器电路与噪声贡献未设计）。
- 引用文献 [8]（Peev 2008, "An anti-aliasing filter inspired by continuous-time ΔΣ modulation"）值得后续单独检索——是"用 ΔΣ 思想做 AAF"的相邻线索。
