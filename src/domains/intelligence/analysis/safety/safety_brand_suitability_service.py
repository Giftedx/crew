"""Safety and Brand Suitability Analysis Service for Creator Intelligence.

This module provides content safety analysis and brand suitability assessment
using multi-label classification for policy compliance and brand safety.

Features:
- Content safety classification (safe, unsafe, sensitive)
- Brand suitability scoring for sponsorship compliance
- Multi-label policy classification
- Integration with content moderation systems

Dependencies:
- transformers: For multi-label classification models
- Optional: Custom fine-tuned models for domain-specific policies
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Literal

from ultimate_discord_intelligence_bot.step_result import StepResult


logger = logging.getLogger(__name__)
try:
    from transformers import pipeline

    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    pipeline = None
    logger.warning("transformers not available, using rule-based safety analysis")


@dataclass
class SafetyClassification:
    """Safety classification result for content."""

    safety_level: str
    confidence: float
    risk_factors: list[str]
    compliance_score: float


@dataclass
class BrandSuitability:
    """Brand suitability assessment for content."""

    suitability_score: float
    brand_alignment: str
    target_audience: str
    content_warnings: list[str]
    sponsorship_readiness: bool


@dataclass
class PolicyCompliance:
    """Policy compliance assessment result."""

    compliance_score: float
    violated_policies: list[str]
    compliance_flags: list[str]
    recommendations: list[str]


@dataclass
class SafetyBrandSuitabilityResult:
    """Result of safety and brand suitability analysis."""

    safety: SafetyClassification
    brand_suitability: BrandSuitability
    policy_compliance: PolicyCompliance
    content_segment: str
    speaker: str | None = None
    timestamp: float | None = None
    analysis_confidence: float = 1.0


class SafetyBrandSuitabilityService:
    """Service for safety analysis and brand suitability assessment.

    Usage:
        service = SafetyBrandSuitabilityService()
        result = service.analyze_content("content text", brand_guidelines)
        safety = result.data["safety"]
    """

    def __init__(self, cache_size: int = 1000):
        """Initialize safety analysis service.

        Args:
            cache_size: Maximum number of cached results
        """
        self.cache_size = cache_size
        self._analysis_cache: dict[str, SafetyBrandSuitabilityResult] = {}
        self._safety_classifier: Any = None
        self._policy_categories = {
            "hate_speech": "Content that promotes hatred or discrimination",
            "violence": "Content depicting or promoting violence",
            "adult_content": "Adult or sexual content",
            "profanity": "Profane or inappropriate language",
            "misinformation": "False or misleading information",
            "spam": "Spam or promotional content",
            "harassment": "Harassment or bullying content",
            "illegal_activity": "Content promoting illegal activities",
        }

    def analyze_content(
        self,
        content: str,
        brand_guidelines: dict[str, Any] | None = None,
        speaker: str | None = None,
        timestamp: float | None = None,
        model: Literal["fast", "balanced", "quality"] = "balanced",
        use_cache: bool = True,
    ) -> StepResult:
        """Analyze content for safety and brand suitability.

        Args:
            content: Content text to analyze
            brand_guidelines: Brand-specific guidelines (optional)
            speaker: Speaker name (optional)
            timestamp: Timestamp of content (optional)
            model: Model selection
            use_cache: Whether to use analysis cache

        Returns:
            StepResult with safety and brand analysis
        """
        try:
            import time

            start_time = time.time()
            if not content or not content.strip():
                return StepResult.fail("Content cannot be empty", status="bad_request")
            if use_cache:
                cache_result = self._check_cache(content, brand_guidelines, model)
                if cache_result:
                    logger.info("Safety analysis cache hit")
                    return StepResult.ok(
                        data={
                            "safety": cache_result.safety.__dict__,
                            "brand_suitability": cache_result.brand_suitability.__dict__,
                            "policy_compliance": cache_result.policy_compliance.__dict__,
                            "content_segment": cache_result.content_segment,
                            "speaker": cache_result.speaker,
                            "timestamp": cache_result.timestamp,
                            "analysis_confidence": cache_result.analysis_confidence,
                            "cache_hit": True,
                            "processing_time_ms": (time.time() - start_time) * 1000,
                        }
                    )
            model_name = self._select_model(model)
            analysis_result = self._analyze_content(content, brand_guidelines, speaker, timestamp, model_name)
            if analysis_result:
                if use_cache:
                    self._cache_result(content, brand_guidelines, model, analysis_result)
                processing_time = (time.time() - start_time) * 1000
                return StepResult.ok(
                    data={
                        "safety": analysis_result.safety.__dict__,
                        "brand_suitability": analysis_result.brand_suitability.__dict__,
                        "policy_compliance": analysis_result.policy_compliance.__dict__,
                        "content_segment": analysis_result.content_segment,
                        "speaker": analysis_result.speaker,
                        "timestamp": analysis_result.timestamp,
                        "analysis_confidence": analysis_result.analysis_confidence,
                        "cache_hit": False,
                        "processing_time_ms": processing_time,
                    }
                )
            else:
                return StepResult.fail("Analysis failed", status="retryable")
        except Exception as e:
            logger.error(f"Safety analysis failed: {e}")
            return StepResult.fail(f"Analysis failed: {e!s}", status="retryable")

    def analyze_segments(
        self,
        segments: list[dict[str, Any]],
        brand_guidelines: dict[str, Any] | None = None,
        model: Literal["fast", "balanced", "quality"] = "balanced",
        use_cache: bool = True,
    ) -> StepResult:
        """Analyze multiple content segments for safety and brand suitability.

        Args:
            segments: List of content segments with text and metadata
            brand_guidelines: Brand-specific guidelines
            model: Model selection
            use_cache: Whether to use analysis cache

        Returns:
            StepResult with analysis results for all segments
        """
        try:
            results = []
            for segment in segments:
                segment_content = segment.get("text", "")
                speaker = segment.get("speaker")
                timestamp = segment.get("timestamp")
                if not segment_content:
                    continue
                segment_result = self.analyze_content(
                    content=segment_content,
                    brand_guidelines=brand_guidelines,
                    speaker=speaker,
                    timestamp=timestamp,
                    model=model,
                    use_cache=False,
                )
                if segment_result.success:
                    segment_data = segment_result.data
                    segment_data["segment_index"] = len(results)
                    segment_data["original_content"] = segment_content
                    results.append(segment_data)
            if results:
                safety_scores = [r["safety"]["compliance_score"] for r in results]
                suitability_scores = [r["brand_suitability"]["suitability_score"] for r in results]
                compliance_scores = [r["policy_compliance"]["compliance_score"] for r in results]
                avg_safety = sum(safety_scores) / len(safety_scores)
                avg_suitability = sum(suitability_scores) / len(suitability_scores)
                avg_compliance = sum(compliance_scores) / len(compliance_scores)
            else:
                avg_safety = avg_suitability = avg_compliance = 0.0
            return StepResult.ok(
                data={
                    "results": results,
                    "total_segments": len(segments),
                    "analyzed_segments": len(results),
                    "average_safety_score": avg_safety,
                    "average_suitability_score": avg_suitability,
                    "average_compliance_score": avg_compliance,
                    "overall_compliance_score": (avg_safety + avg_suitability + avg_compliance) / 3,
                    "model": model,
                }
            )
        except Exception as e:
            logger.error(f"Segment analysis failed: {e}")
            return StepResult.fail(f"Segment analysis failed: {e!s}")

    def _select_model(self, model_alias: str) -> str:
        """Select actual model configuration from alias.

        Args:
            model_alias: Model alias (fast, balanced, quality)

        Returns:
            Model configuration string
        """
        model_configs = {"fast": "fast_analysis", "balanced": "balanced_analysis", "quality": "quality_analysis"}
        return model_configs.get(model_alias, "balanced_analysis")

    def _analyze_content(
        self,
        content: str,
        brand_guidelines: dict[str, Any] | None,
        speaker: str | None,
        timestamp: float | None,
        model_name: str,
    ) -> SafetyBrandSuitabilityResult | None:
        """Analyze content using safety models or fallback.

        Args:
            content: Content to analyze
            brand_guidelines: Brand-specific guidelines
            speaker: Speaker name
            timestamp: Timestamp
            model_name: Model configuration

        Returns:
            SafetyBrandSuitabilityResult or None if analysis fails
        """
        try:
            if TRANSFORMERS_AVAILABLE:
                return self._analyze_with_transformers(content, brand_guidelines, speaker, timestamp, model_name)
            logger.warning("Transformers not available, using rule-based analysis")
            return self._analyze_with_rules(content, brand_guidelines, speaker, timestamp, model_name)
        except Exception as e:
            logger.error(f"Content analysis failed for model {model_name}: {e}")
            return None

    def _analyze_with_transformers(
        self,
        content: str,
        brand_guidelines: dict[str, Any] | None,
        speaker: str | None,
        timestamp: float | None,
        model_name: str,
    ) -> SafetyBrandSuitabilityResult:
        """Analyze content using transformer models.

        Args:
            content: Content to analyze
            brand_guidelines: Brand-specific guidelines
            speaker: Speaker name
            timestamp: Timestamp
            model_name: Model configuration

        Returns:
            SafetyBrandSuitabilityResult with analysis
        """
        if self._safety_classifier is None:
            logger.info("Loading safety classification model")
            try:
                self._safety_classifier = pipeline(
                    "text-classification", model="unitary/toxic-bert", return_all_scores=True
                )
            except Exception:
                self._safety_classifier = None
        safety = self._analyze_safety(content)
        brand_suitability = self._analyze_brand_suitability(content, brand_guidelines)
        policy_compliance = self._analyze_policy_compliance(content)
        confidences = [safety.confidence, brand_suitability.suitability_score, policy_compliance.compliance_score]
        avg_confidence = sum(confidences) / len(confidences)
        return SafetyBrandSuitabilityResult(
            safety=safety,
            brand_suitability=brand_suitability,
            policy_compliance=policy_compliance,
            content_segment=content,
            speaker=speaker,
            timestamp=timestamp,
            analysis_confidence=avg_confidence,
        )

    def _analyze_safety(self, content: str) -> SafetyClassification:
        """Analyze content safety.

        Args:
            content: Content to analyze

        Returns:
            SafetyClassification result
        """
        if self._safety_classifier:
            try:
                results = self._safety_classifier(content)
                if results and isinstance(results[0], list):
                    scores = results[0]
                    toxic_score = next((item["score"] for item in scores if item["label"].lower() == "toxic"), 0)
                    safe_score = next((item["score"] for item in scores if item["label"].lower() == "safe"), 0)
                    if toxic_score > 0.7:
                        safety_level = "unsafe"
                        confidence = toxic_score
                    elif toxic_score > 0.3:
                        safety_level = "sensitive"
                        confidence = toxic_score
                    else:
                        safety_level = "safe"
                        confidence = safe_score
                    risk_factors = []
                    if toxic_score > 0.5:
                        risk_factors.append("toxicity")
                    if "hate" in content.lower():
                        risk_factors.append("hate_speech")
                    if "violence" in content.lower() or "kill" in content.lower():
                        risk_factors.append("violence")
                    compliance_score = 1.0 - toxic_score
                    return SafetyClassification(
                        safety_level=safety_level,
                        confidence=confidence,
                        risk_factors=risk_factors,
                        compliance_score=compliance_score,
                    )
            except Exception as e:
                logger.warning(f"Transformer safety analysis failed: {e}")
        return self._analyze_safety_rules(content)

    def _analyze_brand_suitability(self, content: str, brand_guidelines: dict[str, Any] | None) -> BrandSuitability:
        """Analyze brand suitability for sponsorship.

        Args:
            content: Content to analyze
            brand_guidelines: Brand-specific guidelines

        Returns:
            BrandSuitability result
        """
        content_lower = content.lower()
        brand_friendly_words = ["professional", "educational", "informative", "helpful", "positive"]
        brand_friendly_score = sum(1 for word in brand_friendly_words if word in content_lower) / len(
            brand_friendly_words
        )
        brand_risky_words = ["controversial", "political", "religious", "adult", "violent"]
        brand_risky_score = sum(1 for word in brand_risky_words if word in content_lower) / len(brand_risky_words)
        suitability_score = max(0.0, brand_friendly_score - brand_risky_score)
        if suitability_score > 0.7:
            brand_alignment = "excellent"
        elif suitability_score > 0.5:
            brand_alignment = "good"
        elif suitability_score > 0.3:
            brand_alignment = "fair"
        else:
            brand_alignment = "poor"
        if any(word in content_lower for word in ["family", "kids", "children"]):
            target_audience = "family"
        elif any(word in content_lower for word in ["adult", "mature"]):
            target_audience = "adult"
        else:
            target_audience = "general"
        content_warnings = []
        if brand_risky_score > 0.5:
            content_warnings.append("Contains potentially sensitive topics")
        if "political" in content_lower:
            content_warnings.append("Contains political content")
        sponsorship_readiness = suitability_score > 0.6
        return BrandSuitability(
            suitability_score=suitability_score,
            brand_alignment=brand_alignment,
            target_audience=target_audience,
            content_warnings=content_warnings,
            sponsorship_readiness=sponsorship_readiness,
        )

    def _analyze_policy_compliance(self, content: str) -> PolicyCompliance:
        """Analyze policy compliance.

        Args:
            content: Content to analyze

        Returns:
            PolicyCompliance result
        """
        content_lower = content.lower()
        violated_policies = []
        compliance_flags = []
        for policy, description in self._policy_categories.items():
            if self._check_policy_violation(content_lower, policy):
                violated_policies.append(policy)
                compliance_flags.append(description)
        total_policies = len(self._policy_categories)
        violated_count = len(violated_policies)
        compliance_score = (total_policies - violated_count) / total_policies
        recommendations = []
        if violated_policies:
            recommendations.append("Review content for policy violations")
            recommendations.append("Consider content warnings for sensitive topics")
        if compliance_score < 0.8:
            recommendations.append("Content may require moderation before publication")
        return PolicyCompliance(
            compliance_score=compliance_score,
            violated_policies=violated_policies,
            compliance_flags=compliance_flags,
            recommendations=recommendations,
        )

    def _check_policy_violation(self, content_lower: str, policy: str) -> bool:
        """Check if content violates a specific policy.

        Args:
            content_lower: Lowercase content text
            policy: Policy category to check

        Returns:
            True if policy is violated
        """
        policy_indicators = {
            "hate_speech": ["hate", "racist", "sexist", "homophobic", "discrimination"],
            "violence": ["kill", "murder", "assault", "attack", "fight", "violent"],
            "adult_content": ["sex", "sexual", "porn", "adult", "explicit"],
            "profanity": ["fuck", "shit", "damn", "hell", "ass"],
            "misinformation": ["fake", "false", "lie", "wrong", "incorrect"],
            "spam": ["buy now", "click here", "limited time", "discount"],
            "harassment": ["bully", "harass", "threaten", "intimidate"],
            "illegal_activity": ["drugs", "steal", "illegal", "crime"],
        }
        indicators = policy_indicators.get(policy, [])
        return any(indicator in content_lower for indicator in indicators)

    def _analyze_safety_rules(self, content: str) -> SafetyClassification:
        """Rule-based safety analysis fallback.

        Args:
            content: Content to analyze

        Returns:
            SafetyClassification result
        """
        content_lower = content.lower()
        unsafe_indicators = {
            "hate_speech": ["hate", "racist", "sexist", "homophobic"],
            "violence": ["kill", "murder", "assault", "attack"],
            "profanity": ["fuck", "shit", "damn", "hell"],
        }
        risk_factors = []
        max_risk_score = 0.0
        for category, indicators in unsafe_indicators.items():
            category_score = sum(1 for indicator in indicators if indicator in content_lower)
            if category_score > 0:
                risk_factors.append(category)
                max_risk_score = max(max_risk_score, category_score * 0.2)
        if max_risk_score > 0.6:
            safety_level = "unsafe"
        elif max_risk_score > 0.3:
            safety_level = "sensitive"
        else:
            safety_level = "safe"
        return SafetyClassification(
            safety_level=safety_level,
            confidence=min(max_risk_score + 0.5, 1.0),
            risk_factors=risk_factors,
            compliance_score=max(0.0, 1.0 - max_risk_score),
        )

    def _check_cache(
        self, content: str, brand_guidelines: dict[str, Any] | None, model: str
    ) -> SafetyBrandSuitabilityResult | None:
        """Check if analysis exists in cache.

        Args:
            content: Content text
            brand_guidelines: Brand guidelines
            model: Model alias

        Returns:
            Cached SafetyBrandSuitabilityResult or None
        """
        import hashlib

        guidelines_str = str(brand_guidelines) if brand_guidelines else ""
        combined = f"{content}:{guidelines_str}:{model}"
        cache_key = hashlib.sha256(combined.encode()).hexdigest()
        if cache_key in self._analysis_cache:
            return self._analysis_cache[cache_key]
        return None

    def _cache_result(
        self, content: str, brand_guidelines: dict[str, Any] | None, model: str, result: SafetyBrandSuitabilityResult
    ) -> None:
        """Cache analysis result.

        Args:
            content: Content text
            brand_guidelines: Brand guidelines
            model: Model alias
            result: SafetyBrandSuitabilityResult to cache
        """
        import hashlib
        import time

        guidelines_str = str(brand_guidelines) if brand_guidelines else ""
        combined = f"{content}:{guidelines_str}:{model}"
        cache_key = hashlib.sha256(combined.encode()).hexdigest()
        result.analysis_confidence = time.time() * 1000
        if len(self._analysis_cache) >= self.cache_size:
            first_key = next(iter(self._analysis_cache))
            del self._analysis_cache[first_key]
        self._analysis_cache[cache_key] = result

    def clear_cache(self) -> StepResult:
        """Clear analysis cache.

        Returns:
            StepResult with cache clear status
        """
        cache_size = len(self._analysis_cache)
        self._analysis_cache.clear()
        logger.info(f"Cleared {cache_size} cached analyses")
        return StepResult.ok(data={"cleared_entries": cache_size})

    def get_cache_stats(self) -> StepResult:
        """Get analysis cache statistics.

        Returns:
            StepResult with cache statistics
        """
        try:
            stats = {
                "total_cached": len(self._analysis_cache),
                "cache_size_limit": self.cache_size,
                "utilization": len(self._analysis_cache) / self.cache_size if self.cache_size > 0 else 0.0,
                "models_cached": {},
            }
            for result in self._analysis_cache.values():
                model = "transformer" if hasattr(result, "safety") else "rule_based"
                stats["models_cached"][model] = stats["models_cached"].get(model, 0) + 1
            return StepResult.ok(data=stats)
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return StepResult.fail(f"Failed to get cache stats: {e!s}")


_safety_service: SafetyBrandSuitabilityService | None = None


def get_safety_brand_suitability_service() -> SafetyBrandSuitabilityService:
    """Get singleton safety analysis service instance.

    Returns:
        Initialized SafetyBrandSuitabilityService instance
    """
    global _safety_service
    if _safety_service is None:
        _safety_service = SafetyBrandSuitabilityService()
    return _safety_service
