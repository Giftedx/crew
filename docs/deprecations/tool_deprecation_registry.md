# Tool Deprecation Registry

## Overview

This registry tracks the deprecation lifecycle of tools in the Ultimate Discord Intelligence Bot project. Tools are deprecated when they become redundant, superseded by better implementations, or when their functionality is consolidated into other tools.

## Deprecation Policy

### Timeline

- **Deprecation Notice:** 2 release cycles before removal
- **Migration Period:** 1 release cycle for users to migrate
- **Removal:** After migration period expires

### Process

1. **Mark as Deprecated:** Add deprecation warning to tool
2. **Update Documentation:** Mark in docs and provide migration guide
3. **Registry Entry:** Add to this registry with timeline
4. **Monitor Usage:** Track usage during deprecation period
5. **Remove:** Delete tool and update all references

## Active Deprecations

### Phase 1: Immediate Removal (No Migration Needed)

| Tool | Status | Deprecated | Remove By | Reason | Replacement |
|------|--------|------------|-----------|---------|-------------|
| `multimodal_analysis_tool_old.py` | **REMOVED** | v1.0.0 | v1.1.0 | Legacy file, identical to active version | `multimodal_analysis_tool.py` |
| `youtube_download_tool.py` | **REMOVED** | v1.0.0 | v1.1.0 | Stub file, delegates to yt_dlp_download_tool | `yt_dlp_download_tool.py` |
| `enhanced_youtube_tool.py` | **REMOVED** | v1.0.0 | v1.1.0 | Wrapper file, delegates to yt_dlp_download_tool | `yt_dlp_download_tool.py` |

### Phase 2: Deprecation with Migration (2 Release Cycles)

| Tool | Status | Deprecated | Remove By | Reason | Replacement | Migration Guide |
|------|--------|------------|-----------|---------|-------------|-----------------|
| `multi_modal_analysis_tool.py` | **DEPRECATED** | v1.2.0 | v1.4.0 | Duplicate functionality | `multimodal_analysis_tool.py` | [Migration Guide](#multimodal-analysis-migration) |
| `memory_storage_tool.py` | **DEPRECATED** | v1.2.0 | v1.4.0 | Superseded by unified memory | `unified_memory_tool.py` | [Migration Guide](#memory-storage-migration) |
| `memory_v2_tool.py` | **DEPRECATED** | v1.2.0 | v1.4.0 | Superseded by unified memory | `unified_memory_tool.py` | [Migration Guide](#memory-v2-migration) |
| `mem0_memory_tool.py` | **DEPRECATED** | v1.2.0 | v1.4.0 | Superseded by unified memory | `unified_memory_tool.py` | [Migration Guide](#mem0-memory-migration) |
| `hipporag_continual_memory_tool.py` | **DEPRECATED** | v1.2.0 | v1.4.0 | Superseded by unified memory | `unified_memory_tool.py` | [Migration Guide](#hipporag-memory-migration) |

### Phase 3: Future Deprecations (Planned)

| Tool | Status | Deprecated | Remove By | Reason | Replacement | Notes |
|------|--------|------------|-----------|---------|-------------|-------|
| `instagram_stories_archiver_tool.py` | **PLANNED** | v1.3.0 | v1.5.0 | Platform-specific, use unified downloader | `multi_platform_download_tool.py` | Instagram stories support in unified tool |
| `tiktok_enhanced_download_tool.py` | **PLANNED** | v1.3.0 | v1.5.0 | Platform-specific, use unified downloader | `multi_platform_download_tool.py` | TikTok support in unified tool |
| `advanced_audio_analysis_tool.py` | **PLANNED** | v1.3.0 | v1.5.0 | Specialized analysis, consolidate | `enhanced_analysis_tool.py` | Audio analysis features added to enhanced tool |
| `advanced_performance_analytics_tool.py` | **PLANNED** | v1.3.0 | v1.5.0 | Specialized analysis, consolidate | `enhanced_analysis_tool.py` | Performance analytics in enhanced tool |
| `image_analysis_tool.py` | **PLANNED** | v1.3.0 | v1.5.0 | Specialized analysis, consolidate | `enhanced_analysis_tool.py` | Image analysis in enhanced tool |
| `text_analysis_tool.py` | **PLANNED** | v1.3.0 | v1.5.0 | Specialized analysis, consolidate | `enhanced_analysis_tool.py` | Text analysis in enhanced tool |
| `video_frame_analysis_tool.py` | **PLANNED** | v1.3.0 | v1.5.0 | Specialized analysis, consolidate | `enhanced_analysis_tool.py` | Video analysis in enhanced tool |
| `rag_ingest_url_tool.py` | **PLANNED** | v1.3.0 | v1.5.0 | URL ingestion, consolidate | `rag_ingest_tool.py` | URL support added to main ingest tool |
| `offline_rag_tool.py` | **PLANNED** | v1.3.0 | v1.5.0 | Offline RAG, consolidate | `rag_hybrid_tool.py` | Offline support in hybrid tool |
| `research_and_brief_multi_tool.py` | **PLANNED** | v1.3.0 | v1.5.0 | Multi-research, consolidate | `research_and_brief_tool.py` | Multi-research in main tool |
| `vector_search_tool.py` | **PLANNED** | v1.3.0 | v1.5.0 | Vector search, consolidate | `rag_query_vs_tool.py` | Vector search in query tool |

## Migration Guides

### Multimodal Analysis Migration

**From:** `multi_modal_analysis_tool.py`
**To:** `multimodal_analysis_tool.py`

#### Changes

- Class name: `MultiModalAnalysisTool` → `MultimodalAnalysisTool`
- File name: `multi_modal_analysis_tool.py` → `multimodal_analysis_tool.py`
- API remains the same

#### Migration Steps

1. Update imports:

   ```python
   # Old
   from ultimate_discord_intelligence_bot.tools import MultiModalAnalysisTool

   # New
   from ultimate_discord_intelligence_bot.tools import MultimodalAnalysisTool
   ```

2. Update usage:

   ```python
   # Old
   tool = MultiModalAnalysisTool()

   # New
   tool = MultimodalAnalysisTool()
   ```

3. Update agent configuration:

   ```python
   # Old
   tools=[wrap_tool_for_crewai(MultiModalAnalysisTool())]

   # New
   tools=[wrap_tool_for_crewai(MultimodalAnalysisTool())]
   ```

### Memory Storage Migration

**From:** `memory_storage_tool.py`
**To:** `unified_memory_tool.py`

#### Changes

- Class name: `MemoryStorageTool` → `UnifiedMemoryTool`
- API: Simplified interface with unified operations
- Features: All memory operations through single interface

#### Migration Steps

1. Update imports:

   ```python
   # Old
   from ultimate_discord_intelligence_bot.tools import MemoryStorageTool

   # New
   from ultimate_discord_intelligence_bot.tools import UnifiedMemoryTool
   ```

2. Update usage:

   ```python
   # Old
   tool = MemoryStorageTool()
   result = tool._run(content="data", operation="store")

   # New
   tool = UnifiedMemoryTool()
   result = tool._run(content="data", operation="store", backend="qdrant")
   ```

### Memory V2 Migration

**From:** `memory_v2_tool.py`
**To:** `unified_memory_tool.py`

#### Changes

- Class name: `MemoryV2Tool` → `UnifiedMemoryTool`
- API: Enhanced with additional backends
- Features: Unified interface for all memory operations

#### Migration Steps

1. Update imports:

   ```python
   # Old
   from ultimate_discord_intelligence_bot.tools import MemoryV2Tool

   # New
   from ultimate_discord_intelligence_bot.tools import UnifiedMemoryTool
   ```

2. Update usage:

   ```python
   # Old
   tool = MemoryV2Tool()
   result = tool._run(operation="store", content="data")

   # New
   tool = UnifiedMemoryTool()
   result = tool._run(operation="store", content="data", backend="unified")
   ```

### Mem0 Memory Migration

**From:** `mem0_memory_tool.py`
**To:** `unified_memory_tool.py`

#### Changes

- Class name: `Mem0MemoryTool` → `UnifiedMemoryTool`
- Backend: Mem0 backend available in unified tool
- API: Unified interface with backend selection

#### Migration Steps

1. Update imports:

   ```python
   # Old
   from ultimate_discord_intelligence_bot.tools import Mem0MemoryTool

   # New
   from ultimate_discord_intelligence_bot.tools import UnifiedMemoryTool
   ```

2. Update usage:

   ```python
   # Old
   tool = Mem0MemoryTool()
   result = tool._run(content="data", operation="store")

   # New
   tool = UnifiedMemoryTool()
   result = tool._run(content="data", operation="store", backend="mem0")
   ```

### HippoRAG Memory Migration

**From:** `hipporag_continual_memory_tool.py`
**To:** `unified_memory_tool.py`

#### Changes

- Class name: `HippoRagContinualMemoryTool` → `UnifiedMemoryTool`
- Backend: HippoRAG backend available in unified tool
- API: Unified interface with backend selection

#### Migration Steps

1. Update imports:

   ```python
   # Old
   from ultimate_discord_intelligence_bot.tools import HippoRagContinualMemoryTool

   # New
   from ultimate_discord_intelligence_bot.tools import UnifiedMemoryTool
   ```

2. Update usage:

   ```python
   # Old
   tool = HippoRagContinualMemoryTool()
   result = tool._run(content="data", operation="store")

   # New
   tool = UnifiedMemoryTool()
   result = tool._run(content="data", operation="store", backend="hipporag")
   ```

## Deprecation Warnings

### Current Warnings

The following tools emit deprecation warnings when used:

```python
# multi_modal_analysis_tool.py
import warnings
warnings.warn(
    "MultiModalAnalysisTool is deprecated. Use MultimodalAnalysisTool instead.",
    DeprecationWarning,
    stacklevel=2
)

# memory_storage_tool.py
warnings.warn(
    "MemoryStorageTool is deprecated. Use UnifiedMemoryTool instead.",
    DeprecationWarning,
    stacklevel=2
)

# memory_v2_tool.py
warnings.warn(
    "MemoryV2Tool is deprecated. Use UnifiedMemoryTool instead.",
    DeprecationWarning,
    stacklevel=2
)

# mem0_memory_tool.py
warnings.warn(
    "Mem0MemoryTool is deprecated. Use UnifiedMemoryTool instead.",
    DeprecationWarning,
    stacklevel=2
)

# hipporag_continual_memory_tool.py
warnings.warn(
    "HippoRagContinualMemoryTool is deprecated. Use UnifiedMemoryTool instead.",
    DeprecationWarning,
    stacklevel=2
)
```

## Usage Tracking

### Metrics

Track usage of deprecated tools to understand migration progress:

```python
# In each deprecated tool
from ultimate_discord_intelligence_bot.obs.metrics import get_metrics

class DeprecatedTool(BaseTool):
    def __init__(self):
        super().__init__()
        self._metrics = get_metrics()
        self._usage_counter = self._metrics.counter("deprecated_tool_usage_total")

    def _run(self, *args, **kwargs):
        self._usage_counter.inc(labels={"tool": "DeprecatedTool"})
        warnings.warn("Deprecated tool usage detected", DeprecationWarning)
        # ... rest of implementation
```

### Dashboard

Monitor deprecation progress through observability dashboard:

- Usage counts for deprecated tools
- Migration progress by tool
- Error rates during migration period

## Removal Checklist

Before removing a deprecated tool:

- [ ] **Deprecation period expired** (2 release cycles)
- [ ] **Usage metrics show <5% usage** in last 30 days
- [ ] **Migration guide published** and accessible
- [ ] **All references updated** in codebase
- [ ] **Agent configurations updated** to use replacement tools
- [ ] **Tests updated** to use replacement tools
- [ ] **Documentation updated** to remove references
- [ ] **Import statements updated** in all files
- [ ] **MAPPING entry removed** from `tools/__init__.py`
- [ ] ****all** entry removed** from `tools/__init__.py`
- [ ] **Tool file deleted** from repository
- [ ] **Release notes updated** with removal notice

## Contact and Support

For questions about tool deprecations or migration:

- **Documentation:** [Tool Export Strategy](../development/tool_export_strategy.md)
- **Consolidation Report:** [Tool Consolidation Report](../tool_consolidation_report.md)
- **Issues:** Create GitHub issue with `deprecation` label
- **Discussions:** Use GitHub Discussions for migration questions

---

*Last Updated: 2024-01-XX*
*Next Review: 2024-02-XX*
