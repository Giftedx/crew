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

    # -------------------- optional serialization helpers --------------------
    def state_dict(self) -> dict[str, Any]:
        """Return a serialisable snapshot of LinUCB state."""
        return {
            "policy": self.__class__.__name__,
            "version": 1,
            "alpha": float(self.alpha),
            "dim": int(self.dim),
            "A_diag": {k: list(v) for k, v in self.A_diag.items()},
            "b_vec": {k: list(v) for k, v in self.b_vec.items()},
            "q_values": dict(self.q_values),
            "counts": dict(self.counts),
        }

    def load_state(self, state: dict[str, Any]) -> None:
        """Load state previously produced by :meth:`state_dict`.

        Handles dimension changes by rebuilding default factories to match
        the stored ``dim`` and padding/truncating vectors as needed.
        """
        ver = state.get("version")
        if ver is not None and ver > 1:
            return
        try:
            self.alpha = float(state.get("alpha", self.alpha))
        except Exception:
            pass
        dim_val = state.get("dim", self.dim)
        try:
            self.dim = int(dim_val)
        except Exception:
            self.dim = self.dim

        # Rebuild default dicts with factories that reflect current dim
        def _mk_A_default() -> list[float]:
            return [1.0] * self.dim

        def _mk_b_default() -> list[float]:
            return [0.0] * self.dim

        A_in = state.get("A_diag") or {}
        b_in = state.get("b_vec") or {}

        self.A_diag = defaultdict(_mk_A_default)
        for k, vec in A_in.items():
            lst = list(vec)
            # Adjust length to dim
            if len(lst) < self.dim:
                lst = lst + [1.0] * (self.dim - len(lst))
            elif len(lst) > self.dim:
                lst = lst[: self.dim]
            self.A_diag[k] = lst

        self.b_vec = defaultdict(_mk_b_default)
        for k, vec in b_in.items():
            lst = list(vec)
            if len(lst) < self.dim:
                lst = lst + [0.0] * (self.dim - len(lst))
            elif len(lst) > self.dim:
                lst = lst[: self.dim]
            self.b_vec[k] = lst

        # Scalars
        qv = state.get("q_values") or {}
        ct = state.get("counts") or {}
        self.q_values.clear()
        self.q_values.update(qv)
        self.counts.clear()
        self.counts.update(ct)


__all__ = ["LinUCBDiagBandit"]
