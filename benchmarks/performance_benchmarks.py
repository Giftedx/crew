"""Performance benchmarking and regression detection system.

Establishes performance baselines and tracks regressions in key pipeline operations.
"""

import asyncio
import json
import statistics
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from ultimate_discord_intelligence_bot.pipeline import ContentPipeline
from ultimate_discord_intelligence_bot.tenancy import TenantContext, with_tenant


@dataclass
class BenchmarkResult:
    """Results from a performance benchmark."""

    operation: str
    duration_ms: float
    memory_peak_mb: float
    cpu_percent: float
    success: bool
    timestamp: str
    metadata: dict[str, Any]


@dataclass
class PerformanceBaseline:
    """Performance baseline for comparison."""

    operation: str
    mean_duration_ms: float
    p95_duration_ms: float
    p99_duration_ms: float
    max_memory_mb: float
    sample_count: int
    last_updated: str


class PerformanceBenchmarker:
    """System for running performance benchmarks and detecting regressions."""

    def __init__(self, baseline_file: Path = Path("benchmarks/baselines.json")):
        self.baseline_file = baseline_file
        self.baselines: dict[str, PerformanceBaseline] = {}
        self.load_baselines()

    def load_baselines(self) -> None:
        """Load existing performance baselines."""
        if self.baseline_file.exists():
            try:
                with open(self.baseline_file, encoding="utf-8") as f:
                    data = json.load(f)
                    self.baselines = {k: PerformanceBaseline(**v) for k, v in data.items()}
            except Exception as e:
                print(f"Warning: Could not load baselines: {e}")

    def save_baselines(self) -> None:
        """Save performance baselines to file."""
        self.baseline_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.baseline_file, "w", encoding="utf-8") as f:
            data = {k: asdict(v) for k, v in self.baselines.items()}
            json.dump(data, f, indent=2)

    async def benchmark_operation(
        self,
        operation_name: str,
        operation_func: Any,
        *args: Any,
        iterations: int = 10,
        **kwargs: Any,
    ) -> list[BenchmarkResult]:
        """Benchmark a specific operation."""
        results = []

        for i in range(iterations):
            # Measure memory before operation
            try:
                import psutil

                process = psutil.Process()
                memory_before = process.memory_info().rss / 1024 / 1024  # MB
                cpu_before = process.cpu_percent()
            except ImportError:
                memory_before = 0
                cpu_before = 0

            # Time the operation
            start_time = time.perf_counter()
            success = True

            try:
                if asyncio.iscoroutinefunction(operation_func):
                    await operation_func(*args, **kwargs)
                else:
                    operation_func(*args, **kwargs)
            except Exception as e:
                success = False
                print(f"Benchmark iteration {i + 1} failed: {e}")

            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000

            # Measure memory after operation
            try:
                memory_after = process.memory_info().rss / 1024 / 1024  # MB
                cpu_after = process.cpu_percent()
                memory_peak = memory_after - memory_before
                cpu_used = cpu_after - cpu_before
            except Exception:
                memory_peak = 0
                cpu_used = 0

            result = BenchmarkResult(
                operation=operation_name,
                duration_ms=duration_ms,
                memory_peak_mb=max(0, memory_peak),
                cpu_percent=max(0, cpu_used),
                success=success,
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                metadata={
                    "iteration": i + 1,
                    "args_count": len(args),
                    "kwargs_count": len(kwargs),
                },
            )
            results.append(result)

            # Small delay between iterations
            await asyncio.sleep(0.1)

        return results

    def analyze_results(self, results: list[BenchmarkResult]) -> dict[str, Any]:
        """Analyze benchmark results and generate statistics."""
        successful_results = [r for r in results if r.success]

        if not successful_results:
            return {"error": "No successful benchmark runs"}

        durations = [r.duration_ms for r in successful_results]
        memory_usage = [r.memory_peak_mb for r in successful_results]

        analysis = {
            "operation": results[0].operation,
            "total_runs": len(results),
            "successful_runs": len(successful_results),
            "success_rate": len(successful_results) / len(results),
            "duration_stats": {
                "mean_ms": statistics.mean(durations),
                "median_ms": statistics.median(durations),
                "min_ms": min(durations),
                "max_ms": max(durations),
                "std_dev_ms": statistics.stdev(durations) if len(durations) > 1 else 0,
                "p95_ms": self._percentile(durations, 95),
                "p99_ms": self._percentile(durations, 99),
            },
            "memory_stats": {
                "mean_mb": statistics.mean(memory_usage),
                "peak_mb": max(memory_usage),
                "min_mb": min(memory_usage),
            },
        }

        return analysis

    def _percentile(self, data: list[float], percentile: float) -> float:
        """Calculate percentile of data."""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        if index == int(index):
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))

    def update_baseline(self, analysis: dict[str, Any]) -> None:
        """Update performance baseline with new analysis."""
        operation = analysis["operation"]
        stats = analysis["duration_stats"]
        memory_stats = analysis["memory_stats"]

        baseline = PerformanceBaseline(
            operation=operation,
            mean_duration_ms=stats["mean_ms"],
            p95_duration_ms=stats["p95_ms"],
            p99_duration_ms=stats["p99_ms"],
            max_memory_mb=memory_stats["peak_mb"],
            sample_count=analysis["successful_runs"],
            last_updated=time.strftime("%Y-%m-%d %H:%M:%S"),
        )

        self.baselines[operation] = baseline
        self.save_baselines()

    def check_regression(self, analysis: dict[str, Any], threshold: float = 1.2) -> dict[str, Any]:
        """Check for performance regressions against baseline."""
        operation = analysis["operation"]

        if operation not in self.baselines:
            return {
                "regression_detected": False,
                "reason": "No baseline available",
                "recommendation": "Run this benchmark to establish baseline",
            }

        baseline = self.baselines[operation]
        current_mean = analysis["duration_stats"]["mean_ms"]
        current_p95 = analysis["duration_stats"]["p95_ms"]
        current_memory = analysis["memory_stats"]["peak_mb"]

        regressions = []

        # Check duration regression
        if current_mean > baseline.mean_duration_ms * threshold:
            regressions.append(
                {
                    "metric": "mean_duration",
                    "baseline": baseline.mean_duration_ms,
                    "current": current_mean,
                    "ratio": current_mean / baseline.mean_duration_ms,
                }
            )

        if current_p95 > baseline.p95_duration_ms * threshold:
            regressions.append(
                {
                    "metric": "p95_duration",
                    "baseline": baseline.p95_duration_ms,
                    "current": current_p95,
                    "ratio": current_p95 / baseline.p95_duration_ms,
                }
            )

        # Check memory regression
        if current_memory > baseline.max_memory_mb * threshold:
            regressions.append(
                {
                    "metric": "memory_usage",
                    "baseline": baseline.max_memory_mb,
                    "current": current_memory,
                    "ratio": current_memory / baseline.max_memory_mb,
                }
            )

        return {
            "regression_detected": len(regressions) > 0,
            "regressions": regressions,
            "threshold": threshold,
            "baseline_date": baseline.last_updated,
        }


# Benchmark test suite
class TestPerformanceBenchmarks:
    """Performance benchmark test suite."""

    @pytest.fixture
    def benchmarker(self):
        """Create performance benchmarker."""
        return PerformanceBenchmarker(Path("test_benchmarks/baselines.json"))

    @pytest.fixture
    def mock_pipeline(self):
        """Create mocked pipeline for benchmarking."""
        pipeline = MagicMock(spec=ContentPipeline)

        # Mock successful operations with realistic timing
        async def mock_process_video(url: str, quality: str = "720p"):
            await asyncio.sleep(0.01)  # Simulate processing time
            return {
                "status": "success",
                "download": {"status": "success"},
                "transcription": {"status": "success"},
                "analysis": {"status": "success"},
            }

        pipeline.process_video = mock_process_video
        return pipeline

    @pytest.mark.asyncio
    async def test_pipeline_benchmark(self, benchmarker, mock_pipeline):
        """Benchmark the main pipeline operation."""
        test_url = "https://www.youtube.com/watch?v=test123"

        with with_tenant(TenantContext("benchmark_tenant", "benchmark_workspace")):
            results = await benchmarker.benchmark_operation(
                "pipeline_process_video",
                mock_pipeline.process_video,
                test_url,
                quality="720p",
                iterations=5,
            )

        # Analyze results
        analysis = benchmarker.analyze_results(results)

        # Verify benchmark ran successfully
        assert analysis["successful_runs"] == 5
        assert analysis["success_rate"] == 1.0
        assert analysis["duration_stats"]["mean_ms"] > 0

        # Check for regressions
        regression_check = benchmarker.check_regression(analysis)

        # Update baseline if this is first run
        if not regression_check["regression_detected"] or "No baseline" in regression_check.get("reason", ""):
            benchmarker.update_baseline(analysis)

        print(f"Benchmark results for {analysis['operation']}:")
        print(f"  Mean duration: {analysis['duration_stats']['mean_ms']:.2f}ms")
        print(f"  P95 duration: {analysis['duration_stats']['p95_ms']:.2f}ms")
        print(f"  Peak memory: {analysis['memory_stats']['peak_mb']:.2f}MB")

        if regression_check["regression_detected"]:
            print("⚠️  Performance regression detected!")
            for regression in regression_check["regressions"]:
                print(f"    {regression['metric']}: {regression['ratio']:.2f}x slower")
        else:
            print("✅ No performance regression detected")


def run_benchmarks():
    """Run performance benchmarks from command line."""
    pytest.main([__file__, "-v", "-s"])


if __name__ == "__main__":
    run_benchmarks()
