import pytest

from ultimate_discord_intelligence_bot.pipeline_components.orchestrator import ContentPipeline
from ultimate_discord_intelligence_bot.step_result import StepResult
from ultimate_discord_intelligence_bot.tenancy import TenantContext, with_tenant
from ultimate_discord_intelligence_bot.tools import ContentQualityAssessmentTool


class _DummyStepTool:
    def __init__(self, payload):
        self._payload = payload

    async def run(self, *args, **kwargs):
        return StepResult.ok(**self._payload)


@pytest.fixture(autouse=True)
def enable_quality(monkeypatch):
    monkeypatch.setenv("ENABLE_QUALITY_FILTERING", "1")
    ContentQualityAssessmentTool.MIN_WORD_COUNT = 300
    ContentQualityAssessmentTool.MIN_SENTENCE_COUNT = 12
    ContentQualityAssessmentTool.MIN_COHERENCE_SCORE = 0.9
    ContentQualityAssessmentTool.MIN_OVERALL_SCORE = 0.9
    yield


@pytest.mark.asyncio
async def test_lightweight_processing_bypass(monkeypatch):
    transcript_text = "Uh okay yeah short fragment."
    downloader = _DummyStepTool(
        {
            "status": "success",
            "local_path": "/tmp/video.mp4",
            "video_id": "vid123",
            "title": "Low Quality Clip",
            "platform": "youtube",
            "source_url": "https://example.com/video",
            "duration": 42,
        }
    )
    transcriber = _DummyStepTool({"status": "success", "transcript": transcript_text})
    analyzer = _DummyStepTool({"status": "success", "sentiment": "neutral", "keywords": [], "summary": "N/A"})
    drive = _DummyStepTool({"status": "success", "drive_url": "https://drive/abc", "shared": True})
    discord = _DummyStepTool({"status": "success", "message_id": "m1"})
    fallacy = _DummyStepTool({"status": "success", "fallacies": []})
    perspective = _DummyStepTool({"status": "success", "summary": "Placeholder perspective"})
    memory = _DummyStepTool({"status": "success", "stored": True})
    pipeline = ContentPipeline(
        webhook_url="https://discord/webhook",
        downloader=downloader,
        transcriber=transcriber,
        analyzer=analyzer,
        drive=drive,
        discord=discord,
        fallacy_detector=fallacy,
        perspective=perspective,
        memory=memory,
    )
    with with_tenant(TenantContext("tenant_test", "workspace_test")):
        result = await pipeline.process_video("https://example.com/video")
    assert result["status"] == "success"
    assert result["processing_type"] == "lightweight"
    assert result.get("bypass_reason")
    assert "quality_metrics" in result, "quality_metrics missing from lightweight path result"
    qm = result["quality_metrics"]
    assert isinstance(qm, dict), f"quality_metrics should be a dict, got {type(qm)}"
    expected_keys = {
        "word_count",
        "sentence_count",
        "avg_sentence_length",
        "coherence_score",
        "topic_clarity_score",
        "language_quality_score",
        "overall_quality_score",
    }
    assert expected_keys.issubset(qm.keys()), f"Missing keys in quality_metrics: {expected_keys - set(qm.keys())}"
    assert "summary" in result
    assert "quality_score" in result
    assert "analysis" not in result
    assert "perspective" not in result
    assert "fallacy" not in result
