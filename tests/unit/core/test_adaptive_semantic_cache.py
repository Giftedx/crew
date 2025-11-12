"""Tests for the adaptive semantic cache implementation.

These tests exercise the modern async-aware cache logic, verifying metric
tracking, optimization decisions, singleton helpers, and error handling using a
lightweight in-memory stub instead of the deprecated synchronous helper APIs.
"""
from __future__ import annotations

import time
from platform.cache.adaptive_semantic_cache import (
    ADJUSTMENT_STEP,
    COST_SAVINGS_TARGET,
    HIT_RATE_DECLINE_TOLERANCE,
    HIT_RATE_TARGET,
    MAX_THRESHOLD,
    MIN_THRESHOLD,
    AdaptiveSemanticCache,
    CachePerformanceMetrics,
    OptimizationRecommendation,
    create_adaptive_semantic_cache,
    get_adaptive_semantic_cache,
    optimize_all_caches,
    reset_adaptive_cache,
)
from typing import Any
from unittest.mock import AsyncMock

import pytest


class FakeAsyncCache:
    """Simple asyncio-compatible cache stub used to replace the real backend."""

    def __init__(self) -> None:
        self.store: dict[str, Any] = {}
        self.raise_on_get = False
        self.raise_on_set = False

    async def get(self, key: str) -> Any | None:
        if self.raise_on_get:
            raise RuntimeError("cache get failure")
        return self.store.get(key)

    async def set(self, key: str, value: Any, dependencies: set[str] | None = None) -> bool:
        if self.raise_on_set:
            raise RuntimeError("cache set failure")
        self.store[key] = value
        return True

    async def delete(self, key: str, cascade: bool = True) -> bool:  # pragma: no cover - helper only
        self.store.pop(key, None)
        return True


@pytest.fixture(autouse=True)
def cleanup_singleton() -> None:
    """Ensure the module-level cache singleton is cleared between tests."""

    reset_adaptive_cache()
    yield
    reset_adaptive_cache()


@pytest.fixture
def fake_async_cache(monkeypatch: pytest.MonkeyPatch) -> FakeAsyncCache:
    """Patch the cache factory so every cache instance shares a controllable stub."""

    fake = FakeAsyncCache()

    class MetricStub:
        def labels(self, **kwargs: Any) -> MetricStub:  # pragma: no cover - trivial helper
            return self

        def inc(self) -> None:  # pragma: no cover - trivial helper
            return None

        def set(self, _value: float) -> None:  # pragma: no cover - trivial helper
            return None

        def observe(self, _value: float) -> None:  # pragma: no cover - trivial helper
            return None

    def _factory(name: str, **kwargs: Any) -> FakeAsyncCache:  # pragma: no cover - simple passthrough
        return fake

    def _label_ctx_stub() -> dict[str, str]:  # pragma: no cover - trivial helper
        return {}

    monkeypatch.setattr("platform.cache.adaptive_semantic_cache.get_multi_level_cache", _factory)
    monkeypatch.setattr("platform.cache.adaptive_semantic_cache.label_ctx", _label_ctx_stub)
    metric_stub = MetricStub()
    monkeypatch.setattr("platform.cache.adaptive_semantic_cache.CACHE_HITS", metric_stub)
    monkeypatch.setattr("platform.cache.adaptive_semantic_cache.CACHE_MISSES", metric_stub)
    monkeypatch.setattr("platform.cache.adaptive_semantic_cache.CACHE_HIT_RATE_RATIO", metric_stub)
    monkeypatch.setattr("platform.cache.adaptive_semantic_cache.CACHE_OPERATION_LATENCY", metric_stub)
    return fake


class TestCachePerformanceMetrics:
    """Unit tests for the metrics helper dataclass."""

    def test_metric_accessors_and_ratios(self) -> None:
        metrics = CachePerformanceMetrics()
        assert metrics.total_requests == 0
        assert metrics.cache_hits == 0
        assert metrics.cache_misses == 0
        assert metrics.hit_rate == 0.0
        assert metrics.cost_efficiency == 0.0

        metrics.hit_count = 6
        metrics.miss_count = 4
        metrics.total_cost_saved = 0.75
        assert metrics.total_requests == 10
        assert metrics.cache_hits == 6
        assert metrics.cache_misses == 4
        assert metrics.hit_rate == pytest.approx(0.6)
        expected_cost_efficiency = min(1.0, 0.75 / max(1.0, metrics.total_requests * 0.01))
        assert metrics.cost_efficiency == pytest.approx(expected_cost_efficiency)


class TestAdaptiveSemanticCache:
    """Behavioral tests for the adaptive cache using the async stub."""

    @pytest.mark.asyncio
    async def test_cache_hit_updates_metrics(self, fake_async_cache: FakeAsyncCache) -> None:
        cache = AdaptiveSemanticCache(name="hit-cache")
        payload = {"response": "ok"}
        assert await cache.set("prompt", "model", payload) is True

        result = await cache.get("prompt", "model")
        assert result is not None
        assert result["response"] == payload
        assert cache.metrics.cache_hits == 1
        assert cache.metrics.cache_misses == 0
        assert cache.metrics.total_cost_saved == pytest.approx(cache.cost_per_llm_request)
        assert cache.metrics.total_latency_saved_ms == pytest.approx(cache.avg_llm_latency_ms)

    @pytest.mark.asyncio
    async def test_cache_miss_records_metrics(self, fake_async_cache: FakeAsyncCache) -> None:
        cache = AdaptiveSemanticCache(name="miss-cache")
        result = await cache.get("prompt", "model")
        assert result is None
        assert cache.metrics.cache_misses == 1
        assert cache.metrics.cache_hits == 0

    @pytest.mark.asyncio
    async def test_generate_recommendation_trending_down(self, fake_async_cache: FakeAsyncCache) -> None:
        cache = AdaptiveSemanticCache(name="trend-cache", evaluation_window=4)
        cache.metrics.hit_count = 80
        cache.metrics.miss_count = 20
        cache.metrics.total_cost_saved = COST_SAVINGS_TARGET * 2
        now = time.time()
        cache.recent_requests.clear()
        for idx, hit in enumerate([True, False, False, False]):
            cache.recent_requests.append((f"key{idx}", hit, now - idx))

        recommendation = await cache._generate_optimization_recommendation()
        assert recommendation is not None
        assert recommendation.action == "increase_threshold"
        assert recommendation.recommended_threshold == pytest.approx(
            min(MAX_THRESHOLD, cache.current_threshold + ADJUSTMENT_STEP)
        )
        assert recommendation.confidence > HIT_RATE_DECLINE_TOLERANCE

    @pytest.mark.asyncio
    async def test_consider_optimization_applies_when_confident(self, fake_async_cache: FakeAsyncCache) -> None:
        cache = AdaptiveSemanticCache(name="consider-cache", evaluation_window=2, min_requests_for_adjustment=2)
        cache.metrics.hit_count = 0
        cache.metrics.miss_count = 2
        now = time.time()
        cache.recent_requests.clear()
        cache.recent_requests.append(("a", False, now))
        cache.recent_requests.append(("b", False, now))

        recommendation = OptimizationRecommendation(
            action="decrease_threshold",
            current_threshold=cache.current_threshold,
            recommended_threshold=max(cache.current_threshold - ADJUSTMENT_STEP, MIN_THRESHOLD),
            reason="Low hit rate",
            expected_hit_rate_improvement=0.1,
            expected_cost_savings_improvement=0.05,
            confidence=0.9,
        )

        generator = AsyncMock(return_value=recommendation)
        applier_called = False
        original_apply = cache._apply_optimization

        async def wrapped_apply(rec: OptimizationRecommendation) -> None:
            nonlocal applier_called
            applier_called = True
            await original_apply(rec)

        cache._generate_optimization_recommendation = generator
        cache._apply_optimization = wrapped_apply  # type: ignore[assignment]

        await cache._consider_optimization()
        assert applier_called is True
        assert cache.current_threshold == recommendation.recommended_threshold
        generator.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_force_optimization_respects_confidence(self, fake_async_cache: FakeAsyncCache) -> None:
        cache = AdaptiveSemanticCache(name="force-cache")
        low_conf_rec = OptimizationRecommendation(
            action="increase_threshold",
            current_threshold=cache.current_threshold,
            recommended_threshold=min(MAX_THRESHOLD, cache.current_threshold + ADJUSTMENT_STEP),
            reason="Trending down",
            expected_hit_rate_improvement=0.05,
            expected_cost_savings_improvement=0.02,
            confidence=0.4,
        )
        cache._generate_optimization_recommendation = AsyncMock(return_value=low_conf_rec)  # type: ignore[assignment]
        await cache.force_optimization()
        assert cache.current_threshold == low_conf_rec.current_threshold

        high_conf_rec = OptimizationRecommendation(
            action="increase_threshold",
            current_threshold=cache.current_threshold,
            recommended_threshold=min(MAX_THRESHOLD, cache.current_threshold + ADJUSTMENT_STEP),
            reason="Trending down",
            expected_hit_rate_improvement=0.05,
            expected_cost_savings_improvement=0.02,
            confidence=0.8,
        )
        cache._generate_optimization_recommendation = AsyncMock(return_value=high_conf_rec)  # type: ignore[assignment]
        await cache.force_optimization()
        assert cache.current_threshold == high_conf_rec.recommended_threshold

    @pytest.mark.asyncio
    async def test_cache_error_handling(self, fake_async_cache: FakeAsyncCache) -> None:
        cache = AdaptiveSemanticCache(name="error-cache")
        fake_async_cache.raise_on_get = True
        result = await cache.get("prompt", "model")
        assert result is None
        assert cache.metrics.cache_hits == 0
        assert cache.metrics.cache_misses == 0

        fake_async_cache.raise_on_set = True
        success = await cache.set("prompt", "model", {"response": "x"})
        assert success is False

    @pytest.mark.asyncio
    async def test_get_performance_summary(self, fake_async_cache: FakeAsyncCache) -> None:
        cache = AdaptiveSemanticCache(name="summary-cache")
        await cache.set("prompt", "model", {"response": "data"})
        await cache.get("prompt", "model")
        summary = cache.get_performance_summary()
        assert summary["cache_name"] == "summary-cache"
        assert summary["total_requests"] == cache.metrics.total_requests
        assert summary["targets"]["hit_rate_target"] == HIT_RATE_TARGET
        assert summary["threshold_limits"]["max_threshold"] == MAX_THRESHOLD


class TestFactoryHelpers:
    """Tests for module-level helper functions that wrap the cache."""

    def test_create_factory_uses_current_defaults(self, fake_async_cache: FakeAsyncCache) -> None:
        cache = create_adaptive_semantic_cache(initial_threshold=0.85)
        assert isinstance(cache, AdaptiveSemanticCache)
        assert cache.current_threshold == pytest.approx(0.85)

    @pytest.mark.asyncio
    async def test_get_adaptive_semantic_cache_singleton(self, fake_async_cache: FakeAsyncCache) -> None:
        cache1 = await get_adaptive_semantic_cache(name="singleton-cache")
        cache2 = await get_adaptive_semantic_cache()
        assert cache1 is cache2

    @pytest.mark.asyncio
    async def test_optimize_all_caches_without_instance(self) -> None:
        result = await optimize_all_caches()
        assert result == {"status": "no_caches"}

    @pytest.mark.asyncio
    async def test_optimize_all_caches_with_instance(self, fake_async_cache: FakeAsyncCache) -> None:
        cache = await get_adaptive_semantic_cache(name="opt-cache")
        recommendation = OptimizationRecommendation(
            action="maintain_threshold",
            current_threshold=cache.current_threshold,
            recommended_threshold=cache.current_threshold,
            reason="No change",
            expected_hit_rate_improvement=0.0,
            expected_cost_savings_improvement=0.0,
            confidence=0.75,
        )
        cache.force_optimization = AsyncMock(return_value=recommendation)  # type: ignore[assignment]
        result = await optimize_all_caches()
        assert result["cache_name"] == "opt-cache"
        assert result["recommendation"] == recommendation.__dict__
        assert "performance_summary" in result


if __name__ == "__main__":  # pragma: no cover - manual invocation helper
    pytest.main([__file__])
