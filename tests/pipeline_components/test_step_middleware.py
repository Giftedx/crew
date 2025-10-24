import asyncio
import logging
from collections.abc import Iterable

from ultimate_discord_intelligence_bot.pipeline_components.middleware import (
    BasePipelineStepMiddleware,
    StepContext,
    TracingStepMiddleware,
)
from ultimate_discord_intelligence_bot.pipeline_components.mixins import (
    PipelineExecutionMixin,
)
from ultimate_discord_intelligence_bot.step_result import StepResult


class _StubPipeline(PipelineExecutionMixin):
    def __init__(
        self,
        result: StepResult | Exception,
        *,
        middlewares: Iterable[BasePipelineStepMiddleware] = (),
    ) -> None:
        self._result = result
        self.step_middlewares = tuple(middlewares)
        self.logger = logging.getLogger("StubPipeline")
        self._orchestrator = "StubPipeline"
        self._metrics: list[tuple[str, str]] = []

    async def _run_with_retries(self, func, *args, **kwargs):  # type: ignore[override]
        if isinstance(self._result, Exception):
            raise self._result
        return self._result

    def _record_step_metrics(self, step: str, outcome: str, duration: float | None) -> None:  # type: ignore[override]
        self._metrics.append((step, outcome))


class _RecorderMiddleware(BasePipelineStepMiddleware):
    def __init__(self) -> None:
        self.events: list[tuple[str, StepContext]] = []

    async def before_step(self, context: StepContext) -> None:
        self.events.append(("before", context))

    async def after_step(self, context: StepContext) -> None:
        self.events.append(("after", context))

    async def on_error(self, context: StepContext) -> None:
        self.events.append(("error", context))


def test_execute_step_invokes_middleware_hooks() -> None:
    middleware = _RecorderMiddleware()
    result = StepResult.ok(data={"value": 42})
    pipeline = _StubPipeline(result, middlewares=[middleware])

    async def runner() -> None:
        outcome = await pipeline._execute_step(
            "analysis",
            lambda x, *, y: StepResult.ok(data={"value": x + y}),
            40,
            y=2,
        )

        assert outcome == result
        assert [event for event, _ in middleware.events] == ["before", "after"]
        before_context = middleware.events[0][1]
        after_context = middleware.events[1][1]
        assert before_context.step == "analysis"
        assert before_context.args == (40,)
        assert before_context.kwargs == {"y": 2}
        assert before_context is after_context
        assert after_context.result == result
        assert after_context.exception is None

    asyncio.run(runner())


def test_execute_step_triggers_on_error_for_exceptions() -> None:
    middleware = _RecorderMiddleware()
    pipeline = _StubPipeline(RuntimeError("fatal"), middlewares=[middleware])

    async def runner() -> None:
        outcome = await pipeline._execute_step("download", lambda: StepResult.ok(), 0)

        assert outcome.success is False
        assert outcome.error == "fatal"
        assert [event for event, _ in middleware.events] == ["before", "error"]
        error_context = middleware.events[-1][1]
        assert error_context.exception is not None
        assert isinstance(error_context.exception, RuntimeError)

    asyncio.run(runner())


def test_middleware_errors_do_not_break_pipeline() -> None:
    class FaultyMiddleware(BasePipelineStepMiddleware):
        async def before_step(self, context: StepContext) -> None:
            raise RuntimeError("hook boom")

    recorder = _RecorderMiddleware()
    result = StepResult.ok(data={"value": 1})
    pipeline = _StubPipeline(result, middlewares=[FaultyMiddleware(), recorder])

    async def runner() -> None:
        outcome = await pipeline._execute_step("memory", lambda: StepResult.ok(), 0)

        assert outcome == result
        assert [event for event, _ in recorder.events] == ["before", "after"]
        assert pipeline._metrics[0][0] == "memory"

    asyncio.run(runner())


def test_tracing_middleware_records_span(monkeypatch) -> None:
    recorder: dict[str, list] = {"entered": [], "exits": [], "attrs": []}

    class DummySpan:
        def __init__(self, name: str) -> None:
            self.name = name

        def __enter__(self) -> "DummySpan":
            recorder["entered"].append(self.name)
            return self

        def __exit__(self, exc_type, exc, _tb) -> None:
            recorder["exits"].append((self.name, exc_type))

        def set_attribute(self, key: str, value: object) -> None:
            recorder["attrs"].append((key, value))

    class DummyTracing:
        def start_span(self, name: str) -> DummySpan:
            return DummySpan(name)

    monkeypatch.setattr(
        "ultimate_discord_intelligence_bot.pipeline_components.middleware.tracing_module",
        DummyTracing(),
    )

    result = StepResult.ok(data={"value": 7})
    pipeline = _StubPipeline(result, middlewares=[TracingStepMiddleware()])

    async def runner() -> None:
        await pipeline._execute_step("analysis", lambda: StepResult.ok(data={"value": 7}))

    asyncio.run(runner())

    assert recorder["entered"] == ["pipeline.step.analysis"]
    assert recorder["exits"] == [("pipeline.step.analysis", None)]
    attr_keys = {key for key, _ in recorder["attrs"]}
    assert "step.name" in attr_keys
    assert "step.duration_ms" in attr_keys
    assert ("step.success", True) in recorder["attrs"]
    assert any(key == "step.error_flag" and value is False for key, value in recorder["attrs"])


def test_tracing_middleware_records_error(monkeypatch) -> None:
    recorder: dict[str, list] = {"entered": [], "exits": [], "attrs": []}

    class DummySpan:
        def __init__(self, name: str) -> None:
            self.name = name

        def __enter__(self) -> "DummySpan":
            recorder["entered"].append(self.name)
            return self

        def __exit__(self, exc_type, exc, _tb) -> None:
            recorder["exits"].append((self.name, exc_type.__name__ if exc_type else None))

        def set_attribute(self, key: str, value: object) -> None:
            recorder["attrs"].append((key, value))

    class DummyTracing:
        def start_span(self, name: str) -> DummySpan:
            return DummySpan(name)

    monkeypatch.setattr(
        "ultimate_discord_intelligence_bot.pipeline_components.middleware.tracing_module",
        DummyTracing(),
    )

    pipeline = _StubPipeline(RuntimeError("boom"), middlewares=[TracingStepMiddleware()])

    async def runner() -> None:
        await pipeline._execute_step("download", lambda: StepResult.ok(), 0)

    asyncio.run(runner())

    assert recorder["entered"] == ["pipeline.step.download"]
    assert recorder["exits"] == [("pipeline.step.download", "RuntimeError")]
    assert any(key == "step.error_flag" and value is True for key, value in recorder["attrs"])
    assert any(key == "step.error.type" and value == "RuntimeError" for key, value in recorder["attrs"])
