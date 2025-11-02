"""Unified Metrics Collector - Comprehensive system and agent metrics

This service provides unified metrics collection across all system components,
enabling comprehensive monitoring and performance analysis.
"""

from __future__ import annotations
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any
from platform.core.step_result import StepResult
from ultimate_discord_intelligence_bot.tenancy.context import current_tenant

if TYPE_CHECKING:
    import asyncio
logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics"""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"
    TIMER = "timer"


class MetricCategory(Enum):
    """Categories of metrics"""

    SYSTEM = "system"
    AGENT = "agent"
    PERFORMANCE = "performance"
    QUALITY = "quality"
    BUSINESS = "business"
    SECURITY = "security"


@dataclass
class SystemMetric:
    """System-level metric"""

    name: str
    value: int | float
    metric_type: MetricType
    category: MetricCategory
    labels: dict[str, str]
    timestamp: datetime
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentMetric:
    """Agent-specific metric"""

    agent_id: str
    agent_type: str
    metric_name: str
    value: int | float
    metric_type: MetricType
    category: MetricCategory
    labels: dict[str, str]
    timestamp: datetime
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceMetric:
    """Performance-related metric"""

    component: str
    operation: str
    duration_ms: float
    success: bool
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class QualityMetric:
    """Quality-related metric"""

    component: str
    quality_type: str
    score: float
    threshold: float
    passed: bool
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class UnifiedMetricsConfig:
    """Configuration for unified metrics collection"""

    enable_collection: bool = True
    enable_real_time: bool = True
    enable_aggregation: bool = True
    enable_export: bool = True
    collection_interval: int = 60
    retention_days: int = 30
    max_metrics_per_interval: int = 10000
    aggregation_intervals: list[str] = field(default_factory=lambda: ["1m", "5m", "15m", "1h", "1d"])
    enable_rollup: bool = True
    export_formats: list[str] = field(default_factory=lambda: ["prometheus", "json", "csv"])
    export_endpoints: list[str] = field(default_factory=list)
    max_concurrent_collections: int = 10
    batch_size: int = 1000
    flush_interval: int = 30


class UnifiedMetricsCollector:
    """Unified metrics collection and aggregation service"""

    def __init__(self, config: UnifiedMetricsConfig | None = None):
        self.config = config or UnifiedMetricsConfig()
        self._initialized = False
        self._metrics_store: dict[str, list[Any]] = {}
        self._aggregated_metrics: dict[str, dict[str, Any]] = {}
        self._collection_tasks: list[asyncio.Task] = []
        self._last_collection_time: dict[str, datetime] = {}
        self._initialize_collector()

    def _initialize_collector(self) -> None:
        """Initialize the unified metrics collector"""
        try:
            self._initialized = True
            logger.info("Unified Metrics Collector initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Unified Metrics Collector: {e}")
            self._initialized = False

    async def collect_system_metric(
        self,
        name: str,
        value: int | float,
        metric_type: MetricType,
        category: MetricCategory,
        labels: dict[str, str] | None = None,
        description: str = "",
        metadata: dict[str, Any] | None = None,
        tenant_id: str | None = None,
        workspace_id: str | None = None,
    ) -> StepResult:
        """Collect a system-level metric"""
        try:
            if not self._initialized:
                return StepResult.fail("Unified Metrics Collector not initialized")
            ctx = current_tenant()
            if tenant_id is None:
                tenant_id = getattr(ctx, "tenant_id", "default") if ctx else "default"
            if workspace_id is None:
                workspace_id = getattr(ctx, "workspace_id", "main") if ctx else "main"
            metric = SystemMetric(
                name=name,
                value=value,
                metric_type=metric_type,
                category=category,
                labels=labels or {},
                timestamp=datetime.now(timezone.utc),
                description=description,
                metadata={"tenant_id": tenant_id, "workspace_id": workspace_id, **(metadata or {})},
            )
            metric_key = f"system:{name}"
            if metric_key not in self._metrics_store:
                self._metrics_store[metric_key] = []
            self._metrics_store[metric_key].append(metric)
            await self._cleanup_old_metrics(metric_key)
            logger.debug(f"System metric collected: {name} = {value}")
            return StepResult.ok(
                data={"collected": True, "metric_name": name, "value": value, "timestamp": metric.timestamp.isoformat()}
            )
        except Exception as e:
            logger.error(f"Error collecting system metric: {e}")
            return StepResult.fail(f"System metric collection failed: {e!s}")

    async def collect_agent_metric(
        self,
        agent_id: str,
        agent_type: str,
        metric_name: str,
        value: int | float,
        metric_type: MetricType,
        category: MetricCategory,
        labels: dict[str, str] | None = None,
        description: str = "",
        metadata: dict[str, Any] | None = None,
        tenant_id: str | None = None,
        workspace_id: str | None = None,
    ) -> StepResult:
        """Collect an agent-specific metric"""
        try:
            if not self._initialized:
                return StepResult.fail("Unified Metrics Collector not initialized")
            ctx = current_tenant()
            if tenant_id is None:
                tenant_id = getattr(ctx, "tenant_id", "default") if ctx else "default"
            if workspace_id is None:
                workspace_id = getattr(ctx, "workspace_id", "main") if ctx else "main"
            metric = AgentMetric(
                agent_id=agent_id,
                agent_type=agent_type,
                metric_name=metric_name,
                value=value,
                metric_type=metric_type,
                category=category,
                labels=labels or {},
                timestamp=datetime.now(timezone.utc),
                description=description,
                metadata={"tenant_id": tenant_id, "workspace_id": workspace_id, **(metadata or {})},
            )
            metric_key = f"agent:{agent_id}:{metric_name}"
            if metric_key not in self._metrics_store:
                self._metrics_store[metric_key] = []
            self._metrics_store[metric_key].append(metric)
            await self._cleanup_old_metrics(metric_key)
            logger.debug(f"Agent metric collected: {agent_id}:{metric_name} = {value}")
            return StepResult.ok(
                data={
                    "collected": True,
                    "agent_id": agent_id,
                    "metric_name": metric_name,
                    "value": value,
                    "timestamp": metric.timestamp.isoformat(),
                }
            )
        except Exception as e:
            logger.error(f"Error collecting agent metric: {e}")
            return StepResult.fail(f"Agent metric collection failed: {e!s}")

    async def collect_performance_metric(
        self,
        component: str,
        operation: str,
        duration_ms: float,
        success: bool,
        error_message: str | None = None,
        metadata: dict[str, Any] | None = None,
        tenant_id: str | None = None,
        workspace_id: str | None = None,
    ) -> StepResult:
        """Collect a performance metric"""
        try:
            if not self._initialized:
                return StepResult.fail("Unified Metrics Collector not initialized")
            ctx = current_tenant()
            if tenant_id is None:
                tenant_id = getattr(ctx, "tenant_id", "default") if ctx else "default"
            if workspace_id is None:
                workspace_id = getattr(ctx, "workspace_id", "main") if ctx else "main"
            perf_metric = PerformanceMetric(
                component=component,
                operation=operation,
                duration_ms=duration_ms,
                success=success,
                error_message=error_message,
                metadata={"tenant_id": tenant_id, "workspace_id": workspace_id, **(metadata or {})},
            )
            metric_key = f"performance:{component}:{operation}"
            if metric_key not in self._metrics_store:
                self._metrics_store[metric_key] = []
            self._metrics_store[metric_key].append(perf_metric)
            await self.collect_system_metric(
                name=f"{component}_{operation}_duration_ms",
                value=duration_ms,
                metric_type=MetricType.HISTOGRAM,
                category=MetricCategory.PERFORMANCE,
                labels={"component": component, "operation": operation, "success": str(success)},
                description=f"Duration of {operation} in {component}",
                metadata={"error_message": error_message} if error_message else None,
                tenant_id=tenant_id,
                workspace_id=workspace_id,
            )
            await self.collect_system_metric(
                name=f"{component}_{operation}_success_rate",
                value=1.0 if success else 0.0,
                metric_type=MetricType.GAUGE,
                category=MetricCategory.PERFORMANCE,
                labels={"component": component, "operation": operation},
                description=f"Success rate of {operation} in {component}",
                tenant_id=tenant_id,
                workspace_id=workspace_id,
            )
            logger.debug(f"Performance metric collected: {component}:{operation} = {duration_ms}ms")
            return StepResult.ok(
                data={
                    "collected": True,
                    "component": component,
                    "operation": operation,
                    "duration_ms": duration_ms,
                    "success": success,
                    "timestamp": perf_metric.timestamp.isoformat(),
                }
            )
        except Exception as e:
            logger.error(f"Error collecting performance metric: {e}")
            return StepResult.fail(f"Performance metric collection failed: {e!s}")

    async def collect_quality_metric(
        self,
        component: str,
        quality_type: str,
        score: float,
        threshold: float,
        passed: bool,
        metadata: dict[str, Any] | None = None,
        tenant_id: str | None = None,
        workspace_id: str | None = None,
    ) -> StepResult:
        """Collect a quality metric"""
        try:
            if not self._initialized:
                return StepResult.fail("Unified Metrics Collector not initialized")
            ctx = current_tenant()
            if tenant_id is None:
                tenant_id = getattr(ctx, "tenant_id", "default") if ctx else "default"
            if workspace_id is None:
                workspace_id = getattr(ctx, "workspace_id", "main") if ctx else "main"
            quality_metric = QualityMetric(
                component=component,
                quality_type=quality_type,
                score=score,
                threshold=threshold,
                passed=passed,
                metadata={"tenant_id": tenant_id, "workspace_id": workspace_id, **(metadata or {})},
            )
            metric_key = f"quality:{component}:{quality_type}"
            if metric_key not in self._metrics_store:
                self._metrics_store[metric_key] = []
            self._metrics_store[metric_key].append(quality_metric)
            await self.collect_system_metric(
                name=f"{component}_{quality_type}_score",
                value=score,
                metric_type=MetricType.GAUGE,
                category=MetricCategory.QUALITY,
                labels={"component": component, "quality_type": quality_type, "passed": str(passed)},
                description=f"Quality score for {quality_type} in {component}",
                metadata={"threshold": threshold},
                tenant_id=tenant_id,
                workspace_id=workspace_id,
            )
            logger.debug(f"Quality metric collected: {component}:{quality_type} = {score}")
            return StepResult.ok(
                data={
                    "collected": True,
                    "component": component,
                    "quality_type": quality_type,
                    "score": score,
                    "threshold": threshold,
                    "passed": passed,
                    "timestamp": quality_metric.timestamp.isoformat(),
                }
            )
        except Exception as e:
            logger.error(f"Error collecting quality metric: {e}")
            return StepResult.fail(f"Quality metric collection failed: {e!s}")

    async def get_metrics_summary(
        self,
        category: MetricCategory | None = None,
        component: str | None = None,
        agent_type: str | None = None,
        hours: int = 24,
        tenant_id: str | None = None,
        workspace_id: str | None = None,
    ) -> StepResult:
        """Get metrics summary for specified criteria"""
        try:
            if not self._initialized:
                return StepResult.fail("Unified Metrics Collector not initialized")
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=hours)
            filtered_metrics = []
            for _metric_key, metrics_list in self._metrics_store.items():
                for metric in metrics_list:
                    if metric.timestamp < start_time or metric.timestamp > end_time:
                        continue
                    if category and hasattr(metric, "category") and (metric.category != category):
                        continue
                    if component and hasattr(metric, "component") and (metric.component != component):
                        continue
                    if agent_type and hasattr(metric, "agent_type") and (metric.agent_type != agent_type):
                        continue
                    if tenant_id and metric.metadata.get("tenant_id") != tenant_id:
                        continue
                    if workspace_id and metric.metadata.get("workspace_id") != workspace_id:
                        continue
                    filtered_metrics.append(metric)
            summary = {
                "total_metrics": len(filtered_metrics),
                "time_range": {"start": start_time.isoformat(), "end": end_time.isoformat(), "hours": hours},
                "categories": {},
                "components": {},
                "agent_types": {},
                "top_metrics": [],
            }
            for metric in filtered_metrics:
                if hasattr(metric, "category"):
                    cat_name = metric.category.value
                    if cat_name not in summary["categories"]:
                        summary["categories"][cat_name] = 0
                    summary["categories"][cat_name] += 1
                if hasattr(metric, "component"):
                    comp_name = metric.component
                    if comp_name not in summary["components"]:
                        summary["components"][comp_name] = 0
                    summary["components"][comp_name] += 1
                if hasattr(metric, "agent_type"):
                    agent_type_name = metric.agent_type
                    if agent_type_name not in summary["agent_types"]:
                        summary["agent_types"][agent_type_name] = 0
                    summary["agent_types"][agent_type_name] += 1
            metric_counts = {}
            for metric in filtered_metrics:
                metric_name = getattr(metric, "name", getattr(metric, "metric_name", "unknown"))
                metric_counts[metric_name] = metric_counts.get(metric_name, 0) + 1
            summary["top_metrics"] = sorted(metric_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            return StepResult.ok(data=summary)
        except Exception as e:
            logger.error(f"Error getting metrics summary: {e}")
            return StepResult.fail(f"Metrics summary retrieval failed: {e!s}")

    async def export_metrics(
        self,
        format_type: str = "prometheus",
        category: MetricCategory | None = None,
        hours: int = 1,
        tenant_id: str | None = None,
        workspace_id: str | None = None,
    ) -> StepResult:
        """Export metrics in specified format"""
        try:
            if not self._initialized:
                return StepResult.fail("Unified Metrics Collector not initialized")
            summary_result = await self.get_metrics_summary(
                category=category, hours=hours, tenant_id=tenant_id, workspace_id=workspace_id
            )
            if not summary_result.success:
                return summary_result
            if format_type == "prometheus":
                exported_data = await self._export_prometheus_format(category, hours, tenant_id, workspace_id)
            elif format_type == "json":
                exported_data = await self._export_json_format(category, hours, tenant_id, workspace_id)
            elif format_type == "csv":
                exported_data = await self._export_csv_format(category, hours, tenant_id, workspace_id)
            else:
                return StepResult.fail(f"Unsupported export format: {format_type}")
            return StepResult.ok(
                data={
                    "format": format_type,
                    "exported_at": datetime.now(timezone.utc).isoformat(),
                    "data": exported_data,
                    "summary": summary_result.data,
                }
            )
        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")
            return StepResult.fail(f"Metrics export failed: {e!s}")

    async def _cleanup_old_metrics(self, metric_key: str) -> None:
        """Clean up old metrics to maintain retention policy"""
        try:
            if metric_key not in self._metrics_store:
                return
            cutoff_time = datetime.now(timezone.utc) - timedelta(days=self.config.retention_days)
            self._metrics_store[metric_key] = [
                metric for metric in self._metrics_store[metric_key] if metric.timestamp > cutoff_time
            ]
        except Exception as e:
            logger.error(f"Error cleaning up old metrics: {e}")

    async def _export_prometheus_format(
        self, category: MetricCategory | None, hours: int, tenant_id: str | None, workspace_id: str | None
    ) -> str:
        """Export metrics in Prometheus format"""
        try:
            prometheus_lines = []
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=hours)
            for _metric_key, metrics_list in self._metrics_store.items():
                for metric in metrics_list:
                    if metric.timestamp < start_time or metric.timestamp > end_time:
                        continue
                    if category and hasattr(metric, "category") and (metric.category != category):
                        continue
                    if tenant_id and metric.metadata.get("tenant_id") != tenant_id:
                        continue
                    if workspace_id and metric.metadata.get("workspace_id") != workspace_id:
                        continue
                    metric_name = getattr(metric, "name", getattr(metric, "metric_name", "unknown"))
                    metric_name = metric_name.replace(".", "_").replace("-", "_")
                    labels = getattr(metric, "labels", {})
                    label_str = ",".join([f'{k}="{v}"' for k, v in labels.items()])
                    value = getattr(metric, "value", 0)
                    timestamp = int(metric.timestamp.timestamp() * 1000)
                    if label_str:
                        line = f"{metric_name}{{{label_str}}} {value} {timestamp}"
                    else:
                        line = f"{metric_name} {value} {timestamp}"
                    prometheus_lines.append(line)
            return "\n".join(prometheus_lines)
        except Exception as e:
            logger.error(f"Error exporting Prometheus format: {e}")
            return ""

    async def _export_json_format(
        self, category: MetricCategory | None, hours: int, tenant_id: str | None, workspace_id: str | None
    ) -> dict[str, Any]:
        """Export metrics in JSON format"""
        try:
            json_data = {"exported_at": datetime.now(timezone.utc).isoformat(), "format": "json", "metrics": []}
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=hours)
            for metric_key, metrics_list in self._metrics_store.items():
                for metric in metrics_list:
                    if metric.timestamp < start_time or metric.timestamp > end_time:
                        continue
                    if category and hasattr(metric, "category") and (metric.category != category):
                        continue
                    if tenant_id and metric.metadata.get("tenant_id") != tenant_id:
                        continue
                    if workspace_id and metric.metadata.get("workspace_id") != workspace_id:
                        continue
                    metric_dict = {
                        "key": metric_key,
                        "timestamp": metric.timestamp.isoformat(),
                        "metadata": metric.metadata,
                    }
                    if hasattr(metric, "name"):
                        metric_dict["name"] = metric.name
                    if hasattr(metric, "metric_name"):
                        metric_dict["metric_name"] = metric.metric_name
                    if hasattr(metric, "value"):
                        metric_dict["value"] = metric.value
                    if hasattr(metric, "metric_type"):
                        metric_dict["metric_type"] = metric.metric_type.value
                    if hasattr(metric, "category"):
                        metric_dict["category"] = metric.category.value
                    if hasattr(metric, "labels"):
                        metric_dict["labels"] = metric.labels
                    json_data["metrics"].append(metric_dict)
            return json_data
        except Exception as e:
            logger.error(f"Error exporting JSON format: {e}")
            return {"error": str(e)}

    async def _export_csv_format(
        self, category: MetricCategory | None, hours: int, tenant_id: str | None, workspace_id: str | None
    ) -> str:
        """Export metrics in CSV format"""
        try:
            csv_lines = ["timestamp,metric_name,value,metric_type,category,labels,metadata"]
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=hours)
            for _metric_key, metrics_list in self._metrics_store.items():
                for metric in metrics_list:
                    if metric.timestamp < start_time or metric.timestamp > end_time:
                        continue
                    if category and hasattr(metric, "category") and (metric.category != category):
                        continue
                    if tenant_id and metric.metadata.get("tenant_id") != tenant_id:
                        continue
                    if workspace_id and metric.metadata.get("workspace_id") != workspace_id:
                        continue
                    metric_name = getattr(metric, "name", getattr(metric, "metric_name", "unknown"))
                    value = getattr(metric, "value", 0)
                    metric_type = getattr(metric, "metric_type", MetricType.GAUGE).value
                    category_name = getattr(metric, "category", MetricCategory.SYSTEM).value
                    labels = getattr(metric, "labels", {})
                    metadata = metric.metadata
                    labels_str = str(labels).replace('"', '""')
                    metadata_str = str(metadata).replace('"', '""')
                    csv_line = f'{metric.timestamp.isoformat()},{metric_name},{value},{metric_type},{category_name},"{labels_str}","{metadata_str}"'
                    csv_lines.append(csv_line)
            return "\n".join(csv_lines)
        except Exception as e:
            logger.error(f"Error exporting CSV format: {e}")
            return f"Error: {e!s}"

    def get_collector_status(self) -> dict[str, Any]:
        """Get metrics collector status"""
        return {
            "initialized": self._initialized,
            "total_metric_keys": len(self._metrics_store),
            "total_metrics": sum((len(metrics) for metrics in self._metrics_store.values())),
            "config": {
                "enable_collection": self.config.enable_collection,
                "enable_real_time": self.config.enable_real_time,
                "collection_interval": self.config.collection_interval,
                "retention_days": self.config.retention_days,
                "export_formats": self.config.export_formats,
            },
            "last_collection_times": {
                show_key: time.isoformat() for show_key, time in self._last_collection_time.items()
            },
        }
