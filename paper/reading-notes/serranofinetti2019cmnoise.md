# 精读笔记 · Serrano-Finetti, Casas & Pallàs-Areny 2019《Common mode electronic noise in differential circuits》（Measurement 140:207–214）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。

## 2026-10-27 原图复核与适用范围勘误（优先于下方历史解读）

- 已回看原文 p.208–210、Fig.3，并渲染核对 p.210 版面。Fig.3 左图的外部 Vcm 加在两输入共用连接端；右图 eni 是放大器输入等效噪声源，经不同源阻抗路径形成 en+、eni。二者注入位置/传递路径不同。
- 因而不能把该图概括成“同一外部端口下，确定性信号被精确消去，但随机性使同一共模源漏过”。对同一外部端口、完全相关的单一宽平稳输入和稳定 LTI 电路，Sout=|Gdc|²Sin；Gdc 恒零时该源的随机贡献也为零。这是线性系统分析，不是本文新增结论。
- 本文 Eq.(12) 的相关性模型可支撑噪声预算；p.210 明确限定白噪声闭式 Eq.(10)/(13)/(15) 不能直接用于有色谱。二阶/带通仅为作者预期，不能据此断言所有文献均无推广。
- 下方“P1 空缺主张安然”“多级空缺仍在”“无碰撞”等判断撤回。单篇未研究某问题不能证明整体创新性；当前须与 RC 综合、端接及比率测量近缘共同划界。

## 出处
- Serrano-Finetti, E.; Casas, Ó.; Pallàs-Areny, R., "Common mode electronic noise in differential circuits," *Measurement*, vol. 140, pp. 207–214, 2019. DOI: 10.1016/j.measurement.2019.04.028。
- PDF：`fulltext/H2-差分CMRR/serranofinetti2019cmnoise.pdf`（8 页）。bibkey：`serranofinetti2019cmnoise`。
- 主题：**共模"电子噪声"（随机噪声）在差分电路中的抑制**——提出 CMRR 只适用于确定性信号；建立双路径（一阶低通 H1、H2 + 减法级）共模噪声传播模型，定义噪声抑制因子 kNR 与谱相关系数 C12；证明"改善 CMRR 的同一组参数匹配条件决定共模噪声抑制，但 CMRR 对失配敏感得多"。

## 核心命题（原文）
1. **CMRR 不适用于随机噪声，需要新参数（论文动机）**（p.207, Abstract）：
   > "Differential circuits are assumed to reject common-mode noise yet no parameter is available to describe that rejection as the Common Mode Rejection Ratio (CMRR) applies only to deterministic signals, not to random noise. We propose a model and a method to analyze the contribution of the input common-mode electronic noise to the output voltage noise of differential circuits."
   > "The analysis shows that the same parameter-matching conditions that improve the CMRR determine common-mode noise rejection but CMRR is more sensitive to mismatching."（Abstract, p.207）
2. **差分电路 CMRR 的频域定义就是"平均值/两倍差值"——H1−H2 结构（P1 的 G_DC 同构体）**（p.209, 式 20）：
   > "For a differential circuit like that in Fig. 1, where the two signal paths in the first stage are independent from each other, according to [14,15] we have,  CMRR(f) = [H1(f) + H2(f)] / [2(H1(f) − H2(f))].   (20)"
   （引 [14]=Casas & Pallàs-Areny 1996 "Basics of analog differential filters"（本库已有 casas1996basics.pdf）与 [15]=2007 实测方法文。**分母 H1−H2 即 P1 的 G_DC=H_N−H_P**；本文把它写成 CMRR 倒数形式而非消去条件对象。）
3. **一阶双路径模型的精确消去条件：直流增益相等 + 增益带宽积相等（单级充要，P1 基线命题的既有表述）**（p.209）：
   > "that is a complex parameter whereas kNR is a real number. A perfect CMRR requires G1 = G2 and G1f1 = G2f2, which are the same conditions that yield kNR = 1."
   （对 H1=G1f1/(f1+jf)、H2=G2f2/(f2+jf)：H1−H2≡0 ⇔ G1=G2 且 G1f1=G2f2——即"增益相等且极点（τ）相等"，**单级 τ 匹配充要**在此以一句话形式出现（承 Casas 1996 谱系）；**但全文止步于一阶，无多级/梯形推广定理**。）
4. **失配容忍度惊人：±20% 容差也有 82% 噪声功率抑制；CMRR 低到 8 dB 仍够**（p.207/209）：
   > "For example, a low-frequency CMRR as low as 8 dB implies that more than 82% of common-mode noise is rejected. Thus, often only differential-mode noise is relevant."（Abstract, p.207）
   > "If we assume, for example, ±20% manufacturing tolerances (tG = tf = 0.2) we obtain C12 = 0.98 and kNR = 0.82, which is quite good. Similarly, ±5% tolerances yield C12 = 0.99875 and kNR = 0.9975, which is excellent."（p.209）
   （C12 = sqrt(1−t²f)·sgn(G1)·sgn(G2)，式 11, p.209；只依赖带宽失配不依赖增益失配。）
5. **CMRR 无穷大 ≠ 共模噪声被拒（消去与噪声解耦的关键反例）**（p.210, Fig. 3）：
   > "The differential circuit in Fig. 3 (left), for example, comprises an unbalanced fully-differential low-pass filter connected to a differential amplifier. Since there is no return path for common-mode currents, the filter's CMRR will be infinite and Vcm will not contribute to the output voltage. However, the input common-mode voltage noise eni will propagate differently to the inverting and non-inverting inputs (Fig. 3, right) yielding a low C12, hence a low kNR, and it will contribute to the output voltage noise."
   （必须保留端口差别：外部 Vcm 与放大器等效输入噪声 eni 经过不同路径；不能把出噪声归因于随机性本身。滤波器例子为定性图示。）
6. **高阶情形只是断言可推广、未推导（P1 空缺主张未被触碰的直接证据）**（p.210）：
   > "Nevertheless, the conclusion that differential circuits largely reject input common-mode electronic noise even if gain and signal bandwidth are so poorly matched that the CMRR is low, can be expected to remain true. The same can be said if the frequency response of the circuit is band-pass instead of low-pass, or is second order instead of first order."
   （"二阶/带通同结论可期"——**无推导、无多级梯形、无全频段精确消去条件**；一阶之外全部搁置。）
7. **设计推论：无源前端按"只管差模噪声"设计，大电阻放共模位置**（p.210）：
   > "any passive front-end for differential circuits should be so designed that differential noise is reduced disregarding possible common-mode noise increases, because this last noise will be rejected."
   > "Large resistors in Zi and Zi' would yield differential-mode noise ..., whereas Zb will produce only common-mode noise."（p.210, Fig. 4 偏置网络）

## 关键数值（原文）
- 模型式：E²no = E²n1 + E²n2 − 2C12·En1·En2（式 12, p.208）；kNR = 4G1G2f1f2/[(G1²f1+G2²f2)(f1+f2)]（式 15, p.209）；容差式 kNR = (1−t²G)/[1+(tG+tf)²/(1−t²f)]（式 16, p.209）；CMRR(0)=1/(2tG)（式 22）、CMRR(∞)≈1/[2(tG+tf)]（式 23）、GBW 匹配时 kNR = 1−1/[4·CMRR(0)²]（式 24, p.209）。
- 实验 1（OP270 差放，外注入白噪 100 mV/2 V rms，0.1 Hz–100 kHz，Table 1 p.212）：case 1 CMRR(0)=11、kNR=0.99719、Eno,m=55.8 mV（对 Eu=1183.5 mV，降 95%）；case 2 CMRR(0)=70（好 7 倍）只把抑制提高到 98.5%（36 mV vs 2402.9 mV）（p.211）；case 4（G1=1、|G2|=10，CMRR(0)=0.6，带宽 462 kHz/4824 kHz）预测 C12≈0.56、kNR=0.33，实测 300 mV→251 mV（≈30% 功率抑制）（p.211）。
- 实验 2（单片 IA + 大电阻 Rb，34401A 6½ 位表、100 次读数标准差、5 Hz 带宽，Table 2 p.213）：INA114（Rb=10 MΩ, G=10, CMRR(0) 106 dB typ）Enb=2.45 mV、Enc=2.70 mV、End=2.41 mV、Ene=6.98 mV；AD627（Rb=55 MΩ, G=45, 100 dB）0.38/0.36/0.46 mV、Ene=8.80 mV。由式(12)估 in+/in− 相关系数 **−0.57（INA114）/−0.23（AD627）**，10 片样本落在 −0.1～−0.6（p.212）。
- 器件：OP270 GBW=5 MHz 典型；AD627 的 Ene < En（噪声地板）提示其内部噪声源交叉相关更强（p.212）。

## 对 P1/P2/P3 的对照
- **P1（消去条件）**：相关度 **高**（本批仅次于 Bockelman 的划界重要性，实为 P1 最贴身的模型文献）。
  ① 式(20) 的 CMRR = [H1+H2]/[2(H1−H2)] 正是 P1 的 G_DC=H_N−H_P 取倒数（承 Casas 1996 谱系，本库已有可串读）；
  ② p.209 一句话给出**一阶双路径的精确消去条件（G1=G2 且 G1f1=G2f2）**——即 P1"单级 τ 匹配充要"的既有文献表述，P1 必须引用并注明出处在此非自己首创；
  ③ p.210 对二阶/带通仅作预期，未给相应闭式；这只界定本篇覆盖，不能证明整体 P1 空白；
  ④ 额外贡献：消去（CMRR）与噪声抑制（kNR/C12）的解耦（Fig. 3 无穷 CMRR 反例），P1 可引为"精确消去条件 ≠ 全部故事"的佐证。
  **killRisk 判断：须划界**——单级条件已有；多级与有色谱问题的新颖性须联合核查其他前作。
- **P2（Kelvin 结构地板）**：相关度 **低**。无开尔文/四线；但 Fig. 3"无共模回流路径 ⇒ CMRR=∞"的结构性消去思想与 P2 的"结构优先于匹配"论调同族。
- **P3（平坦度约束下衰减可达上界）**：相关度 **无**。带宽只作一阶极点参数出现，无滤波器综合约束。
- **方法学（增量四 D1–D10）**：相关度 **中**。其实验设计正是**受控增量失配**：case 1–3 递进增益组 + case 4 故意大失配（tG=0.816, tf=0.832），预测值（Eno,t）对实测值（Eno,m）逐例对照；10 片器件样本报相关系数区间。这是 D1–D10 增量四方法学的直接同型实验（失配增量→输出增量→模型验证），可作为方法学先例引用。
- **killRisk 判断（汇总）**：**须划界**。最接近 P1 的两处表述（式 20 + p.209 单级充要句）已逐字锁定；未发现任何"多级无源网络全频段精确消去条件"的表述或逼近。其引文链 [14][15][22][23]（Casas/Pallàs-Areny 差分滤波器与 AC 耦合网络系列）是 P1 谱系的必查上游，本库已藏 casas1996basics、pallasareny1991cmrr、pallasareny1991cascaded 三篇，建议下一批精读。

## 没读到的
- 多级（二阶以上/梯形）差分网络的消去条件——明确只有"可期同结论"的断言（p.210）。
- 有色噪声（1/f）下的解析式（式 10/13/15 明示不适用，p.210 只说结论可保持）。
- 差分滤波器自身的共模→差模传递函数推导（Fig. 3 的滤波器例子是定性图示，无公式）。
- kNR 与 CMRR 的一般换算关系——文中明说"no simple equation relates kNR and CMRR"（p.210）。
- 增益容差与带宽容差对 C12 的不对称性（C12 只含 tf）仅对白输入噪声明；非白谱时未展开。
