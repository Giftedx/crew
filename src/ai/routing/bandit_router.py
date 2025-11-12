"""Compatibility shim for ai.routing.bandit_router.

Re-exports from platform.llm.routing for backward compatibility.
"""

from platform.llm.routing.bandits.bandit_router import ThompsonBanditRouter
from platform.llm.routing.base_router import BanditRouter


__all__ = ["BanditRouter", "ThompsonBanditRouter"]
