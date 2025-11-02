"""RL-based Cache Optimizer - Intelligent TTL and cache level optimization

This module provides reinforcement learning-based optimization for cache TTL
values and cache level selection to maximize hit rates and minimize costs.
"""

from __future__ import annotations
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from platform.core.step_result import StepResult

logger = logging.getLogger(__name__)


@dataclass
class CacheOptimizationConfig:
    """Configuration for cache optimization"""

    enable_rl_optimization: bool = True
    optimization_interval: int = 300
    learning_rate: float = 0.01
    exploration_rate: float = 0.1
    reward_discount: float = 0.95
    min_ttl: int = 60
    max_ttl: int = 86400
    ttl_buckets: int = 20
    performance_window: int = 3600


@dataclass
class TTLOptimizationResult:
    """Result from TTL optimization"""

    original_ttl: int
    optimized_ttl: int
    confidence: float
    expected_hit_rate_improvement: float
    expected_cost_savings: float
    optimization_method: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CachePattern:
    """Pattern for cache access optimization"""

    key_pattern: str
    access_frequency: float
    average_value_size: int
    hit_rate: float
    miss_penalty: float
    ttl_preference: int
    optimal_cache_level: str


class RLCacheOptimizer:
    """Reinforcement Learning-based cache optimizer"""

    def __init__(self, config: CacheOptimizationConfig | None = None):
        self.config = config or CacheOptimizationConfig()
        self._q_table: dict[str, dict[int, float]] = {}
        self._cache_patterns: dict[str, CachePattern] = {}
        self._performance_history: list[dict[str, Any]] = []
        self._last_optimization: dict[str, datetime] = {}
        self._initialize_q_table()

    def _initialize_q_table(self) -> None:
        """Initialize Q-table for RL-based TTL optimization"""
        try:
            ttl_buckets = self._create_ttl_buckets()
            for pattern in self._get_pattern_types():
                self._q_table[pattern] = {}
                for ttl_bucket in ttl_buckets:
                    self._q_table[pattern][ttl_bucket] = 0.0
            logger.info(f"Q-table initialized with {len(self._q_table)} patterns and {len(ttl_buckets)} TTL buckets")
        except Exception as e:
            logger.error(f"Failed to initialize Q-table: {e}")

    def _create_ttl_buckets(self) -> list[int]:
        """Create TTL buckets for discretization"""
        buckets = []
        min_ttl = self.config.min_ttl
        max_ttl = self.config.max_ttl
        for i in range(self.config.ttl_buckets):
            ratio = i / (self.config.ttl_buckets - 1)
            ttl = int(min_ttl * (max_ttl / min_ttl) ** ratio)
            buckets.append(ttl)
        return buckets

    def _get_pattern_types(self) -> list[str]:
        """Get pattern types for Q-table initialization"""
        return [
            "frequent_small",
            "frequent_large",
            "infrequent_small",
            "infrequent_large",
            "burst_pattern",
            "steady_pattern",
            "declining_pattern",
            "growing_pattern",
        ]

    async def optimize_ttl(
        self,
        key_pattern: str,
        current_ttl: int,
        access_history: list[dict[str, Any]],
        tenant_id: str = "default",
        workspace_id: str = "main",
    ) -> StepResult:
        """Optimize TTL using RL-based approach"""
        try:
            pattern_analysis = self._analyze_access_pattern(access_history)
            pattern_type = self._classify_pattern(pattern_analysis)
            ttl_bucket = self._select_ttl_bucket(pattern_type, current_ttl)
            expected_reward = self._calculate_expected_reward(pattern_type, ttl_bucket, pattern_analysis)
            optimization_result = TTLOptimizationResult(
                original_ttl=current_ttl,
                optimized_ttl=self._bucket_to_ttl(ttl_bucket),
                confidence=min(1.0, abs(expected_reward) * 2),
                expected_hit_rate_improvement=expected_reward * 0.1,
                expected_cost_savings=expected_reward * 0.05,
                optimization_method="rl_epsilon_greedy",
                metadata={
                    "pattern_type": pattern_type,
                    "ttl_bucket": ttl_bucket,
                    "expected_reward": expected_reward,
                    "pattern_analysis": pattern_analysis,
                },
            )
            return StepResult.ok(data=optimization_result)
        except Exception as e:
            logger.error(f"TTL optimization failed: {e}", exc_info=True)
            return StepResult.fail(f"TTL optimization failed: {e!s}")

    async def update_reward(
        self,
        key_pattern: str,
        pattern_type: str,
        ttl_bucket: int,
        actual_reward: float,
        metadata: dict[str, Any] | None = None,
    ) -> StepResult:
        """Update Q-table with actual reward"""
        try:
            current_q = self._q_table.get(pattern_type, {}).get(ttl_bucket, 0.0)
            new_q = current_q + self.config.learning_rate * (
                actual_reward
                + self.config.reward_discount * max(self._q_table.get(pattern_type, {}).values(), default=0.0)
                - current_q
            )
            if pattern_type not in self._q_table:
                self._q_table[pattern_type] = {}
            self._q_table[pattern_type][ttl_bucket] = new_q
            self._record_performance(
                {
                    "timestamp": datetime.now(timezone.utc),
                    "pattern_type": pattern_type,
                    "ttl_bucket": ttl_bucket,
                    "actual_reward": actual_reward,
                    "new_q_value": new_q,
                    "metadata": metadata or {},
                }
            )
            logger.debug(f"Updated Q-value for {pattern_type}[{ttl_bucket}]: {current_q:.4f} -> {new_q:.4f}")
            return StepResult.ok(data={"updated": True, "new_q_value": new_q})
        except Exception as e:
            logger.error(f"Failed to update reward: {e}")
            return StepResult.fail(f"Reward update failed: {e!s}")

    def get_optimization_recommendations(self, tenant_id: str = "default", workspace_id: str = "main") -> StepResult:
        """Get optimization recommendations for cache patterns"""
        try:
            recommendations = []
            for pattern_key, pattern in self._cache_patterns.items():
                pattern_type = self._classify_pattern_from_cache_pattern(pattern)
                if pattern_type in self._q_table:
                    best_ttl_bucket = max(self._q_table[pattern_type].items(), key=lambda x: x[1])[0]
                    best_ttl = self._bucket_to_ttl(best_ttl_bucket)
                    current_q = self._q_table[pattern_type].get(self._ttl_to_bucket(pattern.ttl_preference), 0.0)
                    best_q = self._q_table[pattern_type].get(best_ttl_bucket, 0.0)
                    improvement = best_q - current_q
                    if improvement > 0.1:
                        recommendations.append(
                            {
                                "pattern": pattern_key,
                                "current_ttl": pattern.ttl_preference,
                                "recommended_ttl": best_ttl,
                                "expected_improvement": improvement,
                                "confidence": min(1.0, improvement * 2),
                                "pattern_type": pattern_type,
                            }
                        )
            recommendations.sort(key=lambda x: x["expected_improvement"], reverse=True)
            return StepResult.ok(
                data={
                    "recommendations": recommendations,
                    "total_patterns": len(self._cache_patterns),
                    "optimizable_patterns": len(recommendations),
                    "q_table_size": sum((len(buckets) for buckets in self._q_table.values())),
                }
            )
        except Exception as e:
            logger.error(f"Failed to get optimization recommendations: {e}")
            return StepResult.fail(f"Recommendations retrieval failed: {e!s}")

    def get_optimization_metrics(self) -> dict[str, Any]:
        """Get optimization performance metrics"""
        try:
            if not self._performance_history:
                return {"error": "No performance history available"}
            recent_history = self._performance_history[-100:]
            avg_reward = sum((h["actual_reward"] for h in recent_history)) / len(recent_history)
            avg_q_value = sum((h["new_q_value"] for h in recent_history)) / len(recent_history)
            if len(self._performance_history) >= 50:
                early_rewards = [h["actual_reward"] for h in self._performance_history[:50]]
                recent_rewards = [h["actual_reward"] for h in recent_history]
                learning_progress = sum(recent_rewards) / len(recent_rewards) - sum(early_rewards) / len(early_rewards)
            else:
                learning_progress = 0.0
            return {
                "total_updates": len(self._performance_history),
                "avg_reward": avg_reward,
                "avg_q_value": avg_q_value,
                "learning_progress": learning_progress,
                "q_table_size": sum((len(buckets) for buckets in self._q_table.values())),
                "pattern_types": len(self._q_table),
                "last_update": self._performance_history[-1]["timestamp"].isoformat()
                if self._performance_history
                else None,
            }
        except Exception as e:
            logger.error(f"Failed to get optimization metrics: {e}")
            return {"error": str(e)}

    def _analyze_access_pattern(self, access_history: list[dict[str, Any]]) -> dict[str, Any]:
        """Analyze access pattern from history"""
        if not access_history:
            return {"frequency": 0.0, "burstiness": 0.0, "trend": "stable"}
        total_time = access_history[-1]["timestamp"] - access_history[0]["timestamp"]
        frequency = len(access_history) / max(total_time.total_seconds(), 1.0)
        if len(access_history) > 1:
            intervals = []
            for i in range(1, len(access_history)):
                interval = (access_history[i]["timestamp"] - access_history[i - 1]["timestamp"]).total_seconds()
                intervals.append(interval)
            if intervals:
                mean_interval = sum(intervals) / len(intervals)
                variance = sum(((i - mean_interval) ** 2 for i in intervals)) / len(intervals)
                burstiness = variance**0.5 / max(mean_interval, 1.0)
            else:
                burstiness = 0.0
        else:
            burstiness = 0.0
        if len(access_history) >= 10:
            early_count = len(list(access_history[: len(access_history) // 2]))
            late_count = len(list(access_history[len(access_history) // 2 :]))
            if late_count > early_count * 1.2:
                trend = "growing"
            elif late_count < early_count * 0.8:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "stable"
        return {
            "frequency": frequency,
            "burstiness": burstiness,
            "trend": trend,
            "total_accesses": len(access_history),
            "time_span_hours": total_time.total_seconds() / 3600,
        }

    def _classify_pattern(self, pattern_analysis: dict[str, Any]) -> str:
        """Classify pattern based on analysis"""
        frequency = pattern_analysis["frequency"]
        burstiness = pattern_analysis["burstiness"]
        trend = pattern_analysis["trend"]
        high_freq = frequency > 1 / 60
        high_burst = burstiness > 1.0
        if high_freq and (not high_burst):
            return "frequent_small" if trend == "stable" else "frequent_large"
        elif not high_freq and (not high_burst):
            return "infrequent_small" if trend == "stable" else "infrequent_large"
        elif high_burst:
            return "burst_pattern"
        elif trend == "growing":
            return "growing_pattern"
        elif trend == "declining":
            return "declining_pattern"
        else:
            return "steady_pattern"

    def _classify_pattern_from_cache_pattern(self, pattern: CachePattern) -> str:
        """Classify pattern from CachePattern object"""
        high_freq = pattern.access_frequency > 1 / 60
        large_value = pattern.average_value_size > 1024
        if high_freq and (not large_value):
            return "frequent_small"
        elif high_freq and large_value:
            return "frequent_large"
        elif not high_freq and (not large_value):
            return "infrequent_small"
        else:
            return "infrequent_large"

    def _select_ttl_bucket(self, pattern_type: str, current_ttl: int) -> int:
        """Select TTL bucket using epsilon-greedy policy"""
        import random

        if random.random() < self.config.exploration_rate:
            ttl_buckets = self._create_ttl_buckets()
            return random.choice(ttl_buckets)
        elif self._q_table.get(pattern_type):
            best_bucket = max(self._q_table[pattern_type].items(), key=lambda x: x[1])[0]
            return best_bucket
        else:
            return self._ttl_to_bucket(current_ttl)

    def _calculate_expected_reward(self, pattern_type: str, ttl_bucket: int, pattern_analysis: dict[str, Any]) -> float:
        """Calculate expected reward for TTL bucket"""
        base_reward = self._q_table.get(pattern_type, {}).get(ttl_bucket, 0.0)
        frequency = pattern_analysis["frequency"]
        burstiness = pattern_analysis["burstiness"]
        frequency_bonus = min(0.2, frequency * 0.1)
        burstiness_penalty = min(0.2, burstiness * 0.1)
        expected_reward = base_reward + frequency_bonus - burstiness_penalty
        return expected_reward

    def _ttl_to_bucket(self, ttl: int) -> int:
        """Convert TTL to bucket index"""
        ttl_buckets = self._create_ttl_buckets()
        closest_bucket = min(ttl_buckets, key=lambda x: abs(x - ttl))
        return closest_bucket

    def _bucket_to_ttl(self, bucket: int) -> int:
        """Convert bucket to TTL value"""
        return bucket

    def _record_performance(self, performance_data: dict[str, Any]) -> None:
        """Record performance data for analysis"""
        self._performance_history.append(performance_data)
        if len(self._performance_history) > 1000:
            self._performance_history = self._performance_history[-500:]

    def register_cache_pattern(self, pattern: CachePattern) -> None:
        """Register a cache pattern for optimization"""
        pattern_key = pattern.key_pattern
        self._cache_patterns[pattern_key] = pattern
        logger.debug(f"Registered cache pattern: {pattern_key}")

    def get_cache_patterns(self) -> dict[str, CachePattern]:
        """Get all registered cache patterns"""
        return self._cache_patterns.copy()
