#!/usr/bin/env bash
# Week 3 Phase 1 Fix - Quick Test
# Tests Combination 4 with optimized parallel fact-checking (2 tasks instead of 5)

set -e  # Exit on error

echo "========================================="
echo "Phase 1 Fix - Quick Test"
echo "========================================="
echo ""
echo "Changes implemented:"
echo "  - Reduced parallel fact-check tasks: 5 → 2 (60% reduction)"
echo "  - Updated claim extraction: 5 → 2 claims"
echo "  - Enhanced logging in FactCheckTool"
echo ""
echo "Expected outcome:"
echo "  - Execution time: 4-6 minutes (NOT 36 minutes!)"
echo "  - No cascading retry delays"
echo "  - Clear backend success/failure logging"
echo ""
echo "========================================="
echo ""

# Enable parallel fact-checking
export ENABLE_PARALLEL_FACT_CHECKING=1

# Run single iteration
echo "Starting test at $(date '+%H:%M:%S')..."
echo ""

time python scripts/benchmark_autointel_flags.py \
  --url "https://www.youtube.com/watch?v=xtFiJ8AVdW0" \
  --combinations 4 \
  --iterations 1

echo ""
echo "========================================="
echo "Test completed at $(date '+%H:%M:%S')"
echo "========================================="
echo ""
echo "Next steps:"
echo "  1. Check execution time above (should be 4-6 minutes)"
echo "  2. Review logs for:"
echo "     - 'FactCheckTool: Checking claim' (should see 2 occurrences)"
echo "     - Backend success/failure patterns"
echo "     - No '429 Too Many Requests' or cascading retries"
echo "  3. If successful, run full validation:"
echo "     ./scripts/test_phase1_full.sh"
echo ""
