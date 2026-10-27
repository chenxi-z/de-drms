# 初稿文献证据与待补全文清单

本稿文献表由 2 条扩展为 15 条；11 条有本地全文，4 条 RC 综合文献目前按已核题录/摘要引用。全文存在不代表本轮逐页重读。正文只使用下表列明的支撑范围，不能用题名检索替代逐命题对照。英文与中文稿共用 `references.bib`。

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
| P0 | Guillemin, *Synthesis of RC-Networks* (1949) | [10.1002/sapm194928122](https://doi.org/10.1002/sapm194928122) | 给定电压传递与驱动点/输出阻抗的联合综合条件；本稿正元件反解与经典综合结果的关系。 |
| P0 | Fialkow & Gerst, *The Transfer Function of an R-C Ladder Network* (1951) | [10.1002/sapm195130149](https://doi.org/10.1002/sapm195130149) | 两级梯形等传递函数的参数自由度、正元件约束，是否已有等价参数化。 |
| P0 | Fialkow & Gerst, *The transfer function of general two terminal-pair RC networks* (1952) | [10.1090/qam/49081](https://doi.org/10.1090/qam/49081) | 端接变化、二端口函数等价与唯一性的相关定理。出版方页面有 PDF 入口，可请机构浏览器先试。 |
| P0 | Wang, Chen & Chen, *Realization of a transfer function as a passive two-port RC ladder network with a specified gain* (2017) | [10.1002/cta.2328](https://doi.org/10.1002/cta.2328) | 指定增益的连续可实现区间与本稿单/双端接约束的包含关系。 |

这四篇补齐前，正文保留“逐命题比较待完成”的具体标记；不写“首次”“从未研究”或“已有文献均未涉及”。缺口影响新颖性定位的最终强度，不改变本稿已经给出的代数推导是否成立。主库完整下载队列仍见 `../paywall-download-list.md`，本清单只列与本稿核心主张直接相关的缺口。

## 题录核对入口

- [AMS 原出版方页面](https://doi.org/10.1090/qam/49081)：核对 1952 文献题名、作者、卷页；其参考文献列出 1949 与 1951 两篇的题名、卷页与 DOI。
- [CityU 作者机构条目](https://scholars.cityu.edu.hk/en/publications/realization-of-a-transfer-function-as-a-passive-two-port-rc-ladde/)：核对 Wang 2017 作者、卷期页、DOI 和摘要；只据摘要说明“指定增益的无源 RC 梯形实现”研究范围。

本轮未下载新的外部 PDF，未将外部论文放进 Git 仓库。
