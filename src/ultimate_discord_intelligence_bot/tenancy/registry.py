from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from core.time import default_utc_now

from .context import TenantContext
from .models import Tenant


@dataclass
class TenantConfig:
    tenant: Tenant
    workspaces: dict[str, dict[str, Any]]
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
            created_raw = data.get("created_at")
            created_at: datetime
            if isinstance(created_raw, datetime):
                # Normalize to UTC (assume naive datetimes are UTC)
                created_at = created_raw if created_raw.tzinfo else created_raw.replace(tzinfo=UTC)
            elif isinstance(created_raw, str):
                # Try ISO parse, fallback to numeric epoch if digits
                if created_raw.isdigit():
                    try:
                        created_at = datetime.fromtimestamp(float(created_raw), tz=UTC)
                    except Exception:
                        created_at = default_utc_now()
                else:
                    try:
                        parsed = datetime.fromisoformat(created_raw)
                        if parsed.tzinfo is None:
                            parsed = parsed.replace(tzinfo=UTC)
                        created_at = parsed
                    except ValueError:
                        created_at = default_utc_now()
            else:
                # Try numeric epoch (int/float/other castables)
                try:
                    created_at = datetime.fromtimestamp(float(created_raw), tz=UTC)  # type: ignore[arg-type]
                except Exception:
                    created_at = default_utc_now()
            tenant = Tenant(
                id=data.get("id", 0),
                slug=tenant_dir.name,
                name=data.get("name", tenant_dir.name),
                created_at=created_at,
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

    def get_provider_preferences(self, ctx: TenantContext) -> list[str]:
        """Return preferred provider order if configured for the tenant/workspace."""
        cfg = self._cache.get(ctx.tenant_id)
        if not cfg or not cfg.routing:
            return []
        providers: list[str] | None = None
        # workspace override first
        ws_cfg = cfg.workspaces.get(ctx.workspace_id, {})
        ws_routing = ws_cfg.get("routing")
        if isinstance(ws_routing, dict):
            prov = ws_routing.get("providers")
            if isinstance(prov, list):
                providers = [str(p) for p in prov]
        if providers is None:
            prov = cfg.routing.get("providers")
            if isinstance(prov, list):
                providers = [str(p) for p in prov]
        return providers or []

    def get_model_overrides(self, ctx: TenantContext) -> dict[str, str]:
        """Return model name overrides by task type (e.g., analysis, debate)."""
        cfg = self._cache.get(ctx.tenant_id)
        if not cfg or not cfg.routing:
            return {}
        models: dict[str, str] | None = None
        # workspace override first
        ws_cfg = cfg.workspaces.get(ctx.workspace_id, {})
        ws_routing = ws_cfg.get("routing")
        if isinstance(ws_routing, dict) and isinstance(ws_routing.get("models"), dict):
            models = {str(k): str(v) for k, v in ws_routing["models"].items()}
        if models is None and isinstance(cfg.routing.get("models"), dict):
            models = {str(k): str(v) for k, v in cfg.routing["models"].items()}
        return models or {}

    def get_rl_overrides(self, ctx: TenantContext) -> dict[str, float | int]:
        """Return RL reward shaping overrides if present.

        Sources (precedence):
          - flags.yaml: rl: { reward_cost_weight, reward_latency_weight, reward_latency_ms_window }
          - routing.yaml: rewards: { cost_weight, latency_weight, latency_ms_window }
        """
        cfg = self._cache.get(ctx.tenant_id)
        if not cfg:
            return {}
        res: dict[str, float | int] = {}
        # flags.yaml path
        if cfg.flags and isinstance(cfg.flags.get("rl"), dict):
            rl = cfg.flags["rl"]
            for src, dst in (
                ("reward_cost_weight", "reward_cost_weight"),
                ("reward_latency_weight", "reward_latency_weight"),
                ("reward_latency_ms_window", "reward_latency_ms_window"),
            ):
                if src in rl:
                    try:
                        res[dst] = float(rl[src]) if "weight" in src else int(rl[src])
                    except Exception:
                        pass
        # routing.yaml alternative keys
        if cfg.routing and isinstance(cfg.routing.get("rewards"), dict):
            rw = cfg.routing["rewards"]
            if "cost_weight" in rw:
                try:
                    res.setdefault("reward_cost_weight", float(rw["cost_weight"]))
                except Exception:
                    pass
            if "latency_weight" in rw:
                try:
                    res.setdefault("reward_latency_weight", float(rw["latency_weight"]))
                except Exception:
                    pass
            if "latency_ms_window" in rw:
                try:
                    res.setdefault("reward_latency_ms_window", int(rw["latency_ms_window"]))
                except Exception:
                    pass
        return res

    def get_pricing_map(self, ctx: TenantContext) -> dict[str, float]:
        """Return per-model USD/1k token prices if configured under budgets.

        Supports either a top-level `pricing` map or `model_prices` map.
        """
        cfg = self._cache.get(ctx.tenant_id)
        if not cfg or not cfg.budgets:
            return {}
        budgets = cfg.budgets
        pricing = budgets.get("pricing") or budgets.get("model_prices")
        if isinstance(pricing, dict):
            out: dict[str, float] = {}
            for k, v in pricing.items():
                try:
                    out[str(k)] = float(v)
                except Exception:
                    continue
            return out
        return {}

    def get_per_request_limit(self, ctx: TenantContext, task: str) -> float | None:
        """Return per-request cost limit for a given task if configured.

        Supports multiple shapes under `budgets.yaml`:
          - flat: `max_per_request`
          - nested: `limits.max_per_request`
          - nested per-task: `limits.by_task.{task}` or `limits.per_task.{task}`
          - fallback to `limits.by_task.default` or `limits.per_task.default`
        """
        cfg = self._cache.get(ctx.tenant_id)
        if not cfg or not cfg.budgets:
            return None
        budgets = cfg.budgets
        # Highest precedence: per-task under limits
        limits = budgets.get("limits") if isinstance(budgets, dict) else None
        if isinstance(limits, dict):
            for key in ("by_task", "per_task", "tasks"):
                per_task = limits.get(key)
                if isinstance(per_task, dict):
                    if task in per_task:
                        try:
                            return float(per_task[task])
                        except Exception:
                            pass
                    if "default" in per_task:
                        try:
                            return float(per_task["default"])
                        except Exception:
                            pass
            if "max_per_request" in limits:
                try:
                    raw = limits.get("max_per_request")
                    return float(raw) if raw is not None else None
                except Exception:
                    pass
        # Backwards-compatible flat
        if "max_per_request" in budgets:
            try:
                raw = budgets.get("max_per_request")
                return float(raw) if raw is not None else None
            except Exception:
                pass
        return None

    # ------------------------------------------------------------------ cumulative budgets
    def get_request_total_limit(self, ctx: TenantContext) -> float | None:
        """Return cumulative total budget for a single high-level request.

        Supported keys inside ``budgets.yaml`` (first match wins):
          budgets:
            limits:
              total_request: 2.5
              request_total: 2.5
              total_per_request: 2.5
              request:
                max_total: 2.5
            # Backwards-compatible flat key (discouraged): request_total_limit

        The intent is a cap across all model calls within a pipeline execution.
        """
        cfg = self._cache.get(ctx.tenant_id)
        if not cfg or not cfg.budgets:
            return None
        budgets = cfg.budgets
        limits = budgets.get("limits") if isinstance(budgets, dict) else None
        candidates: list[float | None] = []
        if isinstance(limits, dict):
            for key in ("total_request", "request_total", "total_per_request"):
                if key in limits:
                    try:
                        candidates.append(float(limits[key]))
                    except Exception:
                        candidates.append(None)
            # nested: limits.request.max_total
            req = limits.get("request")
            if isinstance(req, dict) and "max_total" in req:
                try:
                    candidates.append(float(req["max_total"]))
                except Exception:
                    candidates.append(None)
        # flat legacy
        if "request_total_limit" in budgets:
            raw_rtl = budgets.get("request_total_limit")
            if raw_rtl is not None:
                try:
                    candidates.append(float(raw_rtl))
                except Exception:
                    candidates.append(None)
        for val in candidates:
            if isinstance(val, float):  # first successful parse wins
                return val
        return None

    def get_per_task_cost_limits(self, ctx: TenantContext) -> dict[str, float]:
        """Return per-task cumulative cost limits for a single request.

        Supported shapes:
          budgets.limits.tasks: { analysis: 0.75, debate: 0.5 }
          budgets.limits.costs.by_task.*
          budgets.limits.costs.per_task.*

        Returns empty dict if none defined.
        """
        cfg = self._cache.get(ctx.tenant_id)
        if not cfg or not cfg.budgets:
            return {}
        budgets = cfg.budgets
        limits = budgets.get("limits") if isinstance(budgets, dict) else None
        out: dict[str, float] = {}
        if isinstance(limits, dict):
            # direct tasks mapping
            tasks = limits.get("tasks")
            if isinstance(tasks, dict):
                for k, v in tasks.items():
                    try:
                        out[str(k)] = float(v)
                    except Exception:
                        pass
            costs = limits.get("costs")
            if isinstance(costs, dict):
                for variant in ("by_task", "per_task"):
                    mapping = costs.get(variant)
                    if isinstance(mapping, dict):
                        for k, v in mapping.items():
                            if k == "default":
                                continue
                            try:
                                out.setdefault(str(k), float(v))
                            except Exception:
                                pass
        return out

    def resolve_discord_guild(self, guild_id: int) -> TenantContext | None:
        for cfg in self._cache.values():
            for ws_key, ws in cfg.workspaces.items():
                if ws.get("discord_guild_id") == guild_id:
                    return TenantContext(tenant_id=cfg.tenant.slug, workspace_id=ws_key)
        return None
