from __future__ import annotations

import logging
from functools import wraps
from typing import TYPE_CHECKING, ParamSpec, TypeVar

from .context import TenantContext, current_tenant


if TYPE_CHECKING:
    from collections.abc import Callable


P = ParamSpec("P")
R = TypeVar("R")


def require_tenant(
    strict_flag_enabled: bool = True,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator to enforce presence of TenantContext.

    If ``strict_flag_enabled`` is True, raise when context is missing; otherwise log a warning
    and continue. This centralizes tenancy checks to avoid copy/paste across services.
    """

    def decorator(fn: Callable[P, R]) -> Callable[P, R]:
        @wraps(fn)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            ctx = current_tenant()
            if ctx is None:
                if strict_flag_enabled:
                    raise RuntimeError("TenantContext required but not set")
                logging.getLogger("tenancy").warning("TenantContext missing; proceeding in non-strict mode")
            return fn(*args, **kwargs)

        return wrapper

    return decorator


__all__ = ["TenantContext", "require_tenant"]
