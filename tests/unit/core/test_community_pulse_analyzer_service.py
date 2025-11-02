from __future__ import annotations

import time

from features.community_pulse.community_pulse_analyzer_service import (
    CommunityPulseAnalyzerService,
    get_community_pulse_analyzer_service,
)


class TestCommunityPulseAnalyzerService:
    def setup_method(self) -> None:
        self.service = CommunityPulseAnalyzerService(cache_size=16)

    def _fake_items(self) -> list[dict]:
        now = time.time()
        return [
            {
                "platform": "youtube",
                "text": "I love this episode, awesome discussion! What do you think about the guest?",
                "timestamp": now - 600,
                "engagement": 25,
            },
            {
                "platform": "x",
                "text": "Bad take. I disagree strongly. Why did they say that?",
                "timestamp": now - 1200,
                "engagement": 15,
            },
            {
                "platform": "reddit",
                "text": "Great breakdown. Any updates on the controversy?",
                "timestamp": now - 3600,
                "engagement": 8,
            },
            {
                "platform": "discord",
                "text": "This was amazing. Helpful details. Any ETA on part 2?",
                "timestamp": now - 300,
                "engagement": 5,
            },
        ]

    def test_analyze_basic(self) -> None:
        items = self._fake_items()
        result = self.service.analyze(items, window_hours=24, use_cache=False)
        assert result.success
        data = result.data
        assert data.global_momentum >= 0.0
        assert -1.0 <= data.global_sentiment <= 1.0
        assert len(data.platform_summaries) >= 1
        # Ensure keywords/questions surfaced
        assert isinstance(data.trending_topics, list)
        assert isinstance(data.audience_questions, list)

    def test_cache(self) -> None:
        items = self._fake_items()
        first = self.service.analyze(items, use_cache=True)
        assert first.success
        second = self.service.analyze(items, use_cache=True)
        assert second.success
        assert second.data.cached is True

    def test_empty_items(self) -> None:
        result = self.service.analyze([], use_cache=False)
        assert not result.success
        assert result.status == "bad_request"


class TestCommunityPulseSingleton:
    def test_singleton(self) -> None:
        s1 = get_community_pulse_analyzer_service()
        s2 = get_community_pulse_analyzer_service()
        assert s1 is s2
