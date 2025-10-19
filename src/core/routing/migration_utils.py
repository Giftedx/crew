"""Utilities for migrating from old router to new unified router architecture."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from ..router import Router as LegacyRouter
from .base_router import BaseRouter, RoutingResult
from .router_factory import RouterFactory

logger = logging.getLogger(__name__)


class LegacyRouterAdapter:
    """Adapter to make legacy Router compatible with new BaseRouter interface."""

    def __init__(self, legacy_router: LegacyRouter) -> None:
        """Initialize adapter with legacy router."""
        self.legacy_router = legacy_router

    def route(
        self,
        task: str,
        candidates: list[str],
        context: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> RoutingResult:
        """Route using legacy router and convert result."""
        try:
            # Call legacy router
            model = self.legacy_router.route(task, candidates, context or {})

            # Convert to new result format
            return RoutingResult(
                model=model,
                strategy_used="legacy",
                fallback_used=False,
                metadata={"legacy_router": True},
            )
        except Exception as e:
            logger.error(f"Legacy router failed: {e}")
            # Fallback to first candidate
            fallback_model = candidates[0] if candidates else "unknown"
            return RoutingResult(
                model=fallback_model,
                strategy_used="legacy_fallback",
                fallback_used=True,
                metadata={"error": str(e), "legacy_router": True},
            )

    def preflight(
        self,
        prompt: str,
        candidates: list[str],
        expected_output_tokens: int,
    ) -> str:
        """Preflight using legacy router."""
        return self.legacy_router.preflight(prompt, candidates, expected_output_tokens)

    def update_reward(self, model: str, reward: float, context: dict[str, Any]) -> None:
        """Update reward using legacy router's learning engine."""
        if hasattr(self.legacy_router, "learning_engine"):
            try:
                # Extract task type from context if available
                task_type = context.get("task", "general")
                self.legacy_router.learning_engine.update(task_type, model, reward)
            except Exception as e:
                logger.warning(f"Failed to update legacy router reward: {e}")


class RouterMigrationHelper:
    """Helper class for migrating from legacy to new router architecture."""

    @staticmethod
    def migrate_legacy_router(
        legacy_router: LegacyRouter,
        target_strategy: str = "balanced",
        preserve_learning: bool = True,
    ) -> BaseRouter:
        """Migrate a legacy router to new architecture.
        Args:
            legacy_router: The legacy router to migrate
            target_strategy: Target strategy for new router
            preserve_learning: Whether to preserve learning state
        Returns:
            New router instance with migrated configuration
        """
        # Extract learning engine if available
        learning_engine = None
        if preserve_learning and hasattr(legacy_router, "learning_engine"):
            learning_engine = legacy_router.learning_engine
            logger.info("Preserved learning engine from legacy router")

        # Extract tenant registry if available
        registry = None
        if hasattr(legacy_router, "registry"):
            registry = legacy_router.registry
            logger.info("Preserved tenant registry from legacy router")

        # Create new router with extracted components
        new_router = RouterFactory.create_router(
            strategy=target_strategy,
            learning_engine=learning_engine,
            registry=registry,
        )

        logger.info(f"Migrated legacy router to new {target_strategy} strategy")
        return new_router

    @staticmethod
    def create_compatibility_wrapper(
        legacy_router: LegacyRouter,
    ) -> Callable[[str, list[str], dict[str, Any] | None], str]:
        """Create a compatibility wrapper for legacy router calls.
        Args:
            legacy_router: Legacy router instance

        Returns:
            Wrapped function that provides new interface
        """
        adapter = LegacyRouterAdapter(legacy_router)

        def wrapped_route(
            task: str,
            candidates: list[str],
            context: dict[str, Any] | None = None,
            **kwargs: Any,
        ) -> str:
            """Wrapped route function that returns just the model string."""
            result = adapter.route(task, candidates, context, **kwargs)
            return result.model

        return wrapped_route

    @staticmethod
    def extract_learning_state(legacy_router: LegacyRouter) -> dict[str, Any]:
        """Extract learning state from legacy router.

        Args:
            legacy_router: Legacy router instance

        Returns:
            Dictionary containing learning state
        """
        state = {}

        if hasattr(legacy_router, "learning_engine"):
            try:
                state = legacy_router.learning_engine.snapshot()
                logger.info("Extracted learning state from legacy router")
            except Exception as e:
                logger.warning(f"Failed to extract learning state: {e}")

        return state

    @staticmethod
    def restore_learning_state(
        new_router: BaseRouter,
        learning_state: dict[str, Any],
    ) -> None:
        """Restore learning state to new router.

        Args:
            new_router: New router instance
            learning_state: Learning state to restore
        """
        if hasattr(new_router.strategy, "restore_policy"):
            try:
                # Try to restore to the strategy's domain
                domain_state = learning_state.get(new_router.strategy.get_strategy_name(), {})
                if domain_state:
                    new_router.strategy.restore_policy(domain_state)
                    logger.info("Restored learning state to new router")
            except Exception as e:
                logger.warning(f"Failed to restore learning state: {e}")


def create_hybrid_router(
    legacy_router: LegacyRouter,
    new_router: BaseRouter,
    use_legacy_for: list[str] | None = None,
) -> Callable[[str, list[str], dict[str, Any] | None], RoutingResult]:
    """Create a hybrid router that uses both legacy and new routers.

    Args:
        legacy_router: Legacy router instance
        new_router: New router instance
        use_legacy_for: List of task types to route with legacy router

    Returns:
        Hybrid routing function
    """
    use_legacy_for = use_legacy_for or []
    legacy_adapter = LegacyRouterAdapter(legacy_router)

    def hybrid_route(
        task: str,
        candidates: list[str],
        context: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> RoutingResult:
        """Hybrid routing function."""
        if task in use_legacy_for:
            logger.debug(f"Using legacy router for task: {task}")
            return legacy_adapter.route(task, candidates, context, **kwargs)
        else:
            logger.debug(f"Using new router for task: {task}")
            return new_router.route(task, candidates, context, **kwargs)

    return hybrid_route


__all__ = [
    "LegacyRouterAdapter",
    "RouterMigrationHelper",
    "create_hybrid_router",
]
