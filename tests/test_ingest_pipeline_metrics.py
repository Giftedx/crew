from __future__ import annotations

import types

from ingest import pipeline as ip
from obs import metrics


class _HistogramStub:
    def __init__(self) -> None:
        self.calls: list[tuple[dict[str, str], float]] = []

    def labels(self, **kwargs):  # type: ignore[no-untyped-def]
        self._labels = dict(kwargs)
        return self

    def observe(self, value: float) -> None:
        self.calls.append((getattr(self, "_labels", {}), float(value)))


def test_pipeline_emits_duration_ok(monkeypatch):
    prov = types.SimpleNamespace(
        fetch_metadata=lambda url: types.SimpleNamespace(id="x", channel="c", published_at=None),
        fetch_transcript=lambda url: "a\nb",
    )
    monkeypatch.setattr(ip, "_get_provider", lambda src: (prov, "channel"))
    stub = _HistogramStub()
    req = type(
        "_C",
        (),
        {
            "count": 0,
            "labels": lambda self, **k: self,
            "inc": lambda self: setattr(self, "count", getattr(self, "count", 0) + 1),
        },
    )()
    monkeypatch.setattr(metrics, "PIPELINE_DURATION", stub)
    monkeypatch.setattr(metrics, "PIPELINE_REQUESTS", req)
    store = types.SimpleNamespace(upsert=lambda ns, recs: None)
    job = ip.IngestJob(source="youtube", external_id="e", url="u", tenant="t", workspace="w", tags=[])
    res = ip.run(job, store)
    assert res["chunks"] > 0
    assert any(lbls.get("status") == "ok" for lbls, _ in stub.calls)
    assert getattr(req, "count", 0) >= 1


def test_pipeline_emits_duration_error_on_exception(monkeypatch):
    prov = types.SimpleNamespace(
        fetch_metadata=lambda url: types.SimpleNamespace(id=None, channel=None, published_at=None),
        fetch_transcript=lambda url: "a\nb",
    )
    monkeypatch.setattr(ip, "_get_provider", lambda src: (prov, "channel"))
    stub = _HistogramStub()
    monkeypatch.setattr(metrics, "PIPELINE_DURATION", stub)
    monkeypatch.setenv("ENABLE_INGEST_STRICT", "1")
    store = types.SimpleNamespace(upsert=lambda ns, recs: None)
    job = ip.IngestJob(source="youtube", external_id="e", url="u", tenant="t", workspace="w", tags=[])
    try:
        ip.run(job, store)
    except ValueError:
        pass
    else:  # pragma: no cover
        assert False, "expected strict mode to raise"
    assert any(lbls.get("status") == "error" for lbls, _ in stub.calls)
