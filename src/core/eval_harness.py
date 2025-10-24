"""Simple A/B evaluation harness using the reward pipeline."""

from __future__ import annotations

from collections.abc import Callable

from .reward_pipe import RewardResult, compute


CandidateFn = Callable[[], tuple[dict[str, float], dict[str, float]]]


def bakeoff(candidates: dict[str, CandidateFn], context: dict[str, float]) -> dict[str, RewardResult]:
    """Run each candidate function and compute rewards.

    ``candidates`` maps an identifier to a callable returning ``(outcome, signals)``.
    The resulting mapping associates each identifier with its :class:`RewardResult`.
    """

    results: dict[str, RewardResult] = {}
    for name, fn in candidates.items():
        outcome, signals = fn()
        results[name] = compute("eval", context, outcome, signals)
    return results


__all__ = ["bakeoff"]
