# Phase 2.1: Cache Consolidation Plan

## Current State

- `src/core/cache/` has 3 files:
  - `__init__.py` - imports from `.bounded_cache` (missing file)
  - `llm_cache.py` - uses `create_llm_cache` from `.bounded_cache`
  - `retrieval_cache.py` - uses `create_retrieval_cache` from `.bounded_cache`

- `src/platform/cache/` exists but is empty

- Files referencing `platform.cache.*` imports:
  - `src/ultimate_discord_intelligence_bot/services/cache.py` expects `platform.cache.bounded_cache`
  - `src/ultimate_discord_intelligence_bot/services/unified_cache_service.py` expects `platform.cache.unified_config`
  - Other files expect `platform.cache.enhanced_semantic_cache`, `platform.cache.semantic_cache`

## Issue

The `core/cache/` files import from `.bounded_cache` but this file doesn't exist in core/cache/ or platform/cache/.

## Action Required

1. Locate `bounded_cache.py` (may be in a different location)
2. If not found, check if functionality exists elsewhere
3. Move all core/cache/ files to platform/cache/
4. Create missing dependencies or move them from other locations
5. Update all imports from `core.cache.*` to `platform.cache.*`

## Next Steps

1. Search for bounded_cache implementation
2. Search for unified_config implementation
3. Search for semantic_cache implementations
4. Consolidate all cache functionality into platform/cache/
5. Update imports systematically

