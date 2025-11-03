# Network & HTTP Conventions

This project centralizes common HTTP patterns to improve security, consistency,
and testability.

## URL Validation

Use `platform.http.http_utils:validate_public_https_url(url)` to ensure:

- HTTPS scheme is enforced.
- Host is present.
- If host is a literal IP it must be globally routable (rejects private / loopback / link-local).

Rationale: Prevent accidental posting to insecure or internal addresses.

## Resilient POST Requests

`platform.http.http_utils:resilient_post` wraps `requests.post` adding:

- Standard timeout (`REQUEST_TIMEOUT_SECONDS`).
- Optional fallback for legacy / monkeypatched test doubles that omit the
  `timeout` parameter (retries without it upon detecting a signature mismatch).

Signature:

```python
resilient_post(
    url: str,
    *,
    json_payload: Any | None = None,
    headers: Mapping[str, str] | None = None,
    files: Mapping[str, Any] | None = None,
    timeout_seconds: int = REQUEST_TIMEOUT_SECONDS,
    allow_legacy_timeout_fallback: bool = True,
    request_fn: Callable[..., Any] = requests.post,
) -> requests.Response
```

## Resilient GET Requests & Streaming

`platform.http.http_utils:resilient_get` mirrors the POST helper (lazy binding + legacy
TypeError fallback) and adds optional streaming support for large downloads
like Discord CDN attachments. Pass `stream=True` and iterate over
`response.iter_content(chunk_size=...)` to process data incrementally.

Guidelines:

- Prefer `resilient_get` over raw `requests.get` when you need a standard
  timeout or test‑friendly monkeypatch resilience.
- For streaming downloads always specify an explicit `chunk_size` and guard
  against empty chunks.
- Avoid loading large binary responses fully into memory.

## Retry & Backoff (Feature-Flagged)

Use `platform.http.http_utils:http_request_with_retry` for transient failures (5xx, 429, selected network
errors). Enable globally via `ENABLE_HTTP_RETRY=1`. The deprecated legacy flag
`ENABLE_ANALYSIS_HTTP_RETRY` remains supported until 2025‑12‑31; the unified flag
takes precedence when both are set.

Example wrapping a GET:

```python
from platform.http.http_utils import http_request_with_retry, resilient_get, REQUEST_TIMEOUT_SECONDS

resp = http_request_with_retry(
    "GET",
    url,
    request_callable=lambda u, **_: resilient_get(u, params=params, timeout_seconds=REQUEST_TIMEOUT_SECONDS),
    max_attempts=4,
)
```

### Service-level integration pattern

When integrating into a higher-level service (e.g. model gateway) keep original helper usage so semantics remain identical when the flag is off:

```python
from platform.http.http_utils import (
    REQUEST_TIMEOUT_SECONDS,
    resilient_post,
    http_request_with_retry,
    is_retry_enabled,
)

url = "https://openrouter.ai/api/v1/chat/completions"
headers = {"Authorization": f"Bearer {self.api_key}"}
if is_retry_enabled():
    resp = http_request_with_retry(
        "POST",
        url,
        request_callable=lambda u, **_: resilient_post(
            u,
            headers=headers,
            json_payload=payload,
            timeout_seconds=REQUEST_TIMEOUT_SECONDS,
        ),
        max_attempts=3,
    )
else:
    resp = resilient_post(
        url,
        headers=headers,
        json_payload=payload,
        timeout_seconds=REQUEST_TIMEOUT_SECONDS,
    )
```

This preserves prior behavior while enabling retries, tracing, and metrics when the flag is enabled.

## Tracing (Retries)

`resilient_post` and `resilient_get` automatically emit spans (`http.post`,
`http.get`) when OpenTelemetry tracing is initialized. The retry helper emits
`http.retry_attempt` spans annotated with attempt counters and error metadata.
If tracing is not initialized these spans are inexpensive no-ops.

## Tracing

## Constants

Provided by `ultimate_discord_intelligence_bot.core.http_utils` for reuse (avoid scattering magic numbers):

- `REQUEST_TIMEOUT_SECONDS` (default 15s)
- `HTTP_SUCCESS_NO_CONTENT` (204)
- `HTTP_RATE_LIMITED` (429)
- `DEFAULT_RATE_LIMIT_RETRY` (60 seconds)

## Migration Guidelines

- Replace ad hoc webhook URL validation with `validate_public_https_url` in `ultimate_discord_intelligence_bot.core.http_utils`.
- Replace direct `requests.post(..., timeout=...)` usages (especially with retry
  logic or fallback) with `resilient_post` where semantics match.
- Replace direct `requests.get` calls that just need a timeout / (optional)
  streaming with `resilient_get` for consistency (especially where tests
  monkeypatch `requests.get`).
- Keep specialized logic (multipart uploads, streaming) local if it adds
  behaviour beyond simple JSON/file POST, but still use the timeout constant.

## Testing Notes

Tests that monkeypatch `requests.post` or `requests.get` with simplified
signatures (e.g., omitting `timeout`, `params`) remain compatible: helpers
retry with only the arguments supported by the provided callable upon detecting
an unexpected keyword.

### Monkeypatch + Reload Preservation

Some tests perform a module reload (`importlib.reload(core.http_utils)`) after
monkeypatching `resilient_post` / `resilient_get`. The module now preserves any
externally monkeypatched versions of these functions if they were replaced
before reload (captured via module globals) to avoid breaking existing test
doubles. New tests should generally avoid the reload pattern—instead monkeypatch
after import—so this preservation shim can be removed in the future with a
straightforward test refactor.

## Future Extensions

Potential future additions:

- Global circuit breaker integration.
- Structured logging of request metadata for observability.

## Compliance Exemption Pragmas

In rare, test‑driven scenarios we intentionally allow a direct `requests.*` call
to preserve a provenance string that the existing test suite asserts on.

Use the inline marker:

```python
import requests  # http-compliance: allow-direct-requests (reason)
```

Rules:

1. Provide a parenthetical reason (short, actionable, tied to a test or perf constraint).
1. Only one exempt import per file; multiple exemptions warrant migrating to wrappers + updating tests.
1. The HTTP compliance auditor (`src/ultimate_discord_intelligence_bot/core/http_compliance_audit.py`) skips any file containing the marker.
1. Exemptions are temporary – prefer migrating tests to assert semantic behavior (status, metrics) instead of raw provenance strings.

Current approved exemption(s):

- `src/ultimate_discord_intelligence_bot/tools/discord_download_tool.py` – small streaming GET where tests assert the `command` field starts with `requests.get`.

Removal Process:

1. Update tests to accept wrapper provenance (e.g., allow either `requests.get` or `resilient_get`).
1. Remove the direct call and marker; switch to `resilient_get` / retry helper where appropriate.
1. Run `make guards` (or the auditor script) to confirm zero direct usages remain.
