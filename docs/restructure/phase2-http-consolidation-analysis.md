# Phase 2.2: HTTP Consolidation Analysis

## Summary

- **2 identical files**: `requests_wrappers.py`, `validators.py` (deleted from core/)
- **4 different implementations**: All are functional equivalents with import path differences

## Analysis of Different Implementations

### 1. `retry.py`
**Differences**: Import paths only
- Core: `from obs import metrics`
- Platform: `from platform.observability import metrics`
- Minor formatting differences (comments, line breaks)
- **Action**: Keep platform/ version, delete core/ version

### 2. `retry_config.py`
**Differences**: Import paths only
- Core: Likely uses `core.*` imports
- Platform: Uses `platform.*` imports
- **Action**: Keep platform/ version, delete core/ version

### 3. `config.py`
**Differences**: Import paths only
- Core: `from core.secure_config import get_config`
- Platform: `from platform.config.configuration import get_config`
- Functionality identical
- **Action**: Keep platform/ version, delete core/ version

### 4. `cache.py`
**Differences**: Import paths only
- Core: `from core.cache.redis_cache`, `from core.cache.unified_config`
- Platform: `from platform.cache.redis_cache`, `from platform.cache.unified_config`
- Minor formatting differences
- **Action**: Keep platform/ version, delete core/ version

## Facade Pattern

### `core/http_utils.py`
- Compatibility facade for legacy imports
- Forwards to `core.http.*` modules
- Contains monkeypatch seams for tests

### `platform/http/http_utils.py`
- Similar facade pattern
- Forwards to `platform.http.*` modules

**Strategy**: Update `core/http_utils.py` to forward to `platform.http.*` instead of `core.http.*`

## Action Plan

1. ✅ Delete 2 identical files: `requests_wrappers.py`, `validators.py`
2. Delete 4 different implementations from core/ (keep platform/ versions)
3. Update `core/http_utils.py` facade to forward to `platform.http.*`
4. Update all `core.http.*` imports to `platform.http.*`
5. Delete empty `core/http/` directory
6. Test HTTP functionality
