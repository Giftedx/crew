"""Policy registry for dependency injection."""
from __future__ import annotations

from typing import Dict


class PolicyRegistry:
    """A minimal registry for RL policies."""

    def __init__(self) -> None:
        self._policies: Dict[str, object] = {}

    def register(self, name: str, policy: object) -> None:
        self._policies[name] = policy

    def get(self, name: str) -> object:
        return self._policies[name]
