# 初稿文献证据与待补全文清单

本稿现引用18条文献；原11条有本地全文，4条RC综合文献及本轮新增3条目前按已核题录/摘要使用。全文存在不代表本轮逐页重读。正文只使用下表列明的支撑范围，不能用题名检索替代逐命题对照。英文与中文稿共用 `references.bib`。

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

## 请优先代下的 4 篇全文

以下四篇在当前 `unfetched-papers.csv` 中均为“直取受限；需机构/浏览器或代下”，全文路径为空。取回后放入 Obsidian 文献库，仓库只保留自有笔记与题录。

| 优先级 | 题名与年份 | DOI / 正式入口 | 需要核对的具体问题 |
|---|---|---|---|
| P0 | Guillemin, *Synthesis of RC-Networks* (1949) | `doi:10.1002/sapm194928122`<br>https://doi.org/10.1002/sapm194928122<br>Wiley **closed**（需机构） | 给定电压传递与驱动点/输出阻抗的联合综合条件；本稿正元件反解与经典综合结果的关系。 |
| P0 | Fialkow & Gerst, *The Transfer Function of an R-C Ladder Network* (1951) | `doi:10.1002/sapm195130149`<br>https://doi.org/10.1002/sapm195130149<br>Wiley **closed**（需机构；新颖性威胁最大，优先取） | 两级梯形等传递函数的参数自由度、正元件约束，是否已有等价参数化。 |
| P0 | Fialkow & Gerst, *The transfer function of general two terminal-pair RC networks* (1952) | `doi:10.1090/qam/49081`<br>https://doi.org/10.1090/qam/49081<br>**bronze OA 免费**：[PDF 直链](https://www.ams.org/qam/1952-10-02/S0033-569X-1952-49081-7/S0033-569X-1952-49081-7.pdf) | 端接变化、二端口函数等价与唯一性的相关定理。出版方页面有 PDF 入口，可请机构浏览器先试。 |
| P0 | Wang, Chen & Chen, *Realization of a transfer function as a passive two-port RC ladder network with a specified gain* (2017) | `doi:10.1002/cta.2328`<br>https://doi.org/10.1002/cta.2328<br>Wiley **closed**（需机构） | 指定增益的连续可实现区间与本稿单/双端接约束的包含关系。 |

这四篇补齐前，正文保留“逐命题比较待完成”的具体标记；不写“首次”“从未研究”或“已有文献均未涉及”。缺口影响新颖性定位的最终强度，不改变本稿已经给出的代数推导是否成立。主库完整下载队列仍见 `../paywall-download-list.md`，本清单只列与本稿核心主张直接相关的缺口。

## 题录核对入口

- [AMS 原出版方页面](https://doi.org/10.1090/qam/49081)：核对 1952 文献题名、作者、卷页；其参考文献列出 1949 与 1951 两篇的题名、卷页与 DOI。
- [CityU 作者机构条目](https://scholars.cityu.edu.hk/en/publications/realization-of-a-transfer-function-as-a-passive-two-port-rc-ladde/)：核对 Wang 2017 作者、卷期页、DOI 和摘要；只据摘要说明“指定增益的无源 RC 梯形实现”研究范围。

本轮未下载新的外部 PDF，未将外部论文放进 Git 仓库。

## 2026-10-28 接手续验

原4篇全文缺口保持不变。已实际重试AMS免费直链：网页工具返回403，直接请求返回“Verifying your connection”的HTML，文件头不是`%PDF-`，因此未移入文献库、未记为取得全文。免费访问状态不保证当前环境能够直接下载。

本轮新增3条支撑题录，核对范围为出版方摘要及元数据；不冒称逐页全文审读：

| 条目 | DOI | 本稿允许使用的范围 | 全文状态 |
|---|---|---|---|
| Johnson, *Thermal Agitation of Electricity in Conductors* (1928) | `doi:10.1103/PhysRev.32.97` | 实验热噪声及实部阻抗关系的历史来源；[APS摘要](https://journals.aps.org/pr/abstract/10.1103/PhysRev.32.97) | 本轮未取得PDF；补全文可用于原式逐页校核 |
| Nyquist, *Thermal Agitation of Electric Charge in Conductors* (1928) | `doi:10.1103/PhysRev.32.110` | 平衡态热噪声理论来源；[APS摘要](https://journals.aps.org/pr/abstract/10.1103/PhysRev.32.110) | 本轮未取得PDF；不从摘要推出特定RC梯形的新定理 |
| Lee, *Chain matrix decompositions, continued fractions and the optimal inhomogeneous ladder networks* (1978) | `doi:10.1016/0016-0032(78)90050-9` | 连分式梯形综合、传输矩阵分解属于既有工具；[出版方摘要](https://www.sciencedirect.com/science/article/abs/pii/0016003278900509) | 全文需补；不得用摘要完成任意RC新颖性划界 |

本轮理论边界修正不依赖“联合可实现性为新结果”的假设。正文给出自身代数推导；原4篇及Lee全文的命题包含关系仍需核查。
