#!/usr/bin/env python3
from __future__ import annotations

import sys
import time
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from features.community_pulse.community_pulse_analyzer_service import (
    get_community_pulse_analyzer_service,
)


def main() -> int:
    print("📊 Community Pulse Analyzer Demo")
    service = get_community_pulse_analyzer_service()

    now = time.time()
    items = [
        {
            "platform": "youtube",
            "text": "Amazing episode. Love the guest! What's next?",
            "timestamp": now - 300,
            "engagement": 30,
        },
        {
            "platform": "x",
            "text": "Bad take tbh. Why so negative?",
            "timestamp": now - 1200,
            "engagement": 15,
        },
        {
            "platform": "reddit",
            "text": "Helpful breakdown. Any update on the controversy?",
            "timestamp": now - 2400,
            "engagement": 7,
        },
    ]

    res = service.analyze(items)
    if not res.success:
        print(f"❌ Failed: {res.error}")
        return 1

    data = res.data
    print(f"Global Sentiment: {data.global_sentiment:.2f}")
    print(f"Global Momentum: {data.global_momentum:.2f}")
    print("Trending Topics:", ", ".join(data.trending_topics))
    print("Audience Questions:")
    for q in data.audience_questions[:5]:
        print(" -", q)
    print("Risk Flags:", ", ".join(data.risk_flags))

    print("\nPer-Platform:")
    for s in data.platform_summaries:
        print(f" - {s.platform}: n={s.total_items}, sentiment={s.avg_sentiment:.2f}, momentum={s.momentum_score:.2f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
