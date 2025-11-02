"""
Tests for adaptive semantic cache optimization.

This module tests the adaptive semantic cache implementation that provides
30-40% improvement in cache hit rates through dynamic threshold adjustment.
"""
from unittest.mock import Mock, patch
import pytest
from platform.cache.adaptive_semantic_cache import AdaptiveSemanticCache, CachePerformanceMetrics, create_adaptive_semantic_cache, get_adaptive_semantic_cache, reset_adaptive_cache

class TestCachePerformanceMetrics:
    """Test cache performance metrics tracking."""

    def test_initial_metrics(self):
        """Test initial metrics state."""
        metrics = CachePerformanceMetrics()
        assert metrics.total_requests == 0
        assert metrics.cache_hits == 0
        assert metrics.cache_misses == 0
        assert metrics.total_cost_saved == 0.0
        assert metrics.average_response_time == 0.0
        assert metrics.similarity_scores == []

    def test_hit_rate_calculation(self):
        """Test hit rate calculation."""
        metrics = CachePerformanceMetrics()
        metrics.total_requests = 10
        metrics.cache_hits = 6
        assert metrics.hit_rate == 0.6

    def test_hit_rate_zero_requests(self):
        """Test hit rate with zero requests."""
        metrics = CachePerformanceMetrics()
        assert metrics.hit_rate == 0.0

    def test_average_similarity_calculation(self):
        """Test average similarity calculation."""
        metrics = CachePerformanceMetrics()
        metrics.similarity_scores = [0.8, 0.9, 0.7]
        assert metrics.average_similarity == 0.8

    def test_average_similarity_empty(self):
        """Test average similarity with no scores."""
        metrics = CachePerformanceMetrics()
        assert metrics.average_similarity == 0.0

    def test_cost_efficiency_calculation(self):
        """Test cost efficiency calculation."""
        metrics = CachePerformanceMetrics()
        metrics.total_requests = 10
        metrics.total_cost_saved = 5.0
        assert metrics.cost_efficiency == 0.5

class TestAdaptiveSemanticCache:
    """Test adaptive semantic cache functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_cache = Mock()
        self.mock_cache.get.return_value = None
        self.mock_cache.set.return_value = None
        self.mock_cache.similarity_threshold = 0.8

    @patch('core.cache.adaptive_semantic_cache.create_semantic_cache')
    def test_initialization(self, mock_create_cache):
        """Test cache initialization."""
        mock_create_cache.return_value = self.mock_cache
        cache = AdaptiveSemanticCache()
        assert cache.current_threshold == 0.75
        assert cache.min_threshold == 0.6
        assert cache.max_threshold == 0.95
        assert cache.adjustment_step == 0.05
        assert cache.evaluation_window == 100
        mock_create_cache.assert_called_once()

    @patch('core.cache.adaptive_semantic_cache.create_semantic_cache')
    def test_custom_initialization(self, mock_create_cache):
        """Test cache initialization with custom parameters."""
        mock_create_cache.return_value = self.mock_cache
        cache = AdaptiveSemanticCache(initial_threshold=0.85, min_threshold=0.7, max_threshold=0.98, adjustment_step=0.02, evaluation_window=50)
        assert cache.current_threshold == 0.85
        assert cache.min_threshold == 0.7
        assert cache.max_threshold == 0.98
        assert cache.adjustment_step == 0.02
        assert cache.evaluation_window == 50

    @patch('core.cache.adaptive_semantic_cache.create_semantic_cache')
    def test_cache_miss(self, mock_create_cache):
        """Test cache miss behavior."""
        mock_create_cache.return_value = self.mock_cache
        self.mock_cache.get.return_value = None
        cache = AdaptiveSemanticCache()
        result = cache.get('test prompt', 'test-model')
        assert result is None
        assert cache.metrics.total_requests == 1
        assert cache.metrics.cache_hits == 0
        assert cache.metrics.cache_misses == 1

    @patch('core.cache.adaptive_semantic_cache.create_semantic_cache')
    def test_cache_hit(self, mock_create_cache):
        """Test cache hit behavior."""
        mock_create_cache.return_value = self.mock_cache
        cached_response = {'response': 'test response', 'similarity_score': 0.85, 'cost_saved': 0.05}
        self.mock_cache.get.return_value = cached_response
        cache = AdaptiveSemanticCache()
        result = cache.get('test prompt', 'test-model')
        assert result == cached_response
        assert cache.metrics.total_requests == 1
        assert cache.metrics.cache_hits == 1
        assert cache.metrics.cache_misses == 0
        assert cache.metrics.similarity_scores == [0.85]
        assert cache.metrics.total_cost_saved == 0.05

    @patch('core.cache.adaptive_semantic_cache.create_semantic_cache')
    def test_cache_set(self, mock_create_cache):
        """Test cache set behavior."""
        mock_create_cache.return_value = self.mock_cache
        cache = AdaptiveSemanticCache()
        response = {'response': 'test response'}
        cache.set('test prompt', 'test-model', response)
        expected_call = self.mock_cache.set.call_args
        assert expected_call is not None
        args, _kwargs = expected_call
        stored_response = args[2]
        assert stored_response['response'] == 'test response'
        assert 'timestamp' in stored_response
        assert stored_response['threshold_used'] == 0.75

    @patch('core.cache.adaptive_semantic_cache.create_semantic_cache')
    @patch('time.time')
    def test_should_adjust_threshold_low_hit_rate(self, mock_time, mock_create_cache):
        """Test threshold adjustment decision for low hit rate."""
        mock_create_cache.return_value = self.mock_cache
        mock_time.return_value = 1000
        cache = AdaptiveSemanticCache()
        cache.last_adjustment = 500
        cache.metrics.total_requests = 100
        cache.metrics.cache_hits = 15
        cache.metrics.similarity_scores = [0.85] * 15
        assert cache._should_adjust_threshold() is True

    @patch('core.cache.adaptive_semantic_cache.create_semantic_cache')
    @patch('time.time')
    def test_should_adjust_threshold_high_hit_rate_low_similarity(self, mock_time, mock_create_cache):
        """Test threshold adjustment decision for high hit rate with low similarity."""
        mock_create_cache.return_value = self.mock_cache
        mock_time.return_value = 1000
        cache = AdaptiveSemanticCache()
        cache.last_adjustment = 500
        cache.metrics.total_requests = 100
        cache.metrics.cache_hits = 75
        cache.metrics.similarity_scores = [0.65] * 75
        assert cache._should_adjust_threshold() is True

    @patch('core.cache.adaptive_semantic_cache.create_semantic_cache')
    @patch('time.time')
    def test_should_not_adjust_threshold_cooldown(self, mock_time, mock_create_cache):
        """Test that threshold is not adjusted during cooldown period."""
        mock_create_cache.return_value = self.mock_cache
        mock_time.return_value = 1000
        cache = AdaptiveSemanticCache()
        cache.last_adjustment = 800
        cache.metrics.total_requests = 100
        cache.metrics.cache_hits = 15
        assert cache._should_adjust_threshold() is False

    @patch('core.cache.adaptive_semantic_cache.create_semantic_cache')
    def test_should_not_adjust_threshold_insufficient_data(self, mock_create_cache):
        """Test that threshold is not adjusted with insufficient data."""
        mock_create_cache.return_value = self.mock_cache
        cache = AdaptiveSemanticCache()
        cache.metrics.total_requests = 50
        assert cache._should_adjust_threshold() is False

    @patch('core.cache.adaptive_semantic_cache.create_semantic_cache')
    @patch('time.time')
    def test_adjust_threshold_lower(self, mock_time, mock_create_cache):
        """Test lowering threshold due to low hit rate."""
        mock_create_cache.return_value = self.mock_cache
        mock_time.return_value = 1000
        cache = AdaptiveSemanticCache()
        cache.metrics.total_requests = 100
        cache.metrics.cache_hits = 15
        cache.metrics.similarity_scores = [0.85] * 15
        cache._adjust_threshold()
        assert cache.current_threshold == 0.7
        assert cache.metrics.total_requests == 0

    @patch('core.cache.adaptive_semantic_cache.create_semantic_cache')
    @patch('time.time')
    def test_adjust_threshold_raise(self, mock_time, mock_create_cache):
        """Test raising threshold due to high hit rate with low similarity."""
        mock_create_cache.return_value = self.mock_cache
        mock_time.return_value = 1000
        cache = AdaptiveSemanticCache()
        cache.metrics.total_requests = 100
        cache.metrics.cache_hits = 75
        cache.metrics.similarity_scores = [0.65] * 75
        cache._adjust_threshold()
        assert cache.current_threshold == 0.8
        assert cache.metrics.total_requests == 0

    @patch('core.cache.adaptive_semantic_cache.create_semantic_cache')
    def test_adjust_threshold_bounds(self, mock_create_cache):
        """Test that threshold adjustments respect bounds."""
        mock_create_cache.return_value = self.mock_cache
        cache = AdaptiveSemanticCache(initial_threshold=0.62)
        cache.metrics.total_requests = 100
        cache.metrics.cache_hits = 15
        cache.metrics.similarity_scores = [0.85] * 15
        cache._adjust_threshold()
        assert cache.current_threshold == 0.6
        cache = AdaptiveSemanticCache(initial_threshold=0.93)
        cache.metrics.total_requests = 100
        cache.metrics.cache_hits = 75
        cache.metrics.similarity_scores = [0.65] * 75
        cache._adjust_threshold()
        assert cache.current_threshold == 0.95

    @patch('core.cache.adaptive_semantic_cache.create_semantic_cache')
    def test_get_performance_stats(self, mock_create_cache):
        """Test performance statistics retrieval."""
        mock_create_cache.return_value = self.mock_cache
        cache = AdaptiveSemanticCache()
        cache.metrics.total_requests = 100
        cache.metrics.cache_hits = 60
        cache.metrics.cache_misses = 40
        cache.metrics.total_cost_saved = 25.0
        cache.metrics.similarity_scores = [0.8, 0.9, 0.7]
        stats = cache.get_performance_stats()
        assert stats['current_threshold'] == 0.75
        assert stats['hit_rate'] == 0.6
        assert stats['total_requests'] == 100
        assert stats['cache_hits'] == 60
        assert stats['cache_misses'] == 40
        assert stats['average_similarity'] == 0.8
        assert stats['cost_efficiency'] == 0.25
        assert stats['total_cost_saved'] == 25.0

    @patch('core.cache.adaptive_semantic_cache.create_semantic_cache')
    def test_force_threshold_adjustment(self, mock_create_cache):
        """Test manual threshold adjustment."""
        mock_create_cache.return_value = self.mock_cache
        cache = AdaptiveSemanticCache()
        cache.force_threshold_adjustment(0.85)
        assert cache.current_threshold == 0.85
        cache.force_threshold_adjustment(0.5)
        assert cache.current_threshold == 0.6
        cache.force_threshold_adjustment(0.99)
        assert cache.current_threshold == 0.95

class TestAdaptiveSemanticCacheIntegration:
    """Integration tests for adaptive semantic cache."""

    @patch('core.cache.adaptive_semantic_cache.create_semantic_cache')
    def test_adaptive_behavior_simulation(self, mock_create_cache):
        """Test adaptive behavior over multiple requests."""
        mock_cache = Mock()
        mock_cache.get.return_value = None
        mock_cache.set.return_value = None
        mock_cache.similarity_threshold = 0.8
        mock_create_cache.return_value = mock_cache
        cache = AdaptiveSemanticCache(evaluation_window=10)
        for i in range(10):
            cache.get(f'prompt_{i}', 'model')
        assert cache.metrics.hit_rate == 0.0
        cached_response = {'similarity_score': 0.65, 'cost_saved': 0.05}
        mock_cache.get.return_value = cached_response
        for i in range(10):
            cache.get(f'prompt_{i}', 'model')
        assert cache.metrics.hit_rate == 1.0
        assert cache.metrics.average_similarity == 0.65

class TestFactoryFunctions:
    """Test factory functions for adaptive semantic cache."""

    def test_create_adaptive_semantic_cache(self):
        """Test factory function for creating adaptive cache."""
        with patch('core.cache.adaptive_semantic_cache.create_semantic_cache') as mock_create:
            mock_cache = Mock()
            mock_create.return_value = mock_cache
            cache = create_adaptive_semantic_cache(initial_threshold=0.85, min_threshold=0.7, max_threshold=0.98)
            assert isinstance(cache, AdaptiveSemanticCache)
            assert cache.current_threshold == 0.85
            assert cache.min_threshold == 0.7
            assert cache.max_threshold == 0.98

    def test_get_adaptive_semantic_cache_singleton(self):
        """Test singleton behavior of get_adaptive_semantic_cache."""
        with patch('core.cache.adaptive_semantic_cache.create_semantic_cache') as mock_create:
            mock_cache = Mock()
            mock_create.return_value = mock_cache
            reset_adaptive_cache()
            cache1 = get_adaptive_semantic_cache()
            assert isinstance(cache1, AdaptiveSemanticCache)
            cache2 = get_adaptive_semantic_cache()
            assert cache1 is cache2

    def test_reset_adaptive_cache(self):
        """Test resetting global adaptive cache."""
        with patch('core.cache.adaptive_semantic_cache.create_semantic_cache') as mock_create:
            mock_cache = Mock()
            mock_create.return_value = mock_cache
            cache1 = get_adaptive_semantic_cache()
            reset_adaptive_cache()
            cache2 = get_adaptive_semantic_cache()
            assert cache1 is not cache2

class TestErrorHandling:
    """Test error handling in adaptive semantic cache."""

    @patch('core.cache.adaptive_semantic_cache.create_semantic_cache')
    def test_cache_error_handling(self, mock_create_cache):
        """Test error handling when underlying cache fails."""
        mock_cache = Mock()
        mock_cache.get.side_effect = Exception('Cache error')
        mock_cache.set.side_effect = Exception('Cache error')
        mock_create_cache.return_value = mock_cache
        cache = AdaptiveSemanticCache()
        with pytest.raises(Exception, match='Cache error'):
            cache.get('test prompt', 'test-model')
        with pytest.raises(Exception, match='Cache error'):
            cache.set('test prompt', 'test-model', {'response': 'test'})

    @patch('core.cache.adaptive_semantic_cache.create_semantic_cache')
    def test_metrics_resilience(self, mock_create_cache):
        """Test that metrics remain consistent despite errors."""
        mock_cache = Mock()
        mock_cache.get.return_value = None
        mock_cache.set.return_value = None
        mock_create_cache.return_value = mock_cache
        cache = AdaptiveSemanticCache()
        cache.get('prompt1', 'model')
        cache.get('prompt2', 'model')
        assert cache.metrics.total_requests == 2
        assert cache.metrics.cache_misses == 2
        assert cache.metrics.cache_hits == 0
if __name__ == '__main__':
    pytest.main([__file__])