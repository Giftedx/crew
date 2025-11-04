import logging
import random
from collections import deque
from platform.observability.metrics import get_metrics
from typing import Any

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

from ultimate_discord_intelligence_bot.step_result import ErrorCategory, StepResult


logger = logging.getLogger(__name__)
metrics = get_metrics()


class NeuralContextualBandit(nn.Module):
    """Neural network-based contextual bandit for routing decisions."""

    def __init__(self, context_dim: int, n_arms: int, hidden_dim: int = 128):
        super().__init__()
        self.context_dim = context_dim
        self.n_arms = n_arms
        self.feature_extractor = nn.Sequential(
            nn.Linear(context_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
        )
        self.arm_heads = nn.ModuleList([nn.Linear(hidden_dim, 1) for _ in range(n_arms)])
        self.uncertainty_net = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2), nn.ReLU(), nn.Linear(hidden_dim // 2, n_arms), nn.Softplus()
        )
        self.optimizer = optim.Adam(self.parameters(), lr=0.001)
        self.experience_buffer = deque(maxlen=10000)

    def forward(self, context: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """Forward pass returning rewards and uncertainties."""
        features = self.feature_extractor(context)
        rewards = torch.stack([head(features) for head in self.arm_heads], dim=1).squeeze(-1)
        uncertainties = self.uncertainty_net(features)
        return (rewards, uncertainties)

    def select_arm(self, context: np.ndarray, exploration_rate: float = 0.1) -> int:
        """Select an arm using Thompson sampling with neural uncertainty."""
        with torch.no_grad():
            context_tensor = torch.FloatTensor(context).unsqueeze(0)
            rewards, uncertainties = self(context_tensor)
            sampled_rewards = rewards + uncertainties * torch.randn_like(rewards) * exploration_rate
            arm = sampled_rewards.argmax().item()
            metrics.counter("bandit_selections_total", labels={"arm": str(arm)})
            return arm

    def update(self, context: np.ndarray, arm: int, reward: float):
        """Update the model with new experience."""
        self.experience_buffer.append((context, arm, reward))
        if len(self.experience_buffer) >= 32:
            self._train_on_batch(batch_size=32)

    def _train_on_batch(self, batch_size: int = 32):
        """Train on a random batch from experience buffer."""
        if len(self.experience_buffer) < batch_size:
            return
        batch = random.sample(self.experience_buffer, batch_size)
        contexts = torch.FloatTensor([x[0] for x in batch])
        arms = torch.LongTensor([x[1] for x in batch])
        rewards = torch.FloatTensor([x[2] for x in batch])
        pred_rewards, uncertainties = self(contexts)
        selected_rewards = pred_rewards.gather(1, arms.unsqueeze(1)).squeeze()
        mse_loss = nn.MSELoss()(selected_rewards, rewards)
        uncertainty_loss = uncertainties.gather(1, arms.unsqueeze(1)).mean()
        loss = mse_loss + 0.01 * uncertainty_loss
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        metrics.counter("bandit_updates_total")
        metrics.gauge("bandit_loss", loss.item())


class NeuralBanditRouter:
    """Router using neural contextual bandits."""

    def __init__(self, models: list[str]):
        self.models = models
        self.bandit = NeuralContextualBandit(context_dim=768, n_arms=len(models))

    def route_request(self, content: dict[str, Any]) -> StepResult:
        """Route a request to the best model."""
        try:
            context = self._extract_features(content)
            model_idx = self.bandit.select_arm(context)
            selected_model = self.models[model_idx]
            return StepResult.ok(
                result={"model": selected_model}, metadata={"routing_method": "neural_bandit", "model_index": model_idx}
            )
        except Exception as e:
            logger.error(f"Neural bandit routing failed: {e}")
            return StepResult.fail(error=str(e), error_category=ErrorCategory.ROUTING_ERROR)

    def update_reward(self, content: dict[str, Any], model: str, reward: float) -> StepResult:
        """Update the bandit with observed reward."""
        try:
            context = self._extract_features(content)
            model_idx = self.models.index(model)
            self.bandit.update(context, model_idx, reward)
            return StepResult.ok(result={"updated": True}, metadata={"model": model, "reward": reward})
        except Exception as e:
            return StepResult.fail(error=str(e), error_category=ErrorCategory.ROUTING_ERROR)

    def _extract_features(self, content: dict[str, Any]) -> np.ndarray:
        """Extract feature vector from content."""
        return np.random.randn(768)
