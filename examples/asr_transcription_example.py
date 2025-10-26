#!/usr/bin/env python3
"""Example usage of the ASR transcription service.

This script demonstrates how to use the ASRService for transcribing
audio files in the Creator Intelligence system.

Usage:
    python examples/asr_transcription_example.py audio_file.mp3

Environment Variables:
    OPENAI_API_KEY: Required for high-quality Whisper API transcription
"""

from __future__ import annotations

import sys
from pathlib import Path


# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from analysis.transcription.asr_service import get_asr_service


def main() -> int:
    """Main example function."""
    if len(sys.argv) != 2:
        print("Usage: python examples/asr_transcription_example.py <audio_file>")
        return 1

    audio_path = Path(sys.argv[1])
    if not audio_path.exists():
        print(f"Error: Audio file not found: {audio_path}")
        return 1

    print(f"🎵 Transcribing: {audio_path}")

    # Get ASR service
    asr_service = get_asr_service()

    # Transcribe with balanced quality
    result = asr_service.transcribe_audio(
        audio_path=audio_path,
        model="balanced",  # Use faster-whisper-base for good quality/speed balance
        language="en",  # English language
        use_cache=True,
    )

    if not result.success:
        print(f"❌ Transcription failed: {result.error}")
        return 1

    data = result.data

    print("✅ Transcription completed!")
    print(f"   Model: {data['model']}")
    print(f"   Duration: {data['duration']:.2f}s")
    print(f"   Language: {data.get('language', 'unknown')}")
    print(f"   Confidence: {data.get('confidence', 0):.2f}")
    print(f"   Cache hit: {data['cache_hit']}")
    print(f"   Processing time: {data['processing_time_ms']:.0f}ms")
    print()
    print("📝 Transcript:")
    print("-" * 40)
    print(data["text"])
    print("-" * 40)

    # Show segments if available
    segments = data.get("segments", [])
    if segments:
        print(f"\n🔤 Segments ({len(segments)}):")
        for i, segment in enumerate(segments[:5]):  # Show first 5 segments
            print(
                f"   {i + 1}. [{segment['start']:.1f}s - {segment['end']:.1f}s] "
                f'"{segment["text"]}" (conf: {segment.get("confidence", 1):.2f})'
            )

        if len(segments) > 5:
            print(f"   ... and {len(segments) - 5} more segments")

    return 0


if __name__ == "__main__":
    sys.exit(main())
