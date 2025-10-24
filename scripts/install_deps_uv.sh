#!/bin/bash
# Optimized dependency installation with uv

set -e

echo "🚀 Installing dependencies with uv (faster than pip)..."

# Install uv if not present
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    pip install uv
fi

# Use uv for faster dependency resolution
echo "Resolving dependencies with uv..."
uv pip install -e .[dev]

echo "✅ Dependencies installed successfully with uv"
