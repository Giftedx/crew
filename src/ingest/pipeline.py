"""Lightweight ingestion pipeline shim for tests.

This module provides a minimal ingestion pipeline compatible with legacy
imports (``from ingest.pipeline import IngestJob``) and the unit tests in
``tests/unit/tools/acquisition/test_ingest_concurrent.py``. It focuses on:

- Selecting the appropriate provider module (currently: youtube)
- Fetching metadata and transcript, optionally concurrently when the
  ``ENABLE_INGEST_CONCURRENT`` environment variable is set
- Building simple transcript segments from plain text
- Naive chunking (by character length) so short inputs coalesce into a single
  chunk, matching test expectations
- Emitting records to an in-memory VectorStore via ``upsert`` and returning a
  small result payload

This shim intentionally avoids importing the heavier, production pipeline in
``domains.ingestion.pipeline`` to keep test environments dependency-light and
fast. It does not implement privacy filtering, topic extraction, or database
provenance recording.
"""

from __future__ import annotations

import concurrent.futures
import hashlib
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from memory import vector_store as _vs


@dataclass
class IngestJob:
    source: str
    external_id: str
    url: str
    tenant: str
    workspace: str
    tags: list[str]
    visibility: str = "public"


def _get_provider(source: str):
    if source == "youtube":
        # Local, lightweight shim that can be monkeypatched by tests
        from .providers import youtube as provider

        return provider, "channel"
    # Additional sources can be added here as needed (e.g., twitch)
    raise ValueError(f"unknown source {source}")


def _fetch_both_concurrent(provider_mod: Any, url: str) -> tuple[Any, str | None]:
    """Fetch metadata and transcript concurrently.

    Any exception in transcript retrieval is swallowed (treated as missing
    transcript) to match permissive behavior; metadata errors propagate.
    """

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        fut_meta = ex.submit(provider_mod.fetch_metadata, url)
        fut_tx = ex.submit(provider_mod.fetch_transcript, url)
        meta = fut_meta.result()
        try:
            transcript_text = fut_tx.result()
        except Exception:
            transcript_text = None
    return meta, transcript_text


def _build_segments_from_text(text: str | None) -> list[tuple[float, float, str]]:
    """Return list of (start, end, text) tuples from plaintext transcript."""

    if not text:
        return []
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return [(float(i), float(i + 1), t) for i, t in enumerate(lines)]


def _chunk_segments(
    segments: list[tuple[float, float, str]], *, max_chars: int = 800, overlap: int = 200
) -> list[tuple[float, float, str]]:
    """Naively combine adjacent segments into text chunks <= max_chars.

    The simple strategy below mirrors the behavior required by the tests: short
    inputs (a few short lines) coalesce into a single chunk. It also maintains
    approximate start/end timestamps.
    """

    if not segments:
        return []
    chunks: list[tuple[float, float, str]] = []
    buf: list[str] = []
    start = segments[0][0]
    end = segments[0][1]
    for _s, e, text in segments:
        candidate_len = sum(len(t) for t in buf) + len(text) + max(0, len(buf))
        if buf and candidate_len > max_chars:
            chunks.append((start, end, " ".join(buf)))
            # Keep a small overlap window to mimic downstream strategies
            overflow = (" ".join(buf))[-overlap:]
            buf = [overflow, text]
            start = max(start, end - max(0, len(overflow)) / max_chars)
        else:
            buf.append(text)
        end = e
    if buf:
        chunks.append((start, end, " ".join(buf)))
    return chunks


def _vectorize(texts: list[str]) -> list[list[float]]:
    """Deterministic, dependency-free vectorization for tests.

    Produces a small fixed-length vector for each text by hashing the content.
    """

    vectors: list[list[float]] = []
    for t in texts:
        h = hashlib.sha256(t.encode("utf-8")).digest()
        # 8-dim vector from hash bytes, normalized to [0, 1)
        vec = [int.from_bytes(h[i : i + 4], "big") / 2**32 for i in range(0, 32, 4)]
        vectors.append(vec)
    return vectors


def _normalize_published_at(value: Any) -> str:
    """Normalize published_at to a string suitable for payloads.

    Rules expected by unit tests:
    - Naive datetime -> ISO 8601 string with explicit UTC offset (+00:00)
    - Aware datetime -> ISO 8601 string as-is
    - String -> preserved as-is
    - None -> empty string
    - Other types -> coerced to string
    """
    try:
        if isinstance(value, datetime):
            dt = value
            # If naive, assign UTC tzinfo
            if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.isoformat()
        if isinstance(value, str):
            return value
        if value is None:
            return ""
        # Fallback: string coercion for numbers/others
        return str(value)
    except Exception:
        # Extremely defensive: on any failure, return empty string
        return ""


def run(job: IngestJob, store: _vs.VectorStore) -> dict:
    """Execute an ingestion job.

    Honors the ``ENABLE_INGEST_CONCURRENT`` flag to run metadata and transcript
    fetches concurrently for supported providers.
    """

    provider_mod, creator_attr = _get_provider(job.source)
    # Fetch metadata and transcript (concurrently when enabled)
    if os.getenv("ENABLE_INGEST_CONCURRENT"):
        try:
            meta, transcript_text = _fetch_both_concurrent(provider_mod, job.url)
        except Exception:
            # Fallback to sequential on executor failure
            meta = provider_mod.fetch_metadata(job.url)
            transcript_text = provider_mod.fetch_transcript(job.url)
    else:
        meta = provider_mod.fetch_metadata(job.url)
        try:
            transcript_text = provider_mod.fetch_transcript(job.url)
        except Exception:
            transcript_text = None

    # Determine creator/namespace (default to "unknown" if missing)
    creator_val = getattr(meta, creator_attr, None)
    creator = (str(creator_val).strip() if creator_val is not None else "") or "unknown"
    namespace = _vs.VectorStore.namespace(job.tenant, job.workspace, creator)

    # Capture published_at from metadata and normalize for payloads
    published_at_raw = getattr(meta, "published_at", None)
    published_at_norm = _normalize_published_at(published_at_raw)

    # Build segments -> chunks
    segs = _build_segments_from_text(transcript_text)
    chunks = _chunk_segments(segs)

    # Prepare embeddings and records
    texts = [c[2] for c in chunks]
    vectors = _vectorize(texts)
    records = [
        _vs.VectorRecord(
            vector=v,
            payload={
                "source_url": job.url,
                "start": c[0],
                "end": c[1],
                "text": c[2],
                "tags": job.tags,
                "published_at": published_at_norm,
            },
        )
        for v, c in zip(vectors, chunks, strict=False)
    ]

    # Upsert into the provided store
    store.upsert(namespace, records)
    return {"chunks": len(records), "namespace": namespace}


__all__ = ["IngestJob", "run"]
