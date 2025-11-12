"""
Discord integration module for the Ultimate Discord Intelligence Bot.

This module provides Discord bot functionality, event handlers,
and artifact publishing capabilities.
"""

from .artifact_handler import ArtifactHandler, create_artifact_handler


# Placeholder module for backward compatibility
class _CommandsModule:
    """Placeholder for commands module."""


commands = _CommandsModule()


__all__ = ["ArtifactHandler", "commands", "create_artifact_handler"]
