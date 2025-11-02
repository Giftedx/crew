from __future__ import annotations

import random
import time
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from collections.abc import Callable


def retry(
    fn: Callable[[], Any],
    retries: int = 3,
    backoff: float = 0.1,
    factor: float = 2.0,
    exc: type[Exception] = Exception,
) -> Any:
    """Retry ``fn`` with exponential backoff and jitter."""
    for attempt in range(retries):
        try:
            return fn()
        except exc:
            if attempt == retries - 1:
                raise
            # Non-crypto jitter; acceptable to use random here. If crypto needed, swap to secrets.
            sleep = backoff * (factor**attempt) + random.random() * backoff
        time.sleep(sleep)
    return fn()  # pragma: no cover - logically unreachable


__all__ = ["retry"]
