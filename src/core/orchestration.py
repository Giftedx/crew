"""Compatibility shim for core.orchestration imports.

Re-exports from domains.orchestration.legacy.protocols for backward compatibility.
"""

from domains.orchestration.legacy.facade import get_orchestration_facade
from domains.orchestration.legacy.protocols import (
    BaseOrchestrator,
    OrchestrationContext,
    OrchestrationLayer,
    OrchestrationType,
)


__all__ = [
    "BaseOrchestrator",
    "OrchestrationContext",
    "OrchestrationLayer",
    "OrchestrationType",
    "get_orchestration_facade",
]
