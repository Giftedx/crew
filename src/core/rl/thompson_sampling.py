"""
Thompson Sampling bandit algorithm implementation for intelligent model selection.

This module provides Thompson Sampling bandit algorithms for multi-armed bandit
problems in model routing and selection, optimizing for cost-quality trade-offs.
"""

from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class BanditStrategy(Enum):
    """Bandit strategies for different scenarios."""

    THOMPSON_SAMPLING = "thompson_sampling"
    UCB = "upper_confidence_bound"
    EPSILON_GREEDY = "epsilon_greedy"
    SOFTMAX = "softmax"


class RewardType(Enum):
    """Types of rewards for bandit algorithms."""

    QUALITY_SCORE = "quality_score"  # Model output quality
    COST_EFFICIENCY = "cost_efficiency"  # Cost per token
    RESPONSE_TIME = "response_time"  # Latency
    SUCCESS_RATE = "success_rate"  # Task completion rate
    COMBINED = "combined"  # Weighted combination


@dataclass
class ThompsonSamplingConfig:
    """Configuration for Thompson Sampling bandit algorithm."""

    # Algorithm parameters
    alpha_prior: float = 1.0  # Prior alpha parameter (successes)
    beta_prior: float = 1.0  # Prior beta parameter (failures)
    exploration_factor: float = 1.0  # Exploration vs exploitation balance

    # Reward normalization
    reward_normalization: bool = True
    reward_clipping: bool = True
    reward_clip_min: float = 0.0
    reward_clip_max: float = 1.0

    # Learning parameters
    learning_rate: float = 0.1
    decay_factor: float = 0.99
    min_samples_for_confidence: int = 10

    # Multi-objective optimization
    reward_weights: dict[RewardType, float] = field(
        default_factory=lambda: {
            RewardType.QUALITY_SCORE: 0.4,
            RewardType.COST_EFFICIENCY: 0.3,
            RewardType.RESPONSE_TIME: 0.2,
            RewardType.SUCCESS_RATE: 0.1,
        }
    )

    # Performance tracking
    enable_metrics: bool = True
    log_selections: bool = False
    warmup_period: int = 100  # Samples before confidence calculations


@dataclass
class BanditArm:
    """Represents an arm in the multi-armed bandit problem."""

    arm_id: str
    name: str
    metadata: dict[str, Any] = field(default_factory=dict)

    # Thompson Sampling parameters
    alpha: float = 1.0  # Success count + prior
    beta: float = 1.0  # Failure count + prior

    # Performance tracking
    total_pulls: int = 0
    total_reward: float = 0.0
    average_reward: float = 0.0

    # Multi-objective rewards
    rewards: dict[RewardType, list[float]] = field(
        default_factory=lambda: {reward_type: [] for reward_type in RewardType}
    )

    # Confidence metrics
    confidence_interval: tuple[float, float] = (0.0, 1.0)
    last_updated: float = 0.0

    def __post_init__(self):
        if self.last_updated == 0.0:
            self.last_updated = time.time()

    @property
    def expected_reward(self) -> float:
        """Calculate expected reward using Beta distribution mean."""
        if self.alpha + self.beta == 0:
            return 0.5  # Default value
        return self.alpha / (self.alpha + self.beta)

    @property
    def variance(self) -> float:
        """Calculate variance of the Beta distribution."""
        total = self.alpha + self.beta
        if total <= 1:
            return 0.25  # Maximum variance for Beta(1, 1)
        return (self.alpha * self.beta) / ((total**2) * (total + 1))

    @property
    def confidence_width(self) -> float:
        """Calculate confidence interval width."""
        return self.confidence_interval[1] - self.confidence_interval[0]

    def update_reward(self, reward: float, reward_type: RewardType = RewardType.QUALITY_SCORE) -> None:
        """Update arm with new reward."""
        self.total_pulls += 1
        self.total_reward += reward
        self.average_reward = self.total_reward / self.total_pulls

        # Update Beta distribution parameters
        if reward > 0.5:  # Threshold for success/failure
            self.alpha += 1
        else:
            self.beta += 1

        # Store reward by type
        self.rewards[reward_type].append(reward)
        if len(self.rewards[reward_type]) > 1000:  # Limit history
            self.rewards[reward_type] = self.rewards[reward_type][-500:]

        self.last_updated = time.time()

        # Update confidence interval
        self._update_confidence_interval()

    def _update_confidence_interval(self) -> None:
        """Update confidence interval for the arm."""
        if self.total_pulls < 10:
            self.confidence_interval = (0.0, 1.0)
            return

        # Use Beta distribution percentiles for confidence interval
        try:
            from scipy.stats import beta

            lower = beta.ppf(0.025, self.alpha, self.beta)
            upper = beta.ppf(0.975, self.alpha, self.beta)
            self.confidence_interval = (lower, upper)
        except ImportError:
            # Fallback to normal approximation
            mean = self.expected_reward
            std = math.sqrt(self.variance)
            margin = 1.96 * std  # 95% confidence
            self.confidence_interval = (max(0, mean - margin), min(1, mean + margin))

    def sample_reward(self) -> float:
        """Sample a reward from the Beta distribution."""
        try:
            from scipy.stats import beta

            return float(beta.rvs(self.alpha, self.beta))
        except ImportError:
            # Fallback to numpy Beta distribution
            return float(np.random.beta(self.alpha, self.beta))


@dataclass
class ThompsonSamplingMetrics:
    """Metrics for Thompson Sampling algorithm performance."""

    # Selection statistics
    total_selections: int = 0
    selections_by_arm: dict[str, int] = field(default_factory=dict)

    # Performance metrics
    total_reward: float = 0.0
    average_reward: float = 0.0
    cumulative_regret: float = 0.0

    # Exploration metrics
    exploration_rate: float = 0.0
    confidence_evolution: dict[str, list[float]] = field(default_factory=dict)

    # Multi-objective metrics
    reward_by_type: dict[RewardType, float] = field(default_factory=dict)

    # Time tracking
    selection_times: list[float] = field(default_factory=list)
    last_updated: float = 0.0

    def __post_init__(self):
        if self.last_updated == 0.0:
            self.last_updated = time.time()

    @property
    def best_arm_id(self) -> str | None:
        """Get the arm with highest selection count."""
        if not self.selections_by_arm:
            return None
        return max(self.selections_by_arm, key=self.selections_by_arm.get)


class ThompsonSamplingBandit:
    """
    Thompson Sampling bandit algorithm for intelligent model selection.

    Implements Thompson Sampling with multi-objective optimization for
    model routing and selection based on quality, cost, and performance metrics.
    """

    def __init__(self, config: ThompsonSamplingConfig | None = None):
        """Initialize Thompson Sampling bandit."""
        self.config = config or ThompsonSamplingConfig()
        self.arms: dict[str, BanditArm] = {}
        self.metrics = ThompsonSamplingMetrics()

        # Performance tracking
        self.best_reward_so_far = 0.0
        self.total_regret = 0.0

        logger.info(f"Thompson Sampling bandit initialized with config: {self.config}")

    def add_arm(self, arm_id: str, name: str, metadata: dict[str, Any] | None = None) -> None:
        """Add a new arm to the bandit."""
        if arm_id in self.arms:
            logger.warning(f"Arm {arm_id} already exists, updating metadata")

        self.arms[arm_id] = BanditArm(
            arm_id=arm_id,
            name=name,
            metadata=metadata or {},
            alpha=self.config.alpha_prior,
            beta=self.config.beta_prior,
        )

        # Initialize metrics
        self.metrics.selections_by_arm[arm_id] = 0
        self.metrics.confidence_evolution[arm_id] = []

        logger.info(f"Added arm {arm_id} ({name}) to Thompson Sampling bandit")

    def remove_arm(self, arm_id: str) -> bool:
        """Remove an arm from the bandit."""
        if arm_id not in self.arms:
            return False

        del self.arms[arm_id]
        self.metrics.selections_by_arm.pop(arm_id, None)
        self.metrics.confidence_evolution.pop(arm_id, None)

        logger.info(f"Removed arm {arm_id} from Thompson Sampling bandit")
        return True

    def select_arm(self) -> str | None:
        """Select an arm using Thompson Sampling."""
        if not self.arms:
            logger.warning("No arms available for selection")
            return None

        start_time = time.time()

        # Sample rewards from all arms
        sampled_rewards = {}
        for arm_id, arm in self.arms.items():
            sampled_rewards[arm_id] = arm.sample_reward()

        # Select arm with highest sampled reward
        selected_arm_id = max(sampled_rewards, key=lambda x: float(sampled_rewards[x]))

        # Update metrics
        self.metrics.total_selections += 1
        self.metrics.selections_by_arm[selected_arm_id] = self.metrics.selections_by_arm.get(selected_arm_id, 0) + 1

        # Track selection time
        selection_time = time.time() - start_time
        self.metrics.selection_times.append(selection_time)
        if len(self.metrics.selection_times) > 1000:
            self.metrics.selection_times = self.metrics.selection_times[-500:]

        # Update confidence evolution
        if selected_arm_id in self.arms:
            arm = self.arms[selected_arm_id]
            self.metrics.confidence_evolution[selected_arm_id].append(arm.confidence_width)
            if len(self.metrics.confidence_evolution[selected_arm_id]) > 100:
                self.metrics.confidence_evolution[selected_arm_id] = self.metrics.confidence_evolution[selected_arm_id][
                    -50:
                ]

        if self.config.log_selections:
            logger.info(f"Selected arm {selected_arm_id} (sampled reward: {sampled_rewards[selected_arm_id]:.3f})")

        return selected_arm_id

    def update_reward(self, arm_id: str, reward: float, reward_type: RewardType = RewardType.QUALITY_SCORE) -> bool:
        """Update reward for a selected arm."""
        if arm_id not in self.arms:
            logger.warning(f"Arm {arm_id} not found for reward update")
            return False

        # Normalize reward if enabled
        normalized_reward = self._normalize_reward(reward)

        # Update arm
        self.arms[arm_id].update_reward(normalized_reward, reward_type)

        # Update metrics
        self.metrics.total_reward += normalized_reward
        self.metrics.average_reward = self.metrics.total_reward / self.metrics.total_selections

        # Update multi-objective metrics
        if reward_type not in self.metrics.reward_by_type:
            self.metrics.reward_by_type[reward_type] = 0.0
        self.metrics.reward_by_type[reward_type] += normalized_reward

        # Calculate regret
        if normalized_reward > self.best_reward_so_far:
            self.best_reward_so_far = normalized_reward

        # Update cumulative regret
        best_possible_reward = max(arm.expected_reward for arm in self.arms.values())
        self.total_regret += best_possible_reward - normalized_reward
        self.metrics.cumulative_regret = self.total_regret

        # Update exploration rate
        self._update_exploration_rate()

        self.metrics.last_updated = time.time()

        return True

    def _normalize_reward(self, reward: float) -> float:
        """Normalize reward to [0, 1] range."""
        if not self.config.reward_normalization:
            return reward

        # Clip reward if enabled
        if self.config.reward_clipping:
            reward = max(self.config.reward_clip_min, min(self.config.reward_clip_max, reward))

        # Simple normalization - in production, this would be more sophisticated
        if reward < 0:
            reward = 0.0
        elif reward > 1:
            reward = 1.0

        return reward

    def _update_exploration_rate(self) -> None:
        """Update exploration rate based on current state."""
        if self.metrics.total_selections < self.config.warmup_period:
            self.metrics.exploration_rate = 1.0
            return

        # Calculate exploration rate based on confidence intervals
        total_confidence = sum(arm.confidence_width for arm in self.arms.values())
        avg_confidence = total_confidence / len(self.arms) if self.arms else 0.0

        # Higher confidence width = more exploration needed
        self.metrics.exploration_rate = min(1.0, avg_confidence * 2.0)

    def get_arm_statistics(self, arm_id: str) -> dict[str, Any] | None:
        """Get detailed statistics for a specific arm."""
        if arm_id not in self.arms:
            return None

        arm = self.arms[arm_id]
        return {
            "arm_id": arm.arm_id,
            "name": arm.name,
            "expected_reward": arm.expected_reward,
            "variance": arm.variance,
            "confidence_interval": arm.confidence_interval,
            "confidence_width": arm.confidence_width,
            "total_pulls": arm.total_pulls,
            "average_reward": arm.average_reward,
            "alpha": arm.alpha,
            "beta": arm.beta,
            "selection_count": self.metrics.selections_by_arm.get(arm_id, 0),
            "last_updated": arm.last_updated,
            "metadata": arm.metadata,
        }

    def get_all_arm_statistics(self) -> dict[str, dict[str, Any]]:
        """Get statistics for all arms."""
        return {
            arm_id: self.get_arm_statistics(arm_id)
            for arm_id in self.arms
            if self.get_arm_statistics(arm_id) is not None
        }

    def get_bandit_metrics(self) -> dict[str, Any]:
        """Get overall bandit performance metrics."""
        return {
            "total_arms": len(self.arms),
            "total_selections": self.metrics.total_selections,
            "total_reward": self.metrics.total_reward,
            "average_reward": self.metrics.average_reward,
            "cumulative_regret": self.metrics.cumulative_regret,
            "exploration_rate": self.metrics.exploration_rate,
            "best_arm_id": self.metrics.best_arm_id,
            "selections_by_arm": dict(self.metrics.selections_by_arm),
            "reward_by_type": {rt.value: reward for rt, reward in self.metrics.reward_by_type.items()},
            "average_selection_time": (
                sum(self.metrics.selection_times) / len(self.metrics.selection_times)
                if self.metrics.selection_times
                else 0.0
            ),
            "last_updated": self.metrics.last_updated,
        }

    def reset_arm(self, arm_id: str) -> bool:
        """Reset an arm to initial state."""
        if arm_id not in self.arms:
            return False

        arm = self.arms[arm_id]
        arm.alpha = self.config.alpha_prior
        arm.beta = self.config.beta_prior
        arm.total_pulls = 0
        arm.total_reward = 0.0
        arm.average_reward = 0.0
        arm.rewards = {reward_type: [] for reward_type in RewardType}
        arm.confidence_interval = (0.0, 1.0)
        arm.last_updated = time.time()

        logger.info(f"Reset arm {arm_id} to initial state")
        return True

    def reset_all_arms(self) -> None:
        """Reset all arms to initial state."""
        for arm_id in list(self.arms.keys()):
            self.reset_arm(arm_id)

        # Reset metrics
        self.metrics = ThompsonSamplingMetrics()
        self.best_reward_so_far = 0.0
        self.total_regret = 0.0

        logger.info("Reset all arms and metrics to initial state")

    def get_best_arms(self, n: int = 3) -> list[dict[str, Any]]:
        """Get top N arms by expected reward."""
        arm_stats = [
            {
                "arm_id": arm_id,
                "expected_reward": arm.expected_reward,
                "confidence_width": arm.confidence_width,
                "total_pulls": arm.total_pulls,
            }
            for arm_id, arm in self.arms.items()
        ]

        # Sort by expected reward (descending)
        arm_stats.sort(key=lambda x: float(x["expected_reward"]), reverse=True)

        return arm_stats[:n]

    def should_explore(self) -> bool:
        """Determine if the algorithm should explore more."""
        if self.metrics.total_selections < self.config.warmup_period:
            return True

        # Check if any arm has low confidence
        low_confidence_arms = [
            arm
            for arm in self.arms.values()
            if arm.confidence_width > 0.2 and arm.total_pulls < self.config.min_samples_for_confidence
        ]

        return len(low_confidence_arms) > 0 or self.metrics.exploration_rate > 0.3

    def get_exploration_recommendation(self) -> str | None:
        """Get recommendation for which arm to explore."""
        if not self.should_explore():
            return None

        # Find arm with highest uncertainty (confidence width)
        best_exploration_arm = max(
            self.arms.values(), key=lambda arm: float(arm.confidence_width * (1.0 / max(1, arm.total_pulls)))
        )

        return best_exploration_arm.arm_id
