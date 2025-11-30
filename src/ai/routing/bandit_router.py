"""Compatibility shim for ai.routing.bandit_router.

Re-exports from platform.llm.routing for backward compatibility.
"""
import warnings

warnings.warn(
    "This module is deprecated. Use src/ultimate_discord_intelligence_bot/services/openrouter_service/plugins instead.",
    DeprecationWarning,
    stacklevel=2,
)

from platform.llm.routing.bandits.bandit_router import ThompsonBanditRouter
from platform.llm.routing.base_router import BanditRouter


__all__ = ["BanditRouter", "ThompsonBanditRouter"]
