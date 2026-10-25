# paper/ — 论文工作区（P1：ΣΔ 前端抗混叠选型方法学）

> 建立于 2026-10-25。论文构思与文献侦察结论见 `docs/design/2026-10-25-信号链论文构思.md`（§H 六轴现状 + 五个科学问题）；本目录只管写作物料。

## 目录结构

```
paper/
├── README.md            # 本文件（管理规则）
├── literature-index.md  # 文献总账：全部来源 + 状态（本地PDF/仅链接）+ 用途（入 git）
├── literature.bib       # BibTeX 库（入 git；Zotero 可直接导入）
├── literature/          # PDF 本体（*.pdf 被 .gitignore 全局忽略 → 仅本地，不入库）
└── draft/  figures/     # 后续建立：正文草稿 / 论文图（DRAW 轨道产物）
```

## 管理规则

1. **PDF 只留本地**：`*.pdf` 在 .gitignore 全局忽略，仓库只跟踪 index 与 bib——外部资料纪律不变，总账即唯一入库记录。
2. **命名规范**：`H{轴号}_{关键词}_{作者年份|机构}.pdf`，轴号对应构思文档 §H（H1 ΣΔ-AAF / H2 差分CMRR / H3 CT-ΣΔ / H4 选型方法学 / H5 kickback / H6 CNT-SHM）。
3. **每新增一篇**：PDF 落 `literature/`（能下则下）→ bib 加条目（元数据不全标 `[待核]`）→ index 加行（含用途一句话）。三者同步更新，同一提交。
4. **Zotero**：客户端未运行时以 `literature.bib` 为桥；启动 Zotero 后「文件 → 导入」本文件即可入库；howtoSCI 技能的 `zotero_coverage.py` 依赖 Zotero 缓存，届时可用其盘点。
5. **论坛/问答帖**（StackExchange、EEVblog、TI E2E）只记 index 不进 bib——正文不引用论坛，仅作现状证据。
6. **下载失败重试策略**见 index 末节（MDPI 浏览器手动下载即可；付费墙摘要级引用已够 P1）。

## 当前状态（2026-10-25 第二轮后）

- 文献总量：**41 项**（第一轮 web 侦察 19 项 + 第二轮 CrossRef API 22 项，后者题录全部已核、带 DOI）；
- 本地 PDF：7 份（~49 MB）；MDPI 开放获取 2 份（Nauman 2021 综述、Ye 2024）curl 被挑战页拦，浏览器手补；
- Zotero 10.0.6 已装于 `~/opt/Zotero_linux-x86_64/` 并在运行——首次导入：GUI「文件 → 导入 → `paper/literature.bib`」；howtoSCI 的 `zotero_coverage.py` 依赖其 MinerU 缓存（面向旧语料库），与本目录 bib 相互独立；
- 待办：Scholar 深扫沿三条引文链（Rogillio 2007 / Breems 书+Pavan 2011 / Sánchez-Romate 2021）补 bib 残余 `[待核]`（首轮条目）并确认无撞车。

## 2026-10-26 更新

- 文献库扩至 **63 条**（第三轮 +18 条近年 2019–2026 脉络，见 index 末节"脉络判读"）；
- **已全部导入 Zotero**：目录树 `P1 论文文献 → H1 ΣΔ-AAF / H2 差分CMRR / H3 CT-ΣΔ / H4 选型方法学 / H5 kickback / H6 CNT-SHM`，条目带标签 `P1论文文献 / P1-Hx / [本地PDF]`；
- 导入工具：`paper/tools/import_bib_to_zotero.py`（直写本地库，**须先退出 Zotero**，自动防重、自动建目录树；后续更新 bib 后可重跑，已存在的 DOI/题名自动跳过）；
- Zotero 库另有用户原有 ERT（电阻层析成像）121 篇——与 P2/P3 的电阻测量仪器方向有天然桥接，写作时可复用。
