"""Tests for insight_generators module."""

from unittest.mock import Mock

from ultimate_discord_intelligence_bot.orchestrator.insight_generators import (
    generate_ai_recommendations,
    generate_autonomous_insights,
    generate_specialized_insights,
    generate_strategic_recommendations,
)


class TestGenerateAutonomousInsights:
    """Test generate_autonomous_insights function."""

    def test_generate_autonomous_insights_low_deception(self):
        """Test insights generation with low deception score."""
        results = {
            "deception_score": {"deception_score": 0.2},
            "fact_analysis": {"logical_fallacies": {"fallacies_detected": []}},
            "cross_platform_intel": {},
            "knowledge_integration": {},
        }

        insights = generate_autonomous_insights(results)

        assert any("🟢 Content shows high reliability" in insight for insight in insights)

    def test_generate_autonomous_insights_medium_deception(self):
        """Test insights generation with medium deception score."""
        results = {
            "deception_score": {"deception_score": 0.5},
            "fact_analysis": {"logical_fallacies": {"fallacies_detected": []}},
            "cross_platform_intel": {},
            "knowledge_integration": {},
        }

        insights = generate_autonomous_insights(results)

        assert any("🟡 Content shows mixed reliability" in insight for insight in insights)

    def test_generate_autonomous_insights_high_deception(self):
        """Test insights generation with high deception score."""
        results = {
            "deception_score": {"deception_score": 0.8},
            "fact_analysis": {"logical_fallacies": {"fallacies_detected": []}},
            "cross_platform_intel": {},
            "knowledge_integration": {},
        }

        insights = generate_autonomous_insights(results)

        assert any("🔴 Content shows significant deception" in insight for insight in insights)

    def test_generate_autonomous_insights_with_fallacies(self):
        """Test insights generation with detected fallacies."""
        results = {
            "deception_score": {"deception_score": 0.3},
            "fact_analysis": {"logical_fallacies": {"fallacies_detected": ["strawman", "ad hominem", "false dilemma"]}},
            "cross_platform_intel": {},
            "knowledge_integration": {},
        }

        insights = generate_autonomous_insights(results)

        assert any("⚠️ Detected 3 logical fallacies" in insight for insight in insights)
        assert any("strawman, ad hominem, false dilemma" in insight for insight in insights)

    def test_generate_autonomous_insights_with_cross_platform_intel(self):
        """Test insights generation with cross-platform intelligence."""
        results = {
            "deception_score": {"deception_score": 0.3},
            "fact_analysis": {"logical_fallacies": {"fallacies_detected": []}},
            "cross_platform_intel": {"source1": "data1", "source2": "data2"},
            "knowledge_integration": {},
        }

        insights = generate_autonomous_insights(results)

        assert any("🌐 Cross-platform intelligence gathered" in insight for insight in insights)

    def test_generate_autonomous_insights_with_knowledge_storage(self):
        """Test insights generation with knowledge base integration."""
        results = {
            "deception_score": {"deception_score": 0.3},
            "fact_analysis": {"logical_fallacies": {"fallacies_detected": []}},
            "cross_platform_intel": {},
            "knowledge_integration": {"knowledge_storage": True},
        }

        insights = generate_autonomous_insights(results)

        assert any("💾 Analysis results successfully integrated" in insight for insight in insights)

    def test_generate_autonomous_insights_exception_handling(self):
        """Test exception handling in insights generation."""
        # Create results that will cause an exception
        results = {"deception_score": Mock(side_effect=Exception("Test exception"))}

        insights = generate_autonomous_insights(results)

        assert len(insights) == 1
        assert "❌ Insight generation failed" in insights[0]


class TestGenerateSpecializedInsights:
    """Test generate_specialized_insights function."""

    def test_generate_specialized_insights_low_threat(self):
        """Test specialized insights with low threat level."""
        results = {
            "deception": {"threat_level": "low"},
            "verification": {"logical_analysis": {"fallacies_detected": []}},
            "knowledge": {},
            "behavioral": {},
            "social": {},
        }

        insights = generate_specialized_insights(results)

        assert any("🟢 Specialized threat analysis indicates low deception risk" in insight for insight in insights)

    def test_generate_specialized_insights_medium_threat(self):
        """Test specialized insights with medium threat level."""
        results = {
            "deception": {"threat_level": "medium"},
            "verification": {"logical_analysis": {"fallacies_detected": []}},
            "knowledge": {},
            "behavioral": {},
            "social": {},
        }

        insights = generate_specialized_insights(results)

        assert any("🟡 Specialized analysis detected mixed reliability" in insight for insight in insights)

    def test_generate_specialized_insights_high_threat(self):
        """Test specialized insights with high threat level."""
        results = {
            "deception": {"threat_level": "high"},
            "verification": {"logical_analysis": {"fallacies_detected": []}},
            "knowledge": {},
            "behavioral": {},
            "social": {},
        }

        insights = generate_specialized_insights(results)

        assert any("🔴 Specialized threat analysis indicates high deception risk" in insight for insight in insights)

    def test_generate_specialized_insights_with_fallacies(self):
        """Test specialized insights with detected fallacies."""
        results = {
            "deception": {"threat_level": "low"},
            "verification": {"logical_analysis": {"fallacies_detected": ["strawman", "ad hominem"]}},
            "knowledge": {},
            "behavioral": {},
            "social": {},
        }

        insights = generate_specialized_insights(results)

        assert any(
            "⚠️ Information Verification Specialist detected 2 logical fallacies" in insight for insight in insights
        )

    def test_generate_specialized_insights_with_knowledge_systems(self):
        """Test specialized insights with knowledge systems."""
        results = {
            "deception": {"threat_level": "low"},
            "verification": {"logical_analysis": {"fallacies_detected": []}},
            "knowledge": {"knowledge_systems": True},
            "behavioral": {},
            "social": {},
        }

        insights = generate_specialized_insights(results)

        assert any("💾 Knowledge Integration Manager successfully stored" in insight for insight in insights)

    def test_generate_specialized_insights_high_consistency(self):
        """Test specialized insights with high behavioral consistency."""
        results = {
            "deception": {"threat_level": "low"},
            "verification": {"logical_analysis": {"fallacies_detected": []}},
            "knowledge": {},
            "behavioral": {"behavioral_indicators": {"consistency_score": 0.8}},
            "social": {},
        }

        insights = generate_specialized_insights(results)

        assert any("📊 Behavioral Pattern Analyst found high consistency indicators" in insight for insight in insights)

    def test_generate_specialized_insights_low_consistency(self):
        """Test specialized insights with low behavioral consistency."""
        results = {
            "deception": {"threat_level": "low"},
            "verification": {"logical_analysis": {"fallacies_detected": []}},
            "knowledge": {},
            "behavioral": {"behavioral_indicators": {"consistency_score": 0.2}},
            "social": {},
        }

        insights = generate_specialized_insights(results)

        assert any("⚠️ Behavioral Pattern Analyst detected consistency anomalies" in insight for insight in insights)

    def test_generate_specialized_insights_with_social_data(self):
        """Test specialized insights with social intelligence data."""
        results = {
            "deception": {"threat_level": "low"},
            "verification": {"logical_analysis": {"fallacies_detected": []}},
            "knowledge": {},
            "behavioral": {},
            "social": {"source1": "data1", "source2": "data2"},
        }

        insights = generate_specialized_insights(results)

        assert any(
            "🌐 Social Intelligence Coordinator gathered cross-platform context" in insight for insight in insights
        )

    def test_generate_specialized_insights_exception_handling(self):
        """Test exception handling in specialized insights generation."""
        # Create a results dict that will cause an exception when accessed
        results = {"deception": Mock()}
        results["deception"].get.side_effect = Exception("Test exception")

        insights = generate_specialized_insights(results)

        assert len(insights) == 1
        assert "❌ Specialized insight generation encountered an error" in insights[0]


class TestGenerateAiRecommendations:
    """Test generate_ai_recommendations function."""

    def test_generate_ai_recommendations_low_scores(self):
        """Test AI recommendations with low quality scores."""
        quality_dimensions = {
            "content_coherence": 0.3,
            "factual_accuracy": 0.2,
            "source_credibility": 0.4,
        }
        ai_quality_score = 0.3
        analysis_data = {}
        verification_data = {}

        recommendations = generate_ai_recommendations(
            quality_dimensions, ai_quality_score, analysis_data, verification_data
        )

        assert any("⚠️ Improve transcript structuring" in rec for rec in recommendations)
        assert any("⚠️ Collect additional evidence" in rec for rec in recommendations)
        assert any("🔍 Monitor source credibility" in rec for rec in recommendations)

    def test_generate_ai_recommendations_high_quality(self):
        """Test AI recommendations with high quality score."""
        quality_dimensions = {"content_coherence": 0.9, "factual_accuracy": 0.8}
        ai_quality_score = 0.9
        analysis_data = {"content_metadata": {"title": "Test Content"}}
        verification_data = {}

        recommendations = generate_ai_recommendations(
            quality_dimensions, ai_quality_score, analysis_data, verification_data
        )

        assert any("✅ Maintain current quality controls for 'Test Content'." in rec for rec in recommendations)

    def test_generate_ai_recommendations_high_quality_no_title(self):
        """Test AI recommendations with high quality but no title."""
        quality_dimensions = {"content_coherence": 0.9, "factual_accuracy": 0.8}
        ai_quality_score = 0.9
        analysis_data = {}
        verification_data = {}

        recommendations = generate_ai_recommendations(
            quality_dimensions, ai_quality_score, analysis_data, verification_data
        )

        assert any("✅ Maintain current quality controls; overall quality is strong." in rec for rec in recommendations)

    def test_generate_ai_recommendations_no_recommendations_with_verification(self):
        """Test AI recommendations with no specific recommendations but verification data."""
        quality_dimensions = {"content_coherence": 0.8, "factual_accuracy": 0.7}
        ai_quality_score = 0.7
        analysis_data = {}
        verification_data = {"fact_checks": True}

        recommendations = generate_ai_recommendations(
            quality_dimensions, ai_quality_score, analysis_data, verification_data
        )

        assert any("✅ Verification coverage is comprehensive" in rec for rec in recommendations)

    def test_generate_ai_recommendations_no_recommendations_no_verification(self):
        """Test AI recommendations with no specific recommendations and no verification."""
        quality_dimensions = {"content_coherence": 0.8, "factual_accuracy": 0.7}
        ai_quality_score = 0.7
        analysis_data = {}
        verification_data = {}

        recommendations = generate_ai_recommendations(
            quality_dimensions, ai_quality_score, analysis_data, verification_data
        )

        assert any("ℹ️ Add more fact-checking coverage" in rec for rec in recommendations)

    def test_generate_ai_recommendations_invalid_dimensions(self):
        """Test AI recommendations with invalid dimension values."""
        quality_dimensions = {
            "content_coherence": "invalid",
            "factual_accuracy": None,
            "valid_dimension": 0.3,
        }
        ai_quality_score = 0.3
        analysis_data = {}
        verification_data = {}

        recommendations = generate_ai_recommendations(
            quality_dimensions, ai_quality_score, analysis_data, verification_data
        )

        # Should only process valid dimensions
        assert any("⚠️ valid_dimension (score 0.30)" in rec for rec in recommendations)


class TestGenerateStrategicRecommendations:
    """Test generate_strategic_recommendations function."""

    def test_generate_strategic_recommendations_high_threat(self):
        """Test strategic recommendations with high threat level."""
        analysis_data = {}
        threat_data = {"threat_level": "high"}
        verification_data = {}

        recommendations = generate_strategic_recommendations(analysis_data, threat_data, verification_data)

        assert "Recommend enhanced scrutiny and additional verification" in recommendations

    def test_generate_strategic_recommendations_medium_threat(self):
        """Test strategic recommendations with medium threat level."""
        analysis_data = {}
        threat_data = {"threat_level": "medium"}
        verification_data = {}

        recommendations = generate_strategic_recommendations(analysis_data, threat_data, verification_data)

        assert "Suggest moderate caution and cross-referencing" in recommendations

    def test_generate_strategic_recommendations_low_threat(self):
        """Test strategic recommendations with low threat level."""
        analysis_data = {}
        threat_data = {"threat_level": "low"}
        verification_data = {}

        recommendations = generate_strategic_recommendations(analysis_data, threat_data, verification_data)

        assert "Standard content handling protocols apply" in recommendations

    def test_generate_strategic_recommendations_unknown_threat(self):
        """Test strategic recommendations with unknown threat level."""
        analysis_data = {}
        threat_data = {"threat_level": "unknown"}
        verification_data = {}

        recommendations = generate_strategic_recommendations(analysis_data, threat_data, verification_data)

        assert "Standard content handling protocols apply" in recommendations

    def test_generate_strategic_recommendations_no_threat_data(self):
        """Test strategic recommendations with no threat data."""
        analysis_data = {}
        threat_data = {}
        verification_data = {}

        recommendations = generate_strategic_recommendations(analysis_data, threat_data, verification_data)

        assert "Standard content handling protocols apply" in recommendations

    def test_generate_strategic_recommendations_exception_handling(self):
        """Test exception handling in strategic recommendations."""
        analysis_data = {}
        threat_data = Mock()
        threat_data.get.side_effect = Exception("Test exception")
        verification_data = {}

        recommendations = generate_strategic_recommendations(analysis_data, threat_data, verification_data)

        assert len(recommendations) == 1
        assert "Strategic recommendation generation encountered an error" in recommendations[0]
