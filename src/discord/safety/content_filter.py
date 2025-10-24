from __future__ import annotations

import asyncio
import re
from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum
from typing import Any

import numpy as np

from ultimate_discord_intelligence_bot.step_result import StepResult


class ContentSeverity(Enum):
    """Content severity levels for moderation."""

    SAFE = "safe"
    LOW_RISK = "low_risk"
    MEDIUM_RISK = "medium_risk"
    HIGH_RISK = "high_risk"
    CRITICAL = "critical"


class ContentCategory(Enum):
    """Content categories for filtering."""

    HARASSMENT = "harassment"
    SPAM = "spam"
    NSFW = "nsfw"
    HATE_SPEECH = "hate_speech"
    VIOLENCE = "violence"
    SELF_HARM = "self_harm"
    MISINFORMATION = "misinformation"
    PERSONAL_INFO = "personal_info"
    COPYRIGHT = "copyright"
    INAPPROPRIATE = "inappropriate"


@dataclass
class ContentFilterResult:
    """Result of content filtering analysis."""

    is_safe: bool
    severity: ContentSeverity
    categories: list[ContentCategory]
    confidence: float
    flagged_patterns: list[str]
    suggestions: list[str]
    metadata: dict[str, Any]


@dataclass
class ContentFilterConfig:
    """Configuration for content filtering."""

    # Severity thresholds
    low_risk_threshold: float = 0.3
    medium_risk_threshold: float = 0.6
    high_risk_threshold: float = 0.8
    critical_threshold: float = 0.9

    # Pattern matching
    enable_regex_filtering: bool = True
    enable_ai_classification: bool = True
    enable_similarity_filtering: bool = True

    # Rate limiting
    enable_rate_limiting: bool = True
    max_messages_per_minute: int = 10
    max_messages_per_hour: int = 100

    # Caching
    enable_caching: bool = True
    cache_size: int = 1000
    cache_ttl_seconds: int = 3600

    # Moderation actions
    auto_delete_high_risk: bool = False
    auto_warn_users: bool = True
    log_moderation_actions: bool = True


class ContentFilter:
    """Advanced content filtering system for Discord messages."""

    def __init__(self, config: ContentFilterConfig):
        self.config = config

        # Pattern databases
        self._harassment_patterns = self._load_harassment_patterns()
        self._spam_patterns = self._load_spam_patterns()
        self._nsfw_patterns = self._load_nsfw_patterns()
        self._hate_speech_patterns = self._load_hate_speech_patterns()
        self._violence_patterns = self._load_violence_patterns()
        self._self_harm_patterns = self._load_self_harm_patterns()
        self._misinformation_patterns = self._load_misinformation_patterns()
        self._personal_info_patterns = self._load_personal_info_patterns()

        # Rate limiting tracking
        self._user_message_counts: dict[str, deque] = defaultdict(lambda: deque())
        self._user_hourly_counts: dict[str, int] = defaultdict(int)
        self._rate_limit_lock = asyncio.Lock()

        # Caching
        self._filter_cache: dict[str, ContentFilterResult] = {}
        self._cache_timestamps: dict[str, float] = {}

        # Statistics
        self._stats = {
            "total_messages_filtered": 0,
            "messages_flagged": 0,
            "messages_deleted": 0,
            "users_warned": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_filtering_time_ms": 0.0,
        }

    async def filter_content(self, content: str, user_id: str, guild_id: str | None = None) -> StepResult:
        """Filter content for safety and appropriateness."""
        try:
            start_time = asyncio.get_event_loop().time()

            # Check cache first
            cache_key = f"{user_id}:{hash(content)}"
            if self.config.enable_caching and cache_key in self._filter_cache:
                cache_age = asyncio.get_event_loop().time() - self._cache_timestamps[cache_key]
                if cache_age < self.config.cache_ttl_seconds:
                    self._stats["cache_hits"] += 1
                    result = self._filter_cache[cache_key]
                    self._update_stats(start_time)
                    return StepResult.ok(data={"filter_result": result})

            self._stats["cache_misses"] += 1

            # Check rate limiting
            if self.config.enable_rate_limiting:
                rate_limit_result = await self._check_rate_limits(user_id)
                if not rate_limit_result.success:
                    return rate_limit_result

            # Perform content filtering
            filter_result = await self._analyze_content(content, user_id, guild_id)

            # Cache result
            if self.config.enable_caching:
                self._filter_cache[cache_key] = filter_result
                self._cache_timestamps[cache_key] = asyncio.get_event_loop().time()

                # Cleanup old cache entries
                await self._cleanup_cache()

            # Update statistics
            self._stats["total_messages_filtered"] += 1
            if not filter_result.is_safe:
                self._stats["messages_flagged"] += 1

            self._update_stats(start_time)

            return StepResult.ok(data={"filter_result": filter_result})

        except Exception as e:
            return StepResult.fail(f"Content filtering failed: {e!s}")

    async def _check_rate_limits(self, user_id: str) -> StepResult:
        """Check if user has exceeded rate limits."""
        async with self._rate_limit_lock:
            current_time = asyncio.get_event_loop().time()

            # Clean old entries from minute-based tracking
            user_messages = self._user_message_counts[user_id]
            while user_messages and current_time - user_messages[0] > 60:
                user_messages.popleft()

            # Check minute limit
            if len(user_messages) >= self.config.max_messages_per_minute:
                return StepResult.fail(f"Rate limit exceeded: {len(user_messages)} messages in the last minute")

            # Check hour limit
            if self._user_hourly_counts[user_id] >= self.config.max_messages_per_hour:
                return StepResult.fail(
                    f"Rate limit exceeded: {self._user_hourly_counts[user_id]} messages in the last hour"
                )

            # Record this message
            user_messages.append(current_time)
            self._user_hourly_counts[user_id] += 1

            return StepResult.ok(data={"rate_limit_check": "passed"})

    async def _analyze_content(self, content: str, user_id: str, guild_id: str | None) -> ContentFilterResult:
        """Analyze content for various safety issues."""
        categories = []
        flagged_patterns = []
        confidence_scores = []

        # Regex-based pattern matching
        if self.config.enable_regex_filtering:
            regex_result = self._check_regex_patterns(content)
            categories.extend(regex_result["categories"])
            flagged_patterns.extend(regex_result["patterns"])
            confidence_scores.extend(regex_result["scores"])

        # AI-based classification (placeholder for future implementation)
        if self.config.enable_ai_classification:
            ai_result = await self._ai_classify_content(content)
            categories.extend(ai_result["categories"])
            confidence_scores.extend(ai_result["scores"])

        # Similarity-based filtering (placeholder for future implementation)
        if self.config.enable_similarity_filtering:
            similarity_result = await self._check_similarity(content)
            categories.extend(similarity_result["categories"])
            confidence_scores.extend(similarity_result["scores"])

        # Determine overall severity
        severity, overall_confidence = self._determine_severity(categories, confidence_scores)
        is_safe = severity in [ContentSeverity.SAFE, ContentSeverity.LOW_RISK]

        # Generate suggestions
        suggestions = self._generate_suggestions(categories, severity)

        return ContentFilterResult(
            is_safe=is_safe,
            severity=severity,
            categories=list(set(categories)),
            confidence=overall_confidence,
            flagged_patterns=flagged_patterns,
            suggestions=suggestions,
            metadata={
                "user_id": user_id,
                "guild_id": guild_id,
                "content_length": len(content),
                "analysis_timestamp": asyncio.get_event_loop().time(),
            },
        )

    def _check_regex_patterns(self, content: str) -> dict[str, Any]:
        """Check content against regex patterns."""
        categories = []
        patterns = []
        scores = []

        content_lower = content.lower()

        # Check each category
        pattern_checks = [
            (self._harassment_patterns, ContentCategory.HARASSMENT, 0.8),
            (self._spam_patterns, ContentCategory.SPAM, 0.7),
            (self._nsfw_patterns, ContentCategory.NSFW, 0.9),
            (self._hate_speech_patterns, ContentCategory.HATE_SPEECH, 0.9),
            (self._violence_patterns, ContentCategory.VIOLENCE, 0.8),
            (self._self_harm_patterns, ContentCategory.SELF_HARM, 0.9),
            (self._misinformation_patterns, ContentCategory.MISINFORMATION, 0.6),
            (self._personal_info_patterns, ContentCategory.PERSONAL_INFO, 0.7),
        ]

        for pattern_list, category, base_score in pattern_checks:
            for pattern in pattern_list:
                if re.search(pattern, content_lower):
                    categories.append(category)
                    patterns.append(pattern)
                    scores.append(base_score)

        return {
            "categories": categories,
            "patterns": patterns,
            "scores": scores,
        }

    async def _ai_classify_content(self, content: str) -> dict[str, Any]:
        """AI-based content classification.

        Integration point: Use LLM service (services/openrouter_service) or
        local transformer model for content classification.

        Example ML integration:
            from transformers import pipeline
            classifier = pipeline("text-classification", model="unitary/toxic-bert")
            result = classifier(content)

        Returns:
            Dict with categories and confidence scores
        """
        # Heuristic fallback until ML model integrated
        from ultimate_discord_intelligence_bot.orchestrator.quality_validators import is_inappropriate

        try:
            is_toxic = is_inappropriate(content)
            if is_toxic:
                return {"categories": [ContentCategory.HARASSMENT], "scores": [0.7]}
            return {"categories": [], "scores": []}
        except Exception:
            return {"categories": [], "scores": []}

    async def _check_similarity(self, content: str) -> dict[str, Any]:
        """Check content similarity to known problematic content.

        Integration point: Use Qdrant vector store via memory/qdrant_provider
        to find semantically similar content.

        Example embedding integration:
            from memory.qdrant_provider import get_qdrant_client
            client = get_qdrant_client()
            results = client.search(collection="flagged_content", query_vector=embedding)

        Returns:
            Dict with categories and similarity scores
        """
        # Hash-based duplicate detection until embeddings integrated
        import hashlib

        try:
            content_hash = hashlib.md5(content.lower().encode(), usedforsecurity=False).hexdigest()  # nosec B324
            # Placeholder: In production, query vector store for semantic similarity
            return {"categories": [], "scores": []}
        except Exception:
            return {"categories": [], "scores": []}

    def _determine_severity(
        self, categories: list[ContentCategory], scores: list[float]
    ) -> tuple[ContentSeverity, float]:
        """Determine overall severity based on categories and scores."""
        if not categories:
            return ContentSeverity.SAFE, 0.0

        # Calculate weighted average confidence
        overall_confidence = np.mean(scores) if scores else 0.0

        # Determine severity based on categories and confidence
        critical_categories = {ContentCategory.HATE_SPEECH, ContentCategory.SELF_HARM, ContentCategory.VIOLENCE}
        high_risk_categories = {ContentCategory.HARASSMENT, ContentCategory.NSFW}
        medium_risk_categories = {ContentCategory.MISINFORMATION, ContentCategory.PERSONAL_INFO}

        if (
            any(cat in critical_categories for cat in categories)
            and overall_confidence >= self.config.critical_threshold
        ):
            return ContentSeverity.CRITICAL, overall_confidence
        elif (
            any(cat in high_risk_categories for cat in categories)
            and overall_confidence >= self.config.high_risk_threshold
        ):
            return ContentSeverity.HIGH_RISK, overall_confidence
        elif (
            any(cat in medium_risk_categories for cat in categories)
            and overall_confidence >= self.config.medium_risk_threshold
        ):
            return ContentSeverity.MEDIUM_RISK, overall_confidence
        elif overall_confidence >= self.config.low_risk_threshold:
            return ContentSeverity.LOW_RISK, overall_confidence
        else:
            return ContentSeverity.SAFE, overall_confidence

    def _generate_suggestions(self, categories: list[ContentCategory], severity: ContentSeverity) -> list[str]:
        """Generate suggestions for content improvement."""
        suggestions = []

        if ContentCategory.HARASSMENT in categories:
            suggestions.append("Please maintain respectful communication with other users.")

        if ContentCategory.SPAM in categories:
            suggestions.append("Avoid repetitive or excessive messaging.")

        if ContentCategory.NSFW in categories:
            suggestions.append("Please keep content appropriate for all audiences.")

        if ContentCategory.HATE_SPEECH in categories:
            suggestions.append("Discriminatory language is not tolerated.")

        if ContentCategory.VIOLENCE in categories:
            suggestions.append("Please avoid content that promotes or glorifies violence.")

        if ContentCategory.SELF_HARM in categories:
            suggestions.append("If you're struggling, please reach out to appropriate support resources.")

        if ContentCategory.MISINFORMATION in categories:
            suggestions.append("Please verify information before sharing.")

        if ContentCategory.PERSONAL_INFO in categories:
            suggestions.append("Please avoid sharing personal information for your safety.")

        if severity == ContentSeverity.CRITICAL:
            suggestions.append("This content violates community guidelines and may result in moderation action.")

        return suggestions

    async def _cleanup_cache(self):
        """Clean up old cache entries."""
        current_time = asyncio.get_event_loop().time()
        expired_keys = [
            key
            for key, timestamp in self._cache_timestamps.items()
            if current_time - timestamp > self.config.cache_ttl_seconds
        ]

        for key in expired_keys:
            self._filter_cache.pop(key, None)
            self._cache_timestamps.pop(key, None)

    def _update_stats(self, start_time: float):
        """Update performance statistics."""
        processing_time = (asyncio.get_event_loop().time() - start_time) * 1000  # Convert to ms

        # Update average processing time
        current_avg = self._stats["avg_filtering_time_ms"]
        total_messages = self._stats["total_messages_filtered"]

        if total_messages > 0:
            self._stats["avg_filtering_time_ms"] = (
                current_avg * (total_messages - 1) + processing_time
            ) / total_messages
        else:
            self._stats["avg_filtering_time_ms"] = processing_time

    # Pattern loading methods (simplified implementations)
    def _load_harassment_patterns(self) -> list[str]:
        """Load harassment detection patterns."""
        return [
            r"\b(kill|murder|destroy)\s+(yourself|urself|urself)\b",
            r"\b(you\s+should\s+die|die\s+already)\b",
            r"\b(waste\s+of\s+space|useless)\b",
            # Add more patterns as needed
        ]

    def _load_spam_patterns(self) -> list[str]:
        """Load spam detection patterns."""
        return [
            r"(.)\1{10,}",  # Repeated characters
            r"\b(buy\s+now|click\s+here|free\s+money)\b",
            r"https?://[^\s]+",  # URLs (basic detection)
            # Add more patterns as needed
        ]

    def _load_nsfw_patterns(self) -> list[str]:
        """Load NSFW content patterns."""
        return [
            r"\b(sex|porn|nude|naked)\b",
            r"\b(fuck|shit|bitch|whore)\b",
            # Add more patterns as needed
        ]

    def _load_hate_speech_patterns(self) -> list[str]:
        """Load hate speech patterns."""
        return [
            r"\b(nazi|hitler|fascist)\b",
            r"\b(white\s+supremacy|racial\s+superiority)\b",
            # Add more patterns as needed
        ]

    def _load_violence_patterns(self) -> list[str]:
        """Load violence-related patterns."""
        return [
            r"\b(bomb|explode|shoot|stab|kill)\b",
            r"\b(violence|fight|attack|harm)\b",
            # Add more patterns as needed
        ]

    def _load_self_harm_patterns(self) -> list[str]:
        """Load self-harm patterns."""
        return [
            r"\b(suicide|kill\s+myself|end\s+it\s+all)\b",
            r"\b(cut\s+myself|hurt\s+myself)\b",
            # Add more patterns as needed
        ]

    def _load_misinformation_patterns(self) -> list[str]:
        """Load misinformation patterns."""
        return [
            r"\b(covid\s+is\s+fake|vaccines\s+cause\s+autism)\b",
            r"\b(flat\s+earth|moon\s+landing\s+fake)\b",
            # Add more patterns as needed
        ]

    def _load_personal_info_patterns(self) -> list[str]:
        """Load personal information patterns."""
        return [
            r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
            r"\b\d{4}\s+\d{4}\s+\d{4}\s+\d{4}\b",  # Credit card
            r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b",  # Email
            # Add more patterns as needed
        ]

    def get_statistics(self) -> dict[str, Any]:
        """Get filtering statistics."""
        return self._stats.copy()

    def reset_statistics(self):
        """Reset filtering statistics."""
        self._stats = {
            "total_messages_filtered": 0,
            "messages_flagged": 0,
            "messages_deleted": 0,
            "users_warned": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_filtering_time_ms": 0.0,
        }


def create_content_filter(config: ContentFilterConfig | None = None) -> ContentFilter:
    """Create a content filter with the specified configuration."""
    if config is None:
        config = ContentFilterConfig()

    return ContentFilter(config)
