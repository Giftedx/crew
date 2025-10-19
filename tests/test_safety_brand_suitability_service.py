"""Tests for Safety and Brand Suitability Analysis Service."""

from __future__ import annotations

from analysis.safety.safety_brand_suitability_service import (
    BrandSuitability,
    PolicyCompliance,
    SafetyBrandSuitabilityService,
    SafetyClassification,
    get_safety_brand_suitability_service,
)


class TestSafetyBrandSuitabilityService:
    """Test safety and brand suitability analysis service functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.service = SafetyBrandSuitabilityService(cache_size=100)

    def test_initialization(self) -> None:
        """Test service initialization."""
        assert self.service.cache_size == 100
        assert len(self.service._analysis_cache) == 0
        assert self.service._safety_classifier is None
        assert len(self.service._policy_categories) == 8

    def test_analyze_fallback(self) -> None:
        """Test analysis with fallback rule-based method."""
        content = "This is safe, professional content that should be brand-friendly."

        result = self.service.analyze_content(content, model="fast", use_cache=False)

        # Should succeed with rule-based analysis
        assert result.success
        assert result.data is not None
        assert "safety" in result.data
        assert "brand_suitability" in result.data
        assert "policy_compliance" in result.data

    def test_analyze_empty_content(self) -> None:
        """Test handling of empty content."""
        result = self.service.analyze_content("", model="fast")

        assert not result.success
        assert result.status == "bad_request"
        assert "empty" in result.error.lower()

    def test_analyze_short_content(self) -> None:
        """Test handling of very short content."""
        result = self.service.analyze_content("Hi", model="fast")

        assert result.success  # Should work with fallback

    def test_analysis_cache_hit(self) -> None:
        """Test analysis cache functionality."""
        content = "This is a test content for caching purposes."

        # First analysis - cache miss
        result1 = self.service.analyze_content(content, model="fast", use_cache=True)
        assert result1.success
        assert result1.data["cache_hit"] is False

        # Second analysis - should be cache hit
        result2 = self.service.analyze_content(content, model="fast", use_cache=True)
        assert result2.success
        assert result2.data["cache_hit"] is True

    def test_clear_cache(self) -> None:
        """Test cache clearing."""
        # Add some cached analyses
        self.service.analyze_content("Content 1", use_cache=True)
        self.service.analyze_content("Content 2", use_cache=True)

        assert len(self.service._analysis_cache) > 0

        # Clear cache
        result = self.service.clear_cache()

        assert result.success
        assert result.data["cleared_entries"] > 0
        assert len(self.service._analysis_cache) == 0

    def test_get_cache_stats(self) -> None:
        """Test cache statistics."""
        # Add some cached analyses
        self.service.analyze_content("Content 1", model="fast", use_cache=True)
        self.service.analyze_content("Content 2", model="balanced", use_cache=True)

        result = self.service.get_cache_stats()

        assert result.success
        assert result.data is not None
        assert "total_cached" in result.data
        assert "cache_size_limit" in result.data
        assert "models_cached" in result.data

        assert result.data["total_cached"] >= 2
        assert result.data["cache_size_limit"] == 100

    def test_model_selection(self) -> None:
        """Test model selection logic."""
        assert self.service._select_model("fast") == "fast_analysis"
        assert self.service._select_model("balanced") == "balanced_analysis"
        assert self.service._select_model("quality") == "quality_analysis"
        assert self.service._select_model("unknown") == "balanced_analysis"  # Default

    def test_analyze_segments(self) -> None:
        """Test analysis of multiple segments."""
        segments = [
            {"text": "This is safe content.", "speaker": "Host"},
            {"text": "This content contains profanity.", "speaker": "Guest"},
        ]

        result = self.service.analyze_segments(segments, model="fast", use_cache=False)

        assert result.success
        assert result.data is not None
        assert "results" in result.data
        assert result.data["total_segments"] == 2
        assert len(result.data["results"]) >= 1  # Some segments might be too short

    def test_safety_analysis_rules(self) -> None:
        """Test rule-based safety analysis."""
        # Test safe content
        safe_result = self.service._analyze_safety_rules("This is safe, professional content.")
        assert safe_result.safety_level == "safe"
        assert safe_result.compliance_score > 0.8

        # Test unsafe content
        unsafe_result = self.service._analyze_safety_rules("This content contains hate speech and violence.")
        assert unsafe_result.safety_level == "unsafe"
        assert len(unsafe_result.risk_factors) > 0

    def test_brand_suitability_analysis(self) -> None:
        """Test brand suitability analysis."""
        # Test brand-friendly content
        brand_friendly = self.service._analyze_brand_suitability("This is professional, educational content.", None)
        assert brand_friendly.brand_alignment in ["excellent", "good"]
        assert brand_friendly.suitability_score > 0.6

        # Test brand-risky content
        brand_risky = self.service._analyze_brand_suitability("This is controversial political content.", None)
        assert brand_risky.brand_alignment in ["poor", "fair"]
        assert brand_risky.suitability_score < 0.6

    def test_policy_compliance_analysis(self) -> None:
        """Test policy compliance analysis."""
        # Test compliant content
        compliant_result = self.service._analyze_policy_compliance("This is safe, professional content.")
        assert compliant_result.compliance_score > 0.8
        assert len(compliant_result.violated_policies) == 0

        # Test non-compliant content
        non_compliant_result = self.service._analyze_policy_compliance(
            "This content contains hate speech and violence."
        )
        assert non_compliant_result.compliance_score < 0.8
        assert len(non_compliant_result.violated_policies) > 0


class TestSafetyBrandSuitabilityServiceSingleton:
    """Test singleton instance management."""

    def test_get_safety_brand_suitability_service(self) -> None:
        """Test getting singleton instance."""
        service1 = get_safety_brand_suitability_service()
        service2 = get_safety_brand_suitability_service()

        # Should return same instance
        assert service1 is service2
        assert isinstance(service1, SafetyBrandSuitabilityService)


class TestSafetyClassification:
    """Test safety classification data structure."""

    def test_create_safety_classification(self) -> None:
        """Test creating safety classification."""
        safety = SafetyClassification(
            safety_level="safe",
            confidence=0.95,
            risk_factors=[],
            compliance_score=0.9,
        )

        assert safety.safety_level == "safe"
        assert safety.confidence == 0.95
        assert safety.risk_factors == []
        assert safety.compliance_score == 0.9

    def test_safety_classification_with_risks(self) -> None:
        """Test safety classification with risk factors."""
        safety = SafetyClassification(
            safety_level="sensitive",
            confidence=0.7,
            risk_factors=["profanity", "adult_content"],
            compliance_score=0.6,
        )

        assert safety.safety_level == "sensitive"
        assert len(safety.risk_factors) == 2
        assert "profanity" in safety.risk_factors


class TestBrandSuitability:
    """Test brand suitability data structure."""

    def test_create_brand_suitability(self) -> None:
        """Test creating brand suitability."""
        brand = BrandSuitability(
            suitability_score=0.8,
            brand_alignment="good",
            target_audience="professional",
            content_warnings=["Contains business topics"],
            sponsorship_readiness=True,
        )

        assert brand.suitability_score == 0.8
        assert brand.brand_alignment == "good"
        assert brand.target_audience == "professional"
        assert len(brand.content_warnings) == 1
        assert brand.sponsorship_readiness is True

    def test_brand_suitability_defaults(self) -> None:
        """Test brand suitability with default values."""
        brand = BrandSuitability(
            suitability_score=0.5,
            brand_alignment="fair",
            target_audience="general",
        )

        assert brand.suitability_score == 0.5
        assert brand.brand_alignment == "fair"
        assert brand.target_audience == "general"
        assert brand.content_warnings == []
        assert brand.sponsorship_readiness is False  # Default


class TestPolicyCompliance:
    """Test policy compliance data structure."""

    def test_create_policy_compliance(self) -> None:
        """Test creating policy compliance."""
        compliance = PolicyCompliance(
            compliance_score=0.85,
            violated_policies=["profanity"],
            compliance_flags=["Contains inappropriate language"],
            recommendations=["Review content for language", "Consider content warning"],
        )

        assert compliance.compliance_score == 0.85
        assert len(compliance.violated_policies) == 1
        assert "profanity" in compliance.violated_policies
        assert len(compliance.recommendations) == 2

    def test_policy_compliance_perfect(self) -> None:
        """Test policy compliance with perfect score."""
        compliance = PolicyCompliance(
            compliance_score=1.0,
            violated_policies=[],
            compliance_flags=[],
            recommendations=[],
        )

        assert compliance.compliance_score == 1.0
        assert len(compliance.violated_policies) == 0
        assert len(compliance.recommendations) == 0


class TestSafetyBrandSuitabilityWithMocking:
    """Test safety analysis service with mocked dependencies."""

    def test_analyze_with_speaker_context(self) -> None:
        """Test analysis with speaker context."""
        content = "This is safe content."
        speaker = "Host"

        result = self.service.analyze_content(content, speaker=speaker, model="fast", use_cache=False)

        assert result.success

        # Should preserve speaker context
        assert result.data["speaker"] == "Host"
        assert result.data["content_segment"] == content

    def test_analyze_with_timestamp(self) -> None:
        """Test analysis with timestamp context."""
        content = "Safe content here."
        timestamp = 45.0

        result = self.service.analyze_content(content, timestamp=timestamp, model="fast", use_cache=False)

        assert result.success
        assert result.data["timestamp"] == 45.0

    def test_analyze_segments_with_brand_guidelines(self) -> None:
        """Test analysis of segments with brand guidelines."""
        brand_guidelines = {
            "target_audience": "family",
            "allowed_topics": ["education", "entertainment"],
            "prohibited_topics": ["politics", "adult_content"],
        }

        segments = [
            {"text": "This is educational content.", "speaker": "Host"},
            {"text": "This discusses politics.", "speaker": "Guest"},
        ]

        result = self.service.analyze_segments(segments, brand_guidelines, model="fast", use_cache=False)

        assert result.success
        assert result.data["total_segments"] == 2

        # Should have different suitability scores for different content
        results = result.data["results"]
        if len(results) >= 2:
            # Educational content should be more suitable for family audience
            educational_score = results[0]["brand_suitability"]["suitability_score"]
            political_score = results[1]["brand_suitability"]["suitability_score"]

            # Educational should be more suitable than political for family audience
            assert educational_score >= political_score
