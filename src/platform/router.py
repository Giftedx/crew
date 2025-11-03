"""Minimal routing facade used in tests.

Provides a very small ``Router`` class that delegates to a learning engine
when available, otherwise picks the first candidate.
"""

from __future__ import annotations

from typing import Any


try:
    # Optional import; tests may run without full RL stack.
    from platform.rl.learning_engine import LearningEngine  # type: ignore
except Exception:  # pragma: no cover - fallback for minimal envs

    class LearningEngine:  # type: ignore
        def recommend(self, *_args: Any, **_kwargs: Any) -> str:
            return "gpt-3.5-turbo"


class Router:
    def __init__(self, engine: LearningEngine | None = None) -> None:  # type: ignore[name-defined]
        self._engine = engine

    def route(self, task: str, candidates: list[str] | None = None, context: dict[str, Any] | None = None) -> str:
        candidates = candidates or ["gpt-3.5-turbo"]
        context = context or {}
        if self._engine:
            try:
                return self._engine.recommend(task, context, candidates)
            except Exception:
                return candidates[0]
        return candidates[0]


__all__ = ["Router"]
