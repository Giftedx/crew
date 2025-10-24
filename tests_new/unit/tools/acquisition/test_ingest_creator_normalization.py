from __future__ import annotations

import types
from dataclasses import dataclass

from ingest import pipeline as ip


@dataclass
class _Meta:
    id: str | None
    channel: object | None


def test_creator_fallback_unknown(monkeypatch):
    prov = types.SimpleNamespace(
        fetch_metadata=lambda url: _Meta(id="x", channel=None),
        fetch_transcript=lambda url: "hello\nworld",
    )
    monkeypatch.setattr(ip, "_get_provider", lambda src: (prov, "channel"))
    captured = {}
    store = types.SimpleNamespace(upsert=lambda ns, recs: captured.setdefault("ns", ns))
    job = ip.IngestJob(source="youtube", external_id="e", url="u", tenant="t", workspace="w", tags=[])
    ip.run(job, store)
    assert captured["ns"] == "t:w:unknown"


def test_creator_non_string_is_coerced(monkeypatch):
    prov = types.SimpleNamespace(
        fetch_metadata=lambda url: _Meta(id="x", channel=12345),
        fetch_transcript=lambda url: "a\nb",
    )
    monkeypatch.setattr(ip, "_get_provider", lambda src: (prov, "channel"))
    captured = {}
    store = types.SimpleNamespace(upsert=lambda ns, recs: captured.setdefault("ns", ns))
    job = ip.IngestJob(source="youtube", external_id="e", url="u", tenant="t", workspace="w", tags=[])
    ip.run(job, store)
    # f-string coercion produces a string namespace
    assert captured["ns"] == "t:w:12345"
