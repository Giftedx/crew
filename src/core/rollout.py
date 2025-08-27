from __future__ import annotations
"""Simple shadow/canary rollout controller."""

from dataclasses import dataclass
from typing import Dict
import random


@dataclass
class RolloutState:
    control: str
    candidate: str
    canary_pct: float
    min_trials: int
    trials: int = 0
    control_reward: float = 0.0
    candidate_reward: float = 0.0
    promoted: bool = False


class RolloutController:
    """Manage staged rollouts between control and candidate arms."""

    def __init__(self) -> None:
        self._domains: Dict[str, RolloutState] = {}

    def start(self, domain: str, control: str, candidate: str, canary_pct: float, min_trials: int = 10) -> None:
        self._domains[domain] = RolloutState(control, candidate, canary_pct, min_trials)

    def choose(self, domain: str) -> str:
        state = self._domains.get(domain)
        if not state:
            raise KeyError(domain)
        if state.promoted:
            return state.control
        return state.candidate if random.random() < state.canary_pct else state.control

    def record(self, domain: str, arm: str, reward: float) -> None:
        state = self._domains.get(domain)
        if not state:
            return
        state.trials += 1
        if arm == state.candidate:
            state.candidate_reward += reward
        else:
            state.control_reward += reward
        if state.trials >= state.min_trials and not state.promoted:
            if state.candidate_reward >= state.control_reward:
                state.control = state.candidate
            state.promoted = True


__all__ = ["RolloutController"]
