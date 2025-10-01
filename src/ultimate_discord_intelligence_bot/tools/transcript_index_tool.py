"""Index transcripts into timestamped chunks and retrieve context."""

from __future__ import annotations

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult

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
    model_config = {"extra": "allow"}

    def __init__(self, window: float = 30.0):
        super().__init__()
        self.window = window
        # indices maps video_id -> list of (start_ts, end_ts, text)
        self.indices: dict[str, list[tuple[float, float, str]]] = {}
        self._metrics = get_metrics()

    def index_transcript(self, transcript: str, video_id: str) -> StepResult:
        """Split a transcript into timestamped chunks and store them.

        Empty/whitespace-only transcripts are treated as a skip (recoverable situation).
        """
        try:
            if not transcript or not transcript.strip():  # treat empty input as skipped OK
                result = StepResult.skip(reason="empty transcript")
                self._metrics.counter(
                    "tool_runs_total",
                    labels={"tool": "transcript_index", "outcome": "skipped"},
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
            self._metrics.counter(
                "tool_runs_total",
                labels={"tool": "transcript_index", "outcome": "success"},
            ).inc()
            return result
        except Exception as exc:  # pragma: no cover - defensive catch
            self._metrics.counter(
                "tool_runs_total",
                labels={"tool": "transcript_index", "outcome": "error"},
            ).inc()
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

    # expose indexing via BaseTool run
    def _run(self, transcript: str, video_id: str) -> StepResult:
        return self.index_transcript(transcript, video_id)

    def run(self, transcript: str, video_id: str) -> StepResult:  # pragma: no cover - thin wrapper
        return self._run(transcript, video_id)
