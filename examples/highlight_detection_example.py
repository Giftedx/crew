#!/usr/bin/env python3
"""Example usage of the Highlight Detection service.

This script demonstrates how to use the HighlightDetectionService for identifying
engaging moments in video/audio content using multiple signals.

Usage:
    python examples/highlight_detection_example.py audio_file.wav

Environment Variables:
    None required - uses fallback methods when dependencies unavailable
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from analysis.highlight.highlight_detection_service import (
    get_highlight_detection_service,
)


def main() -> int:
    """Main example function."""
    if len(sys.argv) < 2:
        print("Usage: python examples/highlight_detection_example.py <audio_file>")
        print("Example: python examples/highlight_detection_example.py episode.wav")
        return 1

    audio_path = Path(sys.argv[1])
    if not audio_path.exists():
        print(f"Error: Audio file not found: {audio_path}")
        return 1

    print(f"🎯 Detecting highlights in: {audio_path}")

    # Get highlight detection service
    highlight_service = get_highlight_detection_service()

    # Detect highlights
    result = highlight_service.detect_highlights(
        audio_path=audio_path,
        model="balanced",  # Use balanced for good quality/speed balance
        min_highlight_duration=5.0,
        max_highlights=10,
        use_cache=True,
    )

    if not result.success:
        print(f"❌ Highlight detection failed: {result.error}")
        return 1

    data = result.data

    print("✅ Highlight detection completed!")
    print(f"   Total duration: {data['total_duration']:.2f}s")
    print(f"   Detection method: {data['detection_method']}")
    print(f"   Cache hit: {data['cache_hit']}")
    print(f"   Processing time: {data['processing_time_ms']:.0f}ms")
    print()

    # Show signal weights
    signal_weights = data.get("signal_weights", {})
    if signal_weights:
        print("⚖️  Signal Weights:")
        for signal, weight in signal_weights.items():
            print(f"   {signal}: {weight:.1%}")
        print()

    # Show detected highlights
    highlights = data.get("highlights", [])
    if highlights:
        print(f"🎬 Detected Highlights ({len(highlights)}):")
        print("-" * 100)

        for i, highlight in enumerate(highlights[:8]):  # Show first 8 highlights
            start_time = highlight["start_time"]
            end_time = highlight["end_time"]
            duration = highlight["duration"]
            score = highlight["highlight_score"]
            confidence = highlight["confidence"]

            print(
                f"   {i + 1}. [{start_time:6.1f}s - {end_time:6.1f}s] "
                f"({duration:5.1f}s) Score: {score:.2f} "
                f"(conf: {confidence:.2f})"
            )

            # Show signal contributions
            audio_score = highlight.get("audio_energy_score", 0)
            chat_score = highlight.get("chat_spike_score", 0)
            novelty_score = highlight.get("semantic_novelty_score", 0)

            print(
                f"         Audio: {audio_score:.2f} | Chat: {chat_score:.2f} | Novelty: {novelty_score:.2f}"
            )

            # Show transcript if available
            if highlight.get("transcript_text"):
                text_preview = highlight["transcript_text"][:60]
                if len(highlight["transcript_text"]) > 60:
                    text_preview += "..."
                print(f'         "{text_preview}"')

        if len(highlights) > 8:
            print(f"   ... and {len(highlights) - 8} more highlights")

    print("-" * 100)

    # Show highlight statistics
    if highlights:
        scores = [h["highlight_score"] for h in highlights]
        durations = [h["duration"] for h in highlights]

        print("📊 Highlight Statistics:")
        print(f"   Total highlights: {len(highlights)}")
        print(f"   Average score: {sum(scores) / len(scores):.2f}")
        print(f"   Average duration: {sum(durations) / len(durations):.1f}s")
        print(
            f"   High-confidence highlights: {sum(1 for h in highlights if h['confidence'] > 0.8)}"
        )

        # Show score distribution
        high_scores = sum(1 for s in scores if s > 0.8)
        med_scores = sum(1 for s in scores if 0.6 <= s <= 0.8)
        low_scores = sum(1 for s in scores if s < 0.6)

        print("   Score distribution:")
        print(f"     High (0.8+): {high_scores}")
        print(f"     Medium (0.6-0.8): {med_scores}")
        print(f"     Low (<0.6): {low_scores}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
