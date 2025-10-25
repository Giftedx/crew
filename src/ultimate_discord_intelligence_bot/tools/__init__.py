"""Tools package with hierarchical domain structure.

This package contains tools organized into domain-specific modules:
- acquisition: Content download and ingestion tools
- analysis: Content analysis and processing tools
- verification: Fact-checking and verification tools
- memory: Storage and retrieval tools
- observability: Monitoring and system health tools

Avoid importing all tool modules at package import time to prevent optional
dependencies from being required during unrelated imports/tests.
Import specific tools or submodules explicitly as needed.
"""

MAPPING = {
    # Acquisition tools
    "AudioTranscriptionTool": ".acquisition.audio_transcription_tool",
    "DiscordDownloadTool": ".acquisition.discord_download_tool",
    "InstagramStoriesArchiverTool": ".acquisition.instagram_stories_archiver_tool",
    "MultiPlatformDownloadTool": ".acquisition.multi_platform_download_tool",
    "RedditAPITool": ".acquisition.reddit_api_tool",
    "TikTokEnhancedDownloadTool": ".acquisition.tiktok_enhanced_download_tool",
    "TranscriptIndexTool": ".acquisition.transcript_index_tool",
    "TwitterAPITool": ".acquisition.twitter_api_tool",
    "YtDlpDownloadTool": ".acquisition.yt_dlp_download_tool",
    "PlaywrightAutomationTool": ".web.playwright_automation_tool",
    # Analysis tools
    "CharacterProfileTool": ".analysis.character_profile_tool",
    "ContentQualityAssessmentTool": ".analysis.content_quality_assessment_tool",
    "CrossPlatformNarrativeTrackingTool": ".analysis.cross_platform_narrative_tool",
    "EnhancedAnalysisTool": ".analysis.enhanced_analysis_tool",
    "ImageAnalysisTool": ".analysis.image_analysis_tool",
    "LiveStreamAnalysisTool": ".analysis.live_stream_analysis_tool",
    "LogicalFallacyTool": ".analysis.logical_fallacy_tool",
    "NarrativeTrackerTool": ".analysis.narrative_tracker_tool",
    "PerspectiveSynthesizerTool": ".analysis.perspective_synthesizer_tool",
    "ReanalysisTriggerTool": ".analysis.reanalysis_trigger_tool",
    "SentimentTool": ".analysis.sentiment_tool",
    "SmartClipComposerTool": ".analysis.smart_clip_composer_tool",
    "SocialGraphAnalysisTool": ".analysis.social_graph_analysis_tool",
    "TextAnalysisTool": ".analysis.text_analysis_tool",
    "TimelineTool": ".analysis.timeline_tool",
    "TrendAnalysisTool": ".analysis.trend_analysis_tool",
    "TrendForecastingTool": ".analysis.trend_forecasting_tool",
    "VideoFrameAnalysisTool": ".analysis.video_frame_analysis_tool",
    "ViralityPredictionTool": ".analysis.virality_prediction_tool",
    "MultimodalAnalysisTool": ".analysis.multimodal_analysis_tool",
    "OpenAIEnhancedAnalysisTool": ".analysis.openai_enhanced_analysis_tool",
    # Verification tools
    "ClaimVerifierTool": ".verification.claim_verifier_tool",
    "ConfidenceScoringTool": ".verification.confidence_scoring_tool",
    "ConsistencyCheckTool": ".verification.consistency_check_tool",
    "ContextVerificationTool": ".verification.context_verification_tool",
    "DeceptionScoringTool": ".verification.deception_scoring_tool",
    "FactCheckTool": ".verification.fact_check_tool",
    "OutputValidationTool": ".verification.output_validation_tool",
    "SponsorComplianceTool": ".verification.sponsor_compliance_tool",
    "TrustworthinessTrackerTool": ".verification.trustworthiness_tracker_tool",
    "TruthScoringTool": ".verification.truth_scoring_tool",
    # Memory tools
    "GraphMemoryTool": ".memory.graph_memory_tool",
    "HippoRagContinualMemoryTool": ".memory.hipporag_continual_memory_tool",
    "KnowledgeOpsTool": ".memory.knowledge_ops_tool",
    "LCSummarizeTool": ".memory.lc_summarize_tool",
    "Mem0MemoryTool": ".memory.mem0_memory_tool",
    "MemoryCompactionTool": ".memory.memory_compaction_tool",
    "MemoryStorageTool": ".memory.memory_storage_tool",
    "MockVectorSearchTool": ".memory.mock_vector_tool",
    "OfflineRAGTool": ".memory.offline_rag_tool",
    "PromptCompressionTool": ".memory.prompt_compression_tool",
    "RagHybridTool": ".memory.rag_hybrid_tool",
    "RagIngestTool": ".memory.rag_ingest_tool",
    "RagIngestUrlTool": ".memory.rag_ingest_url_tool",
    "RagQueryVectorStoreTool": ".memory.rag_query_vs_tool",
    "ResearchAndBriefMultiTool": ".memory.research_and_brief_multi_tool",
    "ResearchAndBriefTool": ".memory.research_and_brief_tool",
    "StrategicPlanningTool": ".memory.strategic_planning_tool",
    "UnifiedMemoryTool": ".memory.unified_memory_tool",
    "UnifiedMemoryStoreTool": ".memory.unified_memory_tool",
    "UnifiedContextTool": ".memory.unified_memory_tool",
    "VectorSearchTool": ".memory.vector_search_tool",
    "VowpalWabbitBanditTool": ".memory.vowpal_wabbit_bandit_tool",
    # Observability tools
    "AdvancedPerformanceAnalyticsTool": ".observability.advanced_performance_analytics_tool",
    "AgentBridgeTool": ".observability.agent_bridge_tool",
    "CheckpointManagementTool": ".observability.checkpoint_management_tool",
    "CollectiveIntelligenceTool": ".observability.agent_bridge_tool",
    "ContentTypeRoutingTool": ".observability.content_type_routing_tool",
    "DependencyResolverTool": ".observability.dependency_resolver_tool",
    "EarlyExitConditionsTool": ".observability.early_exit_conditions_tool",
    "EscalationManagementTool": ".observability.escalation_management_tool",
    "FastMCPClientTool": ".observability.fastmcp_client_tool",
    "IntelligentAlertingTool": ".observability.observability_tool",
    "DashboardIntegrationTool": ".observability.observability_tool",
    "MCPCallTool": ".observability.mcp_call_tool",
    "PipelineTool": ".observability.pipeline_tool",
    "ResourceAllocationTool": ".observability.resource_allocation_tool",
    "SystemStatusTool": ".observability.system_status_tool",
    "TaskRoutingTool": ".observability.task_routing_tool",
    "UnifiedCacheTool": ".observability.unified_cache_tool",
    "UnifiedMetricsTool": ".observability.observability_tool",
    "OrchestrationStatusTool": ".observability.unified_orchestration_tool",
    "CostTrackingTool": ".observability.unified_router_tool",
    "RouterStatusTool": ".observability.unified_router_tool",
    "UnifiedOrchestrationTool": ".observability.unified_orchestration_tool",
    "UnifiedRouterTool": ".observability.unified_router_tool",
    "WorkflowOptimizationTool": ".observability.workflow_optimization_tool",
    "InsightSharingTool": ".observability.agent_bridge_tool",
    "LearningTool": ".observability.agent_bridge_tool",
    # Memory optimization and DSPy tooling
    "DSPyOptimizationTool": ".memory.dspy_optimization_tool",
    # Root tools (not moved to domains)
    "ClaimExtractorTool": ".claim_extractor_tool",
    "ContentGenerationTool": ".content_generation_tool",
    "DebateCommandTool": ".debate_command_tool",
    "DiscordMonitorTool": ".discord_monitor_tool",
    "DiscordPostTool": ".discord_post_tool",
    "DiscordPrivateAlertTool": ".discord_private_alert_tool",
    "DiscordQATool": ".discord_qa_tool",
    "DriveUploadTool": ".drive_upload_tool",
    "LeaderboardTool": ".leaderboard_tool",
    "MultiPlatformMonitorTool": ".multi_platform_monitor_tool",
    "SocialMediaMonitorTool": ".social_media_monitor_tool",
    "TwitterThreadReconstructorTool": ".twitter_thread_reconstructor_tool",
    "XMonitorTool": ".x_monitor_tool",
    # Resolvers under platform_resolver
    "PodcastResolverTool": ".platform_resolver.podcast_resolver",
    "SocialResolverTool": ".platform_resolver.social_resolver",
    "TwitchResolverTool": ".platform_resolver.twitch_resolver",
    "YouTubeResolverTool": ".platform_resolver.youtube_resolver",
    # Social media + downloaders (all in yt_dlp_download_tool where applicable)
    "InstagramDownloadTool": ".acquisition.yt_dlp_download_tool",
    "KickDownloadTool": ".acquisition.yt_dlp_download_tool",
    "RedditDownloadTool": ".acquisition.yt_dlp_download_tool",
    "TikTokDownloadTool": ".acquisition.yt_dlp_download_tool",
    "TwitchDownloadTool": ".acquisition.yt_dlp_download_tool",
    "TwitterDownloadTool": ".acquisition.yt_dlp_download_tool",
}

__all__ = [
    # Analysis tools
    # Observability tools
    "AdvancedPerformanceAnalyticsTool",
    "AgentBridgeTool",
    # Acquisition tools
    "AudioTranscriptionTool",
    "CharacterProfileTool",
    "CheckpointManagementTool",
    # Root tools
    "ClaimExtractorTool",
    # Verification tools
    "ClaimVerifierTool",
    "CollectiveIntelligenceTool",
    "ConfidenceScoringTool",
    "ConsistencyCheckTool",
    "ContentQualityAssessmentTool",
    "ContentTypeRoutingTool",
    "ContextVerificationTool",
    "CostTrackingTool",
    "CrossPlatformNarrativeTrackingTool",
    # Memory tools
    "DSPyOptimizationTool",
    "DashboardIntegrationTool",
    "DebateCommandTool",
    "DeceptionScoringTool",
    "DependencyResolverTool",
    "DiscordDownloadTool",
    "DiscordMonitorTool",
    "DiscordPostTool",
    "DiscordPrivateAlertTool",
    "DiscordQATool",
    "DriveUploadTool",
    "EarlyExitConditionsTool",
    "EnhancedAnalysisTool",
    "EscalationManagementTool",
    "FactCheckTool",
    "FastMCPClientTool",
    "GraphMemoryTool",
    "HippoRagContinualMemoryTool",
    "ImageAnalysisTool",
    "InsightSharingTool",
    # Social media downloaders
    "InstagramDownloadTool",
    "InstagramStoriesArchiverTool",
    "IntelligentAlertingTool",
    "KickDownloadTool",
    "KnowledgeOpsTool",
    "LCSummarizeTool",
    "LeaderboardTool",
    "LearningTool",
    "LiveStreamAnalysisTool",
    "LogicalFallacyTool",
    "MCPCallTool",
    "Mem0MemoryTool",
    "MemoryCompactionTool",
    "MemoryStorageTool",
    "MockVectorSearchTool",
    "MultiPlatformDownloadTool",
    "MultiPlatformMonitorTool",
    "MultimodalAnalysisTool",
    "NarrativeTrackerTool",
    "OfflineRAGTool",
    "OrchestrationStatusTool",
    "OutputValidationTool",
    "PerspectiveSynthesizerTool",
    "PipelineTool",
    # Resolvers
    "PodcastResolverTool",
    "PromptCompressionTool",
    "RagHybridTool",
    "RagIngestTool",
    "RagIngestUrlTool",
    "RagQueryVectorStoreTool",
    "ReanalysisTriggerTool",
    "RedditAPITool",
    "RedditDownloadTool",
    "ResearchAndBriefMultiTool",
    "ResearchAndBriefTool",
    "ResourceAllocationTool",
    "RouterStatusTool",
    "SentimentTool",
    "SmartClipComposerTool",
    "SocialGraphAnalysisTool",
    "SocialMediaMonitorTool",
    "SocialResolverTool",
    "SponsorComplianceTool",
    "StrategicPlanningTool",
    "SystemStatusTool",
    "TaskRoutingTool",
    "TextAnalysisTool",
    "TikTokDownloadTool",
    "TikTokEnhancedDownloadTool",
    "TimelineTool",
    "TranscriptIndexTool",
    "TrendAnalysisTool",
    "TrendForecastingTool",
    "TrustworthinessTrackerTool",
    "TruthScoringTool",
    "TwitchDownloadTool",
    "TwitchResolverTool",
    "TwitterAPITool",
    "TwitterDownloadTool",
    "TwitterThreadReconstructorTool",
    "UnifiedCacheTool",
    "UnifiedContextTool",
    "UnifiedMemoryStoreTool",
    "UnifiedMemoryTool",
    "UnifiedMetricsTool",
    "UnifiedOrchestrationTool",
    "UnifiedRouterTool",
    "VectorSearchTool",
    "VideoFrameAnalysisTool",
    "ViralityPredictionTool",
    "VowpalWabbitBanditTool",
    "WorkflowOptimizationTool",
    "XMonitorTool",
    "YouTubeResolverTool",
    "YtDlpDownloadTool",
]


def __getattr__(name: str):  # PEP 562: lazy attribute loading
    mod = MAPPING.get(name)
    if mod is None:
        raise AttributeError(name)
    from importlib import import_module

    try:
        module = import_module(f"{__name__}{mod}")
    except Exception as exc:  # Optional dependency or heavy module failed to import
        # Provide a soft-fail stub so imports don't break across frameworks/scaffolds.
        # The stub mirrors a minimal tool surface and returns a StepResult.fail() when run.
        def _make_stub(_tool_name: str, _error: Exception):
            class _MissingDependencyTool:
                name = _tool_name
                description = f"{_tool_name} unavailable: optional dependencies missing ({type(_error).__name__})"

                def run(self, *args, **kwargs):  # pragma: no cover - trivial
                    try:
                        from ..step_result import (
                            StepResult as _StepResult,  # lazy import per call
                        )
                    except Exception:
                        # Last-resort preserve original import error
                        raise _error from None
                    return _StepResult.fail(error=f"{_tool_name} is unavailable", details=str(_error))

            _MissingDependencyTool.__name__ = _tool_name
            return _MissingDependencyTool

        return _make_stub(name, exc)

    try:
        return getattr(module, name)
    except AttributeError as exc:  # pragma: no cover - defensive
        raise AttributeError(name) from exc


def __dir__():
    # Expose lazy-exported names to introspection and linters
    return sorted(list(globals().keys()) + __all__)
