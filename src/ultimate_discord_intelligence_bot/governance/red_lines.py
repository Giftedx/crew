"""Red-line principles guard for critical safety boundaries.

This module implements hard boundaries that must never be violated, including
child safety, violence prevention, weapons development blocking, privacy protection,
election integrity safeguards, and human autonomy preservation.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

from ultimate_discord_intelligence_bot.step_result import StepResult


class RedLineType(Enum):
    """Types of red-line violations."""

    CHILD_SAFETY = "child_safety"
    VIOLENCE = "violence"
    WEAPONS = "weapons"
    PRIVACY = "privacy"
    ELECTION = "election"
    AUTONOMY = "autonomy"
    HATE_SPEECH = "hate_speech"
    TERRORISM = "terrorism"


@dataclass
class RedLineViolation:
    """Represents a red-line violation."""

    violation_type: RedLineType
    severity: str  # "critical", "high", "medium"
    description: str
    detected_patterns: list[str]
    confidence: float
    requires_immediate_action: bool = True


class RedLineGuard:
    """Guard for enforcing red-line principles that must never be violated.

    This class implements pre-execution and post-execution checks for critical
    safety boundaries that cannot be overridden by any other rules.
    """

    def __init__(self) -> None:
        """Initialize the red-line guard."""
        self.logger = logging.getLogger(__name__)
        self._initialize_patterns()

    def _initialize_patterns(self) -> None:
        """Initialize detection patterns for red-line violations."""
        self.patterns = {
            RedLineType.CHILD_SAFETY: [
                r"\b(?:child|minor|underage).*(?:sexual|porn|nude|explicit)\b",
                r"\b(?:csam|child.*porn|cp)\b",
                r"\b(?:grooming|luring).*(?:child|minor)\b",
            ],
            RedLineType.VIOLENCE: [
                r"\b(?:kill|murder|assassinate|execute).*(?:person|people|human)\b",
                r"\b(?:torture|mutilate|dismember).*(?:person|people|human)\b",
                r"\b(?:genocide|ethnic.*cleansing)\b",
                r"\b(?:human.*trafficking|slavery)\b",
            ],
            RedLineType.WEAPONS: [
                r"\b(?:bomb|explosive|dynamite|tnt).*(?:making|construction|recipe)\b",
                r"\b(?:chemical|biological|nuclear).*(?:weapon|attack)\b",
                r"\b(?:weapon.*grade|military.*grade).*(?:chemical|biological)\b",
            ],
            RedLineType.PRIVACY: [
                r"\b(?:doxx|doxxing|dox).*(?:address|phone|ssn|social.*security)\b",
                r"\b(?:stalk|stalking|harass).*(?:person|individual)\b",
                r"\b(?:revenge.*porn|non.*consensual.*image)\b",
            ],
            RedLineType.ELECTION: [
                r"\b(?:voter.*suppression|election.*fraud|ballot.*stuffing)\b",
                r"\b(?:disinformation|misinformation).*(?:election|voting)\b",
                r"\b(?:foreign.*interference|election.*hacking)\b",
            ],
            RedLineType.AUTONOMY: [
                r"\b(?:manipulate|coerce|force).*(?:person|individual|human)\b",
                r"\b(?:brainwash|indoctrinate|control).*(?:mind|thought)\b",
                r"\b(?:slavery|forced.*labor|human.*trafficking)\b",
            ],
            RedLineType.HATE_SPEECH: [
                r"\b(?:nazi|hitler|holocaust.*denial)\b",
                r"\b(?:white.*supremacy|racial.*superiority)\b",
                r"\b(?:genocide.*advocacy|ethnic.*cleansing)\b",
            ],
            RedLineType.TERRORISM: [
                r"\b(?:terrorist|terrorism|jihad|islamic.*state)\b",
                r"\b(?:bomb.*threat|terrorist.*attack)\b",
                r"\b(?:radicalization|extremist.*recruitment)\b",
            ],
        }

    def pre_execution_check(self, instruction: str, context: dict[str, Any]) -> StepResult:
        """Perform pre-execution red-line checks.

        Args:
            instruction: The instruction to check
            context: Additional context

        Returns:
            StepResult with violation details if found
        """
        try:
            violations = self._detect_violations(instruction)

            if violations:
                self.logger.warning(f"Red-line violations detected in instruction: {len(violations)}")
                return StepResult.fail(
                    error="Red-line violations detected",
                    data={
                        "violations": [v.__dict__ for v in violations],
                        "instruction_blocked": True,
                        "requires_human_review": True,
                    },
                )

            return StepResult.ok(data={"pre_check_passed": True})

        except Exception as e:
            self.logger.error(f"Pre-execution check failed: {e}")
            return StepResult.fail(f"Pre-execution check failed: {e}")

    def post_execution_check(self, response: str, context: dict[str, Any]) -> StepResult:
        """Perform post-execution red-line checks.

        Args:
            response: The response to check
            context: Additional context

        Returns:
            StepResult with violation details if found
        """
        try:
            violations = self._detect_violations(response)

            if violations:
                self.logger.warning(f"Red-line violations detected in response: {len(violations)}")
                return StepResult.fail(
                    error="Red-line violations detected in response",
                    data={
                        "violations": [v.__dict__ for v in violations],
                        "response_blocked": True,
                        "requires_human_review": True,
                    },
                )

            return StepResult.ok(data={"post_check_passed": True})

        except Exception as e:
            self.logger.error(f"Post-execution check failed: {e}")
            return StepResult.fail(f"Post-execution check failed: {e}")

    def _detect_violations(self, text: str) -> list[RedLineViolation]:
        """Detect red-line violations in text."""
        violations = []
        text_lower = text.lower()

        for violation_type, patterns in self.patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                if matches:
                    violation = RedLineViolation(
                        violation_type=violation_type,
                        severity=self._get_severity(violation_type),
                        description=f"Detected {violation_type.value} violation",
                        detected_patterns=matches,
                        confidence=0.9,  # Simplified confidence scoring
                        requires_immediate_action=True,
                    )
                    violations.append(violation)

        return violations

    def _get_severity(self, violation_type: RedLineType) -> str:
        """Get severity level for a violation type."""
        severity_map = {
            RedLineType.CHILD_SAFETY: "critical",
            RedLineType.VIOLENCE: "critical",
            RedLineType.WEAPONS: "critical",
            RedLineType.TERRORISM: "critical",
            RedLineType.PRIVACY: "high",
            RedLineType.ELECTION: "high",
            RedLineType.AUTONOMY: "high",
            RedLineType.HATE_SPEECH: "medium",
        }
        return severity_map.get(violation_type, "medium")

    def check_content_safety(self, content: str, content_type: str = "text") -> StepResult:
        """Check content for red-line violations.

        Args:
            content: The content to check
            content_type: Type of content (text, image, video, etc.)

        Returns:
            StepResult with safety assessment
        """
        try:
            violations = self._detect_violations(content)

            if violations:
                return StepResult.fail(
                    error="Content safety violations detected",
                    data={"safe": False, "violations": [v.__dict__ for v in violations], "requires_moderation": True},
                )

            return StepResult.ok(data={"safe": True, "violations": [], "requires_moderation": False})

        except Exception as e:
            self.logger.error(f"Content safety check failed: {e}")
            return StepResult.fail(f"Content safety check failed: {e}")

    def get_violation_explanation(self, violation: RedLineViolation) -> str:
        """Get a human-readable explanation of a violation."""
        explanations = {
            RedLineType.CHILD_SAFETY: "Content involving minors in sexual contexts is strictly prohibited",
            RedLineType.VIOLENCE: "Content promoting violence against people is not allowed",
            RedLineType.WEAPONS: "Instructions for creating weapons or explosives are prohibited",
            RedLineType.PRIVACY: "Sharing personal information without consent violates privacy",
            RedLineType.ELECTION: "Content that undermines democratic processes is not allowed",
            RedLineType.AUTONOMY: "Content that manipulates or coerces people is prohibited",
            RedLineType.HATE_SPEECH: "Hate speech and discriminatory content is not allowed",
            RedLineType.TERRORISM: "Content promoting terrorism or violent extremism is prohibited",
        }

        base_explanation = explanations.get(violation.violation_type, "Content violates safety guidelines")
        return f"{base_explanation}. Detected patterns: {', '.join(violation.detected_patterns)}"
