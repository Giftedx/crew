# Flag Combination Validation Results

**Generated:** 2025-10-05T00:44:05.114475
**Baseline Mean:** 629.00s (10.48 min)

---

## Summary Table

| Combination | Name | Mean Time | vs Baseline | Expected Savings | Actual Savings | Status |
|-------------|------|-----------|-------------|------------------|----------------|--------|
| 2 | memory_only | 5.91 min | +4.57 min | 0.5-1.0 min | 4.57 min | ⚠️ Partial |

---

## Detailed Statistics

### Combination 2: memory_only

**Description:** Memory operations parallelization only

**Flags:**
- ENABLE_PARALLEL_MEMORY_OPS: 1
- ENABLE_PARALLEL_ANALYSIS: 0
- ENABLE_PARALLEL_FACT_CHECKING: 0

**Statistics:**
- Iterations: 3
- Mean: 354.83s (5.91 min)
- Median: 360.95s (6.02 min)
- Min: 273.43s (4.56 min)
- Max: 430.10s (7.17 min)
- Std Dev: 64.11s
