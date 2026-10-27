# 精读笔记 · Bulger 1975《Stability analysis of laser trimmed thin-film resistors》（IEEE Trans. PHP-11, p.172；本文档为其 1976 年摘要页）

> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> ⚠️ **文档形态声明**：本地 PDF（`lasertrim1976.pdf`，1 页）**不是论文全文**，而是 *World Abstracts on Microelectronics and Reliability*（Microelectronics Reliability, Vol. 15, 1976）第 26 页的**摘要汇编页**，其中收录了 Bulger 1975 原文的摘要。全部可引内容 = 该摘要（约 120 词）+ 同页其他无关条目。** bib 作者「(作者待补)」据摘要页可补为 Gary A. Bulger（待用户确认后更新 literature.bib）**。

## 出处

- 原文：**Gary A. Bulger**, "Stability analysis of laser trimmed thin-film resistors", *IEEE Trans. Parts, Hybrids, and Packaging*, PHP-11, p.172 (1975)。
- 本地文档：Microelectronics Reliability, Vol. 15 (1976), p. 26（DOI 10.1016/0026-2714(76)90124-4 即此摘要页），Acrobat 3.0 Capture 2002 年 OCR 扫描；摘要归入 "8. THICK- AND THIN-FILM COMPONENTS, HYBRID CIRCUITS AND MATERIALS" 类目。
- bib key：`lasertrim1976`（H2 轴尾——激光修调工艺的**时漂代价**证据：修调买来初始匹配、付出老化速率）。

## 核心命题（原文，全部出自 p.26 摘要，OCR 将 kerf 误作 "kerr"，照录并注）

1. **核心发现：修调过的薄膜电阻比未修调的老化更快**（p.26）：
   > "Laser trimmed tantalum nitride thin-film resistors age at a greater rate than untrimmed films. The high energy required to vaporize material in the cut, or kerf [原文 OCR 作 'kerr'], modifies the aging characteristics of film contiguous to the kerf."
   （激光修调是 Wurcer 1982 那类 ±0.01% 比值匹配的工艺来源；本句给出其代价——切缝邻近膜层老化特性被改坏，**t₀ 时刻的匹配会随寿命发散**。）

2. **建模内容：寿命末期漂移 ↔ 修调深度，两部分区域老化模型**（p.26）：
   > "In this paper a model is developed that relates end of life drift to the extent of laser machining. Experimental data are used to obtain an aging model for material near the kerf and that parallel portion which is more remote."

3. **边界不必精确定义即可表征复合体（鲁棒性表述）**（p.26）：
   > "It is found that precise definition for the boundary between these areas is not essential to complete characterization of the composite. The result is a graphical design procedure that assures laser trimmed resistors will meet end of life tolerance specifications."

4. **L 切位置优化：切在电阻条中点即近最优**（p.26）：
   > "The analysis was extended to determine the position of 'L' cuts in bar resistors yielding optimum lifetime stability. It was found that trimming with an 'L' cut at the midpoint of the resistor results in acceptably small deviations from maximum stability."

## 关键数值（原文）

- 摘要为定性内容，**无任何数值**（无老化速率、无温度、无失配百分比）。原文 PHP-11 p.172 起的实验数据未含于本摘要页（全文未取得）。

## 对 P1/P2/P3 的对照

- **P1（消去条件 G_DC(s)=H_N−H_P≡0）**：中相关（工艺-时间维）。证据链拼图：Wurcer 1982 用激光修调拿到 ±0.01% 比值匹配 → 80 dB 地板；Bulger 1975 证明**被修调的电阻本身老化更快**（切缝热损伤区 + 远区两段老化模型）⇒ 修调建立的匹配是 t₀ 快照，配对两元件（切缝图案/位置各异）按各自模型发散，G_DC≡0 在时间轴上必然破坏。P1"精确消去只在标称点成立"由此获得**工艺物理机理**支撑（热损伤 → 微观结构改 → 老化速率差）。注意口径：摘要未直接讨论"配对失配"，只讨论单体老化，配对发散是合成推论（引用时须声明）。
- **P2（Kelvin 结构地板 ≈56 dB）**：中相关。地板的"工艺匹配供给端"证据：修调精度决定地板初值（Wurcer 链），修调的时漂决定地板的**寿命期退化**——56 dB 类地板若依赖修调匹配，须按 end-of-life tolerance 预算（Bulger 的 graphical design procedure 正是"保证寿命末期公差"的设计法）。
- **P3（平坦度约束衰减上界）**：无。
- **方法学（D1–D10）**：中。①"end of life tolerance specifications"= 把失配预算按寿命末端而非出厂时刻定义——D 系门槛化应有的时间维口径；②图形化设计程序（graphical design procedure）= 工程可用的失配预算图解法先例；③"L 切中点近最优"展示了修调版式本身是设计自由度。
- **killRisk 判断**：无风险。与 killRisk 条目（TI 2015 博客出处勘误）无交集。

## 没读到的

- **原文全文**（IEEE Trans. PHP-11, 1975, p.172–）：老化模型公式、实验数据、图形设计程序本体、TaN 膜具体参数——全部未读到（本地仅摘要页）；如需定量引用必须另取全文（待核）。
- 同页其余摘要（反应键合金膜导体、厚膜材料评价、Ni-Cr 蒸发膜等）与本题无关，未引。
