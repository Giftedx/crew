#!/bin/bash
# Wrapper script to run autointel diagnostic with proper Python environment
#
# Usage:
#   ./run_autointel_test.sh [url] [depth]
#
# Examples:
#   ./run_autointel_test.sh
#   ./run_autointel_test.sh https://www.youtube.com/watch?v=xtFiJ8AVdW0
#   ./run_autointel_test.sh https://www.youtube.com/watch?v=xtFiJ8AVdW0 experimental

cd "$(dirname "$0")"

# Check if venv exists
if [ ! -d ".venv" ]; then
    echo "❌ Error: .venv directory not found"
    echo "Please run: python3 -m venv .venv && .venv/bin/pip install -r requirements.lock"
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found"
    echo "Copy .env.example to .env and configure your API keys"
fi

# Run with proper Python and PYTHONPATH
echo "🚀 Running autointel diagnostic with venv Python..."
echo ""
PYTHONPATH=/home/crew/src .venv/bin/python3 scripts/diagnose_autointel.py "$@"
