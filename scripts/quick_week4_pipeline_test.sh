#!/bin/bash
#
# Quick wrapper for Week 4 ContentPipeline validation
# Usage: ./scripts/quick_week4_pipeline_test.sh [URL] [ITERATIONS]
#

URL="${1:-https://www.youtube.com/watch?v=xtFiJ8AVdW0}"
ITERATIONS="${2:-1}"

echo "🚀 Week 4 ContentPipeline Validation"
echo "   URL: $URL"
echo "   Iterations: $ITERATIONS"
echo ""

# Activate venv and run
.venv/bin/python scripts/run_week4_validation_pipeline.py "$URL" -i "$ITERATIONS"
