"""Simple A/B evaluation harness using the reward pipeline."""
from __future__ import annotations

from typing import Callable, Dict, Tuple

from .reward_pipe import compute, RewardResult

CandidateFn = Callable[[], Tuple[Dict[str, float], Dict[str, float]]]


def bakeoff(candidates: Dict[str, CandidateFn], context: Dict[str, float]) -> Dict[str, RewardResult]:
    """Run each candidate function and compute rewards.

    ``candidates`` maps an identifier to a callable returning ``(outcome, signals)``.
    The resulting mapping associates each identifier with its :class:`RewardResult`.
    """

    results: Dict[str, RewardResult] = {}
    for name, fn in candidates.items():
        outcome, signals = fn()
        results[name] = compute("eval", context, outcome, signals)
    return results


__all__ = ["bakeoff"]
