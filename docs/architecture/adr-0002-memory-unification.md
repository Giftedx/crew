---
adr: 0002
title: Unify Memory and Knowledge Systems
status: Proposed
date: 2025-10-18
authors:
  - Ultimate Discord Intelligence Bot Architecture Group
---

## Context

The repository contains six+ independent memory/knowledge implementations:

- `src/memory/` (production VectorStore with Qdrant)
- `src/ultimate_discord_intelligence_bot/knowledge/unified_memory.py`
- `src/ultimate_discord_intelligence_bot/services/memory_service.py` (in-memory stub)
- `src/ultimate_discord_intelligence_bot/services/mem0_service.py` (third-party integration)
- Multiple memory tools: `mem0_memory_tool.py`, `memory_storage_tool.py`, `graph_memory_tool.py`, `hipporag_continual_memory_tool.py`, `memory_compaction_tool.py`

This fragmentation leads to:

- Inconsistent tenancy handling across memory backends
- Tools bypassing vector storage entirely (in-memory alternatives)
- No single abstraction for semantic retrieval
- Duplicated embedding logic

## Decision

1. **Canonical Store** – `src/memory/vector_store.py` is the production-grade implementation; all memory operations must route through it or a thin tenant-aware facade.
2. **Facade Location** – Create `src/ultimate_discord_intelligence_bot/memory/__init__.py` (new directory) exporting `UnifiedMemoryService` that wraps `memory.vector_store.VectorStore` with tenant context injection.
3. **Tool Consolidation** – Migrate specialty tools (Mem0, HippoRAG, Graph) to either:
   - Plugin architecture if distinct value proposition
   - Deprecation if superseded by core vector store capabilities
4. **Service Migration** – Retire `services/memory_service.py` and `services/mem0_service.py`; route all callers to the unified facade.
5. **Tenancy Enforcement** – All upsert/query operations must accept `(tenant, workspace)` and use namespace isolation per ADR-0001 patterns.

## Consequences

- Single source of truth for vector embeddings and semantic search
- Simpler onboarding (one memory API vs. six competing systems)
- Easier to instrument hit rates, retrieval accuracy, and cost metrics
- Requires migration of tools and ingestion/retrieval workflows
- May need compatibility shims during transition period
