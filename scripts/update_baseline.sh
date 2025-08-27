#!/usr/bin/env bash
set -euo pipefail

REPORT=${1:-reports/eval/latest.json}
BASELINE=${2:-baselines/golden/core/v1/summary.json}
mkdir -p "$(dirname "$BASELINE")"
cp "$REPORT" "$BASELINE"
echo "Baseline updated: $BASELINE"
