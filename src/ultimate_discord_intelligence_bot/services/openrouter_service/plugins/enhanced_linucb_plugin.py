"""Enhanced LinUCB plugin with advanced contextual features.

Extracted from deprecated ai/advanced_contextual_bandits.py with improvements:
- Richer context feature extraction (temporal, cost, quality dimensions)
- Improved confidence bound computation
- Better state serialization
"""

import logging
from datetime import datetime
from typing import Any

import numpy as np

from .base_plugin import BanditPlugin


logger = logging.getLogger(__name__)


class EnhancedLinUCBPlugin(BanditPlugin):
    """Enhanced LinUCB with advanced contextual features.

    This plugin implements Upper Confidence Bound (UCB) algorithm with:
    - Multi-dimensional context features (task, temporal, cost, quality)
    - Adaptive exploration parameter (alpha)
    - Proper matrix updates for online learning
    """

    def __init__(self, alpha: float = 1.0, context_dim: int = 10):
        """Initialize Enhanced LinUCB plugin.

        Args:
            alpha: Exploration parameter (higher = more exploration)
            context_dim: Dimension of context feature vector
        """
        self.alpha = alpha
        self.context_dim = context_dim

        # Model parameters: A = inverse covariance, b = reward vector
        self.A: dict[str, np.ndarray] = {}
        self.b: dict[str, np.ndarray] = {}

        # Performance tracking
        self.selection_counts: dict[str, int] = {}
        self.total_selections = 0

        logger.info(f"EnhancedLinUCBPlugin initialized: alpha={alpha}, context_dim={context_dim}")

    def select_action(self, context: dict[str, Any], available_models: list[str]) -> str:
        """Select model using UCB with confidence bounds.

        Args:
            context: Request context dictionary
            available_models: List of available model names

        Returns:
            Selected model name
        """
        if not available_models:
            raise ValueError("No available models to select from")

        context_vec = self._extract_context_features(context)

        ucb_scores = {}
        for model in available_models:
            if model not in self.A:
                self._initialize_model(model)

            # Compute UCB score: predicted reward + confidence bound
            A_inv = np.linalg.inv(self.A[model])
            theta = A_inv @ self.b[model]

            predicted_reward = theta @ context_vec
            confidence_bound = self.alpha * np.sqrt(context_vec @ A_inv @ context_vec)

            ucb_scores[model] = predicted_reward + confidence_bound

        # Select model with highest UCB score
        selected_model = max(ucb_scores, key=ucb_scores.get)

        # Track selection
        self.selection_counts[selected_model] = self.selection_counts.get(selected_model, 0) + 1
        self.total_selections += 1

        logger.debug(f"Selected model: {selected_model}, UCB score: {ucb_scores[selected_model]:.4f}")

        return selected_model

    def update(self, context: dict[str, Any], model: str, reward: float):
        """Update model parameters with observed reward.

        Args:
            context: Request context that was used for selection
            model: Model that was selected
            reward: Observed reward (normalized 0-1, higher is better)
        """
        if model not in self.A:
            self._initialize_model(model)

        context_vec = self._extract_context_features(context)

        # Update inverse covariance matrix and reward vector
        self.A[model] += np.outer(context_vec, context_vec)
        self.b[model] += reward * context_vec

        logger.debug(f"Updated {model} with reward {reward:.4f}")

    def _extract_context_features(self, context: dict[str, Any]) -> np.ndarray:
        """Extract enhanced contextual features.

        Features include:
        - Task complexity (prompt length, token estimates)
        - Temporal features (time of day, day of week)
        - Cost constraints (budget remaining, target cost)
        - Quality requirements (min quality threshold)
        - Previous performance indicators

        Args:
            context: Request context dictionary

        Returns:
            Feature vector of shape (context_dim,)
        """
        features = []

        # Task complexity features
        prompt = context.get("prompt", "")
        features.append(min(len(prompt) / 1000.0, 1.0))  # Normalize to [0,1]
        features.append(min(context.get("max_tokens", 1000) / 4000.0, 1.0))

        # Temporal features (cyclical patterns)
        now = datetime.now()
        features.append(now.hour / 24.0)  # Hour of day
        features.append(now.weekday() / 7.0)  # Day of week

        # Cost constraint features
        features.append(context.get("budget_remaining", 1.0))
        features.append(1.0 - context.get("target_cost_per_token", 0.5))

        # Quality requirement features
        features.append(context.get("min_quality", 0.5))
        features.append(context.get("require_reasoning", 0.0))

        # Task type indicators (one-hot style)
        task_type = context.get("task_type", "general")
        features.append(1.0 if "code" in task_type.lower() else 0.0)
        features.append(1.0 if "creative" in task_type.lower() else 0.0)

        # Pad or truncate to context_dim
        while len(features) < self.context_dim:
            features.append(0.0)

        return np.array(features[: self.context_dim])

    def _initialize_model(self, model: str):
        """Initialize parameters for new model.

        Args:
            model: Model identifier
        """
        self.A[model] = np.eye(self.context_dim)
        self.b[model] = np.zeros(self.context_dim)
        logger.debug(f"Initialized parameters for model: {model}")

    def get_state(self) -> dict[str, Any]:
        """Get current bandit state for serialization.

        Returns:
            Dictionary containing all bandit state
        """
        return {
            "alpha": self.alpha,
            "context_dim": self.context_dim,
            "A": {k: v.tolist() for k, v in self.A.items()},
            "b": {k: v.tolist() for k, v in self.b.items()},
            "selection_counts": self.selection_counts,
            "total_selections": self.total_selections,
        }

    def load_state(self, state: dict[str, Any]):
        """Load bandit state from serialized form.

        Args:
            state: Previously serialized state dictionary
        """
        self.alpha = state.get("alpha", self.alpha)
        self.context_dim = state.get("context_dim", self.context_dim)
        self.A = {k: np.array(v) for k, v in state.get("A", {}).items()}
        self.b = {k: np.array(v) for k, v in state.get("b", {}).items()}
        self.selection_counts = state.get("selection_counts", {})
        self.total_selections = state.get("total_selections", 0)

        logger.info(f"Loaded state with {len(self.A)} models")
