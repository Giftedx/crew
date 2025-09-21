---
title: UTC Time Conventions
origin: utc_sweep_2025_09_21
status: canonical
last_moved: 2025-09-21
---

This document standardizes how time is represented and handled across the codebase. The goals are to prevent bugs from naive/aware datetime mismatches, ensure consistent storage and comparisons, and align observability, caching, and retries around the same clock.

## Principles

- Single source of truth: all timestamps are in UTC and timezone-aware.
- Never compare naive and aware datetimes.
- Prefer ISO 8601 strings with explicit offset (e.g., `Z` for UTC) for persistence and logs.
- Use centralized helpers to get the current time and to normalize parsed times.

## Required APIs

- Get current time (UTC-aware):
  - Use `core.time.default_utc_now()`.
- Normalize any datetime (parsed or constructed):
  - Use `core.time.ensure_utc(dt)` before storing or comparing.

## Allowed Patterns (Python)

```python
from core.time import default_utc_now, ensure_utc
from datetime import datetime

# NOW: always UTC-aware
started_at = default_utc_now()

# SERIALIZE: ISO 8601
payload = {"timestamp": started_at.isoformat()}

# PARSE: normalize to UTC-aware before compare
parsed = ensure_utc(datetime.fromisoformat(payload["timestamp"]))
if parsed > default_utc_now() - timedelta(days=1):
    ...
```

## Prohibited Patterns

- `datetime.now()` or `datetime.utcnow()` without using project helpers.
- Comparing `datetime.fromisoformat(... )` directly to an aware `datetime`.
- Storing naive datetimes in JSON, DBs, or logs.

## Storage & I/O

- Persist timestamps as ISO 8601 strings with offset (e.g., `2025-09-21T14:31:45.123456+00:00`).
- When reading external data with missing offsets, immediately wrap with `ensure_utc(...)`.
- File names may include UTC timestamps via `default_utc_now().strftime(...)`.

## Observability

- Metrics/tracing timestamps should be derived from `default_utc_now()`.
- Avoid mixing local timezones in labels or attributes.

## Common Pitfalls and Fixes

- TypeError: "can't compare offset-naive and offset-aware datetimes"
  - Fix: wrap parsed datetime with `ensure_utc(...)` before comparison.
- Third-party libraries returning naive datetimes
  - Fix: always normalize with `ensure_utc(...)` on ingestion boundaries.
- Legacy data containing naive timestamps
  - Fix: treat them as UTC by policy and normalize on read; document exceptions if any.

## Testing & Guards

- Prefer tests that assert timestamps are timezone-aware.
- Include at least one comparison path that would fail if naive vs aware were mixed.
- See repository tests covering UTC behavior (e.g., datetime UTC guards).

## Quick Checklist

1. Use `default_utc_now()` for now.
1. Call `ensure_utc(...)` on any parsed/constructed datetime.
1. Compare aware to aware only.
1. Persist ISO 8601 with offset.
1. Avoid local timezone conversions unless user-facing; document when needed.
