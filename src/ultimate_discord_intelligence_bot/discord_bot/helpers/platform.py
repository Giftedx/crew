from __future__ import annotations

import re


def _infer_platform(url: str) -> tuple[str, str]:
    """Infer platform from a URL and return (platform, description).

    This mirrors the behavior used by tests in tests/test_command_helpers.py
    without depending on discord runtime imports.
    """
    u = url.lower().strip()
    patterns: list[tuple[str, str, str]] = [
        (r"youtube\.com|youtu\.be", "YouTube", "Commentary video detected (YouTube)"),
        (r"twitch\.tv", "Twitch", "Live/archived stream (Twitch)"),
        (r"kick\.com", "Kick", "Stream content (Kick)"),
        (r"x\.com|twitter\.com", "Twitter", "Social video (X/Twitter)"),
        (r"instagram\.com", "Instagram", "Reel/post (Instagram)"),
        (r"reddit\.com|redd\.it", "Reddit", "Reddit-hosted media"),
    ]
    for pat, name, desc in patterns:
        if re.search(pat, u):
            return name, desc
    return "Unknown", "Pending resolver (unknown platform)"


# Backward-compatible alias with older type hints (Tuple)
def _infer_platform_legacy(
    url: str,
) -> tuple[str, str]:  # pragma: no cover - legacy alias
    return _infer_platform(url)


__all__ = ["_infer_platform", "_infer_platform_legacy"]
