#!/usr/bin/env python3
"""
SLO Monitoring Test Script

This script tests the SLO monitoring system by simulating various metrics
and evaluating them against defined SLOs.

Usage:
    python3 scripts/test_slo_monitoring.py [--simulate-load] [--duration SECONDS]
"""

import argparse
import random
import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from obs.metrics import get_slo_monitor, initialize_slo_monitoring
from obs.slo import SLO


def create_test_slos() -> list[SLO]:
    """Create test SLOs based on the SLO document."""
    return [
        # Response time SLOs
        SLO("p95_latency", 2.0),  # 95% of requests under 2 seconds
        SLO("vector_search_latency", 0.05),  # Vector search under 50ms
        # Performance SLOs
        SLO("cache_hit_rate", 0.60),  # 60% cache hit rate (inverted - higher is better)
        SLO("error_rate", 0.01),  # Less than 1% error rate
    ]


def simulate_normal_load(duration: int = 60) -> None:
    """Simulate normal system load."""
    print(f"🔄 Simulating normal load for {duration} seconds...")

    slo_monitor = get_slo_monitor()
    if not slo_monitor:
        print("❌ SLO monitor not initialized")
        return

    start_time = time.time()
    request_count = 0

    while time.time() - start_time < duration:
        # Simulate various request types
        endpoints = ["/analyze", "/search", "/health", "/metrics"]
        endpoint = random.choice(endpoints)

        # Simulate request duration (mostly under 2 seconds)
        if random.random() < 0.95:
            duration_sec = random.uniform(0.1, 1.5)  # 95% under 2 seconds
        else:
            duration_sec = random.uniform(2.0, 5.0)  # 5% over 2 seconds

        # Simulate status codes (mostly successful)
        if random.random() < 0.99:
            status_code = 200  # 99% success
        else:
            status_code = random.choice([400, 500, 503])  # 1% errors

        # Record the request
        slo_monitor.record_request(endpoint, duration_sec, status_code)
        request_count += 1

        # Simulate cache operations
        if random.random() < 0.7:  # 70% cache hit rate
            slo_monitor.record_cache_operation("vector_search", hit=True)
        else:
            slo_monitor.record_cache_operation("vector_search", hit=False)

        # Simulate vector search operations
        if random.random() < 0.8:  # 80% under 50ms
            search_duration = random.uniform(0.01, 0.04)
        else:
            search_duration = random.uniform(0.05, 0.2)

        results_count = random.randint(1, 10)
        slo_monitor.record_vector_search(search_duration, results_count)

        # Small delay between requests
        time.sleep(0.1)

    print(f"✅ Simulated {request_count} requests")


def simulate_high_load(duration: int = 30) -> None:
    """Simulate high system load with degraded performance."""
    print(f"🔥 Simulating high load for {duration} seconds...")

    slo_monitor = get_slo_monitor()
    if not slo_monitor:
        print("❌ SLO monitor not initialized")
        return

    start_time = time.time()
    request_count = 0

    while time.time() - start_time < duration:
        # Simulate high load with degraded performance
        endpoints = ["/analyze", "/search", "/health", "/metrics"]
        endpoint = random.choice(endpoints)

        # Simulate degraded performance (more requests over 2 seconds)
        if random.random() < 0.7:  # 70% under 2 seconds (degraded from 95%)
            duration_sec = random.uniform(0.1, 1.5)
        else:
            duration_sec = random.uniform(2.0, 8.0)  # Some very slow requests

        # Simulate higher error rate
        if random.random() < 0.95:  # 95% success (degraded from 99%)
            status_code = 200
        else:
            status_code = random.choice([400, 500, 503])

        # Record the request
        slo_monitor.record_request(endpoint, duration_sec, status_code)
        request_count += 1

        # Simulate degraded cache performance
        if random.random() < 0.4:  # 40% cache hit rate (degraded from 70%)
            slo_monitor.record_cache_operation("vector_search", hit=True)
        else:
            slo_monitor.record_cache_operation("vector_search", hit=False)

        # Simulate slower vector search
        if random.random() < 0.5:  # 50% under 50ms (degraded from 80%)
            search_duration = random.uniform(0.01, 0.04)
        else:
            search_duration = random.uniform(0.05, 0.3)

        results_count = random.randint(1, 10)
        slo_monitor.record_vector_search(search_duration, results_count)

        # Shorter delay for higher load
        time.sleep(0.05)

    print(f"✅ Simulated {request_count} high-load requests")


def evaluate_slos() -> None:
    """Evaluate current SLOs and display results."""
    slo_monitor = get_slo_monitor()
    if not slo_monitor:
        print("❌ SLO monitor not initialized")
        return

    print("\n📊 SLO Evaluation Results")
    print("=" * 50)

    evaluation = slo_monitor.evaluate_slos()
    metrics = evaluation["metrics"]
    slo_results = evaluation["slo_results"]

    # Display current metrics
    print("\n📈 Current Metrics:")
    print(
        f"  Error Rate: {metrics.get('error_rate', 0.0):.3f} ({metrics.get('error_rate', 0.0) * 100:.1f}%)"
    )
    print(f"  P95 Latency: {metrics.get('p95_latency', 0.0):.3f}s")
    print(
        f"  Cache Hit Rate: {metrics.get('cache_hit_rate', 0.0):.3f} ({metrics.get('cache_hit_rate', 0.0) * 100:.1f}%)"
    )
    print(f"  Vector Search Latency: {metrics.get('vector_search_latency', 0.0):.3f}s")

    # Display SLO results
    print("\n🎯 SLO Compliance:")
    for metric, passed in slo_results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        threshold = None

        # Get threshold for display
        for slo in slo_monitor.slos:
            if slo.metric == metric:
                threshold = slo.threshold
                break

        if threshold is not None:
            print(f"  {metric}: {status} (threshold: {threshold})")
        else:
            print(f"  {metric}: {status}")

    # Overall status
    all_passed = all(slo_results.values())
    overall_status = "✅ ALL SLOS MET" if all_passed else "❌ SOME SLOS FAILED"
    print(f"\n🏆 Overall Status: {overall_status}")


def generate_metrics_report() -> str:
    """Generate a detailed metrics report."""
    slo_monitor = get_slo_monitor()
    if not slo_monitor:
        return "❌ SLO monitor not initialized"

    summary = slo_monitor.get_metrics_summary()
    evaluation = summary["slo_evaluation"]

    report = f"""# SLO Monitoring Test Report
Generated: {time.strftime("%Y-%m-%d %H:%M:%S UTC")}

## Metrics Summary

### Request Metrics
- Total Requests: {summary["counters"].get("requests_total", 0)}
- Total Errors: {summary["counters"].get("request_errors_total", 0)}
- Error Rate: {evaluation["metrics"].get("error_rate", 0.0):.3f}

### Performance Metrics
- P95 Latency: {evaluation["metrics"].get("p95_latency", 0.0):.3f}s
- Cache Hit Rate: {evaluation["metrics"].get("cache_hit_rate", 0.0):.3f}
- Vector Search Latency: {evaluation["metrics"].get("vector_search_latency", 0.0):.3f}s

## SLO Compliance

"""

    for metric, passed in evaluation["slo_results"].items():
        status = "✅ PASS" if passed else "❌ FAIL"
        report += f"- {metric}: {status}\n"

    all_passed = all(evaluation["slo_results"].values())
    overall_status = "✅ ALL SLOS MET" if all_passed else "❌ SOME SLOS FAILED"
    report += f"\n## Overall Status: {overall_status}\n"

    return report


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="SLO Monitoring Test")
    parser.add_argument(
        "--simulate-load", action="store_true", help="Simulate system load"
    )
    parser.add_argument(
        "--duration", type=int, default=60, help="Simulation duration in seconds"
    )
    parser.add_argument(
        "--high-load", action="store_true", help="Simulate high load conditions"
    )
    parser.add_argument("--report", action="store_true", help="Generate metrics report")

    args = parser.parse_args()

    # Initialize SLO monitoring
    print("🚀 Initializing SLO Monitoring...")
    slos = create_test_slos()
    slo_monitor = initialize_slo_monitoring(slos)
    print(f"✅ Initialized with {len(slos)} SLOs")

    # Run simulations if requested
    if args.simulate_load:
        if args.high_load:
            simulate_high_load(args.duration)
        else:
            simulate_normal_load(args.duration)

    # Evaluate SLOs
    evaluate_slos()

    # Generate report if requested
    if args.report:
        report = generate_metrics_report()
        report_file = (
            Path(__file__).parent.parent / "docs" / "slo_monitoring_test_report.md"
        )
        with open(report_file, "w") as f:
            f.write(report)
        print(f"\n📄 Report saved to: {report_file}")


if __name__ == "__main__":
    main()
