# Makefile - ACA Project 3 (gem5)
#
# The heavy lifting lives in scripts/ so every target also works when
# invoked directly as a shell script. GEM5_ROOT defaults to ~/gem5 and
# can be overridden: `make run GEM5_ROOT=/path/to/gem5`.

CFLAGS := -O2 -std=c11 -Wall -Wextra -static
WORKLOADS := matrix_naive matrix_tiled linked_list_recursive linked_list_iterative
BINS := $(addprefix bin/,$(WORKLOADS))

.PHONY: all build env run run-matrix-baseline run-matrix-cache run-list \
        extract validate plots screenshots report package clean

all: build

build: $(BINS)

bin/%: src/%.c
	@mkdir -p bin
	gcc $(CFLAGS) -o $@ $<

env:
	bash scripts/detect_environment.sh

run: env build
	bash scripts/run_matrix_baseline.sh
	bash scripts/run_matrix_cache.sh
	bash scripts/run_linked_list.sh

run-matrix-baseline: build
	bash scripts/run_matrix_baseline.sh

run-matrix-cache: build
	bash scripts/run_matrix_cache.sh

run-list: build
	bash scripts/run_linked_list.sh

extract:
	python3 scripts/extract_stats.py

validate:
	python3 scripts/validate_results.py | tee results/logs/validation.log

plots:
	python3 scripts/generate_plots.py

screenshots:
	python3 scripts/log_to_png.py

report:
	cd report && xelatex -interaction=nonstopmode main.tex \
	          && xelatex -interaction=nonstopmode main.tex

package:
	bash scripts/package.sh

clean:
	rm -f $(BINS)
	rm -f report/main.aux report/main.log report/main.out report/main.toc
