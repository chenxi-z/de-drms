# 中英文论文初稿

- [英文主文件](main.tex) → [英文PDF](main.pdf)。
- [中文主文件](main-zh.tex) → [中文PDF](main-zh.pdf)。
- `sections/`、`sections-zh/`：对应的七节正文；公式、图号、表格和引用保持对应。
- [图件目录](figures/MANIFEST.md)：7幅原创图，中英文图注、数据来源、生成方法；SVG可编辑，PNG为600dpi，PDF用于TeX排版。
- `references.bib`：本稿实际引用15条文献；外部全文保留在Obsidian。
- [缺失材料清单](MANUSCRIPT_GAPS.md)、[4篇优先代下全文](LITERATURE_GAPS.md)：明确区分待核文献和待采实验。

## 编译

在本目录执行 `make` 同时更新两版PDF；`make english`、`make chinese` 可单独编译。英文采用pdfLaTeX，中文采用LuaLaTeX，两者均运行BibTeX及两轮交叉引用更新。支持 `PDFLATEX`、`LUALATEX`、`BIBTEX` 覆盖工具路径。`make clean` 只删除中间目录。

中文需要ctex、LuaTeX-ja以及Noto Serif/Sans CJK SC；西文和图件使用Times New Roman。本机已在 `~/.cache/de-drms-tex/texmf` 放置缺少的TeX宏包，Makefile仅在该缓存存在时启用它。标准系统安装对应的TeX Live语言包后，无需本地缓存。

图的矢量PDF若不存在，`make` 会从已保存的SVG生成，因此阅读和排版不依赖私人原始数据路径。完整重新计算图件时，执行：

```bash
python3 tools/generate_figures.py --evidence '/实际的/2026-10-27-qoder-qwen38flash-140348'
```

需要numpy、matplotlib、Pillow与CairoSVG。`figures/provenance.json` 保存原始数据哈希、解析/仿真比较和图检结果；不修改既有仿真。

## 核查记录

`build/qa/` 保存逐页预览、语言门禁、独立逻辑/语言/图件审查和PDF验证，属于本地生成物。正文保留实物验证与经典综合文献逐命题比较的明确占位。作者、单位及投稿模板待用户提供。

TeX、BibTeX、自有SVG、脚本和说明作为源文件管理；PDF、PNG和编译中间文件本地生成，不入库。
