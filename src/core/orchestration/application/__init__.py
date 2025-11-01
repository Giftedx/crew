"""Application layer orchestrators.

Application-level orchestrators coordinate between domain and infrastructure layers,
managing feedback loops, cross-component communication, and system-wide coordination.
"""

from core.orchestration.application.unified_feedback import (
    ComponentType,
    FeedbackSignal,
    FeedbackSource,
    OrchestratorMetrics,
    UnifiedFeedbackOrchestrator,
    UnifiedFeedbackSignal,
    get_orchestrator,
    get_unified_feedback_orchestrator,
    set_orchestrator,
    set_unified_feedback_orchestrator,
)


__all__ = [
    # Main orchestrator
    "UnifiedFeedbackOrchestrator",
    # Data structures
    "ComponentType",
    "FeedbackSignal",
    "FeedbackSource",
    "OrchestratorMetrics",
    "UnifiedFeedbackSignal",
    # Singleton accessors
    "get_unified_feedback_orchestrator",
    "set_unified_feedback_orchestrator",
    # Backward compatibility aliases
    "get_orchestrator",
    "set_orchestrator",
]
