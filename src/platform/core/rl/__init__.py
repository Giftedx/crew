"""Compatibility package for legacy imports under `platform.core.rl`.

This package provides shims that re-export modules from the new
`platform.rl.core` package hierarchy so that older import paths like
`platform.core.rl.policies.bandit_base` continue to work.
"""


# Placeholder classes for backward compatibility
class CostModel:
    """Placeholder for cost model."""


class CostQualityOptimizer:
    """Placeholder for cost-quality optimizer."""


class LearningAlgorithm:
    """Placeholder for learning algorithm."""


class LearningConfig:
    """Placeholder for learning config."""


class ModelSpecification:
    """Placeholder for model specification."""


class OptimizationAlgorithm:
    """Placeholder for optimization algorithm."""


class OptimizationConfig:
    """Placeholder for optimization config."""


class OptimizationObjective:
    """Placeholder for optimization objective."""


class PreferenceMetric:
    """Placeholder for preference metric."""


class ProviderPreferenceLearning:
    """Placeholder for provider preference learning."""


class RewardType:
    """Placeholder for reward type."""


class ThompsonSamplingBandit:
    """Placeholder for Thompson sampling bandit."""


class ThompsonSamplingConfig:
    """Placeholder for Thompson sampling config."""


class UCBBandit:
    """Placeholder for UCB bandit."""


class UCBConfig:
    """Placeholder for UCB config."""


class UCBStrategy:
    """Placeholder for UCB strategy."""


__all__: list[str] = [
    "CostModel",
    "CostQualityOptimizer",
    "LearningAlgorithm",
    "LearningConfig",
    "ModelSpecification",
    "OptimizationAlgorithm",
    "OptimizationConfig",
    "OptimizationObjective",
    "PreferenceMetric",
    "ProviderPreferenceLearning",
    "RewardType",
    "ThompsonSamplingBandit",
    "ThompsonSamplingConfig",
    "UCBBandit",
    "UCBConfig",
    "UCBStrategy",
]
