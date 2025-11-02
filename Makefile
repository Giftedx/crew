# Prefer Python 3 by default when no venv is present
PYTHON ?= python3
# Prefer local virtualenv if present
ifneq (,$(wildcard .venv/bin/python))
PYTHON := .venv/bin/python
endif
PKG := ultimate_discord_intelligence_bot

.PHONY: install dev lint format format-check type test eval docs pre-commit deprecations deprecations-json deprecations-strict deprecations-badge guards ci-all clean clean-dry-run deep-clean organize-root maintain-archive config-validate health health-dashboard health-report metrics metrics-api metrics-dashboard metrics-test
.PHONY: docs-strict
.PHONY: ops-queue
.PHONY: test-fast ci-fast agent-evals-ci
.PHONY: ensure-venv uv-lock uv-sync uv-bootstrap
.PHONY: install dev lint format format-check type type-changed type-baseline type-baseline-update test eval docs pre-commit hooks deprecations deprecations-json deprecations-strict deprecations-badge guards ci-all clean clean-dry-run clean-bytecode deep-clean warn-venv organize-root maintain-archive
.PHONY: run-discord-enhanced

# Target definitions are below to avoid duplicates


install:
	$(PYTHON) -m pip install -e .

dev: install pre-commit

pre-commit:
	$(PYTHON) -m pre_commit install --install-hooks

bootstrap:
	$(PYTHON) scripts/bootstrap_env.py

clean-bytecode:
	find . -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
	find . -name '*.py[co]' -delete || true
	echo "Bytecode caches removed"


setup:
	$(PYTHON) -m ultimate_discord_intelligence_bot.setup_cli wizard

# Validate configuration and system requirements
config-validate:
	$(PYTHON) -m ultimate_discord_intelligence_bot.setup_cli doctor

# Initialize local environment file from template (idempotent)
.PHONY: init-env
init-env:
	@if [ -f .env ]; then \
		echo "[init-env] .env already exists; skipping"; \
	else \
		cp .env.example .env && echo "[init-env] Created .env from .env.example"; \
		echo "[init-env] Next: edit .env and set DISCORD_BOT_TOKEN and one of OPENAI_API_KEY/OPENROUTER_API_KEY"; \
	fi

# First-time developer bootstrap (prefers uv if available)
.PHONY: first-run
first-run:
	@if command -v uv >/dev/null 2>&1; then \
		echo "[first-run] Using uv for bootstrap"; \
		if [ ! -d .venv ]; then uv venv --python 3.11; fi; \
		. .venv/bin/activate && uv pip install -e '.[dev]'; \
	else \
		echo "[first-run] uv not found; falling back to ensure-venv (pip)"; \
		$(MAKE) ensure-venv; \
	fi
	$(MAKE) setup-hooks
	@echo "[first-run] Checking environment (doctor). If this fails due to secrets, we'll continue."
	-$(MAKE) doctor || echo "[first-run] Doctor reported issues (likely missing DISCORD_BOT_TOKEN). Run 'make init-env' then edit .env."
	$(MAKE) quick-check
	@echo "[first-run] Complete. If doctor flagged secrets, run: make init-env && $$(command -v code >/dev/null 2>&1 && echo 'code .' || echo 'vim .env')"

warn-venv:
	@if [ -d venv ] && [ ! -L venv ]; then \
		echo "[warn-venv] Detected legacy 'venv/' directory. Canonical environment is '.venv/'. Consider removing 'venv/' to avoid confusion."; \
	else \
		echo "No legacy 'venv/' directory detected."; \
	fi

doctor:
	$(PYTHON) -m ultimate_discord_intelligence_bot.setup_cli doctor

run-discord:
	$(PYTHON) -m ultimate_discord_intelligence_bot.setup_cli run discord

# Convenience: run Discord with enhancement flags (shadow-safe by default)
run-discord-enhanced:
	ENABLE_GPTCACHE=true \
	ENABLE_SEMANTIC_CACHE_SHADOW=true \
	ENABLE_GPTCACHE_ANALYSIS_SHADOW=true \
	ENABLE_PROMPT_COMPRESSION=true \
	ENABLE_GRAPH_MEMORY=true \
	ENABLE_HIPPORAG_MEMORY=true \
	$(PYTHON) -m ultimate_discord_intelligence_bot.setup_cli run discord

run-crew:
	$(PYTHON) -m ultimate_discord_intelligence_bot.setup_cli run crew

docker-build:
	docker build -t $(IMAGE) .

docker-push:
	docker push $(IMAGE)

k8s-apply:
	kubectl apply -f ops/deployment/k8s/qdrant-pvc.yaml
	kubectl apply -f ops/deployment/k8s/qdrant-deployment.yaml
	kubectl apply -f ops/deployment/k8s/qdrant-service.yaml
	kubectl apply -f ops/deployment/k8s/api-deployment.yaml
	kubectl apply -f ops/deployment/k8s/api-service.yaml

lock:
	$(PYTHON) -m piptools compile pyproject.toml --extra dev -o requirements-dev.txt

sync:
	$(PYTHON) -m piptools sync requirements-dev.txt

lint:
	$(PYTHON) -m ruff check . --exclude examples

format:
	$(PYTHON) -m ruff check --fix . --exclude examples && $(PYTHON) -m ruff format . --exclude examples

format-check:
	$(PYTHON) -m ruff format --check .

type:
	$(PYTHON) -m mypy src/platform src/domains src/app || true  # incremental adoption, non-zero tolerated locally

# Install missing type stubs for optional dependencies
types-install:
	$(PYTHON) -m pip install types-requests types-redis types-beautifulsoup4
	@echo "Type stubs installed. Run 'make type' to verify."

type-guard:
	$(PYTHON) scripts/mypy_snapshot_guard.py --baseline reports/mypy_snapshot.json

type-guard-update:
	$(PYTHON) scripts/mypy_snapshot_guard.py --baseline reports/mypy_snapshot.json --update

ci-type-guard:  ## CI-friendly guard (fails build if increased); can add --json for machine parsing
	$(PYTHON) scripts/mypy_snapshot_guard.py --baseline reports/mypy_snapshot.json

type-guard-json:
	@if [ "$(BREAKDOWN)" = "1" ]; then \
		$(PYTHON) scripts/mypy_snapshot_guard.py --baseline reports/mypy_snapshot.json --json --breakdown; \
	else \
		$(PYTHON) scripts/mypy_snapshot_guard.py --baseline reports/mypy_snapshot.json --json; \
	fi

test:
	PYTHONPATH=src $(PYTHON) -m pytest -q -c .config/pytest.ini

# Fast local CI sweep (quick feedback loop)
test-fast:
	$(PYTHON) -m pytest -q -c .config/pytest.ini -k "http_utils or guards_http_requests or vector_store_dimension or vector_store_namespace"

# Run the fast test sweep with a clean environment for retry precedence tests
.PHONY: test-fast-clean-env
test-fast-clean-env:
	env -u RETRY_MAX_ATTEMPTS PYTHONPATH=src $(PYTHON) -m pytest -q -c .config/pytest.ini -k "http_utils or guards_http_requests or vector_store_dimension or vector_store_namespace"

ci-fast: docs guards test-fast agent-evals-ci

agent-evals-ci:
	$(PYTHON) scripts/run_agentevals_ci.py

# Quick A2A test sweep (router + client)
.PHONY: test-a2a
test-a2a:
	PYTHONPATH=src $(PYTHON) -m pytest -q -c .config/pytest.ini -k "a2a_router or a2a_client or a2a_collections_json"

# Golden evaluation harness (fast path)
eval:
	eval-baseline:  ## Run agentevals against local baseline
	$(PYTHON) -m eval.runner datasets/golden/core/v1 benchmarks/baselines/golden/core/v1/summary.json || true

docs:
	@mkdir -p reports
	$(PYTHON) scripts/validate_docs.py && $(PYTHON) scripts/validate_config_docs.py && $(PYTHON) scripts/validate_dashboards.py && $(PYTHON) scripts/check_deprecations.py --json > reports/deprecations_report.json && $(PYTHON) scripts/update_deprecation_badge.py && PYTHONPATH=$$(pwd) $(PYTHON) scripts/generate_feature_flags_doc.py --check
	@echo "Deprecation scan JSON written to reports/deprecations_report.json"

# Convenience: feature flags doc check/write
.PHONY: docs-flags docs-flags-write
docs-flags:
	PYTHONPATH=$$(pwd) $(PYTHON) scripts/generate_feature_flags_doc.py --check

docs-flags-write:
	PYTHONPATH=$$(pwd) $(PYTHON) scripts/generate_feature_flags_doc.py --write

# Strict docs validation (fails on import issues in examples)
docs-strict:
	$(PYTHON) scripts/validate_docs.py --fail-imports --ignore-import-files "network_conventions.md,advanced-bandits-api.md,observability.md,tools_reference.md,enhanced_performance_monitoring_guide.md,performance_monitoring_integration.md" && $(PYTHON) scripts/validate_config_docs.py

# Ops: print queue backlog by tenant/workspace
ops-queue:
	@if [ -z "$(DB)" ]; then echo "Usage: make ops-queue DB=path/to/sched.db"; exit 2; fi
	$(PYTHON) scripts/ops_queue_status.py --db $(DB)

# Update README deprecations badge/section
deprecations-badge:
	$(PYTHON) scripts/update_deprecation_badge.py

deprecations-strict:
	$(PYTHON) scripts/check_deprecations.py --fail-on-upcoming 90

ci-all: doctor format-check lint type ci-type-guard guards test compliance deprecations-strict

guards:
	$(PYTHON) scripts/validate_dispatcher_usage.py && $(PYTHON) scripts/validate_http_wrappers_usage.py && $(PYTHON) scripts/metrics_instrumentation_guard.py && $(PYTHON) scripts/validate_tools_exports.py && $(PYTHON) scripts/guards/deprecated_directories_guard.py

deprecations:
	$(PYTHON) scripts/check_deprecations.py

deprecations-json:
	$(PYTHON) scripts/check_deprecations.py --json > /dev/stdout

# Remove typical transient build/test/cache artifacts
clean:
	@bash scripts/cleanup.sh
	@rm -rf reports/*.tmp ruff_results
	@rm -rf .gemini gha-creds-*.json
	@echo "Workspace cleaned"

# Preview cleanup without making changes
clean-dry-run:
	@bash scripts/cleanup.sh --dry-run

# Organize root directory by moving clutter to archive
organize-root:
	$(PYTHON) scripts/cleanup_root.py

# Maintain archive directory (compress old files, generate inventory)
maintain-archive:
	$(PYTHON) scripts/maintain_archive.py

# More aggressive: also remove virtual env & node_modules (opt-in)
deep-clean: clean
	rm -rf .venv venv node_modules
	echo "Deep clean completed (virtual envs & node_modules removed)"

# Ensure local virtual environment & editable install (wrapper around script)
ensure-venv:
	bash scripts/ensure_venv.sh

# Produce a fully pinned lock file with uv (faster/more reproducible than pip-tools)
uv-lock:
	@if ! command -v uv >/dev/null 2>&1; then echo "uv not installed (pip install uv)"; exit 2; fi
	uv pip compile pyproject.toml -o requirements.lock
	@echo "Generated requirements.lock"

# Synchronize environment exactly to requirements.lock
uv-sync: ensure-venv
	@if ! command -v uv >/dev/null 2>&1; then echo "uv not installed (pip install uv)"; exit 2; fi
	uv pip sync requirements.lock
	@echo "Environment synchronized from requirements.lock"

# One-shot bootstrap using uv (creates venv if missing, installs dev extras)
uv-bootstrap:
	@if ! command -v uv >/dev/null 2>&1; then echo "uv not installed (pip install uv)"; exit 2; fi
	@if [ ! -d .venv ]; then python3 -m venv .venv; fi
	. .venv/bin/activate && uv pip install -e '.[dev]'
	@echo "uv bootstrap complete"

# Compliance checks per Copilot instructions #3 and #8
.PHONY: compliance
compliance:  ## Run compliance audits (HTTP + StepResult)
	@cd src/ultimate_discord_intelligence_bot && python3 core/http_compliance_audit.py
	@cd src/ultimate_discord_intelligence_bot && python3 tools/step_result_auditor.py

.PHONY: compliance-fix
compliance-fix:  ## Auto-fix simple compliance issues
	@cd src/ultimate_discord_intelligence_bot && python3 tools/batch_stepresult_migration.py

.PHONY: compliance-summary
compliance-summary:  ## Generate compliance summary report
	@cd src/ultimate_discord_intelligence_bot && python3 tools/compliance_executive_summary.py

# Install / update common third-party stub packages + auto-install types for direct deps
.PHONY: types-install
types-install:
	@echo "[types-install] Installing common stub packages..."
	$(PYTHON) -m pip install --quiet --upgrade \
		types-psutil \
		types-jsonschema || true
	@echo "[types-install] Running mypy --install-types (non-interactive)..."
	$(PYTHON) -m mypy --install-types --non-interactive || true
	@echo "[types-install] Complete. Review newly added stub packages for pinning in pyproject if needed."

# Development workflow shortcuts
.PHONY: quick-check full-check setup-hooks
quick-check:  ## Run quick development checks (format + lint + test-fast)
	./scripts/dev-workflow.sh quick-check

full-check:  ## Run comprehensive checks (format + lint + type + test)
	./scripts/dev-workflow.sh full-check

setup-hooks:  ## Setup git hooks for automated quality checks
	./scripts/dev-workflow.sh setup-hooks

# Convenience: run the MCP server via stdio (enable feature flags as needed)
.PHONY: run-mcp
run-mcp:
	$(PYTHON) -c 'from mcp_server.server import main; import sys; sys.exit(main([]))'

# Run MCP-related tests if the optional fastmcp extra is installed; otherwise no-op gracefully
.PHONY: test-mcp
test-mcp:
	@if $(PYTHON) -c "import importlib.util,sys; sys.exit(0 if importlib.util.find_spec('fastmcp') is None else 1)"; then \
		echo "[test-mcp] fastmcp not installed; skipping MCP tests (install with 'pip install .[mcp]')"; \
	else \
		PYTHONPATH=src $(PYTHON) -m pytest -q -c .config/pytest.ini -k "mcp_"; \
	fi

# Demo: LangGraph pilot orchestration
.PHONY: run-langgraph-pilot
run-langgraph-pilot:
	@echo "Hint: set ENABLE_LANGGRAPH_PILOT=1 to exercise the completion metric path"; \
	$(PYTHON) demo_langgraph_pilot.py

# Demo: A2A client against running API service
.PHONY: run-a2a-client-demo
run-a2a-client-demo:
	@echo "Hint: ensure the API is running with ENABLE_A2A_API=1 (and ENABLE_A2A_API_KEY/A2A_API_KEY if needed)"; \
	@echo "Using A2A_BASE_URL=$${A2A_BASE_URL:-http://localhost:8000}"; \
	$(PYTHON) scripts/a2a_client_demo.py

# Smoke: MCP imports always safe (stub or real)
.PHONY: test-mcp-smoke
test-mcp-smoke:
	PYTHONPATH=src $(PYTHON) -m pytest -q -c .config/pytest.ini tests/test_mcp_imports.py

# Health monitoring targets
.PHONY: health
health:
	@echo "🔍 Running tool health monitoring..."
	$(PYTHON) scripts/tool_health_monitor.py

.PHONY: health-dashboard
health-dashboard:
	@echo "🚀 Starting health dashboard..."
	$(PYTHON) scripts/health_dashboard.py --console

.PHONY: health-report
health-report:
	@echo "📊 Generating health report..."
	@if [ -f tool_health_report.json ]; then \
		$(PYTHON) scripts/health_dashboard.py --console; \
	else \
		echo "No health report found. Run 'make health' first."; \
	fi

# Metrics monitoring targets
.PHONY: metrics
metrics:
	@echo "📊 Running metrics collection test..."
	$(PYTHON) scripts/test_metrics_collection.py

.PHONY: metrics-api
metrics-api:
	@echo "🌐 Starting metrics API server..."
	$(PYTHON) -c "from ultimate_discord_intelligence_bot.observability.metrics_api import run_metrics_api; run_metrics_api()"

.PHONY: metrics-dashboard
metrics-dashboard:
	@echo "📊 Starting metrics dashboard..."
	$(PYTHON) scripts/metrics_dashboard.py

.PHONY: metrics-test
metrics-test:
	@echo "🧪 Testing metrics collection system..."
	$(PYTHON) scripts/test_metrics_collection.py

# Enhanced metrics dashboard targets
.PHONY: enhanced-metrics
enhanced-metrics:
	@echo "🚀 Starting enhanced metrics dashboard..."
	$(PYTHON) scripts/enhanced_metrics_dashboard.py

.PHONY: enhanced-metrics-host
enhanced-metrics-host:
	@echo "🌐 Starting enhanced metrics dashboard on all interfaces..."
	$(PYTHON) scripts/enhanced_metrics_dashboard.py --host 0.0.0.0 --port 5002

.PHONY: enhanced-metrics-debug
enhanced-metrics-debug:
	@echo "🐛 Starting enhanced metrics dashboard in debug mode..."
	$(PYTHON) scripts/enhanced_metrics_dashboard.py --debug

# Lazy loading targets
.PHONY: lazy-loading-test
lazy-loading-test:
	@echo "⚡ Testing lazy loading system..."
	$(PYTHON) scripts/test_lazy_loading.py

.PHONY: lazy-loading-benchmark
lazy-loading-benchmark:
	@echo "📊 Running lazy loading benchmarks..."
	$(PYTHON) scripts/test_lazy_loading.py

.PHONY: lazy-loading-stats
lazy-loading-stats:
	@echo "📈 Getting lazy loading statistics..."
	$(PYTHON) -c "from ultimate_discord_intelligence_bot.tools.lazy_loader import get_lazy_loader_stats; import json; print(json.dumps(get_lazy_loader_stats(), indent=2))"

# Result caching targets
.PHONY: cache-test
cache-test:
	@echo "🧪 Testing result caching system..."
	$(PYTHON) scripts/test_result_caching.py

.PHONY: cache-benchmark
cache-benchmark:
	@echo "📊 Running cache performance benchmarks..."
	$(PYTHON) scripts/test_result_caching.py

.PHONY: cache-stats
cache-stats:
	@echo "📈 Getting cache statistics..."
	$(PYTHON) -c "from ultimate_discord_intelligence_bot.caching import get_cache_stats, analyze_cache_performance; import json; print('Basic Cache Stats:'); print(json.dumps(get_cache_stats(), indent=2)); print('\nSmart Cache Analysis:'); print(json.dumps(analyze_cache_performance(), indent=2))"

.PHONY: cache-optimize
cache-optimize:
	@echo "⚙️ Running cache optimization..."
	$(PYTHON) -c "from ultimate_discord_intelligence_bot.caching import auto_optimize_cache; auto_optimize_cache(); print('Cache optimization completed')"

.PHONY: cache-recommendations
cache-recommendations:
	@echo "💡 Getting cache recommendations..."
	$(PYTHON) -c "from ultimate_discord_intelligence_bot.caching import get_cache_recommendations; import json; print(json.dumps(get_cache_recommendations(), indent=2))"

# Memory optimization targets
.PHONY: memory-test
memory-test:
	@echo "🧪 Testing memory optimization system..."
	$(PYTHON) scripts/test_memory_optimization.py

.PHONY: memory-benchmark
memory-benchmark:
	@echo "📊 Running memory optimization benchmarks..."
	$(PYTHON) scripts/test_memory_optimization.py

.PHONY: memory-stats
memory-stats:
	@echo "📈 Getting memory optimization statistics..."
	$(PYTHON) -c "from ultimate_discord_intelligence_bot.optimization import get_memory_stats, analyze_memory_usage; import json; print('Memory Stats:'); print(json.dumps(get_memory_stats(), indent=2)); print('\nMemory Analysis:'); print(json.dumps(analyze_memory_usage(), indent=2))"

.PHONY: memory-optimize
memory-optimize:
	@echo "⚙️ Running memory optimization..."
	$(PYTHON) -c "from ultimate_discord_intelligence_bot.optimization import optimize_memory; import json; result = optimize_memory(); print(json.dumps(result, indent=2))"

.PHONY: memory-analyze
memory-analyze:
	@echo "🔍 Analyzing memory usage patterns..."
	$(PYTHON) -c "from ultimate_discord_intelligence_bot.optimization import analyze_memory_usage; import json; print(json.dumps(analyze_memory_usage(), indent=2))"
