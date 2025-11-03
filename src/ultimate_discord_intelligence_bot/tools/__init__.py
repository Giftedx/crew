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
    # Acquisition tools (migrated to domains/ingestion/providers/)
    "AudioTranscriptionTool": "domains.ingestion.providers.audio_transcription_tool",
    "DiscordDownloadTool": "domains.ingestion.providers.discord_download_tool",
    "InstagramStoriesArchiverTool": "domains.ingestion.providers.instagram_stories_archiver_tool",
    "MultiPlatformDownloadTool": "domains.ingestion.providers.multi_platform_download_tool",
    "RedditAPITool": "domains.ingestion.providers.reddit_api_tool",
    "TikTokEnhancedDownloadTool": "domains.ingestion.providers.tiktok_enhanced_download_tool",
    "TranscriptIndexTool": "domains.ingestion.providers.transcript_index_tool",
    "TwitterAPITool": "domains.ingestion.providers.twitter_api_tool",
    "YtDlpDownloadTool": "domains.ingestion.providers.yt_dlp_download_tool",
    "PlaywrightAutomationTool": ".web.playwright_automation_tool",
    # Analysis tools (migrated to domains/intelligence/analysis/)
    "CharacterProfileTool": "domains.intelligence.analysis.character_profile_tool",
    "ContentQualityAssessmentTool": "domains.intelligence.analysis.content_quality_assessment_tool",
    "CrossPlatformNarrativeTrackingTool": "domains.intelligence.analysis.cross_platform_narrative_tool",
    "EnhancedAnalysisTool": "domains.intelligence.analysis.enhanced_analysis_tool",
    "ImageAnalysisTool": "domains.intelligence.analysis.image_analysis_tool",
    "LiveStreamAnalysisTool": "domains.intelligence.analysis.live_stream_analysis_tool",
    "LogicalFallacyTool": "domains.intelligence.analysis.logical_fallacy_tool",
    "NarrativeTrackerTool": "domains.intelligence.analysis.narrative_tracker_tool",
    "PerspectiveSynthesizerTool": "domains.intelligence.analysis.perspective_synthesizer_tool",
    "ReanalysisTriggerTool": "domains.intelligence.analysis.reanalysis_trigger_tool",
    "SentimentTool": "domains.intelligence.analysis.sentiment_tool",
    "SmartClipComposerTool": "domains.intelligence.analysis.smart_clip_composer_tool",
    "SocialGraphAnalysisTool": "domains.intelligence.analysis.social_graph_analysis_tool",
    "TextAnalysisTool": "domains.intelligence.analysis.text_analysis_tool",
    "TimelineTool": "domains.intelligence.analysis.timeline_tool",
    "TrendAnalysisTool": "domains.intelligence.analysis.trend_analysis_tool",
    "TrendForecastingTool": "domains.intelligence.analysis.trend_forecasting_tool",
    "VideoFrameAnalysisTool": "domains.intelligence.analysis.video_frame_analysis_tool",
    "ViralityPredictionTool": "domains.intelligence.analysis.virality_prediction_tool",
    "MultimodalAnalysisTool": "domains.intelligence.analysis.multimodal_analysis_tool",
    "OpenAIEnhancedAnalysisTool": "domains.intelligence.analysis.openai_enhanced_analysis_tool",
    # Verification tools (migrated to domains/intelligence/verification/)
    "ClaimVerifierTool": "domains.intelligence.verification.claim_verifier_tool",
    "ConfidenceScoringTool": "domains.intelligence.verification.confidence_scoring_tool",
    "ConsistencyCheckTool": "domains.intelligence.verification.consistency_check_tool",
    "ContextVerificationTool": "domains.intelligence.verification.context_verification_tool",
    "DeceptionScoringTool": "domains.intelligence.verification.deception_scoring_tool",
    "FactCheckTool": "domains.intelligence.verification.fact_check_tool",
    "GovernancePolicyTool": "domains.intelligence.verification.governance_policy_tool",
    "OutputValidationTool": "domains.intelligence.verification.output_validation_tool",
    "SponsorComplianceTool": "domains.intelligence.verification.sponsor_compliance_tool",
    "TrustworthinessTrackerTool": "domains.intelligence.verification.trustworthiness_tracker_tool",
    "TruthScoringTool": "domains.intelligence.verification.truth_scoring_tool",
    # Memory tools (migrated to domains/memory/vector/)
    "GraphMemoryTool": "domains.memory.vector.graph_memory_tool",
    "HippoRagContinualMemoryTool": "domains.memory.vector.hipporag_continual_memory_tool",
    "KnowledgeOpsTool": "domains.memory.vector.knowledge_ops_tool",
    "LCSummarizeTool": "domains.memory.vector.lc_summarize_tool",
    "Mem0MemoryTool": "domains.memory.vector.mem0_memory_tool",
    "MemoryCompactionTool": "domains.memory.vector.memory_compaction_tool",
    "MemoryStorageTool": "domains.memory.vector.memory_storage_tool",
    "MockVectorSearchTool": "domains.memory.vector.mock_vector_tool",
    "OfflineRAGTool": "domains.memory.vector.offline_rag_tool",
    "PromptCompressionTool": "domains.memory.vector.prompt_compression_tool",
    "RagHybridTool": "domains.memory.vector.rag_hybrid_tool",
    "RagIngestTool": "domains.memory.vector.rag_ingest_tool",
    "RagIngestUrlTool": "domains.memory.vector.rag_ingest_url_tool",
    "RagQueryVectorStoreTool": "domains.memory.vector.rag_query_vs_tool",
    "ResearchAndBriefMultiTool": "domains.memory.vector.research_and_brief_multi_tool",
    "ResearchAndBriefTool": "domains.memory.vector.research_and_brief_tool",
    "StrategicPlanningTool": "domains.memory.vector.strategic_planning_tool",
    "UnifiedMemoryTool": "domains.memory.vector.unified_memory_tool",
    "UnifiedMemoryStoreTool": "domains.memory.vector.unified_memory_tool",
    "UnifiedContextTool": "domains.memory.vector.unified_memory_tool",
    "VectorSearchTool": "domains.memory.vector.vector_search_tool",
    "VowpalWabbitBanditTool": "domains.memory.vector.vowpal_wabbit_bandit_tool",
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
    # Memory optimization and DSPy tooling (migrated to domains/memory/vector/)
    "DSPyOptimizationTool": "domains.memory.vector.dspy_optimization_tool",
    # Root tools (some migrated to domains/, others remain)
    "ClaimExtractorTool": "domains.intelligence.analysis.claim_extractor_tool",
    "ContentGenerationTool": ".content_generation_tool",
    "DebateCommandTool": "domains.intelligence.analysis.debate_command_tool",
    "DiscordMonitorTool": ".discord_monitor_tool",
    "DiscordPostTool": ".discord_post_tool",
    "DiscordPrivateAlertTool": ".discord_private_alert_tool",
    "DiscordQATool": ".discord_qa_tool",
    "DriveUploadTool": ".drive_upload_tool",
    "LeaderboardTool": "domains.intelligence.analysis.leaderboard_tool",
    "MultiPlatformMonitorTool": ".multi_platform_monitor_tool",
    "SocialMediaMonitorTool": ".social_media_monitor_tool",
    "TwitterThreadReconstructorTool": ".twitter_thread_reconstructor_tool",
    "XMonitorTool": ".x_monitor_tool",
    # Resolvers (migrated to domains/ingestion/providers/)
    "PodcastResolverTool": "domains.ingestion.providers.podcast_resolver",
    "SocialResolverTool": "domains.ingestion.providers.social_resolver",
    "TwitchResolverTool": "domains.ingestion.providers.twitch_resolver",
    "YouTubeResolverTool": "domains.ingestion.providers.youtube_resolver",
    # Social media + downloaders (all in yt_dlp_download_tool where applicable)
    "InstagramDownloadTool": ".acquisition.yt_dlp_download_tool",
    "KickDownloadTool": ".acquisition.yt_dlp_download_tool",
    "RedditDownloadTool": ".acquisition.yt_dlp_download_tool",
    "TikTokDownloadTool": ".acquisition.yt_dlp_download_tool",
    "TwitchDownloadTool": ".acquisition.yt_dlp_download_tool",
    "TwitterDownloadTool": ".acquisition.yt_dlp_download_tool",
}

__all__ = [
    # Combined exports from all domains; kept alphabetically sorted for RUF022 compliance
    "AdvancedPerformanceAnalyticsTool",
    "AgentBridgeTool",
    "AudioTranscriptionTool",
    "CharacterProfileTool",
    "CheckpointManagementTool",
    "ClaimExtractorTool",
    "ClaimVerifierTool",
    "CollectiveIntelligenceTool",
    "ConfidenceScoringTool",
    "ConsistencyCheckTool",
    "ContentQualityAssessmentTool",
    "ContentTypeRoutingTool",
    "ContextVerificationTool",
    "CostTrackingTool",
    "CrossPlatformNarrativeTrackingTool",
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
    "PlaywrightAutomationTool",
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
        # Handle both relative (starting with '.') and absolute imports
        if mod.startswith('.'):
            module_path = f"{__name__}{mod}"
        else:
            # Absolute import (e.g., 'domains.intelligence.analysis.social_graph_analysis_tool')
            module_path = mod
        module = import_module(module_path)
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
