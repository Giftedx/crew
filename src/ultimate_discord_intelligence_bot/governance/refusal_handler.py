from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Any
from platform.core.step_result import StepResult

logger = logging.getLogger(__name__)


@dataclass
class RefusalExplanation:
    """Explanation for why a request was refused."""

    category: str
    reason: str
    alternative_suggestion: str | None = None
    additional_context: dict[str, Any] = field(default_factory=dict)


class RefusalHandler:
    """Handles helpful refusals with clear explanations."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.refusal_categories = self._load_refusal_categories()

    def _load_refusal_categories(self) -> dict[str, dict[str, Any]]:
        """Load refusal categories from configuration."""
        return {
            "safety_violation": {
                "message": "I cannot help with that request as it may cause harm",
                "explanation": "This request could lead to physical, emotional, or other forms of harm",
                "alternatives": ["Consider safer alternatives", "Seek professional help"],
            },
            "illegal_content": {
                "message": "I cannot assist with illegal activities",
                "explanation": "This request involves activities that are illegal in most jurisdictions",
                "alternatives": ["Find legal alternatives", "Consult legal professionals"],
            },
            "privacy_violation": {
                "message": "I cannot help with accessing private information",
                "explanation": "This request would violate someone's privacy or security",
                "alternatives": ["Use public information sources", "Respect privacy boundaries"],
            },
            "harmful_content": {
                "message": "I cannot generate content that could be harmful",
                "explanation": "This request could create content that promotes harm or discrimination",
                "alternatives": ["Create positive content", "Focus on constructive topics"],
            },
            "red_line_violation": {
                "message": "I cannot assist with this request due to safety policies",
                "explanation": "This request violates critical safety boundaries",
                "alternatives": ["Consider alternative approaches", "Contact support for guidance"],
            },
        }

    def handle_refusal(self, request: str, category: str, context: dict[str, Any] | None = None) -> StepResult:
        """Handle a refusal with helpful explanation."""
        if context is None:
            context = {}
        self.logger.info("Handling refusal for category: %s", category)
        if category not in self.refusal_categories:
            category = "harmful_content"
        refusal_info = self.refusal_categories[category]
        explanation = RefusalExplanation(
            category=category,
            reason=refusal_info["explanation"],
            alternative_suggestion=refusal_info.get("alternatives", [None])[0],
            additional_context=context,
        )
        response = self._format_refusal_response(refusal_info, explanation)
        self.logger.info("Refusal handled successfully for category: %s", category)
        return StepResult.ok(data={"refusal_response": response, "explanation": explanation, "category": category})

    def _format_refusal_response(self, refusal_info: dict[str, Any], explanation: RefusalExplanation) -> str:
        """Format a helpful refusal response."""
        response_parts = [refusal_info["message"]]
        if explanation.reason:
            response_parts.append(f"\n{explanation.reason}")
        if explanation.alternative_suggestion:
            response_parts.append(f"\nSuggestion: {explanation.alternative_suggestion}")
        return "\n".join(response_parts)

    def suggest_alternatives(self, original_request: str, refusal_category: str) -> StepResult:
        """Suggest alternative approaches for a refused request."""
        self.logger.info("Suggesting alternatives for refused request in category: %s", refusal_category)
        alternatives = self._generate_alternatives(original_request, refusal_category)
        self.logger.info("Generated %d alternatives for refused request", len(alternatives))
        return StepResult.ok(data={"alternatives": alternatives})

    def _generate_alternatives(self, original_request: str, category: str) -> list[str]:
        """Generate alternative suggestions based on the original request and refusal category."""
        alternatives = []
        if category == "safety_violation":
            alternatives.extend(
                [
                    "Consider safer ways to achieve your goal",
                    "Seek guidance from appropriate professionals",
                    "Look for educational resources on the topic",
                ]
            )
        elif category == "illegal_content":
            alternatives.extend(
                [
                    "Find legal alternatives to achieve your objective",
                    "Consult with legal professionals for guidance",
                    "Research lawful approaches to your goal",
                ]
            )
        elif category == "privacy_violation":
            alternatives.extend(
                [
                    "Use publicly available information sources",
                    "Respect privacy boundaries and consent",
                    "Consider ethical data collection methods",
                ]
            )
        elif category == "harmful_content":
            alternatives.extend(
                [
                    "Create positive, constructive content instead",
                    "Focus on educational or helpful topics",
                    "Consider how to present information responsibly",
                ]
            )
        else:
            alternatives.extend(
                [
                    "Consider alternative approaches to your request",
                    "Contact support for guidance on appropriate alternatives",
                    "Review the guidelines for acceptable requests",
                ]
            )
        return alternatives

    def log_refusal(self, request: str, category: str, context: dict[str, Any] | None = None) -> None:
        """Log a refusal event for monitoring and analysis."""
        if context is None:
            context = {}
        self.logger.info(
            "Refusal logged", extra={"refusal_category": category, "request_snippet": request[:100], "context": context}
        )
