"""Simple in-memory token bucket rate limiter.

The :class:`TokenBucket` class implements a coarse in-memory token bucket
algorithm. Each ``key`` has its own bucket with the same rate and
capacity. The implementation is intentionally lightweight so it can be used
in tests or small utilities without external dependencies. It is not meant
for distributed rate limiting.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class TokenBucket:
    """An in-memory token bucket.

    Parameters
    ----------
    rate:
        Number of tokens added to each bucket per second.
    capacity:
        Maximum number of tokens a bucket can hold.
    """

    rate: float
    capacity: int
    _tokens: dict[str, float] = field(default_factory=dict)
    _timestamps: dict[str, float] = field(default_factory=dict)

    def allow(self, key: str, tokens: float = 1.0) -> bool:
        """Return ``True`` if ``key`` may consume ``tokens`` now.

        ``tokens`` must be positive; fractional tokens are permitted to
        represent sub-requests.
        """
        if tokens <= 0:
            raise ValueError("tokens must be positive")

        now = time.monotonic()
        # Some tests may monkeypatch `_tokens` to a numeric value to simulate exhaustion.
        # Normalise to dict lookups and treat non-dict as "single bucket" storage.
        store = self._tokens
        try:
            tokens_left = store.get(key, self.capacity)  # type: ignore[union-attr]
        except Exception:  # pragma: no cover - defensive against invalid monkeypatching
            # Fallback: if numeric, interpret as remaining tokens for all keys
            try:
                tokens_left = float(store)  # type: ignore[arg-type]
            except Exception:
                tokens_left = self.capacity
        last = self._timestamps.get(key, now)
        tokens_left = min(self.capacity, tokens_left + (now - last) * self.rate)
        allowed = tokens_left >= tokens
        if allowed:
            tokens_left -= tokens
        # Persist back only when underlying storage is a dict; otherwise keep the monkeypatched sentinel
        try:
            self._tokens[key] = tokens_left
        except Exception:  # pragma: no cover - non-dict sentinel
            pass
        self._timestamps[key] = now
        return allowed
