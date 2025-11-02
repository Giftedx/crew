"""Router adapter that maps provider:model arms to a bandit policy.

This module integrates the provider registry with a Thompson Sampling bandit
without modifying restricted directories. It exposes a simple API to build
arms and select a provider:model according to a high-level policy.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from enum import Enum
from platform.core.step_result import StepResult
from platform.observability.metrics import get_metrics
from typing import Any

from core.rl.thompson_sampling import ThompsonSamplingBandit

from .llm_provider_registry import ModelInfo, get_provider_allowlist_from_config, list_models


class RouterPolicy(str, Enum):
    QUALITY_FIRST = "quality_first"
    COST_AWARE = "cost"
    LATENCY_AWARE = "latency"


@dataclass
class Arm:
    arm_id: str
    provider: str
    model: str
    cost_in: float | None
    cost_out: float | None
    latency_ms: int | None
    quality_tier: str | None
    capabilities: set[str]


def _read_policy_from_config() -> RouterPolicy:
    try:
        from platform.config.configuration import get_config

        policy_str = str(getattr(get_config(), "router_policy", "quality_first") or "quality_first").lower()
        if policy_str in {"quality_first", "quality"}:
            return RouterPolicy.QUALITY_FIRST
        if policy_str in {"cost", "cost_aware"}:
            return RouterPolicy.COST_AWARE
        if policy_str in {"latency", "latency_aware"}:
            return RouterPolicy.LATENCY_AWARE
    except Exception:
        pass
    return RouterPolicy.QUALITY_FIRST


class LLMRouterAdapter:
    """Builds arms from the provider registry and selects using a bandit.

    The adapter returns a StepResult with selection and a detailed arm list and
    attaches selection metadata (provider/model/policy) for downstream logging.
    """

    def __init__(self, allowlist: list[str] | None = None, policy: RouterPolicy | None = None):
        self.allowlist = allowlist if allowlist is not None else get_provider_allowlist_from_config()
        self.policy = policy or _read_policy_from_config()
        self._bandit = ThompsonSamplingBandit()

    def _to_arms(self, models: list[ModelInfo]) -> list[Arm]:
        arms: list[Arm] = []
        for mi in models:
            arms.append(
                Arm(
                    arm_id=f"{mi.provider}:{mi.model}",
                    provider=mi.provider,
                    model=mi.model,
                    cost_in=mi.cost_per_1k_input,
                    cost_out=mi.cost_per_1k_output,
                    latency_ms=mi.est_latency_ms,
                    quality_tier=mi.quality_tier,
                    capabilities=set(mi.capabilities),
                )
            )
        return arms

    def _apply_policy_shortlist(self, arms: list[Arm]) -> list[Arm]:
        if self.policy == RouterPolicy.QUALITY_FIRST:
            top = [a for a in arms if (a.quality_tier or "").lower() == "top"]
            return top or arms
        if self.policy == RouterPolicy.COST_AWARE:
            cheap = sorted(arms, key=lambda a: float(a.cost_in or 0.0) + float(a.cost_out or 0.0))
            return cheap[: max(1, min(3, len(cheap)))]
        if self.policy == RouterPolicy.LATENCY_AWARE:
            low = sorted(arms, key=lambda a: a.latency_ms or 10000)
            return low[: max(1, min(3, len(low)))]
        return arms

    def build_arms(self, required_capabilities: set[str] | None = None) -> list[dict[str, Any]]:
        """Build arms as dictionaries for easy serialization and metrics.

        Args:
            required_capabilities: optional capability filter (e.g., {"vision"})
        """
        models = list_models(self.allowlist)
        arms = self._to_arms(models)
        if required_capabilities:
            arms = [a for a in arms if required_capabilities.issubset(a.capabilities)]
        shortlisted = self._apply_policy_shortlist(arms)
        for a in shortlisted:
            self._bandit.add_arm(
                arm_id=a.arm_id,
                name=f"{a.provider}:{a.model}",
                metadata={
                    "provider": a.provider,
                    "model": a.model,
                    "cost_in": a.cost_in,
                    "cost_out": a.cost_out,
                    "latency_ms": a.latency_ms,
                    "quality_tier": a.quality_tier,
                    "capabilities": sorted(a.capabilities),
                },
            )
        with contextlib.suppress(Exception):
            get_metrics().histogram(
                "router_shortlist_size", float(len(shortlisted)), labels={"policy": self.policy.value}
            )
        return [
            {
                "arm_id": a.arm_id,
                "provider": a.provider,
                "model": a.model,
                "capabilities": sorted(a.capabilities),
                "cost_in": a.cost_in,
                "cost_out": a.cost_out,
                "latency_ms": a.latency_ms,
                "quality_tier": a.quality_tier,
            }
            for a in shortlisted
        ]

    def select(self, required_capabilities: set[str] | None = None) -> StepResult:
        """Select an arm and return a StepResult with selection details.

        Emits selection and arm attribute metrics with labels {provider, model, policy}.
        Metrics are best-effort and never raise.
        """
        arms = self.build_arms(required_capabilities=required_capabilities)
        if not arms:
            return StepResult.fail("No routing candidates available")
        forced_arm_id: str | None = None
        with contextlib.suppress(Exception):
            try:
                from platform.config.configuration import get_setting

                forced = get_setting("force_router_selection", None)
            except Exception:
                forced = None
            if isinstance(forced, str):
                val = forced.strip()
                if ":" in val:
                    forced_arm_id = val
        arm_id = None
        if forced_arm_id and any(a["arm_id"] == forced_arm_id for a in arms):
            arm_id = forced_arm_id
        else:
            arm_id = self._bandit.select_arm()
        if not arm_id:
            return StepResult.fail("Bandit failed to select an arm")
        selected = next((a for a in arms if a["arm_id"] == arm_id), None)
        if not selected:
            selected = arms[0]
            arm_id = selected["arm_id"]
        result = StepResult.ok(
            selection={
                "provider": selected["provider"],
                "model": selected["model"],
                "arm_id": arm_id,
                "policy": self.policy.value,
            },
            arms=arms,
        )
        result.metadata.update(
            {"provider": selected["provider"], "model": selected["model"], "policy": self.policy.value}
        )
        with contextlib.suppress(Exception):
            labels = {"provider": selected["provider"], "model": selected["model"], "policy": self.policy.value}
            get_metrics().counter("router_selection_total", labels=labels).inc()
            cost_in = next((a["cost_in"] for a in arms if a["arm_id"] == arm_id), None)
            cost_out = next((a["cost_out"] for a in arms if a["arm_id"] == arm_id), None)
            latency_ms = next((a["latency_ms"] for a in arms if a["arm_id"] == arm_id), None)
            if cost_in is not None:
                get_metrics().histogram("router_cost_in_per_1k", float(cost_in), labels=labels)
            if cost_out is not None:
                get_metrics().histogram("router_cost_out_per_1k", float(cost_out), labels=labels)
            if latency_ms is not None:
                get_metrics().histogram("router_est_latency_ms", float(latency_ms), labels=labels)
        return result


__all__ = ["LLMRouterAdapter", "RouterPolicy"]
