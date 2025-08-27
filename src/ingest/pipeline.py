from __future__ import annotations

"""Ingestion orchestration for media sources."""

from dataclasses import dataclass
from typing import List, Optional

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


def run(job: IngestJob, store: vector_store.VectorStore) -> dict:
    """Run an ingest job and upsert transcript chunks into *store*."""

    if job.source == "youtube":
        meta = youtube.fetch_metadata(job.url)
        transcript_text = youtube.fetch_transcript(job.url)
        creator = meta.channel
    elif job.source == "twitch":
        meta = twitch.fetch_metadata(job.url)
        transcript_text = twitch.fetch_transcript(job.url)
        creator = meta.streamer
    else:  # pragma: no cover - defensive
        raise ValueError(f"unknown source {job.source}")

    if transcript_text is None:
        # fall back to running whisper on the media URL; in tests this will
        # be a small text file path.
        transcript = transcribe.run_whisper(job.url)
    else:
        # treat transcript text as lines
        lines = [l.strip() for l in transcript_text.splitlines() if l.strip()]
        transcript = transcribe.Transcript([
            transcribe.Segment(start=float(i), end=float(i + 1), text=t)
            for i, t in enumerate(lines)
        ])

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
