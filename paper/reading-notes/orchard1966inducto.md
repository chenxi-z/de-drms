# 精读笔记 · Orchard 1966《Inductorless Filters》（Electronics Letters 2(6):224–225）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> 页码用期刊页（224–225）；PDF 页 1–2 与之差 223。Electronics Letters 经典信札（Orchard 定理出处），
> 同页还有 Chaput 等（Toulouse）与另一则 modulator 信札——引注时勿混。

## 出处
- Orchard, H.J., "Inductorless filters", Electronics Letters, vol. 2, no. 6, pp. 224–225, June 1966. doi:10.1049/el:19660190.
- 本地：`H2-差分CMRR/orchard1966inducto.pdf`（2 页）。bib key：`orchard1966inducto`（literature.bib L1482）。

## 核心命题（原文）

1. **RC 有源滤波器对容差的灵敏度远劣于 LC—— gyrator 替代电感是"近似最优"解**（p.224）：
   > "Attempts to produce inductorless filters with RC-active networks lead to circuits which are very much more sensitive to component tolerances than conventional LC filters. An alternative, and apparently optimum, solution is merely to replace each inductor in a conventional doubly loaded LC filter by a gyrator-capacitor combination."（p.224）
   中文：无源（或无源等效）双端接梯形对容差的本质优势由此定型——P1 选无源梯形做 AAF 的理论合法性源头之一。

2. **【核心定理】双端接无损网络的零一阶灵敏度：通带内每个频率、每个元件的损耗对容差的一阶导数为零**（p.224）：
   > "If one designs a flat-passband reactance ladder filter to operate from a resistive source into a resistive load, and arranges that, at the frequencies of minimum loss over the passband, the source delivers its maximum available power into the load, one finds, to a first order of approximation, that, at every frequency in the passband and for every component, the sensitivity of the loss to component tolerances is zero. This is easily checked by noting that, when one has zero loss in a reactance network, a component change, either up or down, can only cause the loss to increase; in the neighbourhood of the correct value, the curve relating loss to any component value must therefore be quadratic, and, consequently, d(loss)/d(component) must be zero."（p.224）
   中文：最大可用功率传输 ⇒ 损耗处于极小值 ⇒ 一阶灵敏度为零、误差只剩二阶项——"极值论证"模板（P1/P3 灵敏度论证可复用的证明风格）。

3. **灵敏度差距的量级：同指标下 LC 允许容差约 100 倍，难滤器超 10³ 倍**（p.224）：
   > "The sensitivity of an RC-active filter increases rapidly with the degree and sharpness of the filter characteristic, whereas, in an LC filter, it gets worse only by virtue of second-order effects becoming noticeable. In the LC equivalents to the bandpass filters described by Kinariwala and Sipress, for example, the component tolerances allowable for the same quality of passband are about 100 times greater. For difficult filters, this factor may easily exceed 10³."（p.224）
   > "They are excellent designs of their class, and yet they require components stable to within about one part in 10⁴ to achieve a passband constant to within 0.1 dB."（p.224，指 Kinariwala/Sipress 的 12–16 kc/s 与 16–20 kc/s RC 有源带通）
   中文：定量锚点——RC 有源要 10⁻⁴ 稳定度才换 0.1 dB 通带恒定；且**灵敏度随滤波器阶数与选择性急剧上升**（RC）对比 LC 只受二阶效应拖累。P3"平坦度-衰减权衡"的历史参照数值。

4. **去敏性质的适用范围限定：单端接与预失真补偿网络没有此性质**（p.224）：
   > "Our ability to make high-quality filters meeting stringent specifications relies heavily on this desensitising property which occurs at zero loss in a doubly loaded reactance network. It may be noted, in passing, that this property does not occur in either singly loaded or predistorted dissipation-compensated filters, which accounts for why such networks are not widely used."（p.224）
   中文：零一阶灵敏度的**拓扑前提 = 双端接 + 无损**——对 P1 的启示：任何"无源天然低敏"论断必须核对这个前提是否成立（接 SC 时变负载即偏离经典前提）。

5. **实现路径与关键工艺约束：Q=500 需 g=1000e；负电阻补偿路线要求 <1% 临界平衡——正是要避免的**（p.224）：
   > "The solution is to design a conventional doubly loaded LC ladder filter to meet the specification, and simply replace each inductor in the filter by a gyrator terminated by a capacitor. This gyrator-capacitor network, like the LC network, is dissipationless and passive, and has exactly the same low sensitivity."（p.224）
   > "The equivalent inductance of a capacitively terminated gyrator is L = C/g², and thus it is at least as stable as a 'real' inductor."（p.224）
   > "Assuming that both principal diagonal terms in the admittance matrix are equal at e, and that one uses a perfect capacitor, the maximum Q factor obtainable from the equivalent inductance is [Qmax=g/2e，式样文本层不完整**待核**]. A Q factor of 500 thus demands g = 1000e."（p.224）
   > "One would have to maintain a critical balance to better than 1% between positive and negative resistances, and this is just what we want to avoid."（p.224）
   中文：靠"临界平衡换性能"的路线被显式否决——与 P1 的立场（不靠可调平衡换 CMRR，而是给出消去条件与门槛）同气相求。
6. **实验验证（p.225）**：
   > "Our first experiments in this direction have been very successful, and a direct replacement of the inductors in a sharp seventh-degree filter has verified the expected low sensitivity."（p.225）

## 关键数值（原文）
- Kinariwala/Sipress RC 有源带通：12–16 kc/s、16–20 kc/s；**1 part in 10⁴** 稳定度 → 0.1 dB 通带恒定（p.224）。
- 同指标容差余量：LC 约 **100 倍**；难滤器 >**10³ 倍**（p.224）。
- Gyrator 等效电感 L=C/g²；Q=500 ⇒ g=1000e（即对角项 e 须小于 g 的 1/1000）（p.224）。
- 负电阻平衡路线要求 **better than 1%** 的正负电阻临界平衡（p.224）。
- 验证对象：sharp seventh-degree filter（p.225）。

## 对 P1/P2/P3 的对照
- **P1（消去条件）**：相关度 **无/低**。全文不涉及差分、共模、CMRR 或消去条件——纯单端网络灵敏度理论。killRisk：**无**。
- **P2（Kelvin 地板）**：相关度 **无**。
- **P3（平坦度约束衰减上界）**：相关度 **中**。P3 的问题结构（通带平坦度 ↔ 可用衰减/选择性的权衡）在这里以"灵敏度"形态出现：双端接无损梯形的平坦度对失配只做二阶响应（"quadratic"），且选择性提高不放大一阶误差（对比 RC 有源"increases rapidly with the degree and sharpness"）——P1 若要论证"无源梯形 AAF 的平坦度在高选择性下仍可预算"，Orchard 是奠基引文；若 P3 的上界与 Orchard 的二阶误差论断有张力（例如 P1 上界比二阶紧），须显式讨论。
- **方法学（D1–D10）**：可借鉴的是论证模板——用"极值点一阶导为零"证明去敏性质，以及"把性能依赖从临界平衡挪到结构性质"的设计哲学。
- **killRisk 总评：无（不同问题；P3 的理论根基引文）**。

## 没读到的
- 差分/共模/CMRR 的任何内容（本信札完全单端）。
- 滤波器衰减与平坦度的定量权衡界（只有灵敏度定性论断 + 两个量级数字）。
- 参考文献所引 Darlington 1939、Tellegen 1948 等原始合成文献的细节。
- Qmax 公式的精确形式（文本层残缺，已标待核）。
