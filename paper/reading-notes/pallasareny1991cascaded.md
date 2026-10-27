# 精读笔记 · Pallàs-Areny & Webster 1991《Common Mode Rejection Ratio for Cascaded Differential Amplifier Stages》（IEEE TIM 40(4):677–681）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> 页码用期刊页（677–681）；PDF 页 1–5 与之差 676（PDF p.1 页眉 OCR 误作 611）。**P0 级**：
> `pallasareny1991cmrr`（669–676，已有笔记）的同 issue 姊妹篇，级联 CMRR 合成规则的正典出处。

## 出处
- Pallàs-Areny, R., Webster, J.G., "Common mode rejection ratio for cascaded differential amplifier stages", IEEE Trans. Instrum. Meas., vol. 40, no. 4, pp. 677–681, Aug. 1991. doi:10.1109/19.85333.
- 本地：`H2-差分CMRR/pallasareny1991cascaded.pdf`（5 页）。bib key：`pallasareny1991cascaded`（literature.bib L690）。
- 文本层公式乱码；eq(21)–(23) 已用页面渲染核对，eq(14)/(15) 未核（见各条待核注）。

## 核心命题（原文）

1. **级联 CMRR 合成规则：等效 CMRR 倒数相加；每级等效 CMRR = C 因子 × 前面各级 D 因子之积**（p.677, 678）：
   > "We define two factors for each stage, C and D, and show that, in general, CMRRT can be calculated by adding the reciprocals of the equivalent CMRR for each stage, which we define as the product of its C factor and the product of D factors for the preceding stages."（Abstract, p.677）
   > "Whenever E_i << C_{i+1} and E_i << D_{i+1}C_{i+2} (i = 1, 2, 3), (9) simplifies to [1/CMRRT = 1/CMRR1 + 1/CMRR2 + 1/CMRR3] (10). Therefore, the total CMRR can be calculated by adding the reciprocals of the equivalent CMRRs for each stage."（p.678）
   中文：级联失配→CM 误差的**通用叠加方法学**；注意两前提条件（E≪C 等）——这是"多级误差如何合成"的权威口径，P1 讨论多级梯形误差积累时的必引规则。

2. **非耦合路径级：D=1、E=1/4C 与实现无关——单级两路失配全由 H₁、H₂ 之差决定**（p.678）：
   > "From here we see that for noncoupled paths we have D = 1, E = 1/4C, regardless of the particular implementation. Factors C and E depend on transfer functions H1(s) and H2(s)."（p.678）
   中文：非耦合级的 CMRR 行为只依赖两条路径传递函数之差——P1 的 G_DC(s)=H_N−H_P 在级联语境下的定理化表述。

3. **单级双路一阶 RC 失配的 C 因子解析（含 90° 相移、20 dB/dec 恶化）**（p.678）：
   > "Specifications for the DG507A model (Siliconix), for example, are Rs = 270 Ω, R1/R2 = 6%, Cs = 23 pF. C' is assumed to be zero. By applying (15), at 10 kHz we obtain C = j42735 = 92.6 dB/90°. Then E = −104.6 dB/−90°, and the assumptions leading to (10) will be correct even if the succeeding stage is far from ideal, i.e., its factor C is not very high. Note that for this stage CMRR = C, which has a 90° phase shift."（p.678）
   中文：差分多路复用器 = 两条独立一阶 RC（导通电阻×输出电容）；C 为纯虚数（分子实部 1 被分母 jωτ 除）→ CMRR 以 −20 dB/dec 随频率恶化、相位 90°。eq(15) 文本层乱码（**形式待核**：按数值自校 C≈(1+jωRC′)/(jω·Δ(RC))，42735=92.6 dB 与 20·log₁₀ 自洽）。

4. **输入失衡（源阻抗 R×共模输入电容 Cc）的 C 因子闭式：交叉差 R₂Cc₂−R₁Cc₁ 出现在分母**（p.679–680，eq(21) 已图像核对）：
   > C = [1 + s(R1Cc1 + R2Cc2)/2] / [s(R2Cc2 − R1Cc1)]　(21)（p.680）
   > "and a 10% imbalance (Cc1/Cc2 = 0.1), for example, would imply C = −10 + j/(0.1ωRCc)."（p.680；虚部系数文本层作 j/ωRCc、图像核对作 j/(0.1ωRCc)，**待核**；高频极限 C→−10 无歧义）
   > "In a similar way, when the problem is mainly one of source imbalance … In this case, C = −Ra/Ri + j/(ωRiCc)."（p.680，eq(23) 已图像核对）
   中文：**这是最接近 P1"失配→CM 误差解析"的既有闭式**——分子零点由两臂 τ 之和、分母由两臂 τ 交叉差构成；纯电容失配 10% → 高频 CMRR 地板 |C|→10（**20 dB**）；纯源阻抗失配 → 地板 |C|→Ra/Ri。"地板=失配比"的模式与 P2 同构（数值不同源）。

5. **探头容差路线的硬地板：10:1 探头要 CMRR>60 dB 需"极低容差"，必须加调整电阻**（p.679）：
   > "For a 10:1 probe, k = 9 and therefore the value for E will usually be low enough to accept (10), but at the same time we see that extremely low tolerances would be necessary to obtain a CMRRT, say, larger than 60 dB. This suggests the provision for resistor adjustment in probes intended for differential measurements, in addition to the common probe compensation trimmer capacitor."（p.679；eq(18) 最坏值重构为 C≤(1+k)/(4kt)，**待核**）
   中文：与姊妹篇 pallasareny1991cmrr 的 CMRRR=(k(1−t²)+1+t²)/4t 地板公式同族——容差路线的天花板论证。

6. **耦合路径级免电阻匹配（三运放 IA 输入级）**（p.680）：
   > "When the differential signal goes through 'coupled paths,' then D ≠ 1 and the relation between C and E depends on the circuit. This is the case for the input stage of the classical three-op-amp IA (Fig. 4). From [1] we obtain for this stage that (26) applies, regardless of the values for resistors R2 and R1, for reasonable differential gains, and without requiring resistor matching. Also, D = 1 + 2R2/R1."（p.680）
   中文：与 Casas 1996"耦合免匹配"同一论断的有源版（"regardless of the values for resistors … without requiring resistor matching"）。

7. **级联合成的复数部分相消陷阱：近似式之外还有相位问题**（p.681）：
   > "an input common mode voltage results in an equivalent input error voltage with the in-phase component attenuated by 85 dB and the out-of-phase component attenuated by 62 dB."（p.681）
   > "It is a bit surprising that now the result is worse than in the previous case, but this is a consequence of partial cancellations taking place when adding different terms. If we interchange the op-amp positions in stage 2 and also in stage 4, then the result is [−7.6×10⁻⁵ − j3.8×10⁻⁵]."（p.681）
   > "In any case, we see that the result is far from the 80 dB, −90° specified for the last stage. The degradation is mostly due to input stage imbalance, but in other situations a different stage can be responsible for it."（p.681）
   中文：倒数相加是复数相加的近似；误差项复数叠加可部分相消也可相长，器件摆位都能改变总 CMRR——P1 做 D 系门槛建模时必须用复数（幅+相）合成而非标量叠加的实证理由。

## 关键数值（原文）
- DG507A 差分多路复用器（p.678）：Ron=270 Ω、通道间失配 6%、Cs=23 pF；10 kHz 时 C=j42735（92.6 dB/90°）、E=−104.6 dB/−90°。
- 输入失衡（p.680）：电容失衡 10%（Cc1/Cc2=0.1）→ C=−10+j/(0.1ωRCc)（虚部系数待核），高频地板 20 dB；源阻抗失衡 → C=−Ra/Ri+j/(ωRiCc)，高频地板 Ra/Ri。
- 五级全链算例（p.681）：OP-27GP 对管 A1o=8×10⁵、A2o=3×10⁵，fd1=10 Hz、fd2=16 Hz，CMRROA1=106 dB、CMRROA2=94 dB（**106 dB 按上下文重构，文本层 OCR 为 "l6 dB" 待核**），fc1=fc2=1 Hz；C1=−5.2+j455、C2=−30−j1352、C4=C2、C3=−8.3+j8891、D4=21、C5=−j10⁴（末级 80 dB/−90° @10 kHz）；总结果同相 85 dB/正交 62 dB；仅 1、3、5 级时 1/CMRRT=−2.5×10⁻⁵−j2.3×10⁻⁵；交换 2、4 级运放位置后 −7.6×10⁻⁵−j3.8×10⁻⁵。
- 10:1 探头（p.679）：k=9；eq(18) 最坏 C≤(1+k)/(4kt)（重构待核）——t=1% 时约 48.9 dB，故"extremely low tolerances"才够 60 dB。

## 对 P1/P2/P3 的对照
- **P1（消去条件）**：相关度 **中-高**。给出单级两独立路径一阶网络（RC 一阶、RC·Cc 一阶）的 C 因子闭式（eq 15/21）＝"单级 τ 失配→CM 误差解析"的 1991 正典；eq(21) 分母正是**交叉差 R₂Cc₂−R₁Cc₁**，与 P1"多级梯形 R₁·C₂ 交叉项"同一数学形态（单级内两个 τ 的交叉差）。但**没有**多级无源网络全频段精确消去条件——其级联规则是"近似倒数相加"且显式给出适用条件与复数相消警告。killRisk：**低**（无消去条件主张，不构成推翻；但 P1 的单级解析必须与 eq(21) 对齐或引用）。
- **P2（Kelvin 地板 ≈56 dB）**：相关度 **中**。三条地板线索：容差探头 (1+k)/4kt（t=1%、k=9 → ~49 dB）；纯电容失衡 10% → 高频 20 dB 地板；源阻抗失衡 → Ra/Ri 地板。"地板由失配比决定、频率上翘后饱和"的完整模式与 P2 的 56 dB 同构——P2 章节可引为方法论先例（数值各自独立）。
- **P3（平坦度约束衰减上界）**：相关度 **低**。无平坦度-衰减权衡。
- **方法学（D1–D10）**：**直接蓝本**——四传递函数（p.677 定义段）+ C/D/E 三因子 + 等效 CMRR 倒数相加（含 E≪C 适用条件）+ 复数部分相消警示 + "whichever is lower"钳位直觉。P1 的门槛化若要处理多级合成，规则在此已穷尽。
- **killRisk 总评：低（方法学必引，主张不冲突）**。

## 没读到的
- 多级（≥2 级）无源网络的全频段精确消去条件——本文级联规则是近似误差合成，不是消去充要条件。
- 无源梯形 AAF / 开关电容 ΣΔ 输入端场景（对象是放大器级、多路器、探头、缓冲对）。
- 失配统计分布（只有最坏情形）；容差→CMRR 的二阶项。
- eq(14)/(15)/(18) 精确形式（文本层乱码未图像核对，已标待核）。
