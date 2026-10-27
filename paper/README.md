# paper/ — 论文工作区（P1：ΣΔ 前端抗混叠选型方法学）

> 建立于 2026-10-25。论文构思与文献侦察结论见 `docs/design/2026-10-25-信号链论文构思.md`（§H 六轴现状 + 五个科学问题）；本目录只管写作物料。

## 目录结构

```
paper/
├── README.md            # 本文件（管理规则）
├── literature-index.md  # 文献总账：全部来源 + 状态（本地PDF/仅链接）+ 用途（入 git）
├── literature.bib       # BibTeX 库（入 git；Zotero 可直接导入）
（全文 PDF 不入本仓——2026-10-26 起统一存 Obsidian，见管理规则 1）
└── draft/  figures/     # 后续建立：正文草稿 / 论文图（DRAW 轨道产物）
```

## 管理规则

1. **全文 PDF 一律存 Obsidian（2026-10-26 起）**：`Obsidian Vault/20-硬件工程/10-项目设计/p1-文献谱系/fulltext/<H轴>/`（八轴目录，163 份在库）；本仓 `*.pdf`/`*.zip` 被 .gitignore 全局忽略，只跟踪 index 与 bib——外部资料纪律（AGENTS.md）不变，总账即唯一入库记录。
2. **命名规范**：文件名 = bib key（如 `ji2016ultra.pdf`），轴由所在目录体现；历史 `H{轴}_关键词` 命名已随迁移统一改为 bib key。
3. **每新增一篇**：PDF 落 Obsidian fulltext 对应轴目录（能下则下）→ bib 加条目（元数据不全标 `[待核]`）→ index 加行（含用途一句话）。三者同步更新，同一提交。
4. **Zotero**：客户端未运行时以 `literature.bib` 为桥；启动 Zotero 后「文件 → 导入」本文件即可入库；howtoSCI 技能的 `zotero_coverage.py` 依赖 Zotero 缓存，届时可用其盘点。
5. **论坛/问答帖**（StackExchange、EEVblog、TI E2E）只记 index 不进 bib——正文不引用论坛，仅作现状证据。
6. **下载失败重试策略**见 index 末节（MDPI 浏览器手动下载即可；付费墙摘要级引用已够 P1）。

## 当前状态（2026-10-26 全文库迁移后：238 条题录、全文 163 份入 Obsidian、66 篇未到货）

- 历史状态（2026-10-25 第二轮后）：

- 文献总量：**41 项**（第一轮 web 侦察 19 项 + 第二轮 CrossRef API 22 项，后者题录全部已核、带 DOI）；
- 本地 PDF：7 份（~49 MB）；MDPI 开放获取 2 份（Nauman 2021 综述、Ye 2024）curl 被挑战页拦，浏览器手补；
- Zotero 10.0.6 已装于 `~/opt/Zotero_linux-x86_64/` 并在运行——首次导入：GUI「文件 → 导入 → `paper/literature.bib`」；howtoSCI 的 `zotero_coverage.py` 依赖其 MinerU 缓存（面向旧语料库），与本目录 bib 相互独立；
- 待办：Scholar 深扫沿三条引文链（Rogillio 2007 / Breems 书+Pavan 2011 / Sánchez-Romate 2021）补 bib 残余 `[待核]`（首轮条目）并确认无撞车。

## 2026-10-26 更新

- 文献库扩至 **63 条**（第三轮 +18 条近年 2019–2026 脉络，见 index 末节"脉络判读"）；
- **已全部导入 Zotero**：目录树 `P1 论文文献 → H1 ΣΔ-AAF / H2 差分CMRR / H3 CT-ΣΔ / H4 选型方法学 / H5 kickback / H6 CNT-SHM`，条目带标签 `P1论文文献 / P1-Hx / [本地PDF]`；
- 导入工具：`paper/tools/import_bib_to_zotero.py`（直写本地库，**须先退出 Zotero**，自动防重、自动建目录树；后续更新 bib 后可重跑，已存在的 DOI/题名自动跳过）；
- Zotero 库另有用户原有 ERT（电阻层析成像）121 篇——与 P2/P3 的电阻测量仪器方向有天然桥接，写作时可复用。

## 2026-10-26 更新（二）

- **go/no-go 判定：GO**。已精读 Hornero 2021 全文（DSpace REST API 绕过反爬取得）：
  其覆盖 GDC=G2−G1 失配解析、带通共模/峰化、级联定性警示与"避免该拓扑"的负面结论；
  **未覆盖**配对不变量（整线同 m）、Kelvin 结构地板、可达性边界——P1 四增量成立，定位句见 literature-screen.md；
- **SBAA230 误归属已更正**（实为数字滤波器笔记）；单级公式真实出处 = TI《Three Guidelines》博客（扫描版 PDF 在库）；
- **Sánchez-Romate 归属混淆更正**：scarfed joints 实为 Augustin/Karsten/Kötter 2018 Composites Part A（本库博士论文期刊版，新入库）；
- 全库 68 条定级完成（A 核心 12 / B 支撑 36 / C 现状证据 17 / D 剔除 3），机械门禁 PASS
  （定级覆盖 100%、核心元数据 12/12，@manual/@misc 无日期培训材料按 IEEE 惯例豁免 year/doi）；
- 筛选总账与判定证据：`paper/literature-screen.md`；误归属更正记录也在此文件 §四。

## 2026-10-26 更新（三）· 纵深扩展

- 文献库 68 → **147 条**（第五轮 +79：14 轴 CrossRef 纵深扫 68 + Hornero 引文链 OpenAlex 精选 11）；
- 新增两轴：**H7 比率与电阻计量**、**H8 灵敏度与统计电路设计**（SQ2/SQ4 理论地基，此前检索面过窄）；
- A 级提升 4 条（Casas 1996、Pallàs-Areny 1991×2、Pallàs-Areny 1993 教材）→ 共 16 条；
- 悬案 `ieeebasicsdiff` 破案 = Casas 1996；Zotero 目录树扩至九轴（H7/H8 新建），库内 153 件 P1 文献；
- 用户原有 ERT/SIP 集（121 篇，谱感应极化测量方法学）与 P2/P3 的搭桥点已在 index 登记。

## 2026-10-26 更新（四）· 时间线回填

- 168 条（+20 经典 1963–2012：Inose 1963 ΣΔ 诞生 / Orchard 1966 / Director 1969 灵敏度理论 /
  McCreary 1975 / Caves 1977 开关电容 / Candy 1981·1985 / Barber 1984 EIT / Chung 1998 自感知 /
  Norsworthy 1996 圣经书 / O'Dwyer 2009 薄膜匹配 / Lee 2012 漂移）；
- A 级 19 条（+3 理论源头）；时间线判读（1963→2026 七段谱系）在 index 第六轮节，可直接作 Intro 素材；
- Zotero 库同步 +20；book review 入库拦截规则建立。

## 2026-10-27 更新（五）· 精读收口与方向重梳

- **精读全部收口**：40 篇缺口按原批次模板补跑（四波、并发 2），`reading-notes/` 现 **165 份**，对库内可读正文（164 PDF + 3 txt）100% 覆盖。P1 反例搜索终态：**全阴性**（无任何一篇给出多级无源差分 RC 网络 G_DC(s)≡0 的元件条件）；
- **新增三份综合文档**：`literature-map.md`（八轴谱系链 + 三命题证据矩阵 + killRisk 划界簿 v2 + 跨域同构对照）、`research-focus.md`（研究重点重梳：文献缺口领衔 N1–N6，我们数据降为标定实例；§五投稿阶梯）、`cnki-scan.md`（知网反例搜索：136 篇中文"抗混叠"题名判读，缺口同样阴性）；
- **bib 勘误与质量治理**（236 条，门禁 0 错误）：khalifeh 作者 Nyathi→Nyambo；lyu2018 双录标注（引用用主条目）；moschytz 年份 0→2002。**中文文献分级 T1/T2/T3**（标准见 cnki-scan.md §三A）：T1 jiang2004 留 / T2 zhang2024 留（引用前复核中英摘要矛盾）/ T3 chen2026 默认不引候删；知网直域命中 wu2023passive（电子与封装 2023，普刊配方文）**不入库**，档案存 cnki-scan.md §三；
- **术语纪律**（用户要求）：自造词登记于 research-focus.md 卷首——"梯形消去/配对不变量/整线同偏/结构地板"等系本项目工作用语，论文中要么平实描述要么显式 "we term this"；文献既有概念 = G_DC（Hornero 2021/Gasulla 2002）等；
- **用户已定方向约束**：底线 **SCI 四区**、中文 EI 及以下不作考虑（research-focus.md §五）；重点排序 N1（必要性证明）第一优先；
- **git 基线**：paper/ 既有 34 个文件在库（最后提交 7ee6ded）；本会话新增 ~140 份笔记与 3 份综合文档、修改 README/bib，随本次收口提交——审查代理可 `git diff 7ee6ded -- paper/` 对照全部增量。

### 给审查代理的入口（建议审查顺序）

1. `research-focus.md` —— 方向与重点重梳（含术语纪律、投稿阶梯）；审查点：N1–N6 排序的证据支撑、四区底线的可达性论证是否成立；
2. `literature-map.md` —— 联系图谱；审查点：谱系链每条边是否落得了笔记锚点、killRisk 划界簿 v2 有无遗漏近缘；
3. `cnki-scan.md` —— 中文反例搜索方法与质量标准；审查点：T1/T2/T3 分级是否合理、"136 篇阴性"结论是否被方法局限（多词查询噪声、97/136 题名、全文未核）支撑；
4. 抽查 `reading-notes/` 任意 3–5 份 —— 引用是否逐字带页码、killRisk 判断是否有据（范例基线：`H2_whitlock2004_new.md`）；
5. `literature.bib` —— 门禁 `python3 tools/gate_bib.py`（应 0 错误）+ 三处勘误与分级注记核对。
