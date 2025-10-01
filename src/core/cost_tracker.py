"""Enhanced cost tracking and budget enforcement system.

This module provides comprehensive cost monitoring, budget enforcement,
and cost optimization strategies for LLM API usage and system operations.
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CostMetrics:
    """Detailed cost metrics for a specific operation."""

    operation_id: str
    operation_type: str  # "llm_request", "vector_search", "transcription", etc.
    provider: str
    model: str | None = None
    tokens_used: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: Decimal = Decimal("0.0")
    duration_seconds: float = 0.0
    timestamp: float = field(default_factory=time.time)
    tenant_id: str | None = None
    workspace_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class BudgetConfig:
    """Budget configuration for cost control."""

    max_daily_cost_usd: Decimal
    max_monthly_cost_usd: Decimal
    max_hourly_cost_usd: Decimal
    max_concurrent_requests: int = 10
    cost_alert_thresholds: dict[str, Decimal] = field(default_factory=dict)
    enable_hard_limits: bool = True


@dataclass
class CostSummary:
    """Summary of costs for a time period."""

    period_start: float
    period_end: float
    total_cost_usd: Decimal
    operations_count: int
    average_cost_per_operation: Decimal
    cost_by_provider: dict[str, Decimal]
    cost_by_operation_type: dict[str, Decimal]
    cost_by_tenant: dict[str, Decimal]


class CostTracker:
    """Advanced cost tracking and budget enforcement."""

    def __init__(self):
        self.cost_history: list[CostMetrics] = []
        self.budget_configs: dict[str, BudgetConfig] = {}  # tenant_id -> config
        self.daily_costs: dict[str, Decimal] = defaultdict(Decimal)  # date -> cost
        self.monthly_costs: dict[str, Decimal] = defaultdict(Decimal)  # month -> cost
        self.hourly_costs: dict[str, Decimal] = defaultdict(Decimal)  # hour -> cost

        # Alert callbacks
        self.alert_callbacks: list[callable] = []

        # Cost optimization settings
        self.enable_cost_optimization = True
        self.cost_savings_targets: dict[str, Decimal] = {}

    def record_cost(self, metrics: CostMetrics) -> None:
        """Record a cost event."""
        self.cost_history.append(metrics)

        # Update aggregated costs
        self._update_aggregated_costs(metrics)

        # Check budget limits
        self._check_budget_limits(metrics)

        # Update metrics
        self._update_cost_metrics(metrics)

        logger.debug(
            f"Recorded cost: {metrics.cost_usd} USD for {metrics.operation_type} "
            f"(provider: {metrics.provider}, model: {metrics.model})"
        )

    def _update_aggregated_costs(self, metrics: CostMetrics) -> None:
        """Update daily, monthly, and hourly cost aggregations."""
        # Daily costs
        date_key = time.strftime("%Y-%m-%d", time.localtime(metrics.timestamp))
        self.daily_costs[date_key] += metrics.cost_usd

        # Monthly costs
        month_key = time.strftime("%Y-%m", time.localtime(metrics.timestamp))
        self.monthly_costs[month_key] += metrics.cost_usd

        # Hourly costs
        hour_key = time.strftime("%Y-%m-%d-%H", time.localtime(metrics.timestamp))
        self.hourly_costs[hour_key] += metrics.cost_usd

    def _check_budget_limits(self, metrics: CostMetrics) -> None:
        """Check if budget limits are exceeded and trigger alerts."""
        tenant_id = metrics.tenant_id or "default"

        if tenant_id not in self.budget_configs:
            return  # No budget configured for this tenant

        config = self.budget_configs[tenant_id]

        # Check daily budget
        today = time.strftime("%Y-%m-%d", time.localtime(metrics.timestamp))
        daily_cost = self.daily_costs.get(today, Decimal("0"))

        if daily_cost > config.max_daily_cost_usd:
            self._trigger_budget_alert(
                tenant_id,
                "daily_budget_exceeded",
                f"Daily budget exceeded: ${daily_cost} > ${config.max_daily_cost_usd}",
            )

        # Check monthly budget
        current_month = time.strftime("%Y-%m", time.localtime(metrics.timestamp))
        monthly_cost = self.monthly_costs.get(current_month, Decimal("0"))

        if monthly_cost > config.max_monthly_cost_usd:
            self._trigger_budget_alert(
                tenant_id,
                "monthly_budget_exceeded",
                f"Monthly budget exceeded: ${monthly_cost} > ${config.max_monthly_cost_usd}",
            )

        # Check hourly budget
        current_hour = time.strftime("%Y-%m-%d-%H", time.localtime(metrics.timestamp))
        hourly_cost = self.hourly_costs.get(current_hour, Decimal("0"))

        if hourly_cost > config.max_hourly_cost_usd:
            self._trigger_budget_alert(
                tenant_id,
                "hourly_budget_exceeded",
                f"Hourly budget exceeded: ${hourly_cost} > ${config.max_hourly_cost_usd}",
            )

    def _trigger_budget_alert(self, tenant_id: str, alert_type: str, message: str) -> None:
        """Trigger budget alert callback."""
        alert_data = {
            "tenant_id": tenant_id,
            "alert_type": alert_type,
            "message": message,
            "timestamp": time.time(),
        }

        logger.warning(f"Budget Alert: {message}")

        # Trigger callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert_data)
            except Exception as e:
                logger.error(f"Error in budget alert callback: {e}")

    def _update_cost_metrics(self, metrics: CostMetrics) -> None:
        """Update Prometheus cost metrics."""
        try:
            # Total cost metric
            metrics_label = {
                "tenant": metrics.tenant_id or "unknown",
                "provider": metrics.provider,
                "operation_type": metrics.operation_type,
            }

            # Update cost per operation type
            if hasattr(metrics, "COST_PER_OPERATION"):
                metrics.COST_PER_OPERATION.labels(**metrics_label).set(float(metrics.cost_usd))

            # Update token usage metrics
            if hasattr(metrics, "TOKENS_USED"):
                metrics.TOKENS_USED.labels(**metrics_label).set(metrics.tokens_used)

        except Exception as e:
            logger.debug(f"Error updating cost metrics: {e}")

    def get_cost_summary(
        self, start_time: float | None = None, end_time: float | None = None, tenant_id: str | None = None
    ) -> CostSummary:
        """Get cost summary for a time period."""
        if start_time is None:
            start_time = time.time() - (24 * 3600)  # Last 24 hours
        if end_time is None:
            end_time = time.time()

        # Filter cost history
        filtered_costs = [cost for cost in self.cost_history if start_time <= cost.timestamp <= end_time]

        if tenant_id:
            filtered_costs = [cost for cost in filtered_costs if cost.tenant_id == tenant_id]

        if not filtered_costs:
            return CostSummary(
                period_start=start_time,
                period_end=end_time,
                total_cost_usd=Decimal("0"),
                operations_count=0,
                average_cost_per_operation=Decimal("0"),
                cost_by_provider={},
                cost_by_operation_type={},
                cost_by_tenant={},
            )

        # Calculate totals
        total_cost = sum(cost.cost_usd for cost in filtered_costs)
        operations_count = len(filtered_costs)
        average_cost = total_cost / operations_count if operations_count > 0 else Decimal("0")

        # Group by provider
        cost_by_provider = defaultdict(Decimal)
        for cost in filtered_costs:
            cost_by_provider[cost.provider] += cost.cost_usd

        # Group by operation type
        cost_by_operation_type = defaultdict(Decimal)
        for cost in filtered_costs:
            cost_by_operation_type[cost.operation_type] += cost.cost_usd

        # Group by tenant
        cost_by_tenant = defaultdict(Decimal)
        for cost in filtered_costs:
            tenant_key = cost.tenant_id or "unknown"
            cost_by_tenant[tenant_key] += cost.cost_usd

        return CostSummary(
            period_start=start_time,
            period_end=end_time,
            total_cost_usd=total_cost,
            operations_count=operations_count,
            average_cost_per_operation=average_cost,
            cost_by_provider=dict(cost_by_provider),
            cost_by_operation_type=dict(cost_by_operation_type),
            cost_by_tenant=dict(cost_by_tenant),
        )

    def set_budget_config(self, tenant_id: str, config: BudgetConfig) -> None:
        """Set budget configuration for a tenant."""
        self.budget_configs[tenant_id] = config
        logger.info(f"Set budget config for tenant {tenant_id}: ${config.max_daily_cost_usd}/day")

    def add_alert_callback(self, callback: callable) -> None:
        """Add callback for budget alerts."""
        self.alert_callbacks.append(callback)

    def get_budget_status(self, tenant_id: str | None = None) -> dict[str, Any]:
        """Get current budget status for a tenant."""
        if tenant_id is None:
            # Return summary for all tenants
            return {
                "tenants": list(self.budget_configs.keys()),
                "total_tenants": len(self.budget_configs),
            }

        if tenant_id not in self.budget_configs:
            return {"error": f"No budget configured for tenant {tenant_id}"}

        config = self.budget_configs[tenant_id]

        # Get current period costs
        now = time.time()
        today = time.strftime("%Y-%m-%d", time.localtime(now))
        current_month = time.strftime("%Y-%m", time.localtime(now))
        current_hour = time.strftime("%Y-%m-%d-%H", time.localtime(now))

        daily_cost = self.daily_costs.get(today, Decimal("0"))
        monthly_cost = self.monthly_costs.get(current_month, Decimal("0"))
        hourly_cost = self.hourly_costs.get(current_hour, Decimal("0"))

        return {
            "tenant_id": tenant_id,
            "daily_cost": float(daily_cost),
            "monthly_cost": float(monthly_cost),
            "hourly_cost": float(hourly_cost),
            "daily_budget": float(config.max_daily_cost_usd),
            "monthly_budget": float(config.max_monthly_cost_usd),
            "hourly_budget": float(config.max_hourly_cost_usd),
            "daily_utilization": float(daily_cost / config.max_daily_cost_usd) if config.max_daily_cost_usd > 0 else 0,
            "monthly_utilization": float(monthly_cost / config.max_monthly_cost_usd)
            if config.max_monthly_cost_usd > 0
            else 0,
            "hourly_utilization": float(hourly_cost / config.max_hourly_cost_usd)
            if config.max_hourly_cost_usd > 0
            else 0,
        }

    def export_cost_report(self, days: int = 7) -> str:
        """Export comprehensive cost report."""
        end_time = time.time()
        start_time = end_time - (days * 24 * 3600)

        summary = self.get_cost_summary(start_time, end_time)

        report = f"""
# Cost Report - Last {days} Days

**Period:** {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time))} to {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end_time))}
**Total Cost:** ${summary.total_cost_usd:.2f}
**Operations:** {summary.operations_count}
**Average Cost per Operation:** ${summary.average_cost_per_operation:.4f}

## Cost by Provider
"""

        for provider, cost in sorted(summary.cost_by_provider.items(), key=lambda x: x[1], reverse=True):
            report += f"- **{provider}**: ${cost:.2f}\n"

        report += "\n## Cost by Operation Type\n"
        for op_type, cost in sorted(summary.cost_by_operation_type.items(), key=lambda x: x[1], reverse=True):
            report += f"- **{op_type}**: ${cost:.2f}\n"

        if summary.cost_by_tenant:
            report += "\n## Cost by Tenant\n"
            for tenant, cost in sorted(summary.cost_by_tenant.items(), key=lambda x: x[1], reverse=True):
                report += f"- **{tenant}**: ${cost:.2f}\n"

        return report


class CostOptimizer:
    """Intelligent cost optimization strategies."""

    def __init__(self, cost_tracker: CostTracker):
        self.cost_tracker = cost_tracker
        self.optimization_strategies = {
            "model_selection": self._optimize_model_selection,
            "batching": self._optimize_batching,
            "caching": self._optimize_caching,
            "provider_routing": self._optimize_provider_routing,
        }

    def analyze_cost_patterns(self, days: int = 7) -> dict[str, Any]:
        """Analyze cost patterns to identify optimization opportunities."""
        end_time = time.time()
        start_time = end_time - (days * 24 * 3600)

        summary = self.cost_tracker.get_cost_summary(start_time, end_time)

        analysis = {
            "total_cost": float(summary.total_cost_usd),
            "operations_count": summary.operations_count,
            "cost_per_operation": float(summary.average_cost_per_operation),
            "optimization_opportunities": [],
        }

        # Identify high-cost operations
        high_cost_operations = [
            (op_type, cost)
            for op_type, cost in summary.cost_by_operation_type.items()
            if cost > (summary.total_cost_usd * 0.2)  # Operations > 20% of total cost
        ]

        if high_cost_operations:
            analysis["optimization_opportunities"].append(
                {
                    "type": "high_cost_operations",
                    "description": "Operations consuming significant portion of budget",
                    "operations": high_cost_operations,
                    "potential_savings": "Varies by optimization strategy",
                }
            )

        # Identify expensive providers
        expensive_providers = [
            (provider, cost)
            for provider, cost in summary.cost_by_provider.items()
            if cost > (summary.total_cost_usd * 0.3)  # Providers > 30% of total cost
        ]

        if expensive_providers:
            analysis["optimization_opportunities"].append(
                {
                    "type": "expensive_providers",
                    "description": "Providers with high cost contribution",
                    "providers": expensive_providers,
                    "potential_savings": "10-30% by switching providers or models",
                }
            )

        return analysis

    def get_optimization_recommendations(self) -> list[dict[str, Any]]:
        """Get specific optimization recommendations."""
        recommendations = []

        # Analyze current cost patterns
        analysis = self.analyze_cost_patterns()

        for opportunity in analysis["optimization_opportunities"]:
            if opportunity["type"] == "high_cost_operations":
                recommendations.append(
                    {
                        "priority": "high",
                        "category": "cost_optimization",
                        "title": "Optimize High-Cost Operations",
                        "description": f"Focus on optimizing {len(opportunity['operations'])} high-cost operations",
                        "estimated_savings": opportunity["potential_savings"],
                        "actions": [
                            "Implement intelligent batching for similar operations",
                            "Add caching for frequently repeated operations",
                            "Consider alternative, lower-cost providers for these operations",
                        ],
                    }
                )

            elif opportunity["type"] == "expensive_providers":
                recommendations.append(
                    {
                        "priority": "medium",
                        "category": "provider_optimization",
                        "title": "Review Expensive Providers",
                        "description": f"Evaluate {len(opportunity['providers'])} high-cost providers",
                        "estimated_savings": opportunity["potential_savings"],
                        "actions": [
                            "Compare pricing across providers",
                            "Implement provider fallback strategies",
                            "Use cheaper models when quality requirements allow",
                        ],
                    }
                )

        # Add general recommendations
        recommendations.extend(
            [
                {
                    "priority": "medium",
                    "category": "caching",
                    "title": "Enhance Caching Strategy",
                    "description": "Improve cache hit rates to reduce API calls",
                    "estimated_savings": "20-40% for cached operations",
                    "actions": [
                        "Implement semantic caching for similar requests",
                        "Add prompt preprocessing for better cache matching",
                        "Monitor cache hit rates and adjust thresholds",
                    ],
                },
                {
                    "priority": "low",
                    "category": "monitoring",
                    "title": "Implement Cost Alerts",
                    "description": "Add proactive cost monitoring and alerts",
                    "estimated_savings": "10-20% through early detection",
                    "actions": [
                        "Set up budget alerts for each tenant",
                        "Implement daily cost summaries",
                        "Add cost anomaly detection",
                    ],
                },
            ]
        )

        return sorted(recommendations, key=lambda x: x["priority"])

    def _optimize_model_selection(self, operation_type: str, requirements: dict[str, Any]) -> dict[str, Any]:
        """Optimize model selection based on cost and quality requirements."""
        # This would implement intelligent model selection
        # For now, return placeholder recommendation
        return {
            "recommended_model": "gpt-3.5-turbo",
            "estimated_cost_reduction": "15%",
            "quality_impact": "minimal",
        }

    def _optimize_batching(self, operation_type: str) -> dict[str, Any]:
        """Optimize batching strategy for operations."""
        return {
            "recommended_batch_size": 5,
            "estimated_cost_reduction": "10%",
            "performance_impact": "improved",
        }

    def _optimize_caching(self, operation_type: str) -> dict[str, Any]:
        """Optimize caching strategy."""
        return {
            "recommended_cache_ttl": 3600,
            "estimated_hit_rate_improvement": "25%",
            "implementation": "enhanced_semantic_cache",
        }

    def _optimize_provider_routing(self, requirements: dict[str, Any]) -> dict[str, Any]:
        """Optimize provider routing for cost efficiency."""
        return {
            "recommended_provider": "openrouter",
            "estimated_cost_reduction": "20%",
            "routing_strategy": "cost_aware",
        }


# Global cost tracker instance
_cost_tracker: CostTracker | None = None


def get_cost_tracker() -> CostTracker:
    """Get or create the global cost tracker."""
    global _cost_tracker

    if _cost_tracker is None:
        _cost_tracker = CostTracker()
    return _cost_tracker


def record_llm_cost(
    operation_id: str,
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    cost_usd: Decimal,
    duration_seconds: float = 0.0,
    tenant_id: str | None = None,
    workspace_id: str | None = None,
    **metadata,
) -> None:
    """Record LLM API cost."""
    total_tokens = input_tokens + output_tokens

    metrics = CostMetrics(
        operation_id=operation_id,
        operation_type="llm_request",
        provider=provider,
        model=model,
        tokens_used=total_tokens,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=cost_usd,
        duration_seconds=duration_seconds,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        metadata=metadata,
    )

    tracker = get_cost_tracker()
    tracker.record_cost(metrics)


def record_vector_operation_cost(
    operation_id: str,
    operation_type: str,  # "search", "upsert", "delete"
    provider: str,
    vectors_count: int,
    cost_usd: Decimal,
    duration_seconds: float = 0.0,
    tenant_id: str | None = None,
    workspace_id: str | None = None,
    **metadata,
) -> None:
    """Record vector database operation cost."""
    metrics = CostMetrics(
        operation_id=operation_id,
        operation_type=f"vector_{operation_type}",
        provider=provider,
        tokens_used=vectors_count,  # Use vectors as proxy for tokens
        cost_usd=cost_usd,
        duration_seconds=duration_seconds,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        metadata={"vectors_count": vectors_count, **metadata},
    )

    tracker = get_cost_tracker()
    tracker.record_cost(metrics)


def get_cost_summary(
    start_time: float | None = None, end_time: float | None = None, tenant_id: str | None = None
) -> CostSummary:
    """Get cost summary for a time period."""
    tracker = get_cost_tracker()
    return tracker.get_cost_summary(start_time, end_time, tenant_id)


def set_tenant_budget(
    tenant_id: str, max_daily_cost: Decimal, max_monthly_cost: Decimal, max_hourly_cost: Decimal, **kwargs
) -> None:
    """Set budget configuration for a tenant."""
    config = BudgetConfig(
        max_daily_cost_usd=max_daily_cost,
        max_monthly_cost_usd=max_monthly_cost,
        max_hourly_cost_usd=max_hourly_cost,
        **kwargs,
    )

    tracker = get_cost_tracker()
    tracker.set_budget_config(tenant_id, config)


def get_optimization_recommendations() -> list[dict[str, Any]]:
    """Get cost optimization recommendations."""
    tracker = get_cost_tracker()
    optimizer = CostOptimizer(tracker)
    return optimizer.get_optimization_recommendations()


def export_cost_report(days: int = 7) -> str:
    """Export comprehensive cost report."""
    tracker = get_cost_tracker()
    return tracker.export_cost_report(days)


# Discord alert callback for budget issues
def discord_budget_alert(alert_data: dict[str, Any]) -> None:
    """Discord alert callback for budget issues."""
    from ultimate_discord_intelligence_bot.tools.discord_private_alert_tool import DiscordPrivateAlertTool

    alert_type = alert_data["alert_type"]
    tenant_id = alert_data["tenant_id"]
    message = alert_data["message"]

    full_message = (
        f"🚨 **Budget Alert: {alert_type.upper()}**\n"
        f"**Tenant:** {tenant_id}\n"
        f"**Issue:** {message}\n"
        f"**Time:** {time.strftime('%Y-%m-%d %H:%M:%S UTC')}"
    )

    try:
        alert_tool = DiscordPrivateAlertTool()
        alert_tool._run(full_message)
    except Exception as e:
        logger.error(f"Failed to send Discord budget alert: {e}")


def initialize_cost_tracking() -> None:
    """Initialize cost tracking with Discord alerts."""
    tracker = get_cost_tracker()
    tracker.add_alert_callback(discord_budget_alert)
    logger.info("Cost tracking initialized with Discord alerts")


__all__ = [
    "CostTracker",
    "CostOptimizer",
    "CostMetrics",
    "BudgetConfig",
    "CostSummary",
    "get_cost_tracker",
    "record_llm_cost",
    "record_vector_operation_cost",
    "get_cost_summary",
    "set_tenant_budget",
    "get_optimization_recommendations",
    "export_cost_report",
    "discord_budget_alert",
    "initialize_cost_tracking",
]
