"""Unit tests for pipeline_result_builders module."""

import time
from typing import Any
from unittest.mock import MagicMock

import pytest

from ultimate_discord_intelligence_bot.orchestrator.pipeline_result_builders import (
    build_pipeline_content_analysis_result,
)
from ultimate_discord_intelligence_bot.step_result import StepResult


class TestBuildPipelineContentAnalysisResult:
    """Test suite for build_pipeline_content_analysis_result function."""

    @pytest.fixture
    def minimal_inputs(self) -> dict[str, Any]:
        """Minimal valid inputs for the function."""
        return {
            "transcript": "This is a test transcript with some words.",
            "transcription_data": {
                "quality_score": 0.8,
                "timeline_anchors": [{"time": 0, "text": "intro"}],
                "transcript_index": {"intro": [0]},
            },
            "pipeline_analysis": {
                "keywords": ["test", "transcript"],
                "sentiment": "positive",
                "sentiment_score": 0.7,
                "summary": "Test summary",
            },
            "media_info": {
                "title": "Test Video",
                "platform": "youtube",
                "duration": 120,
            },
            "pipeline_fallacy": None,
            "pipeline_perspective": None,
            "pipeline_metadata": None,
            "source_url": "https://example.com/video",
        }

    def test_basic_result_structure(self, minimal_inputs):
        """Test that basic result has all required keys."""
        result = build_pipeline_content_analysis_result(**minimal_inputs)

        assert isinstance(result, StepResult)
        assert result.success is True
        assert "transcript" in result.data
        assert "keywords" in result.data
        assert "sentiment" in result.data
        assert "sentiment_analysis" in result.data
        assert "content_metadata" in result.data
        assert "thematic_insights" in result.data

    def test_keyword_extraction_from_keywords(self, minimal_inputs):
        """Test keyword extraction when keywords are provided."""
        minimal_inputs["pipeline_analysis"]["keywords"] = ["python", "testing", "automation"]

        result = build_pipeline_content_analysis_result(**minimal_inputs)

        assert result.data["keywords"] == ["python", "testing", "automation"]
        assert result.data["linguistic_patterns"]["keywords"] == ["python", "testing", "automation"]

    def test_keyword_extraction_from_key_phrases(self, minimal_inputs):
        """Test keyword extraction when only key_phrases are provided."""
        minimal_inputs["pipeline_analysis"].pop("keywords")
        minimal_inputs["pipeline_analysis"]["key_phrases"] = ["data science", "machine learning"]

        result = build_pipeline_content_analysis_result(**minimal_inputs)

        assert result.data["keywords"] == ["data science", "machine learning"]

    def test_sentiment_from_sentiment_details(self, minimal_inputs):
        """Test sentiment extraction from sentiment_details."""
        minimal_inputs["pipeline_analysis"]["sentiment_details"] = {
            "label": "very_positive",
            "score": 0.95,
            "confidence": 0.88,
        }

        result = build_pipeline_content_analysis_result(**minimal_inputs)

        assert result.data["sentiment"] == "very_positive"
        assert result.data["sentiment_score"] == 0.95
        assert result.data["sentiment_analysis"]["confidence"] == 0.88

    def test_word_count_from_structured(self, minimal_inputs):
        """Test word count extraction from structured data."""
        minimal_inputs["pipeline_analysis"]["structured"] = {"word_count": 500}

        result = build_pipeline_content_analysis_result(**minimal_inputs)

        assert result.data["content_metadata"]["word_count"] == 500

    def test_word_count_from_pipeline_analysis(self, minimal_inputs):
        """Test word count extraction from pipeline_analysis."""
        minimal_inputs["pipeline_analysis"]["word_count"] = 350

        result = build_pipeline_content_analysis_result(**minimal_inputs)

        assert result.data["content_metadata"]["word_count"] == 350

    def test_word_count_fallback_to_transcript_split(self, minimal_inputs):
        """Test word count falls back to transcript.split() count."""
        # Don't provide word_count anywhere
        result = build_pipeline_content_analysis_result(**minimal_inputs)

        # "This is a test transcript with some words." = 8 words
        assert result.data["content_metadata"]["word_count"] == 8

    def test_summary_from_pipeline_perspective(self, minimal_inputs):
        """Test summary extraction from pipeline_perspective when not in pipeline_analysis."""
        minimal_inputs["pipeline_analysis"].pop("summary")
        minimal_inputs["pipeline_perspective"] = {
            "summary": "Perspective-derived summary",
            "perspectives": ["viewpoint1", "viewpoint2"],
        }

        result = build_pipeline_content_analysis_result(**minimal_inputs)

        assert result.data["summary"] == "Perspective-derived summary"

    def test_thematic_insights_with_perspectives(self, minimal_inputs):
        """Test thematic insights include perspectives."""
        minimal_inputs["pipeline_analysis"]["keywords"] = ["keyword1", "keyword2"]
        minimal_inputs["pipeline_perspective"] = {
            "perspectives": ["perspective1", "perspective2", "keyword1"],  # keyword1 is duplicate
        }

        result = build_pipeline_content_analysis_result(**minimal_inputs)

        # Should have keywords + unique perspectives
        assert "keyword1" in result.data["thematic_insights"]
        assert "keyword2" in result.data["thematic_insights"]
        assert "perspective1" in result.data["thematic_insights"]
        assert "perspective2" in result.data["thematic_insights"]
        # keyword1 should not be duplicated
        assert result.data["thematic_insights"].count("keyword1") == 1

    def test_media_info_merged_into_metadata(self, minimal_inputs):
        """Test media_info fields are merged into content_metadata."""
        minimal_inputs["media_info"] = {
            "title": "Amazing Video",
            "platform": "youtube",
            "duration": 300,
            "uploader": "TestChannel",
            "video_id": "abc123",
        }

        result = build_pipeline_content_analysis_result(**minimal_inputs)

        metadata = result.data["content_metadata"]
        assert metadata["title"] == "Amazing Video"
        assert metadata["platform"] == "youtube"
        assert metadata["duration"] == 300
        assert metadata["uploader"] == "TestChannel"
        assert metadata["video_id"] == "abc123"

    def test_source_url_from_media_info(self, minimal_inputs):
        """Test source_url extracted from media_info when not provided."""
        minimal_inputs["source_url"] = None
        minimal_inputs["media_info"]["source_url"] = "https://media-info-url.com"

        result = build_pipeline_content_analysis_result(**minimal_inputs)

        assert result.data["source_url"] == "https://media-info-url.com"

    def test_pipeline_metadata_merged(self, minimal_inputs):
        """Test pipeline_metadata fields are merged."""
        minimal_inputs["pipeline_metadata"] = {
            "workflow_type": "autonomous_intelligence",
            "acquisition_timestamp": 1234567890,
        }

        result = build_pipeline_content_analysis_result(**minimal_inputs)

        metadata = result.data["content_metadata"]
        assert metadata["workflow_type"] == "autonomous_intelligence"
        assert metadata["acquisition_timestamp"] == 1234567890

    def test_fallacy_analysis_included(self, minimal_inputs):
        """Test fallacy_analysis is included when provided."""
        minimal_inputs["pipeline_fallacy"] = {
            "fallacies_detected": 3,
            "types": ["ad_hominem", "straw_man"],
        }

        result = build_pipeline_content_analysis_result(**minimal_inputs)

        assert "fallacy_analysis" in result.data
        assert result.data["fallacy_analysis"]["fallacies_detected"] == 3

    def test_perspective_analysis_included(self, minimal_inputs):
        """Test perspective_analysis is included when provided."""
        minimal_inputs["pipeline_perspective"] = {
            "viewpoints": 5,
            "diversity_score": 0.8,
        }

        result = build_pipeline_content_analysis_result(**minimal_inputs)

        assert "perspective_analysis" in result.data
        assert result.data["perspective_analysis"]["viewpoints"] == 5

    def test_degraded_fallback_on_exception(self, minimal_inputs):
        """Test degraded result returned on exception."""
        # Cause an exception by passing invalid data
        minimal_inputs["transcript"] = None  # Will cause error in len(transcript.split())

        logger_mock = MagicMock()
        result = build_pipeline_content_analysis_result(**minimal_inputs, logger=logger_mock)

        # Should still return a result, but degraded
        assert isinstance(result, StepResult)
        assert result.success is True
        assert "degraded" in result.data.get("message", "").lower()
        assert result.data["sentiment_analysis"]["label"] == "neutral"
        logger_mock.warning.assert_called_once()

    def test_all_input_data_preserved(self, minimal_inputs):
        """Test that all input data is preserved in the result."""
        minimal_inputs["pipeline_fallacy"] = {"test": "fallacy"}
        minimal_inputs["pipeline_perspective"] = {"test": "perspective"}
        minimal_inputs["pipeline_metadata"] = {"test": "metadata"}

        result = build_pipeline_content_analysis_result(**minimal_inputs)

        # All original data should be in result
        assert result.data["pipeline_analysis"] == minimal_inputs["pipeline_analysis"]
        assert result.data["pipeline_fallacy"] == minimal_inputs["pipeline_fallacy"]
        assert result.data["pipeline_perspective"] == minimal_inputs["pipeline_perspective"]
        assert result.data["pipeline_metadata"] == minimal_inputs["pipeline_metadata"]
        assert result.data["media_info"] == minimal_inputs["media_info"]

    def test_timestamp_in_metadata(self, minimal_inputs):
        """Test that analysis_timestamp is added to metadata."""
        before = time.time()
        result = build_pipeline_content_analysis_result(**minimal_inputs)
        after = time.time()

        timestamp = result.data["content_metadata"]["analysis_timestamp"]
        assert before <= timestamp <= after

    def test_analysis_source_set(self, minimal_inputs):
        """Test that analysis_source is set to content_pipeline."""
        result = build_pipeline_content_analysis_result(**minimal_inputs)

        assert result.data["content_metadata"]["analysis_source"] == "content_pipeline"

    def test_empty_keywords_handled(self, minimal_inputs):
        """Test handling of empty keywords."""
        minimal_inputs["pipeline_analysis"]["keywords"] = []

        result = build_pipeline_content_analysis_result(**minimal_inputs)

        assert result.data["keywords"] == []
        assert result.data["thematic_insights"] == []

    def test_missing_quality_score_defaults(self, minimal_inputs):
        """Test quality_score defaults to 0.5 when missing."""
        minimal_inputs["transcription_data"].pop("quality_score")

        result = build_pipeline_content_analysis_result(**minimal_inputs)

        assert result.data["content_metadata"]["quality_score"] == 0.5
