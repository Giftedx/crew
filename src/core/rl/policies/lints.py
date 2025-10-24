"""Diagonal Linear Thompson Sampling policy.

Lightweight implementation mirroring the structure of :mod:`linucb` but using
Gaussian sampling for exploration. We maintain per-arm diagonal precision
matrix (A) and reward-weighted feature sum (b). Posterior over weights θ is
approximated as Normal( A^{-1} b, sigma^2 A^{-1} ). For simplicity we treat
``sigma`` (observation noise std) as a tunable scalar and avoid full Bayesian
hyperparameter updates.

This keeps dependencies minimal (no numpy) while providing contextual
exploration that typically outperforms epsilon-greedy / UCB1 in moderately
structured feature spaces when feature dimension is small (<= 16).
"""

from __future__ import annotations

import contextlib
import math
import random
from collections import defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from collections.abc import Sequence


def _ctx_vector(ctx: dict[str, Any], dim: int = 8) -> list[float]:
    feats: list[float] = [1.0]
    for k in sorted(ctx.keys()):
        if len(feats) >= dim:
            break
        v = ctx[k]
        if isinstance(v, (int, float)):
            feats.append(float(v))
        elif isinstance(v, str):
            feats.append(float(abs(hash(v)) % 1000) / 1000.0)
        else:
            feats.append(0.0)
    while len(feats) < dim:
        feats.append(0.0)
    return feats


@dataclass
class LinTSDiagBandit:
    dim: int = 8
    sigma: float = 0.5  # observation noise std (scales posterior sampling)
    prior_scale: float = 1.0  # initial diagonal prior precision
    rng: random.Random | None = None

    A_diag: defaultdict[Any, list[float]] = field(
        default_factory=lambda: defaultdict(lambda: [1.0] * 8)
    )  # precision diagonal (starts at 1/prior_scale but simplified here)
    b_vec: defaultdict[Any, list[float]] = field(default_factory=lambda: defaultdict(lambda: [0.0] * 8))
    q_values: defaultdict[Any, float] = field(default_factory=lambda: defaultdict(float))
    counts: defaultdict[Any, int] = field(default_factory=lambda: defaultdict(int))

    def _sample_theta(self, A: list[float], b: list[float]) -> list[float]:
        theta_mean = [b[i] / max(A[i], 1e-9) for i in range(self.dim)]
        # variance for each dimension ~ sigma^2 / A[i]
        _rng = self.rng or random
        return [
            theta_mean[i] + (self.sigma / math.sqrt(max(A[i], 1e-9))) * _rng.gauss(0.0, 1.0) for i in range(self.dim)
        ]

    def recommend(self, context: dict[str, Any], candidates: Sequence[Any]) -> Any:
        if not candidates:
            raise ValueError("candidates must not be empty")
        x = _ctx_vector(context, self.dim)
        best = None
        best_score = float("-inf")
        for a in candidates:
            A = self.A_diag[a]
            b = self.b_vec[a]
            theta = self._sample_theta(A, b)
            score = sum(x[i] * theta[i] for i in range(self.dim))
            if score > best_score:
                best_score = score
                best = a
        return best

    def update(self, action: Any, reward: float, context: dict[str, Any]) -> None:
        x = _ctx_vector(context, self.dim)
        A = self.A_diag[action]
        b = self.b_vec[action]
        for i in range(self.dim):
            A[i] += x[i] * x[i]
            b[i] += reward * x[i]
        self.counts[action] += 1
        n = self.counts[action]
        q = self.q_values[action]
        self.q_values[action] = q + (reward - q) / n

    # ---------------- serialization helpers -----------------
    def state_dict(self) -> dict[str, Any]:
        return {
            "policy": self.__class__.__name__,
            "version": 1,
            "dim": int(self.dim),
            "sigma": float(self.sigma),
            "A_diag": {k: list(v) for k, v in self.A_diag.items()},
            "b_vec": {k: list(v) for k, v in self.b_vec.items()},
            "q_values": dict(self.q_values),
            "counts": dict(self.counts),
        }

    def load_state(self, state: dict[str, Any]) -> None:
        ver = state.get("version")
        if ver is not None and ver > 1:
            return
        with contextlib.suppress(Exception):
            self.dim = int(state.get("dim", self.dim))
        with contextlib.suppress(Exception):
            self.sigma = float(state.get("sigma", self.sigma))

        def _mk_A_default() -> list[float]:
            return [1.0] * self.dim

        def _mk_b_default() -> list[float]:
            return [0.0] * self.dim

        A_in = state.get("A_diag") or {}
        b_in = state.get("b_vec") or {}
        self.A_diag = defaultdict(_mk_A_default)
        for k, vec in A_in.items():
            arr = list(vec)
            if len(arr) < self.dim:
                arr += [1.0] * (self.dim - len(arr))
            elif len(arr) > self.dim:
                arr = arr[: self.dim]
            self.A_diag[k] = arr
        self.b_vec = defaultdict(_mk_b_default)
        for k, vec in b_in.items():
            arr = list(vec)
            if len(arr) < self.dim:
                arr += [0.0] * (self.dim - len(arr))
            elif len(arr) > self.dim:
                arr = arr[: self.dim]
            self.b_vec[k] = arr
        self.q_values.clear()
        self.q_values.update(state.get("q_values") or {})
        self.counts.clear()
        self.counts.update(state.get("counts") or {})


__all__ = ["LinTSDiagBandit"]
