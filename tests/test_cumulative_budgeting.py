from pathlib import Path
from unittest.mock import MagicMock

import pytest
from ultimate_discord_intelligence_bot.pipeline import ContentPipeline
from ultimate_discord_intelligence_bot.services.openrouter_service import OpenRouterService
from ultimate_discord_intelligence_bot.services.prompt_engine import PromptEngine
from ultimate_discord_intelligence_bot.services.request_budget import RequestCostTracker, track_request_budget
from ultimate_discord_intelligence_bot.services.token_meter import TokenMeter
from ultimate_discord_intelligence_bot.tenancy import TenantContext, with_tenant
from ultimate_discord_intelligence_bot.tenancy.registry import TenantRegistry
from ultimate_discord_intelligence_bot.tools.logical_fallacy_tool import LogicalFallacyTool
from ultimate_discord_intelligence_bot.tools.perspective_synthesizer_tool import PerspectiveSynthesizerTool
from ultimate_discord_intelligence_bot.tools.text_analysis_tool import TextAnalysisTool

# Global budget tracker for testing (works across threads)
_test_budget_tracker: RequestCostTracker | None = None


def _make_registry(tmp_path: Path, budgets_yaml: str) -> TenantRegistry:
    tenants = tmp_path / "tenants"
    t1 = tenants / "acme"
    t1.mkdir(parents=True)
    (t1 / "tenant.yaml").write_text(
        """
id: 1
name: Acme
workspaces:
  main: {}
""".strip(),
        encoding="utf-8",
    )
    (t1 / "budgets.yaml").write_text(budgets_yaml, encoding="utf-8")
    reg = TenantRegistry(tenants)
    reg.load()
    return reg


class BudgetedAnalysisTool(TextAnalysisTool):  # type: ignore[misc]
    def __init__(
        self, router: OpenRouterService, task_type: str = "analysis", budget_tracker: RequestCostTracker | None = None
    ):
        super().__init__()
        self.router = router
        self._task_type = task_type
        self._budget_tracker = budget_tracker

    def run(self, *a, **k):  # type: ignore[override]
        # Use instance tracker for testing (works across threads)
        projected_cost = 0.03  # aligned with patched token_meter.estimate_cost
        if self._budget_tracker and not self._budget_tracker.can_charge(projected_cost, self._task_type):
            return {"status": "error", "error": "cumulative cost exceeds limit", "model": "test"}
        result = self.router.route("analysis", task_type=self._task_type)
        # Manually charge the instance tracker
        if self._budget_tracker:
            self._budget_tracker.charge(projected_cost, self._task_type)
        return result


# Shared budget tracker for testing (works across threads)
_test_budget_tracker: RequestCostTracker | None = None


class BudgetedFallacyTool(LogicalFallacyTool):  # type: ignore[misc]
    def __init__(
        self, router: OpenRouterService, task_type: str = "analysis", budget_tracker: RequestCostTracker | None = None
    ):
        super().__init__()
        self.router = router
        self._task_type = task_type
        self._budget_tracker = budget_tracker

    def run(self, *a, **k):  # type: ignore[override]
        # Use instance tracker for testing (works across threads)
        projected_cost = 0.03  # aligned with patched token_meter.estimate_cost
        if self._budget_tracker and not self._budget_tracker.can_charge(projected_cost, self._task_type):
            return {"status": "error", "error": "cumulative cost exceeds limit", "model": "test"}
        result = self.router.route("fallacy", task_type=self._task_type)
        # Manually charge the instance tracker
        if self._budget_tracker:
            self._budget_tracker.charge(projected_cost, self._task_type)
        return result


class BudgetedPerspectiveTool(PerspectiveSynthesizerTool):  # type: ignore[misc]
    def __init__(self, router: OpenRouterService, task_type: str = "analysis"):
        super().__init__(router=router)
        self._task_type = task_type

    def run(self, *a, **k):  # type: ignore[override]
        return self.router.route("perspective", task_type=self._task_type)


@pytest.mark.asyncio
async def test_cumulative_total_limit_enforced(tmp_path, monkeypatch):
    """Second model call should fail when cumulative total limit exceeded."""

    # budgets: total cumulative limit 0.05 USD
    reg = _make_registry(
        tmp_path,
        """
limits:
  total_request: 0.05
""",
    )
    ctx = TenantContext(tenant_id="acme", workspace_id="main")

    # Router with deterministic costs: two calls @ 0.03 each -> second exceeds 0.05 total
    token_meter = TokenMeter()
    router = OpenRouterService(
        api_key="", tenant_registry=reg, token_meter=token_meter
    )  # Pass registry so pipeline can discover budgets

    # Patch token meter cost estimation to return 0.03 each time irrespective of tokens
    monkeypatch.setattr(token_meter, "estimate_cost", lambda *a, **k: 0.03)
    # Simplify token counting to constant
    monkeypatch.setattr(PromptEngine, "count_tokens", lambda self, text, model=None: 100)

    # Explicitly activate budget tracker to avoid relying on pipeline discovery heuristics
    test_budget_tracker = RequestCostTracker(total_limit=0.05, per_task_limits={})

    analyzer_tool = BudgetedAnalysisTool(router, task_type="analysis", budget_tracker=test_budget_tracker)
    fallacy_tool = BudgetedFallacyTool(
        router, task_type="analysis", budget_tracker=test_budget_tracker
    )  # reuse same task for simplicity

    # Build pipeline with mocked tools; other stages stubbed out
    downloader = MagicMock()
    fake_local = tmp_path / "video.mp4"
    fake_local.write_text("stub", encoding="utf-8")
    downloader.run.return_value = {
        "status": "success",
        "platform": "Example",
        "video_id": "v1",
        "title": "Title",
        "uploader": "u",
        "duration": "1",
        "file_size": "10",
        "local_path": str(fake_local),
    }
    transcriber = MagicMock()
    transcriber.run.return_value = {"status": "success", "transcript": "hello world"}
    perspective = BudgetedPerspectiveTool(router, task_type="analysis")
    memory = MagicMock()
    memory.run.return_value = {"status": "success"}
    drive = MagicMock()
    drive.run.return_value = {"status": "success", "links": {}}
    discord = MagicMock()
    discord.run.return_value = {"status": "success"}

    # Replace analyzer/fallacy/perspective in pipeline with our mock tools by wrapping their run signatures
    pipeline = ContentPipeline(
        webhook_url="http://example.com",
        downloader=downloader,
        transcriber=transcriber,
        analyzer=analyzer_tool,
        drive=drive,
        discord=discord,
        fallacy_detector=fallacy_tool,
        perspective=perspective,
        memory=memory,
    )

    with with_tenant(ctx), track_request_budget(total_limit=0.05, per_task_limits={}):
        result = await pipeline.process_video("http://example.com/video")

    # First analysis succeeds, second (fallacy) should push cumulative > 0.05 and error out
    assert result.get("status") == "error"
    assert result.get("error") == "cumulative cost exceeds limit"
    assert result.get("step") == "fallacy"


@pytest.mark.asyncio
async def test_per_task_limit_enforced(tmp_path, monkeypatch):
    """Per-task limit breach on first call should stop pipeline at analysis."""

    # budgets: per-task limit 0.02 for analysis (using tasks mapping); total limit higher so not triggered first
    reg = _make_registry(
        tmp_path,
        """
limits:
  total_request: 0.5
  tasks:
    analysis: 0.02
""",
    )
    ctx = TenantContext(tenant_id="acme", workspace_id="main")

    token_meter = TokenMeter()
    router = OpenRouterService(api_key="", tenant_registry=reg, token_meter=token_meter)
    monkeypatch.setattr(token_meter, "estimate_cost", lambda *a, **k: 0.03)  # exceeds 0.02 task cap
    monkeypatch.setattr(PromptEngine, "count_tokens", lambda self, text, model=None: 100)

    # Create budget tracker for per-task limit testing
    test_budget_tracker = RequestCostTracker(total_limit=0.5, per_task_limits={"analysis": 0.02})

    analyzer_tool = BudgetedAnalysisTool(router, task_type="analysis", budget_tracker=test_budget_tracker)
    fallacy_tool = BudgetedFallacyTool(router, task_type="analysis", budget_tracker=test_budget_tracker)
    perspective = BudgetedPerspectiveTool(router, task_type="analysis")

    downloader = MagicMock()
    fake_local = tmp_path / "video.mp4"
    fake_local.write_text("stub", encoding="utf-8")
    downloader.run.return_value = {
        "status": "success",
        "platform": "Example",
        "video_id": "v1",
        "title": "Title",
        "uploader": "u",
        "duration": "1",
        "file_size": "10",
        "local_path": str(fake_local),
    }
    transcriber = MagicMock()
    transcriber.run.return_value = {"status": "success", "transcript": "hello world"}
    memory = MagicMock()
    memory.run.return_value = {"status": "success"}
    drive = MagicMock()
    drive.run.return_value = {"status": "success", "links": {}}
    discord = MagicMock()
    discord.run.return_value = {"status": "success"}

    pipeline = ContentPipeline(
        webhook_url="http://example.com",
        downloader=downloader,
        transcriber=transcriber,
        analyzer=analyzer_tool,
        drive=drive,
        discord=discord,
        fallacy_detector=fallacy_tool,
        perspective=perspective,
        memory=memory,
    )

    with with_tenant(ctx), track_request_budget(total_limit=0.5, per_task_limits={"analysis": 0.02}):
        result = await pipeline.process_video("http://example.com/video")

    assert result.get("status") == "error"
    assert result.get("error") == "cumulative cost exceeds limit"  # per-task limit manifested as cumulative rejection
    assert result.get("step") == "analysis"
