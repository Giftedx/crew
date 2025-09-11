"""High-level API for registering and using bandit policies."""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from typing import Any, Protocol, cast, runtime_checkable

from .error_handling import log_error
from .rl.experiment import ExperimentManager
from .rl.policies.bandit_base import EpsilonGreedyBandit, ThompsonSamplingBandit, UCB1Bandit
from .rl.policies.lints import LinTSDiagBandit
from .rl.policies.linucb import LinUCBDiagBandit
from .rl.registry import PolicyRegistry

try:
    from .settings import get_settings
except (ImportError, ModuleNotFoundError) as e:  # More specific exception types
    # Log the import failure for debugging
    log_error(e, message="Failed to import settings module, using fallback", context={"module": "core.settings"})

    def get_settings():  # type: ignore
        class _S:
            rl_policy_model_selection = "epsilon_greedy"

        return _S()


@runtime_checkable
class _BanditLike(Protocol):  # minimal protocol for bandit policies
    def recommend(self, context: dict[str, Any], candidates: Sequence[Any]) -> Any: ...
    def update(self, action: Any, reward: float, context: dict[str, Any]) -> None: ...


class LearningEngine:
    """Wrapper around the RL policy registry."""

    def __init__(
        self, registry: PolicyRegistry | None = None, experiment_manager: ExperimentManager | None = None
    ) -> None:
        self.registry = registry or PolicyRegistry()
        # Lazy opt-in experiment harness; zero cost if flag disabled.
        self._exp_mgr = experiment_manager or ExperimentManager()

    def register_domain(self, name: str, policy: object | None = None, priors: dict[Any, float] | None = None) -> None:
        """Register ``policy`` under ``name`` and apply optional ``priors``."""

        if policy is None:
            # Choose default policy from settings
            try:
                policy_name = getattr(get_settings(), "rl_policy_model_selection", "epsilon_greedy")
            except (AttributeError, TypeError) as e:
                # More specific exception handling for settings access
                log_error(
                    e,
                    message="Failed to get policy selection from settings, using default",
                    context={"default_policy": "epsilon_greedy"},
                )
                policy_name = "epsilon_greedy"
            p = str(policy_name).lower().strip()
            bandit: _BanditLike
            if p == "linucb":
                bandit = LinUCBDiagBandit()
            elif p in {"lints", "lin_ts", "linthompsonsampling"} or (
                os.getenv("ENABLE_RL_LINTS", "").lower() in {"1", "true", "yes", "on"} and p == "lints"
            ):
                bandit = LinTSDiagBandit()
            elif p in ("ucb1", "ucb"):
                bandit = UCB1Bandit()
            elif p in ("ts", "thompson", "thompson_sampling"):
                bandit = ThompsonSamplingBandit()
            else:
                bandit = EpsilonGreedyBandit()
        else:
            bandit = cast(_BanditLike, policy)
        if priors and hasattr(bandit, "q_values"):
            # Access via Any to avoid blanket ignore; many bandit policies expose mutable q_values dict
            qv = cast(Any, getattr(bandit, "q_values"))
            for arm, q in priors.items():
                try:
                    qv[arm] = q
                except Exception:
                    pass
        self.registry.register(name, bandit)

    def recommend(self, domain: str, context: dict[str, Any], candidates: Sequence[Any]) -> Any:
        policy = cast(_BanditLike, self.registry.get(domain))
        if not candidates:
            raise ValueError("candidates must not be empty")
        # Experiment path (flag gated)
        if os.getenv("ENABLE_EXPERIMENT_HARNESS", "").lower() in {"1", "true", "yes", "on"}:
            exp_id = f"policy::{domain}"
            if self._exp_mgr.exists(exp_id):
                # Map policy-level candidates to variants (string names expected)
                variant_choice = self._exp_mgr.recommend(exp_id, context, [str(c) for c in candidates])
                # If the experiment returns a candidate that exists, use that; else fallback to policy.
                if variant_choice in candidates:
                    return variant_choice
        return policy.recommend(context, candidates)

    def record(self, domain: str, context: dict[str, Any], action: Any, reward: float) -> None:
        policy = cast(_BanditLike, self.registry.get(domain))
        policy.update(action, reward, context)
        if os.getenv("ENABLE_EXPERIMENT_HARNESS", "").lower() in {"1", "true", "yes", "on"}:
            exp_id = f"policy::{domain}"
            if self._exp_mgr.exists(exp_id):
                self._exp_mgr.record(exp_id, str(action), reward)

    # ------------------------------------------------------------------ cold-start
    def shadow_bakeoff(
        self,
        domain: str,
        candidates: Sequence[Any],
        trial_fn: Any,
    ) -> None:
        """Run a shadow bakeoff evaluating ``candidates`` without affecting live calls.

        ``trial_fn`` should be a callable accepting an arm and returning a
        reward.  Each candidate is evaluated once and the resulting reward is
        recorded in the policy.  This provides a cheap cold-start prior before
        the domain is used in production.
        """

        for arm in candidates:
            reward = trial_fn(arm)
            self.record(domain, {}, arm, reward)

    # ------------------------------------------------------------------ ops
    def snapshot(self) -> dict[str, dict[str, Any]]:
        """Return a snapshot of all registered policy state.

        The snapshot is a serialisable dictionary mapping ``domain`` to the
        policy class name together with its ``q_values`` and ``counts``.  It can
        be persisted externally and later passed to :meth:`restore` to roll back
        to an earlier state.
        """

        data: dict[str, dict[str, Any]] = {}
        for name, policy_obj in self.registry.items():
            policy = cast(_BanditLike, policy_obj)
            # Prefer richer state when available
            if hasattr(policy, "state_dict") and callable(getattr(policy, "state_dict")):
                try:
                    state = getattr(policy, "state_dict")()
                    if isinstance(state, dict):
                        data[name] = state
                        continue
                except Exception:
                    pass
            q_values = dict(getattr(policy, "q_values", {}))
            counts = dict(getattr(policy, "counts", {}))
            data[name] = {"policy": policy.__class__.__name__, "q_values": q_values, "counts": counts}
        return data

    def restore(self, snapshot: Mapping[str, Mapping[str, Any]]) -> None:
        """Restore policy state from ``snapshot`` produced by :meth:`snapshot`."""

        for name, state in snapshot.items():
            policy = cast(_BanditLike, self.registry.get(name))
            # If the snapshot declares a future version we do not understand, skip early.
            ver = state.get("version") if isinstance(state, Mapping) else None
            if ver is not None and ver > 1:
                continue
            # Prefer richer restore when available
            if hasattr(policy, "load_state") and callable(getattr(policy, "load_state")):
                try:
                    getattr(policy, "load_state")(state)
                    continue
                except Exception:
                    pass
            q_vals = state.get("q_values", {})
            counts = state.get("counts", {})
            # Access optional attributes via Any to satisfy type-checkers
            _p_any = cast(Any, policy)
            if hasattr(_p_any, "q_values") and isinstance(q_vals, Mapping):
                _p_any.q_values.clear()
                _p_any.q_values.update(cast(Mapping[Any, float], q_vals))
            if hasattr(_p_any, "counts") and isinstance(counts, Mapping):
                _p_any.counts.clear()
                _p_any.counts.update(cast(Mapping[Any, int], counts))

    def status(self) -> dict[str, dict[str, Any]]:
        """Return a diagnostic view of all policies and their arms."""

        summary: dict[str, dict[str, Any]] = {}
        for name, policy_obj in self.registry.items():
            policy = cast(_BanditLike, policy_obj)
            arms: dict[Any, dict[str, float | int]] = {}
            q_vals = getattr(policy, "q_values", {})
            counts = getattr(policy, "counts", {})
            for arm, q in q_vals.items():
                arms[arm] = {"q": float(q), "n": int(counts.get(arm, 0))}
            summary[name] = {"policy": policy.__class__.__name__, "arms": arms}
        return summary

    # ------------------- Convenience helpers (legacy compatibility) -------------------
    def select_model(self, task_type: str, candidates: Sequence[str]) -> str:
        """Legacy convenience wrapper used by services.

        Ensures a domain for the given task_type exists and returns a recommended arm.
        """
        domain = f"route.model.select::{task_type}"
        if domain not in self.registry:
            self.register_domain(domain)
        choice = self.recommend(domain, {}, candidates)
        return cast(str, choice)

    def update(self, task_type: str, action: str, reward: float) -> None:
        """Legacy convenience update for model selection domains."""
        domain = f"route.model.select::{task_type}"
        if domain not in self.registry:
            self.register_domain(domain)
        self.record(domain, {}, action, reward)


__all__ = ["LearningEngine"]
