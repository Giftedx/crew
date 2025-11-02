from __future__ import annotations

import types

from ingest import pipeline as ip
from obs import metrics


class _CounterStub:
    def __init__(self) -> None:
        self.count = 0

    def labels(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        # Accept both positional and keyword label styles
        self._labels = {"_pos": args, **kwargs}
        return self

    def inc(self):  # type: ignore[no-untyped-def]
        self.count += 1


def test_embedding_dedup_skips_duplicates(monkeypatch):
    # Provide provider with simple transcript lines; inject duplicates
    prov = types.SimpleNamespace(
        fetch_metadata=lambda url: types.SimpleNamespace(id="vid1", channel="chan", published_at=None),
        fetch_transcript=lambda url: "Line A\nLine B\nLine A\nLine C\nline a\n",  # duplicates of 'Line A' (case + whitespace)
    )
    monkeypatch.setattr(ip, "_get_provider", lambda src: (prov, "channel"))

    # Stub embeddings to count calls & return predictable vectors
    embed_calls = {}

    def fake_embed(texts, model_hint=None):  # type: ignore[no-untyped-def]
        embed_calls["calls"] = embed_calls.get("calls", 0) + 1
        # one vector per unique text (simple length-based vector for determinism)
        return [[len(t)] for t in texts]

    from memory import embeddings as emb_mod

    monkeypatch.setattr(emb_mod, "embed", fake_embed)

    # Stub metric counter for EMBED_DEDUPLICATES_SKIPPED
    dedup_counter = _CounterStub()
    monkeypatch.setattr(metrics, "EMBED_DEDUPLICATES_SKIPPED", dedup_counter)

    # Stub pipeline steps completed metric (needed for embed step increment)
    steps_counter = _CounterStub()
    monkeypatch.setattr(metrics, "PIPELINE_STEPS_COMPLETED", steps_counter)
    # Stub request + duration metrics minimally
    req_counter = _CounterStub()
    monkeypatch.setattr(metrics, "PIPELINE_REQUESTS", req_counter)

    # Ensure privacy filter doesn't alter text (which could defeat duplicate detection in test)
    from core import privacy as privacy_mod

    monkeypatch.setattr(privacy_mod.privacy_filter, "filter_text", lambda text, ctx: (text, {}))

    class _DurationStub:
        def __init__(self):
            self.calls = []

        def labels(self, **k):  # type: ignore[no-untyped-def]
            self._lbl = k
            return self

        def observe(self, v):  # type: ignore[no-untyped-def]
            self.calls.append((getattr(self, "_lbl", {}), v))

    monkeypatch.setattr(metrics, "PIPELINE_DURATION", _DurationStub())

    # Force segmentation to return each transcript line as an individual chunk so duplicates are visible
    from analysis import segmenter as segmenter_mod

    def fake_chunk_transcript(transcript, *_, **__):  # type: ignore[no-untyped-def]
        return [types.SimpleNamespace(text=s.text, start=s.start, end=s.end) for s in transcript.segments]

    monkeypatch.setattr(segmenter_mod, "chunk_transcript", fake_chunk_transcript)

    store = types.SimpleNamespace(upsert=lambda ns, recs: None)  # type: ignore[arg-type]
    job = ip.IngestJob(source="youtube", external_id="e", url="u", tenant="t", workspace="w", tags=[])
    res = ip.run(job, store)

    # We expect 5 original lines -> after stripping/case normalization duplicates reduced.
    # Unique lines: 'Line A', 'Line B', 'Line C'. So embeddings.embed should be called once with 3 texts.
    assert embed_calls.get("calls", 0) == 1
    # Dedup counter should have incremented exactly once (duplicates present)
    assert dedup_counter.count == 1
    # Steps completed should include transcript + segment + embed (>=3)
    assert steps_counter.count >= 3
    assert res["chunks"] >= 1
