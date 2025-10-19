# Flag Combination Validation Results

**Generated:** 2025-10-05T00:05:44.005205
**Baseline Mean:** 629.00s (10.48 min)

---

## Summary Table

| Combination | Name | Mean Time | vs Baseline | Expected Savings | Actual Savings | Status |
|-------------|------|-----------|-------------|------------------|----------------|--------|
| 4 | fact_checking_only | 5.00 min | +5.49 min | 0.5-1.0 min | 5.49 min | ⚠️ Partial |

---

## Detailed Statistics

### Combination 4: fact_checking_only

**Description:** Fact-checking parallelization only

**Flags:**
- ENABLE_PARALLEL_MEMORY_OPS: 0
- ENABLE_PARALLEL_ANALYSIS: 0
- ENABLE_PARALLEL_FACT_CHECKING: 1

**Statistics:**
- Iterations: 3
- Mean: 299.76s (5.00 min)
- Median: 296.12s (4.94 min)
- Min: 240.51s (4.01 min)
- Max: 362.65s (6.04 min)
- Std Dev: 49.93s
