from __future__ import annotations

import types
from dataclasses import dataclass
from datetime import datetime

from ingest import pipeline as ip


@dataclass
class _Meta:
    id: str | None
    channel: str | None
    published_at: object | None


def _capture_store(container: dict):
    def upsert(ns, recs):
        container["ns"] = ns
        container["vals"] = [r.payload.get("published_at") for r in recs]
    return types.SimpleNamespace(upsert=upsert)


def test_published_at_normalizes_naive_datetime(monkeypatch):
    prov = types.SimpleNamespace(
        fetch_metadata=lambda url: _Meta(id="x", channel="creator", published_at=datetime(2024, 1, 2, 3, 4, 5)),
        fetch_transcript=lambda url: "a\nb",
    )
    monkeypatch.setattr(ip, "_get_provider", lambda src: (prov, "channel"))
    captured: dict = {}
    store = _capture_store(captured)
    job = ip.IngestJob(source="youtube", external_id="e", url="u", tenant="t", workspace="w", tags=[])
    ip.run(job, store)
    vals = captured["vals"]
    assert all(isinstance(v, str) and v.endswith("+00:00") for v in vals)


def test_published_at_preserves_string_and_none(monkeypatch):
    # Case 1: string preserved
    prov1 = types.SimpleNamespace(
        fetch_metadata=lambda url: _Meta(id="x", channel="c", published_at="2024-01-02"),
        fetch_transcript=lambda url: "x\ny",
    )
    monkeypatch.setattr(ip, "_get_provider", lambda src: (prov1, "channel"))
    captured: dict = {}
    store = _capture_store(captured)
    job = ip.IngestJob(source="youtube", external_id="e", url="u1", tenant="t", workspace="w", tags=[])
    ip.run(job, store)
    assert all(v == "2024-01-02" for v in captured["vals"])

    # Case 2: None becomes empty string
    prov2 = types.SimpleNamespace(
        fetch_metadata=lambda url: _Meta(id="x", channel="c", published_at=None),
        fetch_transcript=lambda url: "x\ny",
    )
    monkeypatch.setattr(ip, "_get_provider", lambda src: (prov2, "channel"))
    captured2: dict = {}
    store2 = _capture_store(captured2)
    job2 = ip.IngestJob(source="youtube", external_id="e", url="u2", tenant="t", workspace="w", tags=[])
    ip.run(job2, store2)
    assert all(v == "" for v in captured2["vals"])

