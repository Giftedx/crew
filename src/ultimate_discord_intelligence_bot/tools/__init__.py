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
    "EnhancedYouTubeDownloadTool": ".enhanced_youtube_tool",
    "FactCheckTool": ".fact_check_tool",
    "LeaderboardTool": ".leaderboard_tool",
    "LogicalFallacyTool": ".logical_fallacy_tool",
    "MemoryStorageTool": ".memory_storage_tool",
    "MockVectorSearchTool": ".mock_vector_tool",
    "MultiPlatformDownloadTool": ".multi_platform_download_tool",
    "MultiPlatformMonitorTool": ".multi_platform_monitor_tool",
    "PerspectiveSynthesizerTool": ".perspective_synthesizer_tool",
    "PipelineTool": ".pipeline_tool",
    "SystemStatusTool": ".system_status_tool",
    "TextAnalysisTool": ".text_analysis_tool",
    "TimelineTool": ".timeline_tool",
    "TranscriptIndexTool": ".transcript_index_tool",
    "TrustworthinessTrackerTool": ".trustworthiness_tracker_tool",
    "TruthScoringTool": ".truth_scoring_tool",
    "VectorSearchTool": ".vector_search_tool",
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
}

__all__ = [
    "AudioTranscriptionTool",
    "CharacterProfileTool",
    "ClaimExtractorTool",
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
    "EnhancedYouTubeDownloadTool",
    "FactCheckTool",
    "LeaderboardTool",
    "LogicalFallacyTool",
    "MemoryStorageTool",
    "MockVectorSearchTool",
    "MultiPlatformDownloadTool",
    "MultiPlatformMonitorTool",
    "PerspectiveSynthesizerTool",
    "PipelineTool",
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
    "YouTubeResolverTool",
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
]


def __getattr__(name: str):  # PEP 562: lazy attribute loading
    mod = MAPPING.get(name)
    if mod is None:
        raise AttributeError(name)
    from importlib import import_module

    module = import_module(f"{__name__}{mod}")
    try:
        return getattr(module, name)
    except AttributeError as exc:  # pragma: no cover - defensive
        raise AttributeError(name) from exc


def __dir__():
    # Expose lazy-exported names to introspection and linters
    return sorted(list(globals().keys()) + __all__)
