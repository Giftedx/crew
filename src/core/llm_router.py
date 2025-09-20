"""LLM Router integrating bandit selection over multiple LLMClient instances.

Feature flag: ENABLE_BANDIT_ROUTING=1 (same flag used by ThompsonBanditRouter).

Usage:
    router = LLMRouter({"gpt4": client4, "haiku": client_haiku})
    result = router.chat(messages)

Reward Feedback:
    After obtaining a result and computing a quality/cost metric, call
        router.update(model_name, reward)
    so the bandit posterior incorporates feedback.
"""

from __future__ import annotations

import math
import os
from collections.abc import Sequence
from typing import Any

from ai.routing.bandit_router import ThompsonBanditRouter
from ai.routing.linucb_router import LinUCBRouter
from ai.routing.router_registry import RewardNormalizer, get_tenant_router, record_selection

from core.llm_client import LLMCallResult, LLMClient

try:  # metrics optional
    from ultimate_discord_intelligence_bot.obs.metrics import get_metrics as _gm

    def _obtain_metrics() -> Any | None:
        try:
            return _gm()
        except Exception:  # pragma: no cover
            return None
except Exception:  # pragma: no cover

    def _obtain_metrics() -> Any | None:
        return None


class LLMRouter:
    def __init__(self, clients: dict[str, LLMClient]):
        if not clients:
            raise ValueError("At least one client required")
        self._clients = clients
        self._tenant_mode = os.getenv("ENABLE_BANDIT_TENANT", "0").lower() in {"1", "true", "yes", "on"}
        self._contextual_enabled = os.getenv("ENABLE_CONTEXTUAL_BANDIT", "0").lower() in {"1", "true", "yes", "on"}
        self._linucb_dimension = int(os.getenv("LINUCB_DIMENSION", "0") or 0)
        self._hybrid_enabled = os.getenv("ENABLE_CONTEXTUAL_HYBRID", "1").lower() in {"1", "true", "yes", "on"}
        # Feature quality gating configuration
        self._feature_quality_min = float(os.getenv("FEATURE_QUALITY_MIN", "0.5") or 0.5)
        self._feature_min_norm = float(os.getenv("FEATURE_MIN_NORM", "0.0") or 0.0)
        self._feature_max_norm = float(os.getenv("FEATURE_MAX_NORM", "10.0") or 10.0)
        if self._contextual_enabled:
            if self._linucb_dimension <= 0:
                raise ValueError("LINUCB_DIMENSION must be > 0 when ENABLE_CONTEXTUAL_BANDIT=1")
            self._ctx_router: LinUCBRouter | None = LinUCBRouter(dimension=self._linucb_dimension)
            # In pure contextual mode we could disable classic bandit; for hybrid we keep one for fallback
            self._bandit = get_tenant_router() if self._tenant_mode else ThompsonBanditRouter()
        else:
            self._ctx_router = None
            self._bandit = get_tenant_router() if self._tenant_mode else ThompsonBanditRouter()
        self._reward_normalizer = RewardNormalizer()
        self._metrics = _obtain_metrics()
        if self._metrics:
            m = self._metrics
            self._chat_counter = m.counter("llm_router_chats_total")
            self._fallback_counter = m.counter("llm_router_fallback_total")
            self._feature_quality_gauge = m.gauge("linucb_feature_quality")
        else:  # pragma: no cover
            self._chat_counter = None
            self._fallback_counter = None
            self._feature_quality_gauge = None

    # ---------------------- Feature Quality Scoring ----------------------
    def _feature_quality(self, features: Sequence[float] | None) -> float:
        """Return a heuristic feature quality score in [0,1]. Higher is better.

        Heuristics:
          - None or dimension mismatch => 0.0
          - NaN/inf values apply 0.3 penalty (score *= 0.7)
          - Vector L2 norm outside [min_norm, max_norm] scaled penalty up to 0.5
        """
        if features is None:
            return 0.0
        try:
            if len(features) != self._linucb_dimension:
                return 0.0
        except Exception:
            return 0.0
        # base score
        score = 1.0
        # numeric validation
        bad_numeric = False
        norm_sq = 0.0
        for v in features:
            if not isinstance(v, (int, float)) or math.isinf(v) or math.isnan(v):
                bad_numeric = True
                # Skip contribution to norm if non-finite or non-numeric
                continue
            norm_sq += float(v) * float(v)
        if bad_numeric:
            score *= 0.7  # 30% penalty
        l2 = norm_sq**0.5
        if l2 < self._feature_min_norm:
            # scale penalty by distance relative to min_norm (avoid divide by zero)
            span = max(1e-9, self._feature_min_norm)
            ratio = min(1.0, (self._feature_min_norm - l2) / span)
            score *= 1 - 0.5 * ratio
        elif l2 > self._feature_max_norm:
            span = max(1e-9, self._feature_max_norm)
            ratio = min(1.0, (l2 - self._feature_max_norm) / span)
            score *= 1 - 0.5 * ratio
        # clamp
        return max(0.0, min(1.0, score))

    def chat(self, messages: Sequence[dict[str, Any]]) -> tuple[str, LLMCallResult]:
        if self._contextual_enabled:
            # Instead of raising, gracefully fallback to classical bandit to support tenants that
            # toggle contextual flag globally but still invoke legacy chat paths without features.
            # This preserves backward compatibility for non-contextual usage.
            pass
        model_names = list(self._clients.keys())
        selected = self._bandit.select(model_names)
        result = self._clients[selected].chat(messages)
        if self._chat_counter:
            try:
                self._chat_counter.inc(1)
            except Exception:  # pragma: no cover
                pass
        if self._tenant_mode:
            record_selection(selected)
        return selected, result

    def update(self, model_name: str, reward: float) -> None:
        if model_name not in self._clients:
            return
        if self._contextual_enabled:
            # Graceful fallback: allow classical bandit update so legacy reward feedback still works.
            pass
        self._bandit.update(model_name, reward)

    def chat_and_update(
        self,
        messages: Sequence[dict[str, Any]],
        quality: float,
        latency_ms: float,
        cost: float,
    ) -> tuple[str, LLMCallResult, float]:
        """Convenience wrapper: route, invoke, normalize reward, update bandit.

        Returns (model_name, result, reward).
        """
        # In earlier versions this raised when contextual routing was enabled.
        # For backward compatibility we now gracefully fall back to classical
        # Thompson sampling when callers (legacy code/tests) invoke this path
        # with contextual mode toggled on but without feature vectors.
        # This mirrors the fallback already implemented in chat()/update().
        model, result = self.chat(messages)
        reward = self._reward_normalizer.compute(quality=quality, latency_ms=latency_ms, cost=cost)
        self.update(model, reward)
        return model, result, reward

    # ---------------------- Contextual Mode APIs ----------------------
    def chat_with_features(
        self, messages: Sequence[dict[str, Any]], features: Sequence[float]
    ) -> tuple[str, LLMCallResult]:
        if not self._contextual_enabled:
            raise RuntimeError("Contextual mode not enabled")
        # Determine initial contextual viability (length + presence) without mutating later to appease type checkers.
        use_contextual = bool(
            self._hybrid_enabled
            and features is not None
            and isinstance(features, Sequence)
            and len(features) == self._linucb_dimension
        )
        effective_contextual = False
        if use_contextual:
            fq = self._feature_quality(features)
            if self._feature_quality_gauge:
                try:
                    self._feature_quality_gauge.set(fq)
                except Exception:  # pragma: no cover
                    pass
            below = fq < self._feature_quality_min and self._hybrid_enabled
            effective_contextual = not below
        if effective_contextual:
            model_names = list(self._clients.keys())
            assert self._ctx_router is not None
            selected = self._ctx_router.select(model_names, features)
            result = self._clients[selected].chat(messages)
        else:
            model_names = list(self._clients.keys())
            selected = self._bandit.select(model_names)
            result = self._clients[selected].chat(messages)
            if self._fallback_counter:
                try:
                    self._fallback_counter.inc(1)
                except Exception:  # pragma: no cover
                    pass
        if self._chat_counter:
            try:
                self._chat_counter.inc(1)
            except Exception:  # pragma: no cover
                pass
        if self._tenant_mode:
            record_selection(selected)
        return selected, result

    def update_with_features(self, model_name: str, reward: float, features: Sequence[float]) -> None:
        if not self._contextual_enabled:
            raise RuntimeError("Contextual mode not enabled")
        if model_name not in self._clients:
            return
        # Hybrid: if features malformed or dimension mismatch, update classic bandit instead
        if self._hybrid_enabled:
            use_contextual = True
            try:
                if features is None or len(features) != self._linucb_dimension:
                    use_contextual = False
            except Exception:
                use_contextual = False
            # apply quality gate
            if use_contextual:
                fq = self._feature_quality(features)
                if self._feature_quality_gauge:
                    try:
                        self._feature_quality_gauge.set(fq)
                    except Exception:  # pragma: no cover
                        pass
                if fq < self._feature_quality_min:
                    use_contextual = False
            if use_contextual:
                assert self._ctx_router is not None
                self._ctx_router.update(model_name, reward, features)
            else:
                self._bandit.update(model_name, reward)
                if self._fallback_counter:
                    try:
                        self._fallback_counter.inc(1)
                    except Exception:  # pragma: no cover
                        pass
        else:
            assert self._ctx_router is not None
            self._ctx_router.update(model_name, reward, features)

    def chat_with_features_and_update(
        self,
        messages: Sequence[dict[str, Any]],
        features: Sequence[float],
        quality: float,
        latency_ms: float,
        cost: float,
    ) -> tuple[str, LLMCallResult, float]:
        if not self._contextual_enabled:
            raise RuntimeError("Contextual mode not enabled")
        model, result = self.chat_with_features(messages, features)
        reward = self._reward_normalizer.compute(quality=quality, latency_ms=latency_ms, cost=cost)
        self.update_with_features(model, reward, features)
        return model, result, reward


__all__ = ["LLMRouter"]
