import asyncio
import logging
import types
from platform.core.step_result import StepResult

from ultimate_discord_intelligence_bot.autonomous_orchestrator import AutonomousIntelligenceOrchestrator


def test_content_acquisition_flattens_pipeline_payload():
    orchestrator = object.__new__(AutonomousIntelligenceOrchestrator)
    orchestrator.logger = logging.getLogger("autointel-test")
    pipeline_payload = {
        "status": "success",
        "download": {"status": "success", "title": "Sample Video", "platform": "youtube"},
        "transcription": {"status": "success", "transcript": "hello world"},
        "analysis": {"status": "success", "summary": "Example analysis"},
        "fallacy": {"status": "success", "fallacies": []},
        "perspective": {"status": "success", "summary": "Multi-angle"},
        "memory": {"status": "success", "stored": True},
        "graph_memory": {"status": "skipped"},
        "hipporag_memory": {"status": "skipped"},
        "discord": {"status": "success", "message_id": "msg_123"},
    }
    pipeline_wrapper = {
        "url": "https://example.com/video",
        "quality": "1080p",
        "processing_time": 1.23,
        "timestamp": 1700000000.0,
        "data": pipeline_payload,
    }
    pipeline_result = StepResult.ok(**pipeline_wrapper)

    async def fake_pipeline(self, url: str):
        assert url == pipeline_wrapper["url"]
        return pipeline_result

    orchestrator._execute_content_pipeline = types.MethodType(fake_pipeline, orchestrator)
    result = asyncio.run(orchestrator._execute_specialized_content_acquisition(pipeline_wrapper["url"]))
    assert result.success is True
    assert result.data["transcription"]["transcript"] == "hello world"
    assert result.data["download"]["title"] == "Sample Video"
    assert "pipeline_metadata" in result.data
    metadata = result.data["pipeline_metadata"]
    assert metadata["source_url"] == pipeline_wrapper["url"]
    assert metadata["workflow_type"] == "autonomous_intelligence"
    assert "acquisition_timestamp" in metadata
    assert result.data["workflow_type"] == "autonomous_intelligence"
    assert result.data["source_url"] == pipeline_wrapper["url"]
    assert "acquisition_timestamp" in result.data
    assert "raw_pipeline_payload" in result.data
    normalized = orchestrator._normalize_acquisition_data(result)
    assert normalized["transcription"]["transcript"] == "hello world"
    assert normalized["download"]["title"] == "Sample Video"
