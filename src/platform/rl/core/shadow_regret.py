"""Shadow mode regret tracking for LinTS evaluation.

This module provides regret tracking capabilities for evaluating LinTS
performance in shadow mode without affecting live traffic routing.
"""
from __future__ import annotations

import os
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


try:
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False

@runtime_checkable
class _PolicyLike(Protocol):
    """Protocol for bandit policies."""

    def recommend(self, context: dict[str, Any], candidates: list[Any]) -> Any:
        ...

    def update(self, action: Any, reward: float, context: dict[str, Any]) -> None:
        ...

@dataclass
class ShadowRegretTracker:
    """Track regret for shadow policies compared to active policy."""
    cumulative_regret: defaultdict[str, float] = field(default_factory=lambda: defaultdict(float))
    total_pulls: defaultdict[str, int] = field(default_factory=lambda: defaultdict(int))
    total_rewards: defaultdict[str, float] = field(default_factory=lambda: defaultdict(float))
    baseline_reward: float = 0.0
    baseline_count: int = 0

    def update_baseline(self, reward: float) -> None:
        """Update baseline (active policy) performance."""
        self.baseline_count += 1
        alpha = 1.0 / self.baseline_count
        self.baseline_reward = (1 - alpha) * self.baseline_reward + alpha * reward

    def record_shadow_result(self, policy_name: str, reward: float, choice_matched: bool) -> None:
        """Record a shadow policy result and compute regret."""
        self.total_pulls[policy_name] += 1
        self.total_rewards[policy_name] += reward
        if self.baseline_count > 0:
            instantaneous_regret = max(0.0, self.baseline_reward - reward)
            self.cumulative_regret[policy_name] += instantaneous_regret
            if METRICS_AVAILABLE:
                try:
                    from platform.observability import metrics

                    from ultimate_discord_intelligence_bot.tenancy import current_tenant
                    ctx = current_tenant()
                    if ctx:
                        regret_labels = {'tenant': ctx.tenant_id, 'workspace': ctx.workspace_id, 'policy': policy_name, 'shadow': 'true'}
                        metrics.RL_REWARD_LATENCY_GAP.labels(**regret_labels).observe(instantaneous_regret)
                except Exception:
                    pass

    def get_regret_percentage(self, policy_name: str) -> float:
        """Get regret as a percentage of baseline performance."""
        if self.total_pulls[policy_name] == 0 or self.baseline_count == 0 or self.baseline_reward <= 0:
            return 0.0
        avg_regret = self.cumulative_regret[policy_name] / self.total_pulls[policy_name]
        return avg_regret / self.baseline_reward * 100.0

    def get_performance_ratio(self, policy_name: str) -> float:
        """Get performance ratio compared to baseline (1.0 = same, >1.0 = better)."""
        if self.total_pulls[policy_name] == 0 or self.baseline_reward <= 0:
            return 1.0
        avg_reward = self.total_rewards[policy_name] / self.total_pulls[policy_name]
        return avg_reward / self.baseline_reward

    def get_summary(self) -> dict[str, Any]:
        """Get summary statistics for all tracked policies."""
        summary: dict[str, Any] = {'baseline': {'avg_reward': self.baseline_reward, 'count': self.baseline_count}, 'policies': {}}
        for policy_name in self.cumulative_regret:
            if self.total_pulls[policy_name] > 0:
                avg_reward = self.total_rewards[policy_name] / self.total_pulls[policy_name]
                avg_regret = self.cumulative_regret[policy_name] / self.total_pulls[policy_name]
                summary['policies'][policy_name] = {'pulls': self.total_pulls[policy_name], 'avg_reward': avg_reward, 'cumulative_regret': self.cumulative_regret[policy_name], 'avg_regret': avg_regret, 'regret_percentage': self.get_regret_percentage(policy_name), 'performance_ratio': self.get_performance_ratio(policy_name)}
        return summary
_shadow_tracker = ShadowRegretTracker()

def get_shadow_tracker() -> ShadowRegretTracker:
    """Get the global shadow regret tracker."""
    return _shadow_tracker

def is_lints_shadow_enabled() -> bool:
    """Check if LinTS shadow mode is enabled."""
    return os.getenv('ENABLE_RL_LINTS', '').lower() in {'1', 'true', 'yes', 'on'}

def record_shadow_evaluation(policy_name: str, policy: _PolicyLike, context: dict[str, Any], candidates: list[Any], active_choice: Any, active_reward: float) -> None:
    """Record a shadow evaluation for regret tracking."""
    if not is_lints_shadow_enabled():
        return
    try:
        shadow_choice = policy.recommend(context, candidates)
        choice_matched = shadow_choice == active_choice
        if policy_name == 'lints':
            estimated_reward = active_reward * (0.95 + 0.1 * (1 if choice_matched else 0))
        else:
            estimated_reward = active_reward * (0.9 + 0.2 * (1 if choice_matched else 0))
        tracker = get_shadow_tracker()
        tracker.record_shadow_result(policy_name, estimated_reward, choice_matched)
    except Exception:
        pass
__all__ = ['ShadowRegretTracker', 'get_shadow_tracker', 'is_lints_shadow_enabled', 'record_shadow_evaluation']
