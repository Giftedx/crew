"""
Reinforcement Learning Model Router - Contextual Bandit Optimization

This service implements RL-based model selection using contextual bandits
for optimal model routing based on task characteristics and performance history.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

import numpy as np

from core.time import default_utc_now
from obs import metrics
from ultimate_discord_intelligence_bot.step_result import StepResult


if TYPE_CHECKING:  # pragma: no cover - typing only
    from datetime import datetime


logger = logging.getLogger(__name__)


class ModelProvider(Enum):
    """Model provider enumeration."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    META = "meta"
    OPENROUTER = "openrouter"
    LOCAL = "local"


class TaskComplexity(Enum):
    """Task complexity enumeration."""

    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    CRITICAL = "critical"


@dataclass
class ModelCapability:
    """Model capability definition."""

    model_id: str
    provider: ModelProvider
    max_tokens: int
    cost_per_1k_tokens: float
    average_latency_ms: float
    accuracy_score: float
    reliability_score: float
    capabilities: list[str] = field(default_factory=list)
    specializations: list[str] = field(default_factory=list)
    availability_score: float = 1.0


@dataclass
class RoutingContext:
    """Context for model routing decisions."""

    task_type: str
    complexity: TaskComplexity
    token_estimate: int
    latency_requirement_ms: int | None = None
    cost_budget_usd: float | None = None
    quality_requirement: float = 0.8
    tenant: str = ""
    workspace: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelSelection:
    """Model selection result."""

    model_id: str
    provider: ModelProvider
    confidence: float
    expected_reward: float
    reasoning: str
    fallback_models: list[str] = field(default_factory=list)
    estimated_cost: float = 0.0
    estimated_latency_ms: float = 0.0


@dataclass
class RoutingReward:
    """Reward signal for RL learning."""

    model_id: str
    task_id: str
    reward: float
    latency_ms: float
    cost_usd: float
    quality_score: float
    success: bool
    timestamp: datetime = field(default_factory=default_utc_now)
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class TrajectoryFeedback:
    """Feedback signal derived from full trajectory evaluation."""

    trajectory_id: str
    model_id: str
    accuracy_score: float
    efficiency_score: float
    error_handling_score: float
    overall_score: float
    trajectory_length: int
    success: bool
    reasoning: str
    timestamp: datetime = field(default_factory=default_utc_now)
    metadata: dict[str, Any] = field(default_factory=dict)


class ContextualBandit:
    """Contextual bandit implementation for model routing."""

    def __init__(
        self,
        arms: list[ModelCapability],
        context_dim: int = 10,
        exploration_rate: float = 0.1,
    ):
        """
        Initialize contextual bandit.

        Args:
            arms: Available model arms
            context_dim: Dimension of context features
            exploration_rate: Exploration rate for epsilon-greedy
        """
        self.arms = {arm.model_id: arm for arm in arms}
        self.context_dim = context_dim
        self.exploration_rate = exploration_rate
        self.arm_counts = {arm.model_id: 0 for arm in arms}
        self.arm_rewards = {arm.model_id: [] for arm in arms}

        # Linear model parameters for each arm
        self.arm_parameters = {arm.model_id: np.random.normal(0, 0.1, context_dim) for arm in arms}

        # Context feature history
        self.context_history = []
        self.reward_history = []

    def select_arm(self, context: np.ndarray) -> StepResult:
        """
        Select arm using contextual bandit algorithm.

        Args:
            context: Context feature vector

        Returns:
            Tuple of (selected_arm_id, confidence)
        """
        if len(context) != self.context_dim:
            context = self._normalize_context(context)

        # Calculate expected rewards for each arm
        expected_rewards = {}
        for arm_id, parameters in self.arm_parameters.items():
            expected_reward = np.dot(parameters, context)
            expected_rewards[arm_id] = expected_reward

        # Epsilon-greedy selection
        if np.random.random() < self.exploration_rate:
            # Explore: select random arm
            selected_arm = np.random.choice(list(self.arms.keys()))
            confidence = 0.5  # Low confidence for exploration
        else:
            # Exploit: select arm with highest expected reward
            selected_arm = max(expected_rewards.items(), key=lambda x: x[1])[0]
            confidence = self._calculate_confidence(selected_arm, expected_rewards)

        return selected_arm, confidence

    def update(
        self,
        arm_id: str,
        context: np.ndarray,
        reward: float,
        trajectory_feedback: TrajectoryFeedback | None = None,
    ) -> None:
        """
        Update arm parameters based on observed reward.

        Args:
            arm_id: Selected arm ID
            context: Context feature vector
            reward: Observed reward
        """
        if arm_id not in self.arms:
            return

        # Normalize context
        if len(context) != self.context_dim:
            context = self._normalize_context(context)

        enhanced_reward = reward
        if trajectory_feedback is not None:
            trajectory_quality = (
                0.5 * trajectory_feedback.accuracy_score
                + 0.3 * trajectory_feedback.efficiency_score
                + 0.2 * trajectory_feedback.error_handling_score
            )
            enhanced_reward = 0.6 * reward + 0.4 * trajectory_quality

        # Update arm statistics
        self.arm_counts[arm_id] += 1
        self.arm_rewards[arm_id].append(enhanced_reward)

        # Store history
        self.context_history.append(context.copy())
        self.reward_history.append(enhanced_reward)

        # Update parameters using online gradient descent
        learning_rate = 1.0 / (1.0 + self.arm_counts[arm_id])
        prediction = np.dot(self.arm_parameters[arm_id], context)
        error = enhanced_reward - prediction

        # Gradient update
        self.arm_parameters[arm_id] += learning_rate * error * context

        # Keep only recent history to prevent memory issues
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

    def _calculate_confidence(self, selected_arm: str, expected_rewards: dict[str, float]) -> StepResult:
        """Calculate confidence in the selected arm."""
        if selected_arm not in expected_rewards:
            return 0.5

        selected_reward = expected_rewards[selected_arm]
        max_other_reward = max(reward for arm_id, reward in expected_rewards.items() if arm_id != selected_arm)

        # Confidence based on margin between selected and second-best
        margin = selected_reward - max_other_reward
        confidence = min(0.95, max(0.1, 0.5 + margin * 2))

        return confidence

    def get_arm_statistics(self) -> StepResult:
        """Get statistics for all arms."""
        stats = {}
        for arm_id in self.arms:
            rewards = self.arm_rewards[arm_id]
            stats[arm_id] = {
                "count": self.arm_counts[arm_id],
                "average_reward": np.mean(rewards) if rewards else 0.0,
                "reward_std": np.std(rewards) if rewards else 0.0,
                "total_rewards": len(rewards),
            }
        return stats


class RLModelRouter:
    """Reinforcement learning-based model router."""

    def __init__(self):
        """Initialize the RL model router."""
        self.bandit = None
        self.model_capabilities: dict[str, ModelCapability] = {}
        self.routing_history: list[RoutingReward] = []
        self.performance_metrics = {
            "total_routes": 0,
            "successful_routes": 0,
            "average_latency": 0.0,
            "average_cost": 0.0,
            "average_quality": 0.0,
        }
        self.trajectory_feedback_queue: list[TrajectoryFeedback] = []
        self.max_feedback_queue_size = 10000

        # Initialize with default models
        self._initialize_default_models()

    def _initialize_default_models(self):
        """Initialize with default model capabilities."""
        default_models = [
            ModelCapability(
                model_id="gpt-4",
                provider=ModelProvider.OPENAI,
                max_tokens=8192,
                cost_per_1k_tokens=0.03,
                average_latency_ms=2000,
                accuracy_score=0.95,
                reliability_score=0.98,
                capabilities=["text_generation", "reasoning", "analysis"],
                specializations=["complex_reasoning", "creative_writing"],
            ),
            ModelCapability(
                model_id="gpt-3.5-turbo",
                provider=ModelProvider.OPENAI,
                max_tokens=4096,
                cost_per_1k_tokens=0.002,
                average_latency_ms=1000,
                accuracy_score=0.85,
                reliability_score=0.95,
                capabilities=["text_generation", "summarization"],
                specializations=["fast_generation", "cost_effective"],
            ),
            ModelCapability(
                model_id="claude-3-opus",
                provider=ModelProvider.ANTHROPIC,
                max_tokens=200000,
                cost_per_1k_tokens=0.015,
                average_latency_ms=3000,
                accuracy_score=0.97,
                reliability_score=0.99,
                capabilities=["text_generation", "analysis", "reasoning"],
                specializations=["long_context", "high_accuracy"],
            ),
            ModelCapability(
                model_id="claude-3-sonnet",
                provider=ModelProvider.ANTHROPIC,
                max_tokens=200000,
                cost_per_1k_tokens=0.003,
                average_latency_ms=1500,
                accuracy_score=0.92,
                reliability_score=0.97,
                capabilities=["text_generation", "analysis"],
                specializations=["balanced_performance"],
            ),
        ]

        for model in default_models:
            self.model_capabilities[model.model_id] = model

        # Initialize bandit
        self.bandit = ContextualBandit(list(self.model_capabilities.values()))

    async def route_request(self, context: RoutingContext) -> StepResult:
        """
        Route request to optimal model based on context.

        Args:
            context: Routing context with task requirements

        Returns:
            StepResult with model selection
        """
        try:
            if not self.bandit:
                return StepResult.fail("Bandit not initialized")

            # Convert context to feature vector
            context_features = self._context_to_features(context)

            # Select model using bandit
            selected_model_id, confidence = self.bandit.select_arm(context_features)

            if selected_model_id not in self.model_capabilities:
                return StepResult.fail(f"Selected model {selected_model_id} not found")

            selected_model = self.model_capabilities[selected_model_id]

            # Create model selection
            selection = ModelSelection(
                model_id=selected_model_id,
                provider=selected_model.provider,
                confidence=confidence,
                expected_reward=self._calculate_expected_reward(selected_model, context),
                reasoning=self._generate_routing_reason(selected_model, context),
                fallback_models=self._get_fallback_models(selected_model_id, context),
                estimated_cost=self._estimate_cost(selected_model, context.token_estimate),
                estimated_latency_ms=selected_model.average_latency_ms,
            )

            # Update performance metrics
            self.performance_metrics["total_routes"] += 1

            return StepResult.ok(
                data={
                    "model_selection": selection,
                    "context": context,
                    "routing_metadata": {
                        "bandit_confidence": confidence,
                        "available_models": len(self.model_capabilities),
                        "routing_timestamp": default_utc_now().isoformat(),
                    },
                }
            )

        except Exception as e:
            logger.error(f"Model routing failed: {e!s}")
            return StepResult.fail(f"Model routing failed: {e!s}")

    def process_trajectory_feedback(self, batch_size: int = 10) -> StepResult:
        """Process queued trajectory feedback and update routing policy."""

        if not self.trajectory_feedback_queue:
            metrics.RL_FEEDBACK_QUEUE_DEPTH.labels(**metrics.label_ctx()).set(0)
            return StepResult.skip(reason="No trajectory feedback available")

        if not self.bandit:
            metrics.RL_FEEDBACK_QUEUE_DEPTH.labels(**metrics.label_ctx()).set(len(self.trajectory_feedback_queue))
            metrics.RL_FEEDBACK_FAILED.labels(
                **metrics.label_ctx(),
                reason="bandit_not_initialized",
            ).inc()
            return StepResult.fail("Bandit not initialized")

        processed = 0
        failed = 0
        batch_count = min(batch_size, len(self.trajectory_feedback_queue))
        base_labels = metrics.label_ctx()

        for _ in range(batch_count):
            feedback = self.trajectory_feedback_queue.pop(0)
            routing_entry = self._find_routing_entry(feedback)

            if routing_entry is None:
                failed += 1
                metrics.TRAJECTORY_FEEDBACK_PROCESSED.labels(
                    **metrics.label_ctx(),
                    model_id=feedback.model_id,
                    result="missing_history",
                ).inc()
                metrics.RL_FEEDBACK_PROCESSED.labels(
                    **base_labels,
                    result="missing_history",
                ).inc()
                metrics.RL_FEEDBACK_FAILED.labels(
                    **base_labels,
                    reason="missing_history",
                ).inc()
                continue

            try:
                context_vec = self._extract_context_vector(routing_entry.context)
                self.bandit.update(
                    feedback.model_id,
                    context_vec,
                    routing_entry.reward,
                    trajectory_feedback=feedback,
                )
                processed += 1
                metrics.TRAJECTORY_FEEDBACK_PROCESSED.labels(
                    **metrics.label_ctx(),
                    model_id=feedback.model_id,
                    result="success",
                ).inc()
                metrics.RL_FEEDBACK_PROCESSED.labels(
                    **base_labels,
                    result="success",
                ).inc()
            except Exception as exc:  # pragma: no cover - defensive
                failed += 1
                logger.error("Failed to process trajectory feedback: %s", exc, exc_info=True)
                metrics.TRAJECTORY_FEEDBACK_PROCESSED.labels(
                    **metrics.label_ctx(),
                    model_id=feedback.model_id,
                    result="failure",
                ).inc()
                metrics.RL_FEEDBACK_PROCESSED.labels(
                    **base_labels,
                    result="failure",
                ).inc()
                metrics.RL_FEEDBACK_FAILED.labels(
                    **base_labels,
                    reason="exception",
                ).inc()

        metrics.RL_FEEDBACK_QUEUE_DEPTH.labels(**base_labels).set(len(self.trajectory_feedback_queue))
        return StepResult.ok(
            processed=processed,
            failed=failed,
            remaining_queue_size=len(self.trajectory_feedback_queue),
        )

    def _find_routing_entry(self, feedback: TrajectoryFeedback) -> RoutingReward | None:
        """Locate the most recent routing reward entry matching the feedback."""

        for reward in reversed(self.routing_history):
            if reward.task_id == feedback.trajectory_id and reward.model_id == feedback.model_id:
                return reward
        return None

    def _extract_context_vector(self, context: dict[str, Any] | None) -> np.ndarray:
        """Convert routing context metadata into a fixed-length feature vector."""

        features = np.zeros(10)
        context = context or {}

        complexity_map: dict[str, float] = {
            TaskComplexity.SIMPLE.value: 0.25,
            TaskComplexity.MODERATE.value: 0.5,
            TaskComplexity.COMPLEX.value: 0.75,
            TaskComplexity.CRITICAL.value: 1.0,
        }

        complexity = context.get("complexity")
        if isinstance(complexity, TaskComplexity):
            features[0] = complexity_map[complexity.value]
        elif isinstance(complexity, str):
            features[0] = complexity_map.get(complexity.lower(), 0.5)
        else:
            features[0] = 0.5  # default moderate

        token_estimate = context.get("token_estimate")
        if isinstance(token_estimate, (int, float)) and token_estimate > 0:
            features[1] = float(np.log1p(token_estimate) / np.log1p(100_000))
            features[1] = min(1.0, max(0.0, features[1]))
        else:
            features[1] = 0.0

        quality_requirement = context.get("quality_requirement")
        if isinstance(quality_requirement, (int, float)):
            features[2] = float(max(0.0, min(1.0, quality_requirement)))
        else:
            features[2] = 0.8

        latency_requirement = context.get("latency_requirement_ms")
        if isinstance(latency_requirement, (int, float)) and latency_requirement > 0:
            features[3] = 1.0 - min(1.0, float(latency_requirement) / 10_000.0)
        else:
            features[3] = 0.5

        cost_budget = context.get("cost_budget_usd")
        if isinstance(cost_budget, (int, float)) and cost_budget > 0:
            features[4] = min(1.0, float(cost_budget))
        else:
            features[4] = 0.0

        return features

    async def update_reward(self, model_id: str, task_id: str, reward_data: dict[str, Any]) -> StepResult:
        """
        Update model performance with observed reward.

        Args:
            model_id: Model that was used
            task_id: Task identifier
            reward_data: Reward data including latency, cost, quality, success

        Returns:
            StepResult with update status
        """
        try:
            # Create routing reward
            reward = RoutingReward(
                model_id=model_id,
                task_id=task_id,
                reward=reward_data.get("reward", 0.0),
                latency_ms=reward_data.get("latency_ms", 0.0),
                cost_usd=reward_data.get("cost_usd", 0.0),
                quality_score=reward_data.get("quality_score", 0.0),
                success=reward_data.get("success", False),
                context=reward_data.get("context", {}),
            )

            # Store reward
            self.routing_history.append(reward)

            # Update bandit if we have the original context
            if "context_features" in reward_data:
                context_features = np.array(reward_data["context_features"])
                self.bandit.update(model_id, context_features, reward.reward)

            # Update performance metrics
            self._update_performance_metrics(reward)

            # Update model capabilities based on performance
            self._update_model_capabilities(model_id, reward)

            return StepResult.ok(
                data={
                    "model_id": model_id,
                    "task_id": task_id,
                    "reward": reward.reward,
                    "updated_metrics": self.performance_metrics,
                    "bandit_statistics": self.bandit.get_arm_statistics() if self.bandit else {},
                }
            )

        except Exception as e:
            logger.error(f"Reward update failed: {e!s}")
            return StepResult.fail(f"Reward update failed: {e!s}")

    def get_routing_statistics(self) -> StepResult:
        """
        Get routing statistics and performance metrics.

        Returns:
            StepResult with routing statistics
        """
        try:
            stats = {
                "performance_metrics": self.performance_metrics,
                "model_capabilities": {
                    model_id: {
                        "provider": model.provider.value,
                        "max_tokens": model.max_tokens,
                        "cost_per_1k_tokens": model.cost_per_1k_tokens,
                        "average_latency_ms": model.average_latency_ms,
                        "accuracy_score": model.accuracy_score,
                        "reliability_score": model.reliability_score,
                        "capabilities": model.capabilities,
                        "specializations": model.specializations,
                    }
                    for model_id, model in self.model_capabilities.items()
                },
                "bandit_statistics": self.bandit.get_arm_statistics() if self.bandit else {},
                "routing_history_size": len(self.routing_history),
                "recent_performance": self._get_recent_performance(),
            }

            return StepResult.ok(data=stats)

        except Exception as e:
            logger.error(f"Failed to get routing statistics: {e!s}")
            return StepResult.fail(f"Failed to get routing statistics: {e!s}")

    def _context_to_features(self, context: RoutingContext) -> StepResult:
        """Convert routing context to feature vector."""
        features = np.zeros(10)  # Fixed feature dimension

        # Task type encoding (one-hot)
        task_types = [
            "analysis",
            "generation",
            "summarization",
            "translation",
            "reasoning",
        ]
        if context.task_type in task_types:
            features[task_types.index(context.task_type)] = 1.0

        # Complexity encoding
        complexity_values = {
            TaskComplexity.SIMPLE: 0.25,
            TaskComplexity.MODERATE: 0.5,
            TaskComplexity.COMPLEX: 0.75,
            TaskComplexity.CRITICAL: 1.0,
        }
        features[5] = complexity_values.get(context.complexity, 0.5)

        # Token estimate (normalized)
        features[6] = min(1.0, context.token_estimate / 10000.0)

        # Latency requirement (normalized)
        if context.latency_requirement_ms:
            features[7] = min(1.0, context.latency_requirement_ms / 5000.0)

        # Cost budget (normalized)
        if context.cost_budget_usd:
            features[8] = min(1.0, context.cost_budget_usd / 1.0)

        # Quality requirement
        features[9] = context.quality_requirement

        return features

    def _calculate_expected_reward(self, model: ModelCapability, context: RoutingContext) -> StepResult:
        """Calculate expected reward for a model given context."""
        reward = 0.0

        # Base reward from model capabilities
        reward += model.accuracy_score * 0.4
        reward += model.reliability_score * 0.3

        # Latency penalty
        if context.latency_requirement_ms:
            latency_penalty = max(0, (model.average_latency_ms - context.latency_requirement_ms) / 1000.0)
            reward -= latency_penalty * 0.2

        # Cost penalty
        estimated_cost = self._estimate_cost(model, context.token_estimate)
        if context.cost_budget_usd and estimated_cost > context.cost_budget_usd:
            cost_penalty = (estimated_cost - context.cost_budget_usd) / context.cost_budget_usd
            reward -= cost_penalty * 0.3

        # Quality bonus
        if model.accuracy_score >= context.quality_requirement:
            reward += 0.1

        return max(0.0, min(1.0, reward))

    def _generate_routing_reason(self, model: ModelCapability, context: RoutingContext) -> StepResult:
        """Generate human-readable routing reason."""
        reasons = []

        # Check specializations
        if context.task_type in model.specializations:
            reasons.append(f"specialized for {context.task_type}")

        # Check latency requirements
        if context.latency_requirement_ms and model.average_latency_ms <= context.latency_requirement_ms:
            reasons.append("meets latency requirements")

        # Check cost budget
        estimated_cost = self._estimate_cost(model, context.token_estimate)
        if context.cost_budget_usd and estimated_cost <= context.cost_budget_usd:
            reasons.append("within cost budget")

        # Check quality requirements
        if model.accuracy_score >= context.quality_requirement:
            reasons.append("meets quality requirements")

        # Check complexity match
        if context.complexity == TaskComplexity.CRITICAL and model.accuracy_score >= 0.95:
            reasons.append("high accuracy for critical task")
        elif context.complexity == TaskComplexity.SIMPLE and model.cost_per_1k_tokens <= 0.005:
            reasons.append("cost-effective for simple task")

        return ", ".join(reasons) if reasons else "general suitability"

    def _get_fallback_models(self, primary_model_id: str, context: RoutingContext) -> StepResult:
        """Get fallback models for the primary selection."""

        # Sort models by suitability
        model_scores = []
        for model_id, model in self.model_capabilities.items():
            if model_id != primary_model_id:
                score = self._calculate_expected_reward(model, context)
                model_scores.append((model_id, score))

        # Return top 2 fallback models
        model_scores.sort(key=lambda x: x[1], reverse=True)
        return [model_id for model_id, _ in model_scores[:2]]

    def _estimate_cost(self, model: ModelCapability, token_estimate: int) -> StepResult:
        """Estimate cost for a model and token count."""
        return (token_estimate / 1000.0) * model.cost_per_1k_tokens

    def _update_performance_metrics(self, reward: RoutingReward):
        """Update performance metrics with new reward."""
        self.performance_metrics["total_routes"] += 1

        if reward.success:
            self.performance_metrics["successful_routes"] += 1

        # Update averages using exponential moving average
        alpha = 0.1
        self.performance_metrics["average_latency"] = (1 - alpha) * self.performance_metrics[
            "average_latency"
        ] + alpha * reward.latency_ms
        self.performance_metrics["average_cost"] = (1 - alpha) * self.performance_metrics[
            "average_cost"
        ] + alpha * reward.cost_usd
        self.performance_metrics["average_quality"] = (1 - alpha) * self.performance_metrics[
            "average_quality"
        ] + alpha * reward.quality_score

    def _update_model_capabilities(self, model_id: str, reward: RoutingReward):
        """Update model capabilities based on observed performance."""
        if model_id not in self.model_capabilities:
            return

        model = self.model_capabilities[model_id]

        # Update latency using exponential moving average
        alpha = 0.1
        model.average_latency_ms = (1 - alpha) * model.average_latency_ms + alpha * reward.latency_ms

        # Update accuracy score
        model.accuracy_score = (1 - alpha) * model.accuracy_score + alpha * reward.quality_score

        # Update reliability score
        reliability_update = 1.0 if reward.success else 0.0
        model.reliability_score = (1 - alpha) * model.reliability_score + alpha * reliability_update

    def _get_recent_performance(self) -> StepResult:
        """Get recent performance metrics."""
        if not self.routing_history:
            return {}

        # Get last 100 rewards
        recent_rewards = self.routing_history[-100:]

        return {
            "recent_success_rate": sum(1 for r in recent_rewards if r.success) / len(recent_rewards),
            "recent_average_latency": np.mean([r.latency_ms for r in recent_rewards]),
            "recent_average_cost": np.mean([r.cost_usd for r in recent_rewards]),
            "recent_average_quality": np.mean([r.quality_score for r in recent_rewards]),
            "recent_reward_count": len(recent_rewards),
        }

    def save_state(self, filepath: str) -> StepResult:
        """Save router state to file."""
        try:
            # Convert numpy arrays to lists for JSON serialization
            state = {
                "model_capabilities": self.model_capabilities,
                "routing_history": self.routing_history,
                "performance_metrics": self.performance_metrics,
                "bandit_parameters": {
                    k: v.tolist() if hasattr(v, "tolist") else v
                    for k, v in (self.bandit.arm_parameters if self.bandit else {}).items()
                },
                "bandit_counts": {
                    k: v.tolist() if hasattr(v, "tolist") else v
                    for k, v in (self.bandit.arm_counts if self.bandit else {}).items()
                },
                "bandit_rewards": {
                    k: v.tolist() if hasattr(v, "tolist") else v
                    for k, v in (self.bandit.arm_rewards if self.bandit else {}).items()
                },
            }

            with open(filepath, "w") as f:
                json.dump(state, f, indent=2)  # nosec B301 - using secure JSON serialization

            return StepResult.ok(data={"saved_to": filepath})

        except Exception as e:
            logger.error(f"Failed to save router state: {e!s}")
            return StepResult.fail(f"Failed to save router state: {e!s}")

    def load_state(self, filepath: str) -> StepResult:
        """Load router state from file.

        Security: Uses JSON instead of pickle to prevent arbitrary code execution.
        Note: Legacy pickle files will fail to load - manual migration required.
        """
        try:
            with open(filepath) as f:
                state = json.load(f)  # nosec B301 - replaced pickle with secure JSON

            self.model_capabilities = state.get("model_capabilities", {})
            self.routing_history = state.get("routing_history", [])
            self.performance_metrics = state.get("performance_metrics", self.performance_metrics)

            # Reconstruct bandit
            if self.model_capabilities and state.get("bandit_parameters"):
                self.bandit = ContextualBandit(list(self.model_capabilities.values()))
                self.bandit.arm_parameters = state["bandit_parameters"]
                self.bandit.arm_counts = state["bandit_counts"]
                self.bandit.arm_rewards = state["bandit_rewards"]

            return StepResult.ok(data={"loaded_from": filepath})

        except Exception as e:
            logger.error(f"Failed to load router state: {e!s}")
            return StepResult.fail(f"Failed to load router state: {e!s}")
