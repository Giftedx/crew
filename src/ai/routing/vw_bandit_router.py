"""Experimental Vowpal Wabbit-based bandit router (graceful fallback).

This wrapper is gated by ENABLE_VW_BANDIT or ENABLE_VOWPAL_WABBIT_BANDIT.
If the `vowpalwabbit` package is not installed, the router automatically
falls back to `ThompsonBanditRouter` to preserve behavior.

Design goals:
- Optional dependency; import guarded
- Stateless API compatible with ThompsonBanditRouter
- Minimal placeholder that can be upgraded to true VW CB/ADF integration later
"""

from __future__ import annotations

import os
from collections.abc import Sequence
from typing import Any

try:  # Optional dependency
    # Note: depending on version, import path can be `vowpalwabbit` or `vowpalwabbit_next`.
    # We only detect presence; full CB/ADF integration is future work.
    import vowpalwabbit as _vw

    VW_AVAILABLE = True
except Exception:  # pragma: no cover - optional
    VW_AVAILABLE = False
    _vw = None

from .bandit_router import ThompsonBanditRouter


def _flag_enabled() -> bool:
    return any(
        os.getenv(k, "0").lower() in {"1", "true", "yes", "on"}
        for k in ("ENABLE_VW_BANDIT", "ENABLE_VOWPAL_WABBIT_BANDIT")
    )


class VWBanditRouter:
    """Router that prefers Vowpal Wabbit when available; otherwise Thompson fallback.

    Public methods mirror ThompsonBanditRouter:
      - select(arms: Sequence[str], context: dict[str, Any] | None = None) -> str
      - update(arm: str, reward: float, context: dict[str, Any] | None = None) -> None
    """

    def __init__(self) -> None:
        self.enabled = _flag_enabled()
        # Fallback router always present to guarantee functionality
        self._fallback = ThompsonBanditRouter()
        self._vw_ready = bool(self.enabled and VW_AVAILABLE)
        # Placeholder for future VW workspace/model fields
        self._vw_model: Any | None = None
        if self._vw_ready:
            # Defer real VW setup for a future iteration
            # Keeping behavior identical to fallback for now
            self._vw_model = None

    def select(self, arms: Sequence[str], context: dict[str, Any] | None = None) -> str:  # noqa: ARG002
        # Until VW integration is implemented, delegate to fallback
        return self._fallback.select(arms)

    def update(self, arm: str, reward: float, context: dict[str, Any] | None = None) -> None:  # noqa: ARG002
        # Delegate to fallback policy
        self._fallback.update(arm, reward)


__all__ = ["VWBanditRouter", "VW_AVAILABLE"]
