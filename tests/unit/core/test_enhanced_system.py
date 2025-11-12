"""Comprehensive integration tests for enhanced system components."""

import sys
import time
from unittest.mock import Mock


sys.path.insert(0, "src")
from platform.core.llm_cache import QuantizedEmbedding, VectorIndex, get_llm_cache
from platform.core.llm_router import LLMRouter, TaskComplexityMetrics
from platform.database.db_optimizer import DatabaseOptimizer

from memory.vector_store import VectorStore
from ultimate_discord_intelligence_bot.performance_dashboard import PerformanceDashboard
from ultimate_discord_intelligence_bot.step_result import (
    ErrorAnalyzer,
    ErrorCategory,
    ErrorContext,
    ErrorRecoveryStrategy,
    ErrorSeverity,
    StepResult,
)


class TestEnhancedSystemIntegration:
    """Test integration of all enhanced system components."""

    def test_enhanced_llm_cache_functionality(self):
        """Test enhanced LLM cache with all optimizations."""
        cache = get_llm_cache()
        assert hasattr(cache, "_vector_index")
        assert hasattr(cache, "_stats")
        assert hasattr(cache, "_analytics")
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        quantized = QuantizedEmbedding.from_float(embedding)
        assert quantized.dim == 1536
        assert len(quantized.data) == 1536
        vector_index = VectorIndex(max_entries=100)
        assert vector_index.max_entries == 100
        assert len(vector_index.entries) == 0
        stats = cache.get_stats()
        assert isinstance(stats, dict)
        assert "total_requests" in stats
        assert "hit_rate" in stats

    def test_enhanced_llm_router_functionality(self):
        """Test enhanced LLM router with cost-aware features."""
        mock_client1 = Mock()
        mock_client1.chat.return_value = Mock(cost_usd=0.01, latency_ms=100)
        mock_client2 = Mock()
        mock_client2.chat.return_value = Mock(cost_usd=0.02, latency_ms=200)
        clients = {"cheap_model": mock_client1, "expensive_model": mock_client2}
        router = LLMRouter(clients)
        assert hasattr(router, "_cost_aware_enabled")
        assert hasattr(router, "_model_profiles")
        assert hasattr(router, "_cost_optimization_stats")
        messages = [{"content": "This is a simple question"}]
        complexity = TaskComplexityMetrics.analyze_content(messages)
        assert complexity.complexity_score >= 0.0
        assert complexity.complexity_score <= 1.0
        profiles = router.get_model_performance_profiles()
        assert len(profiles) == 2
        assert "cheap_model" in profiles
        assert "expensive_model" in profiles

    def test_enhanced_step_result_functionality(self):
        """Test enhanced StepResult with comprehensive error handling."""
        result = StepResult.ok(data={"test": "value"})
        assert result.success
        assert result.data["test"] == "value"
        error_result = StepResult.fail("Network timeout", ErrorCategory.NETWORK)
        assert not error_result.success
        assert error_result.error_category == ErrorCategory.NETWORK
        assert error_result.retryable
        context = ErrorContext(operation="test_op", component="test_component")
        enhanced_result = StepResult.fail("Database connection failed", ErrorCategory.DATABASE_ERROR, context=context)
        assert enhanced_result.error_context is not None
        assert enhanced_result.error_context.operation == "test_op"
        assert enhanced_result.error_severity == ErrorSeverity.CRITICAL
        strategy = ErrorRecoveryStrategy(
            error_categories=[ErrorCategory.NETWORK, ErrorCategory.TIMEOUT], max_retries=3, retry_delay_base=1.0
        )
        assert strategy.should_retry(1, ErrorCategory.NETWORK)
        assert not strategy.should_retry(4, ErrorCategory.NETWORK)

    def test_enhanced_vector_store_functionality(self):
        """Test enhanced vector store with memory optimizations."""
        store = VectorStore()
        assert hasattr(store, "_vector_index")
        assert hasattr(store, "_analytics")
        assert hasattr(store, "_enable_optimizations")
        analytics = store.get_memory_analytics()
        assert isinstance(analytics, dict)
        batch_size = store._get_adaptive_batch_size("test_namespace", 768)
        assert batch_size > 0
        assert batch_size <= 256
        start_time = time.time()
        store._track_operation_performance("test_op", start_time, vectors_processed=10)
        assert len(store._performance_history) > 0

    def test_enhanced_database_optimizer_functionality(self):
        """Test enhanced database optimizer with query analysis."""
        optimizer = DatabaseOptimizer()
        assert hasattr(optimizer, "query_metrics")
        assert hasattr(optimizer, "query_patterns")
        assert hasattr(optimizer, "_enable_optimizations")
        query = "SELECT * FROM content WHERE tenant = ?"
        execution_time = 150.0
        optimizer._update_query_patterns(query, execution_time)
        assert query in optimizer.query_patterns
        assert optimizer.query_patterns[query]["count"] == 1
        assert optimizer.query_patterns[query]["total_time"] == execution_time

    def test_performance_dashboard_integration(self):
        """Test performance dashboard integration across all components."""
        dashboard = PerformanceDashboard()
        assert hasattr(dashboard, "cache")
        assert hasattr(dashboard, "error_analyzer")
        assert hasattr(dashboard, "vector_store")
        metrics = dashboard.get_comprehensive_metrics()
        assert isinstance(metrics, dict)
        assert "timestamp" in metrics
        assert "cache_performance" in metrics
        assert "error_handling" in metrics
        assert "memory_performance" in metrics
        summary = dashboard.get_dashboard_summary()
        assert isinstance(summary, dict)
        assert "overall_health" in summary
        assert "overall_score" in summary
        assert "active_optimizations" in summary

    def test_system_integration_end_to_end(self):
        """Test end-to-end integration of all enhanced components."""
        from platform.core.llm_cache import get_llm_cache
        from platform.core.llm_router import LLMRouter

        from ultimate_discord_intelligence_bot.performance_dashboard import get_performance_dashboard
        from ultimate_discord_intelligence_bot.step_result import ErrorCategory, StepResult

        get_llm_cache()
        dashboard = get_performance_dashboard()
        mock_client = Mock()
        mock_client.chat.return_value = Mock(cost_usd=0.01, latency_ms=100)
        LLMRouter({"test_model": mock_client})
        error_result = StepResult.fail("Test error", ErrorCategory.PROCESSING)
        assert not error_result.success
        assert error_result.error_category == ErrorCategory.PROCESSING
        summary = dashboard.get_dashboard_summary()
        assert isinstance(summary, dict)
        assert "overall_health" in summary

    def test_performance_improvements_validation(self):
        """Validate that performance improvements are working as expected."""
        cache = get_llm_cache()
        test_prompt = "Test prompt for caching"
        test_response = {"result": "cached response"}
        cache.put(test_prompt, "test_model", test_response)
        retrieved = cache.get(test_prompt, "test_model")
        assert retrieved == test_response
        stats = cache.get_stats()
        assert stats["total_requests"] >= 1
        assert stats["hits"] >= 1

    def test_error_recovery_mechanisms(self):
        """Test error recovery and resilience mechanisms."""
        error_result = StepResult.fail("Connection timeout", ErrorCategory.NETWORK)
        assert error_result.should_retry(1)
        assert error_result.should_retry(2)
        assert not error_result.should_retry(4)
        context = ErrorContext(operation="test_operation", component="test_component")
        enhanced_result = StepResult.fail("Test error", context=context, error_category=ErrorCategory.DATABASE_ERROR)
        assert enhanced_result.error_context is not None
        assert enhanced_result.error_severity == ErrorSeverity.CRITICAL
        assert len(enhanced_result.suggested_actions) > 0

    def test_memory_optimization_functionality(self):
        """Test memory optimization features."""
        store = VectorStore()
        analytics = store.get_memory_analytics()
        assert isinstance(analytics, dict)
        batch_size = store._get_adaptive_batch_size("test", 768)
        assert batch_size > 0
        start_time = time.time()
        store._track_operation_performance("test", start_time, vectors_processed=10)
        assert len(store._performance_history) > 0

    def test_database_optimization_features(self):
        """Test database optimization functionality."""
        optimizer = DatabaseOptimizer()
        query = "SELECT * FROM content WHERE tenant = ? AND workspace = ?"
        optimizer._update_query_patterns(query, 100.0)
        assert query in optimizer.query_patterns
        assert optimizer.query_patterns[query]["count"] == 1
        assert optimizer.query_patterns[query]["total_time"] == 100.0
        columns = optimizer._extract_filter_columns(query)
        assert isinstance(columns, list)

    def test_unified_monitoring_capabilities(self):
        """Test unified monitoring across all components."""
        dashboard = PerformanceDashboard()
        metrics = dashboard.get_comprehensive_metrics()
        assert isinstance(metrics, dict)
        assert "cache_performance" in metrics
        assert "error_handling" in metrics
        assert "memory_performance" in metrics
        summary = dashboard.get_dashboard_summary()
        assert isinstance(summary, dict)
        assert "overall_health" in summary
        assert "overall_score" in summary
        assert "performance_highlights" in summary

    def test_backward_compatibility(self):
        """Test that all enhancements maintain backward compatibility."""
        result = StepResult.ok(data={"test": "value"})
        assert result.success
        assert result["test"] == "value"
        error_result = StepResult.fail("Legacy error")
        assert not error_result.success
        assert error_result.error == "Legacy error"
        cache = get_llm_cache()
        cache.put("test", "model", "response")
        retrieved = cache.get("test", "model")
        assert retrieved == "response"

    def test_error_analysis_and_reporting(self):
        """Test error analysis and reporting capabilities."""
        analyzer = ErrorAnalyzer()
        network_error = StepResult.fail("Network timeout", ErrorCategory.NETWORK)
        database_error = StepResult.fail("Connection failed", ErrorCategory.DATABASE_ERROR)
        validation_error = StepResult.fail("Invalid input", ErrorCategory.VALIDATION)
        analyzer.record_error(network_error)
        analyzer.record_error(database_error)
        analyzer.record_error(validation_error)
        summary = analyzer.get_error_summary()
        assert summary["total_errors"] == 3
        assert "network" in summary["error_categories"]
        assert "database_error" in summary["error_categories"]
        assert "validation" in summary["error_categories"]


if __name__ == "__main__":
    test_suite = TestEnhancedSystemIntegration()
    print("🧪 Running Enhanced System Integration Tests...")
    print("=" * 60)
    test_methods = [method for method in dir(test_suite) if method.startswith("test_")]
    passed = 0
    failed = 0
    for method_name in test_methods:
        try:
            print(f"\n🔍 Running {method_name}...")
            method = getattr(test_suite, method_name)
            method()
            print(f"✅ {method_name} PASSED")
            passed += 1
        except Exception as e:
            print(f"❌ {method_name} FAILED: {e}")
            failed += 1
    print(f"\n{'=' * 60}")
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    if failed == 0:
        print("🎉 All tests passed! Enhanced system is ready for production.")
    else:
        print("⚠️  Some tests failed. Please review the issues before deployment.")
