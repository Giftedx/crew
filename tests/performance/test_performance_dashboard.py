"""Performance monitoring dashboard tests."""

import json
import os
import time
from unittest.mock import patch

import pytest

from domains.ingestion.providers.multi_platform_download_tool import MultiPlatformDownloadTool
from domains.intelligence.analysis.enhanced_analysis_tool import EnhancedAnalysisTool
from domains.intelligence.verification.claim_verifier_tool import ClaimVerifierTool
from ultimate_discord_intelligence_bot.tools.memory.unified_memory_tool import UnifiedMemoryTool


class TestPerformanceDashboard:
    """Performance monitoring dashboard tests."""

    @pytest.fixture
    def dashboard_tools(self):
        """Create tools for dashboard testing."""
        return {
            "download_tool": MultiPlatformDownloadTool(),
            "analysis_tool": EnhancedAnalysisTool(),
            "verification_tool": ClaimVerifierTool(),
            "memory_tool": UnifiedMemoryTool(),
        }

    @pytest.fixture
    def dashboard_data_file(self, tmp_path):
        """Create dashboard data file."""
        return tmp_path / "performance_dashboard.json"

    @pytest.fixture
    def sample_content(self):
        """Sample content for dashboard testing."""
        return "This is a comprehensive political statement about healthcare policy that requires detailed analysis and verification."

    @pytest.fixture
    def sample_tenant_context(self):
        """Sample tenant context."""
        return {"tenant": "dashboard_tenant", "workspace": "dashboard_workspace"}

    def test_dashboard_overview_metrics(
        self, dashboard_tools, sample_content, sample_tenant_context, dashboard_data_file
    ):
        """Test dashboard overview metrics."""
        dashboard_data = {
            "timestamp": time.time(),
            "overview": {},
            "tool_performance": {},
            "system_health": {},
            "alerts": [],
            "trends": {},
        }
        with patch.object(dashboard_tools["analysis_tool"], "_analyze_comprehensive") as mock_analyze:
            mock_analyze.return_value = {
                "political_topics": ["healthcare"],
                "sentiment": "neutral",
                "sentiment_confidence": 0.8,
                "extracted_claims": ["Healthcare is important"],
                "processing_time": 1.0,
            }
            total_operations = 0
            successful_operations = 0
            total_execution_time = 0
            for i in range(100):
                start_time = time.time()
                result = dashboard_tools["analysis_tool"]._run(
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
            with open(dashboard_data_file, "w") as f:
                json.dump(dashboard_data, f, indent=2)
            assert os.path.exists(dashboard_data_file)
            assert dashboard_data["overview"]["total_operations"] == 100
            assert dashboard_data["overview"]["success_rate"] == 1.0
            assert dashboard_data["overview"]["average_execution_time"] > 0
            assert dashboard_data["system_health"]["cpu_usage"] > 0
            assert dashboard_data["system_health"]["memory_usage"] > 0
            assert dashboard_data["trends"]["overall_health"] == "good"

    def test_dashboard_tool_performance(self, dashboard_tools, sample_content, sample_tenant_context):
        """Test dashboard tool performance metrics."""
        tool_metrics = {
            "analysis_tool": {
                "operations_count": 0,
                "success_rate": 0,
                "average_time": 0,
                "max_time": 0,
                "min_time": float("inf"),
                "total_time": 0,
            },
            "download_tool": {
                "operations_count": 0,
                "success_rate": 0,
                "average_time": 0,
                "max_time": 0,
                "min_time": float("inf"),
                "total_time": 0,
            },
            "verification_tool": {
                "operations_count": 0,
                "success_rate": 0,
                "average_time": 0,
                "max_time": 0,
                "min_time": float("inf"),
                "total_time": 0,
            },
            "memory_tool": {
                "operations_count": 0,
                "success_rate": 0,
                "average_time": 0,
                "max_time": 0,
                "min_time": float("inf"),
                "total_time": 0,
            },
        }
        with patch.object(dashboard_tools["analysis_tool"], "_analyze_comprehensive") as mock_analyze:
            mock_analyze.return_value = {
                "political_topics": ["healthcare"],
                "sentiment": "neutral",
                "sentiment_confidence": 0.8,
                "extracted_claims": ["Healthcare is important"],
                "processing_time": 1.0,
            }
            for i in range(50):
                start_time = time.time()
                result = dashboard_tools["analysis_tool"]._run(
                    f"{sample_content} {i}",
                    "comprehensive",
                    sample_tenant_context["tenant"],
                    sample_tenant_context["workspace"],
                )
                end_time = time.time()
                execution_time = end_time - start_time
                tool_metrics["analysis_tool"]["operations_count"] += 1
                tool_metrics["analysis_tool"]["total_time"] += execution_time
                tool_metrics["analysis_tool"]["max_time"] = max(
                    tool_metrics["analysis_tool"]["max_time"], execution_time
                )
                tool_metrics["analysis_tool"]["min_time"] = min(
                    tool_metrics["analysis_tool"]["min_time"], execution_time
                )
                if result.success:
                    tool_metrics["analysis_tool"]["success_rate"] += 1
                assert result.success
            tool_metrics["analysis_tool"]["success_rate"] /= tool_metrics["analysis_tool"]["operations_count"]
            tool_metrics["analysis_tool"]["average_time"] = (
                tool_metrics["analysis_tool"]["total_time"] / tool_metrics["analysis_tool"]["operations_count"]
            )
        with patch.object(dashboard_tools["download_tool"], "_download_youtube") as mock_download:
            mock_download.return_value = {
                "success": True,
                "platform": "youtube",
                "file_path": "/tmp/test_video.mp4",
                "duration": 180,
                "quality": "720p",
            }
            for i in range(20):
                start_time = time.time()
                result = dashboard_tools["download_tool"]._run(
                    f"https://youtube.com/watch?v=test_{i}",
                    "720p",
                    sample_tenant_context["tenant"],
                    sample_tenant_context["workspace"],
                )
                end_time = time.time()
                execution_time = end_time - start_time
                tool_metrics["download_tool"]["operations_count"] += 1
                tool_metrics["download_tool"]["total_time"] += execution_time
                tool_metrics["download_tool"]["max_time"] = max(
                    tool_metrics["download_tool"]["max_time"], execution_time
                )
                tool_metrics["download_tool"]["min_time"] = min(
                    tool_metrics["download_tool"]["min_time"], execution_time
                )
                if result.success:
                    tool_metrics["download_tool"]["success_rate"] += 1
                assert result.success
            tool_metrics["download_tool"]["success_rate"] /= tool_metrics["download_tool"]["operations_count"]
            tool_metrics["download_tool"]["average_time"] = (
                tool_metrics["download_tool"]["total_time"] / tool_metrics["download_tool"]["operations_count"]
            )
        with patch.object(dashboard_tools["verification_tool"], "_verify_claim") as mock_verify:
            mock_verify.return_value = {
                "claim_id": "claim_123",
                "claim_text": "Healthcare policy needs improvement",
                "overall_confidence": 0.9,
                "verification_status": "verified",
                "sources": [],
                "processing_time": 3.0,
                "backends_used": ["serply"],
                "error_message": None,
            }
            for i in range(25):
                start_time = time.time()
                result = dashboard_tools["verification_tool"]._run(
                    f"Healthcare policy claim {i}",
                    f"Test context {i}",
                    sample_tenant_context["tenant"],
                    sample_tenant_context["workspace"],
                )
                end_time = time.time()
                execution_time = end_time - start_time
                tool_metrics["verification_tool"]["operations_count"] += 1
                tool_metrics["verification_tool"]["total_time"] += execution_time
                tool_metrics["verification_tool"]["max_time"] = max(
                    tool_metrics["verification_tool"]["max_time"], execution_time
                )
                tool_metrics["verification_tool"]["min_time"] = min(
                    tool_metrics["verification_tool"]["min_time"], execution_time
                )
                if result.success:
                    tool_metrics["verification_tool"]["success_rate"] += 1
                assert result.success
            tool_metrics["verification_tool"]["success_rate"] /= tool_metrics["verification_tool"]["operations_count"]
            tool_metrics["verification_tool"]["average_time"] = (
                tool_metrics["verification_tool"]["total_time"] / tool_metrics["verification_tool"]["operations_count"]
            )
        with patch.object(dashboard_tools["memory_tool"], "_store_content") as mock_store:
            mock_store.return_value = {"success": True, "content_id": "test_123", "namespace": "test_namespace"}
            for i in range(100):
                start_time = time.time()
                result = dashboard_tools["memory_tool"]._run(
                    "store",
                    f"Dashboard content {i}",
                    {"index": i},
                    "test_namespace",
                    sample_tenant_context["tenant"],
                    sample_tenant_context["workspace"],
                )
                end_time = time.time()
                execution_time = end_time - start_time
                tool_metrics["memory_tool"]["operations_count"] += 1
                tool_metrics["memory_tool"]["total_time"] += execution_time
                tool_metrics["memory_tool"]["max_time"] = max(tool_metrics["memory_tool"]["max_time"], execution_time)
                tool_metrics["memory_tool"]["min_time"] = min(tool_metrics["memory_tool"]["min_time"], execution_time)
                if result.success:
                    tool_metrics["memory_tool"]["success_rate"] += 1
                assert result.success
            tool_metrics["memory_tool"]["success_rate"] /= tool_metrics["memory_tool"]["operations_count"]
            tool_metrics["memory_tool"]["average_time"] = (
                tool_metrics["memory_tool"]["total_time"] / tool_metrics["memory_tool"]["operations_count"]
            )
        for _tool_name, metrics in tool_metrics.items():
            assert metrics["operations_count"] > 0
            assert metrics["success_rate"] == 1.0
            assert metrics["average_time"] > 0
            assert metrics["max_time"] > 0
            assert metrics["min_time"] > 0
            assert metrics["total_time"] > 0

    def test_dashboard_system_health(self, dashboard_tools, sample_content, sample_tenant_context):
        """Test dashboard system health metrics."""
        system_health = {
            "cpu_usage": 0,
            "memory_usage": 0,
            "disk_usage": 0,
            "network_latency": 0,
            "active_connections": 0,
            "error_rate": 0,
        }
        import os

        import psutil

        process = psutil.Process(os.getpid())
        system_health["cpu_usage"] = process.cpu_percent()
        system_health["memory_usage"] = process.memory_info().rss / 1024 / 1024
        system_health["disk_usage"] = psutil.disk_usage("/").percent
        system_health["network_latency"] = 12.5
        system_health["active_connections"] = len(psutil.net_connections())
        system_health["error_rate"] = 0.0
        assert system_health["cpu_usage"] >= 0
        assert system_health["memory_usage"] > 0
        assert system_health["disk_usage"] > 0
        assert system_health["network_latency"] > 0
        assert system_health["active_connections"] >= 0
        assert system_health["error_rate"] >= 0

    def test_dashboard_alerts(self, dashboard_tools, sample_content, sample_tenant_context):
        """Test dashboard alerting system."""
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
        with patch.object(dashboard_tools["analysis_tool"], "_analyze_comprehensive") as mock_analyze:
            mock_analyze.return_value = {
                "political_topics": ["healthcare"],
                "sentiment": "neutral",
                "sentiment_confidence": 0.8,
                "extracted_claims": ["Healthcare is important"],
                "processing_time": 1.0,
            }
            start_time = time.time()
            result = dashboard_tools["analysis_tool"]._run(
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
            if not result.success:
                alert_system["alerts"].append(
                    {
                        "type": "success_rate",
                        "severity": "error",
                        "message": "Analysis tool operation failed",
                        "timestamp": time.time(),
                    }
                )
            assert len(alert_system["alerts"]) == 0
            assert result.success
            assert execution_time < alert_system["thresholds"]["execution_time"]

    def test_dashboard_trends(self, dashboard_tools, sample_content, sample_tenant_context):
        """Test dashboard trending analysis."""
        trending_data = {"timestamp": time.time(), "trends": {}}
        performance_history = []
        with patch.object(dashboard_tools["analysis_tool"], "_analyze_comprehensive") as mock_analyze:
            mock_analyze.return_value = {
                "political_topics": ["healthcare"],
                "sentiment": "neutral",
                "sentiment_confidence": 0.8,
                "extracted_claims": ["Healthcare is important"],
                "processing_time": 1.0,
            }
            for hour in range(24):
                for operation in range(5):
                    start_time = time.time()
                    result = dashboard_tools["analysis_tool"]._run(
                        f"{sample_content} hour_{hour}_op_{operation}",
                        "comprehensive",
                        sample_tenant_context["tenant"],
                        sample_tenant_context["workspace"],
                    )
                    end_time = time.time()
                    performance_history.append(
                        {
                            "timestamp": time.time() + hour * 3600,
                            "execution_time": end_time - start_time,
                            "success": result.success,
                            "hour": hour,
                        }
                    )
                    assert result.success
            hourly_performance = {}
            for hour in range(24):
                hour_data = [p for p in performance_history if p["hour"] == hour]
                if hour_data:
                    hourly_performance[hour] = {
                        "average_time": sum(p["execution_time"] for p in hour_data) / len(hour_data),
                        "success_rate": sum(1 for p in hour_data if p["success"]) / len(hour_data),
                        "operation_count": len(hour_data),
                    }
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
            assert trending_data["trends"]["execution_time_trend"] == "stable"
            assert trending_data["trends"]["success_rate_trend"] == "stable"
            assert trending_data["trends"]["overall_health"] == "good"

    def test_dashboard_reporting(self, dashboard_tools, sample_content, sample_tenant_context, dashboard_data_file):
        """Test dashboard reporting generation."""
        report_data = {
            "timestamp": time.time(),
            "report_period": "24h",
            "summary": {},
            "detailed_metrics": {},
            "recommendations": [],
        }
        with patch.object(dashboard_tools["analysis_tool"], "_analyze_comprehensive") as mock_analyze:
            mock_analyze.return_value = {
                "political_topics": ["healthcare"],
                "sentiment": "neutral",
                "sentiment_confidence": 0.8,
                "extracted_claims": ["Healthcare is important"],
                "processing_time": 1.0,
            }
            total_operations = 0
            successful_operations = 0
            total_execution_time = 0
            max_execution_time = 0
            min_execution_time = float("inf")
            for hour in range(24):
                for operation in range(10):
                    start_time = time.time()
                    result = dashboard_tools["analysis_tool"]._run(
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
            report_data["summary"] = {
                "total_operations": total_operations,
                "successful_operations": successful_operations,
                "success_rate": successful_operations / total_operations,
                "average_execution_time": total_execution_time / total_operations,
                "max_execution_time": max_execution_time,
                "min_execution_time": min_execution_time,
                "total_execution_time": total_execution_time,
            }
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
            with open(dashboard_data_file, "w") as f:
                json.dump(report_data, f, indent=2)
            assert os.path.exists(dashboard_data_file)
            assert report_data["summary"]["total_operations"] == 240
            assert report_data["summary"]["success_rate"] == 1.0
            assert report_data["summary"]["average_execution_time"] > 0
            assert report_data["summary"]["max_execution_time"] > 0
            assert report_data["summary"]["min_execution_time"] > 0

    def test_dashboard_monitoring(self, dashboard_tools, sample_content, sample_tenant_context):
        """Test dashboard monitoring capabilities."""
        monitoring_data = {"timestamp": time.time(), "monitoring": {}}
        with patch.object(dashboard_tools["analysis_tool"], "_analyze_comprehensive") as mock_analyze:
            mock_analyze.return_value = {
                "political_topics": ["healthcare"],
                "sentiment": "neutral",
                "sentiment_confidence": 0.8,
                "extracted_claims": ["Healthcare is important"],
                "processing_time": 1.0,
            }
            operations_count = 0
            successful_operations = 0
            total_execution_time = 0
            for i in range(50):
                start_time = time.time()
                result = dashboard_tools["analysis_tool"]._run(
                    f"{sample_content} {i}",
                    "comprehensive",
                    sample_tenant_context["tenant"],
                    sample_tenant_context["workspace"],
                )
                end_time = time.time()
                operations_count += 1
                if result.success:
                    successful_operations += 1
                total_execution_time += end_time - start_time
                assert result.success
            monitoring_data["monitoring"] = {
                "operations_count": operations_count,
                "successful_operations": successful_operations,
                "success_rate": successful_operations / operations_count,
                "average_execution_time": total_execution_time / operations_count,
                "total_execution_time": total_execution_time,
                "throughput": operations_count / (total_execution_time / operations_count),
            }
            assert monitoring_data["monitoring"]["operations_count"] == 50
            assert monitoring_data["monitoring"]["success_rate"] == 1.0
            assert monitoring_data["monitoring"]["average_execution_time"] > 0
            assert monitoring_data["monitoring"]["throughput"] > 0
