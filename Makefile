# ============================================================
# Matrix OS — developer Makefile
# Self-contained: targets build an isolated .venv so `make install`
# and `make test` work from a clean checkout with no global setup.
# Uses `uv` when available (fast); falls back to python venv + pip.
# ============================================================

PYTHON ?= python3
VENV   := .venv
BIN    := $(VENV)/bin
PY     := $(BIN)/python
MOS    := $(PY) -m matrix_os

PORT ?= 8080
HOST ?= 127.0.0.1
GOAL ?= read and inspect the repository

# Prefer uv if it is on PATH.
UV := $(shell command -v uv 2>/dev/null)

INSTALL_STAMP := $(VENV)/.install.stamp

.DEFAULT_GOAL := help
.PHONY: help install run goal serve test validate eval evals dashboard lint clean distclean

help: ## Show this help
	@echo "Matrix OS — make targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-11s\033[0m %s\n", $$1, $$2}'

$(INSTALL_STAMP): pyproject.toml
ifeq ($(UV),)
	@echo "→ uv not found; using python venv + pip (install uv for faster builds: https://docs.astral.sh/uv/)"
	$(PYTHON) -m venv $(VENV)
	$(BIN)/python -m pip install --quiet --upgrade pip
	$(BIN)/python -m pip install --quiet -e ".[dev]"
else
	@echo "→ using uv ($(UV))"
	uv venv $(VENV)
	uv pip install --python $(PY) -e ".[dev]"
endif
	@touch $(INSTALL_STAMP)

install: $(INSTALL_STAMP) ## Create .venv and install the kernel + dev deps (uv if available)
	@echo "installed: matrix-os (editable) in $(VENV)"

run: $(INSTALL_STAMP) ## Start the backend API + console frontend (auto port fallback)
	$(MOS) serve --host $(HOST) --port $(PORT)

serve: run ## Alias for `make run`

goal: $(INSTALL_STAMP) ## Run the governed loop once for a goal (GOAL="...")
	$(MOS) run "$(GOAL)"

test: $(INSTALL_STAMP) ## Run the test suite
	$(PY) -m pytest -q

validate: $(INSTALL_STAMP) ## Self-check every contract schema
	$(MOS) validate

eval: $(INSTALL_STAMP) ## Run the behavioural eval suite
	$(MOS) eval

evals: validate eval test ## Full check: contracts + eval suite + tests (CI parity)

dashboard: $(INSTALL_STAMP) ## Refresh frontend/data.json from the live run log
	$(MOS) dashboard

lint: $(INSTALL_STAMP) ## Byte-compile all sources (smoke lint)
	$(PY) -m compileall -q matrix_os tests

clean: ## Remove caches, build artifacts, and local runtime state
	rm -rf .pytest_cache .matrix *.egg-info build dist
	find . -type d -name __pycache__ -prune -exec rm -rf {} +

distclean: clean ## clean + remove the virtualenv
	rm -rf $(VENV)
