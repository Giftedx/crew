# HTTP Facade Migration Guide

## Overview

This guide provides a template for migrating direct `requests` usage to the centralized `http_utils` wrappers to ensure consistent retry logic, circuit breaker behavior, metrics collection, and observability across the codebase.

## Why Migrate?

**Benefits of using `core/http_utils.py` facade:**

- ✅ Unified retry/backoff behavior with connection error scaling
- ✅ Centralized circuit breaker protection
- ✅ Automatic metrics instrumentation (requests, errors, latencies)
- ✅ Redis-backed caching for GET requests (`cached_get`)
- ✅ Configurable timeouts with environment/config precedence
- ✅ Easier testing via monkeypatch seams
- ✅ Compliance with architectural guardrails

## Migration Pattern

### Before (Direct requests usage)

```python
import requests

# Direct session usage
session = requests.Session()
response = session.post(
    url="https://api.example.com/endpoint",
    json={"key": "value"},
    headers={"Authorization": f"Bearer {token}"},
    timeout=30,
)
response.raise_for_status()
data = response.json()
```

### After (Using http_utils facade)

```python
from core import http_utils

# Option 1: Simple usage (creates session internally)
response = http_utils.resilient_post(
    url="https://api.example.com/endpoint",
    json={"key": "value"},
    headers={"Authorization": f"Bearer {token}"},
    timeout=30,
)
# resilient_post automatically raises for status
data = response.json()

# Option 2: With retrying wrapper (recommended for flaky endpoints)
response = http_utils.retrying_post(
    url="https://api.example.com/endpoint",
    json={"key": "value"},
    headers={"Authorization": f"Bearer {token}"},
    timeout=30,
    max_retries=3,  # optional, defaults via config
)
data = response.json()
```

### For Connection Pools (Advanced)

If you maintain a persistent `requests.Session` for connection pooling:

```python
from core import http_utils
import requests

# Keep your pooled session
session = requests.Session()
# ... configure retry adapters, headers, etc.

# Pass session to http_utils via request_fn
response = http_utils.resilient_post(
    url="https://api.example.com/endpoint",
    json={"key": "value"},
    headers={"Authorization": f"Bearer {token}"},
    request_fn=session.post,  # Use pooled session
    timeout=30,
)
data = response.json()
```

## Step-by-Step Migration

### 1. Identify Direct Usage

Run the guardrail script to find violations:

```bash
python scripts/validate_http_wrappers_usage.py
```

### 2. Choose the Right Wrapper

| Use Case | Recommended Wrapper | Notes |
|----------|---------------------|-------|
| Simple GET/POST | `resilient_get/post` | Basic retry + raise_for_status |
| Flaky endpoints | `retrying_get/post` | Exponential backoff, configurable retries |
| Cacheable GET | `cached_get` | Redis/in-memory cache, negative caching |
| Full control | `http_request_with_retry` | Low-level with custom retry logic |

### 3. Update Imports

```python
# Remove:
import requests

# Add:
from core import http_utils
```

### 4. Replace Direct Calls

**GET requests:**

```python
# Before
response = requests.get(url, headers=headers, timeout=10)

# After
response = http_utils.resilient_get(url, headers=headers, timeout=10)
```

**POST requests:**

```python
# Before
response = requests.post(url, json=payload, headers=headers)

# After
response = http_utils.resilient_post(url, json=payload, headers=headers)
```

**With session pooling:**

```python
# Before
session = requests.Session()
response = session.get(url, headers=headers)

# After
session = requests.Session()
response = http_utils.resilient_get(url, headers=headers, request_fn=session.get)
```

### 5. Handle Exceptions

The facade raises exceptions consistently:

- `requests.HTTPError` for 4xx/5xx (already raised by `raise_for_status`)
- `requests.Timeout` for timeouts
- `requests.ConnectionError` for network issues
- `requests.RequestException` for other errors

Your existing exception handling should work unchanged:

```python
try:
    response = http_utils.resilient_post(url, json=payload)
    data = response.json()
except requests.HTTPError as e:
    # Handle 4xx/5xx
    logger.error(f"HTTP error: {e}")
except requests.Timeout:
    # Handle timeout
    logger.error("Request timed out")
except requests.RequestException as e:
    # Handle other errors
    logger.error(f"Request failed: {e}")
```

### 6. Configure Retries (Optional)

Override default retry behavior via parameters or config:

```python
# Via parameter (highest precedence)
response = http_utils.retrying_post(
    url=url,
    json=payload,
    max_retries=5,  # Override default
)

# Via config (see core/http/retry_config.py)
from core.http.retry_config import RetryConfig
config = RetryConfig(max_retries=5, backoff_factor=2.0)
response = http_utils.http_request_with_retry(url, method="POST", json=payload, retry_config=config)
```

### 7. Update Tests

Tests should continue to work with `responses` or `requests_mock`:

```python
import responses
from core import http_utils

@responses.activate
def test_api_call():
    responses.add(responses.POST, "https://api.example.com/endpoint", json={"result": "ok"}, status=200)

    # http_utils wrappers are testable
    response = http_utils.resilient_post("https://api.example.com/endpoint", json={})
    assert response.json() == {"result": "ok"}
```

For monkeypatching:

```python
def test_with_monkeypatch(monkeypatch):
    def mock_post(*args, **kwargs):
        class MockResponse:
            status_code = 200
            def json(self): return {"mock": "data"}
            def raise_for_status(self): pass
        return MockResponse()

    monkeypatch.setattr("core.http_utils.resilient_post", mock_post)
    # ... test code
```

### 8. Verify Compliance

After migration, run guardrails:

```bash
# Check HTTP wrapper usage
python scripts/validate_http_wrappers_usage.py

# Run full compliance suite
make guards
```

## Common Pitfalls

### ❌ Don't bypass the facade in new code

```python
# BAD
import requests
response = requests.get(url)
```

```python
# GOOD
from core import http_utils
response = http_utils.resilient_get(url)
```

### ❌ Don't lose connection pooling benefits

If you had a pooled session, preserve it:

```python
# BAD - Creates new connection each time
for url in urls:
    response = http_utils.resilient_get(url)
```

```python
# GOOD - Reuse session across requests
session = requests.Session()
for url in urls:
    response = http_utils.resilient_get(url, request_fn=session.get)
```

### ❌ Don't ignore timeout configuration

Always specify or inherit timeouts:

```python
# BAD - No timeout (can hang forever)
response = http_utils.resilient_get(url)
```

```python
# GOOD - Explicit or config-driven timeout
response = http_utils.resilient_get(url, timeout=30)
```

## Environment Configuration

Configure retry behavior via environment variables:

```bash
# Default retries (if not specified in call or config)
HTTP_MAX_RETRIES=3

# Default timeout (seconds)
HTTP_DEFAULT_TIMEOUT=30

# Backoff multiplier
HTTP_BACKOFF_FACTOR=2.0

# Connection error scaling (multiplies retries for ConnectionError)
HTTP_CONNECTION_ERROR_SCALE=2
```

## Metrics & Observability

The facade automatically instruments:

- Request counts (by method, host, status)
- Error rates (by error type)
- Latencies (p50, p95, p99)
- Retry attempts
- Circuit breaker state

View metrics at `/metrics` endpoint or Prometheus dashboards.

## Pre-commit Hook

The pre-commit hook automatically rejects direct `requests` usage:

```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: validate-http-wrappers-usage
      name: Validate no direct 'requests' usage outside http_utils
      entry: scripts/validate_http_wrappers_usage.py
      language: python
      types: [python]
      files: ^src/.*\.py$
```

## Support & Questions

- **Architecture**: See `docs/architecture/adr-0001-cache-platform.md`
- **HTTP utilities**: See `src/core/http_utils.py` and `src/core/http/`
- **Retry config**: See `src/core/http/retry_config.py`
- **Testing patterns**: See `tests/core/http/`

For questions, contact the Backend team.

---

**Document Version**: 1.0
**Created**: 2025-01-23
**Last Updated**: 2025-01-23
