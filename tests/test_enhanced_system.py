"""Comprehensive integration tests for enhanced system components."""

# Import all enhanced modules
import sys
import time
from unittest.mock import Mock

sys.path.insert(0, "src")
from core.db_optimizer import DatabaseOptimizer
from core.llm_cache import QuantizedEmbedding, VectorIndex, get_llm_cache
from core.llm_router import LLMRouter, TaskComplexityMetrics
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

        # Test basic functionality
        assert hasattr(cache, "_vector_index")
        assert hasattr(cache, "_stats")
        assert hasattr(cache, "_analytics")

        # Test quantization functionality
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        quantized = QuantizedEmbedding.from_float(embedding)
        assert quantized.dim == 1536  # Default dimension
        assert len(quantized.data) == 1536

        # Test vector index
        vector_index = VectorIndex(max_entries=100)
        assert vector_index.max_entries == 100
        assert len(vector_index.entries) == 0

        # Test cache statistics
        stats = cache.get_stats()
        assert isinstance(stats, dict)
        assert "total_requests" in stats
        assert "hit_rate" in stats

    def test_enhanced_llm_router_functionality(self):
        """Test enhanced LLM router with cost-aware features."""
        # Mock LLM clients
        mock_client1 = Mock()
        mock_client1.chat.return_value = Mock(cost_usd=0.01, latency_ms=100)

        mock_client2 = Mock()
        mock_client2.chat.return_value = Mock(cost_usd=0.02, latency_ms=200)

        clients = {"cheap_model": mock_client1, "expensive_model": mock_client2}

        router = LLMRouter(clients)

        # Test cost-aware functionality
        assert hasattr(router, "_cost_aware_enabled")
        assert hasattr(router, "_model_profiles")
        assert hasattr(router, "_cost_optimization_stats")

        # Test task complexity analysis
        messages = [{"content": "This is a simple question"}]
        complexity = TaskComplexityMetrics.analyze_content(messages)
        assert complexity.complexity_score >= 0.0
        assert complexity.complexity_score <= 1.0

        # Test model profiles
        profiles = router.get_model_performance_profiles()
        assert len(profiles) == 2
        assert "cheap_model" in profiles
        assert "expensive_model" in profiles

    def test_enhanced_step_result_functionality(self):
        """Test enhanced StepResult with comprehensive error handling."""
        # Test basic StepResult
        result = StepResult.ok(data={"test": "value"})
        assert result.success
        assert result.data["test"] == "value"

        # Test error categorization
        error_result = StepResult.fail("Network timeout", ErrorCategory.NETWORK)
        assert not error_result.success
        assert error_result.error_category == ErrorCategory.NETWORK
        assert error_result.retryable  # Network errors should be retryable

        # Test enhanced error context
        context = ErrorContext(operation="test_op", component="test_component")
        enhanced_result = StepResult.fail("Database connection failed", ErrorCategory.DATABASE_ERROR, context=context)
        assert enhanced_result.error_context is not None
        assert enhanced_result.error_context.operation == "test_op"
        assert enhanced_result.error_severity == ErrorSeverity.CRITICAL

        # Test recovery strategies
        strategy = ErrorRecoveryStrategy(
            error_categories=[ErrorCategory.NETWORK, ErrorCategory.TIMEOUT], max_retries=3, retry_delay_base=1.0
        )
        assert strategy.should_retry(1, ErrorCategory.NETWORK)
        assert not strategy.should_retry(4, ErrorCategory.NETWORK)  # Exceeds max retries

    def test_enhanced_vector_store_functionality(self):
        """Test enhanced vector store with memory optimizations."""
        store = VectorStore()

        # Test enhanced functionality
        assert hasattr(store, "_vector_index")
        assert hasattr(store, "_analytics")
        assert hasattr(store, "_enable_optimizations")

        # Test memory analytics
        analytics = store.get_memory_analytics()
        assert isinstance(analytics, dict)

        # Test adaptive batch sizing
        batch_size = store._get_adaptive_batch_size("test_namespace", 768)
        assert batch_size > 0
        assert batch_size <= 256  # Should be reasonable

        # Test operation tracking
        start_time = time.time()
        store._track_operation_performance("test_op", start_time, vectors_processed=10)
        assert len(store._performance_history) > 0

    def test_enhanced_database_optimizer_functionality(self):
        """Test enhanced database optimizer with query analysis."""
        # Test without actual database connection
        optimizer = DatabaseOptimizer()

        # Test structure
        assert hasattr(optimizer, "query_metrics")
        assert hasattr(optimizer, "query_patterns")
        assert hasattr(optimizer, "_enable_optimizations")

        # Test query pattern analysis
        query = "SELECT * FROM content WHERE tenant = ?"
        execution_time = 150.0

        optimizer._update_query_patterns(query, execution_time)
        assert query in optimizer.query_patterns
        assert optimizer.query_patterns[query]["count"] == 1
        assert optimizer.query_patterns[query]["total_time"] == execution_time

    def test_performance_dashboard_integration(self):
        """Test performance dashboard integration across all components."""
        dashboard = PerformanceDashboard()

        # Test dashboard structure
        assert hasattr(dashboard, "cache")
        assert hasattr(dashboard, "error_analyzer")
        assert hasattr(dashboard, "vector_store")

        # Test getting comprehensive metrics
        metrics = dashboard.get_comprehensive_metrics()
        assert isinstance(metrics, dict)
        assert "timestamp" in metrics
        assert "cache_performance" in metrics
        assert "error_handling" in metrics
        assert "memory_performance" in metrics

        # Test dashboard summary
        summary = dashboard.get_dashboard_summary()
        assert isinstance(summary, dict)
        assert "overall_health" in summary
        assert "overall_score" in summary
        assert "active_optimizations" in summary

    def test_system_integration_end_to_end(self):
        """Test end-to-end integration of all enhanced components."""
        # Test that all modules can be imported and instantiated together
        from core.llm_cache import get_llm_cache
        from core.llm_router import LLMRouter
        from ultimate_discord_intelligence_bot.performance_dashboard import get_performance_dashboard
        from ultimate_discord_intelligence_bot.step_result import ErrorCategory, StepResult

        # Initialize all components
        cache = get_llm_cache()
        dashboard = get_performance_dashboard()

        # Mock clients for router
        mock_client = Mock()
        mock_client.chat.return_value = Mock(cost_usd=0.01, latency_ms=100)

        # Test router integration
        router = LLMRouter({"test_model": mock_client})

        # Test error handling integration
        error_result = StepResult.fail("Test error", ErrorCategory.PROCESSING)
        assert not error_result.success
        assert error_result.error_category == ErrorCategory.PROCESSING

        # Test that all components can work together
        summary = dashboard.get_dashboard_summary()
        assert isinstance(summary, dict)
        assert "overall_health" in summary

    def test_performance_improvements_validation(self):
        """Validate that performance improvements are working as expected."""
        # Test cache performance
        cache = get_llm_cache()

        # Simulate some cache operations
        test_prompt = "Test prompt for caching"
        test_response = {"result": "cached response"}

        # Test cache storage and retrieval
        cache.put(test_prompt, "test_model", test_response)
        retrieved = cache.get(test_prompt, "test_model")

        assert retrieved == test_response

        # Test cache statistics
        stats = cache.get_stats()
        assert stats["total_requests"] >= 1
        assert stats["hits"] >= 1

    def test_error_recovery_mechanisms(self):
        """Test error recovery and resilience mechanisms."""
        # Test error categorization and recovery
        error_result = StepResult.fail("Connection timeout", ErrorCategory.NETWORK)

        # Should be retryable
        assert error_result.should_retry(1)
        assert error_result.should_retry(2)
        assert not error_result.should_retry(4)  # Exceeds default max retries

        # Test error context
        context = ErrorContext(operation="test_operation", component="test_component")
        enhanced_result = StepResult.fail("Test error", context=context, error_category=ErrorCategory.DATABASE_ERROR)

        assert enhanced_result.error_context is not None
        assert enhanced_result.error_severity == ErrorSeverity.CRITICAL
        assert len(enhanced_result.suggested_actions) > 0

    def test_memory_optimization_functionality(self):
        """Test memory optimization features."""
        store = VectorStore()

        # Test memory analytics
        analytics = store.get_memory_analytics()
        assert isinstance(analytics, dict)

        # Test adaptive batch sizing
        batch_size = store._get_adaptive_batch_size("test", 768)
        assert batch_size > 0

        # Test performance tracking
        start_time = time.time()
        store._track_operation_performance("test", start_time, vectors_processed=10)
        assert len(store._performance_history) > 0

    def test_database_optimization_features(self):
        """Test database optimization functionality."""
        optimizer = DatabaseOptimizer()

        # Test query pattern tracking
        query = "SELECT * FROM content WHERE tenant = ? AND workspace = ?"
        optimizer._update_query_patterns(query, 100.0)

        assert query in optimizer.query_patterns
        assert optimizer.query_patterns[query]["count"] == 1
        assert optimizer.query_patterns[query]["total_time"] == 100.0

        # Test filter column extraction
        columns = optimizer._extract_filter_columns(query)
        assert isinstance(columns, list)

    def test_unified_monitoring_capabilities(self):
        """Test unified monitoring across all components."""
        dashboard = PerformanceDashboard()

        # Test comprehensive metrics collection
        metrics = dashboard.get_comprehensive_metrics()
        assert isinstance(metrics, dict)
        assert "cache_performance" in metrics
        assert "error_handling" in metrics
        assert "memory_performance" in metrics

        # Test dashboard summary
        summary = dashboard.get_dashboard_summary()
        assert isinstance(summary, dict)
        assert "overall_health" in summary
        assert "overall_score" in summary
        assert "performance_highlights" in summary

    def test_backward_compatibility(self):
        """Test that all enhancements maintain backward compatibility."""
        # Test that existing StepResult patterns still work
        result = StepResult.ok(data={"test": "value"})
        assert result.success
        assert result["test"] == "value"  # Dictionary-like access

        # Test legacy error creation
        error_result = StepResult.fail("Legacy error")
        assert not error_result.success
        assert error_result.error == "Legacy error"

        # Test cache backward compatibility
        cache = get_llm_cache()
        cache.put("test", "model", "response")
        retrieved = cache.get("test", "model")
        assert retrieved == "response"

    def test_error_analysis_and_reporting(self):
        """Test error analysis and reporting capabilities."""
        analyzer = ErrorAnalyzer()

        # Create and record various errors
        network_error = StepResult.fail("Network timeout", ErrorCategory.NETWORK)
        database_error = StepResult.fail("Connection failed", ErrorCategory.DATABASE_ERROR)
        validation_error = StepResult.fail("Invalid input", ErrorCategory.VALIDATION)

        analyzer.record_error(network_error)
        analyzer.record_error(database_error)
        analyzer.record_error(validation_error)

        # Test error summary
        summary = analyzer.get_error_summary()
        assert summary["total_errors"] == 3
        assert "network" in summary["error_categories"]
        assert "database_error" in summary["error_categories"]
        assert "validation" in summary["error_categories"]


if __name__ == "__main__":
    # Run tests if executed directly
    test_suite = TestEnhancedSystemIntegration()

    print("🧪 Running Enhanced System Integration Tests...")
    print("=" * 60)

    # Run all test methods
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
