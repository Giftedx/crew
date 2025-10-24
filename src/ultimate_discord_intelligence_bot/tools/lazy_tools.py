"""Lazy loading wrapper for tools.

This module provides lazy loading capabilities for tools to reduce memory
footprint and improve startup performance.
"""

from __future__ import annotations

import logging
from typing import Any

from ultimate_discord_intelligence_bot.lazy_loading import get_lazy_loader
from ultimate_discord_intelligence_bot.step_result import StepResult


logger = logging.getLogger(__name__)

# Tool mapping for lazy loading
LAZY_TOOL_MAPPING = {
    # Acquisition tools
    "AudioTranscriptionTool": {
        "class": "AudioTranscriptionTool",
        "module": "ultimate_discord_intelligence_bot.tools.acquisition.audio_transcription_tool",
        "dependencies": ["whisper", "torch"],
    },
    "DiscordDownloadTool": {
        "class": "DiscordDownloadTool",
        "module": "ultimate_discord_intelligence_bot.tools.acquisition.discord_download_tool",
        "dependencies": ["discord"],
    },
    "MultiPlatformDownloadTool": {
        "class": "MultiPlatformDownloadTool",
        "module": "ultimate_discord_intelligence_bot.tools.acquisition.multi_platform_download_tool",
        "dependencies": ["yt_dlp"],
    },
    "YtDlpDownloadTool": {
        "class": "YtDlpDownloadTool",
        "module": "ultimate_discord_intelligence_bot.tools.acquisition.yt_dlp_download_tool",
        "dependencies": ["yt_dlp"],
    },
    "MultiPlatformDownloadTool": {
        "class": "MultiPlatformDownloadTool",
        "module": "ultimate_discord_intelligence_bot.tools.acquisition.multi_platform_download_tool",
        "dependencies": ["yt_dlp"],
    },
    "TranscriptIndexTool": {
        "class": "TranscriptIndexTool",
        "module": "ultimate_discord_intelligence_bot.tools.acquisition.transcript_index_tool",
        "dependencies": [],
    },
    # Analysis tools
    "EnhancedAnalysisTool": {
        "class": "EnhancedAnalysisTool",
        "module": "ultimate_discord_intelligence_bot.tools.analysis.enhanced_analysis_tool",
        "dependencies": ["openai", "transformers"],
    },
    "TextAnalysisTool": {
        "class": "TextAnalysisTool",
        "module": "ultimate_discord_intelligence_bot.tools.analysis.text_analysis_tool",
        "dependencies": ["openai"],
    },
    "SentimentTool": {
        "class": "SentimentTool",
        "module": "ultimate_discord_intelligence_bot.tools.analysis.sentiment_tool",
        "dependencies": ["openai"],
    },
    "LogicalFallacyTool": {
        "class": "LogicalFallacyTool",
        "module": "ultimate_discord_intelligence_bot.tools.analysis.logical_fallacy_tool",
        "dependencies": ["openai"],
    },
    "ClaimExtractorTool": {
        "class": "ClaimExtractorTool",
        "module": "ultimate_discord_intelligence_bot.tools.analysis.claim_extractor_tool",
        "dependencies": ["openai"],
    },
    "TrendAnalysisTool": {
        "class": "TrendAnalysisTool",
        "module": "ultimate_discord_intelligence_bot.tools.analysis.trend_analysis_tool",
        "dependencies": ["pandas", "numpy"],
    },
    "MultimodalAnalysisTool": {
        "class": "MultimodalAnalysisTool",
        "module": "ultimate_discord_intelligence_bot.tools.analysis.multimodal_analysis_tool",
        "dependencies": ["openai", "PIL"],
    },
    "ImageAnalysisTool": {
        "class": "ImageAnalysisTool",
        "module": "ultimate_discord_intelligence_bot.tools.analysis.image_analysis_tool",
        "dependencies": ["PIL", "torchvision"],
    },
    "VideoFrameAnalysisTool": {
        "class": "VideoFrameAnalysisTool",
        "module": "ultimate_discord_intelligence_bot.tools.analysis.video_frame_analysis_tool",
        "dependencies": ["cv2", "torch"],
    },
    "SocialGraphAnalysisTool": {
        "class": "SocialGraphAnalysisTool",
        "module": "ultimate_discord_intelligence_bot.tools.analysis.social_graph_analysis_tool",
        "dependencies": ["networkx"],
    },
    "LiveStreamAnalysisTool": {
        "class": "LiveStreamAnalysisTool",
        "module": "ultimate_discord_intelligence_bot.tools.analysis.live_stream_analysis_tool",
        "dependencies": ["websockets"],
    },
    "AdvancedAudioAnalysisTool": {
        "class": "AdvancedAudioAnalysisTool",
        "module": "ultimate_discord_intelligence_bot.tools.analysis.advanced_audio_analysis_tool",
        "dependencies": ["librosa", "torch"],
    },
    # Verification tools
    "FactCheckTool": {
        "class": "FactCheckTool",
        "module": "ultimate_discord_intelligence_bot.tools.verification.fact_check_tool",
        "dependencies": ["requests", "beautifulsoup4"],
    },
    "ClaimVerifierTool": {
        "class": "ClaimVerifierTool",
        "module": "ultimate_discord_intelligence_bot.tools.verification.claim_verifier_tool",
        "dependencies": ["openai"],
    },
    "TruthScoringTool": {
        "class": "TruthScoringTool",
        "module": "ultimate_discord_intelligence_bot.tools.verification.truth_scoring_tool",
        "dependencies": ["openai"],
    },
    "DeceptionScoringTool": {
        "class": "DeceptionScoringTool",
        "module": "ultimate_discord_intelligence_bot.tools.verification.deception_scoring_tool",
        "dependencies": ["openai"],
    },
    "ContextVerificationTool": {
        "class": "ContextVerificationTool",
        "module": "ultimate_discord_intelligence_bot.tools.verification.context_verification_tool",
        "dependencies": ["openai"],
    },
    "ConsistencyCheckTool": {
        "class": "ConsistencyCheckTool",
        "module": "ultimate_discord_intelligence_bot.tools.verification.consistency_check_tool",
        "dependencies": ["openai"],
    },
    "OutputValidationTool": {
        "class": "OutputValidationTool",
        "module": "ultimate_discord_intelligence_bot.tools.verification.output_validation_tool",
        "dependencies": ["openai"],
    },
    "TrustworthinessTrackerTool": {
        "class": "TrustworthinessTrackerTool",
        "module": "ultimate_discord_intelligence_bot.tools.verification.trustworthiness_tracker_tool",
        "dependencies": ["openai"],
    },
    # Memory tools
    "MemoryStorageTool": {
        "class": "MemoryStorageTool",
        "module": "ultimate_discord_intelligence_bot.tools.memory.memory_storage_tool",
        "dependencies": ["qdrant_client"],
    },
    "UnifiedMemoryTool": {
        "class": "UnifiedMemoryTool",
        "module": "ultimate_discord_intelligence_bot.tools.memory.unified_memory_tool",
        "dependencies": ["qdrant_client"],
    },
    "Mem0MemoryTool": {
        "class": "Mem0MemoryTool",
        "module": "ultimate_discord_intelligence_bot.tools.memory.mem0_memory_tool",
        "dependencies": ["mem0"],
    },
    "GraphMemoryTool": {
        "class": "GraphMemoryTool",
        "module": "ultimate_discord_intelligence_bot.tools.memory.graph_memory_tool",
        "dependencies": ["networkx"],
    },
    "VectorSearchTool": {
        "class": "VectorSearchTool",
        "module": "ultimate_discord_intelligence_bot.tools.memory.vector_search_tool",
        "dependencies": ["qdrant_client", "numpy"],
    },
    "RagHybridTool": {
        "class": "RagHybridTool",
        "module": "ultimate_discord_intelligence_bot.tools.memory.rag_hybrid_tool",
        "dependencies": ["langchain", "qdrant_client"],
    },
    "ResearchAndBriefTool": {
        "class": "ResearchAndBriefTool",
        "module": "ultimate_discord_intelligence_bot.tools.memory.research_and_brief_tool",
        "dependencies": ["requests", "beautifulsoup4"],
    },
    "ResearchAndBriefMultiTool": {
        "class": "ResearchAndBriefMultiTool",
        "module": "ultimate_discord_intelligence_bot.tools.memory.research_and_brief_multi_tool",
        "dependencies": ["requests", "beautifulsoup4"],
    },
    "StrategicPlanningTool": {
        "class": "StrategicPlanningTool",
        "module": "ultimate_discord_intelligence_bot.tools.memory.strategic_planning_tool",
        "dependencies": ["openai"],
    },
    "KnowledgeOpsTool": {
        "class": "KnowledgeOpsTool",
        "module": "ultimate_discord_intelligence_bot.tools.memory.knowledge_ops_tool",
        "dependencies": ["qdrant_client"],
    },
    # Observability tools
    "SystemStatusTool": {
        "class": "SystemStatusTool",
        "module": "ultimate_discord_intelligence_bot.tools.observability.system_status_tool",
        "dependencies": ["psutil"],
    },
    "AdvancedPerformanceAnalyticsTool": {
        "class": "AdvancedPerformanceAnalyticsTool",
        "module": "ultimate_discord_intelligence_bot.tools.observability.advanced_performance_analytics_tool",
        "dependencies": ["psutil", "pandas"],
    },
    "PipelineTool": {
        "class": "PipelineTool",
        "module": "ultimate_discord_intelligence_bot.tools.observability.pipeline_tool",
        "dependencies": ["openai"],
    },
    "MCPCallTool": {
        "class": "MCPCallTool",
        "module": "ultimate_discord_intelligence_bot.tools.observability.mcp_call_tool",
        "dependencies": ["openai"],
    },
    "CheckpointManagementTool": {
        "class": "CheckpointManagementTool",
        "module": "ultimate_discord_intelligence_bot.tools.observability.checkpoint_management_tool",
        "dependencies": ["openai"],
    },
    "UnifiedRouterTool": {
        "class": "UnifiedRouterTool",
        "module": "ultimate_discord_intelligence_bot.tools.observability.unified_router_tool",
        "dependencies": ["openai"],
    },
    "CostTrackingTool": {
        "class": "CostTrackingTool",
        "module": "ultimate_discord_intelligence_bot.tools.observability.cost_tracking_tool",
        "dependencies": ["openai"],
    },
    "RouterStatusTool": {
        "class": "RouterStatusTool",
        "module": "ultimate_discord_intelligence_bot.tools.observability.router_status_tool",
        "dependencies": ["openai"],
    },
    "UnifiedCacheTool": {
        "class": "UnifiedCacheTool",
        "module": "ultimate_discord_intelligence_bot.tools.observability.unified_cache_tool",
        "dependencies": ["redis"],
    },
    "CacheOptimizationTool": {
        "class": "CacheOptimizationTool",
        "module": "ultimate_discord_intelligence_bot.tools.observability.cache_optimization_tool",
        "dependencies": ["redis"],
    },
    "UnifiedMetricsTool": {
        "class": "UnifiedMetricsTool",
        "module": "ultimate_discord_intelligence_bot.tools.observability.unified_metrics_tool",
        "dependencies": ["prometheus_client"],
    },
    "OrchestrationStatusTool": {
        "class": "OrchestrationStatusTool",
        "module": "ultimate_discord_intelligence_bot.tools.observability.orchestration_status_tool",
        "dependencies": ["openai"],
    },
    "ResourceAllocationTool": {
        "class": "ResourceAllocationTool",
        "module": "ultimate_discord_intelligence_bot.tools.observability.resource_allocation_tool",
        "dependencies": ["psutil"],
    },
    "EscalationManagementTool": {
        "class": "EscalationManagementTool",
        "module": "ultimate_discord_intelligence_bot.tools.observability.escalation_management_tool",
        "dependencies": ["openai"],
    },
    "QualityAssuranceTool": {
        "class": "QualityAssuranceTool",
        "module": "ultimate_discord_intelligence_bot.tools.observability.quality_assurance_tool",
        "dependencies": ["openai"],
    },
    "PerformanceOptimizationTool": {
        "class": "PerformanceOptimizationTool",
        "module": "ultimate_discord_intelligence_bot.tools.observability.performance_optimization_tool",
        "dependencies": ["psutil"],
    },
    "WorkflowOptimizationTool": {
        "class": "WorkflowOptimizationTool",
        "module": "ultimate_discord_intelligence_bot.tools.observability.workflow_optimization_tool",
        "dependencies": ["openai"],
    },
    "EarlyExitConditionsTool": {
        "class": "EarlyExitConditionsTool",
        "module": "ultimate_discord_intelligence_bot.tools.observability.early_exit_conditions_tool",
        "dependencies": ["openai"],
    },
    "TaskRoutingTool": {
        "class": "TaskRoutingTool",
        "module": "ultimate_discord_intelligence_bot.tools.observability.task_routing_tool",
        "dependencies": ["openai"],
    },
    "ContentTypeRoutingTool": {
        "class": "ContentTypeRoutingTool",
        "module": "ultimate_discord_intelligence_bot.tools.observability.content_type_routing_tool",
        "dependencies": ["openai"],
    },
    "AgentBridgeTool": {
        "class": "AgentBridgeTool",
        "module": "ultimate_discord_intelligence_bot.tools.observability.agent_bridge_tool",
        "dependencies": ["openai"],
    },
    "DependencyResolverTool": {
        "class": "DependencyResolverTool",
        "module": "ultimate_discord_intelligence_bot.tools.observability.dependency_resolver_tool",
        "dependencies": ["openai"],
    },
    "StepResultAuditorTool": {
        "class": "StepResultAuditorTool",
        "module": "ultimate_discord_intelligence_bot.tools.observability.step_result_auditor",
        "dependencies": ["openai"],
    },
    "ObservabilityTool": {
        "class": "ObservabilityTool",
        "module": "ultimate_discord_intelligence_bot.tools.observability.observability_tool",
        "dependencies": ["prometheus_client"],
    },
}


def load_tool_lazy(tool_name: str) -> Any:
    """Load a tool lazily with dependency checking."""
    if tool_name not in LAZY_TOOL_MAPPING:
        logger.warning(f"Unknown tool: {tool_name}")
        return _create_fallback_tool(tool_name, "Unknown tool")

    tool_config = LAZY_TOOL_MAPPING[tool_name]
    lazy_loader = get_lazy_loader()

    return lazy_loader.load_tool(
        tool_name=tool_name, tool_class=tool_config["class"], module_path=tool_config["module"]
    )


def _create_fallback_tool(tool_name: str, error_message: str) -> Any:
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


def get_lazy_tool_stats() -> dict[str, Any]:
    """Get statistics about lazy tool loading."""
    lazy_loader = get_lazy_loader()
    return lazy_loader.get_cache_stats()


def clear_lazy_tool_cache() -> None:
    """Clear the lazy tool cache."""
    lazy_loader = get_lazy_loader()
    lazy_loader.clear_cache()
