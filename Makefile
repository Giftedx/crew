PYTHON ?= python
PKG := ultimate_discord_intelligence_bot

.PHONY: install dev lint format type test eval docs pre-commit deprecations deprecations-json deprecations-strict ci-all

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
	$(PYTHON) scripts/validate_docs.py && $(PYTHON) scripts/validate_config_docs.py && $(PYTHON) scripts/check_deprecations.py --json > reports/deprecations_report.json
	@echo "Deprecation scan JSON written to reports/deprecations_report.json"

deprecations-strict:
	$(PYTHON) scripts/check_deprecations.py --fail-on-upcoming 90

ci-all: lint type test deprecations-strict

deprecations:
	$(PYTHON) scripts/check_deprecations.py

deprecations-json:
	$(PYTHON) scripts/check_deprecations.py --json > /dev/stdout
