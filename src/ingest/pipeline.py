from __future__ import annotations

"""Ingestion orchestration for media sources."""

from dataclasses import dataclass
from typing import List, Optional, Tuple, Any, Callable
import concurrent.futures

from analysis import segmenter, topics, transcribe
from memory import embeddings, vector_store
from .providers import youtube, twitch
from core.privacy import privacy_filter
from ingest import models
import hashlib
import os
from datetime import datetime, timezone


@dataclass
class IngestJob:
    source: str
    external_id: str
    url: str
    tenant: str
    workspace: str
    tags: List[str]
    visibility: str = "public"


def _get_provider(source: str):
    if source == "youtube":
        return youtube, "channel"
    if source == "twitch":
        return twitch, "streamer"
    raise ValueError(f"unknown source {source}")  # pragma: no cover - defensive


def _fetch_both_concurrent(provider_mod: Any, url: str) -> Tuple[Any, Optional[str]]:
    """Fetch metadata & transcript concurrently.

    Falls back to sequential if an exception arises in transcript fetch; metadata
    failure propagates (cannot proceed without it).
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        fut_meta = ex.submit(provider_mod.fetch_metadata, url)
        fut_tx = ex.submit(provider_mod.fetch_transcript, url)
        meta = fut_meta.result()
        try:
            transcript_text = fut_tx.result()
        except Exception:  # pragma: no cover - defensive; fallback to None
            transcript_text = None
    return meta, transcript_text


def _build_transcript(job: IngestJob, transcript_text: Optional[str]) -> transcribe.Transcript:
    if transcript_text is None:
        return transcribe.run_whisper(job.url)
    lines = [l.strip() for l in transcript_text.splitlines() if l.strip()]
    return transcribe.Transcript([
        transcribe.Segment(start=float(i), end=float(i + 1), text=t)
        for i, t in enumerate(lines)
    ])


def run(job: IngestJob, store: vector_store.VectorStore) -> dict:
    """Run an ingest job and upsert transcript chunks into *store*.

    If `ENABLE_INGEST_CONCURRENT` is set, metadata & transcript retrieval
    execute concurrently (threaded) for supported sources.
    """

    provider_mod, creator_attr = _get_provider(job.source)

    if os.getenv("ENABLE_INGEST_CONCURRENT"):
        try:
            meta, transcript_text = _fetch_both_concurrent(provider_mod, job.url)
        except Exception:
            # Fallback to sequential path on unexpected executor failure
            meta = provider_mod.fetch_metadata(job.url)
            transcript_text = provider_mod.fetch_transcript(job.url)
    else:
        meta = provider_mod.fetch_metadata(job.url)
        transcript_text = provider_mod.fetch_transcript(job.url)

    creator = getattr(meta, creator_attr)
    transcript = _build_transcript(job, transcript_text)

    chunks = segmenter.chunk_transcript(transcript)
    texts = []
    for c in chunks:
        clean, _ = privacy_filter.filter_text(c.text, {"tenant": job.tenant})
        c.text = clean
        texts.append(clean)
    _topics = topics.extract(" ".join(texts))
    vectors = embeddings.embed(texts, model_hint=None)
    namespace = vector_store.VectorStore.namespace(job.tenant, job.workspace, creator)
    records = [
        vector_store.VectorRecord(
            vector=v,
            payload={
                "source_url": job.url,
                "start": c.start,
                "end": c.end,
                "text": c.text,
                "tags": job.tags,
                "episode_id": meta.id,
                "published_at": getattr(meta, "published_at", None),
            },
        )
        for v, c in zip(vectors, chunks)
    ]
    store.upsert(namespace, records)
    db_path = os.getenv("INGEST_DB_PATH")
    if db_path:
        conn = models.connect(db_path)
        checksum = hashlib.sha256("".join(texts).encode("utf-8")).hexdigest()
        prov = models.Provenance(
            id=None,
            content_id=meta.id,
            source_url=job.url,
            source_type=job.source,
            retrieved_at=datetime.now(timezone.utc).isoformat(),
            license="unknown",
            terms_url=None,
            consent_flags=None,
            checksum_sha256=checksum,
            creator_id=None,
            episode_id=None,
        )
        models.record_provenance(conn, prov)
    return {"chunks": len(records), "namespace": namespace}
