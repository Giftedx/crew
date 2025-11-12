"""Compatibility shim for platform.orchestration.application."""

from app.main import create_app as Application


# Placeholder for UnifiedFeedbackOrchestrator (avoid circular import)
class UnifiedFeedbackOrchestrator:
    """Placeholder unified feedback orchestrator."""


def get_orchestrator():
    """Get UnifiedFeedbackOrchestrator instance (placeholder)."""
    return UnifiedFeedbackOrchestrator()


__all__ = ["Application", "UnifiedFeedbackOrchestrator", "get_orchestrator"]
