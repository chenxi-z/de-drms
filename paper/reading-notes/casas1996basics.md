# 精读笔记 · Casas & Pallàs-Areny 1996《Basics of Analog Differential Filters》（IEEE TIM 45(1):275–279）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> 页码用期刊页（275–279）；PDF 页 1–5 与之差 274（PDF p.2/3 页眉 OCR 误作 216/211）。**P0 级**：
> Hornero 2021 前作同组（Casas＝Serrano-Finetti 2019、Gasulla 2002 一系的源头），差分测量主线正典。

## 出处
- Casas, Ó., Pallàs-Areny, R., "Basics of Analog Differential Filters", IEEE Trans. Instrum. Meas., vol. 45, no. 1, pp. 275–279, Feb. 1996. doi:10.1109/19.481347.
- 本地：`H2-差分CMRR/casas1996basics.pdf`（5 页）。bib key：`casas1996basics`（literature.bib L1388）。
- 文本层公式丢失严重；eq(4)/(16) 已用页面渲染 + 数值自校核对（自校细节见各条注）。

## 核心命题（原文）

1. **差分滤波器 = 耦合两个单端滤波器；目的是把滤波推到差分放大器之前**（p.275）：
   > "We describe and analyze passive and active analog filters with differential input and differential output. They are implemented by coupling single-ended filters and provide very high common-mode rejection ratios. This makes it possible to place these filters before differential amplifiers, thus improving interference rejection and noise reduction."（Abstract, p.275）
   中文：把 AAF 放在差分链最前端（P1 的场景）而不牺牲 CMRR，靠的是"耦合"结构——本文全篇纲领。

2. **非耦合两路滤波器的消去条件 = H₁(s)=H₂(s)；一阶 RC 最坏情形 CMRR 有闭式**（p.275）：
   > "If we had H1(s) = H2(s), then CMRR = ∞, and the output voltage due to the input common-mode voltages would be zero. But, in practice, we will have H1(s) ≠ H2(s) and a finite CMRR."（p.275）
   > "If, for example, α = 1% and β = 5%, in order to ensure CMRR ≈ 60 dB, we need s' = 0.01. That is, the corner frequency for each filter should be 100 times larger than the signal frequency we accept to be attenuated by 3 dB. Such a filter would not be very effective for interference and noise reduction. We are interested in filters whose bandpass be dictated only by the differential signal, not by the CMRR we wish to obtain."（p.275）
   中文：**单级（一阶）非耦合双路的精确消去条件**以传递函数全等表述（一阶 RC 即 τ₁=τ₂）；最坏容差解析 eq(4)（文本层乱码，按图像+数值自校重构为 CMRR(d)=[1+(1+αβ)s′]/[2(α+β)s′]，s′=sRC，α 为 R 容差、β 为 C 容差——代 α=1%、β=5%、s′=0.01 得 841.7≈58.5 dB，与"≈60 dB"自洽；**分母系数 2 待核**）。非耦合路线的致命处：CMRR 需求反过来逼迫转角频率百倍于信号频率——滤波形同虚设。末句是 P3"平坦度约束衰减上界"的问题意识前身。

3. **四传递函数 C/D/E 体系 + "耦合只需两差之差小"**（p.276）：
   > "For an ideal differential filter, the aim is to obtain C = ∞, D = H(s), the desired transfer function for differential signals, and E = 0."（p.276）
   > "In general, however, by comparing (9) to (1) we see that, in order to have a large CMRR, if noncoupled stages are used, in (1) we need to match them, but in (9) we need only the difference between two differences to be small."（p.276）
   中文：承 Pallas-Areny 1991 四增益矩阵；耦合结构的 CMRR 只依赖"两个差之差"，匹配要求被结构性放松——P1 消去条件讨论必须区分这两种前提。

4. **【本文最接近 P1 的表述】耦合式（浮地公共点 P）一阶无源 RC：C=∞ 与元件容差无关**（p.276）：
   > "It is based on two single-ended filters that have been 'coupled,' that is, connected to a common point P that is not connected to ground. Obviously, a single capacitor C1/2 can be used, but we represent two separate capacitors for analysis purposes."（p.276，Fig. 3）
   > "From (9) we obtain C = ∞, irrespective of component tolerances. We can obtain the same result by circuit inspection, because in Fig. 3 there is no way a common-mode input signal can produce a differential output signal."（p.276）
   中文：**浮地耦合（两臂电容底端共接浮点 P）使共模激励下两输出节点电压恒等（可由浮点电荷守恒逐字证明），G_DC≡0 对任意 R、C 值成立**——比"τ 匹配"更强的全频段精确消去，且是拓扑性、免匹配的。这是与 P1 主张最邻近的既有结果；其成立前提（P 浮空、无对地分流）恰是 P1 所分析结构（每臂对地的梯形 AAF + SC 负载）不具备的——划界引用。

5. **耦合结构的多阶推广：把单端电路所有接地阻抗并为一个等效阻抗即可；有源版需匹配运放**（p.277）：
   > "Higher order filters can be implemented by coupling them through the connection of all impedances that go to ground in a single-ended filter (and substituting them by the equivalent impedance). Other filter circuits can be coupled in the same way."（p.277）
   > "By the same reason given for the filter in Fig. 3, the CMRR for the filter in Fig. 6 is infinite, provided we use matched op amps."（p.277）
   中文：**多阶（≥2 阶）无源耦合网络全频段精确消去的最近先例表述**——但只有"By the same reason"一句的定性断言（对称面/ Bartlett 式论证），无逐元件解析条件，也不覆盖"两条独立级联梯形"（P1 的对象）。有源版退化为"matched op amps"前提。

6. **级联合成：倒数相加，实测值由最差级钳位**（p.278）：
   > "From [2] we know that for cascaded differential amplifier stages the reciprocal of the CMRR for the system equals the sum of reciprocals of the CMRR for each stage."（p.278，[2]＝pallasareny1991cascaded）
   > "In practical terms, (26) means that the measured CMRR will approximately be equal either to the CMRR for the filter or the CMRR for the IA, whichever is lower."（p.278）
   > "We see that for coupled stages the CMRR is determined by the IA (and the differential gain for the filter) and is up to 55 dB larger than the CMRR for noncoupled stages. This is in agreement with the theoretically infinite CMRR for passive filters based on coupled stages."（p.278）
   中文：耦合滤波器实测 CMRR 被后级 IA 钳位——理想 C=∞ 落到实测 ~100 dB 级，与 P2"结构地板"的测量口径同题。

## 关键数值（原文）
- 非耦合一阶最坏情形（p.275）：α=1%、β=5% → CMRR≈60 dB 需 s′=0.01（转角=100×信号频率）；eq(4) 重构式 CMRR(d)=[1+(1+αβ)s′]/[2(α+β)s′]（**待核**）。
- 耦合一阶共模增益 E（p.276，eq(16)，图像核对）：E = ½·α(1−β²)·s′；"If, for example, component tolerances are α = 5% and β = 20%, |E| ranges from 2.4 × 10⁻⁵ when s' = 0.001 to 2.4 × 10⁻³ when s' = 1."（p.276；代 α=5%、β=20% 得 0.024·s′，与两数值自洽）
- 实验（p.278）：INA110AG IA，增益 500，CMRR 100 dB min @dc、100 Hz 起 −20 dB/dec；Fig.3 取 R=1 kΩ（α=5%）、C=150 nF（β=20%），f₋₃dB=1 kHz；耦合比非耦合实测最多高 **55 dB**；高通版加 R₂=10 MΩ 偏置：仍改善 50 dB、因 R₂ 损失 10 dB；Fig.5 有源等效阻抗电路再省 R₂ 可多 **9 dB**；有源 Fig.6（TL072，R₁=1.5 kΩ、R₂=5.6 kΩ、C₁=100 nF、C₂=33 nF，f₋₃dB=1 kHz）同样 50 dB；Fig.7（R=110 Ω/220 Ω、C=1 µF、R₃=10 MΩ）再 50 dB。

## 对 P1/P2/P3 的对照
- **P1（消去条件）**：相关度 **高**。本文给出三件直接对手材料：①非耦合双路的消去条件=H₁(s)=H₂(s)（一阶即 τ 匹配）＋最坏容差闭式 eq(4)——P1"单级 τ=R·C 匹配充要"的 1996 版前驱；②**耦合（浮点 P）一阶无源 RC 的 C=∞ 与容差无关**——拓扑性全频段精确消去的明确先例，**强于** τ 匹配；③多阶耦合"By the same reason"的推广断言（无解析）。killRisk 判定：**中-高（边界型）**——若 P1 的"单级 τ 匹配充要"明确限定于每臂独立对地回路（含 SC 负载）的非耦合/半耦合结构，Casas 不构成 kill，反而必须引用作对照；若 P1 把主张写成"任意单级无源双路网络都须 τ 匹配"，则 Fig.3 是现成反例。P1 的"多级梯形不再充分（R₁·C₂ 交叉项）"与 Casas 无冲突（其多阶走的是全耦合合并阻抗路线，不是独立梯形级联）。
- **P2（Kelvin 结构地板 ≈56 dB）**：相关度 **中**。非耦合路线在最坏容差下 CMRR 有限且随频率恶化（eq(4)），实测耦合结构受后级 IA（100 dB@dc、−20 dB/dec）钳位——"地板由链中最弱环节决定"（whichever is lower）与 P2 的链路合成口径一致；无 Kelvin 结构数值。
- **P3（平坦度约束衰减上界）**：相关度 **低-中**。"We are interested in filters whose bandpass be dictated only by the differential signal, not by the CMRR we wish to obtain"（p.275）是 P3 的问题原型（CMRR 约束反噬通带利用），但无定量上界。
- **方法学（D1–D10）**：耦合/非耦合二分法＋C/D/E 三因子＋级联倒数相加规则（引姊妹篇）——门槛化建模可直接沿用；"浮点电荷守恒→CM 输出恒等"的论证是 P1 证明风格的可借鉴模板。
- **killRisk 总评：中-高（边界型，必须引用划界，非推翻）**。

## 没读到的
- 多阶（≥2 阶）耦合结构 C=∞ 的解析证明/逐元件充要条件（只有一句定性断言）。
- 每臂独立对地回路的**多级级联**无源网络（P1 的梯形 AAF）消去条件与失配→CM 误差解析。
- 耦合结构在时变/开关电容负载（SC ΣΔ 输入端）下的行为——本文结构（浮空 P）在接负载后即失去"浮点"前提。
- 失配的统计处理（只做最坏情形）；温度/老化；差分滤波器的群时延/平坦度定量界。
