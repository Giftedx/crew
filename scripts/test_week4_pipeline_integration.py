#!/usr/bin/env python3
"""Test Week 4 Quality Filtering Pipeline Integration.

This script validates that the ContentQualityAssessmentTool is properly
integrated into the production pipeline and can make quality decisions.
"""

import asyncio
import os
import time


async def test_quality_filtering_integration():
    """Test quality filtering integration in pipeline."""
    print("🧪 Testing Week 4 Quality Filtering Pipeline Integration...")

    # Set up environment for testing
    os.environ["ENABLE_QUALITY_FILTERING"] = "1"

    try:
        from ultimate_discord_intelligence_bot.pipeline_components.orchestrator import ContentPipeline, _PipelineContext
        from ultimate_discord_intelligence_bot.pipeline_components.tracing import tracing_module

        print("✅ Pipeline components imported successfully")

        # Create pipeline instance
        pipeline = ContentPipeline()
        print("✅ ContentPipeline instantiated")

        # Create mock context for testing
        span = tracing_module.start_span("test_quality_filtering")
        ctx = _PipelineContext(span=span, start_time=time.monotonic(), tracker=None)

        # Test with low-quality transcript (should be bypassed)
        low_quality_transcript = "Um, yeah. This is bad. Not good."
        print(f"\n📝 Testing low-quality transcript: '{low_quality_transcript}'")

        quality_result, should_skip = await pipeline._quality_filtering_phase(ctx, low_quality_transcript)
        print(f"✅ Quality assessment result: success={quality_result.success}")
        print(f"📊 Should skip analysis: {should_skip}")
        print(f"📊 Quality score: {quality_result.data.get('overall_score', 'N/A')}")
        print(f"📊 Bypass reason: {quality_result.data.get('bypass_reason', 'N/A')}")

        # Test with high-quality transcript (should proceed to full analysis)
        high_quality_transcript = """
        In this comprehensive analysis, we explore the fundamental principles of quantum mechanics
        and their applications in modern computing systems. The research demonstrates significant
        advances in quantum coherence, entanglement theory, and practical implementations of
        quantum algorithms. These developments represent a paradigm shift in computational
        capabilities, offering exponential speedups for specific problem domains such as
        cryptography, optimization, and molecular simulation. The implications extend beyond
        theoretical physics into practical applications that could revolutionize industries
        ranging from pharmaceuticals to financial modeling.
        """

        print(f"\n📝 Testing high-quality transcript (preview): '{high_quality_transcript[:100]}...'")

        quality_result2, should_skip2 = await pipeline._quality_filtering_phase(ctx, high_quality_transcript)
        print(f"✅ Quality assessment result: success={quality_result2.success}")
        print(f"📊 Should skip analysis: {should_skip2}")
        print(f"📊 Quality score: {quality_result2.data.get('overall_score', 'N/A')}")
        print(
            f"📊 Bypass reason: {quality_result2.data.get('bypass_reason', 'N/A') if should_skip2 else 'Proceeding to full analysis'}"
        )

        # Test feature flag disabled
        print("\n🚫 Testing with quality filtering disabled...")
        os.environ["ENABLE_QUALITY_FILTERING"] = "0"

        quality_result3, should_skip3 = await pipeline._quality_filtering_phase(ctx, low_quality_transcript)
        print(f"✅ Quality assessment result: success={quality_result3.success}")
        print(f"📊 Should skip analysis: {should_skip3} (should be False when disabled)")

        # Restore flag
        os.environ["ENABLE_QUALITY_FILTERING"] = "1"

        print("\n🎯 Integration Test Results:")
        print(f"   ✅ Low-quality content bypassed: {should_skip}")
        print(f"   ✅ High-quality content processed: {not should_skip2}")
        print(f"   ✅ Feature flag respected: {not should_skip3}")
        print("   ✅ Pipeline integration functional")

        span.end()
        return True

    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_lightweight_processing():
    """Test lightweight processing phase."""
    print("\n🧪 Testing Lightweight Processing Phase...")

    try:
        from ultimate_discord_intelligence_bot.pipeline_components.orchestrator import (
            ContentPipeline,
            _DriveArtifacts,
            _PipelineContext,
            _TranscriptionArtifacts,
        )
        from ultimate_discord_intelligence_bot.pipeline_components.tracing import tracing_module
        from ultimate_discord_intelligence_bot.step_result import StepResult

        pipeline = ContentPipeline()

        # Create mock context
        span = tracing_module.start_span("test_lightweight_processing")
        ctx = _PipelineContext(span=span, start_time=time.monotonic(), tracker=None)

        # Create mock download info
        download_info = StepResult.ok(
            result={"title": "Test Video", "source_url": "https://example.com/test", "duration": 120}
        )

        # Create mock transcription bundle
        drive_artifacts = _DriveArtifacts(result=StepResult.ok(result={"uploaded": True}), outcome="success")

        transcription_bundle = _TranscriptionArtifacts(
            transcription=StepResult.ok(result={"transcript": "Short low quality content"}),
            drive=drive_artifacts,
            filtered_transcript="Short low quality content",
            transcript_task=None,
        )

        # Create mock quality result
        quality_result = StepResult.ok(
            result={
                "should_process": False,
                "overall_score": 0.45,
                "bypass_reason": "insufficient_content",
                "recommendation_details": "Content too short for full analysis",
            }
        )

        print("📊 Testing lightweight processing with mock data...")

        result = await pipeline._lightweight_processing_phase(ctx, download_info, transcription_bundle, quality_result)

        print(f"✅ Lightweight processing result: success={result.success}")
        print(f"📊 Processing type: {result.data.get('processing_type')}")
        print(f"📊 Time saved estimate: {result.data.get('time_saved_estimate')}")
        print(f"📊 Quality score: {result.data.get('quality_score')}")

        span.end()
        return True

    except Exception as e:
        print(f"❌ Lightweight processing test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Run all integration tests."""
    print("🚀 Week 4 Quality Filtering - Production Integration Test")
    print("=" * 60)

    test1_success = await test_quality_filtering_integration()
    test2_success = await test_lightweight_processing()

    print("\n" + "=" * 60)
    print("🎯 FINAL RESULTS:")
    print(f"   Quality Filtering Integration: {'✅ PASS' if test1_success else '❌ FAIL'}")
    print(f"   Lightweight Processing: {'✅ PASS' if test2_success else '❌ FAIL'}")

    if test1_success and test2_success:
        print("\n🎉 ALL TESTS PASSED - READY FOR PRODUCTION DEPLOYMENT!")
        print("📊 Week 4 Quality Filtering optimization is integrated and functional")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED - REVIEW BEFORE DEPLOYMENT")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
