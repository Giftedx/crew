#!/usr/bin/env python3
"""
PostgreSQL Migration Benchmark Script

This script benchmarks the performance of the PostgreSQL migration
and validates that p99 latency targets are met (<100ms).
"""

import argparse
import json
import logging
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path


# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ultimate_discord_intelligence_bot.core.store_adapter import (
    CreatorProfile,
    Debate,
    KGNode,
    MemoryItem,
    UnifiedStoreManager,
)
from ultimate_discord_intelligence_bot.step_result import StepResult


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class PostgreSQLBenchmark:
    """Benchmark PostgreSQL migration performance."""

    def __init__(self, postgresql_url: str):
        self.postgresql_url = postgresql_url
        self.store_manager = None
        self.results = {}

    def initialize(self) -> StepResult:
        """Initialize the store manager."""
        try:
            self.store_manager = UnifiedStoreManager(self.postgresql_url)
            result = self.store_manager.initialize()
            if not result.success:
                return result
            logger.info("Store manager initialized for benchmarking")
            return StepResult.ok(data={"message": "Benchmark initialized"})
        except Exception as e:
            logger.error(f"Failed to initialize benchmark: {e}")
            return StepResult.fail(f"Failed to initialize benchmark: {e!s}")

    def generate_test_data(
        self, count: int
    ) -> tuple[list[MemoryItem], list[Debate], list[KGNode], list[CreatorProfile]]:
        """Generate test data for benchmarking."""
        logger.info(f"Generating {count} test records for each store type")

        memory_items = []
        debates = []
        kg_nodes = []
        profiles = []

        for i in range(count):
            # Memory items
            memory_item = MemoryItem(
                id=None,
                tenant=f"benchmark_tenant_{i % 10}",
                workspace=f"benchmark_workspace_{i % 5}",
                type="benchmark",
                content_json=f'{{"text": "Benchmark content {i}", "metadata": {{"index": {i}}}}}',
                embedding_json=f"[{0.1 + i * 0.001}, {0.2 + i * 0.001}, {0.3 + i * 0.001}]",
                ts_created=datetime.now().isoformat(),
                ts_last_used=datetime.now().isoformat(),
                retention_policy="benchmark",
                decay_score=1.0 - (i * 0.001),
                pinned=i % 2,
                archived=0,
            )
            memory_items.append(memory_item)

            # Debates
            debate = Debate(
                id=None,
                tenant=f"benchmark_tenant_{i % 10}",
                workspace=f"benchmark_workspace_{i % 5}",
                query=f"Benchmark debate query {i}",
                panel_config_json=f'{{"agents": ["agent_{i}", "agent_{i + 1}"]}}',
                n_rounds=3,
                final_output=f"Benchmark debate output {i}",
                created_at=datetime.now().isoformat(),
            )
            debates.append(debate)

            # KG nodes
            kg_node = KGNode(
                id=None,
                tenant=f"benchmark_tenant_{i % 10}",
                type=f"benchmark_type_{i % 3}",
                name=f"benchmark_node_{i}",
                attrs_json=f'{{"index": {i}, "category": "benchmark", "value": {i * 10}}}',
                created_at=datetime.now().isoformat(),
            )
            kg_nodes.append(kg_node)

            # Profiles
            profile = CreatorProfile(
                name=f"benchmark_profile_{i}",
                data={
                    "platforms": ["youtube", "tiktok", "instagram"],
                    "subscribers": 1000000 + i,
                    "content_types": ["podcast", "shorts"],
                    "index": i,
                },
            )
            profiles.append(profile)

        logger.info(
            f"Generated {len(memory_items)} memory items, {len(debates)} debates, "
            f"{len(kg_nodes)} KG nodes, {len(profiles)} profiles"
        )
        return memory_items, debates, kg_nodes, profiles

    def benchmark_memory_store_operations(self, memory_items: list[MemoryItem], concurrent_workers: int = 5) -> dict:
        """Benchmark memory store operations."""
        logger.info(f"Benchmarking memory store operations with {concurrent_workers} workers")

        results = {
            "add_operations": [],
            "get_operations": [],
            "search_operations": [],
            "update_operations": [],
        }

        def add_memory_item(item):
            start_time = time.time()
            result = self.store_manager.add_memory_item(item)
            end_time = time.time()
            return {
                "success": result.success,
                "latency_ms": (end_time - start_time) * 1000,
                "item_id": result.data.get("id") if result.success else None,
            }

        def get_memory_item(item_id):
            start_time = time.time()
            result = self.store_manager.get_memory_item(item_id)
            end_time = time.time()
            return {
                "success": result.success,
                "latency_ms": (end_time - start_time) * 1000,
            }

        def search_memory_items(tenant, workspace, text):
            start_time = time.time()
            result = self.store_manager.search_memory_keyword(tenant, workspace, text)
            end_time = time.time()
            return {
                "success": result.success,
                "latency_ms": (end_time - start_time) * 1000,
                "result_count": len(result.data.get("items", [])) if result.success else 0,
            }

        def update_memory_item(item_id, timestamp):
            start_time = time.time()
            result = self.store_manager.update_memory_item_last_used(item_id, timestamp)
            end_time = time.time()
            return {
                "success": result.success,
                "latency_ms": (end_time - start_time) * 1000,
            }

        # Benchmark add operations
        logger.info("Benchmarking add operations...")
        with ThreadPoolExecutor(max_workers=concurrent_workers) as executor:
            futures = [executor.submit(add_memory_item, item) for item in memory_items]
            for future in as_completed(futures):
                result = future.result()
                results["add_operations"].append(result)

        # Get successful item IDs for subsequent operations
        successful_ids = [r["item_id"] for r in results["add_operations"] if r["success"] and r["item_id"]]

        if not successful_ids:
            logger.error("No successful add operations, cannot benchmark other operations")
            return results

        # Benchmark get operations
        logger.info("Benchmarking get operations...")
        with ThreadPoolExecutor(max_workers=concurrent_workers) as executor:
            futures = [executor.submit(get_memory_item, item_id) for item_id in successful_ids[:100]]  # Limit to 100
            for future in as_completed(futures):
                result = future.result()
                results["get_operations"].append(result)

        # Benchmark search operations
        logger.info("Benchmarking search operations...")
        search_queries = ["Benchmark", "content", "metadata", "0", "1"]
        with ThreadPoolExecutor(max_workers=concurrent_workers) as executor:
            futures = []
            for query in search_queries:
                futures.extend(
                    [
                        executor.submit(
                            search_memory_items,
                            f"benchmark_tenant_{i % 10}",
                            f"benchmark_workspace_{i % 5}",
                            query,
                        )
                        for i in range(20)  # 20 searches per query
                    ]
                )
            for future in as_completed(futures):
                result = future.result()
                results["search_operations"].append(result)

        # Benchmark update operations
        logger.info("Benchmarking update operations...")
        with ThreadPoolExecutor(max_workers=concurrent_workers) as executor:
            futures = [
                executor.submit(update_memory_item, item_id, datetime.now().isoformat())
                for item_id in successful_ids[:50]  # Limit to 50
            ]
            for future in as_completed(futures):
                result = future.result()
                results["update_operations"].append(result)

        return results

    def benchmark_debate_store_operations(self, debates: list[Debate], concurrent_workers: int = 5) -> dict:
        """Benchmark debate store operations."""
        logger.info(f"Benchmarking debate store operations with {concurrent_workers} workers")

        results = {
            "add_operations": [],
            "list_operations": [],
        }

        def add_debate(debate):
            start_time = time.time()
            result = self.store_manager.add_debate(debate)
            end_time = time.time()
            return {
                "success": result.success,
                "latency_ms": (end_time - start_time) * 1000,
                "debate_id": result.data.get("id") if result.success else None,
            }

        def list_debates(tenant, workspace):
            start_time = time.time()
            result = self.store_manager.list_debates(tenant, workspace)
            end_time = time.time()
            return {
                "success": result.success,
                "latency_ms": (end_time - start_time) * 1000,
                "result_count": len(result.data.get("debates", [])) if result.success else 0,
            }

        # Benchmark add operations
        logger.info("Benchmarking debate add operations...")
        with ThreadPoolExecutor(max_workers=concurrent_workers) as executor:
            futures = [executor.submit(add_debate, debate) for debate in debates]
            for future in as_completed(futures):
                result = future.result()
                results["add_operations"].append(result)

        # Benchmark list operations
        logger.info("Benchmarking debate list operations...")
        tenants = list({debate.tenant for debate in debates})
        workspaces = list({debate.workspace for debate in debates})

        with ThreadPoolExecutor(max_workers=concurrent_workers) as executor:
            futures = []
            for tenant in tenants[:5]:  # Limit to 5 tenants
                for workspace in workspaces[:3]:  # Limit to 3 workspaces
                    futures.append(executor.submit(list_debates, tenant, workspace))

            for future in as_completed(futures):
                result = future.result()
                results["list_operations"].append(result)

        return results

    def benchmark_kg_store_operations(self, kg_nodes: list[KGNode], concurrent_workers: int = 5) -> dict:
        """Benchmark knowledge graph store operations."""
        logger.info(f"Benchmarking KG store operations with {concurrent_workers} workers")

        results = {
            "add_operations": [],
            "query_operations": [],
        }

        def add_kg_node(node):
            start_time = time.time()
            import json

            attrs = json.loads(node.attrs_json) if node.attrs_json else {}
            result = self.store_manager.add_kg_node(node.tenant, node.type, node.name, attrs)
            end_time = time.time()
            return {
                "success": result.success,
                "latency_ms": (end_time - start_time) * 1000,
                "node_id": result.data.get("id") if result.success else None,
            }

        def query_kg_nodes(tenant, node_type=None):
            start_time = time.time()
            result = self.store_manager.query_kg_nodes(tenant, type=node_type)
            end_time = time.time()
            return {
                "success": result.success,
                "latency_ms": (end_time - start_time) * 1000,
                "result_count": len(result.data.get("nodes", [])) if result.success else 0,
            }

        # Benchmark add operations
        logger.info("Benchmarking KG add operations...")
        with ThreadPoolExecutor(max_workers=concurrent_workers) as executor:
            futures = [executor.submit(add_kg_node, node) for node in kg_nodes]
            for future in as_completed(futures):
                result = future.result()
                results["add_operations"].append(result)

        # Benchmark query operations
        logger.info("Benchmarking KG query operations...")
        tenants = list({node.tenant for node in kg_nodes})
        node_types = list({node.type for node in kg_nodes})

        with ThreadPoolExecutor(max_workers=concurrent_workers) as executor:
            futures = []
            for tenant in tenants[:5]:  # Limit to 5 tenants
                # Query all nodes for tenant
                futures.append(executor.submit(query_kg_nodes, tenant))
                # Query by type
                for node_type in node_types[:3]:  # Limit to 3 types
                    futures.append(executor.submit(query_kg_nodes, tenant, node_type))

            for future in as_completed(futures):
                result = future.result()
                results["query_operations"].append(result)

        return results

    def benchmark_profile_store_operations(self, profiles: list[CreatorProfile], concurrent_workers: int = 5) -> dict:
        """Benchmark profile store operations."""
        logger.info(f"Benchmarking profile store operations with {concurrent_workers} workers")

        results = {
            "upsert_operations": [],
            "get_operations": [],
        }

        def upsert_profile(profile):
            start_time = time.time()
            result = self.store_manager.upsert_creator_profile(profile)
            end_time = time.time()
            return {
                "success": result.success,
                "latency_ms": (end_time - start_time) * 1000,
            }

        def get_profile(profile_name):
            start_time = time.time()
            result = self.store_manager.get_creator_profile(profile_name)
            end_time = time.time()
            return {
                "success": result.success,
                "latency_ms": (end_time - start_time) * 1000,
            }

        # Benchmark upsert operations
        logger.info("Benchmarking profile upsert operations...")
        with ThreadPoolExecutor(max_workers=concurrent_workers) as executor:
            futures = [executor.submit(upsert_profile, profile) for profile in profiles]
            for future in as_completed(futures):
                result = future.result()
                results["upsert_operations"].append(result)

        # Benchmark get operations
        logger.info("Benchmarking profile get operations...")
        profile_names = [profile.name for profile in profiles]

        with ThreadPoolExecutor(max_workers=concurrent_workers) as executor:
            futures = [executor.submit(get_profile, name) for name in profile_names[:100]]  # Limit to 100
            for future in as_completed(futures):
                result = future.result()
                results["get_operations"].append(result)

        return results

    def calculate_performance_metrics(self, results: dict) -> dict:
        """Calculate performance metrics from benchmark results."""
        metrics = {}

        for operation_type, operations in results.items():
            if not operations:
                continue

            successful_operations = [op for op in operations if op["success"]]
            if not successful_operations:
                continue

            latencies = [op["latency_ms"] for op in successful_operations]

            metrics[operation_type] = {
                "total_operations": len(operations),
                "successful_operations": len(successful_operations),
                "success_rate": len(successful_operations) / len(operations) * 100,
                "avg_latency_ms": statistics.mean(latencies),
                "median_latency_ms": statistics.median(latencies),
                "p95_latency_ms": self._percentile(latencies, 95),
                "p99_latency_ms": self._percentile(latencies, 99),
                "max_latency_ms": max(latencies),
                "min_latency_ms": min(latencies),
                "std_dev_latency_ms": statistics.stdev(latencies) if len(latencies) > 1 else 0,
            }

        return metrics

    def _percentile(self, data: list[float], percentile: float) -> float:
        """Calculate percentile of data."""
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        if index >= len(sorted_data):
            index = len(sorted_data) - 1
        return sorted_data[index]

    def run_comprehensive_benchmark(self, record_counts: list[int] | None = None, concurrent_workers: int = 5) -> dict:
        """Run comprehensive benchmark across different record counts."""
        if record_counts is None:
            record_counts = [100, 500, 1000]
        logger.info("Starting comprehensive PostgreSQL benchmark")

        comprehensive_results = {}

        for count in record_counts:
            logger.info(f"Benchmarking with {count} records")

            # Generate test data
            memory_items, debates, kg_nodes, profiles = self.generate_test_data(count)

            # Run benchmarks for each store type
            store_results = {}

            # Memory store benchmark
            logger.info(f"Benchmarking memory store with {count} records")
            memory_results = self.benchmark_memory_store_operations(memory_items, concurrent_workers)
            store_results["memory"] = self.calculate_performance_metrics(memory_results)

            # Debate store benchmark
            logger.info(f"Benchmarking debate store with {count} records")
            debate_results = self.benchmark_debate_store_operations(debates, concurrent_workers)
            store_results["debate"] = self.calculate_performance_metrics(debate_results)

            # KG store benchmark
            logger.info(f"Benchmarking KG store with {count} records")
            kg_results = self.benchmark_kg_store_operations(kg_nodes, concurrent_workers)
            store_results["kg"] = self.calculate_performance_metrics(kg_results)

            # Profile store benchmark
            logger.info(f"Benchmarking profile store with {count} records")
            profile_results = self.benchmark_profile_store_operations(profiles, concurrent_workers)
            store_results["profile"] = self.calculate_performance_metrics(profile_results)

            comprehensive_results[count] = store_results

            # Check if p99 targets are met
            self._validate_p99_targets(store_results, count)

        return comprehensive_results

    def _validate_p99_targets(self, store_results: dict, record_count: int):
        """Validate that p99 latency targets are met (<100ms)."""
        target_p99_ms = 100
        violations = []

        for store_name, metrics in store_results.items():
            for operation_type, operation_metrics in metrics.items():
                p99_latency = operation_metrics.get("p99_latency_ms", 0)
                if p99_latency > target_p99_ms:
                    violations.append(f"{store_name}.{operation_type}: {p99_latency:.2f}ms > {target_p99_ms}ms")

        if violations:
            logger.warning(f"P99 latency target violations with {record_count} records:")
            for violation in violations:
                logger.warning(f"  - {violation}")
        else:
            logger.info(f"All P99 latency targets met with {record_count} records")

    def generate_report(self, results: dict) -> str:
        """Generate a comprehensive benchmark report."""
        report = []
        report.append("=" * 80)
        report.append("PostgreSQL Migration Benchmark Report")
        report.append("=" * 80)
        report.append(f"Generated at: {datetime.now().isoformat()}")
        report.append(f"PostgreSQL URL: {self.postgresql_url}")
        report.append("")

        for record_count, store_results in results.items():
            report.append(f"Record Count: {record_count}")
            report.append("-" * 40)

            for store_name, metrics in store_results.items():
                report.append(f"\n{store_name.upper()} STORE:")

                for operation_type, operation_metrics in metrics.items():
                    report.append(f"  {operation_type}:")
                    report.append(f"    Total Operations: {operation_metrics['total_operations']}")
                    report.append(f"    Success Rate: {operation_metrics['success_rate']:.2f}%")
                    report.append(f"    Avg Latency: {operation_metrics['avg_latency_ms']:.2f}ms")
                    report.append(f"    Median Latency: {operation_metrics['median_latency_ms']:.2f}ms")
                    report.append(f"    P95 Latency: {operation_metrics['p95_latency_ms']:.2f}ms")
                    report.append(f"    P99 Latency: {operation_metrics['p99_latency_ms']:.2f}ms")
                    report.append(f"    Max Latency: {operation_metrics['max_latency_ms']:.2f}ms")
                    report.append(f"    Std Dev: {operation_metrics['std_dev_latency_ms']:.2f}ms")

                    # Highlight P99 target violations
                    if operation_metrics["p99_latency_ms"] > 100:
                        report.append(
                            f"    ⚠️  P99 TARGET VIOLATION: {operation_metrics['p99_latency_ms']:.2f}ms > 100ms"
                        )
                    else:
                        report.append(f"    ✅ P99 target met: {operation_metrics['p99_latency_ms']:.2f}ms <= 100ms")
                    report.append("")

            report.append("")

        # Summary
        report.append("SUMMARY:")
        report.append("-" * 20)

        all_p99_values = []
        for store_results in results.values():
            for metrics in store_results.values():
                for operation_metrics in metrics.values():
                    all_p99_values.append(operation_metrics["p99_latency_ms"])

        if all_p99_values:
            overall_p99 = max(all_p99_values)
            report.append(f"Overall Max P99 Latency: {overall_p99:.2f}ms")

            if overall_p99 <= 100:
                report.append("✅ ALL P99 TARGETS MET")
            else:
                report.append("❌ P99 TARGET VIOLATIONS DETECTED")

        report.append("=" * 80)

        return "\n".join(report)

    def cleanup(self):
        """Cleanup resources."""
        if self.store_manager:
            self.store_manager.close()


def main():
    """Main benchmark function."""
    parser = argparse.ArgumentParser(description="Benchmark PostgreSQL migration performance")
    parser.add_argument("--postgresql-url", required=True, help="PostgreSQL connection URL")
    parser.add_argument(
        "--record-counts",
        nargs="+",
        type=int,
        default=[100, 500, 1000],
        help="Record counts to benchmark",
    )
    parser.add_argument("--concurrent-workers", type=int, default=5, help="Number of concurrent workers")
    parser.add_argument("--output-file", help="Output file for benchmark report")

    args = parser.parse_args()

    logger.info("Starting PostgreSQL migration benchmark")
    logger.info(f"PostgreSQL URL: {args.postgresql_url}")
    logger.info(f"Record counts: {args.record_counts}")
    logger.info(f"Concurrent workers: {args.concurrent_workers}")

    benchmark = PostgreSQLBenchmark(args.postgresql_url)

    try:
        # Initialize benchmark
        result = benchmark.initialize()
        if not result.success:
            logger.error(f"Failed to initialize benchmark: {result.error}")
            sys.exit(1)

        # Run comprehensive benchmark
        results = benchmark.run_comprehensive_benchmark(args.record_counts, args.concurrent_workers)

        # Generate report
        report = benchmark.generate_report(results)
        print(report)

        # Save report to file if specified
        if args.output_file:
            with open(args.output_file, "w") as f:
                f.write(report)
            logger.info(f"Benchmark report saved to {args.output_file}")

        # Save raw results as JSON
        json_output_file = args.output_file.replace(".txt", ".json") if args.output_file else "benchmark_results.json"
        with open(json_output_file, "w") as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"Raw benchmark results saved to {json_output_file}")

    except KeyboardInterrupt:
        logger.info("Benchmark interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during benchmark: {e}")
        sys.exit(1)
    finally:
        benchmark.cleanup()


if __name__ == "__main__":
    main()
