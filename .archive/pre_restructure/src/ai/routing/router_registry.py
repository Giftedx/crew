"""Tenant-scoped router registry and reward utilities.

Provides:
  - get_tenant_router(): returns a ThompsonBanditRouter instance scoped to current tenant/workspace
  - compute_selection_entropy(): helper for entropy of recent selection counts
  - RewardNormalizer: incremental EMA-based normalizer to combine quality/latency/cost into [0,1]

Environment:
  ENABLE_BANDIT_ROUTING (controls active routing same as base router)
  ENABLE_BANDIT_PERSIST / BANDIT_STATE_DIR (handled by underlying router)

State File Naming:
  bandit_state__<tenant>__<workspace>.json (colons replaced by double underscores already upstream)

Note: For multi-process deployments, external synchronization (e.g., Redis) would be needed. This
in-memory registry is per-process.
"""

from __future__ import annotations

import json
import math
import os
import threading
from collections import defaultdict
from typing import TYPE_CHECKING, cast

from ai.routing.bandit_router import ThompsonBanditRouter

from ultimate_discord_intelligence_bot.tenancy.context import current_tenant


if TYPE_CHECKING:
    from ._metrics_types import MetricLike, MetricsFacade


_registry_lock = threading.Lock()
_routers: dict[tuple[str, str], ThompsonBanditRouter] = {}
_selection_counts: dict[tuple[str, str], dict[str, int]] = defaultdict(lambda: defaultdict(int))

try:  # optional metrics
    from ultimate_discord_intelligence_bot.obs.metrics import get_metrics as _gm

    def _obtain_metrics() -> MetricsFacade | None:
        try:
            return cast("MetricsFacade", _gm())
        except Exception:  # pragma: no cover
            return None
except Exception:  # pragma: no cover

    def _obtain_metrics() -> MetricsFacade | None:
        return None


_metrics: MetricsFacade | None = _obtain_metrics()
_selection_entropy_gauge: MetricLike | None = None
_posterior_entropy_gauge: MetricLike | None = None
if _metrics:
    try:
        _selection_entropy_gauge = _metrics.gauge(
            name="bandit_router_selection_entropy",
            description="Shannon entropy of model selection distribution (empirical selections)",
        )
        _posterior_entropy_gauge = _metrics.gauge(
            name="bandit_router_posterior_mean_entropy",
            description="Entropy of mean posterior probabilities (informational uncertainty)",
        )
    except Exception:  # pragma: no cover
        _selection_entropy_gauge = None
        _posterior_entropy_gauge = None


def _state_filename(tenant_id: str, workspace_id: str) -> str:
    return f"bandit_state__{tenant_id}__{workspace_id}.json"


def get_tenant_router() -> ThompsonBanditRouter:
    ctx = current_tenant()
    if ctx is None:
        # Fall back to a global router (shared) if tenant not set
        key = ("_global", "_global")
        with _registry_lock:
            r = _routers.get(key)
            if r is None:
                r = ThompsonBanditRouter(state_file=_state_filename(*key))
                _routers[key] = r
            return r
    key = (ctx.tenant_id, ctx.workspace_id)
    with _registry_lock:
        r = _routers.get(key)
        if r is None:
            r = ThompsonBanditRouter(state_file=_state_filename(*key))
            _routers[key] = r
        return r


def record_selection(model: str) -> None:
    ctx = current_tenant()
    key = (ctx.tenant_id, ctx.workspace_id) if ctx else ("_global", "_global")
    with _registry_lock:
        _selection_counts[key][model] += 1
        if _selection_entropy_gauge:
            ent = _compute_entropy_locked(_selection_counts[key])
            if ent is not None:
                _selection_entropy_gauge.set(ent, {})
        # posterior entropy on demand (requires router present)
        if _posterior_entropy_gauge:
            router = _routers.get(key)
            if router is not None:
                pe = _compute_posterior_mean_entropy(router)
                if pe is not None:
                    _posterior_entropy_gauge.set(pe, {})


def compute_selection_entropy() -> float | None:
    """Return Shannon entropy over selection proportions for current tenant.

    Returns None if no selections yet. Units: nats.
    """

    ctx = current_tenant()
    key = (ctx.tenant_id, ctx.workspace_id) if ctx else ("_global", "_global")
    with _registry_lock:
        counts = _selection_counts.get(key)
        return _compute_entropy_locked(counts)


def _compute_entropy_locked(counts: dict[str, int] | None) -> float | None:
    if not counts:
        return None
    total = sum(counts.values())
    if total == 0:
        return None
    entropy = 0.0
    for c in counts.values():
        p = c / total
        entropy -= p * math.log(p)
    return entropy


def _compute_posterior_mean_entropy(router: ThompsonBanditRouter) -> float | None:
    arms = router.arms()
    if not arms:
        return None
    # Mean probability estimate = alpha / (alpha+beta)
    probs = []
    for a in arms:
        st = router.get_state(a)
        if st is None:
            continue
        total = st.alpha + st.beta
        if total <= 0:
            continue
        probs.append(st.alpha / total)
    if not probs:
        return None
    # Normalize to a distribution (they are independent expectations, not guaranteed to sum to 1)
    s = sum(probs)
    if s <= 0:
        return None
    entropy = 0.0
    for p in probs:
        p_norm = p / s
        entropy -= p_norm * math.log(p_norm)
    return entropy


# ---------------------- Selection Count Persistence ----------------------


def _counts_state_path() -> str:
    base_dir = os.getenv("BANDIT_STATE_DIR", "./bandit_state")
    return os.path.join(base_dir, "selection_counts.json")


def load_selection_counts() -> None:
    if os.getenv("ENABLE_BANDIT_PERSIST", "0").lower() not in {
        "1",
        "true",
        "yes",
        "on",
    }:
        return
    path = _counts_state_path()
    if not os.path.isfile(path):
        return
    try:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        if isinstance(raw, dict):
            with _registry_lock:
                for key_str, model_counts in raw.items():
                    if not isinstance(model_counts, dict):
                        continue
                    tenant, workspace = key_str.split("||", 1) if "||" in key_str else (key_str, "")
                    tup = (tenant, workspace)
                    for m, c in model_counts.items():
                        if isinstance(c, int) and c >= 0:
                            _selection_counts[tup][m] = c
    except Exception:  # pragma: no cover
        pass


def save_selection_counts() -> None:
    if os.getenv("ENABLE_BANDIT_PERSIST", "0").lower() not in {
        "1",
        "true",
        "yes",
        "on",
    }:
        return
    path = _counts_state_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data: dict[str, dict[str, int]] = {}
    with _registry_lock:
        for (tenant, workspace), counts in _selection_counts.items():
            key_str = f"{tenant}||{workspace}"
            data[key_str] = dict(counts)
    tmp = path + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, separators=(",", ":"))
        os.replace(tmp, path)
    except Exception:  # pragma: no cover
        pass


# Load counts at import time (best-effort)
load_selection_counts()


class RewardNormalizer:
    """EMA-based normalizer for latency & cost; direct quality passthrough.

    Tracks exponential moving averages of latency and cost to produce a stabilized normalized value
    where lower latency/cost increases reward. Output reward in [0,1].
    """

    def __init__(self, alpha: float = 0.2) -> None:
        self.alpha = alpha
        self._lat_ema: float | None = None
        self._cost_ema: float | None = None

    def _ema(self, prev: float | None, value: float) -> float:
        return value if prev is None else (self.alpha * value + (1 - self.alpha) * prev)

    def compute(self, quality: float, latency_ms: float, cost: float) -> float:
        # Clamp quality into [0,1]
        q = max(0.0, min(1.0, quality))
        self._lat_ema = self._ema(self._lat_ema, latency_ms)
        self._cost_ema = self._ema(self._cost_ema, cost)
        lat_norm = 0.5 if self._lat_ema is None or self._lat_ema == 0 else min(1.0, latency_ms / (2 * self._lat_ema))
        cost_norm = 0.5 if self._cost_ema is None or self._cost_ema == 0 else min(1.0, cost / (2 * self._cost_ema))
        reward = 0.5 * q + 0.3 * (1 - lat_norm) + 0.2 * (1 - cost_norm)
        return max(0.0, min(1.0, reward))


__all__ = [
    "RewardNormalizer",
    "compute_selection_entropy",
    "get_tenant_router",
    "record_selection",
]
