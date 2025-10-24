"""Sponsor and Compliance Assistant for Creator Intelligence.

This module provides automated sponsor compliance checking and safe cut list generation
for creator content, ensuring brand safety and policy compliance.

Features:
- Brand suitability scoring for sponsorship compatibility
- Automated cut list generation for sponsor-safe content
- Policy pack compliance checking
- Sponsor script generation with brand guidelines
- Integration with safety analysis and content moderation

Dependencies:
- Safety analysis service for compliance checking
- Content segmentation for cut list creation
- Brand guidelines configuration system
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from ultimate_discord_intelligence_bot.step_result import StepResult


logger = logging.getLogger(__name__)


@dataclass
class BrandGuidelines:
    """Brand-specific guidelines for content compliance."""

    brand_name: str
    target_audience: str  # family, adult, professional, general
    allowed_topics: list[str]
    prohibited_topics: list[str]
    tone_requirements: list[str]  # professional, casual, educational, entertaining
    content_warnings: list[str]  # Required warnings for certain content
    sponsorship_format: str  # integrated, separate_segment, end_screen
    max_segment_duration: int = 300  # seconds


@dataclass
class ComplianceSegment:
    """A content segment with compliance analysis."""

    start_time: float
    end_time: float
    duration: float
    content_type: str  # discussion, sponsor_read, transition, etc.
    safety_level: str  # safe, sensitive, unsafe
    compliance_score: float  # 0.0 to 1.0
    brand_suitability: float  # 0.0 to 1.0
    risk_factors: list[str]
    recommendations: list[str]
    transcript_text: str | None = None


@dataclass
class SponsorCutList:
    """A sponsor-safe cut list for content editing."""

    total_duration: float
    safe_segments: list[ComplianceSegment]
    unsafe_segments: list[ComplianceSegment]
    transitions: list[dict[str, Any]]
    sponsor_placements: list[dict[str, Any]]
    compliance_summary: dict[str, Any]


@dataclass
class SponsorScript:
    """A sponsor-safe script with compliance annotations."""

    script_segments: list[dict[str, Any]]
    brand_guidelines_applied: list[str]
    compliance_annotations: list[dict[str, Any]]
    total_script_duration: float
    sponsor_integration_points: list[dict[str, Any]]


@dataclass
class ComplianceReport:
    """Compliance analysis report for content."""

    overall_compliance_score: float
    brand_suitability_score: float
    policy_violations: list[str]
    content_warnings: list[str]
    recommendations: list[str]
    safe_content_percentage: float
    audit_trail: list[dict[str, Any]]


class SponsorComplianceAssistant:
    """Service for sponsor compliance checking and safe content generation.

    Usage:
        assistant = SponsorComplianceAssistant()
        result = assistant.generate_compliant_cut_list(content_segments, brand_guidelines)
        cut_list = result.data["cut_list"]
    """

    def __init__(self, cache_size: int = 1000):
        """Initialize sponsor compliance assistant.

        Args:
            cache_size: Maximum number of cached results
        """
        self.cache_size = cache_size
        self._compliance_cache: dict[str, ComplianceReport] = {}

        # Load default policy packs
        self._default_policies = self._load_default_policies()

    def _load_default_policies(self) -> dict[str, Any]:
        """Load default policy packs for compliance checking."""
        return {
            "family_friendly": {
                "prohibited_topics": [
                    "violence",
                    "adult_content",
                    "profanity",
                    "drugs",
                    "alcohol",
                ],
                "required_warnings": ["mild_language", "intense_discussion"],
                "min_compliance_score": 0.9,
            },
            "professional": {
                "prohibited_topics": [
                    "controversial_politics",
                    "profanity",
                    "adult_content",
                ],
                "required_warnings": ["business_content", "technical_discussion"],
                "min_compliance_score": 0.85,
            },
            "general_audience": {
                "prohibited_topics": ["extreme_violence", "explicit_content"],
                "required_warnings": ["mild_violence", "language"],
                "min_compliance_score": 0.8,
            },
        }

    def analyze_compliance(
        self,
        content_segments: list[dict[str, Any]],
        brand_guidelines: BrandGuidelines | None = None,
        policy_pack: str = "general_audience",
        use_cache: bool = True,
    ) -> StepResult:
        """Analyze content segments for compliance and brand suitability.

        Args:
            content_segments: List of content segments with timing and text
            brand_guidelines: Brand-specific guidelines (optional)
            policy_pack: Policy pack to apply (family_friendly, professional, general_audience)
            use_cache: Whether to use compliance cache

        Returns:
            StepResult with compliance analysis
        """
        try:
            import time

            start_time = time.time()

            # Validate inputs
            if not content_segments:
                return StepResult.fail("Content segments cannot be empty", status="bad_request")

            # Check cache first
            if use_cache:
                cache_result = self._check_cache(content_segments, brand_guidelines, policy_pack)
                if cache_result:
                    logger.info("Compliance analysis cache hit")
                    return StepResult.ok(
                        data={
                            "compliance_report": cache_result.__dict__,
                            "cache_hit": True,
                            "processing_time_ms": (time.time() - start_time) * 1000,
                        }
                    )

            # Perform compliance analysis
            compliance_result = self._analyze_compliance(content_segments, brand_guidelines, policy_pack)

            if compliance_result:
                # Cache result
                if use_cache:
                    self._cache_result(
                        content_segments,
                        brand_guidelines,
                        policy_pack,
                        compliance_result,
                    )

                processing_time = (time.time() - start_time) * 1000

                return StepResult.ok(
                    data={
                        "compliance_report": compliance_result.__dict__,
                        "cache_hit": False,
                        "processing_time_ms": processing_time,
                    }
                )
            else:
                return StepResult.fail("Compliance analysis failed", status="retryable")

        except Exception as e:
            logger.error(f"Compliance analysis failed: {e}")
            return StepResult.fail(f"Compliance analysis failed: {e!s}", status="retryable")

    def generate_compliant_cut_list(
        self,
        content_segments: list[dict[str, Any]],
        brand_guidelines: BrandGuidelines,
        max_video_duration: float = 3600.0,  # 1 hour max
        use_cache: bool = True,
    ) -> StepResult:
        """Generate a sponsor-safe cut list for content editing.

        Args:
            content_segments: List of content segments
            brand_guidelines: Brand-specific guidelines
            max_video_duration: Maximum allowed video duration
            use_cache: Whether to use cut list cache

        Returns:
            StepResult with compliant cut list
        """
        try:
            # First, analyze compliance
            compliance_result = self.analyze_compliance(content_segments, brand_guidelines, use_cache=use_cache)

            if not compliance_result.success:
                return StepResult.fail(f"Compliance analysis failed: {compliance_result.error}")

            compliance_report = compliance_result.data["compliance_report"]

            # Generate cut list based on compliance analysis
            cut_list = self._generate_cut_list(
                content_segments,
                compliance_report,
                brand_guidelines,
                max_video_duration,
            )

            return StepResult.ok(
                data={
                    "cut_list": cut_list.__dict__,
                    "compliance_report": compliance_report.__dict__,
                }
            )

        except Exception as e:
            logger.error(f"Cut list generation failed: {e}")
            return StepResult.fail(f"Cut list generation failed: {e!s}")

    def generate_sponsor_script(
        self,
        content_segments: list[dict[str, Any]],
        brand_guidelines: BrandGuidelines,
        sponsor_product: str,
        sponsor_message: str,
        use_cache: bool = True,
    ) -> StepResult:
        """Generate a sponsor-safe script with brand integration.

        Args:
            content_segments: List of content segments
            brand_guidelines: Brand-specific guidelines
            sponsor_product: Product/service to promote
            sponsor_message: Key sponsor message
            use_cache: Whether to use script cache

        Returns:
            StepResult with sponsor script
        """
        try:
            # Analyze compliance first
            compliance_result = self.analyze_compliance(content_segments, brand_guidelines, use_cache=use_cache)

            if not compliance_result.success:
                return StepResult.fail(f"Compliance analysis failed: {compliance_result.error}")

            # Generate sponsor script
            sponsor_script = self._generate_sponsor_script(
                content_segments,
                compliance_result.data["compliance_report"],
                brand_guidelines,
                sponsor_product,
                sponsor_message,
            )

            return StepResult.ok(data={"sponsor_script": sponsor_script.__dict__})

        except Exception as e:
            logger.error(f"Sponsor script generation failed: {e}")
            return StepResult.fail(f"Sponsor script generation failed: {e!s}")

    def _analyze_compliance(
        self,
        content_segments: list[dict[str, Any]],
        brand_guidelines: BrandGuidelines | None,
        policy_pack: str,
    ) -> ComplianceReport | None:
        """Analyze content segments for compliance.

        Args:
            content_segments: Content segments to analyze
            brand_guidelines: Brand-specific guidelines
            policy_pack: Policy pack to apply

        Returns:
            ComplianceReport with analysis results
        """
        try:
            from analysis.safety.safety_brand_suitability_service import (
                get_safety_brand_suitability_service,
            )

            safety_service = get_safety_brand_suitability_service()

            # Get policy pack configuration
            policy_config = self._default_policies.get(policy_pack, self._default_policies["general_audience"])

            # Analyze each segment
            segment_analyses = []
            total_safe_duration = 0.0
            total_duration = 0.0

            for segment in content_segments:
                segment_duration = segment.get("end_time", 0) - segment.get("start_time", 0)
                total_duration += segment_duration

                # Use safety service for compliance analysis
                safety_result = safety_service.analyze_content(
                    content=segment.get("text", ""),
                    model="balanced",
                    use_cache=False,  # Don't cache individual segments
                )

                if safety_result.success:
                    safety_data = safety_result.data
                    compliance_score = safety_data["safety"]["compliance_score"]

                    # Check against policy requirements
                    is_compliant = compliance_score >= policy_config["min_compliance_score"]

                    if is_compliant:
                        total_safe_duration += segment_duration

                    # Generate recommendations
                    recommendations = self._generate_compliance_recommendations(
                        safety_data, policy_config, brand_guidelines
                    )

                    segment_analyses.append(
                        {
                            "segment": segment,
                            "compliance_score": compliance_score,
                            "is_compliant": is_compliant,
                            "recommendations": recommendations,
                        }
                    )

            # Calculate overall metrics
            safe_content_percentage = (total_safe_duration / total_duration) if total_duration > 0 else 0.0

            # Identify violations
            policy_violations = []
            for analysis in segment_analyses:
                if not analysis["is_compliant"]:
                    policy_violations.append(f"Non-compliant segment at {analysis['segment'].get('start_time', 0)}s")

            # Generate overall recommendations
            recommendations = self._generate_overall_recommendations(
                segment_analyses, safe_content_percentage, policy_config
            )

            # Calculate overall compliance score
            compliant_segments = sum(1 for a in segment_analyses if a["is_compliant"])
            overall_compliance = compliant_segments / len(segment_analyses) if segment_analyses else 0.0

            return ComplianceReport(
                overall_compliance_score=overall_compliance,
                brand_suitability_score=safe_content_percentage,
                policy_violations=policy_violations,
                content_warnings=policy_config["required_warnings"],
                recommendations=recommendations,
                safe_content_percentage=safe_content_percentage,
                audit_trail=segment_analyses,
            )

        except Exception as e:
            logger.error(f"Compliance analysis failed: {e}")
            return None

    def _generate_cut_list(
        self,
        content_segments: list[dict[str, Any]],
        compliance_report: ComplianceReport,
        brand_guidelines: BrandGuidelines,
        max_duration: float,
    ) -> SponsorCutList:
        """Generate a sponsor-safe cut list.

        Args:
            content_segments: Original content segments
            compliance_report: Compliance analysis results
            brand_guidelines: Brand guidelines
            max_duration: Maximum allowed duration

        Returns:
            SponsorCutList with safe segments and transitions
        """
        safe_segments = []
        unsafe_segments = []
        transitions = []
        sponsor_placements = []

        current_time = 0.0
        accumulated_duration = 0.0

        for i, segment in enumerate(content_segments):
            segment_duration = segment.get("end_time", 0) - segment.get("start_time", 0)

            # Find compliance analysis for this segment
            segment_analysis = None
            for analysis in compliance_report.audit_trail:
                if analysis["segment"]["start_time"] == segment["start_time"]:
                    segment_analysis = analysis
                    break

            if segment_analysis and segment_analysis["is_compliant"]:
                # Safe segment - include in cut list
                safe_segment = ComplianceSegment(
                    start_time=current_time,
                    end_time=current_time + segment_duration,
                    duration=segment_duration,
                    content_type="discussion",
                    safety_level="safe",
                    compliance_score=segment_analysis["compliance_score"],
                    brand_suitability=1.0,  # Safe segments are brand-suitable
                    risk_factors=[],
                    recommendations=segment_analysis["recommendations"],
                    transcript_text=segment.get("text"),
                )
                safe_segments.append(safe_segment)

                accumulated_duration += segment_duration
                current_time += segment_duration

                # Add sponsor placement opportunities
                if accumulated_duration > 300 and len(sponsor_placements) < 3:  # Every 5 minutes
                    sponsor_placements.append(
                        {
                            "position": current_time,
                            "type": brand_guidelines.sponsorship_format,
                            "duration": 30,  # 30-second sponsor segment
                        }
                    )
            else:
                # Unsafe segment - mark for removal or warning
                unsafe_segment = ComplianceSegment(
                    start_time=segment.get("start_time", 0),
                    end_time=segment.get("end_time", 0),
                    duration=segment_duration,
                    content_type="unsafe",
                    safety_level="unsafe",
                    compliance_score=segment_analysis["compliance_score"] if segment_analysis else 0.0,
                    brand_suitability=0.0,
                    risk_factors=["policy_violation"],
                    recommendations=["Remove or edit this segment"],
                    transcript_text=segment.get("text"),
                )
                unsafe_segments.append(unsafe_segment)

        # Add transitions between safe segments
        for i in range(len(safe_segments) - 1):
            transitions.append(
                {
                    "from_segment": i,
                    "to_segment": i + 1,
                    "transition_type": "fade",
                    "duration": 1.0,
                }
            )

        return SponsorCutList(
            total_duration=accumulated_duration,
            safe_segments=safe_segments,
            unsafe_segments=unsafe_segments,
            transitions=transitions,
            sponsor_placements=sponsor_placements,
            compliance_summary={
                "overall_compliance": compliance_report.overall_compliance_score,
                "safe_percentage": compliance_report.safe_content_percentage,
                "violations": len(compliance_report.policy_violations),
            },
        )

    def _generate_sponsor_script(
        self,
        content_segments: list[dict[str, Any]],
        compliance_report: ComplianceReport,
        brand_guidelines: BrandGuidelines,
        sponsor_product: str,
        sponsor_message: str,
    ) -> SponsorScript:
        """Generate a sponsor-safe script with brand integration.

        Args:
            content_segments: Content segments
            compliance_report: Compliance analysis
            brand_guidelines: Brand guidelines
            sponsor_product: Product to promote
            sponsor_message: Sponsor message

        Returns:
            SponsorScript with integrated sponsorship
        """
        script_segments = []
        compliance_annotations = []
        sponsor_integration_points = []

        # Generate script segments from safe content
        for i, segment in enumerate(content_segments):
            # Find compliance analysis for this segment
            segment_analysis = None
            for analysis in compliance_report.audit_trail:
                if analysis["segment"]["start_time"] == segment["start_time"]:
                    segment_analysis = analysis
                    break

            if segment_analysis and segment_analysis["is_compliant"]:
                script_segment = {
                    "segment_index": i,
                    "start_time": segment["start_time"],
                    "end_time": segment["end_time"],
                    "content": segment.get("text", ""),
                    "speaker": segment.get("speaker", "Host"),
                    "segment_type": "content",
                }
                script_segments.append(script_segment)

                # Add compliance annotation
                compliance_annotations.append(
                    {
                        "segment_index": i,
                        "compliance_score": segment_analysis["compliance_score"],
                        "recommendations": segment_analysis["recommendations"],
                    }
                )

        # Add sponsor integration points
        if brand_guidelines.sponsorship_format == "integrated":
            # Insert sponsor mentions throughout content
            sponsor_points = self._calculate_sponsor_integration_points(script_segments, brand_guidelines)
            sponsor_integration_points.extend(sponsor_points)

        elif brand_guidelines.sponsorship_format == "separate_segment":
            # Add dedicated sponsor segments
            sponsor_segment = {
                "segment_index": len(script_segments),
                "start_time": 0,  # Will be calculated during editing
                "end_time": 0,
                "content": self._generate_sponsor_content(sponsor_product, sponsor_message, brand_guidelines),
                "speaker": "Host",
                "segment_type": "sponsor",
            }
            script_segments.append(sponsor_segment)

        return SponsorScript(
            script_segments=script_segments,
            brand_guidelines_applied=[
                f"target_audience: {brand_guidelines.target_audience}",
                f"tone: {', '.join(brand_guidelines.tone_requirements)}",
                f"format: {brand_guidelines.sponsorship_format}",
            ],
            compliance_annotations=compliance_annotations,
            total_script_duration=sum(s["end_time"] - s["start_time"] for s in script_segments),
            sponsor_integration_points=sponsor_integration_points,
        )

    def _generate_compliance_recommendations(
        self,
        safety_data: dict[str, Any],
        policy_config: dict[str, Any],
        brand_guidelines: BrandGuidelines | None,
    ) -> list[str]:
        """Generate compliance recommendations for a segment.

        Args:
            safety_data: Safety analysis data
            policy_config: Policy configuration
            brand_guidelines: Brand guidelines

        Returns:
            List of recommendations
        """
        recommendations = []

        safety_level = safety_data.get("safety", {}).get("safety_level", "unknown")
        compliance_score = safety_data.get("safety", {}).get("compliance_score", 0.0)

        if safety_level == "unsafe":
            recommendations.append("Remove this segment - violates safety policies")
        elif safety_level == "sensitive":
            recommendations.append("Add content warning for sensitive topics")
        elif compliance_score < policy_config["min_compliance_score"]:
            recommendations.append("Edit content to improve compliance score")

        # Brand-specific recommendations
        if brand_guidelines:
            content_lower = safety_data.get("content_segment", "").lower()

            for prohibited_topic in brand_guidelines.prohibited_topics:
                if prohibited_topic in content_lower:
                    recommendations.append(f"Remove or edit {prohibited_topic} content")

            for allowed_topic in brand_guidelines.allowed_topics:
                if allowed_topic in content_lower:
                    recommendations.append(f"Content aligns with {allowed_topic} guidelines")

        return recommendations

    def _generate_overall_recommendations(
        self,
        segment_analyses: list[dict[str, Any]],
        safe_percentage: float,
        policy_config: dict[str, Any],
    ) -> list[str]:
        """Generate overall compliance recommendations.

        Args:
            segment_analyses: Individual segment analyses
            safe_percentage: Percentage of safe content
            policy_config: Policy configuration

        Returns:
            List of overall recommendations
        """
        recommendations = []

        if safe_percentage < 0.8:
            recommendations.append("Content has low compliance score - consider major edits")
        elif safe_percentage < 0.9:
            recommendations.append("Content mostly compliant but needs minor edits")

        non_compliant_segments = sum(1 for a in segment_analyses if not a["is_compliant"])
        if non_compliant_segments > 0:
            recommendations.append(f"Remove or edit {non_compliant_segments} non-compliant segments")

        if safe_percentage >= 0.9:
            recommendations.append("Content is highly compliant and sponsor-ready")

        return recommendations

    def _calculate_sponsor_integration_points(
        self, script_segments: list[dict[str, Any]], brand_guidelines: BrandGuidelines
    ) -> list[dict[str, Any]]:
        """Calculate optimal points for sponsor integration.

        Args:
            script_segments: Script segments
            brand_guidelines: Brand guidelines

        Returns:
            List of sponsor integration points
        """
        integration_points = []

        # Add sponsor mentions at natural transition points
        for i, segment in enumerate(script_segments):
            # Look for transition words or topic changes
            content = segment.get("content", "").lower()

            transition_indicators = [
                "speaking of",
                "that reminds me",
                "by the way",
                "also",
                "meanwhile",
                "interestingly",
                "actually",
                "so",
            ]

            if any(indicator in content for indicator in transition_indicators):
                integration_points.append(
                    {
                        "segment_index": i,
                        "integration_type": "natural_transition",
                        "suggested_duration": 15,  # 15 seconds
                        "position": "start",  # Insert at beginning of segment
                    }
                )

        # Add end-of-segment sponsor mentions
        if script_segments and brand_guidelines.sponsorship_format == "integrated":
            integration_points.append(
                {
                    "segment_index": len(script_segments) - 1,
                    "integration_type": "segment_end",
                    "suggested_duration": 20,
                    "position": "end",
                }
            )

        return integration_points

    def _generate_sponsor_content(
        self,
        sponsor_product: str,
        sponsor_message: str,
        brand_guidelines: BrandGuidelines,
    ) -> str:
        """Generate sponsor content based on brand guidelines.

        Args:
            sponsor_product: Product to promote
            sponsor_message: Key sponsor message
            brand_guidelines: Brand guidelines

        Returns:
            Generated sponsor script content
        """
        tone = brand_guidelines.tone_requirements[0] if brand_guidelines.tone_requirements else "professional"

        if tone == "casual":
            return f"Hey everyone, I wanted to quickly mention {sponsor_product}. {sponsor_message}"
        elif tone == "professional":
            return f"As a {brand_guidelines.target_audience} content creator, I recommend {sponsor_product}. {sponsor_message}"
        elif tone == "educational":
            return f"Today I want to share information about {sponsor_product}, which {sponsor_message}"
        else:
            return f"I recommend {sponsor_product} because {sponsor_message}"

    def _check_cache(
        self,
        content_segments: list[dict[str, Any]],
        brand_guidelines: BrandGuidelines | None,
        policy_pack: str,
    ) -> ComplianceReport | None:
        """Check if compliance analysis exists in cache.

        Args:
            content_segments: Content segments
            brand_guidelines: Brand guidelines
            policy_pack: Policy pack used

        Returns:
            Cached ComplianceReport or None
        """
        import hashlib

        # Create cache key from content and guidelines
        segments_hash = hashlib.sha256(str(content_segments).encode()).hexdigest()[:16]
        guidelines_hash = (
            hashlib.sha256(str(brand_guidelines).encode()).hexdigest()[:16] if brand_guidelines else "none"
        )
        cache_key = f"{segments_hash}:{guidelines_hash}:{policy_pack}"

        if cache_key in self._compliance_cache:
            return self._compliance_cache[cache_key]

        return None

    def _cache_result(
        self,
        content_segments: list[dict[str, Any]],
        brand_guidelines: BrandGuidelines | None,
        policy_pack: str,
        result: ComplianceReport,
    ) -> None:
        """Cache compliance analysis result.

        Args:
            content_segments: Content segments
            brand_guidelines: Brand guidelines
            policy_pack: Policy pack used
            result: ComplianceReport to cache
        """
        import hashlib

        # Create cache key
        segments_hash = hashlib.sha256(str(content_segments).encode()).hexdigest()[:16]
        guidelines_hash = (
            hashlib.sha256(str(brand_guidelines).encode()).hexdigest()[:16] if brand_guidelines else "none"
        )
        cache_key = f"{segments_hash}:{guidelines_hash}:{policy_pack}"

        # Evict old entries if cache is full
        if len(self._compliance_cache) >= self.cache_size:
            # Simple FIFO eviction - remove first key
            first_key = next(iter(self._compliance_cache))
            del self._compliance_cache[first_key]

        self._compliance_cache[cache_key] = result

    def clear_cache(self) -> StepResult:
        """Clear compliance cache.

        Returns:
            StepResult with cache clear status
        """
        cache_size = len(self._compliance_cache)
        self._compliance_cache.clear()

        logger.info(f"Cleared {cache_size} cached compliance analyses")

        return StepResult.ok(data={"cleared_entries": cache_size})

    def get_cache_stats(self) -> StepResult:
        """Get compliance cache statistics.

        Returns:
            StepResult with cache statistics
        """
        try:
            stats = {
                "total_cached": len(self._compliance_cache),
                "cache_size_limit": self.cache_size,
                "utilization": len(self._compliance_cache) / self.cache_size if self.cache_size > 0 else 0.0,
            }

            return StepResult.ok(data=stats)

        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return StepResult.fail(f"Failed to get cache stats: {e!s}")


# Singleton instance
_sponsor_assistant: SponsorComplianceAssistant | None = None


def get_sponsor_compliance_assistant() -> SponsorComplianceAssistant:
    """Get singleton sponsor compliance assistant instance.

    Returns:
        Initialized SponsorComplianceAssistant instance
    """
    global _sponsor_assistant

    if _sponsor_assistant is None:
        _sponsor_assistant = SponsorComplianceAssistant()

    return _sponsor_assistant
