"""LinUCB contextual bandit router for model selection.

Implements the classic LinUCB (disjoint model) formulation:
  For each arm a: maintain A_a (dxd) and b_a (d)
  Theta_a = A_a^{-1} b_a
  Given feature vector x in R^d, score(a) = theta_a^T x + alpha * sqrt(x^T A_a^{-1} x)

Environment:
  ENABLE_CONTEXTUAL_BANDIT=1 to enable usage by higher-level router integration.
  LINUCB_ALPHA (default 0.8) exploration scaling.

Notes:
  - Features must be provided on both select() and update().
  - Reward expected in [0,1].
    - Persistence optional via ENABLE_BANDIT_PERSIST + BANDIT_STATE_DIR.
"""

from __future__ import annotations

import contextlib
import json
import math
import os
import threading
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast


if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from ._metrics_types import MetricLike, MetricsFacade
try:
    from platform.observability.metrics import get_metrics as _gm

    _real_get_metrics: Callable[[], MetricsFacade] | None = cast("Callable[[], MetricsFacade]", _gm)
except Exception:
    _real_get_metrics = None


def _obtain_metrics() -> MetricsFacade | None:
    func = _real_get_metrics
    if func is None:
        return None
    try:
        return func()
    except Exception:
        return None


def _ctx_flag() -> bool:
    return os.getenv("ENABLE_CONTEXTUAL_BANDIT", "0").lower() in {"1", "true", "yes", "on"}


def _alpha_value() -> float:
    return float(os.getenv("LINUCB_ALPHA", "0.8") or 0.8)


@dataclass
class _ArmCtx:
    A: list[list[float]]
    b: list[float]
    A_inv: list[list[float]] | None = None
    updates: int = 0


class LinUCBRouter:
    def __init__(self, dimension: int) -> None:
        if dimension <= 0:
            raise ValueError("dimension must be positive")
        self._d = dimension
        self._arms: dict[str, _ArmCtx] = {}
        self._lock = threading.Lock()
        self._metrics: MetricsFacade | None = _obtain_metrics()
        self._persist_enabled = os.getenv("ENABLE_BANDIT_PERSIST", "0").lower() in {"1", "true", "yes", "on"}
        self._state_dir = os.getenv("BANDIT_STATE_DIR", "./bandit_state")
        self._recompute_interval = int(os.getenv("LINUCB_RECOMPUTE_INTERVAL", "0") or 0)
        self._alpha = _alpha_value()
        if self._metrics:
            m = self._metrics
            self._sel_counter: MetricLike | None = m.counter(
                name="linucb_selections_total", description="Total LinUCB selections per arm"
            )
            self._update_counter: MetricLike | None = m.counter(
                name="linucb_updates_total", description="Total LinUCB updates per arm"
            )
            self._recompute_counter: MetricLike | None = m.counter(
                name="linucb_recomputes_total", description="Number of full inverse recomputations"
            )
            self._cond_gauge: MetricLike | None = m.gauge(
                name="linucb_condition_number",
                description="Estimated condition number of A matrix per arm (after update)",
            )
        else:
            self._sel_counter = None
            self._update_counter = None
            self._recompute_counter = None
            self._cond_gauge = None
        self._cond_threshold = float(os.getenv("LINUCB_COND_THRESHOLD", "0") or 0.0)
        if self._persist_enabled:
            with contextlib.suppress(Exception):
                os.makedirs(self._state_dir, exist_ok=True)
                self._load_state()

    def _identity(self) -> list[list[float]]:
        return [[1.0 if i == j else 0.0 for j in range(self._d)] for i in range(self._d)]

    def _mat_vec(self, A: list[list[float]], v: list[float]) -> list[float]:
        return [sum(A[i][k] * v[k] for k in range(self._d)) for i in range(self._d)]

    def _vec_outer_add(self, A: list[list[float]], x: list[float]) -> None:
        for i in range(self._d):
            xi = x[i]
            row = A[i]
            for j in range(self._d):
                row[j] += xi * x[j]

    def _mat_inv(self, A: list[list[float]]) -> list[list[float]]:
        n = self._d
        aug = [row[:] + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate(A)]
        for i in range(n):
            pivot = aug[i][i]
            if pivot == 0:
                for k in range(i + 1, n):
                    if aug[k][i] != 0:
                        aug[i], aug[k] = (aug[k], aug[i])
                        pivot = aug[i][i]
                        break
                if pivot == 0:
                    raise ValueError("Matrix singular during inversion")
            inv_p = 1.0 / pivot
            for j in range(2 * n):
                aug[i][j] *= inv_p
            for r in range(n):
                if r == i:
                    continue
                factor = aug[r][i]
                if factor != 0:
                    for c in range(2 * n):
                        aug[r][c] -= factor * aug[i][c]
        return [row[n:] for row in aug]

    def _ensure_arm(self, arm: str) -> _ArmCtx:
        ctx = self._arms.get(arm)
        if ctx is None:
            ctx = _ArmCtx(A=self._identity(), b=[0.0] * self._d, A_inv=self._identity())
            self._arms[arm] = ctx
        return ctx

    def select(self, arms: Sequence[str], features: Sequence[float]) -> str:
        if not _ctx_flag():
            return arms[0]
        if not arms:
            raise ValueError("No arms provided")
        if len(features) != self._d:
            raise ValueError("Feature dimension mismatch")
        x = list(features)
        best_score = -float("inf")
        best_arm = arms[0]
        with self._lock:
            for arm in arms:
                ctx = self._ensure_arm(arm)
                A_inv = ctx.A_inv if ctx.A_inv is not None else self._mat_inv(ctx.A)
                if ctx.A_inv is None:
                    ctx.A_inv = [row[:] for row in A_inv]
                theta = self._mat_vec(A_inv, ctx.b)
                mean = sum(theta[i] * x[i] for i in range(self._d))
                Ax = self._mat_vec(A_inv, x)
                conf = math.sqrt(max(0.0, sum(x[i] * Ax[i] for i in range(self._d))))
                score = mean + self._alpha * conf
                if score > best_score:
                    best_score = score
                    best_arm = arm
        if self._sel_counter:
            with contextlib.suppress(Exception):
                self._sel_counter.inc(1)
        return best_arm

    def update(self, arm: str, reward: float, features: Sequence[float]) -> None:
        if not _ctx_flag():
            return
        if len(features) != self._d:
            raise ValueError("Feature dimension mismatch")
        r = max(0.0, min(1.0, float(reward)))
        x = list(features)
        with self._lock:
            ctx = self._ensure_arm(arm)
            if ctx.A_inv is None:
                ctx.A_inv = self._mat_inv(ctx.A)
            A_inv = ctx.A_inv
            self._vec_outer_add(ctx.A, x)
            Avx = self._mat_vec(A_inv, x)
            denom = 1.0 + sum(x[i] * Avx[i] for i in range(self._d))
            if denom <= 0:
                ctx.A_inv = self._mat_inv(ctx.A)
            else:
                for i in range(self._d):
                    for j in range(self._d):
                        A_inv[i][j] -= Avx[i] * Avx[j] / denom
            for i in range(self._d):
                ctx.b[i] += r * x[i]
            ctx.updates += 1
            if self._recompute_interval > 0 and ctx.updates % self._recompute_interval == 0:
                ctx.A_inv = self._mat_inv(ctx.A)
                if self._recompute_counter:
                    with contextlib.suppress(Exception):
                        self._recompute_counter.inc(1)
            if self._cond_gauge:
                with contextlib.suppress(Exception):
                    norm_A = max(sum(abs(v) for v in row) for row in ctx.A)
                    inv = ctx.A_inv or self._mat_inv(ctx.A)
                    norm_A_inv = max(sum(abs(v) for v in row) for row in inv)
                    cond_est = norm_A * norm_A_inv
                    with contextlib.suppress(Exception):
                        self._cond_gauge.set(cond_est)
                    if self._cond_threshold > 0 and cond_est > self._cond_threshold:
                        ctx.A_inv = self._mat_inv(ctx.A)
                        if self._recompute_counter:
                            with contextlib.suppress(Exception):
                                self._recompute_counter.inc(1)
        if self._update_counter:
            with contextlib.suppress(Exception):
                self._update_counter.inc(1)
        if self._persist_enabled:
            with contextlib.suppress(Exception):
                self._save_state()

    def select_with_score(self, arms: Sequence[str], features: Sequence[float]) -> tuple[str, float]:
        chosen = self.select(arms, features)
        if not _ctx_flag():
            return (chosen, 0.0)
        x = list(features)
        with self._lock:
            ctx = self._ensure_arm(chosen)
            A_inv = self._mat_inv(ctx.A)
            theta = self._mat_vec(A_inv, ctx.b)
            mean = sum(theta[i] * x[i] for i in range(self._d))
            Ax = self._mat_vec(A_inv, x)
            conf = math.sqrt(max(0.0, sum(x[i] * Ax[i] for i in range(self._d))))
            score = mean + self._alpha * conf
        return (chosen, score)

    def arms(self) -> list[str]:
        with self._lock:
            return list(self._arms.keys())

    def _state_path(self) -> str:
        return os.path.join(self._state_dir, f"linucb_d{self._d}.json")

    def _serialize(self) -> dict[str, dict[str, list[list[float]] | list[float]]]:
        with self._lock:
            return {arm: {"A": ctx.A, "b": ctx.b} for arm, ctx in self._arms.items()}

    def _apply(self, data: object) -> None:
        if not isinstance(data, dict):
            return
        with self._lock:
            for arm, payload in data.items():
                if not isinstance(payload, dict):
                    continue
                A = payload.get("A")
                b = payload.get("b")
                if (
                    isinstance(A, list)
                    and isinstance(b, list)
                    and (len(A) == self._d)
                    and all(isinstance(row, list) and len(row) == self._d for row in A)
                    and (len(b) == self._d)
                ):
                    self._arms[arm] = _ArmCtx(A=[row[:] for row in A], b=list(b), A_inv=None)
        with self._lock:
            for ctx in self._arms.values():
                try:
                    ctx.A_inv = self._mat_inv(ctx.A)
                except Exception:
                    ctx.A_inv = None

    def _load_state(self) -> None:
        if not self._persist_enabled:
            return
        path = self._state_path()
        if not os.path.isfile(path):
            return
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        self._apply(raw)

    def _save_state(self) -> None:
        if not self._persist_enabled:
            return
        os.makedirs(self._state_dir, exist_ok=True)
        tmp = self._state_path() + ".tmp"
        data = self._serialize()
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, separators=(",", ":"))
        os.replace(tmp, self._state_path())


__all__ = ["LinUCBRouter"]
