"""Persist and retrieve per-person lie/misquote/misinfo counts."""

from __future__ import annotations

import json
from pathlib import Path

from crewai.tools import BaseTool

from .. import settings


class LeaderboardTool(BaseTool):
    """Simple JSON-backed scoreboard for misinformation tracking."""

    name: str = "Leaderboard Tool"
    description: str = "Maintain counts of lies, misquotes and misinfo per person."
    model_config = {"extra": "allow"}

    def __init__(self, storage_path: Path | None = None):
        super().__init__()
        self.storage_path = storage_path or settings.BASE_DIR / "leaderboard.json"
        if not self.storage_path.exists():
            self._save({})

    def _load(self) -> dict[str, dict[str, int]]:
        try:
            with self.storage_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save(self, data: dict[str, dict[str, int]]) -> None:
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with self.storage_path.open("w", encoding="utf-8") as f:
            json.dump(data, f)

    def update_scores(
        self, person: str, lies_delta: int, misquotes_delta: int, misinfo_delta: int
    ) -> None:
        data = self._load()
        record = data.get(person, {"lies": 0, "misquotes": 0, "misinfo": 0})
        record["lies"] += lies_delta
        record["misquotes"] += misquotes_delta
        record["misinfo"] += misinfo_delta
        data[person] = record
        self._save(data)

    def get_top(self, n: int = 10) -> list[dict[str, int]]:
        data = self._load()
        items = [{"person": person, **scores} for person, scores in data.items()]
        items.sort(key=lambda x: (x["lies"] + x["misquotes"] + x["misinfo"]), reverse=True)
        return items[:n]

    def get_person(self, person: str) -> dict[str, int] | None:
        """Return scoreboard counts for a single person."""
        data = self._load()
        record = data.get(person)
        if record is None:
            return None
        return {"person": person, **record}

    def _run(self, action: str, **kwargs):
        if action == "update":
            self.update_scores(
                kwargs["person"],
                kwargs.get("lies_delta", 0),
                kwargs.get("misquotes_delta", 0),
                kwargs.get("misinfo_delta", 0),
            )
            return {"status": "success"}
        if action == "top":
            return {"status": "success", "results": self.get_top(kwargs.get("n", 10))}
        if action == "get":
            result = self.get_person(kwargs["person"])
            return (
                {"status": "success", "result": result}
                if result
                else {"status": "error", "error": "not found"}
            )
        return {"status": "error", "error": "unknown action"}

    def run(self, *args, **kwargs):  # pragma: no cover - thin wrapper
        return self._run(*args, **kwargs)
