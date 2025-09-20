"""Transcript chunking utilities for retrieval augmented generation."""

from __future__ import annotations

from dataclasses import dataclass

from core.settings import get_settings
from obs import metrics

from .transcribe import Transcript


@dataclass
class Chunk:
    text: str
    start: float
    end: float


def chunk_transcript(transcript: Transcript, *, max_chars: int = 800, overlap: int = 200) -> list[Chunk]:
    """Split a :class:`~analysis.transcribe.Transcript` into overlapping chunks.

    Parameters
    ----------
    transcript:
        Transcript to split.
    max_chars:
        Target maximum characters per chunk.
    overlap:
        Overlap size in characters between consecutive chunks.
    """

    chunks: list[Chunk] = []
    buf: list[str] = []
    start = 0.0
    end = 0.0
    lbl = metrics.label_ctx()
    merges = 0
    settings = get_settings()
    token_mode = getattr(settings, "enable_token_aware_chunker", False)
    approx_tokens_per_char = 0.25  # heuristic (4 chars ~ 1 token)
    target_tokens = getattr(settings, "token_chunk_target_tokens", 220)
    # If token-aware mode enabled, derive a dynamic max_chars bound from target tokens to keep backward compatibility
    if token_mode:
        max_chars = int(target_tokens / approx_tokens_per_char)
    for seg in transcript.segments:
        if not buf:
            start = seg.start
        candidate_len = sum(len(t) for t in buf) + len(seg.text) + len(buf)
        candidate_tokens = int(candidate_len * approx_tokens_per_char) if token_mode else 0
        flush = False
        if token_mode and candidate_tokens > target_tokens and buf:
            flush = True
        elif candidate_len > max_chars and buf:
            flush = True
        if flush:
            text = " ".join(buf)
            chunks.append(Chunk(text=text, start=start, end=end))
            # Observe size of completed chunk
            metrics.SEGMENT_CHUNK_SIZE_CHARS.labels(lbl["tenant"], lbl["workspace"]).observe(len(text))
            if token_mode:
                metrics.SEGMENT_CHUNK_SIZE_TOKENS.labels(lbl["tenant"], lbl["workspace"]).observe(
                    int(len(text) * approx_tokens_per_char)
                )
            merges += 1
            # start new buffer with overlap
            overflow = text[-overlap:]
            buf = [overflow, seg.text]
            start = end - (len(overflow) / max_chars)
        else:
            buf.append(seg.text)
        end = seg.end
    if buf:
        text = " ".join(buf)
        chunks.append(Chunk(text=text, start=start, end=end))
        metrics.SEGMENT_CHUNK_SIZE_CHARS.labels(lbl["tenant"], lbl["workspace"]).observe(len(text))
        if token_mode:
            metrics.SEGMENT_CHUNK_SIZE_TOKENS.labels(lbl["tenant"], lbl["workspace"]).observe(
                int(len(text) * approx_tokens_per_char)
            )
    # Emit count via existing counter semantics (reuse pipeline steps completed for now)
    # Some test stubs provide a simplified labels() signature; fall back gracefully.
    try:
        metrics.PIPELINE_STEPS_COMPLETED.labels(lbl["tenant"], lbl["workspace"], "segment_chunks").inc()
    except TypeError:
        try:
            metrics.PIPELINE_STEPS_COMPLETED.labels(
                tenant=lbl["tenant"], workspace=lbl["workspace"], step="segment_chunks"
            ).inc()
        except Exception:
            pass
    if merges:
        metrics.SEGMENT_CHUNK_MERGES.labels(lbl["tenant"], lbl["workspace"]).inc()
    return chunks
