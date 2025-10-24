"""Load Tests for Unified System

This module provides comprehensive load testing for the unified system,
testing performance under high concurrent load scenarios.
"""

import asyncio
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest


class TestUnifiedSystemLoad:
    """Load tests for the unified system components"""

    @pytest.fixture
    def mock_services(self):
        """Mock external services for load testing"""
        with (
            patch("ultimate_discord_intelligence_bot.knowledge.unified_memory.QdrantClient") as mock_qdrant,
            patch("ultimate_discord_intelligence_bot.knowledge.unified_memory.sqlite3.connect") as mock_sqlite,
            patch(
                "ultimate_discord_intelligence_bot.observability.unified_metrics.prometheus_client"
            ) as mock_prometheus,
            patch("ultimate_discord_intelligence_bot.routing.unified_router.OpenRouterService") as mock_openrouter,
            patch("ultimate_discord_intelligence_bot.caching.unified_cache.redis.Redis") as mock_redis,
        ):
            # Mock Qdrant
            mock_qdrant.return_value = AsyncMock()
            mock_qdrant.return_value.upsert = AsyncMock()
            mock_qdrant.return_value.search = AsyncMock(return_value=[])

            # Mock SQLite
            mock_sqlite.return_value = Mock()
            mock_sqlite.return_value.execute = Mock()
            mock_sqlite.return_value.commit = Mock()

            # Mock Prometheus
            mock_prometheus.Counter = Mock()
            mock_prometheus.Gauge = Mock()
            mock_prometheus.Histogram = Mock()

            # Mock OpenRouter
            mock_openrouter.return_value = AsyncMock()
            mock_openrouter.return_value.route = AsyncMock(
                return_value={
                    "model": "test-model",
                    "provider": "test-provider",
                    "response": "test response",
                    "tokens": 100,
                }
            )

            # Mock Redis
            mock_redis.return_value = AsyncMock()
            mock_redis.return_value.set = AsyncMock()
            mock_redis.return_value.get = AsyncMock(return_value="cached_value")

            yield {
                "qdrant": mock_qdrant,
                "sqlite": mock_sqlite,
                "prometheus": mock_prometheus,
                "openrouter": mock_openrouter,
                "redis": mock_redis,
            }

    @pytest.mark.asyncio
    async def test_memory_service_concurrent_load(self, mock_services):
        """Test memory service under concurrent load"""
        from ultimate_discord_intelligence_bot.knowledge import UnifiedMemoryService

        memory_service = UnifiedMemoryService()

        # Test parameters
        concurrent_requests = 100
        tenant_id = "load_test_tenant"
        workspace_id = "load_test_workspace"

        async def store_content_task(task_id: int) -> dict[str, Any]:
            """Individual task for storing content"""
            start_time = time.time()

            result = await memory_service.store_content(
                content=f"Load test content {task_id}",
                tenant_id=tenant_id,
                workspace_id=workspace_id,
                metadata={"task_id": task_id, "load_test": True},
                embeddings=[0.1, 0.2, 0.3, 0.4, 0.5],
            )

            end_time = time.time()

            return {
                "task_id": task_id,
                "success": result.success,
                "duration": end_time - start_time,
                "error": result.error if not result.success else None,
            }

        # Execute concurrent requests
        start_time = time.time()
        tasks = [store_content_task(i) for i in range(concurrent_requests)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        total_duration = end_time - start_time

        # Analyze results
        successful_results = [r for r in results if isinstance(r, dict) and r.get("success")]
        failed_results = [r for r in results if isinstance(r, dict) and not r.get("success")]
        exceptions = [r for r in results if isinstance(r, Exception)]

        durations = [r["duration"] for r in successful_results if isinstance(r, dict)]

        # Performance metrics
        success_rate = len(successful_results) / concurrent_requests * 100
        avg_duration = statistics.mean(durations) if durations else 0
        max_duration = max(durations) if durations else 0
        min_duration = min(durations) if durations else 0
        throughput = concurrent_requests / total_duration

        print("\nMemory Service Load Test Results:")
        print(f"  Concurrent Requests: {concurrent_requests}")
        print(f"  Total Duration: {total_duration:.2f}s")
        print(f"  Success Rate: {success_rate:.2f}%")
        print(f"  Throughput: {throughput:.2f} requests/second")
        print(f"  Average Duration: {avg_duration:.3f}s")
        print(f"  Max Duration: {max_duration:.3f}s")
        print(f"  Min Duration: {min_duration:.3f}s")
        print(f"  Failed Requests: {len(failed_results)}")
        print(f"  Exceptions: {len(exceptions)}")

        # Assertions
        assert success_rate >= 95.0, f"Success rate {success_rate:.2f}% is below 95%"
        assert avg_duration <= 1.0, f"Average duration {avg_duration:.3f}s is too high"
        assert throughput >= 50.0, f"Throughput {throughput:.2f} req/s is too low"

    @pytest.mark.asyncio
    async def test_router_service_concurrent_load(self, mock_services):
        """Test router service under concurrent load"""
        from ultimate_discord_intelligence_bot.routing import UnifiedRouterService

        router_service = UnifiedRouterService()

        # Test parameters
        concurrent_requests = 50  # Lower due to API rate limits
        tenant_id = "load_test_tenant"
        workspace_id = "load_test_workspace"

        async def route_request_task(task_id: int) -> dict[str, Any]:
            """Individual task for routing requests"""
            start_time = time.time()

            result = await router_service.route_request(
                prompt=f"Load test prompt {task_id}",
                tenant_id=tenant_id,
                workspace_id=workspace_id,
                max_tokens=100,
                temperature=0.7,
            )

            end_time = time.time()

            return {
                "task_id": task_id,
                "success": result.success,
                "duration": end_time - start_time,
                "error": result.error if not result.success else None,
            }

        # Execute concurrent requests
        start_time = time.time()
        tasks = [route_request_task(i) for i in range(concurrent_requests)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        total_duration = end_time - start_time

        # Analyze results
        successful_results = [r for r in results if isinstance(r, dict) and r.get("success")]
        failed_results = [r for r in results if isinstance(r, dict) and not r.get("success")]
        exceptions = [r for r in results if isinstance(r, Exception)]

        durations = [r["duration"] for r in successful_results if isinstance(r, dict)]

        # Performance metrics
        success_rate = len(successful_results) / concurrent_requests * 100
        avg_duration = statistics.mean(durations) if durations else 0
        max_duration = max(durations) if durations else 0
        min_duration = min(durations) if durations else 0
        throughput = concurrent_requests / total_duration

        print("\nRouter Service Load Test Results:")
        print(f"  Concurrent Requests: {concurrent_requests}")
        print(f"  Total Duration: {total_duration:.2f}s")
        print(f"  Success Rate: {success_rate:.2f}%")
        print(f"  Throughput: {throughput:.2f} requests/second")
        print(f"  Average Duration: {avg_duration:.3f}s")
        print(f"  Max Duration: {max_duration:.3f}s")
        print(f"  Min Duration: {min_duration:.3f}s")
        print(f"  Failed Requests: {len(failed_results)}")
        print(f"  Exceptions: {len(exceptions)}")

        # Assertions
        assert success_rate >= 90.0, f"Success rate {success_rate:.2f}% is below 90%"
        assert avg_duration <= 2.0, f"Average duration {avg_duration:.3f}s is too high"
        assert throughput >= 20.0, f"Throughput {throughput:.2f} req/s is too low"

    @pytest.mark.asyncio
    async def test_cache_service_concurrent_load(self, mock_services):
        """Test cache service under concurrent load"""
        from ultimate_discord_intelligence_bot.caching import UnifiedCacheService

        cache_service = UnifiedCacheService()

        # Test parameters
        concurrent_requests = 200  # Higher for cache operations
        tenant_id = "load_test_tenant"
        workspace_id = "load_test_workspace"

        async def cache_operation_task(task_id: int) -> dict[str, Any]:
            """Individual task for cache operations"""
            start_time = time.time()

            # Test both store and get operations
            store_result = await cache_service.store(
                key=f"load_test_key_{task_id}",
                value=f"load_test_value_{task_id}",
                tenant_id=tenant_id,
                workspace_id=workspace_id,
                ttl=3600,
            )

            get_result = await cache_service.get(
                key=f"load_test_key_{task_id}",
                tenant_id=tenant_id,
                workspace_id=workspace_id,
            )

            end_time = time.time()

            success = store_result.success and get_result.success

            return {
                "task_id": task_id,
                "success": success,
                "duration": end_time - start_time,
                "store_success": store_result.success,
                "get_success": get_result.success,
                "error": store_result.error if not store_result.success else get_result.error,
            }

        # Execute concurrent requests
        start_time = time.time()
        tasks = [cache_operation_task(i) for i in range(concurrent_requests)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        total_duration = end_time - start_time

        # Analyze results
        successful_results = [r for r in results if isinstance(r, dict) and r.get("success")]
        failed_results = [r for r in results if isinstance(r, dict) and not r.get("success")]
        exceptions = [r for r in results if isinstance(r, Exception)]

        durations = [r["duration"] for r in successful_results if isinstance(r, dict)]

        # Performance metrics
        success_rate = len(successful_results) / concurrent_requests * 100
        avg_duration = statistics.mean(durations) if durations else 0
        max_duration = max(durations) if durations else 0
        min_duration = min(durations) if durations else 0
        throughput = concurrent_requests / total_duration

        print("\nCache Service Load Test Results:")
        print(f"  Concurrent Requests: {concurrent_requests}")
        print(f"  Total Duration: {total_duration:.2f}s")
        print(f"  Success Rate: {success_rate:.2f}%")
        print(f"  Throughput: {throughput:.2f} requests/second")
        print(f"  Average Duration: {avg_duration:.3f}s")
        print(f"  Max Duration: {max_duration:.3f}s")
        print(f"  Min Duration: {min_duration:.3f}s")
        print(f"  Failed Requests: {len(failed_results)}")
        print(f"  Exceptions: {len(exceptions)}")

        # Assertions
        assert success_rate >= 98.0, f"Success rate {success_rate:.2f}% is below 98%"
        assert avg_duration <= 0.5, f"Average duration {avg_duration:.3f}s is too high"
        assert throughput >= 100.0, f"Throughput {throughput:.2f} req/s is too low"

    @pytest.mark.asyncio
    async def test_orchestration_service_concurrent_load(self, mock_services):
        """Test orchestration service under concurrent load"""
        from ultimate_discord_intelligence_bot.orchestration import (
            UnifiedOrchestrationService,
        )

        orchestrator = UnifiedOrchestrationService()

        # Test parameters
        concurrent_requests = 75
        tenant_id = "load_test_tenant"
        workspace_id = "load_test_workspace"

        async def submit_task_task(task_id: int) -> dict[str, Any]:
            """Individual task for submitting orchestration tasks"""
            start_time = time.time()

            result = await orchestrator.submit_task(
                task_type="load_test_task",
                payload={"task_id": task_id, "load_test": True},
                tenant_id=tenant_id,
                workspace_id=workspace_id,
                priority="medium",
            )

            end_time = time.time()

            return {
                "task_id": task_id,
                "success": result.success,
                "duration": end_time - start_time,
                "error": result.error if not result.success else None,
            }

        # Execute concurrent requests
        start_time = time.time()
        tasks = [submit_task_task(i) for i in range(concurrent_requests)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        total_duration = end_time - start_time

        # Analyze results
        successful_results = [r for r in results if isinstance(r, dict) and r.get("success")]
        failed_results = [r for r in results if isinstance(r, dict) and not r.get("success")]
        exceptions = [r for r in results if isinstance(r, Exception)]

        durations = [r["duration"] for r in successful_results if isinstance(r, dict)]

        # Performance metrics
        success_rate = len(successful_results) / concurrent_requests * 100
        avg_duration = statistics.mean(durations) if durations else 0
        max_duration = max(durations) if durations else 0
        min_duration = min(durations) if durations else 0
        throughput = concurrent_requests / total_duration

        print("\nOrchestration Service Load Test Results:")
        print(f"  Concurrent Requests: {concurrent_requests}")
        print(f"  Total Duration: {total_duration:.2f}s")
        print(f"  Success Rate: {success_rate:.2f}%")
        print(f"  Throughput: {throughput:.2f} requests/second")
        print(f"  Average Duration: {avg_duration:.3f}s")
        print(f"  Max Duration: {max_duration:.3f}s")
        print(f"  Min Duration: {min_duration:.3f}s")
        print(f"  Failed Requests: {len(failed_results)}")
        print(f"  Exceptions: {len(exceptions)}")

        # Assertions
        assert success_rate >= 95.0, f"Success rate {success_rate:.2f}% is below 95%"
        assert avg_duration <= 1.0, f"Average duration {avg_duration:.3f}s is too high"
        assert throughput >= 50.0, f"Throughput {throughput:.2f} req/s is too low"

    @pytest.mark.asyncio
    async def test_agent_bridge_concurrent_load(self, mock_services):
        """Test agent bridge under concurrent load"""
        from ultimate_discord_intelligence_bot.agent_bridge import AgentBridge

        agent_bridge = AgentBridge()

        # Test parameters
        concurrent_requests = 100

        async def share_insight_task(task_id: int) -> dict[str, Any]:
            """Individual task for sharing insights"""
            start_time = time.time()

            result = await agent_bridge.share_insight(
                agent_id=f"load_test_agent_{task_id}",
                agent_type="load_test",
                insight_type="performance",
                title=f"Load Test Insight {task_id}",
                description=f"Load test insight description {task_id}",
                context={"task_id": task_id, "load_test": True},
                tags=["load_test", "performance"],
                confidence_score=0.8,
                priority="medium",
            )

            end_time = time.time()

            return {
                "task_id": task_id,
                "success": result.success,
                "duration": end_time - start_time,
                "error": result.error if not result.success else None,
            }

        # Execute concurrent requests
        start_time = time.time()
        tasks = [share_insight_task(i) for i in range(concurrent_requests)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        total_duration = end_time - start_time

        # Analyze results
        successful_results = [r for r in results if isinstance(r, dict) and r.get("success")]
        failed_results = [r for r in results if isinstance(r, dict) and not r.get("success")]
        exceptions = [r for r in results if isinstance(r, Exception)]

        durations = [r["duration"] for r in successful_results if isinstance(r, dict)]

        # Performance metrics
        success_rate = len(successful_results) / concurrent_requests * 100
        avg_duration = statistics.mean(durations) if durations else 0
        max_duration = max(durations) if durations else 0
        min_duration = min(durations) if durations else 0
        throughput = concurrent_requests / total_duration

        print("\nAgent Bridge Load Test Results:")
        print(f"  Concurrent Requests: {concurrent_requests}")
        print(f"  Total Duration: {total_duration:.2f}s")
        print(f"  Success Rate: {success_rate:.2f}%")
        print(f"  Throughput: {throughput:.2f} requests/second")
        print(f"  Average Duration: {avg_duration:.3f}s")
        print(f"  Max Duration: {max_duration:.3f}s")
        print(f"  Min Duration: {min_duration:.3f}s")
        print(f"  Failed Requests: {len(failed_results)}")
        print(f"  Exceptions: {len(exceptions)}")

        # Assertions
        assert success_rate >= 95.0, f"Success rate {success_rate:.2f}% is below 95%"
        assert avg_duration <= 1.0, f"Average duration {avg_duration:.3f}s is too high"
        assert throughput >= 50.0, f"Throughput {throughput:.2f} req/s is too low"

    @pytest.mark.asyncio
    async def test_observability_concurrent_load(self, mock_services):
        """Test observability system under concurrent load"""
        from ultimate_discord_intelligence_bot.observability import (
            UnifiedMetricsCollector,
        )

        metrics_collector = UnifiedMetricsCollector()

        # Test parameters
        concurrent_requests = 150

        async def collect_metrics_task(task_id: int) -> dict[str, Any]:
            """Individual task for collecting metrics"""
            start_time = time.time()

            # Test multiple metric types
            system_result = await metrics_collector.collect_system_metric(
                name=f"load_test_system_metric_{task_id}",
                value=float(task_id),
                metric_type="gauge",
                category="system",
                labels={"task_id": str(task_id), "load_test": "true"},
                description=f"Load test system metric {task_id}",
            )

            agent_result = await metrics_collector.collect_agent_metric(
                agent_id=f"load_test_agent_{task_id}",
                agent_type="load_test",
                metric_name="task_duration",
                value=float(task_id * 10),
                metric_type="histogram",
                category="agent",
                labels={"task_id": str(task_id), "load_test": "true"},
            )

            end_time = time.time()

            success = system_result.success and agent_result.success

            return {
                "task_id": task_id,
                "success": success,
                "duration": end_time - start_time,
                "system_success": system_result.success,
                "agent_success": agent_result.success,
                "error": system_result.error if not system_result.success else agent_result.error,
            }

        # Execute concurrent requests
        start_time = time.time()
        tasks = [collect_metrics_task(i) for i in range(concurrent_requests)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        total_duration = end_time - start_time

        # Analyze results
        successful_results = [r for r in results if isinstance(r, dict) and r.get("success")]
        failed_results = [r for r in results if isinstance(r, dict) and not r.get("success")]
        exceptions = [r for r in results if isinstance(r, Exception)]

        durations = [r["duration"] for r in successful_results if isinstance(r, dict)]

        # Performance metrics
        success_rate = len(successful_results) / concurrent_requests * 100
        avg_duration = statistics.mean(durations) if durations else 0
        max_duration = max(durations) if durations else 0
        min_duration = min(durations) if durations else 0
        throughput = concurrent_requests / total_duration

        print("\nObservability Load Test Results:")
        print(f"  Concurrent Requests: {concurrent_requests}")
        print(f"  Total Duration: {total_duration:.2f}s")
        print(f"  Success Rate: {success_rate:.2f}%")
        print(f"  Throughput: {throughput:.2f} requests/second")
        print(f"  Average Duration: {avg_duration:.3f}s")
        print(f"  Max Duration: {max_duration:.3f}s")
        print(f"  Min Duration: {min_duration:.3f}s")
        print(f"  Failed Requests: {len(failed_results)}")
        print(f"  Exceptions: {len(exceptions)}")

        # Assertions
        assert success_rate >= 98.0, f"Success rate {success_rate:.2f}% is below 98%"
        assert avg_duration <= 0.5, f"Average duration {avg_duration:.3f}s is too high"
        assert throughput >= 100.0, f"Throughput {throughput:.2f} req/s is too low"

    @pytest.mark.asyncio
    async def test_mixed_workload_load(self, mock_services):
        """Test mixed workload across all unified systems"""
        from ultimate_discord_intelligence_bot.agent_bridge import AgentBridge
        from ultimate_discord_intelligence_bot.caching import UnifiedCacheService
        from ultimate_discord_intelligence_bot.knowledge import UnifiedMemoryService
        from ultimate_discord_intelligence_bot.observability import (
            UnifiedMetricsCollector,
        )
        from ultimate_discord_intelligence_bot.orchestration import (
            UnifiedOrchestrationService,
        )
        from ultimate_discord_intelligence_bot.routing import UnifiedRouterService

        # Initialize all services
        memory_service = UnifiedMemoryService()
        router_service = UnifiedRouterService()
        cache_service = UnifiedCacheService()
        orchestrator = UnifiedOrchestrationService()
        agent_bridge = AgentBridge()
        metrics_collector = UnifiedMetricsCollector()

        # Test parameters
        concurrent_requests = 50  # Mixed workload
        tenant_id = "load_test_tenant"
        workspace_id = "load_test_workspace"

        async def mixed_workload_task(task_id: int) -> dict[str, Any]:
            """Individual task for mixed workload"""
            start_time = time.time()
            results = {}

            # Memory operation
            memory_result = await memory_service.store_content(
                content=f"Mixed workload content {task_id}",
                tenant_id=tenant_id,
                workspace_id=workspace_id,
                metadata={"task_id": task_id, "workload": "mixed"},
            )
            results["memory"] = memory_result.success

            # Cache operation
            cache_result = await cache_service.store(
                key=f"mixed_workload_key_{task_id}",
                value=f"mixed_workload_value_{task_id}",
                tenant_id=tenant_id,
                workspace_id=workspace_id,
                ttl=3600,
            )
            results["cache"] = cache_result.success

            # Router operation
            router_result = await router_service.route_request(
                prompt=f"Mixed workload prompt {task_id}",
                tenant_id=tenant_id,
                workspace_id=workspace_id,
                max_tokens=50,
                temperature=0.7,
            )
            results["router"] = router_result.success

            # Orchestration operation
            orchestration_result = await orchestrator.submit_task(
                task_type="mixed_workload_task",
                payload={"task_id": task_id, "workload": "mixed"},
                tenant_id=tenant_id,
                workspace_id=workspace_id,
                priority="medium",
            )
            results["orchestration"] = orchestration_result.success

            # Agent bridge operation
            bridge_result = await agent_bridge.share_insight(
                agent_id=f"mixed_workload_agent_{task_id}",
                agent_type="mixed_workload",
                insight_type="performance",
                title=f"Mixed Workload Insight {task_id}",
                description=f"Mixed workload insight {task_id}",
                context={"task_id": task_id, "workload": "mixed"},
                tags=["mixed", "workload"],
                confidence_score=0.8,
                priority="medium",
            )
            results["agent_bridge"] = bridge_result.success

            # Metrics operation
            metrics_result = await metrics_collector.collect_system_metric(
                name=f"mixed_workload_metric_{task_id}",
                value=float(task_id),
                metric_type="gauge",
                category="workload",
                labels={"task_id": str(task_id), "workload": "mixed"},
                description=f"Mixed workload metric {task_id}",
            )
            results["metrics"] = metrics_result.success

            end_time = time.time()

            # Overall success
            overall_success = all(results.values())

            return {
                "task_id": task_id,
                "success": overall_success,
                "duration": end_time - start_time,
                "results": results,
                "error": "Multiple failures" if not overall_success else None,
            }

        # Execute concurrent requests
        start_time = time.time()
        tasks = [mixed_workload_task(i) for i in range(concurrent_requests)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        total_duration = end_time - start_time

        # Analyze results
        successful_results = [r for r in results if isinstance(r, dict) and r.get("success")]
        failed_results = [r for r in results if isinstance(r, dict) and not r.get("success")]
        exceptions = [r for r in results if isinstance(r, Exception)]

        durations = [r["duration"] for r in successful_results if isinstance(r, dict)]

        # Performance metrics
        success_rate = len(successful_results) / concurrent_requests * 100
        avg_duration = statistics.mean(durations) if durations else 0
        max_duration = max(durations) if durations else 0
        min_duration = min(durations) if durations else 0
        throughput = concurrent_requests / total_duration

        # Calculate per-service success rates
        service_success_rates = {}
        for service in [
            "memory",
            "cache",
            "router",
            "orchestration",
            "agent_bridge",
            "metrics",
        ]:
            service_successes = sum(1 for r in successful_results if r.get("results", {}).get(service))
            service_success_rates[service] = service_successes / concurrent_requests * 100

        print("\nMixed Workload Load Test Results:")
        print(f"  Concurrent Requests: {concurrent_requests}")
        print(f"  Total Duration: {total_duration:.2f}s")
        print(f"  Overall Success Rate: {success_rate:.2f}%")
        print(f"  Throughput: {throughput:.2f} requests/second")
        print(f"  Average Duration: {avg_duration:.3f}s")
        print(f"  Max Duration: {max_duration:.3f}s")
        print(f"  Min Duration: {min_duration:.3f}s")
        print(f"  Failed Requests: {len(failed_results)}")
        print(f"  Exceptions: {len(exceptions)}")

        print("\nPer-Service Success Rates:")
        for service, rate in service_success_rates.items():
            print(f"  {service}: {rate:.2f}%")

        # Assertions
        assert success_rate >= 90.0, f"Overall success rate {success_rate:.2f}% is below 90%"
        assert avg_duration <= 3.0, f"Average duration {avg_duration:.3f}s is too high"
        assert throughput >= 15.0, f"Throughput {throughput:.2f} req/s is too low"

        # Check individual service success rates
        for service, rate in service_success_rates.items():
            assert rate >= 85.0, f"{service} success rate {rate:.2f}% is below 85%"

    def test_crew_integration_under_load(self, mock_services):
        """Test CrewAI integration under load using threading"""
        from ultimate_discord_intelligence_bot.crew import (
            UltimateDiscordIntelligenceBotCrew,
        )

        def crew_initialization_task(task_id: int) -> dict[str, Any]:
            """Individual task for crew initialization"""
            start_time = time.time()

            try:
                crew = UltimateDiscordIntelligenceBotCrew()
                mission_orchestrator = crew.mission_orchestrator()
                executive_supervisor = crew.executive_supervisor()

                end_time = time.time()

                return {
                    "task_id": task_id,
                    "success": True,
                    "duration": end_time - start_time,
                    "tools_count": len(mission_orchestrator.tools) + len(executive_supervisor.tools),
                    "error": None,
                }
            except Exception as e:
                end_time = time.time()
                return {
                    "task_id": task_id,
                    "success": False,
                    "duration": end_time - start_time,
                    "tools_count": 0,
                    "error": str(e),
                }

        # Test parameters
        concurrent_requests = 25  # Lower for crew initialization

        # Execute concurrent requests using ThreadPoolExecutor
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(crew_initialization_task, i) for i in range(concurrent_requests)]
            results = [future.result() for future in as_completed(futures)]
        end_time = time.time()

        total_duration = end_time - start_time

        # Analyze results
        successful_results = [r for r in results if r.get("success")]
        failed_results = [r for r in results if not r.get("success")]

        durations = [r["duration"] for r in successful_results]
        tools_counts = [r["tools_count"] for r in successful_results]

        # Performance metrics
        success_rate = len(successful_results) / concurrent_requests * 100
        avg_duration = statistics.mean(durations) if durations else 0
        max_duration = max(durations) if durations else 0
        min_duration = min(durations) if durations else 0
        avg_tools_count = statistics.mean(tools_counts) if tools_counts else 0
        throughput = concurrent_requests / total_duration

        print("\nCrew Integration Load Test Results:")
        print(f"  Concurrent Requests: {concurrent_requests}")
        print(f"  Total Duration: {total_duration:.2f}s")
        print(f"  Success Rate: {success_rate:.2f}%")
        print(f"  Throughput: {throughput:.2f} requests/second")
        print(f"  Average Duration: {avg_duration:.3f}s")
        print(f"  Max Duration: {max_duration:.3f}s")
        print(f"  Min Duration: {min_duration:.3f}s")
        print(f"  Average Tools Count: {avg_tools_count:.1f}")
        print(f"  Failed Requests: {len(failed_results)}")

        # Print failed requests for debugging
        if failed_results:
            print("\nFailed Requests:")
            for failed in failed_results[:5]:  # Show first 5 failures
                print(f"  Task {failed['task_id']}: {failed['error']}")

        # Assertions
        assert success_rate >= 95.0, f"Success rate {success_rate:.2f}% is below 95%"
        assert avg_duration <= 5.0, f"Average duration {avg_duration:.3f}s is too high"
        assert avg_tools_count >= 10, f"Average tools count {avg_tools_count:.1f} is too low"
