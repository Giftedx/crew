"""Unit tests for pipeline result builder utilities."""

from __future__ import annotations

import time
from typing import Any
from unittest.mock import MagicMock

import pytest

from ultimate_discord_intelligence_bot.orchestrator.pipeline_result_builders import (
    build_knowledge_payload,
    build_pipeline_content_analysis_result,
    create_executive_summary,
    extract_key_findings,
    extract_system_status_from_crew,
    merge_threat_payload,
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
            "media_info": {"title": "Test Video", "platform": "youtube", "duration": 120},
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
        result = build_pipeline_content_analysis_result(**minimal_inputs)
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
        minimal_inputs["pipeline_perspective"] = {"perspectives": ["perspective1", "perspective2", "keyword1"]}
        result = build_pipeline_content_analysis_result(**minimal_inputs)
        assert "keyword1" in result.data["thematic_insights"]
        assert "keyword2" in result.data["thematic_insights"]
        assert "perspective1" in result.data["thematic_insights"]
        assert "perspective2" in result.data["thematic_insights"]
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
        minimal_inputs["pipeline_fallacy"] = {"fallacies_detected": 3, "types": ["ad_hominem", "straw_man"]}
        result = build_pipeline_content_analysis_result(**minimal_inputs)
        assert "fallacy_analysis" in result.data
        assert result.data["fallacy_analysis"]["fallacies_detected"] == 3

    def test_perspective_analysis_included(self, minimal_inputs):
        """Test perspective_analysis is included when provided."""
        minimal_inputs["pipeline_perspective"] = {"viewpoints": 5, "diversity_score": 0.8}
        result = build_pipeline_content_analysis_result(**minimal_inputs)
        assert "perspective_analysis" in result.data
        assert result.data["perspective_analysis"]["viewpoints"] == 5

    def test_degraded_fallback_on_exception(self, minimal_inputs):
        """Test degraded result returned on exception."""
        minimal_inputs["transcript"] = None
        logger_mock = MagicMock()
        result = build_pipeline_content_analysis_result(**minimal_inputs, logger=logger_mock)
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


class TestMergeThreatPayload:
    """Tests for merge_threat_payload function."""

    @pytest.fixture
    def base_threat_payload(self) -> dict[str, Any]:
        """Fixture for a minimal threat payload."""
        return {"threat_level": "high", "threats_detected": ["malware", "phishing"]}

    def test_empty_inputs_returns_copy(self, base_threat_payload):
        """Test merge with no verification/fact data returns copy of base."""
        result = merge_threat_payload(base_threat_payload, None, None)
        assert result == base_threat_payload
        assert result is not base_threat_payload

    def test_verification_deception_metrics_merged(self, base_threat_payload):
        """Test deception_metrics from verification_data is merged."""
        verification_data = {"deception_metrics": {"score": 0.8, "indicators": ["inconsistency"]}}
        result = merge_threat_payload(base_threat_payload, verification_data, None)
        assert result["deception_metrics"] == {"score": 0.8, "indicators": ["inconsistency"]}

    def test_verification_credibility_assessment_merged(self, base_threat_payload):
        """Test credibility_assessment from verification_data is merged."""
        verification_data = {"credibility_assessment": {"rating": "low", "reasons": ["unverified source"]}}
        result = merge_threat_payload(base_threat_payload, verification_data, None)
        assert result["credibility_assessment"] == {"rating": "low", "reasons": ["unverified source"]}

    def test_verification_deception_score_merged(self, base_threat_payload):
        """Test deception_score from verification_data is merged."""
        verification_data = {"deception_score": 0.75}
        result = merge_threat_payload(base_threat_payload, verification_data, None)
        assert result["deception_score"] == 0.75

    def test_verification_logical_analysis_as_fallacies(self, base_threat_payload):
        """Test logical_analysis from verification becomes logical_fallacies."""
        verification_data = {"logical_analysis": ["ad hominem", "straw man"]}
        result = merge_threat_payload(base_threat_payload, verification_data, None)
        assert result["logical_fallacies"] == ["ad hominem", "straw man"]

    def test_fact_data_fact_checks_merged(self, base_threat_payload):
        """Test fact_checks from fact_data is merged."""
        fact_data = {"fact_checks": [{"claim": "X", "verdict": "false"}]}
        result = merge_threat_payload(base_threat_payload, None, fact_data)
        assert result["fact_checks"] == [{"claim": "X", "verdict": "false"}]

    def test_fact_data_logical_fallacies_merged(self, base_threat_payload):
        """Test logical_fallacies from fact_data is merged."""
        fact_data = {"logical_fallacies": ["false dichotomy"]}
        result = merge_threat_payload(base_threat_payload, None, fact_data)
        assert result["logical_fallacies"] == ["false dichotomy"]

    def test_fact_data_perspective_synthesis_as_perspective(self, base_threat_payload):
        """Test perspective_synthesis from fact_data becomes perspective."""
        fact_data = {"perspective_synthesis": "This content shows bias toward..."}
        result = merge_threat_payload(base_threat_payload, None, fact_data)
        assert result["perspective"] == "This content shows bias toward..."

    def test_does_not_override_existing_values(self, base_threat_payload):
        """Test that existing keys in threat_payload are not overridden."""
        base_threat_payload["deception_metrics"] = {"existing": "value"}
        verification_data = {"deception_metrics": {"new": "should not override"}}
        result = merge_threat_payload(base_threat_payload, verification_data, None)
        assert result["deception_metrics"] == {"existing": "value"}

    def test_multiple_sources_merged_without_conflict(self, base_threat_payload):
        """Test merging from both verification and fact data when no conflicts."""
        verification_data = {"deception_metrics": {"score": 0.9}}
        fact_data = {"fact_checks": [{"claim": "Y", "verdict": "true"}]}
        result = merge_threat_payload(base_threat_payload, verification_data, fact_data)
        assert result["deception_metrics"] == {"score": 0.9}
        assert result["fact_checks"] == [{"claim": "Y", "verdict": "true"}]

    def test_fact_data_logical_fallacies_does_not_override_verification(self, base_threat_payload):
        """Test that fact_data logical_fallacies doesn't override verification logical_analysis."""
        verification_data = {"logical_analysis": ["from verification"]}
        fact_data = {"logical_fallacies": ["from fact data"]}
        result = merge_threat_payload(base_threat_payload, verification_data, fact_data)
        assert result["logical_fallacies"] == ["from verification"]

    def test_invalid_deception_score_type_ignored(self, base_threat_payload):
        """Test that non-numeric deception_score is ignored."""
        verification_data = {"deception_score": "not a number"}
        result = merge_threat_payload(base_threat_payload, verification_data, None)
        assert "deception_score" not in result

    def test_non_dict_threat_payload_returns_empty_dict(self):
        """Test that non-dict threat_payload is handled gracefully."""
        result = merge_threat_payload("not a dict", None, None)
        assert result == {}

    def test_non_dict_verification_data_ignored(self, base_threat_payload):
        """Test that non-dict verification_data is ignored."""
        result = merge_threat_payload(base_threat_payload, "not a dict", None)
        assert result == base_threat_payload

    def test_non_dict_fact_data_ignored(self, base_threat_payload):
        """Test that non-dict fact_data is ignored."""
        result = merge_threat_payload(base_threat_payload, None, "not a dict")
        assert result == base_threat_payload


class TestBuildKnowledgePayload:
    """Test suite for build_knowledge_payload function."""

    @pytest.fixture
    def minimal_inputs(self) -> dict[str, Any]:
        """Minimal valid inputs for the function."""
        return {
            "acquisition_data": {},
            "intelligence_data": {},
            "verification_data": {},
            "threat_data": {},
            "fact_data": {},
            "behavioral_data": {},
        }

    def test_basic_result_structure(self, minimal_inputs):
        """Test that basic result has all required keys."""
        result = build_knowledge_payload(**minimal_inputs)
        assert "url" in result
        assert "source_url" in result
        assert "title" in result
        assert "platform" in result
        assert "analysis_summary" in result
        assert "content_metadata" in result
        assert "fact_check_results" in result
        assert "detected_fallacies" in result
        assert "verification_results" in result
        assert "threat_assessment" in result
        assert "behavioral_profile" in result
        assert "perspective" in result
        assert "keywords" in result

    def test_source_url_fallback_chain(self, minimal_inputs):
        """Test source_url fallback chain: acquisition -> pipeline_meta -> fallback_url -> download_block."""
        inputs = minimal_inputs.copy()
        inputs["acquisition_data"] = {"source_url": "https://from-acquisition.com"}
        result = build_knowledge_payload(**inputs)
        assert result["source_url"] == "https://from-acquisition.com"
        inputs["acquisition_data"] = {"pipeline_metadata": {"url": "https://from-pipeline.com"}}
        result = build_knowledge_payload(**inputs)
        assert result["source_url"] == "https://from-pipeline.com"
        inputs["acquisition_data"] = {}
        result = build_knowledge_payload(**inputs, fallback_url="https://from-fallback.com")
        assert result["source_url"] == "https://from-fallback.com"
        inputs["acquisition_data"] = {"download": {"source_url": "https://from-download.com"}}
        result = build_knowledge_payload(**inputs)
        assert result["source_url"] == "https://from-download.com"

    def test_title_fallback_chain(self, minimal_inputs):
        """Test title extraction: download -> content_metadata -> pipeline_meta."""
        inputs = minimal_inputs.copy()
        inputs["acquisition_data"] = {"download": {"title": "Title from Download"}}
        result = build_knowledge_payload(**inputs)
        assert result["title"] == "Title from Download"
        inputs["acquisition_data"] = {}
        inputs["intelligence_data"] = {"content_metadata": {"title": "Title from Content"}}
        result = build_knowledge_payload(**inputs)
        assert result["title"] == "Title from Content"
        inputs["intelligence_data"] = {}
        inputs["acquisition_data"] = {"pipeline_metadata": {"title": "Title from Pipeline"}}
        result = build_knowledge_payload(**inputs)
        assert result["title"] == "Title from Pipeline"
        inputs["acquisition_data"] = {}
        result = build_knowledge_payload(**inputs)
        assert result["title"] is None

    def test_platform_fallback_chain(self, minimal_inputs):
        """Test platform extraction: download -> content_metadata -> pipeline_meta -> transcription."""
        inputs = minimal_inputs.copy()
        inputs["acquisition_data"] = {"download": {"platform": "youtube"}}
        result = build_knowledge_payload(**inputs)
        assert result["platform"] == "youtube"
        inputs["acquisition_data"] = {}
        inputs["intelligence_data"] = {"content_metadata": {"platform": "vimeo"}}
        result = build_knowledge_payload(**inputs)
        assert result["platform"] == "vimeo"
        inputs["intelligence_data"] = {}
        inputs["acquisition_data"] = {"pipeline_metadata": {"platform": "twitter"}}
        result = build_knowledge_payload(**inputs)
        assert result["platform"] == "twitter"
        inputs["acquisition_data"] = {"transcription": {"platform": "podcast"}}
        result = build_knowledge_payload(**inputs)
        assert result["platform"] == "podcast"

    def test_perspective_data_extraction(self, minimal_inputs):
        """Test perspective data extraction from fact_data or acquisition_data."""
        inputs = minimal_inputs.copy()
        inputs["fact_data"] = {"perspective_synthesis": {"summary": "From fact data"}}
        result = build_knowledge_payload(**inputs)
        assert result["perspective"] == {"summary": "From fact data"}
        inputs["fact_data"] = {}
        inputs["acquisition_data"] = {"perspective": {"summary": "From acquisition"}}
        result = build_knowledge_payload(**inputs)
        assert result["perspective"] == {"summary": "From acquisition"}
        inputs["acquisition_data"] = {}
        result = build_knowledge_payload(**inputs)
        assert result["perspective"] == {}

    def test_summary_fallback_chain(self, minimal_inputs):
        """Test summary fallback: perspective -> content_metadata -> transcript[:400] -> 'Summary unavailable'."""
        inputs = minimal_inputs.copy()
        inputs["fact_data"] = {"perspective_synthesis": {"summary": "Summary from perspective"}}
        result = build_knowledge_payload(**inputs)
        assert result["analysis_summary"] == "Summary from perspective"
        inputs["fact_data"] = {}
        inputs["intelligence_data"] = {"content_metadata": {"summary": "Summary from content"}}
        result = build_knowledge_payload(**inputs)
        assert result["analysis_summary"] == "Summary from content"
        long_transcript = "A" * 500
        inputs["intelligence_data"] = {"enhanced_transcript": long_transcript}
        result = build_knowledge_payload(**inputs)
        assert result["analysis_summary"] == "A" * 400
        inputs["intelligence_data"] = {}
        result = build_knowledge_payload(**inputs)
        assert result["analysis_summary"] == "Summary unavailable"

    def test_fact_checks_extraction(self, minimal_inputs):
        """Test fact_checks extraction from verification_data or fact_data."""
        inputs = minimal_inputs.copy()
        inputs["verification_data"] = {"fact_checks": {"claim1": "verified"}}
        result = build_knowledge_payload(**inputs)
        assert result["fact_check_results"] == {"claim1": "verified"}
        inputs["verification_data"] = {}
        inputs["fact_data"] = {"fact_checks": {"claim2": "disputed"}}
        result = build_knowledge_payload(**inputs)
        assert result["fact_check_results"] == {"claim2": "disputed"}
        inputs["fact_data"] = {}
        result = build_knowledge_payload(**inputs)
        assert result["fact_check_results"] == {}

    def test_logical_fallacies_extraction(self, minimal_inputs):
        """Test logical_fallacies extraction from verification_data or fact_data."""
        inputs = minimal_inputs.copy()
        inputs["verification_data"] = {"logical_analysis": {"fallacy1": "ad hominem"}}
        result = build_knowledge_payload(**inputs)
        assert result["detected_fallacies"] == {"fallacy1": "ad hominem"}
        inputs["verification_data"] = {}
        inputs["fact_data"] = {"logical_fallacies": {"fallacy2": "straw man"}}
        result = build_knowledge_payload(**inputs)
        assert result["detected_fallacies"] == {"fallacy2": "straw man"}
        inputs["fact_data"] = {}
        result = build_knowledge_payload(**inputs)
        assert result["detected_fallacies"] == {}

    def test_deception_score_extraction(self, minimal_inputs):
        """Test deception_score extraction from threat_data and deception_metrics."""
        inputs = minimal_inputs.copy()
        inputs["threat_data"] = {"deception_score": 0.85}
        result = build_knowledge_payload(**inputs)
        assert result["deception_score"] == 0.85
        inputs["threat_data"] = {"deception_metrics": {"deception_score": 0.65}}
        result = build_knowledge_payload(**inputs)
        assert result["deception_score"] == 0.65
        inputs["threat_data"] = {}
        result = build_knowledge_payload(**inputs)
        assert "deception_score" not in result

    def test_keywords_extraction(self, minimal_inputs):
        """Test keywords extraction from intelligence_data.thematic_insights."""
        inputs = minimal_inputs.copy()
        inputs["intelligence_data"] = {"thematic_insights": ["keyword1", "keyword2"]}
        result = build_knowledge_payload(**inputs)
        assert result["keywords"] == ["keyword1", "keyword2"]
        inputs["intelligence_data"] = {"thematic_insights": []}
        result = build_knowledge_payload(**inputs)
        assert result["keywords"] == []
        inputs["intelligence_data"] = {"thematic_insights": "not a list"}
        result = build_knowledge_payload(**inputs)
        assert result["keywords"] == []

    def test_transcript_index_conditional_inclusion(self, minimal_inputs):
        """Test that transcript_index is only included when present and non-empty."""
        inputs = minimal_inputs.copy()
        inputs["intelligence_data"] = {"transcript_index": {"word1": [0, 10]}}
        result = build_knowledge_payload(**inputs)
        assert result["transcript_index"] == {"word1": [0, 10]}
        inputs["intelligence_data"] = {"transcript_index": {}}
        result = build_knowledge_payload(**inputs)
        assert "transcript_index" not in result
        inputs["intelligence_data"] = {"transcript_index": "not a dict"}
        result = build_knowledge_payload(**inputs)
        assert "transcript_index" not in result

    def test_timeline_anchors_conditional_inclusion(self, minimal_inputs):
        """Test that timeline_anchors is only included when present and non-empty."""
        inputs = minimal_inputs.copy()
        inputs["intelligence_data"] = {"timeline_anchors": [{"time": 0, "text": "intro"}]}
        result = build_knowledge_payload(**inputs)
        assert result["timeline_anchors"] == [{"time": 0, "text": "intro"}]
        inputs["intelligence_data"] = {"timeline_anchors": []}
        result = build_knowledge_payload(**inputs)
        assert "timeline_anchors" not in result
        inputs["intelligence_data"] = {"timeline_anchors": "not a list"}
        result = build_knowledge_payload(**inputs)
        assert "timeline_anchors" not in result

    def test_isinstance_type_checking(self, minimal_inputs):
        """Test that isinstance checks prevent errors with non-dict inputs."""
        inputs = minimal_inputs.copy()
        inputs["acquisition_data"] = "not a dict"
        result = build_knowledge_payload(**inputs)
        assert result["source_url"] is None
        assert result["title"] is None
        inputs = minimal_inputs.copy()
        inputs["intelligence_data"] = "not a dict"
        result = build_knowledge_payload(**inputs)
        assert result["content_metadata"] == {}
        assert result["keywords"] == []
        inputs = minimal_inputs.copy()
        inputs["verification_data"] = "not a dict"
        result = build_knowledge_payload(**inputs)
        assert result["verification_results"] == "not a dict"
        inputs = minimal_inputs.copy()
        inputs["threat_data"] = "not a dict"
        result = build_knowledge_payload(**inputs)
        assert result["threat_assessment"] == "not a dict"

    def test_complete_integration_scenario(self):
        """Test a complete integration scenario with all fields populated."""
        acquisition_data = {
            "source_url": "https://example.com/video",
            "download": {"title": "Test Video", "platform": "youtube"},
            "transcription": {"quality_score": 0.9},
            "pipeline_metadata": {"url": "https://fallback.com"},
        }
        intelligence_data = {
            "content_metadata": {"summary": "Content summary", "duration": 300},
            "thematic_insights": ["keyword1", "keyword2"],
            "transcript_index": {"word1": [0, 10]},
            "timeline_anchors": [{"time": 0, "text": "intro"}],
        }
        verification_data = {"fact_checks": {"claim1": "verified"}, "logical_analysis": {"fallacy1": "ad hominem"}}
        threat_data = {"deception_score": 0.75, "deception_metrics": {"confidence": 0.8}}
        fact_data = {"perspective_synthesis": {"summary": "Perspective summary"}}
        behavioral_data = {"profile": "analytical"}
        result = build_knowledge_payload(
            acquisition_data, intelligence_data, verification_data, threat_data, fact_data, behavioral_data
        )
        assert result["source_url"] == "https://example.com/video"
        assert result["title"] == "Test Video"
        assert result["platform"] == "youtube"
        assert result["analysis_summary"] == "Perspective summary"
        assert result["content_metadata"] == {"summary": "Content summary", "duration": 300}
        assert result["fact_check_results"] == {"claim1": "verified"}
        assert result["detected_fallacies"] == {"fallacy1": "ad hominem"}
        assert result["verification_results"] == verification_data
        assert result["threat_assessment"] == threat_data
        assert result["behavioral_profile"] == behavioral_data
        assert result["perspective"] == {"summary": "Perspective summary"}
        assert result["keywords"] == ["keyword1", "keyword2"]
        assert result["deception_score"] == 0.75
        assert result["transcript_index"] == {"word1": [0, 10]}
        assert result["timeline_anchors"] == [{"time": 0, "text": "intro"}]


class TestExtractSystemStatusFromCrew:
    """Test suite for extract_system_status_from_crew function."""

    def test_empty_crew_result_returns_empty_dict(self):
        """Test that empty crew result returns empty dict."""
        result = extract_system_status_from_crew(None)
        assert result == {}

    def test_crew_result_with_all_systems(self):
        """Test crew result containing all memory system keywords."""
        crew_result = "Successfully integrated vector memory, graph memory, and continual memory systems."
        result = extract_system_status_from_crew(crew_result)
        assert result["vector_memory"]["status"] == "integrated"
        assert result["graph_memory"]["status"] == "integrated"
        assert result["continual_memory"]["status"] == "integrated"

    def test_crew_result_with_vector_only(self):
        """Test crew result with only vector memory mentioned."""
        crew_result = "Vector embeddings stored successfully."
        result = extract_system_status_from_crew(crew_result)
        assert result["vector_memory"]["status"] == "integrated"
        assert result["graph_memory"]["status"] == "pending"
        assert result["continual_memory"]["status"] == "pending"

    def test_crew_result_with_graph_only(self):
        """Test crew result with only graph memory mentioned."""
        crew_result = "Graph relationships created and indexed."
        result = extract_system_status_from_crew(crew_result)
        assert result["vector_memory"]["status"] == "pending"
        assert result["graph_memory"]["status"] == "integrated"
        assert result["continual_memory"]["status"] == "pending"

    def test_crew_result_with_continual_only(self):
        """Test crew result with only continual memory mentioned."""
        crew_result = "Continual learning patterns established."
        result = extract_system_status_from_crew(crew_result)
        assert result["vector_memory"]["status"] == "pending"
        assert result["graph_memory"]["status"] == "pending"
        assert result["continual_memory"]["status"] == "integrated"

    def test_crew_result_with_no_systems(self):
        """Test crew result with no memory system keywords."""
        crew_result = "Analysis completed without memory integration."
        result = extract_system_status_from_crew(crew_result)
        assert result["vector_memory"]["status"] == "pending"
        assert result["graph_memory"]["status"] == "pending"
        assert result["continual_memory"]["status"] == "pending"

    def test_case_insensitive_detection(self):
        """Test that system detection is case-insensitive."""
        crew_result = "VECTOR and GRAPH systems ready, CONTINUAL learning active."
        result = extract_system_status_from_crew(crew_result)
        assert result["vector_memory"]["status"] == "integrated"
        assert result["graph_memory"]["status"] == "integrated"
        assert result["continual_memory"]["status"] == "integrated"

    def test_exception_handling_returns_empty_dict(self):
        """Test that exceptions are caught and return empty dict."""

        class BadObject:
            def __str__(self):
                raise ValueError("Cannot convert to string")

        result = extract_system_status_from_crew(BadObject())
        assert result == {}


class TestCreateExecutiveSummary:
    """Test suite for create_executive_summary function."""

    def test_basic_summary_with_threat_level(self):
        """Test basic summary generation with threat level."""
        analysis_data = {}
        threat_data = {"threat_level": "low"}
        result = create_executive_summary(analysis_data, threat_data)
        assert "low threat assessment" in result
        assert "Content analysis completed" in result

    def test_high_threat_level(self):
        """Test summary with high threat level."""
        analysis_data = {}
        threat_data = {"threat_level": "high"}
        result = create_executive_summary(analysis_data, threat_data)
        assert "high threat assessment" in result

    def test_unknown_threat_level(self):
        """Test summary with missing threat_level defaults to 'unknown'."""
        analysis_data = {}
        threat_data = {}
        result = create_executive_summary(analysis_data, threat_data)
        assert "unknown threat assessment" in result

    def test_non_dict_threat_data_returns_default(self):
        """Test that non-dict threat_data returns default summary."""
        analysis_data = {}
        threat_data = "not a dict"
        result = create_executive_summary(analysis_data, threat_data)
        assert result == "Intelligence briefing generated with standard analysis parameters."

    def test_exception_handling(self):
        """Test that exceptions return fallback summary."""
        result = create_executive_summary(None, None)
        assert result == "Intelligence briefing generated with standard analysis parameters."


class TestExtractKeyFindings:
    """Test suite for extract_key_findings function."""

    def test_basic_findings_extraction(self):
        """Test basic findings from all three data sources."""
        analysis_data = {"transcript": "Test transcript with 50 characters in total here."}
        verification_data = {"fact_checks": {"claim1": "verified", "claim2": "disputed"}}
        threat_data = {"threat_level": "medium"}
        result = extract_key_findings(analysis_data, verification_data, threat_data)
        assert len(result) == 3
        assert "Threat assessment: medium" in result
        assert "Fact verification completed with 2 claims analyzed" in result
        assert "Content analysis of" in result[2]
        assert "characters completed" in result[2]

    def test_findings_with_no_fact_checks(self):
        """Test findings when no fact checks present."""
        analysis_data = {"transcript": "Short"}
        verification_data = {}
        threat_data = {"threat_level": "low"}
        result = extract_key_findings(analysis_data, verification_data, threat_data)
        assert len(result) == 2
        assert "Threat assessment: low" in result
        assert any("Content analysis" in finding for finding in result)

    def test_findings_with_empty_transcript(self):
        """Test findings with empty transcript."""
        analysis_data = {"transcript": ""}
        verification_data = {"fact_checks": {"claim1": "verified"}}
        threat_data = {"threat_level": "high"}
        result = extract_key_findings(analysis_data, verification_data, threat_data)
        assert len(result) == 2
        assert "Threat assessment: high" in result
        assert "Fact verification completed" in result[1]

    def test_unknown_threat_level(self):
        """Test findings with missing threat_level."""
        analysis_data = {"transcript": "Test"}
        verification_data = {}
        threat_data = {}
        result = extract_key_findings(analysis_data, verification_data, threat_data)
        assert "Threat assessment: unknown" in result

    def test_fact_checks_non_dict(self):
        """Test that non-dict fact_checks is handled gracefully."""
        analysis_data = {"transcript": "Test"}
        verification_data = {"fact_checks": "not a dict"}
        threat_data = {"threat_level": "low"}
        result = extract_key_findings(analysis_data, verification_data, threat_data)
        assert len(result) == 2

    def test_exception_handling(self):
        """Test that exceptions return default finding."""
        result = extract_key_findings(None, None, None)
        assert result == ["Standard intelligence analysis completed"]

    def test_comprehensive_findings(self):
        """Test comprehensive findings with all data present."""
        analysis_data = {"transcript": "A" * 1000}
        verification_data = {"fact_checks": {f"claim{i}": "verified" for i in range(10)}}
        threat_data = {"threat_level": "critical"}
        result = extract_key_findings(analysis_data, verification_data, threat_data)
        assert len(result) == 3
        assert result[0] == "Threat assessment: critical"
        assert "10 claims analyzed" in result[1]
        assert "1000 characters completed" in result[2]
