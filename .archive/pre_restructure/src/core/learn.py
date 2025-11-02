"""Helper to execute a recommend-act-learn cycle for a decision domain."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, cast

from . import flags, reward_pipe
from .rl import feature_store, registry


if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence


class _PolicyLike(Protocol):  # mirrors interface used in learning_engine
    def recommend(self, context: Mapping[str, Any], candidates: Sequence[Any]) -> Any: ...
    def update(self, action: Any, reward: float, context: Mapping[str, Any]) -> None: ...


def learn(
    domain: str,
    context: Mapping[str, Any],
    candidates: Sequence[Any],
    act_fn: Callable[[Any], tuple[Mapping[str, Any], Mapping[str, Any]]],
    *,
    policy_registry: registry.PolicyRegistry | None = None,
    reward_weights: Mapping[str, float] | None = None,
):
    """Run a single recommend/act/update loop for ``domain``.

    Parameters
    ----------
    domain:
        Name of the decision domain (e.g. ``routing`` or ``prompt``).
    context:
        Context features describing the current call. They are passed through
        the feature store to obtain numeric features for the policy.
    candidates:
        Sequence of candidate arms the policy may choose from.
    act_fn:
        Callable that executes the chosen arm and returns a tuple of
        ``(outcome, signals)``. ``outcome`` contains metrics such as cost and
        latency while ``signals`` holds quality or safety measurements.
    policy_registry:
        Optional registry used to resolve the policy for ``domain``. A new
        instance is created if not provided.
    reward_weights:
        Optional overrides for reward component weights passed to the reward
        pipeline.

    Returns
    -------
    RewardResult
        The result produced by :func:`core.reward_pipe.compute` including the
        scalar reward and breakdown.
    """
    features = feature_store.featurize(dict(context))

    # Honour global and per-domain feature flags. If learning is disabled the
    # first candidate is executed without updating any policy state.
    if not (flags.enabled("ENABLE_RL_GLOBAL") and flags.enabled(f"ENABLE_RL_{domain.upper()}")):
        arm = candidates[0]
        outcome, signals = act_fn(arm)
        # feature_store expects a concrete dict for mutation; ensure copy
        feature_store.update_stats(dict(outcome))
        return reward_pipe.compute(
            domain,
            features,
            outcome,
            signals,
            weights=dict(reward_weights) if reward_weights else None,
        )

    reg = policy_registry or registry.PolicyRegistry()
    policy = cast("_PolicyLike", reg.get(domain))
    arm = policy.recommend(features, candidates)
    outcome, signals = act_fn(arm)
    feature_store.update_stats(dict(outcome))
    result = reward_pipe.compute(
        domain,
        features,
        outcome,
        signals,
        weights=dict(reward_weights) if reward_weights else None,
    )
    policy.update(arm, result.reward, features)
    return result
