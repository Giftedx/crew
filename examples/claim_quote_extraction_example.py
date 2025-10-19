#!/usr/bin/env python3
"""Example usage of the Claim and Quote Extraction service.

This script demonstrates how to use the ClaimQuoteExtractionService for extracting
factual claims and notable quotes from transcribed content.

Usage:
    python examples/claim_quote_extraction_example.py "transcript text"

Environment Variables:
    None required - uses rule-based extraction when NLP models unavailable
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from analysis.nlp.claim_quote_extraction_service import get_claim_quote_extraction_service


def main() -> int:
    """Main example function."""
    if len(sys.argv) < 2:
        print("Usage: python examples/claim_quote_extraction_example.py \"transcript text\"")
        print("Example:")
        print('python examples/claim_quote_extraction_example.py "According to research, AI will change everything by 2025. The expert said, \'This is revolutionary.\' In fact, statistics show 80% improvement."')
        return 1

    text = sys.argv[1]
    if len(text) < 50:
        print("Error: Text too short for meaningful extraction (minimum 50 characters)")
        return 1

    print(f"🔍 Extracting claims and quotes from: {len(text)} characters of text")

    # Get extraction service
    extraction_service = get_claim_quote_extraction_service()

    # Extract claims and quotes
    result = extraction_service.extract_claims_and_quotes(
        text=text,
        model="balanced",  # Use balanced for good quality/speed balance
        use_cache=True,
    )

    if not result.success:
        print(f"❌ Extraction failed: {result.error}")
        return 1

    data = result.data

    print("✅ Extraction completed!")
    print(f"   Model: {data['model']}")
    print(f"   Extraction confidence: {data.get('extraction_confidence', 0):.2f}")
    print(f"   Cache hit: {data['cache_hit']}")
    print(f"   Processing time: {data['processing_time_ms']:.0f}ms")
    print()

    # Show extracted claims
    claims = data.get("claims", [])
    if claims:
        print(f"📋 Extracted Claims ({len(claims)}):")
        print("-" * 80)

        for i, claim in enumerate(claims[:5]):  # Show first 5 claims
            confidence = claim.get("confidence", 0)
            claim_type = claim.get("claim_type", "statement")
            speaker = claim.get("speaker", "Unknown")

            print(f"   {i+1}. \"{claim['text']}\"")
            print(f"      Speaker: {speaker} | Type: {claim_type} | Confidence: {confidence:.2f}")
            print(f"      Status: {claim.get('verification_status', 'unverified')}")

        if len(claims) > 5:
            print(f"   ... and {len(claims) - 5} more claims")

    print("-" * 80)

    # Show extracted quotes
    quotes = data.get("quotes", [])
    if quotes:
        print(f"💬 Extracted Quotes ({len(quotes)}):")
        print("-" * 80)

        for i, quote in enumerate(quotes[:5]):  # Show first 5 quotes
            confidence = quote.get("confidence", 0)
            quote_type = quote.get("quote_type", "notable")
            speaker = quote.get("speaker", "Unknown")
            significance = quote.get("significance_score", 0)

            print(f"   {i+1}. \"{quote['text']}\"")
            print(f"      Speaker: {speaker} | Type: {quote_type} | Confidence: {confidence:.2f}")
            print(f"      Significance: {significance:.2f}")

            if quote.get("context"):
                print(f"      Context: {quote['context'][:60]}...")

        if len(quotes) > 5:
            print(f"   ... and {len(quotes) - 5} more quotes")

    print("-" * 80)

    # Show summary statistics
    total_items = len(claims) + len(quotes)
    if total_items > 0:
        print("📊 Extraction Summary:"        print(f"   Total items extracted: {total_items}")
        print(f"   Claims: {len(claims)} | Quotes: {len(quotes)}")

        # Calculate average confidence
        all_confidences = [c.get("confidence", 0) for c in claims] + [q.get("confidence", 0) for q in quotes]
        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0
        print(f"   Average confidence: {avg_confidence:.2f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

