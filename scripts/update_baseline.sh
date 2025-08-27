#!/usr/bin/env bash
set -euo pipefail
RESULT_JSON="$1"
DATASET_KEY="$2"
QUALITY=$(jq '.aggregates.quality' "$RESULT_JSON")
COST=$(jq '.aggregates.cost_usd' "$RESULT_JSON")
LATENCY=$(jq '.aggregates.latency_ms' "$RESULT_JSON")
LAMBD=$(jq '.aggregates.lambda' "$RESULT_JSON")
MU=$(jq '.aggregates.mu' "$RESULT_JSON")
cat <<YAML > benchmarks/baselines.yaml
$DATASET_KEY:
  quality: $QUALITY
  cost_usd: $COST
  latency_ms: $LATENCY
  lambda: $LAMBD
  mu: $MU
YAML
