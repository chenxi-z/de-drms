# 精读笔记 · Pliquett 2011《Front end with offset-free symmetrical current source optimized for time domain impedance spectroscopy》（Physiological Measurement）——**⚠️ 未能精读：库内 PDF 内容错配**
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> **状态：异常登记，非精读笔记。** 库内 `fulltext/H7-比率与电阻计量/pliquett2011ront.pdf` 的文件名与内容不符，实际是另一篇论文，无法产出 Pliquett 2011 的页级逐字引用。按工作规约**未动库内文件**（发现异常先报告）。

## 出处（目标论文）
- Pliquett U., Schönfeldt M., Barthel A., Frense D., Nacke T., Beckmann D., Physiol. Meas. 32 (2011) 927–944，DOI 10.1088/0967-3334/32/7/s15。
- 题录核对：`paper/literature.bib` L1051–1059（@article{pliquett2011ront}）✅；`paper/paywall-download-list.md` 第 64 项（10.1088/0967-3334/32/7/s15）✅——即该文当时即被列为**付费墙未能下载**项。

## 错配证据（库内 PDF 逐字引用，物理页 1）
> "Experimental Study of the Atomic and Molecular Processes Related to Plasma Detachment in Steady-State Divertor Simulator MAP-II"
> "This content has been downloaded from IOPscience. Please scroll down to see the full text."
> "2004 Plasma Sci. Technol. 6 2451"
> "(http://iopscience.iop.org/1009-0630/6/5/004)"
> "IP Address: 130.88.90.140"
> "This content was downloaded on 18/05/2015 at 07:53"
- 实际作者（OCR 有损）：Kado S., Kajita S., et al.；期刊页眉 "Plasma Science & Technology, V0l.6, No.5, Oct. 2004"；共 6 物理页（2451–2455 + 首页），主题为核聚变偏滤器等离子体再结合光谱诊断——**与 Pliquett 2011 阻抗前端零关联**。
- 判断：疑似 2015-05-18 从 IOPscience 检索/下载时存错文件（目标刊 Physiol. Meas. 同属 IOP，检索结果点错）。与 AGENTS.md 记载的 `ad779x.pdf`（名不副实、实为下载失败 HTML）同类。

## 恢复尝试（均失败，未编造）
1. IOPscience 直链 `…/article/10.1088/0967-3334/32/7/s15/pdf` → 返回 200 但为 HTML（付费墙/反爬页）。
2. Semantic Scholar API → `"openAccessPdf": {"url": "", "status": "CLOSED"}`，摘要字段被出版商隐藏。
3. 库内与项目内全盘检索 `*pliquett*` → 仅此一个错配 PDF，无其他副本。

## 对 P1/P2/P3 的对照
- **未评估**（正文不可得）。仅凭题名与谱系定位：该文属 H7 轴"时域阻抗谱的对称电流源前端"，与 DE-DRMS 恒流激励架构同族，预期对 P1（激励-测量链路消去条件）为**中**相关、对 P2 为**低**相关——此为题录级推断，非精读结论，**不得当作已核证据引用**。
- **killRisk 判断：暂记"未评估（文件缺失）"**。待取得合法全文后补做。

## 没读到的
- **全部内容**。建议处置（需用户/主代理决定）：①将库内错配 PDF 改名或移出（勿直接删除，先向 Obsidian 库管理会话报告）；②通过机构订阅或馆际互借获取 10.1088/0967-3334/32/7/s15 全文后重跑本篇精读；③更新 paywall-download-list 状态。
