"""Tests for Guest/Topic Pre-Briefs Service."""

from __future__ import annotations

from ultimate_discord_intelligence_bot.features.guest_preparation.guest_topic_pre_briefs_service import (
    ArgumentAnalysis,
    AudienceReactionPrediction,
    GuestTopicPreBriefsService,
    InterviewPreparationBrief,
    OpponentProcessSummary,
    get_guest_topic_pre_briefs_service,
)


class TestGuestTopicPreBriefsService:
    """Test guest/topic pre-briefs service functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.service = GuestTopicPreBriefsService(cache_size=100)

    def test_initialization(self) -> None:
        """Test service initialization."""
        assert self.service.cache_size == 100
        assert len(self.service._briefs_cache) == 0
        assert len(self.service._strength_indicators) == 2
        assert len(self.service._controversy_indicators) == 3

    def test_generate_interview_brief_basic(self) -> None:
        """Test basic interview brief generation."""
        guest_content = [
            {"text": "According to research, AI will transform 80% of jobs by 2030."},
            {"text": "I think this is concerning but also exciting."},
        ]

        result = self.service.generate_interview_brief(
            guest_content, guest_name="Test Guest", use_cache=False
        )

        assert result.success
        assert result.data is not None
        assert "interview_brief" in result.data

        brief = result.data["interview_brief"]
        assert brief.guest_name == "Test Guest"
        assert brief.opponent_process_summary.guest_position_summary
        assert len(brief.key_questions_to_ask) > 0

    def test_generate_interview_brief_empty_content(self) -> None:
        """Test handling of empty guest content."""
        result = self.service.generate_interview_brief([], guest_name="Test Guest")

        assert not result.success
        assert result.status == "bad_request"
        assert "cannot be empty" in result.error.lower()

    def test_predict_audience_reactions(self) -> None:
        """Test audience reaction prediction."""
        content_topics = [
            "artificial_intelligence",
            "job_displacement",
            "technology_ethics",
        ]

        prediction = self.service.predict_audience_reactions(content_topics)

        assert prediction.primary_reaction in [
            "excitement",
            "controversy",
            "mixed_reactions",
            "confusion",
        ]
        assert 0 <= prediction.confidence <= 1
        assert len(prediction.likely_questions) > 0
        assert 0 <= prediction.engagement_potential <= 1
        assert 0 <= prediction.controversy_risk <= 1

    def test_generate_live_fact_check_prompts(self) -> None:
        """Test live fact-check prompt generation."""
        guest_statements = [
            {
                "text": "According to research, AI will transform 80% of jobs by 2030.",
                "confidence": 0.7,
            },
            {"text": "I think this might be concerning.", "confidence": 0.4},
        ]

        prompts = self.service.generate_live_fact_check_prompts(guest_statements)

        assert isinstance(prompts, list)
        assert len(prompts) <= 10  # Limited to 10 prompts

    def test_clear_cache(self) -> None:
        """Test cache clearing."""
        # Add some cached briefs
        self.service.generate_interview_brief([{"text": "test"}], use_cache=True)

        assert len(self.service._briefs_cache) > 0

        # Clear cache
        result = self.service.clear_cache()

        assert result.success
        assert result.data["cleared_entries"] > 0
        assert len(self.service._briefs_cache) == 0

    def test_get_cache_stats(self) -> None:
        """Test cache statistics."""
        # Add some cached briefs
        self.service.generate_interview_brief([{"text": "test"}], use_cache=True)

        result = self.service.get_cache_stats()

        assert result.success
        assert result.data is not None
        assert "total_cached" in result.data
        assert "cache_size_limit" in result.data

        assert result.data["total_cached"] >= 1
        assert result.data["cache_size_limit"] == 100

    def test_model_selection(self) -> None:
        """Test model selection logic."""
        assert self.service._select_model("fast") == "fast_briefing"
        assert self.service._select_model("balanced") == "balanced_briefing"
        assert self.service._select_model("quality") == "quality_briefing"
        assert self.service._select_model("unknown") == "balanced_briefing"  # Default

    def test_argument_strength_calculation(self) -> None:
        """Test argument strength calculation."""
        # Strong argument with evidence
        strong_text = "According to research and data analysis, this approach is 80% more effective."
        strength = self.service._calculate_argument_strength(strong_text)
        assert strength > 0.7

        # Weak argument with opinion
        weak_text = "I think this might be better, but I'm not sure."
        strength2 = self.service._calculate_argument_strength(weak_text)
        assert strength2 < 0.5

    def test_evidence_quality_assessment(self) -> None:
        """Test evidence quality assessment."""
        # High quality evidence
        high_evidence = "Research shows that data indicates this approach works."
        quality = self.service._assess_evidence_quality(high_evidence)
        assert quality > 0.7

        # Low quality evidence
        low_evidence = "I think this might be true."
        quality2 = self.service._assess_evidence_quality(low_evidence)
        assert quality2 < 0.5

    def test_logical_coherence_assessment(self) -> None:
        """Test logical coherence assessment."""
        # Coherent argument with logical connectors
        coherent = (
            "Because research shows this works, therefore we should implement it."
        )
        coherence = self.service._assess_logical_coherence(coherent)
        assert coherence > 0.6

        # Less coherent argument
        incoherent = "This is good. That is bad."
        coherence2 = self.service._assess_logical_coherence(incoherent)
        assert coherence2 < coherence

    def test_controversy_calculation(self) -> None:
        """Test controversy level calculation."""
        # Controversial topics
        controversial_topics = ["politics", "controversial_issues", "debated_topics"]
        controversy = self.service._calculate_topic_controversy(controversial_topics)
        assert controversy > 0.5

        # Non-controversial topics
        safe_topics = ["technology", "education", "science"]
        controversy2 = self.service._calculate_topic_controversy(safe_topics)
        assert controversy2 < 0.5


class TestGuestTopicPreBriefsServiceSingleton:
    """Test singleton instance management."""

    def test_get_guest_topic_pre_briefs_service(self) -> None:
        """Test getting singleton instance."""
        service1 = get_guest_topic_pre_briefs_service()
        service2 = get_guest_topic_pre_briefs_service()

        # Should return same instance
        assert service1 is service2
        assert isinstance(service1, GuestTopicPreBriefsService)


class TestArgumentAnalysis:
    """Test argument analysis data structure."""

    def test_create_argument_analysis(self) -> None:
        """Test creating argument analysis."""
        argument = ArgumentAnalysis(
            argument_text="This is a strong argument with evidence.",
            strength_score=0.85,
            strength_category="strong",
            evidence_quality=0.9,
            logical_coherence=0.8,
            potential_counterarguments=["There may be exceptions"],
        )

        assert argument.argument_text == "This is a strong argument with evidence."
        assert argument.strength_score == 0.85
        assert argument.strength_category == "strong"
        assert argument.evidence_quality == 0.9
        assert argument.logical_coherence == 0.8
        assert len(argument.potential_counterarguments) == 1

    def test_argument_analysis_defaults(self) -> None:
        """Test argument analysis with default values."""
        argument = ArgumentAnalysis(
            argument_text="Basic argument",
            strength_score=0.5,
        )

        assert argument.strength_category == "moderate"  # Default category for 0.5
        assert argument.evidence_quality == 0.0  # Default
        assert argument.logical_coherence == 0.0  # Default
        assert argument.potential_counterarguments == []  # Default


class TestAudienceReactionPrediction:
    """Test audience reaction prediction data structure."""

    def test_create_audience_reaction_prediction(self) -> None:
        """Test creating audience reaction prediction."""
        prediction = AudienceReactionPrediction(
            primary_reaction="excitement",
            confidence=0.85,
            likely_questions=["How does this work?", "What are the implications?"],
            engagement_potential=0.9,
            controversy_risk=0.2,
        )

        assert prediction.primary_reaction == "excitement"
        assert prediction.confidence == 0.85
        assert len(prediction.likely_questions) == 2
        assert prediction.engagement_potential == 0.9
        assert prediction.controversy_risk == 0.2

    def test_audience_reaction_prediction_defaults(self) -> None:
        """Test audience reaction prediction with default values."""
        prediction = AudienceReactionPrediction(
            primary_reaction="neutral",
            confidence=0.5,
        )

        assert prediction.primary_reaction == "neutral"
        assert prediction.confidence == 0.5
        assert prediction.likely_questions == []  # Default
        assert prediction.engagement_potential == 0.0  # Default
        assert prediction.controversy_risk == 0.0  # Default


class TestOpponentProcessSummary:
    """Test opponent process summary data structure."""

    def test_create_opponent_process_summary(self) -> None:
        """Test creating opponent process summary."""
        summary = OpponentProcessSummary(
            guest_position_summary="The guest strongly advocates for AI safety measures.",
            key_arguments=[
                ArgumentAnalysis(
                    argument_text="AI needs strict regulation",
                    strength_score=0.9,
                    strength_category="strong",
                    evidence_quality=0.8,
                    logical_coherence=0.85,
                    potential_counterarguments=[
                        "Over-regulation could stifle innovation"
                    ],
                )
            ],
            potential_weaknesses=["May overlook innovation benefits"],
            audience_hooks=["Strong evidence-based arguments"],
            fact_check_priorities=["Verify regulation effectiveness claims"],
        )

        assert summary.guest_position_summary
        assert len(summary.key_arguments) == 1
        assert len(summary.potential_weaknesses) == 1
        assert len(summary.audience_hooks) == 1
        assert len(summary.fact_check_priorities) == 1

    def test_opponent_process_summary_defaults(self) -> None:
        """Test opponent process summary with default values."""
        summary = OpponentProcessSummary(
            guest_position_summary="Basic position",
            key_arguments=[],
            potential_weaknesses=[],
            audience_hooks=[],
            fact_check_priorities=[],
        )

        assert summary.guest_position_summary == "Basic position"
        assert len(summary.key_arguments) == 0
        assert len(summary.potential_weaknesses) == 0


class TestInterviewPreparationBrief:
    """Test interview preparation brief data structure."""

    def test_create_interview_preparation_brief(self) -> None:
        """Test creating interview preparation brief."""
        brief = InterviewPreparationBrief(
            guest_name="Test Guest",
            topic_overview="Discussion about AI and technology",
            opponent_process_summary=OpponentProcessSummary(
                guest_position_summary="Strong advocate for AI safety",
                key_arguments=[],
                potential_weaknesses=[],
                audience_hooks=[],
                fact_check_priorities=[],
            ),
            audience_reaction_prediction=AudienceReactionPrediction(
                primary_reaction="excitement",
                confidence=0.8,
                likely_questions=[],
                engagement_potential=0.9,
                controversy_risk=0.2,
            ),
            interview_strategy=["Focus on evidence-based questions"],
            live_fact_check_prompts=["Verify safety claims"],
            key_questions_to_ask=["What evidence supports your position?"],
            confidence_score=0.85,
        )

        assert brief.guest_name == "Test Guest"
        assert brief.topic_overview
        assert brief.opponent_process_summary.guest_position_summary
        assert brief.audience_reaction_prediction.primary_reaction == "excitement"
        assert len(brief.interview_strategy) == 1
        assert len(brief.live_fact_check_prompts) == 1
        assert len(brief.key_questions_to_ask) == 1
        assert brief.confidence_score == 0.85

    def test_interview_preparation_brief_defaults(self) -> None:
        """Test interview preparation brief with default values."""
        brief = InterviewPreparationBrief(
            guest_name="Test Guest",
            topic_overview="Basic overview",
            opponent_process_summary=OpponentProcessSummary(
                guest_position_summary="Position",
                key_arguments=[],
                potential_weaknesses=[],
                audience_hooks=[],
                fact_check_priorities=[],
            ),
            audience_reaction_prediction=AudienceReactionPrediction(
                primary_reaction="neutral",
                confidence=0.5,
                likely_questions=[],
                engagement_potential=0.5,
                controversy_risk=0.5,
            ),
            interview_strategy=[],
            live_fact_check_prompts=[],
            key_questions_to_ask=[],
        )

        assert brief.guest_name == "Test Guest"
        assert brief.confidence_score == 0.0  # Default


class TestGuestTopicPreBriefsIntegration:
    """Test guest preparation service integration scenarios."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.service = GuestTopicPreBriefsService()

    def test_comprehensive_interview_brief_generation(self) -> None:
        """Test comprehensive interview brief generation."""
        guest_content = [
            {
                "text": "According to extensive research and data analysis, AI safety measures are absolutely essential for responsible development."
            },
            {
                "text": "I believe over-regulation could potentially stifle innovation, but safety must come first."
            },
            {
                "text": "The evidence clearly shows that without proper safeguards, AI could cause significant harm."
            },
        ]

        topic_analysis = {
            "topics": ["artificial_intelligence", "safety_regulation", "innovation"],
        }

        result = self.service.generate_interview_brief(
            guest_content,
            topic_analysis=topic_analysis,
            guest_name="Dr. AI Safety Expert",
            interview_style="educational",
        )

        assert result.success
        brief = result.data["interview_brief"]

        # Should have comprehensive analysis
        assert brief.guest_name == "Dr. AI Safety Expert"
        assert brief.topic_overview
        assert brief.opponent_process_summary.guest_position_summary
        assert len(brief.key_questions_to_ask) > 0

        # Should analyze arguments
        arguments = brief.opponent_process_summary.key_arguments
        assert len(arguments) > 0

        # Should predict audience reactions
        audience = brief.audience_reaction_prediction
        assert audience.primary_reaction in [
            "excitement",
            "controversy",
            "mixed_reactions",
            "confusion",
        ]

    def test_live_fact_check_prompt_generation(self) -> None:
        """Test live fact-check prompt generation."""
        guest_statements = [
            {
                "text": "According to research, AI will transform 80% of jobs by 2030.",
                "confidence": 0.7,
            },
            {"text": "I think this might be concerning.", "confidence": 0.3},
            {
                "text": "The data clearly shows improved performance metrics.",
                "confidence": 0.9,
            },
        ]

        prompts = self.service.generate_live_fact_check_prompts(guest_statements)

        assert isinstance(prompts, list)

        # Should generate prompts for statements with moderate confidence
        moderate_confidence_statements = [
            s for s in guest_statements if 0.3 <= s["confidence"] <= 0.8
        ]
        assert len(prompts) <= len(moderate_confidence_statements)

    def test_audience_reaction_prediction_with_topics(self) -> None:
        """Test audience reaction prediction with different topics."""
        # Controversial topics
        controversial_topics = ["politics", "controversial_issues", "debated_topics"]
        controversial_prediction = self.service.predict_audience_reactions(
            controversial_topics
        )

        # Safe topics
        safe_topics = ["technology", "education", "science"]
        safe_prediction = self.service.predict_audience_reactions(safe_topics)

        # Controversial topics should have higher controversy risk
        assert (
            controversial_prediction.controversy_risk
            >= safe_prediction.controversy_risk
        )

        # Safe topics should have higher engagement potential
        assert (
            safe_prediction.engagement_potential
            >= controversial_prediction.engagement_potential
        )
