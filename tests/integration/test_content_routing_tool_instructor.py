"""Integration tests for ContentTypeRoutingTool with Instructor support.

Tests both LLM-based classification and pattern-matching fallback behavior.
"""

import importlib.util
import sys
from unittest.mock import MagicMock, Mock, patch

import pytest


# Test if instructor is available
try:
    import instructor  # noqa: F401 - imported for availability check

    INSTRUCTOR_AVAILABLE = True
except ImportError:
    INSTRUCTOR_AVAILABLE = False

from ai.response_models import ContentType, ContentTypeClassification


# Import module directly to avoid observability __init__.py triggering crewai imports
spec = importlib.util.spec_from_file_location(
    "content_type_routing_tool",
    "/home/crew/src/ultimate_discord_intelligence_bot/tools/observability/content_type_routing_tool.py",
)
content_routing_module = importlib.util.module_from_spec(spec)
sys.modules["content_type_routing_tool"] = content_routing_module
spec.loader.exec_module(content_routing_module)
ContentTypeRoutingTool = content_routing_module.ContentTypeRoutingTool


class TestContentTypeRoutingToolInstructor:
    """Test suite for ContentTypeRoutingTool with Instructor integration."""

    @pytest.fixture
    def mock_config_enabled(self):
        """Mock SecureConfig with Instructor enabled."""
        config = Mock()
        config.enable_instructor = True
        config.instructor_max_retries = 3
        config.instructor_timeout = 30.0
        config.openrouter_api_key = "test-api-key"
        config.openrouter_llm_model = "anthropic/claude-3.5-sonnet"
        
        with patch("content_type_routing_tool.get_config", return_value=config), \
             patch("platform.rl.structured_outputs.get_config", return_value=config):
            yield config

    @pytest.fixture
    def mock_config_disabled(self):
        """Mock SecureConfig with Instructor disabled."""
        config = Mock()
        config.enable_instructor = False
        config.openrouter_api_key = "test-api-key"
        config.openrouter_llm_model = "anthropic/claude-3.5-sonnet"
        
        with patch("content_type_routing_tool.get_config", return_value=config), \
             patch("platform.rl.structured_outputs.get_config", return_value=config):
            yield config

    @pytest.fixture
    def sample_educational_input(self):
        """Sample educational content input."""
        return {
            "transcript": "In this tutorial, we'll learn about Python programming. "
            "First, let's understand the basic concepts of variables and data types. "
            "A variable is a named location in memory that stores a value.",
            "title": "Python Programming Tutorial for Beginners",
            "description": "Learn Python programming from scratch with this comprehensive tutorial",
            "metadata": {"duration": 1200, "views": 5000},
        }

    @pytest.fixture
    def sample_entertainment_input(self):
        """Sample entertainment content input."""
        return {
            "transcript": "Ha ha ha! That was hilarious! This comedy show is so funny. "
            "The actors are amazing and the jokes keep coming. "
            "I can't stop laughing at this scene.",
            "title": "Funniest Comedy Moments Compilation",
            "description": "Watch the funniest moments from our favorite comedy shows",
            "metadata": {"duration": 600, "views": 100000},
        }

    def test_pattern_matching_fallback_when_instructor_disabled(self, mock_config_disabled, sample_educational_input):
        """Should use pattern-matching when Instructor is disabled."""
        # Create tool AFTER mocking config so __init__ picks up the mock
        tool = ContentTypeRoutingTool()
        result = tool.run(sample_educational_input)

        assert result.success
        assert result.data is not None
        assert "result" in result.data
        assert "classification" in result.data["result"]
        assert result.data["result"].get("analysis_method") == "pattern_matching"
        assert result.data["result"]["classification"]["primary_type"] in ["educational", "general"]

    @pytest.mark.skipif(not INSTRUCTOR_AVAILABLE, reason="Instructor not installed")
    def test_instructor_method_used_when_enabled(self, mock_config_enabled, sample_educational_input):
        """Should attempt to use Instructor when enabled and available."""
        # Mock the Instructor client and response
        mock_client = MagicMock()
        mock_response = ContentTypeClassification(
            primary_type=ContentType.EDUCATIONAL,
            confidence=0.9,
            secondary_types=[ContentType.TECHNOLOGY],
            recommended_pipeline="deep_analysis",
            processing_flags={
                "enable_deep_analysis": True,
                "enable_fallacy_detection": True,
                "skip_transcription": False,
            },
            quality_score=0.85,
            estimated_processing_time=45.0,
            recommendations=[
                "Enable comprehensive analysis for educational content",
                "Extract technical terms and concepts",
            ],
        )

        # Mock the completion call
        mock_completion = MagicMock()
        mock_completion.parsed = mock_response
        mock_client.chat.completions.create.return_value = mock_completion

        with patch("content_type_routing_tool.InstructorClientFactory") as MockFactory:
            MockFactory.is_enabled.return_value = True
            MockFactory.create_openrouter_client.return_value = mock_client

            # Create tool AFTER all mocks are set up
            tool = ContentTypeRoutingTool()
            result = tool.run(sample_educational_input)

        # Verify result
        assert result.success
        assert result.data is not None
        assert "result" in result.data
        assert "classification" in result.data["result"]
        assert result.data["result"]["classification"]["primary_type"] == "educational"
        assert result.data["result"].get("analysis_method") == "llm_instructor"
        assert result.data["result"]["classification"]["confidence"] == 0.9

        # Verify the client was called correctly
        MockFactory.create_openrouter_client.assert_called_once()
        mock_client.chat.completions.create.assert_called_once()

        # Verify the prompt included the content
        call_args = mock_client.chat.completions.create.call_args
        assert call_args is not None
        messages = call_args[1]["messages"]
        # Check that content is in the user message
        user_message = next((msg for msg in messages if msg["role"] == "user"), None)
        assert user_message is not None
        assert "Python" in user_message["content"]

    @pytest.mark.skipif(not INSTRUCTOR_AVAILABLE, reason="Instructor not installed")
    def test_fallback_to_pattern_matching_on_llm_failure(self, mock_config_enabled, sample_educational_input):
        """Should fallback to pattern-matching if LLM classification fails."""
        # Mock the Instructor client to raise an exception
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API error")

        with patch("content_type_routing_tool.InstructorClientFactory") as MockFactory:
            MockFactory.is_enabled.return_value = True
            MockFactory.create_openrouter_client.return_value = mock_client

            # Create tool AFTER all mocks are set up
            tool = ContentTypeRoutingTool()
            result = tool.run(sample_educational_input)

        # Should still succeed via fallback
        assert result.success
        assert result.data is not None
        assert "result" in result.data
        assert "classification" in result.data["result"]
        # Even though Instructor was enabled, should fallback to pattern matching
        assert result.data["result"].get("analysis_method") == "pattern_matching"
        assert result.data["result"]["classification"]["primary_type"] in ["educational", "general"]

    def test_empty_transcript_handling(self):
        """Should handle empty or missing transcript gracefully."""
        empty_input = {"transcript": "", "title": "", "description": "", "metadata": {}}

        # Create tool with default config
        with patch("content_type_routing_tool.get_config") as mock_get:
            config = Mock()
            config.enable_instructor = False
            mock_get.return_value = config
            tool = ContentTypeRoutingTool()
            result = tool.run(empty_input)

        assert result.success is False
        assert "transcript" in result.error.lower()

    def test_entertainment_content_classification(self, mock_config_disabled, sample_entertainment_input):
        """Should correctly classify entertainment content."""
        # Create tool AFTER config mock
        tool = ContentTypeRoutingTool()
        result = tool.run(sample_entertainment_input)

        assert result.success
        assert result.data is not None
        assert "result" in result.data
        classification = result.data["result"]["classification"]
        # Should detect entertainment or general
        assert classification["primary_type"] in ["entertainment", "general"]

    @pytest.mark.skipif(not INSTRUCTOR_AVAILABLE, reason="Instructor not installed")
    def test_processing_flags_populated(self, mock_config_enabled, sample_educational_input):
        """Should populate processing flags from LLM response."""
        mock_client = MagicMock()
        mock_response = ContentTypeClassification(
            primary_type=ContentType.EDUCATIONAL,
            confidence=0.95,
            secondary_types=[],
            recommended_pipeline="deep_analysis",
            processing_flags={
                "enable_deep_analysis": True,
                "enable_fallacy_detection": True,
                "skip_transcription": False,
                "use_fast_model": False,
            },
            quality_score=0.9,
            estimated_processing_time=50.0,
            recommendations=["Full analysis recommended"],
        )

        mock_completion = MagicMock()
        mock_completion.parsed = mock_response
        mock_client.chat.completions.create.return_value = mock_completion

        with patch("content_type_routing_tool.InstructorClientFactory") as MockFactory:
            MockFactory.is_enabled.return_value = True
            MockFactory.create_openrouter_client.return_value = mock_client

            # Create tool AFTER all mocks are set up
            tool = ContentTypeRoutingTool()
            result = tool.run(sample_educational_input)

        assert result.success
        assert "result" in result.data
        routing = result.data["result"]["routing"]
        assert "processing_flags" in routing
        assert routing["processing_flags"]["enable_deep_analysis"] is True
        assert routing["processing_flags"]["enable_fallacy_detection"] is True

    @pytest.mark.skipif(not INSTRUCTOR_AVAILABLE, reason="Instructor not installed")
    def test_recommendations_included(self, mock_config_enabled, sample_educational_input):
        """Should include LLM-generated recommendations."""
        mock_client = MagicMock()
        mock_response = ContentTypeClassification(
            primary_type=ContentType.TECHNOLOGY,
            confidence=0.88,
            secondary_types=[ContentType.EDUCATIONAL],
            recommended_pipeline="deep_analysis",
            processing_flags={"enable_deep_analysis": True},
            quality_score=0.85,
            estimated_processing_time=40.0,
            recommendations=[
                "Extract technical terminology",
                "Enable code snippet detection",
                "Cross-reference with tech knowledge base",
            ],
        )

        mock_completion = MagicMock()
        mock_completion.parsed = mock_response
        mock_client.chat.completions.create.return_value = mock_completion

        with patch("content_type_routing_tool.InstructorClientFactory") as MockFactory:
            MockFactory.is_enabled.return_value = True
            MockFactory.create_openrouter_client.return_value = mock_client

            # Create tool AFTER all mocks are set up
            tool = ContentTypeRoutingTool()
            result = tool.run(sample_educational_input)

        assert result.success
        assert "result" in result.data
        recommendations = result.data["result"]["recommendations"]
        assert isinstance(recommendations, list)
        assert len(recommendations) == 3
        assert "Extract technical terminology" in recommendations


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
