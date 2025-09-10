from __future__ import annotations

import types

from ingest import pipeline as ip
from obs import metrics


class _CounterStub:
    def __init__(self) -> None:
        self.steps: list[str] = []

    def labels(self, **kwargs):  # type: ignore[no-untyped-def]
        # Capture step label if present
        s = kwargs.get("step")
        if s:
            self.steps.append(str(s))
        return self

    def inc(self) -> None:
        return None


def test_pipeline_emits_step_upsert(monkeypatch):
    prov = types.SimpleNamespace(
        fetch_metadata=lambda url: types.SimpleNamespace(id="x", channel="c", published_at=None),
        fetch_transcript=lambda url: "a\nb",
    )
    monkeypatch.setattr(ip, "_get_provider", lambda src: (prov, "channel"))
    stub = _CounterStub()
    monkeypatch.setattr(metrics, "PIPELINE_STEPS_COMPLETED", stub)
    store = types.SimpleNamespace(upsert=lambda ns, recs: None)
    job = ip.IngestJob(source="youtube", external_id="e", url="u", tenant="t", workspace="w", tags=[])
    ip.run(job, store)
    assert "upsert" in stub.steps


def test_pipeline_emits_failed_on_exception(monkeypatch):
    prov = types.SimpleNamespace(
        fetch_metadata=lambda url: types.SimpleNamespace(id=None, channel=None, published_at=None),
        fetch_transcript=lambda url: "a\nb",
    )
    monkeypatch.setattr(ip, "_get_provider", lambda src: (prov, "channel"))
    failed = _CounterStub()
    monkeypatch.setattr(metrics, "PIPELINE_STEPS_FAILED", failed)
    store = types.SimpleNamespace(upsert=lambda ns, recs: None)
    job = ip.IngestJob(source="youtube", external_id="e", url="u", tenant="t", workspace="w", tags=[])
    monkeypatch.setenv("ENABLE_INGEST_STRICT", "1")
    try:
        ip.run(job, store)
    except ValueError:
        pass
    else:  # pragma: no cover
        assert False, "expected strict mode to raise"
    assert "run" in failed.steps
