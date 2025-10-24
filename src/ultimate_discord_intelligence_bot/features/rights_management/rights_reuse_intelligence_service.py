"""Rights and Reuse Intelligence Service for Creator Intelligence.

This module provides rights management and reuse intelligence capabilities including:
- Third-party footage fragment tracking and licensing
- Fair-use risk assessment and signals
- Alternative B-roll suggestions and edits
- Copyright compliance monitoring

Features:
- License and rights holder tracking
- Fair-use risk assessment
- Alternative content suggestions
- Integration with content creation workflows

Dependencies:
- Vector similarity for content matching
- Metadata extraction for rights information
- Risk assessment algorithms
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Literal

from ultimate_discord_intelligence_bot.step_result import StepResult


logger = logging.getLogger(__name__)


@dataclass
class LicenseInfo:
    """License information for content."""

    license_type: str  # creative_commons, fair_use, copyrighted, public_domain
    rights_holder: str
    usage_rights: list[str]
    restrictions: list[str]
    attribution_required: bool
    commercial_use_allowed: bool


@dataclass
class ContentFragment:
    """A fragment of content with rights information."""

    fragment_id: str
    start_time: float
    end_time: float
    duration: float
    content_type: str  # video, audio, image, text
    source_url: str
    license_info: LicenseInfo
    risk_score: float  # 0.0 to 1.0
    alternative_suggestions: list[str]


@dataclass
class ReuseAnalysis:
    """Analysis of content reuse possibilities."""

    can_reuse: bool
    risk_level: str  # low, medium, high
    required_actions: list[str]
    alternative_content: list[str]
    estimated_cost: float  # Cost of alternative content
    compliance_score: float  # 0.0 to 1.0


@dataclass
class RightsReuseIntelligenceResult:
    """Result of rights and reuse intelligence analysis."""

    content_fragments: list[ContentFragment]
    reuse_analysis: ReuseAnalysis
    risk_assessment: dict[str, float]
    recommendations: list[str]
    total_content_duration: float
    processing_time_ms: float = 0.0


class RightsReuseIntelligenceService:
    """Service for rights management and reuse intelligence.

    Usage:
        service = RightsReuseIntelligenceService()
        result = service.analyze_content_rights(content_segments)
        fragments = result.data["content_fragments"]
    """

    def __init__(self, cache_size: int = 1000):
        """Initialize rights management service.

        Args:
            cache_size: Maximum number of cached results
        """
        self.cache_size = cache_size
        self._analysis_cache: dict[str, RightsReuseIntelligenceResult] = {}

        # Known license patterns
        self._license_patterns = {
            "creative_commons": [
                "creativecommons.org",
                "CC BY",
                "CC BY-SA",
                "CC BY-NC",
                "CC BY-ND",
            ],
            "fair_use": [
                "fair use",
                "educational purpose",
                "commentary",
                "criticism",
                "news reporting",
            ],
            "copyrighted": [
                "all rights reserved",
                "copyright",
                "©",
                "trademark",
                "DMCA",
            ],
        }

        # Risk factors
        self._risk_factors = {
            "commercial_use": 0.8,
            "large_audience": 0.6,
            "sensitive_content": 0.7,
            "recent_content": 0.5,
            "unknown_source": 0.9,
        }

    def analyze_content_rights(
        self,
        content_segments: list[dict[str, Any]],
        content_type: str = "video",
        intended_use: str = "educational",
        target_audience_size: str = "medium",
        model: Literal["fast", "balanced", "quality"] = "balanced",
        use_cache: bool = True,
    ) -> StepResult:
        """Analyze content segments for rights and reuse possibilities.

        Args:
            content_segments: Content segments with metadata
            content_type: Type of content (video, audio, image, text)
            intended_use: Intended use (educational, commercial, entertainment)
            target_audience_size: Target audience size (small, medium, large)
            model: Model selection
            use_cache: Whether to use analysis cache

        Returns:
            StepResult with rights analysis
        """
        try:
            import time

            start_time = time.time()

            # Validate inputs
            if not content_segments:
                return StepResult.fail("Content segments cannot be empty", status="bad_request")

            # Check cache first
            if use_cache:
                cache_result = self._check_cache(content_segments, content_type, intended_use, model)
                if cache_result:
                    logger.info("Rights analysis cache hit")
                    return StepResult.ok(
                        data={
                            "content_fragments": [f.__dict__ for f in cache_result.content_fragments],
                            "reuse_analysis": cache_result.reuse_analysis.__dict__,
                            "risk_assessment": cache_result.risk_assessment,
                            "recommendations": cache_result.recommendations,
                            "total_content_duration": cache_result.total_content_duration,
                            "cache_hit": True,
                            "processing_time_ms": (time.time() - start_time) * 1000,
                        }
                    )

            # Perform rights analysis
            model_name = self._select_model(model)
            analysis_result = self._analyze_content_rights(
                content_segments,
                content_type,
                intended_use,
                target_audience_size,
                model_name,
            )

            if analysis_result:
                # Cache result
                if use_cache:
                    self._cache_result(
                        content_segments,
                        content_type,
                        intended_use,
                        model,
                        analysis_result,
                    )

                processing_time = (time.time() - start_time) * 1000

                return StepResult.ok(
                    data={
                        "content_fragments": [f.__dict__ for f in analysis_result.content_fragments],
                        "reuse_analysis": analysis_result.reuse_analysis.__dict__,
                        "risk_assessment": analysis_result.risk_assessment,
                        "recommendations": analysis_result.recommendations,
                        "total_content_duration": analysis_result.total_content_duration,
                        "cache_hit": False,
                        "processing_time_ms": processing_time,
                    }
                )
            else:
                return StepResult.fail("Rights analysis failed", status="retryable")

        except Exception as e:
            logger.error(f"Rights analysis failed: {e}")
            return StepResult.fail(f"Rights analysis failed: {e!s}", status="retryable")

    def assess_fair_use_risk(
        self,
        content_description: str,
        intended_use: str,
        content_type: str,
        audience_size: str,
    ) -> StepResult:
        """Assess fair use risk for content usage.

        Args:
            content_description: Description of content being used
            intended_use: Intended use (educational, commentary, criticism)
            content_type: Type of content (video, audio, image)
            audience_size: Expected audience size

        Returns:
            StepResult with fair use risk assessment
        """
        try:
            # Analyze fair use factors
            fair_use_factors = {
                "purpose_character": self._assess_purpose_and_character(intended_use),
                "nature_of_work": self._assess_nature_of_work(content_type),
                "amount_used": self._assess_amount_used(content_description),
                "market_effect": self._assess_market_effect(audience_size),
            }

            # Calculate overall fair use score
            overall_score = sum(fair_use_factors.values()) / len(fair_use_factors)

            # Determine risk level
            if overall_score >= 0.8:
                risk_level = "low"
            elif overall_score >= 0.6:
                risk_level = "medium"
            else:
                risk_level = "high"

            return StepResult.ok(
                data={
                    "fair_use_score": overall_score,
                    "risk_level": risk_level,
                    "factors": fair_use_factors,
                    "recommendations": self._generate_fair_use_recommendations(fair_use_factors),
                }
            )

        except Exception as e:
            logger.error(f"Fair use assessment failed: {e}")
            return StepResult.fail(f"Fair use assessment failed: {e!s}")

    def suggest_alternative_content(
        self,
        original_content: dict[str, Any],
        risk_threshold: float = 0.7,
    ) -> list[str]:
        """Suggest alternative content with lower rights risks.

        Args:
            original_content: Original content being replaced
            risk_threshold: Maximum acceptable risk level

        Returns:
            List of alternative content suggestions
        """
        alternatives = []

        content_type = original_content.get("content_type", "unknown")
        description = original_content.get("description", "")

        # Generate alternative suggestions based on content type
        if content_type == "video":
            alternatives.extend(self._suggest_video_alternatives(description))
        elif content_type == "image":
            alternatives.extend(self._suggest_image_alternatives(description))
        elif content_type == "audio":
            alternatives.extend(self._suggest_audio_alternatives(description))

        # Filter by risk threshold
        safe_alternatives = [alt for alt in alternatives if self._assess_alternative_risk(alt) <= risk_threshold]

        return safe_alternatives[:5]  # Limit to top 5

    def _select_model(self, model_alias: str) -> str:
        """Select actual model configuration from alias.

        Args:
            model_alias: Model alias (fast, balanced, quality)

        Returns:
            Model configuration string
        """
        model_configs = {
            "fast": "fast_analysis",
            "balanced": "balanced_analysis",
            "quality": "quality_analysis",
        }

        return model_configs.get(model_alias, "balanced_analysis")

    def _analyze_content_rights(
        self,
        content_segments: list[dict[str, Any]],
        content_type: str,
        intended_use: str,
        target_audience_size: str,
        model_name: str,
    ) -> RightsReuseIntelligenceResult | None:
        """Analyze content segments for rights and reuse.

        Args:
            content_segments: Content segments to analyze
            content_type: Type of content
            intended_use: Intended use
            target_audience_size: Target audience size
            model_name: Model configuration

        Returns:
            RightsReuseIntelligenceResult or None if analysis fails
        """
        try:
            content_fragments = []
            total_duration = 0.0

            # Analyze each content segment
            for segment in content_segments:
                start_time = segment.get("start_time", 0)
                end_time = segment.get("end_time", start_time + 30)
                duration = end_time - start_time
                total_duration += duration

                # Extract license information
                license_info = self._extract_license_info(segment)

                # Calculate risk score
                risk_score = self._calculate_risk_score(segment, intended_use, target_audience_size)

                # Generate alternative suggestions
                alternatives = self.suggest_alternative_content(
                    {
                        "content_type": content_type,
                        "description": segment.get("description", ""),
                    }
                )

                fragment = ContentFragment(
                    fragment_id=f"fragment_{int(start_time)}",
                    start_time=start_time,
                    end_time=end_time,
                    duration=duration,
                    content_type=content_type,
                    source_url=segment.get("source_url", ""),
                    license_info=license_info,
                    risk_score=risk_score,
                    alternative_suggestions=alternatives,
                )

                content_fragments.append(fragment)

            # Generate reuse analysis
            reuse_analysis = self._generate_reuse_analysis(content_fragments, intended_use)

            # Generate risk assessment
            risk_assessment = self._generate_risk_assessment(content_fragments)

            # Generate recommendations
            recommendations = self._generate_recommendations(content_fragments, reuse_analysis)

            return RightsReuseIntelligenceResult(
                content_fragments=content_fragments,
                reuse_analysis=reuse_analysis,
                risk_assessment=risk_assessment,
                recommendations=recommendations,
                total_content_duration=total_duration,
            )

        except Exception as e:
            logger.error(f"Content rights analysis failed: {e}")
            return None

    def _extract_license_info(self, segment: dict[str, Any]) -> LicenseInfo:
        """Extract license information from content segment.

        Args:
            segment: Content segment with metadata

        Returns:
            LicenseInfo for the segment
        """
        description = segment.get("description", "").lower()
        source_url = segment.get("source_url", "").lower()

        # Check for license indicators
        license_type = "unknown"

        # Creative Commons detection
        if any(
            pattern in description or pattern in source_url for pattern in self._license_patterns["creative_commons"]
        ):
            license_type = "creative_commons"
        # Fair use detection
        elif any(pattern in description for pattern in self._license_patterns["fair_use"]):
            license_type = "fair_use"
        # Copyright detection
        elif any(pattern in description or pattern in source_url for pattern in self._license_patterns["copyrighted"]):
            license_type = "copyrighted"
        else:
            license_type = "unknown"

        # Determine rights holder
        rights_holder = "Unknown"
        if "youtube.com" in source_url:
            rights_holder = "YouTube Creator"
        elif "twitch.tv" in source_url:
            rights_holder = "Twitch Streamer"
        elif "twitter.com" in source_url:
            rights_holder = "Twitter User"

        # Determine usage rights based on license type
        usage_rights = []
        restrictions = []
        attribution_required = False
        commercial_use_allowed = False

        if license_type == "creative_commons":
            usage_rights = ["reuse", "modify", "redistribute"]
            attribution_required = True
            commercial_use_allowed = True
        elif license_type == "fair_use":
            usage_rights = ["educational_use", "commentary", "criticism"]
            restrictions = ["transformative_use_only", "limited_portions"]
            commercial_use_allowed = False
        elif license_type == "copyrighted":
            usage_rights = []
            restrictions = ["no_reuse_without_permission", "commercial_use_prohibited"]
            attribution_required = True
            commercial_use_allowed = False

        return LicenseInfo(
            license_type=license_type,
            rights_holder=rights_holder,
            usage_rights=usage_rights,
            restrictions=restrictions,
            attribution_required=attribution_required,
            commercial_use_allowed=commercial_use_allowed,
        )

    def _calculate_risk_score(self, segment: dict[str, Any], intended_use: str, audience_size: str) -> float:
        """Calculate risk score for content segment.

        Args:
            segment: Content segment
            intended_use: Intended use
            audience_size: Target audience size

        Returns:
            Risk score (0.0 to 1.0)
        """
        risk_score = 0.0

        # Commercial use risk
        if intended_use == "commercial":
            risk_score += self._risk_factors["commercial_use"]

        # Large audience risk
        if audience_size == "large":
            risk_score += self._risk_factors["large_audience"]

        # Content age risk (newer content = higher risk)
        content_age_days = self._calculate_content_age(segment)
        if content_age_days < 30:  # Less than 30 days old
            risk_score += self._risk_factors["recent_content"]

        # Unknown source risk
        if segment.get("source_url", "") == "":
            risk_score += self._risk_factors["unknown_source"]

        # Sensitive content risk
        description = segment.get("description", "").lower()
        if any(word in description for word in ["violence", "adult", "political", "controversial"]):
            risk_score += self._risk_factors["sensitive_content"]

        return min(risk_score, 1.0)

    def _calculate_content_age(self, segment: dict[str, Any]) -> int:
        """Calculate age of content in days.

        Args:
            segment: Content segment

        Returns:
            Age in days
        """
        # Placeholder - would use actual timestamp
        return 60  # Assume 60 days old as default

    def _generate_reuse_analysis(self, fragments: list[ContentFragment], intended_use: str) -> ReuseAnalysis:
        """Generate reuse analysis for content fragments.

        Args:
            fragments: Content fragments
            intended_use: Intended use

        Returns:
            ReuseAnalysis
        """
        # Calculate overall risk
        total_risk = sum(f.risk_score for f in fragments)
        avg_risk = total_risk / len(fragments) if fragments else 0.0

        # Determine if content can be reused
        can_reuse = avg_risk < 0.7 and all(f.license_info.commercial_use_allowed for f in fragments)

        # Determine risk level
        if avg_risk < 0.3:
            risk_level = "low"
        elif avg_risk < 0.7:
            risk_level = "medium"
        else:
            risk_level = "high"

        # Generate required actions
        required_actions = []
        if not can_reuse:
            required_actions.append("Obtain explicit permission from rights holders")
        if any(not f.license_info.attribution_required for f in fragments):
            required_actions.append("Provide proper attribution")
        if intended_use == "commercial":
            required_actions.append("Ensure commercial use compliance")

        # Generate alternative content suggestions
        alternative_content = []
        for fragment in fragments:
            if fragment.risk_score > 0.7:
                alternative_content.extend(fragment.alternative_suggestions[:2])

        # Estimate cost of alternatives
        estimated_cost = len(alternative_content) * 50  # $50 per alternative

        # Calculate compliance score
        compliance_score = 1.0 - avg_risk

        return ReuseAnalysis(
            can_reuse=can_reuse,
            risk_level=risk_level,
            required_actions=required_actions,
            alternative_content=alternative_content,
            estimated_cost=estimated_cost,
            compliance_score=compliance_score,
        )

    def _generate_risk_assessment(self, fragments: list[ContentFragment]) -> dict[str, float]:
        """Generate risk assessment summary.

        Args:
            fragments: Content fragments

        Returns:
            Risk assessment dictionary
        """
        if not fragments:
            return {}

        risk_scores = [f.risk_score for f in fragments]
        avg_risk = sum(risk_scores) / len(risk_scores)

        return {
            "overall_risk": avg_risk,
            "max_risk": max(risk_scores),
            "min_risk": min(risk_scores),
            "high_risk_fragments": sum(1 for f in fragments if f.risk_score > 0.7),
            "medium_risk_fragments": sum(1 for f in fragments if 0.4 <= f.risk_score <= 0.7),
            "low_risk_fragments": sum(1 for f in fragments if f.risk_score < 0.4),
        }

    def _generate_recommendations(self, fragments: list[ContentFragment], reuse_analysis: ReuseAnalysis) -> list[str]:
        """Generate recommendations for content usage.

        Args:
            fragments: Content fragments
            reuse_analysis: Reuse analysis

        Returns:
            List of recommendations
        """
        recommendations = []

        # Risk-based recommendations
        if reuse_analysis.risk_level == "high":
            recommendations.append("Consider replacing high-risk content segments")
        elif reuse_analysis.risk_level == "medium":
            recommendations.append("Review medium-risk segments for potential issues")

        # License-based recommendations
        for fragment in fragments:
            if fragment.license_info.license_type == "copyrighted":
                recommendations.append(f"Obtain permission for copyrighted content at {fragment.start_time}s")
            if fragment.license_info.attribution_required:
                recommendations.append(f"Provide attribution for content at {fragment.start_time}s")

        # Alternative content recommendations
        if not reuse_analysis.can_reuse:
            recommendations.append("Consider using alternative content with lower risk profiles")

        return recommendations

    def _assess_purpose_and_character(self, intended_use: str) -> float:
        """Assess purpose and character of use (fair use factor 1).

        Args:
            intended_use: Intended use of content

        Returns:
            Score for purpose and character (0.0 to 1.0)
        """
        # Educational and transformative uses score higher
        if intended_use == "educational":
            return 0.9
        elif intended_use == "commentary" or intended_use == "criticism":
            return 0.8
        elif intended_use == "commercial":
            return 0.3
        else:
            return 0.5

    def _assess_nature_of_work(self, content_type: str) -> float:
        """Assess nature of copyrighted work (fair use factor 2).

        Args:
            content_type: Type of content

        Returns:
            Score for nature of work (0.0 to 1.0)
        """
        # Factual/educational content scores higher than creative
        if content_type == "educational":
            return 0.8
        elif content_type == "news":
            return 0.7
        elif content_type == "documentary":
            return 0.6
        else:
            return 0.4

    def _assess_amount_used(self, content_description: str) -> float:
        """Assess amount and substantiality of portion used (fair use factor 3).

        Args:
            content_description: Description of content usage

        Returns:
            Score for amount used (0.0 to 1.0)
        """
        # Smaller portions score higher
        description_lower = content_description.lower()

        if any(word in description_lower for word in ["brief", "short", "excerpt", "clip"]):
            return 0.8
        elif any(word in description_lower for word in ["significant", "large", "major"]):
            return 0.3
        else:
            return 0.5

    def _assess_market_effect(self, audience_size: str) -> float:
        """Assess effect on potential market (fair use factor 4).

        Args:
            audience_size: Size of target audience

        Returns:
            Score for market effect (0.0 to 1.0)
        """
        # Smaller audiences have less market impact
        if audience_size == "small":
            return 0.8
        elif audience_size == "medium":
            return 0.5
        elif audience_size == "large":
            return 0.2
        else:
            return 0.4

    def _generate_fair_use_recommendations(self, factors: dict[str, float]) -> list[str]:
        """Generate fair use recommendations.

        Args:
            factors: Fair use factor scores

        Returns:
            List of recommendations
        """
        recommendations = []

        if factors["purpose_character"] < 0.5:
            recommendations.append("Consider educational or transformative use")
        if factors["nature_of_work"] < 0.5:
            recommendations.append("Focus on factual rather than creative content")
        if factors["amount_used"] < 0.5:
            recommendations.append("Use smaller portions or excerpts")
        if factors["market_effect"] < 0.5:
            recommendations.append("Target smaller audiences to minimize market impact")

        return recommendations

    def _suggest_video_alternatives(self, description: str) -> list[str]:
        """Suggest alternative video content.

        Args:
            description: Description of original content

        Returns:
            List of alternative suggestions
        """
        alternatives = [
            "Stock footage from free video libraries",
            "Public domain archival footage",
            "Creative Commons licensed educational videos",
            "Self-created demonstration videos",
            "Screen recordings of public information",
        ]

        return alternatives

    def _suggest_image_alternatives(self, description: str) -> list[str]:
        """Suggest alternative image content.

        Args:
            description: Description of original content

        Returns:
            List of alternative suggestions
        """
        alternatives = [
            "Public domain images from libraries",
            "Creative Commons licensed photos",
            "Royalty-free stock images",
            "Self-created graphics and illustrations",
            "Screenshots of public websites",
        ]

        return alternatives

    def _suggest_audio_alternatives(self, description: str) -> list[str]:
        """Suggest alternative audio content.

        Args:
            description: Description of original content

        Returns:
            List of alternative suggestions
        """
        alternatives = [
            "Public domain music and sound effects",
            "Creative Commons licensed audio",
            "Royalty-free sound libraries",
            "Self-created voice recordings",
            "Synthetic audio generation",
        ]

        return alternatives

    def _assess_alternative_risk(self, alternative: str) -> float:
        """Assess risk level of alternative content.

        Args:
            alternative: Alternative content suggestion

        Returns:
            Risk score (0.0 to 1.0)
        """
        # Most alternatives have low risk
        low_risk_alternatives = [
            "Public domain",
            "Creative Commons",
            "Royalty-free",
            "Self-created",
            "Synthetic",
        ]

        if any(term in alternative for term in low_risk_alternatives):
            return 0.1  # Very low risk
        else:
            return 0.3  # Low to medium risk

    def _check_cache(
        self,
        content_segments: list[dict[str, Any]],
        content_type: str,
        intended_use: str,
        model: str,
    ) -> RightsReuseIntelligenceResult | None:
        """Check if rights analysis exists in cache.

        Args:
            content_segments: Content segments
            content_type: Content type
            intended_use: Intended use
            model: Model alias

        Returns:
            Cached RightsReuseIntelligenceResult or None
        """
        import hashlib

        # Create cache key from inputs
        segments_hash = hashlib.sha256(str(content_segments).encode()).hexdigest()[:16]
        cache_key = f"{segments_hash}:{content_type}:{intended_use}:{model}"

        if cache_key in self._analysis_cache:
            return self._analysis_cache[cache_key]

        return None

    def _cache_result(
        self,
        content_segments: list[dict[str, Any]],
        content_type: str,
        intended_use: str,
        model: str,
        result: RightsReuseIntelligenceResult,
    ) -> None:
        """Cache rights analysis result.

        Args:
            content_segments: Content segments
            content_type: Content type
            intended_use: Intended use
            model: Model alias
            result: RightsReuseIntelligenceResult to cache
        """
        import hashlib

        # Create cache key
        segments_hash = hashlib.sha256(str(content_segments).encode()).hexdigest()[:16]
        cache_key = f"{segments_hash}:{content_type}:{intended_use}:{model}"

        # Evict old entries if cache is full
        if len(self._analysis_cache) >= self.cache_size:
            # Simple FIFO eviction - remove first key
            first_key = next(iter(self._analysis_cache))
            del self._analysis_cache[first_key]

        self._analysis_cache[cache_key] = result

    def clear_cache(self) -> StepResult:
        """Clear rights analysis cache.

        Returns:
            StepResult with cache clear status
        """
        cache_size = len(self._analysis_cache)
        self._analysis_cache.clear()

        logger.info(f"Cleared {cache_size} cached rights analyses")

        return StepResult.ok(data={"cleared_entries": cache_size})

    def get_cache_stats(self) -> StepResult:
        """Get rights analysis cache statistics.

        Returns:
            StepResult with cache statistics
        """
        try:
            stats = {
                "total_cached": len(self._analysis_cache),
                "cache_size_limit": self.cache_size,
                "utilization": len(self._analysis_cache) / self.cache_size if self.cache_size > 0 else 0.0,
            }

            return StepResult.ok(data=stats)

        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return StepResult.fail(f"Failed to get cache stats: {e!s}")


# Singleton instance
_rights_service: RightsReuseIntelligenceService | None = None


def get_rights_reuse_intelligence_service() -> RightsReuseIntelligenceService:
    """Get singleton rights management service instance.

    Returns:
        Initialized RightsReuseIntelligenceService instance
    """
    global _rights_service

    if _rights_service is None:
        _rights_service = RightsReuseIntelligenceService()

    return _rights_service
