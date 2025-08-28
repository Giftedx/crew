"""Simple utility to score truthfulness from fact-check verdicts.

The tool expects a list of boolean verdicts where ``True`` represents a
verified claim. The returned score is the mean proportion of truthful
statements, laying groundwork for richer historical tracking.
"""

from statistics import mean
from typing import Iterable

from crewai.tools import BaseTool


class TruthScoringTool(BaseTool):
    name: str = "Truth Scoring Tool"
    description: str = "Calculate a trustworthiness score from fact-check results"

    def _run(self, verdicts: Iterable[bool]) -> dict:
        values = list(verdicts)
        if not values:
            return {"status": "success", "score": 0.0}
        score = mean(1 if v else 0 for v in values)
        return {"status": "success", "score": score}

    def run(self, *args, **kwargs):  # pragma: no cover - thin wrapper
        return self._run(*args, **kwargs)
