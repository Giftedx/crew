from __future__ import annotations

import os
from typing import Any

from ultimate_discord_intelligence_bot.agent_training.performance_monitor import (
    AgentPerformanceMonitor,
)


class ToolContainer:
    """Container for all bot tools with graceful degradation."""

    def __init__(self):
        # Core legacy tools (backward compatibility)
        self.pipeline_tool = None
        self.youtube_tool = None
        self.analysis_tool = None
        self.vector_tool = None
        self.fact_check_tool = None
        self.fallacy_tool = None
        self.debate_tool = None

        # Comprehensive set
        self.audio_transcription_tool = None
        self.character_profile_tool = None
        self.claim_extractor_tool = None
        self.context_verification_tool = None
        self.discord_download_tool = None
        self.discord_monitor_tool = None
        self.discord_post_tool = None
        self.discord_private_alert_tool = None
        self.discord_qa_tool = None
        self.instagram_download_tool = None
        self.kick_download_tool = None
        self.leaderboard_tool = None
        self.memory_storage_tool = None
        # V2 tools using unified facades
        self.cache_v2_tool = None
        self.memory_v2_tool = None
        self.multi_platform_download_tool = None
        self.multi_platform_monitor_tool = None
        self.perspective_synthesizer_tool = None
        self.podcast_resolver_tool = None
        self.reddit_download_tool = None
        self.sentiment_tool = None
        self.social_media_monitor_tool = None
        self.social_resolver_tool = None
        self.steelman_argument_tool = None
        self.system_status_tool = None
        self.tiktok_download_tool = None
        self.timeline_tool = None
        self.transcript_index_tool = None
        self.trustworthiness_tracker_tool = None
        self.truth_scoring_tool = None
        self.twitch_download_tool = None
        self.twitch_resolver_tool = None
        self.twitter_download_tool = None
        self.x_monitor_tool = None
        self.youtube_resolver_tool = None
        self.yt_dlp_download_tool = None
        self.text_analysis_tool = None

    def get_all_tools(self) -> dict[str, Any]:
        return {name: tool for name, tool in self.__dict__.items() if tool is not None}


def load_tools() -> ToolContainer:
    tools = ToolContainer()

    # Lazy import tools package and loader helpers
    try:
        try:
            from scripts.helpers.tools_loader import (
                get_comprehensive_tool_specs,
                get_core_tool_specs,
                get_discord_tool_specs,
                get_tool_class,
                load_tools_from_specs,
                safe_instantiate,
            )
        except ImportError:
            # Fallback if scripts.helpers is unavailable (e.g., when installed as a package)
            def get_tool_class(tools_module, name):  # type: ignore[no-redef]
                try:
                    cls = getattr(tools_module, name)
                    if os.getenv("DEBUG_TOOLS") == "true":
                        print(f"🔎 Resolved tool class {name}: {cls!r}")
                    return cls
                except Exception as exc:  # pragma: no cover - defensive
                    print(f"⚠️  Could not resolve tool class {name}: {exc}")
                    return None

            def safe_instantiate(
                tool_class, tools_container, attr_name, *args, **kwargs
            ):  # type: ignore[no-redef]
                if tool_class is None:
                    return False
                try:
                    tool_instance = tool_class(*args, **kwargs)
                    setattr(tools_container, attr_name, tool_instance)
                    return True
                except (
                    Exception
                ) as exc:  # pragma: no cover - tool instantiation failure
                    print(f"⚠️  Failed to load {attr_name}: {exc}")
                    return False

            def _core_specs(tools_module):
                return [
                    (
                        get_tool_class(tools_module, "PipelineTool"),
                        "pipeline_tool",
                        (),
                        {},
                    ),
                    (
                        get_tool_class(tools_module, "EnhancedYouTubeDownloadTool"),
                        "youtube_tool",
                        (),
                        {},
                    ),
                    (
                        get_tool_class(tools_module, "EnhancedAnalysisTool"),
                        "analysis_tool",
                        (),
                        {},
                    ),
                    (
                        get_tool_class(tools_module, "MockVectorSearchTool"),
                        "vector_tool",
                        (),
                        {},
                    ),
                    (
                        get_tool_class(tools_module, "FactCheckTool"),
                        "fact_check_tool",
                        (),
                        {},
                    ),
                    (
                        get_tool_class(tools_module, "LogicalFallacyTool"),
                        "fallacy_tool",
                        (),
                        {},
                    ),
                    (
                        get_tool_class(tools_module, "DebateCommandTool"),
                        "debate_tool",
                        (),
                        {},
                    ),
                ]

            def _comprehensive_specs(tools_module):
                specs = [
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
                    (
                        get_tool_class(tools_module, "DiscordQATool"),
                        "discord_qa_tool",
                        (),
                        {},
                    ),
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
                    (
                        get_tool_class(tools_module, "LeaderboardTool"),
                        "leaderboard_tool",
                        (),
                        {},
                    ),
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
                    (
                        get_tool_class(tools_module, "SentimentTool"),
                        "sentiment_tool",
                        (),
                        {},
                    ),
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
                    (
                        get_tool_class(tools_module, "TimelineTool"),
                        "timeline_tool",
                        (),
                        {},
                    ),
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
                    (
                        get_tool_class(tools_module, "VectorSearchTool"),
                        "vector_tool",
                        (),
                        {},
                    ),
                    (
                        get_tool_class(tools_module, "XMonitorTool"),
                        "x_monitor_tool",
                        (),
                        {},
                    ),
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
                    (
                        get_tool_class(tools_module, "DriveUploadTool"),
                        "drive_upload_tool",
                        (),
                        {},
                    ),
                    (
                        get_tool_class(tools_module, "DriveUploadToolBypass"),
                        "drive_upload_bypass_tool",
                        (),
                        {},
                    ),
                ]

                specs.extend(get_discord_tool_specs(tools_module))
                return specs

            def _discord_specs(tools_module):
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
                    print(
                        "⚠️  DiscordPrivateAlertTool skipped - no DISCORD_PRIVATE_WEBHOOK configured"
                    )

                return specs

            def load_tools_from_specs(tools_container, specs):  # type: ignore[no-redef]
                for cls, name, args, kwargs in specs:
                    safe_instantiate(cls, tools_container, name, *args, **kwargs)

            get_core_tool_specs = _core_specs  # type: ignore[assignment]
            get_comprehensive_tool_specs = _comprehensive_specs  # type: ignore[assignment]
            get_discord_tool_specs = _discord_specs  # type: ignore[assignment]

        from ultimate_discord_intelligence_bot import tools as t  # type: ignore
    except Exception:
        return tools

    core_specs = get_core_tool_specs(t)
    load_tools_from_specs(tools, core_specs)
    comprehensive_specs = get_comprehensive_tool_specs(t)
    load_tools_from_specs(tools, comprehensive_specs)

    # Load V2 tools using unified facades
    try:
        # Cache V2 tool
        if hasattr(t, "cache_v2_tool") and t.cache_v2_tool is not None:
            tools.cache_v2_tool = safe_instantiate(t.cache_v2_tool.CacheV2Tool)
            print("✅ Cache V2 tool loaded (unified facade)")
    except Exception as e:
        print(f"⚠️ Cache V2 tool not available: {e}")

    try:
        # Memory V2 tool
        if hasattr(t, "memory_v2_tool") and t.memory_v2_tool is not None:
            tools.memory_v2_tool = safe_instantiate(t.memory_v2_tool.MemoryV2Tool)
            print("✅ Memory V2 tool loaded (unified facade)")
    except Exception as e:
        print(f"⚠️ Memory V2 tool not available: {e}")

    return tools


def attach_tools(bot: Any, tools: ToolContainer) -> None:
    for tool_name, tool_instance in tools.__dict__.items():
        setattr(bot, tool_name, tool_instance)

    try:
        setattr(bot, "get_all_tools", tools.get_all_tools)
    except Exception:
        pass

    bot.performance_monitor = AgentPerformanceMonitor()

    all_tools = tools.get_all_tools()
    if all_tools:
        core_tools = []
        for name in [
            "pipeline_tool",
            "youtube_tool",
            "analysis_tool",
            "vector_tool",
            "fact_check_tool",
            "fallacy_tool",
            "debate_tool",
        ]:
            if getattr(tools, name, None) is not None:
                core_tools.append(name.replace("_tool", ""))

        additional_count = len(all_tools) - len(core_tools)
        display_tools = (
            core_tools + [f"+{additional_count} more"]
            if additional_count > 0
            else core_tools
        )
        print(
            f"🔧 Tools attached: {', '.join(display_tools) if display_tools else 'none'}"
        )
        print(f"📊 Total tools loaded: {len(all_tools)}")

        if os.getenv("DEBUG_TOOLS") == "true":
            all_tool_names = sorted([name.replace("_tool", "") for name in all_tools])
            print(f"🔍 All loaded tools: {', '.join(all_tool_names)}")
    else:
        print("🔧 Tools attached: none")


__all__ = ["ToolContainer", "load_tools", "attach_tools"]
