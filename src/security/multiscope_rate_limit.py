"""Multi-scope rate limiting with escalation.

This module layers on top of the simple :class:`TokenBucket` implementation to
provide per-scope (user / guild / command / provider) buckets and an escalation
cooldown mechanism driven by ``config/security.yaml``.

Usage:
    limiter = MultiScopeRateLimiter.from_config()
    allowed, reason, cooldown = limiter.check(
        user_id="u123", guild_id="g456", command="/context", provider="openai"
    )
    if not allowed:
        # Handle rejection (e.g., reply with retry-after or escalate alert)
        ...

Escalation:
    Consecutive violations within the reset window increment a counter. When a
    threshold is crossed the key is placed in cooldown for the configured
    duration; further requests auto-deny until cooldown expiry.
"""

from __future__ import annotations

import time
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .events import log_security_event
from .rate_limit import TokenBucket

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "security.yaml"


@dataclass
class _ViolationState:
    count: int = 0
    last_violation: float = 0.0
    cooldown_until: float = 0.0


class MultiScopeRateLimiter:
    """Composite limiter applying multiple scoped token buckets with escalation."""

    def __init__(
        self,
        buckets: dict[str, TokenBucket],
        escalation_thresholds: list[tuple[int, float]],
        reset_window: float,
    ) -> None:
        self._buckets = buckets
        self._escalation_thresholds = sorted(escalation_thresholds, key=lambda x: x[0])
        self._reset_window = reset_window
        self._violations: dict[str, _ViolationState] = {}

    # ---------------------- Construction ---------------------------------
    @classmethod
    def from_config(cls, path: Path | None = None) -> MultiScopeRateLimiter:
        cfg_path = path or DEFAULT_CONFIG_PATH
        raw: dict[str, Any] = {}
        if cfg_path.exists():
            raw = yaml.safe_load(cfg_path.read_text()) or {}
        rl = raw.get("rate_limits", {})
        scopes = rl.get("scopes", {})
        buckets: dict[str, TokenBucket] = {}
        # Convert per-minute config to per-second token bucket parameters.
        for name, conf in scopes.items():
            per_minute = conf.get("per_minute", 60)
            burst = conf.get("burst", per_minute)
            buckets[name] = TokenBucket(rate=per_minute / 60.0, capacity=burst)
        escalation_cfg = rl.get("escalation", {})
        thresholds_cfg = escalation_cfg.get("thresholds", [])
        thresholds: list[tuple[int, float]] = [
            (t.get("violations", 0), float(t.get("cooldown_seconds", 0))) for t in thresholds_cfg
        ]
        reset_window = float(escalation_cfg.get("reset_window_seconds", 900))
        return cls(buckets=buckets, escalation_thresholds=thresholds, reset_window=reset_window)

    # ---------------------- Public API -----------------------------------
    def check(  # noqa: PLR0913 - explicit parameters aid call clarity across varied callers
        self,
        *,
        user_id: str | None = None,
        guild_id: str | None = None,
        command: str | None = None,
        provider: str | None = None,
        tokens: float = 1.0,
        actor: str | None = None,
        tenant: str | None = None,
        workspace: str | None = None,
    ) -> tuple[bool, str | None, float | None]:
        """Evaluate all applicable scopes.

        Returns (allowed, reason, cooldown_seconds_remaining).
        ``reason`` is None on allow. If denied for active cooldown, reason is
        ``"cooldown"``; for token exhaustion it is ``"rate_limited"``.
        """
        now = time.monotonic()
        scope_keys: list[tuple[str, str]] = []
        if user_id:
            scope_keys.append(("user", user_id))
        if guild_id:
            scope_keys.append(("guild", guild_id))
        if command:
            scope_keys.append(("command", command))
        if provider:
            scope_keys.append(("provider", provider))

        # First check cooldowns.
        for scope, key in scope_keys:
            vs = self._violations.get(self._vk(scope, key))
            if vs and vs.cooldown_until > now:
                remaining = vs.cooldown_until - now
                self._log_event(
                    actor=actor,
                    tenant=tenant,
                    workspace=workspace,
                    scope=scope,
                    key=key,
                    decision="deny",
                    reason="cooldown",
                    extra={"cooldown_remaining": round(remaining, 2)},
                )
                return False, "cooldown", remaining

        # Evaluate buckets; any denial triggers violation tracking.
        for scope, key in scope_keys:
            bucket = self._buckets.get(scope)
            if bucket and not bucket.allow(self._vk(scope, key), tokens=tokens):
                cooldown = self._record_violation(scope, key, now)
                reason = "cooldown" if cooldown else "rate_limited"
                self._log_event(
                    actor=actor,
                    tenant=tenant,
                    workspace=workspace,
                    scope=scope,
                    key=key,
                    decision="deny",
                    reason=reason,
                    extra={"cooldown_applied": bool(cooldown)},
                )
                return False, reason, cooldown

        # Allow: optionally reset stale violation counters.
        self._maybe_reset(scope_keys, now)
        return True, None, None

    # ---------------------- Internal helpers -----------------------------
    def _vk(self, scope: str, key: str) -> str:
        return f"{scope}:{key}"

    def _record_violation(self, scope: str, key: str, now: float) -> float | None:
        k = self._vk(scope, key)
        vs = self._violations.setdefault(k, _ViolationState())
        if now - vs.last_violation > self._reset_window:
            vs.count = 0
        vs.count += 1
        vs.last_violation = now
        # Determine if any threshold crosses.
        cooldown: float | None = None
        for threshold, seconds in self._escalation_thresholds:
            if vs.count >= threshold:
                cooldown = seconds
        if cooldown:
            vs.cooldown_until = max(vs.cooldown_until, now + cooldown)
        return cooldown

    def _maybe_reset(self, scope_keys: Iterable[tuple[str, str]], now: float) -> None:
        for scope, key in scope_keys:
            k = self._vk(scope, key)
            vs = self._violations.get(k)
            if vs and now - vs.last_violation > self._reset_window and now >= vs.cooldown_until:
                self._violations.pop(k, None)

    def _log_event(  # noqa: PLR0913 - explicit structured security log fields
        self,
        *,
        actor: str | None,
        tenant: str | None,
        workspace: str | None,
        scope: str,
        key: str,
        decision: str,
        reason: str,
        extra: dict[str, Any] | None = None,
    ) -> None:  # noqa: PLR0913 - structured security log fields explicit
        log_security_event(
            actor=actor or "unknown",
            action="rate_limit",
            resource=f"{scope}:{key}",
            decision=decision,
            reason=reason,
            tenant=tenant,
            workspace=workspace,
            **(extra or {}),
        )


__all__ = ["MultiScopeRateLimiter"]
