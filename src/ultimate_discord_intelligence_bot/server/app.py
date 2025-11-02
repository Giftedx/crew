"""Compatibility shim exposing create_app under ultimate_discord_intelligence_bot.server.app.

Some tests import the app factory from this path. We delegate to the canonical
`server.app.create_app` implementation.
"""

from __future__ import annotations

from server.app import create_app


__all__ = ["create_app"]
