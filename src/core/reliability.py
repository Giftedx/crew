from __future__ import annotations

import random
import time
from collections.abc import Callable
from typing import Any


def retry(
    fn: Callable[[], Any],
    retries: int = 3,
    backoff: float = 0.1,
    factor: float = 2.0,
    exc: type[Exception] = Exception,
):
    """Retry ``fn`` with exponential backoff and jitter."""
    for attempt in range(retries):
        try:
            return fn()
        except exc:
            if attempt == retries - 1:
                raise
            sleep = backoff * (factor**attempt) + random.random() * backoff
            time.sleep(sleep)


__all__ = ["retry"]
