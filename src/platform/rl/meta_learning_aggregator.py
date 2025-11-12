"""Cross-tenant meta-learning for global parameter sharing.

Aggregates learned parameters (bandit posteriors, model weights, agent performance)
across tenants with differential privacy for collective intelligence.
"""

from __future__ import annotations

import contextlib
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

import numpy as np

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics


if TYPE_CHECKING:
    from collections.abc import Sequence
logger = logging.getLogger(__name__)


@dataclass
class GlobalParameters:
    """Global aggregated parameters for meta-learning."""

    agent_context_weights: dict[str, float] | None = None
    agent_performance_priors: dict[str, tuple[float, float]] | None = None
    tool_context_weights: dict[str, float] | None = None
    tool_performance_priors: dict[str, tuple[float, float]] | None = None
    model_posteriors: dict[str, tuple[float, float]] | None = None
    aggregated_from_tenants: list[str] | None = None
    last_sync: datetime | None = None
    total_observations: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        data = asdict(self)
        if self.last_sync:
            data["last_sync"] = self.last_sync.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GlobalParameters:
        """Deserialize from dict."""
        data = dict(data)
        if "last_sync" in data and isinstance(data["last_sync"], str):
            data["last_sync"] = datetime.fromisoformat(data["last_sync"])
        return cls(**data)


class MetaLearningAggregator:
    """Aggregate learning across tenants for collective intelligence.

    Implements federated learning with differential privacy to enable
    cross-tenant knowledge sharing while protecting individual tenant data.
    """

    def __init__(
        self,
        *,
        redis_client: Any = None,
        epsilon: float = 1.0,
        enable_differential_privacy: bool = True,
        sync_interval_seconds: int = 300,
    ):
        """Initialize meta-learning aggregator.

        Args:
            redis_client: Redis client for parameter storage.
            epsilon: Privacy budget for differential privacy (lower = more private).
            enable_differential_privacy: Apply DP noise before aggregation.
            sync_interval_seconds: How often to sync global parameters.
        """
        from platform.config.configuration import get_config

        config = get_config()
        self._redis_client = redis_client
        self.epsilon = epsilon
        self.enable_differential_privacy = enable_differential_privacy
        self.sync_interval_seconds = sync_interval_seconds
        self._metrics = get_metrics()
        if self._redis_client is None:
            try:
                import redis

                redis_url = getattr(config, "redis_url", "redis://redis:6379")
                self._redis_client = redis.from_url(redis_url, decode_responses=True)
                logger.info(f"Connected to Redis for meta-learning at {redis_url}")
            except Exception as e:
                logger.warning(f"Failed to initialize Redis for meta-learning: {e}")

    def _apply_differential_privacy(self, value: float, sensitivity: float = 1.0) -> float:
        """Apply Laplace noise for differential privacy.

        Args:
            value: Original value to protect.
            sensitivity: Query sensitivity (how much one record can change result).

        Returns:
            Noisy value with DP guarantee.
        """
        if not self.enable_differential_privacy:
            return value
        scale = sensitivity / self.epsilon
        noise = np.random.laplace(0, scale)
        return value + noise

    def aggregate_agent_routing_params(self, tenant_ids: Sequence[str] | None = None) -> GlobalParameters:
        """Aggregate agent routing bandit parameters across tenants.

        Args:
            tenant_ids: Specific tenants to aggregate from (None = all tenants).

        Returns:
            GlobalParameters with aggregated context weights and priors.
        """
        if self._redis_client is None:
            logger.warning("Redis client not available - cannot aggregate parameters")
            return GlobalParameters()
        try:
            if tenant_ids is None:
                pattern = "bandit:agent_routing:*:state"
                cursor = 0
                tenant_keys: list[str] = []
                while True:
                    cursor, keys = self._redis_client.scan(cursor, match=pattern, count=100)
                    tenant_keys.extend(keys)
                    if cursor == 0:
                        break
            else:
                tenant_keys = [f"bandit:agent_routing:{tid}:state" for tid in tenant_ids]
            context_weights_sum: dict[str, float] = {}
            context_weights_count: dict[str, int] = {}
            agent_performance_sum: dict[str, tuple[float, float]] = {}
            agent_performance_count: dict[str, int] = {}
            aggregated_tenants: list[str] = []
            total_obs = 0
            for key in tenant_keys:
                try:
                    state_json = self._redis_client.get(key)
                    if not state_json:
                        continue
                    state = json.loads(state_json)
                    tenant_id = key.split(":")[2] if len(key.split(":")) >= 3 else "unknown"
                    aggregated_tenants.append(tenant_id)
                    if "context_weights" in state:
                        weights = state["context_weights"]
                        for feature, weight in weights.items():
                            noisy_weight = self._apply_differential_privacy(weight, sensitivity=1.0)
                            context_weights_sum[feature] = context_weights_sum.get(feature, 0.0) + noisy_weight
                            context_weights_count[feature] = context_weights_count.get(feature, 0) + 1
                    if "agent_bandits" in state:
                        for agent_id, bandit_state in state["agent_bandits"].items():
                            alpha = bandit_state.get("alpha", 1.0)
                            beta = bandit_state.get("beta", 1.0)
                            noisy_alpha = self._apply_differential_privacy(alpha, sensitivity=10.0)
                            noisy_beta = self._apply_differential_privacy(beta, sensitivity=10.0)
                            if agent_id not in agent_performance_sum:
                                agent_performance_sum[agent_id] = (0.0, 0.0)
                            sum_a, sum_b = agent_performance_sum[agent_id]
                            agent_performance_sum[agent_id] = (sum_a + noisy_alpha, sum_b + noisy_beta)
                            agent_performance_count[agent_id] = agent_performance_count.get(agent_id, 0) + 1
                    total_obs += state.get("total_trials", 0)
                except Exception as e:
                    logger.warning(f"Failed to aggregate from {key}: {e}")
            avg_context_weights = {
                feature: total_weight / context_weights_count[feature]
                for feature, total_weight in context_weights_sum.items()
                if context_weights_count.get(feature, 0) > 0
            }
            avg_agent_priors = {
                agent_id: (
                    agent_performance_sum[agent_id][0] / agent_performance_count[agent_id],
                    agent_performance_sum[agent_id][1] / agent_performance_count[agent_id],
                )
                for agent_id in agent_performance_sum
                if agent_performance_count.get(agent_id, 0) > 0
            }
            global_params = GlobalParameters(
                agent_context_weights=avg_context_weights,
                agent_performance_priors=avg_agent_priors,
                aggregated_from_tenants=aggregated_tenants,
                last_sync=datetime.now(timezone.utc),
                total_observations=total_obs,
            )
            self._store_global_params(global_params)
            self._metrics.counter(
                "meta_learning_aggregations_total",
                labels={"type": "agent_routing", "tenants": str(len(aggregated_tenants))},
            ).inc()
            logger.info(
                f"Aggregated agent routing params from {len(aggregated_tenants)} tenants ({total_obs} observations, {len(avg_context_weights)} context features, {len(avg_agent_priors)} agents)"
            )
            return global_params
        except Exception:
            logger.exception("Failed to aggregate agent routing parameters")
            self._metrics.counter("meta_learning_errors_total", labels={"operation": "aggregate"}).inc()
            return GlobalParameters()

    def _store_global_params(self, params: GlobalParameters) -> None:
        """Store global parameters in Redis."""
        if self._redis_client is None:
            return
        try:
            key = "meta_learning:global_params"
            self._redis_client.set(key, json.dumps(params.to_dict()))
            logger.debug(f"Stored global parameters in {key}")
        except Exception as e:
            logger.warning(f"Failed to store global parameters: {e}")

    def get_global_params(self) -> GlobalParameters | None:
        """Retrieve stored global parameters.

        Returns:
            GlobalParameters if available, None otherwise.
        """
        if self._redis_client is None:
            return None
        try:
            key = "meta_learning:global_params"
            params_json = self._redis_client.get(key)
            if not params_json:
                return None
            params_dict = json.loads(params_json)
            return GlobalParameters.from_dict(params_dict)
        except Exception as e:
            logger.warning(f"Failed to retrieve global parameters: {e}")
            return None

    def aggregate_model_routing_params(self, tenant_ids: Sequence[str] | None = None) -> GlobalParameters:
        """Aggregate Thompson Sampling model routing parameters across tenants.

        Args:
            tenant_ids: Specific tenants to aggregate from (None = all tenants).

        Returns:
            GlobalParameters with aggregated model posteriors.
        """
        if self._redis_client is None:
            return GlobalParameters()
        try:
            if tenant_ids is None:
                pattern = "ts_router:*:state"
                cursor = 0
                tenant_keys: list[str] = []
                while True:
                    cursor, keys = self._redis_client.scan(cursor, match=pattern, count=100)
                    tenant_keys.extend(keys)
                    if cursor == 0:
                        break
            else:
                tenant_keys = [f"ts_router:{tid}:state" for tid in tenant_ids]
            model_posteriors_sum: dict[str, tuple[float, float]] = {}
            model_posteriors_count: dict[str, int] = {}
            aggregated_tenants: list[str] = []
            for key in tenant_keys:
                try:
                    state_json = self._redis_client.get(key)
                    if not state_json:
                        continue
                    state = json.loads(state_json)
                    tenant_id = key.split(":")[1] if len(key.split(":")) >= 2 else "unknown"
                    aggregated_tenants.append(tenant_id)
                    if "posteriors" in state:
                        for model_id, posterior_dict in state["posteriors"].items():
                            alpha = posterior_dict.get("alpha", 1.0)
                            beta = posterior_dict.get("beta", 1.0)
                            noisy_alpha = self._apply_differential_privacy(alpha, sensitivity=5.0)
                            noisy_beta = self._apply_differential_privacy(beta, sensitivity=5.0)
                            if model_id not in model_posteriors_sum:
                                model_posteriors_sum[model_id] = (0.0, 0.0)
                            sum_a, sum_b = model_posteriors_sum[model_id]
                            model_posteriors_sum[model_id] = (sum_a + noisy_alpha, sum_b + noisy_beta)
                            model_posteriors_count[model_id] = model_posteriors_count.get(model_id, 0) + 1
                except Exception as e:
                    logger.warning(f"Failed to aggregate model routing from {key}: {e}")
            avg_posteriors = {
                model_id: (
                    model_posteriors_sum[model_id][0] / model_posteriors_count[model_id],
                    model_posteriors_sum[model_id][1] / model_posteriors_count[model_id],
                )
                for model_id in model_posteriors_sum
                if model_posteriors_count.get(model_id, 0) > 0
            }
            global_params = GlobalParameters(
                model_posteriors=avg_posteriors,
                aggregated_from_tenants=aggregated_tenants,
                last_sync=datetime.now(timezone.utc),
            )
            existing_params = self.get_global_params() or GlobalParameters()
            existing_params.model_posteriors = avg_posteriors
            existing_params.last_sync = global_params.last_sync
            if existing_params.aggregated_from_tenants:
                existing_params.aggregated_from_tenants.extend(aggregated_tenants)
            else:
                existing_params.aggregated_from_tenants = aggregated_tenants
            self._store_global_params(existing_params)
            self._metrics.counter(
                "meta_learning_aggregations_total",
                labels={"type": "model_routing", "tenants": str(len(aggregated_tenants))},
            ).inc()
            logger.info(
                f"Aggregated model routing params from {len(aggregated_tenants)} tenants ({len(avg_posteriors)} models)"
            )
            return existing_params
        except Exception:
            logger.exception("Failed to aggregate model routing parameters")
            return GlobalParameters()

    async def sync_all_params(self) -> GlobalParameters:
        """Aggregate all parameter types and return unified global state.

        Returns:
            GlobalParameters with all aggregated learning.
        """
        try:
            agent_params = self.aggregate_agent_routing_params()
            model_params = self.aggregate_model_routing_params()
            global_params = GlobalParameters(
                agent_context_weights=agent_params.agent_context_weights,
                agent_performance_priors=agent_params.agent_performance_priors,
                model_posteriors=model_params.model_posteriors,
                aggregated_from_tenants=list(
                    set((agent_params.aggregated_from_tenants or []) + (model_params.aggregated_from_tenants or []))
                ),
                last_sync=datetime.now(timezone.utc),
                total_observations=agent_params.total_observations,
            )
            self._store_global_params(global_params)
            self._metrics.counter("meta_learning_full_syncs_total").inc()
            logger.info(
                f"Full meta-learning sync complete: {len(global_params.aggregated_from_tenants or [])} tenants, {global_params.total_observations} observations"
            )
            return global_params
        except Exception:
            logger.exception("Failed to sync all meta-learning parameters")
            self._metrics.counter("meta_learning_errors_total", labels={"operation": "full_sync"}).inc()
            return GlobalParameters()

    def close(self) -> None:
        """Close Redis connection."""
        with contextlib.suppress(Exception):
            if self._redis_client is not None:
                self._redis_client.close()
                logger.info("Closed meta-learning Redis client")


__all__ = ["GlobalParameters", "MetaLearningAggregator"]
