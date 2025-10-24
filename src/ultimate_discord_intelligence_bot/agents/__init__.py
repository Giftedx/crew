"""Agent definitions for the Ultimate Discord Intelligence Bot.

This module provides a modular approach to agent definitions, replacing
the monolithic crew.py with organized, testable agent classes.
"""

from __future__ import annotations

from .base import BaseAgent
from .registry import AGENT_REGISTRY, get_agent, register_agent


__all__ = ["AGENT_REGISTRY", "BaseAgent", "get_agent", "register_agent"]
