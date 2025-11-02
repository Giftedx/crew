"""Compatibility shim to expose core.http_utils under the package namespace.

Tests import `ultimate_discord_intelligence_bot.core.http_utils`; the actual
implementation lives in top-level `core/http_utils.py`. This module re-exports
the public API for test and runtime compatibility.
"""
from __future__ import annotations
from platform.http.http_utils import *