# Evaluation Harness

This repository ships a lightweight evaluation harness with tiny public-safe fixtures.
Run the suite against the core dataset and compare against the baseline to catch regressions in quality, cost, and latency.

## Usage

```bash
python -m eval.runner datasets/golden/core/v1 benchmarks/baselines/golden/core/v1/summary.json
```

Use `scripts/update_baseline.sh` to refresh the baseline after intentional improvements.
