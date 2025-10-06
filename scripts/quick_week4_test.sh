#!/usr/bin/env bash
# Week 4 Quick Validation Runner
# Runs Phase 2 optimization validation tests

set -e

cd "$(dirname "$0")/.."

echo "🚀 Week 4 Production Validation"
echo "==============================="
echo ""

# Check if URL provided
URL="${1:-https://www.youtube.com/watch?v=xtFiJ8AVdW0}"
ITERATIONS="${2:-3}"

echo "📹 URL: $URL"
echo "🔁 Iterations: $ITERATIONS"
echo ""

# Run validation
.venv/bin/python scripts/run_week4_validation.py "$URL" "$ITERATIONS"

echo ""
echo "✅ Validation complete!"
echo ""
echo "📊 Next steps:"
echo "  1. Review results in benchmarks/week4_validation_*.json"
echo "  2. Run analysis: python scripts/week4_analysis.py benchmarks/"
echo "  3. If targets met, proceed to production deployment"
