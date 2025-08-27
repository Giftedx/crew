from __future__ import annotations

import random
import time
from typing import Callable, Type


def retry(fn: Callable[[], any], retries: int = 3, backoff: float = 0.1, factor: float = 2.0, exc: Type[Exception] = Exception):
    """Retry ``fn`` with exponential backoff and jitter."""
    for attempt in range(retries):
        try:
            return fn()
        except exc:
            if attempt == retries - 1:
                raise
            sleep = backoff * (factor ** attempt) + random.random() * backoff
            time.sleep(sleep)


__all__ = ["retry"]
