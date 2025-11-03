"""Tests for configuration."""

from unittest.mock import patch

from ultimate_discord_intelligence_bot.settings import get_settings


class TestConfiguration:
    """Test cases for configuration."""

    def test_get_settings(self):
        """Test settings retrieval."""
        settings = get_settings()
        assert settings is not None
        assert hasattr(settings, "DISCORD_BOT_TOKEN")
        assert hasattr(settings, "OPENAI_API_KEY")
        assert hasattr(settings, "QDRANT_URL")

    def test_environment_variables(self):
        """Test environment variable loading."""
        with patch.dict(
            "os.environ",
            {"DISCORD_BOT_TOKEN": "test_token", "OPENAI_API_KEY": "test_key", "QDRANT_URL": "http://localhost:6333"},
        ):
            settings = get_settings()
            assert settings.DISCORD_BOT_TOKEN == "test_token"
            assert settings.OPENAI_API_KEY == "test_key"
            assert settings.QDRANT_URL == "http://localhost:6333"

    def test_default_values(self):
        """Test default configuration values."""
        settings = get_settings()
        assert settings.LOG_LEVEL == "INFO"
        assert settings.ENVIRONMENT == "development"
        assert not settings.TESTING

    def test_feature_flags(self):
        """Test feature flag configuration."""
        with patch.dict("os.environ", {"ENABLE_DEBATE_ANALYSIS": "true", "ENABLE_FACT_CHECKING": "false"}):
            settings = get_settings()
            assert settings.ENABLE_DEBATE_ANALYSIS
            assert not settings.ENABLE_FACT_CHECKING

    def test_database_configuration(self):
        """Test database configuration."""
        with patch.dict(
            "os.environ",
            {"POSTGRES_URL": "postgresql://test:test@localhost:5432/test", "REDIS_URL": "redis://localhost:6379"},
        ):
            settings = get_settings()
            assert settings.POSTGRES_URL == "postgresql://test:test@localhost:5432/test"
            assert settings.REDIS_URL == "redis://localhost:6379"

    def test_security_configuration(self):
        """Test security configuration."""
        with patch.dict("os.environ", {"SECRET_KEY": "test_secret_key", "ALLOWED_HOSTS": "localhost,127.0.0.1"}):
            settings = get_settings()
            assert settings.SECRET_KEY == "test_secret_key"
            assert settings.ALLOWED_HOSTS == "localhost,127.0.0.1"

    def test_monitoring_configuration(self):
        """Test monitoring configuration."""
        with patch.dict("os.environ", {"ENABLE_METRICS": "true", "METRICS_PORT": "9090"}):
            settings = get_settings()
            assert settings.ENABLE_METRICS
            assert settings.METRICS_PORT == 9090

    def test_validation(self):
        """Test configuration validation."""
        settings = get_settings()
        assert settings.DISCORD_BOT_TOKEN is not None
        assert settings.OPENAI_API_KEY is not None
        assert settings.QDRANT_URL is not None
        assert isinstance(settings.LOG_LEVEL, str)
        assert isinstance(settings.ENVIRONMENT, str)
        assert isinstance(settings.TESTING, bool)

    def test_tenant_configuration(self):
        """Test tenant configuration."""
        with patch.dict("os.environ", {"DEFAULT_TENANT": "default_tenant", "DEFAULT_WORKSPACE": "default_workspace"}):
            settings = get_settings()
            assert settings.DEFAULT_TENANT == "default_tenant"
            assert settings.DEFAULT_WORKSPACE == "default_workspace"

    def test_performance_configuration(self):
        """Test performance configuration."""
        with patch.dict("os.environ", {"MAX_CONCURRENT_REQUESTS": "100", "REQUEST_TIMEOUT": "30"}):
            settings = get_settings()
            assert settings.MAX_CONCURRENT_REQUESTS == 100
            assert settings.REQUEST_TIMEOUT == 30
