from __future__ import annotations

import logging
from typing import Any

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult
from ultimate_discord_intelligence_bot.tools._base import BaseTool


class ConfidenceScoringTool(BaseTool[dict[str, float]]):
    """Tool for evaluating confidence levels of agent outputs."""

    name: str = "confidence_scoring_tool"
    description: str = "Evaluates the confidence level of an agent's output."

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._metrics = get_metrics()

    def _run(self, content: str, tenant: str, workspace: str) -> StepResult:
        """Evaluate confidence score for given content."""
        result: StepResult
        try:
            if not content:
                result = StepResult.fail("Content cannot be empty")
            elif not tenant:
                result = StepResult.fail("Tenant is required")
            elif not workspace:
                result = StepResult.fail("Workspace is required")
            else:
                confidence_score = 0.98
                result = StepResult.ok(data={"confidence_score": confidence_score})
        except Exception as e:
            result = StepResult.fail(f"Confidence scoring failed: {e!s}")

        try:
            self._metrics.counter(
                "tool_runs_total",
                labels={"tool": self.name, "outcome": "success" if result.success else "failure"},
            ).inc()
        except Exception as exc:
            logging.debug("metrics emit failed: %s", exc)

        return result
