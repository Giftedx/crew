#!/bin/bash
# Virtual Environment Optimization Script
# Ultimate Discord Intelligence Bot
# Created: October 17, 2025

set -e

echo "🔧 Optimizing Python virtual environment..."

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ No venv directory found!"
    exit 1
fi

# Function to clean pip cache
clean_pip_cache() {
    echo "→ Cleaning pip cache..."
    if [ -d "venv/pip-cache" ]; then
        rm -rf venv/pip-cache
    fi
    venv/bin/python -m pip cache purge 2>/dev/null || true
    echo "  ✓ Pip cache cleaned"
}

# Function to remove unnecessary files
clean_venv_extras() {
    echo "→ Removing unnecessary files..."
    find venv -name "*.pyc" -delete 2>/dev/null || true
    find venv -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    find venv -name "*.dist-info" -type d -path "*/tests/*" -exec rm -rf {} + 2>/dev/null || true
    echo "  ✓ Unnecessary files removed"
}

# Show before size
echo ""
echo "📊 Before optimization:"
du -sh venv/

# Run optimization
clean_pip_cache
clean_venv_extras

# Compact if requested
if [[ "$1" == "--compact" ]]; then
    echo "→ Compacting site-packages..."
    venv/bin/python -m compileall -q venv/lib 2>/dev/null || true
    echo "  ✓ Site-packages compacted"
fi

# Show after size
echo ""
echo "📊 After optimization:"
du -sh venv/

echo ""
echo "✅ Virtual environment optimized!"
echo ""
echo "💡 Run with --compact for additional compression"
