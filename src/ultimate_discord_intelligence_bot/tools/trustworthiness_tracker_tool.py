"""Track per-person truthfulness history and compute trust scores."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from threading import Lock
from typing import TypedDict

from ._base import BaseTool


class _PersonRecord(TypedDict):
    truths: int
    lies: int
    score: float


class _TrackerResult(TypedDict):
    status: str
    person: str
    truths: int
    lies: int
    score: float


class TrustworthinessTrackerTool(BaseTool[_TrackerResult]):
    """Maintain counts of truthful and false statements for each person."""

    name: str = "Trustworthiness Tracker Tool"
    description: str = "Updates and returns per-person trust scores based on fact-check verdicts."
    model_config = {"extra": "allow"}

    def __init__(self, storage_path: str | Path | None = None):
        super().__init__()
        # Resolution order:
        # 1. Explicit storage_path arg
        # 2. TRUST_TRACKER_PATH env var
        # 3. Legacy root file (trustworthiness.json) if it exists and new data/ version absent
        # 4. data/trustworthiness.json (created under data directory)
        env_path = os.environ.get("TRUST_TRACKER_PATH")
        legacy = Path("trustworthiness.json")
        data_dir = Path("data")
        preferred = data_dir / "trustworthiness.json"
        if storage_path:
            resolved = Path(storage_path)
        elif env_path:
            resolved = Path(env_path)
        elif legacy.exists() and not preferred.exists():
            resolved = legacy
        else:
            if not data_dir.exists():  # pragma: no cover - trivial
                try:
                    data_dir.mkdir(parents=True, exist_ok=True)
                except Exception as exc:  # pragma: no cover - extremely unlikely
                    logging.getLogger(__name__).debug(
                        "Failed to create data directory for trust tracker: %s", exc
                    )
            resolved = preferred
        self.storage_path = resolved
        self._lock = Lock()
        if not self.storage_path.exists():
            self._save({})

    def _load(self) -> dict[str, _PersonRecord]:
        try:
            with self.storage_path.open("r", encoding="utf-8") as f:
                raw = json.load(f)
        except Exception:
            return {}
        if not isinstance(raw, dict):
            return {}
        out: dict[str, _PersonRecord] = {}
        for k, v in raw.items():
            if isinstance(v, dict) and {"truths", "lies", "score"}.issubset(v.keys()):
                try:
                    out[k] = {
                        "truths": int(v.get("truths", 0)),
                        "lies": int(v.get("lies", 0)),
                        "score": float(v.get("score", 0.0)),
                    }
                except Exception as exc:  # pragma: no cover - defensive
                    logging.getLogger(__name__).debug("Skipping invalid record %s: %s", k, exc)
        return out

    def _save(self, data: dict[str, _PersonRecord]) -> None:
        with self.storage_path.open("w", encoding="utf-8") as f:
            json.dump(data, f)

    def _run(self, person: str, verdict: bool) -> _TrackerResult:
        with self._lock:
            data = self._load()
            record = data.get(person, {"truths": 0, "lies": 0, "score": 0.0})
            if verdict:
                record["truths"] += 1
            else:
                record["lies"] += 1
            total = record["truths"] + record["lies"]
            score = record["truths"] / total if total else 0.0
            record["score"] = score
            data[person] = record
            self._save(data)
        return {"status": "success", "person": person, **record}

    def run(self, person: str, verdict: bool) -> _TrackerResult:  # pragma: no cover - thin wrapper
        return self._run(person, verdict)
