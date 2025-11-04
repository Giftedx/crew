"""Configuration caching for performance optimization."""

from __future__ import annotations

import time
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from .config_schema import GlobalConfig, TenantConfig


class ConfigCache:
    """Caches configuration data for improved performance."""

    def __init__(self, cache_ttl: int = 300):  # 5 minutes default TTL
        """Initialize configuration cache."""
        self.cache_ttl = cache_ttl
        self._cache: dict[str, dict[str, Any]] = {}
        self._cache_timestamps: dict[str, float] = {}

    def get_global_config(self, cache_key: str = "global") -> GlobalConfig | None:
        """Get cached global configuration."""
        if self._is_cache_valid(cache_key):
            cached_data = self._cache.get(cache_key)
            if cached_data:
                return cached_data.get("config")
        return None

    def set_global_config(self, config: GlobalConfig, cache_key: str = "global") -> None:
        """Cache global configuration."""
        self._cache[cache_key] = {"config": config}
        self._cache_timestamps[cache_key] = time.time()

    def get_tenant_config(self, tenant_id: str) -> TenantConfig | None:
        """Get cached tenant configuration."""
        cache_key = f"tenant_{tenant_id}"
        if self._is_cache_valid(cache_key):
            cached_data = self._cache.get(cache_key)
            if cached_data:
                return cached_data.get("config")
        return None

    def set_tenant_config(self, tenant_id: str, config: TenantConfig) -> None:
        """Cache tenant configuration."""
        cache_key = f"tenant_{tenant_id}"
        self._cache[cache_key] = {"config": config}
        self._cache_timestamps[cache_key] = time.time()

    def get_config_section(self, section: str, cache_key: str = "global") -> Any | None:
        """Get cached configuration section."""
        full_cache_key = f"{cache_key}_{section}"
        if self._is_cache_valid(full_cache_key):
            cached_data = self._cache.get(full_cache_key)
            if cached_data:
                return cached_data.get("section")
        return None

    def set_config_section(self, section: str, data: Any, cache_key: str = "global") -> None:
        """Cache configuration section."""
        full_cache_key = f"{cache_key}_{section}"
        self._cache[full_cache_key] = {"section": data}
        self._cache_timestamps[full_cache_key] = time.time()

    def invalidate(self, cache_key: str | None = None) -> None:
        """Invalidate cache entries."""
        if cache_key is None:
            # Invalidate all caches
            self._cache.clear()
            self._cache_timestamps.clear()
        else:
            # Invalidate specific cache key and related entries
            keys_to_remove = [key for key in self._cache if key.startswith(cache_key)]
            for key in keys_to_remove:
                self._cache.pop(key, None)
                self._cache_timestamps.pop(key, None)

    def invalidate_tenant_cache(self, tenant_id: str) -> None:
        """Invalidate tenant-specific cache entries."""
        self.invalidate(f"tenant_{tenant_id}")

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is still valid."""
        if cache_key not in self._cache_timestamps:
            return False

        timestamp = self._cache_timestamps[cache_key]
        return time.time() - timestamp < self.cache_ttl

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        current_time = time.time()
        valid_entries = 0
        expired_entries = 0

        for timestamp in self._cache_timestamps.values():
            if current_time - timestamp < self.cache_ttl:
                valid_entries += 1
            else:
                expired_entries += 1

        return {
            "total_entries": len(self._cache),
            "valid_entries": valid_entries,
            "expired_entries": expired_entries,
            "cache_ttl": self.cache_ttl,
            "cache_keys": list(self._cache.keys()),
        }


class FileWatcher:
    """Watches configuration files for changes and invalidates cache."""

    def __init__(self, config_dir: Path, cache: ConfigCache):
        """Initialize file watcher."""
        self.config_dir = config_dir
        self.cache = cache
        self._file_timestamps: dict[str, float] = {}
        self._watch_files()

    def _watch_files(self) -> None:
        """Initialize file watching."""
        config_files = [
            "routing.yaml",
            "security.yaml",
            "monitoring.yaml",
            "ingest.yaml",
            "policy.yaml",
            "archive_routes.yaml",
            "poller.yaml",
            "grounding.yaml",
            "profiles.yaml",
            "deprecations.yaml",
        ]

        for filename in config_files:
            file_path = self.config_dir / filename
            if file_path.exists():
                self._file_timestamps[str(file_path)] = file_path.stat().st_mtime

    def check_for_changes(self) -> bool:
        """Check if any watched files have changed."""
        changed = False

        for file_path_str, last_modified in self._file_timestamps.items():
            file_path = Path(file_path_str)
            if file_path.exists():
                current_modified = file_path.stat().st_mtime
                if current_modified > last_modified:
                    self._file_timestamps[file_path_str] = current_modified
                    changed = True

        if changed:
            # Invalidate global config cache when any file changes
            self.cache.invalidate("global")

        return changed

    def update_file_timestamp(self, file_path: Path) -> None:
        """Update file timestamp after manual changes."""
        if file_path.exists():
            self._file_timestamps[str(file_path)] = file_path.stat().st_mtime


@lru_cache(maxsize=128)
def get_cached_config_section(section: str, config_hash: str) -> Any:
    """LRU cache for configuration sections based on content hash."""
    # This is a simple LRU cache that can be used for frequently accessed
    # configuration sections. The config_hash should be computed from the
    # file content to ensure cache invalidation when files change.


def compute_config_hash(config_dir: Path) -> str:
    """Compute hash of configuration directory for cache invalidation."""
    import hashlib

    hash_obj = hashlib.md5(usedforsecurity=False)  # nosec B324 - config cache key only

    # Sort files for consistent hashing
    config_files = sorted(config_dir.glob("*.yaml"))

    for file_path in config_files:
        if file_path.is_file():
            # Include filename and modification time
            hash_obj.update(file_path.name.encode())
            hash_obj.update(str(file_path.stat().st_mtime).encode())

    return hash_obj.hexdigest()
