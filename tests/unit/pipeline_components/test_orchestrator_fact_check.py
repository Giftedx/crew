import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from ultimate_discord_intelligence_bot.pipeline_components.orchestrator import ContentPipeline, _TranscriptionArtifacts
from ultimate_discord_intelligence_bot.step_result import StepResult

@pytest.mark.asyncio
async def test_analysis_phase_fact_check_integration():
    # Setup
    # Patching init to avoid side effects
    with patch("ultimate_discord_intelligence_bot.pipeline_components.base.PipelineBase.__init__", return_value=None):
        pipeline = ContentPipeline()
        # Manually set attributes that __init__ would have set
        pipeline.logger = MagicMock()
        pipeline._step_middlewares = []
        pipeline._step_observability = {}
        # Mock bucket
        pipeline.tool_bucket = MagicMock()
        pipeline.tool_bucket.allow.return_value = True

    # Mock _execute_step to just call the function directly (simplifying test)
    async def mock_execute_step(name, func, *args, **kwargs):
        res = func(*args, **kwargs)
        if asyncio.iscoroutine(res):
            return await res
        return res
    pipeline._execute_step = mock_execute_step

    # Mock other methods
    pipeline._maybe_compress_transcript = MagicMock(return_value=("compressed", None))
    pipeline._apply_pii_filtering = MagicMock(return_value="summary")
    pipeline._schedule_transcript_storage = MagicMock(return_value=None)
    pipeline._record_step_skip = MagicMock()
    pipeline._schedule_discord_post = MagicMock(return_value=(None, StepResult.skip()))
    pipeline._langfuse_start_span = MagicMock()
    pipeline._langfuse_finish_span = MagicMock()

    # Mock tools
    pipeline.analyzer = MagicMock()
    pipeline.analyzer.run.return_value = StepResult.ok(sentiment="positive", keywords=["test"])

    pipeline.fallacy_detector = MagicMock()
    pipeline.fallacy_detector.run.return_value = StepResult.ok(fallacies=[])

    pipeline.perspective = MagicMock()
    pipeline.perspective.run.return_value = StepResult.ok(summary="Summary")

    pipeline.memory = MagicMock()
    pipeline.memory.run.return_value = StepResult.ok(status="stored")

    # Mock NEW tools
    pipeline.claim_extractor = MagicMock()
    pipeline.claim_extractor.run.return_value = StepResult.ok(claims=["Claim 1", "Claim 2"])

    pipeline.fact_checker = MagicMock()
    # Fact check runs per claim. We mock side_effect to return different results
    pipeline.fact_checker.run.side_effect = [
        StepResult.ok(verdict="True", evidence=["Source A"]),
        StepResult.ok(verdict="False", evidence=["Source B"])
    ]

    # Graph/Hippo Disabled
    pipeline.graph_memory = None
    pipeline.hipporag_memory = None

    # Mock context
    ctx = MagicMock()
    ctx.start_time = 0
    ctx.span = MagicMock()

    # Mock inputs
    download_info = StepResult.ok(video_id="123", title="Test Video", platform="youtube")
    transcription_bundle = _TranscriptionArtifacts(
        transcription=StepResult.ok(),
        drive=MagicMock(),
        filtered_transcript="This is a transcript with Claim 1 and Claim 2.",
        transcript_task=None
    )

    # Run
    analysis_bundle, failure = await pipeline._analysis_phase(ctx, download_info, transcription_bundle)

    # Verify
    assert failure is None, f"Pipeline failed with: {failure}"
    assert analysis_bundle is not None

    # Check claims
    assert analysis_bundle.claims.success
    assert analysis_bundle.claims.data["claims"] == ["Claim 1", "Claim 2"]

    # Check fact checks
    assert analysis_bundle.fact_checks.success
    fact_checks_data = analysis_bundle.fact_checks.data["fact_checks"]
    assert len(fact_checks_data) == 2
    assert fact_checks_data[0]["verdict"] == "True"
    assert fact_checks_data[1]["verdict"] == "False"

    # Verify calls
    pipeline.claim_extractor.run.assert_called()
    assert pipeline.fact_checker.run.call_count == 2
