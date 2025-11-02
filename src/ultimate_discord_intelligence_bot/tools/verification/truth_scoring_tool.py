"""Simple utility to score truthfulness from fact-check verdicts.

The tool expects a list of boolean verdicts where ``True`` represents a
verified claim. The returned score is the mean proportion of truthful
statements, laying groundwork for richer historical tracking.
"""
from collections.abc import Iterable
from statistics import mean
from platform.observability.metrics import get_metrics
from platform.core.step_result import StepResult
from ultimate_discord_intelligence_bot.tools._base import BaseTool

class TruthScoringTool(BaseTool[StepResult]):
    name: str = 'Truth Scoring Tool'
    description: str = 'Calculate a trustworthiness score from fact-check results'

    def __init__(self) -> None:
        super().__init__()
        self._metrics = get_metrics()

    def _run(self, verdicts: Iterable[bool]) -> StepResult:
        values = list(verdicts)
        if not values:
            self._metrics.counter('tool_runs_total', labels={'tool': 'truth_scoring', 'outcome': 'skipped'}).inc()
            return StepResult.skip(reason='no verdicts provided', data={'score': 0.0})
        score = mean((1 if v else 0 for v in values))
        self._metrics.counter('tool_runs_total', labels={'tool': 'truth_scoring', 'outcome': 'success'}).inc()
        return StepResult.ok(data={'score': score})

    def run(self, verdicts: Iterable[bool]) -> StepResult:
        try:
            return self._run(verdicts)
        except Exception as exc:
            self._metrics.counter('tool_runs_total', labels={'tool': 'truth_scoring', 'outcome': 'error'}).inc()
            return StepResult.fail(error=str(exc))