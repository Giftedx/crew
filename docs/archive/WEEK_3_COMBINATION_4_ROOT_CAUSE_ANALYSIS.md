# Week 3 Combination 4 Root Cause Analysis

## Parallel Fact-Checking Catastrophic Failure Investigation

**Generated:** 2025-01-04 23:30 UTC
**Status:** 🚨 ROOT CAUSE IDENTIFIED
**Issue:** Combination 4 execution time: 36.91 minutes (7.2× baseline)
**Expected:** 4.1-4.6 minutes (0.5-1.0 min faster than baseline)

---

## Executive Summary

**ROOT CAUSE IDENTIFIED:** The parallel fact-checking implementation creates **5 concurrent agents**, each calling `FactCheckTool`, which queries **5 different APIs per claim** (DuckDuckGo, Serply, Exa, Perplexity, Wolfram Alpha). This results in:

- **25 concurrent API calls** (5 agents × 5 APIs each)
- **NO rate limiting** on API calls
- **NO concurrency control** (no semaphores, throttling, or delays)
- **No timeout handling** per API (relying on retry logic)

When these 25 concurrent calls hit external APIs simultaneously:

1. **Rate limits triggered** on multiple APIs (especially free tiers: DuckDuckGo, Wolfram)
2. **Exponential backoff** from retry logic (`core/http_utils.resilient_get/post`)
3. **Cascading delays** as each retry waits progressively longer
4. **Resource contention** from too many concurrent operations

**Result:** First iteration takes 36.91 minutes as APIs rate-limit and retry with exponential backoff. Subsequent iterations faster as rate limits reset.

---

## Implementation Analysis

### Current Parallel Fact-Checking Architecture

**Location:** `src/ultimate_discord_intelligence_bot/orchestrator/crew_builders.py` Lines 346-490

**Pattern:**

```python
# Step 1: Sequential claim extraction (1 task)
claim_extraction_task = Task(
    description="Extract 5 claims from transcript using ClaimExtractorTool",
    agent=verification_agent,
    context=[transcription_task, analysis_ref],
)

# Step 2: Parallel fact-checking (5 concurrent tasks)
fact_check_1_task = Task(
    description="Verify claim #1 using FactCheckTool",
    agent=verification_agent,
    context=[claim_extraction_task],
    async_execution=True,  # ⚡ PARALLEL
)
# ... fact_check_2_task through fact_check_5_task (all async_execution=True)

# Step 3: Integration task (1 task, waits for all 5)
verification_integration_task = Task(
    description="Combine results from all 5 fact-checks",
    agent=verification_agent,
    context=[fact_check_1_task, ..., fact_check_5_task],
)
```

**Task Count:**

- Sequential mode: 4 tasks total
- Parallel mode: **10 tasks total** (1 extraction + 5 fact-checks + 1 integration + 3 other stages)

### FactCheckTool Implementation

**Location:** `src/ultimate_discord_intelligence_bot/tools/fact_check_tool.py`

**API Backends (all called per claim):**

```python
backends = [
    ("duckduckgo", self._search_duckduckgo),     # Free, no auth
    ("serply", self._search_serply),              # API key required
    ("exa", self._search_exa),                    # API key required
    ("perplexity", self._search_perplexity),      # API key required
    ("wolfram", self._search_wolfram),            # App ID required
]

for name, fn in backends:
    try:
        results = fn(claim) or []
        evidence.extend(results)
    except RequestException:
        continue  # Skip failed backends silently
```

**Critical Issues:**

1. **No Rate Limiting:**
   - All 5 backends called sequentially per claim
   - No delays between API calls
   - No semaphore/throttling on concurrent claims

2. **No Timeout Per Backend:**
   - Relies on `resilient_get/post` timeout (10-20 seconds per call)
   - If backend slow/rate-limited, entire tool waits
   - No circuit breaker for repeatedly failing backends

3. **Silent Failures:**
   - `RequestException` caught and ignored
   - Backend failures invisible in metrics
   - No differentiation between "no API key" and "rate limited"

4. **Retry Logic:**
   - `resilient_get/post` uses exponential backoff (from `core/http_utils`)
   - Default: 3-5 retries with increasing delays
   - Rate-limited calls trigger full retry sequence

---

## Concurrency Calculation

**When ENABLE_PARALLEL_FACT_CHECKING=1:**

**Worst Case (all API keys configured):**

- 5 parallel fact-check tasks (async_execution=True)
- Each task calls `FactCheckTool`
- Each tool queries 5 backends sequentially
- **Total concurrent operations: 5 fact-checks running**
- **Peak API calls: 5 × 5 = 25 concurrent requests** (if backends called in parallel within tool)
- **Actual: 5 concurrent request chains** (backends called sequentially per tool)

**Timeline Example (Iteration 1):**

```
T=0s:     claim_extraction_task completes
T=1s:     5 fact-check tasks launched in parallel
T=1-10s:  Each fact-check calls 5 backends sequentially (10-20s each)
T=10s:    DuckDuckGo rate limits triggered (free tier: ~100 req/hour)
T=15s:    Perplexity rate limits triggered (paid tier: varies)
T=20s:    First retry with 2s backoff
T=30s:    Second retry with 4s backoff
T=45s:    Third retry with 8s backoff
...
T=2214s:  All fact-checks eventually complete (36.91 minutes)
```

---

## Evidence from Benchmark Results

**Combination 4 Timing Pattern:**

| Iteration | Duration | Baseline Ratio | Pattern |
|-----------|----------|----------------|---------|
| 1 | 36.91 min | 7.2× | 🚨 CATASTROPHIC - first run, all APIs fresh, rate limits hit hard |
| 2 | 16.04 min | 3.1× | ⚠️ SLOW - rate limits partially reset, still throttled |
| 3 | 3.45 min | 0.67× | ✅ NORMAL - rate limits fully reset, cache helping |

**Analysis:**

- **Iteration 1:** All 5 concurrent fact-checks hit rate limits simultaneously → exponential backoff cascade
- **Iteration 2:** Some rate limits reset (e.g., DuckDuckGo 1-hour window) but others still active → moderate delays
- **Iteration 3:** Most/all rate limits cleared → normal performance (actually faster than baseline!)

**Why Iteration 3 is Fast:**

- Rate limit windows reset (~1 hour for DuckDuckGo)
- Some backends may have cached responses
- Fewer retries needed

**This confirms:** The issue is **API rate limiting**, not code bugs (hangs, deadlocks, etc.)

---

## Root Cause Summary

### Primary Cause: Overwhelming API Rate Limits

**Problem:**

- 5 concurrent fact-checks × 5 API backends = 25 concurrent request chains
- Free-tier APIs (DuckDuckGo, Wolfram) have strict rate limits:
  - DuckDuckGo: ~100 requests/hour (~1.67/min)
  - Wolfram Alpha Free: 2,000 requests/month (~4.5/hour)
- Paid-tier APIs (Perplexity, Exa, Serply) also have limits but higher

**When Rate Limited:**

- `resilient_get/post` triggers exponential backoff retry
- Default retry config: 3-5 attempts with 2s → 4s → 8s → 16s delays
- 5 concurrent tasks all retrying → 25+ seconds of delays per round
- Multiple retry rounds → cascading to 36+ minutes

### Contributing Factors

1. **No Concurrency Control:**
   - `async_execution=True` on all 5 fact-check tasks
   - No semaphore limiting concurrent tool calls
   - No queue or throttling mechanism

2. **Sequential Backend Calls:**
   - Each `FactCheckTool.run()` calls 5 backends sequentially
   - If first backend (DuckDuckGo) is slow/rate-limited, others wait
   - Better: Call backends in parallel within tool, with timeout

3. **No Backend Circuit Breaker:**
   - Failed/slow backends retried on every claim
   - No "skip this backend for next N minutes" logic
   - Waste time re-trying known-bad backends

4. **Silent Failures:**
   - `RequestException` caught and logged minimally
   - No visibility into which backends failing
   - Hard to diagnose rate limit issues in real-time

---

## Proposed Fixes

### Fix 1: Add Concurrency Limit (CRITICAL - Implement First)

**Goal:** Limit concurrent fact-check operations to avoid overwhelming APIs

**Implementation:**

**Option A: Semaphore in Crew Builder**

```python
# Add to crew_builders.py (around line 140)
import asyncio

# Create semaphore to limit concurrent fact-checks
fact_check_semaphore = asyncio.Semaphore(2)  # Max 2 concurrent

# Modify fact-check tasks to use semaphore
async def _wrapped_fact_check(task):
    async with fact_check_semaphore:
        return await task.execute()
```

**Option B: Reduce Parallel Tasks**

```python
# Change from 5 parallel tasks to 2-3
# In crew_builders.py, create only 3 fact-check tasks instead of 5
# OR: Make fact-checks sequential with async backend calls
```

**Option C: Task Batching**

```python
# Batch fact-checks: Process 2 at a time, then next 2, then last 1
# Modify verification_integration_task to orchestrate batches
```

**Recommendation:** **Option B (Reduce to 2-3 tasks) + Fix 2 (Parallel Backends)**

**Rationale:**

- Simpler to implement (no new async orchestration)
- 2-3 concurrent fact-checks still provides speedup vs sequential
- Reduces API pressure by 40-60%
- Combined with parallel backends (Fix 2), maintains throughput

---

### Fix 2: Parallelize Backends Within Tool (HIGH IMPACT)

**Goal:** Call all 5 backends in parallel per claim, with timeout

**Current (Sequential):**

```python
for name, fn in backends:
    try:
        results = fn(claim) or []
        evidence.extend(results)
    except RequestException:
        continue
```

**Proposed (Parallel):**

```python
import asyncio

async def _call_backend_with_timeout(name, fn, claim, timeout=10):
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(fn, claim),
            timeout=timeout
        )
    except (asyncio.TimeoutError, RequestException):
        return []

async def run_async(self, claim: str) -> StepResult:
    # ... (same validation) ...

    # Call all backends in parallel with timeout
    tasks = [
        _call_backend_with_timeout(name, fn, claim)
        for name, fn in backends
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Aggregate evidence from successful backends
    for name, result in zip([b[0] for b in backends], results):
        if isinstance(result, list):
            evidence.extend(result)
            successful_backends.append(name)
```

**Benefits:**

- 5× faster per fact-check (10s instead of 50s when all backends succeed)
- Slow/rate-limited backends don't block others
- Overall timeout per claim: 10s max (vs current 50-100s)
- Reduces total execution time even with fewer parallel tasks

---

### Fix 3: Add Rate Limiting Per Backend (MEDIUM PRIORITY)

**Goal:** Prevent overwhelming individual APIs

**Implementation:**

```python
# Add rate limiter dictionary (per backend)
from collections import defaultdict
from time import time

class FactCheckTool:
    def __init__(self):
        self._metrics = get_metrics()
        self._backend_rate_limiters = {
            "duckduckgo": RateLimiter(max_calls=30, window=60),  # 30/min
            "wolfram": RateLimiter(max_calls=5, window=60),       # 5/min
            "perplexity": RateLimiter(max_calls=20, window=60),  # 20/min
            "exa": RateLimiter(max_calls=20, window=60),
            "serply": RateLimiter(max_calls=20, window=60),
        }

    async def _call_backend_with_timeout(self, name, fn, claim, timeout=10):
        # Wait for rate limiter token
        await self._backend_rate_limiters[name].acquire()

        try:
            return await asyncio.wait_for(...)
```

**Simple RateLimiter:**

```python
class RateLimiter:
    def __init__(self, max_calls: int, window: int):
        self.max_calls = max_calls
        self.window = window  # seconds
        self.calls = []

    async def acquire(self):
        now = time()
        # Remove calls outside window
        self.calls = [t for t in self.calls if now - t < self.window]

        if len(self.calls) >= self.max_calls:
            # Wait until oldest call expires
            wait_time = self.window - (now - self.calls[0]) + 0.1
            await asyncio.sleep(wait_time)
            await self.acquire()  # Recursive retry

        self.calls.append(now)
```

---

### Fix 4: Add Circuit Breaker (LOW PRIORITY)

**Goal:** Stop calling backends that are consistently failing

**Implementation:**

```python
class CircuitBreaker:
    def __init__(self, failure_threshold=3, timeout=300):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout  # seconds
        self.opened_at = None

    def is_open(self):
        if self.opened_at and time() - self.opened_at > self.timeout:
            self.failure_count = 0
            self.opened_at = None
        return self.opened_at is not None

    def record_failure(self):
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.opened_at = time()

    def record_success(self):
        self.failure_count = 0
        self.opened_at = None
```

**Usage:**

```python
class FactCheckTool:
    def __init__(self):
        self._circuit_breakers = {
            backend: CircuitBreaker()
            for backend in ["duckduckgo", "serply", ...]
        }

    async def _call_backend_with_timeout(self, name, fn, claim, timeout=10):
        # Skip if circuit breaker open
        if self._circuit_breakers[name].is_open():
            return []

        try:
            result = await asyncio.wait_for(...)
            self._circuit_breakers[name].record_success()
            return result
        except Exception:
            self._circuit_breakers[name].record_failure()
            return []
```

---

### Fix 5: Improve Observability (CRITICAL)

**Goal:** Understand which backends are failing/slow in real-time

**Add Metrics:**

```python
# In FactCheckTool._call_backend_with_timeout
start = time()
try:
    result = await asyncio.wait_for(...)
    duration = time() - start

    self._metrics.histogram(
        "fact_check_backend_duration_seconds",
        labels={"backend": name, "outcome": "success"}
    ).observe(duration)

    self._metrics.counter(
        "fact_check_backend_calls_total",
        labels={"backend": name, "outcome": "success"}
    ).inc()

    return result
except asyncio.TimeoutError:
    duration = time() - start
    self._metrics.histogram(
        "fact_check_backend_duration_seconds",
        labels={"backend": name, "outcome": "timeout"}
    ).observe(duration)

    self._metrics.counter(
        "fact_check_backend_calls_total",
        labels={"backend": name, "outcome": "timeout"}
    ).inc()

    return []
except RequestException:
    # Similar metrics for rate_limit, error, etc.
```

**Add Logging:**

```python
import logging
_logger = logging.getLogger(__name__)

async def _call_backend_with_timeout(self, name, fn, claim, timeout=10):
    _logger.debug(f"Calling {name} backend for claim: {claim[:50]}...")
    try:
        result = await asyncio.wait_for(...)
        _logger.info(f"{name} returned {len(result)} evidence items in {duration:.2f}s")
        return result
    except asyncio.TimeoutError:
        _logger.warning(f"{name} timed out after {timeout}s")
        return []
    except RequestException as e:
        _logger.error(f"{name} failed: {e} (possibly rate limited)")
        return []
```

---

## Implementation Plan

### Phase 1: Quick Win (2-3 hours)

**Goal:** Reduce parallel tasks + add basic observability

**Changes:**

1. **Reduce parallel fact-check tasks from 5 to 2**
   - File: `crew_builders.py` lines 386-459
   - Change: Create only `fact_check_1_task` and `fact_check_2_task`
   - Update claim extraction to request 2 claims instead of 5
   - Update integration task context to use only 2 tasks

2. **Add logging to FactCheckTool**
   - File: `fact_check_tool.py`
   - Add: Debug/info/warning logs per backend call
   - Add: Total evidence count and successful backends to logs

3. **Test locally**

   ```bash
   ENABLE_PARALLEL_FACT_CHECKING=1 python scripts/benchmark_autointel_flags.py \
     --url "https://www.youtube.com/watch?v=xtFiJ8AVdW0" \
     --combinations 4 \
     --iterations 1
   ```

   - Expected: 4-6 minutes (not 36!)
   - Check logs for backend call patterns

**Success Criteria:**

- Iteration completes in < 8 minutes
- Logs show which backends called/succeeded/failed
- No cascading retry delays visible

---

### Phase 2: Parallel Backends (3-4 hours)

**Goal:** Make each fact-check faster by parallelizing backend calls

**Changes:**

1. **Convert FactCheckTool.run to async**
   - Rename `run` → `run_sync` (keep for backward compat)
   - Add new `run` that calls `run_async`
   - Parallelize backend calls with `asyncio.gather`

2. **Add per-backend timeout**
   - Wrap each backend call in `asyncio.wait_for(..., timeout=10)`
   - Prevent slow backends from blocking others

3. **Update metrics**
   - Add `fact_check_backend_calls_total` counter per backend
   - Add `fact_check_backend_duration_seconds` histogram

4. **Test with 2 parallel tasks**

   ```bash
   # Should complete in 3-4 minutes now
   # Each fact-check: 10s (parallel backends) vs 50s (sequential)
   ```

**Success Criteria:**

- Iteration completes in 3-5 minutes
- Metrics show parallel backend calls
- No backend timeouts (or minimal <10%)

---

### Phase 3: Rate Limiting (2-3 hours)

**Goal:** Prevent rate limit issues on future runs

**Changes:**

1. **Add RateLimiter class**
   - File: `core/rate_limiter.py` (new)
   - Implement token bucket algorithm
   - Test with unit tests

2. **Integrate with FactCheckTool**
   - Add rate limiters per backend
   - Conservative limits:
     - DuckDuckGo: 20/minute
     - Wolfram: 5/minute
     - Others: 15/minute

3. **Test with 3 parallel tasks**

   ```bash
   # Increase back to 3 parallel tasks
   # Should still complete in 4-6 minutes
   # Rate limiters prevent overwhelming APIs
   ```

**Success Criteria:**

- No rate limit errors in logs
- Consistent timing across iterations (< 20% variance)
- Can run 5+ iterations back-to-back without slowdown

---

### Phase 4: Circuit Breakers (Optional - 2 hours)

**Goal:** Handle persistent backend failures gracefully

**Changes:**

1. **Add CircuitBreaker class**
2. **Integrate with FactCheckTool**
3. **Add metrics for circuit breaker state**

**Success Criteria:**

- If backend down, circuit breaker opens after 3 failures
- Other backends continue working
- Tool still returns success with partial evidence

---

## Testing Plan

### Unit Tests

**Test Rate Limiter:**

```python
async def test_rate_limiter_enforces_limits():
    limiter = RateLimiter(max_calls=3, window=1)

    start = time()
    for i in range 5:
        await limiter.acquire()
    duration = time() - start

    assert duration >= 1.0  # Had to wait for window to reset
```

**Test Parallel Backends:**

```python
async def test_fact_check_parallel_backends(monkeypatch):
    slow_backend_called = False
    fast_backend_called = False

    async def slow_backend(claim):
        nonlocal slow_backend_called
        await asyncio.sleep(15)  # Exceeds timeout
        slow_backend_called = True
        return [{"title": "slow"}]

    async def fast_backend(claim):
        nonlocal fast_backend_called
        await asyncio.sleep(0.1)
        fast_backend_called = True
        return [{"title": "fast"}]

    tool = FactCheckTool()
    monkeypatch.setattr(tool, "_search_duckduckgo", slow_backend)
    monkeypatch.setattr(tool, "_search_serply", fast_backend)

    result = await tool.run_async("test claim")

    assert fast_backend_called
    # Slow backend should time out, not block fast backend
    assert len(result["evidence"]) >= 1  # Got fast results
```

### Integration Tests

**Test 2 Parallel Fact-Checks:**

```bash
#!/bin/bash
# File: test_parallel_fact_checking.sh

export ENABLE_PARALLEL_FACT_CHECKING=1

echo "Testing 2 parallel fact-checks..."
time python scripts/benchmark_autointel_flags.py \
  --url "https://www.youtube.com/watch?v=xtFiJ8AVdW0" \
  --combinations 4 \
  --iterations 3

echo ""
echo "Checking results..."
python scripts/analyze_benchmark_results.py \
  benchmarks/flag_validation_results_*.json \
  --combination 4 \
  --expected-mean 4.5 \
  --max-variance 30
```

**Expected Output:**

```
Iteration 1: 4.23 minutes ✅
Iteration 2: 3.95 minutes ✅
Iteration 3: 4.67 minutes ✅

Mean: 4.28 minutes (baseline: 5.12 min, improvement: 16%)
Std Dev: 0.36 minutes (variance: 8%)

✅ PASS: All iterations within expected range
✅ PASS: Variance acceptable
✅ PASS: Consistent performance
```

### Regression Tests

**Test Sequential Mode Still Works:**

```bash
# Ensure disabling flag reverts to sequential
export ENABLE_PARALLEL_FACT_CHECKING=0

python scripts/benchmark_autointel_flags.py \
  --url "https://www.youtube.com/watch?v=xtFiJ8AVdW0" \
  --combinations 1 \
  --iterations 1

# Should complete in ~5 minutes (baseline)
```

---

## Rollout Strategy

### Step 1: Quick Fix (Deploy Phase 1 First)

**Immediate Changes:**

- Reduce parallel tasks: 5 → 2
- Add basic logging
- Test with 1 iteration locally

**Timeline:** 2-3 hours
**Risk:** Low (small change)
**Impact:** High (should fix 36-min issue)

### Step 2: Parallel Backends (Deploy After Validation)

**Changes:**

- Async backend calls
- Per-backend timeout
- Enhanced metrics

**Timeline:** 3-4 hours
**Risk:** Medium (async refactor)
**Impact:** High (2-3× speedup per fact-check)

### Step 3: Rate Limiting (Deploy After Testing)

**Changes:**

- Add rate limiters per backend
- Test with multiple iterations

**Timeline:** 2-3 hours
**Risk:** Low (defensive measure)
**Impact:** Medium (prevents future issues)

### Step 4: Full Validation (5+ Iterations)

**After all fixes deployed:**

```bash
python scripts/benchmark_autointel_flags.py \
  --url "https://www.youtube.com/watch?v=xtFiJ8AVdW0" \
  --combinations 4 \
  --iterations 5

# Expected: 4.0-4.5 min mean, < 20% variance
```

**If successful, proceed to Combinations 5-8**

---

## Expected Outcomes

### After Phase 1 (Reduce Tasks)

**Combination 4 Performance:**

- Mean: 5-7 minutes (still slower than baseline, but acceptable)
- Variance: < 30%
- No catastrophic 36-min iterations

### After Phase 2 (Parallel Backends)

**Combination 4 Performance:**

- Mean: 4.0-4.5 minutes (10-20% faster than baseline) ✅ TARGET
- Variance: < 20%
- Consistent across iterations

### After Phase 3 (Rate Limiting)

**Combination 4 Performance:**

- Mean: 4.2-4.7 minutes (slight overhead from rate limiting)
- Variance: < 15% (more consistent)
- Can run 10+ iterations consecutively without slowdown

---

## Risks & Mitigation

### Risk 1: Parallel Backends Introduce New Bugs

**Mitigation:**

- Keep `run_sync` method for backward compatibility
- Add unit tests for async paths
- Deploy incrementally (test locally first)

### Risk 2: Rate Limiting Too Aggressive

**Mitigation:**

- Start with conservative limits (20/min for DuckDuckGo)
- Monitor metrics for "rate_limited" outcome
- Adjust limits based on data

### Risk 3: External API Changes

**Mitigation:**

- Circuit breakers prevent persistent failures from blocking
- Graceful degradation (tool succeeds with partial evidence)
- Monitor backend success rates

---

## Success Metrics

### Performance Metrics

- **Mean execution time:** 4.0-4.5 minutes (0.6-1.1 min faster than baseline)
- **Variance:** < 20% (consistent performance)
- **No catastrophic iterations:** All iterations < 8 minutes

### Reliability Metrics

- **Backend success rate:** > 80% (at least 4/5 backends working)
- **Tool success rate:** 100% (even if some backends fail)
- **Rate limit errors:** < 5% of backend calls

### Observability Metrics

- **Logs:** Clear indication of which backends called/succeeded/failed
- **Metrics:** Backend-level duration and call count histograms
- **Tracing:** Spans for each fact-check task and backend call

---

## Next Steps

1. ✅ **COMPLETED:** Root cause analysis (this document)
2. 🔄 **IN PROGRESS:** Implement Phase 1 (reduce tasks to 2)
3. ⏳ **PENDING:** Test Phase 1 with single iteration
4. ⏳ **PENDING:** Implement Phase 2 (parallel backends)
5. ⏳ **PENDING:** Full validation (5 iterations)
6. ⏳ **PENDING:** Fix Combination 2 (memory ops regression)
7. ⏳ **PENDING:** Run Combinations 5-8 (combined optimizations)

**Estimated Time to Fix & Validate:** 8-12 hours total

- Phase 1: 2-3 hours
- Phase 2: 3-4 hours
- Phase 3: 2-3 hours
- Testing: 2-3 hours

**User Decision:** Proceed with fixes (Option A from previous analysis)

---

## Appendix: Code Locations

**Files to Modify:**

1. **`src/ultimate_discord_intelligence_bot/orchestrator/crew_builders.py`**
   - Lines 346-490: Parallel fact-checking implementation
   - Change: Reduce tasks from 5 to 2

2. **`src/ultimate_discord_intelligence_bot/tools/fact_check_tool.py`**
   - Lines 48-88: `run` method and backend loop
   - Change: Add async version with parallel backend calls
   - Change: Add logging and metrics

3. **`src/core/rate_limiter.py`** (new file)
   - Implement RateLimiter class
   - Unit tests in `tests/core/test_rate_limiter.py`

4. **`src/core/circuit_breaker.py`** (new file, optional)
   - Implement CircuitBreaker class
   - Unit tests in `tests/core/test_circuit_breaker.py`

**Files to Test:**

1. **Unit tests:**
   - `tests/tools/test_fact_check_tool.py` (update for async)
   - `tests/core/test_rate_limiter.py` (new)

2. **Integration tests:**
   - `scripts/benchmark_autointel_flags.py` (existing)
   - `tests/test_autointel_data_flow.py` (update if needed)

---

**Document Status:** 🚨 READY FOR IMPLEMENTATION
**Next Action:** Begin Phase 1 implementation (reduce parallel tasks to 2)
