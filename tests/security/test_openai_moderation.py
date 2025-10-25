"""Tests for OpenAI moderation service."""

from unittest.mock import MagicMock, patch

import pytest


try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None


class TestOpenAIModerationService:
    """Test cases for OpenAI moderation service."""

    @pytest.fixture
    def service(self):
        """Create OpenAI moderation service instance."""
        from src.security.openai_moderation import OpenAIModerationService
        return OpenAIModerationService(api_key="test_key")

    def test_service_initialization(self, service):
        """Test service initialization."""
        assert service is not None

    @pytest.mark.skipif(not OPENAI_AVAILABLE, reason="OpenAI not available")
    def test_check_content_flagged(self, service):
        """Test content check with flagged content."""
        # Mock OpenAI API response
        mock_response = MagicMock()
        mock_result = MagicMock()
        mock_result.flagged = True
        mock_result.categories.hate = True
        mock_result.categories.violence = False
        mock_result.category_scores.hate = 0.95
        mock_result.category_scores.violence = 0.1
        mock_response.results = [mock_result]

        with patch.object(service.client.moderations, 'create', return_value=mock_response):
            result = service.check_content("hateful content")

            assert result.flagged is True
            assert result.action == "block"
            assert result.categories["hate"] is True

    @pytest.mark.skipif(not OPENAI_AVAILABLE, reason="OpenAI not available")
    def test_check_content_allowed(self, service):
        """Test content check with allowed content."""
        mock_response = MagicMock()
        mock_result = MagicMock()
        mock_result.flagged = False
        mock_result.categories.hate = False
        mock_result.category_scores.hate = 0.1
        mock_response.results = [mock_result]

        with patch.object(service.client.moderations, 'create', return_value=mock_response):
            result = service.check_content("safe content")

            assert result.flagged is False
            assert result.action == "allow"

    def test_check_content_fallback(self):
        """Test content check fallback when OpenAI unavailable."""
        from src.security.openai_moderation import OpenAIModerationService

        # Service without OpenAI client
        service = OpenAIModerationService(api_key=None)
        result = service.check_content("test content")

        # Should allow content on fallback
        assert result.flagged is False
        assert result.action == "allow"

    @pytest.mark.skipif(not OPENAI_AVAILABLE, reason="OpenAI not available")
    def test_check_batch(self, service):
        """Test batch content checking."""
        mock_response = MagicMock()
        mock_result1 = MagicMock()
        mock_result1.flagged = False
        mock_result1.categories.hate = False
        mock_result1.category_scores.hate = 0.1

        mock_result2 = MagicMock()
        mock_result2.flagged = True
        mock_result2.categories.violence = True
        mock_result2.category_scores.violence = 0.9

        mock_response.results = [mock_result1, mock_result2]

        with patch.object(service.client.moderations, 'create', return_value=mock_response):
            results = service.check_batch(["safe content", "violent content"])

            assert len(results) == 2
            assert results[0].flagged is False
            assert results[1].flagged is True
