"""Compatibility wrapper for YouTube provider used in tests.

This module exposes ``fetch_metadata`` and ``fetch_transcript`` functions so
tests can monkeypatch them via ``import ingest.providers.youtube as ymod``.

Important: Keep this module import-safe with zero heavy dependencies at import
time. Tests will monkeypatch the functions; when not monkeypatched, we lazily
attempt to delegate to the domain provider if available, otherwise return
minimal placeholders.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class VideoMetadata:
    id: str
    title: str = ""
    channel: str | None = None
    channel_id: str | None = None
    streamer: str | None = None
    published_at: str | None = None
    duration: float | None = None
    url: str | None = None
    thumbnails: list[str] | None = None


def _load_domain_provider():
    """Try to import the real domain provider functions lazily.

    Returns a tuple (fetch_metadata_func, fetch_transcript_func) or (None, None)
    if the domain provider (and its optional deps) is unavailable.
    """

    try:
        from domains.ingestion.providers.youtube import (  # type: ignore
            fetch_metadata as _fetch_metadata_impl,
        )
        from domains.ingestion.providers.youtube import (
            fetch_transcript as _fetch_transcript_impl,
        )

        return _fetch_metadata_impl, _fetch_transcript_impl
    except Exception:
        # Keep import-time safe: domain provider not available in this context
        return None, None


def fetch_metadata(url: str) -> VideoMetadata:  # pragma: no cover - replaced in tests
    fm, _ = _load_domain_provider()
    if fm is not None:
        return fm(url)  # type: ignore[return-value]
    # Fallback minimal placeholder
    return VideoMetadata(id="unknown", title="", channel="unknown", url=url, duration=0, thumbnails=[])


def fetch_transcript(url: str) -> str | None:  # pragma: no cover - replaced in tests
    _, ft = _load_domain_provider()
    if ft is not None:
        return ft(url)
    return None


__all__ = ["VideoMetadata", "fetch_metadata", "fetch_transcript"]
