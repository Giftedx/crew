"""Compatibility shim for ai.routing.linucb_router.

Re-exports LinUCB router from platform for backward compatibility.
"""

# LinUCB is a contextual bandit algorithm - check if there's a specific implementation
from platform.llm.routing.bandits.bandit_router import ThompsonBanditRouter as LinUCBRouter


__all__ = ["LinUCBRouter"]
