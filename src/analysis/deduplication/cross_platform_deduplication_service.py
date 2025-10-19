"""Cross-Platform Deduplication Service for Creator Intelligence.

This module provides deduplication capabilities across multiple platforms using:
- Perceptual hashing for images (imagehash library)
- Semantic hashing for text (sentence embeddings)
- Platform-specific deduplication strategies

Features:
- Image deduplication using perceptual hashing
- Text deduplication using semantic similarity
- Cross-platform duplicate cluster identification
- Integration with content ingestion pipeline

Dependencies:
- imagehash: For perceptual image hashing
- PIL: For image processing
- numpy: For similarity calculations
- Optional: Custom embedding models for text deduplication
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from typing import Any, Literal

from ultimate_discord_intelligence_bot.step_result import StepResult

logger = logging.getLogger(__name__)

# Try to import imagehash (optional dependency)
try:
    import imagehash
    from PIL import Image

    IMAGEHASH_AVAILABLE = True
except ImportError:
    IMAGEHASH_AVAILABLE = False
    logger.warning("imagehash not available, image deduplication disabled")


@dataclass
class DuplicateCluster:
    """A cluster of duplicate content items."""

    cluster_id: str
    platform_items: dict[str, list[dict[str, Any]]]  # platform -> items
    similarity_scores: dict[str, float]  # item_id -> similarity_score
    representative_item: dict[str, Any]  # Best representative of the cluster
    confidence: float  # 0.0 to 1.0


@dataclass
class DeduplicationResult:
    """Result of deduplication analysis."""

    duplicate_clusters: list[DuplicateCluster]
    total_items_processed: int
    duplicates_found: int
    unique_items: int
    deduplication_method: str
    processing_time_ms: float = 0.0


class CrossPlatformDeduplicationService:
    """Service for detecting duplicate content across platforms.

    Usage:
        service = CrossPlatformDeduplicationService()
        result = service.find_duplicates(image_paths, text_items)
        clusters = result.data["duplicate_clusters"]
    """

    def __init__(self, cache_size: int = 1000):
        """Initialize deduplication service.

        Args:
            cache_size: Maximum number of cached results
        """
        self.cache_size = cache_size
        self._deduplication_cache: dict[str, DeduplicationResult] = {}

        # Hash storage for deduplication
        self._image_hashes: dict[str, str] = {}  # file_path -> hash
        self._text_hashes: dict[str, list[float]] = {}  # text_hash -> embedding

    def find_duplicates(
        self,
        image_paths: list[str] | None = None,
        text_items: list[dict[str, Any]] | None = None,
        platforms: list[str] | None = None,
        similarity_threshold: float = 0.8,
        model: Literal["fast", "balanced", "quality"] = "balanced",
        use_cache: bool = True,
    ) -> StepResult:
        """Find duplicate content across platforms.

        Args:
            image_paths: List of image file paths to check
            text_items: List of text items with metadata
            platforms: List of platform names for grouping
            similarity_threshold: Threshold for duplicate detection
            model: Model selection
            use_cache: Whether to use deduplication cache

        Returns:
            StepResult with duplicate cluster analysis
        """
        try:
            import time

            start_time = time.time()

            # Validate inputs
            if not image_paths and not text_items:
                return StepResult.fail(
                    "Either image_paths or text_items must be provided",
                    status="bad_request",
                )

            # Check cache first
            if use_cache:
                cache_result = self._check_cache(
                    image_paths, text_items, platforms, similarity_threshold, model
                )
                if cache_result:
                    logger.info("Deduplication cache hit")
                    return StepResult.ok(
                        data={
                            "duplicate_clusters": [
                                c.__dict__ for c in cache_result.duplicate_clusters
                            ],
                            "total_items_processed": cache_result.total_items_processed,
                            "duplicates_found": cache_result.duplicates_found,
                            "unique_items": cache_result.unique_items,
                            "deduplication_method": cache_result.deduplication_method,
                            "cache_hit": True,
                            "processing_time_ms": (time.time() - start_time) * 1000,
                        }
                    )

            # Perform deduplication
            model_name = self._select_model(model)
            deduplication_result = self._find_duplicates(
                image_paths, text_items, platforms, similarity_threshold, model_name
            )

            if deduplication_result:
                # Cache result
                if use_cache:
                    self._cache_result(
                        image_paths,
                        text_items,
                        platforms,
                        similarity_threshold,
                        model,
                        deduplication_result,
                    )

                processing_time = (time.time() - start_time) * 1000

                return StepResult.ok(
                    data={
                        "duplicate_clusters": [
                            c.__dict__ for c in deduplication_result.duplicate_clusters
                        ],
                        "total_items_processed": deduplication_result.total_items_processed,
                        "duplicates_found": deduplication_result.duplicates_found,
                        "unique_items": deduplication_result.unique_items,
                        "deduplication_method": deduplication_result.deduplication_method,
                        "cache_hit": False,
                        "processing_time_ms": processing_time,
                    }
                )
            else:
                return StepResult.fail("Deduplication failed", status="retryable")

        except Exception as e:
            logger.error(f"Deduplication failed: {e}")
            return StepResult.fail(
                f"Deduplication failed: {str(e)}", status="retryable"
            )

    def deduplicate_content_stream(
        self,
        content_items: list[dict[str, Any]],
        similarity_threshold: float = 0.8,
        model: Literal["fast", "balanced", "quality"] = "balanced",
    ) -> StepResult:
        """Deduplicate a stream of content items in real-time.

        Args:
            content_items: List of content items with metadata
            similarity_threshold: Threshold for duplicate detection
            model: Model selection

        Returns:
            StepResult with deduplication results
        """
        try:
            # Process items and track duplicates
            processed_items = []
            seen_hashes = set()

            for item in content_items:
                item_id = item.get("id", str(hash(str(item))))
                content_type = item.get("content_type", "unknown")

                # Generate appropriate hash based on content type
                if content_type == "image" and "image_path" in item:
                    item_hash = self._get_image_hash(item["image_path"])
                elif content_type == "text" and "text" in item:
                    item_hash = self._get_text_hash(item["text"])
                else:
                    # Fallback hash
                    item_hash = hashlib.sha256(str(item).encode()).hexdigest()

                # Check for duplicates
                is_duplicate = False
                for existing_hash in seen_hashes:
                    similarity = self._calculate_similarity(
                        existing_hash, item_hash, content_type
                    )
                    if similarity >= similarity_threshold:
                        is_duplicate = True
                        break

                if is_duplicate:
                    # Add to existing cluster or create new one
                    # For simplicity, we'll mark as duplicate without detailed clustering
                    item["is_duplicate"] = True
                    item["duplicate_of"] = item_id
                else:
                    seen_hashes.add(item_hash)
                    item["is_duplicate"] = False
                    item["item_hash"] = item_hash

                processed_items.append(item)

            # Calculate statistics
            total_items = len(processed_items)
            duplicates = sum(1 for item in processed_items if item.get("is_duplicate"))
            unique_items = total_items - duplicates

            return StepResult.ok(
                data={
                    "processed_items": processed_items,
                    "total_items_processed": total_items,
                    "duplicates_found": duplicates,
                    "unique_items": unique_items,
                    "deduplication_method": "streaming",
                    "similarity_threshold": similarity_threshold,
                }
            )

        except Exception as e:
            logger.error(f"Stream deduplication failed: {e}")
            return StepResult.fail(f"Stream deduplication failed: {str(e)}")

    def _select_model(self, model_alias: str) -> str:
        """Select actual model configuration from alias.

        Args:
            model_alias: Model alias (fast, balanced, quality)

        Returns:
            Model configuration string
        """
        model_configs = {
            "fast": "fast_deduplication",
            "balanced": "balanced_deduplication",
            "quality": "quality_deduplication",
        }

        return model_configs.get(model_alias, "balanced_deduplication")

    def _find_duplicates(
        self,
        image_paths: list[str] | None,
        text_items: list[dict[str, Any]] | None,
        platforms: list[str] | None,
        similarity_threshold: float,
        model_name: str,
    ) -> DeduplicationResult | None:
        """Find duplicates using appropriate methods for each content type.

        Args:
            image_paths: List of image file paths
            text_items: List of text items with metadata
            platforms: List of platform names
            similarity_threshold: Threshold for duplicate detection
            model_name: Model configuration

        Returns:
            DeduplicationResult or None if deduplication fails
        """
        try:
            all_clusters = []

            # Process images if provided
            if image_paths:
                image_clusters = self._find_image_duplicates(
                    image_paths, similarity_threshold
                )
                all_clusters.extend(image_clusters)

            # Process text if provided
            if text_items:
                text_clusters = self._find_text_duplicates(
                    text_items, similarity_threshold
                )
                all_clusters.extend(text_clusters)

            # Calculate statistics
            total_items = (len(image_paths) if image_paths else 0) + (
                len(text_items) if text_items else 0
            )
            duplicates_found = sum(
                len(cluster.platform_items) for cluster in all_clusters
            ) - len(all_clusters)

            return DeduplicationResult(
                duplicate_clusters=all_clusters,
                total_items_processed=total_items,
                duplicates_found=duplicates_found,
                unique_items=total_items - duplicates_found,
                deduplication_method=model_name,
            )

        except Exception as e:
            logger.error(f"Deduplication failed: {e}")
            return None

    def _find_image_duplicates(
        self, image_paths: list[str], threshold: float
    ) -> list[DuplicateCluster]:
        """Find duplicate images using perceptual hashing.

        Args:
            image_paths: List of image file paths
            threshold: Similarity threshold for duplicates

        Returns:
            List of duplicate clusters
        """
        if not IMAGEHASH_AVAILABLE:
            logger.warning("imagehash not available, skipping image deduplication")
            return []

        clusters = []
        processed_hashes = {}

        for image_path in image_paths:
            try:
                # Generate perceptual hash
                image_hash = self._get_image_hash(image_path)

                # Check against existing hashes
                found_cluster = False
                for cluster_id, existing_hash in processed_hashes.items():
                    similarity = self._calculate_image_similarity(
                        existing_hash, image_hash
                    )

                    if similarity >= threshold:
                        # Add to existing cluster
                        clusters[cluster_id].platform_items["images"].append(
                            {
                                "path": image_path,
                                "hash": image_hash,
                                "similarity": similarity,
                            }
                        )
                        clusters[cluster_id].similarity_scores[image_path] = similarity
                        found_cluster = True
                        break

                if not found_cluster:
                    # Create new cluster
                    cluster_id = f"image_cluster_{len(clusters)}"
                    new_cluster = DuplicateCluster(
                        cluster_id=cluster_id,
                        platform_items={
                            "images": [{"path": image_path, "hash": image_hash}]
                        },
                        similarity_scores={image_path: 1.0},
                        representative_item={"path": image_path, "hash": image_hash},
                        confidence=1.0,
                    )
                    clusters.append(new_cluster)
                    processed_hashes[cluster_id] = image_hash

            except Exception as e:
                logger.warning(f"Failed to process image {image_path}: {e}")

        return clusters

    def _find_text_duplicates(
        self, text_items: list[dict[str, Any]], threshold: float
    ) -> list[DuplicateCluster]:
        """Find duplicate text using semantic similarity.

        Args:
            text_items: List of text items with metadata
            threshold: Similarity threshold for duplicates

        Returns:
            List of duplicate clusters
        """
        clusters = []

        for i, item1 in enumerate(text_items):
            item1_text = item1.get("text", "")
            item1_id = item1.get("id", f"item_{i}")

            if not item1_text:
                continue

            # Check against other items
            for j, item2 in enumerate(text_items[i + 1 :], i + 1):
                item2_text = item2.get("text", "")
                item2_id = item2.get("id", f"item_{j}")

                if not item2_text:
                    continue

                # Calculate semantic similarity
                similarity = self._calculate_text_similarity(item1_text, item2_text)

                if similarity >= threshold:
                    # Create or add to cluster
                    cluster_id = f"text_cluster_{len(clusters)}"
                    cluster = DuplicateCluster(
                        cluster_id=cluster_id,
                        platform_items={"text": [item1, item2]},
                        similarity_scores={
                            item1_id: similarity,
                            item2_id: similarity,
                        },
                        representative_item=item1,  # Use first item as representative
                        confidence=similarity,
                    )
                    clusters.append(cluster)

        return clusters

    def _get_image_hash(self, image_path: str) -> str:
        """Generate perceptual hash for image.

        Args:
            image_path: Path to image file

        Returns:
            Perceptual hash as string
        """
        if not IMAGEHASH_AVAILABLE:
            # Fallback hash
            return hashlib.sha256(image_path.encode()).hexdigest()

        try:
            image = Image.open(image_path)
            # Use average hash for good balance of speed/accuracy
            hash_value = imagehash.average_hash(image)
            return str(hash_value)

        except Exception as e:
            logger.warning(f"Failed to generate image hash for {image_path}: {e}")
            return hashlib.sha256(image_path.encode()).hexdigest()

    def _get_text_hash(self, text: str) -> list[float]:
        """Generate semantic embedding for text.

        Args:
            text: Input text

        Returns:
            List of embedding values
        """
        # Simple fallback: use hash of text as embedding
        # In production, would use actual sentence embeddings
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        hash_int = int(text_hash, 16)

        # Generate pseudo-embedding (768 dimensions like sentence-transformers)
        embedding = []
        for i in range(768):
            # Use hash bits to generate pseudo-random but deterministic values
            bit_value = (hash_int >> (i % 64)) & 1
            embedding.append(float(bit_value) * 2 - 1)  # Convert to -1/+1 range

        return embedding

    def _calculate_image_similarity(self, hash1: str, hash2: str) -> float:
        """Calculate similarity between two image hashes.

        Args:
            hash1: First image hash
            hash2: Second image hash

        Returns:
            Similarity score (0.0 to 1.0)
        """
        if not IMAGEHASH_AVAILABLE:
            # Simple string similarity fallback
            return 1.0 if hash1 == hash2 else 0.0

        try:
            # Convert string hashes back to hash objects
            hash_obj1 = imagehash.hex_to_hash(hash1)
            hash_obj2 = imagehash.hex_to_hash(hash2)

            # Calculate hamming distance and convert to similarity
            distance = hash_obj1 - hash_obj2
            max_distance = 64  # For 8x8 hash

            similarity = 1.0 - (distance / max_distance)
            return max(0.0, similarity)

        except Exception as e:
            logger.warning(f"Failed to calculate image similarity: {e}")
            return 0.0

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score (0.0 to 1.0)
        """
        # Simple fallback: use character-level similarity
        # In production, would use actual semantic embeddings

        if text1 == text2:
            return 1.0

        # Calculate Jaccard similarity of character n-grams
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

    def _calculate_similarity(self, hash1: str, hash2: str, content_type: str) -> float:
        """Calculate similarity between two content hashes.

        Args:
            hash1: First hash
            hash2: Second hash
            content_type: Type of content (image, text)

        Returns:
            Similarity score (0.0 to 1.0)
        """
        if content_type == "image":
            return self._calculate_image_similarity(hash1, hash2)
        elif content_type == "text":
            # For text, we'd need to compare embeddings
            # For now, use simple string comparison
            return 1.0 if hash1 == hash2 else 0.0
        else:
            return 0.0

    def _check_cache(
        self,
        image_paths: list[str] | None,
        text_items: list[dict[str, Any]] | None,
        platforms: list[str] | None,
        similarity_threshold: float,
        model: str,
    ) -> DeduplicationResult | None:
        """Check if deduplication exists in cache.

        Args:
            image_paths: Image file paths
            text_items: Text items
            platforms: Platform names
            similarity_threshold: Similarity threshold
            model: Model alias

        Returns:
            Cached DeduplicationResult or None
        """
        import hashlib

        # Create cache key from inputs
        combined = f"{str(image_paths)}:{str(text_items)}:{str(platforms)}:{similarity_threshold}:{model}"
        cache_key = hashlib.sha256(combined.encode()).hexdigest()

        if cache_key in self._deduplication_cache:
            return self._deduplication_cache[cache_key]

        return None

    def _cache_result(
        self,
        image_paths: list[str] | None,
        text_items: list[dict[str, Any]] | None,
        platforms: list[str] | None,
        similarity_threshold: float,
        model: str,
        result: DeduplicationResult,
    ) -> None:
        """Cache deduplication result.

        Args:
            image_paths: Image file paths
            text_items: Text items
            platforms: Platform names
            similarity_threshold: Similarity threshold
            model: Model alias
            result: DeduplicationResult to cache
        """
        import hashlib
        import time

        # Create cache key
        combined = f"{str(image_paths)}:{str(text_items)}:{str(platforms)}:{similarity_threshold}:{model}"
        cache_key = hashlib.sha256(combined.encode()).hexdigest()

        # Add processing timestamp
        result.processing_time_ms = time.time() * 1000

        # Evict old entries if cache is full
        if len(self._deduplication_cache) >= self.cache_size:
            # Simple FIFO eviction - remove first key
            first_key = next(iter(self._deduplication_cache))
            del self._deduplication_cache[first_key]

        self._deduplication_cache[cache_key] = result

    def clear_cache(self) -> StepResult:
        """Clear deduplication cache.

        Returns:
            StepResult with cache clear status
        """
        cache_size = len(self._deduplication_cache)
        self._deduplication_cache.clear()

        logger.info(f"Cleared {cache_size} cached deduplication results")

        return StepResult.ok(data={"cleared_entries": cache_size})

    def get_cache_stats(self) -> StepResult:
        """Get deduplication cache statistics.

        Returns:
            StepResult with cache statistics
        """
        try:
            stats = {
                "total_cached": len(self._deduplication_cache),
                "cache_size_limit": self.cache_size,
                "utilization": len(self._deduplication_cache) / self.cache_size
                if self.cache_size > 0
                else 0.0,
                "models_cached": {},
            }

            # Count entries per model
            for result in self._deduplication_cache.values():
                model = result.deduplication_method
                stats["models_cached"][model] = stats["models_cached"].get(model, 0) + 1

            return StepResult.ok(data=stats)

        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return StepResult.fail(f"Failed to get cache stats: {str(e)}")


# Singleton instance
_deduplication_service: CrossPlatformDeduplicationService | None = None


def get_cross_platform_deduplication_service() -> CrossPlatformDeduplicationService:
    """Get singleton deduplication service instance.

    Returns:
        Initialized CrossPlatformDeduplicationService instance
    """
    global _deduplication_service

    if _deduplication_service is None:
        _deduplication_service = CrossPlatformDeduplicationService()

    return _deduplication_service
