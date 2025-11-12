"""Compatibility shim for router_registry.

Re-exports from platform.llm.routing.bandits for backward compatibility.
"""

from platform.llm.routing.bandits.router_registry import (
    RewardNormalizer,
    compute_selection_entropy,
    get_tenant_router,
    record_selection,
)


__all__ = ["RewardNormalizer", "compute_selection_entropy", "get_tenant_router", "record_selection"]
