"""Reward pipeline that fuses signals into a scalar reward."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from .rl import reward_engine


if TYPE_CHECKING:
    from collections.abc import Mapping, MutableMapping


@dataclass
class RewardResult:
    """Result returned by :func:`compute`.

    Attributes
    ----------
    domain:
        Name of the decision domain the reward corresponds to.
    context:
        Context features associated with the call.
    reward:
        The scalar composite reward value.
    breakdown:
        The :class:`reward_engine.RewardBreakdown` for inspection.
    signals:
        Raw reward signals provided by callers.
    outcome:
        Raw outcome metrics such as cost or latency.
    """

    domain: str
    context: dict[str, Any]
    reward: float
    breakdown: reward_engine.RewardBreakdown
    signals: dict[str, Any]
    outcome: dict[str, Any]


def compute(
    domain: str,
    context: Mapping[str, Any],
    outcome: Mapping[str, Any],
    signals: Mapping[str, Any],
    *,
    weights: MutableMapping[str, float] | None = None,
) -> RewardResult:
    """Compute the scalar reward for ``domain``.

    Parameters
    ----------
    domain:
        Name of the decision domain (routing, prompt, retrieval, ...).
    context:
        Context features associated with the call. Currently unused but kept
        for future extensions.
    outcome:
        Mapping of system metrics such as cost and latency.
    signals:
        Quality and safety related measurements.
    weights:
        Optional overrides for component weights passed through to the
        reward engine.

    Returns
    -------
    RewardResult
        Object containing the scalar reward, the breakdown, and raw inputs for
        logging or downstream analysis.
    """

    breakdown = reward_engine.compute_reward(outcome, signals, weights)
    return RewardResult(
        domain=domain,
        context=dict(context),
        reward=breakdown.total,
        breakdown=breakdown,
        signals=dict(signals),
        outcome=dict(outcome),
    )
