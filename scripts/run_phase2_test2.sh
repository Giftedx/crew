#!/bin/bash
# Phase 2 Test 2: Prompt Compression Only
# This script runs the benchmark with compression enabled but cache disabled

set -e
cd /home/crew

echo "🧪 Starting Phase 2 Test 2: Prompt Compression Only"
echo "Configuration: ENABLE_PROMPT_COMPRESSION=1, ENABLE_SEMANTIC_CACHE=0"
echo "Expected: 10-20% improvement (2.84 min → 2.3-2.6 min)"
echo ""

# Set environment variables
export ENABLE_SEMANTIC_CACHE=0
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
  > benchmarks/phase2_prompt_compression.log 2>&1

echo "✅ Phase 2 Test 2 completed - check benchmarks/phase2_prompt_compression.log for results"
