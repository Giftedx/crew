"""
Upper Confidence Bound (UCB) bandit algorithm implementation for intelligent model selection.

This module provides UCB bandit algorithms for multi-armed bandit problems in model routing
and selection, optimizing for exploration-exploitation balance.
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


class UCBStrategy(Enum):
    """UCB algorithm variants."""

    UCB1 = "ucb1"  # Standard UCB1
    UCB2 = "ucb2"  # UCB2 with improved bounds
    UCB_NORMAL = "ucb_normal"  # UCB for normal distributions
    DISCOUNTED_UCB = "discounted_ucb"  # UCB with discounting
    BERNSTEIN_UCB = "bernstein_ucb"  # Bernstein-style UCB


class ConfidenceLevel(Enum):
    """Confidence levels for UCB bounds."""

    LOW = 0.68  # 1 standard deviation
    MEDIUM = 0.95  # 2 standard deviations
    HIGH = 0.99  # 3 standard deviations


@dataclass
class UCBConfig:
    """Configuration for UCB bandit algorithm."""

    # Algorithm parameters
    strategy: UCBStrategy = UCBStrategy.UCB1
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM
    exploration_factor: float = 2.0  # sqrt(2) for UCB1

    # UCB2 specific parameters
    alpha: float = 0.5  # UCB2 parameter
    beta: float = 1.0  # UCB2 parameter

    # Discounted UCB parameters
    discount_factor: float = 0.95
    window_size: int = 100

    # Bernstein UCB parameters
    variance_penalty: float = 1.0
    confidence_radius: float = 1.0

    # Reward normalization
    reward_normalization: bool = True
    reward_clipping: bool = True
    reward_clip_min: float = 0.0
    reward_clip_max: float = 1.0

    # Learning parameters
    min_samples_for_confidence: int = 10
    max_samples_per_arm: int = 10000

    # Performance tracking
    enable_metrics: bool = True
    log_selections: bool = False
    warmup_period: int = 100


@dataclass
class UCBArm:
    """Represents an arm in the UCB bandit problem."""

    arm_id: str
    name: str
    metadata: dict[str, Any] = field(default_factory=dict)

    # UCB parameters
    total_pulls: int = 0
    total_reward: float = 0.0
    average_reward: float = 0.0

    # Reward history for variance calculation
    rewards: list[float] = field(default_factory=list)
    reward_variance: float = 0.0

    # UCB bounds
    upper_confidence_bound: float = float("inf")
    lower_confidence_bound: float = 0.0
    confidence_interval: tuple[float, float] = (0.0, 1.0)

    # Time tracking
    last_updated: float = 0.0
    creation_time: float = 0.0

    def __post_init__(self):
        current_time = time.time()
        if self.last_updated == 0.0:
            self.last_updated = current_time
        if self.creation_time == 0.0:
            self.creation_time = current_time

    @property
    def expected_reward(self) -> float:
        """Calculate expected reward."""
        return self.average_reward if self.total_pulls > 0 else 0.5

    @property
    def confidence_width(self) -> float:
        """Calculate confidence interval width."""
        return self.confidence_interval[1] - self.confidence_interval[0]

    @property
    def age(self) -> float:
        """Calculate arm age in seconds."""
        return time.time() - self.creation_time

    def update_reward(self, reward: float) -> None:
        """Update arm with new reward."""
        self.total_pulls += 1
        self.total_reward += reward
        self.average_reward = self.total_reward / self.total_pulls

        # Update reward history
        self.rewards.append(reward)
        if len(self.rewards) > 1000:  # Limit history
            self.rewards = self.rewards[-500:]

        # Update variance
        if len(self.rewards) > 1:
            self.reward_variance = float(np.var(self.rewards))

        self.last_updated = time.time()

    def calculate_ucb_bound(self, total_pulls: int, config: UCBConfig, strategy: UCBStrategy) -> float:
        """Calculate UCB bound based on strategy."""
        if self.total_pulls == 0:
            return float("inf")  # Always pull unpulled arms

        if strategy == UCBStrategy.UCB1:
            return self._calculate_ucb1_bound(total_pulls, config)
        elif strategy == UCBStrategy.UCB2:
            return self._calculate_ucb2_bound(total_pulls, config)
        elif strategy == UCBStrategy.UCB_NORMAL:
            return self._calculate_ucb_normal_bound(total_pulls, config)
        elif strategy == UCBStrategy.DISCOUNTED_UCB:
            return self._calculate_discounted_ucb_bound(total_pulls, config)
        elif strategy == UCBStrategy.BERNSTEIN_UCB:
            return self._calculate_bernstein_ucb_bound(total_pulls, config)
        else:
            return self._calculate_ucb1_bound(total_pulls, config)

    def _calculate_ucb1_bound(self, total_pulls: int, config: UCBConfig) -> float:
        """Calculate UCB1 bound."""
        exploration_bonus = math.sqrt((config.exploration_factor * math.log(total_pulls)) / self.total_pulls)
        return self.expected_reward + exploration_bonus

    def _calculate_ucb2_bound(self, total_pulls: int, config: UCBConfig) -> float:
        """Calculate UCB2 bound."""
        # UCB2 has a more complex bound calculation
        n = self.total_pulls
        alpha = config.alpha
        beta = config.beta

        # Calculate UCB2 specific bound
        bound = self.expected_reward + math.sqrt((alpha * math.log(beta * n)) / n)
        return bound

    def _calculate_ucb_normal_bound(self, total_pulls: int, config: UCBConfig) -> float:
        """Calculate UCB bound for normal distributions."""
        if len(self.rewards) < 2:
            return self.expected_reward

        # Use sample variance for confidence bound
        std_error = math.sqrt(self.reward_variance / self.total_pulls)

        # Z-score based on confidence level
        z_score = self._get_z_score(config.confidence_level)

        return self.expected_reward + (z_score * std_error)

    def _calculate_discounted_ucb_bound(self, total_pulls: int, config: UCBConfig) -> float:
        """Calculate discounted UCB bound."""
        # Apply discounting to older rewards
        discounted_rewards = []
        discount = config.discount_factor

        for i, reward in enumerate(reversed(self.rewards[-config.window_size :])):
            discounted_reward = reward * (discount**i)
            discounted_rewards.append(discounted_reward)

        if not discounted_rewards:
            return self.expected_reward

        discounted_avg = sum(discounted_rewards) / len(discounted_rewards)
        np.var(discounted_rewards) if len(discounted_rewards) > 1 else 0.0

        exploration_bonus = math.sqrt((config.exploration_factor * math.log(total_pulls)) / len(discounted_rewards))

        return discounted_avg + exploration_bonus

    def _calculate_bernstein_ucb_bound(self, total_pulls: int, config: UCBConfig) -> float:
        """Calculate Bernstein-style UCB bound."""
        if len(self.rewards) < 2:
            return self.expected_reward

        # Bernstein bound includes variance penalty
        variance_term = math.sqrt((2 * self.reward_variance * math.log(total_pulls)) / self.total_pulls)

        confidence_term = config.confidence_radius * math.log(total_pulls) / (3 * self.total_pulls)

        return self.expected_reward + variance_term + confidence_term

    def _get_z_score(self, confidence_level: ConfidenceLevel) -> float:
        """Get Z-score for confidence level."""
        z_scores = {
            ConfidenceLevel.LOW: 1.0,
            ConfidenceLevel.MEDIUM: 1.96,
            ConfidenceLevel.HIGH: 2.58,
        }
        return z_scores.get(confidence_level, 1.96)

    def update_confidence_bounds(self, total_pulls: int, config: UCBConfig, strategy: UCBStrategy) -> None:
        """Update confidence bounds for the arm."""
        self.upper_confidence_bound = self.calculate_ucb_bound(total_pulls, config, strategy)

        # Calculate lower bound (symmetric for simplicity)
        if self.total_pulls > 0:
            std_error = math.sqrt(self.reward_variance / self.total_pulls) if self.reward_variance > 0 else 0.1
            z_score = self._get_z_score(config.confidence_level)
            self.lower_confidence_bound = max(0, self.expected_reward - (z_score * std_error))
        else:
            self.lower_confidence_bound = 0.0

        self.confidence_interval = (
            self.lower_confidence_bound,
            self.upper_confidence_bound,
        )


@dataclass
class UCBMetrics:
    """Metrics for UCB algorithm performance."""

    # Selection statistics
    total_selections: int = 0
    selections_by_arm: dict[str, int] = field(default_factory=dict)

    # Performance metrics
    total_reward: float = 0.0
    average_reward: float = 0.0
    cumulative_regret: float = 0.0

    # UCB specific metrics
    exploration_bonus_evolution: dict[str, list[float]] = field(default_factory=dict)
    confidence_bound_evolution: dict[str, list[float]] = field(default_factory=dict)

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


class UCBBandit:
    """
    Upper Confidence Bound (UCB) bandit algorithm for intelligent model selection.

    Implements various UCB strategies for model routing and selection with
    configurable exploration-exploitation balance.
    """

    def __init__(self, config: UCBConfig | None = None):
        """Initialize UCB bandit."""
        self.config = config or UCBConfig()
        self.arms: dict[str, UCBArm] = {}
        self.metrics = UCBMetrics()

        # Performance tracking
        self.best_reward_so_far = 0.0
        self.total_regret = 0.0

        logger.info(f"UCB bandit initialized with strategy {self.config.strategy.value}")

    def add_arm(self, arm_id: str, name: str, metadata: dict[str, Any] | None = None) -> None:
        """Add a new arm to the bandit."""
        if arm_id in self.arms:
            logger.warning(f"Arm {arm_id} already exists, updating metadata")

        self.arms[arm_id] = UCBArm(arm_id=arm_id, name=name, metadata=metadata or {})

        # Initialize metrics
        self.metrics.selections_by_arm[arm_id] = 0
        self.metrics.exploration_bonus_evolution[arm_id] = []
        self.metrics.confidence_bound_evolution[arm_id] = []

        logger.info(f"Added arm {arm_id} ({name}) to UCB bandit")

    def remove_arm(self, arm_id: str) -> bool:
        """Remove an arm from the bandit."""
        if arm_id not in self.arms:
            return False

        del self.arms[arm_id]
        self.metrics.selections_by_arm.pop(arm_id, None)
        self.metrics.exploration_bonus_evolution.pop(arm_id, None)
        self.metrics.confidence_bound_evolution.pop(arm_id, None)

        logger.info(f"Removed arm {arm_id} from UCB bandit")
        return True

    def select_arm(self) -> str | None:
        """Select an arm using UCB algorithm."""
        if not self.arms:
            logger.warning("No arms available for selection")
            return None

        start_time = time.time()

        # Update confidence bounds for all arms
        for arm in self.arms.values():
            arm.update_confidence_bounds(self.metrics.total_selections, self.config, self.config.strategy)

        # Select arm with highest UCB bound
        selected_arm_id = max(
            self.arms.keys(),
            key=lambda arm_id: float(self.arms[arm_id].upper_confidence_bound),
        )

        # Update metrics
        self.metrics.total_selections += 1
        self.metrics.selections_by_arm[selected_arm_id] = self.metrics.selections_by_arm.get(selected_arm_id, 0) + 1

        # Track selection time
        selection_time = time.time() - start_time
        self.metrics.selection_times.append(selection_time)
        if len(self.metrics.selection_times) > 1000:
            self.metrics.selection_times = self.metrics.selection_times[-500:]

        # Update evolution tracking
        selected_arm = self.arms[selected_arm_id]
        exploration_bonus = selected_arm.upper_confidence_bound - selected_arm.expected_reward
        self.metrics.exploration_bonus_evolution[selected_arm_id].append(exploration_bonus)
        self.metrics.confidence_bound_evolution[selected_arm_id].append(selected_arm.upper_confidence_bound)

        # Limit evolution history
        for arm_id in self.metrics.exploration_bonus_evolution:
            if len(self.metrics.exploration_bonus_evolution[arm_id]) > 100:
                self.metrics.exploration_bonus_evolution[arm_id] = self.metrics.exploration_bonus_evolution[arm_id][
                    -50:
                ]
            if len(self.metrics.confidence_bound_evolution[arm_id]) > 100:
                self.metrics.confidence_bound_evolution[arm_id] = self.metrics.confidence_bound_evolution[arm_id][-50:]

        if self.config.log_selections:
            logger.info(
                f"Selected arm {selected_arm_id} "
                f"(UCB bound: {selected_arm.upper_confidence_bound:.3f}, "
                f"expected: {selected_arm.expected_reward:.3f}, "
                f"bonus: {exploration_bonus:.3f})"
            )

        return selected_arm_id

    def update_reward(self, arm_id: str, reward: float) -> bool:
        """Update reward for a selected arm."""
        if arm_id not in self.arms:
            logger.warning(f"Arm {arm_id} not found for reward update")
            return False

        # Normalize reward if enabled
        normalized_reward = self._normalize_reward(reward)

        # Update arm
        self.arms[arm_id].update_reward(normalized_reward)

        # Update metrics
        self.metrics.total_reward += normalized_reward
        self.metrics.average_reward = self.metrics.total_reward / self.metrics.total_selections

        # Calculate regret
        if normalized_reward > self.best_reward_so_far:
            self.best_reward_so_far = normalized_reward

        # Update cumulative regret
        best_possible_reward = max(arm.expected_reward for arm in self.arms.values())
        self.total_regret += best_possible_reward - normalized_reward
        self.metrics.cumulative_regret = self.total_regret

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

    def get_arm_statistics(self, arm_id: str) -> dict[str, Any] | None:
        """Get detailed statistics for a specific arm."""
        if arm_id not in self.arms:
            return None

        arm = self.arms[arm_id]
        return {
            "arm_id": arm.arm_id,
            "name": arm.name,
            "expected_reward": arm.expected_reward,
            "upper_confidence_bound": arm.upper_confidence_bound,
            "lower_confidence_bound": arm.lower_confidence_bound,
            "confidence_interval": arm.confidence_interval,
            "confidence_width": arm.confidence_width,
            "total_pulls": arm.total_pulls,
            "average_reward": arm.average_reward,
            "reward_variance": arm.reward_variance,
            "selection_count": self.metrics.selections_by_arm.get(arm_id, 0),
            "age": arm.age,
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
            "strategy": self.config.strategy.value,
            "total_arms": len(self.arms),
            "total_selections": self.metrics.total_selections,
            "total_reward": self.metrics.total_reward,
            "average_reward": self.metrics.average_reward,
            "cumulative_regret": self.metrics.cumulative_regret,
            "best_arm_id": self.metrics.best_arm_id,
            "selections_by_arm": dict(self.metrics.selections_by_arm),
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
        arm.total_pulls = 0
        arm.total_reward = 0.0
        arm.average_reward = 0.0
        arm.rewards = []
        arm.reward_variance = 0.0
        arm.upper_confidence_bound = float("inf")
        arm.lower_confidence_bound = 0.0
        arm.confidence_interval = (0.0, 1.0)
        arm.last_updated = time.time()

        logger.info(f"Reset arm {arm_id} to initial state")
        return True

    def reset_all_arms(self) -> None:
        """Reset all arms to initial state."""
        for arm_id in list(self.arms.keys()):
            self.reset_arm(arm_id)

        # Reset metrics
        self.metrics = UCBMetrics()
        self.best_reward_so_far = 0.0
        self.total_regret = 0.0

        logger.info("Reset all arms and metrics to initial state")

    def get_best_arms(self, n: int = 3) -> list[dict[str, Any]]:
        """Get top N arms by expected reward."""
        arm_stats = [
            {
                "arm_id": arm_id,
                "expected_reward": arm.expected_reward,
                "upper_confidence_bound": arm.upper_confidence_bound,
                "confidence_width": arm.confidence_width,
                "total_pulls": arm.total_pulls,
            }
            for arm_id, arm in self.arms.items()
        ]

        # Sort by expected reward (descending)
        arm_stats.sort(key=lambda x: float(x["expected_reward"]), reverse=True)

        return arm_stats[:n]

    def get_exploration_analysis(self) -> dict[str, Any]:
        """Get analysis of exploration vs exploitation."""
        if not self.arms:
            return {}

        # Calculate average exploration bonus
        avg_exploration_bonus = 0.0
        total_bonus = 0.0
        bonus_count = 0

        for arm_id, bonuses in self.metrics.exploration_bonus_evolution.items():
            if bonuses:
                total_bonus += sum(bonuses)
                bonus_count += len(bonuses)

        if bonus_count > 0:
            avg_exploration_bonus = total_bonus / bonus_count

        # Find most explored arm
        most_explored_arm = None
        max_exploration = 0.0

        for arm_id, arm in self.arms.items():
            if arm.total_pulls > 0:
                exploration_ratio = (arm.upper_confidence_bound - arm.expected_reward) / arm.expected_reward
                if exploration_ratio > max_exploration:
                    max_exploration = exploration_ratio
                    most_explored_arm = arm_id

        return {
            "average_exploration_bonus": avg_exploration_bonus,
            "most_explored_arm": most_explored_arm,
            "max_exploration_ratio": max_exploration,
            "total_exploration_events": bonus_count,
            "exploration_trend": self._get_exploration_trend(),
        }

    def _get_exploration_trend(self) -> dict[str, list[float]]:
        """Get exploration trend over time."""
        trend = {}
        for arm_id, bonuses in self.metrics.exploration_bonus_evolution.items():
            if len(bonuses) > 10:
                # Calculate moving average
                window_size = min(10, len(bonuses) // 5)
                moving_avg = []
                for i in range(window_size, len(bonuses)):
                    avg = sum(bonuses[i - window_size : i]) / window_size
                    moving_avg.append(avg)
                trend[arm_id] = moving_avg[-20:]  # Last 20 points
        return trend

    def should_explore_more(self) -> bool:
        """Determine if the algorithm should explore more."""
        if self.metrics.total_selections < self.config.warmup_period:
            return True

        # Check if any arm has high confidence width (uncertainty)
        high_uncertainty_arms = [
            arm
            for arm in self.arms.values()
            if arm.confidence_width > 0.3 and arm.total_pulls < self.config.min_samples_for_confidence
        ]

        return len(high_uncertainty_arms) > 0

    def get_exploration_recommendation(self) -> str | None:
        """Get recommendation for which arm to explore."""
        if not self.should_explore_more():
            return None

        # Find arm with highest uncertainty-to-pulls ratio
        best_exploration_arm = max(
            self.arms.values(),
            key=lambda arm: arm.confidence_width / max(1, arm.total_pulls),
        )

        return best_exploration_arm.arm_id
