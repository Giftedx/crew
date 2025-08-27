from __future__ import annotations

"""Transcript chunking utilities for retrieval augmented generation."""

from dataclasses import dataclass
from typing import Iterable, List

from .transcribe import Transcript


@dataclass
class Chunk:
    text: str
    start: float
    end: float


def chunk_transcript(
    transcript: Transcript, *, max_chars: int = 800, overlap: int = 200
) -> List[Chunk]:
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

    chunks: List[Chunk] = []
    buf: List[str] = []
    start = 0.0
    end = 0.0
    for seg in transcript.segments:
        if not buf:
            start = seg.start
        candidate_len = sum(len(t) for t in buf) + len(seg.text) + len(buf)
        if candidate_len > max_chars and buf:
            text = " ".join(buf)
            chunks.append(Chunk(text=text, start=start, end=end))
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
    return chunks
