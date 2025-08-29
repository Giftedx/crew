from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .context import TenantContext
from .models import Tenant


@dataclass
class TenantConfig:
    tenant: Tenant
    workspaces: dict[str, dict]
    budgets: dict[str, Any] | None = None
    routing: dict[str, Any] | None = None
    flags: dict[str, Any] | None = None


class TenantRegistry:
    """Load lightweight tenant configurations from the filesystem."""

    def __init__(self, tenants_dir: Path):
        self.tenants_dir = tenants_dir
        self._cache: dict[str, TenantConfig] = {}

    def load(self) -> None:
        for path in self.tenants_dir.glob("*/tenant.yaml"):
            tenant_dir = path.parent
            with path.open("r", encoding="utf-8") as fh:
                data = yaml.safe_load(fh) or {}
            tenant = Tenant(
                id=data.get("id", 0),
                slug=tenant_dir.name,
                name=data.get("name", tenant_dir.name),
                created_at=data.get("created_at"),
                status=data.get("status", "active"),
            )
            budgets = self._load_yaml(tenant_dir / "budgets.yaml")
            routing = self._load_yaml(tenant_dir / "routing.yaml")
            flags = self._load_yaml(tenant_dir / "flags.yaml")
            self._cache[tenant.slug] = TenantConfig(
                tenant=tenant,
                workspaces=data.get("workspaces", {}),
                budgets=budgets,
                routing=routing,
                flags=flags,
            )

    @staticmethod
    def _load_yaml(path: Path) -> dict[str, Any] | None:
        if path.exists():
            with path.open("r", encoding="utf-8") as fh:
                return yaml.safe_load(fh) or {}
        return None

    def get_tenant(self, slug: str) -> TenantConfig | None:
        return self._cache.get(slug)

    # ------------------------------------------------------------------ helpers
    def get_budget_config(self, tenant_id: str) -> dict[str, Any] | None:
        cfg = self._cache.get(tenant_id)
        return cfg.budgets if cfg else None

    def get_allowed_models(self, ctx: TenantContext) -> list[str]:
        cfg = self._cache.get(ctx.tenant_id)
        if not cfg:
            return []
        allowed: list[str] | None = None
        if cfg.routing:
            # workspace override takes precedence
            ws_cfg = cfg.workspaces.get(ctx.workspace_id, {})
            ws_routing = ws_cfg.get("routing")
            if isinstance(ws_routing, dict):
                allowed = ws_routing.get("allowed_models")
            if allowed is None:
                allowed = cfg.routing.get("allowed_models")
        return allowed or []

    def resolve_discord_guild(self, guild_id: int) -> TenantContext | None:
        for cfg in self._cache.values():
            for ws_key, ws in cfg.workspaces.items():
                if ws.get("discord_guild_id") == guild_id:
                    return TenantContext(tenant_id=cfg.tenant.slug, workspace_id=ws_key)
        return None
