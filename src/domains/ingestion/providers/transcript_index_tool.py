"""Index transcripts into timestamped chunks and retrieve context."""

from __future__ import annotations
from platform.observability.metrics import get_metrics
from platform.core.step_result import StepResult
from ._base import BaseTool


class TranscriptIndexTool(BaseTool[StepResult]):
    """Store transcript chunks for later context lookup.

    Returns
    -------
    StepResult
        ok: when transcript indexed (fields: chunks: int)
        skip: when provided transcript is empty or whitespace
        fail: unexpected exception while indexing
    """

    name: str = "Transcript Index Tool"
    description: str = "Index transcripts into timestamped windows and fetch surrounding context."
    from typing import Any, ClassVar

    model_config: ClassVar[dict[str, Any]] = {"extra": "allow"}

    def __init__(self, window: float = 30.0):
        super().__init__()
        self.window = window
        self.indices: dict[str, list[tuple[float, float, str]]] = {}
        self._metrics = get_metrics()
        self._shared_context: dict[str, any] = {}

    def update_context(self, context_data: dict[str, any]) -> None:
        """Update shared context from orchestrator (enables video_id propagation)."""
        self._shared_context.update(context_data)

    def index_transcript(self, transcript: str, video_id: str) -> StepResult:
        """Split a transcript into timestamped chunks and store them.

        Empty/whitespace-only transcripts are treated as a skip (recoverable situation).
        """
        try:
            if not transcript or not transcript.strip():
                result = StepResult.skip(reason="empty transcript")
                self._metrics.counter(
                    "tool_runs_total", labels={"tool": "transcript_index", "outcome": "skipped"}
                ).inc()
                return result
            lines = transcript.splitlines()
            chunks: list[tuple[float, float, str]] = []
            for i, line in enumerate(lines):
                start = i * self.window
                end = start + self.window
                chunks.append((start, end, line))
            self.indices[video_id] = chunks
            result = StepResult.ok(chunks=len(chunks))
            self._metrics.counter("tool_runs_total", labels={"tool": "transcript_index", "outcome": "success"}).inc()
            return result
        except Exception as exc:
            self._metrics.counter("tool_runs_total", labels={"tool": "transcript_index", "outcome": "error"}).inc()
            return StepResult.fail(error=str(exc))

    def get_context(self, video_id: str, ts: float, window: float = 45.0) -> str:
        """Return transcript text around a timestamp within a window."""
        chunks = self.indices.get(video_id, [])
        context: list[str] = []
        for start, end, text in chunks:
            if end < ts - window:
                continue
            if start > ts + window:
                break
            context.append(text)
        return " ".join(context)

    def _run(self, transcript: str, video_id: str | None = None) -> StepResult:
        """Run indexing with optional video_id (falls back to shared context)."""
        if not video_id:
            video_id = self._shared_context.get("video_id") or self._shared_context.get("url", "unknown")
        return self.index_transcript(transcript, video_id)

    def run(self, transcript: str, video_id: str | None = None) -> StepResult:
        return self._run(transcript, video_id)
