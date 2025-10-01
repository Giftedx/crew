from __future__ import annotations

import threading
from collections import defaultdict
from typing import Any

try:  # pragma: no cover - optional dependency
    from ax.service.ax_client import AxClient

    _AX_AVAILABLE = True
except Exception:  # pragma: no cover - gracefully degrade when Ax is unavailable
    AxClient = None  # type: ignore[assignment]
    _AX_AVAILABLE = False


class AdaptiveRoutingManager:
    """Thin wrapper around Ax to suggest and record model routing decisions."""

    def __init__(self, enabled: bool = False, experiment_prefix: str = "openrouter") -> None:
        self._enabled = bool(enabled) and _AX_AVAILABLE
        self._experiment_prefix = experiment_prefix
        self._clients: dict[str, AxClient] = {}
        self._candidate_map: dict[str, list[str]] = {}
        self._pending: dict[str, dict[int, dict[str, Any]]] = defaultdict(dict)
        self._events: list[dict[str, Any]] = []
        self._lock = threading.Lock()

    @property
    def enabled(self) -> bool:
        return self._enabled

    def suggest(
        self,
        task_type: str,
        candidates: list[str],
        context: dict[str, Any],
    ) -> tuple[int, str] | None:
        """Ask Ax for the next model to try for ``task_type``.

        Returns a tuple of ``(trial_index, model)`` when Ax is enabled, otherwise ``None``.
        """

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
                        parameters=[{"name": "model", "type": "choice", "values": normalized}],
                        objective_name="reward",
                        minimize=False,
                    )
                    self._clients[task_type] = client
                    self._candidate_map[task_type] = normalized
                except Exception:
                    self._enabled = False
                    return None
            elif recorded_candidates:
                intersection = [cand for cand in normalized if cand in recorded_candidates]
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

        if not self._enabled:
            return
        with self._lock:
            client = self._clients.get(task_type)
            if client is None:
                return
            pending = self._pending.get(task_type, {}).pop(trial_index, {})
            payload = {"task_type": task_type, "trial_index": trial_index, "reward": float(reward)}
            payload.update(pending.get("context", {}))
            payload.update(metadata)
            self._events.append(payload)
            try:
                client.complete_trial(trial_index, raw_data={"reward": (float(reward), 0.0)})
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
