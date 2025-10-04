# Flag Combination Validation Results

**Generated:** 2025-10-04T23:42:12.502241
**Baseline Mean:** 629.00s (10.48 min)

---

## Summary Table

| Combination | Name | Mean Time | vs Baseline | Expected Savings | Actual Savings | Status |
|-------------|------|-----------|-------------|------------------|----------------|--------|
| 4 | fact_checking_only | 6.45 min | +4.03 min | 0.5-1.0 min | 4.03 min | ⚠️ Partial |

---

## Detailed Statistics

### Combination 4: fact_checking_only

**Description:** Fact-checking parallelization only

**Flags:**
- ENABLE_PARALLEL_MEMORY_OPS: 0
- ENABLE_PARALLEL_ANALYSIS: 0
- ENABLE_PARALLEL_FACT_CHECKING: 1

**Statistics:**
- Iterations: 1
- Mean: 387.14s (6.45 min)
- Median: 387.14s (6.45 min)
- Min: 387.14s (6.45 min)
- Max: 387.14s (6.45 min)
- Std Dev: 0.00s
