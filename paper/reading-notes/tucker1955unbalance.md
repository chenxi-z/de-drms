# 精读笔记 · Tucker 1955《Unbalance Effects in Modulators》（Journal of the British Institution of Radio Engineers, 15(4), pp.199–207）

> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> 页码口径：所引页码为**期刊印刷页码**（PDF 第 1–9 页 = 印刷 p.199–207，逐页对应已核对）。
> 文件：`fulltext/H2-差分CMRR/tucker1955unbalance.pdf`；bib key `tucker1955unbalance`。

## 出处

- D. G. Tucker, "Unbalance Effects in Modulators," *J. British Institution of Radio Engineers*, vol. 15, no. 4, pp. 199–207, Apr. 1955. DOI 10.1049/jbire.1955.0024.（作者单位：H.M. Underwater Detection Establishment；手稿 1954-10-08 收到，印刷页 p.199 脚注）
- 主题：整流子调制器（shunt/"Cowan" 型与环形型）在不平衡时的输出分量分类、平衡电位器调整能力、以及信号电压对载漏的影响。属于电话载波/longitudinal balance 谱系（参考文献 5 Henkler 1948 为载波电话德文文献）。

## 核心命题（原文）

1. **不平衡分量可分类为"可平衡"与"不可平衡"两族，单个调整旋钮只能真正置零一个分量，但整族分量会同向变化**（p.199, Summary）：
   > "It is shown that in the shunt modulator only one balance control potentiometer is needed, and only one unbalance component can, in general, be brought to a real minimum by a particular adjustment; nevertheless, all the unbalance components tend to vary (and balance) together. In the ring modulator, two independent balance controls can be provided, and two (though not any two) unbalance components can be simultaneously brought to a minimum."
   （解释：一族谱分量共享一个平衡自由度——"整族一起平衡"是该文的中心经验结论，与 P1"单级 τ 匹配即可消去整条 G_DC"在结构上同源，但其对象是离散谱线而非连续频段。）

2. **实际高平衡度条件"通常相当复杂"，不平衡产物"非常多"**（p.199, Introduction）：
   > "However, the number of output components which are produced in an unbalanced modulator in addition to those produced in a perfectly balanced one is very large, and the conditions for attaining a high degree of balance in a practical modulator are usually rather complicated."
   （解释：开篇即承认精确平衡条件复杂——这是 P1 立论"精确消去条件苛刻"的 1955 年先声，但停留在定性陈述。）

3. **同一旋钮对"所有受控分量"同时最优是例外情形，仅当系统无电抗且器件差仅为固定电阻时成立**（p.202, §3）：
   > "It will be exceptional, of course, for the optimum settings of each potentiometer to be identical for all components controlled by it, since this would only occur if the system were non-reactive and the only difference between one rectifier and another were a fixed resistance which did not vary with the voltage across the rectifiers."
   （解释：**这是全文最接近 P1 消去条件的表述**——"全部谱分量同时精确平衡"需要非电抗（纯阻、无频率依赖）+ 失配为固定阻差这两个强前提；一旦元件特性随电压（类比：随频率）变化，单旋钮全消去即失守。与"多级梯形 τ 匹配不再充分"逻辑同构。）

4. **"全部产物同时消去"的显式系数条件及其"实践中难以满足"判语**（p.205, Appendix 1）：
   > "The condition for simultaneous balancing-out of all such products by means of a resistance adjustment is evidently cn1 − cn2 = constant for all values of n, where it is assumed that cn1 applies to rectifiers 1 and 4 and cn2 to rectifiers 2 and 3. If all four rectifiers are different the condition becomes cn1 − cn2 + cn3 − cn4 = constant. These conditions are unlikely to be met in practice."
   （解释：幂级数系数域的"全阶（all n）匹配"充要条件，且作者明言实践难满足——形式上就是"全阶/全频段精确消去条件"，但作用域是整流器非线性幂级数系数，不是线性时不变 RC 网络的传递函数差 G_DC(s)。下标 n1…n4 为 OCR 重构，公式形状已核对无误。）

5. **完全平衡的调制器不会因对称信号产生不平衡产物（与器件特性形状无关）**（p.203, §4）：
   > "If a modulator is perfectly balanced (i.e. has all rectifiers identical) in the absence of a signal, then the application of a signal of perfectly symmetrical waveform (i.e. positive and negative excursions identical) cannot cause unbalance products to be formed whatever the shape of the rectifier characteristics."
   （解释：理想对称（全同器件）下不平衡产物恒为零——即"完美匹配 ⇒ 精确消去"的方向性结论；P1 研究的恰是失配后何值仍可消去，此文只处理了完美匹配端点。）

6. **平衡电位器间的二阶互作用只在追求高平衡度时显现**（p.202, 脚注）：
   > "It should be noted that adjustment of RV1, by slightly redistributing the voltages across the rectifiers, does slightly change their resistances and so has a second-order effect on the adjustment of RV2. … These interactions show up in practice only when a high degree of balance is sought."
   （解释：多旋钮平衡并非独立正交——高目标下耦合显现，可作为 P3/方法学讨论"多自由度平衡耦合"的历史注脚。）

## 关键数值（原文）

- p.201（Fig. 2 图注 + 正文）：并联型实验，锗整流器；R = 1300 Ω；fc = 3 kc/s；fs = 300 c/s；Vc ≈ 0.6 V；fc±fs 输出 70 mV。正文："the output of 2fc ± fs was 1.15 mV and did not vary by more than ± 0.5 db over the range of potentiometer settings involved in Fig. 2."（"1-15 mV"为原文 OCR 连字符写法，即 1.15 mV）
- p.202（Fig. 4 图注）：环形调制器，锗整流器随机批次；R = 5 kΩ；fc = 3 kc/s；fs = 300 c/s；E/Vc ≈ 0.3；Vc = 0.5 V peak；fc±fs 输出 47 mV；四个受 RV2 控制的重要分量"optimum balances fairly close together, and tend to vary together"。
- p.203–204（Fig. 5）：铜氧整流器、fc = 3 kc/s 案例，初始载漏 8 mV；信号电压引起的载漏增/减方向随平衡点偏置侧而反号（p.204）："Although this type of result was often obtained, it was by no means the rule."
- p.204（§5 结论复述）：可平衡/不可平衡分量族列表——并联型可平衡 mfc ± 2rfs、不可平衡 mfc ± (2r+1)fs；环形型不可平衡 (2m+1)fc ± (2r+1)fs（m、r 为含零正整数）。
- **无任何 dB 计的 CMRR/共模抑制指标，无频率连续域的曲线**（Fig. 2/4/5 均为分量幅度对旋钮位置的描点图，仅图注数值可引用）。

## 对 P1/P2/P3 的对照

- **P1（消去条件）**：相关度**高（先例级）**。最接近表述 = p.205 "cn1 − cn2 = constant for all values of n … These conditions are unlikely to be met in practice" 与 p.202 "It will be exceptional … non-reactive and … a fixed resistance"。这是"全阶同时精确消去需强结构前提、且实践难满足"的明确先例；但作用对象是**调制器开关非线性幂级数系数**（离散谱分量意义下的平衡），**不是**无源 RC 差分滤波网络在连续频段 s 域上的 H_N−H_P≡0，也非多级梯形。方向上**支持** P1 的"精确消去苛刻"论断而非反驳。
- **P2（Kelvin 结构地板 ≈56 dB）**：**无**。全文无 Kelvin 四线结构、无 dB 口径的共模抑制地板。
- **P3（平坦度约束衰减上界）**：**无**。无衰减-平坦度权衡；最接近的只是"非电抗才可全消去"（p.202），未量化。
- **方法学（D1–D8 门槛化）**：相关度**低**。无 D1/D2/D3/D4/D8 对应数据；其方法论贡献是"用直流表监测载漏做平衡维护"（p.201 引文献 2）与"分量按可平衡性分类测量"的思路，不涉及门槛数值。
- **killRisk：低**。未给出任何"多级无源网络全频段精确消去条件"的连续域结果；其系数域全阶条件反可被 P1 引作"全频段精确消去需苛刻条件"的谱系先例（bib 注记"最近邻但不构成 kill"经本次全文核实成立）。

## 没读到的

- 连续频率域（s 域/傅氏域）的传递函数差恒为零的条件——全文平衡概念均建立在离散谱分量（mfc±rfs 族）上。
- 无源 RC 网络、多级梯形、Kelvin 结构的任何分析。
- CMRR/dB 口径的抑制比数值与频率特性曲线（载流实验数据以 mV 与 ±0.5 dB 变化量出现，非抑制比）。
- Fig. 2/4/5 曲线上的具体读数（扫描描点图，OCR 无法提取曲线内部数值，仅图注可引）。
- 附录公式 (2)/(3)、(6)–(11) 的下标细节存在 OCR 重排（dni/dn2/dn3/dn4 的下标数字无法逐字核verify），引用时以"公式形状+文字判语"为准；如需逐字符引用须回看扫描图（标 [OCR损] 处理）。
