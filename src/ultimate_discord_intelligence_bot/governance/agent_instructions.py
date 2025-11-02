"""Agent instruction system with hierarchy support.

This module implements Model Spec instruction hierarchy including
root principles, system defaults, developer rules, user preferences,
and guideline-level suggestions.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from platform.core.step_result import StepResult
from typing import Any


@dataclass
class InstructionContext:
    """Context for instruction generation."""

    user_id: str
    tenant: str
    workspace: str
    developer_config: dict[str, Any] | None = None
    user_preferences: dict[str, Any] | None = None
    session_context: dict[str, Any] | None = None


class AgentInstructions:
    """Agent instruction system with Model Spec hierarchy.

    Implements the chain of command for agent instructions:
    1. Root principles (cannot be overridden)
    2. System defaults (platform defaults)
    3. Developer rules (API customization)
    4. User preferences (end user customization)
    5. Guideline suggestions (soft defaults)
    """

    def __init__(self) -> None:
        """Initialize the agent instruction system."""
        self.logger = logging.getLogger(__name__)
        self._initialize_instruction_templates()

    def _initialize_instruction_templates(self) -> None:
        """Initialize instruction templates for different levels."""
        self.root_principles = [
            "You must never provide information that could cause harm to humans",
            "You must respect human autonomy and dignity in all interactions",
            "You must protect privacy and personal information",
            "You must not engage in illegal activities or provide instructions for them",
            "You must not create or share harmful content",
        ]
        self.system_defaults = [
            "Be helpful, harmless, and honest in all responses",
            "Maintain appropriate professional boundaries",
            "Provide accurate information and admit uncertainty when appropriate",
            "Use clear and direct communication",
            "Respect user preferences when they don't conflict with safety principles",
        ]
        self.developer_guidelines = [
            "Follow domain-specific guidelines provided by the developer",
            "Adapt communication style to the application context",
            "Maintain consistency with the application's purpose",
        ]
        self.user_guidelines = [
            "Respect user-specified communication preferences",
            "Adapt detail level to user needs",
            "Consider user's expertise level in explanations",
        ]
        self.soft_guidelines = [
            "Provide contextually appropriate responses",
            "Match the user's formality level",
            "Include relevant examples when helpful",
            "Structure information clearly and logically",
        ]

    def apply_root_principles(self) -> list[str]:
        """Apply root-level principles that cannot be overridden."""
        return self.root_principles.copy()

    def apply_system_defaults(self) -> list[str]:
        """Apply system-level default instructions."""
        return self.system_defaults.copy()

    def apply_developer_rules(self, developer_config: dict[str, Any]) -> list[str]:
        """Apply developer-specified rules and guidelines.

        Args:
            developer_config: Developer configuration dictionary

        Returns:
            List of developer-specific instructions
        """
        if not developer_config:
            return []
        instructions = []
        if "domain" in developer_config:
            domain = developer_config["domain"]
            instructions.append(f"Focus on {domain} domain knowledge and expertise")
        if "communication_style" in developer_config:
            style = developer_config["communication_style"]
            if style == "formal":
                instructions.append("Use formal, professional language")
            elif style == "casual":
                instructions.append("Use casual, friendly language")
            elif style == "technical":
                instructions.append("Use technical language appropriate for experts")
        if "safety_level" in developer_config:
            safety_level = developer_config["safety_level"]
            if safety_level == "strict":
                instructions.append("Apply strict safety guidelines")
            elif safety_level == "moderate":
                instructions.append("Apply moderate safety guidelines")
        if "custom_instructions" in developer_config:
            custom = developer_config["custom_instructions"]
            if isinstance(custom, list):
                instructions.extend(custom)
            elif isinstance(custom, str):
                instructions.append(custom)
        return instructions

    def apply_user_preferences(self, user_config: dict[str, Any]) -> list[str]:
        """Apply user-specified preferences.

        Args:
            user_config: User configuration dictionary

        Returns:
            List of user-specific instructions
        """
        if not user_config:
            return []
        instructions = []
        if "detail_level" in user_config:
            detail_level = user_config["detail_level"]
            if detail_level == "brief":
                instructions.append("Provide concise, brief responses")
            elif detail_level == "detailed":
                instructions.append("Provide comprehensive, detailed responses")
            elif detail_level == "expert":
                instructions.append("Provide expert-level technical details")
        if "language" in user_config:
            language = user_config["language"]
            instructions.append(f"Respond in {language}")
        if "expertise_level" in user_config:
            level = user_config["expertise_level"]
            if level == "beginner":
                instructions.append("Explain concepts in simple terms for beginners")
            elif level == "intermediate":
                instructions.append("Provide intermediate-level explanations")
            elif level == "expert":
                instructions.append("Use advanced terminology and concepts")
        if "preferences" in user_config:
            prefs = user_config["preferences"]
            if isinstance(prefs, dict):
                if prefs.get("include_examples", False):
                    instructions.append("Include relevant examples in responses")
                if prefs.get("include_sources", False):
                    instructions.append("Cite sources when providing information")
                if prefs.get("step_by_step", False):
                    instructions.append("Provide step-by-step instructions when appropriate")
        return instructions

    def generate_final_instructions(self, context: InstructionContext) -> StepResult:
        """Generate final instructions by combining all levels.

        Args:
            context: Instruction context with user and configuration data

        Returns:
            StepResult with final instruction set
        """
        try:
            instructions = []
            root_instructions = self.apply_root_principles()
            instructions.extend(root_instructions)
            system_instructions = self.apply_system_defaults()
            instructions.extend(system_instructions)
            if context.developer_config:
                developer_instructions = self.apply_developer_rules(context.developer_config)
                instructions.extend(developer_instructions)
            if context.user_preferences:
                user_instructions = self.apply_user_preferences(context.user_preferences)
                instructions.extend(user_instructions)
            soft_instructions = self.soft_guidelines.copy()
            instructions.extend(soft_instructions)
            resolved_instructions = self._resolve_conflicts(instructions)
            final_instructions = self._format_instructions(resolved_instructions, context)
            return StepResult.ok(
                data={
                    "instructions": final_instructions,
                    "instruction_count": len(resolved_instructions),
                    "context_applied": {
                        "root_principles": len(root_instructions),
                        "system_defaults": len(system_instructions),
                        "developer_rules": len(developer_instructions) if context.developer_config else 0,
                        "user_preferences": len(user_instructions) if context.user_preferences else 0,
                        "soft_guidelines": len(soft_instructions),
                    },
                }
            )
        except Exception as e:
            self.logger.error(f"Instruction generation failed: {e}")
            return StepResult.fail(f"Instruction generation failed: {e}")

    def _resolve_conflicts(self, instructions: list[str]) -> list[str]:
        """Resolve conflicts between instructions.

        Args:
            instructions: List of potentially conflicting instructions

        Returns:
            List of resolved instructions
        """
        return instructions

    def _format_instructions(self, instructions: list[str], context: InstructionContext) -> str:
        """Format instructions into a final instruction string.

        Args:
            instructions: List of instructions
            context: Instruction context

        Returns:
            Formatted instruction string
        """
        if not instructions:
            return "Follow standard AI safety and helpfulness guidelines."
        formatted = "You are an AI assistant. Follow these instructions:\n\n"
        for i, instruction in enumerate(instructions, 1):
            formatted += f"{i}. {instruction}\n"
        if context.tenant:
            formatted += f"\nContext: Operating in tenant '{context.tenant}'"
        if context.workspace:
            formatted += f", workspace '{context.workspace}'"
        return formatted

    def validate_instructions(self, instructions: list[str]) -> StepResult:
        """Validate a set of instructions for conflicts and safety.

        Args:
            instructions: List of instructions to validate

        Returns:
            StepResult with validation results
        """
        try:
            issues = []
            warnings = []
            safety_keywords = ["harm", "dangerous", "illegal", "violence", "hate"]
            for instruction in instructions:
                instruction_lower = instruction.lower()
                for keyword in safety_keywords:
                    if keyword in instruction_lower:
                        issues.append(f"Potential safety concern: {instruction}")
            conflicts = self._detect_conflicts(instructions)
            if conflicts:
                issues.extend(conflicts)
            unclear_instructions = self._detect_unclear_instructions(instructions)
            if unclear_instructions:
                warnings.extend(unclear_instructions)
            if issues:
                return StepResult.fail(
                    error="Instruction validation failed", data={"issues": issues, "warnings": warnings, "valid": False}
                )
            else:
                return StepResult.ok(data={"issues": issues, "warnings": warnings, "valid": True})
        except Exception as e:
            self.logger.error(f"Instruction validation failed: {e}")
            return StepResult.fail(f"Instruction validation failed: {e}")

    def _detect_conflicts(self, instructions: list[str]) -> list[str]:
        """Detect conflicts between instructions."""
        conflicts = []
        for i, instruction1 in enumerate(instructions):
            for j, instruction2 in enumerate(instructions[i + 1 :], i + 1):
                if self._are_conflicting(instruction1, instruction2):
                    conflicts.append(
                        f"Conflict between instructions {i + 1} and {j + 1}: '{instruction1}' vs '{instruction2}'"
                    )
        return conflicts

    def _are_conflicting(self, instruction1: str, instruction2: str) -> bool:
        """Check if two instructions conflict."""
        instruction1_lower = instruction1.lower()
        instruction2_lower = instruction2.lower()
        contradictions = [("always", "never"), ("formal", "casual"), ("brief", "detailed"), ("technical", "simple")]
        for term1, term2 in contradictions:
            if term1 in instruction1_lower and term2 in instruction2_lower:
                return True
            if term2 in instruction1_lower and term1 in instruction2_lower:
                return True
        return False

    def _detect_unclear_instructions(self, instructions: list[str]) -> list[str]:
        """Detect unclear or ambiguous instructions."""
        unclear = []
        for instruction in instructions:
            vague_terms = ["appropriate", "reasonable", "when necessary", "as needed"]
            if any(term in instruction.lower() for term in vague_terms):
                unclear.append(f"Vague instruction: {instruction}")
            if len(instruction.split()) > 20:
                unclear.append(f"Complex instruction: {instruction}")
        return unclear
