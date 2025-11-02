"""Compatibility wrapper to expose server application factory under the
ultimate_discord_intelligence_bot.server namespace expected by some tests.

This module re-exports create_app from the canonical server.app module.
"""
from __future__ import annotations
from server.app import create_app
__all__ = ['create_app']