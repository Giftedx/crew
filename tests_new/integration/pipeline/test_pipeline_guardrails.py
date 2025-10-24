from types import SimpleNamespace

import pytest

from ultimate_discord_intelligence_bot.pipeline import ContentPipeline, StepResult


class _StubRouter:
    def __init__(self, registry):
        self.tenant_registry = registry


class _BudgetRegistry:
    def get_request_total_limit(self, ctx):  # pragma: no cover - trivial
        return 5.0

    def get_per_task_cost_limits(self, ctx):  # pragma: no cover - trivial
        return {"analysis": 2.0, "perspective": 1.5}


class _StubTool:
    def __init__(self, result):
        self._result = result
        self.router = None

    def run(self, *_, **__):
        return self._result


class _AnalyzerTool(_StubTool):
    def __init__(self):
        super().__init__(StepResult.ok(sentiment="neutral", keywords=["stub"], data={"score": 0.5}))
        self.router = _StubRouter(_BudgetRegistry())


class _PerspectiveTool(_StubTool):
    def __init__(self, summary: str = "sanitise me"):
        super().__init__(StepResult.ok(summary=summary, perspectives=["p1"]))
        self.router = _StubRouter(_BudgetRegistry())


class _DownloaderTool(_StubTool):
    def __init__(self):
        super().__init__(
            StepResult.ok(
                local_path="/tmp/video.mp4",
                video_id="vid-123",
                title="Video Title",
                platform="YouTube",
            )
        )


class _TranscriberTool(_StubTool):
    def __init__(self):
        super().__init__(StepResult.ok(transcript="hello world"))


class _FallacyTool(_StubTool):
    def __init__(self):
        super().__init__(StepResult.ok(fallacies=[]))


class _MemoryTool(_StubTool):
    def __init__(self):
        super().__init__(StepResult.ok(collection="analysis", tenant_scoped=True))
        self.calls = []

    def run(self, text, metadata, **kwargs):
        self.calls.append((text, metadata, kwargs))
        return super().run(text, metadata, **kwargs)


class _DiscordTool(_StubTool):
    def __init__(self):
        super().__init__(StepResult.ok(message_id="123"))
        self.calls = []

    def run(self, payload, drive_links):
        self.calls.append((payload, drive_links))
        return super().run(payload, drive_links)


@pytest.mark.asyncio
async def test_run_with_retries_normalises_mapping(monkeypatch):
    pipeline = ContentPipeline(
        downloader=_DownloaderTool(),
        transcriber=_TranscriberTool(),
        analyzer=_AnalyzerTool(),
        drive=None,
        discord=None,
        fallacy_detector=_FallacyTool(),
        perspective=_PerspectiveTool(),
        memory=_MemoryTool(),
    )

    async def _stub_func():
        return {"status": "success", "value": 42}

    result = await pipeline._run_with_retries(_stub_func, step="stub", attempts=1, check_tool_rate_limit=False)
    assert isinstance(result, StepResult)
    assert result.success
    assert result["status"] == "success"
    assert result["value"] == 42


@pytest.mark.asyncio
async def test_process_video_uses_request_budget(monkeypatch):
    budget_events = []

    class _BudgetCtx:
        def __enter__(self):
            budget_events.append("enter")
            return SimpleNamespace()

        def __exit__(self, exc_type, exc, tb):
            budget_events.append("exit")
            return False

    def _fake_budget(total_limit=None, per_task_limits=None):
        assert isinstance(per_task_limits, dict)
        return _BudgetCtx()

    monkeypatch.setattr("ultimate_discord_intelligence_bot.pipeline.track_request_budget", _fake_budget)

    class _FakeReport:
        found = False
        redacted_by_type = {}

    monkeypatch.setattr(
        "ultimate_discord_intelligence_bot.pipeline.privacy_filter",
        SimpleNamespace(filter_text=lambda text, ctx: (text, _FakeReport())),
    )

    memory_tool = _MemoryTool()
    pipeline = ContentPipeline(
        downloader=_DownloaderTool(),
        transcriber=_TranscriberTool(),
        analyzer=_AnalyzerTool(),
        drive=None,
        discord=_DiscordTool(),
        fallacy_detector=_FallacyTool(),
        perspective=_PerspectiveTool(),
        memory=memory_tool,
    )

    result = await pipeline.process_video("https://example.com/video")
    assert result["status"] == "success"
    assert budget_events == ["enter", "exit"]
    assert memory_tool.calls, "memory tool should be invoked during pipeline run"


@pytest.mark.asyncio
async def test_pipeline_sanitises_perspective_summary(monkeypatch):
    class _BudgetCtx:
        def __enter__(self):
            return SimpleNamespace()

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(
        "ultimate_discord_intelligence_bot.pipeline.track_request_budget",
        lambda *a, **k: _BudgetCtx(),
    )

    class _FakeReport:
        def __init__(self, replaced: bool):
            self.found = replaced
            self.redacted_by_type = {"pii": 1} if replaced else {}

    def _filter_text(text: str, ctx):
        replaced = "secret" in text
        return (text.replace("secret", "[REDACTED]"), _FakeReport(replaced))

    monkeypatch.setattr(
        "ultimate_discord_intelligence_bot.pipeline.privacy_filter",
        SimpleNamespace(filter_text=_filter_text),
    )

    memory_tool = _MemoryTool()
    discord_tool = _DiscordTool()
    pipeline = ContentPipeline(
        downloader=_DownloaderTool(),
        transcriber=_TranscriberTool(),
        analyzer=_AnalyzerTool(),
        drive=None,
        discord=discord_tool,
        fallacy_detector=_FallacyTool(),
        perspective=_PerspectiveTool(summary="secret summary"),
        memory=memory_tool,
    )

    result = await pipeline.process_video("https://example.com/video")
    assert result["status"] == "success"

    stored_text, _, _ = memory_tool.calls[0]
    assert "secret" not in stored_text
    assert "[REDACTED]" in stored_text

    payload, _ = discord_tool.calls[0]
    assert payload["summary"] == stored_text
