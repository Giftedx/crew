# Deprecated: performance_optimization/

**Archived:** 2024-10-31  
**Original Location:** `/home/crew/performance_optimization/`  
**New Location:** `/home/crew/archive/deprecated/performance_optimization_archived_20241031/`

## Reason for Deprecation

The `performance_optimization/` directory contained legacy performance optimization code that has been superseded by the current architecture:

1. **Deprecated Directory Policy**: Per `scripts/guards/deprecated_directories_guard.py`, adding new code to performance-related directories is restricted
2. **Modern Replacement**: Current performance monitoring and optimization code is properly organized under:
   - `src/obs/performance_monitor.py`
   - `src/obs/performance_baselines.py`
   - `src/obs/resource_monitor.py`
3. **No Active Usage**: Analysis confirmed no active imports from `performance_optimization/` in current codebase
4. **Legacy Structure**: Contained old `src/discord/performance/` hierarchy that predates current architecture

## Contents (Archived)

```
performance_optimization/
└── src/
    └── discord/
        └── performance/
            ├── __init__.py
            ├── config.py
            ├── embedding_optimizer.py
            ├── message_batcher.py
            ├── optimization_integration.py
            ├── performance_manager.py
            └── semantic_cache.py
```

## Migration Notes

- **Embedding Optimization**: Current implementation uses semantic cache in `src/core/cache/semantic/`
- **Message Batching**: Replaced by orchestrator-based batching patterns
- **Performance Management**: Migrated to `src/obs/` observability platform
- **Semantic Cache**: Unified under `src/core/cache/` with multi-level caching

## Restoration

If any code from this archived directory is needed:

1. Review archived code at `archive/deprecated/performance_optimization_archived_20241031/`
2. Extract specific functions/classes needed
3. Adapt to current architecture (orchestrators, StepResult pattern, obs platform)
4. **Do NOT** restore the entire directory - it violates current architectural boundaries

## Related Documentation

- Current performance monitoring: `src/obs/README.md`
- Deprecated directories policy: `scripts/guards/deprecated_directories_guard.py`
- Cache architecture: `docs/architecture/adr-0001-cache-platform.md`
- Orchestration framework: `docs/orchestration/usage_guide.md`

---

**Archive performed during:** Phase 1.2 Orchestration Unification (Task 8: Organizational Cleanup)  
**Related Work:** Strategic Refactoring Plan 2025, Section 1.2
