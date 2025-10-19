"""
Advanced memory management system for multi-modal embeddings and optimization.

This module provides comprehensive memory management capabilities including
multi-modal embeddings, advanced compaction algorithms, and cross-tenant
similarity prevention for optimal vector storage and retrieval.
"""

from .advanced_compaction import (
    AdvancedMemoryCompactor,
    CompactionConfig,
    CompactionMetrics,
    CompactionStrategy,
    CompactionTrigger,
    MemoryEntry,
)
from .cross_tenant_similarity import (
    CrossTenantConfig,
    CrossTenantSimilarityDetector,
    IsolationStrategy,
    SimilarityDetectionMethod,
    SimilarityViolation,
    TenantIsolationMetrics,
)
from .multimodal_embeddings import (
    EmbeddingConfig,
    EmbeddingModel,
    EmbeddingResult,
    EmbeddingType,
    MultiModalEmbedding,
    MultiModalEmbeddingGenerator,
)

__all__ = [
    # Advanced compaction exports
    "AdvancedMemoryCompactor",
    "CompactionConfig",
    "CompactionMetrics",
    "CompactionStrategy",
    "CompactionTrigger",
    "MemoryEntry",
    # Cross-tenant similarity exports
    "CrossTenantConfig",
    "CrossTenantSimilarityDetector",
    "IsolationStrategy",
    "SimilarityDetectionMethod",
    "SimilarityViolation",
    "TenantIsolationMetrics",
    # Multi-modal embeddings exports
    "EmbeddingConfig",
    "EmbeddingModel",
    "EmbeddingResult",
    "EmbeddingType",
    "MultiModalEmbedding",
    "MultiModalEmbeddingGenerator",
]
