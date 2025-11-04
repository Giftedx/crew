#!/bin/bash
# Phase 2 Test 3: Combined Optimization (Semantic Cache + Prompt Compression)
# This script runs the benchmark with both optimizations enabled

set -e
cd /home/crew

echo "🚀 Starting Phase 2 Test 3: Combined Optimization"
echo "Configuration: ENABLE_SEMANTIC_CACHE=1, ENABLE_PROMPT_COMPRESSION=1"
echo "Expected: 30-40% improvement (2.84 min → 1.7-2.0 min)"
echo ""

# Set environment variables
export ENABLE_SEMANTIC_CACHE=1
export ENABLE_PROMPT_COMPRESSION=1
export ENABLE_PARALLEL_MEMORY_OPS=0
export ENABLE_PARALLEL_ANALYSIS=0
export ENABLE_PARALLEL_FACT_CHECKING=0

# Run benchmark with timeout
timeout 45m .venv/bin/python scripts/benchmark_autointel_flags.py \
  --url "https://www.youtube.com/watch?v=xtFiJ8AVdW0" \
  --depth experimental \
  --iterations 3 \
  --combinations 1 \
  > benchmarks/phase2_combined_optimization.log 2>&1

echo "✅ Phase 2 Test 3 completed - check benchmarks/phase2_combined_optimization.log for results"
