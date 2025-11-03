# Makefile to manage dataset cloning and running code analysis

PYTHON ?= python3
REPO ?=
DEPTH ?= 1
KEEP_GIT ?=
FORCE ?=

# derive NAME and TARGET using Make functions (handles ':' in ssh urls)
NAME := $(patsubst %.git,%,$(notdir $(subst :,/,$(REPO))))
TARGET := dataset/codes/$(NAME)

.PHONY: help add-dataset-codes analyze-code

help:
	@echo "Usage:"
	@echo "  make add-dataset-codes REPO=git@github.com:owner/repo.git [DEPTH=1] [KEEP_GIT=1] [FORCE=1]"
	@echo "  make analyze-code REPO=git@github.com:owner/repo.git [PYTHON=python3]"

# Clone a repository into dataset/codes/<repo-name>
add-dataset-codes:
	@if [ -z "$(REPO)" ]; then \
		echo "Specify REPO=git@github.com:owner/repo.git"; exit 1; \
	fi; \
	# compute and show the target path
	@echo "Target path: $(TARGET)"; \
	mkdir -p dataset/codes; \
	if [ -d "$(TARGET)" ]; then \
		if [ "$(FORCE)" = "1" ]; then rm -rf "$(TARGET)"; else echo "$(TARGET) exists, skipping (use FORCE=1 to re-clone)"; exit 0; fi; \
	fi; \
	keepopt=""; \
	if [ "$(KEEP_GIT)" = "1" ]; then keepopt="--keep-git"; fi; \
	forceopt=""; \
	if [ "$(FORCE)" = "1" ]; then forceopt="--force"; fi; \
	$(PYTHON) scripts/fetch_datasets.py --repo "$(REPO)" --path "$(TARGET)" --depth $(DEPTH) $$keepopt $$forceopt || { echo "fetch_datasets failed"; exit 1; }; \
	echo "Cloned $(REPO) -> $(TARGET)"

# Clone, then run code analysis pointed at the cloned path
analyze-code: add-dataset-codes
	@if [ -z "$(REPO)" ]; then \
		echo "Specify REPO=..."; exit 1; \
	fi; \
	echo "Running code analysis on $(TARGET)"; \
	$(PYTHON) scripts/code_analysis.py -p "$(TARGET)"

