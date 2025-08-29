import importlib
import importlib.util

from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from discord import commands as dc
from obs import metrics, slo, tracing
from ultimate_discord_intelligence_bot.tenancy import TenantContext, with_tenant


def test_tracing_decorator_records_span():
    exporter = InMemorySpanExporter()
    tracing.init_tracing("test-service", exporter=exporter)

    @tracing.trace_call("demo")
    def add(x, y):
        return x + y

    assert add(1, 2) == 3
    spans = exporter.get_finished_spans()
    assert spans and spans[0].name == "demo"


def test_metrics_and_slo_and_incident_ops():
    metrics.reset()
    with with_tenant(TenantContext("t", "w")):
        metrics.ROUTER_DECISIONS.labels(**metrics.label_ctx()).inc()
    out = metrics.render()
    if importlib.util.find_spec("prometheus_client"):
        assert b'tenant="t"' in out
    else:
        assert out == b""

    evaluator = slo.SLOEvaluator([slo.SLO("latency_ms", 100)])
    result = evaluator.evaluate({"latency_ms": 150})
    assert result["latency_ms"] is False

    inc = dc.ops_incident_open("db down")
    inc_id = inc["id"]
    dc.ops_incident_ack(inc_id, "alice")
    dc.ops_incident_resolve(inc_id)
    listing = dc.ops_incident_list()
    assert any(i["id"] == inc_id and i["status"] == "resolved" for i in listing)


def test_ops_slo_status():
    slos = [slo.SLO("cost", 5.0)]
    res = dc.ops_slo_status({"cost": 2.0}, slos)
    assert res["cost"] is True


def test_logging_includes_tenant():
    import io
    import json
    import logging

    from obs import logging as obs_logging

    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    obs_logging.logger.addHandler(handler)
    try:
        with with_tenant(TenantContext("t", "w")):
            obs_logging.logger.info("hi")
        handler.flush()
        payload = json.loads(stream.getvalue().strip())
        assert payload["tenant"] == "t"
    finally:
        obs_logging.logger.removeHandler(handler)


def test_metrics_module_degrades_without_prometheus(monkeypatch):
    """Metrics module should operate with no-op stubs when Prometheus is absent."""
    import importlib
    import sys

    import obs.metrics as metrics_mod

    with monkeypatch.context() as m:
        m.setitem(sys.modules, "prometheus_client", None)
        importlib.reload(metrics_mod)
        metrics_mod.reset()
        metrics_mod.ROUTER_DECISIONS.labels(**metrics_mod.label_ctx()).inc()
        assert metrics_mod.render() == b""

    # restore real implementation for other tests
    importlib.reload(metrics_mod)
