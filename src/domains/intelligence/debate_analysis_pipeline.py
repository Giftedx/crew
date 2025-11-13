"""Minimal stub for DebateAnalysisPipeline to allow DebateCommandTool to initialize."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from collections.abc import Callable


class DebateAnalysisPipeline:
    """Minimal stub implementation of DebateAnalysisPipeline."""

    def __init__(
        self,
        ethan_defender: Callable[[str], str] | None = None,
        hasan_defender: Callable[[str], str] | None = None,
    ):
        """Initialize the debate analysis pipeline stub."""
        self.ethan_defender = ethan_defender
        self.hasan_defender = hasan_defender

        # Create minimal stub components
        self.index_tool = StubIndexTool()
        self.fact_checker = StubFactChecker()
        self.leaderboard = StubLeaderboard()
        self.timeline = StubTimeline()
        self.trust_tracker = StubTrustTracker()
        self.profile_tool = StubProfileTool()


class StubIndexTool:
    """Stub index tool."""

    def get_context(self, video_id: str, ts: float = 0.0) -> dict[str, Any]:
        """Return stub context."""
        return {"video_id": video_id, "timestamp": ts, "context": "stub implementation"}


class StubFactChecker:
    """Stub fact checker."""

    def run(self, claim: str) -> dict[str, Any]:
        """Return stub fact check result."""
        return {"verdict": "unknown", "evidence": [], "claim": claim}


class StubLeaderboard:
    """Stub leaderboard."""

    def update_scores(self, person: str, lies: int, misquotes: int, misinfo: int) -> None:
        """Stub score update."""

    def get_top(self, n: int = 10) -> list[dict[str, Any]]:
        """Return stub leaderboard."""
        return []


class StubTimeline:
    """Stub timeline."""

    def get_timeline(self, video_id: str) -> list[dict[str, Any]]:
        """Return stub timeline."""
        return []


class StubTrustTracker:
    """Stub trust tracker."""

    def run(self, person: str, is_truthful: bool) -> None:
        """Stub trust tracking."""


class StubProfileTool:
    """Stub profile tool."""

    def get_profile(self, person: str) -> dict[str, Any]:
        """Return stub profile."""
        return {"person": person, "events": []}

    def record_event(self, person: str, event: dict[str, Any]) -> None:
        """Stub event recording."""
