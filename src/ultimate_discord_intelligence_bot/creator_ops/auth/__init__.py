"""
Authentication and OAuth management for Creator Operations.

This module provides OAuth flows, token management, and scope validation
for all supported platforms.
"""

from __future__ import annotations

__all__ = [
    "OAuthManager",
    "YouTubeOAuthManager",
    "TwitchOAuthManager",
    "TikTokOAuthManager",
    "InstagramOAuthManager",
    "XOAuthManager",
    "TokenStorage",
    "ScopeValidator",
    "AuditLogger",
]

from .audit import AuditLogger
from .oauth_manager import (
    InstagramOAuthManager,
    OAuthManager,
    TikTokOAuthManager,
    TwitchOAuthManager,
    XOAuthManager,
    YouTubeOAuthManager,
)
from .scopes import ScopeValidator
from .token_storage import TokenStorage
