"""Aggregate per-person trust metrics and events."""

from __future__ import annotations

import json
from pathlib import Path

from crewai.tools import BaseTool

from .. import settings
from .leaderboard_tool import LeaderboardTool
from .trustworthiness_tracker_tool import TrustworthinessTrackerTool


class CharacterProfileTool(BaseTool):
    """Store per-person events and summarise trust statistics."""

    name: str = "Character Profile Tool"
    description: str = "Persist events with sources and return combined trust metrics for a person."
    model_config = {"extra": "allow"}

    def __init__(
        self,
        storage_path: Path | None = None,
        leaderboard: LeaderboardTool | None = None,
        trust_tracker: TrustworthinessTrackerTool | None = None,
    ) -> None:
        super().__init__()
        self.storage_path = storage_path or settings.BASE_DIR / "character_profiles.json"
        self.leaderboard = leaderboard or LeaderboardTool()
        self.trust_tracker = trust_tracker or TrustworthinessTrackerTool()
        if not self.storage_path.exists():
            self._save({})

    def _load(self) -> dict[str, dict[str, list[dict]]]:
        try:
            with self.storage_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save(self, data: dict[str, dict[str, list[dict]]]) -> None:
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with self.storage_path.open("w", encoding="utf-8") as f:
            json.dump(data, f)

    def record_event(self, person: str, event: dict) -> None:
        data = self._load()
        profile = data.get(person, {"events": []})
        profile["events"].append(event)
        data[person] = profile
        self._save(data)

    def get_profile(self, person: str) -> dict:
        data = self._load()
        profile = data.get(person, {"events": []})
        board = self.leaderboard.get_person(person) or {
            "person": person,
            "lies": 0,
            "misquotes": 0,
            "misinfo": 0,
        }
        trust = self.trust_tracker._load().get(person, {"truths": 0, "lies": 0, "score": 0.0})
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

    def _run(self, person: str) -> dict:
        return {"status": "success", "profile": self.get_profile(person)}

    def run(self, *args, **kwargs) -> dict:  # pragma: no cover - thin wrapper
        return self._run(*args, **kwargs)
