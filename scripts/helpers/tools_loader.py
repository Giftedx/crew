"""Helper functions for loading and managing tools."""

import os


def get_tool_class(tools_module, name: str):
    """Get a tool class from the tools module with error handling."""
    try:
        cls = getattr(tools_module, name)
        if os.getenv("DEBUG_TOOLS") == "true":
            print(f"🔎 Resolved tool class {name}: {cls!r}")
        return cls
    except Exception as e:
        print(f"⚠️  Could not resolve tool class {name}: {e}")
        return None


def safe_instantiate(tool_class, tools_container, attr_name, *args, **kwargs) -> bool:
    """Safely instantiate a tool class and add it to the container."""
    if tool_class is not None:
        try:
            tool_instance = tool_class(*args, **kwargs)
            setattr(tools_container, attr_name, tool_instance)
            return True
        except Exception as e:
            print(f"⚠️  Failed to load {attr_name}: {e}")
            return False
    return False


def get_core_tool_specs(tools_module) -> list[tuple]:
    """Get specifications for core tools."""
    return [
        (get_tool_class(tools_module, "PipelineTool"), "pipeline_tool", (), {}),
        (
            get_tool_class(tools_module, "EnhancedYouTubeDownloadTool"),
            "youtube_tool",
            (),
            {},
        ),
        (get_tool_class(tools_module, "EnhancedAnalysisTool"), "analysis_tool", (), {}),
        (get_tool_class(tools_module, "MockVectorSearchTool"), "vector_tool", (), {}),
        (get_tool_class(tools_module, "FactCheckTool"), "fact_check_tool", (), {}),
        (get_tool_class(tools_module, "LogicalFallacyTool"), "fallacy_tool", (), {}),
        (get_tool_class(tools_module, "DebateCommandTool"), "debate_tool", (), {}),
    ]


def get_comprehensive_tool_specs(tools_module) -> list[tuple]:
    """Get specifications for comprehensive tool set."""
    specs: list[tuple] = [
        (
            get_tool_class(tools_module, "AudioTranscriptionTool"),
            "audio_transcription_tool",
            (),
            {},
        ),
        (
            get_tool_class(tools_module, "CharacterProfileTool"),
            "character_profile_tool",
            (),
            {},
        ),
        (
            get_tool_class(tools_module, "ClaimExtractorTool"),
            "claim_extractor_tool",
            (),
            {},
        ),
        (
            get_tool_class(tools_module, "ContextVerificationTool"),
            "context_verification_tool",
            (),
            {},
        ),
        (
            get_tool_class(tools_module, "DiscordDownloadTool"),
            "discord_download_tool",
            (),
            {},
        ),
        (
            get_tool_class(tools_module, "DiscordMonitorTool"),
            "discord_monitor_tool",
            (),
            {},
        ),
        (get_tool_class(tools_module, "DiscordQATool"), "discord_qa_tool", (), {}),
        (
            get_tool_class(tools_module, "InstagramDownloadTool"),
            "instagram_download_tool",
            (),
            {},
        ),
        (
            get_tool_class(tools_module, "KickDownloadTool"),
            "kick_download_tool",
            (),
            {},
        ),
        (get_tool_class(tools_module, "LeaderboardTool"), "leaderboard_tool", (), {}),
        (
            get_tool_class(tools_module, "MemoryStorageTool"),
            "memory_storage_tool",
            (),
            {},
        ),
        (
            get_tool_class(tools_module, "MultiPlatformDownloadTool"),
            "multi_platform_download_tool",
            (),
            {},
        ),
        (
            get_tool_class(tools_module, "MultiPlatformMonitorTool"),
            "multi_platform_monitor_tool",
            (),
            {},
        ),
        (
            get_tool_class(tools_module, "PerspectiveSynthesizerTool"),
            "perspective_synthesizer_tool",
            (),
            {},
        ),
        (
            get_tool_class(tools_module, "DeceptionScoringTool"),
            "deception_scoring_tool",
            (),
            {},
        ),
        (
            get_tool_class(tools_module, "PodcastResolverTool"),
            "podcast_resolver_tool",
            (),
            {},
        ),
        (
            get_tool_class(tools_module, "RedditDownloadTool"),
            "reddit_download_tool",
            (),
            {},
        ),
        (get_tool_class(tools_module, "SentimentTool"), "sentiment_tool", (), {}),
        (
            get_tool_class(tools_module, "SocialMediaMonitorTool"),
            "social_media_monitor_tool",
            (),
            {},
        ),
        (
            get_tool_class(tools_module, "SocialResolverTool"),
            "social_resolver_tool",
            (),
            {},
        ),
        (
            get_tool_class(tools_module, "SteelmanArgumentTool"),
            "steelman_argument_tool",
            (),
            {},
        ),
        (
            get_tool_class(tools_module, "SystemStatusTool"),
            "system_status_tool",
            (),
            {},
        ),
        (
            get_tool_class(tools_module, "TikTokDownloadTool"),
            "tiktok_download_tool",
            (),
            {},
        ),
        (get_tool_class(tools_module, "TimelineTool"), "timeline_tool", (), {}),
        (
            get_tool_class(tools_module, "TranscriptIndexTool"),
            "transcript_index_tool",
            (),
            {},
        ),
        (
            get_tool_class(tools_module, "TrustworthinessTrackerTool"),
            "trustworthiness_tracker_tool",
            (),
            {},
        ),
        (
            get_tool_class(tools_module, "TruthScoringTool"),
            "truth_scoring_tool",
            (),
            {},
        ),
        (
            get_tool_class(tools_module, "TwitchDownloadTool"),
            "twitch_download_tool",
            (),
            {},
        ),
        (
            get_tool_class(tools_module, "TwitchResolverTool"),
            "twitch_resolver_tool",
            (),
            {},
        ),
        (
            get_tool_class(tools_module, "TwitterDownloadTool"),
            "twitter_download_tool",
            (),
            {},
        ),
        (get_tool_class(tools_module, "VectorSearchTool"), "vector_tool", (), {}),
        (get_tool_class(tools_module, "XMonitorTool"), "x_monitor_tool", (), {}),
        (
            get_tool_class(tools_module, "YouTubeDownloadTool"),
            "youtube_resolver_tool",
            (),
            {},
        ),
        (
            get_tool_class(tools_module, "YouTubeResolverTool"),
            "youtube_resolver_tool",
            (),
            {},
        ),
        (
            get_tool_class(tools_module, "YtDlpDownloadTool"),
            "yt_dlp_download_tool",
            (),
            {},
        ),
        (
            get_tool_class(tools_module, "TextAnalysisTool"),
            "text_analysis_tool",
            (),
            {},
        ),
        (get_tool_class(tools_module, "DriveUploadTool"), "drive_upload_tool", (), {}),
        (
            get_tool_class(tools_module, "DriveUploadToolBypass"),
            "drive_upload_bypass_tool",
            (),
            {},
        ),
    ]

    # Add Discord tools if webhooks are configured
    specs.extend(get_discord_tool_specs(tools_module))

    return specs


def get_discord_tool_specs(tools_module) -> list[tuple]:
    """Get Discord-specific tool specifications based on webhook configuration."""
    specs = []

    discord_webhook = os.getenv("DISCORD_WEBHOOK", "")
    discord_private_webhook = os.getenv("DISCORD_PRIVATE_WEBHOOK", "")

    if discord_webhook:
        specs.append(
            (
                get_tool_class(tools_module, "DiscordPostTool"),
                "discord_post_tool",
                (discord_webhook,),
                {},
            )
        )
    else:
        print("⚠️  DiscordPostTool skipped - no DISCORD_WEBHOOK configured")

    if discord_private_webhook:
        specs.append(
            (
                get_tool_class(tools_module, "DiscordPrivateAlertTool"),
                "discord_private_alert_tool",
                (discord_private_webhook,),
                {},
            )
        )
    else:
        print("⚠️  DiscordPrivateAlertTool skipped - no DISCORD_PRIVATE_WEBHOOK configured")

    return specs


def load_tools_from_specs(tools_container, specs: list[tuple]) -> None:
    """Load tools from specifications into the container."""
    for cls, name, args, kwargs in specs:
        safe_instantiate(cls, tools_container, name, *args, **kwargs)
