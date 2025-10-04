"""
Unit tests for orchestrator/data_transformers module.

Tests all data transformation functions in isolation:
- normalize_acquisition_data
- merge_threat_and_deception_data
- transform_evidence_to_verdicts
- extract_fallacy_data
- calculate_data_completeness
- assign_intelligence_grade
- calculate_enhanced_summary_statistics
- generate_comprehensive_intelligence_insights
"""

import logging
from unittest.mock import Mock

from ultimate_discord_intelligence_bot.orchestrator import data_transformers
from ultimate_discord_intelligence_bot.step_result import StepResult


class TestNormalizeAcquisitionData:
    """Test normalize_acquisition_data function."""

    def test_handles_step_result_input(self):
        """Test normalization of StepResult input."""
        step_result = StepResult.ok(download={"url": "https://example.com"}, transcription={"text": "test"})
        normalized = data_transformers.normalize_acquisition_data(step_result)

        assert isinstance(normalized, dict)
        assert "download" in normalized
        assert "transcription" in normalized

    def test_handles_dict_input_with_pipeline_keys(self):
        """Test normalization of dict with pipeline keys."""
        data = {"download": {"file": "test.mp3"}, "analysis": {"summary": "test summary"}}
        normalized = data_transformers.normalize_acquisition_data(data)

        assert normalized == data
        assert "download" in normalized
        assert "analysis" in normalized

    def test_unwraps_nested_data_structure(self):
        """Test unwrapping of legacy nested data."""
        nested_data = {"data": {"transcription": {"text": "unwrapped"}, "download": {"url": "test"}}}
        normalized = data_transformers.normalize_acquisition_data(nested_data)

        assert "transcription" in normalized
        assert normalized["transcription"]["text"] == "unwrapped"

    def test_unwraps_raw_pipeline_payload(self):
        """Test unwrapping of raw_pipeline_payload."""
        data = {"raw_pipeline_payload": {"download": {"source": "youtube"}, "fallacy": {"count": 3}}}
        normalized = data_transformers.normalize_acquisition_data(data)

        assert "download" in normalized
        assert "fallacy" in normalized

    def test_returns_empty_dict_for_none_input(self):
        """Test handling of None input."""
        normalized = data_transformers.normalize_acquisition_data(None)

        assert normalized == {}

    def test_returns_empty_dict_for_non_dict_step_result(self):
        """Test handling of StepResult with non-dict data."""
        # When StepResult.data itself is not a dict (constructor doesn't prevent this)
        step_result = StepResult(success=True, data="not a dict")  # type: ignore
        normalized = data_transformers.normalize_acquisition_data(step_result)

        assert normalized == {}

    def test_returns_original_dict_when_no_unwrapping_needed(self):
        """Test passthrough when data has no nested structures."""
        data = {"some": "data", "other": "fields"}
        normalized = data_transformers.normalize_acquisition_data(data)

        assert normalized == data


class TestMergeThreatAndDeceptionData:
    """Test merge_threat_and_deception_data function."""

    def test_merges_successful_results(self):
        """Test merging two successful StepResults."""
        threat = StepResult.ok(threat_level="high", indicators=5)
        deception = StepResult.ok(deception_score=0.85, markers=["inconsistency"])

        merged = data_transformers.merge_threat_and_deception_data(threat, deception)

        assert merged.success
        # StepResult.ok(data=X, message=Y) nests X under 'data' key
        assert merged.data["data"]["threat_level"] == "high"
        assert merged.data["data"]["deception_metrics"]["deception_score"] == 0.85
        assert merged.data["data"]["deception_score"] == 0.85

    def test_preserves_threat_data_when_deception_fails(self):
        """Test that threat data is preserved when deception fails."""
        threat = StepResult.ok(threat_level="medium", message="Threat analyzed")
        deception = StepResult.fail(error="Deception analysis failed")

        merged = data_transformers.merge_threat_and_deception_data(threat, deception)

        assert merged.success
        assert merged.data["data"]["threat_level"] == "medium"
        assert "deception_metrics" in merged.data["data"]
        assert merged.data["data"]["deception_metrics"]["status"] == "skipped"

    def test_preserves_original_message(self):
        """Test that original threat message is preserved."""
        threat = StepResult.ok(threat_level="low", message="Original threat message")
        deception = StepResult.ok(deception_score=0.3)

        merged = data_transformers.merge_threat_and_deception_data(threat, deception)

        # Message is preserved at top level
        assert merged.data.get("message") == "Original threat message"
        # And original message from threat.data is in nested data
        assert merged.data["data"].get("message") == "Original threat message"

    def test_returns_threat_when_not_successful(self):
        """Test that failed threat result is returned as-is."""
        threat = StepResult.fail(error="Threat analysis failed")
        deception = StepResult.ok(result={"deception_score": 0.5})

        merged = data_transformers.merge_threat_and_deception_data(threat, deception)

        assert not merged.success
        assert merged.error == "Threat analysis failed"

    def test_returns_input_when_not_step_result(self):
        """Test that non-StepResult input is returned as-is."""
        threat = {"not": "a step result"}
        deception = StepResult.ok(result={"deception_score": 0.5})

        merged = data_transformers.merge_threat_and_deception_data(threat, deception)

        assert merged == threat

    def test_handles_skipped_deception(self):
        """Test handling of skipped deception analysis."""
        threat = StepResult.ok(threat_level="low")
        # Skip is actually success=True with custom_status='skipped'
        # So it goes through the success branch, not the error branch
        deception = StepResult.skip(reason="Deception analysis not needed")

        merged = data_transformers.merge_threat_and_deception_data(threat, deception)

        assert merged.success
        # Skipped deception data is merged directly (it's a successful result)
        assert "deception_metrics" in merged.data["data"]
        # The skip reason is in the deception_metrics
        assert merged.data["data"]["deception_metrics"]["reason"] == "Deception analysis not needed"


class TestTransformEvidenceToVerdicts:
    """Test transform_evidence_to_verdicts function."""

    def test_extracts_verdicts_from_items(self):
        """Test extraction of verdicts from items list."""
        fact_data = {
            "items": [
                {"verdict": "verified", "confidence": 0.9, "claim": "AI uses neural networks"},
                {"verdict": "disputed", "confidence": 0.4, "claim": "AGI by 2025"},
            ]
        }

        verdicts = data_transformers.transform_evidence_to_verdicts(fact_data)

        assert len(verdicts) == 2
        assert verdicts[0]["verdict"] == "verified"
        assert verdicts[0]["confidence"] == 0.9
        assert verdicts[1]["verdict"] == "disputed"

    def test_normalizes_verdict_strings(self):
        """Test that verdicts are lowercased and stripped."""
        fact_data = {"items": [{"verdict": "  VERIFIED  ", "claim": "Test"}]}

        verdicts = data_transformers.transform_evidence_to_verdicts(fact_data)

        assert verdicts[0]["verdict"] == "verified"

    def test_defaults_confidence_to_half(self):
        """Test that missing confidence defaults to 0.5."""
        fact_data = {"items": [{"verdict": "uncertain", "claim": "No confidence provided"}]}

        verdicts = data_transformers.transform_evidence_to_verdicts(fact_data)

        assert verdicts[0]["confidence"] == 0.5

    def test_clamps_confidence_to_valid_range(self):
        """Test that confidence is clamped between 0 and 1."""
        fact_data = {
            "items": [
                {"verdict": "verified", "confidence": 1.5, "claim": "Too high"},
                {"verdict": "verified", "confidence": -0.3, "claim": "Too low"},
            ]
        }

        verdicts = data_transformers.transform_evidence_to_verdicts(fact_data)

        assert verdicts[0]["confidence"] == 1.0
        assert verdicts[1]["confidence"] == 0.0

    def test_adds_default_fields_to_verdicts(self):
        """Test that default fields are added."""
        fact_data = {"items": [{"verdict": "verified", "claim": "Test claim"}]}

        verdicts = data_transformers.transform_evidence_to_verdicts(fact_data)

        assert verdicts[0]["source"] == "factcheck"
        assert verdicts[0]["salience"] == 1.0
        assert "claim" in verdicts[0]

    def test_fallback_creates_uncertain_verdict_with_no_evidence(self):
        """Test fallback when no items and no evidence."""
        fact_data = {"claim": "Unsupported claim", "evidence": []}

        verdicts = data_transformers.transform_evidence_to_verdicts(fact_data)

        assert len(verdicts) == 1
        assert verdicts[0]["verdict"] == "uncertain"
        assert verdicts[0]["confidence"] == 0.3
        assert verdicts[0]["source"] == "evidence_search"

    def test_fallback_creates_needs_context_with_multiple_evidence(self):
        """Test fallback when multiple evidence sources but no items."""
        fact_data = {"claim": "Complex claim", "evidence": ["source1", "source2", "source3", "source4"]}

        verdicts = data_transformers.transform_evidence_to_verdicts(fact_data)

        assert len(verdicts) == 1
        assert verdicts[0]["verdict"] == "needs context"
        assert verdicts[0]["confidence"] == 0.6
        assert verdicts[0]["source"] == "multi_source_evidence"

    def test_fallback_creates_uncertain_with_limited_evidence(self):
        """Test fallback when limited evidence sources."""
        fact_data = {"claim": "Partially supported", "evidence": ["source1", "source2"]}

        verdicts = data_transformers.transform_evidence_to_verdicts(fact_data)

        assert len(verdicts) == 1
        assert verdicts[0]["verdict"] == "uncertain"
        assert verdicts[0]["confidence"] == 0.4
        assert verdicts[0]["source"] == "limited_evidence"

    def test_uses_custom_logger(self):
        """Test that custom logger is accepted."""
        mock_logger = Mock(spec=logging.Logger)
        fact_data = {"items": [{"verdict": "verified", "claim": "Test"}]}

        verdicts = data_transformers.transform_evidence_to_verdicts(fact_data, logger_instance=mock_logger)

        assert len(verdicts) == 1
        # Logger should not be called for successful case


class TestExtractFallacyData:
    """Test extract_fallacy_data function."""

    def test_extracts_fallacies_list_of_dicts(self):
        """Test extraction from fallacies as list of dicts."""
        analysis = {
            "fallacies": [
                {"type": "ad hominem", "confidence": 0.8, "context": "Attack on person"},
                {"type": "strawman", "confidence": 0.6},
            ]
        }

        fallacies = data_transformers.extract_fallacy_data(analysis)

        assert len(fallacies) == 2
        assert fallacies[0]["type"] == "ad hominem"
        assert fallacies[0]["confidence"] == 0.8

    def test_extracts_fallacies_list_of_strings(self):
        """Test extraction from fallacies as list of strings."""
        analysis = {"fallacies": ["slippery slope", "false dilemma"]}

        fallacies = data_transformers.extract_fallacy_data(analysis)

        assert len(fallacies) == 2
        assert fallacies[0]["type"] == "slippery slope"
        assert fallacies[0]["confidence"] == 0.7  # Default

    def test_extracts_from_fallacies_detected_key(self):
        """Test extraction from alternative fallacies_detected key."""
        analysis = {
            "fallacies_detected": [
                {"type": "appeal to authority", "confidence": 0.85},
                {"type": "hasty generalization"},
            ]
        }

        fallacies = data_transformers.extract_fallacy_data(analysis)

        assert len(fallacies) == 2
        assert fallacies[0]["type"] == "appeal to authority"

    def test_returns_empty_list_when_no_fallacies(self):
        """Test returns empty list when no fallacies present."""
        analysis = {"other": "data"}

        fallacies = data_transformers.extract_fallacy_data(analysis)

        assert fallacies == []

    def test_handles_mixed_dict_and_string_fallacies(self):
        """Test handling of mixed format fallacies."""
        analysis = {"fallacies": [{"type": "red herring", "confidence": 0.75}, "bandwagon"]}

        fallacies = data_transformers.extract_fallacy_data(analysis)

        assert len(fallacies) == 2
        assert fallacies[0]["type"] == "red herring"
        assert fallacies[1]["type"] == "bandwagon"
        assert fallacies[1]["confidence"] == 0.7


class TestCalculateDataCompleteness:
    """Test calculate_data_completeness function."""

    def test_returns_one_when_all_sources_complete(self):
        """Test completeness of 1.0 when all sources have data."""
        source1 = {"data": "present"}
        source2 = {"more": "data"}
        source3 = {"also": "complete"}

        completeness = data_transformers.calculate_data_completeness(source1, source2, source3)

        assert completeness == 1.0

    def test_returns_half_when_half_sources_complete(self):
        """Test completeness of 0.5 when half sources complete."""
        source1 = {"data": "present"}
        source2 = {}
        source3 = None
        source4 = {"more": "data"}

        completeness = data_transformers.calculate_data_completeness(source1, source2, source3, source4)

        assert completeness == 0.5

    def test_returns_zero_when_all_sources_empty(self):
        """Test completeness of 0.0 when all sources empty."""
        completeness = data_transformers.calculate_data_completeness({}, None, {})

        assert completeness == 0.0

    def test_handles_single_source(self):
        """Test calculation with single source."""
        source = {"data": "present"}

        completeness = data_transformers.calculate_data_completeness(source)

        assert completeness == 1.0

    def test_handles_no_sources(self):
        """Test calculation with no sources."""
        completeness = data_transformers.calculate_data_completeness()

        assert completeness == 0.0

    def test_ignores_non_dict_sources(self):
        """Test that non-dict sources count as empty."""
        source1 = {"data": "present"}
        source2 = "not a dict"
        source3 = 123

        completeness = data_transformers.calculate_data_completeness(source1, source2, source3)

        assert completeness == 1.0 / 3.0

    def test_handles_exception_gracefully(self):
        """Test graceful error handling."""
        # Should not crash even with unusual inputs
        completeness = data_transformers.calculate_data_completeness(None, None, None)

        assert completeness == 0.0


class TestAssignIntelligenceGrade:
    """Test assign_intelligence_grade function."""

    def test_assigns_grade_a_for_complete_analysis(self):
        """Test grade A when all data sources complete."""
        analysis = {"transcript": "Full transcript"}
        threat = {"threat_level": "medium"}
        verification = {"fact_checks": [{"claim": "test"}]}

        grade = data_transformers.assign_intelligence_grade(analysis, threat, verification)

        assert grade == "A"

    def test_assigns_grade_b_for_threat_and_verification(self):
        """Test grade B when threat and verification present."""
        analysis = {}
        threat = {"threat_level": "low"}
        verification = {"fact_checks": [{"claim": "test"}]}

        grade = data_transformers.assign_intelligence_grade(analysis, threat, verification)

        assert grade == "B"

    def test_assigns_grade_b_for_verification_and_analysis(self):
        """Test grade B when verification and analysis present."""
        analysis = {"transcript": "Present"}
        threat = {"threat_level": "unknown"}
        verification = {"fact_checks": [{"claim": "test"}]}

        grade = data_transformers.assign_intelligence_grade(analysis, threat, verification)

        assert grade == "B"

    def test_assigns_grade_c_for_analysis_only(self):
        """Test grade C when only analysis present."""
        analysis = {"transcript": "Present"}
        threat = {}
        verification = {}

        grade = data_transformers.assign_intelligence_grade(analysis, threat, verification)

        assert grade == "C"

    def test_assigns_grade_d_for_minimal_data(self):
        """Test grade D when minimal data present."""
        analysis = {}
        threat = {}
        verification = {}

        grade = data_transformers.assign_intelligence_grade(analysis, threat, verification)

        assert grade == "D"

    def test_handles_unknown_threat_level(self):
        """Test handling of unknown threat level."""
        analysis = {"transcript": "Present"}
        threat = {"threat_level": "unknown"}
        verification = {}

        grade = data_transformers.assign_intelligence_grade(analysis, threat, verification)

        assert grade == "C"

    def test_handles_exception_returns_c(self):
        """Test that exceptions return grade C."""
        # Pass None values to trigger exception
        grade = data_transformers.assign_intelligence_grade(None, None, None)

        assert grade == "C"


class TestCalculateEnhancedSummaryStatistics:
    """Test calculate_enhanced_summary_statistics function."""

    def test_calculates_successful_stages(self):
        """Test counting of successful analysis stages."""
        results = {
            "transcription": {"text": "transcript"},
            "analysis": {"summary": "analyzed"},
            "threat_analysis": {},
            "verification": {"fact_checks": []},
        }

        stats = data_transformers.calculate_enhanced_summary_statistics(results)

        assert stats["successful_stages"] == 3  # Three non-empty dicts
        assert stats["total_stages_attempted"] == 4

    def test_extracts_workflow_metadata(self):
        """Test extraction of workflow metadata."""
        results = {
            "workflow_metadata": {"processing_time": 12.5, "capabilities_used": ["transcribe", "analyze", "verify"]},
            "transcription": {"text": "test"},
        }

        stats = data_transformers.calculate_enhanced_summary_statistics(results)

        assert stats["processing_time"] == 12.5
        assert stats["capabilities_used"] == 3

    def test_calculates_transcript_length(self):
        """Test calculation of transcript length."""
        results = {"transcription": {"transcript": "This is a test transcript with some words."}}

        stats = data_transformers.calculate_enhanced_summary_statistics(results)

        assert stats["transcript_length"] == len("This is a test transcript with some words.")

    def test_counts_fact_checks(self):
        """Test counting of fact checks performed."""
        results = {
            "information_verification": {
                "fact_checks": {"claim1": "verified", "claim2": "disputed", "claim3": "uncertain"}
            }
        }

        stats = data_transformers.calculate_enhanced_summary_statistics(results)

        assert stats["fact_checks_performed"] == 3

    def test_counts_threat_indicators(self):
        """Test counting of threat indicators."""
        results = {"threat_analysis": {"deception_analysis": {"indicator1": "high", "indicator2": "medium"}}}

        stats = data_transformers.calculate_enhanced_summary_statistics(results)

        assert stats["threat_indicators_found"] == 2

    def test_handles_empty_results(self):
        """Test handling of empty results."""
        results = {}

        stats = data_transformers.calculate_enhanced_summary_statistics(results)

        assert stats["successful_stages"] == 0
        assert stats["total_stages_attempted"] == 0

    def test_handles_exception_returns_error_dict(self):
        """Test that exceptions return error dictionary."""
        mock_logger = Mock(spec=logging.Logger)

        # Pass invalid data to trigger exception
        stats = data_transformers.calculate_enhanced_summary_statistics(None, logger_instance=mock_logger)

        assert "error" in stats
        assert "Statistics calculation failed" in stats["error"]


class TestGenerateComprehensiveIntelligenceInsights:
    """Test generate_comprehensive_intelligence_insights function."""

    def test_generates_threat_assessment_insight(self):
        """Test generation of threat assessment insight."""
        results = {"threat_analysis": {"threat_level": "high"}}

        insights = data_transformers.generate_comprehensive_intelligence_insights(results)

        assert len(insights) == 1
        assert "🛡️ Threat Assessment: HIGH level detected" in insights[0]

    def test_generates_verification_insight(self):
        """Test generation of verification insight."""
        results = {"information_verification": {"fact_checks": {"claim1": "verified", "claim2": "disputed"}}}

        insights = data_transformers.generate_comprehensive_intelligence_insights(results)

        assert len(insights) == 1
        assert "✅ Information Verification: 2 claims analyzed" in insights[0]

    def test_generates_behavioral_insight(self):
        """Test generation of behavioral insight."""
        results = {"behavioral_profiling": {"behavioral_risk_score": 0.73}}

        insights = data_transformers.generate_comprehensive_intelligence_insights(results)

        assert len(insights) == 1
        assert "👤 Behavioral Risk Score: 0.73" in insights[0]

    def test_generates_research_insight(self):
        """Test generation of research insight."""
        results = {"research_synthesis": {"research_topics": ["AI", "ML", "NLP"]}}

        insights = data_transformers.generate_comprehensive_intelligence_insights(results)

        assert len(insights) == 1
        assert "📚 Research Topics Analyzed: 3" in insights[0]

    def test_generates_content_quality_insight(self):
        """Test generation of content quality insight."""
        results = {"content_analysis": {"quality_score": 0.87}}

        insights = data_transformers.generate_comprehensive_intelligence_insights(results)

        assert len(insights) == 1
        assert "📊 Content Quality Score: 0.87" in insights[0]

    def test_generates_multiple_insights(self):
        """Test generation of multiple insights."""
        results = {
            "threat_analysis": {"threat_level": "medium"},
            "information_verification": {"fact_checks": {"claim": "verified"}},
            "behavioral_profiling": {"behavioral_risk_score": 0.5},
        }

        insights = data_transformers.generate_comprehensive_intelligence_insights(results)

        assert len(insights) == 3
        assert any("Threat Assessment" in insight for insight in insights)
        assert any("Information Verification" in insight for insight in insights)
        assert any("Behavioral Risk Score" in insight for insight in insights)

    def test_returns_empty_list_for_no_insights(self):
        """Test empty list when no insights available."""
        results = {}

        insights = data_transformers.generate_comprehensive_intelligence_insights(results)

        assert insights == []

    def test_handles_exception_returns_error_insight(self):
        """Test that exceptions return error insight."""
        mock_logger = Mock(spec=logging.Logger)

        # Pass invalid data to trigger exception
        insights = data_transformers.generate_comprehensive_intelligence_insights(None, logger_instance=mock_logger)

        assert len(insights) == 1
        assert "⚠️ Insights generation failed" in insights[0]

    def test_skips_zero_quality_score(self):
        """Test that zero quality scores are skipped."""
        results = {"content_analysis": {"quality_score": 0.0}}

        insights = data_transformers.generate_comprehensive_intelligence_insights(results)

        assert insights == []  # Should not include zero score
