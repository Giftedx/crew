---
adr: 0004
title: Unify Orchestration Layer
status: Accepted
date: 2025-10-18
implementation_date: 2025-10-30
implementation_status: Complete
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

1. **Primary Orchestrator** – `src/ultimate_discord_intelligence_bot/pipeline_components/orchestrator.py` (ContentPipeline) is the single orchestration entry point.
2. **Strategy Integration** – Specialized behaviors (fallback, hierarchical, monitoring) are modeled as pipeline strategies/components within the ContentPipeline rather than separate orchestrators.
3. **Deprecation** – Archive standalone orchestrator modules; ensure agents/tasks and HTTP entry points call the ContentPipeline orchestrator.

## Consequences

- Single orchestration API simplifies agent coordination
- Strategy pattern allows runtime switching (e.g., fallback mode during outages)
- Requires refactoring orchestrator-specific logic into composable components
- Migration of crew configuration and tooling

## Implementation Status (Updated November 3, 2025)

**Canonical Implementation**: ✅ Complete

- `src/ultimate_discord_intelligence_bot/pipeline_components/orchestrator.py` - Unified ContentPipeline (1637 lines)
- 7-stage pipeline: download → transcription → content routing → quality filtering → analysis/lightweight → finalization
- Early exit system with 3 checkpoints (post-download, post-transcription, post-quality)
- Langfuse tracing integration
- Parallel analysis execution

**Pipeline Stages**:

- `_download_phase`: Multi-platform content acquisition
- `_transcription_phase`: Speech-to-text conversion
- `_content_routing_phase`: Content classification
- `_quality_filtering_phase`: Quality assessment and routing
- `_lightweight_processing_phase`: Minimal processing path
- `_analysis_phase`: Comprehensive parallel analysis
- `_finalize_phase`: Storage and notifications

**Migration Status**: ✅ Complete

- All orchestration routed through ContentPipeline
- Early exit configuration in `config/early_exit.yaml`
- Quality thresholds in `config/content_types.yaml`
