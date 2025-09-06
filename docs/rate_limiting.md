# Rate Limiting & Metrics Shim

This project vendors a **minimal FastAPI-like shim** (see `src/fastapi/`) for test speed
and isolation. Because Starlette and the full FastAPI stack are not always installed
in lightweight environments, a small compatibility layer (`server.middleware_shim`)
adds support for `add_middleware` semantics and chained execution used by the
rate limiting and metrics middlewares.

## Why a Shim?

The original regression suite needed deterministic, dependency‑light HTTP behavior:

* Avoids importing Starlette / uvicorn in unit tests.
* Keeps middleware logic pure-Python and easily inspectable.
* Eliminates side effects from ASGI lifespan handlers during fast test runs.

## Fixed Window Limiter

`server.rate_limit._FixedWindowRateLimiter` implements a simple 1-second fixed
window with a configurable burst (`RATE_LIMIT_BURST` / `RATE_LIMIT_RPS`). It is
deliberately minimal—just enough to exercise rejection & metrics paths.

Key behaviors:

* First `burst` requests per second pass; subsequent requests -> 429.
* `/metrics` and `/health` are never rate limited (observability / liveness).
* Rejections increment `rate_limit_rejections_total` (labels: route, method).

## Metrics Endpoint Fallback

The vendored `Settings` object can sometimes expose raw `FieldInfo` instances
when environment resolution is bypassed. To keep tests resilient:

* Environment variable `ENABLE_PROMETHEUS_ENDPOINT=1` forces `/metrics` route registration.
* The code normalizes a `FieldInfo` path to its `.default` value.
* If `prometheus_client` is absent the exposition returns an empty body (`b""`).

## Testing Strategy

Two focused tests cover rate limiting:

1. `test_rate_limit_middleware_basic` – functional 429 behavior.
2. `test_rate_limit_metrics` – conditional assertion: if Prometheus available,
   the counter name appears in exposition; otherwise only endpoint reachability is asserted.

## Extending

For production-grade semantics (leaky bucket / token bucket / Redis distributed
limits) add a new middleware behind a feature flag rather than modifying the
current fixed window implementation. This preserves deterministic test behavior.

## Maintenance Notes

* Keep shim-specific logic isolated (no Starlette imports inside core logic).
* When upgrading to real FastAPI in all environments, the shim detection blocks
  become no-ops and can be removed once validated.
