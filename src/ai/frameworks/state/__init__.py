"""Framework-agnostic workflow state management.

This package provides unified state management that works across all supported
AI frameworks (CrewAI, LangGraph, AutoGen, LlamaIndex).
"""

from .protocols import (
    Checkpoint,
    Message,
    MessageRole,
    StateConverter,
    StateMetadata,
    StatePersistence,
)
from .unified_state import UnifiedWorkflowState


__all__ = [
    "Checkpoint",
    "Message",
    "MessageRole",
    "StateConverter",
    "StateMetadata",
    "StatePersistence",
    "UnifiedWorkflowState",
]
