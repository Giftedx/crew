"""Compatibility shim for unified feedback orchestrator.

Re-exports from platform.orchestration.application for backward compatibility.
"""

from platform.orchestration.application.unified_feedback import *  # noqa: F403, F401

__all__ = [
    "UnifiedFeedbackOrchestrator",
    "ComponentType",
    "FeedbackSignal",
    "get_orchestrator",
]
