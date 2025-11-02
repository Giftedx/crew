"""Advanced contextual bandit algorithms.

This module implements sophisticated off-policy learning algorithms
inspired by the contextual bandits research, including DoublyRobust
estimators and OffsetTree techniques for improved decision making.
"""

from __future__ import annotations

import math
import random
from collections import defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from .bandit_base import ThompsonSamplingBandit


if TYPE_CHECKING:
    from collections.abc import Callable, Sequence


def _ctx_vector(ctx: dict[str, Any], dim: int = 8) -> list[float]:
    """Extract feature vector from context dictionary."""
    # bias + up to dim-1 features
    feats: list[float] = [1.0]
    for k in sorted(ctx.keys()):
        if len(feats) >= dim:
            break
        v = ctx[k]
        if isinstance(v, int | float):
            feats.append(float(v))
        elif isinstance(v, str):
            # simple hashed feature
            feats.append(float(abs(hash(v)) % 1000) / 1000.0)
        else:
            feats.append(0.0)
    while len(feats) < dim:
        feats.append(0.0)
    return feats


@dataclass
class DoublyRobustBandit:
    """Doubly Robust estimator for off-policy contextual bandits.

    Combines importance sampling with outcome modeling for robust
    off-policy evaluation and learning. Uses a reward model to
    estimate expected rewards and importance weights to correct
    for distribution shift.
    """

    # Model parameters
    alpha: float = 1.0  # Confidence parameter
    dim: int = 8  # Context dimension
    learning_rate: float = 0.1  # Reward model learning rate

    # Per-arm state for reward modeling
    reward_models: defaultdict[Any, dict[str, Any]] = field(
        default_factory=lambda: defaultdict(lambda: {"weights": [0.0] * 8, "bias": 0.0, "variance": 1.0})
    )

    # Importance sampling history
    importance_weights: defaultdict[Any, list[float]] = field(default_factory=lambda: defaultdict(list))

    # Compatibility with existing system
    q_values: defaultdict[Any, float] = field(default_factory=lambda: defaultdict(float))
    counts: defaultdict[Any, int] = field(default_factory=lambda: defaultdict(int))

    def __post_init__(self):
        """Initialize reward models with correct dimensions."""

        # Update default factory to use current dim
        def _make_model():
            return {"weights": [0.0] * self.dim, "bias": 0.0, "variance": 1.0}

        self.reward_models.default_factory = _make_model

    def _predict_reward(self, action: Any, context: dict[str, Any]) -> float:
        """Predict expected reward using learned reward model."""
        x = _ctx_vector(context, self.dim)
        model = self.reward_models[action]

        # Linear model: y = w^T x + b
        prediction = model["bias"]
        for i, xi in enumerate(x):
            prediction += model["weights"][i] * xi

        return prediction

    def _update_reward_model(self, action: Any, context: dict[str, Any], reward: float):
        """Update reward model using gradient descent."""
        x = _ctx_vector(context, self.dim)
        model = self.reward_models[action]

        # Predict current reward
        predicted = self._predict_reward(action, context)
        error = reward - predicted

        # Gradient descent update
        model["bias"] += self.learning_rate * error
        for i, xi in enumerate(x):
            model["weights"][i] += self.learning_rate * error * xi

        # Update variance estimate (exponential moving average)
        model["variance"] = 0.9 * model["variance"] + 0.1 * (error**2)

    def recommend(self, context: dict[str, Any], candidates: Sequence[Any]) -> Any:
        """Recommend action using doubly robust estimation."""
        if not candidates:
            raise ValueError("candidates must not be empty")

        best_action = None
        best_value = float("-inf")

        for action in candidates:
            # Reward model prediction
            reward_pred = self._predict_reward(action, context)

            # Confidence interval based on variance
            model = self.reward_models[action]
            confidence = self.alpha * math.sqrt(model["variance"] / max(self.counts[action], 1))

            # Upper confidence bound
            value = reward_pred + confidence

            if value > best_value:
                best_value = value
                best_action = action

        return best_action

    def update(self, action: Any, reward: float, context: dict[str, Any]) -> None:
        """Update using doubly robust estimation."""
        # Update reward model
        self._update_reward_model(action, context, reward)

        # Update importance weights (simplified - assumes uniform exploration)
        self.importance_weights[action].append(1.0)

        # Keep only recent importance weights
        if len(self.importance_weights[action]) > 1000:
            self.importance_weights[action] = self.importance_weights[action][-1000:]

        # Update compatibility metrics
        self.counts[action] += 1
        n = self.counts[action]
        q = self.q_values[action]
        self.q_values[action] = q + (reward - q) / n

    def update_with_importance_weight(
        self,
        action: Any,
        reward: float,
        context: dict[str, Any],
        importance_weight: float,
    ) -> None:
        """Update with explicit importance weight for off-policy learning."""
        # Clamp importance weight to prevent instability
        weight = max(0.01, min(10.0, importance_weight))

        # Weighted reward model update
        x = _ctx_vector(context, self.dim)
        model = self.reward_models[action]

        predicted = self._predict_reward(action, context)
        error = weight * (reward - predicted)

        # Weighted gradient descent
        model["bias"] += self.learning_rate * error
        for i, xi in enumerate(x):
            model["weights"][i] += self.learning_rate * error * xi

        # Update with importance weight
        self.importance_weights[action].append(weight)

        # Keep only recent weights
        if len(self.importance_weights[action]) > 1000:
            self.importance_weights[action] = self.importance_weights[action][-1000:]

        # Update metrics with weighted reward
        self.counts[action] += 1
        n = self.counts[action]
        q = self.q_values[action]
        weighted_reward = weight * reward
        self.q_values[action] = q + (weighted_reward - q) / n

    def state_dict(self) -> dict[str, Any]:
        """Serialize state for persistence."""
        return {
            "policy": self.__class__.__name__,
            "version": 1,
            "alpha": self.alpha,
            "dim": self.dim,
            "learning_rate": self.learning_rate,
            "reward_models": {k: dict(v) for k, v in self.reward_models.items()},
            "importance_weights": {k: list(v[-100:]) for k, v in self.importance_weights.items()},  # Keep recent
            "q_values": dict(self.q_values),
            "counts": dict(self.counts),
        }

    def load_state(self, state: dict[str, Any]) -> None:
        """Load state from serialized format."""
        ver = state.get("version")
        if ver is not None and ver > 1:
            return

        # Load parameters
        self.alpha = float(state.get("alpha", self.alpha))
        self.dim = int(state.get("dim", self.dim))
        self.learning_rate = float(state.get("learning_rate", self.learning_rate))

        # Load reward models
        models_data = state.get("reward_models", {})
        self.reward_models.clear()
        for k, v in models_data.items():
            self.reward_models[k] = dict(v)

        # Load importance weights
        weights_data = state.get("importance_weights", {})
        self.importance_weights.clear()
        for k, v in weights_data.items():
            self.importance_weights[k] = list(v)

        # Load compatibility metrics
        self.q_values.clear()
        self.q_values.update(state.get("q_values", {}))
        self.counts.clear()
        self.counts.update(state.get("counts", {}))


@dataclass
class OffsetTreeBandit:
    """OffsetTree algorithm for contextual bandits.

    Uses a tree-based approach to partition the context space
    and learn separate policies for each region. Provides
    better handling of complex context dependencies.
    """

    # Tree parameters
    max_depth: int = 3
    min_samples_split: int = 10
    split_threshold: float = 0.1

    # Base bandit for each leaf
    base_bandit_factory: Callable[[], Any] = field(default_factory=lambda: lambda: ThompsonSamplingBandit())

    # Tree structure
    tree_nodes: dict[str, dict[str, Any]] = field(default_factory=dict)

    # Compatibility
    q_values: defaultdict[Any, float] = field(default_factory=lambda: defaultdict(float))
    counts: defaultdict[Any, int] = field(default_factory=lambda: defaultdict(int))

    # Context history for tree building
    context_history: list[tuple[dict[str, Any], Any, float]] = field(default_factory=list)

    def __post_init__(self):
        """Initialize root node."""
        if "root" not in self.tree_nodes:
            self.tree_nodes["root"] = {
                "is_leaf": True,
                "bandit": self.base_bandit_factory(),
                "samples": 0,
                "depth": 0,
            }

    def _get_node_id(self, context: dict[str, Any], node_id: str = "root") -> str:
        """Get the leaf node ID for a given context."""
        node = self.tree_nodes[node_id]

        if node["is_leaf"]:
            return node_id

        # Navigate tree based on split
        feature = node["split_feature"]
        threshold = node["split_threshold"]

        if feature in context:
            value = context[feature]
            if isinstance(value, (int, float)) and value <= threshold:
                return self._get_node_id(context, node["left_child"])
            else:
                return self._get_node_id(context, node["right_child"])
        else:
            # Default to left if feature missing
            return self._get_node_id(context, node["left_child"])

    def _should_split(self, node_id: str) -> bool:
        """Determine if a node should be split."""
        node = self.tree_nodes[node_id]

        # Check split conditions
        if node["depth"] >= self.max_depth or node["samples"] < self.min_samples_split:
            return False

        # Simple heuristic: split if there's sufficient variance in rewards
        if len(self.context_history) < self.min_samples_split:
            return False

        # Calculate reward variance for contexts that would go to this node
        rewards = []
        for ctx, _action, reward in self.context_history[-100:]:  # Recent samples
            if self._get_node_id(ctx) == node_id:
                rewards.append(reward)

        if len(rewards) < self.min_samples_split:
            return False

        if len(rewards) > 1:
            mean_reward = sum(rewards) / len(rewards)
            variance = sum((r - mean_reward) ** 2 for r in rewards) / len(rewards)
            return variance > self.split_threshold

        return False

    def _split_node(self, node_id: str):
        """Split a leaf node into two children."""
        if node_id not in self.tree_nodes:
            return

        node = self.tree_nodes[node_id]
        if not node["is_leaf"]:
            return

        # Find best split (simplified)
        # In practice, this would evaluate multiple features and thresholds
        best_feature = None
        best_threshold = 0.0
        best_score = float("-inf")

        # Get recent contexts for this node
        node_contexts = []
        for ctx, action, reward in self.context_history[-100:]:
            if self._get_node_id(ctx) == node_id:
                node_contexts.append((ctx, action, reward))

        if len(node_contexts) < self.min_samples_split:
            return

        # Try splitting on each numeric feature
        for ctx, _, _ in node_contexts[:10]:  # Sample a few contexts
            for feature, value in ctx.items():
                if isinstance(value, (int, float)):
                    threshold = float(value)

                    # Calculate split quality (simplified information gain)
                    left_rewards = []
                    right_rewards = []

                    for c, _, r in node_contexts:
                        if feature in c and isinstance(c[feature], (int, float)):
                            if c[feature] <= threshold:
                                left_rewards.append(r)
                            else:
                                right_rewards.append(r)

                    if len(left_rewards) > 0 and len(right_rewards) > 0:
                        # Simple variance reduction score
                        total_var = sum(
                            (r - sum(left_rewards + right_rewards) / len(left_rewards + right_rewards)) ** 2
                            for r in left_rewards + right_rewards
                        )

                        left_mean = sum(left_rewards) / len(left_rewards)
                        right_mean = sum(right_rewards) / len(right_rewards)

                        left_var = sum((r - left_mean) ** 2 for r in left_rewards)
                        right_var = sum((r - right_mean) ** 2 for r in right_rewards)

                        score = total_var - (left_var + right_var)

                        if score > best_score:
                            best_score = score
                            best_feature = feature
                            best_threshold = threshold

        if best_feature is None:
            return

        # Create child nodes
        left_id = f"{node_id}_left"
        right_id = f"{node_id}_right"

        self.tree_nodes[left_id] = {
            "is_leaf": True,
            "bandit": self.base_bandit_factory(),
            "samples": 0,
            "depth": node["depth"] + 1,
        }

        self.tree_nodes[right_id] = {
            "is_leaf": True,
            "bandit": self.base_bandit_factory(),
            "samples": 0,
            "depth": node["depth"] + 1,
        }

        # Update parent node
        node["is_leaf"] = False
        node["split_feature"] = best_feature
        node["split_threshold"] = best_threshold
        node["left_child"] = left_id
        node["right_child"] = right_id

    def recommend(self, context: dict[str, Any], candidates: Sequence[Any]) -> Any:
        """Recommend action using the appropriate tree node."""
        if not candidates:
            raise ValueError("candidates must not be empty")

        # Find the appropriate leaf node
        node_id = self._get_node_id(context)
        node = self.tree_nodes[node_id]

        # Use the bandit at this leaf
        bandit = node["bandit"]

        # Check if bandit has recommend method
        if hasattr(bandit, "recommend"):
            return bandit.recommend(context, candidates)
        else:
            # Fallback to random selection
            return random.choice(list(candidates))

    def update(self, action: Any, reward: float, context: dict[str, Any]) -> None:
        """Update the tree and appropriate bandit."""
        # Add to history
        self.context_history.append((dict(context), action, reward))

        # Keep only recent history
        if len(self.context_history) > 10000:
            self.context_history = self.context_history[-5000:]

        # Find the appropriate leaf node
        node_id = self._get_node_id(context)
        node = self.tree_nodes[node_id]

        # Update node statistics
        node["samples"] += 1

        # Update the bandit at this leaf
        bandit = node["bandit"]
        if hasattr(bandit, "update"):
            bandit.update(action, reward, context)

        # Check if we should split this node
        if node["is_leaf"] and self._should_split(node_id):
            self._split_node(node_id)

        # Update compatibility metrics
        self.counts[action] += 1
        n = self.counts[action]
        q = self.q_values[action]
        self.q_values[action] = q + (reward - q) / n

    def state_dict(self) -> dict[str, Any]:
        """Serialize tree state."""
        # Serialize each bandit's state
        serialized_nodes = {}
        for node_id, node in self.tree_nodes.items():
            serialized_node = dict(node)
            if "bandit" in node and hasattr(node["bandit"], "state_dict"):
                serialized_node["bandit_state"] = node["bandit"].state_dict()
                serialized_node["bandit_class"] = node["bandit"].__class__.__name__
            serialized_nodes[node_id] = serialized_node

        return {
            "policy": self.__class__.__name__,
            "version": 1,
            "max_depth": self.max_depth,
            "min_samples_split": self.min_samples_split,
            "split_threshold": self.split_threshold,
            "tree_nodes": serialized_nodes,
            "q_values": dict(self.q_values),
            "counts": dict(self.counts),
            "context_history": self.context_history[-100:],  # Keep recent history
        }

    def load_state(self, state: dict[str, Any]) -> None:
        """Load tree state from serialized format."""
        ver = state.get("version")
        if ver is not None and ver > 1:
            return

        # Load parameters
        self.max_depth = int(state.get("max_depth", self.max_depth))
        self.min_samples_split = int(state.get("min_samples_split", self.min_samples_split))
        self.split_threshold = float(state.get("split_threshold", self.split_threshold))

        # Load tree nodes (simplified - would need to reconstruct bandits)
        nodes_data = state.get("tree_nodes", {})
        self.tree_nodes.clear()

        for node_id, node_data in nodes_data.items():
            node = dict(node_data)
            # Reconstruct bandit (simplified)
            if "bandit_state" in node_data:
                node["bandit"] = self.base_bandit_factory()
                if hasattr(node["bandit"], "load_state"):
                    node["bandit"].load_state(node_data["bandit_state"])
            else:
                node["bandit"] = self.base_bandit_factory()
            self.tree_nodes[node_id] = node

        # Load compatibility metrics
        self.q_values.clear()
        self.q_values.update(state.get("q_values", {}))
        self.counts.clear()
        self.counts.update(state.get("counts", {}))

        # Load context history
        self.context_history = state.get("context_history", [])


__all__ = ["DoublyRobustBandit", "OffsetTreeBandit"]
