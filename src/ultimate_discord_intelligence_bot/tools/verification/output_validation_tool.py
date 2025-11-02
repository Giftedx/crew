from __future__ import annotations
from typing import Any
from pydantic import BaseModel, Field
from platform.core.step_result import StepResult
from ultimate_discord_intelligence_bot.tools._base import BaseTool


class ValidationSchema(BaseModel):
    output_data: Any = Field(..., description="The agent output data to be validated.")
    rules: list[str] = Field(..., description="A list of validation rules to apply.")


class OutputValidationTool(BaseTool[dict[str, str]]):
    """A tool to validate agent outputs against a set of rules."""

    name: str = "output_validation_tool"
    description: str = "Validates agent outputs for quality, consistency, and adherence to predefined rules."
    args_schema: type[BaseModel] = ValidationSchema

    def _run(self, output_data: Any, rules: list[str]) -> StepResult:
        """
        Executes the output validation.

        Args:
            output_data: The data produced by an agent.
            rules: A list of rules to validate against.

        Returns:
            A StepResult indicating if the validation passed or failed.
        """
        validation_errors = []
        for rule in rules:
            if rule == "not_empty":
                if not output_data:
                    validation_errors.append("Output data must not be empty.")
            elif rule == "has_summary":
                if isinstance(output_data, dict) and "summary" not in output_data:
                    validation_errors.append("Output must contain a 'summary' field.")
            elif rule.startswith("min_length:"):
                try:
                    min_len = int(rule.split(":")[1])
                    if len(str(output_data)) < min_len:
                        validation_errors.append(f"Output must be at least {min_len} characters long.")
                except (ValueError, IndexError):
                    validation_errors.append(f"Invalid min_length rule: {rule}")
        if validation_errors:
            return StepResult.fail("Output validation failed.", data={"errors": validation_errors})
        return StepResult.ok(data={"status": "validation_passed"})
