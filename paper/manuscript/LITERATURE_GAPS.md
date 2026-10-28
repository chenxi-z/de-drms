# 初稿文献证据与待补全文清单

本稿现引用20条文献；17条现有本地全文，其中用户本次补齐4条核心RC综合文献，身份/页数已核、**逐命题精读已完成**（2026-10-28晚），判定见[经典先行工作对照矩阵](reviews/2026-10-28-classical-prior-art-comparison.md)；其余3条按已核题录/摘要使用。全文存在不代表本轮逐页重读。正文只使用下表列明的支撑范围，不能用题名检索替代逐命题对照。英文与中文稿共用 `references.bib`（254条总库，正文引用20条）。

## 已有全文：本稿实际用途

| bib key | 使用范围与核对锚点 |
|---|---|
| casas1996basics | 非耦合/耦合差分滤波，浮动公共点拓扑及高阶扩展；原文 pp.275–279、既有精读笔记。不能把“二阶/多级”本身称为新意。 |
| hornero2021cm | 失配造成带通型共模响应及相位变化；原文摘要、引言与式(5)附近，既有笔记。 |
| pallasareny1991cmrr | 有限差模/共模增益，幅相实测；本轮重新核对原文 p.669。 |
| pallasareny1991cascaded | 四传递函数、级联及“不加载前级”假设；本轮重新核对原文 p.677。 |
| gasulla2002cmresp | 共模增益、共模转差模增益与瞬态/稳定性；原文 p.1045。年份为 **2000**，旧 key 中 2002 只作兼容。 |
| koide1997redef | 复数 CMRR 与有意失衡补偿；本轮重新核对原文 p.737。 |
| serranofinetti2019cmnoise | 随机电子噪声需要噪声源/相关性模型；本轮重新核对原文 p.207，不能由确定性 CMRR 直接推出总噪声改善。 |
| whitlock2004balancedinput | 源端和接收端共模阻抗失衡的交互；本轮重新核对 AES 6261 原文 p.1，2004、两位作者身份准确。 |
| director1969the | 通用伴随网络与参数灵敏度方法；原文 pp.318–323、既有笔记。不能当作本文消去条件的来源。 |
| endres0ensitivi | PLL 差分环路滤波器失配引入瞬态；原文 pp.213–224、既有笔记。不能跨拓扑照搬其“元件完全匹配”条件。 |
| moschytz0radeffs | 灵敏度、元件比、元件容差的权衡；原文 Ch.11 pp.315–339，2002 年书章。受损 OCR 公式未用于本文。 |

## 四篇核心综合全文已归档并完成逐命题精读（2026-10-28）

本批四份由用户提供，均按bib key归档到Obsidian H8，已从代下载清单移出。**逐命题对照已完成**，判定与修改建议见[经典先行工作对照矩阵](reviews/2026-10-28-classical-prior-art-comparison.md)；四份精读笔记已扩充为带页码/定理号锚点的正式笔记。

| 文献 | DOI | PDF页数 / 印刷页码 | 精读笔记与判定要点 |
|---|---|---|---|
| Guillemin 1949 | `doi:10.1002/sapm194928122` | 21 / 22–42 | [笔记](../reading-notes/guillemin1949rcsynthesis.md)；式(5) 端接结构=本稿 H_g 分解祖先；连分式综合①经典 |
| Fialkow–Gerst 1951 | `doi:10.1002/sapm195130149` | 24 / 49–72 | [笔记](../reading-notes/fialkow1951rcladder.md)；K 区间理论（Thm 2/4）；p.59–60 同传函连续族；p.62 端接注记 |
| Fialkow–Gerst 1952 | `doi:10.1090/qam/49081` | 15 / 113–127 | [笔记](../reading-notes/fialkow1952rcnetworks.md)；Thm 1 完整刻画；p.114"一般≠子类"声明；p.120 1 Ω 负载提纲 |
| Wang等2017 | `doi:10.1002/cta.2328` | 15 / 1467–1481 | [笔记](../reading-notes/wang2017rcladder.md)；Thm 1 指定增益全区间可达；式(9) g₁=g_{n+1}=0 塌缩印证本稿拓扑边界 |

四篇的文件获取缺口与逐命题包含关系均已关闭。**正文修改**（引用分层、降格两处、划界句）按对照矩阵 §三清单另行执行；**新缺两条题录**（CrossRef 已核元数据）：Paige–Kuh 1960（`doi:10.1109/tct.1960.1086620`，IRE Trans. CT 7(1):32–40）、Ali–Kim 1975（`doi:10.1109/tcs.1975.1083969`，IEEE TCAS 22(10):831–833），正文引用前须入册。主库完整获取队列见 `../paywall-download-list.md`，本批哈希与来源名见[归档验收记录](../fulltext-archive-2026-10-28.md)。

## 题录核对入口

- [AMS 原出版方页面](https://doi.org/10.1090/qam/49081)：核对 1952 文献题名、作者、卷页；其参考文献列出 1949 与 1951 两篇的题名、卷页与 DOI。
- [CityU 作者机构条目](https://scholars.cityu.edu.hk/en/publications/realization-of-a-transfer-function-as-a-passive-two-port-rc-ladde/)：核对 Wang 2017 作者、卷期页、DOI 和摘要；只据摘要说明“指定增益的无源 RC 梯形实现”研究范围。

此前自动获取阶段未取得这四篇；本次由用户补齐，PDF仅归档Obsidian。

## 2026-10-28 接手续验（归档前历史）

以下保留归档前的访问尝试，本页上方到货记录为当前状态。当时原4篇全文缺口尚在。已实际重试AMS免费直链：网页工具返回403，直接请求返回“Verifying your connection”的HTML，文件头不是`%PDF-`，因此未移入文献库、未记为取得全文。免费访问状态不保证当前环境能够直接下载。

本轮新增3条支撑题录，核对范围为出版方摘要及元数据；不冒称逐页全文审读：

| 条目 | DOI | 本稿允许使用的范围 | 全文状态 |
|---|---|---|---|
| Johnson, *Thermal Agitation of Electricity in Conductors* (1928) | `doi:10.1103/PhysRev.32.97` | 实验热噪声及实部阻抗关系的历史来源；[APS摘要](https://journals.aps.org/pr/abstract/10.1103/PhysRev.32.97) | 本轮未取得PDF；补全文可用于原式逐页校核 |
| Nyquist, *Thermal Agitation of Electric Charge in Conductors* (1928) | `doi:10.1103/PhysRev.32.110` | 平衡态热噪声理论来源；[APS摘要](https://journals.aps.org/pr/abstract/10.1103/PhysRev.32.110) | 本轮未取得PDF；不从摘要推出特定RC梯形的新定理 |
| Lee, *Chain matrix decompositions, continued fractions and the optimal inhomogeneous ladder networks* (1978) | `doi:10.1016/0016-0032(78)90050-9` | 连分式梯形综合、传输矩阵分解属于既有工具；[出版方摘要](https://www.sciencedirect.com/science/article/abs/pii/0016003278900509) | 全文需补；不得用摘要完成任意RC新颖性划界 |

本轮理论边界修正不依赖“联合可实现性为新结果”的假设。正文给出自身代数推导；原4篇的逐命题对照，以及Lee全文获取/核读，仍需完成。
