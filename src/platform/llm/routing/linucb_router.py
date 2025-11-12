"""Compatibility shim for linucb_router.

Re-exports from platform.llm.routing.bandits for backward compatibility.
"""

from platform.llm.routing.bandits.bandit_router import ThompsonBanditRouter


# LinUCB is an alias to Thompson Bandit Router
LinUCBRouter = ThompsonBanditRouter

__all__ = ["LinUCBRouter"]
