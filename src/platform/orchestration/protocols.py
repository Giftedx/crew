"""Compatibility shim for platform.orchestration.protocols imports.

This module provides backward compatibility for imports expecting platform.orchestration.protocols
by redirecting to the actual location in domains.orchestration.legacy.protocols.
"""

# Re-export from domains.orchestration.legacy.protocols
from domains.orchestration.legacy.protocols import (
    BaseOrchestrator,
    OrchestrationContext,
    OrchestrationLayer,
    OrchestrationType,
    OrchestratorProtocol,
)


__all__ = [
    "BaseOrchestrator",
    "OrchestrationContext",
    "OrchestrationLayer",
    "OrchestrationType",
    "OrchestratorProtocol",
]
