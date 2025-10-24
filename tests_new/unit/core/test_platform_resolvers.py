import importlib
from typing import Any

from ultimate_discord_intelligence_bot.tools.platform_resolver.podcast_resolver import (
    PodcastResolverTool,
)
from ultimate_discord_intelligence_bot.tools.platform_resolver.social_resolver import (
    SocialResolverTool,
)
from ultimate_discord_intelligence_bot.tools.platform_resolver.twitch_resolver import (
    TwitchResolverTool,
)
from ultimate_discord_intelligence_bot.tools.platform_resolver.youtube_resolver import (
    YouTubeResolverTool,
)


def test_youtube_resolver_success():
    tool = YouTubeResolverTool()
    res = tool.run("@SomeHandle")
    assert res.success is True
    assert isinstance(res.data, dict)
    payload = _unpack(res.data)
    assert payload.get("handle") == "@SomeHandle"
    assert "url" in payload


def test_social_resolver_success():
    tool = SocialResolverTool()
    res = tool.run("twitter", "user123")
    assert res.success is True
    payload = _unpack(res.data)
    assert payload.get("handle") == "@user123"
    assert payload.get("url") == "https://twitter.com/user123"


essential_pod_keys = {"rss_url", "directory_urls"}


def test_podcast_resolver_success_known_mapping():
    tool = PodcastResolverTool()
    res = tool.run("Lex Fridman")
    assert res.success is True
    payload = _unpack(res.data)
    assert set(payload.keys()) & essential_pod_keys == essential_pod_keys


def test_twitch_resolver_success():
    tool = TwitchResolverTool()
    res = tool.run("Ninja")
    assert res.success is True
    payload = _unpack(res.data)
    assert payload.get("handle") == "Ninja"  # Twitch resolver returns raw handle without '@'
    assert payload.get("url") == "https://twitch.tv/Ninja"


def test_youtube_resolver_error_path(monkeypatch):
    # Monkeypatch helper to raise and assert StepResult.fail
    mod = importlib.import_module("ultimate_discord_intelligence_bot.tools.platform_resolver.youtube_resolver")

    def boom(_handle: str):
        raise RuntimeError("forced failure")

    monkeypatch.setattr(mod, "resolve_youtube_handle", boom)
    tool = YouTubeResolverTool()
    res = tool.run("@boom")
    assert res.success is False
    assert "forced failure" in (res.error or "")


def _unpack(data: dict[str, Any] | Any) -> dict[str, Any]:
    """Normalize StepResult.data to a flat dict for assertions.

    Accepts cases where the result is {"data": {...}} or already a flat dict.
    """
    if isinstance(data, dict):
        inner = data.get("data")
        if isinstance(inner, dict):
            return inner
        return data
    return {}
