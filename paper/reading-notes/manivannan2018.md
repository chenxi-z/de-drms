# 精读笔记 · Manivannan 2018《Degradation of Alias Rejection in Continuous-Time Delta–Sigma Modulators by Weak Loop-Filter Nonlinearities》（IEEE TCAS-I）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> H3 轴定位：**逃生门不完美的正典实测证据**。Pavan 组发现：时不变环路的 CT-ΣΔ 理论混叠抑制 ~160dB，实测只剩 ~70dB——退化 90dB 的元凶是输入 OTA 的**弱非线性 × 寄生电容**（输入与 DAC 反馈波形的平方项混频）。对 P1 而言：残余量由**元件级参数（g₃、c₁、c₂、α）显式决定**，且"加阶数/换架构无用"——这正是"消去条件的元件条件"在 CT-ΣΔ 上的完全同构物。

## 出处
- Manivannan, Saravana; Pavan, Shanthi, "Degradation of Alias Rejection in Continuous-Time Delta–Sigma Modulators by Weak Loop-Filter Nonlinearities," *IEEE Transactions on Circuits and Systems—I: Regular Papers*, 2018. DOI: 10.1109/tcsi.2018.2826443.
- **终版出处**（据姊妹篇 ISCAS 2019 参考文献 [6]）：**vol. 65, no. 10, pp. 3207–3215, Oct. 2018**。
- 所读 PDF 为 **early-access 版**（页眉 "accepted for inclusion…with the exception of pagination"），正文 9 页无终版页码；本篇引用页码 = PDF 页 1–9（与终版 pp.3207–3215 的对应关系未逐页核对，正式引用建议换算或按终版页码）。
- 文件：`fulltext/H3-CT-ΣΔ/manivannan2018.pdf`。作者单位 IIT Madras。

## 核心命题（原文）
1. **弱非线性 + 寄生 = 隐式抗混叠大幅退化（摘要定调）**（p.1）：
   > "Implicit anti-aliasing is a remarkable property of continuous-time delta–sigma modulators employing a time-invariant loop filter. It turns out that weak nonlinearity of the operational transconductance amplifier (OTA) used in the input integrator, in conjunction with the DAC pulse shape and OTA parasitics can greatly degrade the alias rejection of the modulator."
   > "The alias-rejection of the modulator, which is expected to be about 160 dB, is degraded to around 70 dB by weak OTA nonlinearity and OTA parasitics."

2. **时间变环路（SC DAC / RTO DAC）直接毁掉隐式抗混叠**（p.1）：
   > "For a long time, it was assumed that the implicit anti-aliasing was a characteristic of all CTΔΣMs. It turns out, however, that this holds only when the loop filter is time-invariant [1]–[3]. Using switched-capacitor DACs (to achieve reduced jitter sensitivity [4]) or return-to-open DACs (to achieve immunity to inter-symbol interference [5]) make the loop filter time-varying and result in a severe degradation of the modulator's alias rejection."
   （**对现代商用 CTSD（含 ADI 教程类器件）最致命的一条**：为降抖动灵敏度普遍采用的 SC DAC 恰恰使环路时变——商用「逃生门」的混叠抑制天然带伤。）

3. **发现过程：90dB 差距无法用已知非理想解释**（p.1–2）：
   > "We were characterizing a filtering CTΔΣM whose (theoretical) alias rejection was expected to be about 160 dB. Strangely, measurements indicated a rejection of only about 70 dB, which is about 90 dB worse than expected. This could not be explained by any of the nonideal effects (like switch mismatch and clock non-overlap) that can also cause alias rejection problems [3]."

4. **单效应不致命、两效应共谋才致命（互为条件的元件条件）**（p.2）：
   > "We see that the rejection of the CTΔΣM around fs degrades (on average) by about 60 dB, solely due to the effect of weak nonlinearity in the OTA. Interestingly, if the parasitic capacitance c1 is set to 0, the alias rejection is restored to that with a linear OTA (in spite of the fact that the OTA is weakly nonlinear). Thus, the degraded alias rejection is the result of nonlinearity and parasitic capacitance."
   （g₃=0 或 c₁=0 任一为零即恢复理想——退化项 ∝ g₃·τ/c… 的乘积结构，与 P1 的 G_DC=H_N−H_P 残余"须两路同时失配"完全同构。）

5. **根因 = 输入与 DAC 波形平方项的混频下变换**（p.4）：
   > "The root cause for this is the mixing of the input (u(t)) and the squared DAC feedback waveform. The latter has a component at fs, which when multiplied by the input (also a tone at fs), yields dc."
   （NRZ DAC 在虚地上的波形 v̂₁² 含 fs 分量；与 fs±Δf 输入相乘降频到 Δf——混叠不走"采样折叠"而走"非线性混频"通道。）

6. **加阶数/换架构救不了（架构级免疫失效）**（p.4，**对 P1/P3 最关键**）：
   > "The analysis that lead to (8) did not make any assumptions on the order or architecture of the modulator. This means that in the presence of weak nonlinearity of the OTA, increasing the order of the CTΔΣM or choosing a loop-filter architecture with an inherently better rejection around fs (e.g. CIFB instead of CIFF) does not help."
   （一旦混频通道主导，Keller 2007 的"阶数封顶"资源全部失效——逃生门的天花板由元件参数而非拓扑决定。）

7. **多比特/FIR 反馈按 M² 改善（有代价）**（p.7）：
   > "From the equation above, it is seen that all else remaining unchanged, using a multibit quantizer or FIR feedback improves alias-rejection by a factor of M²."
   > "In practice, however, the improvement will be somewhat smaller due to the following. Since the current supplied by the OTA in a multibit modulator is smaller than that in a single-bit design, the quiescent current in the second stage of the OTA will be smaller. As a result, gm2 and gm3 will be smaller, somewhat reducing the antialiasing benefit to be had with multibit operation."
   （缓解手段存在但要花 M² 倍阶数/功耗筹码，且实际收益打折。）

8. **实测确认：退化 ~90dB = 四个数量级以上**（p.9）：
   > "We see that weak nonlinearity of the input OTA has degraded the rejection by about 90 dB, corresponding to more than four orders of magnitude. Further, our estimate is in good agreement with measurements."
   > "The measured alias-rejection of the filtering CTΔΣM was degraded by about 90 dB due to weakly nonlinear effects."

## 关键数值（原文）
- 理论预期 vs 实测混叠抑制：**~160 dB → ~70 dB（退化 ~90 dB）**（p.1 摘要、p.9 实测）。
- 单级 OTA 三阶 CIFB 仿真：平均退化 **~60 dB**；fs=128 MHz、OSR=64、R=10 kΩ、gmR=20、Vref=1.2 V、c₁=250 fF、g₃/gm=5 V⁻²、μ=0.7（p.2、p.4）。
- 两级前馈 OTA 仿真：gm1R=8.8、gm2/gm1=10.5、gm3/gm1=12.3、**g₃/gm1=70 V⁻²**、c₁=250 fF、c₂=1.28 pF；退化时间常数 τ₂≈c₂gm3/(gm1gm2)，**c₂ 贡献主要退化**（p.5–6）。
- 测试芯片：**65 nm CMOS**、四阶单比特滤波型 CT-ΣΔ（内嵌二阶 Rauch/Butterworth、2 MHz 截止）、信号带宽 1 MHz、fs=128 MS/s、**动态范围 80 dB**、8-tap FIR DAC、有源面积 0.62 mm²（p.2、p.8）。
- 芯片 OTA 参数（晶体管级+版图寄生提取）：c₁=164 fF、c₂=394 fF、gm₁/gm₂/gm₃=440/1150/1350 µS、**g₃=30.8 mA/V³**、α=0.045（p.8）。
- 式 (7)/(8)：STF(fs)/STF(0) = 12g₃μVref²τ / [gm(2+gmR)³Ts]，分解为 (τ/Ts)×[虚地衰减]×[OTA 非线性注入] 三因子（p.4）；两级版式 (12)（p.6）；多比特/FIR 版式 (13) 含 M² 因子（p.7）。
- 旁证他人芯片：Philips 2004 [8] 实测 |STF@fs| ≈ **−70 dB**，按架构计算应优于 **−110 dB**（p.4）。
- FIR DAC 情形 μ=0.5（长 FIR 输出 M 拍近似不相关）、单比特小直流输入 μ≈0.7（p.4、p.7）。

## 对 P1/P2/P3 的对照
- **P1（G_DC=H_N−H_P≡0 元件条件）**：相关度**高**。本文给出 CT-ΣΔ 侧最完整的"残余=元件条件显式函数"案例：退化 ∝ g₃·(τ/Ts)·[Vref/(gmR+2)]²，且**任一因子归零即恢复理想**（第 4 条引文）——与 P1"消去须两路同时满足条件、单一失配即残余"的逻辑同构。式 (8) 的三因子分解可直接类比 G_DC 的参数化写法。P1 论文引它作"对消/免疫机制的残余由元件参数决定"的权威先例。
- **P2（Kelvin 结构地板 ≈56dB）**：相关度**无**（无 Kelvin 内容）。注意勿把本文实测 ~70 dB 与 56 dB 地板混为一谈——机理完全不同（非线性混频 vs 结构几何）。
- **P3（平坦度约束衰减上界 ≈76dB<80dB）**：相关度**高**。同一认识论结构：**理想线性理论承诺的抑制（160 dB）被物理（弱非线性）砍掉 90 dB**；且"加阶数/换架构无用"（第 6 条引文）与 P3"两阶理想也只到 76dB"同属"理想资源封顶+现实再砍"的双重限制叙事。
- **方法学（门槛化、D3@16.384MHz≥100dB 最难关）**：相关度**中高**。① **电流注入法**（current injection，引 Bussgang [6]/Pavan [7]）分析弱非线性 ΣΔ 的套路可移植到 P1 的 G_DC 推导；② 流程范式：晶体管级+版图寄生提取 g₃/c₁/c₂ → 解析式预测混叠抑制 → 硅后实测对账（"estimate is in good agreement with measurements"）——即**下带前预测门槛**，P1 的 D3 关卡可沿用此验证结构。
- **killRisk**：**低**。本文是 P1 必要性的正面弹药：逃生门（CT-ΣΔ 隐式抗混叠）在元件非理想下退化 90dB 且架构不可救——外置 AAF 链路的 RC 匹配问题没有被 CT-ΣΔ 免除。防反咬点：若对手称"用线性 OTA/多比特/FIR 即可恢复"，回应 = 第 2 条（SC DAC 时变毁伤，商用主流恰是 SC DAC）+ 第 7 条（M² 筹码与 gm 缩水打折）。

## 没读到的
- 终版期刊卷期与页码（所读为 early-access，**待核**；引文格式建议按 DOI 引）。
- Fig. 3/6/10/12/15 各曲线的逐点 dB 数值（图内数据，文本只给均值级结论）。
- SC DAC 情形的退化定量（本文只处理阻性 NRZ DAC + 时不变环路；SC DAC 细节在引文 [1] Pavan 2011 "Alias rejection of CT ΔΣ modulators with switched-capacitor feedback DACs"，若 P1 需要商用 CTSD 的 SC-DAC 残余公式须另读该文）。
- 测试芯片 SNDR/低频 STF 测量（作者声明另文发表，本文只给混叠抑制）。
