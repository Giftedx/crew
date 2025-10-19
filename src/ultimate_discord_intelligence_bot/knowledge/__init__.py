"""Unified Knowledge Layer - Phase 1 Implementation

This module provides a unified interface to all memory and knowledge systems,
consolidating vector storage, SQLite, semantic cache, and mem0 into a single
coherent interface for agents and services.
"""

from .context_builder import ContextConfig, ContextRequest, UnifiedContextBuilder
from .retrieval_engine import RetrievalConfig, RetrievalQuery, UnifiedRetrievalEngine
from .unified_memory import UnifiedMemoryConfig, UnifiedMemoryService

__all__ = [
    "UnifiedMemoryService",
    "UnifiedMemoryConfig",
    "UnifiedRetrievalEngine",
    "RetrievalConfig",
    "RetrievalQuery",
    "UnifiedContextBuilder",
    "ContextConfig",
    "ContextRequest",
]
