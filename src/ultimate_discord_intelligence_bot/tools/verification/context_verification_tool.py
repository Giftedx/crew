"""Verify whether a clip aligns with its transcript context."""

from __future__ import annotations

from typing import TypedDict, ClassVar

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult
from ultimate_discord_intelligence_bot.tools._base import BaseTool
from ultimate_discord_intelligence_bot.tools.acquisition.transcript_index_tool import TranscriptIndexTool


class _ContextVerificationResult(TypedDict):
    status: str
    verdict: str
    context: str
    notes: str


class ContextVerificationTool(BaseTool[StepResult]):
    """Check if provided clip text appears in transcript around a timestamp."""

    name: str = "Context Verification Tool"
    description: str = "Compare clip text to indexed transcript context to flag missing context."
    # Allow tests/pipeline to attach helper objects dynamically (pydantic v2 strict by default)
    model_config: ClassVar[dict[str, str]] = {"extra": "allow"}

    def __init__(self, index_tool: TranscriptIndexTool | None = None):
        super().__init__()
        self.index_tool = index_tool or TranscriptIndexTool()
        self._metrics = get_metrics()

    def _run(self, video_id: str, ts: float, clip_text: str | None = None) -> StepResult:
        try:
            context = self.index_tool.get_context(video_id, ts)
            if not context:
                # treat as skip (no indexed transcript yet)
                self._metrics.counter(
                    "tool_runs_total",
                    labels={"tool": "context_verification", "outcome": "skipped"},
                ).inc()
                return StepResult.skip(verdict="uncertain", context="", notes="no transcript indexed")
            if clip_text and clip_text.strip() in context:
                verdict = "in-context"
                notes = "clip text matches context"
            else:
                verdict = "missing-context"
                notes = "clip text not found near timestamp"
            self._metrics.counter(
                "tool_runs_total",
                labels={"tool": "context_verification", "outcome": "success"},
            ).inc()
            return StepResult.ok(verdict=verdict, context=context, notes=notes)
        except Exception as exc:  # pragma: no cover - defensive
            self._metrics.counter(
                "tool_runs_total",
                labels={"tool": "context_verification", "outcome": "error"},
            ).inc()
            return StepResult.fail(error=str(exc))

    def run(
        self,
        video_id: str,
        ts: float,
        clip_text: str | None = None,
    ) -> StepResult:  # pragma: no cover - thin wrapper
        return self._run(video_id, ts, clip_text)
