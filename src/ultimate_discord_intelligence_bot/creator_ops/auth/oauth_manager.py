"""
OAuth managers for platform authentication.

This module provides OAuth flow implementations for YouTube, Twitch, TikTok,
Instagram, and X (Twitter) platforms with token management and refresh logic.
"""
from __future__ import annotations
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import TYPE_CHECKING
from urllib.parse import urlencode
from platform.http.http_utils import requests, resilient_get, resilient_post
from platform.core.step_result import StepResult
if TYPE_CHECKING:
    from ultimate_discord_intelligence_bot.creator_ops.auth.token_storage import TokenStorage
logger = logging.getLogger(__name__)

class OAuthManager(ABC):
    """Abstract base class for OAuth managers."""

    def __init__(self, platform: str, client_id: str, client_secret: str, redirect_uri: str, scopes: list[str], token_storage: TokenStorage | None=None) -> None:
        """Initialize OAuth manager.

        Args:
            platform: Platform name
            client_id: OAuth client ID
            client_secret: OAuth client secret
            redirect_uri: OAuth redirect URI
            scopes: List of OAuth scopes
            token_storage: Token storage instance
        """
        self.platform = platform
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scopes = scopes
        self.token_storage = token_storage

    @abstractmethod
    def get_authorization_url(self, state: str | None=None) -> str:
        """Get authorization URL for OAuth flow.

        Args:
            state: Optional state parameter for security

        Returns:
            Authorization URL
        """

    @abstractmethod
    def exchange_code_for_tokens(self, code: str) -> StepResult:
        """Exchange authorization code for access tokens.

        Args:
            code: Authorization code from callback

        Returns:
            StepResult with token data
        """

    @abstractmethod
    def refresh_access_token(self, refresh_token: str) -> StepResult:
        """Refresh expired access token.

        Args:
            refresh_token: Refresh token

        Returns:
            StepResult with new token data
        """

    @abstractmethod
    def validate_token(self, access_token: str) -> StepResult:
        """Validate access token.

        Args:
            access_token: Access token to validate

        Returns:
            StepResult with validation results
        """

    def store_tokens(self, access_token: str, refresh_token: str | None, expires_in: int | None, scope: str | None, tenant: str, workspace: str, user_id: str | None=None) -> StepResult:
        """Store tokens securely.

        Args:
            access_token: Access token
            refresh_token: Refresh token
            expires_in: Token expiration in seconds
            scope: Granted scopes
            tenant: Tenant identifier
            workspace: Workspace identifier
            user_id: Platform user ID

        Returns:
            StepResult indicating success or failure
        """
        if not self.token_storage:
            return StepResult.fail('Token storage not configured')
        try:
            expires_at = None
            if expires_in:
                expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            return self.token_storage.store_tokens(platform=self.platform, tenant=tenant, workspace=workspace, user_id=user_id, access_token=access_token, refresh_token=refresh_token, expires_at=expires_at, scope=scope)
        except Exception as e:
            logger.error(f'Failed to store tokens for {self.platform}: {e!s}')
            return StepResult.fail(f'Token storage failed: {e!s}')

    def get_stored_tokens(self, tenant: str, workspace: str, user_id: str | None=None) -> StepResult:
        """Get stored tokens.

        Args:
            tenant: Tenant identifier
            workspace: Workspace identifier
            user_id: Platform user ID

        Returns:
            StepResult with token data
        """
        if not self.token_storage:
            return StepResult.fail('Token storage not configured')
        try:
            return self.token_storage.get_tokens(platform=self.platform, tenant=tenant, workspace=workspace, user_id=user_id)
        except Exception as e:
            logger.error(f'Failed to get tokens for {self.platform}: {e!s}')
            return StepResult.fail(f'Token retrieval failed: {e!s}')

class YouTubeOAuthManager(OAuthManager):
    """OAuth manager for YouTube Data API."""

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str, scopes: list[str] | None=None, token_storage: TokenStorage | None=None) -> None:
        """Initialize YouTube OAuth manager."""
        if scopes is None:
            scopes = ['https://www.googleapis.com/auth/youtube.readonly']
        super().__init__(platform='youtube', client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, scopes=scopes, token_storage=token_storage)
        self.auth_url = 'https://accounts.google.com/o/oauth2/v2/auth'
        self.token_url = 'https://oauth2.googleapis.com/token'
        self.revoke_url = 'https://oauth2.googleapis.com/revoke'

    def get_authorization_url(self, state: str | None=None) -> str:
        """Get YouTube authorization URL."""
        params = {'client_id': self.client_id, 'redirect_uri': self.redirect_uri, 'scope': ' '.join(self.scopes), 'response_type': 'code', 'access_type': 'offline', 'prompt': 'consent'}
        if state:
            params['state'] = state
        return f'{self.auth_url}?{urlencode(params)}'

    def exchange_code_for_tokens(self, code: str) -> StepResult:
        """Exchange authorization code for YouTube tokens."""
        try:
            data = {'client_id': self.client_id, 'client_secret': self.client_secret, 'code': code, 'grant_type': 'authorization_code', 'redirect_uri': self.redirect_uri}
            response = resilient_post(self.token_url, data=data, timeout=30)
            response.raise_for_status()
            token_data = response.json()
            return StepResult.ok(data={'access_token': token_data['access_token'], 'refresh_token': token_data.get('refresh_token'), 'expires_in': token_data.get('expires_in'), 'scope': token_data.get('scope'), 'token_type': token_data.get('token_type', 'Bearer')})
        except requests.exceptions.RequestException as e:
            logger.error(f'YouTube token exchange failed: {e!s}')
            return StepResult.fail(f'Token exchange failed: {e!s}')

    def refresh_access_token(self, refresh_token: str) -> StepResult:
        """Refresh YouTube access token."""
        try:
            data = {'client_id': self.client_id, 'client_secret': self.client_secret, 'refresh_token': refresh_token, 'grant_type': 'refresh_token'}
            response = resilient_post(self.token_url, data=data, timeout=30)
            response.raise_for_status()
            token_data = response.json()
            return StepResult.ok(data={'access_token': token_data['access_token'], 'expires_in': token_data.get('expires_in'), 'scope': token_data.get('scope'), 'token_type': token_data.get('token_type', 'Bearer')})
        except requests.exceptions.RequestException as e:
            logger.error(f'YouTube token refresh failed: {e!s}')
            return StepResult.fail(f'Token refresh failed: {e!s}')

    def validate_token(self, access_token: str) -> StepResult:
        """Validate YouTube access token."""
        try:
            headers = {'Authorization': f'Bearer {access_token}'}
            url = 'https://www.googleapis.com/oauth2/v1/tokeninfo'
            response = resilient_get(url, headers=headers, timeout=30)
            response.raise_for_status()
            token_info = response.json()
            return StepResult.ok(data={'valid': True, 'expires_in': token_info.get('expires_in'), 'scope': token_info.get('scope'), 'audience': token_info.get('audience')})
        except requests.exceptions.RequestException as e:
            logger.error(f'YouTube token validation failed: {e!s}')
            return StepResult.fail(f'Token validation failed: {e!s}')

class TwitchOAuthManager(OAuthManager):
    """OAuth manager for Twitch API."""

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str, scopes: list[str] | None=None, token_storage: TokenStorage | None=None) -> None:
        """Initialize Twitch OAuth manager."""
        if scopes is None:
            scopes = ['user:read:email', 'channel:read:stream_key']
        super().__init__(platform='twitch', client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, scopes=scopes, token_storage=token_storage)
        self.auth_url = 'https://id.twitch.tv/oauth2/authorize'
        self.token_url = 'https://id.twitch.tv/oauth2/token'
        self.validate_url = 'https://id.twitch.tv/oauth2/validate'

    def get_authorization_url(self, state: str | None=None) -> str:
        """Get Twitch authorization URL."""
        params = {'client_id': self.client_id, 'redirect_uri': self.redirect_uri, 'response_type': 'code', 'scope': ' '.join(self.scopes)}
        if state:
            params['state'] = state
        return f'{self.auth_url}?{urlencode(params)}'

    def exchange_code_for_tokens(self, code: str) -> StepResult:
        """Exchange authorization code for Twitch tokens."""
        try:
            data = {'client_id': self.client_id, 'client_secret': self.client_secret, 'code': code, 'grant_type': 'authorization_code', 'redirect_uri': self.redirect_uri}
            response = resilient_post(self.token_url, data=data, timeout=30)
            response.raise_for_status()
            token_data = response.json()
            return StepResult.ok(data={'access_token': token_data['access_token'], 'refresh_token': token_data.get('refresh_token'), 'expires_in': token_data.get('expires_in'), 'scope': token_data.get('scope'), 'token_type': token_data.get('token_type', 'Bearer')})
        except requests.exceptions.RequestException as e:
            logger.error(f'Twitch token exchange failed: {e!s}')
            return StepResult.fail(f'Token exchange failed: {e!s}')

    def refresh_access_token(self, refresh_token: str) -> StepResult:
        """Refresh Twitch access token."""
        try:
            data = {'client_id': self.client_id, 'client_secret': self.client_secret, 'refresh_token': refresh_token, 'grant_type': 'refresh_token'}
            response = resilient_post(self.token_url, data=data, timeout=30)
            response.raise_for_status()
            token_data = response.json()
            return StepResult.ok(data={'access_token': token_data['access_token'], 'expires_in': token_data.get('expires_in'), 'scope': token_data.get('scope'), 'token_type': token_data.get('token_type', 'Bearer')})
        except requests.exceptions.RequestException as e:
            logger.error(f'Twitch token refresh failed: {e!s}')
            return StepResult.fail(f'Token refresh failed: {e!s}')

    def validate_token(self, access_token: str) -> StepResult:
        """Validate Twitch access token."""
        try:
            headers = {'Authorization': f'OAuth {access_token}'}
            response = resilient_get(self.validate_url, headers=headers, timeout=30)
            response.raise_for_status()
            token_info = response.json()
            return StepResult.ok(data={'valid': True, 'expires_in': token_info.get('expires_in'), 'scope': token_info.get('scopes'), 'user_id': token_info.get('user_id'), 'login': token_info.get('login')})
        except requests.exceptions.RequestException as e:
            logger.error(f'Twitch token validation failed: {e!s}')
            return StepResult.fail(f'Token validation failed: {e!s}')

class TikTokOAuthManager(OAuthManager):
    """OAuth manager for TikTok API."""

    def __init__(self, client_key: str, client_secret: str, redirect_uri: str, scopes: list[str] | None=None, token_storage: TokenStorage | None=None) -> None:
        """Initialize TikTok OAuth manager."""
        if scopes is None:
            scopes = ['user.info.basic', 'video.list']
        super().__init__(platform='tiktok', client_id=client_key, client_secret=client_secret, redirect_uri=redirect_uri, scopes=scopes, token_storage=token_storage)
        self.auth_url = 'https://www.tiktok.com/auth/authorize'
        self.token_url = 'https://open-api.tiktok.com/oauth/access_token'

    def get_authorization_url(self, state: str | None=None) -> str:
        """Get TikTok authorization URL."""
        params = {'client_key': self.client_id, 'response_type': 'code', 'scope': ','.join(self.scopes), 'redirect_uri': self.redirect_uri}
        if state:
            params['state'] = state
        return f'{self.auth_url}?{urlencode(params)}'

    def exchange_code_for_tokens(self, code: str) -> StepResult:
        """Exchange authorization code for TikTok tokens."""
        try:
            data = {'client_key': self.client_id, 'client_secret': self.client_secret, 'code': code, 'grant_type': 'authorization_code', 'redirect_uri': self.redirect_uri}
            response = resilient_post(self.token_url, data=data, timeout=30)
            response.raise_for_status()
            token_data = response.json()
            if token_data.get('error'):
                return StepResult.fail(f'TikTok API error: {token_data['error']}')
            return StepResult.ok(data={'access_token': token_data['access_token'], 'refresh_token': token_data.get('refresh_token'), 'expires_in': token_data.get('expires_in'), 'scope': token_data.get('scope'), 'token_type': 'Bearer'})
        except requests.exceptions.RequestException as e:
            logger.error(f'TikTok token exchange failed: {e!s}')
            return StepResult.fail(f'Token exchange failed: {e!s}')

    def refresh_access_token(self, refresh_token: str) -> StepResult:
        """Refresh TikTok access token."""
        try:
            data = {'client_key': self.client_id, 'client_secret': self.client_secret, 'refresh_token': refresh_token, 'grant_type': 'refresh_token'}
            response = resilient_post(self.token_url, data=data, timeout=30)
            response.raise_for_status()
            token_data = response.json()
            if token_data.get('error'):
                return StepResult.fail(f'TikTok API error: {token_data['error']}')
            return StepResult.ok(data={'access_token': token_data['access_token'], 'expires_in': token_data.get('expires_in'), 'scope': token_data.get('scope'), 'token_type': 'Bearer'})
        except requests.exceptions.RequestException as e:
            logger.error(f'TikTok token refresh failed: {e!s}')
            return StepResult.fail(f'Token refresh failed: {e!s}')

    def validate_token(self, access_token: str) -> StepResult:
        """Validate TikTok access token."""
        try:
            headers = {'Authorization': f'Bearer {access_token}'}
            url = 'https://open-api.tiktok.com/user/info/'
            response = resilient_get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                return StepResult.ok(data={'valid': True})
            else:
                return StepResult.ok(data={'valid': False, 'error': response.text})
        except requests.exceptions.RequestException as e:
            logger.error(f'TikTok token validation failed: {e!s}')
            return StepResult.fail(f'Token validation failed: {e!s}')

class InstagramOAuthManager(OAuthManager):
    """OAuth manager for Instagram Graph API."""

    def __init__(self, app_id: str, app_secret: str, redirect_uri: str, scopes: list[str] | None=None, token_storage: TokenStorage | None=None) -> None:
        """Initialize Instagram OAuth manager."""
        if scopes is None:
            scopes = ['instagram_basic', 'instagram_manage_insights']
        super().__init__(platform='instagram', client_id=app_id, client_secret=app_secret, redirect_uri=redirect_uri, scopes=scopes, token_storage=token_storage)
        self.auth_url = 'https://www.facebook.com/v18.0/dialog/oauth'
        self.token_url = 'https://graph.facebook.com/v18.0/oauth/access_token'
        self.long_lived_token_url = 'https://graph.facebook.com/v18.0/oauth/access_token'

    def get_authorization_url(self, state: str | None=None) -> str:
        """Get Instagram authorization URL."""
        params = {'client_id': self.client_id, 'redirect_uri': self.redirect_uri, 'scope': ','.join(self.scopes), 'response_type': 'code'}
        if state:
            params['state'] = state
        return f'{self.auth_url}?{urlencode(params)}'

    def exchange_code_for_tokens(self, code: str) -> StepResult:
        """Exchange authorization code for Instagram tokens."""
        try:
            data = {'client_id': self.client_id, 'client_secret': self.client_secret, 'code': code, 'grant_type': 'authorization_code', 'redirect_uri': self.redirect_uri}
            response = resilient_post(self.token_url, data=data, timeout=30)
            response.raise_for_status()
            token_data = response.json()
            if 'error' in token_data:
                return StepResult.fail(f'Instagram API error: {token_data['error']}')
            long_lived_data = {'grant_type': 'fb_exchange_token', 'client_id': self.client_id, 'client_secret': self.client_secret, 'fb_exchange_token': token_data['access_token']}
            long_lived_response = resilient_post(self.long_lived_token_url, data=long_lived_data, timeout=30)
            long_lived_response.raise_for_status()
            long_lived_token_data = long_lived_response.json()
            return StepResult.ok(data={'access_token': long_lived_token_data['access_token'], 'expires_in': long_lived_token_data.get('expires_in', 5184000), 'scope': ','.join(self.scopes), 'token_type': 'Bearer'})
        except requests.exceptions.RequestException as e:
            logger.error(f'Instagram token exchange failed: {e!s}')
            return StepResult.fail(f'Token exchange failed: {e!s}')

    def refresh_access_token(self, refresh_token: str) -> StepResult:
        """Refresh Instagram access token (not supported by Instagram)."""
        return StepResult.fail('Instagram does not support token refresh. Re-authentication required.')

    def validate_token(self, access_token: str) -> StepResult:
        """Validate Instagram access token."""
        try:
            url = f'https://graph.facebook.com/v18.0/me?access_token={access_token}'
            response = resilient_get(url, timeout=30)
            response.raise_for_status()
            token_info = response.json()
            return StepResult.ok(data={'valid': True, 'user_id': token_info.get('id'), 'name': token_info.get('name')})
        except requests.exceptions.RequestException as e:
            logger.error(f'Instagram token validation failed: {e!s}')
            return StepResult.fail(f'Token validation failed: {e!s}')

class XOAuthManager(OAuthManager):
    """OAuth manager for X (Twitter) API v2."""

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str, scopes: list[str] | None=None, token_storage: TokenStorage | None=None) -> None:
        """Initialize X OAuth manager."""
        if scopes is None:
            scopes = ['tweet.read', 'users.read', 'offline.access']
        super().__init__(platform='x', client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, scopes=scopes, token_storage=token_storage)
        self.auth_url = 'https://twitter.com/i/oauth2/authorize'
        self.token_url = 'https://api.twitter.com/2/oauth2/token'

    def get_authorization_url(self, state: str | None=None) -> str:
        """Get X authorization URL."""
        params = {'response_type': 'code', 'client_id': self.client_id, 'redirect_uri': self.redirect_uri, 'scope': ' '.join(self.scopes), 'code_challenge': 'challenge', 'code_challenge_method': 'plain'}
        if state:
            params['state'] = state
        return f'{self.auth_url}?{urlencode(params)}'

    def exchange_code_for_tokens(self, code: str) -> StepResult:
        """Exchange authorization code for X tokens."""
        try:
            data = {'code': code, 'grant_type': 'authorization_code', 'client_id': self.client_id, 'redirect_uri': self.redirect_uri, 'code_verifier': 'challenge'}
            auth = (self.client_id, self.client_secret)
            response = resilient_post(self.token_url, data=data, auth=auth, timeout=30)
            response.raise_for_status()
            token_data = response.json()
            return StepResult.ok(data={'access_token': token_data['access_token'], 'refresh_token': token_data.get('refresh_token'), 'expires_in': token_data.get('expires_in'), 'scope': token_data.get('scope'), 'token_type': token_data.get('token_type', 'Bearer')})
        except requests.exceptions.RequestException as e:
            logger.error(f'X token exchange failed: {e!s}')
            return StepResult.fail(f'Token exchange failed: {e!s}')

    def refresh_access_token(self, refresh_token: str) -> StepResult:
        """Refresh X access token."""
        try:
            data = {'refresh_token': refresh_token, 'grant_type': 'refresh_token', 'client_id': self.client_id}
            auth = (self.client_id, self.client_secret)
            response = resilient_post(self.token_url, data=data, auth=auth, timeout=30)
            response.raise_for_status()
            token_data = response.json()
            return StepResult.ok(data={'access_token': token_data['access_token'], 'refresh_token': token_data.get('refresh_token'), 'expires_in': token_data.get('expires_in'), 'scope': token_data.get('scope'), 'token_type': token_data.get('token_type', 'Bearer')})
        except requests.exceptions.RequestException as e:
            logger.error(f'X token refresh failed: {e!s}')
            return StepResult.fail(f'Token refresh failed: {e!s}')

    def validate_token(self, access_token: str) -> StepResult:
        """Validate X access token."""
        try:
            headers = {'Authorization': f'Bearer {access_token}'}
            url = 'https://api.twitter.com/2/users/me'
            response = resilient_get(url, headers=headers, timeout=30)
            response.raise_for_status()
            token_info = response.json()
            return StepResult.ok(data={'valid': True, 'user_id': token_info.get('data', {}).get('id'), 'username': token_info.get('data', {}).get('username')})
        except requests.exceptions.RequestException as e:
            logger.error(f'X token validation failed: {e!s}')
            return StepResult.fail(f'Token validation failed: {e!s}')