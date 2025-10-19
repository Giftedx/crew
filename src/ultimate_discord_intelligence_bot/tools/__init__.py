"""Tools package (lightweight).

Avoid importing all tool modules at package import time to prevent optional
dependencies from being required during unrelated imports/tests.
Import specific tools or submodules explicitly as needed.
"""

MAPPING = {
    # Core analysis/download
    "AudioTranscriptionTool": ".audio_transcription_tool",
    "CharacterProfileTool": ".character_profile_tool",
    "ClaimExtractorTool": ".claim_extractor_tool",
    "ContentQualityAssessmentTool": ".content_quality_assessment_tool",
    "ContentTypeRoutingTool": ".content_type_routing_tool",
    "EarlyExitConditionsTool": ".early_exit_conditions_tool",
    "ContextVerificationTool": ".context_verification_tool",
    "DebateCommandTool": ".debate_command_tool",
    "DiscordDownloadTool": ".discord_download_tool",
    "DiscordMonitorTool": ".discord_monitor_tool",
    "DiscordPostTool": ".discord_post_tool",
    "DiscordPrivateAlertTool": ".discord_private_alert_tool",
    "DiscordQATool": ".discord_qa_tool",
    "DriveUploadTool": ".drive_upload_tool",
    "DriveUploadToolBypass": ".drive_upload_tool_bypass",
    "EnhancedAnalysisTool": ".enhanced_analysis_tool",
    "AdvancedPerformanceAnalyticsTool": ".advanced_performance_analytics_tool",
    "EnhancedYouTubeDownloadTool": ".enhanced_youtube_tool",
    "FactCheckTool": ".fact_check_tool",
    # RAG & Retrieval
    "LCSummarizeTool": ".lc_summarize_tool",
    "OfflineRAGTool": ".offline_rag_tool",
    "RagHybridTool": ".rag_hybrid_tool",
    "RagIngestTool": ".rag_ingest_tool",
    "RagIngestUrlTool": ".rag_ingest_url_tool",
    "RagQueryVectorStoreTool": ".rag_query_vs_tool",
    "GraphMemoryTool": ".graph_memory_tool",
    "HippoRagContinualMemoryTool": ".hipporag_continual_memory_tool",
    "LeaderboardTool": ".leaderboard_tool",
    "LogicalFallacyTool": ".logical_fallacy_tool",
    "Mem0MemoryTool": ".mem0_memory_tool",
    "MemoryStorageTool": ".memory_storage_tool",
    "MemoryCompactionTool": ".memory_compaction_tool",
    "MockVectorSearchTool": ".mock_vector_tool",
    "MultiPlatformDownloadTool": ".multi_platform_download_tool",
    "MultiPlatformMonitorTool": ".multi_platform_monitor_tool",
    # MCP & Research
    "MCPCallTool": ".mcp_call_tool",
    "FastMCPClientTool": ".fastmcp_client_tool",
    "MCPResourceTool": ".fastmcp_client_tool",
    "ResearchAndBriefTool": ".research_and_brief_tool",
    "ResearchAndBriefMultiTool": ".research_and_brief_multi_tool",
    "PerspectiveSynthesizerTool": ".perspective_synthesizer_tool",
    "PipelineTool": ".pipeline_tool",
    "PromptCompressionTool": ".prompt_compression_tool",
    "DeceptionScoringTool": ".deception_scoring_tool",
    "SystemStatusTool": ".system_status_tool",
    "TextAnalysisTool": ".text_analysis_tool",
    "TimelineTool": ".timeline_tool",
    "TranscriptIndexTool": ".transcript_index_tool",
    "TrustworthinessTrackerTool": ".trustworthiness_tracker_tool",
    "TruthScoringTool": ".truth_scoring_tool",
    "VectorSearchTool": ".vector_search_tool",
    "VowpalWabbitBanditTool": ".vowpal_wabbit_bandit_tool",
    "DSPyOptimizationTool": ".dspy_optimization_tool",
    "CheckpointManagementTool": ".checkpoint_management_tool",
    # Resolvers under platform_resolver
    "PodcastResolverTool": ".platform_resolver.podcast_resolver",
    "SocialResolverTool": ".platform_resolver.social_resolver",
    "TwitchResolverTool": ".platform_resolver.twitch_resolver",
    "YouTubeResolverTool": ".platform_resolver.youtube_resolver",
    # Social media + downloaders (all in yt_dlp_download_tool where applicable)
    "InstagramDownloadTool": ".yt_dlp_download_tool",
    "KickDownloadTool": ".yt_dlp_download_tool",
    "RedditDownloadTool": ".yt_dlp_download_tool",
    "SentimentTool": ".sentiment_tool",
    "SocialMediaMonitorTool": ".social_media_monitor_tool",
    "SteelmanArgumentTool": ".steelman_argument_tool",
    "TikTokDownloadTool": ".yt_dlp_download_tool",
    "TwitchDownloadTool": ".yt_dlp_download_tool",
    "TwitterDownloadTool": ".yt_dlp_download_tool",
    "XMonitorTool": ".x_monitor_tool",
    "YouTubeDownloadTool": ".yt_dlp_download_tool",
    "YtDlpDownloadTool": ".yt_dlp_download_tool",
    # Computer Vision & Multimodal AI Tools
    "VideoFrameAnalysisTool": ".video_frame_analysis_tool",
    "ImageAnalysisTool": ".image_analysis_tool",
    "VisualSummaryTool": ".visual_summary_tool",
    "AdvancedAudioAnalysisTool": ".advanced_audio_analysis_tool",
    "MultimodalAnalysisTool": ".multimodal_analysis_tool",
    "ContentGenerationTool": ".content_generation_tool",
    # Real-Time AI Processing Tools
    "LiveStreamAnalysisTool": ".live_stream_analysis_tool",
    "TrendAnalysisTool": ".trend_analysis_tool",
    "ViralityPredictionTool": ".virality_prediction_tool",
    # Predictive Analytics Tools
    "TrendForecastingTool": ".trend_forecasting_tool",
    "EngagementPredictionTool": ".engagement_prediction_tool",
    "ContentRecommendationTool": ".content_recommendation_tool",
    # Creator Network Intelligence Tools
    "SocialGraphAnalysisTool": ".social_graph_analysis_tool",
    "InstagramStoriesArchiverTool": ".instagram_stories_archiver_tool",
    "TikTokEnhancedDownloadTool": ".tiktok_enhanced_download_tool",
    "TwitterThreadReconstructorTool": ".twitter_thread_reconstructor_tool",
    "CrossPlatformNarrativeTrackingTool": ".cross_platform_narrative_tool",
}

__all__ = [
    "AudioTranscriptionTool",
    "CharacterProfileTool",
    "ClaimExtractorTool",
    "ContentQualityAssessmentTool",
    "ContentTypeRoutingTool",
    "EarlyExitConditionsTool",
    "ContextVerificationTool",
    "DebateCommandTool",
    "DiscordDownloadTool",
    "DiscordMonitorTool",
    "DiscordPostTool",
    "DiscordPrivateAlertTool",
    "DiscordQATool",
    "DriveUploadTool",
    "DriveUploadToolBypass",
    "EnhancedAnalysisTool",
    "AdvancedPerformanceAnalyticsTool",
    "EnhancedYouTubeDownloadTool",
    "FactCheckTool",
    # RAG & Retrieval
    "LCSummarizeTool",
    "OfflineRAGTool",
    "RagHybridTool",
    "RagIngestTool",
    "RagIngestUrlTool",
    "RagQueryVectorStoreTool",
    "GraphMemoryTool",
    "HippoRagContinualMemoryTool",
    "LeaderboardTool",
    "LogicalFallacyTool",
    "Mem0MemoryTool",
    "MemoryCompactionTool",
    "MemoryStorageTool",
    "MockVectorSearchTool",
    "MultiPlatformDownloadTool",
    "MultiPlatformMonitorTool",
    # MCP & Research
    "MCPCallTool",
    "FastMCPClientTool",
    "MCPResourceTool",
    "ResearchAndBriefTool",
    "ResearchAndBriefMultiTool",
    "PerspectiveSynthesizerTool",
    "PipelineTool",
    "PromptCompressionTool",
    "DeceptionScoringTool",
    "SystemStatusTool",
    "TextAnalysisTool",
    "TimelineTool",
    "TranscriptIndexTool",
    "TrustworthinessTrackerTool",
    "TruthScoringTool",
    "VectorSearchTool",
    "PodcastResolverTool",
    "SocialResolverTool",
    "TwitchResolverTool",
    "YoutubeTranscriptTool",
    "VowpalWabbitBanditTool",
    "DSPyOptimizationTool",
] + [
    "InstagramDownloadTool",
    "KickDownloadTool",
    "RedditDownloadTool",
    "SentimentTool",
    "SocialMediaMonitorTool",
    "SteelmanArgumentTool",
    "TikTokDownloadTool",
    "TwitchDownloadTool",
    "TwitterDownloadTool",
    "XMonitorTool",
    "YouTubeDownloadTool",
    "YtDlpDownloadTool",
    # Computer Vision & Multimodal AI Tools
    "VideoFrameAnalysisTool",
    "ImageAnalysisTool",
    "VisualSummaryTool",
    "AdvancedAudioAnalysisTool",
    "MultimodalAnalysisTool",
    "ContentGenerationTool",
    # Real-Time AI Processing Tools
    "LiveStreamAnalysisTool",
    "TrendAnalysisTool",
    "ViralityPredictionTool",
    # Predictive Analytics Tools
    "TrendForecastingTool",
    "EngagementPredictionTool",
    "ContentRecommendationTool",
    # Creator Network Intelligence Tools
    "SocialGraphAnalysisTool",
    "InstagramStoriesArchiverTool",
    "TikTokEnhancedDownloadTool",
    "TwitterThreadReconstructorTool",
    "CrossPlatformNarrativeTrackingTool",
]


def __getattr__(name: str):  # PEP 562: lazy attribute loading
    mod = MAPPING.get(name)
    if mod is None:
        raise AttributeError(name)
    from importlib import import_module

    try:
        module = import_module(f"{__name__}{mod}")
    except Exception as exc:  # Optional dependency or heavy module failed to import
        # Provide a soft-fail stub so imports don’t break across frameworks/scaffolds.
        # The stub mirrors a minimal tool surface and returns a StepResult.fail() when run.
        def _make_stub(_tool_name: str, _error: Exception):  # noqa: D401 - tiny helper
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
                        raise _error
                    return _StepResult.fail(
                        error=f"{_tool_name} is unavailable", details=str(_error)
                    )

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
