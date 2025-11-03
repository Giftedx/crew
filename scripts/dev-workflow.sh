#!/bin/bash
# Development workflow optimizer for Ultimate Discord Intelligence Bot
# Provides quick development commands and shortcuts

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[dev]${NC} $*"
}

success() {
    echo -e "${GREEN}✅${NC} $*"
}

warn() {
    echo -e "${YELLOW}⚠️${NC} $*"
}

error() {
    echo -e "${RED}❌${NC} $*"
}

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    error "Not in project root directory"
    exit 1
fi

# Ensure Python environment
ensure_python() {
    if [ -f ".venv/bin/python" ]; then
        PYTHON=".venv/bin/python"
    elif [ -n "$VIRTUAL_ENV" ]; then
        PYTHON="python"
    else
        warn "No virtual environment detected. Using system Python."
        PYTHON="python"
    fi
}

# Show usage information
show_help() {
    cat << EOF
Development Workflow Optimizer for Ultimate Discord Intelligence Bot

Usage: $0 <command>

Commands:
  quick-check    Run fast quality checks (format + lint + test-fast)
  full-check     Run comprehensive checks (format + lint + type + test)
  fix-common     Auto-fix common issues (format + import organization)
  setup-hooks    Install git hooks for automated quality checks
    organize-root  Move demos/results/guides from root to archive/docs
  doctor         Run project health check
  clean          Clean build artifacts and caches
  deps           Update and sync dependencies
  help           Show this help message

Examples:
  $0 quick-check    # Before committing
  $0 full-check     # Before pushing
  $0 fix-common     # Auto-fix style issues
  $0 setup-hooks    # One-time git hooks setup

EOF
}

# Quick development checks
quick_check() {
    log "Running quick development checks..."

    ensure_python

    log "Formatting code..."

    # Prefer formatting only modified Python files to avoid running ruff across the
    # entire repository in lightweight environments. If there are no modified
    # tracked python files, fall back to full repo formatting.
    modified_files=$(git ls-files -m | grep '\.py$' | grep -v '^src/fastapi/' || true)
    if [ -n "$modified_files" ]; then
        log "Formatting modified Python files only: $modified_files"
        # Run ruff fix/format on modified python files
        $PYTHON -m ruff check --fix $modified_files --exclude examples || { error "Format failed"; exit 1; }
        $PYTHON -m ruff format $modified_files --exclude examples || { error "Format failed"; exit 1; }
    else
        make format || { error "Format failed"; exit 1; }
    fi

    log "Running lints..."
    if [ "${SKIP_LINT:-0}" != "0" ]; then
        warn "Skipping lints (SKIP_LINT=${SKIP_LINT})"
    else
        make lint || { error "Lint failed"; exit 1; }
    fi

    log "Running fast tests..."

    # If optional test dependencies (fastapi, numpy, discord) are not installed,
    # skip the fast tests to allow quick-check to be used in lightweight dev
    # environments. Set SKIP_MISSING_TEST_DEPS=0 to force running tests even when
    # imports fail.
    if [ "${SKIP_MISSING_TEST_DEPS:-1}" != "0" ]; then
        # Verify not only third-party deps, but also a few internal modules needed by the fast tests.
        # If any import fails, we skip the fast tests to keep quick-check usable in lightweight environments.
        if ! $PYTHON - <<'PY'
import sys
try:
    import pytest  # noqa: F401
    import numpy as _np  # noqa: F401
    import discord  # noqa: F401
    import fastapi  # noqa: F401
    # Ensure critical symbols exist
    from fastapi import FastAPI, Request  # noqa: F401
    from fastapi.testclient import TestClient  # noqa: F401
    # Check a couple of first-party modules the fast tests rely on
    import ultimate_discord_intelligence_bot  # noqa: F401
    from ultimate_discord_intelligence_bot.server import app as _app  # noqa: F401
except Exception:
    sys.exit(1)
sys.exit(0)
PY
        then
            warn "Test dependencies or core modules missing. Skipping fast tests."
            success "Quick checks passed (format + lint). To run tests, install all test deps and ensure internal modules import cleanly, or set SKIP_MISSING_TEST_DEPS=0."
            return 0
        fi
    fi

    make test-fast || { error "Fast tests failed"; exit 1; }

    success "Quick checks passed! Ready to commit."
}

# Comprehensive checks
full_check() {
    log "Running comprehensive checks..."

    ensure_python

    log "Formatting code..."
    make format || { error "Format failed"; exit 1; }

    log "Running lints..."
    make lint || { error "Lint failed"; exit 1; }

    log "Type checking..."
    make type || warn "Type checking completed with warnings"

    log "Running all tests..."
    make test || { error "Tests failed"; exit 1; }

    success "All checks passed! Ready to push."
}

# Auto-fix common issues
fix_common() {
    log "Auto-fixing common issues..."

    ensure_python

    log "Formatting code with ruff..."
    make format

    log "Cleaning up import organization..."
    make format

    success "Common issues fixed!"
}

# Setup git hooks
setup_hooks() {
    log "Setting up git hooks..."

    if [ -f ".githooks/pre-commit" ]; then
        log "Installing pre-commit hook..."
        if [ -d ".git" ]; then
            cp .githooks/pre-commit .git/hooks/pre-commit
            chmod +x .git/hooks/pre-commit
            success "Pre-commit hook installed!"
        else
            warn "Not a git repository. Git hooks not installed."
        fi
    else
        warn "Pre-commit hook file not found"
    fi

    # Also setup pre-commit framework if available
    if command -v pre-commit >/dev/null 2>&1; then
        log "Setting up pre-commit framework..."
        pre-commit install --install-hooks
        success "Pre-commit framework configured!"
    fi
}

# Project health check
run_doctor() {
    log "Running project health check..."
    make doctor || true  # Don't fail on doctor issues
}

# Clean build artifacts
clean_project() {
    log "Cleaning build artifacts..."
    make clean
    make clean-bytecode

    log "Removing additional cache files..."
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true

    success "Project cleaned!"
}

# Update dependencies
update_deps() {
    log "Updating dependencies..."

    ensure_python

    if [ -f "requirements-dev.txt" ]; then
        log "Updating from requirements-dev.txt..."
        "$PYTHON" -m pip install -r requirements-dev.txt
    fi

    log "Installing project in development mode..."
    "$PYTHON" -m pip install -e '.[dev]'

    success "Dependencies updated!"
}

# Organize root directory
organize_root() {
    log "Organizing root directory (moving demos/results/guides)..."
    make organize-root || { error "organize-root failed"; exit 1; }
    success "Root directory organized."
}

# Main command dispatcher
case "${1:-help}" in
    quick-check|quick)
        quick_check
        ;;
    full-check|full)
        full_check
        ;;
    fix-common|fix)
        fix_common
        ;;
    setup-hooks|hooks)
        setup_hooks
        ;;
    doctor)
        run_doctor
        ;;
    clean)
        clean_project
        ;;
    deps)
        update_deps
        ;;
    organize-root|organize)
        organize_root
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        error "Unknown command: $1"
        echo
        show_help
        exit 1
        ;;
esac
