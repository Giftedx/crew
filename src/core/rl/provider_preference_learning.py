"""
Provider preference learning system for intelligent model routing.

This module implements learning algorithms to identify and adapt to provider
preferences based on performance, cost, and reliability metrics.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class PreferenceMetric(Enum):
    """Metrics used for provider preference learning."""

    RESPONSE_TIME = "response_time"
    COST_EFFICIENCY = "cost_efficiency"
    SUCCESS_RATE = "success_rate"
    QUALITY_SCORE = "quality_score"
    RELIABILITY = "reliability"
    AVAILABILITY = "availability"


class LearningAlgorithm(Enum):
    """Algorithms for preference learning."""

    EXPONENTIAL_SMOOTHING = "exponential_smoothing"
    MOVING_AVERAGE = "moving_average"
    WEIGHTED_REGRESSION = "weighted_regression"
    NEURAL_NETWORK = "neural_network"
    BAYESIAN_UPDATE = "bayesian_update"


@dataclass
class ProviderMetrics:
    """Metrics for a specific provider."""

    provider_id: str
    provider_name: str

    # Performance metrics
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0

    # Timing metrics
    total_response_time: float = 0.0
    average_response_time: float = 0.0
    min_response_time: float = float("inf")
    max_response_time: float = 0.0

    # Cost metrics
    total_cost: float = 0.0
    average_cost: float = 0.0
    cost_per_token: float = 0.0

    # Quality metrics
    total_quality_score: float = 0.0
    average_quality_score: float = 0.0

    # Availability metrics
    uptime_percentage: float = 100.0
    last_successful_request: float = 0.0
    last_failed_request: float = 0.0

    # Preference scores (learned)
    preference_scores: dict[PreferenceMetric, float] = field(
        default_factory=lambda: {metric: 0.5 for metric in PreferenceMetric}
    )

    # Learning history
    learning_history: dict[PreferenceMetric, list[float]] = field(
        default_factory=lambda: {metric: [] for metric in PreferenceMetric}
    )

    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)
    last_updated: float = 0.0

    def __post_init__(self):
        if self.last_updated == 0.0:
            self.last_updated = time.time()

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests

    @property
    def failure_rate(self) -> float:
        """Calculate failure rate."""
        return 1.0 - self.success_rate

    @property
    def reliability_score(self) -> float:
        """Calculate reliability score based on success rate and uptime."""
        return (self.success_rate * 0.7) + (self.uptime_percentage / 100.0 * 0.3)

    @property
    def cost_efficiency_score(self) -> float:
        """Calculate cost efficiency score (higher is better)."""
        if self.average_cost == 0:
            return 1.0

        # Invert cost so higher values are better
        # Normalize to [0, 1] range
        max_expected_cost = 0.01  # $0.01 per request as reference
        efficiency = max_expected_cost / self.average_cost
        return min(1.0, max(0.0, efficiency))

    @property
    def response_time_score(self) -> float:
        """Calculate response time score (higher is better)."""
        if self.average_response_time == 0:
            return 1.0

        # Invert response time so higher values are better
        # Normalize to [0, 1] range
        max_expected_time = 5.0  # 5 seconds as reference
        score = max_expected_time / self.average_response_time
        return min(1.0, max(0.0, score))

    def update_request(
        self, success: bool, response_time: float, cost: float, quality_score: float | None = None
    ) -> None:
        """Update provider metrics with new request data."""
        self.total_requests += 1

        if success:
            self.successful_requests += 1
            self.last_successful_request = time.time()
        else:
            self.failed_requests += 1
            self.last_failed_request = time.time()

        # Update response time metrics
        self.total_response_time += response_time
        self.average_response_time = self.total_response_time / self.total_requests
        self.min_response_time = min(self.min_response_time, response_time)
        self.max_response_time = max(self.max_response_time, response_time)

        # Update cost metrics
        self.total_cost += cost
        self.average_cost = self.total_cost / self.total_requests

        # Update quality metrics
        if quality_score is not None:
            self.total_quality_score += quality_score
            self.average_quality_score = self.total_quality_score / self.total_requests

        self.last_updated = time.time()

    def calculate_preference_scores(self) -> dict[PreferenceMetric, float]:
        """Calculate current preference scores."""
        scores = {
            PreferenceMetric.SUCCESS_RATE: self.success_rate,
            PreferenceMetric.RESPONSE_TIME: self.response_time_score,
            PreferenceMetric.COST_EFFICIENCY: self.cost_efficiency_score,
            PreferenceMetric.QUALITY_SCORE: self.average_quality_score,
            PreferenceMetric.RELIABILITY: self.reliability_score,
            PreferenceMetric.AVAILABILITY: self.uptime_percentage / 100.0,
        }

        # Update stored scores
        self.preference_scores.update(scores)

        return scores


@dataclass
class LearningConfig:
    """Configuration for provider preference learning."""

    # Learning algorithm
    algorithm: LearningAlgorithm = LearningAlgorithm.EXPONENTIAL_SMOOTHING

    # Exponential smoothing parameters
    alpha: float = 0.3  # Smoothing factor
    beta: float = 0.1  # Trend smoothing factor

    # Moving average parameters
    window_size: int = 50

    # Weighted regression parameters
    regression_weights: dict[PreferenceMetric, float] = field(
        default_factory=lambda: {
            PreferenceMetric.SUCCESS_RATE: 0.3,
            PreferenceMetric.RESPONSE_TIME: 0.2,
            PreferenceMetric.COST_EFFICIENCY: 0.25,
            PreferenceMetric.QUALITY_SCORE: 0.15,
            PreferenceMetric.RELIABILITY: 0.1,
        }
    )

    # Learning parameters
    learning_rate: float = 0.01
    decay_factor: float = 0.99
    min_samples_for_learning: int = 10

    # Preference thresholds
    high_preference_threshold: float = 0.8
    low_preference_threshold: float = 0.3

    # Update frequency
    update_frequency_seconds: int = 300  # 5 minutes
    batch_update_size: int = 10

    # Performance tracking
    enable_metrics: bool = True
    log_updates: bool = False


@dataclass
class ProviderPreferenceLearning:
    """Provider preference learning system."""

    config: LearningConfig
    providers: dict[str, ProviderMetrics] = field(default_factory=dict)

    # Learning state
    last_global_update: float = 0.0
    update_count: int = 0

    # Performance tracking
    learning_metrics: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.last_global_update == 0.0:
            self.last_global_update = time.time()

    def add_provider(self, provider_id: str, provider_name: str, metadata: dict[str, Any] | None = None) -> None:
        """Add a new provider to the learning system."""
        if provider_id in self.providers:
            logger.warning(f"Provider {provider_id} already exists, updating metadata")

        self.providers[provider_id] = ProviderMetrics(
            provider_id=provider_id, provider_name=provider_name, metadata=metadata or {}
        )

        logger.info(f"Added provider {provider_id} ({provider_name}) to preference learning")

    def remove_provider(self, provider_id: str) -> bool:
        """Remove a provider from the learning system."""
        if provider_id not in self.providers:
            return False

        del self.providers[provider_id]
        logger.info(f"Removed provider {provider_id} from preference learning")
        return True

    def update_provider_request(
        self, provider_id: str, success: bool, response_time: float, cost: float, quality_score: float | None = None
    ) -> bool:
        """Update provider with new request data."""
        if provider_id not in self.providers:
            logger.warning(f"Provider {provider_id} not found for request update")
            return False

        provider = self.providers[provider_id]
        provider.update_request(success, response_time, cost, quality_score)

        # Trigger learning update if conditions are met
        if self._should_trigger_learning_update():
            self._update_preferences()

        return True

    def _should_trigger_learning_update(self) -> bool:
        """Check if learning update should be triggered."""
        # Time-based update
        if time.time() - self.last_global_update > self.config.update_frequency_seconds:
            return True

        # Count-based update
        if self.update_count >= self.config.batch_update_size:
            return True

        return False

    def _update_preferences(self) -> None:
        """Update provider preferences using configured learning algorithm."""
        if self.config.algorithm == LearningAlgorithm.EXPONENTIAL_SMOOTHING:
            self._update_with_exponential_smoothing()
        elif self.config.algorithm == LearningAlgorithm.MOVING_AVERAGE:
            self._update_with_moving_average()
        elif self.config.algorithm == LearningAlgorithm.WEIGHTED_REGRESSION:
            self._update_with_weighted_regression()
        elif self.config.algorithm == LearningAlgorithm.BAYESIAN_UPDATE:
            self._update_with_bayesian()
        else:
            logger.warning(f"Unknown learning algorithm: {self.config.algorithm}")
            self._update_with_exponential_smoothing()  # Fallback

        self.last_global_update = time.time()
        self.update_count = 0

        if self.config.log_updates:
            logger.info(f"Updated provider preferences using {self.config.algorithm.value}")

    def _update_with_exponential_smoothing(self) -> None:
        """Update preferences using exponential smoothing."""
        for provider in self.providers.values():
            if provider.total_requests < self.config.min_samples_for_learning:
                continue

            # Calculate current scores
            current_scores = provider.calculate_preference_scores()

            # Apply exponential smoothing
            for metric, current_score in current_scores.items():
                old_score = provider.preference_scores[metric]
                new_score = self.config.alpha * current_score + (1 - self.config.alpha) * old_score

                provider.preference_scores[metric] = new_score
                provider.learning_history[metric].append(new_score)

                # Limit history size
                if len(provider.learning_history[metric]) > 1000:
                    provider.learning_history[metric] = provider.learning_history[metric][-500:]

    def _update_with_moving_average(self) -> None:
        """Update preferences using moving average."""
        for provider in self.providers.values():
            if provider.total_requests < self.config.min_samples_for_learning:
                continue

            current_scores = provider.calculate_preference_scores()

            for metric, current_score in current_scores.items():
                history = provider.learning_history[metric]
                history.append(current_score)

                # Keep only recent history
                if len(history) > self.config.window_size:
                    history = history[-self.config.window_size :]
                    provider.learning_history[metric] = history

                # Calculate moving average
                if len(history) >= self.config.min_samples_for_learning:
                    new_score = sum(history) / len(history)
                    provider.preference_scores[metric] = new_score

    def _update_with_weighted_regression(self) -> None:
        """Update preferences using weighted regression."""
        for provider in self.providers.values():
            if provider.total_requests < self.config.min_samples_for_learning:
                continue

            current_scores = provider.calculate_preference_scores()

            for metric, current_score in current_scores.items():
                history = provider.learning_history[metric]
                history.append(current_score)

                if len(history) >= self.config.min_samples_for_learning:
                    # Simple weighted average with decay
                    weights = [self.config.decay_factor ** (len(history) - 1 - i) for i in range(len(history))]

                    weighted_sum = sum(score * weight for score, weight in zip(history, weights))
                    weight_sum = sum(weights)

                    new_score = weighted_sum / weight_sum
                    provider.preference_scores[metric] = new_score

    def _update_with_bayesian(self) -> None:
        """Update preferences using Bayesian inference."""
        for provider in self.providers.values():
            if provider.total_requests < self.config.min_samples_for_learning:
                continue

            current_scores = provider.calculate_preference_scores()

            for metric, current_score in current_scores.items():
                history = provider.learning_history[metric]
                history.append(current_score)

                if len(history) >= self.config.min_samples_for_learning:
                    # Simple Bayesian update assuming Beta distribution
                    # Prior: Beta(1, 1) (uniform)
                    # Likelihood: Binomial with current_score as success rate

                    alpha_prior = 1.0
                    beta_prior = 1.0

                    # Convert score to successes and failures
                    successes = int(current_score * len(history))
                    failures = len(history) - successes

                    # Posterior parameters
                    alpha_posterior = alpha_prior + successes
                    beta_posterior = beta_prior + failures

                    # Posterior mean
                    new_score = alpha_posterior / (alpha_posterior + beta_posterior)
                    provider.preference_scores[metric] = new_score

    def get_provider_ranking(self, metric: PreferenceMetric | None = None) -> list[dict[str, Any]]:
        """Get providers ranked by preference score."""
        rankings = []

        for provider in self.providers.values():
            if metric:
                score = provider.preference_scores.get(metric, 0.0)
            else:
                # Overall score as weighted average
                weights = self.config.regression_weights
                score = sum(provider.preference_scores.get(m, 0.0) * weights.get(m, 0.0) for m in PreferenceMetric)

            rankings.append(
                {
                    "provider_id": provider.provider_id,
                    "provider_name": provider.provider_name,
                    "preference_score": score,
                    "total_requests": provider.total_requests,
                    "success_rate": provider.success_rate,
                    "average_response_time": provider.average_response_time,
                    "average_cost": provider.average_cost,
                    "reliability_score": provider.reliability_score,
                }
            )

        # Sort by preference score (descending)
        rankings.sort(key=lambda x: float(x["preference_score"]), reverse=True)

        return rankings

    def get_preferred_providers(self, n: int = 3) -> list[str]:
        """Get top N preferred provider IDs."""
        rankings = self.get_provider_ranking()
        return [ranking["provider_id"] for ranking in rankings[:n]]

    def get_provider_preferences(self, provider_id: str) -> dict[PreferenceMetric, float] | None:
        """Get preference scores for a specific provider."""
        if provider_id not in self.providers:
            return None

        return dict(self.providers[provider_id].preference_scores)

    def get_learning_metrics(self) -> dict[str, Any]:
        """Get learning system metrics."""
        total_requests = sum(provider.total_requests for provider in self.providers.values())
        total_providers = len(self.providers)

        # Calculate average preference scores
        avg_preferences = {}
        for metric in PreferenceMetric:
            scores = [provider.preference_scores.get(metric, 0.0) for provider in self.providers.values()]
            avg_preferences[metric.value] = sum(scores) / len(scores) if scores else 0.0

        return {
            "total_providers": total_providers,
            "total_requests": total_requests,
            "learning_algorithm": self.config.algorithm.value,
            "last_update": self.last_global_update,
            "update_count": self.update_count,
            "average_preference_scores": avg_preferences,
            "provider_count_by_preference": self._get_provider_count_by_preference(),
        }

    def _get_provider_count_by_preference(self) -> dict[str, int]:
        """Get count of providers by preference level."""
        high_pref = 0
        medium_pref = 0
        low_pref = 0

        for provider in self.providers.values():
            # Calculate overall preference score
            weights = self.config.regression_weights
            overall_score = sum(provider.preference_scores.get(m, 0.0) * weights.get(m, 0.0) for m in PreferenceMetric)

            if overall_score >= self.config.high_preference_threshold:
                high_pref += 1
            elif overall_score <= self.config.low_preference_threshold:
                low_pref += 1
            else:
                medium_pref += 1

        return {
            "high_preference": high_pref,
            "medium_preference": medium_pref,
            "low_preference": low_pref,
        }

    def should_prefer_provider(self, provider_id: str) -> bool:
        """Check if a provider should be preferred."""
        if provider_id not in self.providers:
            return False

        provider = self.providers[provider_id]
        weights = self.config.regression_weights

        overall_score = sum(provider.preference_scores.get(m, 0.0) * weights.get(m, 0.0) for m in PreferenceMetric)

        return overall_score >= self.config.high_preference_threshold

    def get_provider_recommendation(self, exclude_providers: list[str] | None = None) -> str | None:
        """Get recommended provider for next request."""
        if not self.providers:
            return None

        exclude_set = set(exclude_providers or [])
        available_providers = [
            provider for provider in self.providers.values() if provider.provider_id not in exclude_set
        ]

        if not available_providers:
            return None

        # Find provider with highest overall preference score
        best_provider = max(
            available_providers,
            key=lambda p: sum(
                p.preference_scores.get(m, 0.0) * self.config.regression_weights.get(m, 0.0) for m in PreferenceMetric
            ),
        )

        return best_provider.provider_id

    def reset_provider(self, provider_id: str) -> bool:
        """Reset a provider to initial state."""
        if provider_id not in self.providers:
            return False

        provider = self.providers[provider_id]

        # Reset metrics
        provider.total_requests = 0
        provider.successful_requests = 0
        provider.failed_requests = 0
        provider.total_response_time = 0.0
        provider.average_response_time = 0.0
        provider.min_response_time = float("inf")
        provider.max_response_time = 0.0
        provider.total_cost = 0.0
        provider.average_cost = 0.0
        provider.total_quality_score = 0.0
        provider.average_quality_score = 0.0

        # Reset preference scores
        for metric in PreferenceMetric:
            provider.preference_scores[metric] = 0.5
            provider.learning_history[metric] = []

        provider.last_updated = time.time()

        logger.info(f"Reset provider {provider_id} to initial state")
        return True

    def reset_all_providers(self) -> None:
        """Reset all providers to initial state."""
        for provider_id in list(self.providers.keys()):
            self.reset_provider(provider_id)

        self.last_global_update = time.time()
        self.update_count = 0

        logger.info("Reset all providers to initial state")
