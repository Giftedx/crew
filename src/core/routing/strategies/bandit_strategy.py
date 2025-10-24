"""Bandit-based routing strategy implementation."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from ultimate_discord_intelligence_bot.tenancy import current_tenant

from ...learning_engine import LearningEngine
from ..base_router import RoutingContext, RoutingStrategy


if TYPE_CHECKING:
    from ultimate_discord_intelligence_bot.tenancy.registry import TenantRegistry


logger = logging.getLogger(__name__)


class BanditStrategy(RoutingStrategy):
    """Bandit-based routing strategy using reinforcement learning."""

    def __init__(
        self,
        learning_engine: LearningEngine | None = None,
        registry: TenantRegistry | None = None,
        domain: str = "routing",
        epsilon: float = 0.1,
    ) -> None:
        """Initialize bandit strategy.

        Args:
            learning_engine: The learning engine for model selection
            registry: Tenant registry for permission filtering
            domain: Domain name for the bandit policy
            epsilon: Exploration rate for epsilon-greedy behavior
        """
        self.learning_engine = learning_engine or LearningEngine()
        self.registry = registry
        self.domain = domain
        self.epsilon = epsilon
        self._ensure_domain()

    def _ensure_domain(self) -> None:
        """Ensure routing domain is registered."""
        try:
            self.learning_engine.registry.get(self.domain)
        except KeyError:
            self.learning_engine.register_domain(self.domain)

    def select_model(self, context: RoutingContext) -> str:
        """Select model using bandit learning."""
        if not self.validate_candidates(context.candidates):
            raise ValueError("No candidates available")

        # Filter candidates by tenant permissions
        candidates = self._filter_candidates(context.candidates)
        if not candidates:
            raise ValueError("No allowed models for tenant")

        try:
            # Use learning engine to recommend model
            model = self.learning_engine.recommend(self.domain, context.metadata or {}, candidates)
            logger.debug(f"Bandit strategy selected model: {model} from {len(candidates)} candidates")
            return model
        except Exception as e:
            logger.warning(f"Bandit strategy failed, using fallback: {e}")
            return candidates[0]

    def _filter_candidates(self, candidates: list[str]) -> list[str]:
        """Filter candidates based on tenant permissions."""
        ctx = current_tenant()
        if not ctx or not self.registry:
            return candidates

        allowed = self.registry.get_allowed_models(ctx)
        if allowed:
            filtered = [c for c in candidates if c in allowed]
            logger.debug(f"Filtered {len(candidates)} candidates to {len(filtered)} allowed models")
            return filtered
        return candidates

    def get_strategy_name(self) -> str:
        """Return strategy name."""
        return "bandit"

    def update_reward(self, model: str, reward: float, context: dict[str, Any]) -> None:
        """Update the bandit with reward feedback."""
        try:
            self.learning_engine.record(self.domain, context, model, reward)
            logger.debug(f"Updated bandit reward for {model}: {reward}")
        except Exception as e:
            logger.warning(f"Failed to update bandit reward: {e}")

    def get_policy_status(self) -> dict[str, Any]:
        """Get current policy status for monitoring."""
        try:
            return self.learning_engine.status().get(self.domain, {})
        except Exception as e:
            logger.warning(f"Failed to get policy status: {e}")
            return {}

    def snapshot_policy(self) -> dict[str, Any]:
        """Get policy snapshot for persistence."""
        try:
            snapshot = self.learning_engine.snapshot()
            return snapshot.get(self.domain, {})
        except Exception as e:
            logger.warning(f"Failed to snapshot policy: {e}")
            return {}

    def restore_policy(self, snapshot: dict[str, Any]) -> None:
        """Restore policy from snapshot."""
        try:
            full_snapshot = {self.domain: snapshot}
            self.learning_engine.restore(full_snapshot)
            logger.info(f"Restored policy for domain {self.domain}")
        except Exception as e:
            logger.warning(f"Failed to restore policy: {e}")
