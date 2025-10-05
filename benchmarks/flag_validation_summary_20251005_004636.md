# Flag Combination Validation Results

**Generated:** 2025-10-05T01:23:10.528850
**Baseline Mean:** 629.00s (10.48 min)

---

## Summary Table

| Combination | Name | Mean Time | vs Baseline | Expected Savings | Actual Savings | Status |
|-------------|------|-----------|-------------|------------------|----------------|--------|
| 3 | analysis_only | 12.19 min | -1.70 min | 1.0-2.0 min | -1.70 min | ❌ Fail |

---

## Detailed Statistics

### Combination 3: analysis_only

**Description:** Analysis subtasks parallelization only

**Flags:**
- ENABLE_PARALLEL_MEMORY_OPS: 0
- ENABLE_PARALLEL_ANALYSIS: 1
- ENABLE_PARALLEL_FACT_CHECKING: 0

**Statistics:**
- Iterations: 3
- Mean: 731.22s (12.19 min)
- Median: 615.31s (10.26 min)
- Min: 289.60s (4.83 min)
- Max: 1288.75s (21.48 min)
- Std Dev: 416.05s
