"""Orchestration facade for unified orchestrator management.

This module provides a central facade for registering, discovering, and
executing orchestrators across the orchestration hierarchy.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog


if TYPE_CHECKING:
    from collections.abc import Sequence

    from domains.orchestration.legacy.protocols import OrchestrationContext, OrchestrationLayer, OrchestratorProtocol
    from ultimate_discord_intelligence_bot.step_result import StepResult
logger = structlog.get_logger(__name__)


class OrchestrationFacade:
    """Facade for managing orchestrators across layers.

    This class provides a central registry and execution engine for all
    orchestrators in the system, enabling hierarchical orchestration with
    proper lifecycle management.
    """

    def __init__(self) -> None:
        """Initialize the orchestration facade."""
        self._orchestrators: dict[str, OrchestratorProtocol] = {}
        self._orchestrators_by_layer: dict[OrchestrationLayer, list[OrchestratorProtocol]] = {}
        logger.info("orchestration_facade_initialized")

    def register(self, orchestrator: OrchestratorProtocol) -> None:
        """Register an orchestrator.

        Args:
            orchestrator: The orchestrator to register

        Raises:
            ValueError: If an orchestrator with the same name already exists
        """
        if orchestrator.name in self._orchestrators:
            msg = f"Orchestrator '{orchestrator.name}' is already registered"
            raise ValueError(msg)
        self._orchestrators[orchestrator.name] = orchestrator
        if orchestrator.layer not in self._orchestrators_by_layer:
            self._orchestrators_by_layer[orchestrator.layer] = []
        self._orchestrators_by_layer[orchestrator.layer].append(orchestrator)
        logger.info("orchestrator_registered", name=orchestrator.name, layer=orchestrator.layer.value)

    def unregister(self, name: str) -> None:
        """Unregister an orchestrator.

        Args:
            name: Name of the orchestrator to unregister

        Raises:
            KeyError: If no orchestrator with the given name exists
        """
        if name not in self._orchestrators:
            msg = f"Orchestrator '{name}' is not registered"
            raise KeyError(msg)
        orchestrator = self._orchestrators.pop(name)
        self._orchestrators_by_layer[orchestrator.layer].remove(orchestrator)
        logger.info("orchestrator_unregistered", name=name, layer=orchestrator.layer.value)

    def get(self, name: str) -> OrchestratorProtocol | None:
        """Get an orchestrator by name.

        Args:
            name: Name of the orchestrator

        Returns:
            The orchestrator, or None if not found
        """
        return self._orchestrators.get(name)

    def get_by_layer(self, layer: OrchestrationLayer) -> Sequence[OrchestratorProtocol]:
        """Get all orchestrators for a specific layer.

        Args:
            layer: The orchestration layer

        Returns:
            List of orchestrators for the layer
        """
        return self._orchestrators_by_layer.get(layer, [])

    async def orchestrate(self, orchestrator_name: str, context: OrchestrationContext, **kwargs) -> StepResult:
        """Execute an orchestrator by name.

        Args:
            orchestrator_name: Name of the orchestrator to execute
            context: Orchestration context
            **kwargs: Additional parameters for the orchestrator

        Returns:
            StepResult from the orchestration
        """
        from ultimate_discord_intelligence_bot.step_result import ErrorCategory, StepResult

        orchestrator = self.get(orchestrator_name)
        if orchestrator is None:
            logger.error("orchestrator_not_found", name=orchestrator_name, request_id=context.request_id)
            return StepResult.fail(
                f"Orchestrator '{orchestrator_name}' not found", error_category=ErrorCategory.PROCESSING
            )
        can_handle = await orchestrator.can_orchestrate(context, **kwargs)
        if not can_handle:
            logger.warning("orchestrator_cannot_handle", name=orchestrator_name, request_id=context.request_id)
            return StepResult.skip(f"Orchestrator '{orchestrator_name}' cannot handle this request")
        try:
            logger.info(
                "orchestration_executing",
                name=orchestrator_name,
                layer=orchestrator.layer.value,
                request_id=context.request_id,
            )
            result = await orchestrator.orchestrate(context, **kwargs)
            logger.info(
                "orchestration_completed", name=orchestrator_name, success=result.success, request_id=context.request_id
            )
            return result
        except Exception as e:
            logger.exception(
                "orchestration_failed", name=orchestrator_name, error=str(e), request_id=context.request_id
            )
            return StepResult.fail(
                f"Orchestration failed: {e}", error_category=ErrorCategory.PROCESSING, retryable=True
            )
        finally:
            try:
                await orchestrator.cleanup()
            except Exception as e:
                logger.warning("orchestrator_cleanup_failed", name=orchestrator_name, error=str(e))

    def list_orchestrators(self) -> dict[str, dict]:
        """List all registered orchestrators.

        Returns:
            Dictionary mapping orchestrator names to their metadata
        """
        return {
            name: {"layer": orc.layer.value, "type": orc.orchestration_type.value}
            for name, orc in self._orchestrators.items()
        }


_facade: OrchestrationFacade | None = None


def get_orchestration_facade() -> OrchestrationFacade:
    """Get the global orchestration facade.

    Returns:
        The global OrchestrationFacade instance
    """
    global _facade
    if _facade is None:
        _facade = OrchestrationFacade()
    return _facade
