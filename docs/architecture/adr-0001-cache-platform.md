---
adr: 0001
title: Standardize Cache Platform on Multi-Level Cache Facade
status: Accepted
date: 2025-10-18
implementation_date: 2025-10-22
implementation_status: Partially Complete
authors:
  - Ultimate Discord Intelligence Bot Architecture Group
---

## Context

Repository analysis (`CODEBASE_AUDIT_FINDINGS.md`, October 2025) surfaced more than twenty
independent cache implementations across `core/cache/`, `ultimate_discord_intelligence_bot/services/`,
`ultimate_discord_intelligence_bot/cache/`, `performance/`, and various tools. The duplication has
resulted in:

- Divergent cache policies, TTL defaults, and eviction strategies
- No single tenant-aware cache interface for tools and services
- Frequent regressions when enabling or disabling caching features
- Inability to measure aggregate hit rate or cost savings

The canonical implementation that already satisfies most requirements lives in
`src/platform/cache/multi_level_cache.py`, but numerous services bypass it.

## Decision

Adopt the following principles for cache usage:

1. **Canonical API** – All cache consumers must call through a thin adapter exported from
   `src/ultimate_discord_intelligence_bot/cache/__init__.py`. The adapter will be backed by the
   `platform.cache.multi_level_cache.MultiLevelCache` implementation.
2. **Tenant Awareness** – Adapters must require `(tenant, workspace)` to avoid cross-tenant data
   leakage.
3. **Feature Flag Control** – Introduce `ENABLE_CACHE_V2` to gate the unified cache in production
   and allow gradual cutover.
4. **Metrics Integration** – The adapter must emit cache metrics via `obs.metrics`, replacing
   bespoke logging inside performance scripts.
5. **Deprecation Plan** – Mark the following modules as deprecated entry points and migrate callers:
   `services/cache.py`, `services/cache_optimizer.py`, `services/rl_cache_optimizer.py`,
   `performance/cache_optimizer.py`, `performance/cache_warmer.py`, and cache-related tools that
    maintain their own policy logic.

## Consequences

- Provides a single location to evolve cache behaviour, instrumentation, and policy updates.
- Requires incremental migration of services and tools; during migration shadow mode should compare
  legacy vs. unified hit/miss metrics.
- Adds a new mandatory feature flag documented in `docs/configuration.md`.
- Deprecation guard scripts must prevent new modules being added to the deprecated cache directories.

## Implementation Status (Updated November 3, 2025)

**Canonical Implementation**: ✅ Complete

- `src/platform/cache/multi_level_cache.py` - Production-ready multi-level cache
- Cache API exported from platform layer
- Tenant-aware caching with namespace isolation

**Migration Status**: 🔄 In Progress

- Deprecated modules still exist (`services/cache.py`, `performance/cache_optimizer.py`)
- New code uses platform cache layer
- Legacy code migration ongoing

**Next Steps**:

- Complete migration of remaining cache consumers
- Remove deprecated cache modules
- Update deprecation guard scripts
