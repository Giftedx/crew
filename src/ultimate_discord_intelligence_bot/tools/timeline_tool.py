"""Persist and retrieve chronological events with references."""

from __future__ import annotations

import json
from pathlib import Path

from crewai.tools import BaseTool

from .. import settings


class TimelineTool(BaseTool):
    """Store timeline events per video with sources."""

    name: str = "Timeline Tool"
    description: str = "Record and fetch timeline events for videos."
    model_config = {"extra": "allow"}

    def __init__(self, storage_path: Path | None = None):
        super().__init__()
        self.storage_path = storage_path or settings.BASE_DIR / "timeline.json"
        if not self.storage_path.exists():
            self._save({})

    def _load(self) -> dict[str, list[dict]]:
        try:
            with self.storage_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save(self, data: dict[str, list[dict]]) -> None:
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with self.storage_path.open("w", encoding="utf-8") as f:
            json.dump(data, f)

    def add_event(self, video_id: str, event: dict) -> None:
        data = self._load()
        events = data.get(video_id, [])
        events.append(event)
        events.sort(key=lambda x: x.get("ts", 0))
        data[video_id] = events
        self._save(data)

    def get_timeline(self, video_id: str) -> list[dict]:
        data = self._load()
        return data.get(video_id, [])

    def _run(self, action: str, **kwargs):
        if action == "add":
            self.add_event(kwargs["video_id"], kwargs.get("event", {}))
            return {"status": "success"}
        if action == "get":
            return {"status": "success", "events": self.get_timeline(kwargs["video_id"])}
        return {"status": "error", "error": "unknown action"}

    def run(self, *args, **kwargs):  # pragma: no cover - thin wrapper
        return self._run(*args, **kwargs)
