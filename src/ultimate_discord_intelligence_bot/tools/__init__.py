"""Tools package (lightweight).

Avoid importing all tool modules at package import time to prevent optional
dependencies from being required during unrelated imports/tests.
Import specific tools or submodules explicitly as needed.
"""

__all__ = [
    # Advertise common tool names without importing them eagerly.
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
    "FactCheckTool",
    "LeaderboardTool",
    # "DriveUploadTool",
    "LogicalFallacyTool",
    "MemoryStorageTool",
    "MultiPlatformDownloadTool",
    "MultiPlatformMonitorTool",
    "PerspectiveSynthesizerTool",
    "PodcastResolverTool",
    "SocialResolverTool",
    "TwitchResolverTool",
    "YouTubeResolverTool",
    "SentimentTool",
    "SocialMediaMonitorTool",
    "SteelmanArgumentTool",
    "SystemStatusTool",
    "TimelineTool",
    "TranscriptIndexTool",
    "TrustworthinessTrackerTool",
    "TruthScoringTool",
    "VectorSearchTool",
    "XMonitorTool",
    "InstagramDownloadTool",
    "KickDownloadTool",
    "RedditDownloadTool",
    "TikTokDownloadTool",
    "TwitchDownloadTool",
    "TwitterDownloadTool",
    "YouTubeDownloadTool",
    "YtDlpDownloadTool",
]


def __getattr__(name: str):  # PEP 562: lazy attribute loading
    # Minimal on-demand loader for tools used in tests without importing all heavy deps
    mapping = {
        "PerspectiveSynthesizerTool": ".perspective_synthesizer_tool",
    }
    mod = mapping.get(name)
    if mod is None:
        raise AttributeError(name)
    from importlib import import_module

    module = import_module(f"{__name__}{mod}")
    try:
        return getattr(module, name)
    except AttributeError as exc:  # pragma: no cover - defensive
        raise AttributeError(name) from exc
