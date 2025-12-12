"""
Personality state management system with vector embeddings and RL integration.

This module manages the bot's evolving personality traits using reinforcement
learning and vector storage for durable personality memory.
"""

from __future__ import annotations

from domains.intelligence.personality import (
    PersonalityContext,
    PersonalityStateManager,
    PersonalityTraits,
)


__all__ = ["PersonalityContext", "PersonalityStateManager", "PersonalityTraits"]
