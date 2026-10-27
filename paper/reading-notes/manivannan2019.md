# 精读笔记 · Manivannan 2019《Degradation of Alias Rejection in Continuous-Time Bandpass Delta-Sigma Converters due to Weak Loop Filter Nonlinearities》（IEEE ISCAS 2019）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> H3 轴定位：Manivannan & Pavan 2018（TCAS-I，低通版）的**带通姊妹篇**。价值有二：① 证明弱非线性混频退化机理**跨架构普适**（低通/带通同公式形）；② 带通特有增量——谐振器振铃（fs/4）使虚地波形更复杂，但退化公式形式不变。对 P1：又一次"残余 ∝ 非线性系数 × 寄生参数、任一为零即恢复理想"的元件条件案例。

## 出处
- Manivannan, Saravana; Pavan, Shanthi, "Degradation of Alias Rejection in Continuous-Time Bandpass Delta-Sigma Converters due to Weak Loop Filter Nonlinearities," *2019 IEEE International Symposium on Circuits and Systems (ISCAS)*, 2019. DOI: 10.1109/iscas.2019.8702763.
- ISCAS PDF 无印刷页码，本篇引用页码 = **PDF 页 1–5**。
- 文件：`fulltext/H3-CT-ΣΔ/manivannan2019.pdf`。IIT Madras。
- 重要副产品：本文参考文献 [6] 给出低通版终版出处——**TCAS-I vol. 65, no. 10, pp. 3207–3215, Oct. 2018**（已回填 `manivannan2018.md` 笔记）。

## 核心命题（原文）
1. **带通 CT-ΣΔ 的隐式抗混叠同样被弱非线性摧毁（摘要）**（p.1）：
   > "We show that the nonlinearity of the first integrator's operational transconductance amplifier (OTA) significantly degrades the alias rejection of a bandpass CT∆ΣM in the presence of OTA parasitics."
   > "As we show in this work, it unfortunately turns out that the alias rejection of a bandpass CT∆ΣM can be greatly degraded by weak nonlinearity of the input OTA and its associated parasitics."

2. **理想情形：NRZ DAC 带通 CTΔΣM 在 fs/4 处本应有无限混叠抑制**（p.1）：
   > "with an NRZ feedback DAC, in principle, should therefore have infinite alias rejection at fs/4 (and high alias rejection in the signal band)."
   （理想线性模型的承诺是"无限"——为后文实测级别的退化（~80dB）提供落差基线；逃逸门叙事的极端版本。）

3. **机理与低通版相同：输入 × DAC 波形平方项混频**（p.2）：
   > "It turns out that due to the third order nonlinearity, g3vx1³, the CT∆ΣM's input component mixes with the square of the component of the DAC waveform at the virtual ground node. The former is a tone at 5fs/4 which mixes with the fs component of the latter to give the alias tone at fs/4."
   （5fs/4 输入 × v̂g²(t) 中的 fs 分量 → fs/4 混叠音；与 2018 低通版（fs×fs→dc）完全同构，只是频点搬移。）

4. **退化量级：六阶带通也挡不住 ~80dB 退化**（p.2）：
   > "Clearly, we see that the alias rejection has degraded by about 80 dB."
   （期望 ~160 dB → 实际 ~−71 至 −74 dB；**六阶**高阶环路仍被弱非线性打穿——再次印证"阶数不是护身符"。）

5. **非线性的"位置条件"：第一级 OTA 是要害，第二级可忽略**（p.2、p.4）：
   > "Macromodel simulations were run with nonlinearity in the input resonator's second OTA (gm1 in Fig. 1(a)). The first OTA (gm0) is linear in this case. The simulated alias rejection is around 115 dB. So the degradation due to nonlinearity in the resonator's second OTA is small compared to the first."
   > "the degradation in alias rejection due to nonlinearity in the resonator's second OTA (in Fig. 1) is negligible."
   （输入级转移函数是带通、5fs/4 输入在第二级 OTA 处已被强烈衰减——**非线性在哪一级决定残余大小**，又一个"位置/元件条件"。）

6. **联合条件结构：c₂ 寄生仅在 gm₁ 非线性存在时才致退化**（p.4）：
   > "Thus the parasitic capacitance c2 degrades the alias rejection of the bandpass CT∆ΣM only in the presence of gm1 nonlinearity."
   （与 2018 版"g₃ 或 c₁ 任一为零即恢复理想"一致的乘积结构——P1 消去条件的直接类比。）

7. **带通特有修正：谐振器振铃使 v̂₁(t) 含 fs/4 正弦分量**（p.3）：
   > "In band-pass CT∆ΣMs, the virtual ground node does not settle to zero at the end of one sampling period... The virtual ground voltage, thus sees an oscillatory response, typical of any second order system. The oscillation frequency is fs/4, which is the resonant frequency of the tank."
   （带通版需把 v̂₁ 分解为 glitch 分量 + fs/4 振铃分量处理；最终只有 û·v̂g² 项落入混叠频点。）

8. **结论：机理普适、公式封闭形式与仿真吻合**（p.4）：
   > "The alias rejection in a bandpass CT∆ΣM can be severely degraded by the OTA nonlinearity in the presence of parasitic capacitances. We showed that the mechanism of degradation is the mixing of the input component with the square of the DAC component at the virtual ground node of the OTA."

## 关键数值（原文）
- 例设计：六阶 CIFF-B 带通 CT∆ΣM、OSR=64、fs=128 MHz、信号带宽 1 MHz、中心 32 MHz（=fs/4）、NTF OBG=1.5、单比特、NRZ DAC、输入电阻 R=8 kΩ（p.2）。
- OTA 参数：gm₁=880 µS、gm₂=9.24 mS、gm₃=10.82 mS、**g₃/gm₁=70 V⁻²**、c₁=250 fF、c₂=1.28 pF；µ≈0.7（p.2、p.4）。
- 期望混叠抑制 **~160 dB** → 实际退化 **~80 dB**；图 3 曲线在混叠带附近约 **−71 / −72.5 / −74 dB**（p.2 图注数据）。
- 仿真 vs 解析式 (3) 差异 **< 2 dB**（p.4）。
- 非线性放第二级 OTA：抑制 ~**115 dB**（退化小，p.2）。
- 闭式公式 (3)：STF(5fs/4)/STF(fs/4) = 12g₃µαVref²τ₂ / [gm₁(2+gm₃R)²Ts]，τ₂≈c₂gm₃/(gm₁gm₂)（p.4）——与 2018 低通版式 (12) 同形（仅频点替换）。
- 多比特：DAC 步长 ÷M ⇒ v̂g² ÷M² ⇒ **混叠抑制按 M² 改善**（p.4）。
- Fig. 6：c₂ 从 0.4–1.4 pF 扫描，抑制约 −65 至 −90 dB（图中数据，趋势 = c₂ 越大越差）。

## 对 P1/P2/P3 的对照
- **P1（G_DC=H_N−H_P≡0 元件条件）**：相关度**高**。与 2018 低通版构成**跨架构重复验证**：同公式形、同"任一因子归零即恢复理想"乘积结构（第 6 条）、且新增"非线性位置条件"（输入级 vs 第二级，第 5 条）。P1 引用这对姊妹篇可主张"残余由元件参数及其位置显式决定"是 CT-ΣΔ 领域已确立的规律，而非孤例。
- **P2（Kelvin 结构地板 ≈56dB）**：相关度**无**。
- **P3（平坦度约束衰减上界）**：相关度**中**。"无限抑制（p.1）→ 退化 80dB、六阶亦然"再一次展示理想线性理论的承诺与物理现实的落差；但本文不含 P3 所需的衰减-带宽资源权衡内容。
- **方法学（门槛化、D3）**：相关度**中**。电流注入法在带通情形的适配（振铃分解近似、卷积简化假设）示范了**近似假设显式声明 + 解析式 + 仿真对账（<2dB）**的验证纪律；式 (3) 这类"残余 = 元件参数闭式"正是 P1 期望对 G_DC 给出的产品形态。
- **killRisk**：**低**。纯支持性文献；无 P1 反证风险。注意它与 2018 的分工：若 P1 只引一篇，引 2018（TCAS-I 期刊全文+实测芯片）；2019 作"带通普适性"补强。

## 没读到的
- ISCAS 版无印刷页码；终版收录卷期页码（若 IEEE Xplore 分配）待核。
- Fig. 3 / Fig. 6 曲线逐点数值（仅图中标注了三个 dB 值与坐标范围）。
- 环路延迟/额外半拍延迟对带通退化的影响（本文未处理）。
- 与 2018 版重复的推导细节被省略（"Proceeding along the same lines as in [6]"）——需 2018 版式 (12) 才能完整复现。
