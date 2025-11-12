"""Compatibility shim for bandit_router.

Re-exports from platform.llm.routing.bandits for backward compatibility.
"""

from platform.llm.routing.bandits.bandit_router import ThompsonBanditRouter


__all__ = ["ThompsonBanditRouter"]
