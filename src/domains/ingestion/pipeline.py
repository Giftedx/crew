"""Ingestion orchestration for media sources."""
from __future__ import annotations
import concurrent.futures
import contextlib
import hashlib
import os
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from analysis import segmenter, topics, transcribe
from core.error_handling import handle_error_safely
from core.privacy import privacy_filter
from core.time import default_utc_now
from ingest import models
from memory import embeddings, vector_store
from platform.observability import metrics
from .providers import twitch, youtube

@dataclass
class IngestJob:
    source: str
    external_id: str
    url: str
    tenant: str
    workspace: str
    tags: list[str]
    visibility: str = 'public'

def _get_provider(source: str):
    if source == 'youtube':
        return (youtube, 'channel')
    if source == 'twitch':
        return (twitch, 'streamer')
    raise ValueError(f'unknown source {source}')

def _fetch_both_concurrent(provider_mod: Any, url: str) -> tuple[Any, str | None]:
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
        except Exception:
            transcript_text = None
    return (meta, transcript_text)

def _build_transcript(job: IngestJob, transcript_text: str | None) -> transcribe.Transcript:
    if transcript_text is None:
        handle_error_safely(lambda: metrics.INGEST_TRANSCRIPT_FALLBACKS.labels(**metrics.label_ctx(), source=job.source).inc(), error_message=f'Failed to record transcript fallback metric for source {job.source}')
        return transcribe.run_whisper(job.url)
    lines = [line.strip() for line in transcript_text.splitlines() if line.strip()]
    return transcribe.Transcript([transcribe.Segment(start=float(i), end=float(i + 1), text=t) for i, t in enumerate(lines)])

def _normalize_published_at(value: Any) -> str:
    """Return a safe ISO8601 string for published_at or empty string.

    - Accepts None, str, datetime, or other types.
    - For naive datetimes, assume UTC to preserve monotonic ordering in tests.
    """
    if value is None:
        return ''
    if isinstance(value, str):
        return value
    if isinstance(value, datetime):
        dt = value if value.tzinfo else value.replace(tzinfo=UTC)
        return dt.isoformat()
    try:
        return str(value)
    except Exception:
        return ''

def run(job: IngestJob, store: vector_store.VectorStore) -> dict:
    """Run an ingest job and upsert transcript chunks into *store*.

    If `ENABLE_INGEST_CONCURRENT` is set, metadata & transcript retrieval
    execute concurrently (threaded) for supported sources.
    """
    provider_mod, creator_attr = _get_provider(job.source)
    strict = os.getenv('ENABLE_INGEST_STRICT', '').lower() in {'1', 'true', 'yes', 'on'}
    t0 = time.perf_counter()
    _status = 'ok'
    try:
        handle_error_safely(lambda: metrics.PIPELINE_REQUESTS.labels(**metrics.label_ctx()).inc(), error_message='Failed to record pipeline request metric')
        if os.getenv('ENABLE_INGEST_CONCURRENT'):
            try:
                meta, transcript_text = _fetch_both_concurrent(provider_mod, job.url)
            except Exception:
                handle_error_safely(lambda: metrics.DEGRADATION_EVENTS.labels(**metrics.label_ctx(), component='ingest', event_type='concurrency_executor_failure', severity='warn').inc(), error_message='Failed to record concurrency executor failure degradation event')
                meta = provider_mod.fetch_metadata(job.url)
                transcript_text = provider_mod.fetch_transcript(job.url)
        else:
            meta = provider_mod.fetch_metadata(job.url)
            try:
                transcript_text = provider_mod.fetch_transcript(job.url)
            except Exception:
                transcript_text = None
        creator_val = getattr(meta, creator_attr, None)
        creator = (str(creator_val).strip() if creator_val is not None else '') or 'unknown'
        transcript = _build_transcript(job, transcript_text)
        handle_error_safely(lambda: metrics.PIPELINE_STEPS_COMPLETED.labels(**metrics.label_ctx(), step='transcript').inc(), error_message='Failed to record transcript completion metric')
        chunks = segmenter.chunk_transcript(transcript)
        handle_error_safely(lambda: metrics.PIPELINE_STEPS_COMPLETED.labels(**metrics.label_ctx(), step='segment').inc(), error_message='Failed to record segment completion metric')
        texts = []
        for c in chunks:
            clean, _ = privacy_filter.filter_text(c.text, {'tenant': job.tenant})
            c.text = clean
            texts.append(clean)
        _topics = topics.extract(' '.join(texts))
        norm_map: dict[str, int] = {}
        unique_texts: list[str] = []
        index_remap: list[int] = []
        for t in texts:
            key = t.strip().lower()
            if key in norm_map:
                index_remap.append(norm_map[key])
            else:
                norm_map[key] = len(unique_texts)
                index_remap.append(len(unique_texts))
                unique_texts.append(t)
        dup_count = len(texts) - len(unique_texts)
        if dup_count:
            handle_error_safely(lambda: metrics.EMBED_DEDUPLICATES_SKIPPED.labels(**metrics.label_ctx()).inc(), error_message='Failed to record embed dedup skipped metric')
        vectors_unique = embeddings.embed(unique_texts, model_hint=None)
        vectors = [vectors_unique[i] for i in index_remap]
        handle_error_safely(lambda: metrics.PIPELINE_STEPS_COMPLETED.labels(**metrics.label_ctx(), step='embed').inc(), error_message='Failed to record embed completion metric')
        namespace = vector_store.VectorStore.namespace(job.tenant, job.workspace, creator)
        meta_id = getattr(meta, 'id', None)
        is_missing_id = not meta_id
        episode_id = meta_id or hashlib.sha256(job.url.encode('utf-8')).hexdigest()[:16]
        if is_missing_id:
            handle_error_safely(lambda: metrics.INGEST_MISSING_ID_FALLBACKS.labels(**metrics.label_ctx(), source=job.source).inc(), error_message=f'Failed to record missing ID fallback metric for source {job.source}')
        if strict and (creator == 'unknown' or is_missing_id):
            missing = []
            if creator == 'unknown':
                missing.append('creator')
            if is_missing_id:
                missing.append('episode_id')
            raise ValueError(f'ingest strict mode violation: missing {', '.join(missing)}')
        records = [vector_store.VectorRecord(vector=v, payload={'source_url': job.url, 'start': c.start, 'end': c.end, 'text': c.text, 'tags': job.tags, 'episode_id': episode_id, 'published_at': _normalize_published_at(getattr(meta, 'published_at', None))}) for v, c in zip(vectors, chunks, strict=False)]
        store.upsert(namespace, records)
        handle_error_safely(lambda: metrics.PIPELINE_STEPS_COMPLETED.labels(**metrics.label_ctx(), step='upsert').inc(), error_message='Failed to record upsert completion metric')
        db_path = os.getenv('INGEST_DB_PATH')
        if db_path:
            conn = models.connect(db_path)
            checksum = hashlib.sha256(''.join(texts).encode('utf-8')).hexdigest()
            prov = models.Provenance(id=None, content_id=episode_id, source_url=job.url, source_type=job.source, retrieved_at=default_utc_now().isoformat(), license='unknown', terms_url=None, consent_flags=None, checksum_sha256=checksum, creator_id=None, episode_id=None)
            models.record_provenance(conn, prov)
            try:
                if os.getenv('ENABLE_YOUTUBE_CHANNEL_BACKFILL_AFTER_INGEST', '0') == '1' and job.source == 'youtube':
                    chan_id = getattr(meta, 'channel_id', None)
                    chan_handle = getattr(meta, 'channel', None)
                    handle_url: str | None = None
                    if chan_id:
                        handle_url = f'https://www.youtube.com/channel/{chan_id}/videos'
                    elif isinstance(chan_handle, str) and chan_handle.strip():
                        h = chan_handle.strip()
                        if not h.startswith('@'):
                            h = f'@{h}'
                        handle_url = f'https://www.youtube.com/{h}/videos'
                    if handle_url:
                        models.ensure_watchlist(conn, tenant=job.tenant, workspace=job.workspace, source_type='youtube_channel', handle=handle_url, label=None)
                        if isinstance(chan_id, str) and chan_id:
                            with contextlib.suppress(Exception):
                                models.upsert_creator_by_youtube_channel(conn, tenant=job.tenant, workspace=job.workspace, channel_id=chan_id)
            except Exception:
                pass
        return {'chunks': len(records), 'namespace': namespace}
    except Exception:
        _status = 'error'
        handle_error_safely(lambda: metrics.PIPELINE_STEPS_FAILED.labels(**metrics.label_ctx(), step='run').inc(), error_message='Failed to record pipeline failure metric')
        raise
    finally:
        elapsed = max(0.0, time.perf_counter() - t0)
        handle_error_safely(lambda: metrics.PIPELINE_DURATION.labels(**metrics.label_ctx(), status=_status).observe(elapsed), error_message='Failed to record pipeline duration metric')