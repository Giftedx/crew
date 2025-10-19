---
adr: 0003
title: Consolidate Model Routing Stack
status: Proposed
date: 2025-10-18
authors:
  - Ultimate Discord Intelligence Bot Architecture Group
---

## Context

The system has 15+ router implementations competing for the same purpose:

- `src/core/router.py`, `src/core/llm_router.py`
- `src/core/routing/` (6 router classes)
- `src/ai/routing/` (bandit routers)
- `src/ai/enhanced_ai_router.py`, `src/ai/adaptive_ai_router.py`, `src/ai/performance_router.py`, `src/ai/advanced_bandits_router.py`
- `src/ultimate_discord_intelligence_bot/services/openrouter_service/` (primary production service)
- `src/ultimate_discord_intelligence_bot/services/model_router.py`
- `src/ultimate_discord_intelligence_bot/services/rl_model_router.py`
- `src/ultimate_discord_intelligence_bot/services/semantic_router_service.py`

## Decision

1. **Canonical Stack** – `services/openrouter_service/` (modular workflow) + `services/model_router.py` are the production routing layer.
2. **Deprecate Legacy** – Archive `core/routing/*`, `ai/routing/*`, `services/rl_model_router.py`, `services/semantic_router_service.py`.
3. **RL Integration** – Preserve reinforcement learning capabilities by integrating bandit logic into `openrouter_service/adaptive_routing.py` or as plugins.
4. **Migration Path** – Services importing deprecated routers must switch to `services.openrouter_service.OpenRouterService`.

## Consequences

- Single routing API reduces maintenance and cognitive load
- Easier to A/B test routing strategies
- Deprecating 10+ modules requires careful dependency analysis
- Existing RL experiments may need adapter layer
