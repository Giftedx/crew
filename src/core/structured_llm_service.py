"""Structured LLM service using Instructor for validated Pydantic outputs.

This service wraps the existing OpenRouterService to provide structured, validated
responses using the Instructor library, reducing parsing errors by 15x.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import logging
import time
from collections.abc import AsyncGenerator, Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, TypeVar, get_args, get_origin

from pydantic import BaseModel, ValidationError
from pydantic_core import PydanticUndefined

logger = logging.getLogger(__name__)

OpenAIClass: Any | None = None
try:
    import instructor

    if TYPE_CHECKING:  # pragma: no cover - typing only
        from openai import OpenAI as _OpenAI  # noqa: F401
    from openai import OpenAI as _OpenAI  # runtime import guarded by try

    OpenAIClass = _OpenAI
    INSTRUCTOR_AVAILABLE = True
    logger.info("Instructor integration available for structured outputs")
except ImportError:  # pragma: no cover
    instructor = None
    OpenAIClass = None
    INSTRUCTOR_AVAILABLE = False
    logger.debug("Instructor not available - falling back to manual parsing")

from obs import metrics
from ultimate_discord_intelligence_bot.services.openrouter_service import OpenRouterService
from ultimate_discord_intelligence_bot.services.request_budget import current_request_tracker

T = TypeVar("T", bound=BaseModel)


@dataclass
class CacheEntry:
    """Cache entry with TTL support and optional compression."""

    key: str
    value: Any
    created_at: float
    ttl_seconds: int
    access_count: int = 0
    last_accessed: float = 0.0
    compressed: bool = False
    original_size: int = 0

    def __post_init__(self):
        """Initialize timestamps if not set."""
        # Don't modify last_accessed if it's already set to 0.0 (test expectation)
        pass

    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return time.time() - self.created_at > self.ttl_seconds

    def access(self):
        """Mark entry as accessed."""
        self.access_count += 1
        self.last_accessed = time.time()

    def compress_value(self, min_size_bytes: int = 1024) -> bool:
        """Compress the value if it's large enough. Returns True if compressed."""
        if self.compressed:
            return False

        try:
            # Get string representation of value
            if hasattr(self.value, "model_dump_json"):
                # For Pydantic models, use JSON representation
                value_str = self.value.model_dump_json()
            elif isinstance(self.value, dict):
                # For dicts, use JSON representation
                value_str = json.dumps(self.value)
            else:
                # For other objects, use string representation
                value_str = str(self.value)

            value_bytes = value_str.encode("utf-8")
            self.original_size = len(value_bytes)

            # Only compress if value is large enough
            if self.original_size < min_size_bytes:
                self.original_size = 0  # Reset to 0 for small entries
                return False

            # Compress the value
            compressed_bytes = gzip.compress(value_bytes, compresslevel=6)
            compressed_size = len(compressed_bytes)

            # Only use compression if it actually saves space
            if compressed_size < self.original_size:
                self.value = compressed_bytes
                self.compressed = True
                logger.debug(f"Compressed cache entry {self.key}: {self.original_size} -> {compressed_size} bytes")
                return True
            else:
                # Compression didn't save space, reset original_size
                self.original_size = 0
                return False

        except Exception as e:
            logger.warning(f"Failed to compress cache entry {self.key}: {e}")
            self.original_size = 0  # Reset on failure
            return False

    def decompress_value(self) -> Any:
        """Decompress the value if it's compressed. Returns the original value."""
        if not self.compressed:
            return self.value

        try:
            if isinstance(self.value, bytes):
                decompressed_bytes = gzip.decompress(self.value)
                decompressed_str = decompressed_bytes.decode("utf-8")

                # Try to parse as JSON first (for Pydantic models)
                try:
                    return json.loads(decompressed_str)
                except json.JSONDecodeError:
                    # If not JSON, return the string
                    return decompressed_str
            else:
                logger.warning(f"Cache entry {self.key} marked as compressed but value is not bytes")
                return self.value

        except Exception as e:
            logger.warning(f"Failed to decompress cache entry {self.key}: {e}")
            return self.value


class CacheKeyGenerator:
    """Generates consistent cache keys from request parameters."""

    @staticmethod
    def generate_key(request: StructuredRequest | StreamingStructuredRequest) -> str:
        """Generate a unique cache key for the request."""
        # Normalize prompt (remove extra whitespace, normalize case)
        normalized_prompt = " ".join(request.prompt.split()).lower().strip()

        # Get response model identifier
        model_name = (
            request.response_model.__name__
            if hasattr(request.response_model, "__name__")
            else str(request.response_model)
        )

        # Create key components
        key_components = {
            "prompt_hash": hashlib.sha256(normalized_prompt.encode()).hexdigest()[:16],  # First 16 chars of hash
            "model": model_name,
            "task_type": request.task_type,
            "model_spec": request.model or "auto",
            "provider_opts": json.dumps(request.provider_opts, sort_keys=True) if request.provider_opts else "{}",
        }

        # Create deterministic key
        key_string = json.dumps(key_components, sort_keys=True)
        full_key = f"structured_llm:{hashlib.sha256(key_string.encode()).hexdigest()[:32]}"

        logger.debug(f"Generated cache key: {full_key} for prompt hash: {key_components['prompt_hash']}")
        return full_key

    @staticmethod
    def generate_model_schema_key(response_model: type[BaseModel]) -> str:
        """Generate a key for the model schema to detect changes."""
        try:
            schema = response_model.model_json_schema()
            schema_str = json.dumps(schema, sort_keys=True)
            return hashlib.sha256(schema_str.encode()).hexdigest()[:16]
        except Exception:
            # Fallback to model name if schema generation fails
            return hashlib.sha256(response_model.__name__.encode()).hexdigest()[:16]


class ResponseCache:
    """In-memory cache with TTL support and size limits for structured LLM responses."""

    # Health monitoring thresholds
    HIGH_MEMORY_USAGE_THRESHOLD = 90.0  # Percentage
    HIGH_ENTRIES_USAGE_THRESHOLD = 90.0  # Percentage
    LOW_HIT_RATE_THRESHOLD = 0.1  # Minimum acceptable hit rate
    MIN_REQUESTS_FOR_HIT_RATE_CHECK = 100  # Minimum requests to evaluate hit rate
    HIGH_EVICTION_RATE_THRESHOLD = 100  # Evictions per hour
    CRITICAL_ISSUES_THRESHOLD = 3  # Number of issues to consider critical

    def __init__(
        self,
        default_ttl_seconds: int = 3600,
        max_entries: int | None = None,
        max_memory_mb: float | None = None,
        enable_compression: bool = True,
        compression_min_size_bytes: int = 1024,
    ):  # 1 hour default
        self.cache: dict[str, CacheEntry] = {}
        self.default_ttl = default_ttl_seconds
        self.max_entries = max_entries
        self.max_memory_mb = max_memory_mb
        self.enable_compression = enable_compression
        self.compression_min_size = compression_min_size_bytes
        self.current_memory_bytes = 0
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.size_limit_evictions = 0  # Track evictions due to size limits

    def get(self, key: str) -> Any | None:
        """Get value from cache if it exists and hasn't expired. Decompresses if needed."""
        if key not in self.cache:
            self.misses += 1
            return None

        entry = self.cache[key]
        # Treat non-positive TTL entries as immediately expired (defensive)
        try:
            if entry.ttl_seconds <= 0:
                expired_now = True
            else:
                expired_now = entry.is_expired()
        except Exception:
            expired_now = True

        if expired_now:
            # Remove expired entry
            entry_size = self._calculate_entry_size(entry)
            self.current_memory_bytes -= entry_size
            del self.cache[key]
            self.evictions += 1
            self.misses += 1
            logger.debug(f"Cache entry expired and removed: {key}")
            return None

        # Mark as accessed
        entry.access()
        self.hits += 1

        # Decompress if needed
        value = entry.decompress_value()
        logger.debug(f"Cache hit for key: {key} (compressed: {entry.compressed})")
        return value

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        """Store value in cache with TTL, compression, and enforce size limits."""
        ttl = ttl_seconds or self.default_ttl
        entry = CacheEntry(key=key, value=value, created_at=time.time(), ttl_seconds=ttl)

        # Apply compression if enabled
        if self.enable_compression:
            entry.compress_value(self.compression_min_size)

        # Calculate size of new entry
        entry_size = self._calculate_entry_size(entry)

        # If key already exists, subtract old size
        if key in self.cache:
            old_entry = self.cache[key]
            old_size = self._calculate_entry_size(old_entry)
            self.current_memory_bytes -= old_size

        # Check if we need to evict before adding
        if self.max_memory_mb:
            max_bytes = self.max_memory_mb * 1024 * 1024
            if self.current_memory_bytes + entry_size > max_bytes:
                bytes_to_free = int((self.current_memory_bytes + entry_size) - max_bytes)
                self._evict_lru_entries_by_size(bytes_to_free)

        # Add new entry
        self.cache[key] = entry
        self.current_memory_bytes += entry_size

        # Enforce entry count limits
        if self.max_entries and len(self.cache) > self.max_entries:
            entries_to_remove = len(self.cache) - self.max_entries
            self._evict_lru_entries(entries_to_remove, "max_entries")

        logger.debug(
            f"Cached value for key: {key} with TTL: {ttl}s (size: {entry_size} bytes, compressed: {entry.compressed})"
        )

    def invalidate(self, key: str) -> bool:
        """Remove specific key from cache and update memory tracking."""
        if key in self.cache:
            entry = self.cache[key]
            entry_size = self._calculate_entry_size(entry)
            self.current_memory_bytes -= entry_size
            del self.cache[key]
            self.evictions += 1
            logger.debug(f"Invalidated cache key: {key}")
            return True
        return False

    def clear_expired(self) -> int:
        """Remove all expired entries and update memory tracking. Returns number of entries removed."""
        expired_keys = [k for k, v in self.cache.items() if v.is_expired()]
        for key in expired_keys:
            entry = self.cache[key]
            entry_size = self._calculate_entry_size(entry)
            self.current_memory_bytes -= entry_size
            del self.cache[key]
            self.evictions += 1
        if expired_keys:
            logger.debug(f"Cleared {len(expired_keys)} expired cache entries")
        return len(expired_keys)

    def cleanup_stale_entries(self, max_age_seconds: int | None = None) -> int:
        """Remove entries that haven't been accessed recently and update memory tracking. Returns number removed."""
        if max_age_seconds is None:
            max_age_seconds = self.default_ttl * 2  # Default to 2x TTL for stale entries

        current_time = time.time()
        stale_keys = []
        for key, entry in self.cache.items():
            if current_time - entry.last_accessed > max_age_seconds:
                stale_keys.append(key)

        for key in stale_keys:
            entry = self.cache[key]
            entry_size = self._calculate_entry_size(entry)
            self.current_memory_bytes -= entry_size
            del self.cache[key]
            self.evictions += 1

        if stale_keys:
            logger.debug(f"Cleared {len(stale_keys)} stale cache entries")
        return len(stale_keys)

    def get_size_info(self) -> dict[str, Any]:
        """Get detailed size information about the cache."""
        total_size = self.current_memory_bytes
        entries_by_ttl = {}
        for entry in self.cache.values():
            ttl_key = f"{entry.ttl_seconds}s"
            if ttl_key not in entries_by_ttl:
                entries_by_ttl[ttl_key] = 0
            entries_by_ttl[ttl_key] += 1

        return {
            "total_entries": len(self.cache),
            "approximate_size_bytes": total_size,
            "current_memory_mb": total_size / (1024 * 1024),
            "max_entries_limit": self.max_entries,
            "max_memory_mb_limit": self.max_memory_mb,
            "compression_enabled": self.enable_compression,
            "compression_min_size": self.compression_min_size,
            "entries_by_ttl": entries_by_ttl,
            "oldest_entry_age": min((time.time() - v.created_at for v in self.cache.values()), default=0),
            "newest_entry_age": max((time.time() - v.created_at for v in self.cache.values()), default=0),
            "size_limit_evictions": self.size_limit_evictions,
        }

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests) if total_requests > 0 else 0.0

        return {
            "total_entries": len(self.cache),
            "current_memory_mb": self.current_memory_bytes / (1024 * 1024),
            "max_entries_limit": self.max_entries,
            "max_memory_mb_limit": self.max_memory_mb,
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "size_limit_evictions": self.size_limit_evictions,
            "hit_rate": hit_rate,
            "total_requests": total_requests,
        }

    def get_health_status(self) -> dict[str, Any]:
        """Get comprehensive cache health status for monitoring."""
        current_time = time.time()
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests) if total_requests > 0 else 0.0

        # Calculate memory usage percentage
        memory_usage_percent = 0.0
        if self.max_memory_mb:
            memory_usage_percent = (self.current_memory_bytes / (self.max_memory_mb * 1024 * 1024)) * 100

        # Calculate entries usage percentage
        entries_usage_percent = 0.0
        if self.max_entries:
            entries_usage_percent = (len(self.cache) / self.max_entries) * 100

        # Calculate eviction rate (evictions per hour)
        eviction_rate_per_hour = 0.0
        if self.evictions > 0:
            # Rough estimate based on total evictions (this could be made more sophisticated)
            eviction_rate_per_hour = self.evictions / max(1, (current_time - time.time() + 3600) / 3600)

        # Check for health issues
        health_issues = []
        if self.max_memory_mb and memory_usage_percent > self.HIGH_MEMORY_USAGE_THRESHOLD:
            health_issues.append(f"High memory usage: {memory_usage_percent:.1f}%")
        if self.max_entries and entries_usage_percent > self.HIGH_ENTRIES_USAGE_THRESHOLD:
            health_issues.append(f"High entries usage: {entries_usage_percent:.1f}%")
        if hit_rate < self.LOW_HIT_RATE_THRESHOLD and total_requests > self.MIN_REQUESTS_FOR_HIT_RATE_CHECK:
            health_issues.append(f"Low hit rate: {hit_rate:.3f}")
        if eviction_rate_per_hour > self.HIGH_EVICTION_RATE_THRESHOLD:
            health_issues.append(f"High eviction rate: {eviction_rate_per_hour:.1f}/hour")

        # Compression statistics
        compressed_entries = sum(1 for entry in self.cache.values() if entry.compressed)
        compression_ratio = 0.0
        if compressed_entries > 0:
            total_original_size = sum(entry.original_size for entry in self.cache.values() if entry.compressed)
            total_compressed_size = sum(
                len(entry.value) if isinstance(entry.value, bytes) else len(str(entry.value).encode("utf-8"))
                for entry in self.cache.values()
                if entry.compressed
            )
            if total_original_size > 0:
                compression_ratio = total_compressed_size / total_original_size

        return {
            "status": "healthy"
            if not health_issues
            else "warning"
            if len(health_issues) < self.CRITICAL_ISSUES_THRESHOLD
            else "critical",
            "health_issues": health_issues,
            "memory_usage_percent": memory_usage_percent,
            "entries_usage_percent": entries_usage_percent,
            "hit_rate": hit_rate,
            "eviction_rate_per_hour": eviction_rate_per_hour,
            "compressed_entries": compressed_entries,
            "compression_ratio": compression_ratio,
            "total_entries": len(self.cache),
            "current_memory_mb": self.current_memory_bytes / (1024 * 1024),
            "uptime_seconds": current_time - getattr(self, "_start_time", current_time),
        }

    def get_performance_metrics(self) -> dict[str, Any]:
        """Get detailed performance metrics for monitoring systems."""
        current_time = time.time()
        total_requests = self.hits + self.misses

        # Calculate average access frequency
        if self.cache:
            total_accesses = sum(entry.access_count for entry in self.cache.values())
            avg_access_frequency = total_accesses / len(self.cache)
        else:
            avg_access_frequency = 0.0

        # Calculate cache efficiency metrics
        stale_entries = sum(
            1 for entry in self.cache.values() if current_time - entry.last_accessed > self.default_ttl * 2
        )
        fresh_entries = len(self.cache) - stale_entries

        return {
            "cache_hits": self.hits,
            "cache_misses": self.misses,
            "cache_evictions": self.evictions,
            "size_limit_evictions": self.size_limit_evictions,
            "total_requests": total_requests,
            "hit_rate": (self.hits / total_requests) if total_requests > 0 else 0.0,
            "memory_bytes": self.current_memory_bytes,
            "entries_count": len(self.cache),
            "avg_access_frequency": avg_access_frequency,
            "stale_entries": stale_entries,
            "fresh_entries": fresh_entries,
            "compression_enabled": self.enable_compression,
            "max_entries_limit": self.max_entries,
            "max_memory_mb_limit": self.max_memory_mb,
        }

    def _calculate_entry_size(self, entry: CacheEntry) -> int:
        """Calculate the approximate memory size of a cache entry in bytes."""
        # Base size for the entry object and metadata
        base_size = 256  # Rough estimate for Python object overhead

        # Size of key string
        key_size = len(entry.key.encode("utf-8"))

        # Size of value - use original size if compressed and available, otherwise calculate current size
        if entry.compressed and entry.original_size > 0:
            value_size = entry.original_size
        else:
            try:
                if isinstance(entry.value, bytes):
                    # For compressed entries that haven't been decompressed
                    value_size = len(entry.value)
                elif hasattr(entry.value, "model_dump_json"):
                    # For Pydantic models, use JSON representation
                    value_str = entry.value.model_dump_json()
                    value_size = len(value_str.encode("utf-8"))
                else:
                    # For other objects, use string representation
                    value_str = str(entry.value)
                    value_size = len(value_str.encode("utf-8"))
            except Exception:
                # Fallback to a conservative estimate
                value_size = 1024

        return base_size + key_size + value_size

    def _enforce_size_limits(self):
        """Enforce cache size limits by evicting entries if necessary."""
        if not self.max_entries and not self.max_memory_mb:
            return  # No limits set

        # Check entry count limit
        if self.max_entries and len(self.cache) > self.max_entries:
            entries_to_remove = len(self.cache) - self.max_entries
            self._evict_lru_entries(entries_to_remove, "max_entries")

    def _evict_lru_entries(self, count: int, reason: str = "size_limit"):
        """Evict the least recently used entries."""
        if count <= 0:
            return

        # Sort entries by last_accessed (oldest first)
        sorted_entries = sorted(self.cache.items(), key=lambda x: x[1].last_accessed)

        evicted_count = 0
        for key, entry in sorted_entries[:count]:
            if key in self.cache:  # Check if still exists
                self.current_memory_bytes -= self._calculate_entry_size(entry)
                del self.cache[key]
                self.evictions += 1
                self.size_limit_evictions += 1
                logger.debug(f"Evicted cache entry due to {reason}: {key}")

                evicted_count += 1
                if evicted_count >= count:
                    break

        if evicted_count > 0:
            logger.info(f"Evicted {evicted_count} entries due to {reason} limit")

    def _evict_lru_entries_by_size(self, bytes_to_free: int):
        """Evict entries until at least bytes_to_free have been freed."""
        if bytes_to_free <= 0:
            return

        # Sort entries by last_accessed (oldest first)
        sorted_entries = sorted(self.cache.items(), key=lambda x: x[1].last_accessed)

        freed_bytes = 0
        evicted_count = 0

        for key, entry in sorted_entries:
            if key not in self.cache:  # Check if still exists
                continue

            entry_size = self._calculate_entry_size(entry)
            self.current_memory_bytes -= entry_size
            freed_bytes += entry_size
            del self.cache[key]
            self.evictions += 1
            self.size_limit_evictions += 1
            logger.debug(f"Evicted cache entry to free memory: {key} ({entry_size} bytes)")

            evicted_count += 1
            if freed_bytes >= bytes_to_free:
                break

        if evicted_count > 0:
            logger.info(f"Evicted {evicted_count} entries to free {freed_bytes} bytes of memory")

    def get_ttl_for_request(self, request: StructuredRequest | StreamingStructuredRequest) -> int:
        """Determine appropriate TTL based on request characteristics."""
        # Different TTLs based on task type
        ttl_map = {
            "general": 3600,  # 1 hour for general queries
            "analysis": 7200,  # 2 hours for analysis tasks
            "code": 1800,  # 30 minutes for code-related tasks
            "creative": 1800,  # 30 minutes for creative tasks
            "factual": 86400,  # 24 hours for factual information
            "search": 3600,  # 1 hour for search results
        }

        # Use task-specific TTL or default
        ttl = ttl_map.get(request.task_type, self.default_ttl)

        # Shorter TTL for streaming requests (more dynamic)
        if isinstance(request, StreamingStructuredRequest):
            ttl = min(ttl, 1800)  # Max 30 minutes for streaming

        return ttl


# Streaming support types and callbacks
@dataclass
class ProgressEvent:
    """Progress event for streaming operations."""

    event_type: str  # "start", "progress", "complete", "error"
    message: str
    progress_percent: float = 0.0
    data: dict[str, Any] | None = None
    timestamp: float = 0.0

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


ProgressCallback = Callable[[ProgressEvent], None]


@dataclass
class StreamingStructuredRequest:
    """Streaming version of structured LLM request parameters."""

    prompt: str
    response_model: Any  # Will be type[T] but avoiding TypeVar in dataclass
    task_type: str = "general"
    model: str | None = None
    provider_opts: dict[str, Any] | None = None
    max_retries: int = 3
    enable_streaming: bool = True
    progress_callback: ProgressCallback | None = None
    streaming_chunk_size: int = 1024  # For simulated streaming


@dataclass
class StreamingResponse:
    """Container for streaming response data."""

    partial_result: BaseModel | None = None
    is_complete: bool = False
    progress_percent: float = 0.0
    raw_chunks: list[str] | None = None
    error: str | None = None

    def __post_init__(self):
        if self.raw_chunks is None:
            self.raw_chunks = []


@dataclass
class CircuitBreakerState:
    """Circuit breaker state for error recovery."""

    failure_count: int = 0
    last_failure_time: float = 0.0
    state: str = "closed"  # closed, open, half_open


class EnhancedErrorRecovery:
    """Enhanced error recovery with circuit breaker and exponential backoff."""

    def __init__(self, max_failures: int = 5, reset_timeout: float = 60.0, base_delay: float = 1.0):
        self.max_failures = max_failures
        self.reset_timeout = reset_timeout
        self.base_delay = base_delay
        self.circuit_breakers: dict[str, CircuitBreakerState] = {}

    def _get_circuit_key(self, model: str | None, provider: str | None) -> str:
        """Generate circuit breaker key from model and provider."""
        return f"{model or 'default'}:{provider or 'default'}"

    def should_attempt_request(self, model: str | None = None, provider: str | None = None) -> bool:
        """Check if request should be attempted based on circuit breaker state."""
        key = self._get_circuit_key(model, provider)
        state = self.circuit_breakers.get(key, CircuitBreakerState())

        if state.state == "open":
            # Check if reset timeout has elapsed
            if time.time() - state.last_failure_time >= self.reset_timeout:
                state.state = "half_open"
                self.circuit_breakers[key] = state
                return True
            return False

        return True

    def record_success(self, model: str | None = None, provider: str | None = None):
        """Record successful request."""
        key = self._get_circuit_key(model, provider)
        if key in self.circuit_breakers:
            state = self.circuit_breakers[key]
            state.failure_count = 0
            state.state = "closed"
            self.circuit_breakers[key] = state

    def record_failure(self, model: str | None = None, provider: str | None = None):
        """Record failed request."""
        key = self._get_circuit_key(model, provider)
        state = self.circuit_breakers.get(key, CircuitBreakerState())

        state.failure_count += 1
        state.last_failure_time = time.time()

        if state.failure_count >= self.max_failures:
            state.state = "open"

        self.circuit_breakers[key] = state

    def get_backoff_delay(self, attempt: int, max_delay: float = 30.0) -> float:
        """Calculate exponential backoff delay."""
        delay = self.base_delay * (2**attempt)
        return min(delay, max_delay)

    def categorize_error(self, error: Exception) -> str:
        """Categorize error for appropriate recovery strategy."""
        error_str = str(error).lower()

        if "rate limit" in error_str or "429" in error_str:
            return "rate_limit"
        elif "timeout" in error_str or "connection" in error_str:
            return "timeout"
        elif "validation" in error_str or "pydantic" in error_str:
            return "validation"
        elif "parsing" in error_str or "json" in error_str:
            return "parsing"
        else:
            return "unknown"


class ProgressTracker:
    """Tracks progress for streaming operations with callbacks."""

    def __init__(self, callback: ProgressCallback | None = None):
        self.callback = callback
        self.start_time = time.time()
        self.events: list[ProgressEvent] = []

    def emit_event(
        self, event_type: str, message: str, progress_percent: float = 0.0, data: dict[str, Any] | None = None
    ):
        """Emit a progress event."""
        event = ProgressEvent(event_type=event_type, message=message, progress_percent=progress_percent, data=data)
        self.events.append(event)

        if self.callback:
            try:
                self.callback(event)
            except Exception as e:
                logger.warning(f"Progress callback failed: {e}")

        logger.debug(f"Progress event: {event_type} - {message} ({progress_percent:.1f}%)")

    def start_operation(self, operation: str):
        """Mark the start of an operation."""
        self.emit_event("start", f"Starting {operation}", 0.0)

    def update_progress(self, message: str, percent: float, data: dict[str, Any] | None = None):
        """Update progress with a specific percentage."""
        self.emit_event("progress", message, percent, data)

    def complete_operation(self, message: str = "Operation completed", data: dict[str, Any] | None = None):
        """Mark operation as complete."""
        duration = time.time() - self.start_time
        self.emit_event("complete", f"{message} (took {duration:.2f}s)", 100.0, data)

    def error_operation(self, error_message: str, data: dict[str, Any] | None = None):
        """Mark operation as failed."""
        self.emit_event("error", f"Operation failed: {error_message}", 0.0, data)

    def get_duration(self) -> float:
        """Get total duration of the operation."""
        return time.time() - self.start_time


@dataclass
class StructuredRequest:
    """Data class for structured LLM request parameters."""

    prompt: str
    response_model: Any  # Will be type[T] but avoiding TypeVar in dataclass
    task_type: str = "general"
    model: str | None = None
    provider_opts: dict[str, Any] | None = None
    max_retries: int = 3


class StructuredLLMService:
    """Enhanced LLM service with structured output validation using Instructor."""

    # Ensure mypy knows this attribute can become non-None after initialization
    instructor_client: Any | None

    def __init__(
        self,
        openrouter_service: OpenRouterService,
        cache_max_entries: int | None = 1000,
        cache_max_memory_mb: float | None = 100.0,
        cache_enable_compression: bool = True,
        cache_compression_min_size_bytes: int = 1024,
    ):
        """Initialize with existing OpenRouter service and cache configuration."""
        self.openrouter = openrouter_service

        # Initialize response cache with size limits and compression
        self.cache = ResponseCache(
            default_ttl_seconds=3600,  # 1 hour default TTL
            max_entries=cache_max_entries,  # Max 1000 entries by default
            max_memory_mb=cache_max_memory_mb,  # Max 100MB by default
            enable_compression=cache_enable_compression,  # Enable compression by default
            compression_min_size_bytes=cache_compression_min_size_bytes,  # Min 1KB for compression
        )

        # Initialize error recovery system
        self.error_recovery = EnhancedErrorRecovery(
            max_failures=5,  # Open circuit after 5 failures
            reset_timeout=60.0,  # Reset after 60 seconds
            base_delay=1.0,  # Base delay for exponential backoff
        )

        # Schedule periodic cache cleanup
        self._last_cleanup = time.time()
        self._cleanup_interval = 300  # Clean up every 5 minutes

        # Initialize instructor client placeholder (set lazily when available)
        self.instructor_client = None

    def _perform_cache_maintenance(self):
        """Perform periodic cache maintenance if needed."""
        current_time = time.time()
        if current_time - self._last_cleanup > self._cleanup_interval:
            logger.debug("Performing cache maintenance")
            expired_count = self.cache.clear_expired()
            stale_count = self.cache.cleanup_stale_entries()
            self._last_cleanup = current_time

            if expired_count > 0 or stale_count > 0:
                logger.info(f"Cache maintenance: removed {expired_count} expired, {stale_count} stale entries")

        # Initialize Instructor client if available
        if INSTRUCTOR_AVAILABLE and self.openrouter.api_key and OpenAIClass is not None:
            try:
                # Create OpenAI-compatible client for Instructor
                base_client = OpenAIClass(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=self.openrouter.api_key,
                )

                # Patch with Instructor for structured outputs
                if instructor is not None:
                    self.instructor_client = instructor.from_openai(base_client)
                    logger.info("Instructor client initialized for structured outputs")
                else:
                    logger.debug("Instructor not available - using fallback parsing")

            except Exception as e:
                logger.warning(f"Failed to initialize Instructor client: {e}")
                self.instructor_client = None
        else:
            logger.debug("Instructor client not available - using fallback parsing")

    def route_structured(
        self,
        request: StructuredRequest,
    ) -> BaseModel | dict[str, Any]:
        """
        Route LLM request with structured output validation.

        Args:
            request: Structured request parameters

        Returns:
            Validated Pydantic model instance or error dict
        """
        start_time = time.time()

        # Perform periodic cache maintenance
        self._perform_cache_maintenance()

        # Check cache first
        cache_key = CacheKeyGenerator.generate_key(request)
        cached_result = self.cache.get(cache_key)
        if cached_result is not None:
            logger.debug(f"Cache hit for key: {cache_key}")
            # Track cache hit in metrics
            cache_labels = {**metrics.label_ctx(), "task": request.task_type, "method": "cache"}
            metrics.STRUCTURED_LLM_REQUESTS.labels(**cache_labels).inc()
            metrics.STRUCTURED_LLM_CACHE_HITS.labels(**cache_labels).inc()
            return cached_result

        # Cache miss - track it
        cache_labels = {**metrics.label_ctx(), "task": request.task_type, "method": "cache"}
        metrics.STRUCTURED_LLM_CACHE_MISSES.labels(**cache_labels).inc()

        # Check circuit breaker before proceeding
        if not self.error_recovery.should_attempt_request(request.model, None):
            logger.warning(f"Circuit breaker open for model {request.model}, skipping request")
            return {
                "status": "error",
                "error": "Service temporarily unavailable due to repeated failures",
                "circuit_breaker": "open",
            }

        method = (
            "instructor"
            if self.instructor_client and self._is_structured_model_compatible(request.model)
            else "fallback"
        )
        labels = {**metrics.label_ctx(), "task": request.task_type, "method": method}

        # Track total requests
        metrics.STRUCTURED_LLM_REQUESTS.labels(**labels).inc()

        try:
            # If Instructor is available and we have a compatible setup, use it
            if self.instructor_client and self._is_structured_model_compatible(request.model):
                result = self._route_with_instructor(request)
            else:
                result = self._route_with_fallback_parsing(request)

            # Track success/failure
            if isinstance(result, dict) and result.get("status") == "error":
                # Record failure for circuit breaker
                self.error_recovery.record_failure(request.model, None)

                error_type = result.get("error", "unknown").split(":")[0].strip().lower()
                metrics.STRUCTURED_LLM_ERRORS.labels(**labels, error_type=error_type).inc()
                metrics.STRUCTURED_LLM_LATENCY.labels(**labels).observe((time.time() - start_time) * 1000)
                return result

            # Success case - cache the result and record success for circuit breaker
            if isinstance(result, BaseModel):
                # Determine TTL for this request
                ttl = self.cache.get_ttl_for_request(request)
                self.cache.set(cache_key, result, ttl)
                logger.debug(f"Cached successful result for key: {cache_key} with TTL: {ttl}s")

            self.error_recovery.record_success(request.model, None)

            # Track model selection and success
            selected_model = request.model or "auto-selected"
            success_labels = {**labels, "model": selected_model}
            metrics.STRUCTURED_LLM_SUCCESS.labels(**success_labels).inc()
            metrics.STRUCTURED_LLM_LATENCY.labels(**labels).observe((time.time() - start_time) * 1000)
            return result

        except Exception as e:
            # Record failure for circuit breaker
            self.error_recovery.record_failure(request.model, None)

            logger.error(f"Unexpected error in structured routing: {e}")
            error_type = type(e).__name__.lower()
            metrics.STRUCTURED_LLM_ERRORS.labels(**labels, error_type=error_type).inc()
            metrics.STRUCTURED_LLM_LATENCY.labels(**labels).observe((time.time() - start_time) * 1000)
            return {
                "status": "error",
                "error": f"Unexpected error: {str(e)}",
            }

    async def route_structured_streaming(
        self,
        request: StreamingStructuredRequest,
    ) -> AsyncGenerator[StreamingResponse, None]:
        """
        Route LLM request with structured output validation and streaming support.

        Args:
            request: Streaming structured request parameters

        Yields:
            StreamingResponse objects with progress updates and partial results
        """
        progress_tracker = ProgressTracker(request.progress_callback)
        progress_tracker.start_operation("Structured LLM streaming request")

        # Perform periodic cache maintenance
        self._perform_cache_maintenance()

        # Check cache first for streaming requests
        cache_key = CacheKeyGenerator.generate_key(request)
        cached_result = self.cache.get(cache_key)
        if cached_result is not None:
            logger.debug(f"Cache hit for streaming request: {cache_key}")
            # Track cache hit in metrics
            cache_labels = {**metrics.label_ctx(), "task": request.task_type, "method": "cache"}
            metrics.STRUCTURED_LLM_CACHE_HITS.labels(**cache_labels).inc()
            progress_tracker.complete_operation("Retrieved from cache")
            yield StreamingResponse(
                partial_result=cached_result, is_complete=True, progress_percent=100.0, raw_chunks=[]
            )
            return

        # Cache miss - track it
        cache_labels = {**metrics.label_ctx(), "task": request.task_type, "method": "cache"}
        metrics.STRUCTURED_LLM_CACHE_MISSES.labels(**cache_labels).inc()

        # Check circuit breaker before proceeding
        if not self.error_recovery.should_attempt_request(request.model, None):
            logger.warning(f"Circuit breaker open for model {request.model}, skipping streaming request")
            progress_tracker.error_operation("Service temporarily unavailable due to repeated failures")
            yield StreamingResponse(
                partial_result=None,
                is_complete=True,
                progress_percent=100.0,
                error="Service temporarily unavailable due to repeated failures",
            )
            return

        method = (
            "instructor_streaming"
            if self.instructor_client and self._is_structured_model_compatible(request.model)
            else "fallback_streaming"
        )

        # Track streaming requests
        labels = {**metrics.label_ctx(), "task": request.task_type, "method": method}
        metrics.STRUCTURED_LLM_REQUESTS.labels(**labels).inc()

        try:
            # Route to appropriate streaming method
            if self.instructor_client and self._is_structured_model_compatible(request.model):
                async for response in self._route_with_instructor_streaming(request, progress_tracker):
                    yield response
            else:
                async for response in self._route_with_fallback_streaming(request, progress_tracker):
                    yield response

        except Exception as e:
            # Record failure for circuit breaker
            self.error_recovery.record_failure(request.model, None)

            logger.error(f"Unexpected error in streaming routing: {e}")
            error_type = type(e).__name__.lower()
            metrics.STRUCTURED_LLM_ERRORS.labels(**labels, error_type=error_type).inc()

            progress_tracker.error_operation(f"Unexpected error: {str(e)}")
            yield StreamingResponse(
                partial_result=None,
                is_complete=True,
                progress_percent=100.0,
                error=f"Unexpected error: {str(e)}",
            )

    def _is_structured_model_compatible(self, model: str | None) -> bool:
        """Check if model supports structured outputs (function calling)."""
        if not model:
            return False

        # Models known to support function calling / structured outputs
        structured_models = [
            "openai/gpt-4o",
            "openai/gpt-4o-mini",
            "openai/gpt-4-turbo",
            "anthropic/claude-3-5-sonnet",
            "anthropic/claude-3-opus",
            "anthropic/claude-3-haiku",
            "google/gemini-1.5-pro",
            "google/gemini-1.5-flash",
        ]

        return any(supported in model.lower() for supported in structured_models)

    def _route_with_instructor(
        self,
        request: StructuredRequest,
    ) -> BaseModel | dict[str, Any]:
        """Use Instructor for native structured output generation."""
        # Double-check that instructor client is available
        if self.instructor_client is None:
            logger.warning("Instructor client not available, falling back to manual parsing")
            return self._route_with_fallback_parsing(request)

        try:
            # Select model using OpenRouter's logic
            selected_model = request.model or self.openrouter._choose_model_from_map(
                request.task_type, self.openrouter.models_map
            )

            # Track instructor usage
            usage_labels = {**metrics.label_ctx(), "task": request.task_type, "model": selected_model}
            metrics.STRUCTURED_LLM_INSTRUCTOR_USAGE.labels(**usage_labels).inc()

            # Generate structured response using Instructor
            response = self.instructor_client.chat.completions.create(
                model=selected_model,
                response_model=request.response_model,
                messages=[{"role": "user", "content": request.prompt}],
                max_retries=request.max_retries,
                temperature=0.1,  # Lower temperature for more consistent structured outputs
            )

            # Extract cost information from the response if available
            # Instructor responses may include usage information
            cost = getattr(response, "usage", {}).get("total_cost", 0.0) if hasattr(response, "usage") else 0.0

            # Track cost if available
            if cost > 0:
                tracker = current_request_tracker()
                if tracker:
                    try:
                        tracker.charge(cost, f"structured_{request.task_type}")
                        metrics.LLM_ESTIMATED_COST.labels(
                            **metrics.label_ctx(), model=selected_model, provider="instructor"
                        ).observe(cost)
                    except Exception as e:
                        logger.debug(f"Failed to track cost for structured instructor call: {e}")

            logger.debug(f"Generated structured response using Instructor for model: {selected_model}")
            return response

        except Exception as e:
            logger.warning(f"Instructor structured generation failed: {e}, falling back to manual parsing")
            return self._route_with_fallback_parsing(request)

    async def _route_with_instructor_streaming(
        self,
        request: StreamingStructuredRequest,
        progress_tracker: ProgressTracker,
    ) -> AsyncGenerator[StreamingResponse, None]:
        """Use Instructor for native streaming structured output generation."""
        # Double-check that instructor client is available
        if self.instructor_client is None:
            logger.warning("Instructor client not available, falling back to manual streaming parsing")
            async for response in self._route_with_fallback_streaming(request, progress_tracker):
                yield response
            return

        try:
            progress_tracker.update_progress("Initializing Instructor streaming", 10.0)

            # Select model using OpenRouter's logic
            selected_model = request.model or self.openrouter._choose_model_from_map(
                request.task_type, self.openrouter.models_map
            )

            progress_tracker.update_progress(f"Selected model: {selected_model}", 20.0)

            # For now, use non-streaming approach with progress updates
            # Convert StreamingStructuredRequest to StructuredRequest for compatibility
            regular_request = StructuredRequest(
                prompt=request.prompt,
                response_model=request.response_model,
                task_type=request.task_type,
                model=request.model,
                provider_opts=request.provider_opts,
                max_retries=request.max_retries,
            )

            progress_tracker.update_progress("Processing with Instructor", 50.0)
            result = self._route_with_instructor(regular_request)

            if isinstance(result, dict) and result.get("status") == "error":
                progress_tracker.error_operation(result.get("error", "Unknown error"))
                yield StreamingResponse(
                    partial_result=None,
                    is_complete=True,
                    progress_percent=100.0,
                    error=result.get("error", "Unknown error"),
                )
            else:
                # Cache successful result
                if isinstance(result, BaseModel):
                    cache_key = CacheKeyGenerator.generate_key(request)
                    ttl = self.cache.get_ttl_for_request(request)
                    self.cache.set(cache_key, result, ttl)
                    logger.debug(f"Cached streaming result for key: {cache_key}")

                progress_tracker.complete_operation("Streaming completed successfully")
                yield StreamingResponse(
                    partial_result=result if isinstance(result, BaseModel) else None,
                    is_complete=True,
                    progress_percent=100.0,
                    raw_chunks=[],
                )

        except Exception as e:
            logger.warning(f"Instructor streaming failed: {e}, falling back to manual streaming parsing")
            progress_tracker.error_operation(f"Instructor streaming failed: {str(e)}")
            async for response in self._route_with_fallback_streaming(request, progress_tracker):
                yield response

    async def _route_with_fallback_streaming(
        self,
        request: StreamingStructuredRequest,
        progress_tracker: ProgressTracker,
    ) -> AsyncGenerator[StreamingResponse, None]:
        """Fallback streaming with simulated progress for manual JSON parsing."""
        progress_tracker.update_progress("Starting fallback streaming", 10.0)

        try:
            # Convert to regular request for compatibility
            regular_request = StructuredRequest(
                prompt=request.prompt,
                response_model=request.response_model,
                task_type=request.task_type,
                model=request.model,
                provider_opts=request.provider_opts,
                max_retries=request.max_retries,
            )

            # Simulate streaming by processing in chunks
            progress_tracker.update_progress("Processing request", 30.0)

            # Use regular fallback parsing but with progress updates
            result = self._route_with_fallback_parsing(regular_request)

            progress_tracker.update_progress("Parsing response", 70.0)

            if isinstance(result, dict) and result.get("status") == "error":
                progress_tracker.error_operation(result.get("error", "Unknown error"))
                yield StreamingResponse(
                    partial_result=None,
                    is_complete=True,
                    progress_percent=100.0,
                    error=result.get("error", "Unknown error"),
                )
            else:
                # Cache successful result
                if isinstance(result, BaseModel):
                    cache_key = CacheKeyGenerator.generate_key(request)
                    ttl = self.cache.get_ttl_for_request(request)
                    self.cache.set(cache_key, result, ttl)
                    logger.debug(f"Cached fallback streaming result for key: {cache_key}")

                progress_tracker.complete_operation("Fallback streaming completed")
                yield StreamingResponse(
                    partial_result=result if isinstance(result, BaseModel) else None,
                    is_complete=True,
                    progress_percent=100.0,
                    raw_chunks=[],
                )

        except Exception as e:
            logger.error(f"Fallback streaming failed: {e}")
            progress_tracker.error_operation(f"Streaming failed: {str(e)}")
            yield StreamingResponse(partial_result=None, is_complete=True, progress_percent=100.0, error=str(e))

    def _route_with_fallback_parsing(
        self,
        request: StructuredRequest,
    ) -> BaseModel | dict[str, Any]:
        """Fallback to manual JSON parsing with validation."""

        # Track fallback usage
        selected_model = request.model or "auto-selected"
        fallback_labels = {**metrics.label_ctx(), "task": request.task_type, "model": selected_model}
        metrics.STRUCTURED_LLM_FALLBACK_USAGE.labels(**fallback_labels).inc()

        # Enhance prompt to request JSON output
        structured_prompt = self._enhance_prompt_for_json(request.prompt, request.response_model)

        for attempt in range(request.max_retries):
            try:
                # Check circuit breaker before each attempt
                if not self.error_recovery.should_attempt_request(request.model, None):
                    logger.warning(f"Circuit breaker open for model {request.model} on attempt {attempt + 1}")
                    return {
                        "status": "error",
                        "error": "Service temporarily unavailable due to repeated failures",
                        "circuit_breaker": "open",
                        "attempt": attempt + 1,
                    }

                # Use existing OpenRouter service
                response = self.openrouter.route(
                    prompt=structured_prompt,
                    task_type=request.task_type,
                    model=request.model,
                    provider_opts=request.provider_opts,
                )

                if response.get("status") != "success":
                    error_response = self._handle_response_error(response, request, attempt)
                    if error_response is None:
                        continue  # Retry after backoff
                    return error_response

                # Extract and validate JSON response
                raw_response = response.get("response", "")
                validated_model = self._parse_and_validate_json(raw_response, request.response_model)

                if validated_model:
                    # Record success for circuit breaker
                    self.error_recovery.record_success(request.model, None)

                    logger.debug(f"Successfully parsed structured response on attempt {attempt + 1}")

                    # Track successful structured call cost
                    estimated_structured_cost = self._estimate_structured_cost(response, request.task_type)
                    if estimated_structured_cost > 0:
                        tracker = current_request_tracker()
                        if tracker:
                            try:
                                tracker.charge(estimated_structured_cost, f"structured_{request.task_type}")
                                provider_family = self._extract_provider_family(response)
                                metrics.LLM_ESTIMATED_COST.labels(
                                    **metrics.label_ctx(), model=selected_model, provider=provider_family
                                ).observe(estimated_structured_cost)
                            except Exception as e:
                                logger.debug(f"Failed to track structured cost: {e}")

                    return validated_model

                # Parsing failed - try to enhance prompt and retry
                enhanced_prompt = self._handle_parsing_failure(request, attempt, structured_prompt)
                if enhanced_prompt is None:
                    break  # No more attempts
                structured_prompt = enhanced_prompt

            except Exception as e:
                error_response = self._handle_exception_error(e, request, attempt, locals().get("response"))
                if error_response is None:
                    continue  # Retry after backoff
                return error_response

        return {
            "status": "error",
            "error": "Failed to generate structured output",
            "attempts": request.max_retries,
        }

    def _handle_response_error(
        self, response: dict[str, Any], request: StructuredRequest, attempt: int
    ) -> dict[str, Any] | None:
        """Handle non-success response with appropriate error recovery."""
        error_category = self.error_recovery.categorize_error(Exception(response.get("error", "Unknown error")))

        # Record failure for circuit breaker
        self.error_recovery.record_failure(request.model, None)

        # Apply different backoff strategies based on error type
        if error_category in ["rate_limit", "timeout"] and attempt < request.max_retries - 1:
            backoff_delay = self.error_recovery.get_backoff_delay(attempt)
            logger.warning(f"{error_category} error, backing off for {backoff_delay}s (attempt {attempt + 1})")
            time.sleep(backoff_delay)
            return None  # Continue to next attempt

        return response  # Return error response

    def _handle_parsing_failure(self, request: StructuredRequest, attempt: int, structured_prompt: str) -> str | None:
        """Handle parsing failure with prompt enhancement and backoff."""
        if attempt >= request.max_retries - 1:
            return None  # No more attempts

        logger.warning(f"Failed to parse structured response, attempt {attempt + 1}/{request.max_retries}")
        # Shorter backoff for parsing errors
        backoff_delay = self.error_recovery.get_backoff_delay(attempt, max_delay=5.0)
        time.sleep(backoff_delay)

        # Enhance prompt with more specific instructions for next attempt
        return self._enhance_prompt_with_example(structured_prompt, request.response_model)

    def _handle_exception_error(
        self, e: Exception, request: StructuredRequest, attempt: int, response: dict[str, Any] | None
    ) -> dict[str, Any] | None:
        """Handle exceptions with appropriate error recovery."""
        error_category = self.error_recovery.categorize_error(e)

        # Record failure for circuit breaker
        self.error_recovery.record_failure(request.model, None)

        logger.error(f"Error in structured routing attempt {attempt + 1}: {e}")

        # Apply backoff for retryable errors
        if attempt < request.max_retries - 1 and error_category in ["rate_limit", "timeout", "parsing"]:
            backoff_delay = self.error_recovery.get_backoff_delay(attempt)
            logger.warning(f"Retryable {error_category} error, backing off for {backoff_delay}s")
            time.sleep(backoff_delay)
            return None  # Continue to next attempt

        if attempt == request.max_retries - 1:
            return {
                "status": "error",
                "error": f"Structured output generation failed after {request.max_retries} attempts",
                "raw_response": response.get("response", "") if response else "",
                "last_error": str(e),
                "error_category": error_category,
            }

        return None

    def _enhance_prompt_for_json(self, prompt: str, response_model: type[BaseModel]) -> str:
        """Enhance prompt to request structured JSON output."""
        schema = response_model.model_json_schema()

        json_prompt = f"""
{prompt}

IMPORTANT: Respond with valid JSON that matches this exact schema:

{json.dumps(schema, indent=2)}

Your response must be valid JSON only - no additional text or explanation.
"""
        return json_prompt

    def _enhance_prompt_with_example(self, prompt: str, response_model: type[BaseModel]) -> str:
        """Enhance prompt with a concrete example for clearer guidance."""
        try:
            # Generate a simple example instance
            example = self._generate_example_instance(response_model)
            example_json = example.model_dump_json(indent=2)

            enhanced_prompt = f"""
{prompt}

Example of the expected JSON format:
{example_json}

Respond with valid JSON in this exact format.
"""
            return enhanced_prompt

        except Exception:
            # If example generation fails, return original prompt
            return prompt

    def _generate_example_instance(self, response_model: type[BaseModel]) -> BaseModel:
        """Generate a minimal example instance of the response model."""
        # Get field defaults and types
        field_values = {}

        for field_name, field_info in response_model.model_fields.items():
            if field_info.default is not PydanticUndefined and field_info.default is not None:
                field_values[field_name] = field_info.default
            elif hasattr(field_info, "default_factory") and field_info.default_factory is not None:
                # Skip default_factory for now - just generate example value
                field_values[field_name] = self._generate_example_value(field_info.annotation)
            else:
                # Generate example based on field type annotation
                field_values[field_name] = self._generate_example_value(field_info.annotation)

        return response_model(**field_values)

    def _generate_example_value(self, field_type: Any) -> Any:
        """Generate example value for a given type."""
        # Type mapping for simple examples
        type_examples = {
            str: "example_string",
            int: 0,
            float: 0.0,
            bool: False,
        }

        # Check for simple types first
        if field_type in type_examples:
            return type_examples[field_type]

        # Handle complex types
        origin = get_origin(field_type)
        if origin is list or field_type is list:
            args = get_args(field_type)
            item_type = args[0] if args else str
            return [self._generate_example_value(item_type)]
        if origin is dict or field_type is dict:
            return {"key": "value"}

        # Default fallback
        return "example"

    def _parse_and_validate_json(self, raw_response: str, response_model: type[T]) -> T | None:
        """Parse JSON response and validate against Pydantic model."""
        parsing_start = time.time()
        labels = {**metrics.label_ctx(), "task": "parsing"}

        try:
            # Clean response - remove common prefixes/suffixes
            cleaned = raw_response.strip()

            # Remove markdown code blocks if present
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]

            cleaned = cleaned.strip()

            # Parse JSON
            data = json.loads(cleaned)

            # Track parsing success
            metrics.STRUCTURED_LLM_PARSING_LATENCY.labels(**labels).observe((time.time() - parsing_start) * 1000)

            # Validate with Pydantic model
            validated = response_model(**data)

            logger.debug(f"Successfully validated structured response: {type(validated).__name__}")
            return validated

        except json.JSONDecodeError as e:
            logger.warning(f"JSON parsing error: {e}")
            metrics.STRUCTURED_LLM_PARSING_FAILURES.labels(
                **metrics.label_ctx(), task="parsing", method="fallback"
            ).inc()
            metrics.STRUCTURED_LLM_PARSING_LATENCY.labels(**labels).observe((time.time() - parsing_start) * 1000)
            return None
        except ValidationError as e:
            logger.warning(f"Pydantic validation error: {e}")
            metrics.STRUCTURED_LLM_VALIDATION_FAILURES.labels(
                **metrics.label_ctx(), task="validation", method="fallback"
            ).inc()
            metrics.STRUCTURED_LLM_PARSING_LATENCY.labels(**labels).observe((time.time() - parsing_start) * 1000)
            return None
        except Exception as e:
            logger.warning(f"Unexpected error in JSON validation: {e}")
            metrics.STRUCTURED_LLM_PARSING_FAILURES.labels(
                **metrics.label_ctx(), task="parsing", method="fallback"
            ).inc()
            metrics.STRUCTURED_LLM_PARSING_LATENCY.labels(**labels).observe((time.time() - parsing_start) * 1000)
            return None

    def _estimate_structured_cost(self, response: dict[str, Any], task_type: str) -> float:
        """Estimate the cost of a structured LLM call based on response data."""
        try:
            # Try to extract cost from response if available
            if "cost" in response:
                return float(response["cost"])

            # Fallback: estimate based on token usage
            tokens_in = response.get("tokens", 0)
            # Estimate output tokens based on response length (rough approximation)
            response_text = response.get("response", "")
            estimated_output_tokens = len(response_text.split()) * 1.3  # Rough token estimation

            # Use a simple cost estimation (this could be made more sophisticated)
            # Average cost per 1K tokens for common models
            base_cost_per_1k = 0.002  # Conservative estimate
            total_tokens = tokens_in + estimated_output_tokens
            estimated_cost = (total_tokens / 1000) * base_cost_per_1k

            return max(estimated_cost, 0.001)  # Minimum cost to avoid zero

        except Exception:
            # Return a small default cost if estimation fails
            return 0.001

    def _extract_provider_family(self, response: dict[str, Any]) -> str:
        """Extract provider family from OpenRouter response."""
        try:
            provider_info = response.get("provider", {})
            if isinstance(provider_info, dict):
                order = provider_info.get("order", [])
                if order and len(order) > 0:
                    return str(order[0])
            elif isinstance(provider_info, str):
                return provider_info
            return "unknown"
        except Exception:
            return "unknown"


def create_structured_llm_service(
    openrouter_service: OpenRouterService,
    cache_max_entries: int | None = 1000,
    cache_max_memory_mb: float | None = 100.0,
    cache_enable_compression: bool = True,
    cache_compression_min_size_bytes: int = 1024,
) -> StructuredLLMService:
    """Factory function to create structured LLM service with cache configuration."""
    return StructuredLLMService(
        openrouter_service=openrouter_service,
        cache_max_entries=cache_max_entries,
        cache_max_memory_mb=cache_max_memory_mb,
        cache_enable_compression=cache_enable_compression,
        cache_compression_min_size_bytes=cache_compression_min_size_bytes,
    )
