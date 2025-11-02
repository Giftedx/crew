"""Tests for Rights and Reuse Intelligence Service."""

from __future__ import annotations

from features.rights_management.rights_reuse_intelligence_service import (
    ContentFragment,
    LicenseInfo,
    ReuseAnalysis,
    RightsReuseIntelligenceService,
    get_rights_reuse_intelligence_service,
)


class TestRightsReuseIntelligenceService:
    """Test rights and reuse intelligence service functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.service = RightsReuseIntelligenceService(cache_size=100)

    def test_initialization(self) -> None:
        """Test service initialization."""
        assert self.service.cache_size == 100
        assert len(self.service._analysis_cache) == 0
        assert len(self.service._license_patterns) == 3
        assert len(self.service._risk_factors) == 5

    def test_analyze_content_rights_basic(self) -> None:
        """Test basic content rights analysis."""
        content_segments = [
            {
                "start_time": 0.0,
                "end_time": 30.0,
                "description": "Educational content about technology",
                "source_url": "https://youtube.com/watch?v=test",
            }
        ]

        result = self.service.analyze_content_rights(
            content_segments,
            content_type="video",
            intended_use="educational",
            use_cache=False,
        )

        assert result.success
        assert result.data is not None
        assert "content_fragments" in result.data
        assert "reuse_analysis" in result.data
        assert "risk_assessment" in result.data

    def test_analyze_content_rights_empty_segments(self) -> None:
        """Test handling of empty content segments."""
        result = self.service.analyze_content_rights([], content_type="video", intended_use="educational")

        assert not result.success
        assert result.status == "bad_request"
        assert "cannot be empty" in result.error.lower()

    def test_assess_fair_use_risk(self) -> None:
        """Test fair use risk assessment."""
        result = self.service.assess_fair_use_risk(
            content_description="Educational commentary on news event",
            intended_use="educational",
            content_type="video",
            audience_size="medium",
        )

        assert result.success
        assert result.data is not None
        assert "fair_use_score" in result.data
        assert "risk_level" in result.data
        assert "factors" in result.data

        # Educational use should have lower risk
        assert result.data["risk_level"] in ["low", "medium"]

    def test_suggest_alternative_content(self) -> None:
        """Test alternative content suggestions."""
        original_content = {
            "content_type": "video",
            "description": "Commercial video content",
        }

        alternatives = self.service.suggest_alternative_content(original_content)

        assert isinstance(alternatives, list)
        assert len(alternatives) > 0
        assert all(isinstance(alt, str) for alt in alternatives)

    def test_clear_cache(self) -> None:
        """Test cache clearing."""
        # Add some cached analyses
        self.service.analyze_content_rights([{"description": "test"}], use_cache=True)

        assert len(self.service._analysis_cache) > 0

        # Clear cache
        result = self.service.clear_cache()

        assert result.success
        assert result.data["cleared_entries"] > 0
        assert len(self.service._analysis_cache) == 0

    def test_get_cache_stats(self) -> None:
        """Test cache statistics."""
        # Add some cached analyses
        self.service.analyze_content_rights([{"description": "test"}], use_cache=True)

        result = self.service.get_cache_stats()

        assert result.success
        assert result.data is not None
        assert "total_cached" in result.data
        assert "cache_size_limit" in result.data

        assert result.data["total_cached"] >= 1
        assert result.data["cache_size_limit"] == 100

    def test_model_selection(self) -> None:
        """Test model selection logic."""
        assert self.service._select_model("fast") == "fast_analysis"
        assert self.service._select_model("balanced") == "balanced_analysis"
        assert self.service._select_model("quality") == "quality_analysis"
        assert self.service._select_model("unknown") == "balanced_analysis"  # Default

    def test_license_info_extraction(self) -> None:
        """Test license information extraction."""
        # Test Creative Commons detection
        segment_cc = {
            "description": "Content licensed under CC BY-SA",
            "source_url": "https://creativecommons.org/licenses/by-sa/4.0/",
        }

        license_info = self.service._extract_license_info(segment_cc)
        assert license_info.license_type == "creative_commons"
        assert license_info.attribution_required is True

        # Test copyrighted detection
        segment_copyright = {
            "description": "All rights reserved content",
            "source_url": "https://example.com/video",
        }

        license_info2 = self.service._extract_license_info(segment_copyright)
        assert license_info2.license_type == "copyrighted"
        assert license_info2.commercial_use_allowed is False

    def test_risk_score_calculation(self) -> None:
        """Test risk score calculation."""
        segment = {
            "description": "Recent controversial content",
            "source_url": "https://youtube.com/watch?v=test",
        }

        risk_score = self.service._calculate_risk_score(segment, "commercial", "large")

        assert 0 <= risk_score <= 1
        # Commercial use + large audience + recent content should be higher risk
        assert risk_score > 0.5


class TestRightsReuseIntelligenceServiceSingleton:
    """Test singleton instance management."""

    def test_get_rights_reuse_intelligence_service(self) -> None:
        """Test getting singleton instance."""
        service1 = get_rights_reuse_intelligence_service()
        service2 = get_rights_reuse_intelligence_service()

        # Should return same instance
        assert service1 is service2
        assert isinstance(service1, RightsReuseIntelligenceService)


class TestLicenseInfo:
    """Test license info data structure."""

    def test_create_license_info(self) -> None:
        """Test creating license info."""
        license_info = LicenseInfo(
            license_type="creative_commons",
            rights_holder="Content Creator",
            usage_rights=["reuse", "modify", "redistribute"],
            restrictions=["attribution_required"],
            attribution_required=True,
            commercial_use_allowed=True,
        )

        assert license_info.license_type == "creative_commons"
        assert license_info.rights_holder == "Content Creator"
        assert len(license_info.usage_rights) == 3
        assert license_info.attribution_required is True
        assert license_info.commercial_use_allowed is True

    def test_license_info_defaults(self) -> None:
        """Test license info with default values."""
        license_info = LicenseInfo(
            license_type="unknown",
            rights_holder="Unknown",
            usage_rights=[],
            restrictions=[],
        )

        assert license_info.license_type == "unknown"
        assert license_info.attribution_required is False  # Default
        assert license_info.commercial_use_allowed is False  # Default


class TestContentFragment:
    """Test content fragment data structure."""

    def test_create_content_fragment(self) -> None:
        """Test creating content fragment."""
        license_info = LicenseInfo(
            license_type="fair_use",
            rights_holder="News Organization",
            usage_rights=["commentary"],
            restrictions=["limited_portions"],
            attribution_required=True,
            commercial_use_allowed=False,
        )

        fragment = ContentFragment(
            fragment_id="fragment_1",
            start_time=0.0,
            end_time=30.0,
            duration=30.0,
            content_type="video",
            source_url="https://youtube.com/watch?v=test",
            license_info=license_info,
            risk_score=0.6,
            alternative_suggestions=["Use stock footage", "Create custom content"],
        )

        assert fragment.fragment_id == "fragment_1"
        assert fragment.start_time == 0.0
        assert fragment.end_time == 30.0
        assert fragment.duration == 30.0
        assert fragment.content_type == "video"
        assert fragment.license_info.license_type == "fair_use"
        assert fragment.risk_score == 0.6
        assert len(fragment.alternative_suggestions) == 2

    def test_content_fragment_defaults(self) -> None:
        """Test content fragment with default values."""
        license_info = LicenseInfo(
            license_type="unknown",
            rights_holder="Unknown",
            usage_rights=[],
            restrictions=[],
        )

        fragment = ContentFragment(
            fragment_id="fragment_1",
            start_time=0.0,
            end_time=30.0,
            duration=30.0,
            content_type="video",
            source_url="https://example.com",
            license_info=license_info,
            risk_score=0.5,
        )

        assert fragment.alternative_suggestions == []  # Default


class TestReuseAnalysis:
    """Test reuse analysis data structure."""

    def test_create_reuse_analysis(self) -> None:
        """Test creating reuse analysis."""
        analysis = ReuseAnalysis(
            can_reuse=True,
            risk_level="low",
            required_actions=["Provide attribution"],
            alternative_content=["Stock footage", "Public domain content"],
            estimated_cost=100.0,
            compliance_score=0.9,
        )

        assert analysis.can_reuse is True
        assert analysis.risk_level == "low"
        assert len(analysis.required_actions) == 1
        assert len(analysis.alternative_content) == 2
        assert analysis.estimated_cost == 100.0
        assert analysis.compliance_score == 0.9

    def test_reuse_analysis_cannot_reuse(self) -> None:
        """Test reuse analysis when content cannot be reused."""
        analysis = ReuseAnalysis(
            can_reuse=False,
            risk_level="high",
            required_actions=["Obtain permission", "Remove content"],
            alternative_content=["Create original content"],
            estimated_cost=500.0,
            compliance_score=0.2,
        )

        assert analysis.can_reuse is False
        assert analysis.risk_level == "high"
        assert len(analysis.required_actions) == 2
        assert analysis.compliance_score < 0.5


class TestRightsReuseIntelligenceIntegration:
    """Test rights management service integration scenarios."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.service = RightsReuseIntelligenceService()

    def test_comprehensive_rights_analysis(self) -> None:
        """Test comprehensive rights analysis with multiple segments."""
        content_segments = [
            {
                "start_time": 0.0,
                "end_time": 30.0,
                "description": "Educational content with Creative Commons license",
                "source_url": "https://creativecommons.org/licenses/by/4.0/",
            },
            {
                "start_time": 30.0,
                "end_time": 60.0,
                "description": "Recent copyrighted news footage",
                "source_url": "https://news.example.com/video",
            },
        ]

        result = self.service.analyze_content_rights(
            content_segments,
            content_type="video",
            intended_use="educational",
            target_audience_size="medium",
        )

        assert result.success
        content_fragments = result.data["content_fragments"]

        # Should have 2 fragments
        assert len(content_fragments) == 2

        # First should be Creative Commons (low risk)
        assert content_fragments[0]["license_info"]["license_type"] == "creative_commons"

        # Second should be copyrighted (higher risk)
        assert content_fragments[1]["license_info"]["license_type"] == "copyrighted"

    def test_fair_use_assessment_factors(self) -> None:
        """Test fair use assessment with different factors."""
        # Educational use of factual content for small audience
        result_educational = self.service.assess_fair_use_risk(
            content_description="Brief clip for educational commentary",
            intended_use="educational",
            content_type="news",
            audience_size="small",
        )

        # Commercial use of creative content for large audience
        result_commercial = self.service.assess_fair_use_risk(
            content_description="Full song for commercial promotion",
            intended_use="commercial",
            content_type="music",
            audience_size="large",
        )

        assert result_educational.success and result_commercial.success

        # Educational should have lower risk
        educational_score = result_educational.data["fair_use_score"]
        commercial_score = result_commercial.data["fair_use_score"]

        assert educational_score >= commercial_score

    def test_alternative_content_suggestions(self) -> None:
        """Test alternative content suggestions for different types."""
        # Video content
        video_content = {"content_type": "video", "description": "News footage"}
        video_alternatives = self.service.suggest_alternative_content(video_content)

        assert len(video_alternatives) > 0
        assert any("stock footage" in alt.lower() for alt in video_alternatives)

        # Image content
        image_content = {"content_type": "image", "description": "Photo"}
        image_alternatives = self.service.suggest_alternative_content(image_content)

        assert len(image_alternatives) > 0
        assert any("stock images" in alt.lower() for alt in image_alternatives)

        # Audio content
        audio_content = {"content_type": "audio", "description": "Music"}
        audio_alternatives = self.service.suggest_alternative_content(audio_content)

        assert len(audio_alternatives) > 0
        assert any("public domain" in alt.lower() for alt in audio_alternatives)
