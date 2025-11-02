"""
Reinforcement Learning and Model Routing Module.

This module provides reinforcement learning algorithms and intelligent model routing
capabilities for the Ultimate Discord Intelligence Bot, including bandit algorithms,
provider preference learning, and cost-quality optimization.
"""

from .cost_quality_optimization import (
    CostModel,
    CostQualityOptimizer,
    ModelSpecification,
    OptimizationAlgorithm,
    OptimizationConfig,
    OptimizationObjective,
    OptimizationResult,
)
from .provider_preference_learning import (
    LearningAlgorithm,
    LearningConfig,
    PreferenceMetric,
    ProviderMetrics,
    ProviderPreferenceLearning,
)
from .thompson_sampling import (
    BanditArm,
    BanditStrategy,
    RewardType,
    ThompsonSamplingBandit,
    ThompsonSamplingConfig,
    ThompsonSamplingMetrics,
)
from .ucb_bandit import (
    ConfidenceLevel,
    UCBArm,
    UCBBandit,
    UCBConfig,
    UCBMetrics,
    UCBStrategy,
)


__all__ = [
    "BanditArm",
    "BanditStrategy",
    "ConfidenceLevel",
    "CostModel",
    # Cost-Quality Optimization
    "CostQualityOptimizer",
    "LearningAlgorithm",
    "LearningConfig",
    "ModelSpecification",
    "OptimizationAlgorithm",
    "OptimizationConfig",
    "OptimizationObjective",
    "OptimizationResult",
    "PreferenceMetric",
    "ProviderMetrics",
    # Provider Preference Learning
    "ProviderPreferenceLearning",
    "RewardType",
    # Thompson Sampling
    "ThompsonSamplingBandit",
    "ThompsonSamplingConfig",
    "ThompsonSamplingMetrics",
    "UCBArm",
    # UCB Bandit
    "UCBBandit",
    "UCBConfig",
    "UCBMetrics",
    "UCBStrategy",
]
