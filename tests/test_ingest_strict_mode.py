from __future__ import annotations

import types

import pytest
from ingest import pipeline as ip


def test_strict_mode_missing_both_raises(monkeypatch):
    monkeypatch.setenv("ENABLE_INGEST_STRICT", "1")
    prov = types.SimpleNamespace(
        fetch_metadata=lambda url: types.SimpleNamespace(id=None, channel=None),
        fetch_transcript=lambda url: "a\nb",
    )
    monkeypatch.setattr(ip, "_get_provider", lambda src: (prov, "channel"))
    store = types.SimpleNamespace(upsert=lambda ns, recs: None)
    job = ip.IngestJob(source="youtube", external_id="e", url="u", tenant="t", workspace="w", tags=[])
    with pytest.raises(ValueError):
        ip.run(job, store)


def test_strict_mode_missing_creator_raises(monkeypatch):
    monkeypatch.setenv("ENABLE_INGEST_STRICT", "1")
    prov = types.SimpleNamespace(
        fetch_metadata=lambda url: types.SimpleNamespace(id="x", channel=None),
        fetch_transcript=lambda url: "a\nb",
    )
    monkeypatch.setattr(ip, "_get_provider", lambda src: (prov, "channel"))
    store = types.SimpleNamespace(upsert=lambda ns, recs: None)
    job = ip.IngestJob(source="youtube", external_id="e", url="u", tenant="t", workspace="w", tags=[])
    with pytest.raises(ValueError):
        ip.run(job, store)


def test_strict_mode_missing_id_raises(monkeypatch):
    monkeypatch.setenv("ENABLE_INGEST_STRICT", "1")
    prov = types.SimpleNamespace(
        fetch_metadata=lambda url: types.SimpleNamespace(id=None, channel="c"),
        fetch_transcript=lambda url: "a\nb",
    )
    monkeypatch.setattr(ip, "_get_provider", lambda src: (prov, "channel"))
    store = types.SimpleNamespace(upsert=lambda ns, recs: None)
    job = ip.IngestJob(source="youtube", external_id="e", url="u", tenant="t", workspace="w", tags=[])
    with pytest.raises(ValueError):
        ip.run(job, store)
