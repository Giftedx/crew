"""Contextual(ish) bandit router for model/tool selection.

Initial minimal implementation: Thompson Sampling for Bernoulli-ish reward
(normalized scalar in [0,1]) with simple context hashing for future extension.

Feature flag: ENABLE_BANDIT_ROUTING=1 gates usage by higher-level router wrappers.

Env tuning:
- Exploration and reset parameters (BANDIT_MIN_EPSILON, BANDIT_RESET_ENTROPY_THRESHOLD, BANDIT_RESET_ENTROPY_WINDOW)
    are read dynamically at selection/reset time to support mid-process adjustments in tests and controlled environments.
    Priors (BANDIT_PRIOR_ALPHA, BANDIT_PRIOR_BETA) remain import-time defaults.

Design principles:
- Stateless API aside from internal per-arm posterior parameters
- Thread-safe updates via a lock (lightweight)
- Pluggable exploration decay / priors via env vars
- Serialization hook (future) for persistence not included yet
"""
from __future__ import annotations

import contextlib
import json
import os
import random
import threading
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast


if TYPE_CHECKING:
    from collections.abc import Sequence

    from ._metrics_types import MetricLike, MetricsFacade
try:
    from platform.observability.metrics import get_metrics as _gm

    def _obtain_metrics() -> MetricsFacade | None:
        try:
            return cast('MetricsFacade', _gm())
        except Exception:
            return None
except Exception:

    def _obtain_metrics() -> MetricsFacade | None:
        return None

def _flag_enabled() -> bool:
    return os.getenv('ENABLE_BANDIT_ROUTING', '0').lower() in {'1', 'true', 'yes', 'on'}
_PRIOR_ALPHA = float(os.getenv('BANDIT_PRIOR_ALPHA', '1.0') or 1.0)
_PRIOR_BETA = float(os.getenv('BANDIT_PRIOR_BETA', '1.0') or 1.0)

def _min_epsilon() -> float:
    """Return the current forced exploration floor from env.

    Read dynamically to avoid import-time caching so tests can monkeypatch
    BANDIT_MIN_EPSILON per test without requiring module reloads.
    """
    try:
        return float(os.getenv('BANDIT_MIN_EPSILON', '0.0') or 0.0)
    except Exception:
        return 0.0

def _reset_entropy_threshold() -> float:
    try:
        return float(os.getenv('BANDIT_RESET_ENTROPY_THRESHOLD', '0.05') or 0.05)
    except Exception:
        return 0.05

def _reset_entropy_window() -> int:
    try:
        return int(os.getenv('BANDIT_RESET_ENTROPY_WINDOW', '50') or 50)
    except Exception:
        return 50

@dataclass
class ArmState:
    alpha: float
    beta: float

    def sample(self) -> float:
        return random.betavariate(self.alpha, self.beta)

    def update(self, reward: float) -> None:
        r = max(0.0, min(1.0, reward))
        self.alpha += r
        self.beta += 1.0 - r

class ThompsonBanditRouter:
    """Multi-arm Thompson Sampling bandit.

    Public methods:
        select(arms: Sequence[str], context: dict | None) -> str
        update(arm: str, reward: float, context: dict | None) -> None
    """

    def __init__(self, state_file: str | None=None) -> None:
        self._arms: dict[str, ArmState] = {}
        self._lock = threading.Lock()
        self._metrics: MetricsFacade | None = _obtain_metrics()
        self._persist_enabled = os.getenv('ENABLE_BANDIT_PERSIST', '0').lower() in {'1', 'true', 'yes', 'on'}
        self._state_dir = os.getenv('BANDIT_STATE_DIR', './data/bandit_state')
        self._state_file_override = state_file
        self._low_entropy_run = 0
        self._last_reset_count = 0
        if self._metrics:
            m = self._metrics
            self._sel_counter: MetricLike | None = m.counter('bandit_router_selections_total')
            self._reward_counter: MetricLike | None = m.counter('bandit_router_reward_total')
            self._update_counter: MetricLike | None = m.counter('bandit_router_updates_total')
            self._explore_counter: MetricLike | None = m.counter('bandit_router_forced_explorations_total')
            self._reset_counter: MetricLike | None = m.counter('bandit_router_resets_total')
        else:
            self._sel_counter = None
            self._reward_counter = None
            self._update_counter = None
            self._explore_counter = None
            self._reset_counter = None
        if self._persist_enabled:
            with contextlib.suppress(Exception):
                os.makedirs(self._state_dir, exist_ok=True)
                self._load_state()

    def select(self, arms: Sequence[str], context: dict[str, Any] | None=None) -> str:
        if not arms:
            raise ValueError('No arms provided')
        if not _flag_enabled():
            chosen = arms[0]
            if self._sel_counter:
                with contextlib.suppress(Exception):
                    self._sel_counter.inc(1)
            return chosen
        samples: list[tuple[float, str]] = []
        with self._lock:
            for a in arms:
                st = self._arms.get(a)
                if st is None:
                    st = ArmState(alpha=_PRIOR_ALPHA, beta=_PRIOR_BETA)
                    self._arms[a] = st
                samples.append((st.sample(), a))
        samples.sort(reverse=True)
        chosen = samples[0][1]
        _eps = _min_epsilon()
        if _eps > 0 and random.random() < _eps and (len(arms) > 1):
            alt_choices = [a for a in arms if a != chosen]
            if alt_choices:
                chosen = random.choice(alt_choices)
                if self._explore_counter:
                    with contextlib.suppress(Exception):
                        self._explore_counter.inc(1)
        if self._sel_counter:
            with contextlib.suppress(Exception):
                self._sel_counter.inc(1)
        return chosen

    def update(self, arm: str, reward: float, context: dict[str, Any] | None=None) -> None:
        with self._lock:
            st = self._arms.get(arm)
            if st is None:
                st = ArmState(alpha=_PRIOR_ALPHA, beta=_PRIOR_BETA)
                self._arms[arm] = st
            st.update(reward)
        if not _flag_enabled():
            return
        if self._reward_counter:
            with contextlib.suppress(Exception):
                self._reward_counter.inc(float(max(0.0, min(1.0, reward))))
        if self._update_counter:
            with contextlib.suppress(Exception):
                self._update_counter.inc(1)
        if self._persist_enabled:
            with contextlib.suppress(Exception):
                self._save_state()
        self._maybe_reset()

    def get_state(self, arm: str) -> ArmState | None:
        return self._arms.get(arm)

    def arms(self) -> list[str]:
        with self._lock:
            return list(self._arms.keys())

    def _posterior_mean_entropy(self) -> float | None:
        arms = self.arms()
        if not arms:
            return None
        probs = []
        with self._lock:
            for a in arms:
                st = self._arms.get(a)
                if not st:
                    continue
                total = st.alpha + st.beta
                if total <= 0:
                    continue
                probs.append(st.alpha / total)
        if not probs:
            return None
        s = sum(probs)
        if s <= 0:
            return None
        entropy = 0.0
        for p in probs:
            pn = p / s
            entropy -= pn * (0 if pn <= 0 else pn and __import__('math').log(pn))
        return entropy

    def _maybe_reset(self) -> None:
        window = _reset_entropy_window()
        if window <= 0:
            return
        ent = self._posterior_mean_entropy()
        if ent is None:
            return
        threshold = _reset_entropy_threshold()
        if ent < threshold:
            self._low_entropy_run += 1
        else:
            self._low_entropy_run = 0
        if self._low_entropy_run >= window:
            with self._lock:
                for arm in list(self._arms.keys()):
                    self._arms[arm] = ArmState(alpha=_PRIOR_ALPHA, beta=_PRIOR_BETA)
                self._low_entropy_run = 0
            if self._reset_counter:
                with contextlib.suppress(Exception):
                    self._reset_counter.inc(1)
            if self._persist_enabled:
                with contextlib.suppress(Exception):
                    self._save_state()

    def _state_path(self) -> str:
        if self._state_file_override:
            return os.path.join(self._state_dir, self._state_file_override)
        return os.path.join(self._state_dir, 'bandit_state.json')

    def _serialize(self) -> dict[str, dict[str, float]]:
        with self._lock:
            return {arm: {'alpha': st.alpha, 'beta': st.beta} for arm, st in self._arms.items()}

    def _apply(self, data: dict[str, dict[str, float]]) -> None:
        with self._lock:
            for arm, ab in data.items():
                a = float(ab.get('alpha', _PRIOR_ALPHA))
                b = float(ab.get('beta', _PRIOR_BETA))
                if a > 0 and b > 0:
                    self._arms[arm] = ArmState(alpha=a, beta=b)

    def _load_state(self) -> None:
        path = self._state_path()
        if not os.path.isfile(path):
            return
        with open(path, encoding='utf-8') as f:
            raw = json.load(f)
        if isinstance(raw, dict):
            self._apply(raw)

    def _save_state(self) -> None:
        tmp_path = self._state_path() + '.tmp'
        data = self._serialize()
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, separators=(',', ':'))
        os.replace(tmp_path, self._state_path())
__all__ = ['ThompsonBanditRouter']
