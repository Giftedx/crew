import time

from ingest import pipeline
from ingest.pipeline import IngestJob


class DummyMeta:
    def __init__(self, id="vid1", channel="chan", streamer="stream", published_at=None):
        self.id = id
        self.channel = channel
        self.streamer = streamer
        self.published_at = published_at
        self.duration = 1.0
        self.url = "http://example.com"


# Monkeypatch targets for youtube provider


def test_concurrent_flag_monkeypatch_youtube(monkeypatch, tmp_path):
    """Verify concurrency flag executes metadata + transcript fetch in parallel.

    We assert on:
    - Returned chunk count (single chunk because all lines fit under max_chars)
    - Upserted record count
    - Wall clock improvement (<0.09s vs ~0.10s sequential)
    - Structural overlap: start timestamps of both fetches within 20ms.
    """

    fake_transcript = "line1\nline2\nline3"
    timings = {}

    def fake_fetch_metadata(url):
        timings["meta_start"] = time.time()
        time.sleep(0.05)  # simulate network delay
        timings["meta_end"] = time.time()
        return DummyMeta(channel="CreatorA")

    def fake_fetch_transcript(url):
        timings["tx_start"] = time.time()
        time.sleep(0.05)
        timings["tx_end"] = time.time()
        return fake_transcript

    import ingest.providers.youtube as ymod

    monkeypatch.setattr(ymod, "fetch_metadata", fake_fetch_metadata)
    monkeypatch.setattr(ymod, "fetch_transcript", fake_fetch_transcript)

    # Enable concurrency
    monkeypatch.setenv("ENABLE_INGEST_CONCURRENT", "1")

    # Use in-memory vector store substitute: monkeypatch vector_store.VectorStore.upsert to capture records
    from memory import vector_store

    captured = {}

    def fake_upsert(ns, recs):
        captured["ns"] = ns
        captured["count"] = len(recs)

    monkeypatch.setattr(vector_store.VectorStore, "upsert", lambda self, ns, recs: fake_upsert(ns, recs))

    store = vector_store.VectorStore()
    job = IngestJob(
        source="youtube",
        external_id="x",
        url="http://youtube.test/video",
        tenant="t1",
        workspace="w1",
        tags=["a"],
    )

    start = time.time()
    result = pipeline.run(job, store)
    elapsed = time.time() - start

    # All three short segments fit into one chunk with current max_chars settings.
    assert result["chunks"] == 1
    assert captured["count"] == 1
    # concurrency should reduce wall time below sequential (~0.10s). Allow margin.
    assert elapsed < 0.09
    # Structural overlap: the second task should start almost immediately after the first.
    assert "meta_start" in timings and "tx_start" in timings
    start_delta = abs(timings["meta_start"] - timings["tx_start"])
    assert start_delta < 0.02, f"Expected concurrent start (<20ms apart), delta={start_delta:.4f}s"


def test_concurrent_flag_fallback_sequential(monkeypatch):
    # disable flag - should still work; ensure slower (>=0.09) due to sequential sleeps
    fake_transcript = "one\n" * 2

    def fake_fetch_metadata(url):
        time.sleep(0.05)
        return DummyMeta(channel="C2")

    def fake_fetch_transcript(url):
        time.sleep(0.05)
        return fake_transcript

    import ingest.providers.youtube as ymod

    monkeypatch.setattr(ymod, "fetch_metadata", fake_fetch_metadata)
    monkeypatch.setattr(ymod, "fetch_transcript", fake_fetch_transcript)

    # Ensure flag not set
    monkeypatch.delenv("ENABLE_INGEST_CONCURRENT", raising=False)

    from memory import vector_store

    monkeypatch.setattr(vector_store.VectorStore, "upsert", lambda self, ns, recs: None)
    store = vector_store.VectorStore()
    job = IngestJob(
        source="youtube",
        external_id="x",
        url="http://youtube.test/video",
        tenant="t1",
        workspace="w1",
        tags=[],
    )
    start = time.time()
    result = pipeline.run(job, store)
    elapsed = time.time() - start
    # Two short segments also coalesce into a single chunk.
    assert result["chunks"] == 1
    assert elapsed >= 0.10
