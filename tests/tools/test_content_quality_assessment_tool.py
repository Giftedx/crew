"""Tests for ContentQualityAssessmentTool."""

from platform.core.step_result import StepResult
from unittest.mock import patch

import pytest

from domains.intelligence.analysis.content_quality_assessment_tool import ContentQualityAssessmentTool


class TestContentQualityAssessmentTool:
    """Test cases for ContentQualityAssessmentTool."""

    @pytest.fixture
    def tool(self, test_tenant_context):
        """Create ContentQualityAssessmentTool instance."""
        return ContentQualityAssessmentTool()

    @pytest.fixture
    def sample_content(self):
        """Sample content for testing."""
        return {
            "content": "This is a high-quality piece of content with proper grammar and structure.",
            "title": "Test Content",
            "author": "Test Author",
            "platform": "test",
            "content_type": "text",
        }

    @pytest.fixture
    def low_quality_content(self):
        """Low quality content for testing."""
        return {
            "content": "bad content no grammar errors",
            "title": "",
            "author": "",
            "platform": "test",
            "content_type": "text",
        }

    def test_tool_initialization(self, tool):
        """Test tool initialization."""
        assert tool is not None
        assert hasattr(tool, "_run")
        assert hasattr(tool, "args_schema")

    def test_args_schema(self, tool):
        """Test args schema definition."""
        schema = tool.args_schema
        assert schema is not None
        assert hasattr(schema, "content")
        assert hasattr(schema, "content_type")
        assert hasattr(schema, "quality_criteria")

    @pytest.mark.unit
    def test_assess_high_quality_content(self, tool, sample_content, test_tenant_context):
        """Test quality assessment of high-quality content."""
        with patch.object(tool, "_assess_grammar_quality", return_value=0.9):
            with patch.object(tool, "_assess_structure_quality", return_value=0.8):
                with patch.object(tool, "_assess_relevance_quality", return_value=0.85):
                    result = tool._run(
                        content=sample_content["content"],
                        content_type=sample_content["content_type"],
                        quality_criteria=["grammar", "structure", "relevance"],
                        tenant_context=test_tenant_context,
                    )
        assert isinstance(result, StepResult)
        assert result.success
        assert "quality_score" in result.data
        assert result.data["quality_score"] > 0.8
        assert "assessments" in result.data
        assert len(result.data["assessments"]) == 3

    @pytest.mark.unit
    def test_assess_low_quality_content(self, tool, low_quality_content, test_tenant_context):
        """Test quality assessment of low-quality content."""
        with patch.object(tool, "_assess_grammar_quality", return_value=0.3):
            with patch.object(tool, "_assess_structure_quality", return_value=0.2):
                with patch.object(tool, "_assess_relevance_quality", return_value=0.4):
                    result = tool._run(
                        content=low_quality_content["content"],
                        content_type=low_quality_content["content_type"],
                        quality_criteria=["grammar", "structure", "relevance"],
                        tenant_context=test_tenant_context,
                    )
        assert isinstance(result, StepResult)
        assert result.success
        assert "quality_score" in result.data
        assert result.data["quality_score"] < 0.5
        assert "assessments" in result.data
        assert len(result.data["assessments"]) == 3

    @pytest.mark.unit
    def test_assess_video_content(self, tool, test_tenant_context):
        """Test quality assessment of video content."""
        video_content = {
            "content": "Test video content",
            "content_type": "video",
            "duration": 300,
            "resolution": "1080p",
            "audio_quality": "high",
        }
        with patch.object(tool, "_assess_video_quality", return_value=0.9):
            with patch.object(tool, "_assess_audio_quality", return_value=0.8):
                result = tool._run(
                    content=video_content["content"],
                    content_type=video_content["content_type"],
                    quality_criteria=["video_quality", "audio_quality"],
                    tenant_context=test_tenant_context,
                )
        assert isinstance(result, StepResult)
        assert result.success
        assert "quality_score" in result.data
        assert result.data["quality_score"] > 0.8

    @pytest.mark.unit
    def test_assess_audio_content(self, tool, test_tenant_context):
        """Test quality assessment of audio content."""
        audio_content = {
            "content": "Test audio content",
            "content_type": "audio",
            "bitrate": 320,
            "sample_rate": 44100,
            "channels": 2,
        }
        with patch.object(tool, "_assess_audio_quality", return_value=0.9):
            with patch.object(tool, "_assess_clarity_quality", return_value=0.8):
                result = tool._run(
                    content=audio_content["content"],
                    content_type=audio_content["content_type"],
                    quality_criteria=["audio_quality", "clarity"],
                    tenant_context=test_tenant_context,
                )
        assert isinstance(result, StepResult)
        assert result.success
        assert "quality_score" in result.data
        assert result.data["quality_score"] > 0.8

    @pytest.mark.unit
    def test_assess_image_content(self, tool, test_tenant_context):
        """Test quality assessment of image content."""
        image_content = {
            "content": "Test image content",
            "content_type": "image",
            "width": 1920,
            "height": 1080,
            "format": "jpg",
            "compression": "high",
        }
        with patch.object(tool, "_assess_image_quality", return_value=0.9):
            with patch.object(tool, "_assess_resolution_quality", return_value=0.8):
                result = tool._run(
                    content=image_content["content"],
                    content_type=image_content["content_type"],
                    quality_criteria=["image_quality", "resolution"],
                    tenant_context=test_tenant_context,
                )
        assert isinstance(result, StepResult)
        assert result.success
        assert "quality_score" in result.data
        assert result.data["quality_score"] > 0.8

    @pytest.mark.unit
    def test_invalid_content_type(self, tool, test_tenant_context):
        """Test handling of invalid content type."""
        result = tool._run(
            content="Test content",
            content_type="invalid_type",
            quality_criteria=["grammar"],
            tenant_context=test_tenant_context,
        )
        assert isinstance(result, StepResult)
        assert not result.success
        assert "error" in result.data

    @pytest.mark.unit
    def test_empty_content(self, tool, test_tenant_context):
        """Test handling of empty content."""
        result = tool._run(
            content="", content_type="text", quality_criteria=["grammar"], tenant_context=test_tenant_context
        )
        assert isinstance(result, StepResult)
        assert not result.success
        assert "error" in result.data

    @pytest.mark.unit
    def test_empty_quality_criteria(self, tool, test_tenant_context):
        """Test handling of empty quality criteria."""
        result = tool._run(
            content="Test content", content_type="text", quality_criteria=[], tenant_context=test_tenant_context
        )
        assert isinstance(result, StepResult)
        assert not result.success
        assert "error" in result.data

    @pytest.mark.unit
    def test_grammar_quality_assessment(self, tool):
        """Test grammar quality assessment."""
        good_text = "This is a well-written sentence with proper grammar."
        bad_text = "this is bad grammar no punctuation"
        good_score = tool._assess_grammar_quality(good_text)
        bad_score = tool._assess_grammar_quality(bad_text)
        assert good_score > bad_score
        assert 0 <= good_score <= 1
        assert 0 <= bad_score <= 1

    @pytest.mark.unit
    def test_structure_quality_assessment(self, tool):
        """Test structure quality assessment."""
        structured_text = "Introduction. Main content. Conclusion."
        unstructured_text = "random words no structure"
        structured_score = tool._assess_structure_quality(structured_text)
        unstructured_score = tool._assess_structure_quality(unstructured_text)
        assert structured_score > unstructured_score
        assert 0 <= structured_score <= 1
        assert 0 <= unstructured_score <= 1

    @pytest.mark.unit
    def test_relevance_quality_assessment(self, tool):
        """Test relevance quality assessment."""
        relevant_text = "This content is highly relevant to the topic."
        irrelevant_text = "Random unrelated content about something else."
        relevant_score = tool._assess_relevance_quality(relevant_text, "topic")
        irrelevant_score = tool._assess_relevance_quality(irrelevant_text, "topic")
        assert relevant_score > irrelevant_score
        assert 0 <= relevant_score <= 1
        assert 0 <= irrelevant_score <= 1

    @pytest.mark.unit
    def test_video_quality_assessment(self, tool):
        """Test video quality assessment."""
        high_quality_video = {"resolution": "1080p", "bitrate": 5000, "fps": 60, "codec": "h264"}
        low_quality_video = {"resolution": "480p", "bitrate": 1000, "fps": 24, "codec": "h264"}
        high_score = tool._assess_video_quality(high_quality_video)
        low_score = tool._assess_video_quality(low_quality_video)
        assert high_score > low_score
        assert 0 <= high_score <= 1
        assert 0 <= low_score <= 1

    @pytest.mark.unit
    def test_audio_quality_assessment(self, tool):
        """Test audio quality assessment."""
        high_quality_audio = {"bitrate": 320, "sample_rate": 44100, "channels": 2, "format": "flac"}
        low_quality_audio = {"bitrate": 128, "sample_rate": 22050, "channels": 1, "format": "mp3"}
        high_score = tool._assess_audio_quality(high_quality_audio)
        low_score = tool._assess_audio_quality(low_quality_audio)
        assert high_score > low_score
        assert 0 <= high_score <= 1
        assert 0 <= low_score <= 1

    @pytest.mark.unit
    def test_image_quality_assessment(self, tool):
        """Test image quality assessment."""
        high_quality_image = {"width": 1920, "height": 1080, "format": "png", "compression": "lossless"}
        low_quality_image = {"width": 640, "height": 480, "format": "jpg", "compression": "high"}
        high_score = tool._assess_image_quality(high_quality_image)
        low_score = tool._assess_image_quality(low_quality_image)
        assert high_score > low_score
        assert 0 <= high_score <= 1
        assert 0 <= low_score <= 1

    @pytest.mark.unit
    def test_tenant_isolation(self, tool, test_tenant_context):
        """Test tenant isolation in quality assessment."""
        content = "Test content for tenant isolation"
        with patch.object(tool, "_assess_grammar_quality", return_value=0.8):
            result = tool._run(
                content=content, content_type="text", quality_criteria=["grammar"], tenant_context=test_tenant_context
            )
        assert isinstance(result, StepResult)
        assert result.success
        assert result.data["tenant"] == test_tenant_context.tenant
        assert result.data["workspace"] == test_tenant_context.workspace

    @pytest.mark.unit
    def test_error_handling(self, tool, test_tenant_context):
        """Test error handling in quality assessment."""
        with patch.object(tool, "_assess_grammar_quality", side_effect=Exception("Test error")):
            result = tool._run(
                content="Test content",
                content_type="text",
                quality_criteria=["grammar"],
                tenant_context=test_tenant_context,
            )
        assert isinstance(result, StepResult)
        assert not result.success
        assert "error" in result.data

    @pytest.mark.unit
    def test_performance_benchmark(self, tool, sample_content, test_tenant_context, performance_benchmark):
        """Test performance of quality assessment."""
        performance_benchmark.start()
        with patch.object(tool, "_assess_grammar_quality", return_value=0.8):
            with patch.object(tool, "_assess_structure_quality", return_value=0.8):
                with patch.object(tool, "_assess_relevance_quality", return_value=0.8):
                    result = tool._run(
                        content=sample_content["content"],
                        content_type=sample_content["content_type"],
                        quality_criteria=["grammar", "structure", "relevance"],
                        tenant_context=test_tenant_context,
                    )
        elapsed_time = performance_benchmark.stop()
        assert isinstance(result, StepResult)
        assert result.success
        assert elapsed_time < 1.0

    @pytest.mark.integration
    def test_integration_with_real_content(self, tool, test_tenant_context):
        """Test integration with real content (mocked external services)."""
        real_content = {
            "content": "This is a comprehensive analysis of the current market trends and their implications for investors.",
            "content_type": "text",
            "title": "Market Analysis Report",
            "author": "Financial Analyst",
            "platform": "research",
        }
        with patch("ultimate_discord_intelligence_bot.tools.content_quality_assessment_tool.requests.get") as mock_get:
            mock_get.return_value.json.return_value = {"grammar_score": 0.9}
            result = tool._run(
                content=real_content["content"],
                content_type=real_content["content_type"],
                quality_criteria=["grammar", "structure", "relevance"],
                tenant_context=test_tenant_context,
            )
        assert isinstance(result, StepResult)
        assert result.success
        assert "quality_score" in result.data
        assert "assessments" in result.data
        assert "metadata" in result.data

    @pytest.mark.performance
    def test_large_content_performance(self, tool, test_tenant_context):
        """Test performance with large content."""
        large_content = "This is a test content. " * 1000
        import time

        start_time = time.time()
        with patch.object(tool, "_assess_grammar_quality", return_value=0.8):
            result = tool._run(
                content=large_content,
                content_type="text",
                quality_criteria=["grammar"],
                tenant_context=test_tenant_context,
            )
        elapsed_time = time.time() - start_time
        assert isinstance(result, StepResult)
        assert result.success
        assert elapsed_time < 5.0

    @pytest.mark.parametrize(
        "content_type,expected_criteria",
        [
            ("text", ["grammar", "structure", "relevance"]),
            ("video", ["video_quality", "audio_quality", "resolution"]),
            ("audio", ["audio_quality", "clarity", "bitrate"]),
            ("image", ["image_quality", "resolution", "compression"]),
        ],
    )
    def test_content_type_specific_criteria(self, tool, content_type, expected_criteria, test_tenant_context):
        """Test that appropriate criteria are used for different content types."""
        content = f"Test {content_type} content"
        with patch.object(tool, f"_assess_{expected_criteria[0]}_quality", return_value=0.8):
            result = tool._run(
                content=content,
                content_type=content_type,
                quality_criteria=expected_criteria,
                tenant_context=test_tenant_context,
            )
        assert isinstance(result, StepResult)
        assert result.success
        assert "quality_score" in result.data
        assert len(result.data["assessments"]) == len(expected_criteria)
