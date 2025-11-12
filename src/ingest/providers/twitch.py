"""Compatibility wrapper for Twitch provider used in tests.

Import-safe module exposing ``ClipMetadata``, ``fetch_metadata`` and
``fetch_transcript`` so unit tests can monkeypatch them. Defaults lazily
delegate to the domain provider when available; otherwise return minimal
placeholders.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ClipMetadata:
    id: str
    title: str
    streamer: str
    published_at: str | None
    duration: float | None
    url: str


def _load_domain_provider():
    try:
        from domains.ingestion.providers.twitch import (  # type: ignore
            fetch_metadata as _fetch_metadata_impl,
        )
        from domains.ingestion.providers.twitch import (
            fetch_transcript as _fetch_transcript_impl,
        )

        return _fetch_metadata_impl, _fetch_transcript_impl
    except Exception:
        return None, None


def fetch_metadata(url: str) -> ClipMetadata:  # pragma: no cover - patched in tests
    fm, _ = _load_domain_provider()
    if fm is not None:
        return fm(url)  # type: ignore[return-value]
    return ClipMetadata(
        id="unknown",
        title="",
        streamer="unknown",
        published_at=None,
        duration=None,
        url=url,
    )


def fetch_transcript(url: str) -> str | None:  # pragma: no cover - patched in tests
    _, ft = _load_domain_provider()
    if ft is not None:
        return ft(url)
    return "clip"


__all__ = ["ClipMetadata", "fetch_metadata", "fetch_transcript"]
