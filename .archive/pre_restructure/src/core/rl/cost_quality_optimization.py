"""
Cost-quality trade-off optimization for intelligent model routing.

This module implements optimization algorithms to balance cost and quality
in model selection decisions, considering multiple objectives and constraints.
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


class OptimizationObjective(Enum):
    """Optimization objectives for cost-quality trade-offs."""

    MINIMIZE_COST = "minimize_cost"
    MAXIMIZE_QUALITY = "maximize_quality"
    BALANCED = "balanced"
    COST_CONSTRAINED = "cost_constrained"
    QUALITY_CONSTRAINED = "quality_constrained"
    CUSTOM = "custom"


class OptimizationAlgorithm(Enum):
    """Algorithms for cost-quality optimization."""

    WEIGHTED_SUM = "weighted_sum"
    PARETO_FRONT = "pareto_front"
    CONSTRAINT_SATISFACTION = "constraint_satisfaction"
    GENETIC_ALGORITHM = "genetic_algorithm"
    SIMULATED_ANNEALING = "simulated_annealing"
    MULTI_OBJECTIVE_OPTIMIZATION = "multi_objective_optimization"


class CostModel(Enum):
    """Cost models for different pricing structures."""

    PER_TOKEN = "per_token"
    PER_REQUEST = "per_request"
    TIERED = "tiered"
    TIME_BASED = "time_based"
    HYBRID = "hybrid"


@dataclass
class ModelSpecification:
    """Specification for a model including cost and quality characteristics."""

    model_id: str
    provider_id: str
    model_name: str

    # Cost characteristics
    cost_per_token: float = 0.0
    cost_per_request: float = 0.0
    minimum_cost: float = 0.0
    maximum_cost: float = float("inf")
    cost_model: CostModel = CostModel.PER_TOKEN

    # Quality characteristics
    expected_quality_score: float = 0.5
    quality_variance: float = 0.1
    quality_confidence: float = 0.5

    # Performance characteristics
    expected_response_time: float = 1.0
    response_time_variance: float = 0.5
    success_rate: float = 0.95

    # Constraints
    max_tokens: int = 4096
    min_tokens: int = 1
    availability: float = 1.0

    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    def calculate_cost(self, tokens: int, requests: int = 1) -> float:
        """Calculate total cost for given tokens and requests."""
        if self.cost_model == CostModel.PER_TOKEN:
            return max(self.minimum_cost, tokens * self.cost_per_token)
        elif self.cost_model == CostModel.PER_REQUEST:
            return max(self.minimum_cost, requests * self.cost_per_request)
        elif self.cost_model == CostModel.TIERED:
            # Simple tiered model - in production this would be more complex
            if tokens <= 1000:
                return tokens * self.cost_per_token * 0.8
            elif tokens <= 4000:
                return tokens * self.cost_per_token * 0.9
            else:
                return tokens * self.cost_per_token
        elif self.cost_model == CostModel.HYBRID:
            return max(
                self.minimum_cost,
                (tokens * self.cost_per_token) + (requests * self.cost_per_request),
            )
        else:
            return self.minimum_cost

    def calculate_quality_score(self, context: dict[str, Any] | None = None) -> float:
        """Calculate expected quality score with optional context."""
        base_score = self.expected_quality_score

        # Apply context-based adjustments
        if context:
            # Example adjustments based on context
            if context.get("task_complexity", 1.0) > 1.5:
                base_score *= 0.9  # Complex tasks may have lower quality
            if context.get("time_pressure", 0.0) > 0.7:
                base_score *= 0.95  # Time pressure may affect quality

        # Add some variance
        variance = np.random.normal(0, self.quality_variance)
        return max(0.0, min(1.0, base_score + variance))

    def calculate_utility_score(self, cost: float, quality: float, weights: dict[str, float] | None = None) -> float:
        """Calculate utility score combining cost and quality."""
        if weights is None:
            weights = {"cost": 0.3, "quality": 0.7}

        # Normalize cost (lower is better)
        cost_score = 1.0 / (1.0 + cost) if cost > 0 else 1.0

        # Combine scores
        utility = (weights["cost"] * cost_score) + (weights["quality"] * quality)
        return utility


@dataclass
class OptimizationConfig:
    """Configuration for cost-quality optimization."""

    # Optimization objective
    objective: OptimizationObjective = OptimizationObjective.BALANCED
    algorithm: OptimizationAlgorithm = OptimizationAlgorithm.WEIGHTED_SUM

    # Weight configuration
    cost_weight: float = 0.3
    quality_weight: float = 0.7
    custom_weights: dict[str, float] = field(default_factory=dict)

    # Constraints
    max_cost_per_request: float = 1.0
    min_quality_threshold: float = 0.6
    max_response_time: float = 30.0

    # Budget constraints
    daily_budget: float = 100.0
    monthly_budget: float = 3000.0
    cost_threshold_percentage: float = 0.8

    # Optimization parameters
    population_size: int = 50
    max_iterations: int = 100
    convergence_threshold: float = 0.01

    # Genetic algorithm parameters
    mutation_rate: float = 0.1
    crossover_rate: float = 0.8
    elite_percentage: float = 0.1

    # Simulated annealing parameters
    initial_temperature: float = 100.0
    cooling_rate: float = 0.95
    final_temperature: float = 0.1

    # Performance tracking
    enable_metrics: bool = True
    log_optimization: bool = False


@dataclass
class OptimizationResult:
    """Result of cost-quality optimization."""

    selected_model: ModelSpecification | None = None
    optimization_score: float = 0.0

    # Detailed metrics
    predicted_cost: float = 0.0
    predicted_quality: float = 0.0
    predicted_response_time: float = 0.0

    # Optimization metadata
    algorithm_used: OptimizationAlgorithm = OptimizationAlgorithm.WEIGHTED_SUM
    iterations_performed: int = 0
    convergence_achieved: bool = False

    # Alternative solutions
    pareto_front: list[dict[str, Any]] = field(default_factory=list)
    constraint_violations: list[str] = field(default_factory=list)

    # Performance metrics
    optimization_time: float = 0.0
    memory_usage: float = 0.0

    def is_feasible(self) -> bool:
        """Check if the solution is feasible."""
        return len(self.constraint_violations) == 0

    def get_cost_quality_ratio(self) -> float:
        """Get cost-quality efficiency ratio."""
        if self.predicted_cost == 0:
            return float("inf")
        return self.predicted_quality / self.predicted_cost


class CostQualityOptimizer:
    """
    Cost-quality trade-off optimizer for intelligent model routing.

    Implements various optimization algorithms to find the best balance
    between cost and quality in model selection decisions.
    """

    def __init__(self, config: OptimizationConfig | None = None):
        """Initialize cost-quality optimizer."""
        self.config = config or OptimizationConfig()
        self.models: dict[str, ModelSpecification] = {}

        # Optimization history
        self.optimization_history: list[OptimizationResult] = []

        # Performance tracking
        self.total_optimizations: int = 0
        self.successful_optimizations: int = 0

        logger.info(f"Cost-quality optimizer initialized with objective: {self.config.objective.value}")

    def add_model(self, model: ModelSpecification) -> None:
        """Add a model to the optimization set."""
        self.models[model.model_id] = model
        logger.info(f"Added model {model.model_id} to optimizer")

    def remove_model(self, model_id: str) -> bool:
        """Remove a model from the optimization set."""
        if model_id not in self.models:
            return False

        del self.models[model_id]
        logger.info(f"Removed model {model_id} from optimizer")
        return True

    def optimize_model_selection(
        self, tokens: int, requests: int = 1, context: dict[str, Any] | None = None
    ) -> OptimizationResult:
        """Optimize model selection based on cost-quality trade-offs."""
        start_time = time.time()

        if not self.models:
            return OptimizationResult()

        # Filter models based on constraints
        feasible_models = self._filter_feasible_models(tokens, requests, context)

        if not feasible_models:
            return OptimizationResult(constraint_violations=["No feasible models found"])

        # Perform optimization based on algorithm
        result = self._perform_optimization(feasible_models, tokens, requests, context)

        # Update performance tracking
        optimization_time = time.time() - start_time
        result.optimization_time = optimization_time

        self.total_optimizations += 1
        if result.is_feasible():
            self.successful_optimizations += 1

        # Store in history
        self.optimization_history.append(result)
        if len(self.optimization_history) > 1000:
            self.optimization_history = self.optimization_history[-500:]

        if self.config.log_optimization:
            logger.info(
                f"Optimization completed: {result.selected_model.model_id if result.selected_model else 'None'} "
                f"(score: {result.optimization_score:.3f}, time: {optimization_time:.3f}s)"
            )

        return result

    def _filter_feasible_models(
        self, tokens: int, requests: int, context: dict[str, Any] | None
    ) -> list[ModelSpecification]:
        """Filter models based on constraints."""
        feasible_models = []

        for model in self.models.values():
            violations = []

            # Check token constraints
            if tokens < model.min_tokens or tokens > model.max_tokens:
                violations.append(f"Token count {tokens} outside range [{model.min_tokens}, {model.max_tokens}]")

            # Check cost constraints
            estimated_cost = model.calculate_cost(tokens, requests)
            if estimated_cost > self.config.max_cost_per_request:
                violations.append(f"Cost {estimated_cost:.3f} exceeds limit {self.config.max_cost_per_request}")

            # Check quality constraints
            estimated_quality = model.calculate_quality_score(context)
            if estimated_quality < self.config.min_quality_threshold:
                violations.append(
                    f"Quality {estimated_quality:.3f} below threshold {self.config.min_quality_threshold}"
                )

            # Check response time constraints
            if model.expected_response_time > self.config.max_response_time:
                violations.append(
                    f"Response time {model.expected_response_time:.1f}s exceeds limit {self.config.max_response_time}s"
                )

            # Check availability
            if model.availability < 0.9:
                violations.append(f"Availability {model.availability:.2f} below 90%")

            if not violations:
                feasible_models.append(model)

        return feasible_models

    def _perform_optimization(
        self,
        feasible_models: list[ModelSpecification],
        tokens: int,
        requests: int,
        context: dict[str, Any] | None,
    ) -> OptimizationResult:
        """Perform optimization using the configured algorithm."""
        if self.config.algorithm == OptimizationAlgorithm.WEIGHTED_SUM:
            return self._optimize_weighted_sum(feasible_models, tokens, requests, context)
        elif self.config.algorithm == OptimizationAlgorithm.PARETO_FRONT:
            return self._optimize_pareto_front(feasible_models, tokens, requests, context)
        elif self.config.algorithm == OptimizationAlgorithm.CONSTRAINT_SATISFACTION:
            return self._optimize_constraint_satisfaction(feasible_models, tokens, requests, context)
        elif self.config.algorithm == OptimizationAlgorithm.GENETIC_ALGORITHM:
            return self._optimize_genetic_algorithm(feasible_models, tokens, requests, context)
        elif self.config.algorithm == OptimizationAlgorithm.SIMULATED_ANNEALING:
            return self._optimize_simulated_annealing(feasible_models, tokens, requests, context)
        else:
            return self._optimize_weighted_sum(feasible_models, tokens, requests, context)

    def _optimize_weighted_sum(
        self,
        feasible_models: list[ModelSpecification],
        tokens: int,
        requests: int,
        context: dict[str, Any] | None,
    ) -> OptimizationResult:
        """Optimize using weighted sum approach."""
        best_model = None
        best_score = float("-inf")

        for model in feasible_models:
            cost = model.calculate_cost(tokens, requests)
            quality = model.calculate_quality_score(context)

            # Calculate weighted score
            if self.config.objective == OptimizationObjective.MINIMIZE_COST:
                score = -cost  # Negative cost for maximization
            elif self.config.objective == OptimizationObjective.MAXIMIZE_QUALITY:
                score = quality
            elif self.config.objective == OptimizationObjective.BALANCED:
                # Normalize cost and quality to [0, 1]
                normalized_cost = 1.0 / (1.0 + cost) if cost > 0 else 1.0
                score = (self.config.cost_weight * normalized_cost) + (self.config.quality_weight * quality)
            else:
                score = model.calculate_utility_score(cost, quality)

            if score > best_score:
                best_score = score
                best_model = model

        if best_model:
            cost = best_model.calculate_cost(tokens, requests)
            quality = best_model.calculate_quality_score(context)

            return OptimizationResult(
                selected_model=best_model,
                optimization_score=best_score,
                predicted_cost=cost,
                predicted_quality=quality,
                predicted_response_time=best_model.expected_response_time,
                algorithm_used=OptimizationAlgorithm.WEIGHTED_SUM,
                iterations_performed=1,
                convergence_achieved=True,
            )

        return OptimizationResult()

    def _optimize_pareto_front(
        self,
        feasible_models: list[ModelSpecification],
        tokens: int,
        requests: int,
        context: dict[str, Any] | None,
    ) -> OptimizationResult:
        """Optimize using Pareto front approach."""
        # Calculate cost and quality for all models
        model_scores = []
        for model in feasible_models:
            cost = model.calculate_cost(tokens, requests)
            quality = model.calculate_quality_score(context)
            model_scores.append((model, cost, quality))

        # Find Pareto optimal solutions
        pareto_optimal = []
        for i, (model, cost, quality) in enumerate(model_scores):
            is_pareto = True
            for j, (_other_model, other_cost, other_quality) in enumerate(model_scores):
                if (
                    i != j
                    and other_cost <= cost
                    and other_quality >= quality
                    and (other_cost < cost or other_quality > quality)
                ):
                    # Check if other solution dominates this one
                    is_pareto = False
                    break

            if is_pareto:
                pareto_optimal.append((model, cost, quality))

        # Select best from Pareto front based on objective
        if pareto_optimal:
            if self.config.objective == OptimizationObjective.MINIMIZE_COST:
                best_model, cost, quality = min(pareto_optimal, key=lambda x: x[1])
            elif self.config.objective == OptimizationObjective.MAXIMIZE_QUALITY:
                best_model, cost, quality = max(pareto_optimal, key=lambda x: x[2])
            else:
                # Balanced approach - minimize cost/quality ratio
                best_model, cost, quality = min(pareto_optimal, key=lambda x: x[1] / x[2])

            return OptimizationResult(
                selected_model=best_model,
                optimization_score=quality / cost if cost > 0 else float("inf"),
                predicted_cost=cost,
                predicted_quality=quality,
                predicted_response_time=best_model.expected_response_time,
                algorithm_used=OptimizationAlgorithm.PARETO_FRONT,
                iterations_performed=len(pareto_optimal),
                convergence_achieved=True,
                pareto_front=[{"model_id": model.model_id, "cost": c, "quality": q} for model, c, q in pareto_optimal],
            )

        return OptimizationResult()

    def _optimize_constraint_satisfaction(
        self,
        feasible_models: list[ModelSpecification],
        tokens: int,
        requests: int,
        context: dict[str, Any] | None,
    ) -> OptimizationResult:
        """Optimize using constraint satisfaction approach."""
        # All models are already feasible, so find the one that best satisfies constraints
        best_model = None
        best_satisfaction_score = float("-inf")

        for model in feasible_models:
            cost = model.calculate_cost(tokens, requests)
            quality = model.calculate_quality_score(context)

            # Calculate constraint satisfaction score
            cost_satisfaction = max(0, 1.0 - (cost / self.config.max_cost_per_request))
            quality_satisfaction = max(
                0,
                (quality - self.config.min_quality_threshold) / (1.0 - self.config.min_quality_threshold),
            )
            time_satisfaction = max(0, 1.0 - (model.expected_response_time / self.config.max_response_time))

            satisfaction_score = (cost_satisfaction + quality_satisfaction + time_satisfaction) / 3.0

            if satisfaction_score > best_satisfaction_score:
                best_satisfaction_score = satisfaction_score
                best_model = model

        if best_model:
            cost = best_model.calculate_cost(tokens, requests)
            quality = best_model.calculate_quality_score(context)

            return OptimizationResult(
                selected_model=best_model,
                optimization_score=best_satisfaction_score,
                predicted_cost=cost,
                predicted_quality=quality,
                predicted_response_time=best_model.expected_response_time,
                algorithm_used=OptimizationAlgorithm.CONSTRAINT_SATISFACTION,
                iterations_performed=1,
                convergence_achieved=True,
            )

        return OptimizationResult()

    def _optimize_genetic_algorithm(
        self,
        feasible_models: list[ModelSpecification],
        tokens: int,
        requests: int,
        context: dict[str, Any] | None,
    ) -> OptimizationResult:
        """Optimize using genetic algorithm approach."""
        # Simplified genetic algorithm for model selection
        population_size = min(self.config.population_size, len(feasible_models))
        population = feasible_models[:population_size]

        best_model = None
        best_score = float("-inf")

        for _iteration in range(self.config.max_iterations):
            # Evaluate fitness
            fitness_scores = []
            for model in population:
                cost = model.calculate_cost(tokens, requests)
                quality = model.calculate_quality_score(context)

                # Fitness function
                fitness = (self.config.quality_weight * quality) - (self.config.cost_weight * cost)
                fitness_scores.append((model, fitness))

                if fitness > best_score:
                    best_score = fitness
                    best_model = model

            # Check convergence
            if _iteration > 0:
                prev_best_score = best_score
                if abs(best_score - prev_best_score) < self.config.convergence_threshold:
                    break

            # Selection, crossover, mutation (simplified)
            # In a full implementation, this would be more sophisticated
            population = [
                model for model, _ in sorted(fitness_scores, key=lambda x: x[1], reverse=True)[:population_size]
            ]

        if best_model:
            cost = best_model.calculate_cost(tokens, requests)
            quality = best_model.calculate_quality_score(context)

            return OptimizationResult(
                selected_model=best_model,
                optimization_score=best_score,
                predicted_cost=cost,
                predicted_quality=quality,
                predicted_response_time=best_model.expected_response_time,
                algorithm_used=OptimizationAlgorithm.GENETIC_ALGORITHM,
                iterations_performed=_iteration + 1,
                convergence_achieved=True,
            )

        return OptimizationResult()

    def _optimize_simulated_annealing(
        self,
        feasible_models: list[ModelSpecification],
        tokens: int,
        requests: int,
        context: dict[str, Any] | None,
    ) -> OptimizationResult:
        """Optimize using simulated annealing approach."""
        if not feasible_models:
            return OptimizationResult()

        # Start with random model
        current_model = feasible_models[np.random.randint(len(feasible_models))]
        current_cost = current_model.calculate_cost(tokens, requests)
        current_quality = current_model.calculate_quality_score(context)
        current_score = (self.config.quality_weight * current_quality) - (self.config.cost_weight * current_cost)

        best_model = current_model
        best_score = current_score

        temperature = self.config.initial_temperature

        for _iteration in range(self.config.max_iterations):
            # Generate neighbor (random model)
            neighbor = feasible_models[np.random.randint(len(feasible_models))]
            neighbor_cost = neighbor.calculate_cost(tokens, requests)
            neighbor_quality = neighbor.calculate_quality_score(context)
            neighbor_score = (self.config.quality_weight * neighbor_quality) - (self.config.cost_weight * neighbor_cost)

            # Accept or reject neighbor
            if neighbor_score > current_score:
                # Accept better solution
                current_model = neighbor
                current_score = neighbor_score
            else:
                # Accept worse solution with probability
                probability = math.exp((neighbor_score - current_score) / temperature)
                if np.random.random() < probability:
                    current_model = neighbor
                    current_score = neighbor_score

            # Update best solution
            if current_score > best_score:
                best_score = current_score
                best_model = current_model

            # Cool down
            temperature *= self.config.cooling_rate

            # Check convergence
            if temperature < self.config.final_temperature:
                break

        if best_model:
            cost = best_model.calculate_cost(tokens, requests)
            quality = best_model.calculate_quality_score(context)

            return OptimizationResult(
                selected_model=best_model,
                optimization_score=best_score,
                predicted_cost=cost,
                predicted_quality=quality,
                predicted_response_time=best_model.expected_response_time,
                algorithm_used=OptimizationAlgorithm.SIMULATED_ANNEALING,
                iterations_performed=self.config.max_iterations,
                convergence_achieved=True,
            )

        return OptimizationResult()

    def get_optimization_metrics(self) -> dict[str, Any]:
        """Get optimization system metrics."""
        if not self.optimization_history:
            return {}

        recent_results = self.optimization_history[-100:]  # Last 100 optimizations

        success_rate = self.successful_optimizations / max(1, self.total_optimizations)
        avg_optimization_time = sum(r.optimization_time for r in recent_results) / len(recent_results)

        # Cost-quality analysis
        avg_cost = sum(r.predicted_cost for r in recent_results) / len(recent_results)
        avg_quality = sum(r.predicted_quality for r in recent_results) / len(recent_results)

        return {
            "total_optimizations": self.total_optimizations,
            "successful_optimizations": self.successful_optimizations,
            "success_rate": success_rate,
            "average_optimization_time": avg_optimization_time,
            "average_predicted_cost": avg_cost,
            "average_predicted_quality": avg_quality,
            "current_models_count": len(self.models),
            "optimization_objective": self.config.objective.value,
            "optimization_algorithm": self.config.algorithm.value,
        }

    def update_model_performance(
        self,
        model_id: str,
        actual_cost: float,
        actual_quality: float,
        actual_response_time: float,
    ) -> bool:
        """Update model performance based on actual results."""
        if model_id not in self.models:
            return False

        model = self.models[model_id]

        # Update model characteristics based on actual performance
        # This is a simplified update - in production, this would be more sophisticated
        model.expected_quality_score = (model.expected_quality_score + actual_quality) / 2.0
        model.expected_response_time = (model.expected_response_time + actual_response_time) / 2.0

        # Update quality variance based on prediction error
        quality_error = abs(actual_quality - model.expected_quality_score)
        model.quality_variance = (model.quality_variance + quality_error) / 2.0

        logger.info(f"Updated model {model_id} performance based on actual results")
        return True
