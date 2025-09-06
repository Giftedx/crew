"""Lightweight diagonal LinUCB policy.

Avoids heavy numeric deps by approximating LinUCB with a diagonal covariance
matrix. Uses a fixed-size context feature vector built from the provided
dictionary (bias + first few numeric/string-derived features).
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any


def _ctx_vector(ctx: dict[str, Any], dim: int = 8) -> list[float]:
    # bias + up to dim-1 features
    feats: list[float] = [1.0]
    for k in sorted(ctx.keys()):
        if len(feats) >= dim:
            break
        v = ctx[k]
        if isinstance(v, int | float):
            feats.append(float(v))
        elif isinstance(v, str):
            # simple hashed feature
            feats.append(float(abs(hash(v)) % 1000) / 1000.0)
        else:
            feats.append(0.0)
    while len(feats) < dim:
        feats.append(0.0)
    return feats


@dataclass
class LinUCBDiagBandit:
    alpha: float = 1.0
    dim: int = 8
    # Per-arm state
    # Diagonal A (variance) initialised to 1s; b accumulates rewards * x
    A_diag: defaultdict[Any, list[float]] = field(default_factory=lambda: defaultdict(lambda: [1.0] * 8))
    b_vec: defaultdict[Any, list[float]] = field(default_factory=lambda: defaultdict(lambda: [0.0] * 8))
    # For compatibility with LearningEngine snapshot/status
    q_values: defaultdict[Any, float] = field(default_factory=lambda: defaultdict(float))
    counts: defaultdict[Any, int] = field(default_factory=lambda: defaultdict(int))

    def recommend(self, context: dict[str, Any], candidates: Sequence[Any]) -> Any:
        if not candidates:
            raise ValueError("candidates must not be empty")
        x = _ctx_vector(context, self.dim)
        best = None
        best_p = float("-inf")
        for a in candidates:
            A = self.A_diag[a]
            b = self.b_vec[a]
            # theta = A^{-1} b (diagonal inverse)
            theta = [b[i] / A[i] for i in range(self.dim)]
            # p = x^T theta + alpha * sqrt(x^T A^{-1} x)
            x_dot_theta = sum(x[i] * theta[i] for i in range(self.dim))
            conf = (sum((x[i] ** 2) / max(A[i], 1e-9) for i in range(self.dim))) ** 0.5
            p = x_dot_theta + self.alpha * conf
            if p > best_p:
                best_p = p
                best = a
        return best

    def update(self, action: Any, reward: float, context: dict[str, Any]) -> None:
        x = _ctx_vector(context, self.dim)
        A = self.A_diag[action]
        b = self.b_vec[action]
        # A += x*x (diagonal only)
        for i in range(self.dim):
            A[i] += x[i] * x[i]
            b[i] += reward * x[i]
        self.counts[action] += 1
        n = self.counts[action]
        q = self.q_values[action]
        self.q_values[action] = q + (reward - q) / n

__all__ = ["LinUCBDiagBandit"]

