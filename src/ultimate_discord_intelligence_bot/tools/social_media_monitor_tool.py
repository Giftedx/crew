"""Aggregate basic social media chatter across platforms.

This lightweight tool simulates monitoring Reddit, X/Twitter and
Discord by scanning provided text snippets for a keyword. It
establishes the contract for future, API-driven implementations while
keeping unit tests fast and self-contained.
"""

from crewai.tools import BaseTool


class SocialMediaMonitorTool(BaseTool):
    """Collect posts mentioning a keyword across platforms."""

    name: str = "Social Media Monitor"
    description: str = "Aggregate social media posts and return those containing the keyword"

    def _run(self, posts: dict[str, list[str]], keyword: str) -> dict[str, object]:
        matches: dict[str, list[str]] = {}
        lower = keyword.lower()
        for platform, items in posts.items():
            platform_matches = [p for p in items if lower in p.lower()]
            if platform_matches:
                matches[platform] = platform_matches
        return {"status": "success", "matches": matches}

