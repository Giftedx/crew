"""Unified orchestrator facade with strategy selection.

Consolidates nine competing orchestrator implementations into a single
entry point with pluggable strategy classes.

See ADR-0004 for architectural decision rationale.
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Any, Protocol

from ..step_result import StepResult
from .strategies import get_strategy_registry


logger = logging.getLogger(__name__)


class OrchestrationStrategy(str, Enum):
    """Available orchestration strategies."""

    AUTONOMOUS = "autonomous"  # Default full intelligence workflow
    FALLBACK = "fallback"  # Degraded mode during outages
    HIERARCHICAL = "hierarchical"  # Multi-tier agent coordination
    MONITORING = "monitoring"  # Observability-focused workflow
    TRAINING = "training"  # Agent training and evaluation


class OrchestratorProtocol(Protocol):
    """Protocol for orchestrator implementations."""

    async def execute_workflow(
        self,
        url: str,
        depth: str,
        tenant: str,
        workspace: str,
        **kwargs: Any,
    ) -> StepResult:
        """Execute intelligence workflow."""
        ...


class OrchestrationFacade:
    """Unified orchestrator facade with strategy selection."""

    def __init__(self, strategy: OrchestrationStrategy = OrchestrationStrategy.AUTONOMOUS):
        """Initialize orchestrator with specified strategy.

        Args:
            strategy: Orchestration strategy to use
        """
        self.strategy = strategy
        self._orchestrator: Any | None = None

    def _get_orchestrator(self) -> Any:
        """Lazy-load orchestrator based on strategy via registry.

        Supports both new registry-based strategies and legacy direct imports
        for backward compatibility during migration.
        """
        if self._orchestrator is not None:
            return self._orchestrator

        registry = get_strategy_registry()

        # Try registry first (Phase 5 strategies)
        strategy_name = self.strategy.value
        strategy_class = registry.get(strategy_name)

        if strategy_class is not None:
            # Found in registry - instantiate and return
            self._orchestrator = strategy_class()
            logger.info(f"Initialized {strategy_name} strategy from registry")
            return self._orchestrator

        # Fallback to legacy direct imports for strategies not yet migrated
        logger.debug(f"Strategy '{strategy_name}' not in registry, using legacy import")

        if self.strategy == OrchestrationStrategy.AUTONOMOUS:
            from ..autonomous_orchestrator import AutonomousIntelligenceOrchestrator

            self._orchestrator = AutonomousIntelligenceOrchestrator()

        elif self.strategy == OrchestrationStrategy.TRAINING:
            from ..agent_training.orchestrator import TrainingOrchestrator

            self._orchestrator = TrainingOrchestrator()

        else:
            raise ValueError(f"Strategy '{strategy_name}' not found in registry and no legacy fallback available")

        logger.info(f"Initialized {self.strategy.value} orchestrator (legacy)")
        return self._orchestrator

    async def execute_workflow(
        self,
        url: str,
        depth: str = "standard",
        tenant: str = "default",
        workspace: str = "main",
        **kwargs: Any,
    ) -> StepResult:
        """Execute intelligence workflow with selected strategy.

        Args:
            url: Content URL to process
            depth: Analysis depth (standard, deep, comprehensive, experimental)
            tenant: Tenant identifier
            workspace: Workspace identifier
            **kwargs: Strategy-specific parameters

        Returns:
            StepResult with workflow execution outcome
        """
        try:
            orchestrator = self._get_orchestrator()

            # Route to orchestrator's execution method
            if hasattr(orchestrator, "execute_workflow"):
                return await orchestrator.execute_workflow(
                    url=url,
                    depth=depth,
                    tenant=tenant,
                    workspace=workspace,
                    **kwargs,
                )
            elif hasattr(orchestrator, "run_intelligence_workflow"):
                result = await orchestrator.run_intelligence_workflow(
                    url=url,
                    depth=depth,
                    tenant=tenant,
                    workspace=workspace,
                    **kwargs,
                )
                # Wrap non-StepResult returns
                if not isinstance(result, StepResult):
                    return StepResult.ok(data=result)
                return result
            else:
                return StepResult.fail(f"Orchestrator {type(orchestrator).__name__} missing execute method")

        except Exception as exc:
            logger.error(f"Workflow execution failed: {exc}", exc_info=True)
            return StepResult.fail(f"Orchestration failed: {exc}")


_default_orchestrator: OrchestrationFacade | None = None


def _register_strategies() -> None:
    """Register Phase 5 strategies in registry on module import."""
    registry = get_strategy_registry()

    # Import and register Phase 5 strategies
    try:
        from .strategies import (
            FallbackStrategy,
            HierarchicalStrategy,
            MonitoringStrategy,
        )

        registry.register(FallbackStrategy)
        registry.register(HierarchicalStrategy)
        registry.register(MonitoringStrategy)

        logger.debug("Registered 3 Phase 5 orchestration strategies")
    except ImportError as exc:
        logger.warning(f"Could not register Phase 5 strategies: {exc}")


def get_orchestrator(
    strategy: OrchestrationStrategy = OrchestrationStrategy.AUTONOMOUS,
) -> OrchestrationFacade:
    """Get orchestrator with specified strategy.

    Args:
        strategy: Orchestration strategy

    Returns:
        OrchestrationFacade instance
    """
    global _default_orchestrator
    if _default_orchestrator is None or _default_orchestrator.strategy != strategy:
        _default_orchestrator = OrchestrationFacade(strategy=strategy)
    return _default_orchestrator


# Register strategies on module import
_register_strategies()


__all__ = [
    "OrchestrationFacade",
    "OrchestrationStrategy",
    "get_orchestrator",
]
