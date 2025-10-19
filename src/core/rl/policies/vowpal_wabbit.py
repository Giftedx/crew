"""Vowpal Wabbit contextual bandit policy wrapper."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

try:  # pragma: no cover - optional dependency
    from vowpalwabbit import pyvw
except Exception:  # pragma: no cover - handled gracefully at runtime
    pyvw = None


def _sanitize_token(raw: Any) -> str:
    """Convert arbitrary values to safe VW feature tokens."""
    token = str(raw) if raw is not None else "unknown"
    safe = [ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in token]
    stripped = "".join(safe).strip("_")
    return stripped or "token"


def _flatten_context(context: Mapping[str, Any] | None) -> Mapping[str, Any]:
    """Return a shallow mapping for context inputs."""
    if not context:
        return {}
    flat: dict[str, Any] = {}
    for key, value in context.items():
        if isinstance(value, Mapping):
            for inner_key, inner_value in value.items():
                flat[f"{key}_{inner_key}"] = inner_value
        else:
            flat[str(key)] = value
    return flat


def _format_namespace(namespace: str, features: Mapping[str, Any] | None) -> str:
    """Render a VW namespace string from feature mapping."""
    if not features:
        return f"|{namespace} bias"
    tokens: list[str] = []
    for key, value in sorted(features.items()):
        name = _sanitize_token(key)
        if isinstance(value, bool):
            if value:
                tokens.append(name)
        elif isinstance(value, (int, float)):
            tokens.append(f"{name}:{float(value):.6f}")
        elif value is None:
            continue
        else:
            tokens.append(f"{name}_{_sanitize_token(value)}")
    if not tokens:
        tokens.append("bias")
    return f"|{namespace} {' '.join(tokens)}"


class VowpalWabbitBandit:
    """Contextual bandit policy powered by Vowpal Wabbit."""

    def __init__(self, vw_args: str | None = None) -> None:
        if pyvw is None:  # pragma: no cover - handled in calling code/tests skip
            raise ImportError("vowpalwabbit is not installed")
        args = vw_args or "--cb_explore_adf --epsilon 0.1 --quiet"
        self._workspace = pyvw.Workspace(args)
        self._last_decision: dict[str, Any] | None = None
        self.q_values: defaultdict[Any, float] = defaultdict(float)
        self.counts: defaultdict[Any, int] = defaultdict(int)

    # ------------------------------------------------------------------ helpers
    def _prepare_example(
        self,
        context: Mapping[str, Any] | None,
        candidates: Sequence[Any],
    ) -> tuple[str, list[str]]:
        flat_context = _flatten_context(context) if context else {}
        shared_line = f"shared {_format_namespace('c', flat_context)}"

        action_lines: list[str] = []
        for idx, candidate in enumerate(candidates):
            features: dict[str, Any] = {}
            descriptor: str | None = None
            if isinstance(candidate, Mapping):
                for key, value in candidate.items():
                    features[str(key)] = value
                candidate_id = (
                    candidate.get("id") if hasattr(candidate, "get") else None
                )  # type: ignore[assignment]
                if isinstance(candidate_id, str):
                    descriptor = candidate_id
            else:
                descriptor = None
            features.setdefault(
                "arm", descriptor or f"arm_{idx}_" + _sanitize_token(candidate)
            )
            action_lines.append(_format_namespace(f"a{idx}", features))
        return shared_line, action_lines

    # ------------------------------------------------------------------ policy API
    def recommend(self, context: dict[str, Any], candidates: Sequence[Any]) -> Any:
        if not candidates:
            raise ValueError("candidates must not be empty")

        shared_line, action_lines = self._prepare_example(context, candidates)
        example_lines = [shared_line, *action_lines, ""]
        example_payload = "\n".join(example_lines)

        try:
            probabilities: Iterable[float] = self._workspace.predict(example_payload)
            probs = list(probabilities)
        except Exception as exc:  # pragma: no cover - defensive fallback
            # If VW prediction fails, fall back to uniform random selection
            self._last_decision = None
            raise RuntimeError(f"Vowpal Wabbit prediction failed: {exc}")

        if len(probs) != len(candidates):
            raise RuntimeError(
                "Vowpal Wabbit returned probability vector of unexpected length",
            )

        best_index = max(range(len(candidates)), key=lambda idx: probs[idx])
        best_action = candidates[best_index]

        self._last_decision = {
            "shared": shared_line,
            "actions": action_lines,
            "probabilities": probs,
            "chosen_index": best_index,
            "candidates": list(candidates),
        }
        return best_action

    def update(self, action: Any, reward: float, context: dict[str, Any]) -> None:
        reward_clamped = max(0.0, min(1.0, float(reward)))
        self.counts[action] += 1
        n = self.counts[action]
        q = self.q_values[action]
        self.q_values[action] = q + (reward_clamped - q) / n

        if not self._last_decision:
            return

        last_candidates: list[Any] = self._last_decision.get("candidates", [])  # type: ignore[assignment]
        try:
            chosen_index = last_candidates.index(action)
        except ValueError:
            self._last_decision = None
            return

        shared_line = self._last_decision["shared"]
        action_lines: list[str] = list(self._last_decision["actions"])
        probabilities: Sequence[float] = self._last_decision["probabilities"]
        prob = max(1e-6, float(probabilities[chosen_index]))
        cost = 1.0 - reward_clamped

        labelled_actions: list[str] = []
        for idx, line in enumerate(action_lines):
            if idx == chosen_index:
                labelled_actions.append(f"0:{cost:.6f}:{prob:.6f} {line}")
            else:
                labelled_actions.append(line)

        example_lines = [shared_line, *labelled_actions, ""]
        example_payload = "\n".join(example_lines)
        try:
            self._workspace.learn(example_payload)
        finally:
            self._last_decision = None

    # ------------------------------------------------------------------ snapshot helpers
    def state_dict(self) -> dict[str, Any]:
        return {
            "policy": self.__class__.__name__,
            "version": 1,
            "q_values": dict(self.q_values),
            "counts": dict(self.counts),
        }

    def load_state(self, state: Mapping[str, Any]) -> None:
        ver = state.get("version") if isinstance(state, Mapping) else None
        if ver is not None and ver > 1:
            return
        q_values = state.get("q_values") if isinstance(state, Mapping) else None
        counts = state.get("counts") if isinstance(state, Mapping) else None
        self.q_values.clear()
        if isinstance(q_values, Mapping):
            for arm, value in q_values.items():
                self.q_values[arm] = float(value)
        self.counts.clear()
        if isinstance(counts, Mapping):
            for arm, value in counts.items():
                self.counts[arm] = int(value)

    # ------------------------------------------------------------------ lifecycle
    def close(self) -> None:
        try:
            self._workspace.finish()
        except Exception:  # pragma: no cover - defensive
            pass

    def __del__(self) -> None:  # pragma: no cover - defensive
        self.close()


__all__ = ["VowpalWabbitBandit"]
