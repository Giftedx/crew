"""Base interface for routing bandit plugins."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BanditPlugin(ABC):
    """Base interface for routing bandit plugins.

    Plugins implement different exploration/exploitation strategies
    for model selection in the routing layer.
    """

    @abstractmethod
    def select_action(
        self, context: Dict[str, Any], available_models: List[str]
    ) -> str:
        """Select model based on context and RL policy.

        Args:
            context: Request context with features like prompt length,
                    task type, budget constraints, quality requirements
            available_models: List of model identifiers that can be selected

        Returns:
            Selected model identifier
        """
        pass

    @abstractmethod
    def update(self, context: Dict[str, Any], model: str, reward: float):
        """Update bandit with observed reward.

        Args:
            context: Request context that was used for selection
            model: Model that was selected
            reward: Observed reward (e.g., quality score, cost efficiency)
        """
        pass

    @abstractmethod
    def get_state(self) -> Dict[str, Any]:
        """Get current bandit state for serialization.

        Returns:
            Serializable dictionary of bandit state
        """
        pass

    def load_state(self, state: Dict[str, Any]):
        """Load bandit state from serialized form.

        Args:
            state: Previously serialized state dictionary
        """
        pass
