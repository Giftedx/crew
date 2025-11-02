"""Persist and retrieve per-person lie/misquote/misinfo counts."""

from __future__ import annotations

import json
from platform.core.step_result import StepResult
from platform.observability.metrics import get_metrics
from typing import TYPE_CHECKING, Any, ClassVar, TypedDict, cast

from .. import settings
from ._base import BaseTool


if TYPE_CHECKING:
    from pathlib import Path


class _LeaderboardRecord(TypedDict):
    person: str
    lies: int
    misquotes: int
    misinfo: int


class _LeaderboardTopResult(TypedDict):
    status: str
    results: list[_LeaderboardRecord]


class LeaderboardTool(BaseTool[StepResult]):
    """Simple JSON-backed scoreboard for misinformation tracking."""

    name: str = "Leaderboard Tool"
    description: str = "Maintain counts of lies, misquotes and misinfo per person."
    model_config: ClassVar[dict[str, Any]] = {"extra": "allow"}

    def __init__(self, storage_path: Path | None = None):
        super().__init__()
        self._metrics = get_metrics()
        self.storage_path = storage_path or settings.BASE_DIR / "leaderboard.json"
        if not self.storage_path.exists():
            self._save({})

    def _load(self) -> dict[str, dict[str, int]]:
        try:
            with self.storage_path.open("r", encoding="utf-8") as f:
                raw: Any = json.load(f)
        except Exception:
            return {}
        if not isinstance(raw, dict):
            return {}
        out: dict[str, dict[str, int]] = {}
        for person, scores in raw.items():
            if not isinstance(person, str) or not isinstance(scores, dict):
                continue
            rec: dict[str, int] = {}
            for k in ("lies", "misquotes", "misinfo"):
                v = scores.get(k, 0)
                if isinstance(v, int | float):
                    rec[k] = int(v)
                else:
                    rec[k] = 0
            out[person] = rec
        return out

    def _save(self, data: dict[str, dict[str, int]]) -> None:
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with self.storage_path.open("w", encoding="utf-8") as f:
            json.dump(data, f)

    def update_scores(self, person: str, lies_delta: int, misquotes_delta: int, misinfo_delta: int) -> None:
        data = self._load()
        record = data.get(person, {"lies": 0, "misquotes": 0, "misinfo": 0})
        record["lies"] += lies_delta
        record["misquotes"] += misquotes_delta
        record["misinfo"] += misinfo_delta
        data[person] = record
        self._save(data)

    def get_top(self, n: int = 10) -> list[_LeaderboardRecord]:
        data = self._load()
        items: list[_LeaderboardRecord] = []
        for person, scores in data.items():
            rec: _LeaderboardRecord = {
                "person": person,
                "lies": int(scores.get("lies", 0)),
                "misquotes": int(scores.get("misquotes", 0)),
                "misinfo": int(scores.get("misinfo", 0)),
            }
            items.append(rec)
        items.sort(key=lambda x: x["lies"] + x["misquotes"] + x["misinfo"], reverse=True)
        return items[:n]

    def get_person(self, person: str) -> _LeaderboardRecord | None:
        """Return scoreboard counts for a single person."""
        data = self._load()
        record = data.get(person)
        if record is None:
            return None
        return {
            "person": person,
            "lies": int(record.get("lies", 0)),
            "misquotes": int(record.get("misquotes", 0)),
            "misinfo": int(record.get("misinfo", 0)),
        }

    def _run(self, action: str, **kwargs: object) -> StepResult:
        if action == "update":
            person = cast("str", kwargs["person"])

            def _as_int(key: str, default: int = 0) -> int:
                val = kwargs.get(key, default)
                if isinstance(val, int):
                    return val
                if isinstance(val, str) and val.isdigit():
                    return int(val)
                return default

            lies_delta = _as_int("lies_delta")
            misquotes_delta = _as_int("misquotes_delta")
            misinfo_delta = _as_int("misinfo_delta")
            self.update_scores(person, lies_delta, misquotes_delta, misinfo_delta)
            self._metrics.counter("tool_runs_total", labels={"tool": "leaderboard", "outcome": "success"}).inc()
            return StepResult.ok(data={"action": "update", "person": person})
        if action == "top":
            n_val = kwargs.get("n", 10)
            n = int(n_val) if isinstance(n_val, int) else 10
            results = self.get_top(n)
            self._metrics.counter("tool_runs_total", labels={"tool": "leaderboard", "outcome": "success"}).inc()
            return StepResult.ok(data={"action": "top", "results": results})
        if action == "get":
            person = cast("str", kwargs["person"])
            result = self.get_person(person)
            if result is None:
                self._metrics.counter("tool_runs_total", labels={"tool": "leaderboard", "outcome": "error"}).inc()
                return StepResult.fail(error="not found")
            self._metrics.counter("tool_runs_total", labels={"tool": "leaderboard", "outcome": "success"}).inc()
            return StepResult.ok(data={"action": "get", "result": result})
        self._metrics.counter("tool_runs_total", labels={"tool": "leaderboard", "outcome": "skipped"}).inc()
        return StepResult.skip(reason="unknown action", data={"action": action})

    def run(self, action: str, **kwargs: object) -> StepResult:
        try:
            return self._run(action, **kwargs)
        except Exception as exc:
            self._metrics.counter("tool_runs_total", labels={"tool": "leaderboard", "outcome": "error"}).inc()
            return StepResult.fail(error=str(exc))
