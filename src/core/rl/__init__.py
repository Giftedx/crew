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
    # Thompson Sampling
    "ThompsonSamplingBandit",
    "ThompsonSamplingConfig",
    "ThompsonSamplingMetrics",
    "BanditArm",
    "BanditStrategy",
    "RewardType",
    # UCB Bandit
    "UCBBandit",
    "UCBConfig",
    "UCBMetrics",
    "UCBArm",
    "UCBStrategy",
    "ConfidenceLevel",
    # Provider Preference Learning
    "ProviderPreferenceLearning",
    "LearningConfig",
    "ProviderMetrics",
    "LearningAlgorithm",
    "PreferenceMetric",
    # Cost-Quality Optimization
    "CostQualityOptimizer",
    "OptimizationConfig",
    "ModelSpecification",
    "OptimizationResult",
    "OptimizationObjective",
    "OptimizationAlgorithm",
    "CostModel",
]
