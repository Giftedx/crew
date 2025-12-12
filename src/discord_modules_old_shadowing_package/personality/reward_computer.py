"""
Reward signal computation for personality evolution.

This module computes reward signals from user reactions and engagement metrics
to guide personality adaptation through reinforcement learning.
"""

from __future__ import annotations

from domains.intelligence.personality import InteractionMetrics, RewardComputer


__all__ = ["InteractionMetrics", "RewardComputer"]
