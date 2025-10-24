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
    # Message batching
    "MessageBatcher",
    "SmartMessageBatcher",
    "MessageBatch",
    "BatchedMessage",
    "BatchConfig",
    "create_message_batcher",
    # Semantic caching
    "SemanticCache",
    "AdaptiveSemanticCache",
    "CacheEntry",
    "SemanticCacheConfig",
    "create_semantic_cache",
    # Embedding optimization
    "EmbeddingOptimizer",
    "EmbeddingCacheEntry",
    "EmbeddingConfig",
    "create_embedding_optimizer",
    # Performance monitoring
    "PerformanceManager",
    "PerformanceMetrics",
    "ProcessingMetrics",
    "OptimizationConfig",
    "create_performance_manager",
    # Integration
    "DiscordAIOptimizationSystem",
    "create_discord_ai_optimization_system",
    # Configuration
    "PerformanceOptimizationConfig",
    "PerformanceConfigManager",
    "get_performance_config",
    "load_performance_config",
    "update_performance_config",
    "validate_performance_config",
    "get_environment_optimized_config",
]
