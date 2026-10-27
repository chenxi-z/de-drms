# 精读笔记 · Gao 2010《Anti-aliasing Filter Circuit Design for Active Power Filter》（IHMSC 2010）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> H1 轴"配方线"标准样本：APF 前向通道 AAF 的**"指标→阶数→传递函数→元件值"全链条配方**（四阶 Butterworth + MFB 电路）。
> 其通带衰减指标恰为 **0.5 dB**——与 P1 方法学 D4 门槛同值，可作行业惯例佐证；
> 但通篇无失配分析（唯一一处隐含匹配假设：令电阻两两相等来凑单位增益）。

## 出处
- Zhengzhong Gao, Zhifeng Sang, Xu Zhang, Songmei Zhang（山东科技大学等）, "Anti-aliasing Filter Circuit Design for Active Power Filter," *2010 Second International Conference on Intelligent Human-Machine Systems and Cybernetics (IHMSC)*, pp. 147–150. DOI: 10.1109/IHMSC.2010.44。
- 本地文件 `fulltext/H1-ΣΔ-AAF/gao2010ntialias.pdf`，4 页。**页码换算**：PDF p.1–p.4 = 期刊 pp.147–150（抽取文本中的 151/152/153 为公式/图幅碎片，非页码）。原文含较多数学排版转写噪声（µF→"PF"、Ω→":"），引用按原意复原并注明。

## 核心命题（原文）
1. **配方定位：重点在"如何算元件值"，验证靠 Multisim 仿真**（p.147, Abstract）：
   > "adopting low-pass Butterworth filter as the prototype, and using Multiple-Feedback architecture. The implementation of actual circuit to meet the established specifications was represented. And how to calculate the circuit-component values required was focused on . To test the design results, simulation was performed using the software, Mutisim, afterwards. This circuit had been applied in practice and played a perfect anti-aliasing filtering part."
2. **AAF 的双面要求 = 清除 fs/2 以上分量 + 保证低频分量"几乎无衰减"通过**（p.147, I–II）：
   > "On the one hand, the circuit is to restrict the bandwidth of the signal by clearing up any high-frequency component above ωs/2 completely. Thus, it turns out to be a piece of cake to satisfy the Nyquist sampling condition for proper sampling and actual prevention of spectral aliasing. But on the other hand, the anti-aliasing filter ought to minimize its adverse effects on the low-frequency components, which are so significant and informative that the filter should ensure their safe passage with slight attenuation scarcely."
   （平坦度—衰减两面性的教科书式陈述；"a piece of cake"的口吻亦见配方文风。）
3. **指标三件套（配方输入）：fp=2.5 kHz（国标 A 级 0–2500 Hz、50 次谐波）、Ap=0.5 dB、fs=12.8 kHz → 阻带边 fs/2=6.4 kHz、As=20 dB**（p.148, III.A–D）：
   > "According to Chinese National Standard for harmonics in public supply network, the frequency range of measuring instruments classified A was from zero to 2500 hertz [5]. Therefore, the pass-band edge frequency of low-pass Butterworth filter was designed at 2.5kHz, assuring the safe passage of harmonics below 50 times."
   > "To guarantee the slight attenuation of useful components passed by the filter, set the maximum pass-band attenuation denoted Ap to be 0.5dB."
   > "the analog signal in single channel of active power filter was sampled 256 times per power-frequency period throughout the data acquisition; that is, the sampling frequency just was fs = 50×256 = 12.8kHz. Thus, the stop-band edge frequency of low-pass Butterworth filter should be less than or equal to fs/2."
   > "To make sure of eliminations of all high-frequency components above 6.4kHz contained in the analog signal, and perfect effects of anti-aliasing filter, the minimum stop-band attenuation of low-pass Butterworth filter denoted AS was set 20dB."
   （注意：**Ap=0.5 dB 与 P1 方法学 D4 的"≤0.5 dB"同值**——0.5 dB 通带口径在应用配方线中是通行惯例；As=20 dB 则远低于 D1/D3。）
4. **阶数公式与结果：N ≥ 3.57 → 四阶**（p.148, IV.A）：
   > "ksp = sqrt[(10^0.1Ap − 1)/(10^0.1As − 1)] = 0.035 and Ωps = Fp/Fs = 0.391, and the order of low-pass Butterworth filter to be designed should meet the following formula: N ≥ log10 ksp / log10 Ωps = 3.57 … From above, it drew a conclusion that all given targets could be realized by a fourth-order filter."
   （式(3)；上标/根号按原式复原。归一化传递函数 G(p)=1/[(p²+0.7654p+1)(p²+1.8478p+1)]，式(6)；−3 dB 截止 fc=3.38 kHz，式(4)(5)。）
5. **隐含匹配假设：令电阻两两相等（R11=R31、R12=R32）以获得单位通带增益**（p.149, IV.D）：
   > "Setting R11 R31 and R12 R32 yielded Kp1 Kp2 1; thus the overall gain of fourth-order filter circuit in pass-band was Kp Kp1 × Kp2 1."
   （这是**通道内元件匹配假设**——用"设相等"直接令增益为 1，未分析容差下的增益偏差；P1 所指"配方给匹配条件但不给偏差预算"的原文级实例。）
6. **元件值配方（MFB 双二阶级联）**（p.149, IV.D）：
   > "Setting C11 = 1200 pF, C12 = 1500 pF … Therefore, choose R11 R21 R31 R1 10kΩ and R12 R22 R32 R2 20kΩ. Afterwards … C21 = 0.018µF and C22 = 3900 pF … R41 = 15kΩ and R42 = 30kΩ."
   （R41/R42 为运放同相端补偿电阻，R41 = 1.5·R1 = 15 kΩ、R42 = 1.5·R2 = 30 kΩ；四阶 = 两个二阶 MFB（Multiple-Feedback）节级联，图 2/图 3。）
7. **仿真结果与"元件精度"归因（唯一的精度相关表述，无量化）**（p.150, IV.E）：
   > "The results in Tab. 1 implied that the designed anti-aliasing filter circuit achieved a maximum pass-band attenuation about 0.65dB, a minimum stop-band attenuation up to 23dB, and a cutoff frequency about 3.3kHz, all of which conformed well to calculating data. The given specifications had been satisfied. But the only fly in the ointment was that the filter's maximum pass-band attenuation was a little bigger because of virtual components' unsatisfactory feature and precision primarily."
   （实测通带衰减 0.65 dB > 规格 0.5 dB，却称"conformed well / satisfied"——**自相矛盾的验收口径**；把偏差归因于"虚拟元件精度"但零容差分析。）

## 关键数值（原文）
- 规格：fp = 2.5 kHz（GB A 级 0–2500 Hz，50 次谐波）；Ap ≤ 0.5 dB；fs = 50 Hz×256 = 12.8 kHz；阻带边 6.4 kHz（=fs/2）；As ≥ 20 dB（p.148）。
- 阶数：ksp=0.035、Ωps=0.391 → N ≥ 3.57 → **四阶**；fc（−3 dB）= 3.38 kHz（p.148）。
- 传递函数系数（p.148 式(7)）：k1=4.7111×10⁻⁵、k2=3.6059×10⁻⁵、k3=8.7051×10⁻⁵（经 p=s/Fc 反归一代入）。
- 元件值（p.149）：第一节 C11=1200 pF、C21=0.018 µF、R11=R21=R31=10 kΩ、R41=15 kΩ；第二节 C12=1500 pF、C22=3900 pF、R12=R22=R32=20 kΩ、R42=30 kΩ；通带总增益 Kp=1。
- Multisim 结果（p.150, Tab. 1）：最大通带衰减 ≈0.65 dB、最小阻带衰减 ≈23 dB、fc≈3.3 kHz；表格采样点：2.467 kHz → −0.625 dB；2.529 kHz → −0.705 dB（**超 0.5 dB 规格**）；3.330 kHz → −3.107 dB；6.220 kHz → −21.567 dB。

## 对 P1/P2/P3 的对照
- **P1（G_DC=H_N−H_P≡0 消去条件）**：相关度 **低（旁证）**。单通道前向链路、无差分两路、无失配预算；唯一触碰"匹配"处是命题 5 的"设电阻相等得单位增益"——**匹配被当作恒等式假设而非需论证的条件**。这正构成 P1 的反面教材：配方线连通道内的增益匹配都不做偏差分析，遑论两路 H_N/H_P。
- **P2（Kelvin 结构地板）**：相关度 **无**。
- **P3（平坦度约束下衰减可达上界）**：相关度 **中**。给出完整的"平坦度指标（0.5 dB）+ 衰减指标（20 dB@fs/2）→ 最低阶数（N≥3.57→4）"定量链（Butterworth 阶数公式），即**给定双指标反推实现代价（阶数）**——与 P3"平坦度约束下衰减可达上界"同属一个权衡空间的工程解；但其"上界"由理想 Butterworth 解析式给出，**不含元件容差修正**（仿真 0.65 dB 超差即其现实代价的冰山一角）。
- **方法学（D1–D4/D8）**：**Ap=0.5 dB 与 D4 同值**（佐证 D4 门槛的行业惯例性）；As=20 dB << D1（80 dB）/D3（100 dB），说明功率谐波场景的抗混叠强度需求远低于 P1 的 ΣΔ 前端场景；无共模内容（D8 不适用）。
- **killRisk**：**无**。不冲击 P1/P2/P3；引用价值：①D4 的 0.5 dB 惯例佐证；②"配方无失配预算"的原文实例（命题 5、命题 7）。

## 没读到的
- 元件容差对 Ap/As/fc/Q 的敏感性分析——零（仅一句归因"virtual components' precision"，p.150）。
- 通带衰减仿真 0.65 dB 超规格 0.5 dB 仍判"满足"的判据——未解释（验收口径矛盾，照录）。
- 运放型号、带宽、压摆率、噪声（图 3 电路用理想运放仿真）——未给。
- 相频/群时延的定量评估（图 5b 仅给相位曲线图，无群时延数据；APF 控制回路对相位本应敏感，见 zamaruiev2019）。
- 实际应用效果数据（结论称"practically applied…perfect harmonic suppression"，无实测数字）。
- 与采样保持/ADC 输入阻抗的接口考量——零讨论。
