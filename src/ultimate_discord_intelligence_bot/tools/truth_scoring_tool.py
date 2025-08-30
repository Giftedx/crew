"""Simple utility to score truthfulness from fact-check verdicts.

The tool expects a list of boolean verdicts where ``True`` represents a
verified claim. The returned score is the mean proportion of truthful
statements, laying groundwork for richer historical tracking.
"""

from collections.abc import Iterable
from statistics import mean
from typing import TypedDict

from ._base import BaseTool


class _TruthScoreResult(TypedDict):
    status: str
    score: float


class TruthScoringTool(BaseTool[_TruthScoreResult]):
    name: str = "Truth Scoring Tool"
    description: str = "Calculate a trustworthiness score from fact-check results"

    def _run(self, verdicts: Iterable[bool]) -> _TruthScoreResult:
        values = list(verdicts)
        if not values:
            return {"status": "success", "score": 0.0}
        score = mean(1 if v else 0 for v in values)
        return {"status": "success", "score": score}

    def run(self, verdicts: Iterable[bool]) -> _TruthScoreResult:  # pragma: no cover - thin wrapper
        return self._run(verdicts)
