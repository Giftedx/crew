from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional
import yaml

from .context import TenantContext
from .models import Tenant


@dataclass
class TenantConfig:
    tenant: Tenant
    workspaces: Dict[str, dict]


class TenantRegistry:
    """Load lightweight tenant configurations from the filesystem."""

    def __init__(self, tenants_dir: Path):
        self.tenants_dir = tenants_dir
        self._cache: Dict[str, TenantConfig] = {}

    def load(self) -> None:
        for path in self.tenants_dir.glob("*/tenant.yaml"):
            with path.open("r", encoding="utf-8") as fh:
                data = yaml.safe_load(fh) or {}
            tenant = Tenant(
                id=data.get("id", 0),
                slug=path.parent.name,
                name=data.get("name", path.parent.name),
                created_at=data.get("created_at"),
                status=data.get("status", "active"),
            )
            self._cache[tenant.slug] = TenantConfig(
                tenant=tenant, workspaces=data.get("workspaces", {})
            )

    def get_tenant(self, slug: str) -> Optional[TenantConfig]:
        return self._cache.get(slug)

    def resolve_discord_guild(self, guild_id: int) -> Optional[TenantContext]:
        for cfg in self._cache.values():
            for ws_key, ws in cfg.workspaces.items():
                if ws.get("discord_guild_id") == guild_id:
                    return TenantContext(
                        tenant_id=cfg.tenant.slug, workspace_id=ws_key
                    )
        return None
