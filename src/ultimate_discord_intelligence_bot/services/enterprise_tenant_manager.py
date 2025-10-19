"""Enterprise tenant management with advanced isolation, resource quotas, and billing."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from ultimate_discord_intelligence_bot.settings import (
    ENABLE_ENTERPRISE_TENANT_MANAGEMENT,
)
from ultimate_discord_intelligence_bot.step_result import StepResult

log = logging.getLogger(__name__)


class TenantTier(Enum):
    """Tenant subscription tiers."""

    FREE = "free"
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"


class ResourceType(Enum):
    """Types of resources that can be allocated."""

    CPU_UNITS = "cpu_units"
    MEMORY_MB = "memory_mb"
    GPU_HOURS = "gpu_hours"
    STORAGE_GB = "storage_gb"
    API_CALLS = "api_calls"
    AGENT_EXECUTIONS = "agent_executions"
    STREAM_HOURS = "stream_hours"


@dataclass
class ResourceQuota:
    """Resource quota configuration for a tenant."""

    resource_type: ResourceType
    limit: float
    current_usage: float = 0.0
    reset_period: str = "monthly"  # daily, weekly, monthly, yearly
    last_reset: float = field(default_factory=time.time)

    def is_exceeded(self) -> bool:
        """Check if quota is exceeded."""
        return self.current_usage >= self.limit

    def remaining(self) -> float:
        """Get remaining quota."""
        return max(0.0, self.limit - self.current_usage)

    def usage_percentage(self) -> float:
        """Get usage as percentage of limit."""
        return (self.current_usage / self.limit * 100) if self.limit > 0 else 0.0


@dataclass
class BillingConfig:
    """Billing configuration for a tenant."""

    tier: TenantTier
    monthly_fee: float = 0.0
    overage_rate: Dict[ResourceType, float] = field(default_factory=dict)
    billing_email: str = ""
    payment_method: str = ""
    auto_renew: bool = True
    next_billing_date: float = field(default_factory=time.time)

    def calculate_overage_cost(
        self,
        usage: Dict[ResourceType, float],
        quotas: Dict[ResourceType, ResourceQuota],
    ) -> float:
        """Calculate overage costs based on usage and quotas."""
        total_cost = 0.0
        for resource_type, usage_amount in usage.items():
            if resource_type in quotas:
                quota = quotas[resource_type]
                overage = max(0.0, usage_amount - quota.limit)
                if overage > 0 and resource_type in self.overage_rate:
                    total_cost += overage * self.overage_rate[resource_type]
        return total_cost


@dataclass
class TenantConfig:
    """Configuration for a tenant."""

    tenant_id: str
    name: str
    tier: TenantTier
    quotas: Dict[ResourceType, ResourceQuota]
    billing: BillingConfig
    custom_agents: Set[str] = field(default_factory=set)
    isolated_storage: bool = True
    custom_domains: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    status: str = "active"  # active, suspended, terminated


@dataclass
class TenantInstance:
    """Active tenant instance with runtime data."""

    config: TenantConfig
    current_usage: Dict[ResourceType, float] = field(default_factory=dict)
    active_sessions: Set[str] = field(default_factory=set)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    last_activity: float = field(default_factory=time.time)

    def update_usage(self, resource_type: ResourceType, amount: float) -> bool:
        """Update resource usage and check if quota is exceeded."""
        if resource_type not in self.current_usage:
            self.current_usage[resource_type] = 0.0

        self.current_usage[resource_type] += amount
        self.last_activity = time.time()

        # Check if quota is exceeded
        if resource_type in self.config.quotas:
            quota = self.config.quotas[resource_type]
            return self.current_usage[resource_type] > quota.limit

        return False

    def get_usage_summary(self) -> Dict[str, Any]:
        """Get comprehensive usage summary."""
        summary = {
            "tenant_id": self.config.tenant_id,
            "current_usage": {},
            "quotas": {},
            "overages": {},
            "usage_percentages": {},
            "last_activity": self.last_activity,
        }

        for resource_type in ResourceType:
            current = self.current_usage.get(resource_type, 0.0)
            quota = self.config.quotas.get(resource_type)

            summary["current_usage"][resource_type.value] = current
            summary["quotas"][resource_type.value] = quota.limit if quota else None
            summary["overages"][resource_type.value] = max(
                0.0, current - (quota.limit if quota else 0.0)
            )
            summary["usage_percentages"][resource_type.value] = (
                (current / quota.limit * 100) if quota and quota.limit > 0 else 0.0
            )

        return summary


class EnterpriseTenantManager:
    """Advanced tenant management with resource isolation and billing."""

    def __init__(self):
        """Initialize enterprise tenant manager."""
        self.enabled = ENABLE_ENTERPRISE_TENANT_MANAGEMENT
        self.tenants: Dict[str, TenantInstance] = {}
        self.tenant_configs: Dict[str, TenantConfig] = {}
        self.resource_pools: Dict[str, Dict[ResourceType, float]] = {}

        if self.enabled:
            log.info("Enterprise Tenant Manager initialized")
            self._initialize_default_tiers()
        else:
            log.info("Enterprise Tenant Manager disabled via feature flag")

    def _initialize_default_tiers(self) -> None:
        """Initialize default tenant tiers and resource allocations."""
        # Default tier configurations
        tier_configs = {
            TenantTier.FREE: {
                ResourceType.CPU_UNITS: 100,
                ResourceType.MEMORY_MB: 1024,
                ResourceType.GPU_HOURS: 0,
                ResourceType.STORAGE_GB: 1,
                ResourceType.API_CALLS: 1000,
                ResourceType.AGENT_EXECUTIONS: 100,
                ResourceType.STREAM_HOURS: 0,
            },
            TenantTier.BASIC: {
                ResourceType.CPU_UNITS: 500,
                ResourceType.MEMORY_MB: 4096,
                ResourceType.GPU_HOURS: 10,
                ResourceType.STORAGE_GB: 10,
                ResourceType.API_CALLS: 10000,
                ResourceType.AGENT_EXECUTIONS: 1000,
                ResourceType.STREAM_HOURS: 50,
            },
            TenantTier.PROFESSIONAL: {
                ResourceType.CPU_UNITS: 2000,
                ResourceType.MEMORY_MB: 16384,
                ResourceType.GPU_HOURS: 50,
                ResourceType.STORAGE_GB: 100,
                ResourceType.API_CALLS: 100000,
                ResourceType.AGENT_EXECUTIONS: 10000,
                ResourceType.STREAM_HOURS: 500,
            },
            TenantTier.ENTERPRISE: {
                ResourceType.CPU_UNITS: 10000,
                ResourceType.MEMORY_MB: 65536,
                ResourceType.GPU_HOURS: 200,
                ResourceType.STORAGE_GB: 1000,
                ResourceType.API_CALLS: 1000000,
                ResourceType.AGENT_EXECUTIONS: 100000,
                ResourceType.STREAM_HOURS: 2000,
            },
        }

        # Store tier configurations for easy access
        self.tier_configs = tier_configs

    def create_tenant(self, tenant_config: TenantConfig) -> StepResult:
        """Create a new tenant with isolated resources."""
        if not self.enabled:
            return StepResult.fail("Enterprise tenant management disabled")

        try:
            if tenant_config.tenant_id in self.tenants:
                return StepResult.fail(
                    f"Tenant {tenant_config.tenant_id} already exists"
                )

            # Validate tenant configuration
            validation_result = self._validate_tenant_config(tenant_config)
            if not validation_result.success:
                return validation_result

            # Create isolated resource pool for tenant
            self._create_tenant_resource_pool(tenant_config)

            # Create tenant instance
            tenant_instance = TenantInstance(config=tenant_config)
            self.tenants[tenant_config.tenant_id] = tenant_instance
            self.tenant_configs[tenant_config.tenant_id] = tenant_config

            log.info(
                f"Created tenant {tenant_config.tenant_id} with tier {tenant_config.tier.value}"
            )

            return StepResult.ok(
                data={
                    "tenant_id": tenant_config.tenant_id,
                    "tier": tenant_config.tier.value,
                    "quotas": {
                        rt.value: q.limit for rt, q in tenant_config.quotas.items()
                    },
                    "created_at": tenant_config.created_at,
                }
            )

        except Exception as e:
            log.error(f"Failed to create tenant {tenant_config.tenant_id}: {e}")
            return StepResult.fail(f"Failed to create tenant: {e}")

    def _validate_tenant_config(self, config: TenantConfig) -> StepResult:
        """Validate tenant configuration."""
        if not config.tenant_id or not config.name:
            return StepResult.fail("Tenant ID and name are required")

        if not config.quotas:
            return StepResult.fail("Resource quotas are required")

        # Check if tier exists
        if config.tier not in self.tier_configs:
            return StepResult.fail(f"Unknown tenant tier: {config.tier}")

        return StepResult.ok(data={"valid": True})

    def _create_tenant_resource_pool(self, config: TenantConfig) -> None:
        """Create isolated resource pool for tenant."""
        pool_id = f"tenant_{config.tenant_id}"
        self.resource_pools[pool_id] = {}

        for resource_type, quota in config.quotas.items():
            self.resource_pools[pool_id][resource_type] = quota.limit

    def get_tenant(self, tenant_id: str) -> Optional[TenantInstance]:
        """Get tenant instance by ID."""
        return self.tenants.get(tenant_id)

    def update_tenant_usage(
        self, tenant_id: str, resource_type: ResourceType, amount: float
    ) -> StepResult:
        """Update tenant resource usage."""
        if not self.enabled:
            return StepResult.ok(data={"quota_exceeded": False})

        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return StepResult.fail(f"Tenant {tenant_id} not found")

        try:
            quota_exceeded = tenant.update_usage(resource_type, amount)

            if quota_exceeded:
                log.warning(
                    f"Tenant {tenant_id} exceeded quota for {resource_type.value}"
                )
                # Trigger quota exceeded handling
                self._handle_quota_exceeded(tenant, resource_type)

            return StepResult.ok(
                data={
                    "tenant_id": tenant_id,
                    "resource_type": resource_type.value,
                    "current_usage": tenant.current_usage.get(resource_type, 0.0),
                    "quota_exceeded": quota_exceeded,
                }
            )

        except Exception as e:
            log.error(f"Failed to update usage for tenant {tenant_id}: {e}")
            return StepResult.fail(f"Failed to update usage: {e}")

    def _handle_quota_exceeded(
        self, tenant: TenantInstance, resource_type: ResourceType
    ) -> None:
        """Handle quota exceeded scenarios."""
        # Log the event
        log.warning(
            f"Tenant {tenant.config.tenant_id} exceeded quota for {resource_type.value}"
        )

        # Update tenant status if necessary
        if tenant.config.status == "active":
            # For now, just log. In production, you might want to:
            # - Send alerts
            # - Suspend the tenant
            # - Charge overage fees
            # - Scale up their tier automatically
            pass

    def check_tenant_quota(
        self, tenant_id: str, resource_type: ResourceType, required_amount: float
    ) -> StepResult:
        """Check if tenant has sufficient quota for a resource."""
        if not self.enabled:
            return StepResult.ok(data={"sufficient": True})

        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return StepResult.fail(f"Tenant {tenant_id} not found")

        if resource_type not in tenant.config.quotas:
            return StepResult.ok(data={"sufficient": True})  # No quota defined

        quota = tenant.config.quotas[resource_type]
        current_usage = tenant.current_usage.get(resource_type, 0.0)
        available = quota.limit - current_usage

        sufficient = available >= required_amount

        return StepResult.ok(
            data={
                "sufficient": sufficient,
                "available": available,
                "required": required_amount,
                "quota_limit": quota.limit,
                "current_usage": current_usage,
            }
        )

    def get_tenant_usage_summary(self, tenant_id: str) -> StepResult:
        """Get comprehensive usage summary for a tenant."""
        if not self.enabled:
            return StepResult.ok(data={"usage_summary": {}})

        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return StepResult.fail(f"Tenant {tenant_id} not found")

        try:
            summary = tenant.get_usage_summary()
            return StepResult.ok(data={"usage_summary": summary})

        except Exception as e:
            log.error(f"Failed to get usage summary for tenant {tenant_id}: {e}")
            return StepResult.fail(f"Failed to get usage summary: {e}")

    def upgrade_tenant_tier(self, tenant_id: str, new_tier: TenantTier) -> StepResult:
        """Upgrade tenant to a new tier."""
        if not self.enabled:
            return StepResult.fail("Enterprise tenant management disabled")

        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return StepResult.fail(f"Tenant {tenant_id} not found")

        try:
            old_tier = tenant.config.tier
            tenant.config.tier = new_tier

            # Update quotas based on new tier
            if new_tier in self.tier_configs:
                new_quotas = {}
                for resource_type, limit in self.tier_configs[new_tier].items():
                    new_quotas[resource_type] = ResourceQuota(
                        resource_type=resource_type,
                        limit=limit,
                        current_usage=tenant.current_usage.get(resource_type, 0.0),
                    )
                tenant.config.quotas = new_quotas

            log.info(
                f"Upgraded tenant {tenant_id} from {old_tier.value} to {new_tier.value}"
            )

            return StepResult.ok(
                data={
                    "tenant_id": tenant_id,
                    "old_tier": old_tier.value,
                    "new_tier": new_tier.value,
                    "new_quotas": {
                        rt.value: q.limit for rt, q in tenant.config.quotas.items()
                    },
                }
            )

        except Exception as e:
            log.error(f"Failed to upgrade tenant {tenant_id}: {e}")
            return StepResult.fail(f"Failed to upgrade tenant: {e}")

    def suspend_tenant(self, tenant_id: str, reason: str = "") -> StepResult:
        """Suspend a tenant."""
        if not self.enabled:
            return StepResult.fail("Enterprise tenant management disabled")

        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return StepResult.fail(f"Tenant {tenant_id} not found")

        try:
            tenant.config.status = "suspended"
            log.info(f"Suspended tenant {tenant_id}. Reason: {reason}")

            return StepResult.ok(
                data={
                    "tenant_id": tenant_id,
                    "status": "suspended",
                    "reason": reason,
                    "suspended_at": time.time(),
                }
            )

        except Exception as e:
            log.error(f"Failed to suspend tenant {tenant_id}: {e}")
            return StepResult.fail(f"Failed to suspend tenant: {e}")

    def get_all_tenants(self) -> StepResult:
        """Get summary of all tenants."""
        if not self.enabled:
            return StepResult.ok(data={"tenants": []})

        try:
            tenant_summaries = []
            for tenant_id, tenant in self.tenants.items():
                summary = {
                    "tenant_id": tenant_id,
                    "name": tenant.config.name,
                    "tier": tenant.config.tier.value,
                    "status": tenant.config.status,
                    "created_at": tenant.config.created_at,
                    "last_accessed": tenant.last_activity,
                    "usage_summary": tenant.get_usage_summary(),
                }
                tenant_summaries.append(summary)

            return StepResult.ok(data={"tenants": tenant_summaries})

        except Exception as e:
            log.error(f"Failed to get tenant summaries: {e}")
            return StepResult.fail(f"Failed to get tenant summaries: {e}")

    def get_system_resource_usage(self) -> StepResult:
        """Get system-wide resource usage across all tenants."""
        if not self.enabled:
            return StepResult.ok(data={"system_usage": {}})

        try:
            system_usage = {}
            for resource_type in ResourceType:
                total_usage = 0.0
                total_quota = 0.0

                for tenant in self.tenants.values():
                    if resource_type in tenant.current_usage:
                        total_usage += tenant.current_usage[resource_type]
                    if resource_type in tenant.config.quotas:
                        total_quota += tenant.config.quotas[resource_type].limit

                system_usage[resource_type.value] = {
                    "total_usage": total_usage,
                    "total_quota": total_quota,
                    "utilization_percentage": (total_usage / total_quota * 100)
                    if total_quota > 0
                    else 0.0,
                }

            return StepResult.ok(data={"system_usage": system_usage})

        except Exception as e:
            log.error(f"Failed to get system resource usage: {e}")
            return StepResult.fail(f"Failed to get system resource usage: {e}")


# Global instance for easy access
_tenant_manager: Optional[EnterpriseTenantManager] = None


def get_tenant_manager() -> EnterpriseTenantManager:
    """Get the global tenant manager instance."""
    global _tenant_manager
    if _tenant_manager is None:
        _tenant_manager = EnterpriseTenantManager()
    return _tenant_manager


# Convenience functions
def create_tenant(tenant_config: TenantConfig) -> StepResult:
    """Create a new tenant."""
    manager = get_tenant_manager()
    return manager.create_tenant(tenant_config)


def update_tenant_usage(
    tenant_id: str, resource_type: ResourceType, amount: float
) -> StepResult:
    """Update tenant resource usage."""
    manager = get_tenant_manager()
    return manager.update_tenant_usage(tenant_id, resource_type, amount)


def check_tenant_quota(
    tenant_id: str, resource_type: ResourceType, required_amount: float
) -> StepResult:
    """Check tenant quota."""
    manager = get_tenant_manager()
    return manager.check_tenant_quota(tenant_id, resource_type, required_amount)


def get_tenant_usage_summary(tenant_id: str) -> StepResult:
    """Get tenant usage summary."""
    manager = get_tenant_manager()
    return manager.get_tenant_usage_summary(tenant_id)
