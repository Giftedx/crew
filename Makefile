PYTHON ?= python
PKG := ultimate_discord_intelligence_bot

.PHONY: install dev lint format type test eval docs pre-commit

install:
	$(PYTHON) -m pip install -e .

deV: install pre-commit

pre-commit:
	pre-commit install --install-hooks

lint:
	ruff check .

format:
	ruff check --fix . && ruff format .

type:
	mypy src || true  # incremental adoption, non-zero tolerated locally

test:
	pytest -q

# Golden evaluation harness (fast path)
eval:
	$(PYTHON) -m eval.runner datasets/golden/core/v1 baselines/golden/core/v1/summary.json || true

docs:
	$(PYTHON) scripts/validate_docs.py && $(PYTHON) scripts/validate_config_docs.py
