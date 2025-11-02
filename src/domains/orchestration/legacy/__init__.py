"""Core orchestration package.

This package provides a hierarchical orchestration system for coordinating
complex multi-agent workflows across domain, application, and infrastructure layers.

Usage:
    from core.orchestration import (
        OrchestrationLayer,
        OrchestrationContext,
        OrchestratorProtocol,
        BaseOrchestrator,
        get_orchestration_facade,
    )

    # Create context
    context = OrchestrationContext(
        tenant_id="crew",
        request_id="req-123",
        metadata={"task": "analysis"},
    )

    # Get facade
    facade = get_orchestration_facade()

    # Execute orchestration
    result = await facade.orchestrate("my_orchestrator", context)
"""

from core.orchestration.facade import OrchestrationFacade, get_orchestration_facade
from core.orchestration.protocols import (
    BaseOrchestrator,
    OrchestrationContext,
    OrchestrationLayer,
    OrchestrationType,
    OrchestratorProtocol,
)


__all__ = [
    # Protocols
    "OrchestratorProtocol",
    "BaseOrchestrator",
    # Enums
    "OrchestrationLayer",
    "OrchestrationType",
    # Context
    "OrchestrationContext",
    # Facade
    "OrchestrationFacade",
    "get_orchestration_facade",
]
