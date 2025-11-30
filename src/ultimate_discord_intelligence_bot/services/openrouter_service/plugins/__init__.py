"""Bandit plugin protocols and implementations.

Extracted from legacy routing modules for better consolidation.
"""

from __future__ import annotations

import contextlib
import logging
import math
import os
import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol, cast

import numpy as np


logger = logging.getLogger(__name__)

# Try to import metrics, but fail gracefully if not available (e.g. in tests)
try:
    from ultimate_discord_intelligence_bot.obs.metrics import get_metrics as _gm
    _real_get_metrics = _gm
except ImportError:
    _real_get_metrics = None


def _obtain_metrics():
    if _real_get_metrics:
        try:
            return _real_get_metrics()
        except Exception:
            pass
    return None


class BanditPlugin(Protocol):
    """Protocol for bandit routing plugins."""

    def select_model(self, candidates: list[str], context: dict[str, Any]) -> str:
        """Select a model from candidates based on context."""
        ...

    def record_outcome(self, model: str, reward: float, context: dict[str, Any]) -> None:
        """Record the outcome of a selection to update internal state."""
        ...

    def select_action(self, context: dict[str, Any], actions: list[str]) -> str:
        """Alias for select_model (legacy compatibility)."""
        ...

    def update(self, context: dict[str, Any], action: str, reward: float) -> None:
        """Alias for record_outcome (legacy compatibility)."""
        ...


@dataclass
class _ArmCtx:
    """Context for a single arm in LinUCB."""
    A: list[list[float]]
    b: list[float]
    A_inv: list[list[float]] | None = None
    updates: int = 0


class LinUCBPlugin:
    """LinUCB (Linear Upper Confidence Bound) bandit implementation.

    Derived from src/platform/llm/routing/bandits/linucb_router.py
    """

    def __init__(self, dimension: int = 10, alpha: float = 1.0) -> None:
        if dimension <= 0:
            raise ValueError("dimension must be positive")
        self._d = dimension
        self._alpha = alpha
        self._arms: dict[str, _ArmCtx] = {}
        self._metrics = _obtain_metrics()
        self._feature_extractor = self._default_feature_extractor

        # Metrics setup
        if self._metrics:
            self._sel_counter = self._metrics.counter(
                name="linucb_selections_total", description="Total LinUCB selections per arm"
            )
            self._update_counter = self._metrics.counter(
                name="linucb_updates_total", description="Total LinUCB updates per arm"
            )
        else:
            self._sel_counter = None
            self._update_counter = None

    def _default_feature_extractor(self, context: dict[str, Any]) -> list[float]:
        """Simple default feature extractor if none provided."""
        # Simple hashing of context keys/values into fixed dimension
        features = [0.0] * self._d
        try:
            for i, (k, v) in enumerate(context.items()):
                idx = hash(k) % self._d
                val = 1.0
                if isinstance(v, (int, float)):
                    val = float(v)
                elif isinstance(v, str):
                    val = float(hash(v) % 100) / 100.0
                features[idx] += val

            # Normalize
            norm = math.sqrt(sum(f*f for f in features))
            if norm > 0:
                features = [f/norm for f in features]
            else:
                features[0] = 1.0 # Bias term

        except Exception:
            features[0] = 1.0 # Fallback

        return features

    def set_feature_extractor(self, extractor):
        """Set a custom feature extractor function."""
        self._feature_extractor = extractor

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
                # Find non-zero pivot
                for k in range(i + 1, n):
                    if aug[k][i] != 0:
                        aug[i], aug[k] = (aug[k], aug[i])
                        pivot = aug[i][i]
                        break
                if pivot == 0:
                    # Matrix singular, return identity as fallback
                    return self._identity()
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

    def select_model(self, candidates: list[str], context: dict[str, Any]) -> str:
        if not candidates:
            return "default"

        features = self._feature_extractor(context)
        if len(features) != self._d:
            # Resize features if dimension mismatch
            features = (features + [0.0] * self._d)[:self._d]

        x = list(features)
        best_score = -float("inf")
        best_arm = candidates[0]

        for arm in candidates:
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

    def record_outcome(self, model: str, reward: float, context: dict[str, Any]) -> None:
        features = self._feature_extractor(context)
        if len(features) != self._d:
             features = (features + [0.0] * self._d)[:self._d]

        r = max(0.0, min(1.0, float(reward)))
        x = list(features)

        ctx = self._ensure_arm(model)
        if ctx.A_inv is None:
            ctx.A_inv = self._mat_inv(ctx.A)
        A_inv = ctx.A_inv

        self._vec_outer_add(ctx.A, x)

        # Sherman-Morrison update for A_inv
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

        if self._update_counter:
            with contextlib.suppress(Exception):
                self._update_counter.inc(1)

    # Aliases
    select_action = select_model
    update = record_outcome


@dataclass
class BetaPosterior:
    """Beta distribution posterior for Thompson Sampling."""
    alpha: float = 1.0
    beta: float = 1.0
    trials: int = 0

    def sample(self) -> float:
        return np.random.beta(self.alpha, self.beta)

    def update(self, reward: float) -> None:
        self.alpha += reward
        self.beta += 1.0 - reward
        self.trials += 1

    def mean(self) -> float:
        return self.alpha / (self.alpha + self.beta)


class ThompsonSamplingPlugin:
    """Thompson Sampling router plugin.

    Derived from src/platform/llm/routing/bandits/thompson_sampling_router.py
    """

    def __init__(self, cold_start_trials: int = 5) -> None:
        self.cold_start_trials = cold_start_trials
        self._posteriors: dict[str, dict[str, BetaPosterior]] = {}
        self._metrics = _obtain_metrics()

    def select_model(self, candidates: list[str], context: dict[str, Any]) -> str:
        if not candidates:
            return "default"

        task_name = str(context.get("task", "default"))

        if task_name not in self._posteriors:
            self._posteriors[task_name] = {}
        posteriors = self._posteriors[task_name]

        for model in candidates:
            if model not in posteriors:
                posteriors[model] = BetaPosterior()

        total_trials = sum(p.trials for p in posteriors.values())

        if total_trials < self.cold_start_trials:
             # Random exploration
             selected = np.random.choice(candidates)
        else:
             # Thompson sampling
             samples = {model: posteriors[model].sample() for model in candidates}
             selected = max(samples, key=samples.get)

        if self._metrics:
            try:
                self._metrics.counter(
                   "ts_selections_total",
                   labels={"task": task_name, "model": selected}
                ).inc(1)
            except Exception:
                pass

        return selected

    def record_outcome(self, model: str, reward: float, context: dict[str, Any]) -> None:
        task_name = str(context.get("task", "default"))
        reward = max(0.0, min(1.0, reward))

        if task_name not in self._posteriors:
            self._posteriors[task_name] = {}

        if model not in self._posteriors[task_name]:
            self._posteriors[task_name][model] = BetaPosterior()

        self._posteriors[task_name][model].update(reward)

    # Aliases
    select_action = select_model
    update = record_outcome


# Re-export or alias EnhancedLinUCBPlugin from legacy if needed, or implement it here
# For now, we alias LinUCBPlugin as EnhancedLinUCBPlugin for compatibility with adaptive_routing.py
EnhancedLinUCBPlugin = LinUCBPlugin

# Placeholder for DoublyRobustPlugin
class DoublyRobustPlugin:
    def __init__(self, num_actions: int = 20, context_dim: int = 10, alpha: float = 1.5):
        self._linucb = LinUCBPlugin(dimension=context_dim, alpha=alpha)

    def select_model(self, candidates: list[str], context: dict[str, Any]) -> str:
        return self._linucb.select_model(candidates, context)

    def record_outcome(self, model: str, reward: float, context: dict[str, Any]) -> None:
        self._linucb.record_outcome(model, reward, context)

    # Aliases
    select_action = select_model
    update = record_outcome


__all__ = [
    "BanditPlugin",
    "LinUCBPlugin",
    "ThompsonSamplingPlugin",
    "EnhancedLinUCBPlugin",
    "DoublyRobustPlugin"
]
