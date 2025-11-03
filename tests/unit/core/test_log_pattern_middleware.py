import asyncio
import logging
import time
from platform.core.step_result import StepResult

from ultimate_discord_intelligence_bot.pipeline_components.log_pattern_middleware import LogPatternMiddleware
from ultimate_discord_intelligence_bot.pipeline_components.middleware import StepContext
from ultimate_discord_intelligence_bot.pipeline_components.mixins import PipelineExecutionMixin


class _DummyPipeline:
    def __init__(self) -> None:
        self.logger = logging.getLogger("ultimate_discord_intelligence_bot.test_pipeline")
        self._orchestrator = "DummyPipeline"


def test_log_pattern_middleware_attaches_summary() -> None:
    middleware = LogPatternMiddleware(max_patterns=3)
    pipeline = _DummyPipeline()
    context = StepContext(step="demo", args=(), kwargs={}, pipeline=pipeline)

    async def _run() -> None:
        await middleware.before_step(context)
        logging.getLogger().setLevel(logging.INFO)
        logger = logging.getLogger("ultimate_discord_intelligence_bot.test_pipeline")
        logger.setLevel(logging.INFO)
        logger.info("Processing item 42")
        logger.warning("Processing item 42 failed once")
        logger.warning("Processing item 42 failed once")
        context.result = StepResult.ok(value="demo")
        await middleware.after_step(context)

    root_level = logging.getLogger().level
    try:
        asyncio.run(_run())
    finally:
        logging.getLogger().setLevel(root_level)
    summary = context.result.metadata["observability"]["log_patterns"]
    assert summary["total_records"] >= 3
    assert summary["levels"]["WARNING"] >= 2
    assert any(pattern["count"] >= 2 for pattern in summary["top_patterns"])


def test_log_pattern_middleware_captures_summary_on_error() -> None:
    middleware = LogPatternMiddleware()
    pipeline = _DummyPipeline()
    context = StepContext(step="demo", args=(), kwargs={}, pipeline=pipeline)

    async def _run() -> None:
        await middleware.before_step(context)
        logger = logging.getLogger("ultimate_discord_intelligence_bot.test_pipeline")
        logger.error("Unable to connect to service 12345")
        await middleware.on_error(context)

    asyncio.run(_run())
    summary = context.metadata.get("log_patterns.summary")
    assert summary is not None
    assert summary["total_records"] == 1
    assert summary["recent_errors"]
    assert summary["recent_errors"][0]["message"].startswith("Unable to connect")


class _ObservabilityPipeline(PipelineExecutionMixin):
    def __init__(self) -> None:
        self.logger = logging.getLogger("ultimate_discord_intelligence_bot.test_observability_pipeline")
        self._orchestrator = "ObservabilityPipeline"
        self._step_middlewares = [LogPatternMiddleware(max_patterns=5)]
        self._step_observability: dict[str, dict[str, object]] = {}

    @property
    def step_middlewares(self):
        return tuple(self._step_middlewares)

    async def _run_with_retries(self, func, *args, **kwargs) -> StepResult:
        local_kwargs = dict(kwargs)
        local_kwargs.pop("step", None)
        local_kwargs.pop("attempts", None)
        local_kwargs.pop("delay", None)
        local_kwargs.pop("retry_delay", None)
        local_kwargs.pop("check_tool_rate_limit", None)
        result = await func(*args, **local_kwargs)
        return result if isinstance(result, StepResult) else StepResult.from_dict(result)

    def _record_step_metrics(self, step: str, outcome: str, duration: float | None) -> None:
        return None

    def _record_pipeline_duration(self, status: str, duration: float) -> None:
        return None

    def _record_dashboard_metrics_background(self, payload: dict[str, object], duration: float) -> None:
        return None


def test_pipeline_final_payload_includes_observability_summary() -> None:
    pipeline = _ObservabilityPipeline()
    root_level = logging.getLogger().level

    async def _run() -> None:
        logger = logging.getLogger("ultimate_discord_intelligence_bot.test_observability_pipeline")

        async def _step() -> StepResult:
            logger.warning("Processing item 42 failed once")
            logger.warning("Processing item 42 failed once")
            return StepResult.ok(result="done")

        start = time.monotonic()
        result = await pipeline._execute_step("analysis", _step)
        assert result.success
        payload = pipeline._finalize_pipeline(start, "success", {"status": "success"})
        observability = payload.get("observability", {}).get("log_patterns")
        assert observability is not None
        assert "summary" in observability
        assert "per_step" in observability
        assert "analysis" in observability["per_step"]
        assert observability["summary"]["step_count"] == 1
        assert observability["summary"]["total_records"] >= 2
        assert pipeline._step_observability == {}

    try:
        logging.getLogger().setLevel(logging.INFO)
        asyncio.run(_run())
    finally:
        logging.getLogger().setLevel(root_level)


def test_pipeline_observability_records_failure_summary() -> None:
    pipeline = _ObservabilityPipeline()
    root_level = logging.getLogger().level

    async def _run() -> None:
        logger = logging.getLogger("ultimate_discord_intelligence_bot.test_observability_pipeline")

        async def _step() -> StepResult:
            logger.error("Unable to connect to backend 5001")
            raise RuntimeError("failure")

        start = time.monotonic()
        result = await pipeline._execute_step("analysis", _step)
        assert not result.success
        payload = pipeline._finalize_pipeline(start, "error", {"status": "error"})
        observability = payload.get("observability", {}).get("log_patterns")
        assert observability is not None
        assert observability["summary"]["step_count"] == 1
        assert observability["summary"]["recent_errors"]
        assert pipeline._step_observability == {}

    try:
        logging.getLogger().setLevel(logging.INFO)
        asyncio.run(_run())
    finally:
        logging.getLogger().setLevel(root_level)
