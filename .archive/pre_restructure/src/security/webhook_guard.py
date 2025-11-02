"""Inbound webhook verification utilities.

Provides a single high-level helper :func:`verify_incoming` that validates
HMAC signature headers (timestamp + nonce), enforces clock skew limits,
and emits structured security events. On failure a :class:`SecurityError`
is raised. Success returns ``True`` (idempotent) so callers can chain
additional validation if desired.

Configuration
-------------
Uses the ``webhooks`` section of ``config/security.yaml``:

webhooks:
  secrets:
    default: "CHANGE_ME"
    next: "ROTATING_KEY"   # optional second secret for rotation
  clock_skew_seconds: 300

Rotation Strategy
-----------------
Multiple secrets are all attempted during verification to permit a safe
rollover window. (Future enhancement can include key IDs.)
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING, Any, NamedTuple

import yaml

from .events import log_security_event
from .net_guard import SecurityError  # reuse exception type
from .secrets import get_secret
from .signing import verify_signature_headers


if TYPE_CHECKING:
    from collections.abc import Mapping


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "security.yaml"


def _load_webhook_config(path: Path | None = None) -> dict[str, Any]:
    path = path or DEFAULT_CONFIG_PATH
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text()) or {}
    return data.get("webhooks", {})


class _Ctx(NamedTuple):
    actor: str | None
    tenant: str | None
    workspace: str | None


def _log(decision: str, resource: str, reason: str, ctx: _Ctx, **extra: Any) -> None:
    log_security_event(
        actor=ctx.actor or "unknown",
        action="webhook",
        resource=resource,
        decision=decision,
        reason=reason,
        tenant=ctx.tenant,
        workspace=ctx.workspace,
        **extra,
    )


def verify_incoming(
    body: bytes,
    headers: Mapping[str, str],
    *,
    secret_id: str = "default",  # secret key identifier (not a secret value)
    config_path: Path | None = None,
    actor: str | None = None,
    tenant: str | None = None,
    workspace: str | None = None,
    signature_header: str = "X-Signature",
    timestamp_header: str = "X-Timestamp",
    nonce_header: str = "X-Nonce",
) -> bool:
    """Validate an inbound webhook request.

    Parameters
    ----------
    body: Raw request body bytes.
    headers: Case-insensitive mapping of header names to values (must supply the ones configured).
    secret_id: Key name within ``webhooks.secrets`` to prioritize. All secrets are attempted.
    config_path: Optional override path for config file.
    actor, tenant, workspace: Included in security events for audit.
    signature_header, timestamp_header, nonce_header: Override header names if necessary.

    Returns
    -------
    bool
        True if verification succeeds. Raises :class:`SecurityError` otherwise.
    """

    cfg = _load_webhook_config(config_path)
    ctx = _Ctx(actor, tenant, workspace)
    secrets_map: dict[str, str] = dict(cfg.get("secrets") or {})
    clock_skew = int(cfg.get("clock_skew_seconds", 300))
    # Derive secret reference from environment naming convention
    secret_ref = f"WEBHOOK_SECRET_{secret_id.upper()}"

    # Resolve candidate secrets: prefer config file mapping when present; otherwise
    # fall back to environment variable with validation against default/empty values.
    ordered: list[str] = []
    if secrets_map:
        # Try the specifically requested secret first, then any others to support rotation windows
        if secrets_map.get(secret_id):
            ordered.append(str(secrets_map[secret_id]))
        for k, v in secrets_map.items():
            if k != secret_id and v:
                ordered.append(str(v))
    else:
        import os as _os

        if secret_ref not in _os.environ:
            _log(
                "allow",
                resource="webhook:*",
                reason="no_secrets_configured",
                ctx=ctx,
            )
            return True
        try:
            secret = get_secret(secret_ref)
        except KeyError as exc:
            _log("block", resource="webhook:*", reason="missing_secret", ctx=ctx)
            raise SecurityError(f"Webhook secret not configured: WEBHOOK_SECRET_{secret_id.upper()}") from exc
        if secret in ("CHANGE_ME", "changeme", "default", ""):
            _log("block", resource="webhook:*", reason="default_secret", ctx=ctx)
            raise SecurityError(
                f"Webhook secret '{secret_id}' is using default/empty value. "
                f"Set {secret_ref} environment variable to a secure random value."
            )
        ordered = [secret]

    # Extract required headers.
    try:
        # Case-insensitive dict-like; we assume keys are present as given
        signature = headers[signature_header]
        ts_raw = headers[timestamp_header]
        headers[nonce_header]  # access to ensure presence only
    except KeyError as exc:
        _log("block", resource="webhook:*", reason="missing_headers", ctx=ctx)
        raise SecurityError("missing required signature headers") from exc

    # Attempt verification across candidate secrets.
    # Reuse verify_signature_headers sequentially until one passes.
    try:
        ts_int = int(ts_raw)
    except ValueError as exc:
        _log("block", resource="webhook:*", reason="bad_timestamp", ctx=ctx)
        raise SecurityError("invalid timestamp header") from exc

    verified = False
    for secret in ordered:
        if verify_signature_headers(
            body,
            secret,
            headers,
            signature_header=signature_header,
            timestamp_header=timestamp_header,
            nonce_header=nonce_header,
            tolerance=clock_skew,
        ):
            verified = True
            break

    if not verified:
        # Distinguish skew vs invalid vs replay to the extent possible:
        # If absolute skew exceeds limit treat as skew else generic invalid.
        now = int(time.time())
        reason = "skew" if abs(now - ts_int) > clock_skew else "invalid_signature_or_replay"
        _log("block", resource="webhook:*", reason=reason, ctx=ctx)
        raise SecurityError("webhook signature verification failed")

    _log(
        "allow",
        resource="webhook:*",
        reason="ok",
        ctx=ctx,
        signature_prefix=signature[:8],  # short prefix for correlation without leaking full HMAC
    )
    return True


__all__ = ["verify_incoming"]
