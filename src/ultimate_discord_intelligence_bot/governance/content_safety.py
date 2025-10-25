"""Content safety classification system with four-tier model.

This module implements OpenAI's content safety classification system with
four tiers: Prohibited, Restricted, Sensitive, and Regulated content.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

from ultimate_discord_intelligence_bot.step_result import StepResult


class ContentTier(Enum):
    """Content safety classification tiers."""

    PROHIBITED = "prohibited"  # Always block
    RESTRICTED = "restricted"  # Context-dependent
    SENSITIVE = "sensitive"  # Appropriate context only
    REGULATED = "regulated"  # Guidance without advice
    SAFE = "safe"  # No restrictions


@dataclass
class SafetyReport:
    """Report of content safety analysis."""

    tier: ContentTier
    confidence: float
    reasons: list[str]
    context_appropriate: bool
    requires_human_review: bool
    mitigation_suggestions: list[str] | None = None


class ContentClassifier:
    """Classifier for content safety using four-tier model.

    Implements OpenAI's content safety classification system:
    1. Prohibited Content (always block)
    2. Restricted Content (context-dependent)
    3. Sensitive Content (appropriate context only)
    4. Regulated Content (guidance without advice)
    """

    def __init__(self) -> None:
        """Initialize the content classifier."""
        self.logger = logging.getLogger(__name__)
        self._initialize_classification_rules()

    def _initialize_classification_rules(self) -> None:
        """Initialize content classification rules."""
        self.prohibited_patterns = [
            # Child safety
            r"\b(?:child|minor|underage).*(?:sexual|porn|nude|explicit)\b",
            r"\b(?:csam|child.*porn|cp)\b",
            # Violence
            r"\b(?:detailed.*instructions).*(?:violence|harm|kill|murder)\b",
            r"\b(?:step.*by.*step).*(?:bomb|explosive|weapon)\b",
            # Illegal activities
            r"\b(?:how.*to).*(?:hack|steal|fraud|scam)\b",
        ]

        self.restricted_patterns = [
            # Information hazards
            r"\b(?:biosecurity|cybersecurity).*(?:vulnerability|exploit)\b",
            r"\b(?:chemical|biological).*(?:weapon|attack)\b",
            # Political manipulation
            r"\b(?:election.*interference|voter.*suppression)\b",
            r"\b(?:disinformation|misinformation).*(?:campaign|strategy)\b",
            # Privacy violations
            r"\b(?:doxx|doxxing|dox).*(?:address|phone|ssn)\b",
            r"\b(?:revenge.*porn|non.*consensual)\b",
        ]

        self.sensitive_patterns = [
            # Adult content
            r"\b(?:erotica|porn|sexual).*(?:content|material)\b",
            r"\b(?:gore|violence).*(?:graphic|explicit)\b",
            # Extremist content
            r"\b(?:extremist|radical).*(?:ideology|belief)\b",
            r"\b(?:hate.*speech|discrimination)\b",
        ]

        self.regulated_patterns = [
            # Medical information
            r"\b(?:medical|health).*(?:advice|diagnosis|treatment)\b",
            r"\b(?:prescription|medication).*(?:advice|recommendation)\b",
            # Legal information
            r"\b(?:legal|law).*(?:advice|counsel|representation)\b",
            r"\b(?:court|lawsuit).*(?:advice|strategy)\b",
            # Financial advice
            r"\b(?:investment|financial).*(?:advice|recommendation)\b",
            r"\b(?:trading|stock).*(?:advice|tip)\b",
        ]

    def classify(self, content: str) -> StepResult:
        """Classify content into safety tiers.

        Args:
            content: The content to classify

        Returns:
            StepResult with classification results
        """
        try:
            content_lower = content.lower()

            # Check for prohibited content
            prohibited_matches = self._check_patterns(content_lower, self.prohibited_patterns)
            if prohibited_matches:
                return StepResult.ok(
                    data={
                        "tier": ContentTier.PROHIBITED.value,
                        "confidence": 0.95,
                        "reasons": ["Contains prohibited content"],
                        "matches": prohibited_matches,
                        "requires_blocking": True,
                    }
                )

            # Check for restricted content
            restricted_matches = self._check_patterns(content_lower, self.restricted_patterns)
            if restricted_matches:
                return StepResult.ok(
                    data={
                        "tier": ContentTier.RESTRICTED.value,
                        "confidence": 0.85,
                        "reasons": ["Contains restricted content"],
                        "matches": restricted_matches,
                        "requires_context_review": True,
                    }
                )

            # Check for sensitive content
            sensitive_matches = self._check_patterns(content_lower, self.sensitive_patterns)
            if sensitive_matches:
                return StepResult.ok(
                    data={
                        "tier": ContentTier.SENSITIVE.value,
                        "confidence": 0.75,
                        "reasons": ["Contains sensitive content"],
                        "matches": sensitive_matches,
                        "requires_consent": True,
                    }
                )

            # Check for regulated content
            regulated_matches = self._check_patterns(content_lower, self.regulated_patterns)
            if regulated_matches:
                return StepResult.ok(
                    data={
                        "tier": ContentTier.REGULATED.value,
                        "confidence": 0.70,
                        "reasons": ["Contains regulated content"],
                        "matches": regulated_matches,
                        "requires_disclaimer": True,
                    }
                )

            # Content appears safe
            return StepResult.ok(
                data={
                    "tier": ContentTier.SAFE.value,
                    "confidence": 0.90,
                    "reasons": ["No safety concerns detected"],
                    "matches": [],
                    "requires_no_action": True,
                }
            )

        except Exception as e:
            self.logger.error(f"Content classification failed: {e}")
            return StepResult.fail(f"Content classification failed: {e}")

    def _check_patterns(self, content: str, patterns: list[str]) -> list[str]:
        """Check content against a list of patterns."""
        import re

        matches = []

        for pattern in patterns:
            found = re.findall(pattern, content, re.IGNORECASE)
            if found:
                matches.extend(found)

        return matches

    def assess_context_appropriateness(self, content: str, context: dict[str, Any]) -> StepResult:
        """Assess if content is appropriate for the given context.

        Args:
            content: The content to assess
            context: Context information (user age, purpose, etc.)

        Returns:
            StepResult with appropriateness assessment
        """
        try:
            # Get content classification
            classification = self.classify(content)
            if not classification.success:
                return classification

            tier = classification.data["tier"]

            # Check context appropriateness
            appropriate = True
            reasons = []

            if tier == ContentTier.PROHIBITED.value:
                appropriate = False
                reasons.append("Prohibited content is never appropriate")

            elif tier == ContentTier.RESTRICTED.value:
                # Check if context allows restricted content
                if not self._is_restricted_content_allowed(context):
                    appropriate = False
                    reasons.append("Restricted content not allowed in this context")

            elif tier == ContentTier.SENSITIVE.value:
                # Check if user has consented to sensitive content
                if not self._has_sensitive_content_consent(context):
                    appropriate = False
                    reasons.append("User consent required for sensitive content")

            elif tier == ContentTier.REGULATED.value:
                # Check if regulated content is appropriate
                if not self._is_regulated_content_appropriate(context):
                    appropriate = False
                    reasons.append("Regulated content requires appropriate context")

            return StepResult.ok(
                data={"appropriate": appropriate, "tier": tier, "reasons": reasons, "context": context}
            )

        except Exception as e:
            self.logger.error(f"Context assessment failed: {e}")
            return StepResult.fail(f"Context assessment failed: {e}")

    def _is_restricted_content_allowed(self, context: dict[str, Any]) -> bool:
        """Check if restricted content is allowed in context."""
        # Check for educational or research context
        purpose = context.get("purpose", "")
        if purpose in ["educational", "research", "moderation"]:
            return True

        # Check for appropriate user role
        user_role = context.get("user_role", "")
        return user_role in ["moderator", "researcher", "educator"]

    def _has_sensitive_content_consent(self, context: dict[str, Any]) -> bool:
        """Check if user has consented to sensitive content."""
        return context.get("sensitive_content_consent", False)

    def _is_regulated_content_appropriate(self, context: dict[str, Any]) -> bool:
        """Check if regulated content is appropriate for context."""
        # Check for appropriate disclaimer
        has_disclaimer = context.get("has_disclaimer", False)
        if not has_disclaimer:
            return False

        # Check for appropriate user intent
        intent = context.get("intent", "")
        return intent in ["educational", "informational", "research"]

    def generate_safety_report(self, content: str, context: dict[str, Any] | None = None) -> StepResult:
        """Generate a comprehensive safety report.

        Args:
            content: The content to analyze
            context: Optional context information

        Returns:
            StepResult with detailed safety report
        """
        try:
            # Classify content
            classification = self.classify(content)
            if not classification.success:
                return classification

            # Assess context appropriateness
            if context:
                appropriateness = self.assess_context_appropriateness(content, context)
                if not appropriateness.success:
                    return appropriateness
            else:
                appropriateness = StepResult.ok(data={"appropriate": True, "reasons": []})

            # Generate safety report
            tier = classification.data["tier"]
            appropriate = appropriateness.data["appropriate"]

            report = SafetyReport(
                tier=ContentTier(tier),
                confidence=classification.data["confidence"],
                reasons=classification.data["reasons"],
                context_appropriate=appropriate,
                requires_human_review=tier in [ContentTier.PROHIBITED.value, ContentTier.RESTRICTED.value],
                mitigation_suggestions=self._generate_mitigation_suggestions(tier, appropriate),
            )

            return StepResult.ok(data={"safety_report": report})

        except Exception as e:
            self.logger.error(f"Safety report generation failed: {e}")
            return StepResult.fail(f"Safety report generation failed: {e}")

    def _generate_mitigation_suggestions(self, tier: str, appropriate: bool) -> list[str]:
        """Generate suggestions for mitigating safety concerns."""
        suggestions = []

        if tier == ContentTier.PROHIBITED.value:
            suggestions.append("Content should be blocked entirely")
            suggestions.append("Consider reporting to appropriate authorities")

        elif tier == ContentTier.RESTRICTED.value:
            suggestions.append("Review content in appropriate context")
            suggestions.append("Ensure user has necessary permissions")

        elif tier == ContentTier.SENSITIVE.value:
            suggestions.append("Obtain explicit user consent")
            suggestions.append("Provide appropriate warnings")

        elif tier == ContentTier.REGULATED.value:
            suggestions.append("Include appropriate disclaimers")
            suggestions.append("Ensure content is for informational purposes only")

        if not appropriate:
            suggestions.append("Content may not be appropriate for current context")
            suggestions.append("Consider alternative approaches")

        return suggestions
