PDF := effect-of-prompt-phrasing-on-llms.pdf

.PHONY: all analysis clean

all: $(PDF)

analysis:
	python3 analysis/analyze.py

$(PDF): analysis paper/main.tex paper/refs.bib
	cd paper && tectonic -X compile main.tex
	cp paper/main.pdf $(PDF)

clean:
	rm -f paper/main.pdf
