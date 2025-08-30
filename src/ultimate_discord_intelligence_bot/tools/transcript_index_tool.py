"""Index transcripts into timestamped chunks and retrieve context."""

from __future__ import annotations

from ._base import BaseTool


class TranscriptIndexTool(BaseTool[dict[str, object]]):
    """Store transcript chunks for later context lookup."""

    name: str = "Transcript Index Tool"
    description: str = "Index transcripts into timestamped windows and fetch surrounding context."
    model_config = {"extra": "allow"}

    def __init__(self, window: float = 30.0):
        super().__init__()
        self.window = window
        self.indices: dict[str, list[tuple[float, float, str]]] = {}

    def index_transcript(self, transcript: str, video_id: str) -> dict[str, object]:
        """Split a transcript into timestamped chunks and store them."""
        chunks: list[tuple[float, float, str]] = []
        for i, line in enumerate(transcript.splitlines()):
            start = i * self.window
            end = start + self.window
            chunks.append((start, end, line))
        self.indices[video_id] = chunks
        return {"status": "success", "chunks": len(chunks)}

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
    def _run(self, transcript: str, video_id: str) -> dict[str, object]:
        return self.index_transcript(transcript, video_id)

    def run(self, transcript: str, video_id: str) -> dict[str, object]:  # pragma: no cover - thin wrapper
        return self._run(transcript, video_id)
