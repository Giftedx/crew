#!/usr/bin/env bash
# Week 4 Phase 2 Full Testing Script
# Comprehensive testing of all optimizations with multiple iterations

set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_DIR="benchmarks/week4_full_test_${TIMESTAMP}"
BASELINE_URL="https://www.youtube.com/watch?v=xtFiJ8AVdW0"

echo "🚀 Week 4 Phase 2 Full Testing Suite"
echo "===================================="
echo ""
echo "📅 Timestamp: ${TIMESTAMP}"
echo "📁 Results Dir: ${RESULTS_DIR}"
echo "🎯 Baseline URL: ${BASELINE_URL}"
echo ""

# Create results directory
mkdir -p "${RESULTS_DIR}"

# Test 1: Quality Filtering (5 iterations)
echo "📊 Test 1: Quality Filtering (5 iterations)"
echo "Expected: 45-62% improvement"
echo ""
python benchmarks/performance_benchmarks.py \
  --suite week4_algorithmic_optimization \
  --test quality_filtering \
  --iterations 5 \
  --url "${BASELINE_URL}" \
  2>&1 | tee "${RESULTS_DIR}/quality_filtering.log"

# Test 2: Content Type Routing (5 iterations)
echo ""
echo "📊 Test 2: Content Type Routing (5 iterations)"
echo "Expected: 15-25% improvement"
echo ""
python benchmarks/performance_benchmarks.py \
  --suite week4_algorithmic_optimization \
  --test content_routing \
  --iterations 5 \
  --url "${BASELINE_URL}" \
  2>&1 | tee "${RESULTS_DIR}/content_routing.log"

# Test 3: Early Exit Conditions (5 iterations)
echo ""
echo "📊 Test 3: Early Exit Conditions (5 iterations)"
echo "Expected: 20-25% improvement"
echo ""
python benchmarks/performance_benchmarks.py \
  --suite week4_algorithmic_optimization \
  --test early_exit \
  --iterations 5 \
  --url "${BASELINE_URL}" \
  2>&1 | tee "${RESULTS_DIR}/early_exit.log"

# Test 4: Combined Optimization (10 iterations)
echo ""
echo "📊 Test 4: Combined Optimization (10 iterations)"
echo "Expected: 65-80% improvement"
echo ""
python benchmarks/performance_benchmarks.py \
  --suite week4_algorithmic_optimization \
  --test combined \
  --iterations 10 \
  --url "${BASELINE_URL}" \
  2>&1 | tee "${RESULTS_DIR}/combined.log"

# Test 5: Multi-Content Type Validation
echo ""
echo "📊 Test 5: Multi-Content Type Validation"
echo "Testing with different content types"
echo ""

# Array of test URLs (update with real URLs)
DISCUSSION_URL="https://www.youtube.com/watch?v=discussion_example"
ENTERTAINMENT_URL="https://www.youtube.com/watch?v=entertainment_example"
NEWS_URL="https://www.youtube.com/watch?v=news_example"

# For now, use the same URL 3 times (update when real URLs available)
for content_type in discussion entertainment news; do
  echo "Testing ${content_type} content..."
  python benchmarks/performance_benchmarks.py \
    --suite week4_content_type_validation \
    --test "${content_type}" \
    --iterations 2 \
    --url "${BASELINE_URL}" \
    2>&1 | tee "${RESULTS_DIR}/${content_type}_validation.log"
done

# Aggregate results
echo ""
echo "📈 Aggregating Results"
echo "====================="
echo ""

# Copy week4 results to aggregated location
cp benchmarks/week4_results_*.json "${RESULTS_DIR}/" 2>/dev/null || true
cp benchmarks/week4_summary_*.md "${RESULTS_DIR}/" 2>/dev/null || true
cp benchmarks/week4_direct_validation_*.json "${RESULTS_DIR}/" 2>/dev/null || true

# Generate summary report
cat > "${RESULTS_DIR}/SUMMARY.md" <<EOF
# Week 4 Full Testing Summary

**Generated**: $(date)
**Test Suite**: Week 4 Phase 2 Full Validation
**Total Tests**: 25 (5 + 5 + 5 + 10)

## Test Breakdown

### Quality Filtering
- Iterations: 5
- Expected: 45-62% improvement
- Log: quality_filtering.log

### Content Type Routing
- Iterations: 5
- Expected: 15-25% improvement
- Log: content_routing.log

### Early Exit Conditions
- Iterations: 5
- Expected: 20-25% improvement
- Log: early_exit.log

### Combined Optimization
- Iterations: 10
- Expected: 65-80% improvement
- Log: combined.log

### Content Type Validation
- Discussion: 2 iterations
- Entertainment: 2 iterations
- News: 2 iterations

## Files Generated

\`\`\`
${RESULTS_DIR}/
├── quality_filtering.log
├── content_routing.log
├── early_exit.log
├── combined.log
├── discussion_validation.log
├── entertainment_validation.log
├── news_validation.log
├── week4_results_*.json
├── week4_summary_*.md
└── SUMMARY.md
\`\`\`

## Next Steps

1. Analyze aggregated results
2. Compare against targets
3. Generate configuration recommendations
4. Update deployment guide
5. Proceed to A/B testing

EOF

echo "✅ Testing Complete!"
echo ""
echo "📂 Results: ${RESULTS_DIR}"
echo "📄 Summary: ${RESULTS_DIR}/SUMMARY.md"
echo ""
echo "🔍 Review Results:"
echo "  cat ${RESULTS_DIR}/SUMMARY.md"
echo "  ls -lh ${RESULTS_DIR}/"
echo ""
echo "📊 Next: Analyze results and tune thresholds"
