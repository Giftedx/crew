"""Track per-person truthfulness history and compute trust scores."""

from __future__ import annotations

import json
import os
from pathlib import Path
from threading import Lock

from crewai.tools import BaseTool


class TrustworthinessTrackerTool(BaseTool):
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
                except Exception:  # pragma: no cover
                    pass
            resolved = preferred
        self.storage_path = resolved
        self._lock = Lock()
        if not self.storage_path.exists():
            self._save({})

    def _load(self) -> dict[str, dict[str, int]]:
        try:
            with self.storage_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save(self, data: dict[str, dict[str, int]]) -> None:
        with self.storage_path.open("w", encoding="utf-8") as f:
            json.dump(data, f)

    def _run(self, person: str, verdict: bool) -> dict:
        with self._lock:
            data = self._load()
            record = data.get(person, {"truths": 0, "lies": 0})
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

    def run(self, *args, **kwargs):  # pragma: no cover - thin wrapper
        return self._run(*args, **kwargs)
