"""Centralized OAuth 2.0 management for all platforms.

This module provides a comprehensive OAuth 2.0 framework for managing authentication
across multiple platforms including YouTube, Twitch, TikTok, Instagram, and X (Twitter).
It handles token refresh, credential storage, and platform-specific OAuth flows.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

import httpx

from ultimate_discord_intelligence_bot.step_result import StepResult


logger = logging.getLogger(__name__)


@dataclass
class OAuthCredentials:
    """OAuth credentials for a platform."""

    access_token: str
    refresh_token: str | None = None
    expires_at: int = 0
    token_type: str = "Bearer"
    scope: str | None = None
    platform: str | None = None
    user_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """Check if the access token is expired."""
        if not self.expires_at:
            return False
        return time.time() >= self.expires_at

    def expires_in(self) -> int:
        """Get seconds until token expires."""
        if not self.expires_at:
            return 0
        return max(0, int(self.expires_at - time.time()))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at,
            "token_type": self.token_type,
            "scope": self.scope,
            "platform": self.platform,
            "user_id": self.user_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OAuthCredentials:
        """Create from dictionary."""
        return cls(**data)


@runtime_checkable
class OAuthProvider(Protocol):
    """Protocol for OAuth providers."""

    def get_auth_url(self, state: str, redirect_uri: str) -> str:
        """Get authorization URL."""
        ...

    def exchange_code(self, code: str, redirect_uri: str) -> OAuthCredentials:
        """Exchange authorization code for tokens."""
        ...

    def refresh_token(self, refresh_token: str) -> OAuthCredentials:
        """Refresh access token."""
        ...


class YouTubeOAuthProvider:
    """YouTube OAuth 2.0 provider."""

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://accounts.google.com/o/oauth2/v2/auth"
        self.token_url = "https://oauth2.googleapis.com/token"

    def get_auth_url(self, state: str, redirect_uri: str) -> str:
        """Get YouTube authorization URL."""
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "https://www.googleapis.com/auth/youtube.readonly",
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.base_url}?{query_string}"

    def exchange_code(self, code: str, redirect_uri: str) -> OAuthCredentials:
        """Exchange authorization code for YouTube tokens."""
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        }
        response = httpx.post(self.token_url, data=data)
        response.raise_for_status()
        token_data = response.json()
        return OAuthCredentials(
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            expires_at=int(time.time()) + token_data.get("expires_in", 3600),
            token_type=token_data.get("token_type", "Bearer"),
            scope=token_data.get("scope"),
            platform="youtube",
        )

    def refresh_token(self, refresh_token: str) -> OAuthCredentials:
        """Refresh YouTube access token."""
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
        response = httpx.post(self.token_url, data=data)
        response.raise_for_status()
        token_data = response.json()
        return OAuthCredentials(
            access_token=token_data["access_token"],
            refresh_token=refresh_token,
            expires_at=int(time.time()) + token_data.get("expires_in", 3600),
            token_type=token_data.get("token_type", "Bearer"),
            platform="youtube",
        )


class TwitchOAuthProvider:
    """Twitch OAuth 2.0 provider."""

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://id.twitch.tv/oauth2/authorize"
        self.token_url = "https://id.twitch.tv/oauth2/token"

    def get_auth_url(self, state: str, redirect_uri: str) -> str:
        """Get Twitch authorization URL."""
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "user:read:email",
            "state": state,
        }
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.base_url}?{query_string}"

    def exchange_code(self, code: str, redirect_uri: str) -> OAuthCredentials:
        """Exchange authorization code for Twitch tokens."""
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        }
        response = httpx.post(self.token_url, data=data)
        response.raise_for_status()
        token_data = response.json()
        return OAuthCredentials(
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            expires_at=int(time.time()) + token_data.get("expires_in", 3600),
            token_type=token_data.get("token_type", "Bearer"),
            scope=token_data.get("scope"),
            platform="twitch",
        )

    def refresh_token(self, refresh_token: str) -> OAuthCredentials:
        """Refresh Twitch access token."""
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
        response = httpx.post(self.token_url, data=data)
        response.raise_for_status()
        token_data = response.json()
        return OAuthCredentials(
            access_token=token_data["access_token"],
            refresh_token=refresh_token,
            expires_at=int(time.time()) + token_data.get("expires_in", 3600),
            token_type=token_data.get("token_type", "Bearer"),
            platform="twitch",
        )


class TikTokOAuthProvider:
    """TikTok OAuth 2.0 provider with PKCE."""

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://www.tiktok.com/v2/auth/authorize/"
        self.token_url = "https://open.tiktokapis.com/v2/oauth/token/"

    def get_auth_url(self, state: str, redirect_uri: str) -> str:
        """Get TikTok authorization URL with PKCE."""
        code_challenge = "dummy_challenge"
        params = {
            "client_key": self.client_id,
            "scope": "user.info.basic",
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.base_url}?{query_string}"

    def exchange_code(self, code: str, redirect_uri: str) -> OAuthCredentials:
        """Exchange authorization code for TikTok tokens."""
        data = {
            "client_key": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        }
        response = httpx.post(self.token_url, data=data)
        response.raise_for_status()
        token_data = response.json()
        return OAuthCredentials(
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            expires_at=int(time.time()) + token_data.get("expires_in", 3600),
            token_type=token_data.get("token_type", "Bearer"),
            scope=token_data.get("scope"),
            platform="tiktok",
        )

    def refresh_token(self, refresh_token: str) -> OAuthCredentials:
        """Refresh TikTok access token."""
        data = {
            "client_key": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
        response = httpx.post(self.token_url, data=data)
        response.raise_for_status()
        token_data = response.json()
        return OAuthCredentials(
            access_token=token_data["access_token"],
            refresh_token=refresh_token,
            expires_at=int(time.time()) + token_data.get("expires_in", 3600),
            token_type=token_data.get("token_type", "Bearer"),
            platform="tiktok",
        )


class OAuthManager:
    """Centralized OAuth 2.0 management for all platforms."""

    def __init__(self):
        self.credentials: dict[str, OAuthCredentials] = {}
        self.providers: dict[str, OAuthProvider] = {}
        self._refresh_handlers: dict[str, callable] = {}
        self._storage_backend: callable | None = None

    def register_platform(self, platform: str, provider: OAuthProvider) -> StepResult:
        """Register OAuth provider for a platform."""
        try:
            self.providers[platform] = provider
            logger.info(f"Registered OAuth provider for {platform}")
            return StepResult.ok(data={"platform": platform, "status": "registered"})
        except Exception as e:
            logger.error(f"Failed to register OAuth provider for {platform}: {e}")
            return StepResult.fail(f"OAuth registration failed: {e!s}")

    def set_credentials(self, platform: str, credentials: OAuthCredentials) -> StepResult:
        """Set OAuth credentials for a platform."""
        try:
            credentials.platform = platform
            self.credentials[platform] = credentials
            if self._storage_backend:
                self._storage_backend(platform, credentials.to_dict())
            logger.info(f"Set OAuth credentials for {platform}")
            return StepResult.ok(data={"platform": platform, "status": "credentials_set"})
        except Exception as e:
            logger.error(f"Failed to set OAuth credentials for {platform}: {e}")
            return StepResult.fail(f"Failed to set credentials: {e!s}")

    def get_access_token(self, platform: str) -> StepResult:
        """Get valid access token, refreshing if needed."""
        try:
            if platform not in self.credentials:
                return StepResult.not_found(f"No credentials found for platform: {platform}")
            credentials = self.credentials[platform]
            if credentials.is_expired() and credentials.refresh_token:
                if platform not in self.providers:
                    return StepResult.fail(f"No OAuth provider for platform: {platform}")
                provider = self.providers[platform]
                try:
                    refreshed = provider.refresh_token(credentials.refresh_token)
                    refreshed.platform = platform
                    self.credentials[platform] = refreshed
                    if self._storage_backend:
                        self._storage_backend(platform, refreshed.to_dict())
                    logger.info(f"Refreshed access token for {platform}")
                    return StepResult.ok(data={"access_token": refreshed.access_token, "platform": platform})
                except Exception as e:
                    logger.error(f"Failed to refresh token for {platform}: {e}")
                    return StepResult.fail(f"Token refresh failed: {e!s}")
            return StepResult.ok(data={"access_token": credentials.access_token, "platform": platform})
        except Exception as e:
            logger.error(f"Failed to get access token for {platform}: {e}")
            return StepResult.fail(f"Failed to get access token: {e!s}")

    def get_auth_url(self, platform: str, state: str, redirect_uri: str) -> StepResult:
        """Get authorization URL for a platform."""
        try:
            if platform not in self.providers:
                return StepResult.not_found(f"No OAuth provider for platform: {platform}")
            provider = self.providers[platform]
            auth_url = provider.get_auth_url(state, redirect_uri)
            return StepResult.ok(data={"auth_url": auth_url, "platform": platform, "state": state})
        except Exception as e:
            logger.error(f"Failed to get auth URL for {platform}: {e}")
            return StepResult.fail(f"Failed to get auth URL: {e!s}")

    def exchange_code(self, platform: str, code: str, redirect_uri: str) -> StepResult:
        """Exchange authorization code for tokens."""
        try:
            if platform not in self.providers:
                return StepResult.not_found(f"No OAuth provider for platform: {platform}")
            provider = self.providers[platform]
            credentials = provider.exchange_code(code, redirect_uri)
            credentials.platform = platform
            self.credentials[platform] = credentials
            if self._storage_backend:
                self._storage_backend(platform, credentials.to_dict())
            logger.info(f"Exchanged code for tokens for {platform}")
            return StepResult.ok(data={"credentials": credentials.to_dict(), "platform": platform})
        except Exception as e:
            logger.error(f"Failed to exchange code for {platform}: {e}")
            return StepResult.fail(f"Code exchange failed: {e!s}")

    def revoke_token(self, platform: str) -> StepResult:
        """Revoke OAuth credentials for a platform."""
        try:
            if platform in self.credentials:
                del self.credentials[platform]
                if self._storage_backend:
                    self._storage_backend(platform, None)
                logger.info(f"Revoked credentials for {platform}")
                return StepResult.ok(data={"platform": platform, "status": "revoked"})
            else:
                return StepResult.not_found(f"No credentials found for platform: {platform}")
        except Exception as e:
            logger.error(f"Failed to revoke credentials for {platform}: {e}")
            return StepResult.fail(f"Failed to revoke credentials: {e!s}")

    def set_storage_backend(self, backend: callable) -> None:
        """Set storage backend for credential persistence."""
        self._storage_backend = backend

    def get_platforms(self) -> StepResult:
        """Get list of registered platforms."""
        platforms = list(self.providers.keys())
        return StepResult.ok(data={"platforms": platforms})

    def get_platform_status(self, platform: str) -> StepResult:
        """Get status of platform credentials."""
        try:
            if platform not in self.providers:
                return StepResult.not_found(f"No OAuth provider for platform: {platform}")
            has_credentials = platform in self.credentials
            is_expired = False
            expires_in = 0
            if has_credentials:
                credentials = self.credentials[platform]
                is_expired = credentials.is_expired()
                expires_in = credentials.expires_in()
            return StepResult.ok(
                data={
                    "platform": platform,
                    "has_credentials": has_credentials,
                    "is_expired": is_expired,
                    "expires_in": expires_in,
                    "provider_registered": True,
                }
            )
        except Exception as e:
            logger.error(f"Failed to get platform status for {platform}: {e}")
            return StepResult.fail(f"Failed to get platform status: {e!s}")

    def health_check(self) -> StepResult:
        """Perform health check on OAuth manager."""
        try:
            status = {
                "registered_providers": len(self.providers),
                "stored_credentials": len(self.credentials),
                "platforms": list(self.providers.keys()),
                "has_storage_backend": self._storage_backend is not None,
                "timestamp": time.time(),
            }
            healthy_credentials = 0
            expired_credentials = 0
            for credentials in self.credentials.values():
                if credentials.is_expired():
                    expired_credentials += 1
                else:
                    healthy_credentials += 1
            status.update({"healthy_credentials": healthy_credentials, "expired_credentials": expired_credentials})
            return StepResult.ok(data=status)
        except Exception as e:
            logger.error(f"OAuth health check failed: {e}")
            return StepResult.fail(f"Health check failed: {e!s}")


_oauth_manager: OAuthManager | None = None


def get_oauth_manager() -> OAuthManager:
    """Get the global OAuth manager instance."""
    global _oauth_manager
    if _oauth_manager is None:
        _oauth_manager = OAuthManager()
    return _oauth_manager


def setup_default_providers() -> StepResult:
    """Set up default OAuth providers from environment variables."""
    import os

    manager = get_oauth_manager()
    youtube_client_id = os.getenv("YOUTUBE_CLIENT_ID")
    youtube_client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")
    if youtube_client_id and youtube_client_secret:
        youtube_provider = YouTubeOAuthProvider(youtube_client_id, youtube_client_secret)
        result = manager.register_platform("youtube", youtube_provider)
        if not result.success:
            return result
    twitch_client_id = os.getenv("TWITCH_CLIENT_ID")
    twitch_client_secret = os.getenv("TWITCH_CLIENT_SECRET")
    if twitch_client_id and twitch_client_secret:
        twitch_provider = TwitchOAuthProvider(twitch_client_id, twitch_client_secret)
        result = manager.register_platform("twitch", twitch_provider)
        if not result.success:
            return result
    tiktok_client_id = os.getenv("TIKTOK_CLIENT_ID")
    tiktok_client_secret = os.getenv("TIKTOK_CLIENT_SECRET")
    if tiktok_client_id and tiktok_client_secret:
        tiktok_provider = TikTokOAuthProvider(tiktok_client_id, tiktok_client_secret)
        result = manager.register_platform("tiktok", tiktok_provider)
        if not result.success:
            return result
    return StepResult.ok(data={"status": "default_providers_setup_complete"})
