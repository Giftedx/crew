"""Compatibility shim for domains.memory.tenancy imports.

Re-exports from ultimate_discord_intelligence_bot.tenancy for backward compatibility.
"""

from ultimate_discord_intelligence_bot.tenancy.context import current_tenant, mem_ns


__all__ = ["current_tenant", "mem_ns"]
