"""Orchestration protocols and base classes.

This module defines the core protocols and base classes for the hierarchical
orchestration system. All orchestrators must conform to these interfaces.
"""

from __future__ import annotations

import contextlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

import structlog


if TYPE_CHECKING:
    from ultimate_discord_intelligence_bot.step_result import StepResult
logger = structlog.get_logger(__name__)


class OrchestrationLayer(Enum):
    """Orchestration layers in the hierarchy.

    The orchestration system is organized into three layers:
    - DOMAIN: Business logic orchestration (content analysis, agent coordination)
    - APPLICATION: Application-level coordination (request handling, workflow management)
    - INFRASTRUCTURE: Infrastructure concerns (deployment, monitoring, resilience)
    """

    DOMAIN = "domain"
    APPLICATION = "application"
    INFRASTRUCTURE = "infrastructure"


class OrchestrationType(Enum):
    """Types of orchestration operations."""

    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HIERARCHICAL = "hierarchical"
    ADAPTIVE = "adaptive"
    FEEDBACK = "feedback"
    MONITORING = "monitoring"
    COORDINATION = "coordination"


@dataclass
class OrchestrationContext:
    """Shared context for orchestration operations.

    This context is passed through the orchestration hierarchy and contains
    all necessary information for orchestrators to make decisions.
    """

    tenant_id: str
    "Tenant identifier for multi-tenant isolation."
    request_id: str
    "Unique identifier for this orchestration request."
    metadata: dict[str, Any] = field(default_factory=dict)
    "Additional metadata for the orchestration."
    trace_id: str | None = None
    "Optional distributed trace ID for observability."
    parent_orchestrator: str | None = None
    "Name of the parent orchestrator (for hierarchical orchestration)."
    orchestration_depth: int = 0
    "Depth in the orchestration hierarchy (0 = top level)."

    def create_child_context(self, parent_name: str) -> OrchestrationContext:
        """Create a child context for nested orchestration.

        Args:
            parent_name: Name of the parent orchestrator

        Returns:
            New context with incremented depth and parent reference
        """
        return OrchestrationContext(
            tenant_id=self.tenant_id,
            request_id=self.request_id,
            metadata=self.metadata.copy(),
            trace_id=self.trace_id,
            parent_orchestrator=parent_name,
            orchestration_depth=self.orchestration_depth + 1,
        )


class OrchestratorProtocol(ABC):
    """Base protocol for all orchestrators.

    All orchestrators must implement this protocol to ensure consistent
    behavior across the orchestration hierarchy.
    """

    @property
    @abstractmethod
    def layer(self) -> OrchestrationLayer:
        """The orchestration layer this orchestrator belongs to."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name of this orchestrator."""
        ...

    @property
    def orchestration_type(self) -> OrchestrationType:
        """Type of orchestration performed (default: SEQUENTIAL)."""
        return OrchestrationType.SEQUENTIAL

    @abstractmethod
    async def orchestrate(self, context: OrchestrationContext, **kwargs: Any) -> StepResult:
        """Orchestrate a workflow or operation.

        Args:
            context: Orchestration context
            **kwargs: Additional operation-specific parameters

        Returns:
            StepResult indicating success or failure
        """
        ...

    async def can_orchestrate(self, context: OrchestrationContext, **kwargs: Any) -> bool:
        """Check if this orchestrator can handle the given context.

        Args:
            context: Orchestration context
            **kwargs: Additional operation-specific parameters

        Returns:
            True if this orchestrator can handle the request
        """
        return True

    async def cleanup(self) -> None:
        """Cleanup resources after orchestration.

        This is called after orchestration completes, whether successful or not.
        Default implementation does nothing - override in subclasses if needed.
        """
        # Provide a non-empty default implementation to satisfy linters (B027)
        # while keeping behavior as a no-op. Subclasses may override for
        # concrete cleanup logic.
        with contextlib.suppress(Exception):
            logger.debug(
                "orchestrator_cleanup_noop",
                orchestrator=getattr(self, "name", self.__class__.__name__),
            )


class BaseOrchestrator(OrchestratorProtocol):
    """Base class for orchestrators with common functionality.

    This class provides a foundation for concrete orchestrator implementations,
    handling common concerns like logging and context management.
    """

    def __init__(
        self, layer: OrchestrationLayer, name: str, orchestration_type: OrchestrationType = OrchestrationType.SEQUENTIAL
    ) -> None:
        """Initialize the base orchestrator.

        Args:
            layer: The orchestration layer
            name: Unique name for this orchestrator
            orchestration_type: Type of orchestration performed
        """
        self._layer = layer
        self._name = name
        self._orchestration_type = orchestration_type
        logger.info(
            "orchestrator_initialized", layer=layer.value, name=name, orchestration_type=orchestration_type.value
        )

    @property
    def layer(self) -> OrchestrationLayer:
        """The orchestration layer this orchestrator belongs to."""
        return self._layer

    @property
    def name(self) -> str:
        """Unique name of this orchestrator."""
        return self._name

    @property
    def orchestration_type(self) -> OrchestrationType:
        """Type of orchestration performed."""
        return self._orchestration_type

    async def orchestrate(self, context: OrchestrationContext, **kwargs: Any) -> StepResult:
        """Orchestrate a workflow or operation.

        This method must be implemented by concrete orchestrators.

        Args:
            context: Orchestration context
            **kwargs: Additional operation-specific parameters

        Returns:
            StepResult indicating success or failure
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement orchestrate()")

    def _log_orchestration_start(self, context: OrchestrationContext, **kwargs: Any) -> None:
        """Log the start of orchestration.

        Args:
            context: Orchestration context
            **kwargs: Additional parameters to log (filtered to avoid conflicts)
        """
        safe_kwargs = {k: v for k, v in kwargs.items() if k not in {"depth", "event", "level", "logger", "timestamp"}}
        logger.info(
            "orchestration_started",
            orchestrator=self.name,
            layer=self.layer.value,
            tenant_id=context.tenant_id,
            request_id=context.request_id,
            depth=context.orchestration_depth,
            **safe_kwargs,
        )

    def _log_orchestration_end(self, context: OrchestrationContext, result: StepResult) -> None:
        """Log the end of orchestration.

        Args:
            context: Orchestration context
            result: The orchestration result
        """
        logger.info(
            "orchestration_completed",
            orchestrator=self.name,
            layer=self.layer.value,
            tenant_id=context.tenant_id,
            request_id=context.request_id,
            success=result.success,
            depth=context.orchestration_depth,
        )
