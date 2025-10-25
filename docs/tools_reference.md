# Tools Reference Guide

This document provides comprehensive documentation for all available CrewAI tools in the system. Tools are organized by category and functionality.

**Total Tools:** 110+  
**Last Updated:** 2025-01-05  
**Status:** Active (see [Deprecation Registry](../deprecations/tool_deprecation_registry.md) for deprecated tools)

## Architecture Overview

The Ultimate Discord Intelligence Bot uses a sophisticated CrewAI-based architecture with specialized agents, comprehensive error handling, and advanced observability. For detailed architecture information, see:

- **[CrewAI System Architecture](architecture/crew_system.md)** - Complete system architecture and agent design
- **[Error Handling Architecture](architecture/error_handling.md)** - Comprehensive error handling and recovery systems
- **[Configuration Management](configuration.md)** - Configuration system and feature flags

> Network & HTTP Conventions: See `docs/network_conventions.md` for canonical outbound HTTP guidance (timeouts, URL validation, resilient POST/GET helpers, rate‑limit handling, optional retry/backoff & tracing). Tools performing network I/O should rely on `src/core/http_utils.py` (`resilient_post`, `resilient_get`, `retrying_post`, `retrying_get`, `http_request_with_retry`, constants) rather than re‑implementing validation, timeouts, or monkeypatch‑friendly fallbacks.

## Tool Categories Overview

| Category | Count | Description |
|----------|-------|-------------|
| [Content Analysis](#content-analysis-tools) | 14 | Text, audio, video, and multimodal analysis tools |
| [Memory & Storage](#memory--storage-tools) | 8 | Vector storage, memory management, and retrieval tools |
| [Download & Media](#download--media-tools) | 16 | Platform-specific downloaders and media processing tools |
| [RAG & Retrieval](#rag--retrieval-tools) | 6 | Retrieval-augmented generation and knowledge retrieval tools |
| [Discord Integration](#discord-integration-tools) | 8 | Discord bot interaction and monitoring tools |
| [Monitoring & Observability](#monitoring--observability-tools) | 4 | System monitoring, metrics, and status tools |
| [Routing & Orchestration](#routing--orchestration-tools) | 5 | Task routing, orchestration, and workflow management tools |
| [Research & Briefing](#research--briefing-tools) | 2 | Research automation and briefing generation tools |
| [Compliance & Quality](#compliance--quality-tools) | 2 | Content compliance and quality assessment tools |
| [Other](#other-tools) | 52 | Specialized tools for specific use cases |

## Quick Reference

### Most Used Tools

- `EnhancedAnalysisTool` - Primary content analysis interface
- `UnifiedMemoryTool` - Unified memory operations
- `MultiPlatformDownloadTool` - Cross-platform content download
- `RagHybridTool` - Retrieval-augmented generation
- `DiscordPostTool` - Discord bot posting

### Recently Added Tools

- `ClaimVerifierTool` - Fact verification and claim checking
- `ConfidenceScoringTool` - Confidence assessment for analysis results
- `ConsistencyCheckTool` - Content consistency validation
- `OutputValidationTool` - Output quality validation
- `ReanalysisTriggerTool` - Workflow control for reanalysis

### Deprecated Tools

See [Deprecation Registry](../deprecations/tool_deprecation_registry.md) for tools marked for removal.

## Complete Tool Inventory

### Content Analysis Tools (14 tools)

| Tool | File | Description | Status |
|------|------|-------------|--------|
| `AdvancedAudioAnalysisTool` | `advanced_audio_analysis_tool.py` | Advanced audio content analysis | Active |
| `AudioTranscriptionTool` | `audio_transcription_tool.py` | Audio-to-text transcription | Active |
| `ContextVerificationTool` | `context_verification_tool.py` | Context verification and validation | Active |
| `EnhancedAnalysisTool` | `enhanced_analysis_tool.py` | Primary content analysis interface | Active |
| `ImageAnalysisTool` | `image_analysis_tool.py` | Image content analysis | Active |
| `LiveStreamAnalysisTool` | `live_stream_analysis_tool.py` | Real-time stream analysis | Active |
| `MultimodalAnalysisTool` | `multimodal_analysis_tool.py` | Cross-modal content analysis | Active |
| `ReanalysisTriggerTool` | `reanalysis_trigger_tool.py` | Workflow control for reanalysis | Active |
| `SentimentTool` | `sentiment_tool.py` | Sentiment analysis | Active |
| `SocialGraphAnalysisTool` | `social_graph_analysis_tool.py` | Social network analysis | Active |
| `TextAnalysisTool` | `text_analysis_tool.py` | Text content analysis | Active |
| `TrendAnalysisTool` | `trend_analysis_tool.py` | Trend detection and analysis | Active |
| `TrendForecastingTool` | `trend_forecasting_tool.py` | Trend prediction | Active |
| `VideoFrameAnalysisTool` | `video_frame_analysis_tool.py` | Video frame analysis | Active |

### Memory & Storage Tools (8 tools)

| Tool | File | Description | Status |
|------|------|-------------|--------|
| `GraphMemoryTool` | `graph_memory_tool.py` | Graph-based memory operations | Active |
| `HippoRagContinualMemoryTool` | `hipporag_continual_memory_tool.py` | HippoRAG memory integration | Deprecated |
| `Mem0MemoryTool` | `mem0_memory_tool.py` | Mem0 memory integration | Deprecated |
| `MemoryCompactionTool` | `memory_compaction_tool.py` | Memory optimization | Active |
| `MemoryStorageTool` | `memory_storage_tool.py` | Qdrant-based storage | Deprecated |
| `MockVectorSearchTool` | `mock_vector_tool.py` | Mock vector search for testing | Active |
| `RagQueryVectorStoreTool` | `rag_query_vs_tool.py` | Vector store queries | Active |
| `VectorSearchTool` | `vector_search_tool.py` | Vector search operations | Active |

### Download & Media Tools (16 tools)

| Tool | File | Description | Status |
|------|------|-------------|--------|
| `DiscordDownloadTool` | `discord_download_tool.py` | Discord content download | Active |
| `EnhancedYouTubeDownloadTool` | `enhanced_youtube_tool.py` | Enhanced YouTube downloader | Deprecated |
| `InstagramDownloadTool` | `yt_dlp_download_tool.py` | Instagram content download | Active |
| `InstagramStoriesArchiverTool` | `instagram_stories_archiver_tool.py` | Instagram stories archiving | Active |
| `KickDownloadTool` | `yt_dlp_download_tool.py` | Kick platform download | Active |
| `MultiPlatformDownloadTool` | `multi_platform_download_tool.py` | Unified download interface | Active |
| `RedditDownloadTool` | `yt_dlp_download_tool.py` | Reddit content download | Active |
| `TikTokDownloadTool` | `yt_dlp_download_tool.py` | TikTok content download | Active |
| `TikTokEnhancedDownloadTool` | `tiktok_enhanced_download_tool.py` | Enhanced TikTok downloader | Active |
| `TwitchDownloadTool` | `yt_dlp_download_tool.py` | Twitch content download | Active |
| `TwitchResolverTool` | `yt_dlp_download_tool.py` | Twitch URL resolution | Active |
| `TwitterDownloadTool` | `yt_dlp_download_tool.py` | Twitter content download | Active |
| `TwitterThreadReconstructorTool` | `twitter_thread_reconstructor_tool.py` | Twitter thread reconstruction | Active |
| `YouTubeDownloadTool` | `youtube_download_tool.py` | YouTube download stub | Deprecated |
| `YouTubeResolverTool` | `yt_dlp_download_tool.py` | YouTube URL resolution | Active |
| `YtDlpDownloadTool` | `yt_dlp_download_tool.py` | Core yt-dlp implementation | Active |

### RAG & Retrieval Tools (6 tools)

| Tool | File | Description | Status |
|------|------|-------------|--------|
| `OfflineRAGTool` | `offline_rag_tool.py` | Offline RAG operations | Active |
| `RagHybridTool` | `rag_hybrid_tool.py` | Hybrid RAG implementation | Active |
| `RagIngestTool` | `rag_ingest_tool.py` | RAG content ingestion | Active |
| `RagIngestUrlTool` | `rag_ingest_url_tool.py` | URL-based RAG ingestion | Active |
| `ResearchAndBriefMultiTool` | `research_and_brief_multi_tool.py` | Multi-source research | Active |
| `ResearchAndBriefTool` | `research_and_brief_tool.py` | Research and briefing | Active |

### Discord Integration Tools (8 tools)

| Tool | File | Description | Status |
|------|------|-------------|--------|
| `DiscordMonitorTool` | `discord_monitor_tool.py` | Discord channel monitoring | Active |
| `DiscordPostTool` | `discord_post_tool.py` | Discord message posting | Active |
| `DiscordPrivateAlertTool` | `discord_private_alert_tool.py` | Private Discord alerts | Active |
| `DiscordQATool` | `discord_qa_tool.py` | Discord Q&A functionality | Active |
| `IntelligentAlertingTool` | `intelligent_alerting_tool.py` | Intelligent alert system | Active |
| `MultiPlatformMonitorTool` | `multi_platform_monitor_tool.py` | Cross-platform monitoring | Active |
| `SocialMediaMonitorTool` | `social_media_monitor_tool.py` | Social media monitoring | Active |
| `XMonitorTool` | `x_monitor_tool.py` | X/Twitter monitoring | Active |

### Monitoring & Observability Tools (4 tools)

| Tool | File | Description | Status |
|------|------|-------------|--------|
| `OrchestrationStatusTool` | `orchestration_status_tool.py` | Orchestration status monitoring | Active |
| `RouterStatusTool` | `router_status_tool.py` | Router status monitoring | Active |
| `SystemStatusTool` | `system_status_tool.py` | System health monitoring | Active |
| `UnifiedMetricsTool` | `unified_metrics_tool.py` | Unified metrics collection | Active |

### Routing & Orchestration Tools (5 tools)

| Tool | File | Description | Status |
|------|------|-------------|--------|
| `AgentBridgeTool` | `agent_bridge_tool.py` | Agent communication bridge | Active |
| `ContentTypeRoutingTool` | `content_type_routing_tool.py` | Content type routing | Active |
| `TaskRoutingTool` | `task_routing_tool.py` | Task routing and distribution | Active |
| `UnifiedOrchestrationTool` | `unified_orchestration_tool.py` | Unified orchestration | Active |
| `UnifiedRouterTool` | `unified_router_tool.py` | Unified routing system | Active |

### Research & Briefing Tools (2 tools)

| Tool | File | Description | Status |
|------|------|-------------|--------|
| `ResearchAndBriefTool` | `research_and_brief_tool.py` | Research and briefing | Active |
| `ResearchAndBriefMultiTool` | `research_and_brief_multi_tool.py` | Multi-source research | Active |

### Compliance & Quality Tools (2 tools)

| Tool | File | Description | Status |
|------|------|-------------|--------|
| `ContentQualityAssessmentTool` | `content_quality_assessment_tool.py` | Content quality assessment | Active |
| `SponsorComplianceTool` | `sponsor_compliance_tool.py` | Sponsor compliance checking | Active |

### Other Tools (52 tools)

| Tool | File | Description | Status |
|------|------|-------------|--------|
| `AdvancedPerformanceAnalyticsTool` | `advanced_performance_analytics_tool.py` | Performance analytics | Active |
| `CharacterProfileTool` | `character_profile_tool.py` | Character profile analysis | Active |
| `CheckpointManagementTool` | `checkpoint_management_tool.py` | Checkpoint management | Active |
| `ClaimExtractorTool` | `claim_extractor_tool.py` | Claim extraction | Active |
| `ClaimVerifierTool` | `claim_verifier_tool.py` | Claim verification | Active |
| `CollectiveIntelligenceTool` | `collective_intelligence_tool.py` | Collective intelligence | Active |
| `ConfidenceScoringTool` | `confidence_scoring_tool.py` | Confidence scoring | Active |
| `ConsistencyCheckTool` | `consistency_check_tool.py` | Consistency checking | Active |
| `ContentGenerationTool` | `content_generation_tool.py` | Content generation | Active |
| `ContentRecommendationTool` | `content_recommendation_tool.py` | Content recommendation | Active |
| `CostTrackingTool` | `cost_tracking_tool.py` | Cost tracking | Active |
| `CrossPlatformNarrativeTrackingTool` | `cross_platform_narrative_tool.py` | Cross-platform narrative tracking | Active |
| `DSPyOptimizationTool` | `dspy_optimization_tool.py` | DSPy optimization | Active |
| `DashboardIntegrationTool` | `dashboard_integration_tool.py` | Dashboard integration | Active |
| `DebateCommandTool` | `debate_command_tool.py` | Debate command handling | Active |
| `DeceptionScoringTool` | `deception_scoring_tool.py` | Deception scoring | Active |
| `DependencyResolverTool` | `dependency_resolver_tool.py` | Dependency resolution | Active |
| `DriveUploadTool` | `drive_upload_tool.py` | Google Drive upload | Active |
| `DriveUploadToolBypass` | `drive_upload_tool_bypass.py` | Drive upload bypass | Active |
| `EarlyExitConditionsTool` | `early_exit_conditions_tool.py` | Early exit conditions | Active |
| `EngagementPredictionTool` | `engagement_prediction_tool.py` | Engagement prediction | Active |
| `EscalationManagementTool` | `escalation_management_tool.py` | Escalation management | Active |
| `FactCheckTool` | `fact_check_tool.py` | Fact checking | Active |
| `FastMCPClientTool` | `fastmcp_client_tool.py` | Fast MCP client | Active |
| `InsightSharingTool` | `insight_sharing_tool.py` | Insight sharing | Active |
| `KnowledgeOpsTool` | `knowledge_ops_tool.py` | Knowledge operations | Active |
| `LCSummarizeTool` | `lc_summarize_tool.py` | LangChain summarization | Active |
| `LeaderboardTool` | `leaderboard_tool.py` | Leaderboard management | Active |
| `LearningTool` | `learning_tool.py` | Learning and adaptation | Active |
| `LogicalFallacyTool` | `logical_fallacy_tool.py` | Logical fallacy detection | Active |
| `MCPCallTool` | `mcp_call_tool.py` | MCP call handling | Active |
| `MCPResourceTool` | `mcp_resource_tool.py` | MCP resource management | Active |
| `NarrativeTrackerTool` | `narrative_tracker_tool.py` | Narrative tracking | Active |
| `OutputValidationTool` | `output_validation_tool.py` | Output validation | Active |
| `PerspectiveSynthesizerTool` | `perspective_synthesizer_tool.py` | Perspective synthesis | Active |
| `PipelineTool` | `pipeline_tool.py` | Pipeline management | Active |
| `PodcastResolverTool` | `podcast_resolver_tool.py` | Podcast resolution | Active |
| `PromptCompressionTool` | `prompt_compression_tool.py` | Prompt compression | Active |
| `ResourceAllocationTool` | `resource_allocation_tool.py` | Resource allocation | Active |
| `SmartClipComposerTool` | `smart_clip_composer_tool.py` | Smart clip composition | Active |
| `SocialResolverTool` | `social_resolver_tool.py` | Social media resolution | Active |
| `SteelmanArgumentTool` | `steelman_argument_tool.py` | Steelman argumentation | Active |
| `StrategicPlanningTool` | `strategic_planning_tool.py` | Strategic planning | Active |
| `TaskManagementTool` | `task_management_tool.py` | Task management | Active |
| `TimelineTool` | `timeline_tool.py` | Timeline management | Active |
| `TranscriptIndexTool` | `transcript_index_tool.py` | Transcript indexing | Active |
| `TrustworthinessTrackerTool` | `trustworthiness_tracker_tool.py` | Trustworthiness tracking | Active |
| `TruthScoringTool` | `truth_scoring_tool.py` | Truth scoring | Active |
| `ViralityPredictionTool` | `virality_prediction_tool.py` | Virality prediction | Active |
| `VisualSummaryTool` | `visual_summary_tool.py` | Visual summarization | Active |
| `VowpalWabbitBanditTool` | `vowpal_wabbit_bandit_tool.py` | Vowpal Wabbit bandit | Active |
| `WorkflowOptimizationTool` | `workflow_optimization_tool.py` | Workflow optimization | Active |

## Content Analysis Tools

### Logical Fallacy Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/logical_fallacy_tool.py`

Detects logical fallacies in text using sophisticated pattern matching and heuristics. Enhanced beyond basic keyword matching to include complex linguistic patterns. A prior backup variant was removed as dead code to avoid duplication; this canonical implementation defines explicit heuristic threshold constants for maintainability.

**Features:**

- 17+ fallacy types including ad hominem, straw man, false dilemma, slippery slope
- Keyword-based detection (`KEYWORD_FALLACIES`)
- Regex pattern matching (`PATTERN_FALLACIES`)
- Confidence scoring and detailed explanations
- Context-aware analysis

**Usage:**

```python
from ultimate_discord_intelligence_bot.tools.logical_fallacy_tool import LogicalFallacyTool

tool = LogicalFallacyTool()
result = tool._run("Everyone knows this is true, so you must agree.")
# Returns: detected fallacies with confidence scores
```

### Claim Extractor Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/claim_extractor_tool.py`

Extracts factual claims from text using knowledge graph extraction patterns.

**Features:**

- Integration with KG extraction utilities (`kg.extract`)
- Filters out short/insignificant matches
- Returns structured claim data
- NLP-based pattern recognition

**Usage:**

```python
result = tool._run("The Earth is round and orbits the Sun.")
# Returns: {"status": "success", "claims": ["The Earth is round", "Earth orbits the Sun"]}
```

### Perspective Synthesizer Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/perspective_synthesizer_tool.py`

Combines multiple search results into a coherent, unified summary using LLM processing.

**Features:**

- Merges search backends (memory, vector, external)
- Memory retrieval integration
- OpenRouter service integration
- Prompt engine processing

**Dependencies:**

- `MemoryService` - Retrieves relevant memories
- `OpenRouterService` - LLM processing
- `PromptEngine` - Prompt construction

### Steelman Argument Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/steelman_argument_tool.py`

Creates the strongest possible version of arguments for debate analysis.

### Sentiment Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/sentiment_tool.py`

Analyzes emotional tone and sentiment in text content. Uses VADER when available; otherwise falls back to a lightweight lexical heuristic. Thresholds (`POSITIVE_THRESHOLD`, `NEGATIVE_THRESHOLD`) are declared as module constants for clarity.

### Text Analysis Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/text_analysis_tool.py`

Provides general-purpose text processing and analysis capabilities.

## Memory & Storage Tools

### Character Profile Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/analysis/character_profile_tool.py`

Aggregates per-person trust metrics and events to build comprehensive character profiles.

**Features:**

- Event storage with source attribution
- Trust score calculation and tracking
- Leaderboard integration for comparative analysis
- Persistent storage with JSON serialization
- Metrics integration for observability

**Usage:**

```python
from ultimate_discord_intelligence_bot.tools.analysis.character_profile_tool import CharacterProfileTool

tool = CharacterProfileTool()
result = tool._run("John Doe", "truth", "The Earth is round", "scientific_fact")
# Returns: Character profile with trust metrics and event history
```

### Claim Verifier Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/verification/claim_verifier_tool.py`

Verifies factual claims using multiple search backends and provides confidence scoring.

**Features:**

- Multi-backend verification (Serply, Exa, Perplexity)
- Confidence scoring with source attribution
- Configurable verification thresholds
- Source relevance scoring
- Timestamp tracking for verification history

**Usage:**

```python
from ultimate_discord_intelligence_bot.tools.verification.claim_verifier_tool import ClaimVerifierTool

tool = ClaimVerifierTool()
result = tool._run("The Earth is round", context="Scientific fact", max_sources=5)
# Returns: Verification results with confidence scores and sources
```

### Trustworthiness Tracker Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/analysis/trustworthiness_tracker_tool.py`

Tracks and analyzes trustworthiness patterns across different sources and claims.

**Features:**

- Trust score calculation algorithms
- Pattern recognition for deceptive content
- Historical trust tracking
- Confidence interval analysis
- Source reliability assessment

### Leaderboard Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/analysis/leaderboard_tool.py`

Manages competitive rankings and leaderboards for various metrics and achievements.

**Features:**

- Dynamic ranking calculations
- Multi-metric leaderboards
- Historical ranking tracking
- Performance analytics
- Custom scoring algorithms

### Content Generation Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/analysis/content_generation_tool.py`

Generates content using AI models with quality assessment and optimization.

**Features:**

- Multi-model content generation
- Quality scoring and validation
- Content optimization suggestions
- Style and tone adaptation
- Plagiarism detection

### Content Recommendation Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/analysis/content_recommendation_tool.py`

Provides intelligent content recommendations based on user preferences and behavior.

**Features:**

- Collaborative filtering algorithms
- Content-based recommendations
- Hybrid recommendation systems
- User preference learning
- A/B testing for recommendation optimization

### Cross-Platform Narrative Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/analysis/cross_platform_narrative_tool.py`

Tracks and analyzes narratives across multiple platforms and sources.

**Features:**

- Cross-platform content correlation
- Narrative evolution tracking
- Sentiment analysis across platforms
- Influence mapping
- Viral content prediction

### Debate Command Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/analysis/debate_command_tool.py`

Manages debate commands and argumentation structures for formal debates.

**Features:**

- Argument structure validation
- Debate timing management
- Evidence verification
- Scoring algorithms
- Moderator assistance

### Engagement Prediction Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/analysis/engagement_prediction_tool.py`

Predicts content engagement metrics using machine learning models.

**Features:**

- Engagement score prediction
- Viral potential assessment
- Audience behavior modeling
- Content optimization suggestions
- Performance forecasting

### Smart Clip Composer Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/analysis/smart_clip_composer_tool.py`

Intelligently composes video clips from longer content with optimal timing and content selection.

**Features:**

- Automatic highlight detection
- Optimal clip timing
- Content relevance scoring
- Multi-format output
- Quality optimization

### Timeline Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/analysis/timeline_tool.py`

Creates and manages chronological timelines of events and content.

**Features:**

- Event sequencing and correlation
- Timeline visualization
- Chronological analysis
- Event impact assessment
- Historical context integration

### Virality Prediction Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/analysis/virality_prediction_tool.py`

Predicts viral potential of content using advanced analytics and machine learning.

**Features:**

- Viral score calculation
- Content optimization suggestions
- Platform-specific predictions
- Audience targeting
- Trend analysis integration

### Visual Summary Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/analysis/visual_summary_tool.py`

Creates visual summaries and infographics from text content.

**Features:**

- Automatic infographic generation
- Data visualization
- Chart and graph creation
- Visual content optimization
- Multi-format output support

## Memory & Storage Tools

### Unified Memory Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/memory/unified_memory_tool.py`

Provides unified access to multiple memory systems with intelligent routing and optimization.

**Features:**

- Multi-backend memory integration
- Intelligent memory routing
- Cache optimization
- Memory consolidation
- Performance monitoring

**Usage:**

```python
from ultimate_discord_intelligence_bot.tools.memory.unified_memory_tool import UnifiedMemoryTool

tool = UnifiedMemoryTool()
result = tool._run("store", "key", "value", "metadata")
# Returns: Memory operation result with performance metrics
```

### DSPy Optimization Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/memory/dspy_optimization_tool.py`

Optimizes DSPy models for better performance and accuracy in memory operations.

**Features:**

- Model optimization algorithms
- Performance tuning
- Accuracy improvement
- Resource optimization
- A/B testing for model variants

### Knowledge Ops Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/memory/knowledge_ops_tool.py`

Manages knowledge operations including storage, retrieval, and optimization.

**Features:**

- Knowledge graph operations
- Semantic search optimization
- Knowledge consolidation
- Relationship mapping
- Knowledge quality assessment

### LangChain Summarize Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/memory/lc_summarize_tool.py`

Provides LangChain-based summarization capabilities with advanced text processing.

**Features:**

- Multi-model summarization
- Context-aware summarization
- Length-adaptive summaries
- Quality scoring
- Multi-language support

### Memory Compaction Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/memory/memory_compaction_tool.py`

Optimizes memory usage through intelligent compaction and cleanup operations.

**Features:**

- Memory usage analysis
- Intelligent compaction algorithms
- Cleanup optimization
- Performance monitoring
- Resource management

### Offline RAG Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/memory/offline_rag_tool.py`

Provides offline retrieval-augmented generation capabilities for local processing.

**Features:**

- Local model integration
- Offline knowledge retrieval
- Privacy-preserving processing
- Local vector storage
- Performance optimization

### Prompt Compression Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/memory/prompt_compression_tool.py`

Compresses prompts while maintaining semantic meaning and effectiveness.

**Features:**

- Semantic compression algorithms
- Quality preservation
- Token optimization
- Context maintenance
- Performance improvement

### RAG Hybrid Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/memory/rag_hybrid_tool.py`

Combines multiple RAG approaches for optimal retrieval and generation performance.

**Features:**

- Hybrid retrieval strategies
- Multi-source integration
- Quality optimization
- Performance monitoring
- Adaptive routing

### Strategic Planning Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/memory/strategic_planning_tool.py`

Provides strategic planning capabilities with memory integration and optimization.

**Features:**

- Strategic analysis
- Planning optimization
- Resource allocation
- Timeline management
- Performance tracking

### Vowpal Wabbit Bandit Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/memory/vowpal_wabbit_bandit_tool.py`

Implements bandit algorithms for optimal decision-making in memory operations.

**Features:**

- Multi-armed bandit algorithms
- Contextual bandits
- Online learning
- Performance optimization
- Adaptive strategies

## Discord Integration Tools

### Discord Post Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/discord/discord_post_tool.py`

Handles Discord message posting with rich formatting and media support.

**Features:**

- Rich message formatting
- Media attachment support
- Channel management
- User interaction handling
- Rate limiting compliance

### Discord Monitor Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/discord/discord_monitor_tool.py`

Monitors Discord channels for specific content and events.

**Features:**

- Real-time monitoring
- Content filtering
- Event detection
- Alert management
- Analytics collection

### Discord Download Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/discord/discord_download_tool.py`

Downloads content from Discord channels with metadata preservation.

**Features:**

- Content downloading
- Metadata extraction
- Format preservation
- Batch processing
- Quality optimization

## Monitoring & Observability Tools

### Advanced Performance Analytics Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/observability/advanced_performance_analytics_tool.py`

Provides comprehensive performance analytics and monitoring capabilities.

**Features:**

- Performance metrics collection
- Trend analysis
- Anomaly detection
- Resource monitoring
- Optimization recommendations

### Cost Tracking Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/observability/cost_tracking_tool.py`

Tracks and analyzes costs across different services and operations.

**Features:**

- Cost aggregation
- Budget monitoring
- Cost optimization
- Resource allocation
- Financial reporting

### Orchestration Status Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/observability/orchestration_status_tool.py`

Monitors orchestration status and provides system health insights.

**Features:**

- System health monitoring
- Orchestration status tracking
- Performance metrics
- Alert management
- Status reporting

### Router Status Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/observability/router_status_tool.py`

Monitors routing status and provides optimization recommendations.

**Features:**

- Routing performance monitoring
- Load balancing analysis
- Traffic pattern analysis
- Optimization suggestions
- Performance reporting

### Unified Metrics Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/observability/unified_metrics_tool.py`

Provides unified access to all system metrics and monitoring data.

**Features:**

- Metric aggregation
- Cross-system monitoring
- Performance analysis
- Trend identification
- Optimization insights

## Routing & Orchestration Tools

### Task Routing Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/integration/task_routing_tool.py`

Intelligently routes tasks to appropriate agents and services.

**Features:**

- Intelligent task routing
- Load balancing
- Performance optimization
- Resource allocation
- Quality assurance

### Unified Orchestration Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/integration/unified_orchestration_tool.py`

Provides unified orchestration capabilities across all system components.

**Features:**

- Workflow orchestration
- Service coordination
- Resource management
- Performance optimization
- Quality monitoring

### Unified Router Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/integration/unified_router_tool.py`

Provides unified routing capabilities with intelligent load balancing.

**Features:**

- Intelligent routing
- Load balancing
- Performance optimization
- Resource allocation
- Quality assurance

### Enhanced Analysis Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/enhanced_analysis_tool.py`

Provides enhanced analysis capabilities, including political topic extraction and claim detection.

## Verification & Quality Tools

### Claim Verifier Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/verification/claim_verifier_tool.py`

Verifies claims against multiple sources and provides confidence scores.

**Features:**

- Multi-source verification
- Confidence scoring
- Source credibility assessment
- Fact-checking integration
- Bias detection

**Usage:**

```python
from ultimate_discord_intelligence_bot.tools.verification.claim_verifier_tool import ClaimVerifierTool

tool = ClaimVerifierTool()
result = tool._run("claim_text", "context", "sources")
# Returns: Verification result with confidence score and sources
```

### Consistency Check Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/verification/consistency_check_tool.py`

Checks for consistency across multiple sources and claims.

**Features:**

- Cross-source consistency analysis
- Contradiction detection
- Reliability scoring
- Source comparison
- Quality assessment

### Context Verification Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/verification/context_verification_tool.py`

Verifies claims within their proper context and historical background.

**Features:**

- Contextual analysis
- Historical verification
- Timeline validation
- Source context checking
- Accuracy assessment

### Deception Scoring Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/verification/deception_scoring_tool.py`

Scores content for potential deception and misinformation.

**Features:**

- Deception detection algorithms
- Misinformation scoring
- Credibility assessment
- Source verification
- Quality metrics

### Fact Check Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/verification/fact_check_tool.py`

Comprehensive fact-checking with multiple verification sources.

**Features:**

- Multi-source fact-checking
- Real-time verification
- Source credibility scoring
- Bias detection
- Accuracy reporting

### Output Validation Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/verification/output_validation_tool.py`

Validates outputs for accuracy, consistency, and quality.

**Features:**

- Output quality assessment
- Consistency validation
- Accuracy verification
- Quality scoring
- Error detection

## Content Processing Tools

### Audio Transcription Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/content/audio_transcription_tool.py`

Transcribes audio content with high accuracy and metadata preservation.

**Features:**

- Multi-format audio support
- Speaker identification
- Timestamp preservation
- Quality optimization
- Batch processing

### Content Ingestion Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/content/content_ingestion_tool.py`

Ingests content from multiple sources with metadata extraction.

**Features:**

- Multi-source ingestion
- Metadata extraction
- Format normalization
- Quality validation
- Batch processing

### Content Optimization Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/content/content_optimization_tool.py`

Optimizes content for better performance and engagement.

**Features:**

- Content optimization algorithms
- Performance enhancement
- Engagement optimization
- Quality improvement
- A/B testing support

### Multi-Platform Download Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/content/multi_platform_download_tool.py`

Downloads content from multiple platforms with unified interface.

**Features:**

- Multi-platform support
- Unified download interface
- Metadata preservation
- Quality optimization
- Batch processing

### Platform-Specific Download Tools

#### YouTube Download Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/content/youtube_download_tool.py`

Specialized YouTube content downloading with metadata extraction.

**Features:**

- YouTube API integration
- Video metadata extraction
- Quality selection
- Thumbnail extraction
- Batch processing

#### TikTok Download Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/content/tiktok_download_tool.py`

TikTok content downloading with engagement metrics.

**Features:**

- TikTok API integration
- Engagement metrics
- Hashtag analysis
- Trend detection
- Content optimization

#### Instagram Download Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/content/instagram_download_tool.py`

Instagram content downloading with visual analysis.

**Features:**

- Instagram API integration
- Visual content analysis
- Engagement metrics
- Hashtag tracking
- Story archiving

#### Twitch Download Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/content/twitch_download_tool.py`

Twitch stream downloading with chat analysis.

**Features:**

- Twitch API integration
- Stream metadata extraction
- Chat analysis
- Viewer metrics
- Clip generation

#### Kick Download Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/content/kick_download_tool.py`

Kick platform content downloading with engagement tracking.

**Features:**

- Kick API integration
- Engagement tracking
- Content analysis
- Performance metrics
- Quality optimization

## Data Management Tools

### Mem0 Memory Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/mem0_memory_tool.py`

Provides Mem0-based memory operations with advanced storage and retrieval capabilities.

**Features:**

- Mem0 integration
- Advanced memory operations
- Storage optimization
- Retrieval enhancement
- Performance monitoring

### Graph Memory Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/graph_memory_tool.py`

Manages graph-based memory with relationship tracking and semantic search.

**Features:**

- Graph-based memory storage
- Relationship tracking
- Semantic search
- Knowledge graph operations
- Performance optimization

### Insight Sharing Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/insight_sharing_tool.py`

Shares insights across agents and systems with intelligent routing.

**Features:**

- Cross-agent insight sharing
- Intelligent routing
- Quality assessment
- Performance optimization
- Collaboration enhancement

### Knowledge Ops Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/knowledge_ops_tool.py`

Manages knowledge operations including storage, retrieval, and optimization.

**Features:**

- Knowledge graph operations
- Semantic search optimization
- Knowledge consolidation
- Relationship mapping
- Knowledge quality assessment

## Tool Statistics

### Total Tools: 110+

The Ultimate Discord Intelligence Bot includes over 110 specialized tools organized into the following categories:

- **Analysis Tools**: 25+ tools for content analysis, scoring, and insights
- **Memory & Storage**: 15+ tools for memory management and optimization
- **Content Processing**: 20+ tools for multi-platform content handling
- **Verification & Quality**: 10+ tools for fact-checking and validation
- **Discord Integration**: 8+ tools for Discord-specific operations
- **Monitoring & Observability**: 12+ tools for system monitoring and analytics
- **Routing & Orchestration**: 10+ tools for intelligent task routing
- **Data Management**: 10+ tools for data processing and storage

### Tool Categories

1. **Core Analysis**: Text analysis, sentiment analysis, bias detection, fact-checking
2. **Content Processing**: Multi-platform downloading, transcription, optimization
3. **Memory Management**: Vector storage, knowledge graphs, semantic search
4. **Quality Assurance**: Verification, validation, consistency checking
5. **System Integration**: Discord, monitoring, routing, orchestration
6. **Performance**: Analytics, optimization, caching, monitoring

### Usage Patterns

- **High-Frequency**: Content ingestion, analysis, and Discord integration tools
- **Medium-Frequency**: Memory operations, verification, and monitoring tools
- **Specialized**: Platform-specific downloaders, advanced analytics, and optimization tools

### Development Status

- **Production Ready**: 80+ tools with comprehensive testing and documentation
- **Beta**: 20+ tools with basic functionality and testing
- **Development**: 10+ tools in active development with experimental features

## Getting Started

To use any tool in your CrewAI agents:

```python
from ultimate_discord_intelligence_bot.tools import YourTool

# Initialize the tool
tool = YourTool()

# Use in your agent
agent = Agent(
    role="Your Role",
    goal="Your Goal",
    tools=[tool],
    # ... other configuration
)
```

For more detailed information about specific tools, refer to their individual documentation files in the `src/ultimate_discord_intelligence_bot/tools/` directory.

---

## Web Automation Tools

### Playwright Automation Tool

**File:** `src/ultimate_discord_intelligence_bot/tools/web/playwright_automation_tool.py`

Automates browser interactions using Playwright for dynamic content scraping. Supports JavaScript-rendered content, element interaction, and multi-page workflows.

**Features:**

- Screenshot capture (full page or element-specific)
- Content extraction (HTML and text)
- Element interaction (click, fill, wait for selector)
- Dynamic content scraping
- Graceful degradation when Playwright unavailable

**Actions:**

- `screenshot`: Capture page or element screenshot
- `content`: Extract HTML and text content
- `wait_for_selector`: Wait for element to appear
- `click`: Click an element by selector
- `fill`: Fill form fields with text

**Configuration:**

- `ENABLE_PLAYWRIGHT_AUTOMATION`: Enable/disable browser automation (default: false)
- `PLAYWRIGHT_TIMEOUT_MS`: Browser timeout in milliseconds (default: 30000)
- `PLAYWRIGHT_HEADLESS`: Run browser in headless mode (default: true)

**Installation:**

```bash
pip install playwright
playwright install chromium
```

**Usage:**

```python
from ultimate_discord_intelligence_bot.tools.web import PlaywrightAutomationTool

tool = PlaywrightAutomationTool()

# Capture screenshot
result = tool._run(
    url="https://example.com",
    action="screenshot",
    tenant="test",
    workspace="test"
)

# Extract content
result = tool._run(
    url="https://example.com",
    action="content",
    tenant="test",
    workspace="test"
)

# Click element
result = tool._run(
    url="https://example.com",
    action="click",
    selector="button#submit",
    tenant="test",
    workspace="test"
)
```

**Error Handling:**

- Returns StepResult with DEPENDENCY error when Playwright unavailable
- Returns StepResult with INVALID_INPUT for malformed URLs or missing selectors
- Returns StepResult with TIMEOUT for pages that exceed timeout threshold
- Returns StepResult with PROCESSING error for general automation failures

**Performance:**

- Screenshot latency: < 5s for simple pages
- Content extraction: < 3s for typical pages
- Element interaction: < 2s per action

**Security:**

- Runs in headless mode by default
- Sandboxed browser context
- No JavaScript execution without explicit commands
- Tenant-aware isolation

For more detailed information about specific tools, refer to their individual documentation files in the `src/ultimate_discord_intelligence_bot/tools/` directory.
