"""Trust-tier policies for plugins installed via the marketplace.

This module centralises limits applied to plugins based on their trust tier.
It does **not** duplicate permission logic; instead it provides helpers that
other components (e.g. install/update flows) can call to clamp requested
capabilities or resource quotas before storing them in the registry.  The
runtime executor receives the already-clamped grants.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Trust tier definitions
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TierPolicy:
    """Policy describing the ceilings for a trust tier."""

    allowed_capabilities: set[str] | None  # ``None`` means all capabilities.
    max_cpu_ms: int | None
    max_memory_mb: int | None


TIERS: dict[str, TierPolicy] = {
    "untrusted": TierPolicy(set(), 100, 128),
    "community": TierPolicy({"rag.read", "llm.call"}, 500, 256),
    "verified": TierPolicy({"rag.read", "rag.write", "llm.call", "web.fetch"}, 1000, 512),
    "partner": TierPolicy(
        {"rag.read", "rag.write", "llm.call", "web.fetch", "tool.exec"}, 2000, 1024
    ),
    # ``None`` means unlimited/first party.
    "first_party": TierPolicy(None, None, None),
}

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def clamp_capabilities(requested: Iterable[str], tier: str) -> list[str]:
    """Return capabilities allowed for ``tier`` intersected with ``requested``.

    Parameters
    ----------
    requested:
        Capabilities requested by the plugin's manifest.
    tier:
        Trust tier assigned to the plugin.
    """

    policy = TIERS.get(tier)
    if policy is None:
        raise ValueError(f"unknown trust tier: {tier}")
    if policy.allowed_capabilities is None:  # first_party
        return list(requested)
    return sorted(set(requested) & policy.allowed_capabilities)


def clamp_resources(cpu_ms: int | None, memory_mb: int | None, tier: str) -> dict[str, int | None]:
    """Clamp requested resource quotas to tier ceilings."""

    policy = TIERS.get(tier)
    if policy is None:
        raise ValueError(f"unknown trust tier: {tier}")
    return {
        "cpu_ms": min(cpu_ms, policy.max_cpu_ms) if (cpu_ms and policy.max_cpu_ms) else cpu_ms,
        "memory_mb": min(memory_mb, policy.max_memory_mb)
        if (memory_mb and policy.max_memory_mb)
        else memory_mb,
    }
