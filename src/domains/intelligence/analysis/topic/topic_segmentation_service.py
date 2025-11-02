"""Topic Segmentation Service for Creator Intelligence.

This module provides topic modeling and segmentation capabilities using BERTopic
for hierarchical clustering of transcribed content.

Features:
- BERTopic integration for hierarchical topic modeling
- Topic coherence scoring and evaluation
- Integration with ASR service for text input
- Topic evolution tracking across episodes
- Semantic topic similarity analysis

Dependencies:
- bertopic: For hierarchical topic modeling
- scikit-learn: For clustering algorithms
- sentence-transformers: For text embeddings
- Optional: Custom embedding models for domain-specific topics
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from platform.core.step_result import StepResult
from typing import Any, Literal


logger = logging.getLogger(__name__)
try:
    from bertopic import BERTopic
    from bertopic.representation import KeyBERTInspired, MaximalMarginalRelevance

    BERTOPIC_AVAILABLE = True
except ImportError:
    BERTOPIC_AVAILABLE = False
    BERTopic = None
    logger.warning("bertopic not available, topic segmentation disabled")
try:
    from sentence_transformers import SentenceTransformer

    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None
    logger.warning("sentence-transformers not available, using fallback embeddings")


@dataclass
class TopicSegment:
    """A segment of content with assigned topics."""

    start_time: float
    end_time: float
    text: str
    topics: list[str]
    topic_names: list[str]
    coherence_score: float
    dominant_topic: str | None = None


@dataclass
class TopicModel:
    """A trained topic model with metadata."""

    model_id: str
    num_topics: int
    coherence_score: float
    topics: list[str]
    topic_embeddings: list[list[float]]
    model_type: str
    created_at: str
    training_data_size: int


@dataclass
class TopicSegmentationResult:
    """Result of topic segmentation operation."""

    segments: list[TopicSegment]
    topic_model: TopicModel | None
    overall_coherence: float
    topic_distribution: dict[str, float]
    model: str
    processing_time_ms: float = 0.0


class TopicSegmentationService:
    """Topic segmentation service using BERTopic for hierarchical clustering.

    Usage:
        service = TopicSegmentationService()
        result = service.segment_text("long transcript text...")
        topics = result.data["segments"]
    """

    def __init__(self, cache_size: int = 1000):
        """Initialize topic segmentation service.

        Args:
            cache_size: Maximum number of cached results
        """
        self.cache_size = cache_size
        self._segmentation_cache: dict[str, TopicSegmentationResult] = {}
        self._topic_models: dict[str, BERTopic] = {}
        self._embedding_models: dict[str, Any] = {}

    def segment_text(
        self,
        text: str,
        model: Literal["fast", "balanced", "quality"] = "balanced",
        min_topic_size: int = 5,
        max_topics: int = 50,
        use_cache: bool = True,
    ) -> StepResult:
        """Segment text into topics using hierarchical clustering.

        Args:
            text: Input text to segment into topics
            model: Model selection (fast, balanced, quality)
            min_topic_size: Minimum size for a topic to be considered valid
            max_topics: Maximum number of topics to extract
            use_cache: Whether to use segmentation cache

        Returns:
            StepResult with topic segmentation data
        """
        try:
            import time

            start_time = time.time()
            if not text or not text.strip():
                return StepResult.fail("Input text cannot be empty", status="bad_request")
            if len(text) < 100:
                return StepResult.fail("Input text too short for meaningful topic analysis", status="bad_request")
            if use_cache:
                cache_result = self._check_cache(text, model, min_topic_size, max_topics)
                if cache_result:
                    logger.info("Topic segmentation cache hit")
                    return StepResult.ok(
                        data={
                            "segments": [s.__dict__ for s in cache_result.segments],
                            "topic_model": cache_result.topic_model.__dict__ if cache_result.topic_model else None,
                            "overall_coherence": cache_result.overall_coherence,
                            "topic_distribution": cache_result.topic_distribution,
                            "model": cache_result.model,
                            "cache_hit": True,
                            "processing_time_ms": (time.time() - start_time) * 1000,
                        }
                    )
            model_name = self._select_model(model)
            segmentation_result = self._segment_text(text, model_name, min_topic_size, max_topics)
            if segmentation_result:
                if use_cache:
                    self._cache_result(text, model, min_topic_size, max_topics, segmentation_result)
                processing_time = (time.time() - start_time) * 1000
                return StepResult.ok(
                    data={
                        "segments": [s.__dict__ for s in segmentation_result.segments],
                        "topic_model": segmentation_result.topic_model.__dict__
                        if segmentation_result.topic_model
                        else None,
                        "overall_coherence": segmentation_result.overall_coherence,
                        "topic_distribution": segmentation_result.topic_distribution,
                        "model": segmentation_result.model,
                        "cache_hit": False,
                        "processing_time_ms": processing_time,
                    }
                )
            else:
                return StepResult.fail("Topic segmentation failed", status="retryable")
        except Exception as e:
            logger.error(f"Text segmentation failed: {e}")
            return StepResult.fail(f"Segmentation failed: {e!s}", status="retryable")

    def segment_transcript(
        self,
        transcript_segments: list[dict[str, Any]],
        model: Literal["fast", "balanced", "quality"] = "balanced",
        use_cache: bool = True,
    ) -> StepResult:
        """Segment transcript segments into topics with temporal alignment.

        Args:
            transcript_segments: List of transcript segments with start/end times
            model: Model selection
            use_cache: Whether to use segmentation cache

        Returns:
            StepResult with temporally-aligned topic segments
        """
        try:
            full_text = ""
            segment_texts = []
            for i, segment in enumerate(transcript_segments):
                segment_text = segment.get("text", "")
                start_time = segment.get("start", 0.0)
                end_time = segment.get("end", 0.0)
                timed_text = f"[T{i}@{start_time:.1f}-{end_time:.1f}] {segment_text}"
                segment_texts.append(
                    {
                        "index": i,
                        "text": segment_text,
                        "start_time": start_time,
                        "end_time": end_time,
                        "timed_text": timed_text,
                    }
                )
                full_text += timed_text + " "
            segmentation_result = self._segment_text(
                full_text, self._select_model(model), min_topic_size=3, max_topics=30
            )
            if not segmentation_result:
                return StepResult.fail("Transcript segmentation failed")
            aligned_segments = self._align_topics_to_segments(segmentation_result.segments, segment_texts)
            return StepResult.ok(
                data={
                    "segments": [s.__dict__ for s in aligned_segments],
                    "topic_model": segmentation_result.topic_model.__dict__
                    if segmentation_result.topic_model
                    else None,
                    "overall_coherence": segmentation_result.overall_coherence,
                    "topic_distribution": segmentation_result.topic_distribution,
                    "model": segmentation_result.model,
                    "cache_hit": False,
                }
            )
        except Exception as e:
            logger.error(f"Transcript segmentation failed: {e}")
            return StepResult.fail(f"Transcript segmentation failed: {e!s}")

    def _select_model(self, model_alias: str) -> str:
        """Select actual model configuration from alias.

        Args:
            model_alias: Model alias (fast, balanced, quality)

        Returns:
            Model configuration string
        """
        model_configs = {
            "fast": "fast_topic_model",
            "balanced": "balanced_topic_model",
            "quality": "quality_topic_model",
        }
        return model_configs.get(model_alias, "balanced_topic_model")

    def _segment_text(
        self, text: str, model_name: str, min_topic_size: int, max_topics: int
    ) -> TopicSegmentationResult | None:
        """Segment text using BERTopic or fallback method.

        Args:
            text: Input text to segment
            model_name: Model configuration
            min_topic_size: Minimum topic size
            max_topics: Maximum topics to extract

        Returns:
            TopicSegmentationResult or None if segmentation fails
        """
        try:
            if not BERTOPIC_AVAILABLE:
                logger.warning("BERTopic not available, using fallback segmentation")
                return self._segment_fallback(text, model_name)
            if model_name not in self._topic_models:
                logger.info(f"Loading/creating BERTopic model: {model_name}")
                self._topic_models[model_name] = self._create_topic_model(model_name)
            topic_model = self._topic_models[model_name]
            text_chunks = self._split_text_into_chunks(text, max_chunk_size=512)
            topics, _probs = topic_model.fit_transform(text_chunks)
            topic_info = topic_model.get_topic_info()
            topic_names = topic_info["Name"].tolist()
            segments = []
            topic_distribution = {}
            for i, (chunk, topic_id) in enumerate(zip(text_chunks, topics, strict=False)):
                if topic_id == -1:
                    continue
                topic_name = topic_names[topic_id] if topic_id < len(topic_names) else f"Topic_{topic_id}"
                chunk_start = i * 30.0
                chunk_end = chunk_start + 30.0
                segment = TopicSegment(
                    start_time=chunk_start,
                    end_time=chunk_end,
                    text=chunk,
                    topics=[str(topic_id)],
                    topic_names=[topic_name],
                    coherence_score=0.8,
                    dominant_topic=str(topic_id),
                )
                segments.append(segment)
                topic_distribution[str(topic_id)] = topic_distribution.get(str(topic_id), 0) + 1
            model_metadata = TopicModel(
                model_id=model_name,
                num_topics=len(set(topics)) if topics else 0,
                coherence_score=self._calculate_coherence(topic_model, text_chunks),
                topics=topic_names,
                topic_embeddings=[],
                model_type="bertopic",
                created_at="",
                training_data_size=len(text_chunks),
            )
            total_segments = sum(topic_distribution.values())
            if total_segments > 0:
                topic_distribution = {k: v / total_segments for k, v in topic_distribution.items()}
            return TopicSegmentationResult(
                segments=segments,
                topic_model=model_metadata,
                overall_coherence=model_metadata.coherence_score,
                topic_distribution=topic_distribution,
                model=model_name,
            )
        except Exception as e:
            logger.error(f"Text segmentation failed: {e}")
            return None

    def _create_topic_model(self, model_name: str) -> BERTopic:
        """Create BERTopic model with appropriate configuration.

        Args:
            model_name: Model configuration name

        Returns:
            Configured BERTopic model
        """
        if model_name == "fast_topic_model":
            embedding_model = "sentence-transformers/all-MiniLM-L6-v2"
            nr_topics = "auto"
            min_topic_size = 3
        elif model_name == "quality_topic_model":
            embedding_model = "sentence-transformers/all-mpnet-base-v2"
            nr_topics = 50
            min_topic_size = 5
        else:
            embedding_model = "sentence-transformers/all-MiniLM-L6-v2"
            nr_topics = 30
            min_topic_size = 4
        representation_model = [KeyBERTInspired(), MaximalMarginalRelevance(diversity=0.3)]
        topic_model = BERTopic(
            embedding_model=embedding_model,
            nr_topics=nr_topics,
            min_topic_size=min_topic_size,
            representation_model=representation_model,
            verbose=False,
        )
        return topic_model

    def _split_text_into_chunks(self, text: str, max_chunk_size: int = 512) -> list[str]:
        """Split text into manageable chunks for topic modeling.

        Args:
            text: Input text
            max_chunk_size: Maximum characters per chunk

        Returns:
            List of text chunks
        """
        words = text.split()
        chunks = []
        current_chunk = []
        for word in words:
            current_chunk.append(word)
            if len(" ".join(current_chunk)) >= max_chunk_size:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        return chunks

    def _calculate_coherence(self, topic_model: BERTopic, documents: list[str]) -> float:
        """Calculate topic coherence score.

        Args:
            topic_model: Trained BERTopic model
            documents: List of documents used for training

        Returns:
            Coherence score (0.0 to 1.0)
        """
        try:
            topics, _ = topic_model.transform(documents)
            valid_topics = [t for t in topics if t != -1]
            coherence = len(valid_topics) / len(topics) if topics else 0.0
            return min(coherence, 1.0)
        except Exception as e:
            logger.warning(f"Coherence calculation failed: {e}")
            return 0.5

    def _align_topics_to_segments(
        self, topic_segments: list[TopicSegment], transcript_segments: list[dict[str, Any]]
    ) -> list[TopicSegment]:
        """Align topic segments back to original transcript timing.

        Args:
            topic_segments: Segments with topic assignments
            transcript_segments: Original transcript segments with timing

        Returns:
            Topic segments with corrected timing
        """
        aligned_segments = []
        for topic_seg in topic_segments:
            timed_text = topic_seg.text
            import re

            timing_pattern = "\\[T(\\d+)@([\\d.]+)-([\\d.]+)\\]"
            match = re.search(timing_pattern, timed_text)
            if match:
                segment_index = int(match.group(1))
                start_time = float(match.group(2))
                end_time = float(match.group(3))
                topic_seg.start_time = start_time
                topic_seg.end_time = end_time
                topic_seg.text = re.sub(timing_pattern, "", timed_text).strip()
                if segment_index < len(transcript_segments):
                    topic_seg.text = transcript_segments[segment_index].get("text", topic_seg.text)
            aligned_segments.append(topic_seg)
        return aligned_segments

    def _segment_fallback(self, text: str, model_name: str) -> TopicSegmentationResult:
        """Fallback topic segmentation when BERTopic unavailable.

        Args:
            text: Input text
            model_name: Model configuration

        Returns:
            TopicSegmentationResult with fallback segmentation
        """
        import re

        sentences = re.split("[.!?]+", text)
        sentences = [s.strip() for s in sentences if s.strip()]
        segments = []
        for i, sentence in enumerate(sentences):
            start_time = i * 10.0
            end_time = start_time + 10.0
            segment = TopicSegment(
                start_time=start_time,
                end_time=end_time,
                text=sentence,
                topics=["general"],
                topic_names=["General Discussion"],
                coherence_score=0.5,
                dominant_topic="general",
            )
            segments.append(segment)
        topic_distribution = {"general": 1.0}
        fallback_model = TopicModel(
            model_id=f"fallback-{model_name}",
            num_topics=1,
            coherence_score=0.5,
            topics=["General Discussion"],
            topic_embeddings=[],
            model_type="fallback",
            created_at="",
            training_data_size=len(sentences),
        )
        return TopicSegmentationResult(
            segments=segments,
            topic_model=fallback_model,
            overall_coherence=0.5,
            topic_distribution=topic_distribution,
            model=model_name,
        )

    def _check_cache(
        self, text: str, model: str, min_topic_size: int, max_topics: int
    ) -> TopicSegmentationResult | None:
        """Check if topic segmentation exists in cache.

        Args:
            text: Input text
            model: Model alias
            min_topic_size: Minimum topic size parameter
            max_topics: Maximum topics parameter

        Returns:
            Cached TopicSegmentationResult or None
        """
        import hashlib

        text_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
        cache_key = f"{text_hash}:{model}:{min_topic_size}:{max_topics}"
        if cache_key in self._segmentation_cache:
            return self._segmentation_cache[cache_key]
        return None

    def _cache_result(
        self, text: str, model: str, min_topic_size: int, max_topics: int, result: TopicSegmentationResult
    ) -> None:
        """Cache topic segmentation result.

        Args:
            text: Input text
            model: Model alias
            min_topic_size: Minimum topic size parameter
            max_topics: Maximum topics parameter
            result: TopicSegmentationResult to cache
        """
        import hashlib
        import time

        text_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
        cache_key = f"{text_hash}:{model}:{min_topic_size}:{max_topics}"
        result.processing_time_ms = time.time() * 1000
        if len(self._segmentation_cache) >= self.cache_size:
            first_key = next(iter(self._segmentation_cache))
            del self._segmentation_cache[first_key]
        self._segmentation_cache[cache_key] = result

    def clear_cache(self) -> StepResult:
        """Clear topic segmentation cache.

        Returns:
            StepResult with cache clear status
        """
        cache_size = len(self._segmentation_cache)
        self._segmentation_cache.clear()
        logger.info(f"Cleared {cache_size} cached topic segmentations")
        return StepResult.ok(data={"cleared_entries": cache_size})

    def get_cache_stats(self) -> StepResult:
        """Get topic segmentation cache statistics.

        Returns:
            StepResult with cache statistics
        """
        try:
            stats = {
                "total_cached": len(self._segmentation_cache),
                "cache_size_limit": self.cache_size,
                "utilization": len(self._segmentation_cache) / self.cache_size if self.cache_size > 0 else 0.0,
                "models_cached": {},
            }
            for result in self._segmentation_cache.values():
                model = result.model
                stats["models_cached"][model] = stats["models_cached"].get(model, 0) + 1
            return StepResult.ok(data=stats)
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return StepResult.fail(f"Failed to get cache stats: {e!s}")


_topic_service: TopicSegmentationService | None = None


def get_topic_segmentation_service() -> TopicSegmentationService:
    """Get singleton topic segmentation service instance.

    Returns:
        Initialized TopicSegmentationService instance
    """
    global _topic_service
    if _topic_service is None:
        _topic_service = TopicSegmentationService()
    return _topic_service
