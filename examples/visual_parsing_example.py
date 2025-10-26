#!/usr/bin/env python3
"""Example usage of the Visual Parsing service.

This script demonstrates how to use the VisualParsingService for analyzing
visual content in videos, including OCR and scene segmentation.

Usage:
    python examples/visual_parsing_example.py video_file.mp4

Environment Variables:
    None required - uses fallback methods when dependencies unavailable
"""

from __future__ import annotations

import sys
from pathlib import Path


# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from analysis.vision.visual_parsing_service import get_visual_parsing_service


def main() -> int:
    """Main example function."""
    if len(sys.argv) != 2:
        print("Usage: python examples/visual_parsing_example.py <video_file>")
        return 1

    video_path = Path(sys.argv[1])
    if not video_path.exists():
        print(f"Error: Video file not found: {video_path}")
        return 1

    print(f"🎬 Analyzing visual content in: {video_path}")

    # Get visual parsing service
    visual_service = get_visual_parsing_service()

    # Analyze video for visual content
    result = visual_service.analyze_video(
        video_path=video_path,
        model="balanced",  # Use balanced for good quality/speed balance
        extract_keyframes=True,
        perform_ocr=True,
        use_cache=True,
    )

    if not result.success:
        print(f"❌ Visual analysis failed: {result.error}")
        return 1

    data = result.data

    print("✅ Visual analysis completed!")
    print(f"   Model: {data['model']}")
    print(f"   Total frames: {data['total_frames']}")
    print(f"   Duration: {data['duration_seconds']:.2f}s")
    print(f"   Confidence: {data.get('confidence', 0):.2f}")
    print(f"   Cache hit: {data['cache_hit']}")
    print(f"   Processing time: {data['processing_time_ms']:.0f}ms")
    print()

    # Show scene segments
    scene_segments = data.get("scene_segments", [])
    if scene_segments:
        print(f"🎭 Scene Segments ({len(scene_segments)}):")
        print("-" * 80)

        for i, segment in enumerate(scene_segments[:5]):  # Show first 5 segments
            start_time = segment["start_frame"] / 30  # Assume 30fps
            end_time = segment["end_frame"] / 30
            duration = end_time - start_time

            print(
                f"   {i + 1}. [{start_time:6.1f}s - {end_time:6.1f}s] "
                f"({duration:5.1f}s) {segment['scene_type']} "
                f"(conf: {segment.get('confidence', 1):.2f})"
            )

            # Show keyframes if available
            if segment.get("keyframes"):
                print(f"      Keyframes: {len(segment['keyframes'])} extracted")

            # Show text overlays if available
            if segment.get("text_overlays"):
                print(f"      Text overlays: {len(segment['text_overlays'])} detected")

        if len(scene_segments) > 5:
            print(f"   ... and {len(scene_segments) - 5} more segments")

    print("-" * 80)

    # Show keyframes
    keyframes = data.get("keyframes", [])
    if keyframes:
        print(f"\n📸 Keyframes ({len(keyframes)} extracted):")
        for i, keyframe in enumerate(keyframes[:3]):  # Show first 3
            print(f"   {i + 1}. {Path(keyframe).name}")
        if len(keyframes) > 3:
            print(f"   ... and {len(keyframes) - 3} more keyframes")

    # Show OCR results
    ocr_results = data.get("ocr_results", [])
    if ocr_results:
        print(f"\n🔤 OCR Results ({len(ocr_results)} text detections):")
        for i, ocr in enumerate(ocr_results[:3]):  # Show first 3
            print(f'   {i + 1}. "{ocr["text"]}" (conf: {ocr["confidence"]:.2f}) at {ocr["bounding_box"]}')
        if len(ocr_results) > 3:
            print(f"   ... and {len(ocr_results) - 3} more text detections")

    return 0


if __name__ == "__main__":
    sys.exit(main())
