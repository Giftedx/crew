"""Community Pulse Analyzer Service.

Analyzes audience/community signals across platforms (YouTube, Twitch, X, Reddit, Discord)
to produce actionable insights: sentiment, momentum, topics, questions, and risk flags.

Follows StepResult pattern and includes caching.
"""

from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass
from typing import Any, Literal

from ultimate_discord_intelligence_bot.step_result import StepResult


logger = logging.getLogger(__name__)


@dataclass
class PlatformSignalSummary:
    platform: str
    total_items: int
    avg_sentiment: float  # -1..1
    momentum_score: float  # 0..1
    top_keywords: list[str]
    top_questions: list[str]
    risk_indicators: list[str]


@dataclass
class CommunityPulseResult:
    platform_summaries: list[PlatformSignalSummary]
    global_sentiment: float
    global_momentum: float
    trending_topics: list[str]
    audience_questions: list[str]
    risk_flags: list[str]
    cached: bool = False
    processing_time_ms: float = 0.0


class CommunityPulseAnalyzerService:
    """Aggregates and analyzes community signals across platforms."""

    def __init__(self, cache_size: int = 1000) -> None:
        self.cache_size = cache_size
        self._cache: dict[str, CommunityPulseResult] = {}

        # Simple lexicon for sentiment and risks
        self._positive_words = {
            "love",
            "great",
            "awesome",
            "amazing",
            "good",
            "helpful",
            "smart",
            "agree",
            "win",
        }
        self._negative_words = {
            "hate",
            "bad",
            "terrible",
            "awful",
            "stupid",
            "angry",
            "disagree",
            "fail",
        }
        self._risk_terms = {
            "controversy",
            "drama",
            "strike",
            "piracy",
            "dmca",
            "lawsuit",
            "unsafe",
            "boycott",
        }

    def analyze(
        self,
        items: list[dict[str, Any]],
        window_hours: int = 24,
        model: Literal["fast", "balanced", "quality"] = "fast",
        use_cache: bool = True,
    ) -> StepResult:
        """Analyze community items.

        Args:
            items: List of items with fields: platform, text, timestamp, engagement (optional)
            window_hours: Time window to consider
            model: Analysis profile
            use_cache: Use cache
        """
        try:
            if not items:
                return StepResult.fail("No items provided", status="bad_request")

            start = time.time()

            cache_key = None
            if use_cache:
                cache_key = self._make_cache_key(items, window_hours, model)
                cached = self._cache.get(cache_key)
                if cached:
                    logger.debug("Community pulse cache hit")
                    cached.processing_time_ms = (time.time() - start) * 1000
                    cached.cached = True
                    return StepResult.ok(data=cached)

            # Filter by window (assumes timestamps are epoch seconds)
            cutoff = time.time() - window_hours * 3600
            window_items = [it for it in items if float(it.get("timestamp", 0)) >= cutoff]
            if not window_items:
                window_items = items[:]

            # Group by platform
            by_platform: dict[str, list[dict[str, Any]]] = {}
            for it in window_items:
                p = str(it.get("platform", "unknown")).lower()
                by_platform.setdefault(p, []).append(it)

            platform_summaries: list[PlatformSignalSummary] = []
            all_keywords: list[str] = []
            all_questions: list[str] = []
            all_risks: list[str] = []
            sentiments: list[float] = []
            momenta: list[float] = []

            for platform, p_items in by_platform.items():
                texts = [str(it.get("text", "")) for it in p_items]
                sentiments_p = [self._sentiment_from_text(t) for t in texts]
                avg_sentiment = sum(sentiments_p) / len(sentiments_p) if sentiments_p else 0.0

                momentum = self._momentum_score(p_items)

                keywords = self._extract_keywords(texts)
                questions = self._extract_questions(texts)
                risks = self._extract_risks(texts)

                platform_summaries.append(
                    PlatformSignalSummary(
                        platform=platform,
                        total_items=len(p_items),
                        avg_sentiment=avg_sentiment,
                        momentum_score=momentum,
                        top_keywords=keywords[:8],
                        top_questions=questions[:6],
                        risk_indicators=risks[:6],
                    )
                )

                sentiments.append(avg_sentiment)
                momenta.append(momentum)
                all_keywords.extend(keywords)
                all_questions.extend(questions)
                all_risks.extend(risks)

            global_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0
            global_momentum = sum(momenta) / len(momenta) if momenta else 0.0
            trending_topics = self._top_n(all_keywords, n=10)
            audience_questions = self._top_n(all_questions, n=10)
            risk_flags = self._top_n(all_risks, n=10)

            result = CommunityPulseResult(
                platform_summaries=platform_summaries,
                global_sentiment=global_sentiment,
                global_momentum=global_momentum,
                trending_topics=trending_topics,
                audience_questions=audience_questions,
                risk_flags=risk_flags,
                cached=False,
                processing_time_ms=(time.time() - start) * 1000,
            )

            if use_cache and cache_key:
                self._cache_put(cache_key, result)

            return StepResult.ok(data=result)
        except Exception as e:
            logger.error(f"Community pulse analysis failed: {e}")
            return StepResult.fail(f"Community pulse analysis failed: {e!s}")

    def clear_cache(self) -> StepResult:
        size = len(self._cache)
        self._cache.clear()
        return StepResult.ok(data={"cleared": size})

    # --- Internal heuristics -------------------------------------------------

    def _make_cache_key(self, items: list[dict[str, Any]], window_hours: int, model: str) -> str:
        return hashlib.sha256(f"{items}|{window_hours}|{model}".encode()).hexdigest()[:24]

    def _cache_put(self, key: str, value: CommunityPulseResult) -> None:
        if len(self._cache) >= self.cache_size:
            # FIFO eviction
            first = next(iter(self._cache))
            del self._cache[first]
        self._cache[key] = value

    def _sentiment_from_text(self, text: str) -> float:
        t = text.lower()
        pos = sum(1 for w in self._positive_words if w in t)
        neg = sum(1 for w in self._negative_words if w in t)
        if pos == 0 and neg == 0:
            return 0.0
        score = (pos - neg) / max(pos + neg, 1)
        # Clamp to [-1, 1]
        return max(-1.0, min(1.0, score))

    def _momentum_score(self, items: list[dict[str, Any]]) -> float:
        # Simple momentum: normalized recentness + engagement
        if not items:
            return 0.0
        now = time.time()
        recencies = []
        engagements = []
        for it in items:
            ts = float(it.get("timestamp", now))
            recency = max(0.0, 1.0 - (now - ts) / (72 * 3600))  # 0..1 over last 72h
            recencies.append(recency)
            engagements.append(float(it.get("engagement", 1)))
        avg_recency = sum(recencies) / len(recencies)
        avg_engagement = sum(engagements) / len(engagements)
        # Normalize engagement via log-like squashing
        norm_eng = min(1.0, avg_engagement / (avg_engagement + 10.0))
        return round(0.6 * avg_recency + 0.4 * norm_eng, 4)

    def _extract_keywords(self, texts: list[str]) -> list[str]:
        import re

        tokens: list[str] = []
        for t in texts:
            tokens.extend(re.findall(r"[a-zA-Z][a-zA-Z0-9_\-]{3,}", t.lower()))

        stop = {
            "this",
            "that",
            "with",
            "http",
            "https",
            "from",
            "about",
            "there",
            "which",
            "have",
            "been",
            "your",
            "they",
            "them",
            "will",
            "what",
            "when",
            "where",
            "who",
        }
        tokens = [tok for tok in tokens if tok not in stop]

        return self._top_n(tokens, n=15)

    def _extract_questions(self, texts: list[str]) -> list[str]:
        import re

        qs: list[str] = []
        for t in texts:
            # Grab lines or clauses that end with a question mark
            qs.extend([q.strip() for q in re.findall(r"([^\n\r\?]{8,}\?)", t)])
        return qs[:20]

    def _extract_risks(self, texts: list[str]) -> list[str]:
        risks: list[str] = []
        for t in texts:
            tl = t.lower()
            for term in self._risk_terms:
                if term in tl:
                    risks.append(term)
        return risks

    def _top_n(self, items: list[str], n: int) -> list[str]:
        from collections import Counter

        if not items:
            return []
        counts = Counter(items)
        return [w for w, _ in counts.most_common(n)]


_community_pulse_service: CommunityPulseAnalyzerService | None = None


def get_community_pulse_analyzer_service(
    cache_size: int = 1000,
) -> CommunityPulseAnalyzerService:
    global _community_pulse_service
    if _community_pulse_service is None:
        _community_pulse_service = CommunityPulseAnalyzerService(cache_size=cache_size)
    return _community_pulse_service
