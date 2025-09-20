import asyncio
from unittest.mock import MagicMock

from ultimate_discord_intelligence_bot.pipeline import ContentPipeline


class MockPipeline(ContentPipeline):
    """Subclass to avoid real MemoryStorageTool dependency during tests."""

    def __init__(self, *args, **kwargs):  # noqa: D401 - thin wrapper
        # Force memory kw to be a dummy before base init attempts to create one
        kwargs.setdefault("memory", DummyMemory())  # type: ignore[arg-type]
        super().__init__(*args, **kwargs)


class DummyMemory:
    def run(self, *args, **kwargs):  # mimic tool interface returning success
        return {"status": "success"}


def test_pipeline_rate_limit(monkeypatch):
    """Test pipeline respects HTTP rate limiting."""
    pipeline = MockPipeline()

    # Mock URL validation to always succeed
    monkeypatch.setattr("core.http_utils.validate_public_https_url", lambda x: x)

    # Mock the rate limit check to return False to trigger rate limit exceeded
    monkeypatch.setattr(pipeline, "_check_rate_limit", lambda op_type: False)

    result = asyncio.run(pipeline.process_video("http://example.com/video"))
    assert result.get("status") == "error"
    assert result.get("step") == "rate_limit"
    assert result.get("rate_limit_exceeded") is True
    assert result.get("status_code") == 429


def test_tool_rate_limit_download(monkeypatch):
    # Downloader will be first tool step; simulate passing pipeline limit but failing tool limit
    downloader = MagicMock()
    pipeline = MockPipeline(downloader=downloader)

    calls = {"tool": 0}

    def fake_check(op_type: str):
        if op_type == "pipeline":
            return True
        if op_type == "tool":
            # First tool invocation returns False to trigger rate limit, subsequent not reached
            calls["tool"] += 1
            return False
        return True

    monkeypatch.setattr(pipeline, "_check_rate_limit", fake_check)

    result = asyncio.run(pipeline.process_video("http://example.com/video"))
    # Should fail at download step with rate limit error propagated
    assert result.get("status") == "error"
    assert result.get("step") == "download"
    # error message contains rate limit wording from StepResult.fail
    assert "rate limit" in result.get("error", "").lower() or result.get("rate_limit_exceeded")
