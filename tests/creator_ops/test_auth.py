"""
Tests for Creator Operations authentication and OAuth framework.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from ultimate_discord_intelligence_bot.creator_ops.auth.audit import AuditLogger
from ultimate_discord_intelligence_bot.creator_ops.auth.oauth_manager import (
    InstagramOAuthManager,
    TikTokOAuthManager,
    TwitchOAuthManager,
    XOAuthManager,
    YouTubeOAuthManager,
)
from ultimate_discord_intelligence_bot.creator_ops.auth.scopes import ScopeValidator
from ultimate_discord_intelligence_bot.creator_ops.auth.token_storage import TokenStorage


class TestOAuthManager:
    """Test OAuth manager implementations."""

    def test_youtube_oauth_manager_initialization(self):
        """Test YouTube OAuth manager initialization."""
        manager = YouTubeOAuthManager(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="http://localhost:8000/callback",
        )

        assert manager.platform == "youtube"
        assert manager.client_id == "test_client_id"
        assert manager.client_secret == "test_client_secret"
        assert "youtube.readonly" in manager.scopes[0]

    def test_youtube_authorization_url(self):
        """Test YouTube authorization URL generation."""
        manager = YouTubeOAuthManager(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="http://localhost:8000/callback",
        )

        url = manager.get_authorization_url(state="test_state")

        assert "accounts.google.com" in url
        assert "client_id=test_client_id" in url
        assert "state=test_state" in url
        assert "response_type=code" in url

    @patch('requests.post')
    def test_youtube_token_exchange_success(self, mock_post):
        """Test successful YouTube token exchange."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_in": 3600,
            "scope": "https://www.googleapis.com/auth/youtube.readonly",
            "token_type": "Bearer",
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        manager = YouTubeOAuthManager(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="http://localhost:8000/callback",
        )

        result = manager.exchange_code_for_tokens("test_code")

        assert result.success
        assert result.data["access_token"] == "test_access_token"
        assert result.data["refresh_token"] == "test_refresh_token"

    @patch('requests.post')
    def test_youtube_token_exchange_failure(self, mock_post):
        """Test failed YouTube token exchange."""
        mock_post.side_effect = Exception("Network error")

        manager = YouTubeOAuthManager(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="http://localhost:8000/callback",
        )

        result = manager.exchange_code_for_tokens("test_code")

        assert not result.success
        assert "Token exchange failed" in result.error

    def test_twitch_oauth_manager_initialization(self):
        """Test Twitch OAuth manager initialization."""
        manager = TwitchOAuthManager(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="http://localhost:8000/callback",
        )

        assert manager.platform == "twitch"
        assert "user:read:email" in manager.scopes

    def test_tiktok_oauth_manager_initialization(self):
        """Test TikTok OAuth manager initialization."""
        manager = TikTokOAuthManager(
            client_key="test_client_key",
            client_secret="test_client_secret",
            redirect_uri="http://localhost:8000/callback",
        )

        assert manager.platform == "tiktok"
        assert "user.info.basic" in manager.scopes

    def test_instagram_oauth_manager_initialization(self):
        """Test Instagram OAuth manager initialization."""
        manager = InstagramOAuthManager(
            app_id="test_app_id",
            app_secret="test_app_secret",
            redirect_uri="http://localhost:8000/callback",
        )

        assert manager.platform == "instagram"
        assert "instagram_basic" in manager.scopes

    def test_x_oauth_manager_initialization(self):
        """Test X OAuth manager initialization."""
        manager = XOAuthManager(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="http://localhost:8000/callback",
        )

        assert manager.platform == "x"
        assert "tweet.read" in manager.scopes


class TestTokenStorage:
    """Test token storage functionality."""

    def test_token_storage_initialization(self):
        """Test token storage initialization."""
        with patch('sqlalchemy.create_engine'):
            storage = TokenStorage(
                database_url="sqlite:///:memory:",
                encryption_key="test_key",
            )

            assert storage is not None
            assert storage.vault is not None

    @patch('sqlalchemy.create_engine')
    @patch('sqlalchemy.orm.sessionmaker')
    def test_store_tokens_success(self, mock_sessionmaker, mock_engine):
        """Test successful token storage."""
        # Mock session
        mock_session = Mock()
        mock_sessionmaker.return_value.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        storage = TokenStorage(
            database_url="sqlite:///:memory:",
            encryption_key="test_key",
        )

        result = storage.store_tokens(
            platform="youtube",
            tenant="test_tenant",
            workspace="test_workspace",
            user_id="test_user",
            access_token="test_token",
            refresh_token="test_refresh",
            expires_at=datetime.utcnow() + timedelta(hours=1),
            scope="readonly",
        )

        assert result.success
        assert result.data["platform"] == "youtube"

    @patch('sqlalchemy.create_engine')
    @patch('sqlalchemy.orm.sessionmaker')
    def test_get_tokens_success(self, mock_sessionmaker, mock_engine):
        """Test successful token retrieval."""
        # Mock account
        mock_account = Mock()
        mock_account.id = 1
        mock_account.platform_id = "test_user"
        mock_account.handle = "@test"
        mock_account.display_name = "Test User"
        mock_account.access_token_encrypted = "encrypted_token"
        mock_account.refresh_token_encrypted = "encrypted_refresh"
        mock_account.token_expires_at = datetime.utcnow() + timedelta(hours=1)
        mock_account.oauth_scopes = "readonly"
        mock_account.is_active = True

        # Mock session
        mock_session = Mock()
        mock_sessionmaker.return_value.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_account

        storage = TokenStorage(
            database_url="sqlite:///:memory:",
            encryption_key="test_key",
        )

        # Mock vault decryption
        with patch.object(storage.vault, 'decrypt_secret', return_value="decrypted_token"):
            result = storage.get_tokens(
                platform="youtube",
                tenant="test_tenant",
                workspace="test_workspace",
                user_id="test_user",
            )

        assert result.success
        assert result.data["access_token"] == "decrypted_token"

    @patch('sqlalchemy.create_engine')
    @patch('sqlalchemy.orm.sessionmaker')
    def test_get_tokens_not_found(self, mock_sessionmaker, mock_engine):
        """Test token retrieval when not found."""
        # Mock session
        mock_session = Mock()
        mock_sessionmaker.return_value.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        storage = TokenStorage(
            database_url="sqlite:///:memory:",
            encryption_key="test_key",
        )

        result = storage.get_tokens(
            platform="youtube",
            tenant="test_tenant",
            workspace="test_workspace",
            user_id="test_user",
        )

        assert not result.success
        assert "No tokens found" in result.error


class TestScopeValidator:
    """Test scope validation functionality."""

    def test_scope_validator_initialization(self):
        """Test scope validator initialization."""
        validator = ScopeValidator()

        assert "youtube" in validator.required_scopes
        assert "twitch" in validator.required_scopes
        assert "tiktok" in validator.required_scopes
        assert "instagram" in validator.required_scopes
        assert "x" in validator.required_scopes

    def test_validate_scopes_success(self):
        """Test successful scope validation."""
        validator = ScopeValidator()

        result = validator.validate_scopes(
            platform="youtube",
            requested_scopes=["https://www.googleapis.com/auth/youtube.readonly"],
            purpose="readonly",
        )

        assert result.success
        assert result.data["valid"] is True

    def test_validate_scopes_missing_required(self):
        """Test scope validation with missing required scopes."""
        validator = ScopeValidator()

        result = validator.validate_scopes(
            platform="youtube",
            requested_scopes=[],
            purpose="readonly",
        )

        assert not result.success
        assert "Missing required scopes" in result.error

    def test_validate_scopes_unknown_platform(self):
        """Test scope validation with unknown platform."""
        validator = ScopeValidator()

        result = validator.validate_scopes(
            platform="unknown",
            requested_scopes=["test_scope"],
            purpose="readonly",
        )

        assert not result.success
        assert "Unknown platform" in result.error

    def test_get_scope_descriptions(self):
        """Test getting scope descriptions."""
        validator = ScopeValidator()

        descriptions = validator.get_scope_descriptions([
            "https://www.googleapis.com/auth/youtube.readonly",
            "user:read:email",
        ])

        assert len(descriptions) == 2
        assert "Read YouTube channel and video data" in descriptions["https://www.googleapis.com/auth/youtube.readonly"]

    def test_is_scope_sensitive(self):
        """Test checking if scope is sensitive."""
        validator = ScopeValidator()

        # Test sensitive scope
        assert validator.is_scope_sensitive("youtube", "https://www.googleapis.com/auth/youtube")

        # Test non-sensitive scope
        assert not validator.is_scope_sensitive("youtube", "https://www.googleapis.com/auth/youtube.readonly")

    def test_get_minimal_scopes(self):
        """Test getting minimal scopes."""
        validator = ScopeValidator()

        scopes = validator.get_minimal_scopes("youtube", "readonly")

        assert len(scopes) == 1
        assert "https://www.googleapis.com/auth/youtube.readonly" in scopes

    def test_audit_scope_request(self):
        """Test scope request auditing."""
        validator = ScopeValidator()

        result = validator.audit_scope_request(
            platform="youtube",
            requested_scopes=["https://www.googleapis.com/auth/youtube.readonly"],
            purpose="readonly",
            tenant="test_tenant",
            workspace="test_workspace",
            user_id="test_user",
        )

        assert result.success
        assert "audit_record" in result.data
        assert result.data["audit_record"]["platform"] == "youtube"


class TestAuditLogger:
    """Test audit logging functionality."""

    def test_audit_logger_initialization(self):
        """Test audit logger initialization."""
        logger = AuditLogger()

        assert logger is not None
        assert logger.audit_logger is not None

    def test_log_oauth_authorization_request(self):
        """Test logging OAuth authorization request."""
        logger = AuditLogger()

        # Should not raise an exception
        logger.log_oauth_authorization_request(
            platform="youtube",
            tenant="test_tenant",
            workspace="test_workspace",
            scopes=["readonly"],
            purpose="content_analysis",
            user_id="test_user",
            client_ip="127.0.0.1",
        )

    def test_log_oauth_authorization_success(self):
        """Test logging OAuth authorization success."""
        logger = AuditLogger()

        # Should not raise an exception
        logger.log_oauth_authorization_success(
            platform="youtube",
            tenant="test_tenant",
            workspace="test_workspace",
            user_id="test_user",
            scopes=["readonly"],
            token_expires_at=datetime.utcnow() + timedelta(hours=1),
        )

    def test_log_oauth_authorization_failure(self):
        """Test logging OAuth authorization failure."""
        logger = AuditLogger()

        # Should not raise an exception
        logger.log_oauth_authorization_failure(
            platform="youtube",
            tenant="test_tenant",
            workspace="test_workspace",
            error="Invalid client credentials",
            user_id="test_user",
            scopes=["readonly"],
        )

    def test_log_token_refresh(self):
        """Test logging token refresh."""
        logger = AuditLogger()

        # Should not raise an exception
        logger.log_token_refresh(
            platform="youtube",
            tenant="test_tenant",
            workspace="test_workspace",
            user_id="test_user",
            success=True,
            new_expires_at=datetime.utcnow() + timedelta(hours=1),
        )

    def test_log_security_event(self):
        """Test logging security event."""
        logger = AuditLogger()

        # Should not raise an exception
        logger.log_security_event(
            event_type="suspicious_activity",
            platform="youtube",
            tenant="test_tenant",
            workspace="test_workspace",
            user_id="test_user",
            details={"activity": "multiple_failed_attempts"},
            severity="high",
        )

    def test_get_audit_events(self):
        """Test getting audit events."""
        logger = AuditLogger()

        result = logger.get_audit_events(
            tenant="test_tenant",
            workspace="test_workspace",
        )

        assert result.success
        assert "events" in result.data

    def test_export_audit_log(self):
        """Test exporting audit log."""
        logger = AuditLogger()

        result = logger.export_audit_log(
            tenant="test_tenant",
            workspace="test_workspace",
            format="json",
        )

        assert result.success
        assert "export_data" in result.data
        assert result.data["format"] == "json"
