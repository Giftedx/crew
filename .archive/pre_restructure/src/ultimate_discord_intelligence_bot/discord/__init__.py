"""
Discord integration module for the Ultimate Discord Intelligence Bot.

This module provides Discord bot functionality, event handlers,
and artifact publishing capabilities.
"""

from .artifact_handler import ArtifactHandler, create_artifact_handler


__all__ = ["ArtifactHandler", "create_artifact_handler"]
