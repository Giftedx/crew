"""Security event logging helpers.

This module provides a tiny wrapper around :mod:`obs.logging` so that
security relevant actions are recorded in a consistent JSON format.
"""

from __future__ import annotations

from typing import Any

from ultimate_discord_intelligence_bot.obs.logging import logger


def log_security_event(
    *,
    actor: str,
    action: str,
    resource: str,
    decision: str,
    reason: str | None = None,
    tenant: str | None = None,
    workspace: str | None = None,
    **extra: Any,
) -> None:
    """Emit a structured security event.

    Parameters
    ----------
    actor:
        Identifier for the user or system responsible for the action.
    action:
        Subsystem or category, e.g. ``"rbac"`` or ``"moderation"``.
    resource:
        Target of the action such as a permission string or URL.
    decision:
        Outcome like ``"allow"``, ``"deny"`` or ``"block"``.
    reason:
        Optional human readable reason for the decision.
    tenant, workspace:
        Optional tenancy identifiers.
    extra:
        Additional key-value pairs to include in the log payload.
    """
    payload: dict[str, Any] = {"actor": actor, "action": action, "resource": resource, "decision": decision}
    if reason is not None:
        payload["reason"] = reason
    if tenant is not None:
        payload["tenant"] = tenant
    if workspace is not None:
        payload["workspace"] = workspace
    if extra:
        payload.update(extra)
    logger.info("security_event", **payload)


__all__ = ["log_security_event"]
