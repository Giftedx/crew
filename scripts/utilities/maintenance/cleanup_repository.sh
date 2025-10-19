#!/bin/bash
# Repository Cleanup Script
# Ultimate Discord Intelligence Bot
# Created: October 17, 2025

set -e

echo "🧹 Starting repository cleanup..."

# Function to clean Python cache
clean_python_cache() {
    echo "→ Cleaning Python cache..."
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    find . -type f -name "*.pyo" -delete 2>/dev/null || true
    echo "  ✓ Python cache cleaned"
}

# Function to clean temporary files
clean_temp_files() {
    echo "→ Cleaning temporary files..."
    find . -type f -name "*.tmp" -delete 2>/dev/null || true
    find . -type f -name "*.swp" -delete 2>/dev/null || true
    find . -type f -name "*~" -delete 2>/dev/null || true
    find . -type f -name ".DS_Store" -delete 2>/dev/null || true
    echo "  ✓ Temporary files cleaned"
}

# Function to organize logs
organize_logs() {
    echo "→ Organizing log files..."
    if [ -d "archive/logs" ]; then
        find . -name "*.log" -not -path "./archive/*" -not -path "./venv/*" \
            -exec mv {} archive/logs/ 2>/dev/null \; || true
        echo "  ✓ Logs organized"
    fi
}

# Function to show directory sizes
show_sizes() {
    echo ""
    echo "📊 Directory sizes:"
    du -sh */ 2>/dev/null | sort -rh | head -10
}

# Main cleanup
echo ""
clean_python_cache
clean_temp_files
organize_logs

# Optional: Remove empty directories
if [[ "$1" == "--remove-empty" ]]; then
    echo "→ Removing empty directories..."
    find . -type d -empty -not -path "./venv/*" -not -path "./.git/*" \
        -delete 2>/dev/null || true
    echo "  ✓ Empty directories removed"
fi

# Show results
echo ""
echo "✅ Cleanup complete!"
show_sizes

echo ""
echo "💡 Run with --remove-empty to also remove empty directories"
