"""
Cross-tenant similarity prevention system for multi-tenant memory isolation.

This module provides sophisticated cross-tenant similarity detection and prevention
to ensure proper data isolation and privacy in multi-tenant environments.
"""

from __future__ import annotations

import hashlib
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class SimilarityDetectionMethod(Enum):
    """Methods for detecting cross-tenant similarity."""

    COSINE_SIMILARITY = "cosine_similarity"
    EUCLIDEAN_DISTANCE = "euclidean_distance"
    MANHATTAN_DISTANCE = "manhattan_distance"
    JACCARD_SIMILARITY = "jaccard_similarity"
    EMBEDDING_SIMILARITY = "embedding_similarity"
    CONTENT_HASH = "content_hash"


class IsolationStrategy(Enum):
    """Strategies for preventing cross-tenant similarity."""

    NAMESPACE_ISOLATION = "namespace_isolation"  # Separate namespaces
    EMBEDDING_PERTURBATION = "embedding_perturbation"  # Add noise to embeddings
    SIMILARITY_THRESHOLD = "similarity_threshold"  # Block similar content
    CONTENT_FILTERING = "content_filtering"  # Filter similar content
    HYBRID_ISOLATION = "hybrid_isolation"  # Combination of strategies


@dataclass
class CrossTenantConfig:
    """Configuration for cross-tenant similarity prevention."""

    # Similarity detection
    similarity_threshold: float = 0.85  # Threshold for cross-tenant similarity
    detection_methods: list[SimilarityDetectionMethod] = field(
        default_factory=lambda: [
            SimilarityDetectionMethod.COSINE_SIMILARITY,
            SimilarityDetectionMethod.EMBEDDING_SIMILARITY,
        ]
    )

    # Isolation strategies
    primary_strategy: IsolationStrategy = IsolationStrategy.HYBRID_ISOLATION
    enable_namespace_isolation: bool = True
    enable_embedding_perturbation: bool = True
    enable_content_filtering: bool = True

    # Perturbation settings
    perturbation_noise_level: float = 0.1  # Noise level for embedding perturbation
    perturbation_seed: str = "tenant_isolation"  # Seed for consistent perturbation

    # Content filtering
    content_similarity_threshold: float = 0.8  # Content similarity threshold
    enable_semantic_filtering: bool = True
    semantic_similarity_threshold: float = 0.75

    # Performance settings
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600  # 1 hour
    batch_size: int = 100

    # Monitoring
    enable_metrics: bool = True
    log_violations: bool = True
    alert_threshold: float = 0.9  # Alert when similarity exceeds this threshold


@dataclass
class SimilarityViolation:
    """Represents a cross-tenant similarity violation."""

    tenant1: str
    tenant2: str
    similarity_score: float
    detection_method: SimilarityDetectionMethod
    content_ids: tuple[str, str]
    timestamp: float
    severity: str  # "low", "medium", "high", "critical"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()

    @property
    def is_critical(self) -> bool:
        """Check if violation is critical."""
        return self.similarity_score > 0.95 or self.severity == "critical"

    @property
    def is_high_risk(self) -> bool:
        """Check if violation is high risk."""
        return self.similarity_score > 0.9 or self.severity in ["high", "critical"]


@dataclass
class TenantIsolationMetrics:
    """Metrics for tenant isolation monitoring."""

    # Violation tracking
    total_violations: int = 0
    violations_by_tenant: dict[str, int] = field(default_factory=dict)
    violations_by_method: dict[SimilarityDetectionMethod, int] = field(default_factory=dict)
    violations_by_severity: dict[str, int] = field(default_factory=dict)

    # Performance metrics
    total_checks: int = 0
    average_check_time: float = 0.0
    cache_hit_rate: float = 0.0

    # Prevention effectiveness
    prevented_violations: int = 0
    blocked_operations: int = 0
    isolation_effectiveness: float = 0.0

    # Recent activity
    recent_violations: list[SimilarityViolation] = field(default_factory=list)
    violation_trend: list[tuple[float, int]] = field(default_factory=list)  # (timestamp, count)


class CrossTenantSimilarityDetector:
    """
    Cross-tenant similarity detector and prevention system.

    Provides comprehensive detection and prevention of cross-tenant similarity
    violations to ensure proper data isolation and privacy.
    """

    def __init__(self, config: CrossTenantConfig | None = None):
        """Initialize cross-tenant similarity detector."""
        self.config = config or CrossTenantConfig()
        self.metrics = TenantIsolationMetrics()

        # Tenant data storage
        self.tenant_embeddings: dict[str, dict[str, np.ndarray]] = defaultdict(dict)
        self.tenant_content: dict[str, dict[str, Any]] = defaultdict(dict)
        self.tenant_namespaces: dict[str, str] = {}

        # Similarity cache
        self.similarity_cache: dict[tuple[str, str, str], float] = {}  # (tenant1, tenant2, method)
        self.violation_cache: set[tuple[str, str]] = set()  # Cached violations

        # Perturbation seeds for consistent noise
        self.perturbation_seeds: dict[str, int] = {}

        logger.info(f"Cross-tenant similarity detector initialized with config: {self.config}")

    async def add_tenant_content(
        self,
        tenant_id: str,
        content_id: str,
        embedding: np.ndarray,
        content: Any,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """
        Add content for a tenant with cross-tenant similarity checking.

        Returns True if content was added, False if blocked due to similarity.
        """
        start_time = time.time()

        try:
            # Check for cross-tenant similarity
            violation = await self.check_cross_tenant_similarity(tenant_id, embedding, content)

            if violation and self._should_block_content(violation):
                self.metrics.blocked_operations += 1
                if self.config.log_violations:
                    logger.warning(
                        f"Blocked content {content_id} for tenant {tenant_id} due to "
                        f"cross-tenant similarity with tenant {violation.tenant2} "
                        f"(similarity: {violation.similarity_score:.3f})"
                    )
                return False

            # Add content with isolation measures
            await self._add_content_with_isolation(tenant_id, content_id, embedding, content, metadata)

            # Update metrics
            self.metrics.total_checks += 1
            check_time = time.time() - start_time
            self.metrics.average_check_time = (
                self.metrics.average_check_time * (self.metrics.total_checks - 1) + check_time
            ) / self.metrics.total_checks

            return True

        except Exception as e:
            logger.error(f"Error adding tenant content: {e}")
            return False

    async def check_cross_tenant_similarity(
        self, tenant_id: str, embedding: np.ndarray, content: Any
    ) -> SimilarityViolation | None:
        """Check for cross-tenant similarity violations."""
        # Check cache first
        if self.config.enable_caching:
            cached_violation = self._get_cached_violation(tenant_id, embedding)
            if cached_violation:
                self.metrics.cache_hit_rate = (
                    self.metrics.cache_hit_rate * (self.metrics.total_checks - 1) + 1
                ) / self.metrics.total_checks
                return cached_violation

        # Check against all other tenants
        for other_tenant_id, other_embeddings in self.tenant_embeddings.items():
            if other_tenant_id == tenant_id:
                continue

            for other_content_id, other_embedding in other_embeddings.items():
                # Calculate similarity using multiple methods
                similarities = await self._calculate_similarities(embedding, other_embedding, content, other_content_id)

                # Check if any similarity exceeds threshold
                for method, similarity in similarities.items():
                    if similarity >= self.config.similarity_threshold:
                        violation = SimilarityViolation(
                            tenant1=tenant_id,
                            tenant2=other_tenant_id,
                            similarity_score=similarity,
                            detection_method=method,
                            content_ids=(content_id, other_content_id),
                            timestamp=time.time(),
                            severity=self._calculate_severity(similarity),
                            metadata={"similarities": similarities},
                        )

                        # Record violation
                        self._record_violation(violation)

                        # Cache violation
                        if self.config.enable_caching:
                            self._cache_violation(tenant_id, embedding, violation)

                        return violation

        # Update cache miss rate
        self.metrics.cache_hit_rate = (
            self.metrics.cache_hit_rate * (self.metrics.total_checks - 1)
        ) / self.metrics.total_checks

        return None

    async def _calculate_similarities(
        self, embedding1: np.ndarray, embedding2: np.ndarray, content1: Any, content2_id: str
    ) -> dict[SimilarityDetectionMethod, float]:
        """Calculate similarities using multiple methods."""
        similarities = {}

        for method in self.config.detection_methods:
            if method == SimilarityDetectionMethod.COSINE_SIMILARITY:
                similarities[method] = self._cosine_similarity(embedding1, embedding2)
            elif method == SimilarityDetectionMethod.EUCLIDEAN_DISTANCE:
                similarities[method] = self._euclidean_similarity(embedding1, embedding2)
            elif method == SimilarityDetectionMethod.EMBEDDING_SIMILARITY:
                similarities[method] = self._embedding_similarity(embedding1, embedding2)
            elif method == SimilarityDetectionMethod.CONTENT_HASH:
                similarities[method] = self._content_hash_similarity(content1, content2_id)

        return similarities

    def _cosine_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity between embeddings."""
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(np.dot(embedding1, embedding2) / (norm1 * norm2))

    def _euclidean_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate Euclidean distance similarity (1 - normalized_distance)."""
        distance = np.linalg.norm(embedding1 - embedding2)
        max_distance = np.linalg.norm(embedding1) + np.linalg.norm(embedding2)

        if max_distance == 0:
            return 1.0

        return float(1.0 - (distance / max_distance))

    def _embedding_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate comprehensive embedding similarity."""
        # Combine multiple similarity measures
        cosine_sim = self._cosine_similarity(embedding1, embedding2)
        euclidean_sim = self._euclidean_similarity(embedding1, embedding2)

        # Weighted combination
        return 0.7 * cosine_sim + 0.3 * euclidean_sim

    def _content_hash_similarity(self, content1: Any, content2_id: str) -> float:
        """Calculate content hash similarity."""
        # Get other tenant's content
        content2 = self._get_content_by_id(content2_id)
        if content2 is None:
            return 0.0

        # Simple content similarity based on string representation
        str1 = str(content1).lower()
        str2 = str(content2).lower()

        # Calculate Jaccard similarity of character n-grams
        ngrams1 = set(str1[i : i + 3] for i in range(len(str1) - 2))
        ngrams2 = set(str2[i : i + 3] for i in range(len(str2) - 2))

        if not ngrams1 and not ngrams2:
            return 1.0
        if not ngrams1 or not ngrams2:
            return 0.0

        intersection = len(ngrams1.intersection(ngrams2))
        union = len(ngrams1.union(ngrams2))

        return intersection / union if union > 0 else 0.0

    async def _add_content_with_isolation(
        self, tenant_id: str, content_id: str, embedding: np.ndarray, content: Any, metadata: dict[str, Any] | None
    ) -> None:
        """Add content with isolation measures applied."""
        # Apply isolation strategy
        if self.config.primary_strategy == IsolationStrategy.NAMESPACE_ISOLATION:
            embedding = self._apply_namespace_isolation(tenant_id, embedding)
        elif self.config.primary_strategy == IsolationStrategy.EMBEDDING_PERTURBATION:
            embedding = self._apply_embedding_perturbation(tenant_id, embedding)
        elif self.config.primary_strategy == IsolationStrategy.HYBRID_ISOLATION:
            embedding = self._apply_hybrid_isolation(tenant_id, embedding)

        # Store content
        self.tenant_embeddings[tenant_id][content_id] = embedding
        self.tenant_content[tenant_id][content_id] = content

        # Ensure namespace isolation
        if self.config.enable_namespace_isolation:
            self.tenant_namespaces[tenant_id] = self._get_tenant_namespace(tenant_id)

    def _apply_namespace_isolation(self, tenant_id: str, embedding: np.ndarray) -> np.ndarray:
        """Apply namespace isolation to embedding."""
        # Create tenant-specific namespace vector
        namespace_vector = self._generate_namespace_vector(tenant_id)

        # Project embedding into tenant namespace
        isolated_embedding = embedding + namespace_vector * 0.1

        # Normalize
        norm = np.linalg.norm(isolated_embedding)
        if norm > 0:
            isolated_embedding = isolated_embedding / norm

        return isolated_embedding

    def _apply_embedding_perturbation(self, tenant_id: str, embedding: np.ndarray) -> np.ndarray:
        """Apply controlled perturbation to embedding."""
        # Generate tenant-specific noise
        noise = self._generate_tenant_noise(tenant_id, embedding.shape)

        # Apply perturbation
        perturbed_embedding = embedding + noise * self.config.perturbation_noise_level

        # Normalize
        norm = np.linalg.norm(perturbed_embedding)
        if norm > 0:
            perturbed_embedding = perturbed_embedding / norm

        return perturbed_embedding

    def _apply_hybrid_isolation(self, tenant_id: str, embedding: np.ndarray) -> np.ndarray:
        """Apply hybrid isolation combining multiple strategies."""
        # Apply namespace isolation
        isolated = self._apply_namespace_isolation(tenant_id, embedding)

        # Apply light perturbation
        perturbed = self._apply_embedding_perturbation(tenant_id, isolated)

        return perturbed

    def _generate_namespace_vector(self, tenant_id: str) -> np.ndarray:
        """Generate tenant-specific namespace vector."""
        # Use tenant ID as seed for consistent namespace
        seed = hash(tenant_id + self.config.perturbation_seed) % 2**32
        np.random.seed(seed)

        # Generate random unit vector
        vector = np.random.normal(0, 1, 1536)  # Assume standard embedding dimension
        return vector / np.linalg.norm(vector)

    def _generate_tenant_noise(self, tenant_id: str, shape: tuple[int, ...]) -> np.ndarray:
        """Generate tenant-specific noise."""
        # Use tenant ID as seed for consistent noise
        seed = hash(tenant_id + self.config.perturbation_seed) % 2**32
        np.random.seed(seed)

        # Generate Gaussian noise
        return np.random.normal(0, 1, shape)

    def _get_tenant_namespace(self, tenant_id: str) -> str:
        """Get tenant namespace identifier."""
        return f"tenant_{hash(tenant_id) % 10000:04d}"

    def _should_block_content(self, violation: SimilarityViolation) -> bool:
        """Determine if content should be blocked based on violation."""
        if violation.is_critical:
            return True

        if violation.similarity_score > self.config.alert_threshold:
            return True

        # Additional blocking logic based on strategy
        if self.config.primary_strategy == IsolationStrategy.SIMILARITY_THRESHOLD:
            return violation.similarity_score >= self.config.similarity_threshold

        return False

    def _calculate_severity(self, similarity_score: float) -> str:
        """Calculate violation severity based on similarity score."""
        if similarity_score >= 0.95:
            return "critical"
        elif similarity_score >= 0.9:
            return "high"
        elif similarity_score >= 0.85:
            return "medium"
        else:
            return "low"

    def _record_violation(self, violation: SimilarityViolation) -> None:
        """Record similarity violation."""
        self.metrics.total_violations += 1
        self.metrics.violations_by_tenant[violation.tenant1] = (
            self.metrics.violations_by_tenant.get(violation.tenant1, 0) + 1
        )
        self.metrics.violations_by_tenant[violation.tenant2] = (
            self.metrics.violations_by_tenant.get(violation.tenant2, 0) + 1
        )
        self.metrics.violations_by_method[violation.detection_method] = (
            self.metrics.violations_by_method.get(violation.detection_method, 0) + 1
        )
        self.metrics.violations_by_severity[violation.severity] = (
            self.metrics.violations_by_severity.get(violation.severity, 0) + 1
        )

        # Add to recent violations
        self.metrics.recent_violations.append(violation)
        if len(self.metrics.recent_violations) > 100:  # Keep last 100 violations
            self.metrics.recent_violations = self.metrics.recent_violations[-100:]

        # Update violation trend
        current_time = time.time()
        self.metrics.violation_trend.append((current_time, self.metrics.total_violations))
        if len(self.metrics.violation_trend) > 1000:  # Keep last 1000 data points
            self.metrics.violation_trend = self.metrics.violation_trend[-1000:]

    def _get_cached_violation(self, tenant_id: str, embedding: np.ndarray) -> SimilarityViolation | None:
        """Get cached violation for similar embedding."""
        # Simple cache lookup based on embedding hash
        embedding_hash = hashlib.md5(embedding.tobytes()).hexdigest()

        # Check if we have a cached violation for this tenant and similar embedding
        for cached_tenant, cached_hash, violation in self.violation_cache:
            if cached_tenant == tenant_id and cached_hash == embedding_hash:
                return violation

        return None

    def _cache_violation(self, tenant_id: str, embedding: np.ndarray, violation: SimilarityViolation) -> None:
        """Cache violation for future reference."""
        embedding_hash = hashlib.md5(embedding.tobytes()).hexdigest()

        # Add to cache (implement proper cache management in production)
        if len(self.violation_cache) > 10000:  # Limit cache size
            # Remove oldest entries
            self.violation_cache = set(list(self.violation_cache)[-5000:])

        self.violation_cache.add((tenant_id, embedding_hash, violation))

    def _get_content_by_id(self, content_id: str) -> Any | None:
        """Get content by ID across all tenants."""
        for tenant_content in self.tenant_content.values():
            if content_id in tenant_content:
                return tenant_content[content_id]
        return None

    def get_tenant_isolation_stats(self) -> dict[str, Any]:
        """Get tenant isolation statistics."""
        return {
            "total_tenants": len(self.tenant_embeddings),
            "total_content_items": sum(len(embeddings) for embeddings in self.tenant_embeddings.values()),
            "total_violations": self.metrics.total_violations,
            "blocked_operations": self.metrics.blocked_operations,
            "average_check_time": self.metrics.average_check_time,
            "cache_hit_rate": self.metrics.cache_hit_rate,
            "violations_by_severity": dict(self.metrics.violations_by_severity),
            "violations_by_method": {
                method.value: count for method, count in self.metrics.violations_by_method.items()
            },
            "isolation_effectiveness": self._calculate_isolation_effectiveness(),
        }

    def _calculate_isolation_effectiveness(self) -> float:
        """Calculate isolation effectiveness score."""
        if self.metrics.total_checks == 0:
            return 1.0

        # Effectiveness = (total_checks - violations) / total_checks
        return (self.metrics.total_checks - self.metrics.total_violations) / self.metrics.total_checks

    async def cleanup_tenant_data(self, tenant_id: str) -> dict[str, Any]:
        """Clean up all data for a specific tenant."""
        embeddings_count = len(self.tenant_embeddings.get(tenant_id, {}))
        content_count = len(self.tenant_content.get(tenant_id, {}))

        # Remove tenant data
        self.tenant_embeddings.pop(tenant_id, None)
        self.tenant_content.pop(tenant_id, None)
        self.tenant_namespaces.pop(tenant_id, None)

        # Clean up caches
        self._cleanup_tenant_cache(tenant_id)

        logger.info(
            f"Cleaned up data for tenant {tenant_id}: {embeddings_count} embeddings, {content_count} content items"
        )

        return {
            "tenant_id": tenant_id,
            "embeddings_removed": embeddings_count,
            "content_removed": content_count,
            "cache_entries_removed": len(self.violation_cache),  # Approximate
        }

    def _cleanup_tenant_cache(self, tenant_id: str) -> None:
        """Clean up cache entries for a specific tenant."""
        # Remove violation cache entries for this tenant
        entries_to_remove = []
        for entry in self.violation_cache:
            if entry[0] == tenant_id:
                entries_to_remove.append(entry)

        for entry in entries_to_remove:
            self.violation_cache.discard(entry)

        # Clean up similarity cache
        keys_to_remove = []
        for key in self.similarity_cache:
            if tenant_id in key[:2]:  # Check tenant IDs in key
                keys_to_remove.append(key)

        for key in keys_to_remove:
            self.similarity_cache.pop(key, None)
