"""Base protocol and registry for orchestration strategies.

Defines the interface that all orchestration strategies must implement,
enabling dynamic strategy selection and runtime swapping.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Protocol


if TYPE_CHECKING:
    from ultimate_discord_intelligence_bot.step_result import StepResult
logger = logging.getLogger(__name__)


class OrchestrationStrategyProtocol(Protocol):
    """Protocol interface for orchestration strategies.

    All orchestration strategies must implement this protocol to enable
    dynamic loading and execution through the OrchestrationFacade.
    """

    name: str
    description: str

    async def execute_workflow(self, url: str, depth: str, tenant: str, workspace: str, **kwargs: Any) -> StepResult:
        """Execute intelligence workflow with this strategy.

        Args:
            url: Content URL to process
            depth: Analysis depth (standard, deep, comprehensive, experimental)
            tenant: Tenant identifier for isolation
            workspace: Workspace identifier
            **kwargs: Strategy-specific parameters

        Returns:
            StepResult with workflow execution outcome
        """
        ...

    async def initialize(self) -> None:
        """Initialize strategy resources (optional hook)."""
        ...

    async def cleanup(self) -> None:
        """Cleanup strategy resources (optional hook)."""
        ...


class StrategyRegistry:
    """Registry for orchestration strategies."""

    def __init__(self):
        """Initialize strategy registry."""
        self._strategies: dict[str, OrchestrationStrategyProtocol] = {}
        logger.info("Strategy registry initialized")

    def register(self, strategy: type | OrchestrationStrategyProtocol, name: str | None = None) -> None:
        """Register a strategy.

        Args:
            strategy: Strategy class or instance
            name: Optional strategy name override (defaults to strategy.name)

        Raises:
            ValueError: If strategy lacks 'name' attribute and no name provided
        """
        if name is None:
            if hasattr(strategy, "name"):
                name = strategy.name
            else:
                raise ValueError(f"Strategy {strategy} has no 'name' attribute and no name provided")
        self._strategies[name] = strategy
        logger.info(f"Registered orchestration strategy: {name}")

    def get(self, name: str) -> OrchestrationStrategyProtocol | None:
        """Get strategy by name.

        Args:
            name: Strategy name

        Returns:
            Strategy instance or None if not found
        """
        strategy = self._strategies.get(name)
        if strategy is None:
            return None
        if isinstance(strategy, type):
            return strategy()
        return strategy

    def list_strategies(self) -> dict[str, str]:
        """List all registered strategies.

        Returns:
            Dict mapping strategy name to description
        """
        result = {}
        for name, strategy in self._strategies.items():
            if hasattr(strategy, "description"):
                result[name] = strategy.description
            else:
                result[name] = "No description available"
        return result

    def unregister(self, name: str) -> bool:
        """Unregister a strategy.

        Args:
            name: Strategy name

        Returns:
            True if strategy was removed, False if not found
        """
        if name in self._strategies:
            del self._strategies[name]
            logger.info(f"Unregistered orchestration strategy: {name}")
            return True
        return False


_global_registry: StrategyRegistry | None = None


def get_strategy_registry() -> StrategyRegistry:
    """Get global strategy registry.

    Returns:
        Global StrategyRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = StrategyRegistry()
    return _global_registry


__all__ = ["OrchestrationStrategyProtocol", "StrategyRegistry", "get_strategy_registry"]
