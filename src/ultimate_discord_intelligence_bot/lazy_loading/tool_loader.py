"""Lazy tool loader for deferred tool instantiation.

This module provides lazy loading capabilities for tools to reduce memory
footprint and improve startup performance.
"""

from __future__ import annotations
import importlib
import logging
from typing import Any
from platform.core.step_result import StepResult

logger = logging.getLogger(__name__)


class LazyToolLoader:
    """Lazy loader for tools with dependency management."""

    def __init__(self):
        """Initialize the lazy tool loader."""
        self._tool_cache: dict[str, Any] = {}
        self._dependency_cache: dict[str, bool] = {}
        self._import_cache: dict[str, Any] = {}

    def load_tool(self, tool_name: str, tool_class: str, module_path: str) -> Any:
        """Load a tool lazily with dependency checking."""
        cache_key = f"{tool_name}:{tool_class}:{module_path}"
        if cache_key in self._tool_cache:
            return self._tool_cache[cache_key]
        try:
            if not self._check_dependencies(tool_name):
                return self._create_fallback_tool(tool_name, "Missing dependencies")
            module = self._import_module(module_path)
            if module is None:
                return self._create_fallback_tool(tool_name, "Module import failed")
            tool_class_obj = getattr(module, tool_class, None)
            if tool_class_obj is None:
                return self._create_fallback_tool(tool_name, f"Class {tool_class} not found")
            tool_instance = tool_class_obj()
            self._tool_cache[cache_key] = tool_instance
            return tool_instance
        except Exception as e:
            logger.warning(f"Failed to load tool {tool_name}: {e}")
            return self._create_fallback_tool(tool_name, str(e))

    def _check_dependencies(self, tool_name: str) -> bool:
        """Check if all dependencies for a tool are available."""
        tool_dependencies = {
            "YtDlpDownloadTool": ["yt_dlp"],
            "DiscordDownloadTool": ["discord"],
            "InstagramDownloadTool": ["instaloader"],
            "TikTokDownloadTool": ["tiktok_scraper"],
            "TwitchDownloadTool": ["twitch"],
            "TwitterDownloadTool": ["tweepy"],
            "RedditDownloadTool": ["praw"],
            "KickDownloadTool": ["requests"],
            "AudioTranscriptionTool": ["whisper", "torch"],
            "EnhancedAnalysisTool": ["openai", "transformers"],
            "FactCheckTool": ["requests", "beautifulsoup4"],
            "MemoryStorageTool": ["qdrant_client"],
            "SystemStatusTool": ["psutil"],
            "MultimodalAnalysisTool": ["openai", "PIL"],
            "ImageAnalysisTool": ["PIL", "torchvision"],
            "VideoFrameAnalysisTool": ["cv2", "torch"],
            "SocialGraphAnalysisTool": ["networkx"],
            "LiveStreamAnalysisTool": ["websockets"],
            "AdvancedAudioAnalysisTool": ["librosa", "torch"],
            "TrendAnalysisTool": ["pandas", "numpy"],
            "TrendForecastingTool": ["scikit-learn", "pandas"],
            "VectorSearchTool": ["qdrant_client", "numpy"],
            "RagHybridTool": ["langchain", "qdrant_client"],
            "ResearchAndBriefTool": ["requests", "beautifulsoup4"],
            "StrategicPlanningTool": ["openai"],
            "NarrativeTrackerTool": ["requests"],
            "CrossPlatformNarrativeTrackingTool": ["requests"],
            "CollectiveIntelligenceTool": ["openai"],
            "InsightSharingTool": ["openai"],
            "KnowledgeOpsTool": ["qdrant_client"],
            "Mem0MemoryTool": ["mem0"],
            "GraphMemoryTool": ["networkx"],
            "HippoRagContinualMemoryTool": ["qdrant_client"],
            "OfflineRagTool": ["langchain"],
            "RagIngestTool": ["langchain", "qdrant_client"],
            "RagIngestUrlTool": ["langchain", "qdrant_client"],
            "RagQueryVectorStoreTool": ["langchain", "qdrant_client"],
            "UnifiedMemoryTool": ["qdrant_client"],
            "UnifiedMemoryStoreTool": ["qdrant_client"],
            "UnifiedContextTool": ["qdrant_client"],
            "UnifiedRouterTool": ["openai"],
            "CostTrackingTool": ["openai"],
            "RouterStatusTool": ["openai"],
            "UnifiedCacheTool": ["redis"],
            "CacheOptimizationTool": ["redis"],
            "UnifiedMetricsTool": ["prometheus_client"],
            "OrchestrationStatusTool": ["openai"],
            "ResourceAllocationTool": ["psutil"],
            "EscalationManagementTool": ["openai"],
            "QualityAssuranceTool": ["openai"],
            "PerformanceOptimizationTool": ["psutil"],
            "WorkflowOptimizationTool": ["openai"],
            "EarlyExitConditionsTool": ["openai"],
            "CheckpointManagementTool": ["openai"],
            "TaskRoutingTool": ["openai"],
            "ContentTypeRoutingTool": ["openai"],
            "AgentBridgeTool": ["openai"],
            "PipelineTool": ["openai"],
            "MCPCallTool": ["openai"],
            "FastMCPClientTool": ["openai"],
            "DependencyResolverTool": ["openai"],
            "StepResultAuditorTool": ["openai"],
            "ObservabilityTool": ["prometheus_client"],
        }
        dependencies = tool_dependencies.get(tool_name, [])
        if not dependencies:
            return True
        return all((self._check_dependency(dep) for dep in dependencies))

    def _check_dependency(self, dependency: str) -> bool:
        """Check if a specific dependency is available."""
        if dependency in self._dependency_cache:
            return self._dependency_cache[dependency]
        try:
            importlib.import_module(dependency)
            self._dependency_cache[dependency] = True
            return True
        except ImportError:
            self._dependency_cache[dependency] = False
            return False

    def _import_module(self, module_path: str) -> Any | None:
        """Import a module lazily with caching."""
        if module_path in self._import_cache:
            return self._import_cache[module_path]
        try:
            module = importlib.import_module(module_path)
            self._import_cache[module_path] = module
            return module
        except ImportError as e:
            logger.warning(f"Failed to import module {module_path}: {e}")
            return None

    def _create_fallback_tool(self, tool_name: str, error_message: str) -> Any:
        """Create a fallback tool when the real tool cannot be loaded."""

        class FallbackTool:
            def __init__(self, name: str, error: str):
                self.name = name
                self.description = f"{name} unavailable: {error}"
                self.error = error

            def run(self, *args, **kwargs) -> StepResult:
                return StepResult.fail(error=f"{self.name} is unavailable", details=self.error)

            def _run(self, *args, **kwargs) -> StepResult:
                return self.run(*args, **kwargs)

        return FallbackTool(tool_name, error_message)

    def clear_cache(self) -> None:
        """Clear all caches."""
        self._tool_cache.clear()
        self._dependency_cache.clear()
        self._import_cache.clear()

    def get_cache_stats(self) -> dict[str, int]:
        """Get cache statistics."""
        return {
            "tool_cache_size": len(self._tool_cache),
            "dependency_cache_size": len(self._dependency_cache),
            "import_cache_size": len(self._import_cache),
        }


_lazy_loader = LazyToolLoader()


def get_lazy_loader() -> LazyToolLoader:
    """Get the global lazy loader instance."""
    return _lazy_loader


def load_tool_lazy(tool_name: str, tool_class: str, module_path: str) -> Any:
    """Load a tool lazily using the global loader."""
    return _lazy_loader.load_tool(tool_name, tool_class, module_path)
