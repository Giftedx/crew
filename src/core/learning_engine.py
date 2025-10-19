"""High-level API for registering and using bandit policies."""

from __future__ import annotations

import os
import time
from collections.abc import Mapping, Sequence
from typing import Any, Protocol, cast, runtime_checkable

from obs import metrics

from .error_handling import log_error
from .rl.advanced_config import get_config_manager
from .rl.experiment import ExperimentManager
from .rl.policies.advanced_bandits import DoublyRobustBandit, OffsetTreeBandit
from .rl.policies.bandit_base import (
    EpsilonGreedyBandit,
    ThompsonSamplingBandit,
    UCB1Bandit,
)
from .rl.policies.lints import LinTSDiagBandit
from .rl.policies.linucb import LinUCBDiagBandit
from .rl.registry import PolicyRegistry

try:  # optional dependency
    from .rl.policies.vowpal_wabbit import VowpalWabbitBandit
except Exception:  # pragma: no cover - gracefully degrade when VW missing
    VowpalWabbitBandit = None  # type: ignore[assignment]

try:
    from .settings import get_settings
except (ImportError, ModuleNotFoundError) as e:  # More specific exception types
    # Log the import failure for debugging
    log_error(
        e,
        message="Failed to import settings module, using fallback",
        context={"module": "core.settings"},
    )

    def get_settings():  # type: ignore
        class _S:  # minimal attribute surface used in this module
            rl_policy_model_selection = "epsilon_greedy"

        return _S()  # returning instance keeps attribute access consistent


@runtime_checkable
class _BanditLike(Protocol):  # minimal protocol for bandit policies
    def recommend(self, context: dict[str, Any], candidates: Sequence[Any]) -> Any: ...
    def update(self, action: Any, reward: float, context: dict[str, Any]) -> None: ...


class LearningEngine:
    """Wrapper around the RL policy registry."""

    def __init__(
        self,
        registry: PolicyRegistry | None = None,
        experiment_manager: ExperimentManager | None = None,
    ) -> None:
        self.registry = registry or PolicyRegistry()
        # Lazy opt-in experiment harness; zero cost if flag disabled.
        self._exp_mgr = experiment_manager or ExperimentManager()

    def register_domain(
        self,
        name: str,
        policy: object | None = None,
        priors: dict[Any, float] | None = None,
    ) -> None:
        """Register ``policy`` under ``name`` and apply optional ``priors``."""
        if policy is None:
            # Choose default policy from settings (fallback epsilon)
            try:
                policy_name = getattr(
                    get_settings(), "rl_policy_model_selection", "epsilon_greedy"
                )
            except (AttributeError, TypeError) as e:
                log_error(
                    e,
                    message="Failed to get policy selection from settings, using default",
                    context={"default_policy": "epsilon_greedy"},
                )
                policy_name = "epsilon_greedy"
            p = str(policy_name).lower().strip()

            # Feature flag overrides (explicit enable wins irrespective of config default)
            # Order of precedence: explicit env force -> configured policy -> fallback
            force_vowpal = os.getenv("ENABLE_RL_VOWPAL", "").lower() in {
                "1",
                "true",
                "yes",
                "on",
            }
            force_thompson = os.getenv("ENABLE_RL_THOMPSON", "").lower() in {
                "1",
                "true",
                "yes",
                "on",
            }
            force_contextual = os.getenv("ENABLE_RL_CONTEXTUAL", "").lower() in {
                "1",
                "true",
                "yes",
                "on",
            }
            force_advanced = os.getenv("ENABLE_RL_ADVANCED", "").lower() in {
                "1",
                "true",
                "yes",
                "on",
            }

            bandit: _BanditLike
            if (
                force_vowpal or p in {"vowpal", "vw", "vowpal_wabbit"}
            ) and VowpalWabbitBandit is None:
                log_error(
                    RuntimeError("vowpalwabbit missing"),
                    message="Vowpal Wabbit bandit requested but dependency is not installed",
                    context={"policy": p},
                )
            if (
                force_vowpal or p in {"vowpal", "vw", "vowpal_wabbit"}
            ) and VowpalWabbitBandit is not None:
                try:
                    vw_args = getattr(get_settings(), "vw_bandit_args", None)
                except Exception:  # pragma: no cover - defensive fallback
                    vw_args = None
                try:
                    bandit = VowpalWabbitBandit(vw_args=vw_args)
                except Exception as exc:  # pragma: no cover - fallback
                    log_error(
                        exc,
                        message="Failed to initialize Vowpal Wabbit bandit; falling back to epsilon-greedy",
                        context={"policy": p},
                    )
                    bandit = EpsilonGreedyBandit()
            elif force_advanced:
                config_manager = get_config_manager()
                if p in {"doubly_robust", "doubler", "dr"}:
                    dr_config = config_manager.get_doubly_robust_config()
                    bandit = DoublyRobustBandit(
                        alpha=dr_config.alpha,
                        dim=dr_config.dim,
                        learning_rate=dr_config.learning_rate,
                    )
                elif p in {"offset_tree", "tree", "ot"}:
                    ot_config = config_manager.get_offset_tree_config()
                    bandit = OffsetTreeBandit(
                        max_depth=ot_config.max_depth,
                        min_samples_split=ot_config.min_samples_split,
                        split_threshold=ot_config.split_threshold,
                    )
                else:
                    # Default advanced algorithm
                    dr_config = config_manager.get_doubly_robust_config()
                    bandit = DoublyRobustBandit(
                        alpha=dr_config.alpha,
                        dim=dr_config.dim,
                        learning_rate=dr_config.learning_rate,
                    )
            elif force_contextual:
                bandit = LinUCBDiagBandit()
            elif force_thompson:
                bandit = ThompsonSamplingBandit()
            elif p == "linucb":
                bandit = LinUCBDiagBandit()
            elif p in {"lints", "lin_ts", "linthompsonsampling"} or (
                os.getenv("ENABLE_RL_LINTS", "").lower() in {"1", "true", "yes", "on"}
                and p == "lints"
            ):
                bandit = LinTSDiagBandit()
            elif p in ("ucb1", "ucb"):
                bandit = UCB1Bandit()
            elif p in ("ts", "thompson", "thompson_sampling"):
                bandit = ThompsonSamplingBandit()
            elif p in {"doubly_robust", "doubler", "dr"}:
                config_manager = get_config_manager()
                dr_config = config_manager.get_doubly_robust_config()
                bandit = DoublyRobustBandit(
                    alpha=dr_config.alpha,
                    dim=dr_config.dim,
                    learning_rate=dr_config.learning_rate,
                )
            elif p in {"offset_tree", "tree", "ot"}:
                config_manager = get_config_manager()
                ot_config = config_manager.get_offset_tree_config()
                bandit = OffsetTreeBandit(
                    max_depth=ot_config.max_depth,
                    min_samples_split=ot_config.min_samples_split,
                    split_threshold=ot_config.split_threshold,
                )
            elif (
                force_vowpal or p in {"vowpal", "vw", "vowpal_wabbit"}
            ) and VowpalWabbitBandit is not None:
                try:
                    vw_args = getattr(get_settings(), "vw_bandit_args", None)
                except Exception:  # pragma: no cover - defensive fallback
                    vw_args = None
                try:
                    bandit = VowpalWabbitBandit(vw_args=vw_args)
                except Exception as exc:  # pragma: no cover - fallback
                    log_error(
                        exc,
                        message="Failed to initialize Vowpal Wabbit bandit; falling back to epsilon-greedy",
                        context={"policy": p},
                    )
                    bandit = EpsilonGreedyBandit()
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
        # Emit ACTIVE_BANDIT_POLICY gauge (1 for active)
        try:
            metrics.ACTIVE_BANDIT_POLICY.labels(
                **metrics.label_ctx(), domain=name, policy=bandit.__class__.__name__
            ).set(1)
        except Exception:
            pass

    def recommend(
        self, domain: str, context: dict[str, Any], candidates: Sequence[Any]
    ) -> Any:
        policy = cast(_BanditLike, self.registry.get(domain))
        if not candidates:
            raise ValueError("candidates must not be empty")
        # Experiment path (flag gated)
        if os.getenv("ENABLE_EXPERIMENT_HARNESS", "").lower() in {
            "1",
            "true",
            "yes",
            "on",
        }:
            exp_id = f"policy::{domain}"
            if self._exp_mgr.exists(exp_id):
                # Map policy-level candidates to variants (string names expected)
                variant_choice = self._exp_mgr.recommend(
                    exp_id, context, [str(c) for c in candidates]
                )
                # If the experiment returns a candidate that exists, use that; else fallback to policy.
                if variant_choice in candidates:
                    return variant_choice
        return policy.recommend(context, candidates)

    def record(
        self, domain: str, context: dict[str, Any], action: Any, reward: float
    ) -> None:
        policy = cast(_BanditLike, self.registry.get(domain))
        started = time.perf_counter()
        policy.update(action, reward, context)
        try:
            gap_ms = (time.perf_counter() - started) * 1000.0
            metrics.RL_REWARD_LATENCY_GAP.labels(
                **metrics.label_ctx(), domain=domain
            ).observe(gap_ms)
        except Exception:
            pass
        if os.getenv("ENABLE_EXPERIMENT_HARNESS", "").lower() in {
            "1",
            "true",
            "yes",
            "on",
        }:
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
            if hasattr(policy, "state_dict") and callable(
                getattr(policy, "state_dict")
            ):
                try:
                    state = getattr(policy, "state_dict")()
                    if isinstance(state, dict):
                        data[name] = state
                        continue
                except Exception:
                    pass
            q_values = dict(getattr(policy, "q_values", {}))
            counts = dict(getattr(policy, "counts", {}))
            data[name] = {
                "policy": policy.__class__.__name__,
                "q_values": q_values,
                "counts": counts,
            }
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
            if hasattr(policy, "load_state") and callable(
                getattr(policy, "load_state")
            ):
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
        # Shadow evaluation path (does not affect live choice)
        shadow_enabled = os.getenv("ENABLE_RL_SHADOW", "").lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        choice = self.recommend(domain, {}, candidates)
        if shadow_enabled:
            try:
                # Evaluate Thompson, LinUCB, and LinTS in shadow if they are not the active policy
                shadow_candidates: list[tuple[str, _BanditLike]] = []
                active = self.registry.get(domain)
                if not isinstance(active, ThompsonSamplingBandit):
                    shadow_candidates.append(("thompson", ThompsonSamplingBandit()))
                if not isinstance(active, LinUCBDiagBandit):
                    shadow_candidates.append(("linucb", LinUCBDiagBandit()))
                # Add LinTS shadow evaluation if flag is enabled
                if os.getenv("ENABLE_RL_LINTS", "").lower() in {
                    "1",
                    "true",
                    "yes",
                    "on",
                } and not isinstance(active, LinTSDiagBandit):
                    shadow_candidates.append(("lints", LinTSDiagBandit()))

                for tag, policy in shadow_candidates:
                    try:
                        # Independent recommendation (no update to keep pure observation)
                        shadow_pick = policy.recommend({}, candidates)
                        # Encode as similarity (1 if same model else 0) using existing metric surfaces (reuse model_selected counter with task=shadow::<tag>)
                        metrics.LLM_MODEL_SELECTED.labels(
                            **metrics.label_ctx(),
                            task=f"shadow::{tag}",
                            model=str(shadow_pick),
                            provider="shadow",
                        ).inc()
                    except Exception:
                        continue
            except Exception:
                pass
        return cast(str, choice)

    def update(self, task_type: str, action: str, reward: float) -> None:
        """Legacy convenience update for model selection domains."""
        domain = f"route.model.select::{task_type}"
        if domain not in self.registry:
            self.register_domain(domain)
        self.record(domain, {}, action, reward)

        # Update shadow regret tracking if LinTS shadow mode is enabled
        if os.getenv("ENABLE_RL_LINTS", "").lower() in {"1", "true", "yes", "on"}:
            try:
                from .rl.shadow_regret import get_shadow_tracker

                tracker = get_shadow_tracker()
                tracker.update_baseline(reward)
            except Exception:
                pass  # Shadow tracking should never affect main flow


__all__ = ["LearningEngine"]
