"""Simple in-memory caches for LLM calls and retrieval results."""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMCache:
    """Deterministic prompt→response cache with TTL."""

    ttl: int = 300
    _store: dict[str, tuple[float, dict[str, Any]]] = field(default_factory=dict)

    def _now(self) -> float:
        return time.time()

    def _is_valid(self, expiry: float) -> bool:
        return expiry > self._now()

    def make_key(self, prompt: str, model: str) -> str:
        digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        return f"{model}:{digest}"

    def get(self, key: str) -> dict[str, Any] | None:
        item = self._store.get(key)
        if not item:
            return None
        expiry, value = item
        if self._is_valid(expiry):
            return value
        self._store.pop(key, None)
        return None

    def set(self, key: str, value: dict[str, Any]) -> None:
        self._store[key] = (self._now() + self.ttl, value)
