# Tools Reference Guide

This document enumerates all public tools exported by `ultimate_discord_intelligence_bot.tools` and groups them by function. It is code-verified against the registry in `src/ultimate_discord_intelligence_bot/tools/__init__.py`.

- Total Tools: 111
- Last Updated: November 4, 2025
- Source of truth: `tools/__init__.py::MAPPING` and `__all__`
- Status: Active (see Deprecations below)

Notes

- All tools subclass `BaseTool` and return `StepResult` instances for unified error handling. See `src/platform/core/step_result.py` (compat shim at `src/ultimate_discord_intelligence_bot/step_result.py`).
- For any HTTP I/O, use `src/platform/http/http_utils.py` wrappers (`resilient_get`, `resilient_post`, `retrying_*`). Direct `requests.*` is prohibited by guards.

## Category overview

| Category | Count | Description |
|---|---:|---|
| Observability | 26 | Metrics, monitoring, routing/orchestration helpers |
| Analysis | 23 | Content understanding, scoring, and insights |
| Memory | 23 | Vector/graph memory, RAG, optimization |
| Acquisition/Ingestion | 19 | Acquisition and provider adapters |
| Verification | 10 | Fact-checking and quality validation |
| Social Monitoring | 3 | Social stream monitors and X/Twitter monitoring |
| Discord | 4 | Discord bot integrations |
| Web Automation | 1 | Playwright-based browser automation |
| Other | 2 | Utilities (e.g., drive upload, content generation) |

Counts derive from the tool registry; see “Regeneration” below to refresh this page.

## Inventory by category

### Observability (26)

- AdvancedPerformanceAnalyticsTool
- AgentBridgeTool
- CheckpointManagementTool
- CollectiveIntelligenceTool
- ContentTypeRoutingTool
- CostTrackingTool
- DashboardIntegrationTool
- DependencyResolverTool
- EarlyExitConditionsTool
- EscalationManagementTool
- FastMCPClientTool
- InsightSharingTool
- IntelligentAlertingTool
- LearningTool
- MCPCallTool
- OrchestrationStatusTool
- PipelineTool
- ResourceAllocationTool
- RouterStatusTool
- SystemStatusTool
- TaskRoutingTool
- UnifiedCacheTool
- UnifiedMetricsTool
- UnifiedOrchestrationTool
- UnifiedRouterTool
- WorkflowOptimizationTool

### Analysis (23)

- CharacterProfileTool
- ClaimExtractorTool
- ContentQualityAssessmentTool
- CrossPlatformNarrativeTrackingTool
- DebateCommandTool
- EnhancedAnalysisTool
- ImageAnalysisTool
- LeaderboardTool
- LiveStreamAnalysisTool
- LogicalFallacyTool
- MultimodalAnalysisTool
- NarrativeTrackerTool
- PerspectiveSynthesizerTool
- ReanalysisTriggerTool
- SentimentTool
- SmartClipComposerTool
- SocialGraphAnalysisTool
- TextAnalysisTool
- TimelineTool
- TrendAnalysisTool
- TrendForecastingTool
- VideoFrameAnalysisTool
- ViralityPredictionTool

### Memory (23)

- DSPyOptimizationTool
- GraphMemoryTool
- HippoRagContinualMemoryTool
- KnowledgeOpsTool
- LCSummarizeTool
- Mem0MemoryTool
- MemoryCompactionTool
- MemoryStorageTool
- MockVectorSearchTool
- OfflineRAGTool
- PromptCompressionTool
- RagHybridTool
- RagIngestTool
- RagIngestUrlTool
- RagQueryVectorStoreTool
- ResearchAndBriefMultiTool
- ResearchAndBriefTool
- StrategicPlanningTool
- UnifiedContextTool
- UnifiedMemoryStoreTool
- UnifiedMemoryTool
- VectorSearchTool
- VowpalWabbitBanditTool

### Acquisition/Ingestion (19)

- AudioTranscriptionTool
- DiscordDownloadTool
- InstagramStoriesArchiverTool
- MultiPlatformDownloadTool
- PodcastResolverTool
- RedditAPITool
- SocialResolverTool
- TikTokEnhancedDownloadTool
- TranscriptIndexTool
- TwitchResolverTool
- TwitterAPITool
- YouTubeResolverTool
- YtDlpDownloadTool
- InstagramDownloadTool
- KickDownloadTool
- RedditDownloadTool
- TikTokDownloadTool
- TwitchDownloadTool
- TwitterDownloadTool

### Verification (10)

- ClaimVerifierTool
- ConfidenceScoringTool
- ConsistencyCheckTool
- ContextVerificationTool
- DeceptionScoringTool
- FactCheckTool
- OutputValidationTool
- SponsorComplianceTool
- TrustworthinessTrackerTool
- TruthScoringTool

### Social Monitoring (3)

- MultiPlatformMonitorTool
- SocialMediaMonitorTool
- XMonitorTool

### Discord (4)

- DiscordMonitorTool
- DiscordPostTool
- DiscordPrivateAlertTool
- DiscordQATool

### Web Automation (1)

- PlaywrightAutomationTool

### Other (2)

- DriveUploadTool
- TwitterThreadReconstructorTool

## Deprecations

Refer to `docs/deprecations/tool_deprecation_registry.md` for full details. Snapshot:

- Removed: EnhancedYoutubeTool, MultimodalAnalysisToolOld, YoutubeDownloadTool
- Deprecated (migrate soon): HippoRagContinualMemoryTool, Mem0MemoryTool, MemoryStorageTool, MemoryV2Tool, MultiModalAnalysisTool
- Planned deprecations: AdvancedAudioAnalysisTool, AdvancedPerformanceAnalyticsTool, ImageAnalysisTool, InstagramStoriesArchiverTool, OfflineRagTool, RagIngestUrlTool, ResearchAndBriefMultiTool, TextAnalysisTool, TiktokEnhancedDownloadTool, VectorSearchTool, VideoFrameAnalysisTool

Status labels in this document reflect the registry; some deprecated tools remain exportable for compatibility until removal windows close.

## Import and usage

Recommended import pattern (lazy, guard-friendly):

```python
from ultimate_discord_intelligence_bot.tools import EnhancedAnalysisTool, UnifiedMemoryTool

analysis = EnhancedAnalysisTool()
mem = UnifiedMemoryTool()
```

All tools should return a StepResult via `.ok()/.skip()/.fail()/.uncertain()`, and instrument metrics as appropriate.

## Regeneration

This page is generated from `tools/__init__.py::MAPPING` and the deprecation registry.

- To validate exports, run the guards (see `scripts/validate_tools_exports.py`).
- If you add/rename tools, update the registry and re-run the docs refresh step.

If a tool import fails due to optional dependencies, `tools.__getattr__` returns a stub that fails at runtime with a descriptive StepResult. Keep optional deps documented in the tool README.
