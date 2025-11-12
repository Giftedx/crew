"""
Reinforcement Learning Cache Optimizer - Adaptive TTL and Strategy Optimization

This service implements RL-based cache optimization using contextual bandits
for TTL optimization, predictive cache warming, and usage pattern recognition.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import numpy as np

from ultimate_discord_intelligence_bot.step_result import StepResult


logger = logging.getLogger(__name__)


class CacheStrategy(Enum):
    """Cache strategy enumeration."""

    LRU = "lru"
    LFU = "lfu"
    TTL = "ttl"
    ADAPTIVE = "adaptive"
    PREDICTIVE = "predictive"


class AccessPattern(Enum):
    """Access pattern enumeration."""

    RANDOM = "random"
    SEQUENTIAL = "sequential"
    TEMPORAL = "temporal"
    FREQUENCY_BASED = "frequency_based"
    SEASONAL = "seasonal"


@dataclass
class CacheEntry:
    """Cache entry with metadata."""

    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    ttl_seconds: int = 3600
    size_bytes: int = 0
    priority: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CacheContext:
    """Context for cache optimization decisions."""

    key_pattern: str
    access_frequency: float
    data_size: int
    time_since_last_access: float
    time_of_day: int
    day_of_week: int
    tenant: str = ""
    workspace: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CacheAction:
    """Cache action with parameters."""

    action_type: str
    key: str
    ttl_seconds: int = 3600
    priority: float = 1.0
    strategy: CacheStrategy = CacheStrategy.ADAPTIVE
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CacheReward:
    """Reward signal for cache optimization."""

    action: CacheAction
    hit: bool
    latency_ms: float
    cost_savings: float
    quality_impact: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    context: CacheContext = None


class CacheOptimizationBandit:
    """Contextual bandit for cache optimization."""

    def __init__(self, action_space: list[CacheAction], context_dim: int = 12, exploration_rate: float = 0.15):
        """
        Initialize cache optimization bandit.

        Args:
            action_space: Available cache actions
            context_dim: Dimension of context features
            exploration_rate: Exploration rate for epsilon-greedy
        """
        self.action_space = dict(enumerate(action_space))
        self.context_dim = context_dim
        self.exploration_rate = exploration_rate
        self.action_counts = dict.fromkeys(range(len(action_space)), 0)
        self.action_rewards = {i: [] for i in range(len(action_space))}
        self.action_parameters = {i: np.random.normal(0, 0.1, context_dim) for i in range(len(action_space))}
        self.context_history = []
        self.reward_history = []

    def select_action(self, context: np.ndarray) -> StepResult:
        """
        Select cache action using contextual bandit.

        Args:
            context: Context feature vector

        Returns:
            Tuple of (selected_action_index, confidence)
        """
        if len(context) != self.context_dim:
            context = self._normalize_context(context)
        expected_rewards = {}
        for action_idx, parameters in self.action_parameters.items():
            expected_reward = np.dot(parameters, context)
            expected_rewards[action_idx] = expected_reward
        if np.random.random() < self.exploration_rate:
            selected_action = np.random.choice(list(self.action_space.keys()))
            confidence = 0.3
        else:
            selected_action = max(expected_rewards.items(), key=lambda x: x[1])[0]
            confidence = self._calculate_confidence(selected_action, expected_rewards)
        return (selected_action, confidence)

    def update(self, action_idx: int, context: np.ndarray, reward: float):
        """
        Update action parameters based on observed reward.

        Args:
            action_idx: Selected action index
            context: Context feature vector
            reward: Observed reward
        """
        if action_idx not in self.action_space:
            return
        if len(context) != self.context_dim:
            context = self._normalize_context(context)
        self.action_counts[action_idx] += 1
        self.action_rewards[action_idx].append(reward)
        self.context_history.append(context.copy())
        self.reward_history.append(reward)
        learning_rate = 1.0 / (1.0 + self.action_counts[action_idx])
        prediction = np.dot(self.action_parameters[action_idx], context)
        error = reward - prediction
        self.action_parameters[action_idx] += learning_rate * error * context
        if len(self.context_history) > 10000:
            self.context_history = self.context_history[-5000:]
            self.reward_history = self.reward_history[-5000:]

    def _normalize_context(self, context: np.ndarray) -> StepResult:
        """Normalize context to required dimension."""
        if len(context) > self.context_dim:
            return context[: self.context_dim]
        elif len(context) < self.context_dim:
            padded = np.zeros(self.context_dim)
            padded[: len(context)] = context
            return padded
        return context

    def _calculate_confidence(self, selected_action: int, expected_rewards: dict[int, float]) -> StepResult:
        """Calculate confidence in the selected action."""
        if selected_action not in expected_rewards:
            return 0.5
        selected_reward = expected_rewards[selected_action]
        max_other_reward = max(
            (reward for action_idx, reward in expected_rewards.items() if action_idx != selected_action)
        )
        margin = selected_reward - max_other_reward
        confidence = min(0.95, max(0.1, 0.5 + margin * 3))
        return confidence

    def get_action_statistics(self) -> StepResult:
        """Get statistics for all actions."""
        stats = {}
        for action_idx in self.action_space:
            rewards = self.action_rewards[action_idx]
            stats[action_idx] = {
                "action": self.action_space[action_idx],
                "count": self.action_counts[action_idx],
                "average_reward": np.mean(rewards) if rewards else 0.0,
                "reward_std": np.std(rewards) if rewards else 0.0,
                "total_rewards": len(rewards),
            }
        return stats


class RLCacheOptimizer:
    """Reinforcement learning-based cache optimizer."""

    def __init__(self, max_cache_size: int = 10000):
        """
        Initialize the RL cache optimizer.

        Args:
            max_cache_size: Maximum number of cache entries
        """
        self.max_cache_size = max_cache_size
        self.cache: dict[str, CacheEntry] = {}
        self.access_patterns: dict[str, list[datetime]] = {}
        self.bandit = None
        self.optimization_history: list[CacheReward] = []
        self.metrics = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_latency_ms": 0.0,
            "total_cost_savings": 0.0,
            "evictions": 0,
            "predictive_warmings": 0,
        }
        self._initialize_action_space()

    def _initialize_action_space(self):
        """Initialize the action space for the bandit."""
        action_space = []
        for ttl in [300, 600, 1800, 3600, 7200, 14400]:
            action_space.append(CacheAction(action_type="store", key="", ttl_seconds=ttl, strategy=CacheStrategy.TTL))
        for priority in [0.5, 1.0, 1.5, 2.0]:
            action_space.append(
                CacheAction(action_type="store", key="", priority=priority, strategy=CacheStrategy.ADAPTIVE)
            )
        action_space.append(CacheAction(action_type="warm", key="", strategy=CacheStrategy.PREDICTIVE))
        action_space.append(CacheAction(action_type="evict", key="", strategy=CacheStrategy.LRU))
        self.bandit = CacheOptimizationBandit(action_space)

    async def optimize_cache_operation(self, context: CacheContext, operation: str) -> StepResult:
        """
        Optimize cache operation using RL.

        Args:
            context: Cache context
            operation: Cache operation type

        Returns:
            StepResult with optimization recommendations
        """
        try:
            context_features = self._context_to_features(context)
            action_idx, confidence = self.bandit.select_action(context_features)
            selected_action = self.bandit.action_space[action_idx]
            optimized_action = self._customize_action(selected_action, context, operation)
            return StepResult.ok(
                data={
                    "optimized_action": optimized_action,
                    "confidence": confidence,
                    "context": context,
                    "operation": operation,
                    "optimization_metadata": {
                        "action_index": action_idx,
                        "bandit_confidence": confidence,
                        "optimization_timestamp": datetime.utcnow().isoformat(),
                    },
                }
            )
        except Exception as e:
            logger.error(f"Cache optimization failed: {e!s}")
            return StepResult.fail(f"Cache optimization failed: {e!s}")

    async def update_cache_performance(self, action: CacheAction, reward_data: dict[str, Any]) -> StepResult:
        """
        Update cache performance with observed reward.

        Args:
            action: Cache action that was performed
            reward_data: Performance data including hit/miss, latency, etc.

        Returns:
            StepResult with update status
        """
        try:
            reward = CacheReward(
                action=action,
                hit=reward_data.get("hit", False),
                latency_ms=reward_data.get("latency_ms", 0.0),
                cost_savings=reward_data.get("cost_savings", 0.0),
                quality_impact=reward_data.get("quality_impact", 0.0),
                context=reward_data.get("context"),
            )
            composite_reward = self._calculate_composite_reward(reward)
            if reward.context and "context_features" in reward_data:
                context_features = np.array(reward_data["context_features"])
                action_idx = self._find_action_index(action)
                if action_idx is not None:
                    self.bandit.update(action_idx, context_features, composite_reward)
            self.optimization_history.append(reward)
            self._update_metrics(reward)
            return StepResult.ok(
                data={
                    "action": action,
                    "composite_reward": composite_reward,
                    "updated_metrics": self.metrics,
                    "bandit_statistics": self.bandit.get_action_statistics(),
                }
            )
        except Exception as e:
            logger.error(f"Cache performance update failed: {e!s}")
            return StepResult.fail(f"Cache performance update failed: {e!s}")

    async def predict_cache_warming(self, access_patterns: dict[str, list[datetime]]) -> StepResult:
        """
        Predict cache warming opportunities based on access patterns.

        Args:
            access_patterns: Historical access patterns

        Returns:
            StepResult with warming predictions
        """
        try:
            warming_predictions = []
            for key, accesses in access_patterns.items():
                if len(accesses) < 3:
                    continue
                pattern_analysis = self._analyze_access_pattern(accesses)
                predicted_access = self._predict_next_access(accesses, pattern_analysis)
                if predicted_access:
                    warming_predictions.append(
                        {
                            "key": key,
                            "predicted_access_time": predicted_access.isoformat(),
                            "confidence": pattern_analysis.get("confidence", 0.5),
                            "pattern_type": pattern_analysis.get("pattern_type", "unknown"),
                            "recommended_action": self._get_warming_recommendation(pattern_analysis),
                        }
                    )
            warming_predictions.sort(key=lambda x: (x["confidence"], x["predicted_access_time"]), reverse=True)
            return StepResult.ok(
                data={
                    "warming_predictions": warming_predictions[:10],
                    "total_predictions": len(warming_predictions),
                    "prediction_metadata": {
                        "analysis_timestamp": datetime.utcnow().isoformat(),
                        "patterns_analyzed": len(access_patterns),
                    },
                }
            )
        except Exception as e:
            logger.error(f"Cache warming prediction failed: {e!s}")
            return StepResult.fail(f"Cache warming prediction failed: {e!s}")

    def get_cache_statistics(self) -> StepResult:
        """
        Get comprehensive cache statistics and performance metrics.

        Returns:
            StepResult with cache statistics
        """
        try:
            hit_rate = self.metrics["cache_hits"] / max(1, self.metrics["total_requests"])
            average_latency = self.metrics["total_latency_ms"] / max(1, self.metrics["total_requests"])
            stats = {
                "cache_metrics": {
                    "hit_rate": hit_rate,
                    "miss_rate": 1 - hit_rate,
                    "average_latency_ms": average_latency,
                    "total_cost_savings": self.metrics["total_cost_savings"],
                    "cache_size": len(self.cache),
                    "max_cache_size": self.max_cache_size,
                    "utilization": len(self.cache) / self.max_cache_size,
                },
                "performance_metrics": self.metrics,
                "bandit_statistics": self.bandit.get_action_statistics() if self.bandit else {},
                "optimization_history_size": len(self.optimization_history),
                "recent_performance": self._get_recent_performance(),
            }
            return StepResult.ok(data=stats)
        except Exception as e:
            logger.error(f"Failed to get cache statistics: {e!s}")
            return StepResult.fail(f"Failed to get cache statistics: {e!s}")

    def _context_to_features(self, context: CacheContext) -> StepResult:
        """Convert cache context to feature vector."""
        features = np.zeros(12)
        key_hash = int(hashlib.md5(context.key_pattern.encode(), usedforsecurity=False).hexdigest()[:8], 16)
        features[0] = key_hash % 1000 / 1000.0
        features[1] = min(1.0, context.access_frequency / 100.0)
        features[2] = min(1.0, context.data_size / 1000000.0)
        features[3] = min(1.0, context.time_since_last_access / 3600.0)
        features[4] = np.sin(2 * np.pi * context.time_of_day / 24)
        features[5] = np.cos(2 * np.pi * context.time_of_day / 24)
        features[6] = np.sin(2 * np.pi * context.day_of_week / 7)
        features[7] = np.cos(2 * np.pi * context.day_of_week / 7)
        tenant_hash = int(hashlib.md5(context.tenant.encode(), usedforsecurity=False).hexdigest()[:8], 16)
        features[8] = tenant_hash % 100 / 100.0
        workspace_hash = int(hashlib.md5(context.workspace.encode(), usedforsecurity=False).hexdigest()[:8], 16)
        features[9] = workspace_hash % 100 / 100.0
        features[10] = len(context.metadata) / 10.0
        features[11] = 1.0 if context.metadata.get("high_priority", False) else 0.0
        return features

    def _customize_action(self, base_action: CacheAction, context: CacheContext, operation: str) -> StepResult:
        """Customize base action for specific context and operation."""
        customized = CacheAction(
            action_type=operation,
            key=context.key_pattern,
            ttl_seconds=base_action.ttl_seconds,
            priority=base_action.priority,
            strategy=base_action.strategy,
            metadata=base_action.metadata.copy(),
        )
        if context.access_frequency > 10:
            customized.ttl_seconds = min(customized.ttl_seconds * 2, 14400)
        elif context.access_frequency < 1:
            customized.ttl_seconds = max(customized.ttl_seconds // 2, 300)
        if context.data_size > 100000:
            customized.priority *= 1.5
        if context.time_since_last_access < 300:
            customized.priority *= 1.2
        return customized

    def _calculate_composite_reward(self, reward: CacheReward) -> StepResult:
        """Calculate composite reward from multiple factors."""
        composite = 0.0
        if reward.hit:
            composite += 1.0
        else:
            composite -= 0.5
        latency_reward = max(0, 1.0 - reward.latency_ms / 1000.0)
        composite += latency_reward * 0.3
        cost_reward = min(1.0, reward.cost_savings / 0.01)
        composite += cost_reward * 0.4
        composite += reward.quality_impact * 0.3
        return max(-1.0, min(1.0, composite))

    def _find_action_index(self, action: CacheAction) -> StepResult:
        """Find action index in the bandit's action space."""
        for idx, bandit_action in self.bandit.action_space.items():
            if (
                bandit_action.action_type == action.action_type
                and bandit_action.strategy == action.strategy
                and (abs(bandit_action.ttl_seconds - action.ttl_seconds) < 60)
                and (abs(bandit_action.priority - action.priority) < 0.1)
            ):
                return idx
        return None

    def _update_metrics(self, reward: CacheReward):
        """Update performance metrics with new reward."""
        self.metrics["total_requests"] += 1
        if reward.hit:
            self.metrics["cache_hits"] += 1
        else:
            self.metrics["cache_misses"] += 1
        self.metrics["total_latency_ms"] += reward.latency_ms
        self.metrics["total_cost_savings"] += reward.cost_savings
        if reward.action.action_type == "evict":
            self.metrics["evictions"] += 1
        elif reward.action.action_type == "warm":
            self.metrics["predictive_warmings"] += 1

    def _analyze_access_pattern(self, accesses: list[datetime]) -> StepResult:
        """Analyze access pattern to determine type and confidence."""
        if len(accesses) < 3:
            return {"pattern_type": "insufficient_data", "confidence": 0.0}
        intervals = []
        for i in range(1, len(accesses)):
            interval = (accesses[i] - accesses[i - 1]).total_seconds()
            intervals.append(interval)
        avg_interval = np.mean(intervals)
        interval_std = np.std(intervals)
        cv = interval_std / avg_interval if avg_interval > 0 else float("inf")
        if cv < 0.1:
            pattern_type = "regular"
            confidence = 0.9
        elif cv < 0.3:
            pattern_type = "semi_regular"
            confidence = 0.7
        elif avg_interval < 300:
            pattern_type = "frequent"
            confidence = 0.6
        else:
            pattern_type = "sporadic"
            confidence = 0.3
        return {
            "pattern_type": pattern_type,
            "confidence": confidence,
            "average_interval": avg_interval,
            "interval_std": interval_std,
            "coefficient_of_variation": cv,
        }

    def _predict_next_access(self, accesses: list[datetime], pattern_analysis: dict[str, Any]) -> StepResult:
        """Predict next access time based on pattern analysis."""
        if pattern_analysis["confidence"] < 0.5:
            return None
        last_access = accesses[-1]
        avg_interval = pattern_analysis["average_interval"]
        predicted_time = last_access + timedelta(seconds=avg_interval)
        max_prediction = datetime.utcnow() + timedelta(hours=24)
        if predicted_time > max_prediction:
            return None
        return predicted_time

    def _get_warming_recommendation(self, pattern_analysis: dict[str, Any]) -> StepResult:
        """Get cache warming recommendation based on pattern analysis."""
        pattern_type = pattern_analysis["pattern_type"]
        confidence = pattern_analysis["confidence"]
        if pattern_type == "regular" and confidence > 0.8:
            return {
                "action": "preemptive_warming",
                "ttl_seconds": 3600,
                "priority": 2.0,
                "reasoning": "High confidence regular pattern",
            }
        elif pattern_type == "frequent" and confidence > 0.6:
            return {
                "action": "aggressive_caching",
                "ttl_seconds": 1800,
                "priority": 1.5,
                "reasoning": "Frequent access pattern",
            }
        else:
            return {"action": "standard_caching", "ttl_seconds": 600, "priority": 1.0, "reasoning": "Uncertain pattern"}

    def _get_recent_performance(self) -> StepResult:
        """Get recent performance metrics."""
        if not self.optimization_history:
            return {}
        recent_rewards = self.optimization_history[-100:]
        recent_hits = sum(1 for r in recent_rewards if r.hit)
        recent_requests = len(recent_rewards)
        return {
            "recent_hit_rate": recent_hits / recent_requests if recent_requests > 0 else 0.0,
            "recent_average_latency": np.mean([r.latency_ms for r in recent_rewards]),
            "recent_average_cost_savings": np.mean([r.cost_savings for r in recent_rewards]),
            "recent_reward_count": recent_requests,
        }

    def save_state(self, filepath: str) -> StepResult:
        """Save optimizer state to file."""
        try:
            state = {
                "cache": self.cache,
                "access_patterns": self.access_patterns,
                "optimization_history": self.optimization_history,
                "metrics": self.metrics,
                "bandit_parameters": {
                    k: v.tolist() if hasattr(v, "tolist") else v
                    for k, v in (self.bandit.action_parameters if self.bandit else {}).items()
                },
                "bandit_counts": {
                    k: v.tolist() if hasattr(v, "tolist") else v
                    for k, v in (self.bandit.action_counts if self.bandit else {}).items()
                },
                "bandit_rewards": {
                    k: v.tolist() if hasattr(v, "tolist") else v
                    for k, v in (self.bandit.action_rewards if self.bandit else {}).items()
                },
            }
            with open(filepath, "w") as f:
                json.dump(state, f, indent=2)
            return StepResult.ok(data={"saved_to": filepath})
        except Exception as e:
            logger.error(f"Failed to save optimizer state: {e!s}")
            return StepResult.fail(f"Failed to save optimizer state: {e!s}")

    def load_state(self, filepath: str) -> StepResult:
        """Load optimizer state from file.

        Security: Uses JSON instead of pickle to prevent arbitrary code execution.
        Note: Legacy pickle files will fail to load - manual migration required.
        """
        try:
            with open(filepath) as f:
                state = json.load(f)
            self.cache = state.get("cache", {})
            self.access_patterns = state.get("access_patterns", {})
            self.optimization_history = state.get("optimization_history", [])
            self.metrics = state.get("metrics", self.metrics)
            if state.get("bandit_parameters"):
                self._initialize_action_space()
                self.bandit.action_parameters = state["bandit_parameters"]
                self.bandit.action_counts = state["bandit_counts"]
                self.bandit.action_rewards = state["bandit_rewards"]
            return StepResult.ok(data={"loaded_from": filepath})
        except Exception as e:
            logger.error(f"Failed to load optimizer state: {e!s}")
            return StepResult.fail(f"Failed to load optimizer state: {e!s}")
