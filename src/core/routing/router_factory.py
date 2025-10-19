"""Factory for creating and configuring router instances."""

from __future__ import annotations

import logging
from typing import Any

from ultimate_discord_intelligence_bot.tenancy.registry import TenantRegistry

from ..learning_engine import LearningEngine
from .base_router import BaseRouter

logger = logging.getLogger(__name__)


class RouterFactory:
    """Factory for creating router instances with different configurations."""

    @staticmethod
    def create_router(
        strategy: str = "balanced",
        learning_engine: LearningEngine | None = None,
        registry: TenantRegistry | None = None,
        **kwargs: Any,
    ) -> BaseRouter:
        """Create a router with the specified strategy.

        Args:
            strategy: Routing strategy to use
            learning_engine: Learning engine for adaptive strategies
            registry: Tenant registry for permission management
            **kwargs: Additional strategy-specific configuration

        Returns:
            Configured router instance
        """
        # Create router with strategy
        router = BaseRouter(
            strategy=strategy,
            learning_engine=learning_engine,
            registry=registry,
            **kwargs,
        )

        logger.info(f"Created router with {strategy} strategy")
        return router

    @staticmethod
    def create_bandit_router(
        learning_engine: LearningEngine | None = None,
        registry: TenantRegistry | None = None,
        epsilon: float = 0.1,
        domain: str = "routing",
    ) -> BaseRouter:
        """Create a router with bandit strategy.

        Args:
            learning_engine: Learning engine for bandit algorithm
            registry: Tenant registry for permission management
            epsilon: Exploration rate for epsilon-greedy
            domain: Domain name for the bandit policy

        Returns:
            Router configured with bandit strategy
        """
        return RouterFactory.create_router(
            strategy="bandit",
            learning_engine=learning_engine,
            registry=registry,
            epsilon=epsilon,
            domain=domain,
        )

    @staticmethod
    def create_cost_aware_router(
        max_cost_per_request: float = 5.0,
        cost_alert_threshold: float = 0.8,
        learning_engine: LearningEngine | None = None,
        prioritize_cheap: bool = True,
    ) -> BaseRouter:
        """Create a router with cost-aware strategy.

        Args:
            max_cost_per_request: Maximum cost allowed per request
            cost_alert_threshold: Threshold for cost alerts
            learning_engine: Optional learning engine
            prioritize_cheap: Whether to prioritize cheaper models

        Returns:
            Router configured with cost-aware strategy
        """
        return RouterFactory.create_router(
            strategy="cost_aware",
            max_cost_per_request=max_cost_per_request,
            cost_alert_threshold=cost_alert_threshold,
            learning_engine=learning_engine,
            prioritize_cheap=prioritize_cheap,
        )

    @staticmethod
    def create_performance_router(
        learning_engine: LearningEngine | None = None,
    ) -> BaseRouter:
        """Create a router with performance strategy.

        Args:
            learning_engine: Optional learning engine

        Returns:
            Router configured with performance strategy
        """
        return RouterFactory.create_router(
            strategy="performance",
            learning_engine=learning_engine,
        )

    @staticmethod
    def create_balanced_router(
        cost_weight: float = 0.4,
        performance_weight: float = 0.3,
        quality_weight: float = 0.3,
        learning_engine: LearningEngine | None = None,
    ) -> BaseRouter:
        """Create a router with balanced strategy.

        Args:
            cost_weight: Weight for cost factor
            performance_weight: Weight for performance factor
            quality_weight: Weight for quality factor
            learning_engine: Optional learning engine

        Returns:
            Router configured with balanced strategy
        """
        return RouterFactory.create_router(
            strategy="balanced",
            cost_weight=cost_weight,
            performance_weight=performance_weight,
            quality_weight=quality_weight,
            learning_engine=learning_engine,
        )

    @staticmethod
    def create_fallback_router(
        default_selection: str = "first",
    ) -> BaseRouter:
        """Create a router with fallback strategy.

        Args:
            default_selection: How to select from candidates

        Returns:
            Router configured with fallback strategy
        """
        return RouterFactory.create_router(
            strategy="fallback",
            default_selection=default_selection,
        )

    @staticmethod
    def create_from_config(config: dict[str, Any]) -> BaseRouter:
        """Create a router from configuration dictionary.

        Args:
            config: Configuration dictionary with router settings

        Returns:
            Configured router instance
        """
        strategy = config.get("strategy", "balanced")
        learning_engine = config.get("learning_engine")
        registry = config.get("registry")

        # Remove non-router config items
        router_config = {k: v for k, v in config.items() if k not in ["strategy", "learning_engine", "registry"]}

        return RouterFactory.create_router(
            strategy=strategy,
            learning_engine=learning_engine,
            registry=registry,
            **router_config,
        )


# Global router instance for backward compatibility
_global_router: BaseRouter | None = None


def get_global_router() -> BaseRouter:
    """Get or create the global router instance."""
    global _global_router
    if _global_router is None:
        _global_router = RouterFactory.create_router()
        logger.info("Created global router instance")
    return _global_router


def set_global_router(router: BaseRouter) -> None:
    """Set the global router instance."""
    global _global_router
    _global_router = router
    logger.info("Set global router instance")


def reset_global_router() -> None:
    """Reset the global router instance."""
    global _global_router
    _global_router = None
    logger.info("Reset global router instance")


__all__ = [
    "RouterFactory",
    "get_global_router",
    "set_global_router",
    "reset_global_router",
]
