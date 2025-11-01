"""
Performance optimization module for Discord AI processing.

This module provides comprehensive performance optimization capabilities including:
- Message batching for efficient processing
- Semantic caching for reduced redundancy
- Embedding optimization for faster vector operations
- Performance monitoring and adaptive optimization
"""

from .config import (
    PerformanceConfigManager,
    PerformanceOptimizationConfig,
    get_environment_optimized_config,
    get_performance_config,
    load_performance_config,
    update_performance_config,
    validate_performance_config,
)
from .embedding_optimizer import EmbeddingCacheEntry, EmbeddingConfig, EmbeddingOptimizer, create_embedding_optimizer
from .message_batcher import (
    BatchConfig,
    BatchedMessage,
    MessageBatch,
    MessageBatcher,
    SmartMessageBatcher,
    create_message_batcher,
)
from .optimization_integration import DiscordAIOptimizationSystem, create_discord_ai_optimization_system
from .performance_manager import (
    OptimizationConfig,
    PerformanceManager,
    PerformanceMetrics,
    ProcessingMetrics,
    create_performance_manager,
)
from .semantic_cache import AdaptiveSemanticCache, CacheEntry, SemanticCache, SemanticCacheConfig, create_semantic_cache


__all__ = [
    "AdaptiveSemanticCache",
    "BatchConfig",
    "BatchedMessage",
    "CacheEntry",
    # Integration
    "DiscordAIOptimizationSystem",
    "EmbeddingCacheEntry",
    "EmbeddingConfig",
    # Embedding optimization
    "EmbeddingOptimizer",
    "MessageBatch",
    # Message batching
    "MessageBatcher",
    "OptimizationConfig",
    "PerformanceConfigManager",
    # Performance monitoring
    "PerformanceManager",
    "PerformanceMetrics",
    # Configuration
    "PerformanceOptimizationConfig",
    "ProcessingMetrics",
    # Semantic caching
    "SemanticCache",
    "SemanticCacheConfig",
    "SmartMessageBatcher",
    "create_discord_ai_optimization_system",
    "create_embedding_optimizer",
    "create_message_batcher",
    "create_performance_manager",
    "create_semantic_cache",
    "get_environment_optimized_config",
    "get_performance_config",
    "load_performance_config",
    "update_performance_config",
    "validate_performance_config",
]
