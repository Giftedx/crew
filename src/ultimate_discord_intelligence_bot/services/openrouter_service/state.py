"""Shared dataclasses capturing state during OpenRouter routing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from collections.abc import Callable

    from ultimate_discord_intelligence_bot.tenancy.context import TenantContext


@dataclass(slots=True)
class RouteState:
    """Mutable container passed between routing stages."""

    prompt: str
    task_type: str
    requested_model: str | None
    chosen_model: str
    ctx_effective: TenantContext | None
    labels_factory: Callable[[], dict[str, str]]
    effective_models: dict[str, list[str]]
    provider: dict[str, Any]
    provider_family: str
    tokens_in: int
    projected_cost: float
    affordable_alternative: str | None
    effective_prices: dict[str, float]
    tracker: Any
    offline_mode: bool
    provider_overrides: dict[str, Any] | None
    cache_key: str | None = None
    namespace: str | None = None
    cache_metadata: dict[str, Any] | None = None
    compression_metadata: dict[str, Any] | None = None
    effective_max: float = float("inf")
    latency_ms: float = 0.0
    tokens_out: int = 0
    result: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
    start_time: float = 0.0
    adaptive_trial_index: int | None = None
    adaptive_suggested_model: str | None = None
    adaptive_candidates: list[str] | None = None
    adaptive_recorded: bool = False
    rl_router_selection: dict[str, Any] | None = None

    def labels(self) -> dict[str, str]:
        """Return lazily-computed metric labels."""
        return self.labels_factory()
