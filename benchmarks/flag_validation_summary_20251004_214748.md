# Flag Combination Validation Results

**Generated:** 2025-10-04T23:18:53.350936
**Baseline Mean:** 629.00s (10.48 min)

---

## Summary Table

| Combination | Name | Mean Time | vs Baseline | Expected Savings | Actual Savings | Status |
|-------------|------|-----------|-------------|------------------|----------------|--------|
| 2 | memory_only | 6.96 min | +3.53 min | 0.5-1.0 min | 3.53 min | ⚠️ Partial |
| 3 | analysis_only | 4.60 min | +5.88 min | 1.0-2.0 min | 5.88 min | ⚠️ Partial |
| 4 | fact_checking_only | 18.80 min | -8.32 min | 0.5-1.0 min | -8.32 min | ❌ Fail |

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
- Mean: 417.49s (6.96 min)
- Median: 485.08s (8.08 min)
- Min: 260.94s (4.35 min)
- Max: 506.44s (8.44 min)
- Std Dev: 111.04s

### Combination 3: analysis_only

**Description:** Analysis subtasks parallelization only

**Flags:**
- ENABLE_PARALLEL_MEMORY_OPS: 0
- ENABLE_PARALLEL_ANALYSIS: 1
- ENABLE_PARALLEL_FACT_CHECKING: 0

**Statistics:**
- Iterations: 3
- Mean: 276.23s (4.60 min)
- Median: 179.89s (3.00 min)
- Min: 159.17s (2.65 min)
- Max: 489.62s (8.16 min)
- Std Dev: 151.13s

### Combination 4: fact_checking_only

**Description:** Fact-checking parallelization only

**Flags:**
- ENABLE_PARALLEL_MEMORY_OPS: 0
- ENABLE_PARALLEL_ANALYSIS: 0
- ENABLE_PARALLEL_FACT_CHECKING: 1

**Statistics:**
- Iterations: 3
- Mean: 1127.95s (18.80 min)
- Median: 962.36s (16.04 min)
- Min: 206.98s (3.45 min)
- Max: 2214.52s (36.91 min)
- Std Dev: 827.90s
