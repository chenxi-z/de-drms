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

## 当前状态（2026-10-25）

- 本地 PDF：7 份（H1×1、H3×2、H4×1、H5×2、H6×1），共 ~49 MB；
- 仅链接记录：12 项学术 + 若干 app note/论坛（见 index）；
- 待办：Scholar 深扫补齐 bib 中全部 `[待核]` 字段（构思文档 §G 步骤 0），沿 Rogillio 2007 / Breems 2023 / Sánchez-Romate 2021 三条引文链。
