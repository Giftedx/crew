# Flag Combination Validation Results

**Generated:** 2025-10-04T20:48:36.272830
**Baseline Mean:** 0.00s (0.00 min)

---

## Summary Table

| Combination | Name | Mean Time | vs Baseline | Expected Savings | Actual Savings | Status |
|-------------|------|-----------|-------------|------------------|----------------|--------|
| 1 | sequential_baseline | 0.00 min | +0.00 min | 0.0-0.0 min | 0.00 min | 📊 Baseline |
| 2 | memory_only | 0.00 min | +0.00 min | 0.5-1.0 min | 0.00 min | ❌ Fail |
| 3 | analysis_only | 0.00 min | +0.00 min | 1.0-2.0 min | 0.00 min | ❌ Fail |
| 4 | fact_checking_only | 0.00 min | +0.00 min | 0.5-1.0 min | 0.00 min | ❌ Fail |
| 5 | memory_analysis | 0.00 min | +0.00 min | 1.5-3.0 min | 0.00 min | ❌ Fail |
| 6 | memory_fact_checking | 0.00 min | +0.00 min | 1.0-2.0 min | 0.00 min | ❌ Fail |
| 7 | analysis_fact_checking | 0.00 min | +0.00 min | 1.5-3.0 min | 0.00 min | ❌ Fail |
| 8 | all_parallel | 0.00 min | +0.00 min | 2.0-4.0 min | 0.00 min | ❌ Fail |

---

## Detailed Statistics

### Combination 1: sequential_baseline

**Description:** Original sequential flow (baseline)

**Flags:**
- ENABLE_PARALLEL_MEMORY_OPS: 0
- ENABLE_PARALLEL_ANALYSIS: 0
- ENABLE_PARALLEL_FACT_CHECKING: 0

**Statistics:**
- Iterations: 3
- Mean: 0.00s (0.00 min)
- Median: 0.00s (0.00 min)
- Min: 0.00s (0.00 min)
- Max: 0.00s (0.00 min)
- Std Dev: 0.00s

### Combination 2: memory_only

**Description:** Memory operations parallelization only

**Flags:**
- ENABLE_PARALLEL_MEMORY_OPS: 1
- ENABLE_PARALLEL_ANALYSIS: 0
- ENABLE_PARALLEL_FACT_CHECKING: 0

**Statistics:**
- Iterations: 3
- Mean: 0.00s (0.00 min)
- Median: 0.00s (0.00 min)
- Min: 0.00s (0.00 min)
- Max: 0.00s (0.00 min)
- Std Dev: 0.00s

### Combination 3: analysis_only

**Description:** Analysis subtasks parallelization only

**Flags:**
- ENABLE_PARALLEL_MEMORY_OPS: 0
- ENABLE_PARALLEL_ANALYSIS: 1
- ENABLE_PARALLEL_FACT_CHECKING: 0

**Statistics:**
- Iterations: 3
- Mean: 0.00s (0.00 min)
- Median: 0.00s (0.00 min)
- Min: 0.00s (0.00 min)
- Max: 0.00s (0.00 min)
- Std Dev: 0.00s

### Combination 4: fact_checking_only

**Description:** Fact-checking parallelization only

**Flags:**
- ENABLE_PARALLEL_MEMORY_OPS: 0
- ENABLE_PARALLEL_ANALYSIS: 0
- ENABLE_PARALLEL_FACT_CHECKING: 1

**Statistics:**
- Iterations: 3
- Mean: 0.00s (0.00 min)
- Median: 0.00s (0.00 min)
- Min: 0.00s (0.00 min)
- Max: 0.00s (0.00 min)
- Std Dev: 0.00s

### Combination 5: memory_analysis

**Description:** Memory + Analysis parallelization (combined)

**Flags:**
- ENABLE_PARALLEL_MEMORY_OPS: 1
- ENABLE_PARALLEL_ANALYSIS: 1
- ENABLE_PARALLEL_FACT_CHECKING: 0

**Statistics:**
- Iterations: 3
- Mean: 0.00s (0.00 min)
- Median: 0.00s (0.00 min)
- Min: 0.00s (0.00 min)
- Max: 0.00s (0.00 min)
- Std Dev: 0.00s

### Combination 6: memory_fact_checking

**Description:** Memory + Fact-checking parallelization (combined)

**Flags:**
- ENABLE_PARALLEL_MEMORY_OPS: 1
- ENABLE_PARALLEL_ANALYSIS: 0
- ENABLE_PARALLEL_FACT_CHECKING: 1

**Statistics:**
- Iterations: 3
- Mean: 0.00s (0.00 min)
- Median: 0.00s (0.00 min)
- Min: 0.00s (0.00 min)
- Max: 0.00s (0.00 min)
- Std Dev: 0.00s

### Combination 7: analysis_fact_checking

**Description:** Analysis + Fact-checking parallelization (combined)

**Flags:**
- ENABLE_PARALLEL_MEMORY_OPS: 0
- ENABLE_PARALLEL_ANALYSIS: 1
- ENABLE_PARALLEL_FACT_CHECKING: 1

**Statistics:**
- Iterations: 3
- Mean: 0.00s (0.00 min)
- Median: 0.00s (0.00 min)
- Min: 0.00s (0.00 min)
- Max: 0.00s (0.00 min)
- Std Dev: 0.00s

### Combination 8: all_parallel

**Description:** All parallelizations enabled (full optimization)

**Flags:**
- ENABLE_PARALLEL_MEMORY_OPS: 1
- ENABLE_PARALLEL_ANALYSIS: 1
- ENABLE_PARALLEL_FACT_CHECKING: 1

**Statistics:**
- Iterations: 3
- Mean: 0.00s (0.00 min)
- Median: 0.00s (0.00 min)
- Min: 0.00s (0.00 min)
- Max: 0.00s (0.00 min)
- Std Dev: 0.00s
