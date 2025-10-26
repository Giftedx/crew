#!/usr/bin/env python3
"""Example usage of the Multimodal Analysis Pipeline.

This script demonstrates how to use the MultimodalAnalysisPipeline for comprehensive
content analysis, orchestrating all analysis services together.

Usage:
    python examples/multimodal_pipeline_example.py

Environment Variables:
    None required - uses fallback methods when dependencies unavailable
"""

from __future__ import annotations

import sys
from pathlib import Path


# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pipeline.multimodal_analysis_pipeline import (
    PipelineConfig,
    get_multimodal_analysis_pipeline,
)


def main() -> int:
    """Main example function."""
    print("🚀 Multimodal Analysis Pipeline Demo")
    print("=" * 60)

    # Get pipeline instance
    pipeline = get_multimodal_analysis_pipeline()

    # Check pipeline status
    print("🔍 Checking Pipeline Status...")
    status_result = pipeline.get_pipeline_status()

    if status_result.success:
        status = status_result.data
        print(f"   Services initialized: {status['services_initialized']}")
        print(f"   Available services: {len(status['available_services'])}")
        print(
            f"   Service health: {sum(1 for h in status['service_health'].values() if h == 'available')} / {len(status['service_health'])}"
        )

        for service, health in status["service_health"].items():
            print(f"     {service}: {health}")
    else:
        print(f"❌ Pipeline status check failed: {status_result.error}")
        return 1

    print()

    # Example 1: Fast analysis (minimal services)
    print("⚡ Fast Analysis (Minimal Services)...")
    fast_config = PipelineConfig(
        model_quality="fast",
        max_processing_time=30,
        enable_asr=True,
        enable_speaker_diarization=False,
        enable_visual_parsing=False,
        enable_topic_segmentation=True,
        enable_claim_extraction=False,
        enable_highlight_detection=True,
        enable_sentiment_analysis=True,
        enable_safety_analysis=False,
        enable_deduplication=False,
        enable_publishing=False,
    )

    fast_result = pipeline.analyze_content(
        content_url="https://example.com/fast_video.mp4",
        platform="youtube",
        config=fast_config,
    )

    if fast_result.success:
        data = fast_result.data
        print("✅ Fast analysis completed!")
        print(f"   Processing time: {data['total_processing_time']:.1f}s")
        print(f"   Analysis results: {len(data['analysis_results'])} services")
        print(f"   Errors: {len(data['errors'])}")
        print(f"   Warnings: {len(data['warnings'])}")

        for service, result in data["analysis_results"].items():
            print(f"     ✅ {service}")
    else:
        print(f"❌ Fast analysis failed: {fast_result.error}")

    print()

    # Example 2: Balanced analysis (most services)
    print("⚖️  Balanced Analysis (Most Services)...")
    balanced_config = PipelineConfig(
        model_quality="balanced",
        max_processing_time=120,
        enable_asr=True,
        enable_speaker_diarization=True,
        enable_visual_parsing=True,
        enable_topic_segmentation=True,
        enable_claim_extraction=True,
        enable_highlight_detection=True,
        enable_sentiment_analysis=True,
        enable_safety_analysis=True,
        enable_deduplication=True,
        enable_publishing=False,  # Disable for demo
    )

    balanced_result = pipeline.analyze_content(
        content_url="https://example.com/balanced_video.mp4",
        platform="youtube",
        config=balanced_config,
    )

    if balanced_result.success:
        data = balanced_result.data
        print("✅ Balanced analysis completed!")
        print(f"   Processing time: {data['total_processing_time']:.1f}s")
        print(f"   Analysis results: {len(data['analysis_results'])} services")
        print(f"   Published reports: {len(data['published_reports'])}")

        # Show analysis breakdown
        for service, result in data["analysis_results"].items():
            if isinstance(result, dict) and "success" in result:
                status = "✅" if result["success"] else "❌"
                print(f"     {status} {service}")

        # Show any errors or warnings
        if data["errors"]:
            print(f"   Errors: {len(data['errors'])}")
            for error in data["errors"][:2]:  # Show first 2 errors
                print(f"     - {error}")

        if data["warnings"]:
            print(f"   Warnings: {len(data['warnings'])}")
            for warning in data["warnings"][:2]:  # Show first 2 warnings
                print(f"     - {warning}")

    else:
        print(f"❌ Balanced analysis failed: {balanced_result.error}")

    print()

    # Example 3: Custom configuration
    print("🎛️  Custom Configuration Demo...")
    custom_config = PipelineConfig(
        model_quality="quality",
        max_processing_time=300,
        enable_asr=True,
        enable_speaker_diarization=True,
        enable_visual_parsing=True,
        enable_topic_segmentation=True,
        enable_claim_extraction=True,
        enable_highlight_detection=True,
        enable_sentiment_analysis=True,
        enable_safety_analysis=True,
        enable_deduplication=True,
        enable_publishing=True,  # Enable publishing
        enable_caching=True,
        publish_reports=True,
    )

    print("   Configuration:")
    print(f"     Model quality: {custom_config.model_quality}")
    print(f"     Max processing time: {custom_config.max_processing_time}s")
    print(
        f"     Services enabled: {sum([custom_config.enable_asr, custom_config.enable_speaker_diarization, custom_config.enable_visual_parsing, custom_config.enable_topic_segmentation, custom_config.enable_claim_extraction, custom_config.enable_highlight_detection, custom_config.enable_sentiment_analysis, custom_config.enable_safety_analysis, custom_config.enable_deduplication, custom_config.enable_publishing])}"
    )
    print(f"     Caching: {'enabled' if custom_config.enable_caching else 'disabled'}")
    print(f"     Publishing: {'enabled' if custom_config.publish_reports else 'disabled'}")

    print()

    # Example 4: Pipeline capabilities summary
    print("📋 Pipeline Capabilities Summary:")
    print("   ✅ Content Ingestion (MCP tools)")
    print("   ✅ ASR Transcription (Whisper models)")
    print("   ✅ Speaker Diarization (pyannote.audio)")
    print("   ✅ Visual Parsing (OCR + scene analysis)")
    print("   ✅ Topic Segmentation (BERTopic)")
    print("   ✅ Claim & Quote Extraction (NLP patterns)")
    print("   ✅ Highlight Detection (multi-signal)")
    print("   ✅ Sentiment & Stance Analysis (transformers)")
    print("   ✅ Safety & Brand Suitability (policy compliance)")
    print("   ✅ Cross-Platform Deduplication (perceptual + semantic)")
    print("   ✅ Artifact Publishing (Discord integration)")
    print()

    print("🎯 Pipeline Architecture:")
    print("   ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐")
    print("   │   Ingestion     │ -> │   Analysis      │ -> │   Publishing    │")
    print("   │   (MCP tools)   │    │   (All services)│    │   (Discord)     │")
    print("   └─────────────────┘    └─────────────────┘    └─────────────────┘")
    print("          │                        │                        │")
    print("          ▼                        ▼                        ▼")
    print("   ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐")
    print("   │   Vector DB     │    │   Knowledge     │    │   Reports       │")
    print("   │   Storage       │    │   Graph         │    │   Generated     │")
    print("   └─────────────────┘    └─────────────────┘    └─────────────────┘")

    print()
    print("=" * 60)
    print("🎉 Multimodal Analysis Pipeline Demo Complete!")
    print()
    print("💡 Next Steps:")
    print("   1. Configure DISCORD_WEBHOOK_URL for report publishing")
    print("   2. Add real content URLs for analysis")
    print("   3. Customize PipelineConfig for your use case")
    print("   4. Integrate with MCP tools for content ingestion")

    return 0


if __name__ == "__main__":
    sys.exit(main())
