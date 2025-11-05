"""Adaptive Semantic Cache with Performance Optimization.

This module implements an intelligent semantic cache that automatically optimizes
hit rates through adaptive threshold adjustment, performance monitoring, and
cost-aware caching strategies.

Key Features:
- Dynamic threshold adjustment based on performance metrics
- Automatic optimization of similarity thresholds
- Performance monitoring and cost tracking
- Configurable evaluation windows and adjustment steps
- Multi-level caching with promotion/demotion strategies
- Real-time cache performance metrics
"""
from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from platform.cache.enhanced_redis_cache import EnhancedRedisCache
from platform.cache.multi_level_cache import get_multi_level_cache
from platform.observability.metrics import (
    CACHE_HIT_RATE_RATIO,
    CACHE_HITS,
    CACHE_MISSES,
    CACHE_OPERATION_LATENCY,
    label_ctx,
)
from typing import Any


logger = logging.getLogger(__name__)
DEFAULT_THRESHOLD = 0.75
MIN_THRESHOLD = 0.6
MAX_THRESHOLD = 0.95
ADJUSTMENT_STEP = 0.05
EVALUATION_WINDOW = 100
MIN_REQUESTS_FOR_ADJUSTMENT = 50
COST_SAVINGS_TARGET = 0.2
HIT_RATE_TARGET = 0.6

@dataclass
class CachePerformanceMetrics:
    """Track cache performance metrics for optimization."""
    hit_count: int = 0
    miss_count: int = 0
    total_cost_saved: float = 0.0
    total_latency_saved_ms: float = 0.0
    threshold: float = DEFAULT_THRESHOLD
    evaluation_start_time: float = field(default_factory=time.time)
    last_adjustment_time: float = field(default_factory=time.time)

    def get_hit_rate(self) -> float:
        """Calculate current hit rate."""
        total_requests = self.hit_count + self.miss_count
        return self.hit_count / total_requests if total_requests > 0 else 0.0

    def get_total_requests(self) -> int:
        """Get total number of requests."""
        return self.hit_count + self.miss_count

    def get_cost_savings_ratio(self) -> float:
        """Calculate cost savings ratio."""
        return min(1.0, self.total_cost_saved / max(1.0, self.get_total_requests() * 0.01))

    def get_avg_latency_savings_ms(self) -> float:
        """Calculate average latency savings per request."""
        total_requests = self.get_total_requests()
        return self.total_latency_saved_ms / total_requests if total_requests > 0 else 0.0

@dataclass
class OptimizationRecommendation:
    """Recommendation for cache optimization."""
    action: str
    current_threshold: float
    recommended_threshold: float
    reason: str
    expected_hit_rate_improvement: float
    expected_cost_savings_improvement: float
    confidence: float

class AdaptiveSemanticCache:
    """Adaptive semantic cache with automatic optimization."""

    def __init__(self, name: str='adaptive_semantic_cache', initial_threshold: float=DEFAULT_THRESHOLD, enable_adaptive_optimization: bool=True, evaluation_window: int=EVALUATION_WINDOW, min_requests_for_adjustment: int=MIN_REQUESTS_FOR_ADJUSTMENT, adjustment_step: float=ADJUSTMENT_STEP, l2_cache: EnhancedRedisCache | None=None, cost_per_llm_request: float=0.01, avg_llm_latency_ms: float=2000.0):
        """Initialize adaptive semantic cache.

        Args:
            name: Cache instance name
            initial_threshold: Initial similarity threshold
            enable_adaptive_optimization: Enable automatic threshold adjustment
            evaluation_window: Number of requests to evaluate before adjustment
            min_requests_for_adjustment: Minimum requests before considering adjustment
            adjustment_step: Step size for threshold adjustments
            l2_cache: Optional L2 Redis cache
            cost_per_llm_request: Estimated cost per LLM request for savings calculation
            avg_llm_latency_ms: Average LLM response latency for savings calculation
        """
        self.name = name
        self.current_threshold = initial_threshold
        self.enable_adaptive_optimization = enable_adaptive_optimization
        self.evaluation_window = evaluation_window
        self.min_requests_for_adjustment = min_requests_for_adjustment
        self.adjustment_step = adjustment_step
        self.cost_per_llm_request = cost_per_llm_request
        self.avg_llm_latency_ms = avg_llm_latency_ms
        self.cache = get_multi_level_cache(name=name, l2_cache=l2_cache, enable_compression=True, enable_promotion=True, enable_monitoring=True, enable_dependency_tracking=True)
        self.metrics = CachePerformanceMetrics(threshold=initial_threshold)
        self.recent_requests: deque[tuple[str, bool, float]] = deque(maxlen=evaluation_window)
        self.optimization_history: list[OptimizationRecommendation] = []
        self._labels = label_ctx()
        logger.info(f"Initialized adaptive semantic cache '{name}' with threshold {initial_threshold}")

    async def get(self, prompt: str, model: str, namespace: str | None=None) -> dict[str, Any] | None:
        """Get cached response for prompt and model.

        Args:
            prompt: Input prompt
            model: Model identifier
            namespace: Optional namespace for tenant isolation

        Returns:
            Cached response or None if not found
        """
        start_time = time.time()
        cache_key = self._generate_cache_key(prompt, model, namespace)
        try:
            cached_response = await self.cache.get(cache_key)
            if cached_response:
                self.metrics.hit_count += 1
                self.recent_requests.append((cache_key, True, time.time()))
                self.metrics.total_cost_saved += self.cost_per_llm_request
                self.metrics.total_latency_saved_ms += self.avg_llm_latency_ms
                labels = {**self._labels, 'cache_name': self.name, 'cache_level': 'semantic'}
                CACHE_HITS.labels(**labels).inc()
                hit_rate = self.metrics.get_hit_rate()
                CACHE_HIT_RATE_RATIO.labels(**labels).set(hit_rate)
                operation_time = (time.time() - start_time) * 1000
                CACHE_OPERATION_LATENCY.labels(**labels, operation='get').observe(operation_time)
                logger.debug(f'Cache HIT for {cache_key} (threshold: {self.current_threshold:.3f})')
                return cached_response
            else:
                self.metrics.miss_count += 1
                self.recent_requests.append((cache_key, False, time.time()))
                labels = {**self._labels, 'cache_name': self.name, 'cache_level': 'semantic'}
                CACHE_MISSES.labels(**labels).inc()
                hit_rate = self.metrics.get_hit_rate()
                CACHE_HIT_RATE_RATIO.labels(**labels).set(hit_rate)
                operation_time = (time.time() - start_time) * 1000
                CACHE_OPERATION_LATENCY.labels(**labels, operation='get').observe(operation_time)
                logger.debug(f'Cache MISS for {cache_key} (threshold: {self.current_threshold:.3f})')
                if self.enable_adaptive_optimization:
                    await self._consider_optimization()
                return None
        except Exception as e:
            logger.error(f'Error getting from semantic cache: {e}')
            return None

    async def set(self, prompt: str, model: str, response: dict[str, Any], namespace: str | None=None) -> bool:
        """Store response in cache.

        Args:
            prompt: Input prompt
            model: Model identifier
            response: Response to cache
            namespace: Optional namespace for tenant isolation

        Returns:
            True if successful, False otherwise
        """
        start_time = time.time()
        cache_key = self._generate_cache_key(prompt, model, namespace)
        try:
            cache_data = {'response': response, 'prompt': prompt, 'model': model, 'timestamp': time.time(), 'threshold_used': self.current_threshold, 'namespace': namespace}
            success = await self.cache.set(cache_key, cache_data)
            operation_time = (time.time() - start_time) * 1000
            labels = {**self._labels, 'cache_name': self.name, 'cache_level': 'semantic'}
            CACHE_OPERATION_LATENCY.labels(**labels, operation='set').observe(operation_time)
            if success:
                logger.debug(f'Cached response for {cache_key}')
            else:
                logger.warning(f'Failed to cache response for {cache_key}')
            return success
        except Exception as e:
            logger.error(f'Error setting semantic cache: {e}')
            return False

    async def _consider_optimization(self) -> None:
        """Consider adjusting threshold based on recent performance."""
        if not self.enable_adaptive_optimization:
            return
        total_requests = self.metrics.get_total_requests()
        if total_requests < self.min_requests_for_adjustment:
            return
        if total_requests % self.evaluation_window != 0:
            return
        recommendation = await self._generate_optimization_recommendation()
        if recommendation and recommendation.confidence > 0.7:
            await self._apply_optimization(recommendation)

    async def _generate_optimization_recommendation(self) -> OptimizationRecommendation | None:
        """Generate optimization recommendation based on current performance."""
        current_hit_rate = self.metrics.get_hit_rate()
        current_cost_savings = self.metrics.get_cost_savings_ratio()
        recent_hits = sum((1 for _, hit, _ in self.recent_requests if hit))
        recent_total = len(self.recent_requests)
        recent_hit_rate = recent_hits / recent_total if recent_total > 0 else 0.0
        needs_improvement = current_hit_rate < HIT_RATE_TARGET or current_cost_savings < COST_SAVINGS_TARGET
        if not needs_improvement:
            return OptimizationRecommendation(action='maintain_threshold', current_threshold=self.current_threshold, recommended_threshold=self.current_threshold, reason='Performance targets met', expected_hit_rate_improvement=0.0, expected_cost_savings_improvement=0.0, confidence=0.8)
        if current_hit_rate < HIT_RATE_TARGET:
            if self.current_threshold > MIN_THRESHOLD:
                new_threshold = max(MIN_THRESHOLD, self.current_threshold - self.adjustment_step)
                action = 'decrease_threshold'
                reason = f'Hit rate {current_hit_rate:.3f} below target {HIT_RATE_TARGET}'
                expected_improvement = min(0.15, (HIT_RATE_TARGET - current_hit_rate) * 0.5)
            else:
                return OptimizationRecommendation(action='maintain_threshold', current_threshold=self.current_threshold, recommended_threshold=self.current_threshold, reason='Already at minimum threshold', expected_hit_rate_improvement=0.0, expected_cost_savings_improvement=0.0, confidence=0.5)
        elif self.current_threshold < MAX_THRESHOLD:
            new_threshold = min(MAX_THRESHOLD, self.current_threshold + self.adjustment_step)
            action = 'increase_threshold'
            reason = f'Cost savings {current_cost_savings:.3f} below target {COST_SAVINGS_TARGET}'
            expected_improvement = min(0.1, (COST_SAVINGS_TARGET - current_cost_savings) * 0.3)
        else:
            return OptimizationRecommendation(action='maintain_threshold', current_threshold=self.current_threshold, recommended_threshold=self.current_threshold, reason='Already at maximum threshold', expected_hit_rate_improvement=0.0, expected_cost_savings_improvement=0.0, confidence=0.5)
        total_requests = self.metrics.get_total_requests()
        confidence = min(0.9, total_requests / (self.evaluation_window * 2))
        return OptimizationRecommendation(action=action, current_threshold=self.current_threshold, recommended_threshold=new_threshold, reason=reason, expected_hit_rate_improvement=expected_improvement, expected_cost_savings_improvement=expected_improvement * 0.5, confidence=confidence)

    async def _apply_optimization(self, recommendation: OptimizationRecommendation) -> None:
        """Apply optimization recommendation."""
        old_threshold = self.current_threshold
        new_threshold = recommendation.recommended_threshold
        self.current_threshold = new_threshold
        self.metrics.threshold = new_threshold
        self.metrics.last_adjustment_time = time.time()
        self.optimization_history.append(recommendation)
        self.metrics.hit_count = 0
        self.metrics.miss_count = 0
        self.metrics.total_cost_saved = 0.0
        self.metrics.total_latency_saved_ms = 0.0
        self.metrics.evaluation_start_time = time.time()
        logger.info(f'Applied optimization: {recommendation.action} (threshold: {old_threshold:.3f} -> {new_threshold:.3f}) reason: {recommendation.reason} confidence: {recommendation.confidence:.3f}')

    def _generate_cache_key(self, prompt: str, model: str, namespace: str | None=None) -> str:
        """Generate cache key for prompt, model, and namespace."""
        import hashlib
        prompt_hash = hashlib.sha256(prompt.encode('utf-8')).hexdigest()[:16]
        key_parts = [prompt_hash, model]
        if namespace:
            key_parts.append(namespace)
        return ':'.join(key_parts)

    def get_performance_summary(self) -> dict[str, Any]:
        """Get comprehensive performance summary."""
        return {'cache_name': self.name, 'current_threshold': self.current_threshold, 'hit_rate': self.metrics.get_hit_rate(), 'total_requests': self.metrics.get_total_requests(), 'cost_savings_ratio': self.metrics.get_cost_savings_ratio(), 'avg_latency_savings_ms': self.metrics.get_avg_latency_savings_ms(), 'total_cost_saved': self.metrics.total_cost_saved, 'total_latency_saved_ms': self.metrics.total_latency_saved_ms, 'optimization_history_count': len(self.optimization_history), 'last_adjustment_time': self.metrics.last_adjustment_time, 'adaptive_optimization_enabled': self.enable_adaptive_optimization, 'targets': {'hit_rate_target': HIT_RATE_TARGET, 'cost_savings_target': COST_SAVINGS_TARGET}, 'threshold_limits': {'min_threshold': MIN_THRESHOLD, 'max_threshold': MAX_THRESHOLD}}

    def get_optimization_history(self) -> list[dict[str, Any]]:
        """Get optimization history."""
        return [{'action': rec.action, 'old_threshold': rec.current_threshold, 'new_threshold': rec.recommended_threshold, 'reason': rec.reason, 'expected_hit_rate_improvement': rec.expected_hit_rate_improvement, 'expected_cost_savings_improvement': rec.expected_cost_savings_improvement, 'confidence': rec.confidence} for rec in self.optimization_history]

    async def force_optimization(self) -> OptimizationRecommendation | None:
        """Force optimization evaluation and return recommendation."""
        if not self.enable_adaptive_optimization:
            return None
        recommendation = await self._generate_optimization_recommendation()
        if recommendation and recommendation.confidence > 0.5:
            await self._apply_optimization(recommendation)
        return recommendation

    async def reset_metrics(self) -> None:
        """Reset performance metrics."""
        self.metrics = CachePerformanceMetrics(threshold=self.current_threshold)
        self.recent_requests.clear()
        logger.info(f"Reset metrics for cache '{self.name}'")
_adaptive_cache: AdaptiveSemanticCache | None = None

async def get_adaptive_semantic_cache(name: str='default', **kwargs: Any) -> AdaptiveSemanticCache:
    """Get or create adaptive semantic cache instance."""
    global _adaptive_cache
    if _adaptive_cache is None:
        _adaptive_cache = AdaptiveSemanticCache(name=name, **kwargs)
    return _adaptive_cache

async def optimize_all_caches() -> dict[str, Any]:
    """Optimize all adaptive semantic caches."""
    if _adaptive_cache is None:
        return {'status': 'no_caches'}
    recommendation = await _adaptive_cache.force_optimization()
    return {'cache_name': _adaptive_cache.name, 'recommendation': recommendation.__dict__ if recommendation else None, 'performance_summary': _adaptive_cache.get_performance_summary()}
__all__ = ['AdaptiveSemanticCache', 'CachePerformanceMetrics', 'OptimizationRecommendation', 'get_adaptive_semantic_cache', 'optimize_all_caches']
