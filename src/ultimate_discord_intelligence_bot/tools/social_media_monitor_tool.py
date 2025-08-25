"""Aggregate basic social media chatter across platforms.

This lightweight tool simulates monitoring Reddit, X/Twitter and
Discord by scanning provided text snippets for a keyword. It
establishes the contract for future, API-driven implementations while
keeping unit tests fast and self-contained.
"""

from typing import Dict, List

from crewai_tools import BaseTool


class SocialMediaMonitorTool(BaseTool):
    """Collect posts mentioning a keyword across platforms."""

    name = "Social Media Monitor"
    description = (
        "Aggregate social media posts and return those containing the keyword"
    )

    def _run(self, posts: Dict[str, List[str]], keyword: str) -> dict:
        matches: Dict[str, List[str]] = {}
        lower = keyword.lower()
        for platform, items in posts.items():
            platform_matches = [p for p in items if lower in p.lower()]
            if platform_matches:
                matches[platform] = platform_matches
        return {"status": "success", "matches": matches}

    def run(self, *args, **kwargs):  # pragma: no cover - thin wrapper
        return self._run(*args, **kwargs)
