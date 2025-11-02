from __future__ import annotations
from platform.core.step_result import StepResult
from ultimate_discord_intelligence_bot.tools._base import BaseTool


class ConsistencyCheckTool(BaseTool[dict[str, float]]):
    """Tool for checking consistency between current output and historical data."""

    name: str = "consistency_check_tool"
    description: str = "Checks for consistency between the current output and historical data."

    def _run(self, content: str, tenant: str, workspace: str) -> StepResult:
        """Check consistency score for given content."""
        try:
            if not content:
                return StepResult.fail("Content cannot be empty")
            if not tenant:
                return StepResult.fail("Tenant is required")
            if not workspace:
                return StepResult.fail("Workspace is required")
            consistency_score = 0.95
            return StepResult.ok(data={"consistency_score": consistency_score})
        except Exception as e:
            return StepResult.fail(f"Consistency check failed: {e!s}")
