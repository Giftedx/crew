"""
MetricsCollectionTool - Collect and report telemetry metrics.

This tool provides metrics collection and reporting capabilities for monitoring
application performance, tracking events, and gathering operational telemetry.
"""

from typing import Any

import structlog

from ai.frameworks.tools.converters import BaseUniversalTool
from ai.frameworks.tools.protocols import ParameterSchema, ToolMetadata


logger = structlog.get_logger(__name__)


class MetricsCollectionTool(BaseUniversalTool):
    """
    A universal metrics collection tool for telemetry and monitoring.

    Supports various metric types (counter, gauge, histogram, summary) with
    tags/labels for dimensional metrics and integration with monitoring systems.

    Example:
        # Increment a counter
        result = await metrics.run(
            metric_name="api_requests_total",
            metric_type="counter",
            value=1,
            tags={"endpoint": "/users", "method": "GET"}
        )

        # Record a gauge value
        result = await metrics.run(
            metric_name="memory_usage_bytes",
            metric_type="gauge",
            value=1024000000,
            tags={"service": "api"}
        )
    """

    name = "metrics-collection"
    description = (
        "Collect and report application metrics for monitoring and observability. "
        "Supports counters, gauges, histograms, and summaries with dimensional tags. "
        "Integrates with Prometheus, StatsD, and other monitoring systems."
    )

    parameters = {
        "metric_name": ParameterSchema(
            type="string",
            description="Name of the metric (use snake_case, e.g., 'api_requests_total')",
            required=True,
        ),
        "metric_type": ParameterSchema(
            type="string",
            description="Type of metric to collect",
            required=True,
            enum=["counter", "gauge", "histogram", "summary"],
        ),
        "value": ParameterSchema(
            type="number",
            description="Metric value to record",
            required=True,
        ),
        "tags": ParameterSchema(
            type="object",
            description="Tags/labels for dimensional metrics (optional)",
            required=False,
            default={},
        ),
        "timestamp": ParameterSchema(
            type="string",
            description="Timestamp for the metric (ISO 8601 format, optional)",
            required=False,
        ),
        "unit": ParameterSchema(
            type="string",
            description="Unit of measurement (optional)",
            required=False,
        ),
    }

    metadata = ToolMetadata(
        category="observability",
        return_type="dict",
        examples=[
            "Track API request counts",
            "Monitor memory usage",
            "Record response time histograms",
            "Collect custom business metrics",
        ],
        version="1.0.0",
        tags=["metrics", "telemetry", "monitoring", "observability", "prometheus"],
        requires_auth=False,
    )

    async def run(
        self,
        metric_name: str,
        metric_type: str,
        value: float,
        tags: dict[str, str] | None = None,
        timestamp: str | None = None,
        unit: str | None = None,
    ) -> dict[str, Any]:
        """
        Collect and report a metric.

        Args:
            metric_name: Name of the metric
            metric_type: Type (counter, gauge, histogram, summary)
            value: Metric value
            tags: Dimensional tags/labels
            timestamp: Metric timestamp (ISO 8601)
            unit: Unit of measurement

        Returns:
            Dictionary containing:
            - success (bool): Whether metric was recorded
            - metric_id (str): Unique metric identifier
            - metric_name (str): Name of the metric
            - metric_type (str): Type of metric
            - value (float): Recorded value
            - tags (dict): Applied tags
            - timestamp (str): Recording timestamp

        Raises:
            ValueError: If metric_name is invalid or value is negative for counter
        """
        logger.info(
            "metrics_collection_execution",
            metric_name=metric_name,
            metric_type=metric_type,
            value=value,
            has_tags=bool(tags),
        )

        tags = tags or {}

        # Validate metric name
        if not metric_name or not metric_name.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                f"Invalid metric name '{metric_name}'. Use alphanumeric characters, underscores, and hyphens."
            )

        # Validate counter values (must be non-negative and typically increments)
        if metric_type == "counter" and value < 0:
            raise ValueError(f"Counter values must be non-negative, got {value}")

        # Generate timestamp if not provided
        if timestamp is None:
            timestamp = "2025-11-01T00:00:00Z"  # Mock timestamp

        # Mock implementation for testing/demo
        # Production version would integrate with actual metrics backends
        try:
            # Generate unique metric ID
            metric_id = f"{metric_name}_{hash(str(tags))}_{timestamp}"

            result = {
                "success": True,
                "metric_id": metric_id[:32],  # Truncate for readability
                "metric_name": metric_name,
                "metric_type": metric_type,
                "value": value,
                "tags": tags,
                "timestamp": timestamp,
            }

            if unit:
                result["unit"] = unit

            # Log different message based on metric type
            if metric_type == "counter":
                logger.info(
                    "metrics_counter_incremented",
                    metric_name=metric_name,
                    value=value,
                    tags=tags,
                )
            elif metric_type == "gauge":
                logger.info(
                    "metrics_gauge_recorded",
                    metric_name=metric_name,
                    value=value,
                    tags=tags,
                )
            elif metric_type in ["histogram", "summary"]:
                logger.info(
                    "metrics_distribution_recorded",
                    metric_name=metric_name,
                    metric_type=metric_type,
                    value=value,
                    tags=tags,
                )

            logger.info(
                "metrics_collection_success",
                metric_id=result["metric_id"],
                metric_name=metric_name,
            )

            return result

        except Exception as e:
            logger.error(
                "metrics_collection_error",
                metric_name=metric_name,
                error=str(e),
            )
            raise
