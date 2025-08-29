"""Structured log data models for core services."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LLMCallLog:
    prompt: str
    response: str
    model: str
    provider: str
    tokens_prompt: int
    tokens_completion: int
    cost_usd: float
    latency_ms: float


@dataclass
class RoutingDecisionLog:
    domain: str
    candidates: list[str]
    chosen: str
    reward: float | None = None


@dataclass
class RewardLog:
    domain: str
    reward: float
    breakdown: dict[str, float]


__all__ = ["LLMCallLog", "RoutingDecisionLog", "RewardLog"]
