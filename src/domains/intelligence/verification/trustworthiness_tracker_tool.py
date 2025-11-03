"""Track per-person truthfulness history and compute trust scores."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from platform.core.step_result import StepResult
from platform.observability.metrics import get_metrics
from platform.time import default_utc_now
from threading import Lock
from typing import ClassVar, TypedDict

from ultimate_discord_intelligence_bot.tools._base import BaseTool


HIGH_TRUST_THRESHOLD = 0.8
TRUSTED_THRESHOLD = 0.6
NEUTRAL_THRESHOLD = 0.4
QUESTIONABLE_THRESHOLD = 0.2


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


class TrustworthinessTrackerTool(BaseTool[StepResult]):
    """Track and manage trustworthiness scores for sources per instruction #3."""

    name: str = "Trustworthiness Tracker Tool"
    description: str = "Updates and returns per-person trust scores based on fact-check verdicts."
    model_config: ClassVar[dict[str, str]] = {"extra": "allow"}

    def __init__(self, storage_path: str | Path | None = None, namespace: str | None = None):
        super().__init__()
        self.namespace = namespace or "trustworthiness"
        self.metrics = get_metrics()
        env_path = os.environ.get("TRUST_TRACKER_PATH")
        legacy = Path("trustworthiness.json")
        data_dir = Path("data")
        preferred = data_dir / "trustworthiness.json"
        if storage_path:
            resolved = Path(storage_path)
        elif env_path:
            resolved = Path(env_path)
        elif legacy.exists() and (not preferred.exists()):
            resolved = legacy
        else:
            if not data_dir.exists():
                try:
                    data_dir.mkdir(parents=True, exist_ok=True)
                except Exception as exc:
                    logging.getLogger(__name__).debug("Failed to create data directory for trust tracker: %s", exc)
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
                except Exception as exc:
                    logging.getLogger(__name__).debug("Skipping invalid record %s: %s", k, exc)
        return out

    def _save(self, data: dict[str, _PersonRecord]) -> None:
        with self.storage_path.open("w", encoding="utf-8") as f:
            json.dump(data, f)

    def _run(self, person: str, verdict: bool) -> StepResult:
        """Internal implementation following StepResult pattern per instruction #3.

        Flatten output so callers can access result["score"] directly (tests do this).
        Adds tool_runs_total metrics with outcome labels success|error|skipped.
        """
        if not person:
            self.metrics.counter(
                "tool_runs_total", labels={"tool": "trustworthiness_tracker", "outcome": "skipped"}
            ).inc()
            return StepResult.skip(reason="No person provided")
        try:
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
            self.metrics.histogram(
                "trustworthiness_score", score, labels={"source_type": self._classify_source(person)}
            )
            self.metrics.counter(
                "tool_runs_total", labels={"tool": "trustworthiness_tracker", "outcome": "success"}
            ).inc()
            return StepResult.ok(person=person, truths=record["truths"], lies=record["lies"], score=record["score"])
        except Exception as e:
            self.metrics.counter(
                "tool_runs_total", labels={"tool": "trustworthiness_tracker", "outcome": "error"}
            ).inc()
            return StepResult.fail(error=str(e))

    def run(self, *args, **kwargs) -> StepResult:
        """Track truthfulness verdict following StepResult pattern.

        Accepts positional or keyword args to remain compatible with orchestrators that
        call tools with variadic parameters.
        """

        def _parse_bool(val: object) -> bool:
            if isinstance(val, bool):
                return val
            if isinstance(val, (int, float)):
                return bool(val)
            if isinstance(val, str):
                t = val.strip().lower()
                if t in {"true", "yes", "y", "1"}:
                    return True
                if t in {"false", "no", "n", "0"}:
                    return False
            return False

        if args:
            try:
                person = str(args[0])
                verdict_raw = args[1] if len(args) > 1 else kwargs.get("verdict", False)
                verdict = _parse_bool(verdict_raw)
                return self._run(person, verdict)
            except Exception:
                return StepResult.fail(error="Invalid arguments for TrustworthinessTrackerTool.run")
        person = str(kwargs.get("person", kwargs.get("source", "")))
        verdict = _parse_bool(kwargs.get("verdict", False))
        return self._run(person, verdict)

    def get_report(self) -> StepResult:
        """Generate trustworthiness report for all tracked sources."""
        try:
            with self._lock:
                data = self._load()
            report = []
            for person, record in data.items():
                report.append(
                    {
                        "source": person,
                        "truths": record["truths"],
                        "lies": record["lies"],
                        "trustworthiness": record["score"],
                        "classification": self._classify_trustworthiness(record["score"]),
                    }
                )
            timestamp = default_utc_now()
            self.metrics.counter(
                "tool_runs_total", labels={"tool": "trustworthiness_tracker_report", "outcome": "success"}
            ).inc()
            return StepResult.ok(report=report, total_sources=len(report), timestamp=timestamp.isoformat())
        except Exception as e:
            self.metrics.counter(
                "tool_runs_total", labels={"tool": "trustworthiness_tracker_report", "outcome": "error"}
            ).inc()
            return StepResult.fail(error=str(e))

    def _classify_source(self, source: str) -> str:
        """Classify source type for metrics - low cardinality per instruction #9."""
        source_lower = source.lower()
        if "youtube" in source_lower:
            return "youtube"
        elif "twitter" in source_lower or "x.com" in source_lower:
            return "twitter"
        elif "reddit" in source_lower:
            return "reddit"
        else:
            return "other"

    def _classify_trustworthiness(self, score: float) -> str:
        """Classify trustworthiness level."""
        if score >= HIGH_TRUST_THRESHOLD:
            return "highly_trusted"
        if score >= TRUSTED_THRESHOLD:
            return "trusted"
        if score >= NEUTRAL_THRESHOLD:
            return "neutral"
        if score >= QUESTIONABLE_THRESHOLD:
            return "questionable"
        return "untrusted"
