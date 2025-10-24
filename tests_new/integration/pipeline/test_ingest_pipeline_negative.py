from __future__ import annotations

import types
from dataclasses import dataclass

import pytest

from ingest import pipeline as ip


@dataclass
class _Meta:
    id: str
    channel: str | None = None
    streamer: str | None = None
    published_at: str | None = None


def test_ingest_pipeline_unsupported_source_errors():
    store = types.SimpleNamespace(upsert=lambda ns, recs: None)  # no-op
    job = ip.IngestJob(source="unknown", external_id="x", url="u", tenant="t", workspace="w", tags=[])
    with pytest.raises(ValueError):
        ip.run(job, store)  # unknown source handled by _get_provider


def test_ingest_pipeline_handles_missing_transcript(monkeypatch):
    # Provider with metadata but transcript fetch raising; run() should fall back to whisper path
    prov = types.SimpleNamespace(
        fetch_metadata=lambda url: _Meta(id="vid", channel="creator"),
        fetch_transcript=lambda url: (_ for _ in ()).throw(RuntimeError("tx failed")),
    )
    monkeypatch.setattr(ip, "_get_provider", lambda src: (prov, "channel"))

    # Minimal store that captures upserts and asserts records have text payloads
    captured = {}

    def upsert(ns, recs):
        captured["ns"] = ns
        captured["n"] = len(recs)
        assert all("text" in r.payload for r in recs)

    store = types.SimpleNamespace(upsert=upsert)

    # Monkeypatch whisper fallback to avoid file IO
    class _Seg:
        def __init__(self, start: float, end: float, text: str):
            self.start, self.end, self.text = start, end, text

    class _Tx:
        def __init__(self, segments):
            self.segments = segments

    monkeypatch.setattr(
        ip.transcribe,
        "run_whisper",
        lambda path: _Tx([_Seg(0.0, 1.0, "hello"), _Seg(1.0, 2.0, "world")]),
    )
    job = ip.IngestJob(
        source="youtube",
        external_id="x",
        url="https://x",
        tenant="t",
        workspace="w",
        tags=["a"],
    )
    # Force sequential path to exercise fallback without threads
    monkeypatch.delenv("ENABLE_INGEST_CONCURRENT", raising=False)
    res = ip.run(job, store)
    assert res["chunks"] == captured["n"]
    assert captured["ns"].startswith("t:w:")


def test_ingest_pipeline_missing_meta_id_uses_fallback(monkeypatch):
    # Provider returns metadata without an id; pipeline should derive a stable fallback from URL
    prov = types.SimpleNamespace(
        fetch_metadata=lambda url: _Meta(id=None, channel="creatorx"),
        fetch_transcript=lambda url: "line1\nline2",
    )
    monkeypatch.setattr(ip, "_get_provider", lambda src: (prov, "channel"))

    captured = {}

    def upsert(ns, recs):
        captured["ns"] = ns
        captured["ids"] = {r.payload.get("episode_id") for r in recs}
        assert all(r.payload.get("source_url") for r in recs)

    store = types.SimpleNamespace(upsert=upsert)
    job = ip.IngestJob(
        source="youtube",
        external_id="x",
        url="https://e/abc",
        tenant="t",
        workspace="w",
        tags=[],
    )
    ip.run(job, store)
    # Namespace uses creatorx
    assert captured["ns"] == "t:w:creatorx"
    # All records share the same derived episode id
    assert len(captured["ids"]) == 1
