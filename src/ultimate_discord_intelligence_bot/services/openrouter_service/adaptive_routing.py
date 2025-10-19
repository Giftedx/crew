from __future__ import annotations

import logging
import os
import threading
from collections import defaultdict
from typing import Any, Optional

try:  # pragma: no cover - optional dependency
    from ax.service.ax_client import AxClient

    _AX_AVAILABLE = True
except Exception:  # pragma: no cover - gracefully degrade when Ax is unavailable
    AxClient = None  # type: ignore[assignment]
    _AX_AVAILABLE = False

# Import bandit plugins
try:
    from .plugins import BanditPlugin, DoublyRobustPlugin, EnhancedLinUCBPlugin

    _PLUGINS_AVAILABLE = True
except ImportError:
    BanditPlugin = None  # type: ignore[assignment, misc]
    EnhancedLinUCBPlugin = None  # type: ignore[assignment]
    DoublyRobustPlugin = None  # type: ignore[assignment]
    _PLUGINS_AVAILABLE = False

logger = logging.getLogger(__name__)


class AdaptiveRoutingManager:
    """Adaptive routing with Ax or bandit plugins for model selection.

    Supports two modes:
    1. Ax-based Bayesian optimization (default when enabled)
    2. Bandit plugins (EnhancedLinUCB, DoublyRobust) via ROUTING_PLUGIN env var
    """

    def __init__(
        self, enabled: bool = False, experiment_prefix: str = "openrouter"
    ) -> None:
        self._enabled = bool(enabled) and _AX_AVAILABLE
        self._experiment_prefix = experiment_prefix
        self._clients: dict[str, AxClient] = {}
        self._candidate_map: dict[str, list[str]] = {}
        self._pending: dict[str, dict[int, dict[str, Any]]] = defaultdict(dict)
        self._events: list[dict[str, Any]] = []
        self._lock = threading.Lock()

        # Bandit plugin support (ADR-0003 enhanced routing)
        self._plugin: Optional[BanditPlugin] = None
        self._plugin_trial_counter = 0

        # Initialize plugin if requested and available
        if _PLUGINS_AVAILABLE:
            plugin_type = os.getenv("ROUTING_PLUGIN", "").lower()
            if plugin_type == "enhanced_linucb":
                alpha = float(os.getenv("UCB_ALPHA", "1.0"))
                self._plugin = EnhancedLinUCBPlugin(alpha=alpha)
                logger.info(f"Initialized EnhancedLinUCB plugin with alpha={alpha}")
            elif plugin_type == "doubly_robust":
                self._plugin = DoublyRobustPlugin(
                    num_actions=20,  # Will expand dynamically
                    context_dim=10,
                    alpha=1.5,
                )
                logger.info("Initialized DoublyRobust plugin")
            elif plugin_type:
                logger.warning(f"Unknown plugin type: {plugin_type}")

    @property
    def enabled(self) -> bool:
        return self._enabled

    def suggest(
        self,
        task_type: str,
        candidates: list[str],
        context: dict[str, Any],
    ) -> tuple[int, str] | None:
        """Suggest next model using Ax or bandit plugin.

        Returns a tuple of ``(trial_index, model)`` when enabled, otherwise ``None``.
        """

        # Try plugin-based routing first
        if self._plugin and candidates:
            try:
                selected_model = self._plugin.select_action(context, candidates)
                trial_index = self._plugin_trial_counter
                self._plugin_trial_counter += 1

                # Track pending for reward observation
                with self._lock:
                    self._pending[task_type][trial_index] = {
                        "context": dict(context),
                        "model": selected_model,
                        "candidates": list(candidates),
                        "plugin_based": True,
                    }

                logger.debug(f"Plugin selected {selected_model} for {task_type}")
                return trial_index, selected_model
            except Exception as e:
                logger.warning(f"Plugin selection failed: {e}, falling back to Ax")

        if not self._enabled or not candidates:
            return None
        normalized = list(dict.fromkeys(candidates))
        with self._lock:
            client = self._clients.get(task_type)
            recorded_candidates = self._candidate_map.get(task_type)
            if client is None:
                if AxClient is None:
                    return None
                try:
                    client = AxClient(enforce_sequential_optimization=False)
                    client.create_experiment(
                        name=f"{self._experiment_prefix}-{task_type}",
                        parameters=[
                            {"name": "model", "type": "choice", "values": normalized}
                        ],
                        objective_name="reward",
                        minimize=False,
                    )
                    self._clients[task_type] = client
                    self._candidate_map[task_type] = normalized
                except Exception:
                    self._enabled = False
                    return None
            elif recorded_candidates:
                intersection = [
                    cand for cand in normalized if cand in recorded_candidates
                ]
                if not intersection:
                    normalized = recorded_candidates
                else:
                    normalized = intersection
            try:
                trial_index, params = client.get_next_trial()
                model = params.get("model") if isinstance(params, dict) else None
                if not isinstance(model, str) or model not in normalized:
                    model = normalized[0]
                self._pending[task_type][trial_index] = {
                    "context": dict(context),
                    "model": model,
                    "candidates": list(normalized),
                }
                return trial_index, model
            except Exception:
                return None

    def observe(
        self,
        task_type: str,
        trial_index: int,
        reward: float,
        metadata: dict[str, Any],
    ) -> None:
        """Report observed reward for a previously suggested trial."""

        with self._lock:
            pending = self._pending.get(task_type, {}).pop(trial_index, {})

            # Handle plugin-based trials
            if pending.get("plugin_based") and self._plugin:
                try:
                    context = pending.get("context", {})
                    model = pending.get("model", "")
                    self._plugin.update(context, model, reward)
                    logger.debug(f"Updated plugin with reward {reward} for {model}")
                except Exception as e:
                    logger.error(f"Plugin update failed: {e}")

            # Track event regardless of backend
            payload = {
                "task_type": task_type,
                "trial_index": trial_index,
                "reward": float(reward),
            }
            payload.update(pending.get("context", {}))
            payload.update(metadata)
            self._events.append(payload)

            # Handle Ax-based trials
            if not pending.get("plugin_based"):
                if not self._enabled:
                    return
                client = self._clients.get(task_type)
                if client is None:
                    return
                try:
                    client.complete_trial(
                        trial_index, raw_data={"reward": (float(reward), 0.0)}
                    )
                except Exception:
                    try:
                        client.log_trial_data(trial_index, {"reward": float(reward)})
                        client.complete_trial(trial_index)
                    except Exception:
                        return

    def pending_count(self) -> int:
        with self._lock:
            return sum(len(items) for items in self._pending.values())

    def drain_events(self) -> list[dict[str, Any]]:
        with self._lock:
            events = list(self._events)
            self._events.clear()
            return events


__all__ = ["AdaptiveRoutingManager"]
