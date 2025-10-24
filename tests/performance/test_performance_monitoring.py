"""Performance monitoring and dashboard tests."""

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock, patch

import pytest

from ultimate_discord_intelligence_bot.tools.acquisition.multi_platform_download_tool import MultiPlatformDownloadTool
from ultimate_discord_intelligence_bot.tools.analysis.enhanced_analysis_tool import EnhancedAnalysisTool
from ultimate_discord_intelligence_bot.tools.memory.unified_memory_tool import UnifiedMemoryTool
from ultimate_discord_intelligence_bot.tools.verification.claim_verifier_tool import ClaimVerifierTool


class TestPerformanceMonitoring:
    """Performance monitoring and dashboard tests."""

    @pytest.fixture
    def monitoring_tools(self):
        """Create tools for monitoring testing."""
        return {
            "download_tool": MultiPlatformDownloadTool(),
            "analysis_tool": EnhancedAnalysisTool(),
            "verification_tool": ClaimVerifierTool(),
            "memory_tool": UnifiedMemoryTool(),
        }

    @pytest.fixture
    def monitoring_data_file(self, tmp_path):
        """Create monitoring data file."""
        return tmp_path / "performance_monitoring.json"

    @pytest.fixture
    def sample_content(self):
        """Sample content for monitoring testing."""
        return "This is a comprehensive political statement about healthcare policy that requires detailed analysis and verification."

    @pytest.fixture
    def sample_tenant_context(self):
        """Sample tenant context."""
        return {"tenant": "monitoring_tenant", "workspace": "monitoring_workspace"}

    def test_performance_metrics_collection(self, monitoring_tools, sample_content, sample_tenant_context):
        """Test performance metrics collection."""
        metrics_data = {"timestamp": time.time(), "tool_metrics": {}}

        with patch("ultimate_discord_intelligence_bot.obs.metrics.get_metrics") as mock_metrics:
            mock_metrics_instance = MagicMock()
            mock_metrics.return_value = mock_metrics_instance

            # Test analysis tool metrics
            with patch.object(monitoring_tools["analysis_tool"], "_analyze_comprehensive") as mock_analyze:
                mock_analyze.return_value = {
                    "political_topics": ["healthcare", "policy"],
                    "bias_indicators": ["subjective_language"],
                    "sentiment": "neutral",
                    "sentiment_confidence": 0.8,
                    "extracted_claims": ["Healthcare policy needs improvement"],
                    "processing_time": 1.5,
                }

                start_time = time.time()
                result = monitoring_tools["analysis_tool"]._run(
                    sample_content, "comprehensive", sample_tenant_context["tenant"], sample_tenant_context["workspace"]
                )
                end_time = time.time()

                # Collect metrics
                metrics_data["tool_metrics"]["analysis_tool"] = {
                    "execution_time": end_time - start_time,
                    "success": result.success,
                    "processing_time": result.data.get("processing_time", 0) if result.success else 0,
                    "topics_detected": len(result.data.get("political_topics", [])) if result.success else 0,
                    "claims_extracted": len(result.data.get("extracted_claims", [])) if result.success else 0,
                }

                # Verify metrics collection
                mock_metrics_instance.increment.assert_called()
                mock_metrics_instance.timing.assert_called()

                assert result.success
                assert metrics_data["tool_metrics"]["analysis_tool"]["execution_time"] > 0
                assert metrics_data["tool_metrics"]["analysis_tool"]["success"] is True

    def test_performance_dashboard_data(
        self, monitoring_tools, sample_content, sample_tenant_context, monitoring_data_file
    ):
        """Test performance dashboard data generation."""
        dashboard_data = {"timestamp": time.time(), "overview": {}, "tool_performance": {}, "system_health": {}}

        # Collect overview metrics
        with patch.object(monitoring_tools["analysis_tool"], "_analyze_comprehensive") as mock_analyze:
            mock_analyze.return_value = {
                "political_topics": ["healthcare"],
                "sentiment": "neutral",
                "sentiment_confidence": 0.8,
                "extracted_claims": ["Healthcare is important"],
                "processing_time": 1.0,
            }

            # Simulate multiple operations
            total_operations = 0
            successful_operations = 0
            total_execution_time = 0

            for i in range(5):
                start_time = time.time()
                result = monitoring_tools["analysis_tool"]._run(
                    f"{sample_content} {i}",
                    "comprehensive",
                    sample_tenant_context["tenant"],
                    sample_tenant_context["workspace"],
                )
                end_time = time.time()

                total_operations += 1
                if result.success:
                    successful_operations += 1
                total_execution_time += end_time - start_time

            # Generate overview metrics
            dashboard_data["overview"] = {
                "total_operations": total_operations,
                "successful_operations": successful_operations,
                "success_rate": successful_operations / total_operations,
                "average_execution_time": total_execution_time / total_operations,
                "total_execution_time": total_execution_time,
            }

            # Generate tool performance metrics
            dashboard_data["tool_performance"]["analysis_tool"] = {
                "operations_count": total_operations,
                "success_rate": successful_operations / total_operations,
                "average_time": total_execution_time / total_operations,
                "total_time": total_execution_time,
            }

            # Generate system health metrics
            dashboard_data["system_health"] = {
                "cpu_usage": 45.2,  # Mock CPU usage
                "memory_usage": 67.8,  # Mock memory usage
                "disk_usage": 23.1,  # Mock disk usage
                "network_latency": 12.5,  # Mock network latency
            }

            # Save dashboard data
            with open(monitoring_data_file, "w") as f:
                json.dump(dashboard_data, f, indent=2)

            # Verify dashboard data
            assert os.path.exists(monitoring_data_file)
            assert dashboard_data["overview"]["total_operations"] == 5
            assert dashboard_data["overview"]["success_rate"] == 1.0
            assert dashboard_data["overview"]["average_execution_time"] > 0

    def test_performance_alerts(self, monitoring_tools, sample_content, sample_tenant_context):
        """Test performance alerting system."""
        alert_config = {
            "execution_time_threshold": 5.0,  # 5 seconds
            "success_rate_threshold": 0.95,  # 95%
            "error_rate_threshold": 0.05,  # 5%
            "memory_usage_threshold": 80.0,  # 80%
            "cpu_usage_threshold": 90.0,  # 90%
        }

        alerts = []

        # Test execution time alert
        with patch.object(monitoring_tools["analysis_tool"], "_analyze_comprehensive") as mock_analyze:
            mock_analyze.return_value = {
                "political_topics": ["healthcare"],
                "sentiment": "neutral",
                "sentiment_confidence": 0.8,
                "extracted_claims": ["Healthcare is important"],
                "processing_time": 1.0,
            }

            start_time = time.time()
            result = monitoring_tools["analysis_tool"]._run(
                sample_content, "comprehensive", sample_tenant_context["tenant"], sample_tenant_context["workspace"]
            )
            end_time = time.time()

            execution_time = end_time - start_time

            if execution_time > alert_config["execution_time_threshold"]:
                alerts.append(
                    {
                        "type": "execution_time",
                        "message": f"Analysis tool execution time {execution_time:.2f}s exceeds threshold {alert_config['execution_time_threshold']}s",
                        "severity": "warning",
                    }
                )

            # Test success rate alert
            if not result.success:
                alerts.append(
                    {"type": "success_rate", "message": "Analysis tool operation failed", "severity": "error"}
                )

            # Verify no alerts were triggered
            assert len(alerts) == 0
            assert result.success

    def test_performance_trending(self, monitoring_tools, sample_content, sample_tenant_context):
        """Test performance trending analysis."""
        trending_data = {"timestamp": time.time(), "trends": {}}

        # Collect performance data over time
        performance_history = []

        with patch.object(monitoring_tools["analysis_tool"], "_analyze_comprehensive") as mock_analyze:
            mock_analyze.return_value = {
                "political_topics": ["healthcare"],
                "sentiment": "neutral",
                "sentiment_confidence": 0.8,
                "extracted_claims": ["Healthcare is important"],
                "processing_time": 1.0,
            }

            # Simulate performance over time
            for hour in range(24):  # 24 hours of data
                for operation in range(10):  # 10 operations per hour
                    start_time = time.time()
                    result = monitoring_tools["analysis_tool"]._run(
                        f"{sample_content} hour_{hour}_op_{operation}",
                        "comprehensive",
                        sample_tenant_context["tenant"],
                        sample_tenant_context["workspace"],
                    )
                    end_time = time.time()

                    performance_history.append(
                        {
                            "timestamp": time.time() + (hour * 3600),  # Simulate time progression
                            "execution_time": end_time - start_time,
                            "success": result.success,
                            "hour": hour,
                        }
                    )

                    assert result.success

            # Analyze trends
            hourly_performance = {}
            for hour in range(24):
                hour_data = [p for p in performance_history if p["hour"] == hour]
                if hour_data:
                    hourly_performance[hour] = {
                        "average_time": sum(p["execution_time"] for p in hour_data) / len(hour_data),
                        "success_rate": sum(1 for p in hour_data if p["success"]) / len(hour_data),
                        "operation_count": len(hour_data),
                    }

            # Calculate trends
            execution_times = [hourly_performance[h]["average_time"] for h in hourly_performance]
            success_rates = [hourly_performance[h]["success_rate"] for h in hourly_performance]

            trending_data["trends"] = {
                "execution_time_trend": "stable" if max(execution_times) - min(execution_times) < 0.5 else "variable",
                "success_rate_trend": "stable" if min(success_rates) > 0.95 else "degrading",
                "performance_variance": max(execution_times) - min(execution_times),
                "overall_health": "good"
                if min(success_rates) > 0.95 and max(execution_times) - min(execution_times) < 0.5
                else "needs_attention",
            }

            # Verify trending data
            assert trending_data["trends"]["execution_time_trend"] == "stable"
            assert trending_data["trends"]["success_rate_trend"] == "stable"
            assert trending_data["trends"]["overall_health"] == "good"

    def test_performance_optimization_recommendations(self, monitoring_tools, sample_tenant_context):
        """Test performance optimization recommendations."""
        recommendations = []

        # Test concurrent operations optimization
        with patch.object(monitoring_tools["memory_tool"], "_store_content") as mock_store:
            mock_store.return_value = {"success": True, "content_id": "test_123", "namespace": "test_namespace"}

            # Sequential operations
            start_time = time.time()
            for i in range(20):
                result = monitoring_tools["memory_tool"]._run(
                    "store",
                    f"Sequential content {i}",
                    {"index": i},
                    "test_namespace",
                    sample_tenant_context["tenant"],
                    sample_tenant_context["workspace"],
                )
                assert result.success
            sequential_time = time.time() - start_time

            # Concurrent operations
            start_time = time.time()
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [
                    executor.submit(
                        monitoring_tools["memory_tool"]._run,
                        "store",
                        f"Concurrent content {i}",
                        {"index": i},
                        "test_namespace",
                        sample_tenant_context["tenant"],
                        sample_tenant_context["workspace"],
                    )
                    for i in range(20)
                ]

                for future in futures:
                    result = future.result()
                    assert result.success
            concurrent_time = time.time() - start_time

            # Calculate optimization opportunity
            if concurrent_time < sequential_time:
                improvement_percentage = (sequential_time - concurrent_time) / sequential_time * 100
                recommendations.append(
                    {
                        "type": "concurrent_operations",
                        "description": "Use concurrent operations for better performance",
                        "improvement": f"{improvement_percentage:.1f}% faster",
                        "implementation": "Use ThreadPoolExecutor for parallel operations",
                    }
                )

            # Test caching optimization
            with patch.object(monitoring_tools["analysis_tool"], "_analyze_comprehensive") as mock_analyze:
                mock_analyze.return_value = {
                    "political_topics": ["healthcare"],
                    "sentiment": "neutral",
                    "sentiment_confidence": 0.8,
                    "extracted_claims": ["Healthcare is important"],
                    "processing_time": 1.0,
                }

                # Test repeated analysis of same content
                content = "Healthcare policy is important for society"

                # First analysis
                start_time = time.time()
                result1 = monitoring_tools["analysis_tool"]._run(
                    content, "comprehensive", sample_tenant_context["tenant"], sample_tenant_context["workspace"]
                )
                first_time = time.time() - start_time

                # Second analysis (should be cached)
                start_time = time.time()
                result2 = monitoring_tools["analysis_tool"]._run(
                    content, "comprehensive", sample_tenant_context["tenant"], sample_tenant_context["workspace"]
                )
                second_time = time.time() - start_time

                # Check for caching opportunity
                if second_time < first_time:
                    caching_improvement = (first_time - second_time) / first_time * 100
                    recommendations.append(
                        {
                            "type": "caching",
                            "description": "Implement caching for repeated operations",
                            "improvement": f"{caching_improvement:.1f}% faster",
                            "implementation": "Cache analysis results for identical content",
                        }
                    )

                assert result1.success
                assert result2.success

            # Verify recommendations
            assert len(recommendations) > 0
            assert any(rec["type"] == "concurrent_operations" for rec in recommendations)

    def test_performance_reporting(self, monitoring_tools, sample_content, sample_tenant_context, monitoring_data_file):
        """Test performance reporting generation."""
        report_data = {
            "timestamp": time.time(),
            "report_period": "24h",
            "summary": {},
            "detailed_metrics": {},
            "recommendations": [],
        }

        # Generate summary metrics
        with patch.object(monitoring_tools["analysis_tool"], "_analyze_comprehensive") as mock_analyze:
            mock_analyze.return_value = {
                "political_topics": ["healthcare"],
                "sentiment": "neutral",
                "sentiment_confidence": 0.8,
                "extracted_claims": ["Healthcare is important"],
                "processing_time": 1.0,
            }

            # Simulate 24 hours of operations
            total_operations = 0
            successful_operations = 0
            total_execution_time = 0
            max_execution_time = 0
            min_execution_time = float("inf")

            for hour in range(24):
                for operation in range(10):
                    start_time = time.time()
                    result = monitoring_tools["analysis_tool"]._run(
                        f"{sample_content} hour_{hour}_op_{operation}",
                        "comprehensive",
                        sample_tenant_context["tenant"],
                        sample_tenant_context["workspace"],
                    )
                    end_time = time.time()

                    execution_time = end_time - start_time
                    total_operations += 1
                    if result.success:
                        successful_operations += 1
                    total_execution_time += execution_time
                    max_execution_time = max(max_execution_time, execution_time)
                    min_execution_time = min(min_execution_time, execution_time)

                    assert result.success

            # Generate summary
            report_data["summary"] = {
                "total_operations": total_operations,
                "successful_operations": successful_operations,
                "success_rate": successful_operations / total_operations,
                "average_execution_time": total_execution_time / total_operations,
                "max_execution_time": max_execution_time,
                "min_execution_time": min_execution_time,
                "total_execution_time": total_execution_time,
            }

            # Generate detailed metrics
            report_data["detailed_metrics"] = {
                "analysis_tool": {
                    "operations_count": total_operations,
                    "success_rate": successful_operations / total_operations,
                    "average_time": total_execution_time / total_operations,
                    "max_time": max_execution_time,
                    "min_time": min_execution_time,
                    "total_time": total_execution_time,
                }
            }

            # Generate recommendations
            if max_execution_time > 5.0:
                report_data["recommendations"].append(
                    {
                        "type": "performance",
                        "description": "Some operations are taking longer than expected",
                        "action": "Investigate and optimize slow operations",
                    }
                )

            if successful_operations / total_operations < 0.95:
                report_data["recommendations"].append(
                    {
                        "type": "reliability",
                        "description": "Success rate is below 95%",
                        "action": "Investigate and fix failing operations",
                    }
                )

            # Save report
            with open(monitoring_data_file, "w") as f:
                json.dump(report_data, f, indent=2)

            # Verify report data
            assert os.path.exists(monitoring_data_file)
            assert report_data["summary"]["total_operations"] == 240  # 24 hours * 10 operations
            assert report_data["summary"]["success_rate"] == 1.0
            assert report_data["summary"]["average_execution_time"] > 0
            assert report_data["summary"]["max_execution_time"] > 0
            assert report_data["summary"]["min_execution_time"] > 0

    def test_performance_alerting_system(self, monitoring_tools, sample_content, sample_tenant_context):
        """Test performance alerting system."""
        alert_system = {
            "alerts": [],
            "thresholds": {
                "execution_time": 5.0,
                "success_rate": 0.95,
                "error_rate": 0.05,
                "memory_usage": 80.0,
                "cpu_usage": 90.0,
            },
        }

        # Test execution time alert
        with patch.object(monitoring_tools["analysis_tool"], "_analyze_comprehensive") as mock_analyze:
            mock_analyze.return_value = {
                "political_topics": ["healthcare"],
                "sentiment": "neutral",
                "sentiment_confidence": 0.8,
                "extracted_claims": ["Healthcare is important"],
                "processing_time": 1.0,
            }

            start_time = time.time()
            result = monitoring_tools["analysis_tool"]._run(
                sample_content, "comprehensive", sample_tenant_context["tenant"], sample_tenant_context["workspace"]
            )
            end_time = time.time()

            execution_time = end_time - start_time

            if execution_time > alert_system["thresholds"]["execution_time"]:
                alert_system["alerts"].append(
                    {
                        "type": "execution_time",
                        "severity": "warning",
                        "message": f"Analysis tool execution time {execution_time:.2f}s exceeds threshold {alert_system['thresholds']['execution_time']}s",
                        "timestamp": time.time(),
                    }
                )

            # Test success rate alert
            if not result.success:
                alert_system["alerts"].append(
                    {
                        "type": "success_rate",
                        "severity": "error",
                        "message": "Analysis tool operation failed",
                        "timestamp": time.time(),
                    }
                )

            # Verify alert system
            assert len(alert_system["alerts"]) == 0  # No alerts should be triggered
            assert result.success
            assert execution_time < alert_system["thresholds"]["execution_time"]

    def test_performance_monitoring_dashboard(
        self, monitoring_tools, sample_content, sample_tenant_context, monitoring_data_file
    ):
        """Test performance monitoring dashboard."""
        dashboard_data = {
            "timestamp": time.time(),
            "overview": {},
            "tool_performance": {},
            "system_health": {},
            "alerts": [],
            "trends": {},
        }

        # Collect overview metrics
        with patch.object(monitoring_tools["analysis_tool"], "_analyze_comprehensive") as mock_analyze:
            mock_analyze.return_value = {
                "political_topics": ["healthcare"],
                "sentiment": "neutral",
                "sentiment_confidence": 0.8,
                "extracted_claims": ["Healthcare is important"],
                "processing_time": 1.0,
            }

            # Simulate dashboard data collection
            total_operations = 0
            successful_operations = 0
            total_execution_time = 0

            for i in range(100):  # 100 operations
                start_time = time.time()
                result = monitoring_tools["analysis_tool"]._run(
                    f"{sample_content} {i}",
                    "comprehensive",
                    sample_tenant_context["tenant"],
                    sample_tenant_context["workspace"],
                )
                end_time = time.time()

                total_operations += 1
                if result.success:
                    successful_operations += 1
                total_execution_time += end_time - start_time

                assert result.success

            # Generate dashboard data
            dashboard_data["overview"] = {
                "total_operations": total_operations,
                "successful_operations": successful_operations,
                "success_rate": successful_operations / total_operations,
                "average_execution_time": total_execution_time / total_operations,
                "total_execution_time": total_execution_time,
            }

            dashboard_data["tool_performance"]["analysis_tool"] = {
                "operations_count": total_operations,
                "success_rate": successful_operations / total_operations,
                "average_time": total_execution_time / total_operations,
                "total_time": total_execution_time,
            }

            dashboard_data["system_health"] = {
                "cpu_usage": 45.2,
                "memory_usage": 67.8,
                "disk_usage": 23.1,
                "network_latency": 12.5,
            }

            dashboard_data["trends"] = {
                "execution_time_trend": "stable",
                "success_rate_trend": "stable",
                "performance_variance": 0.1,
                "overall_health": "good",
            }

            # Save dashboard data
            with open(monitoring_data_file, "w") as f:
                json.dump(dashboard_data, f, indent=2)

            # Verify dashboard data
            assert os.path.exists(monitoring_data_file)
            assert dashboard_data["overview"]["total_operations"] == 100
            assert dashboard_data["overview"]["success_rate"] == 1.0
            assert dashboard_data["overview"]["average_execution_time"] > 0
            assert dashboard_data["system_health"]["cpu_usage"] > 0
            assert dashboard_data["system_health"]["memory_usage"] > 0
            assert dashboard_data["trends"]["overall_health"] == "good"
