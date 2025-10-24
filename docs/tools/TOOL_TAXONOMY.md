# Tool Taxonomy and Consolidation Plan

## Current Tool Count: ~64 tools

## Tool Categories and Consolidation Opportunities

### 1. Acquisition Tools (6 tools)

**Current:**

- `multi_platform_download_tool.py` - Primary downloader
- `youtube_download_tool.py` - Legacy wrapper
- `enhanced_youtube_tool.py` - Legacy wrapper  
- `yt_dlp_download_tool.py` - Core implementation
- `tiktok_enhanced_download_tool.py` - Platform-specific
- `discord_download_tool.py` - Platform-specific

**Consolidation Plan:**

- Keep `MultiPlatformDownloadTool` as primary
- Keep `YouTubeDownloadTool` as platform-specific
- Keep `DiscordDownloadTool` as platform-specific
- **Remove:** `enhanced_youtube_tool.py` (legacy wrapper)
- **Target:** 4 tools (33% reduction)

### 2. Analysis Tools (16 tools)

**Current:**

- `enhanced_analysis_tool.py` - Primary analyzer
- `text_analysis_tool.py` - Text-specific
- `sentiment_tool.py` - Sentiment analysis
- `multimodal_analysis_tool.py` - Multi-modal
- `timeline_tool.py` - Timeline analysis
- `trend_analysis_tool.py` - Trend analysis
- `engagement_prediction_tool.py` - Engagement
- `content_quality_assessment_tool.py` - Quality
- `image_analysis_tool.py` - Image analysis
- `video_frame_analysis_tool.py` - Video frames
- `character_profile_tool.py` - Character analysis
- `narrative_tracker_tool.py` - Narrative tracking
- `social_graph_analysis_tool.py` - Social graphs
- `cross_platform_narrative_tool.py` - Cross-platform
- `live_stream_analysis_tool.py` - Live streams
- `content_recommendation_tool.py` - Recommendations

**Consolidation Plan:**

- Keep `EnhancedAnalysisTool` as primary
- Keep `MultimodalAnalysisTool` for multi-modal
- Keep `SentimentTool` for sentiment
- Keep `ImageAnalysisTool` for images
- **Merge:** `text_analysis_tool.py` into `EnhancedAnalysisTool`
- **Merge:** `timeline_tool.py` into `EnhancedAnalysisTool`
- **Merge:** `trend_analysis_tool.py` into `EnhancedAnalysisTool`
- **Target:** 8 tools (50% reduction)

### 3. Memory Tools (12 tools)

**Current:**

- `memory_storage_tool.py` - Primary storage
- `graph_memory_tool.py` - Graph storage
- `vector_search_tool.py` - Vector search
- `rag_ingest_tool.py` - RAG ingestion
- `rag_hybrid_tool.py` - Hybrid RAG
- `mem0_memory_tool.py` - Mem0 integration
- `hipporag_continual_memory_tool.py` - Continual learning
- `memory_compaction_tool.py` - Memory compaction
- `knowledge_ops_tool.py` - Knowledge operations
- `research_and_brief_tool.py` - Research
- `research_and_brief_multi_tool.py` - Multi-research
- `offline_rag_tool.py` - Offline RAG

**Consolidation Plan:**

- Keep `MemoryStorageTool` as primary
- Keep `VectorSearchTool` for search
- Keep `RagHybridTool` for RAG
- Keep `Mem0MemoryTool` for Mem0
- **Merge:** `graph_memory_tool.py` into `MemoryStorageTool`
- **Merge:** `rag_ingest_tool.py` into `RagHybridTool`
- **Target:** 6 tools (50% reduction)

### 4. Verification Tools (7 tools)

**Current:**

- `fact_check_tool.py` - Primary fact-checking
- `claim_extractor_tool.py` - Claim extraction
- `logical_fallacy_tool.py` - Fallacy detection
- `context_verification_tool.py` - Context verification
- `deception_scoring_tool.py` - Deception scoring
- `claim_verifier_tool.py` - Claim verification
- `sponsor_compliance_tool.py` - Sponsor compliance

**Consolidation Plan:**

- Keep `FactCheckTool` as primary
- Keep `ClaimExtractorTool` for extraction
- Keep `LogicalFallacyTool` for fallacies
- **Merge:** `context_verification_tool.py` into `FactCheckTool`
- **Merge:** `deception_scoring_tool.py` into `FactCheckTool`
- **Target:** 4 tools (43% reduction)

### 5. Observability Tools (12 tools)

**Current:**

- `pipeline_tool.py` - Pipeline monitoring
- `advanced_performance_analytics_tool.py` - Performance
- `unified_metrics_tool.py` - Metrics
- `intelligent_alerting_tool.py` - Alerting
- `dashboard_integration_tool.py` - Dashboard
- `unified_router_tool.py` - Router
- `unified_cache_tool.py` - Cache
- `unified_orchestration_tool.py` - Orchestration
- `agent_bridge_tool.py` - Agent bridge
- `mcp_call_tool.py` - MCP calls
- `workflow_optimization_tool.py` - Optimization
- `task_routing_tool.py` - Task routing

**Consolidation Plan:**

- Keep `PipelineTool` as primary
- Keep `AdvancedPerformanceAnalyticsTool` for performance
- Keep `UnifiedMetricsTool` for metrics
- Keep `IntelligentAlertingTool` for alerting
- **Merge:** `dashboard_integration_tool.py` into `UnifiedMetricsTool`
- **Merge:** `workflow_optimization_tool.py` into `AdvancedPerformanceAnalyticsTool`
- **Target:** 8 tools (33% reduction)

## Standardized Tool Base Classes

### 1. Core Tool Base

```python
class StandardTool(BaseTool):
    """Base class for all project tools with StepResult pattern."""
    
    @abstractmethod
    def _run(self, *args, **kwargs) -> StepResult:
        """Execute tool logic. Must return StepResult."""
        pass
    
    def _handle_error(self, error: Exception) -> StepResult:
        """Standard error handling."""
        return StepResult.fail(str(error))
```

### 2. Acquisition Tool Base

```python
class AcquisitionTool(StandardTool):
    """Base class for content acquisition tools."""
    
    def _validate_url(self, url: str) -> bool:
        """Validate URL format."""
        pass
    
    def _get_platform(self, url: str) -> str:
        """Detect platform from URL."""
        pass
```

### 3. Analysis Tool Base

```python
class AnalysisTool(StandardTool):
    """Base class for content analysis tools."""
    
    def _preprocess_content(self, content: str) -> str:
        """Preprocess content for analysis."""
        pass
    
    def _postprocess_results(self, results: dict) -> dict:
        """Postprocess analysis results."""
        pass
```

## Consolidation Timeline

### Phase 1: Remove Legacy Wrappers (Week 1)

- Remove `enhanced_youtube_tool.py`
- Remove `youtube_download_tool.py` (keep as import stub)
- Update imports in affected files

### Phase 2: Merge Similar Tools (Week 2)

- Merge text analysis into enhanced analysis
- Merge timeline/trend analysis into enhanced analysis
- Merge context verification into fact checking

### Phase 3: Standardize Base Classes (Week 3)

- Implement `StandardTool` base class
- Implement category-specific base classes
- Update all tools to inherit from standardized bases

## Success Metrics

### Tool Count Reduction

- **Current:** ~64 tools
- **Target:** <50 tools (22% reduction)
- **Stretch:** <40 tools (38% reduction)

### Code Quality Improvements

- All tools inherit from `StandardTool`
- Consistent error handling with `StepResult`
- Standardized tool discovery documentation
- No functional regressions

### Maintenance Benefits

- Reduced cognitive load for developers
- Easier tool discovery and usage
- Consistent patterns across all tools
- Better test coverage with standardized base classes
