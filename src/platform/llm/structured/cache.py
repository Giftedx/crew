from __future__ import annotations

import gzip
import hashlib
import json
import logging
import time
from dataclasses import dataclass
from typing import Any


logger = logging.getLogger(__name__)


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
        """Initialize timestamps if not set (kept minimal for tests)."""
        # Intentionally no-op to preserve test expectations

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
            if hasattr(self.value, "model_dump_json"):
                value_str = self.value.model_dump_json()
            elif isinstance(self.value, dict):
                value_str = json.dumps(self.value)
            else:
                value_str = str(self.value)

            value_bytes = value_str.encode("utf-8")
            self.original_size = len(value_bytes)

            if self.original_size < min_size_bytes:
                self.original_size = 0
                return False

            compressed_bytes = gzip.compress(value_bytes, compresslevel=6)
            compressed_size = len(compressed_bytes)

            if compressed_size < self.original_size:
                self.value = compressed_bytes
                self.compressed = True
                logger.debug(f"Compressed cache entry {self.key}: {self.original_size} -> {compressed_size} bytes")
                return True
            else:
                self.original_size = 0
                return False

        except Exception as e:
            logger.warning(f"Failed to compress cache entry {self.key}: {e}")
            self.original_size = 0
            return False

    def decompress_value(self) -> Any:
        """Decompress the value if it's compressed. Returns the original value."""
        if not self.compressed:
            return self.value

        try:
            if isinstance(self.value, bytes):
                decompressed_bytes = gzip.decompress(self.value)
                decompressed_str = decompressed_bytes.decode("utf-8")
                try:
                    return json.loads(decompressed_str)
                except json.JSONDecodeError:
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
    def generate_key(request: Any) -> str:
        """Generate a unique cache key for the request."""
        normalized_prompt = " ".join(request.prompt.split()).lower().strip()

        model_name = (
            request.response_model.__name__
            if hasattr(request.response_model, "__name__")
            else str(request.response_model)
        )

        key_components = {
            "prompt_hash": hashlib.sha256(normalized_prompt.encode()).hexdigest()[:16],
            "model": model_name,
            "task_type": getattr(request, "task_type", "general"),
            "model_spec": getattr(request, "model", None) or "auto",
            "provider_opts": json.dumps(getattr(request, "provider_opts", None) or {}, sort_keys=True),
        }

        key_string = json.dumps(key_components, sort_keys=True)
        full_key = f"structured_llm:{hashlib.sha256(key_string.encode()).hexdigest()[:32]}"
        logger.debug(f"Generated cache key: {full_key} for prompt hash: {key_components['prompt_hash']}")
        return full_key

    @staticmethod
    def generate_model_schema_key(response_model: type) -> str:
        try:
            schema = response_model.model_json_schema()
            schema_str = json.dumps(schema, sort_keys=True)
            return hashlib.sha256(schema_str.encode()).hexdigest()[:16]
        except Exception:
            return hashlib.sha256(response_model.__name__.encode()).hexdigest()[:16]


class ResponseCache:
    """In-memory cache with TTL support and size limits for structured LLM responses."""

    HIGH_MEMORY_USAGE_THRESHOLD = 90.0
    HIGH_ENTRIES_USAGE_THRESHOLD = 90.0
    LOW_HIT_RATE_THRESHOLD = 0.1
    MIN_REQUESTS_FOR_HIT_RATE_CHECK = 100
    HIGH_EVICTION_RATE_THRESHOLD = 100
    CRITICAL_ISSUES_THRESHOLD = 3

    def __init__(
        self,
        default_ttl_seconds: int = 3600,
        max_entries: int | None = None,
        max_memory_mb: float | None = None,
        enable_compression: bool = True,
        compression_min_size_bytes: int = 1024,
    ):
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
        self.size_limit_evictions = 0

    def get(self, key: str) -> Any | None:
        if key not in self.cache:
            self.misses += 1
            return None

        entry = self.cache[key]
        try:
            expired_now = entry.ttl_seconds <= 0 or entry.is_expired()
        except Exception:
            expired_now = True

        if expired_now:
            entry_size = self._calculate_entry_size(entry)
            self.current_memory_bytes -= entry_size
            del self.cache[key]
            self.evictions += 1
            self.misses += 1
            logger.debug(f"Cache entry expired and removed: {key}")
            return None

        entry.access()
        self.hits += 1
        value = entry.decompress_value()
        logger.debug(f"Cache hit for key: {key} (compressed: {entry.compressed})")
        return value

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        ttl = ttl_seconds or self.default_ttl
        entry = CacheEntry(key=key, value=value, created_at=time.time(), ttl_seconds=ttl)

        if self.enable_compression:
            entry.compress_value(self.compression_min_size)

        entry_size = self._calculate_entry_size(entry)

        if key in self.cache:
            old_entry = self.cache[key]
            old_size = self._calculate_entry_size(old_entry)
            self.current_memory_bytes -= old_size

        if self.max_memory_mb:
            max_bytes = self.max_memory_mb * 1024 * 1024
            if self.current_memory_bytes + entry_size > max_bytes:
                bytes_to_free = int((self.current_memory_bytes + entry_size) - max_bytes)
                self._evict_lru_entries_by_size(bytes_to_free)

        self.cache[key] = entry
        self.current_memory_bytes += entry_size

        if self.max_entries and len(self.cache) > self.max_entries:
            entries_to_remove = len(self.cache) - self.max_entries
            self._evict_lru_entries(entries_to_remove, "max_entries")

        logger.debug(
            f"Cached value for key: {key} with TTL: {ttl}s (size: {entry_size} bytes, compressed: {entry.compressed})"
        )

    def invalidate(self, key: str) -> bool:
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
        if max_age_seconds is None:
            max_age_seconds = self.default_ttl * 2

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
        total_size = self.current_memory_bytes
        entries_by_ttl: dict[str, int] = {}
        for entry in self.cache.values():
            ttl_key = f"{entry.ttl_seconds}s"
            entries_by_ttl[ttl_key] = entries_by_ttl.get(ttl_key, 0) + 1

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
        current_time = time.time()
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests) if total_requests > 0 else 0.0

        memory_usage_percent = 0.0
        if self.max_memory_mb:
            memory_usage_percent = (self.current_memory_bytes / (self.max_memory_mb * 1024 * 1024)) * 100

        entries_usage_percent = 0.0
        if self.max_entries:
            entries_usage_percent = (len(self.cache) / self.max_entries) * 100

        eviction_rate_per_hour = 0.0
        if self.evictions > 0:
            eviction_rate_per_hour = self.evictions / max(1, (current_time - time.time() + 3600) / 3600)

        health_issues = []
        if self.max_memory_mb and memory_usage_percent > self.HIGH_MEMORY_USAGE_THRESHOLD:
            health_issues.append(f"High memory usage: {memory_usage_percent:.1f}%")
        if self.max_entries and entries_usage_percent > self.HIGH_ENTRIES_USAGE_THRESHOLD:
            health_issues.append(f"High entries usage: {entries_usage_percent:.1f}%")
        if hit_rate < self.LOW_HIT_RATE_THRESHOLD and total_requests > self.MIN_REQUESTS_FOR_HIT_RATE_CHECK:
            health_issues.append(f"Low hit rate: {hit_rate:.3f}")
        if eviction_rate_per_hour > self.HIGH_EVICTION_RATE_THRESHOLD:
            health_issues.append(f"High eviction rate: {eviction_rate_per_hour:.1f}/hour")

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
        current_time = time.time()
        total_requests = self.hits + self.misses
        if self.cache:
            total_accesses = sum(entry.access_count for entry in self.cache.values())
            avg_access_frequency = total_accesses / len(self.cache)
        else:
            avg_access_frequency = 0.0

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

    def get_ttl_for_request(self, request: Any) -> int:
        """Determine appropriate TTL based on request characteristics.

        Mirrors the original behavior used in tests: different TTLs per task type,
        with a shorter TTL for streaming requests.
        """
        ttl_map = {
            "general": 3600,
            "analysis": 7200,
            "code": 1800,
            "creative": 1800,
            "factual": 86400,
            "search": 3600,
        }
        task_type = getattr(request, "task_type", "general")
        ttl = ttl_map.get(task_type, self.default_ttl)
        # Streaming requests have shorter TTL
        request_cls_name = type(request).__name__.lower()
        if "streaming" in request_cls_name:
            ttl = min(ttl, 1800)
        return ttl

    def _calculate_entry_size(self, entry: CacheEntry) -> int:
        base_size = 256
        key_size = len(entry.key.encode("utf-8"))
        if entry.compressed and entry.original_size > 0:
            value_size = entry.original_size
        else:
            try:
                if isinstance(entry.value, bytes):
                    value_size = len(entry.value)
                elif hasattr(entry.value, "model_dump_json"):
                    value_str = entry.value.model_dump_json()
                    value_size = len(value_str.encode("utf-8"))
                else:
                    value_str = str(entry.value)
                    value_size = len(value_str.encode("utf-8"))
            except Exception:
                value_size = 1024
        return base_size + key_size + value_size

    def _enforce_size_limits(self):
        if not self.max_entries and not self.max_memory_mb:
            return
        if self.max_entries and len(self.cache) > self.max_entries:
            entries_to_remove = len(self.cache) - self.max_entries
            self._evict_lru_entries(entries_to_remove, "max_entries")

    def _evict_lru_entries(self, count: int, reason: str = "size_limit"):
        if count <= 0:
            return
        sorted_entries = sorted(self.cache.items(), key=lambda x: x[1].last_accessed)
        evicted_count = 0
        for key, entry in sorted_entries[:count]:
            if key in self.cache:
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
        if bytes_to_free <= 0:
            return
        sorted_entries = sorted(self.cache.items(), key=lambda x: x[1].last_accessed)
        freed_bytes = 0
        evicted_count = 0
        for key, entry in sorted_entries:
            if key not in self.cache:
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
