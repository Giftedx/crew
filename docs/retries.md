# HTTP Retry Configuration

This service provides feature-flagged HTTP retry logic centralised in `core.http_utils`.

## Quick Start

1. Enable retries by setting one of:
    - `ENABLE_HTTP_RETRY=1` (preferred)
    - `ENABLE_ANALYSIS_HTTP_RETRY=1` (deprecated, grace thru 2025-12-31)
2. (Optional) Create / edit `config/retry.yaml`:

    ```yaml
    # config/retry.yaml
    max_attempts: 5  # 1-20 acceptable
    ```

3. (Optional) Override per-call attempts via `retrying_get(..., max_attempts=7)` or `retrying_post(...)`.

## Precedence (Highest First)

1. Explicit `max_attempts` argument passed to `retrying_get` / `retrying_post`
2. `config/retry.yaml` (`max_attempts:` key)
3. Environment variable `RETRY_MAX_ATTEMPTS`
4. Library constant `DEFAULT_HTTP_RETRY_ATTEMPTS` (currently 3)

Invalid / out-of-range values (<=0 or >20, non-integer) are ignored and the resolver falls back to the next source.

## API Surface

- `is_retry_enabled()` – public boolean helper (prefers new flag, honors legacy with deprecation warning)
- `retrying_get(url, ..., max_attempts=None)`
- `retrying_post(url, ..., max_attempts=None)`
- `resolve_retry_attempts(call_arg=None)` – internal precedence resolver (also used when wrappers receive `None`)

## Legacy Flag Deprecation

`ENABLE_ANALYSIS_HTTP_RETRY` emits a `DeprecationWarning` and structured log when used. After 2025-12-31, usage will raise at runtime.

## Observability

Retry attempts and give-ups are counted via metrics in `obs.metrics` (counters: `HTTP_RETRY_ATTEMPTS`, `HTTP_RETRY_GIVEUPS`). Spans annotate attempts with `retry.attempt` and final status.

## Example

```python
from core.http_utils import retrying_get

resp = retrying_get(
     "https://api.example.com/data",
     params={"q": "value"},
     # max_attempts omitted -> resolved dynamically
)
print(resp.status_code)
```

## Troubleshooting

| Symptom | Likely Cause | Resolution |
|---------|--------------|------------|
| No retries happening | Flags disabled | Set `ENABLE_HTTP_RETRY=1` |
| Warning about legacy flag | Using deprecated env var | Migrate to `ENABLE_HTTP_RETRY` |
| Attempts higher than expected | Explicit arg or config overriding | Inspect call sites & config/retry.yaml |
| Runtime error about legacy flag removal | Past grace period | Remove `ENABLE_ANALYSIS_HTTP_RETRY` |

## Future Work

- Potential settings module unification replacing env + ad-hoc YAML
- Adaptive backoff (jitter strategies) selection via config
- Metrics cardinality reduction if high-volume services expand
