# Phase 2.1 Cache Consolidation - Blocker

## Issue

`bounded_cache.py` is missing but required by:
- `src/core/cache/__init__.py` imports from `.bounded_cache`
- `src/core/cache/llm_cache.py` imports `create_llm_cache` from `.bounded_cache`
- `src/core/cache/retrieval_cache.py` imports `create_retrieval_cache` from `.bounded_cache`
- `src/ultimate_discord_intelligence_bot/services/cache.py` expects `platform.cache.bounded_cache`

## Current State

- `src/core/cache/` has 3 files but missing `bounded_cache.py` dependency
- `src/platform/cache/` is empty (just created)
- No `bounded_cache.py` found in repository

## Action Required

1. Search repository history for `bounded_cache.py`
2. Check if functionality was merged into another module
3. If found elsewhere, move to `platform/cache/bounded_cache.py`
4. If not found, implement based on usage patterns

## Next Steps

1. Continue with other Phase 2 consolidations (http/, rl/, observability/)
2. Return to cache consolidation after locating/creating bounded_cache
3. Alternative: Move core/cache files to platform/cache/ and fix imports later

