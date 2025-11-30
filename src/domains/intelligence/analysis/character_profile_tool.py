"""Aggregate per-person trust metrics and events.

This module provides the `CharacterProfileTool`, which persists events related
to individuals (e.g., statements, actions) and aggregates trust statistics
from various sources like leaderboards and trust trackers.
"""

from __future__ import annotations

import json
from platform.cache.tool_cache_decorator import cache_tool_result
from typing import TYPE_CHECKING, Any, ClassVar, TypedDict

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult
from ultimate_discord_intelligence_bot.tools.settings import BASE_DIR

from ..verification.trustworthiness_tracker_tool import TrustworthinessTrackerTool
from ._base import BaseTool
from .leaderboard_tool import LeaderboardTool


if TYPE_CHECKING:
    from pathlib import Path


class _ProfileLeaderboardSection(TypedDict):
    """Leaderboard statistics for a profile.

    Attributes:
        lies: Count of lies detected.
        misquotes: Count of misquotes attributed.
        misinfo: Count of misinformation instances.
    """

    lies: int
    misquotes: int
    misinfo: int


class _ProfileTrustSection(TypedDict, total=False):
    """Trust metrics for a profile.

    Attributes:
        truths: Count of verified truths.
        lies: Count of verified lies.
        score: Calculated trust score (typically 0.0 to 1.0).
    """

    truths: int
    lies: int
    score: float


class _ProfileResult(TypedDict):
    """Complete character profile result.

    Attributes:
        person: Name of the person.
        events: List of recorded events/actions.
        leaderboard: Leaderboard statistics.
        trust: Trustworthiness metrics.
    """

    person: str
    events: list[dict[str, object]]
    leaderboard: _ProfileLeaderboardSection
    trust: _ProfileTrustSection


class CharacterProfileTool(BaseTool[StepResult]):
    """Store per-person events and summarise trust statistics.

    This tool acts as a central registry for character profiles, combining
    event logs with quantitative metrics from the leaderboard and trust
    tracking systems.
    """

    name: str = "Character Profile Tool"
    description: str = "Persist events with sources and return combined trust metrics for a person."
    model_config: ClassVar[dict[str, Any]] = {"extra": "allow"}

    def __init__(
        self,
        storage_path: Path | None = None,
        leaderboard: LeaderboardTool | None = None,
        trust_tracker: TrustworthinessTrackerTool | None = None,
    ) -> None:
        """Initialize the CharacterProfileTool.

        Args:
            storage_path: Path to the JSON file for storing profiles.
            leaderboard: Instance of LeaderboardTool for retrieving rankings.
            trust_tracker: Instance of TrustworthinessTrackerTool for trust scores.
        """
        super().__init__()
        self._metrics = get_metrics()
        self.storage_path = storage_path or BASE_DIR / "character_profiles.json"
        self.leaderboard = leaderboard or LeaderboardTool()
        self.trust_tracker = trust_tracker or TrustworthinessTrackerTool()
        if not self.storage_path.exists():
            self._save({})

    def _load(self) -> dict[str, dict[str, list[dict[str, object]]]]:
        """Load profile data from storage.

        Returns:
            dict: The loaded profile data structure.
        """
        try:
            with self.storage_path.open("r", encoding="utf-8") as f:
                raw: Any = json.load(f)
        except Exception:
            return {}
        if not isinstance(raw, dict):
            return {}
        out: dict[str, dict[str, list[dict[str, object]]]] = {}
        for person, payload in raw.items():
            if not isinstance(person, str) or not isinstance(payload, dict):
                continue
            events_val = payload.get("events", [])
            if not isinstance(events_val, list):
                events_list: list[dict[str, object]] = []
            else:
                events_list = [ev for ev in events_val if isinstance(ev, dict)]
            out[person] = {"events": events_list}
        return out

    def _save(self, data: dict[str, dict[str, list[dict[str, object]]]]) -> None:
        """Save profile data to storage.

        Args:
            data: The profile data to save.
        """
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with self.storage_path.open("w", encoding="utf-8") as f:
            json.dump(data, f)

    def record_event(self, person: str, event: dict[str, object]) -> None:
        """Record a new event for a person.

        Args:
            person: Name of the person.
            event: Dictionary describing the event.
        """
        data = self._load()
        profile = data.get(person, {"events": []})
        profile["events"].append(event)
        data[person] = profile
        self._save(data)

    def get_profile(self, person: str) -> _ProfileResult:
        """Retrieve the complete profile for a person.

        Aggregates data from local storage, the leaderboard, and the trust tracker.

        Args:
            person: Name of the person.

        Returns:
            _ProfileResult: The aggregated profile data.
        """
        data = self._load()
        profile = data.get(person, {"events": []})
        board = self.leaderboard.get_person(person) or {"person": person, "lies": 0, "misquotes": 0, "misinfo": 0}
        raw_trust = self.trust_tracker._load().get(person, {"truths": 0, "lies": 0, "score": 0.0})
        trust: _ProfileTrustSection = {
            "truths": int(raw_trust.get("truths", 0)),
            "lies": int(raw_trust.get("lies", 0)),
            "score": float(raw_trust.get("score", 0.0)),
        }
        return {
            "person": person,
            "events": profile.get("events", []),
            "leaderboard": {
                "lies": board.get("lies", 0),
                "misquotes": board.get("misquotes", 0),
                "misinfo": board.get("misinfo", 0),
            },
            "trust": trust,
        }

    @cache_tool_result(namespace="tool:character_profile", ttl=3600)
    def _run(self, person: str) -> StepResult:
        """Execute the tool to retrieve a person's profile.

        Args:
            person: Name of the person to look up.

        Returns:
            StepResult: Result containing the profile data.
        """
        if not person or not person.strip():
            self._metrics.counter("tool_runs_total", labels={"tool": "character_profile", "outcome": "skipped"}).inc()
            return StepResult.skip(reason="empty person")
        profile = self.get_profile(person)
        self._metrics.counter("tool_runs_total", labels={"tool": "character_profile", "outcome": "success"}).inc()
        return StepResult.ok(data={"profile": profile})

    def run(self, *args, **kwargs) -> StepResult:
        """Public interface for running the tool.

        Extracts arguments and delegates to `_run`.

        Args:
            *args: Positional arguments (expects person name at index 0).
            **kwargs: Keyword arguments (expects 'person' or 'name').

        Returns:
            StepResult: The result of the operation.
        """
        try:
            person = str(args[0]) if args and len(args) > 0 else str(kwargs.get("person", kwargs.get("name", "")))
            return self._run(person)
        except Exception as exc:
            self._metrics.counter("tool_runs_total", labels={"tool": "character_profile", "outcome": "error"}).inc()
            return StepResult.fail(error=str(exc))
