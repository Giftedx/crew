"""Compatibility shim for ai.routing.linucb_router.

Re-exports LinUCB router from platform for backward compatibility.
"""
import warnings

warnings.warn(
    "This module is deprecated. Use src/ultimate_discord_intelligence_bot/services/openrouter_service/plugins instead.",
    DeprecationWarning,
    stacklevel=2,
)

# LinUCB is a contextual bandit algorithm - check if there's a specific implementation
from platform.llm.routing.bandits.bandit_router import ThompsonBanditRouter as LinUCBRouter


__all__ = ["LinUCBRouter"]
