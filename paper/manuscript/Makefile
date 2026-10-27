.DEFAULT_GOAL := all
PDFLATEX ?= pdflatex
LUALATEX ?= lualatex
BIBTEX ?= bibtex
# Optional local TeX runtime; system-wide installations need no cache.
ifneq ($(wildcard $(HOME)/.cache/de-drms-tex/texmf),)
export TEXMFHOME := $(HOME)/.cache/de-drms-tex/texmf
endif
FIGURES := $(patsubst %.svg,%.pdf,$(wildcard figures/Fig_*.svg)) $(wildcard figures/fig*.tex)
figures/%.pdf: figures/%.svg
	python3 -c 'import cairosvg; cairosvg.svg2pdf(url="$<",write_to="$@")'
.PHONY: all english chinese clean figures
all: english chinese
english: main.pdf
chinese: main-zh.pdf
main.pdf: main.tex references.bib $(wildcard sections/*.tex) $(FIGURES)
	mkdir -p build/en
	$(PDFLATEX) -interaction=nonstopmode -halt-on-error -file-line-error -output-directory=build/en main.tex
	$(BIBTEX) build/en/main
	$(PDFLATEX) -interaction=nonstopmode -halt-on-error -file-line-error -output-directory=build/en main.tex
	$(PDFLATEX) -interaction=nonstopmode -halt-on-error -file-line-error -output-directory=build/en main.tex
	cp build/en/main.pdf main.pdf
main-zh.pdf: main-zh.tex references.bib $(wildcard sections-zh/*.tex) $(FIGURES)
	mkdir -p build/zh
	$(LUALATEX) -interaction=nonstopmode -halt-on-error -file-line-error -output-directory=build/zh main-zh.tex
	$(BIBTEX) build/zh/main-zh
	$(LUALATEX) -interaction=nonstopmode -halt-on-error -file-line-error -output-directory=build/zh main-zh.tex
	$(LUALATEX) -interaction=nonstopmode -halt-on-error -file-line-error -output-directory=build/zh main-zh.tex
	cp build/zh/main-zh.pdf main-zh.pdf
figures:
	python3 tools/generate_figures.py
clean:
	rm -rf build
