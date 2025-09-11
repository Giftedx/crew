# Ultimate Discord Intelligence Bot - Makefile
# Compliance and quality checks per Copilot instructions

.PHONY: help
help:  ## Show this help
    @grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Compliance checks per instructions #3 and #8
.PHONY: compliance
compliance:  ## Run compliance audits (HTTP + StepResult)
    @echo "🔍 Running HTTP compliance check (Instruction #8)..."
    @python3 core/http_compliance_audit.py
    @echo ""
    @echo "🔍 Running StepResult pattern check (Instruction #3)..."
    @python3 tools/step_result_auditor.py

.PHONY: compliance-fix
compliance-fix:  ## Auto-fix simple compliance issues
    @echo "🔧 Attempting auto-fixes for StepResult pattern..."
    @python3 tools/batch_stepresult_migration.py

.PHONY: compliance-summary
compliance-summary:  ## Generate compliance summary report
    @python3 tools/compliance_summary.py

.PHONY: guards
guards: compliance  ## Enforce compliance (fail on violations)
    @echo "✅ All guards passed"

.PHONY: format
format:  ## Format code with black and isort
    @echo "🎨 Formatting code..."
    @black . --line-length 120
    @isort . --profile black --line-length 120

.PHONY: lint
lint:  ## Run linting checks
    @echo "🔍 Running linters..."
    @flake8 . --max-line-length 120
    @pylint src/

.PHONY: type
type:  ## Run type checking with mypy
    @echo "🔍 Type checking..."
    @mypy src/ --config-file mypy.ini

.PHONY: test-fast
test-fast:  ## Run fast unit tests
    @echo "🧪 Running fast tests..."
    @pytest tests/ -v --tb=short -m "not slow"

.PHONY: test
test:  ## Run all tests
    @echo "🧪 Running all tests..."
    @pytest tests/ -v --tb=short

.PHONY: clean
clean:  ## Clean build artifacts
    @echo "🧹 Cleaning..."
    @find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    @find . -type f -name "*.pyc" -delete
    @find . -type f -name "*.pyo" -delete
    @rm -rf build/ dist/ *.egg-info .pytest_cache/ .mypy_cache/

.PHONY: install-dev
install-dev:  ## Install development dependencies
    @echo "📦 Installing development dependencies..."
    @pip install -e '.[dev]'

.PHONY: docs
docs:  ## Generate documentation
    @echo "📚 Generating docs..."
    @python3 -m mkdocs build

# Default target
.DEFAULT_GOAL := help
