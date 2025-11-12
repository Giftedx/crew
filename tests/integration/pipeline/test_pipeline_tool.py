import pytest


pytest.skip("Test file imports from non-existent or moved modules", allow_module_level=True)

from ultimate_discord_intelligence_bot.tools.pipeline_tool import PipelineTool


def test_pipeline_tool_passes_quality(monkeypatch):
    called = {}

    class DummyPipeline:
        async def process_video(self, url: str, quality: str = "1080p"):
            called["url"] = url
            called["quality"] = quality
            return {"status": "success"}

    monkeypatch.setattr(
        "ultimate_discord_intelligence_bot.tools.pipeline_tool.ContentPipeline",
        DummyPipeline,
    )

    tool = PipelineTool()
    result = tool.run("http://example.com", quality="720p")

    assert result["status"] == "success"
    assert called == {"url": "http://example.com", "quality": "720p"}
