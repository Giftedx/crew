"""Aggregate per-person trust metrics and events."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TypedDict

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult

from .. import settings
from ._base import BaseTool
from .leaderboard_tool import LeaderboardTool
from .trustworthiness_tracker_tool import TrustworthinessTrackerTool


class _ProfileLeaderboardSection(TypedDict):
    lies: int
    misquotes: int
    misinfo: int


class _ProfileTrustSection(TypedDict, total=False):
    truths: int
    lies: int
    score: float


class _ProfileResult(TypedDict):
    person: str
    events: list[dict[str, object]]
    leaderboard: _ProfileLeaderboardSection
    trust: _ProfileTrustSection


class CharacterProfileTool(BaseTool[StepResult]):
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
        self._metrics = get_metrics()
        self.storage_path = storage_path or settings.BASE_DIR / "character_profiles.json"
        self.leaderboard = leaderboard or LeaderboardTool()
        self.trust_tracker = trust_tracker or TrustworthinessTrackerTool()
        if not self.storage_path.exists():
            self._save({})

    def _load(self) -> dict[str, dict[str, list[dict[str, object]]]]:
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
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with self.storage_path.open("w", encoding="utf-8") as f:
            json.dump(data, f)

    def record_event(self, person: str, event: dict[str, object]) -> None:
        data = self._load()
        profile = data.get(person, {"events": []})
        profile["events"].append(event)
        data[person] = profile
        self._save(data)

    def get_profile(self, person: str) -> _ProfileResult:
        data = self._load()
        profile = data.get(person, {"events": []})
        board = self.leaderboard.get_person(person) or {
            "person": person,
            "lies": 0,
            "misquotes": 0,
            "misinfo": 0,
        }
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

    def _run(self, person: str) -> StepResult:
        if not person or not person.strip():
            self._metrics.counter("tool_runs_total", labels={"tool": "character_profile", "outcome": "skipped"}).inc()
            return StepResult.ok(skipped=True, reason="empty person")
        profile = self.get_profile(person)
        self._metrics.counter("tool_runs_total", labels={"tool": "character_profile", "outcome": "success"}).inc()
        return StepResult.ok(data={"profile": profile})

    def run(self, person: str) -> StepResult:  # pragma: no cover - thin wrapper
        try:
            return self._run(person)
        except Exception as exc:  # pragma: no cover - unexpected
            self._metrics.counter("tool_runs_total", labels={"tool": "character_profile", "outcome": "error"}).inc()
            return StepResult.fail(error=str(exc))
