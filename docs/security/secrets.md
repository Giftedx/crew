# Secrets Management

Use the `security.secrets` helpers to load secrets from environment variables
with optional versioning. A reference such as `OPENAI_KEY:v2` maps to the
environment variable `OPENAI_KEY_V2`.

## Basic usage

```python
from security.secrets import get_secret, rotate_secret

key = get_secret("OPENAI_KEY:v2")
# ... later after rotating the key in the environment
new_key = rotate_secret("OPENAI_KEY:v2")
```

The helpers cache values in-memory to avoid repeated lookups. Calling
`rotate_secret` clears the cache for a reference and returns the fresh value.

## Rotation grace & dual-reference verification

When rotating a secret in production you often need a short grace window where
both the previous and newly promoted secret remain valid. This allows in-flight
requests (or staggered deploys) still using the old credential to succeed while
new traffic migrates to the replacement.

The rotation registry tracks for each logical secret reference:

* `current_ref` – the active reference (e.g. `OPENAI_KEY:v3`).
* `previous_ref` – the immediately prior reference (if any) still within a
  grace period.
* `activated_at` – timestamp when the current reference became active.
* `previous_activated_at` – the original activation timestamp for the previous
  reference (preserved so grace evaluation is based on when it was first
  promoted, not when it was superseded).

### Grace validation

`validate_grace(logical_name, now)` evaluates whether the previous reference is
still within the configured grace interval (default sourced from settings /
flags). Once the window elapses the previous reference is no longer accepted
and is cleared from the registry.

### Verifying an incoming credential

Use `verify_ref(logical_name, presented_ref)` to check a credential presented by
an external system (e.g. webhook callback, background worker). It returns
`True` if the presented reference matches either:

1. The current reference; or
1. The previous reference while still within grace.

If accepted the function emits an audit event `verify_accept` (with which ref
matched). If rejected it emits `verify_reject` including the presented value
for traceability (do NOT log raw secret material—only reference identifiers).

Example:

```python
from security.secret_rotation import verify_ref

if not verify_ref("OPENAI_KEY", "OPENAI_KEY:v2"):
    raise PermissionError("stale or unknown secret reference")
```

### Promoting a new secret

When calling `promote(logical_name, new_ref)` the existing `current_ref` (if
present) is shifted into `previous_ref` and its original activation timestamp is
stored in `previous_activated_at`. The grace window for the previous ref then
continues counting from that preserved timestamp ensuring deterministic expiry
even if multiple promotions happen quickly.

### Observability & auditing

Each verify attempt increments structured metrics (if enabled) and writes a
structured audit event indicating acceptance or rejection. This provides a
forensic trail during incident analysis (e.g. detecting replay attempts using
retired credentials during the grace boundary).

### Recommended rotation workflow

1. Export new secret (e.g. `OPENAI_KEY_V3`) alongside the existing version.
1. Deploy with a call to `promote("OPENAI_KEY", "OPENAI_KEY:v3")`.
1. Monitor logs/metrics for any `verify_accept` events referencing the previous
   ref; when they cease (or after grace expiry) remove the old environment
   variable (`OPENAI_KEY_V2`).
1. Optionally shorten grace via configuration once confidence is established.

This approach minimises downtime and avoids race conditions across rolling
deployments while keeping the previous credential’s validity strictly bounded.
