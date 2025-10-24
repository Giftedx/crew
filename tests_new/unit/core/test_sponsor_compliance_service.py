"""Tests for Sponsor Compliance Assistant."""

from __future__ import annotations

from features.sponsor_assistant.sponsor_compliance_service import (
    BrandGuidelines,
    ComplianceReport,
    SponsorComplianceAssistant,
    SponsorCutList,
    SponsorScript,
    get_sponsor_compliance_assistant,
)


class TestSponsorComplianceAssistant:
    """Test sponsor compliance assistant functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.assistant = SponsorComplianceAssistant(cache_size=100)

    def test_initialization(self) -> None:
        """Test service initialization."""
        assert self.assistant.cache_size == 100
        assert len(self.assistant._compliance_cache) == 0
        assert len(self.assistant._default_policies) == 3

    def test_analyze_compliance_safe_content(self) -> None:
        """Test compliance analysis of safe content."""
        content_segments = [
            {
                "start_time": 0.0,
                "end_time": 30.0,
                "text": "This is safe, professional content.",
            },
            {
                "start_time": 30.0,
                "end_time": 60.0,
                "text": "Educational discussion about technology.",
            },
        ]

        result = self.assistant.analyze_compliance(content_segments, policy_pack="general_audience", use_cache=False)

        assert result.success
        assert result.data is not None
        assert "compliance_report" in result.data

        compliance_report = result.data["compliance_report"]
        assert compliance_report.overall_compliance_score > 0.8
        assert len(compliance_report.policy_violations) == 0

    def test_analyze_compliance_unsafe_content(self) -> None:
        """Test compliance analysis of unsafe content."""
        content_segments = [
            {
                "start_time": 0.0,
                "end_time": 30.0,
                "text": "This content contains profanity and hate speech.",
            },
        ]

        result = self.assistant.analyze_compliance(content_segments, policy_pack="family_friendly", use_cache=False)

        assert result.success
        compliance_report = result.data["compliance_report"]
        assert compliance_report.overall_compliance_score < 0.8
        assert len(compliance_report.policy_violations) > 0

    def test_generate_cut_list(self) -> None:
        """Test sponsor-safe cut list generation."""
        content_segments = [
            {"start_time": 0.0, "end_time": 30.0, "text": "Safe content introduction."},
            {
                "start_time": 30.0,
                "end_time": 60.0,
                "text": "Unsafe content with violations.",
            },
            {"start_time": 60.0, "end_time": 90.0, "text": "Safe conclusion."},
        ]

        brand_guidelines = BrandGuidelines(
            brand_name="TestBrand",
            target_audience="family",
            allowed_topics=["education", "entertainment"],
            prohibited_topics=["violence", "profanity"],
            tone_requirements=["professional"],
        )

        result = self.assistant.generate_compliant_cut_list(content_segments, brand_guidelines)

        assert result.success
        assert result.data is not None
        assert "cut_list" in result.data

        cut_list = result.data["cut_list"]
        assert len(cut_list.safe_segments) >= 2  # Should include safe segments
        assert len(cut_list.unsafe_segments) >= 1  # Should mark unsafe segments

    def test_generate_sponsor_script(self) -> None:
        """Test sponsor script generation."""
        content_segments = [
            {"start_time": 0.0, "end_time": 30.0, "text": "Safe educational content."},
        ]

        brand_guidelines = BrandGuidelines(
            brand_name="TestBrand",
            target_audience="professional",
            allowed_topics=["education"],
            prohibited_topics=["controversial"],
            tone_requirements=["professional"],
        )

        result = self.assistant.generate_sponsor_script(
            content_segments,
            brand_guidelines,
            sponsor_product="Premium Software",
            sponsor_message="It helps professionals work more efficiently",
        )

        assert result.success
        assert result.data is not None
        assert "sponsor_script" in result.data

        sponsor_script = result.data["sponsor_script"]
        assert len(sponsor_script.script_segments) >= 1
        assert len(sponsor_script.brand_guidelines_applied) > 0

    def test_clear_cache(self) -> None:
        """Test cache clearing."""
        # Add some cached analyses
        self.assistant.analyze_compliance([{"text": "test"}], use_cache=True)

        assert len(self.assistant._compliance_cache) > 0

        # Clear cache
        result = self.assistant.clear_cache()

        assert result.success
        assert result.data["cleared_entries"] > 0
        assert len(self.assistant._compliance_cache) == 0

    def test_get_cache_stats(self) -> None:
        """Test cache statistics."""
        # Add some cached analyses
        self.assistant.analyze_compliance([{"text": "test"}], use_cache=True)

        result = self.assistant.get_cache_stats()

        assert result.success
        assert result.data is not None
        assert "total_cached" in result.data
        assert "cache_size_limit" in result.data

        assert result.data["total_cached"] >= 1
        assert result.data["cache_size_limit"] == 100


class TestSponsorComplianceAssistantSingleton:
    """Test singleton instance management."""

    def test_get_sponsor_compliance_assistant(self) -> None:
        """Test getting singleton instance."""
        assistant1 = get_sponsor_compliance_assistant()
        assistant2 = get_sponsor_compliance_assistant()

        # Should return same instance
        assert assistant1 is assistant2
        assert isinstance(assistant1, SponsorComplianceAssistant)


class TestBrandGuidelines:
    """Test brand guidelines data structure."""

    def test_create_brand_guidelines(self) -> None:
        """Test creating brand guidelines."""
        guidelines = BrandGuidelines(
            brand_name="TestBrand",
            target_audience="family",
            allowed_topics=["education", "entertainment"],
            prohibited_topics=["violence", "adult_content"],
            tone_requirements=["professional", "educational"],
            content_warnings=["mild_language"],
            sponsorship_format="integrated",
            max_segment_duration=300,
        )

        assert guidelines.brand_name == "TestBrand"
        assert guidelines.target_audience == "family"
        assert len(guidelines.allowed_topics) == 2
        assert len(guidelines.prohibited_topics) == 2
        assert len(guidelines.tone_requirements) == 2
        assert guidelines.sponsorship_format == "integrated"
        assert guidelines.max_segment_duration == 300

    def test_brand_guidelines_defaults(self) -> None:
        """Test brand guidelines with default values."""
        guidelines = BrandGuidelines(
            brand_name="TestBrand",
            target_audience="general",
            allowed_topics=["general"],
            prohibited_topics=[],
            tone_requirements=["casual"],
        )

        assert guidelines.target_audience == "general"
        assert guidelines.content_warnings == []
        assert guidelines.max_segment_duration == 300  # Default
        assert guidelines.sponsorship_format == "integrated"  # Default


class TestComplianceReport:
    """Test compliance report data structure."""

    def test_create_compliance_report(self) -> None:
        """Test creating compliance report."""
        report = ComplianceReport(
            overall_compliance_score=0.85,
            brand_suitability_score=0.9,
            policy_violations=["profanity"],
            content_warnings=["mild_language"],
            recommendations=["Remove inappropriate content"],
            safe_content_percentage=0.8,
            audit_trail=[{"segment": 1, "compliance_score": 0.8}],
        )

        assert report.overall_compliance_score == 0.85
        assert report.brand_suitability_score == 0.9
        assert len(report.policy_violations) == 1
        assert "profanity" in report.policy_violations
        assert len(report.recommendations) == 1
        assert report.safe_content_percentage == 0.8

    def test_compliance_report_perfect_score(self) -> None:
        """Test compliance report with perfect compliance."""
        report = ComplianceReport(
            overall_compliance_score=1.0,
            brand_suitability_score=1.0,
            policy_violations=[],
            content_warnings=[],
            recommendations=[],
            safe_content_percentage=1.0,
            audit_trail=[],
        )

        assert report.overall_compliance_score == 1.0
        assert report.brand_suitability_score == 1.0
        assert len(report.policy_violations) == 0
        assert len(report.recommendations) == 0


class TestSponsorCutList:
    """Test sponsor cut list data structure."""

    def test_create_sponsor_cut_list(self) -> None:
        """Test creating sponsor cut list."""
        from features.sponsor_assistant.sponsor_compliance_service import (
            ComplianceSegment,
        )

        safe_segment = ComplianceSegment(
            start_time=0.0,
            end_time=30.0,
            duration=30.0,
            content_type="discussion",
            safety_level="safe",
            compliance_score=0.9,
            brand_suitability=0.95,
            risk_factors=[],
            recommendations=[],
        )

        cut_list = SponsorCutList(
            total_duration=30.0,
            safe_segments=[safe_segment],
            unsafe_segments=[],
            transitions=[],
            sponsor_placements=[{"position": 15.0, "type": "integrated"}],
            compliance_summary={"overall_compliance": 0.9},
        )

        assert cut_list.total_duration == 30.0
        assert len(cut_list.safe_segments) == 1
        assert len(cut_list.unsafe_segments) == 0
        assert len(cut_list.sponsor_placements) == 1

    def test_sponsor_cut_list_with_unsafe_content(self) -> None:
        """Test sponsor cut list with unsafe segments."""
        from features.sponsor_assistant.sponsor_compliance_service import (
            ComplianceSegment,
        )

        safe_segment = ComplianceSegment(
            start_time=0.0,
            end_time=30.0,
            duration=30.0,
            content_type="discussion",
            safety_level="safe",
            compliance_score=0.9,
            brand_suitability=0.95,
            risk_factors=[],
            recommendations=[],
        )

        unsafe_segment = ComplianceSegment(
            start_time=30.0,
            end_time=60.0,
            duration=30.0,
            content_type="unsafe",
            safety_level="unsafe",
            compliance_score=0.3,
            brand_suitability=0.0,
            risk_factors=["profanity"],
            recommendations=["Remove segment"],
        )

        cut_list = SponsorCutList(
            total_duration=30.0,  # Only safe content included
            safe_segments=[safe_segment],
            unsafe_segments=[unsafe_segment],
            transitions=[],
            sponsor_placements=[],
            compliance_summary={"overall_compliance": 0.5},
        )

        assert cut_list.total_duration == 30.0
        assert len(cut_list.safe_segments) == 1
        assert len(cut_list.unsafe_segments) == 1


class TestSponsorScript:
    """Test sponsor script data structure."""

    def test_create_sponsor_script(self) -> None:
        """Test creating sponsor script."""
        script = SponsorScript(
            script_segments=[
                {
                    "segment_index": 0,
                    "content": "Introduction",
                    "segment_type": "content",
                },
                {
                    "segment_index": 1,
                    "content": "Sponsor message",
                    "segment_type": "sponsor",
                },
            ],
            brand_guidelines_applied=["professional_tone", "family_audience"],
            compliance_annotations=[{"segment_index": 0, "compliance_score": 0.9}],
            total_script_duration=60.0,
            sponsor_integration_points=[{"segment_index": 1, "integration_type": "integrated"}],
        )

        assert len(script.script_segments) == 2
        assert len(script.brand_guidelines_applied) == 2
        assert len(script.compliance_annotations) == 1
        assert script.total_script_duration == 60.0
        assert len(script.sponsor_integration_points) == 1

    def test_sponsor_script_empty(self) -> None:
        """Test sponsor script with no content."""
        script = SponsorScript(
            script_segments=[],
            brand_guidelines_applied=[],
            compliance_annotations=[],
            total_script_duration=0.0,
            sponsor_integration_points=[],
        )

        assert len(script.script_segments) == 0
        assert script.total_script_duration == 0.0


class TestSponsorComplianceIntegration:
    """Test sponsor compliance service integration."""

    def test_end_to_end_compliance_workflow(self) -> None:
        """Test complete compliance analysis workflow."""
        content_segments = [
            {
                "start_time": 0.0,
                "end_time": 30.0,
                "text": "This is safe educational content.",
            },
            {
                "start_time": 30.0,
                "end_time": 60.0,
                "text": "This contains profanity and should be flagged.",
            },
            {
                "start_time": 60.0,
                "end_time": 90.0,
                "text": "This is also safe content.",
            },
        ]

        brand_guidelines = BrandGuidelines(
            brand_name="TestBrand",
            target_audience="family",
            allowed_topics=["education"],
            prohibited_topics=["profanity"],
            tone_requirements=["professional"],
        )

        # Step 1: Analyze compliance
        compliance_result = self.assistant.analyze_compliance(
            content_segments, brand_guidelines, policy_pack="family_friendly"
        )

        assert compliance_result.success
        compliance_report = compliance_result.data["compliance_report"]

        # Should detect violations
        assert len(compliance_report.policy_violations) > 0
        assert compliance_report.overall_compliance_score < 1.0

        # Step 2: Generate cut list
        cut_list_result = self.assistant.generate_compliant_cut_list(content_segments, brand_guidelines)

        assert cut_list_result.success
        cut_list = cut_list_result.data["cut_list"]

        # Should have safe and unsafe segments
        assert len(cut_list.safe_segments) >= 2
        assert len(cut_list.unsafe_segments) >= 1
        assert cut_list.total_duration < 90.0  # Should exclude unsafe content

    def test_sponsor_script_generation(self) -> None:
        """Test sponsor script generation with brand integration."""
        content_segments = [
            {"start_time": 0.0, "end_time": 30.0, "text": "Safe educational content."},
        ]

        brand_guidelines = BrandGuidelines(
            brand_name="TestBrand",
            target_audience="professional",
            allowed_topics=["education"],
            prohibited_topics=[],
            tone_requirements=["professional"],
            sponsorship_format="integrated",
        )

        script_result = self.assistant.generate_sponsor_script(
            content_segments,
            brand_guidelines,
            sponsor_product="Premium Software",
            sponsor_message="It helps professionals work more efficiently",
        )

        assert script_result.success
        sponsor_script = script_result.data["sponsor_script"]

        # Should generate script segments
        assert len(sponsor_script.script_segments) >= 1

        # Should include sponsor content
        sponsor_segments = [s for s in sponsor_script.script_segments if s["segment_type"] == "sponsor"]
        assert len(sponsor_segments) >= 1

        # Should include brand guidelines
        assert len(sponsor_script.brand_guidelines_applied) > 0

    def test_different_policy_packs(self) -> None:
        """Test compliance analysis with different policy packs."""
        unsafe_content = [
            {"start_time": 0.0, "end_time": 30.0, "text": "Content with profanity."},
        ]

        # Test with strict policy pack
        strict_result = self.assistant.analyze_compliance(unsafe_content, policy_pack="family_friendly")

        # Test with lenient policy pack
        lenient_result = self.assistant.analyze_compliance(unsafe_content, policy_pack="general_audience")

        assert strict_result.success and lenient_result.success

        strict_report = strict_result.data["compliance_report"]
        lenient_report = lenient_result.data["compliance_report"]

        # Strict policy should be more restrictive
        assert strict_report.overall_compliance_score <= lenient_report.overall_compliance_score
