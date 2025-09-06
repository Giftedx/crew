## Distributed Rate Limiting (Design Stub)

Status: Draft / Proposal

### Problem

Current rate limiting is an in‑process token bucket keyed by client IP. In a multi‑replica deployment this allows a client to multiply its effective limit linearly with the number of replicas. It also loses counters on restart and cannot coordinate global backoff / burst smoothing.

### Goals

1. Consistent global limit enforcement across replicas.
2. Low latency (sub‑millisecond hot path target) & predictable degradation when the backing store is unavailable.
3. Support differentiated limits (e.g. default vs. privileged API keys or internal jobs) and per‑route overrides.
4. Expose unified Prometheus metrics (rejections, remaining tokens) without double counting.
5. Preserve existing local implementation as a fallback when the feature is disabled or the store is unreachable.

### Non‑Goals (Initial Phase)

- Dynamic, per‑user limit reconfiguration via API (can follow later).
- Sliding window accuracy at sub‑second granularity (approximate token bucket is acceptable).
- Multi‑tenant isolation beyond current namespace strategy (handled at higher layers).

### Candidate Backends

| Backend | Pros | Cons |
|---------|------|------|
| Redis (cluster) | Mature primitives (INCR, LUA, scripts), TTL support, high throughput | External dependency, network latency |
| KeyDB | Drop‑in Redis superset with multi‑threading | Less ubiquitous operational expertise |
| In‑memory + gossip | No external infra | Complexity & eventual consistency risk |

Redis is preferred for early implementation due to simplicity and existing operational familiarity.

### Algorithm

Token bucket stored per key: `rl:{tenant}:{bucket_key}` with value = current tokens + last refill timestamp encoded (or separate keys). Refill rate & capacity configured per policy. We evaluate two approaches:

1. Scripted Atomic Refill + Consume (single Lua script):
   - Input: capacity, refill_rate (tokens/sec * 1e6 precision), now (microseconds), cost (default 1).
   - Script loads current tokens + last_refill_ts (or initializes to full capacity), performs proportional refill: `new_tokens = min(capacity, tokens + (now - last)/1e6 * refill_rate)`. If `new_tokens >= cost` consume and return remaining; else return rejection marker.
2. Redis 7+ `FCALL` / Functions for better deployment packaging.

Lua approach ensures atomicity without requiring distributed locks.

### Configuration / Flags

| Flag | Purpose | Default |
|------|---------|---------|
| `ENABLE_DISTRIBUTED_RATE_LIMITING` | Activate Redis backed limiter; fallback to local on error. | off |
| `RATE_LIMIT_REDIS_URL` | Redis connection string (e.g. `redis://host:6379/0`). | unset |
| `RATE_LIMIT_GLOBAL_CAPACITY` | Default bucket size (tokens). | 60 |
| `RATE_LIMIT_GLOBAL_REFILL_PER_SEC` | Refill tokens per second. | 1 |
| (future) `RATE_LIMIT_RULES_PATH` | YAML for per‑route / API key overrides. | unset |

Add settings to `src/core/settings.py` with validation; document in `docs/feature_flags.md` once implemented.

### Fallback & Resilience

- On Redis connectivity failure: log structured warning once every N minutes, increment `rate_limit_backend_errors_total`, and automatically revert to local in‑process bucket for that request (circuit open). Periodic background health probe attempts to restore distributed mode.
- Hard failure (script errors): treat as transient; do not block requests unless local limiter also exhausted.

### Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `rate_limit_rejections_total` | Counter | `reason` (`local_exhausted`, `distributed_exhausted`, `backend_error`) | Already exists (extend reasons) |
| `rate_limit_tokens_remaining` | Gauge | `scope` (`global`/`route`) | Optional approximate last observed tokens |
| `rate_limit_backend_errors_total` | Counter | - | Redis operation failures |

### Incremental Rollout Plan

1. Implement Redis client + Lua script behind flag (no removal of local code).
2. Shadow mode: run distributed evaluation but do not enforce (compare decisions & emit divergence metric `rate_limit_shadow_divergence_total`).
3. Enable enforcement for low risk routes.
4. Full enable + deprecate shadow divergence metric.

### Testing Strategy

- Unit test Lua script logic via `fakeredis` or an abstract interface.
- Integration test with ephemeral Redis container (pytest service) gating tests behind env flag to keep default suite lightweight.
- Property tests for refill correctness vs. elapsed time.
- Concurrency stress test (async / threads) to ensure atomic consumption under load.

### Open Questions

- Do we need per‑tenant isolation at the Redis DB level or is key prefixing sufficient? (Likely sufficient with proper key hygiene.)
- Should burst capacity adapt based on historical success (adaptive limits)? (Future extension.)

### Next Steps

- Confirm Redis availability in target deployment environments.
- Finalize settings & add to `Settings` model.
- Implement shadow mode instrumentation.
- Roll out with observability dashboard panels.

---
Draft prepared as part of the production readiness polish initiative.
