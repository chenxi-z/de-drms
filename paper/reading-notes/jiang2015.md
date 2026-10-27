# 精读笔记 · Jiang 2015《Dual-Mode Dual-Band Balanced Filter with High Differential-Mode Frequency Selectivity and Enhanced Common-Mode Suppression》（IEEE MTT-S IMS 2015）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
## 出处
- Jiang, Wei; Peng, Yujia; Wang, Guoan（University of South Carolina）；Shen, Wei（上海航天技术研究院微电子中心）
- 2015 IEEE MTT-S International Microwave Symposium, doi:10.1109/mwsym.2015.7166741
- PDF 共 3 物理页。全文已读（OCR 将 CM 识别为 "eM"、下标数字有噪声）。

## 核心命题（原文）
1. **CM 抑制来自 DM/CM 通带错位（misalignment），非失配消去**（p.1，摘要）：> "The presented dual-band balanced filter has inherent good eM suppression level within each DM passband because passbands of eM are misaligned with those of DM."（共模抑制机理 = 让 CM 谐振峰与 DM 通带错开，是结构频率规划手段；与 P1 的「元件失配→CM 误差」解析通道完全不同类。）
2. **物理对称性防 DM↔CM 转换（PEC/PMC 等效壁）**（p.2）：> "The whole structure is arranged symmetric with respect to the dashed line to prevent conversion between DM and CM signals. In that regard, a perfect electric conductor wall and a perfect magnetic conductor wall will be present along the symmetric line of the DOSLR under DM and CM excitation, respectively, as shown in Fig. 2(a)."（把「对称=模解耦」作为设计公理——理想对称下无 DM↔CM 转换；与 Bartlett/Forte 谱系「精确对称→理想抑制」同源思想，但本文不分析对称破缺后的残余转换量。）
3. **阶跃阻抗短截线错开两谐振器的 CM 二次谐波以加深抑制**（p.2）：> "In order to obtain a better CM suppression level of 20 dB in a relatively large range, covering from lower DM passband to upper DM passband, a stub is attached to the center of Resonator A to shift the second harmonic of resonator A away from that of resonator B."
4. **源-负载耦合产生有限传输零点，同时提升 DM 选择性与带内 CM 抑制**（p.2）：> "the controllable finite transmission zeros will not only improve frequency selectivity of DM response, but also enhance the suppression level of CM response within two desired DM passbands"

## 关键数值（原文）
- 实测样机：双通带中心 2.49 / 5.35 GHz（设计 2.4/5.2 GHz）；介质 εr=2.65, tanδ=0.003, h=1 mm（p.3）。
- 实测 DM 插损约 2.64 dB 与 2.58 dB；三个实测 DM 传输零点 2.75、5.0、5.5 GHz（p.3）。
- **实测 CM 抑制**（p.3）：> "The measured CM suppression level of 20 dB is observed from the lower to the upper DM passband. Specially, the CM suppression level is up to 50 dB within two DM passbands."
- 初始设计 CM 二次谐波处仅 10 dB 抑制（@3.75 GHz，p.2）：> "The CM second harmonic leads to an unsatisfied CM suppression level of 10 dB around 3,75 GHz."
- Table I 与 [3]–[7]、[8] 对比插损/CM 衰减/DM 传输零点数/尺寸（具体对比行 OCR 未能可靠读出，「待核」）。

## 对 P1/P2/P3 的对照
- **P1（无源差分网络失配→CM 误差解析条件）**：低。同属「无源差分滤波器」大类（微波微带平衡滤波器），但 CM 抑制机理是**通带错位+结构对称**，不处理元件失配→CM 误差映射，无 G_DC=H_N−H_P≡0 类条件、无 τ=R·C 匹配充要性讨论。可在 P1 相关工作中作「无源差分 CM 抑制的另一机理家族（频带规划）」一句话对照。
- **P2（Kelvin 结构地板）**：无。
- **P3（平坦度约束衰减上界）**：中低。其「在不劣化 DM 响应的前提下加深 CM 抑制」的叙事（stub 在 DM 激励下被短路，DM 响应不变：> "the DM response keeps unaltered as shown in Fig, 4 (a) because the stepped-impedance stub is short-circuited under DM excitation."）与 P3「平坦度约束下的衰减上界」问题同构（带内平坦/带外衰减的权衡），但本文无上界定理、纯数值设计。
- **方法学（D1–D10）**：无。
- **killRisk 判断**：无威胁。频段（GHz 微带）与机理（错位而非失配消去）均与 P1 四主张不同域；无解析重叠。
- 谱系定位：四层谱系之外（微波平衡滤波器线，Wu/Wang/Chen 2007 与 Shi/Xue 系）。

## 没读到的
- Table I 对比数值行（各文献 CM 衰减具体 dB）OCR 不可靠未引；Fig.5 实测曲线的 CM 全频段包络仅从文字拿到 20 dB/50 dB 两个值。
