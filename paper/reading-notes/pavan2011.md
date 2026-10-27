# 精读笔记 · Pavan 2011《Alias Rejection of Continuous-Time ΔΣ Modulators With Switched-Capacitor Feedback DACs》（IEEE TCSI-I, 58(2):233–243）

> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> 读法：pdftotext -layout 全文逐节；刊印页 233–243（PDF 页 N = 刊印页 232+N）。公式内符号（gm、fs、τ 等）在文本层缺失，引文中以 [符号缺失] 标注；文字性数值全部可读。

## 出处

- Shanthi Pavan (Member, IEEE)，IEEE Transactions on Circuits and Systems—I: Regular Papers, Vol. 58, No. 2, Feb. 2011, pp. 233–243，DOI 10.1109/TCSI.2010.2071930。
- 单位：Indian Institute of Technology Madras（印度政府 Swarnajayanthi Fellowship 资助）。
- bib key：`pavan2011`（H3-CT-ΣΔ 轴，P0 级正典——"隐式抗混叠在何种条件下失效"的机理+解析+实测三重证据）。

## 核心命题（原文）

1. **SC/SCR 反馈 DAC 会摧毁 CT-ΣΔ 的隐式抗混叠**（p.233 摘要）：
   > "However, as we show in this paper, using an SC DAC can seriously compromise the alias rejection of the modulator, thereby nullifying one of the principal advantages of continuous-time operation."
   （p.233 引言又定义两大优点："Implicit antialiasing and resistive input impedance are perhaps the most attractive features of these converters."）

2. **失效机理 = 虚地摆幅被 DAC 电容"采样"**（p.235，机理句）：
   > "It is thus seen that an SCR DAC implicitly 'samples' the input through the finite swing at the virtual ground node of the first integrator, which is inevitable in practice, due to the finite bandwidth of the first opamp."
   （D3 逃生门的**边界条件**：隐式抗混叠并非架构免费赠品，它依赖第一条运放的有限带宽之外的理想性——降阶成立条件在此被精确刻画。）

3. **"采样率量级的运放单位增益带宽对噪声整形够用、对抗混叠不够用"**（p.235）：
   > "Several studies [11] have shown that opamp unity gain frequencies on the order of the sampling rate are sufficient to achieve the desired noise shaping—however, this is not adequate to achieve sufficient alias rejection."

4. **多级运放救不了；高阶调制器同样沦陷、与环路拓扑无关**（p.235, p.239）：
   > "A multistage OTA can indeed have a much higher transconductance at low frequencies. However, for good alias rejection, the swing at the virtual ground node should be sufficiently small for high-frequency inputs, … At these frequencies, the transconductance of multistage OTAs is likely to be much smaller than the low-frequency value."（p.235）
   > "It is commonly believed that higher order CTDSMs have better alias rejection (and lower in-band noise). However, as we will show below, this is not the case when SCR DACs are used."（p.239）
   > "The modulator topology [Cascade of Integrators with Feedback (CIFB)/Cascade of Integrators with Feed Forward (CIFF)] is irrelevant, since the DAC injects charge that has a component proportional to the sampled (and aliased) input."（p.235）
   （**"提高阶数≠提高抗混叠"**——与 P1"多级梯形不再充分"同型的结构论断：泄漏通道只取决于注入点，不取决于滤波器阶数。）

5. **辅助运放（assisted opamp）= 消去型技术，其性能由失配定量决定**（p.240–241，P1 核心证据链）：
   > "The alias rejection can be increased in two fundamental ways: 1) by making the virtual ground voltage zero; 2) by preventing the feedback DAC capacitor from discharging into the virtual ground."（p.240）
   > "The assisted opamp integrator is a circuit technique based on cancellation—any mismatch in the assistant and the input currents must be supplied by the opamp (which means a nonzero swing at the virtual ground node)."（p.241）
   > "A 10% mismatch in the assistant current improves the alias rejection (with respect to the unassisted case) by about 20 dB. … if the mismatch reduces to 5% (2%), we see improvements of 26 dB (34 dB) in the rejection. Note that, without assistance, [gm] of the OTA would have to be increased by a factor of 50 to achieve an alias rejection of 56 dB."（p.241）
   （这是**失配→消去残余→地板**的完整量化链：消去型方案即使失配 10% 仍有净收益（20 dB），失配 2% 收益 34 dB；对照"硬堆 gm ×50 才到 56 dB"。—— P1 的"精确消去 vs 鲁棒设计"之争在本文有标准数值模板。）
   > "it is apparent that the assistant should supply a current which is exactly 180 [degrees] out of phase with the input current. This must be achieved at the sampling frequency, which necessitates sufficient matching in the bandwidths of the input current path and the assistant transconductor."（p.241）
   （精确消去条件不止幅度匹配，还有**带宽/相位匹配**——P1 单级 τ=R·C 匹配充要性讨论的"相位维"旁证。）

6. **实测确认：无源 SCR 比理想差 30 dB、有源 SCR 补回 15 dB**（p.242）：
   > "If the first opamp was ideal, the alias rejection of the SCR-DAC-based converters should be about 90 dB. However, as seen in Fig. 22, measurements show that the alias rejection is 30 dB worse when a passive SCR DAC is used. An active SCR DAC improves the rejection by about 15 dB when compared to the passive case."

## 关键数值（原文）

- 一阶解析（p.235–237）："choosing [τDAC=fs/…（式值缺失）] results in an AR of only 20 dB"（p.235）；SC DAC 在 fs 处抑制 "only about 30 dB"（G0=29 归一，Fig.7，p.237）与 "only about 21.5 dB"（G0=9，Fig.8/9，p.237）；NRZ 对照为无限抑制（采样在环滤波之后）。
- 增益带宽对比（p.240）："doubling the transconductance of the single-stage OTA reduces the magnitude of the STF at the sampling rate by only 6 dB"（gm 翻倍只换 6 dB——暴力参数化路径的边际收益）。
- 辅助运放失配链（p.241）：10%→+20 dB；5%→+26 dB；2%→+34 dB；无辅助时 "increased by a factor of 50 to achieve an alias rejection of 56 dB"；助手电路噪声/失真/失配折算到输入被衰减 "by a factor on the order of [gms/gm]"（p.240）。
- 实验平台（p.241–242）：三阶单比特音频 CTDSM、CIFF；0.18 µm CMOS、1.8 V、目标 15-bit/24 kHz、额定 fs=6.144 MHz（实测因 4.7 MHz 带通滤波器可用而降频运行，积分器单位增益频率同步降为 0.8×）；理想一运放时 SCR 方案 AR ≈ 90 dB；实测无源 SCR 差 30 dB、有源 SCR（共栅级）再补 ~15 dB，受限原因是共栅管有限 gm·ro "does not fully isolate the DAC capacitor from the virtual ground"（p.242）；助手跨导在 fs 处相位差约 35°（"about 35 [degrees] out of phase"，p.242——当时设计未按抗混叠需求给助手带宽的历史局限自述）。
- 状态空间分析框架（p.236–238）：基于 Liou 1972 周期开关线性电路精确分析（参考文献 [12]），两相状态矩阵 + 稳态解 (8)，与宏模型仿真逐点吻合。

## 对 P1/P2/P3 的对照

- **P1（消去条件 G_DC(s)≡0）**：高度相关。本文是"**消去型电路技术的失配敏感度定量律**"正典：辅助运放的本质是电流消去（原文自认 "based on cancellation"），失配残余 = 由 OTA 吸收的电流 = 非零虚地摆幅 = 混叠泄漏通道；并给出幅度失配（10/5/2% → 20/26/34 dB）与相位失配（fs 处 180° 精确反相要求、35° 相位差削弱收益）两维的完整刻画。P1 若主张"单级 τ 匹配是 G_DC≡0 的充要、多级梯形不再充分"，本文提供方法论模板：①消去条件的**带宽/频率条件**与幅度条件同等必要（p.241）；②失配→残余的映射可解析闭式（(1)–(3) 式一阶案例）；③"阶数无助于泄漏通道"（p.235/239 CIFB/CIFF 无关论）与"多级梯形不再充分"结构同型。**口径差异须声明**：本文对象是 STF/混叠抑制（时变采样通道），非 G_DC 共模差模转换。
- **P2（Kelvin 结构地板 ≈56 dB）**：中-高相关，须谨慎。"56 dB" 这一数字在本文 p.241 原文出现，但其语境是"无辅助时需 gm×50 才能达到 56 dB 混叠抑制"——**不是** Kelvin 结构地板，机理不同（OTA 带宽 vs 结构泄漏）。若 P1 论文的 56 dB 地板数值溯源自本文，属张冠李戴，应回查 P1 主张的 56 dB 原始出处（待核）。可作为数字撞车警示登记。
- **P3（平坦度约束衰减上界）**：中相关。p.240 "gm 翻倍只换 6 dB"是"参数化改善受结构上界锁死"的干净数值样本；p.234–235 表明隐式 AAF 的抑制深度受第一条运放有限带宽硬约束（20–30 dB 量级地板），即**任何滤波机制的衰减上界都由其泄漏通道决定**——P3 立论的领域内平行证据。
- **方法学（D1–D10）**：直接可用。①解析（状态空间精确解）→ 宏模型仿真 → 硅实测三级对齐的验证范式；②失配扫描实验设计（10/5/2% 三点 + 相位 35° 单点）是门槛化 D 系实验的直接模板；③对"常见信念"（higher order better / multistage OTA helps / SCR inherits CT advantages）逐条证伪的写法，与 D 系"逐门验证"同构。
- **killRisk 判断**：无新增风险，但**须登记一处数字撞车**：本文 56 dB（p.241，gm×50 语境）与 P2 主张的 ≈56 dB（Kelvin 地板语境）数值相同、机理不同——引用 P2 时若不慎将出处链到 Pavan，即构成失实归因；建议在 P1 论文中对 56 dB 加脚注区分。本文与 killRisk 条目（ti_threeguidelines2015 出处勘误）无交集。

## 没读到的

- 公式内符号/参数（(1)–(19) 的 τ、gm、fs 系数、G0=29/9 的定义式）：数学排版未入文本层，正文文字数值可用，精确定量复算需对照原刊（待核）。
- 参考文献 [14][15]（Pavan & Sankar, assisted opamp JSSC 2010 / ESSCIRC 2009）与 [12]（Liou 1972 精确分析法）原件未读——失配衰减因子 "on the order of [gms/gm]" 的精确推导在 [15]。
- Fig. 6–9、15–18 的曲线具体读数（仅正文给出的 20/21.5/30 dB 等锚点可引）。
