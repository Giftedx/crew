---
adr: 0004
title: Unify Orchestration Layer
status: Proposed
date: 2025-10-18
authors:
  - Ultimate Discord Intelligence Bot Architecture Group
---

## Context

Nine orchestrators compete instead of collaborating:

- `src/ultimate_discord_intelligence_bot/autonomous_orchestrator.py` (primary)
- `src/ultimate_discord_intelligence_bot/enhanced_autonomous_orchestrator.py`
- `src/ultimate_discord_intelligence_bot/fallback_orchestrator.py`
- `src/ultimate_discord_intelligence_bot/services/hierarchical_orchestrator.py`
- `src/ultimate_discord_intelligence_bot/services/monitoring_orchestrator.py`
- `src/ultimate_discord_intelligence_bot/orchestration/unified_orchestrator.py`
- `src/ultimate_discord_intelligence_bot/agent_training/orchestrator.py`
- `src/core/resilience_orchestrator.py`
- `src/core/autonomous_intelligence.py`

## Decision

1. **Primary Orchestrator** – `autonomous_orchestrator.py` remains the main entry point.
2. **Strategy Pattern** – Refactor specialized orchestrators (fallback, hierarchical, monitoring) into strategy classes injectable into `AutonomousIntelligenceOrchestrator`.
3. **Facade** – Create `orchestration/facade.py` providing `get_orchestrator(strategy="autonomous")` to centralize instantiation.
4. **Deprecation** – Archive standalone orchestrators; ensure agents/tasks configuration references the facade.

## Consequences

- Single orchestration API simplifies agent coordination
- Strategy pattern allows runtime switching (e.g., fallback mode during outages)
- Requires refactoring orchestrator-specific logic into composable components
- Migration of crew configuration and tooling
