from __future__ import annotations

from typing import Any

import pytest

from opentelemetry import trace as trace_api
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExporter


class _RecordingProcessor:
    def __init__(self) -> None:
        self.started: list[Any] = []
        self.ended: list[Any] = []
        self.force_flush_calls: list[int] = []
        self.shutdown_calls = 0

    def on_start(self, span: Any, parent: Any) -> None:  # pragma: no cover - simple method
        self.started.append(span)

    def on_end(self, span: Any) -> None:  # pragma: no cover - simple method
        self.ended.append(span)

    def force_flush(self, timeout_millis: int = 30000) -> bool:  # pragma: no cover - simple method
        self.force_flush_calls.append(timeout_millis)
        return True

    def shutdown(self) -> None:  # pragma: no cover - simple method
        self.shutdown_calls += 1


class _RecordingExporter(SpanExporter):
    def __init__(self) -> None:
        self.batches: list[list[Any]] = []

    def export(self, spans):  # pragma: no cover - simple method
        self.batches.append(list(spans))
        return None

    def shutdown(self):  # pragma: no cover - simple method
        self.batches.append(["shutdown"])


@pytest.fixture(autouse=True)
def _reset_tracer_provider(monkeypatch):
    monkeypatch.setattr(trace_api, "_GLOBAL_PROVIDER", None)
    yield
    monkeypatch.setattr(trace_api, "_GLOBAL_PROVIDER", None)


def test_tracer_notifies_processors_without_global_registration():
    provider = trace_api.TracerProvider()
    recorder = _RecordingProcessor()
    provider.add_span_processor(recorder)

    tracer = provider.get_tracer("example")
    span = tracer.start_span("operation")

    assert recorder.started == [span]
    assert recorder.ended == []

    span.end()
    assert recorder.started == [span]
    assert recorder.ended == [span]


def test_provider_force_flush_forwarding():
    provider = trace_api.TracerProvider()
    recorder = _RecordingProcessor()
    provider.add_span_processor(recorder)

    assert provider.force_flush(42) is True
    assert recorder.force_flush_calls == [42]


def test_batch_span_processor_flushes_on_force_and_shutdown():
    provider = trace_api.TracerProvider()
    trace_api.set_tracer_provider(provider)

    exporter = _RecordingExporter()
    batch = BatchSpanProcessor(exporter)
    provider.add_span_processor(batch)

    tracer = provider.get_tracer("demo")

    first = tracer.start_span("first")
    first.end()

    # Ending the span should not immediately export because the batch still buffers.
    assert exporter.batches == []

    assert provider.force_flush() is True
    assert len(exporter.batches) == 1
    assert exporter.batches[0][0] is first

    second = tracer.start_span("second")
    second.end()
    batch.shutdown()

    # Shutdown should flush remaining spans and call exporter shutdown.
    assert len(exporter.batches) == 3
    assert exporter.batches[1][0] is second
    assert exporter.batches[2] == ["shutdown"]
