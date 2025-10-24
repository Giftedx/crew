#!/usr/bin/env python3
"""
Performance Optimization Testing Script.

This script tests the performance optimization system including cache optimization,
model routing, and overall system performance improvements.
"""

import sys
import time
from pathlib import Path
from typing import Any


# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from obs.metrics import (
    MODEL_ROUTING_COUNT,
    MODEL_ROUTING_LATENCY,
    REQUEST_COUNT,
    REQUEST_LATENCY,
)
from ultimate_discord_intelligence_bot.services.performance_optimizer import (
    PerformanceOptimizer,
)


class PerformanceOptimizationTester:
    """Test performance optimization system."""

    def __init__(self):
        """Initialize the tester."""
        self.optimizer = PerformanceOptimizer()
        self.results: dict[str, Any] = {}

    def test_cache_optimization(self) -> dict[str, Any]:
        """Test cache optimization functionality."""
        print("\n💾 Testing Cache Optimization...")

        cache_results = {
            "tests_performed": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "test_details": {},
        }

        # Test 1: Cache key generation
        cache_results["tests_performed"] += 1
        try:
            cache_key = self.optimizer.cache_optimizer.generate_cache_key(
                operation="content_analysis",
                params={"url": "https://example.com", "type": "video"},
                tenant="test_tenant",
                workspace="test_workspace",
            )
            if cache_key and cache_key.startswith("cache:content_analysis:"):
                cache_results["tests_passed"] += 1
                cache_results["test_details"]["cache_key_generation"] = "✅ Working"
            else:
                cache_results["tests_failed"] += 1
                cache_results["test_details"]["cache_key_generation"] = "❌ Invalid key format"
        except Exception as e:
            cache_results["tests_failed"] += 1
            cache_results["test_details"]["cache_key_generation"] = f"❌ Exception: {e!s}"

        # Test 2: Cache strategy determination
        cache_results["tests_performed"] += 1
        try:
            strategy = self.optimizer.cache_optimizer.determine_cache_strategy(
                operation="content_analysis",
                data_size=2048,
                access_frequency="frequent",
            )
            if strategy and "ttl" in strategy and "compress" in strategy:
                cache_results["tests_passed"] += 1
                cache_results["test_details"]["cache_strategy"] = "✅ Working"
            else:
                cache_results["tests_failed"] += 1
                cache_results["test_details"]["cache_strategy"] = "❌ Invalid strategy"
        except Exception as e:
            cache_results["tests_failed"] += 1
            cache_results["test_details"]["cache_strategy"] = f"❌ Exception: {e!s}"

        # Test 3: Cache optimization
        cache_results["tests_performed"] += 1
        try:
            optimization_result = self.optimizer.cache_optimizer.optimize_cache_policies()
            if optimization_result.success:
                cache_results["tests_passed"] += 1
                cache_results["test_details"]["cache_optimization"] = "✅ Working"
            else:
                cache_results["tests_failed"] += 1
                cache_results["test_details"]["cache_optimization"] = f"❌ Failed: {optimization_result.error}"
        except Exception as e:
            cache_results["tests_failed"] += 1
            cache_results["test_details"]["cache_optimization"] = f"❌ Exception: {e!s}"

        # Test 4: Cache analytics
        cache_results["tests_performed"] += 1
        try:
            analytics = self.optimizer.cache_optimizer.get_cache_analytics()
            if analytics and "hit_rate" in analytics:
                cache_results["tests_passed"] += 1
                cache_results["test_details"]["cache_analytics"] = "✅ Working"
            else:
                cache_results["tests_failed"] += 1
                cache_results["test_details"]["cache_analytics"] = "❌ Invalid analytics"
        except Exception as e:
            cache_results["tests_failed"] += 1
            cache_results["test_details"]["cache_analytics"] = f"❌ Exception: {e!s}"

        return cache_results

    def test_model_routing(self) -> dict[str, Any]:
        """Test model routing functionality."""
        print("\n🔄 Testing Model Routing...")

        routing_results = {
            "tests_performed": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "test_details": {},
        }

        # Test 1: Simple task routing
        routing_results["tests_performed"] += 1
        try:
            start_time = time.time()
            routing_result = self.optimizer.model_router.route_model(
                task_type="content_analysis",
                task_complexity="simple",
                token_count=1000,
            )
            duration = time.time() - start_time
            MODEL_ROUTING_LATENCY.labels(model="test").observe(duration)

            if routing_result.success and routing_result.data:
                routing_results["tests_passed"] += 1
                MODEL_ROUTING_COUNT.labels(model=routing_result.data.selected_model).inc()
                routing_results["test_details"]["simple_routing"] = "✅ Working"
            else:
                routing_results["tests_failed"] += 1
                routing_results["test_details"]["simple_routing"] = f"❌ Failed: {routing_result.error}"
        except Exception as e:
            routing_results["tests_failed"] += 1
            routing_results["test_details"]["simple_routing"] = f"❌ Exception: {e!s}"

        # Test 2: Complex task routing
        routing_results["tests_performed"] += 1
        try:
            routing_result = self.optimizer.model_router.route_model(
                task_type="fact_checking",
                task_complexity="complex",
                token_count=5000,
                latency_requirement=2.0,
                cost_budget=0.01,
                accuracy_requirement=0.9,
            )

            if routing_result.success and routing_result.data:
                routing_results["tests_passed"] += 1
                routing_results["test_details"]["complex_routing"] = "✅ Working"
            else:
                routing_results["tests_failed"] += 1
                routing_results["test_details"]["complex_routing"] = f"❌ Failed: {routing_result.error}"
        except Exception as e:
            routing_results["tests_failed"] += 1
            routing_results["test_details"]["complex_routing"] = f"❌ Exception: {e!s}"

        # Test 3: Routing analytics
        routing_results["tests_performed"] += 1
        try:
            analytics = self.optimizer.model_router.get_routing_analytics()
            if analytics and "total_requests" in analytics:
                routing_results["tests_passed"] += 1
                routing_results["test_details"]["routing_analytics"] = "✅ Working"
            else:
                routing_results["tests_failed"] += 1
                routing_results["test_details"]["routing_analytics"] = "❌ Invalid analytics"
        except Exception as e:
            routing_results["tests_failed"] += 1
            routing_results["test_details"]["routing_analytics"] = f"❌ Exception: {e!s}"

        # Test 4: Routing optimization
        routing_results["tests_performed"] += 1
        try:
            optimization_result = self.optimizer.model_router.optimize_routing_policies()
            if optimization_result.success:
                routing_results["tests_passed"] += 1
                routing_results["test_details"]["routing_optimization"] = "✅ Working"
            else:
                routing_results["tests_failed"] += 1
                routing_results["test_details"]["routing_optimization"] = f"❌ Failed: {optimization_result.error}"
        except Exception as e:
            routing_results["tests_failed"] += 1
            routing_results["test_details"]["routing_optimization"] = f"❌ Exception: {e!s}"

        return routing_results

    def test_combined_optimization(self) -> dict[str, Any]:
        """Test combined cache and routing optimization."""
        print("\n🚀 Testing Combined Optimization...")

        combined_results = {
            "tests_performed": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "test_details": {},
        }

        # Test 1: Simple request optimization
        combined_results["tests_performed"] += 1
        try:
            start_time = time.time()
            optimization_result = self.optimizer.optimize_request(
                operation="content_analysis",
                task_type="content_analysis",
                task_complexity="simple",
                params={"url": "https://example.com", "type": "video"},
                tenant="test_tenant",
                workspace="test_workspace",
                token_count=1000,
            )
            duration = time.time() - start_time
            REQUEST_LATENCY.labels(method="POST", endpoint="/optimize").observe(duration)

            if optimization_result.success:
                combined_results["tests_passed"] += 1
                REQUEST_COUNT.labels(method="POST", endpoint="/optimize").inc()
                combined_results["test_details"]["simple_optimization"] = "✅ Working"
            else:
                combined_results["tests_failed"] += 1
                combined_results["test_details"]["simple_optimization"] = f"❌ Failed: {optimization_result.error}"
        except Exception as e:
            combined_results["tests_failed"] += 1
            combined_results["test_details"]["simple_optimization"] = f"❌ Exception: {e!s}"

        # Test 2: Complex request optimization
        combined_results["tests_performed"] += 1
        try:
            optimization_result = self.optimizer.optimize_request(
                operation="fact_checking",
                task_type="fact_checking",
                task_complexity="complex",
                params={"content": "test content", "sources": ["source1", "source2"]},
                tenant="test_tenant",
                workspace="test_workspace",
                token_count=5000,
                latency_requirement=2.0,
                cost_budget=0.01,
                accuracy_requirement=0.9,
            )

            if optimization_result.success:
                combined_results["tests_passed"] += 1
                combined_results["test_details"]["complex_optimization"] = "✅ Working"
            else:
                combined_results["tests_failed"] += 1
                combined_results["test_details"]["complex_optimization"] = f"❌ Failed: {optimization_result.error}"
        except Exception as e:
            combined_results["tests_failed"] += 1
            combined_results["test_details"]["complex_optimization"] = f"❌ Exception: {e!s}"

        # Test 3: System optimization
        combined_results["tests_performed"] += 1
        try:
            system_optimization = self.optimizer.optimize_system_performance()
            if system_optimization.success:
                combined_results["tests_passed"] += 1
                combined_results["test_details"]["system_optimization"] = "✅ Working"
            else:
                combined_results["tests_failed"] += 1
                combined_results["test_details"]["system_optimization"] = f"❌ Failed: {system_optimization.error}"
        except Exception as e:
            combined_results["tests_failed"] += 1
            combined_results["test_details"]["system_optimization"] = f"❌ Exception: {e!s}"

        # Test 4: Performance analytics
        combined_results["tests_performed"] += 1
        try:
            analytics = self.optimizer.get_performance_analytics()
            if analytics and "overall_performance" in analytics:
                combined_results["tests_passed"] += 1
                combined_results["test_details"]["performance_analytics"] = "✅ Working"
            else:
                combined_results["tests_failed"] += 1
                combined_results["test_details"]["performance_analytics"] = "❌ Invalid analytics"
        except Exception as e:
            combined_results["tests_failed"] += 1
            combined_results["test_details"]["performance_analytics"] = f"❌ Exception: {e!s}"

        return combined_results

    def test_performance_benchmarks(self) -> dict[str, Any]:
        """Test performance benchmarks."""
        print("\n📊 Testing Performance Benchmarks...")

        benchmark_results = {
            "benchmarks_performed": 0,
            "benchmarks_passed": 0,
            "benchmarks_failed": 0,
            "benchmark_details": {},
        }

        # Benchmark 1: Cache performance
        benchmark_results["benchmarks_performed"] += 1
        try:
            start_time = time.time()
            for i in range(100):
                self.optimizer.cache_optimizer.generate_cache_key(
                    operation="test_operation",
                    params={"test": f"value_{i}"},
                    tenant="benchmark_tenant",
                    workspace="benchmark_workspace",
                )
            cache_duration = time.time() - start_time

            if cache_duration < 1.0:  # Should complete in under 1 second
                benchmark_results["benchmarks_passed"] += 1
                benchmark_results["benchmark_details"]["cache_performance"] = (
                    f"✅ {cache_duration:.3f}s for 100 operations"
                )
            else:
                benchmark_results["benchmarks_failed"] += 1
                benchmark_results["benchmark_details"]["cache_performance"] = f"❌ Too slow: {cache_duration:.3f}s"
        except Exception as e:
            benchmark_results["benchmarks_failed"] += 1
            benchmark_results["benchmark_details"]["cache_performance"] = f"❌ Exception: {e!s}"

        # Benchmark 2: Routing performance
        benchmark_results["benchmarks_performed"] += 1
        try:
            start_time = time.time()
            for i in range(50):
                self.optimizer.model_router.route_model(
                    task_type="content_analysis",
                    task_complexity="moderate",
                    token_count=1000 + i * 100,
                )
            routing_duration = time.time() - start_time

            if routing_duration < 2.0:  # Should complete in under 2 seconds
                benchmark_results["benchmarks_passed"] += 1
                benchmark_results["benchmark_details"]["routing_performance"] = (
                    f"✅ {routing_duration:.3f}s for 50 operations"
                )
            else:
                benchmark_results["benchmarks_failed"] += 1
                benchmark_results["benchmark_details"]["routing_performance"] = f"❌ Too slow: {routing_duration:.3f}s"
        except Exception as e:
            benchmark_results["benchmarks_failed"] += 1
            benchmark_results["benchmark_details"]["routing_performance"] = f"❌ Exception: {e!s}"

        # Benchmark 3: Combined optimization performance
        benchmark_results["benchmarks_performed"] += 1
        try:
            start_time = time.time()
            for i in range(25):
                self.optimizer.optimize_request(
                    operation="test_optimization",
                    task_type="content_analysis",
                    task_complexity="simple",
                    params={"test": f"value_{i}"},
                    tenant="benchmark_tenant",
                    workspace="benchmark_workspace",
                    token_count=1000,
                )
            optimization_duration = time.time() - start_time

            if optimization_duration < 5.0:  # Should complete in under 5 seconds
                benchmark_results["benchmarks_passed"] += 1
                benchmark_results["benchmark_details"]["optimization_performance"] = (
                    f"✅ {optimization_duration:.3f}s for 25 operations"
                )
            else:
                benchmark_results["benchmarks_failed"] += 1
                benchmark_results["benchmark_details"]["optimization_performance"] = (
                    f"❌ Too slow: {optimization_duration:.3f}s"
                )
        except Exception as e:
            benchmark_results["benchmarks_failed"] += 1
            benchmark_results["benchmark_details"]["optimization_performance"] = f"❌ Exception: {e!s}"

        return benchmark_results

    def run_all_tests(self) -> dict[str, Any]:
        """Run all performance optimization tests."""
        print("🚀 Starting Performance Optimization Tests...")

        start_time = time.time()

        # Run all test suites
        self.results["cache_optimization"] = self.test_cache_optimization()
        self.results["model_routing"] = self.test_model_routing()
        self.results["combined_optimization"] = self.test_combined_optimization()
        self.results["performance_benchmarks"] = self.test_performance_benchmarks()

        # Calculate overall results
        total_tests = sum(
            suite.get("tests_performed", 0) + suite.get("benchmarks_performed", 0) for suite in self.results.values()
        )

        total_passed = sum(
            suite.get("tests_passed", 0) + suite.get("benchmarks_passed", 0) for suite in self.results.values()
        )

        total_failed = sum(
            suite.get("tests_failed", 0) + suite.get("benchmarks_failed", 0) for suite in self.results.values()
        )

        self.results["summary"] = {
            "total_tests": total_tests,
            "total_passed": total_passed,
            "total_failed": total_failed,
            "success_rate": total_passed / total_tests if total_tests > 0 else 0.0,
            "test_duration": time.time() - start_time,
        }

        return self.results

    def generate_report(self) -> str:
        """Generate a comprehensive test report."""
        report = []
        report.append("# Performance Optimization Test Report")
        report.append("")
        report.append(f"**Test Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # Summary
        summary = self.results.get("summary", {})
        report.append("## Summary")
        report.append("")
        report.append(f"- **Total Tests:** {summary.get('total_tests', 0)}")
        report.append(f"- **Passed:** {summary.get('total_passed', 0)}")
        report.append(f"- **Failed:** {summary.get('total_failed', 0)}")
        report.append(f"- **Success Rate:** {summary.get('success_rate', 0.0):.2%}")
        report.append(f"- **Test Duration:** {summary.get('test_duration', 0.0):.2f}s")
        report.append("")

        # Detailed results
        for suite_name, suite_results in self.results.items():
            if suite_name == "summary":
                continue

            report.append(f"## {suite_name.replace('_', ' ').title()}")
            report.append("")

            # Suite summary
            suite_tests = suite_results.get("tests_performed", 0) + suite_results.get("benchmarks_performed", 0)
            suite_passed = suite_results.get("tests_passed", 0) + suite_results.get("benchmarks_passed", 0)
            suite_failed = suite_results.get("tests_failed", 0) + suite_results.get("benchmarks_failed", 0)

            report.append(f"- **Tests:** {suite_tests}")
            report.append(f"- **Passed:** {suite_passed}")
            report.append(f"- **Failed:** {suite_failed}")
            report.append("")

            # Detailed results
            details = suite_results.get("test_details", {}) or suite_results.get("benchmark_details", {})
            for item_name, status in details.items():
                report.append(f"- **{item_name}:** {status}")
            report.append("")

        return "\n".join(report)


def main() -> None:
    """Main function."""
    tester = PerformanceOptimizationTester()

    # Run all tests
    results = tester.run_all_tests()

    # Generate and save report
    report = tester.generate_report()

    report_path = Path("docs/performance_optimization_test_report.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, "w") as f:
        f.write(report)

    print(f"\n✅ Performance optimization test report saved: {report_path}")

    # Print summary
    summary = results.get("summary", {})
    print("\n📊 Test Summary:")
    print(f"  Total Tests: {summary.get('total_tests', 0)}")
    print(f"  Passed: {summary.get('total_passed', 0)}")
    print(f"  Failed: {summary.get('total_failed', 0)}")
    print(f"  Success Rate: {summary.get('success_rate', 0.0):.2%}")
    print(f"  Duration: {summary.get('test_duration', 0.0):.2f}s")


if __name__ == "__main__":
    main()
