# 精读笔记 · Li 2018《Filter Selection for Optimizing the Spectral Sensitivity of Broadband Multispectral Cameras Based on Maximum Linear Independence》（Sensors 18(5):1455）

> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> 读法：pdftotext 逐页；页码 = 期刊页 "X of 17"（PDF 页 = 期刊页）。⚠️ 本 PDF 内嵌预印本水印层（部分页有 "Sensors 2018, 18, x" 双层重复文本，p.5/7/12/13 明显），引用均已取正式层。
> 定位：**H4 选型方法学靶子**——一篇专门做「从商业货架元件集合中选型」方法学的论文，检验「多目标选型是否存在解析框架」的现状（C 级证据）。

## 出处

- Sui-Xian Li（滨州学院飞行学院）, "Filter Selection for Optimizing the Spectral Sensitivity of Broadband Multispectral Cameras Based on Maximum Linear Independence," *Sensors*, 2018, 18(5), 1455. DOI: 10.3390/s18051455. Received 2018-02-26 / Accepted 2018-05-04。
- 本地全文：`fulltext/H4-选型方法学/mdpi2018_filterselection.pdf`（17 页）。
- ⚠️ **bib 题录勘误**：`literature.bib` 的 key `mdpi2018_filterselection` 写题名 "…Multispectral Imaging Systems"、作者 "Li, J. and others"；PDF 实际题名是 "…Multispectral Cameras **Based on Maximum Linear Independence**"，作者是**独著 Sui-Xian Li**（非 Li, J.）。建议改 bib。

## 核心命题（原文）

1. **选型方法学的两大流派分类（本文的领域地图）**（p.2）："There are two kinds of algorithms for filter selection. One is the filter vector analyzing method (FVAM). The FVAM is used for selecting a filter set directly from a large number of filters by considering the mathematical features of the filters without considering other imaging parameters… The other is the systematic recursion method (SRM), which searches exhaustively for an optimal filter set among all the combinations of a commercial available filter collections in terms of the results of spectrometric and/or colorimetric recovery [4–6,10,12]. The SRM is time-consuming because it requires a large amount of data acquisition and reconstruction, while the FVAM is more straightforward and can be conducted only by simple vector analysis of the filters."（**向量特征法（快但代理指标）vs 系统递归穷举法（准但昂贵）**——这个两难正是「无解析框架」的现状结构）
2. **MLI 的核心 = 透射矩阵条件数最小**（p.2）："The insight of the MLI method is the transmittances matrix of the selected filter set featuring a minimum condition number. The MLI method was verified to outperform other vector analysis methods such as maximizing the orthogonality in the vector space of the transmittances of broadband filters [3,11]. However, the limitation of the tradition MLI method is defined by the `2 norm of the transmittance vector of the first filter being the maximum among all those of the filters to be selected."（传统 MLI 需预设首个滤波器为最大 ℓ2 范数——**为保首通道 SNR 的启发式，非系统最优**）
3. **多指标评价无共识单一度量（H4 空白的直接证词）**（p.6）："However, it is a disputed question for a single competent metric evaluating both the performances of color reproduction and spectra reconstruction."；"Imai et al. concluded that there is no consensus metric that can been recommended as conclusively superior to others for all purposes [25]. López-Alvarez, et al. constructed a simple single-cost metric CSCM that combined several metrics at once, but it is designed for evaluating daylight spectra recovery by a simulated annealing algorithm [26]. In most cases, several evaluation metrics are adopted separately such as PNSR, GFC, CIEDE2000, MSE and so on… Despite the fact the metrics are roughly consistent with each other, perceptible conflicts of such indices exist because of the differences in their corresponding definitions."（**四指标（PSNR/GFC/MSE/CIEDE2000）彼此大体一致但存在可感知冲突；无人能给出普适单一代价函数**）
4. **最优集的几何特征（仿真归纳，事后描述）**（p.15 结论）："Besides a smaller condition number of the best-performing filter set, the geometric features comprise a distinct peak of the transmittance of the first filter, a generally uniform distribution of the peaks of the transmittance curves of the filter sets, and substantial overlaps of the transmittance curves with those of the adjacent filters. The geometric features of the best-performed filter sets can be quantified by the two metrics, UF and OLP."（首片峰明显 + 峰位均匀分布 + 相邻片充分交叠；量化指标 UF（峰位均匀度）、OLP（交叠度）为**事后归纳的几何描述**，非从目标函数推出的解析条件）
5. **方法学自白：直观、难以操作（H4 靶眼）**（p.13）："However, the methodology is intuitive and still difficult to operate in practice. The reasons are two-fold. The first is that the best-performing filter set is not always the one with the smallest condition number, as it have been shown in Tables 4 and 7, and Figure 7. The other is that the characteristics of the transmittance curves of the filter set are too intuitive to be handled quantitatively. Therefore, we recommend two steps to resolve the problem."（**代理指标（条件数）非充分 + 几何判据难量化 → 只能退到两步经验流程**）
6. **两步推荐流程（最终交付物）**（p.13–14）："The first step is to select a subset of the filter sets with smaller condition number from the entire filter sets… the condition numbers of the best-performing filter sets are almost the closest to the smallest; the maximum deviation is seen for the No. 38 filter set, of which the condition number is smaller than about 89% of other 40 filter sets. Namely, if the subset of filter sets is composed by the five filter sets with the smallest condition number, we can decide the best-performed filter set is in it."（p.14）"The second step is to select a filter set among the subset in terms of the geometric distribution of its transmittance curves or by a few experimental explorations… Because of the number of the filter sets in the subset is less than five according to the typical case in this article, it should be an efficient way."（**先用条件数筛出 ≤5 个候选，再靠几何直觉或少量实验挑出**——筛选必要不充分，最后一步是试）
7. **指标冲突的实操解法 = 打分排名（ad hoc）**（p.8）："Another applicable method to decide explicitly which filter set is more optimal is a score ranking method. The score ranking method is designed like this: let the first filter series in Table 1 have the highest score of 9, the second have 8 and so on, then we can get the cumulative scores of the filter sets… Consequently, if there is not just one filter set series sharing the same maximum frequency, the score ranking method should be irreplaceable."（频率计数 + 名次加权打分——**纯排名启发式，无权重理论依据**）

## 关键数值（原文）

- 元件库：Hoya 色玻璃 45 片单滤光片 → 可用透射向量 K=1035（单片 + 两片叠合，式(6)，p.3–4）；"It would not be practical if the number of the filters stacked up to form a filter combination were larger than 2 due to larger thickness and smaller transmitted energy of rays."（p.3）
- 仿真规模："2250 groups of results from the imaging simulation"（p.6；45 首滤片 × 5 通道数(4–8) × 10 噪声档(SNR∈{∞,50,47,43,40,37,33,30,27,23} dB)）；光谱数据 Macbeth ColorChecker 24 块、400–700 nm 61 采样点、186,240 体素（p.4）
- 条件数（Table 4，p.10）：最优系列 No.44/45/38 在 4–8 通道下条件数 1.37–3.91（除 No.38 八通道异常 92.35、No.44 八通道 20.34），传统选法 No.2 系列 5.84–13.99；"the condition numbers of the best filter sets are less than four, although the condition numbers are not always the minimum for the best-performed filter set"（p.9–10）
- 性能增益（Table 3，p.9，6 通道，No.44 vs 传统 No.2）：50 dB 噪声下 PSNR 45.72 vs 43.30；40 dB 下 40.56 vs 34.37；30 dB 下 **32.46 vs 25.53（≈7 dB）**；GFC 30 dB 下 0.9139 vs −0.0465
- 几何量化（Table 5，p.12）：最优集 UF（峰位均匀度，式(11)，UF=1 为完美均匀）= 0.937–0.984；OLP（交叠度）= 0.094–0.176
- 光源鲁棒性（Table 6 vs Table 2，p.13）：换 CIE A 光源后 4/6/7/8 通道最优集不变、仅 5 通道从 No.38 变 No.16；"the criteria for selecting a filter set to optimize the spectral sensitivity of broadband camera would be insensitive to varying the imaging parameter"（p.13）
- No.38(5 通道) 全噪声档 PSNR（Table 9，p.15）：∞→43.2 dB … 23 dB→25.6 dB

## 对 P1/P2/P3 的对照

- **P1（失配消去条件，G_DC≡0）——相关性：无**。光谱域选择问题，无差分网络/共模概念。killRisk：无。
- **P2（Kelvin 地板）——相关性：无**。killRisk：无。
- **P3（平坦度约束衰减上界）——相关性：低（域不同，型似）**。UF（响应峰位均匀分布）+ OLP（相邻响应充分交叠）与 P3 的「通带平坦度」同属「响应形状约束」家族，但本文无阻带衰减概念、无任何「形状约束 ↔ 性能上界」的解析式——只有「形状 → 事后归纳的良好性」。型比价值：证明**响应形状约束在选型中只能事后量化**是跨域常态。killRisk：无。
- **方法学（D1–D10，增量四）——相关性：高（这正是 H4 空白靶子，且结论支持「空白存在」）**。四点现状证据：
  ① **无共识代价函数**：多目标（PSNR/GFC/MSE/CIEDE2000）"no consensus metric…conclusively superior for all purposes"（p.6，引 Imai 等 [25]）；
  ② **代理指标必要不充分**：条件数最小的集合不保证最优（p.13 自认），只能做粗筛（≤5 候选，p.14）；
  ③ **最终裁决靠实验**："or by a few experimental explorations"（p.14）——**门槛化/两步筛选是行业实际做法，而非解析选型**；
  ④ **穷举仿真代价高昂**：为验证一个启发式改动（换首滤片）跑了 2250 组仿真（p.6）。
  → 对增量四（门槛化方法学 D1–D10）的用法：作为「选型方法学在相邻域的现状基线」——**即便是专门研究选型方法的论文，其框架也是「代理指标粗筛 + 几何直觉/实验终选」，没有从元件参数到性能的解析映射**。P1 论文的门槛化方法学若给出可解析的门槛判据，即显著超出此基线。
- killRisk 总判：**无**。本文不触碰 P1/P2/P3 的任何主张；它是方法学空白的证人，不是对手。

## 没读到的

- UF/OLP 两个几何指标的完整定义式：式(11)（UF）在文本层可读，OLP 的定义式（p.10–11 交界，含"10% of the transmittance of the filter peaks"阈值波长表述）文本层被预印本水印层干扰、公式符号缺失——**待核**（可对照期刊 HTML 版）。
- 参考文献 [3]（Hardeberg 2004 FVAM 原始文献）、[10]（Hardeberg 2001 博士论文，MLI 首次用于训练集选择）、[25]（Imai 2002 指标比较研究）、[26]（López-Alvarez CSCM）原文未读——这些是「无共识度量」断言的一手来源，若 P1 论文要引「空白」证据，**更权威的锚点是 [25] 而非本文**。
- 表格数值仅核了正文引用的 Table 2/3/4/5/8/9；Table 1（20% 最优统计明细）与 Table 7（No.16 条件数，含 2.01×10⁻⁵ 的异常小值——疑似排版错误，条件数不可能 <1，**待核**）未逐项核。
- 页 15 提到的 SFA（光谱滤光阵列）设计适用性讨论只到"future work"，无展开。
