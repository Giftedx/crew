from __future__ import annotations

from platform.core.step_result import StepResult

from ._base import BaseTool


class ReanalysisTriggerTool(BaseTool):
    name: str = "reanalysis_trigger_tool"
    description: str = "Triggers a re-analysis of a task if quality is below a set threshold."

    def _run(self) -> StepResult:
        print("--- Re-analysis Triggered ---")
        return StepResult.ok(data={"status": "reanalysis_triggered"})
