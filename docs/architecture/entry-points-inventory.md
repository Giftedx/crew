# Entry Points Inventory

**Date**: 2025-10-18  
**Purpose**: Document active vs. deprecated entry points for consolidation roadmap

## Caching Subsystems

### Active (Post-Consolidation)

- `core/cache/multi_level_cache.py` – Production L1/L2 cache hierarchy
- `ultimate_discord_intelligence_bot/cache/__init__.py` – Unified facade with tenant-aware helpers (ADR-0001)

### Deprecated (To Be Archived)

- `ultimate_discord_intelligence_bot/services/cache.py` – Legacy `RedisLLMCache` and `make_key`
- `ultimate_discord_intelligence_bot/services/cache_optimizer.py` – Bespoke cache policies
- `ultimate_discord_intelligence_bot/services/rl_cache_optimizer.py` – RL-based cache tuning (7 classes)
- `src/performance/cache_optimizer.py` – Duplicate optimizer logic
- `src/performance/cache_warmer.py` – Predictive warming (superseded by multi-level promotion)
- `src/ultimate_discord_intelligence_bot/caching/unified_cache.py` – Three-tier prototype (not production)
- `src/core/advanced_cache.py` – Experimental cache classes

## Memory & Knowledge Subsystems

### Active (Post-Consolidation)

- `src/memory/vector_store.py` – Production VectorStore with Qdrant
- `src/ultimate_discord_intelligence_bot/memory/` (to be created) – Unified facade

### Deprecated (To Be Archived)

- `src/ultimate_discord_intelligence_bot/services/memory_service.py` – In-memory testing stub
- `src/ultimate_discord_intelligence_bot/services/mem0_service.py` – Third-party wrapper
- `src/ultimate_discord_intelligence_bot/knowledge/unified_memory.py` – Partial unification attempt
- `src/ultimate_discord_intelligence_bot/tools/mem0_memory_tool.py` – Tool-level Mem0 integration
- `src/ultimate_discord_intelligence_bot/tools/memory_storage_tool.py` – Duplicate storage logic
- `src/ultimate_discord_intelligence_bot/tools/graph_memory_tool.py` – Graph-specific tool
- `src/ultimate_discord_intelligence_bot/tools/hipporag_continual_memory_tool.py` – HippoRAG tool
- `src/ultimate_discord_intelligence_bot/tools/memory_compaction_tool.py` – Compaction logic

## Routing Subsystems

### Active (Post-Consolidation)

- `src/ultimate_discord_intelligence_bot/services/openrouter_service/` – Primary routing workflow
- `src/ultimate_discord_intelligence_bot/services/model_router.py` – Model selection helper

### Deprecated (To Be Archived)

- `src/core/router.py`, `src/core/llm_router.py` – Legacy core routers
- `src/core/routing/` – Full routing subsystem (6 classes + factory + adapters + migrations)
- `src/ai/routing/` – Bandit routers (BanditRouter, LinUCBRouter, VWBanditRouter)
- `src/ai/enhanced_ai_router.py`, `src/ai/adaptive_ai_router.py`, `src/ai/performance_router.py`
- `src/ai/advanced_bandits_router.py`, `src/ai/advanced_contextual_bandits.py`
- `src/ultimate_discord_intelligence_bot/services/rl_model_router.py` – RL routing variant
- `src/ultimate_discord_intelligence_bot/services/semantic_router_service.py` – Semantic routing

## Orchestration Subsystems

### Active (Post-Consolidation)

- `src/ultimate_discord_intelligence_bot/autonomous_orchestrator.py` – Main orchestrator
- `src/ultimate_discord_intelligence_bot/orchestration/facade.py` (to be created) – Strategy selector

### Deprecated (To Be Archived)

- `src/ultimate_discord_intelligence_bot/enhanced_autonomous_orchestrator.py`
- `src/ultimate_discord_intelligence_bot/fallback_orchestrator.py`
- `src/ultimate_discord_intelligence_bot/services/hierarchical_orchestrator.py`
- `src/ultimate_discord_intelligence_bot/services/monitoring_orchestrator.py`
- `src/ultimate_discord_intelligence_bot/orchestration/unified_orchestrator.py`
- `src/ultimate_discord_intelligence_bot/agent_training/orchestrator.py`
- `src/core/resilience_orchestrator.py`
- `src/core/autonomous_intelligence.py`

## Performance & Analytics Subsystems

### Active (Post-Consolidation)

- `src/obs/metrics.py` – Canonical metrics emission
- `src/ultimate_discord_intelligence_bot/observability/` – Dashboard integration, intelligent alerts, unified metrics

### Deprecated (To Be Archived)

- `src/ultimate_discord_intelligence_bot/performance_dashboard.py`
- `src/ultimate_discord_intelligence_bot/performance_optimization_engine.py`
- `src/ultimate_discord_intelligence_bot/advanced_performance_analytics.py`
- `src/ultimate_discord_intelligence_bot/advanced_performance_analytics_alert_engine.py`
- `src/ultimate_discord_intelligence_bot/advanced_performance_analytics_alert_management.py`
- `src/ultimate_discord_intelligence_bot/advanced_performance_analytics_discord_integration.py`
- `src/ultimate_discord_intelligence_bot/advanced_performance_analytics_integration.py`
- `src/ultimate_discord_intelligence_bot/advanced_performance_analytics_impl/` (9 modules)
- `src/ultimate_discord_intelligence_bot/monitoring/production_monitor.py`
- `src/performance/cache_optimizer.py`, `src/performance/cache_warmer.py` (overlap with caching deprecations)
