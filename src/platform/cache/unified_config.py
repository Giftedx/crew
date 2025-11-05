"""Unified Cache Configuration - Single source of truth for all caching settings.

This module consolidates all cache configuration into a single, well-structured
system that replaces scattered cache settings across the codebase.

Design Principles:
- Single source of truth for cache settings
- Environment variable standardization
- Backward compatibility with existing systems
- Type-safe configuration with validation
- Graceful degradation on missing dependencies

Migration Path:
1. Import this config in new code
2. Existing configs marked deprecated (Phase 2)
3. Gradual migration of services (Phase 3)
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


logger = logging.getLogger(__name__)


class CacheTTLTier(Enum):
    """Standardized TTL tiers for consistent cache expiration."""

    VERY_SHORT = 60  # 1 minute - real-time data
    SHORT = 300  # 5 minutes - frequently changing data
    MEDIUM = 3600  # 1 hour - moderate stability
    LONG = 86400  # 24 hours - stable data
    VERY_LONG = 604800  # 7 days - rarely changing data
    PERSISTENT = None  # No expiration (manual cleanup)


class CacheBackend(Enum):
    """Available cache backend types."""

    MEMORY = "memory"  # L1 - In-memory dict
    REDIS = "redis"  # L2 - Redis server
    SEMANTIC = "semantic"  # L3 - Vector similarity
    DISK = "disk"  # File-based persistence


@dataclass
class RedisConfig:
    """Redis (L2) cache configuration."""

    enabled: bool = True
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: str | None = None
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    max_connections: int = 50
    decode_responses: bool = False  # Handle serialization manually
    ssl: bool = False
    ssl_ca_certs: str | None = None

    @classmethod
    def from_env(cls) -> RedisConfig:
        """Load Redis config from environment variables."""
        return cls(
            enabled=os.getenv("REDIS_ENABLED", "true").lower() == "true",
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=int(os.getenv("REDIS_DB", "0")),
            password=os.getenv("REDIS_PASSWORD"),
            socket_timeout=int(os.getenv("REDIS_SOCKET_TIMEOUT", "5")),
            socket_connect_timeout=int(os.getenv("REDIS_CONNECT_TIMEOUT", "5")),
            max_connections=int(os.getenv("REDIS_MAX_CONNECTIONS", "50")),
            ssl=os.getenv("REDIS_SSL", "false").lower() == "true",
            ssl_ca_certs=os.getenv("REDIS_SSL_CA_CERTS"),
        )


@dataclass
class SemanticCacheConfig:
    """Semantic (L3) cache configuration."""

    enabled: bool = True
    similarity_threshold: float = 0.8
    max_results: int = 10
    embedding_model: str = "text-embedding-ada-002"
    vector_dimension: int = 1536
    use_qdrant: bool = True
    collection_name: str = "semantic_cache"
    default_ttl: int = CacheTTLTier.LONG.value

    @classmethod
    def from_env(cls) -> SemanticCacheConfig:
        """Load semantic cache config from environment variables."""
        return cls(
            enabled=os.getenv("SEMANTIC_CACHE_ENABLED", "true").lower() == "true",
            similarity_threshold=float(os.getenv("SEMANTIC_CACHE_SIMILARITY", "0.8")),
            max_results=int(os.getenv("SEMANTIC_CACHE_MAX_RESULTS", "10")),
            embedding_model=os.getenv("SEMANTIC_CACHE_EMBEDDING_MODEL", "text-embedding-ada-002"),
            vector_dimension=int(os.getenv("SEMANTIC_CACHE_VECTOR_DIM", "1536")),
            use_qdrant=os.getenv("SEMANTIC_CACHE_USE_QDRANT", "true").lower() == "true",
            collection_name=os.getenv("SEMANTIC_CACHE_COLLECTION", "semantic_cache"),
            default_ttl=int(os.getenv("SEMANTIC_CACHE_TTL", str(CacheTTLTier.LONG.value))),
        )


@dataclass
class MemoryCacheConfig:
    """Memory (L1) cache configuration."""

    enabled: bool = True
    max_size: int = 10000  # Maximum number of entries
    max_memory_mb: int = 512  # Maximum memory usage in MB
    eviction_policy: str = "lru"  # lru, lfu, fifo
    ttl_check_interval: int = 60  # Seconds between TTL checks
    default_ttl: int = CacheTTLTier.SHORT.value

    @classmethod
    def from_env(cls) -> MemoryCacheConfig:
        """Load memory cache config from environment variables."""
        return cls(
            enabled=os.getenv("MEMORY_CACHE_ENABLED", "true").lower() == "true",
            max_size=int(os.getenv("MEMORY_CACHE_MAX_SIZE", "10000")),
            max_memory_mb=int(os.getenv("MEMORY_CACHE_MAX_MB", "512")),
            eviction_policy=os.getenv("MEMORY_CACHE_EVICTION", "lru"),
            ttl_check_interval=int(os.getenv("MEMORY_CACHE_TTL_CHECK", "60")),
            default_ttl=int(os.getenv("MEMORY_CACHE_TTL", str(CacheTTLTier.SHORT.value))),
        )


@dataclass
class DomainCacheSettings:
    """Domain-specific cache settings (transcription, analysis, etc.)."""

    # Transcription cache
    transcription_enabled: bool = True
    transcription_ttl: int = CacheTTLTier.VERY_LONG.value
    transcription_max_size_gb: int = 10
    transcription_compression: bool = True

    # Analysis cache
    analysis_enabled: bool = True
    analysis_ttl: int = CacheTTLTier.LONG.value
    analysis_max_entries: int = 100
    analysis_persistence: bool = True

    # LLM response cache
    llm_response_enabled: bool = True
    llm_response_ttl: int = CacheTTLTier.MEDIUM.value
    llm_response_max_size: int = 5000

    # Tool execution cache
    tool_execution_enabled: bool = True
    tool_execution_ttl: int = CacheTTLTier.SHORT.value

    # Routing decision cache
    routing_decision_enabled: bool = True
    routing_decision_ttl: int = CacheTTLTier.SHORT.value

    @classmethod
    def from_env(cls) -> DomainCacheSettings:
        """Load domain cache settings from environment variables."""
        return cls(
            # Transcription
            transcription_enabled=os.getenv("CACHE_TRANSCRIPTION_ENABLED", "true").lower() == "true",
            transcription_ttl=int(os.getenv("CACHE_TRANSCRIPTION_TTL", str(CacheTTLTier.VERY_LONG.value))),
            transcription_max_size_gb=int(os.getenv("CACHE_TRANSCRIPTION_MAX_GB", "10")),
            transcription_compression=os.getenv("CACHE_TRANSCRIPTION_COMPRESSION", "true").lower() == "true",
            # Analysis
            analysis_enabled=os.getenv("CACHE_ANALYSIS_ENABLED", "true").lower() == "true",
            analysis_ttl=int(os.getenv("CACHE_ANALYSIS_TTL", str(CacheTTLTier.LONG.value))),
            analysis_max_entries=int(os.getenv("CACHE_ANALYSIS_MAX_ENTRIES", "100")),
            analysis_persistence=os.getenv("CACHE_ANALYSIS_PERSISTENCE", "true").lower() == "true",
            # LLM Response
            llm_response_enabled=os.getenv("CACHE_LLM_ENABLED", "true").lower() == "true",
            llm_response_ttl=int(os.getenv("CACHE_LLM_TTL", str(CacheTTLTier.MEDIUM.value))),
            llm_response_max_size=int(os.getenv("CACHE_LLM_MAX_SIZE", "5000")),
            # Tool Execution
            tool_execution_enabled=os.getenv("CACHE_TOOL_ENABLED", "true").lower() == "true",
            tool_execution_ttl=int(os.getenv("CACHE_TOOL_TTL", str(CacheTTLTier.SHORT.value))),
            # Routing
            routing_decision_enabled=os.getenv("CACHE_ROUTING_ENABLED", "true").lower() == "true",
            routing_decision_ttl=int(os.getenv("CACHE_ROUTING_TTL", str(CacheTTLTier.SHORT.value))),
        )


@dataclass
class CacheMetricsConfig:
    """Cache metrics and monitoring configuration."""

    enabled: bool = True
    prometheus_enabled: bool = True
    logging_enabled: bool = True
    stats_interval: int = 60  # Seconds between stats logging
    export_to_file: bool = False
    export_file_path: str = "cache/metrics/cache_stats.json"

    @classmethod
    def from_env(cls) -> CacheMetricsConfig:
        """Load metrics config from environment variables."""
        return cls(
            enabled=os.getenv("CACHE_METRICS_ENABLED", "true").lower() == "true",
            prometheus_enabled=os.getenv("CACHE_METRICS_PROMETHEUS", "true").lower() == "true",
            logging_enabled=os.getenv("CACHE_METRICS_LOGGING", "true").lower() == "true",
            stats_interval=int(os.getenv("CACHE_METRICS_INTERVAL", "60")),
            export_to_file=os.getenv("CACHE_METRICS_EXPORT", "false").lower() == "true",
            export_file_path=os.getenv("CACHE_METRICS_FILE", "cache/metrics/cache_stats.json"),
        )


@dataclass
class UnifiedCacheConfiguration:
    """Unified cache configuration - single source of truth.

    This configuration consolidates all caching settings into one place,
    replacing scattered cache configs across the codebase.

    Attributes:
        enabled: Global cache enable/disable switch
        memory: L1 memory cache configuration
        redis: L2 Redis cache configuration
        semantic: L3 semantic cache configuration
        domain: Domain-specific cache settings
        metrics: Metrics and monitoring configuration
        auto_tier_selection: Enable intelligent tier selection
        graceful_degradation: Continue without failed backends
    """

    enabled: bool = True
    memory: MemoryCacheConfig = field(default_factory=MemoryCacheConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    semantic: SemanticCacheConfig = field(default_factory=SemanticCacheConfig)
    domain: DomainCacheSettings = field(default_factory=DomainCacheSettings)
    metrics: CacheMetricsConfig = field(default_factory=CacheMetricsConfig)

    # Advanced features
    auto_tier_selection: bool = True
    graceful_degradation: bool = True
    enable_compression: bool = True
    enable_key_validation: bool = True

    @classmethod
    def from_env(cls) -> UnifiedCacheConfiguration:
        """Load complete cache configuration from environment variables.

        Returns:
            UnifiedCacheConfiguration with all settings loaded from env
        """
        return cls(
            enabled=os.getenv("CACHE_ENABLED", "true").lower() == "true",
            memory=MemoryCacheConfig.from_env(),
            redis=RedisConfig.from_env(),
            semantic=SemanticCacheConfig.from_env(),
            domain=DomainCacheSettings.from_env(),
            metrics=CacheMetricsConfig.from_env(),
            auto_tier_selection=os.getenv("CACHE_AUTO_TIER", "true").lower() == "true",
            graceful_degradation=os.getenv("CACHE_GRACEFUL_DEGRADATION", "true").lower() == "true",
            enable_compression=os.getenv("CACHE_COMPRESSION", "true").lower() == "true",
            enable_key_validation=os.getenv("CACHE_KEY_VALIDATION", "true").lower() == "true",
        )

    def get_ttl_for_domain(self, domain: str) -> int:
        """Get TTL for a specific domain.

        Args:
            domain: Cache domain (transcription, analysis, llm, tool, routing)

        Returns:
            TTL in seconds for the domain
        """
        domain_map = {
            "transcription": self.domain.transcription_ttl,
            "analysis": self.domain.analysis_ttl,
            "llm": self.domain.llm_response_ttl,
            "tool": self.domain.tool_execution_ttl,
            "routing": self.domain.routing_decision_ttl,
        }
        return domain_map.get(domain, CacheTTLTier.MEDIUM.value)

    def is_domain_enabled(self, domain: str) -> bool:
        """Check if caching is enabled for a specific domain.

        Args:
            domain: Cache domain to check

        Returns:
            True if domain caching is enabled
        """
        if not self.enabled:
            return False

        domain_map = {
            "transcription": self.domain.transcription_enabled,
            "analysis": self.domain.analysis_enabled,
            "llm": self.domain.llm_response_enabled,
            "tool": self.domain.tool_execution_enabled,
            "routing": self.domain.routing_decision_enabled,
        }
        return domain_map.get(domain, True)

    def get_active_backends(self) -> list[CacheBackend]:
        """Get list of enabled cache backends.

        Returns:
            List of CacheBackend enums for enabled backends
        """
        backends = []
        if self.memory.enabled:
            backends.append(CacheBackend.MEMORY)
        if self.redis.enabled:
            backends.append(CacheBackend.REDIS)
        if self.semantic.enabled:
            backends.append(CacheBackend.SEMANTIC)
        return backends

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary for serialization.

        Returns:
            Dictionary representation of configuration
        """
        return {
            "enabled": self.enabled,
            "memory": {
                "enabled": self.memory.enabled,
                "max_size": self.memory.max_size,
                "max_memory_mb": self.memory.max_memory_mb,
                "eviction_policy": self.memory.eviction_policy,
                "default_ttl": self.memory.default_ttl,
            },
            "redis": {
                "enabled": self.redis.enabled,
                "host": self.redis.host,
                "port": self.redis.port,
                "db": self.redis.db,
                "max_connections": self.redis.max_connections,
            },
            "semantic": {
                "enabled": self.semantic.enabled,
                "similarity_threshold": self.semantic.similarity_threshold,
                "collection_name": self.semantic.collection_name,
                "default_ttl": self.semantic.default_ttl,
            },
            "domain": {
                "transcription": {
                    "enabled": self.domain.transcription_enabled,
                    "ttl": self.domain.transcription_ttl,
                },
                "analysis": {
                    "enabled": self.domain.analysis_enabled,
                    "ttl": self.domain.analysis_ttl,
                },
                "llm": {
                    "enabled": self.domain.llm_response_enabled,
                    "ttl": self.domain.llm_response_ttl,
                },
            },
            "metrics": {
                "enabled": self.metrics.enabled,
                "prometheus_enabled": self.metrics.prometheus_enabled,
            },
            "active_backends": [b.value for b in self.get_active_backends()],
        }


# Global configuration singleton
_global_cache_config: UnifiedCacheConfiguration | None = None


def get_unified_cache_config() -> UnifiedCacheConfiguration:
    """Get the global unified cache configuration instance.

    Returns:
        UnifiedCacheConfiguration singleton
    """
    global _global_cache_config
    if _global_cache_config is None:
        _global_cache_config = UnifiedCacheConfiguration.from_env()
        logger.info(
            f"Unified cache config initialized: {len(_global_cache_config.get_active_backends())} backends active"
        )
    return _global_cache_config


def reset_unified_cache_config() -> None:
    """Reset the global cache configuration (mainly for testing)."""
    global _global_cache_config
    _global_cache_config = None


# Backward compatibility helpers
def get_cache_ttl(domain: str = "default") -> int:
    """Get cache TTL for backward compatibility.

    Args:
        domain: Cache domain

    Returns:
        TTL in seconds
    """
    config = get_unified_cache_config()
    return config.get_ttl_for_domain(domain)


def is_cache_enabled(domain: str = "default") -> bool:
    """Check if cache is enabled for backward compatibility.

    Args:
        domain: Cache domain

    Returns:
        True if caching is enabled
    """
    config = get_unified_cache_config()
    return config.is_domain_enabled(domain)
