"""Unified Cost Tracking Service - Budget management across all routing systems

This service provides unified cost tracking, budget management, and spending
analytics across all routing backends to ensure cost optimization and
budget compliance.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from ultimate_discord_intelligence_bot.step_result import StepResult

logger = logging.getLogger(__name__)


@dataclass
class BudgetConfig:
    """Budget configuration for cost tracking"""

    tenant_id: str
    workspace_id: str
    daily_limit: Decimal
    monthly_limit: Decimal
    per_request_limit: Decimal
    alert_threshold: float = 0.8  # Alert when 80% of budget used
    reset_period: str = "daily"  # daily, monthly
    currency: str = "USD"


@dataclass
class CostRecord:
    """Record of a cost transaction"""

    transaction_id: str
    tenant_id: str
    workspace_id: str
    model: str
    provider: str
    cost: Decimal
    tokens_used: Optional[int] = None
    request_type: str = "routing"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BudgetStatus:
    """Current budget status"""

    tenant_id: str
    workspace_id: str
    daily_spent: Decimal
    monthly_spent: Decimal
    daily_remaining: Decimal
    monthly_remaining: Decimal
    daily_limit: Decimal
    monthly_limit: Decimal
    alert_level: str  # green, yellow, red
    last_reset: datetime
    next_reset: datetime


class UnifiedCostTracker:
    """Unified cost tracking and budget management service"""

    def __init__(self):
        self._budgets: Dict[str, BudgetConfig] = {}
        self._cost_records: List[CostRecord] = []
        self._budget_cache: Dict[str, BudgetStatus] = {}
        self._cache_ttl = 300  # 5 minutes
        self._last_cache_update: Dict[str, datetime] = {}

    def set_budget(
        self,
        tenant_id: str,
        workspace_id: str,
        daily_limit: float,
        monthly_limit: float,
        per_request_limit: float = 1.0,
        alert_threshold: float = 0.8,
        reset_period: str = "daily",
    ) -> StepResult:
        """Set budget limits for a tenant/workspace"""
        try:
            key = f"{tenant_id}:{workspace_id}"

            budget_config = BudgetConfig(
                tenant_id=tenant_id,
                workspace_id=workspace_id,
                daily_limit=Decimal(str(daily_limit)),
                monthly_limit=Decimal(str(monthly_limit)),
                per_request_limit=Decimal(str(per_request_limit)),
                alert_threshold=alert_threshold,
                reset_period=reset_period,
            )

            self._budgets[key] = budget_config

            # Clear cache for this budget
            if key in self._budget_cache:
                del self._budget_cache[key]
            if key in self._last_cache_update:
                del self._last_cache_update[key]

            logger.info(
                f"Budget set for {key}: daily=${daily_limit}, monthly=${monthly_limit}"
            )
            return StepResult.ok(data={"budget_set": True, "key": key})

        except Exception as e:
            logger.error(f"Failed to set budget: {e}")
            return StepResult.fail(f"Budget configuration failed: {str(e)}")

    def get_budget_status(self, tenant_id: str, workspace_id: str) -> StepResult:
        """Get current budget status for tenant/workspace"""
        try:
            key = f"{tenant_id}:{workspace_id}"

            # Check cache first
            if self._is_cache_valid(key):
                return StepResult.ok(data=self._budget_cache[key])

            # Calculate current status
            budget_config = self._budgets.get(key)
            if not budget_config:
                return StepResult.fail(f"No budget configured for {key}")

            # Get spending for current period
            daily_spent, monthly_spent = self._calculate_spending(
                tenant_id, workspace_id
            )

            # Calculate remaining budget
            daily_remaining = budget_config.daily_limit - daily_spent
            monthly_remaining = budget_config.monthly_limit - monthly_spent

            # Determine alert level
            daily_usage_ratio = daily_spent / budget_config.daily_limit
            monthly_usage_ratio = monthly_spent / budget_config.monthly_limit

            if daily_usage_ratio >= 1.0 or monthly_usage_ratio >= 1.0:
                alert_level = "red"
            elif (
                daily_usage_ratio >= budget_config.alert_threshold
                or monthly_usage_ratio >= budget_config.alert_threshold
            ):
                alert_level = "yellow"
            else:
                alert_level = "green"

            # Calculate reset times
            now = datetime.now(timezone.utc)
            if budget_config.reset_period == "daily":
                last_reset = now.replace(hour=0, minute=0, second=0, microsecond=0)
                next_reset = last_reset + timedelta(days=1)
            else:  # monthly
                last_reset = now.replace(
                    day=1, hour=0, minute=0, second=0, microsecond=0
                )
                if now.month == 12:
                    next_reset = now.replace(
                        year=now.year + 1,
                        month=1,
                        day=1,
                        hour=0,
                        minute=0,
                        second=0,
                        microsecond=0,
                    )
                else:
                    next_reset = now.replace(
                        month=now.month + 1,
                        day=1,
                        hour=0,
                        minute=0,
                        second=0,
                        microsecond=0,
                    )

            budget_status = BudgetStatus(
                tenant_id=tenant_id,
                workspace_id=workspace_id,
                daily_spent=daily_spent,
                monthly_spent=monthly_spent,
                daily_remaining=daily_remaining,
                monthly_remaining=monthly_remaining,
                daily_limit=budget_config.daily_limit,
                monthly_limit=budget_config.monthly_limit,
                alert_level=alert_level,
                last_reset=last_reset,
                next_reset=next_reset,
            )

            # Update cache
            self._budget_cache[key] = budget_status
            self._last_cache_update[key] = now

            return StepResult.ok(data=budget_status)

        except Exception as e:
            logger.error(f"Failed to get budget status: {e}")
            return StepResult.fail(f"Budget status retrieval failed: {str(e)}")

    def record_cost(
        self,
        tenant_id: str,
        workspace_id: str,
        model: str,
        provider: str,
        cost: float,
        tokens_used: Optional[int] = None,
        request_type: str = "routing",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> StepResult:
        """Record a cost transaction"""
        try:
            # Validate cost
            if cost < 0:
                return StepResult.fail("Cost cannot be negative")

            # Check budget limits
            budget_check = self.check_budget_compliance(tenant_id, workspace_id, cost)

            if not budget_check.success:
                return budget_check

            # Generate transaction ID
            transaction_id = (
                f"{tenant_id}:{workspace_id}:{int(datetime.now().timestamp() * 1000)}"
            )

            # Create cost record
            cost_record = CostRecord(
                transaction_id=transaction_id,
                tenant_id=tenant_id,
                workspace_id=workspace_id,
                model=model,
                provider=provider,
                cost=Decimal(str(cost)),
                tokens_used=tokens_used,
                request_type=request_type,
                metadata=metadata or {},
            )

            # Store record
            self._cost_records.append(cost_record)

            # Clear cache for this budget
            key = f"{tenant_id}:{workspace_id}"
            if key in self._budget_cache:
                del self._budget_cache[key]
            if key in self._last_cache_update:
                del self._last_cache_update[key]

            logger.debug(f"Recorded cost: {cost_record}")
            return StepResult.ok(
                data={"transaction_id": transaction_id, "cost_recorded": True}
            )

        except Exception as e:
            logger.error(f"Failed to record cost: {e}")
            return StepResult.fail(f"Cost recording failed: {str(e)}")

    def check_budget_compliance(
        self, tenant_id: str, workspace_id: str, requested_cost: float
    ) -> StepResult:
        """Check if a cost request complies with budget limits"""
        try:
            key = f"{tenant_id}:{workspace_id}"
            budget_config = self._budgets.get(key)

            if not budget_config:
                # No budget set, allow request
                return StepResult.ok(
                    data={"compliant": True, "reason": "no_budget_set"}
                )

            # Check per-request limit
            if Decimal(str(requested_cost)) > budget_config.per_request_limit:
                return StepResult.fail(
                    f"Request cost ${requested_cost:.4f} exceeds per-request limit ${budget_config.per_request_limit}"
                )

            # Get current spending
            daily_spent, monthly_spent = self._calculate_spending(
                tenant_id, workspace_id
            )

            # Check daily limit
            if daily_spent + Decimal(str(requested_cost)) > budget_config.daily_limit:
                return StepResult.fail(
                    f"Request would exceed daily budget limit. "
                    f"Current: ${daily_spent:.4f}, Request: ${requested_cost:.4f}, "
                    f"Limit: ${budget_config.daily_limit}"
                )

            # Check monthly limit
            if (
                monthly_spent + Decimal(str(requested_cost))
                > budget_config.monthly_limit
            ):
                return StepResult.fail(
                    f"Request would exceed monthly budget limit. "
                    f"Current: ${monthly_spent:.4f}, Request: ${requested_cost:.4f}, "
                    f"Limit: ${budget_config.monthly_limit}"
                )

            return StepResult.ok(
                data={
                    "compliant": True,
                    "reason": "within_budget",
                    "daily_remaining": float(budget_config.daily_limit - daily_spent),
                    "monthly_remaining": float(
                        budget_config.monthly_limit - monthly_spent
                    ),
                }
            )

        except Exception as e:
            logger.error(f"Failed to check budget compliance: {e}")
            return StepResult.fail(f"Budget compliance check failed: {str(e)}")

    def get_cost_analytics(
        self,
        tenant_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        days: int = 30,
    ) -> StepResult:
        """Get cost analytics and spending patterns"""
        try:
            # Filter records by tenant/workspace and time period
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

            filtered_records = []
            for record in self._cost_records:
                if record.timestamp < cutoff_date:
                    continue

                if tenant_id and record.tenant_id != tenant_id:
                    continue

                if workspace_id and record.workspace_id != workspace_id:
                    continue

                filtered_records.append(record)

            if not filtered_records:
                return StepResult.ok(
                    data={"total_cost": 0.0, "total_requests": 0, "analytics": {}}
                )

            # Calculate analytics
            total_cost = sum(record.cost for record in filtered_records)
            total_requests = len(filtered_records)

            # Group by provider
            provider_costs = {}
            for record in filtered_records:
                provider = record.provider
                if provider not in provider_costs:
                    provider_costs[provider] = {"cost": Decimal("0"), "requests": 0}
                provider_costs[provider]["cost"] += record.cost
                provider_costs[provider]["requests"] += 1

            # Group by model
            model_costs = {}
            for record in filtered_records:
                model = record.model
                if model not in model_costs:
                    model_costs[model] = {"cost": Decimal("0"), "requests": 0}
                model_costs[model]["cost"] += record.cost
                model_costs[model]["requests"] += 1

            # Daily spending pattern
            daily_spending = {}
            for record in filtered_records:
                day = record.timestamp.date()
                if day not in daily_spending:
                    daily_spending[day] = Decimal("0")
                daily_spending[day] += record.cost

            # Convert to float for JSON serialization
            analytics = {
                "total_cost": float(total_cost),
                "total_requests": total_requests,
                "avg_cost_per_request": float(total_cost / total_requests)
                if total_requests > 0
                else 0.0,
                "provider_breakdown": {
                    provider: {
                        "cost": float(data["cost"]),
                        "requests": data["requests"],
                        "percentage": float(data["cost"] / total_cost * 100)
                        if total_cost > 0
                        else 0.0,
                    }
                    for provider, data in provider_costs.items()
                },
                "model_breakdown": {
                    model: {
                        "cost": float(data["cost"]),
                        "requests": data["requests"],
                        "percentage": float(data["cost"] / total_cost * 100)
                        if total_cost > 0
                        else 0.0,
                    }
                    for model, data in model_costs.items()
                },
                "daily_spending": {
                    str(day): float(cost) for day, cost in daily_spending.items()
                },
                "period_days": days,
                "records_analyzed": len(filtered_records),
            }

            return StepResult.ok(data=analytics)

        except Exception as e:
            logger.error(f"Failed to get cost analytics: {e}")
            return StepResult.fail(f"Cost analytics retrieval failed: {str(e)}")

    def _calculate_spending(
        self, tenant_id: str, workspace_id: str
    ) -> tuple[Decimal, Decimal]:
        """Calculate daily and monthly spending for tenant/workspace"""
        try:
            now = datetime.now(timezone.utc)

            # Daily period
            daily_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

            # Monthly period
            monthly_start = now.replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )

            daily_spent = Decimal("0")
            monthly_spent = Decimal("0")

            for record in self._cost_records:
                if (
                    record.tenant_id == tenant_id
                    and record.workspace_id == workspace_id
                ):
                    if record.timestamp >= daily_start:
                        daily_spent += record.cost

                    if record.timestamp >= monthly_start:
                        monthly_spent += record.cost

            return daily_spent, monthly_spent

        except Exception as e:
            logger.error(f"Failed to calculate spending: {e}")
            return Decimal("0"), Decimal("0")

    def _is_cache_valid(self, key: str) -> bool:
        """Check if budget cache is still valid"""
        if key not in self._budget_cache or key not in self._last_cache_update:
            return False

        cache_age = datetime.now(timezone.utc) - self._last_cache_update[key]
        return cache_age.total_seconds() < self._cache_ttl

    def get_all_budgets(self) -> Dict[str, BudgetConfig]:
        """Get all configured budgets"""
        return self._budgets.copy()

    def reset_budget(
        self, tenant_id: str, workspace_id: str, reset_type: str = "daily"
    ) -> StepResult:
        """Reset budget counters (for testing or manual reset)"""
        try:
            key = f"{tenant_id}:{workspace_id}"

            if key not in self._budgets:
                return StepResult.fail(f"No budget configured for {key}")

            # Clear cache
            if key in self._budget_cache:
                del self._budget_cache[key]
            if key in self._last_cache_update:
                del self._last_cache_update[key]

            logger.info(f"Budget cache reset for {key} ({reset_type})")
            return StepResult.ok(data={"reset": True, "type": reset_type})

        except Exception as e:
            logger.error(f"Failed to reset budget: {e}")
            return StepResult.fail(f"Budget reset failed: {str(e)}")
