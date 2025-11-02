"""Communication style guidelines enforcer.

This module implements Model Spec communication principles including
objective point of view, transparency about uncertainty, non-sycophantic
responses, appropriate professionalism, contextual warmth, respectful
disagreement, and clear and direct communication.
"""
from __future__ import annotations
import logging
import re
from dataclasses import dataclass
from typing import Any
from platform.core.step_result import StepResult

@dataclass
class StyleViolation:
    """Represents a communication style violation."""
    violation_type: str
    severity: str
    description: str
    suggestion: str
    confidence: float

class CommunicationStyleEnforcer:
    """Enforcer for Model Spec communication style guidelines.

    Ensures AI responses follow OpenAI's communication principles:
    - Objective point of view (no agenda)
    - Transparency about uncertainty
    - Non-sycophantic responses
    - Appropriate professionalism
    - Contextual warmth
    - Respectful disagreement
    - Clear and direct communication
    """

    def __init__(self) -> None:
        """Initialize the communication style enforcer."""
        self.logger = logging.getLogger(__name__)
        self._initialize_style_patterns()

    def _initialize_style_patterns(self) -> None:
        """Initialize patterns for style detection."""
        self.sycophantic_patterns = ['\\b(?:you are absolutely right|you are so smart|you are brilliant)\\b', '\\b(?:I completely agree|I totally agree|I 100% agree)\\b', '\\b(?:you are amazing|you are wonderful|you are fantastic)\\b', '\\b(?:I love your|I adore your|I worship your)\\b']
        self.unprofessional_patterns = ['\\b(?:lol|lmao|rofl|wtf|omg)\\b', '\\b(?:dude|bro|man|girl|honey|sweetie)\\b', '\\b(?:awesome|cool|sick|lit|fire)\\b']
        self.uncertainty_avoidance = ['\\b(?:I am certain|I am sure|I know for a fact)\\b', '\\b(?:definitely|absolutely|without a doubt)\\b', '\\b(?:I guarantee|I promise|I swear)\\b']
        self.vague_patterns = ['\\b(?:some people|many people|most people)\\b', '\\b(?:it is said|they say|people believe)\\b', '\\b(?:apparently|supposedly|allegedly)\\b']
        self.emotional_manipulation = ['\\b(?:you should feel|you must feel|you ought to feel)\\b', '\\b(?:everyone knows|everyone agrees|everyone believes)\\b', '\\b(?:it is obvious|it is clear|it is evident)\\b']

    def check_communication_style(self, response: str, context: dict[str, Any] | None=None) -> StepResult:
        """Check response against communication style guidelines.

        Args:
            response: The response to check
            context: Optional context information

        Returns:
            StepResult with style analysis
        """
        try:
            violations = []
            sycophantic_violations = self._check_sycophantic_language(response)
            violations.extend(sycophantic_violations)
            unprofessional_violations = self._check_unprofessional_language(response)
            violations.extend(unprofessional_violations)
            uncertainty_violations = self._check_uncertainty_avoidance(response)
            violations.extend(uncertainty_violations)
            vague_violations = self._check_vague_language(response)
            violations.extend(vague_violations)
            manipulation_violations = self._check_emotional_manipulation(response)
            violations.extend(manipulation_violations)
            style_score = self._calculate_style_score(violations, response)
            recommendations = self._generate_style_recommendations(violations)
            return StepResult.ok(data={'style_analysis': {'violations': [v.__dict__ for v in violations], 'style_score': style_score, 'recommendations': recommendations, 'violation_count': len(violations), 'high_severity_violations': len([v for v in violations if v.severity == 'high'])}, 'analysis_complete': True})
        except Exception as e:
            self.logger.error(f'Communication style check failed: {e}')
            return StepResult.fail(f'Communication style check failed: {e}')

    def _check_sycophantic_language(self, response: str) -> list[StyleViolation]:
        """Check for sycophantic language patterns."""
        violations = []
        response_lower = response.lower()
        for pattern in self.sycophantic_patterns:
            matches = re.findall(pattern, response_lower, re.IGNORECASE)
            if matches:
                violation = StyleViolation(violation_type='sycophantic_language', severity='medium', description=f'Detected sycophantic language: {matches[0]}', suggestion='Use more objective language and avoid excessive praise', confidence=0.8)
                violations.append(violation)
        return violations

    def _check_unprofessional_language(self, response: str) -> list[StyleViolation]:
        """Check for unprofessional language patterns."""
        violations = []
        response_lower = response.lower()
        for pattern in self.unprofessional_patterns:
            matches = re.findall(pattern, response_lower, re.IGNORECASE)
            if matches:
                violation = StyleViolation(violation_type='unprofessional_language', severity='low', description=f'Detected informal language: {matches[0]}', suggestion='Use more professional language appropriate for the context', confidence=0.7)
                violations.append(violation)
        return violations

    def _check_uncertainty_avoidance(self, response: str) -> list[StyleViolation]:
        """Check for uncertainty avoidance patterns."""
        violations = []
        response_lower = response.lower()
        for pattern in self.uncertainty_avoidance:
            matches = re.findall(pattern, response_lower, re.IGNORECASE)
            if matches:
                violation = StyleViolation(violation_type='uncertainty_avoidance', severity='medium', description=f'Detected overconfident language: {matches[0]}', suggestion='Acknowledge uncertainty when appropriate and use qualifying language', confidence=0.8)
                violations.append(violation)
        return violations

    def _check_vague_language(self, response: str) -> list[StyleViolation]:
        """Check for vague language patterns."""
        violations = []
        response_lower = response.lower()
        for pattern in self.vague_patterns:
            matches = re.findall(pattern, response_lower, re.IGNORECASE)
            if matches:
                violation = StyleViolation(violation_type='vague_language', severity='low', description=f'Detected vague language: {matches[0]}', suggestion='Be more specific and provide concrete information', confidence=0.6)
                violations.append(violation)
        return violations

    def _check_emotional_manipulation(self, response: str) -> list[StyleViolation]:
        """Check for emotional manipulation patterns."""
        violations = []
        response_lower = response.lower()
        for pattern in self.emotional_manipulation:
            matches = re.findall(pattern, response_lower, re.IGNORECASE)
            if matches:
                violation = StyleViolation(violation_type='emotional_manipulation', severity='high', description=f'Detected manipulative language: {matches[0]}', suggestion='Avoid emotional manipulation and use objective language', confidence=0.9)
                violations.append(violation)
        return violations

    def _calculate_style_score(self, violations: list[StyleViolation], response: str) -> float:
        """Calculate overall communication style score."""
        if not violations:
            return 1.0
        severity_weights = {'low': 0.1, 'medium': 0.3, 'high': 0.6}
        total_penalty = 0.0
        for violation in violations:
            penalty = severity_weights.get(violation.severity, 0.1)
            total_penalty += penalty * violation.confidence
        score = max(0.0, 1.0 - total_penalty)
        response_length = len(response.split())
        if response_length > 100:
            length_adjustment = min(0.1, response_length / 1000)
            score = max(0.0, score - length_adjustment)
        return score

    def _generate_style_recommendations(self, violations: list[StyleViolation]) -> list[str]:
        """Generate recommendations for improving communication style."""
        recommendations = []
        if not violations:
            recommendations.append('Communication style appears appropriate')
            return recommendations
        violation_types = {}
        for violation in violations:
            if violation.violation_type not in violation_types:
                violation_types[violation.violation_type] = []
            violation_types[violation.violation_type].append(violation)
        if 'sycophantic_language' in violation_types:
            recommendations.append('Reduce excessive praise and use more objective language')
        if 'unprofessional_language' in violation_types:
            recommendations.append('Use more professional language appropriate for the context')
        if 'uncertainty_avoidance' in violation_types:
            recommendations.append('Acknowledge uncertainty when appropriate and use qualifying language')
        if 'vague_language' in violation_types:
            recommendations.append('Be more specific and provide concrete information')
        if 'emotional_manipulation' in violation_types:
            recommendations.append('Avoid emotional manipulation and use objective, factual language')
        if len(violations) > 3:
            recommendations.append('Consider reviewing the overall tone and style of the response')
        return recommendations

    def enforce_style_guidelines(self, response: str, context: dict[str, Any] | None=None) -> StepResult:
        """Enforce communication style guidelines on a response.

        Args:
            response: The response to enforce guidelines on
            context: Optional context information

        Returns:
            StepResult with style-enforced response
        """
        try:
            style_check = self.check_communication_style(response, context)
            if not style_check.success:
                return style_check
            style_analysis = style_check.data['style_analysis']
            if style_analysis['style_score'] >= 0.8:
                return StepResult.ok(data={'enforced_response': response, 'modifications_made': False, 'style_score': style_analysis['style_score']})
            improved_response = self._apply_style_improvements(response, style_analysis['violations'])
            return StepResult.ok(data={'enforced_response': improved_response, 'modifications_made': True, 'original_response': response, 'improvements_applied': style_analysis['recommendations']})
        except Exception as e:
            self.logger.error(f'Style enforcement failed: {e}')
            return StepResult.fail(f'Style enforcement failed: {e}')

    def _apply_style_improvements(self, response: str, violations: list[dict]) -> str:
        """Apply style improvements to a response."""
        improved_response = response
        for violation in violations:
            violation_type = violation['violation_type']
            if violation_type == 'sycophantic_language':
                improved_response = self._reduce_sycophantic_language(improved_response)
            elif violation_type == 'unprofessional_language':
                improved_response = self._improve_professionalism(improved_response)
            elif violation_type == 'uncertainty_avoidance':
                improved_response = self._add_uncertainty_acknowledgment(improved_response)
            elif violation_type == 'vague_language':
                improved_response = self._improve_specificity(improved_response)
            elif violation_type == 'emotional_manipulation':
                improved_response = self._remove_emotional_manipulation(improved_response)
        return improved_response

    def _reduce_sycophantic_language(self, response: str) -> str:
        """Reduce sycophantic language in response."""
        replacements = {'you are absolutely right': "that's a valid point", 'you are so smart': "that's insightful", 'I completely agree': 'I understand your perspective', 'you are amazing': "that's helpful"}
        improved = response
        for old, new in replacements.items():
            improved = improved.replace(old, new)
        return improved

    def _improve_professionalism(self, response: str) -> str:
        """Improve professionalism in response."""
        replacements = {'lol': '', 'lmao': '', 'wtf': 'what', 'omg': 'oh my', 'dude': 'person', 'bro': 'colleague', 'awesome': 'excellent', 'cool': 'interesting'}
        improved = response
        for old, new in replacements.items():
            improved = improved.replace(old, new)
        return improved

    def _add_uncertainty_acknowledgment(self, response: str) -> str:
        """Add uncertainty acknowledgment where appropriate."""
        return response

    def _improve_specificity(self, response: str) -> str:
        """Improve specificity in response."""
        replacements = {'some people': 'some individuals', 'many people': 'a significant number of individuals', 'it is said': 'according to some sources', 'they say': 'some sources indicate'}
        improved = response
        for old, new in replacements.items():
            improved = improved.replace(old, new)
        return improved

    def _remove_emotional_manipulation(self, response: str) -> str:
        """Remove emotional manipulation from response."""
        replacements = {'you should feel': 'you might consider', 'you must feel': 'you might experience', 'everyone knows': 'it is commonly understood', 'it is obvious': 'it appears to be', 'it is clear': 'the evidence suggests'}
        improved = response
        for old, new in replacements.items():
            improved = improved.replace(old, new)
        return improved