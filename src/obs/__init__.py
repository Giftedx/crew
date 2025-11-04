"""Compatibility namespace for legacy imports.

This package provides a minimal shim so imports like `from obs import metrics`
continue to work. It forwards to the project metrics facade under
`ultimate_discord_intelligence_bot.obs`.
"""

__all__ = ["metrics"]
