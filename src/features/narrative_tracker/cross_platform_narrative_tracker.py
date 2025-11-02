"""Cross-Platform Narrative Tracker for Creator Intelligence.

This module provides narrative tracking capabilities across multiple platforms,
identifying how stories evolve, contradict, or clarify across YouTube, Twitch,
and X (Twitter).

Features:
- Story evolution tracking across platforms
- Contradiction and clarification detection
- Timeline alignment of related content
- Source credibility assessment
- Real-time narrative monitoring

Dependencies:
- Vector DB for similarity matching
- Temporal alignment algorithms
- Platform-specific content ingestion
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from platform.core.step_result import StepResult
from typing import Any, Literal


logger = logging.getLogger(__name__)


@dataclass
class NarrativeEvent:
    """A narrative event with cross-platform alignment."""

    event_id: str
    primary_content: dict[str, Any]
    related_content: list[dict[str, Any]]
    narrative_type: str
    evolution_timeline: list[dict[str, Any]]
    confidence: float
    created_at: float
    updated_at: float


@dataclass
class NarrativeThread:
    """A complete narrative thread across platforms."""

    thread_id: str
    title: str
    summary: str
    events: list[NarrativeEvent]
    platforms_involved: list[str]
    key_participants: list[str]
    total_reach: int
    evolution_score: float
    created_at: float
    updated_at: float


@dataclass
class NarrativeTrackerResult:
    """Result of narrative tracking analysis."""

    narrative_threads: list[NarrativeThread]
    total_content_analyzed: int
    cross_platform_connections: int
    tracking_confidence: float
    processing_time_ms: float = 0.0


class CrossPlatformNarrativeTracker:
    """Service for tracking narrative evolution across platforms.

    Usage:
        tracker = CrossPlatformNarrativeTracker()
        result = tracker.track_narrative_evolution(content_items, time_window)
        threads = result.data["narrative_threads"]
    """

    def __init__(self, cache_size: int = 1000):
        """Initialize narrative tracker.

        Args:
            cache_size: Maximum number of cached results
        """
        self.cache_size = cache_size
        self._tracking_cache: dict[str, NarrativeTrackerResult] = {}
        self._embedding_service = None

    def track_narrative_evolution(
        self,
        content_items: list[dict[str, Any]],
        time_window_hours: int = 24,
        similarity_threshold: float = 0.7,
        max_threads: int = 50,
        model: Literal["fast", "balanced", "quality"] = "balanced",
        use_cache: bool = True,
    ) -> StepResult:
        """Track how narratives evolve across platforms.

        Args:
            content_items: List of content items from multiple platforms
            time_window_hours: Time window for narrative tracking
            similarity_threshold: Threshold for content similarity
            max_threads: Maximum number of narrative threads to return
            model: Model selection
            use_cache: Whether to use tracking cache

        Returns:
            StepResult with narrative tracking results
        """
        try:
            import time

            start_time = time.time()
            if not content_items:
                return StepResult.fail("Content items cannot be empty", status="bad_request")
            if use_cache:
                cache_result = self._check_cache(content_items, time_window_hours, similarity_threshold, model)
                if cache_result:
                    logger.info("Narrative tracking cache hit")
                    return StepResult.ok(
                        data={
                            "narrative_threads": [t.__dict__ for t in cache_result.narrative_threads],
                            "total_content_analyzed": cache_result.total_content_analyzed,
                            "cross_platform_connections": cache_result.cross_platform_connections,
                            "tracking_confidence": cache_result.tracking_confidence,
                            "cache_hit": True,
                            "processing_time_ms": (time.time() - start_time) * 1000,
                        }
                    )
            model_name = self._select_model(model)
            tracking_result = self._track_narrative_evolution(
                content_items, time_window_hours, similarity_threshold, max_threads, model_name
            )
            if tracking_result:
                if use_cache:
                    self._cache_result(content_items, time_window_hours, similarity_threshold, model, tracking_result)
                processing_time = (time.time() - start_time) * 1000
                return StepResult.ok(
                    data={
                        "narrative_threads": [t.__dict__ for t in tracking_result.narrative_threads],
                        "total_content_analyzed": tracking_result.total_content_analyzed,
                        "cross_platform_connections": tracking_result.cross_platform_connections,
                        "tracking_confidence": tracking_result.tracking_confidence,
                        "cache_hit": False,
                        "processing_time_ms": processing_time,
                    }
                )
            else:
                return StepResult.fail("Narrative tracking failed", status="retryable")
        except Exception as e:
            logger.error(f"Narrative tracking failed: {e}")
            return StepResult.fail(f"Narrative tracking failed: {e!s}", status="retryable")

    def find_contradictions_and_clarifications(
        self,
        content_items: list[dict[str, Any]],
        similarity_threshold: float = 0.8,
        model: Literal["fast", "balanced", "quality"] = "balanced",
    ) -> StepResult:
        """Find contradictions and clarifications in narrative evolution.

        Args:
            content_items: Content items to analyze
            similarity_threshold: Threshold for content similarity
            model: Model selection

        Returns:
            StepResult with contradiction/clarification analysis
        """
        try:
            topic_clusters = self._cluster_by_topic(content_items, similarity_threshold)
            contradictions = []
            clarifications = []
            for cluster in topic_clusters:
                cluster_items = cluster["items"]
                if len(cluster_items) < 2:
                    continue
                for i, item1 in enumerate(cluster_items):
                    for item2 in cluster_items[i + 1 :]:
                        relationship = self._analyze_content_relationship(item1, item2)
                        if relationship["type"] == "contradiction":
                            contradictions.append(
                                {
                                    "item1": item1,
                                    "item2": item2,
                                    "contradiction_score": relationship["score"],
                                    "contradiction_type": relationship["subtype"],
                                }
                            )
                        elif relationship["type"] == "clarification":
                            clarifications.append(
                                {
                                    "original_item": item1,
                                    "clarifying_item": item2,
                                    "clarification_score": relationship["score"],
                                    "clarification_type": relationship["subtype"],
                                }
                            )
            return StepResult.ok(
                data={
                    "contradictions": contradictions,
                    "clarifications": clarifications,
                    "total_clusters_analyzed": len(topic_clusters),
                    "contradictions_found": len(contradictions),
                    "clarifications_found": len(clarifications),
                }
            )
        except Exception as e:
            logger.error(f"Contradiction analysis failed: {e}")
            return StepResult.fail(f"Contradiction analysis failed: {e!s}")

    def generate_narrative_timeline(
        self, narrative_thread: NarrativeThread, include_confidence_intervals: bool = True
    ) -> StepResult:
        """Generate a chronological timeline for a narrative thread.

        Args:
            narrative_thread: Narrative thread to analyze
            include_confidence_intervals: Whether to include confidence intervals

        Returns:
            StepResult with timeline data
        """
        try:
            timeline_events = []
            for event in narrative_thread.events:
                sorted_content = sorted(
                    [event.primary_content, *event.related_content], key=lambda x: x.get("timestamp", 0)
                )
                timeline_event = {
                    "event_id": event.event_id,
                    "timestamp": event.created_at,
                    "platform_sequence": [
                        {
                            "platform": item.get("platform", "unknown"),
                            "timestamp": item.get("timestamp", 0),
                            "content_type": item.get("content_type", "unknown"),
                            "title": item.get("title", ""),
                            "confidence": item.get("confidence", 1.0),
                        }
                        for item in sorted_content
                    ],
                    "narrative_type": event.narrative_type,
                    "confidence": event.confidence,
                }
                if include_confidence_intervals:
                    timeline_event["confidence_interval"] = self._calculate_confidence_interval(event)
                timeline_events.append(timeline_event)
            timeline_events.sort(key=lambda x: x["timestamp"])
            return StepResult.ok(
                data={
                    "timeline_events": timeline_events,
                    "thread_id": narrative_thread.thread_id,
                    "total_events": len(timeline_events),
                    "platforms_involved": narrative_thread.platforms_involved,
                }
            )
        except Exception as e:
            logger.error(f"Timeline generation failed: {e}")
            return StepResult.fail(f"Timeline generation failed: {e!s}")

    def _select_model(self, model_alias: str) -> str:
        """Select actual model configuration from alias.

        Args:
            model_alias: Model alias (fast, balanced, quality)

        Returns:
            Model configuration string
        """
        model_configs = {"fast": "fast_tracking", "balanced": "balanced_tracking", "quality": "quality_tracking"}
        return model_configs.get(model_alias, "balanced_tracking")

    def _track_narrative_evolution(
        self,
        content_items: list[dict[str, Any]],
        time_window_hours: int,
        similarity_threshold: float,
        max_threads: int,
        model_name: str,
    ) -> NarrativeTrackerResult | None:
        """Track narrative evolution across platforms.

        Args:
            content_items: Content items to analyze
            time_window_hours: Time window for tracking
            similarity_threshold: Threshold for similarity matching
            max_threads: Maximum threads to return
            model_name: Model configuration

        Returns:
            NarrativeTrackerResult or None if tracking fails
        """
        try:
            current_time = time.time()
            time_cutoff = current_time - time_window_hours * 3600
            recent_items = [item for item in content_items if item.get("timestamp", 0) >= time_cutoff]
            if not recent_items:
                return NarrativeTrackerResult(
                    narrative_threads=[],
                    total_content_analyzed=0,
                    cross_platform_connections=0,
                    tracking_confidence=0.0,
                )
            topic_clusters = self._cluster_by_topic(recent_items, similarity_threshold)
            narrative_threads = []
            total_connections = 0
            for cluster in topic_clusters[:max_threads]:
                thread = self._create_narrative_thread(cluster)
                if thread:
                    narrative_threads.append(thread)
                    total_connections += len(cluster["platforms"]) - 1
            avg_confidence = (
                sum(t.confidence for t in narrative_threads) / len(narrative_threads) if narrative_threads else 0.0
            )
            return NarrativeTrackerResult(
                narrative_threads=narrative_threads,
                total_content_analyzed=len(recent_items),
                cross_platform_connections=total_connections,
                tracking_confidence=avg_confidence,
            )
        except Exception as e:
            logger.error(f"Narrative evolution tracking failed: {e}")
            return None

    def _cluster_by_topic(self, content_items: list[dict[str, Any]], threshold: float) -> list[dict[str, Any]]:
        """Cluster content items by topic similarity.

        Args:
            content_items: Items to cluster
            threshold: Similarity threshold for clustering

        Returns:
            List of topic clusters
        """
        clusters = []
        for item in content_items:
            item_text = item.get("text", item.get("title", ""))
            item.get("id", str(hash(str(item))))
            if not item_text:
                continue
            found_cluster = False
            for cluster in clusters:
                representative = cluster["representative"]
                similarity = self._calculate_text_similarity(
                    item_text, representative.get("text", representative.get("title", ""))
                )
                if similarity >= threshold:
                    cluster["items"].append(item)
                    cluster["platforms"].add(item.get("platform", "unknown"))
                    found_cluster = True
                    break
            if not found_cluster:
                new_cluster = {
                    "id": f"cluster_{len(clusters)}",
                    "representative": item,
                    "items": [item],
                    "platforms": {item.get("platform", "unknown")},
                    "created_at": time.time(),
                }
                clusters.append(new_cluster)
        return clusters

    def _create_narrative_thread(self, topic_cluster: dict[str, Any]) -> NarrativeThread | None:
        """Create a narrative thread from a topic cluster.

        Args:
            topic_cluster: Topic cluster data

        Returns:
            NarrativeThread or None if creation fails
        """
        try:
            cluster_items = topic_cluster["items"]
            if len(cluster_items) < 2:
                return None
            sorted_items = sorted(cluster_items, key=lambda x: x.get("timestamp", 0))
            events = []
            for i, item in enumerate(sorted_items):
                event = NarrativeEvent(
                    event_id=f"event_{topic_cluster['id']}_{i}"
                    primary_content=item,
                    related_content=[],
                    narrative_type=self._classify_narrative_type(item, i, len(sorted_items)),
                    evolution_timeline=[{"item": item, "timestamp": item.get("timestamp", 0)}],
                    confidence=self._calculate_event_confidence(item),
                    created_at=time.time(),
                    updated_at=time.time(),
                )
                events.append(event)
            thread_summary = self._generate_thread_summary(sorted_items)
            thread_title = self._generate_thread_title(sorted_items)
            evolution_score = self._calculate_evolution_score(sorted_items)
            return NarrativeThread(
                thread_id=topic_cluster["id"],
                title=thread_title,
                summary=thread_summary,
                events=events,
                platforms_involved=list(topic_cluster["platforms"]),
                key_participants=self._extract_key_participants(sorted_items),
                total_reach=sum(item.get("reach", 0) for item in sorted_items),
                evolution_score=evolution_score,
                created_at=time.time(),
                updated_at=time.time(),
            )
        except Exception as e:
            logger.error(f"Narrative thread creation failed: {e}")
            return None

    def _classify_narrative_type(self, item: dict[str, Any], position: int, total_items: int) -> str:
        """Classify the narrative type of an item in the evolution.

        Args:
            item: Content item
            position: Position in chronological sequence
            total_items: Total items in sequence

        Returns:
            Narrative type classification
        """
        if position == 0:
            return "breaking_news"
        elif position == total_items - 1:
            return "clarification"
        else:
            return "evolution"

    def _calculate_event_confidence(self, item: dict[str, Any]) -> float:
        """Calculate confidence score for an event.

        Args:
            item: Content item

        Returns:
            Confidence score (0.0 to 1.0)
        """
        confidence_factors = []
        if item.get("platform"):
            confidence_factors.append(0.8)
        if item.get("timestamp"):
            confidence_factors.append(0.7)
        if item.get("text") or item.get("title"):
            confidence_factors.append(0.9)
        if item.get("author"):
            confidence_factors.append(0.6)
        return sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.5

    def _generate_thread_summary(self, items: list[dict[str, Any]]) -> str:
        """Generate a summary for the narrative thread.

        Args:
            items: Items in the thread

        Returns:
            Summary string
        """
        if not items:
            return "No content available"
        first_item = items[0]
        last_item = items[-1]
        first_title = first_item.get("title", "Initial content")
        last_title = last_item.get("title", "Latest update")
        platforms = list({item.get("platform", "unknown") for item in items})
        return f"Narrative evolving from '{first_title}' to '{last_title}' across {len(platforms)} platforms"

    def _generate_thread_title(self, items: list[dict[str, Any]]) -> str:
        """Generate a title for the narrative thread.

        Args:
            items: Items in the thread

        Returns:
            Title string
        """
        for item in items:
            title = item.get("title")
            if title and len(title) > 10:
                return title
        platforms = list({item.get("platform", "unknown") for item in items})
        return f"Cross-Platform Story on {', '.join(platforms[:2])}"

    def _calculate_evolution_score(self, items: list[dict[str, Any]]) -> float:
        """Calculate how much the narrative has evolved.

        Args:
            items: Items in chronological order

        Returns:
            Evolution score (0.0 to 1.0)
        """
        if len(items) < 2:
            return 0.0
        evolution_factors = []
        first_time = items[0].get("timestamp", 0)
        last_time = items[-1].get("timestamp", 0)
        time_span = last_time - first_time if last_time > first_time else 3600
        evolution_factors.append(min(time_span / 3600, 1.0))
        platforms = {item.get("platform", "unknown") for item in items}
        evolution_factors.append(len(platforms) / 3.0)
        content_lengths = [len(str(item.get("text", item.get("title", "")))) for item in items]
        if content_lengths:
            avg_length = sum(content_lengths) / len(content_lengths)
            length_variation = max(content_lengths) / avg_length if avg_length > 0 else 1.0
            evolution_factors.append(min(length_variation / 2.0, 1.0))
        return sum(evolution_factors) / len(evolution_factors) if evolution_factors else 0.0

    def _extract_key_participants(self, items: list[dict[str, Any]]) -> list[str]:
        """Extract key participants from content items.

        Args:
            items: Content items

        Returns:
            List of participant names
        """
        participants = set()
        for item in items:
            author = item.get("author") or item.get("speaker")
            if author:
                participants.add(author)
        return list(participants)[:5]

    def _analyze_content_relationship(self, item1: dict[str, Any], item2: dict[str, Any]) -> dict[str, Any]:
        """Analyze the relationship between two content items.

        Args:
            item1: First content item
            item2: Second content item

        Returns:
            Relationship analysis dictionary
        """
        text1 = item1.get("text", item1.get("title", ""))
        text2 = item2.get("text", item2.get("title", ""))
        similarity = self._calculate_text_similarity(text1, text2)
        if similarity > 0.8:
            if item2.get("timestamp", 0) > item1.get("timestamp", 0):
                return {"type": "clarification", "score": similarity, "subtype": "elaboration"}
            else:
                return {"type": "contradiction", "score": similarity, "subtype": "revision"}
        else:
            return {"type": "unrelated", "score": similarity, "subtype": "different_topic"}

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score (0.0 to 1.0)
        """
        if text1 == text2:
            return 1.0

        def get_ngrams(text: str, n: int = 3) -> set[str]:
            ngrams = set()
            for i in range(len(text) - n + 1):
                ngrams.add(text[i : i + n])
            return ngrams

        ngrams1 = get_ngrams(text1.lower())
        ngrams2 = get_ngrams(text2.lower())
        if not ngrams1 or not ngrams2:
            return 0.0
        intersection = len(ngrams1.intersection(ngrams2))
        union = len(ngrams1.union(ngrams2))
        return intersection / union if union > 0 else 0.0

    def _calculate_confidence_interval(self, event: NarrativeEvent) -> dict[str, float]:
        """Calculate confidence interval for event timing.

        Args:
            event: Narrative event

        Returns:
            Confidence interval dictionary
        """
        base_confidence = event.confidence
        content_indicators = 0
        if event.primary_content.get("text"):
            content_indicators += 1
        if event.primary_content.get("title"):
            content_indicators += 1
        if event.primary_content.get("platform"):
            content_indicators += 1
        adjusted_confidence = base_confidence * (content_indicators / 3.0)
        return {
            "lower_bound": event.created_at - 60 * (1 - adjusted_confidence),
            "upper_bound": event.created_at + 60 * (1 - adjusted_confidence),
            "confidence": adjusted_confidence,
        }

    def _check_cache(
        self, content_items: list[dict[str, Any]], time_window_hours: int, similarity_threshold: float, model: str
    ) -> NarrativeTrackerResult | None:
        """Check if narrative tracking exists in cache.

        Args:
            content_items: Content items
            time_window_hours: Time window
            similarity_threshold: Similarity threshold
            model: Model alias

        Returns:
            Cached NarrativeTrackerResult or None
        """
        import hashlib

        items_hash = hashlib.sha256(str(content_items).encode()).hexdigest()[:16]
        cache_key = f"{items_hash}:{time_window_hours}:{similarity_threshold}:{model}"
        if cache_key in self._tracking_cache:
            return self._tracking_cache[cache_key]
        return None

    def _cache_result(
        self,
        content_items: list[dict[str, Any]],
        time_window_hours: int,
        similarity_threshold: float,
        model: str,
        result: NarrativeTrackerResult,
    ) -> None:
        """Cache narrative tracking result.

        Args:
            content_items: Content items
            time_window_hours: Time window
            similarity_threshold: Similarity threshold
            model: Model alias
            result: NarrativeTrackerResult to cache
        """
        import hashlib

        items_hash = hashlib.sha256(str(content_items).encode()).hexdigest()[:16]
        cache_key = f"{items_hash}:{time_window_hours}:{similarity_threshold}:{model}"
        if len(self._tracking_cache) >= self.cache_size:
            first_key = next(iter(self._tracking_cache))
            del self._tracking_cache[first_key]
        self._tracking_cache[cache_key] = result

    def clear_cache(self) -> StepResult:
        """Clear narrative tracking cache.

        Returns:
            StepResult with cache clear status
        """
        cache_size = len(self._tracking_cache)
        self._tracking_cache.clear()
        logger.info(f"Cleared {cache_size} cached narrative tracking results")
        return StepResult.ok(data={"cleared_entries": cache_size})

    def get_cache_stats(self) -> StepResult:
        """Get narrative tracking cache statistics.

        Returns:
            StepResult with cache statistics
        """
        try:
            stats = {
                "total_cached": len(self._tracking_cache),
                "cache_size_limit": self.cache_size,
                "utilization": len(self._tracking_cache) / self.cache_size if self.cache_size > 0 else 0.0,
            }
            return StepResult.ok(data=stats)
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return StepResult.fail(f"Failed to get cache stats: {e!s}")


_narrative_tracker: CrossPlatformNarrativeTracker | None = None


def get_cross_platform_narrative_tracker() -> CrossPlatformNarrativeTracker:
    """Get singleton narrative tracker instance.

    Returns:
        Initialized CrossPlatformNarrativeTracker instance
    """
    global _narrative_tracker
    if _narrative_tracker is None:
        _narrative_tracker = CrossPlatformNarrativeTracker()
    return _narrative_tracker
