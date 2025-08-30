"""Verify whether a clip aligns with its transcript context."""

from __future__ import annotations

from typing import TypedDict

from ._base import BaseTool
from .transcript_index_tool import TranscriptIndexTool


class _ContextVerificationResult(TypedDict):
    status: str
    verdict: str
    context: str
    notes: str


class ContextVerificationTool(BaseTool[_ContextVerificationResult]):
    """Check if provided clip text appears in transcript around a timestamp."""

    name: str = "Context Verification Tool"
    description: str = "Compare clip text to indexed transcript context to flag missing context."
    # Allow tests/pipeline to attach helper objects dynamically (pydantic v2 strict by default)
    model_config = {"extra": "allow"}

    def __init__(self, index_tool: TranscriptIndexTool | None = None):
        super().__init__()
        self.index_tool = index_tool or TranscriptIndexTool()

    def _run(self, video_id: str, ts: float, clip_text: str | None = None) -> _ContextVerificationResult:
        context = self.index_tool.get_context(video_id, ts)
        if not context:
            return {
                "status": "success",
                "verdict": "uncertain",
                "context": "",
                "notes": "no transcript indexed",
            }
        if clip_text and clip_text.strip() in context:
            verdict = "in-context"
            notes = "clip text matches context"
        else:
            verdict = "missing-context"
            notes = "clip text not found near timestamp"
        return {
            "status": "success",
            "verdict": verdict,
            "context": context,
            "notes": notes,
        }

    def run(
        self,
        video_id: str,
        ts: float,
        clip_text: str | None = None,
    ) -> _ContextVerificationResult:  # pragma: no cover - thin wrapper
        return self._run(video_id, ts, clip_text)
