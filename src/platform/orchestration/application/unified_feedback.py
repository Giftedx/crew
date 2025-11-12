"""Compatibility shim for unified feedback orchestrator.

Re-exports from domains.orchestration.legacy for backward compatibility.
"""

# Import directly from the implementation file to avoid circular import through __init__
from domains.orchestration.legacy.application.unified_feedback import (
    ComponentType,
    FeedbackSignal,
    FeedbackSource,
    OrchestratorMetrics,
    UnifiedFeedbackOrchestrator,
    UnifiedFeedbackSignal,
)


def get_orchestrator():
    """Get orchestrator instance (placeholder)."""
    return UnifiedFeedbackOrchestrator()


def get_unified_feedback_orchestrator():
    """Get unified feedback orchestrator (placeholder)."""
    return UnifiedFeedbackOrchestrator()


def set_orchestrator(orch):
    """Set orchestrator (placeholder)."""


__all__ = [
    "ComponentType",
    "FeedbackSignal",
    "FeedbackSource",
    "OrchestratorMetrics",
    "UnifiedFeedbackOrchestrator",
    "UnifiedFeedbackSignal",
    "get_orchestrator",
    "get_unified_feedback_orchestrator",
    "set_orchestrator",
]
