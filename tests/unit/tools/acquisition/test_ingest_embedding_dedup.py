from __future__ import annotations

import types

from ingest import pipeline as ip
from ultimate_discord_intelligence_bot.obs import metrics


class _CounterStub:
    def __init__(self) -> None:
        self.count = 0

    def labels(self, *args, **kwargs):
        self._labels = {"_pos": args, **kwargs}
        return self

    def inc(self):
        self.count += 1


def test_embedding_dedup_skips_duplicates(monkeypatch):
    prov = types.SimpleNamespace(
        fetch_metadata=lambda url: types.SimpleNamespace(id="vid1", channel="chan", published_at=None),
        fetch_transcript=lambda url: "Line A\nLine B\nLine A\nLine C\nline a\n",
    )
    monkeypatch.setattr(ip, "_get_provider", lambda src: (prov, "channel"))
    embed_calls = {}

    def fake_embed(texts, model_hint=None):
        embed_calls["calls"] = embed_calls.get("calls", 0) + 1
        return [[len(t)] for t in texts]

    from memory import embeddings as emb_mod

    monkeypatch.setattr(emb_mod, "embed", fake_embed)
    dedup_counter = _CounterStub()
    monkeypatch.setattr(metrics, "EMBED_DEDUPLICATES_SKIPPED", dedup_counter)
    steps_counter = _CounterStub()
    monkeypatch.setattr(metrics, "PIPELINE_STEPS_COMPLETED", steps_counter)
    req_counter = _CounterStub()
    monkeypatch.setattr(metrics, "PIPELINE_REQUESTS", req_counter)
    from core import privacy as privacy_mod

    monkeypatch.setattr(privacy_mod.privacy_filter, "filter_text", lambda text, ctx: (text, {}))

    class _DurationStub:
        def __init__(self):
            self.calls = []

        def labels(self, **k):
            self._lbl = k
            return self

        def observe(self, v):
            self.calls.append((getattr(self, "_lbl", {}), v))

    monkeypatch.setattr(metrics, "PIPELINE_DURATION", _DurationStub())
    from analysis import segmenter as segmenter_mod

    def fake_chunk_transcript(transcript, *_, **__):
        return [types.SimpleNamespace(text=s.text, start=s.start, end=s.end) for s in transcript.segments]

    monkeypatch.setattr(segmenter_mod, "chunk_transcript", fake_chunk_transcript)
    store = types.SimpleNamespace(upsert=lambda ns, recs: None)
    job = ip.IngestJob(source="youtube", external_id="e", url="u", tenant="t", workspace="w", tags=[])
    res = ip.run(job, store)
    assert embed_calls.get("calls", 0) == 1
    assert dedup_counter.count == 1
    assert steps_counter.count >= 3
    assert res["chunks"] >= 1
