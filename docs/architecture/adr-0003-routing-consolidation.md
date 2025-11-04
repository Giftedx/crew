---
adr: 0003
title: Consolidate Model Routing Stack
status: Accepted
date: 2025-10-18
implementation_date: 2025-10-28
implementation_status: Complete
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

1. **Canonical Stack** – `src/platform/llm/` provides the unified, provider-agnostic routing layer for completions and embeddings.
2. **Deprecate Legacy** – Archive `src/core/routing/*`, `src/ai/routing/*`, `src/ultimate_discord_intelligence_bot/services/rl_model_router.py`, and `src/ultimate_discord_intelligence_bot/services/semantic_router_service.py`.
3. **RL Integration** – Preserve reinforcement learning capabilities by integrating bandit logic under `src/platform/rl/` as first-class plugins to the LLM router.
4. **Migration Path** – Callers of deprecated routers must migrate to the platform LLM router APIs (`platform.llm.*`).

## Consequences

- Single routing API reduces maintenance and cognitive load
- Easier to A/B test routing strategies
- Deprecating 10+ modules requires careful dependency analysis
- Existing RL experiments may need adapter layer

## Implementation Status (Updated November 3, 2025)

**Canonical Implementation**: ✅ Complete

- `src/platform/llm/` - Unified LLM routing layer
- Provider-agnostic router with 15+ LLM providers
- `ROUTER_POLICY` configuration (quality_first, cost, latency)
- Contextual bandits for adaptive routing

**Supported Providers**: OpenAI, Anthropic, Google, OpenRouter, Groq, Together AI, Cohere, Mistral, Fireworks, Perplexity, X.AI, DeepSeek, Azure OpenAI, AWS Bedrock

**RL Integration**: ✅ Complete

- `src/platform/rl/` - Reinforcement learning for routing
- LinUCB contextual bandits implementation
- Reward shaping with quality/cost weights

**Migration Status**: 🔄 In Progress

- New code uses platform LLM layer
- Deprecated routing modules still exist (`src/core/routing/`, `src/ai/routing/`)
- Guard script blocks new code in deprecated directories
