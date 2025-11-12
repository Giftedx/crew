from __future__ import annotations

from core import degradation_reporter as dr
from ultimate_discord_intelligence_bot.obs import metrics


class EnabledSettings:
    enable_degradation_reporter = True


class DisabledSettings:
    enable_degradation_reporter = False


def test_degradation_reporter_records_and_metrics(monkeypatch):
    metrics.reset()
    r = dr.get_degradation_reporter()
    r.clear()
    from core import settings as settings_mod

    monkeypatch.setattr(settings_mod, "get_settings", lambda: EnabledSettings())
    monkeypatch.setattr(dr, "get_settings", lambda: EnabledSettings())
    dr.record_degradation("ingest", "transcript_fallback", severity="warn", added_latency_ms=42.5)
    dr.record_degradation("ingest", "transcript_fallback", severity="warn")
    snapshot = r.snapshot()
    assert len(snapshot) == 2
    assert any(e.added_latency_ms == 42.5 for e in snapshot)
    rendered = metrics.render().decode("utf-8") if metrics.PROMETHEUS_AVAILABLE else ""
    assert "degradation_events_total" in rendered or not metrics.PROMETHEUS_AVAILABLE
    assert "degradation_impact_latency_ms" in rendered or not metrics.PROMETHEUS_AVAILABLE


def test_degradation_reporter_flag_gated(monkeypatch):
    metrics.reset()
    r = dr.get_degradation_reporter()
    r.clear()
    from core import settings as settings_mod

    monkeypatch.setattr(settings_mod, "get_settings", lambda: DisabledSettings())
    monkeypatch.setattr(dr, "get_settings", lambda: DisabledSettings())
    dr.record_degradation("rerank", "provider_fallback", severity="warn")
    assert r.snapshot() == []


def test_degradation_reporter_ring_buffer(monkeypatch):
    metrics.reset()
    small = dr.DegradationReporter(max_events=3)
    from core import settings as settings_mod

    monkeypatch.setattr(settings_mod, "get_settings", lambda: EnabledSettings())
    monkeypatch.setattr(dr, "get_settings", lambda: EnabledSettings())
    for i in range(10):
        small.record("comp", f"evt_{i}")
    snap = small.snapshot()
    assert len(snap) == 3
    suffixes = [e.event_type for e in snap]
    assert suffixes == ["evt_7", "evt_8", "evt_9"]
