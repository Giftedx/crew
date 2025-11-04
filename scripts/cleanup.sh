#!/usr/bin/env bash
# Comprehensive cleanup script for the crew codebase
# Usage: ./scripts/cleanup.sh [--dry-run]

set -euo pipefail

DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=true
    echo "🔍 DRY RUN MODE - No files will be deleted"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

echo "🧹 Starting cleanup of crew codebase..."
echo "📁 Project root: ${PROJECT_ROOT}"
echo ""

# Function to remove files/directories
cleanup_item() {
    local item="$1"
    local description="$2"

    if [[ -e "${item}" ]]; then
        if [[ "${DRY_RUN}" == "true" ]]; then
            echo "  [DRY RUN] Would remove: ${item}"
        else
            rm -rf "${item}"
            echo "  ✓ Removed: ${description}"
        fi
    fi
}

# 1. Python artifacts
echo "🐍 Cleaning Python artifacts..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
find . -type f -name "*.pyd" -delete 2>/dev/null || true
echo "  ✓ Removed all __pycache__, .pyc, .pyo, .pyd files"

# 2. Test and coverage caches
echo "🧪 Cleaning test and coverage artifacts..."
cleanup_item ".pytest_cache" "pytest cache"
cleanup_item ".coverage" "coverage data"
cleanup_item "coverage.xml" "coverage XML"
cleanup_item "htmlcov" "HTML coverage report"
cleanup_item ".tox" "tox cache"

# 3. Type checker and linter caches
echo "🔍 Cleaning type checker and linter caches..."
cleanup_item ".mypy_cache" "mypy cache"
cleanup_item ".ruff_cache" "ruff cache"
cleanup_item "pyrightcache" "pyright cache"

# 4. Build artifacts
echo "📦 Cleaning build artifacts..."
cleanup_item "build" "build directory"
cleanup_item "dist" "dist directory"
find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
echo "  ✓ Removed build and dist directories"

# 5. IDE and editor files
echo "💻 Cleaning IDE artifacts..."
cleanup_item ".DS_Store" "macOS files"
find . -name ".DS_Store" -delete 2>/dev/null || true
find . -name "*.swp" -delete 2>/dev/null || true
find . -name "*.swo" -delete 2>/dev/null || true
find . -name "*~" -delete 2>/dev/null || true
echo "  ✓ Removed IDE and editor temp files"

# 6. PID files
echo "🔒 Cleaning PID files..."
find . -name "*.pid" -delete 2>/dev/null || true
echo "  ✓ Removed PID files"

# 7. Log files (excluding organized log directories)
echo "📝 Cleaning loose log files..."
find . -maxdepth 1 -name "*.log" -delete 2>/dev/null || true
echo "  ✓ Removed root-level log files"

# 8. Temporary files
echo "🗑️  Cleaning temporary files..."
find . -name "*.tmp" -delete 2>/dev/null || true
find . -name "*.bak" -delete 2>/dev/null || true
find . -name "*.orig" -delete 2>/dev/null || true
echo "  ✓ Removed temporary files"

# 9. Node artifacts (if any)
echo "📦 Cleaning Node artifacts..."
cleanup_item "node_modules" "node_modules"
find . -name "package-lock.json" -not -path "*/node_modules/*" -delete 2>/dev/null || true
echo "  ✓ Checked for Node artifacts"

# 10. Jupyter notebook checkpoints
echo "📓 Cleaning Jupyter checkpoints..."
find . -type d -name ".ipynb_checkpoints" -exec rm -rf {} + 2>/dev/null || true
echo "  ✓ Removed Jupyter checkpoints"

echo ""
echo "✨ Cleanup complete!"
echo ""
echo "💡 Tip: Run './scripts/cleanup.sh --dry-run' to preview changes"
