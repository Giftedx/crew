#!/usr/bin/env python3
"""Example usage of the Speaker Diarization service.

This script demonstrates how to use the SpeakerDiarizationService for identifying
speakers in audio content, which is essential for creator intelligence analysis.

Usage:
    python examples/speaker_diarization_example.py audio_file.mp3

Environment Variables:
    None required - uses fallback diarization when pyannote.audio unavailable
"""

from __future__ import annotations

import sys
from pathlib import Path


# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from analysis.transcription.speaker_diarization_service import get_diarization_service


def main() -> int:
    """Main example function."""
    if len(sys.argv) != 2:
        print("Usage: python examples/speaker_diarization_example.py <audio_file>")
        return 1

    audio_path = Path(sys.argv[1])
    if not audio_path.exists():
        print(f"Error: Audio file not found: {audio_path}")
        return 1

    print(f"🎤 Analyzing speakers in: {audio_path}")

    # Get diarization service
    diarization_service = get_diarization_service()

    # Diarize audio
    result = diarization_service.diarize_audio(
        audio_path=audio_path,
        model="balanced",  # Use balanced for good quality/speed balance
        use_cache=True,
    )

    if not result.success:
        print(f"❌ Diarization failed: {result.error}")
        return 1

    data = result.data

    print("✅ Speaker diarization completed!")
    print(f"   Model: {data['model']}")
    print(f"   Duration: {data['duration']:.2f}s")
    print(f"   Confidence: {data.get('confidence', 0):.2f}")
    print(f"   Cache hit: {data['cache_hit']}")
    print(f"   Processing time: {data['processing_time_ms']:.0f}ms")
    print()

    # Show speaker information
    print("👥 Speaker Analysis:")
    print(f"   Number of speakers: {data['num_speakers']}")
    print(f"   Speaker map: {data['speaker_map']}")
    print()

    # Show segments
    segments = data.get("segments", [])
    if segments:
        print(f"🎬 Speaker Segments ({len(segments)}):")
        print("-" * 80)

        for i, segment in enumerate(segments[:10]):  # Show first 10 segments
            duration = segment["end"] - segment["start"]
            speaker_info = (
                f"{segment['speaker_name']} ({segment['speaker_role']})"
                if segment.get("speaker_name")
                else segment["speaker_id"]
            )

            print(
                f"   {i + 1:2d}. [{segment['start']:6.1f}s - {segment['end']:6.1f}s] "
                f"({duration:5.1f}s) {speaker_info} "
                f"(conf: {segment.get('confidence', 1):.2f})"
            )

            if segment.get("transcript_text"):
                # Show first 60 chars of transcript
                transcript_preview = segment["transcript_text"][:60]
                if len(segment["transcript_text"]) > 60:
                    transcript_preview += "..."
                print(f'         "{transcript_preview}"')

        if len(segments) > 10:
            print(f"   ... and {len(segments) - 10} more segments")

    print("-" * 80)

    # Show speaking time breakdown
    print("\n⏱️  Speaking Time Breakdown:")
    speaker_times = {}
    for segment in segments:
        speaker_id = segment["speaker_id"]
        duration = segment["end"] - segment["start"]
        speaker_times[speaker_id] = speaker_times.get(speaker_id, 0) + duration

    for speaker_id, total_time in sorted(speaker_times.items(), key=lambda x: x[1], reverse=True):
        speaker_name = data["speaker_map"].get(speaker_id, speaker_id)
        percentage = (total_time / data["duration"]) * 100 if data["duration"] > 0 else 0
        print(f"   {speaker_name}: {total_time:6.1f}s ({percentage:5.1f}%)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
