"""Compatibility shim for vw_bandit_router.

Re-exports from platform.llm.routing.bandits for backward compatibility.
"""

from platform.llm.routing.bandits.vw_bandit_router import VWBanditRouter


__all__ = ["VWBanditRouter"]
