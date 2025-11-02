from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from datetime import datetime


@dataclass
class Tenant:
    """A group of users and workspaces sharing configuration."""

    id: int
    slug: str
    name: str
    created_at: datetime
    status: str = "active"


@dataclass
class Workspace:
    """Sub-division of a tenant mapping to a Discord guild or team."""

    id: int
    tenant_id: int
    key: str
    display_name: str
    discord_guild_id: int | None = None
    description: str | None = None


@dataclass
class RoutingProfile:
    id: int
    tenant_id: int
    name: str
    allowed_models: list[str]
    provider_prefs: dict[str, str] | None = None
    cost_ceiling_usd: float | None = None
    latency_slo_ms: int | None = None


@dataclass
class Budget:
    id: int
    tenant_id: int
    daily_cap_usd: float
    hourly_cap_usd: float
    soft_caps_by_command: dict[str, float] | None = None


@dataclass
class PolicyBinding:
    id: int
    tenant_id: int
    policy_version: str
    overrides_yaml: str | None = None


@dataclass
class Flags:
    id: int
    tenant_id: int
    values_yaml: str | None = None


@dataclass
class SecretsRef:
    id: int
    tenant_id: int
    vault_path: str | None = None
    env_prefix: str | None = None
