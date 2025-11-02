"""Global registry for RLModelRouter singleton.

This module provides a simple, thread-safe registry for a shared
RLModelRouter instance so that disparate parts of the system (e.g.,
trajectory evaluators emitting feedback and background processors
draining the feedback queue) can coordinate on the same router.

Design goals:
- Optional dependency: avoid importing RLModelRouter at module import time
  to prevent circular imports. Type hints are guarded behind TYPE_CHECKING.
- Safe defaults: get_rl_model_router(create_if_missing=True) lazily creates
  an instance when needed; callers can disable creation to simply probe.
- Testability: set_rl_model_router(...) allows tests or services to inject
  a pre-constructed instance (e.g., PerformanceLearningEngine.model_router).
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any


_LOCK = threading.RLock()
_INSTANCE: Any | None = None


if TYPE_CHECKING:  # pragma: no cover
    # Import for type checking only to avoid runtime cycles
    from .rl_model_router import RLModelRouter  # noqa: F401


def set_rl_model_router(router: Any) -> None:
    """Register a shared RLModelRouter instance.

    Accepts Any to avoid importing RLModelRouter at runtime in this module.
    """
    global _INSTANCE
    with _LOCK:
        _INSTANCE = router


def get_rl_model_router(create_if_missing: bool = True) -> Any | None:
    """Return the shared RLModelRouter instance.

    If none is registered and ``create_if_missing`` is True, a new instance
    will be constructed lazily.
    """
    global _INSTANCE
    with _LOCK:
        if _INSTANCE is not None:
            return _INSTANCE
        if not create_if_missing:
            return None
        # Lazy import to avoid circular dependencies
        try:
            from .rl_model_router import RLModelRouter  # type: ignore

            _INSTANCE = RLModelRouter()
            return _INSTANCE
        except Exception:
            # If construction fails, leave as None so callers can degrade gracefully
            return None


__all__ = ["get_rl_model_router", "set_rl_model_router"]
