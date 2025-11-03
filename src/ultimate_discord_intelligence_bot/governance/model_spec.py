"""Model Spec core framework with chain of command implementation.

This module implements OpenAI's Model Spec principles including the chain of command
hierarchy, instruction evaluation, and compliance checking.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from platform.core.step_result import StepResult
from typing import Any, Literal


class ComplianceLevel(Enum):
    """Compliance levels for Model Spec adherence."""

    FULLY_COMPLIANT = "fully_compliant"
    MOSTLY_COMPLIANT = "mostly_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NON_COMPLIANT = "non_compliant"
    VIOLATION = "violation"


@dataclass
class ChainOfCommand:
    """Represents a rule in the chain of command hierarchy.

    The chain of command determines which rules take precedence when conflicts arise.
    Higher priority rules can override lower priority ones, but only if explicitly allowed.
    """

    level: Literal["root", "system", "developer", "user", "guideline"]
    priority: int
    principle: str
    can_override: bool = False
    description: str = ""
    examples: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate chain of command configuration."""
        if self.level == "root" and self.can_override:
            raise ValueError("Root-level principles cannot be overridden")
        if self.priority < 1 or self.priority > 100:
            raise ValueError("Priority must be between 1 and 100")


@dataclass
class ComplianceReport:
    """Report of Model Spec compliance for a given response."""

    compliance_level: ComplianceLevel
    violations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    applied_rules: list[str] = field(default_factory=list)
    confidence_score: float = 0.0
    human_review_required: bool = False
    recommendations: list[str] = field(default_factory=list)


class ModelSpecEnforcer:
    """Enforces OpenAI Model Spec principles and chain of command.

    This class implements the core governance logic for ensuring AI behavior
    aligns with Model Spec principles including safety, helpfulness, and honesty.
    """

    def __init__(self) -> None:
        """Initialize the Model Spec enforcer."""
        self.logger = logging.getLogger(__name__)
        self.chain_of_command: list[ChainOfCommand] = []
        self._initialize_default_rules()

    def _initialize_default_rules(self) -> None:
        """Initialize default Model Spec rules."""
        self.chain_of_command.extend(
            [
                ChainOfCommand(
                    level="root",
                    priority=1,
                    principle="Never provide information that could cause harm",
                    can_override=False,
                    description="Fundamental safety principle that cannot be violated",
                    examples=["No instructions for violence", "No harmful medical advice"],
                ),
                ChainOfCommand(
                    level="root",
                    priority=2,
                    principle="Respect human autonomy and dignity",
                    can_override=False,
                    description="Preserve human agency and treat all people with respect",
                    examples=["No manipulation", "Respect user choices"],
                ),
                ChainOfCommand(
                    level="root",
                    priority=3,
                    principle="Protect privacy and personal information",
                    can_override=False,
                    description="Never share or misuse personal data",
                    examples=["No data harvesting", "Respect confidentiality"],
                ),
            ]
        )
        self.chain_of_command.extend(
            [
                ChainOfCommand(
                    level="system",
                    priority=10,
                    principle="Be helpful, harmless, and honest",
                    can_override=True,
                    description="Core behavioral guidelines for AI assistance",
                    examples=["Provide accurate information", "Admit uncertainty"],
                ),
                ChainOfCommand(
                    level="system",
                    priority=11,
                    principle="Maintain appropriate boundaries",
                    can_override=True,
                    description="Keep interactions professional and appropriate",
                    examples=["No personal relationships", "Professional tone"],
                ),
            ]
        )
        self.chain_of_command.extend(
            [
                ChainOfCommand(
                    level="developer",
                    priority=20,
                    principle="Follow developer-specified guidelines",
                    can_override=True,
                    description="Custom rules set by API developers",
                    examples=["Custom safety rules", "Domain-specific guidelines"],
                )
            ]
        )
        self.chain_of_command.extend(
            [
                ChainOfCommand(
                    level="user",
                    priority=30,
                    principle="Respect user preferences when appropriate",
                    can_override=True,
                    description="User-specified preferences that don't violate higher rules",
                    examples=["Communication style", "Detail level preferences"],
                )
            ]
        )
        self.chain_of_command.extend(
            [
                ChainOfCommand(
                    level="guideline",
                    priority=40,
                    principle="Provide contextually appropriate responses",
                    can_override=True,
                    description="Soft guidelines for response appropriateness",
                    examples=["Match user's formality level", "Provide relevant examples"],
                )
            ]
        )

    def add_rule(self, rule: ChainOfCommand) -> StepResult:
        """Add a new rule to the chain of command.

        Args:
            rule: The rule to add

        Returns:
            StepResult indicating success or failure
        """
        try:
            conflicts = self._check_rule_conflicts(rule)
            if conflicts:
                return StepResult.fail(f"Rule conflicts with existing rules: {conflicts}")
            self.chain_of_command.append(rule)
            self.chain_of_command.sort(key=lambda r: r.priority)
            self.logger.info(f"Added rule: {rule.principle} (priority {rule.priority})")
            return StepResult.ok(data={"rule_added": rule.principle})
        except Exception as e:
            self.logger.error(f"Failed to add rule: {e}")
            return StepResult.fail(f"Failed to add rule: {e}")

    def _check_rule_conflicts(self, new_rule: ChainOfCommand) -> list[str]:
        """Check for conflicts between a new rule and existing rules."""
        conflicts = []
        for existing_rule in self.chain_of_command:
            if existing_rule.priority == new_rule.priority and existing_rule.principle != new_rule.principle:
                conflicts.append(f"Priority {new_rule.priority} conflict with {existing_rule.principle}")
            if (
                new_rule.priority < existing_rule.priority
                and (not existing_rule.can_override)
                and (new_rule.level != "root")
            ):
                conflicts.append(f"Cannot override non-overridable rule: {existing_rule.principle}")
        return conflicts

    def evaluate_instruction(self, instruction: str, context: dict[str, Any]) -> StepResult:
        """Evaluate an instruction against Model Spec principles.

        Args:
            instruction: The instruction to evaluate
            context: Additional context for evaluation

        Returns:
            StepResult with evaluation results
        """
        try:
            violations = []
            warnings = []
            applied_rules = []
            for rule in self.chain_of_command:
                if self._is_rule_applicable(rule, context):
                    result = self._evaluate_against_rule(instruction, rule, context)
                    if result["violation"]:
                        violations.append(result["reason"])
                    elif result["warning"]:
                        warnings.append(result["reason"])
                    applied_rules.append(rule.principle)
            compliance_level = self._determine_compliance_level(violations, warnings)
            return StepResult.ok(
                data={
                    "instruction": instruction,
                    "compliance_level": compliance_level.value,
                    "violations": violations,
                    "warnings": warnings,
                    "applied_rules": applied_rules,
                    "human_review_required": len(violations) > 0,
                }
            )
        except Exception as e:
            self.logger.error(f"Failed to evaluate instruction: {e}")
            return StepResult.fail(f"Instruction evaluation failed: {e}")

    def _is_rule_applicable(self, rule: ChainOfCommand, context: dict[str, Any]) -> bool:
        """Determine if a rule is applicable to the given context."""
        return True

    def _evaluate_against_rule(self, instruction: str, rule: ChainOfCommand, context: dict[str, Any]) -> dict[str, Any]:
        """Evaluate an instruction against a specific rule."""
        instruction_lower = instruction.lower()
        if rule.level == "root" and any(
            term in instruction_lower for term in ["harm", "violence", "illegal", "dangerous"]
        ):
            return {
                "violation": True,
                "warning": False,
                "reason": f"Potential violation of root principle: {rule.principle}",
            }
        if any(term in instruction_lower for term in ["personal", "private", "confidential"]):
            return {"violation": False, "warning": True, "reason": f"Warning for rule: {rule.principle}"}
        return {"violation": False, "warning": False, "reason": "No issues detected"}

    def _determine_compliance_level(self, violations: list[str], warnings: list[str]) -> ComplianceLevel:
        """Determine the overall compliance level."""
        if violations:
            return ComplianceLevel.VIOLATION
        elif len(warnings) > 2:
            return ComplianceLevel.PARTIALLY_COMPLIANT
        elif warnings:
            return ComplianceLevel.MOSTLY_COMPLIANT
        else:
            return ComplianceLevel.FULLY_COMPLIANT

    def resolve_conflicts(self, instructions: list[str]) -> StepResult:
        """Resolve conflicts between multiple instructions.

        Args:
            instructions: List of potentially conflicting instructions

        Returns:
            StepResult with resolved instruction list
        """
        try:
            if not instructions:
                return StepResult.ok(data={"resolved_instructions": []})
            resolved = instructions.copy()
            self.logger.info(f"Resolved {len(instructions)} instructions")
            return StepResult.ok(data={"resolved_instructions": resolved})
        except Exception as e:
            self.logger.error(f"Failed to resolve conflicts: {e}")
            return StepResult.fail(f"Conflict resolution failed: {e}")

    def check_compliance(self, response: str) -> StepResult:
        """Check a response for Model Spec compliance.

        Args:
            response: The response to check

        Returns:
            StepResult with compliance report
        """
        try:
            violations = []
            warnings = []
            applied_rules = []
            for rule in self.chain_of_command:
                result = self._check_response_against_rule(response, rule)
                if result["violation"]:
                    violations.append(result["reason"])
                elif result["warning"]:
                    warnings.append(result["reason"])
                applied_rules.append(rule.principle)
            compliance_level = self._determine_compliance_level(violations, warnings)
            report = ComplianceReport(
                compliance_level=compliance_level,
                violations=violations,
                warnings=warnings,
                applied_rules=applied_rules,
                confidence_score=0.8,
                human_review_required=len(violations) > 0,
                recommendations=self._generate_recommendations(violations, warnings),
            )
            return StepResult.ok(data={"compliance_report": report})
        except Exception as e:
            self.logger.error(f"Failed to check compliance: {e}")
            return StepResult.fail(f"Compliance check failed: {e}")

    def _check_response_against_rule(self, response: str, rule: ChainOfCommand) -> dict[str, Any]:
        """Check a response against a specific rule."""
        response_lower = response.lower()
        if rule.level == "root" and any(term in response_lower for term in ["harmful", "dangerous", "illegal"]):
            return {
                "violation": True,
                "warning": False,
                "reason": f"Response violates root principle: {rule.principle}",
            }
        return {"violation": False, "warning": False, "reason": "No issues detected"}

    def _generate_recommendations(self, violations: list[str], warnings: list[str]) -> list[str]:
        """Generate recommendations based on violations and warnings."""
        recommendations = []
        if violations:
            recommendations.append("Review and revise response to address violations")
            recommendations.append("Consider human review for complex cases")
        if warnings:
            recommendations.append("Consider addressing warnings to improve compliance")
        if not violations and (not warnings):
            recommendations.append("Response appears compliant with Model Spec")
        return recommendations
