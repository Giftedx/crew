"""Bypass version of Drive Upload Tool that doesn't require credentials.

Migrated to StepResult pattern per instrumentation standard.
Always returns a skipped StepResult with file links (local file paths) – no upload occurs.
Metrics: tool_runs_total{tool="drive_upload_bypass", outcome=skipped}
"""

import logging

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult

from ._base import BaseTool

logger = logging.getLogger(__name__)


class DriveUploadTool(BaseTool):
    """Drive upload tool that works without Google credentials (bypass)."""

    name: str = "Google Drive Upload Tool (Bypass)"
    description: str = "Upload files to Google Drive (disabled - no credentials)"

    def __init__(self) -> None:
        super().__init__()
        print("⚠️  Google Drive uploads disabled - no credentials configured")
        self._metrics = get_metrics()

    def _run(self, file_path: str, platform: str) -> StepResult:
        """Bypass Google Drive upload returning skipped StepResult."""
        self._metrics.counter("tool_runs_total", labels={"tool": "drive_upload_bypass", "outcome": "skipped"}).inc()
        return StepResult.skip(
            message="Google Drive uploads disabled (no credentials configured)",
            file_path=file_path,
            platform=platform,
            links={
                "preview_link": f"file://{file_path}",
                "direct_link": f"file://{file_path}",
                "view_link": f"file://{file_path}",
            },
        )

    def run(self, file_path: str, platform: str) -> StepResult:  # pragma: no cover - thin wrapper
        return self._run(file_path, platform)
