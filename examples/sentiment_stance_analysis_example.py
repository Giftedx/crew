#!/usr/bin/env python3
"""Example usage of the Sentiment and Stance Analysis service.

This script demonstrates how to use the SentimentStanceAnalysisService for analyzing
emotional content, stance positions, and rhetorical devices in transcribed text.

Usage:
    python examples/sentiment_stance_analysis_example.py "sample text to analyze"

Environment Variables:
    None required - uses rule-based analysis when transformers unavailable
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from analysis.sentiment.sentiment_stance_analysis_service import (
    get_sentiment_stance_analysis_service,
)


def main() -> int:
    """Main example function."""
    if len(sys.argv) < 2:
        print(
            'Usage: python examples/sentiment_stance_analysis_example.py "text to analyze"'
        )
        print("Example:")
        print(
            'python examples/sentiment_stance_analysis_example.py "This is absolutely amazing! I love this content so much. The discussion was incredible and I completely agree with everything said."'
        )
        return 1

    text = sys.argv[1]
    if len(text) < 20:
        print("Error: Text too short for meaningful analysis (minimum 20 characters)")
        return 1

    print(f"🧠 Analyzing sentiment and stance in: {len(text)} characters of text")

    # Get sentiment analysis service
    analysis_service = get_sentiment_stance_analysis_service()

    # Analyze text
    result = analysis_service.analyze_text(
        text=text,
        model="balanced",  # Use balanced for good quality/speed balance
        use_cache=True,
    )

    if not result.success:
        print(f"❌ Analysis failed: {result.error}")
        return 1

    data = result.data

    print("✅ Analysis completed!")
    print(f"   Analysis confidence: {data.get('analysis_confidence', 0):.2f}")
    print(f"   Cache hit: {data['cache_hit']}")
    print(f"   Processing time: {data['processing_time_ms']:.0f}ms")
    print()

    # Show sentiment analysis
    sentiment = data.get("sentiment", {})
    if sentiment:
        print("😊 Sentiment Analysis:")
        print(f"   Sentiment: {sentiment.get('sentiment', 'unknown')}")
        print(f"   Confidence: {sentiment.get('confidence', 0):.2f}")
        print(f"   Intensity: {sentiment.get('intensity', 0):.2f}")
        print()

    # Show emotion analysis
    emotion = data.get("emotion", {})
    if emotion:
        print("🎭 Emotion Analysis:")
        print(f"   Primary emotion: {emotion.get('primary_emotion', 'unknown')}")
        print(f"   Confidence: {emotion.get('confidence', 0):.2f}")

        emotion_scores = emotion.get("emotion_scores", {})
        if emotion_scores:
            print("   Emotion scores:")
            for emotion_name, score in sorted(
                emotion_scores.items(), key=lambda x: x[1], reverse=True
            )[:3]:
                print(f"     {emotion_name}: {score:.2f}")
        print()

    # Show stance analysis
    stance = data.get("stance", {})
    if stance:
        print("🗣️  Stance Analysis:")
        print(f"   Stance: {stance.get('stance', 'unknown')}")
        print(f"   Confidence: {stance.get('confidence', 0):.2f}")
        print(f"   Stance type: {stance.get('stance_type', 'unknown')}")
        print()

    # Show rhetorical analysis
    rhetorical = data.get("rhetorical", {})
    if rhetorical:
        print("📝 Rhetorical Analysis:")
        print(f"   Has question: {rhetorical.get('has_question', False)}")
        print(f"   Has exclamation: {rhetorical.get('has_exclamation', False)}")
        print(f"   Has emphasis: {rhetorical.get('has_emphasis', False)}")

        if rhetorical.get("rhetorical_questions"):
            print(f"   Rhetorical questions: {len(rhetorical['rhetorical_questions'])}")
            for question in rhetorical["rhetorical_questions"][:2]:
                print(f'     "{question}"')

        if rhetorical.get("emphasis_words"):
            print(f"   Emphasis words: {', '.join(rhetorical['emphasis_words'][:3])}")
        print()

    # Show text analysis
    print("📄 Text Analysis:")
    print(f"   Speaker: {data.get('speaker', 'Unknown')}")
    print(f"   Timestamp: {data.get('timestamp', 'N/A')}")
    print()

    # Show original text
    print("📝 Original Text:")
    print("-" * 60)
    print(data.get("text_segment", text))
    print("-" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
